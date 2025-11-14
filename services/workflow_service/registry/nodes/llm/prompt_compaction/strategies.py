"""
Compaction strategies for prompt management (v2.1).

Provides three main strategies:
1. SummarizationStrategy: LLM-based summarization (continued/hierarchical or from-scratch)
2. ExtractionStrategy: Vector-based relevant message extraction
3. HybridStrategy: Combination of extraction and summarization

v2.1 Features:
- Enhanced extraction with 3 construction strategies (dump, extract_full, llm_rewrite)
- Hybrid strategy with reserved extraction budget (5% default)
- Bipartite graph metadata tracking
- Message section labels
- Configurable model provider with retry logic
- Duplicate chunk tracking and overflow handling

Each strategy implements the CompactionStrategy interface and returns a CompactionResult.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Set, TYPE_CHECKING
from enum import Enum
from uuid import uuid4
from datetime import datetime
from collections import defaultdict
import logging

from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, ToolMessage

from workflow_service.registry.nodes.llm.config import ModelMetadata, LLMModelProvider
if TYPE_CHECKING:
    from workflow_service.registry.nodes.llm.prompt_compaction.compactor import PromptCompactionConfig
from workflow_service.registry.nodes.llm.prompt_compaction.context_manager import ContextBudget
from workflow_service.registry.nodes.llm.prompt_compaction.token_utils import (
    count_tokens,
    count_tokens_in_message,
    count_tokens_in_text,
    estimate_tokens_for_summary,
    summarize_oversized_message,
    check_prompt_size_and_split,
    MessageTokenCache,
)
from workflow_service.registry.nodes.llm.prompt_compaction.utils import (
    format_messages,
    format_message_for_embedding,
    format_messages_for_embedding,
    cosine_similarity,
    parse_salient_points,
    create_summary_message,
    create_extraction_summary_message,
    get_message_metadata,
    set_message_metadata,
    get_compaction_metadata,
    hash_content,
    CompactionError,
    # v2.1: Metadata helpers
    set_section_label,
    add_graph_edge,
    set_extraction_metadata,
    set_ingestion_metadata,
    is_message_ingested,
    get_extraction_chunk_ids,
    MessageSectionLabel,
    GraphEdgeType,
    ExtractionStrategy as ExtractionStrategyType,
    # Tool sequence conversion
    convert_tool_sequence_to_text,
    # v2.4: Message sorting
    sort_messages_by_weight,
)

# Initialize logger
logger = logging.getLogger(__name__)


# ============================================================================
# Summarization Prompt Template (v3.1)
# ============================================================================

# Central summarization prompt template used by all summarization functions
# Placeholders: {context_text}, {task_system_prompts_text}, {batch_number}, 
#               {messages_text}, {max_tokens}, {approximate_words}
SUMMARIZATION_PROMPT_TEMPLATE = """Summarize the following conversation messages concisely.

### Recent Context (for reference, DO NOT summarize):
{context_text}

### Task System Prompts (for reference, DO NOT summarize, use this to identify the task for which the summary is being created to create more relevant summary):
{task_system_prompts_text}

### Messages to Summarize (Batch {batch_number}):
{messages_text}

Create a summary that:
- Preserves key facts, decisions, and conclusions
- Maintains chronological flow  
- Uses 2nd person ("You discussed...")
- Is concise but complete
- Fits within {max_tokens} tokens (approximately {approximate_words} words)
- IMPORTANT: Your summary MUST NOT exceed {max_tokens} tokens

### Summary:
"""


# ============================================================================
# Helper Functions (v2.4)
# ============================================================================

def _add_section_messages_with_labels(
    compacted_messages: List[BaseMessage],
    messages: List[BaseMessage],
    section_label: MessageSectionLabel,
    full_history_ids: Optional[Set[str]],
) -> None:
    """
    Add messages to compacted list with section labels and graph edges.
    
    Helper to eliminate code duplication across strategies. Only adds metadata
    to messages from full_history (not old summaries with existing metadata).
    
    Args:
        compacted_messages: List to append messages to (modified in-place)
        messages: Messages to add
        section_label: Section label to apply (SYSTEM, MARKED, RECENT, etc.)
        full_history_ids: Set of full_history message IDs, or None for first compaction
    """
    for msg in messages:
        # Add metadata if message is from full_history (not an old summary):
        # - full_history_ids is None: first compaction or backward compat → add to all
        # - msg.id in full_history_ids: message from full_history → add metadata
        # - msg.id NOT in full_history_ids: old summary with existing metadata → skip
        if full_history_ids is None or (msg.id and msg.id in full_history_ids):
            set_section_label(msg, section_label)
            add_graph_edge(msg, GraphEdgeType.PASSTHROUGH)
        compacted_messages.append(msg)


def _get_full_history_ids(runtime_config: Optional[Dict]) -> Optional[Set[str]]:
    """
    Extract message IDs from full_history for filtering operations (v2.1).
    
    Used to identify which messages are from full_history (need fresh metadata)
    vs which are from previous compaction (already have metadata).
    
    Args:
        runtime_config: Runtime configuration dict
        
    Returns:
        None if full_history not provided (apply metadata to all messages)
        Set of message IDs if full_history provided (apply only to these)
    """
    if not runtime_config:
        return None
    full_history = runtime_config.get("full_history")
    if full_history is None:
        return None
    return {msg.id for msg in full_history if hasattr(msg, 'id') and msg.id}


class CompactionStrategyType(str, Enum):
    """Compaction strategy types."""
    SUMMARIZATION = "summarization"
    EXTRACTIVE = "extractive"
    HYBRID = "hybrid"
    NOOP = "noop"


class SummarizationMode(str, Enum):
    """Summarization modes."""
    FROM_SCRATCH = "from_scratch"
    CONTINUED = "continued"  # Hierarchical


class CompactionResult(BaseModel):
    """Result of prompt compaction operation."""
    compacted_messages: List[BaseMessage]
    summary_messages: List[BaseMessage] = Field(default_factory=list)
    extracted_messages: List[BaseMessage] = Field(default_factory=list)
    removed_message_ids: List[str] = Field(default_factory=list)
    token_usage: Dict[str, Any] = Field(default_factory=dict)
    cost: float = 0.0
    compression_ratio: float = 1.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SummarizationResult(BaseModel):
    """Result of summarization operation."""
    summaries: List[AIMessage]
    new_summary: Optional[AIMessage] = None
    token_usage: Dict[str, int] = Field(default_factory=dict)
    cost: float = 0.0


class ExtractionResult(BaseModel):
    """Result of extraction operation."""
    extracted_messages: List[BaseMessage]
    removed_messages: List[str]
    cost: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


async def check_and_handle_oversized_messages(
    messages: List[BaseMessage],
    max_single_message_pct: float,
    budget: ContextBudget,
    model_metadata: ModelMetadata,
    ext_context: Any,
    token_cache: Optional[MessageTokenCache] = None,
) -> List[BaseMessage]:
    """
    Detect and handle oversized messages that exceed context window limits.

    Uses MessageTokenCache for O(n) token counting instead of O(n) repeated counts.

    **Performance Optimization:**
    - Without cache: O(n) - counts each message individually
    - With cache: O(n) - counts once during cache creation, then O(1) lookups
    
    For 100 messages with 5 oversized:
    - Without cache: ~100 count operations (one per message check)
    - With cache: 100 counts once + 100 array lookups (faster for repeated access)

    Checks each message to see if it exceeds a percentage threshold of the context budget.
    If oversized, automatically summarizes the message using chunk-wise summarization.

    This prevents single messages from consuming too much context and causing overflow.

    Args:
        messages (List[BaseMessage]): Messages to check
        max_single_message_pct (float): Maximum percentage of budget a single message can use
            - Recommended: 0.6 (60%) for detection threshold
            - Messages exceeding this will be summarized
        budget (ContextBudget): Context budget for threshold calculation
        model_metadata (ModelMetadata): Model metadata for token counting and LLM calls
        ext_context (ExternalContextManager): External context for LLM access
        token_cache (Optional[MessageTokenCache]): Pre-computed token cache
            - If None, creates cache internally
            - If provided, reuses cache for efficiency

    Returns:
        List[BaseMessage]: Messages with oversized ones replaced by summaries
            - Same order as input
            - Oversized messages replaced with summary messages
            - Normal messages unchanged

    Example:
        ```python
        messages = [msg1, huge_msg (110K tokens), msg3]
        budget = ContextBudget(available_input_tokens=128000, ...)

        # Without cache
        processed = await check_and_handle_oversized_messages(
            messages=messages,
            max_single_message_pct=0.6,  # 60% threshold
            budget=budget,
            model_metadata=metadata,
            ext_context=ext_context,
        )

        # With cache (reuse across operations)
        cache = MessageTokenCache(messages, metadata)
        processed = await check_and_handle_oversized_messages(
            messages=messages,
            max_single_message_pct=0.6,
            budget=budget,
            model_metadata=metadata,
            ext_context=ext_context,
            token_cache=cache,
        )
        # Returns: [msg1, summary_msg (~20K tokens), msg3]
        ```

    Cross-references:
        - Called by: SummarizationStrategy.compact() before summarization
        - Called by: ExtractionStrategy.compact() before extraction
        - Calls: summarize_oversized_message() for chunking and summarization

    Notes:
        - Only processes messages exceeding threshold (default 60%)
        - Uses chunk-wise summarization with recursive handling
        - Preserves message order and metadata
        - Edge case: If summary still exceeds threshold, logs warning but continues
        - Performance: Cache enables O(1) lookups per message check
    """
    max_tokens_threshold = int(budget.available_input_tokens * max_single_message_pct)
    # v2.1 fix: Use smaller chunk size to account for prompt overhead when summarizing
    # Chunks should be small enough that chunk + prompt template fits in context
    chunk_size_for_splitting = int(budget.available_input_tokens * 0.4)  # 40% instead of 80%

    # Create cache if not provided (count tokens once for all messages)
    if token_cache is None:
        token_cache = MessageTokenCache(messages, model_metadata)

    processed_messages = []

    for i, msg in enumerate(messages):
        # Check message size using cache (O(1) lookup)
        msg_tokens = token_cache.get_message_count(i)

        if msg_tokens > max_tokens_threshold:
            # Message is oversized - summarize it
            try:
                summary = await summarize_oversized_message(
                    message=msg,
                    max_tokens_per_chunk=chunk_size_for_splitting,
                    model_metadata=model_metadata,
                    ext_context=ext_context,
                )
                processed_messages.append(summary)
            except Exception as e:
                # Log error and keep original message (fallback)
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(
                    f"Failed to summarize oversized message (ID: {msg.id}, "
                    f"tokens: {msg_tokens}): {e}. Keeping original message."
                )
                processed_messages.append(msg)
        else:
            # Normal message - keep as is
            processed_messages.append(msg)

    return processed_messages


class CompactionStrategy(ABC):
    """Abstract base class for compaction strategies."""

    def __init__(self, compaction_config: "PromptCompactionConfig"):
        self.compaction_config: "PromptCompactionConfig" = compaction_config

    @abstractmethod
    async def compact(
        self,
        sections: Dict[str, List[BaseMessage]],
        budget: ContextBudget,
        model_metadata: ModelMetadata,
        ext_context: Any,  # ExternalContextManager
        runtime_config: Optional[Dict] = None,
    ) -> CompactionResult:
        """
        Compact messages according to strategy (v2.1 with runtime_config).

        Args:
            sections: Classified message sections
            budget: Context budget
            model_metadata: Model metadata
            ext_context: External context manager
            runtime_config: Runtime configuration (thread_id, node_id, etc.)

        Returns:
            CompactionResult
        """
        pass

    async def _call_llm(
        self,
        prompt: str,
        model_metadata: ModelMetadata,
        ext_context: Any,
        max_tokens: int = 2000,
    ) -> Any:
        """
        Call LLM for summarization/extraction.

        Reuses existing LLM infrastructure instead of hardcoding models.

        Args:
            prompt: Prompt text
            model_metadata: Model metadata (determines which provider/model to use)
            ext_context: External context manager
            max_tokens: Maximum tokens for response

        Returns:
            LLM response with content, token_usage, and cost
        """
        from workflow_service.registry.nodes.llm.prompt_compaction.llm_utils import call_llm_for_compaction

        try:
            result = await call_llm_for_compaction(
                prompt=prompt,
                model_metadata=model_metadata,
                ext_context=ext_context,
                max_tokens=max_tokens,
                temperature=0.0,  # Deterministic for summaries
            )

            # Create response object matching expected interface
            class LLMResponse:
                def __init__(self, content, token_usage, cost):
                    self.content = content
                    self.token_usage = token_usage
                    self.cost = cost

            return LLMResponse(result["content"], result["token_usage"], result["cost"])

        except Exception as e:
            raise CompactionError(f"LLM call failed: {e}")


class NoOpStrategy(CompactionStrategy):
    """No-op strategy that passes through without compaction (v2.1)."""

    def __init__(self, compaction_config: Optional["PromptCompactionConfig"] = None):
        """Initialize NoOp strategy - compaction_config is optional since no compaction happens."""
        super().__init__(compaction_config)

    async def compact(
        self,
        sections: Dict[str, List[BaseMessage]],
        budget: ContextBudget,
        model_metadata: ModelMetadata,
        ext_context: Any,
        runtime_config: Optional[Dict] = None,
    ) -> CompactionResult:
        """Pass through without compaction - add section labels (v2.1 with runtime_config)."""
        # v2.1: Get full_history IDs for metadata filtering
        full_history_ids = _get_full_history_ids(runtime_config)

        all_messages = []

        # System
        _add_section_messages_with_labels(all_messages, sections["system"], MessageSectionLabel.SYSTEM, full_history_ids)

        # Summaries (already have labels from create_summary_message)
        all_messages.extend(sections["summaries"])

        # Historical (pass through as historical - includes old tool sequences in v2.5)
        _add_section_messages_with_labels(all_messages, sections["historical"], MessageSectionLabel.HISTORICAL, full_history_ids)

        # Marked
        _add_section_messages_with_labels(all_messages, sections["marked"], MessageSectionLabel.MARKED, full_history_ids)

        # Recent (includes latest tool sequences in v2.5)
        _add_section_messages_with_labels(all_messages, sections["recent"], MessageSectionLabel.RECENT, full_history_ids)

        return CompactionResult(
            compacted_messages=all_messages,
            compression_ratio=1.0,
            metadata={"strategy": "noop", "compaction_skipped": True},
        )


class SummarizationStrategy(CompactionStrategy):
    """
    LLM-based summarization strategy.

    Supports two modes:
    1. FROM_SCRATCH: Summarize all messages into one summary
    2. CONTINUED: Hierarchical summarization with summary chunks
    """

    def __init__(
        self,
        compaction_config: Optional["PromptCompactionConfig"] = None,
        mode: SummarizationMode = SummarizationMode.CONTINUED,
    ):
        """
        Initialize summarization strategy (v3.0 - linear batching).

        Args:
            compaction_config: Compaction configuration (optional for backward compatibility)
            mode: Summarization mode (FROM_SCRATCH or CONTINUED)
        """
        # Initialize parent class with compaction_config
        super().__init__(compaction_config)
        
        self.mode = mode

    async def compact(
        self,
        sections: Dict[str, List[BaseMessage]],
        budget: ContextBudget,
        model_metadata: ModelMetadata,
        ext_context: Any,
        runtime_config: Optional[Dict] = None,
    ) -> CompactionResult:
        """
        Compact using summarization (v2.1 with runtime_config).

        Args:
            sections: Classified message sections
            budget: Context budget
            model_metadata: Model metadata
            ext_context: External context manager
            runtime_config: Runtime configuration (thread_id, node_id, etc.)

        Returns:
            CompactionResult
        """
        # v2.1: Get full_history IDs for metadata filtering
        full_history_ids = _get_full_history_ids(runtime_config)

        # v2.5: Tools merged into historical/recent (no separate tool sections)
        historical = sections["historical"]
        recent = sections["recent"]
        existing_summaries = sections["summaries"]

        # Historical messages are ready for compaction (includes old tool sequences)
        messages_to_compact = historical

        if not messages_to_compact:
            # Nothing to summarize - add section labels (v2.1)
            compacted_messages = []

            # System
            _add_section_messages_with_labels(compacted_messages, sections["system"], MessageSectionLabel.SYSTEM, full_history_ids)

            # Summaries
            compacted_messages.extend(existing_summaries)

            # Marked
            _add_section_messages_with_labels(compacted_messages, sections["marked"], MessageSectionLabel.MARKED, full_history_ids)

            # Recent (includes latest tool sequences if present)
            _add_section_messages_with_labels(compacted_messages, recent, MessageSectionLabel.RECENT, full_history_ids)

            return CompactionResult(
                compacted_messages=compacted_messages,
                summary_messages=existing_summaries,
                compression_ratio=1.0,
                metadata={"strategy": "summarization", "reason": "no_historical_messages"},
            )

        # Extract full_history_indices from runtime_config for position weight tracking (v2.4)
        full_history_indices = runtime_config.get("full_history_indices", {}) if runtime_config else {}
        
        # Choose mode
        if self.mode == SummarizationMode.FROM_SCRATCH:
            # Get full_history for from_scratch mode to retrieve original messages
            full_history = runtime_config.get("full_history") if runtime_config else None
            
            result = await self._summarize_from_scratch(
                messages_to_summarize=messages_to_compact,
                existing_summaries=existing_summaries,
                full_history=full_history,
                context_messages=recent,
                task_system_prompts=sections["system"],
                budget=budget,
                model_metadata=model_metadata,
                ext_context=ext_context,
                full_history_indices=full_history_indices,
            )
            all_summaries = [result]
        else:  # CONTINUED
            result = await self._summarize_continued(
                historical_messages=messages_to_compact,
                existing_summaries=existing_summaries,
                context_messages=recent,
                task_system_prompts=sections["system"],
                budget=budget,
                model_metadata=model_metadata,
                ext_context=ext_context,
                full_history_indices=full_history_indices,
            )
            all_summaries = result.summaries

        # Assign position weights to summaries based on messages they summarize (v2.4)
        if full_history_indices:
            for summary in all_summaries:
                summarized_ids = get_message_metadata(summary, "summarized_message_ids", [])
                if summarized_ids:
                    # Calculate average weight of summarized messages
                    weights = [full_history_indices[msg_id] for msg_id in summarized_ids if msg_id in full_history_indices]
                    if weights:
                        avg_weight = sum(weights) / len(weights)
                        set_message_metadata(summary, "position_weight", avg_weight)

        # Combine all sections with labels (v2.1)
        compacted_messages = []

        # System
        _add_section_messages_with_labels(compacted_messages, sections["system"], MessageSectionLabel.SYSTEM, full_history_ids)

        # Summaries (already have labels from create_summary_message)
        compacted_messages.extend(all_summaries)

        # Marked
        _add_section_messages_with_labels(compacted_messages, sections["marked"], MessageSectionLabel.MARKED, full_history_ids)

        # Recent (includes latest tool sequences if present - v2.5)
        _add_section_messages_with_labels(compacted_messages, recent, MessageSectionLabel.RECENT, full_history_ids)

        # Assign position weights for chronological ordering (v2.5)
        # Use full_history_indices instead of original_indices
        if full_history_indices:
            from workflow_service.registry.nodes.llm.prompt_compaction.utils import assign_position_weights
            # For section messages from full_history
            system_in_history = [m for m in sections["system"] if m.id and m.id in full_history_indices]
            marked_in_history = [m for m in sections["marked"] if m.id and m.id in full_history_indices]
            recent_in_history = [m for m in recent if m.id and m.id in full_history_indices]
            
            assign_position_weights(system_in_history, full_history_indices)
            assign_position_weights(marked_in_history, full_history_indices)
            assign_position_weights(recent_in_history, full_history_indices)

        # Calculate compression ratio (v2.5: tools now in recent/historical)
        original_count = (
            len(sections["system"]) +
            len(existing_summaries) +
            len(sections["marked"]) +
            len(recent) +
            len(messages_to_compact)
        )
        compressed_count = len(compacted_messages)
        compression_ratio = original_count / compressed_count if compressed_count > 0 else 1.0

        # v2.4: Sort messages by position weight for chronological ordering
        from workflow_service.registry.nodes.llm.prompt_compaction.utils import sort_messages_by_weight
        compacted_messages = sort_messages_by_weight(compacted_messages)

        return CompactionResult(
            compacted_messages=compacted_messages,
            summary_messages=all_summaries,
            removed_message_ids=[msg.id for msg in messages_to_compact if msg.id is not None],
            token_usage=result.token_usage if isinstance(result, SummarizationResult) else {"total_tokens": 0},
            cost=result.cost if isinstance(result, SummarizationResult) else 0.0,
            compression_ratio=compression_ratio,
            metadata={
                "strategy": "summarization",
                "mode": self.mode.value,
                "num_summaries": len(all_summaries),
            },
        )

    async def _batch_and_summarize_messages(
        self,
        messages_to_summarize: List[BaseMessage],
        context_messages: List[BaseMessage],
        task_system_prompts: List[BaseMessage],
        budget: ContextBudget,
        model_metadata: ModelMetadata,
        ext_context: Any,
        full_history_indices: Optional[Dict[str, int]] = None,
        mode_label: str = "batching",
    ) -> List[AIMessage]:
        """
        Core batching and summarization logic shared by both from-scratch and continued modes (v3.1).
        
        This is the shared implementation that handles:
        1. Calculating overhead tokens
        2. Handling oversized messages
        3. Splitting into batches
        4. Parallel batch summarization
        
        Both _summarize_from_scratch and _summarize_continued use this, differing only
        in how they post-process the results.
        
        Args:
            messages_to_summarize: All messages to summarize (including existing summaries)
            context_messages: Recent messages for context
            task_system_prompts: System prompts for the task
            budget: Context budget
            model_metadata: Model metadata
            ext_context: External context
            full_history_indices: Fallback indices for messages without position_weight
            mode_label: Label for logging ("from-scratch" or "continued")
            
        Returns:
            List of summary AIMessages (one per batch)
        """
        import asyncio
        
        # Step 1: Calculate target output tokens (for overhead calculation)
        estimated_target_tokens = max(
            500,  # Minimum 500 tokens per summary
            min(2000, budget.summary_limit // max(1, len(messages_to_summarize) // 10))
        )
        
        # Step 2: Calculate overhead tokens using shared helper
        context_text, task_system_prompts_text, template_overhead_tokens = \
            self._calculate_summarization_overhead(
                context_messages=context_messages,
                task_system_prompts=task_system_prompts,
                model_metadata=model_metadata,
                estimated_max_output_tokens=estimated_target_tokens,
            )
        
        # Step 3: Batch messages based on model context limit
        max_batch_tokens = int(model_metadata.context_limit * 0.8)
        
        # Calculate max tokens per individual message (handle oversized messages)
        max_tokens_per_message = max_batch_tokens - template_overhead_tokens - estimated_target_tokens
        
        # Handle oversized messages BEFORE batching
        messages_to_summarize = await self._handle_oversized_messages(
            messages=messages_to_summarize,
            max_tokens_per_message=max_tokens_per_message,
            model_metadata=model_metadata,
            ext_context=ext_context,
        )
        
        batches = check_prompt_size_and_split(
            messages=messages_to_summarize,
            max_tokens=max_batch_tokens,
            model_metadata=model_metadata,
            overhead_tokens=template_overhead_tokens + estimated_target_tokens,
        )
        
        logger.info(
            f"[SUMMARIZATION] {mode_label}: {len(messages_to_summarize)} messages "
            f"→ {len(batches)} batches (max_batch_tokens={max_batch_tokens}, "
            f"overhead={template_overhead_tokens + estimated_target_tokens})"
        )
        
        # Step 4: Calculate target output tokens per batch
        target_tokens_per_batch = max(
            500,  # Minimum 500 tokens per summary
            budget.summary_limit // len(batches)
        )
        
        logger.info(
            f"[SUMMARIZATION] Target: {target_tokens_per_batch} tokens per summary "
            f"(budget: {budget.summary_limit}, batches: {len(batches)})"
        )
        
        # Step 5: Parallel summarize all batches
        tasks = []
        for batch_idx, batch in enumerate(batches):
            task = self._summarize_single_batch(
                messages=batch,
                context_messages=context_messages,
                task_system_prompts=task_system_prompts,
                model_metadata=model_metadata,
                ext_context=ext_context,
                max_output_tokens=target_tokens_per_batch,
                batch_idx=batch_idx,
                full_history_indices=full_history_indices,
                context_text=context_text,
                task_system_prompts_text=task_system_prompts_text,
            )
            tasks.append(task)
        
        # Execute all batches in parallel
        batch_summaries = await asyncio.gather(*tasks)
        
        return list(batch_summaries)

    async def _summarize_from_scratch(
        self,
        messages_to_summarize: List[BaseMessage],
        existing_summaries: List[AIMessage],
        full_history: Optional[List[BaseMessage]],
        context_messages: List[BaseMessage],
        task_system_prompts: List[BaseMessage],
        budget: ContextBudget,
        model_metadata: ModelMetadata,
        ext_context: Any,
        full_history_indices: Optional[Dict[str, int]] = None,
    ) -> AIMessage:
        """
        From-scratch summarization using linear batching (v3.1 - true from-scratch).
        
        Returns a SINGLE combined summary from all ORIGINAL messages (not summaries).
        
        KEY DIFFERENCE from _summarize_continued:
        - from_scratch: Retrieves ORIGINAL messages from full_history that were previously
          summarized, then combines them with new messages and summarizes everything fresh.
        - continued: Re-uses existing summaries (re-batches summaries with new messages).
        
        This is the true "from scratch" behavior - ignore existing summaries and
        re-summarize the original source messages.
        
        Args:
            messages_to_summarize: New messages to summarize
            existing_summaries: Previous summaries (used to find original message IDs)
            full_history: Full message history to retrieve original messages from
            context_messages: Recent messages for context
            task_system_prompts: System prompts for the task
            budget: Context budget
            model_metadata: Model metadata
            ext_context: External context
            full_history_indices: Fallback indices for messages without position_weight
            
        Returns:
            Single summary AIMessage (combined if multiple batches)
        """
        # FROM SCRATCH: Retrieve original messages that were previously summarized
        # instead of re-using the summaries themselves
        original_messages = []
        
        if existing_summaries and full_history:
            # Collect all message IDs that were previously summarized
            previously_summarized_ids = set()
            for summary in existing_summaries:
                summarized_ids = get_message_metadata(summary, "summarized_message_ids", [])
                previously_summarized_ids.update(summarized_ids)
            
            # Retrieve the original messages in chronological order (preserve full_history order)
            for msg in full_history:
                if hasattr(msg, 'id') and msg.id and msg.id in previously_summarized_ids:
                    original_messages.append(msg)
            
            logger.info(
                f"[FROM_SCRATCH] Reconstructed {len(original_messages)} original messages "
                f"from {len(existing_summaries)} summaries (covering {len(previously_summarized_ids)} message IDs)"
            )
        
        # Combine original messages + new messages for true from-scratch summarization
        all_messages_to_summarize = original_messages + list(messages_to_summarize)
        
        # Log the actual behavior
        if original_messages:
            logger.info(
                f"[FROM_SCRATCH] Summarizing {len(all_messages_to_summarize)} total messages: "
                f"{len(original_messages)} original (previously summarized) + "
                f"{len(messages_to_summarize)} new messages"
            )
        else:
            logger.info(
                f"[FROM_SCRATCH] No existing summaries or full_history unavailable. "
                f"Summarizing {len(all_messages_to_summarize)} new messages only"
            )
        
        # Use shared batching and summarization logic
        batch_summaries = await self._batch_and_summarize_messages(
            messages_to_summarize=all_messages_to_summarize,
            context_messages=context_messages,
            task_system_prompts=task_system_prompts,
            budget=budget,
            model_metadata=model_metadata,
            ext_context=ext_context,
            full_history_indices=full_history_indices,
            mode_label="From-scratch batching",
        )
        
        # If single batch, return it directly
        if len(batch_summaries) == 1:
            return batch_summaries[0]
        
        # Multiple batches: combine into ONE summary
        combined_text = "\n\n".join([
            f"[Part {i+1}]\n{s.content}" 
            for i, s in enumerate(batch_summaries)
        ])
        
        # Collect transitive IDs from all batch summaries
        all_summarized_ids = []
        for s in batch_summaries:
            batch_ids = get_message_metadata(s, "summarized_message_ids", [])
            all_summarized_ids.extend(batch_ids)
        
        # Aggregate costs
        total_cost = sum(get_message_metadata(s, "cost", 0.0) for s in batch_summaries)
        total_tokens = sum(
            get_message_metadata(s, "token_usage", {}).get("total_tokens", 0)
            for s in batch_summaries
        )
        
        # Create combined summary
        combined_summary = create_summary_message(
            content=combined_text,
            summarized_message_ids=all_summarized_ids,
            generation=0,
            token_usage={"total_tokens": total_tokens},
            cost=total_cost,
            compression_ratio=len(all_messages_to_summarize),
        )
        
        return combined_summary

    async def _handle_oversized_messages(
        self,
        messages: List[BaseMessage],
        max_tokens_per_message: int,
        model_metadata: ModelMetadata,
        ext_context: Any,
    ) -> List[BaseMessage]:
        """
        Check and handle oversized messages before batching (v3.1).
        
        Handles edge case where individual messages exceed the context limit.
        Such messages would cause batch splitting to fail, so we summarize them
        first before proceeding to normal batching.
        
        Args:
            messages: Messages to check for oversized content
            max_tokens_per_message: Maximum tokens allowed per message
                - Typically 80% of context limit minus overhead
            model_metadata: Model metadata for token counting and summarization
            ext_context: External context for LLM access
            
        Returns:
            List of messages where oversized ones have been replaced with summaries
        """
        processed_messages = []
        oversized_count = 0
        
        for msg in messages:
            msg_tokens = count_tokens_in_message(msg, model_metadata)
            
            if msg_tokens > max_tokens_per_message:
                # Message is too large - summarize it
                logger.warning(
                    f"[SUMMARIZATION] Found oversized message: {msg_tokens} tokens "
                    f"(limit: {max_tokens_per_message}). Summarizing..."
                )
                
                # Summarize the oversized message
                summarized_msg = await summarize_oversized_message(
                    message=msg,
                    max_tokens_per_chunk=max_tokens_per_message,
                    model_metadata=model_metadata,
                    ext_context=ext_context,
                )
                
                processed_messages.append(summarized_msg)
                oversized_count += 1
                
                logger.info(
                    f"[SUMMARIZATION] Oversized message summarized: "
                    f"{msg_tokens} → {count_tokens_in_message(summarized_msg, model_metadata)} tokens"
                )
            else:
                # Message is fine - keep as is
                processed_messages.append(msg)
        
        if oversized_count > 0:
            logger.info(
                f"[SUMMARIZATION] Handled {oversized_count} oversized messages "
                f"out of {len(messages)} total"
            )
        
        return processed_messages

    def _calculate_summarization_overhead(
        self,
        context_messages: List[BaseMessage],
        task_system_prompts: List[BaseMessage],
        model_metadata: ModelMetadata,
        estimated_max_output_tokens: int,
    ) -> tuple[str, str, int]:
        """
        Calculate overhead tokens for summarization prompt (v3.1).
        
        Shared helper for _summarize_from_scratch and _summarize_continued to avoid
        code duplication. Formats the prompt components and calculates accurate
        token overhead for batch splitting using the global SUMMARIZATION_PROMPT_TEMPLATE.
        
        Args:
            context_messages: Recent messages for context
            task_system_prompts: System prompts for the task
            model_metadata: Model metadata for token counting
            estimated_max_output_tokens: Estimated max output tokens per batch
            
        Returns:
            Tuple of (context_text, task_system_prompts_text, template_overhead_tokens)
        """
        # Format context and task system prompts once
        context_text = format_messages(context_messages[-3:]) if context_messages else "None"
        task_system_prompts_text = format_messages(task_system_prompts)
        
        # Count tokens in the prompt template components (excluding messages to summarize)
        context_tokens = count_tokens_in_text(context_text, model_metadata)
        task_prompts_tokens = count_tokens_in_text(task_system_prompts_text, model_metadata)
        
        # Calculate approximate word count for prompt instructions
        approximate_word_count = int(estimated_max_output_tokens * 0.75)
        
        # Format the global template with all components EXCEPT messages (use placeholder)
        # This gives us accurate overhead token count for batch splitting
        template_with_overhead = SUMMARIZATION_PROMPT_TEMPLATE.format(
            context_text=context_text,
            task_system_prompts_text=task_system_prompts_text,
            batch_number=1,
            messages_text="[MESSAGES_PLACEHOLDER]",
            max_tokens=estimated_max_output_tokens,
            approximate_words=approximate_word_count,
        )
        
        # Count template overhead tokens (everything except the actual messages)
        template_overhead_tokens = count_tokens_in_text(
            template_with_overhead.replace("[MESSAGES_PLACEHOLDER]", ""),
            model_metadata
        )
        
        logger.info(
            f"[SUMMARIZATION] Token overhead breakdown: "
            f"context={context_tokens}, task_prompts={task_prompts_tokens}, "
            f"template={template_overhead_tokens}, total_overhead={template_overhead_tokens}"
        )
        
        return context_text, task_system_prompts_text, template_overhead_tokens

    async def _summarize_continued(
        self,
        historical_messages: List[BaseMessage],
        existing_summaries: List[AIMessage],
        context_messages: List[BaseMessage],
        task_system_prompts: List[BaseMessage],
        budget: ContextBudget,
        model_metadata: ModelMetadata,
        ext_context: Any,
        full_history_indices: Optional[Dict[str, int]] = None,
    ) -> SummarizationResult:
        """
        Continued summarization - re-batches existing summaries with new messages (v3.1).
        
        Returns batch summaries as-is (does NOT combine them into one).
        
        KEY DIFFERENCE from _summarize_from_scratch:
        - from_scratch: Retrieves ORIGINAL messages from full_history and re-summarizes everything
        - continued: Re-uses existing summaries (re-batches summaries with new messages)
        
        This is "continued" behavior - existing summaries are treated as regular messages
        and re-batched together with new historical messages. More efficient but may
        compound summarization loss over multiple rounds.
        
        Args:
            historical_messages: New messages to summarize
            existing_summaries: Previous summaries to re-batch with new messages
            context_messages: Recent messages for context
            task_system_prompts: System prompts for the task
            budget: Context budget
            model_metadata: Model metadata
            ext_context: External context
            full_history_indices: Fallback indices for messages without position_weight
            
        Returns:
            SummarizationResult with list of batch summaries (not combined)
        """
        # CONTINUED: Combine existing summaries + new messages
        # Existing summaries are treated as regular messages (not expanded to originals)
        all_messages_to_summarize = list(existing_summaries) + list(historical_messages)
        
        logger.info(
            f"[CONTINUED] Summarizing {len(all_messages_to_summarize)} messages: "
            f"{len(existing_summaries)} existing summaries + "
            f"{len(historical_messages)} new messages"
        )
        
        # Use shared batching and summarization logic
        batch_summaries = await self._batch_and_summarize_messages(
            messages_to_summarize=all_messages_to_summarize,
            context_messages=context_messages,
            task_system_prompts=task_system_prompts,
            budget=budget,
            model_metadata=model_metadata,
            ext_context=ext_context,
            full_history_indices=full_history_indices,
            mode_label="Continued batching",
        )
        
        # Aggregate costs and return batch summaries as-is
        total_cost = sum(
            get_message_metadata(s, "cost", 0.0) for s in batch_summaries
        )
        total_tokens = sum(
            get_message_metadata(s, "token_usage", {}).get("total_tokens", 0)
            for s in batch_summaries
        )
        
        return SummarizationResult(
            summaries=list(batch_summaries),
            token_usage={"total_tokens": total_tokens},
            cost=total_cost,
        )

    async def _summarize_single_batch(
        self,
        messages: List[BaseMessage],
        context_messages: List[BaseMessage],
        task_system_prompts: List[BaseMessage],
        model_metadata: ModelMetadata,
        ext_context: Any,
        max_output_tokens: int,
        batch_idx: int = 0,
        full_history_indices: Optional[Dict[str, int]] = None,
        context_text: Optional[str] = None,
        task_system_prompts_text: Optional[str] = None,
    ) -> AIMessage:
        """
        Summarize a single batch of messages (v3.0 - linear batching).
        
        No hierarchical merging - just summarize the batch with specified token limit.
        This is the core method for the new linear batching strategy where:
        - Each batch is summarized independently
        - Target tokens per summary = budget / num_batches
        - No recursive merging needed
        
        v3.1 Enhancements:
        - Accepts pre-formatted context_text and task_system_prompts_text to avoid recomputation
        - Communicates max output tokens clearly to LLM in prompt (with word count estimate)
        - Logs token counts for debugging
        
        Args:
            messages: Messages in this batch to summarize
            context_messages: Recent context for reference (last 3 messages)
            task_system_prompts: System prompts for the task
            model_metadata: Model metadata for LLM call
            ext_context: External context manager
            max_output_tokens: Target tokens for this summary (budget / num_batches)
            batch_idx: Batch index for logging and metadata
            full_history_indices: Fallback indices for messages without position_weight
            context_text: Pre-formatted context text (v3.1 optimization)
            task_system_prompts_text: Pre-formatted task system prompts (v3.1 optimization)
        
        Returns:
            Summary AIMessage with metadata
        """
        from workflow_service.registry.nodes.llm.prompt_compaction.llm_utils import call_llm_for_compaction
        import logging
        logger = logging.getLogger(__name__)
        
        # Cap max_output_tokens to model's limit (v3.0 bugfix)
        # Prevents "max_tokens too large" API errors
        capped_max_tokens = min(max_output_tokens, model_metadata.output_token_limit)
        
        # Calculate approximate word count (1 token ≈ 0.75 words for English)
        approximate_word_count = int(capped_max_tokens * 0.75)
        
        # Log LLM call for verification (v3.0 debugging)
        logger.info(f"[SUMMARIZATION] Making LLM call: batch_idx={batch_idx}, "
                   f"max_tokens={capped_max_tokens}, num_messages={len(messages)}, "
                   f"model={model_metadata.model_name}")
        
        # Sort messages by position_weight for chronological order (v2.4)
        messages_sorted = sort_messages_by_weight(messages, full_history_indices=full_history_indices or {})
        
        # Build prompt components (v3.1: reuse pre-formatted text if provided)
        if context_text is None:
            context_text = format_messages(context_messages[-3:]) if context_messages else "None"
        if task_system_prompts_text is None:
            task_system_prompts_text = format_messages(task_system_prompts)
        
        messages_text = format_messages(messages_sorted)
        
        # Count tokens in messages being summarized (for logging/debugging)
        messages_tokens = count_tokens_in_text(messages_text, model_metadata)
        
        logger.info(
            f"[SUMMARIZATION] Batch {batch_idx + 1}: summarizing {len(messages_sorted)} messages "
            f"({messages_tokens} tokens) into max {capped_max_tokens} tokens"
        )
        
        # Build the summarization prompt using global template (v3.1)
        prompt = SUMMARIZATION_PROMPT_TEMPLATE.format(
            context_text=context_text,
            task_system_prompts_text=task_system_prompts_text,
            batch_number=batch_idx + 1,
            messages_text=messages_text,
            max_tokens=capped_max_tokens,
            approximate_words=approximate_word_count,
        )
        
        # Count total prompt tokens (for verification)
        prompt_tokens = count_tokens_in_text(prompt, model_metadata)
        logger.info(
            f"[SUMMARIZATION] Batch {batch_idx + 1}: total prompt tokens={prompt_tokens}, "
            f"available_context={model_metadata.context_limit}, "
            f"usage={prompt_tokens / model_metadata.context_limit * 100:.1f}%"
        )
        
        # Single LLM call (no recursive batching - batch already sized correctly)
        result = await call_llm_for_compaction(
            prompt=prompt,
            model_metadata=model_metadata,
            ext_context=ext_context,
            max_tokens=capped_max_tokens,
            temperature=0.0,
        )
        
        # Log actual output tokens (v3.1: verification)
        actual_output_tokens = result.get("token_usage", {}).get("completion_tokens", 0)
        logger.info(
            f"[SUMMARIZATION] Batch {batch_idx + 1}: requested={capped_max_tokens} tokens, "
            f"actual={actual_output_tokens} tokens, "
            f"utilization={actual_output_tokens / capped_max_tokens * 100:.1f}%"
        )
        
        # Collect ALL message IDs including transitive IDs from existing summaries (v2.4)
        all_summarized_ids = []
        for m in messages_sorted:  # Use sorted messages
            if hasattr(m, 'id') and m.id:
                # Check if this message has transitive IDs (it was a summary)
                existing_ids = get_message_metadata(m, "summarized_message_ids", [])
                if existing_ids:
                    # This was a summary - add its transitive IDs
                    all_summarized_ids.extend(existing_ids)
                else:
                    # Regular message - add its own ID
                    all_summarized_ids.append(m.id)
        
        # Create summary message (result is a dict)
        summary = create_summary_message(
            content=result["content"],
            summarized_message_ids=all_summarized_ids,  # Transitive IDs
            generation=0,  # All summaries same generation now (no hierarchy)
            token_usage=result["token_usage"],
            cost=result["cost"],
            compression_ratio=len(messages),
        )
        
        # Add batch metadata for tracking
        set_message_metadata(summary, "batch_idx", batch_idx)
        set_message_metadata(summary, "linear_batch", True)  # Mark as v3.0 linear batch
        
        # Add verification metadata (v3.0 debugging, v3.1: enhanced)
        set_message_metadata(summary, "llm_call_made", True)
        set_message_metadata(summary, "summarization_model", model_metadata.model_name)
        set_message_metadata(summary, "summarization_tokens_requested", capped_max_tokens)
        set_message_metadata(summary, "summarization_tokens_actual", actual_output_tokens)
        set_message_metadata(summary, "input_messages_tokens", messages_tokens)
        set_message_metadata(summary, "compression_achieved", messages_tokens / max(1, actual_output_tokens))
        
        return summary



class ExtractionStrategy(CompactionStrategy):
    """
    Vector-based extractive compaction (v2.1).

    Approach:
    1. JIT ingest messages if not already ingested
    2. Embed historical messages (or salient points)
    3. Embed recent messages as query
    4. Retrieve top-K most similar
    5. Construct extraction message using selected strategy
    6. Track duplicates and handle overflow

    v2.1 Features:
    - 3 construction strategies (dump, extract_full, llm_rewrite)
    - JIT ingestion
    - Duplicate tracking
    - Overflow handling
    """

    def __init__(
        self,
        compaction_config: Optional["PromptCompactionConfig"] = None,
        construction_strategy: ExtractionStrategyType = ExtractionStrategyType.EXTRACT_FULL,
        top_k: int = 5,
        similarity_threshold: float = 0.7,
        embedding_model: str = "text-embedding-3-small",
        allow_duplicate_chunks: bool = True,
        max_duplicate_appearances: int = 3,
        overflow_strategy: str = "remove_oldest",
        extract_salient_points: bool = False,
        use_reranking: bool = False,
        deduplication: bool = True,
        store_embeddings: bool = True,
        rewrite_model: Optional[str] = None,
        # v2.1: Message chunking for embeddings
        enable_message_chunking: bool = True,
        chunk_size_tokens: int = 1000,
        chunk_overlap_tokens: int = 50,
        chunk_strategy: str = "semantic_overlap",
        chunk_score_aggregation: str = "weighted_mean",
        expansion_mode: str = "hybrid",
        expansion_threshold: float = 0.85,
        expansion_budget_pct: float = 0.80,
        max_expansion_tokens: int = 16000,
        max_chunks_per_message: int = 10,
        chars_per_token: int = 3,
        max_embedding_chars: int = 21000,
    ):
        """
        Initialize extraction strategy (v2.1).
        
        Args:
            compaction_config: Compaction configuration (optional for backward compatibility)

        Args:
            construction_strategy: How to construct extraction messages (v2.1)
            top_k: Number of messages to extract
            similarity_threshold: Minimum similarity score
            embedding_model: OpenAI embedding model
            allow_duplicate_chunks: Allow re-extracting same chunks (v2.1)
            max_duplicate_appearances: Max times a chunk can appear (v2.1)
            overflow_strategy: How to handle overflow (v2.1)
            extract_salient_points: Extract key points from messages
            use_reranking: Use LLM for reranking
            deduplication: Deduplicate extracted messages
            store_embeddings: Store embeddings in Weaviate
            rewrite_model: Model for llm_rewrite strategy (v2.1)
            enable_message_chunking: (v2.1) Enable message chunking before embedding
            chunk_size_tokens: (v2.1) Max tokens per chunk (default: 1000)
            chunk_overlap_tokens: (v2.1) Token overlap between chunks (default: 50)
            chunk_strategy: (v2.1) Chunking strategy (semantic_overlap or fixed_token)
            chunk_score_aggregation: (v2.1) How to aggregate chunk scores (weighted_mean, max, mean)
            expansion_mode: (v2.1) Chunk expansion mode (hybrid, full_message, top_chunks_only)
            expansion_threshold: (v2.1) Min relevance score to expand chunk → full message (default: 0.85)
            expansion_budget_pct: (v2.1) % of extraction budget for expansion (default: 0.80 = 80%)
            max_expansion_tokens: (v2.1) Max tokens when expanding chunk → message (default: 16K)
            max_chunks_per_message: (v2.1) Max chunks per message in result
            chars_per_token: (v2.1) Character-to-token ratio for chunking (default: 3)
            max_embedding_chars: (v2.1) Max characters for embedding input (default: 21000)
        """
        # Initialize parent class with compaction_config
        super().__init__(compaction_config)
        
        self.construction_strategy = construction_strategy
        self.top_k = top_k
        self.similarity_threshold = similarity_threshold
        self.embedding_model = embedding_model
        self.allow_duplicate_chunks = allow_duplicate_chunks
        self.max_duplicate_appearances = max_duplicate_appearances
        self.overflow_strategy = overflow_strategy
        self.extract_salient_points = extract_salient_points
        self.use_reranking = use_reranking
        self.deduplication = deduplication
        self.store_embeddings = store_embeddings
        self.rewrite_model = rewrite_model
        # v2.1: Chunking parameters
        self.enable_message_chunking = enable_message_chunking
        self.chunk_size_tokens = chunk_size_tokens
        self.chunk_overlap_tokens = chunk_overlap_tokens
        self.chunk_strategy = chunk_strategy
        self.chunk_score_aggregation = chunk_score_aggregation
        self.expansion_mode = expansion_mode
        self.expansion_threshold = expansion_threshold
        self.expansion_budget_pct = expansion_budget_pct
        self.max_expansion_tokens = max_expansion_tokens
        self.max_chunks_per_message = max_chunks_per_message
        self.chars_per_token = chars_per_token
        self.max_embedding_chars = max_embedding_chars

    async def compact(
        self,
        sections: Dict[str, List[BaseMessage]],
        budget: ContextBudget,
        model_metadata: ModelMetadata,
        ext_context: Any,
        runtime_config: Optional[Dict] = None,
    ) -> CompactionResult:
        """
        Compact using extraction (v2.1 with runtime_config).

        Args:
            sections: Classified message sections
            budget: Context budget
            model_metadata: Model metadata
            ext_context: External context manager
            runtime_config: Runtime configuration (thread_id, node_id, etc.)

        Returns:
            CompactionResult
        """
        # v2.1: Get full_history IDs for metadata filtering
        full_history_ids = _get_full_history_ids(runtime_config)

        # Extract thread_id and node_id from runtime_config (v2.1)
        thread_id = None
        node_id = None
        if runtime_config:
            thread_id = runtime_config.get("thread_id")
            node_id = runtime_config.get("node_id")

        # v2.5: Tools merged into historical/recent (no separate tool sections)
        historical = sections["historical"]
        recent = sections["recent"]
        marked = sections["marked"]

        # Historical messages ready for extraction (includes old tool sequences)
        messages_to_extract_from = historical

        if not messages_to_extract_from:
            # Nothing to extract - add section labels (v2.1)
            compacted_messages = []

            # Add system with labels
            _add_section_messages_with_labels(compacted_messages, sections["system"], MessageSectionLabel.SYSTEM, full_history_ids)

            # Summaries already have labels
            compacted_messages.extend(sections["summaries"])

            # Add marked
            _add_section_messages_with_labels(compacted_messages, marked, MessageSectionLabel.MARKED, full_history_ids)

            # Add recent (includes latest tool sequences if present - v2.5)
            _add_section_messages_with_labels(compacted_messages, recent, MessageSectionLabel.RECENT, full_history_ids)

            return CompactionResult(
                compacted_messages=compacted_messages,
                compression_ratio=1.0,
                metadata={"strategy": "extraction", "reason": "no_historical_messages"},
            )

        # Extract relevant messages (v2.1: with JIT ingestion and deduplication)
        extraction_result = await self._extract_relevant_messages(
            historical_messages=messages_to_extract_from,
            recent_messages=recent,
            existing_marked=marked,
            existing_summaries=sections["summaries"],  # v2.1: For chunk deduplication
            model_metadata=model_metadata,
            ext_context=ext_context,
            thread_id=thread_id,
            node_id=node_id,
            budget=budget,
            runtime_config=runtime_config,
        )

        extracted = extraction_result.extracted_messages

        # Combine all sections with labels (v2.1)
        compacted_messages = []

        # Add system with labels
        _add_section_messages_with_labels(compacted_messages, sections["system"], MessageSectionLabel.SYSTEM, full_history_ids)

        # Summaries already have labels
        compacted_messages.extend(sections["summaries"])

        # Extracted messages already have labels from construction
        compacted_messages.extend(extracted)

        # Add marked
        _add_section_messages_with_labels(compacted_messages, marked, MessageSectionLabel.MARKED, full_history_ids)

        # Add recent (includes latest tool sequences if present - v2.5)
        _add_section_messages_with_labels(compacted_messages, recent, MessageSectionLabel.RECENT, full_history_ids)

        # Assign position weights for chronological ordering (v2.5)
        # Use full_history_indices instead of original_indices
        full_history_indices = runtime_config.get("full_history_indices", {}) if runtime_config else {}
        if full_history_indices:
            from workflow_service.registry.nodes.llm.prompt_compaction.utils import assign_position_weights
            # For section messages from full_history
            system_in_history = [m for m in sections["system"] if m.id and m.id in full_history_indices]
            marked_in_history = [m for m in marked if m.id and m.id in full_history_indices]
            recent_in_history = [m for m in recent if m.id and m.id in full_history_indices]
            
            assign_position_weights(system_in_history, full_history_indices)
            assign_position_weights(marked_in_history, full_history_indices)
            assign_position_weights(recent_in_history, full_history_indices)

        # Calculate compression ratio (v2.5: tools now in recent/historical)
        original_count = (
            len(sections["system"]) +
            len(sections["summaries"]) +
            len(marked) +
            len(recent) +
            len(messages_to_extract_from)
        )
        compressed_count = len(compacted_messages)
        compression_ratio = original_count / compressed_count if compressed_count > 0 else 1.0

        # v2.4: Sort messages by position weight with configurable extraction placement
        from workflow_service.registry.nodes.llm.prompt_compaction.utils import sort_messages_by_weight, ExtractionPlacement
        extraction_placement = (
            self.compaction_config.extraction.extraction_placement
            if self.compaction_config and hasattr(self.compaction_config, 'extraction')
            else ExtractionPlacement.CHRONOLOGICAL
        )
        compacted_messages = sort_messages_by_weight(compacted_messages, extraction_placement=extraction_placement)

        return CompactionResult(
            compacted_messages=compacted_messages,
            extracted_messages=extracted,
            removed_message_ids=extraction_result.removed_messages,
            cost=extraction_result.cost,
            compression_ratio=compression_ratio,
            metadata={
                "strategy": "extraction",
                "num_extracted": len(extracted),
                **extraction_result.metadata,
            },
        )

    async def _jit_ingest_messages(
        self,
        messages: List[BaseMessage],
        ext_context: Any,
        thread_id: Optional[str] = None,
        node_id: Optional[str] = None,
        section_label: str = "historical",
    ) -> List[BaseMessage]:
        """
        JIT (Just-In-Time) ingest messages to Weaviate if not already ingested (v2.1).

        v2.1 Features:
        - Message chunking for oversized messages (>6K tokens)
        - Re-ingestion prevention: Checks ingestion metadata to skip already-ingested messages
        - Iterative summarization support: Only ingests new messages from current turn

        Args:
            messages: Messages to ingest
            ext_context: External context manager
            thread_id: Workflow thread ID for Weaviate storage
            node_id: LLM node ID for Weaviate storage
            section_label: Section label for tracking (e.g., "historical", "marked_overflow")

        Returns:
            Messages with ingestion metadata (already-ingested messages unchanged)
        """
        from weaviate_client import ThreadMessageWeaviateClient
        from workflow_service.registry.nodes.llm.prompt_compaction.llm_utils import get_embeddings_batch
        from workflow_service.registry.nodes.llm.prompt_compaction.utils import (
            is_message_ingested,
            set_ingestion_metadata,
        )
        from workflow_service.registry.nodes.llm.prompt_compaction.token_utils import (
            chunk_message_for_embedding,
            count_tokens,
        )
        from datetime import datetime
        import logging

        logger = logging.getLogger(__name__)

        # Filter to only non-ingested messages (v2.1 re-ingestion prevention)
        to_ingest = [msg for msg in messages if not is_message_ingested(msg)]
        already_ingested = len(messages) - len(to_ingest)

        if already_ingested > 0:
            logger.info(
                f"Re-ingestion prevention: Skipping {already_ingested}/{len(messages)} "
                f"already-ingested messages (section: {section_label})"
            )

        if not to_ingest or not self.store_embeddings:
            return messages

        # Need thread_id and node_id for Weaviate storage
        if not thread_id or not node_id:
            logger.warning("Skipping Weaviate ingestion: thread_id or node_id not provided")
            # Mark as ingested without storage (fallback)
            for msg in to_ingest:
                chunk_ids = [f"chunk_{msg.id}"]
                set_ingestion_metadata(msg, chunk_ids=chunk_ids, section_label=section_label)
            return messages

        # Chunk messages and generate embeddings (v2.1)
        try:
            all_chunk_data = []
            all_chunk_texts = []

            # Step 1: Chunk all messages
            for sequence_no, msg in enumerate(to_ingest):
                # Chunk message if enabled and message is large
                if self.enable_message_chunking:
                    chunks = chunk_message_for_embedding(
                        message=msg,
                        chunk_size_tokens=self.chunk_size_tokens,
                        chunk_overlap_tokens=self.chunk_overlap_tokens,
                        chunk_strategy=self.chunk_strategy,
                        model_metadata=self.model_metadata if hasattr(self, 'model_metadata') else None,
                        chars_per_token=self.chars_per_token,
                    )
                else:
                    # No chunking - but still need to respect embedding model's token limit
                    # Use chunking with large chunk size to truncate oversized messages
                    MAX_EMBEDDING_TOKENS = 8000  # Safety margin below 8192
                    
                    # Reuse chunking logic to handle truncation
                    chunks = chunk_message_for_embedding(
                        message=msg,
                        chunk_size_tokens=MAX_EMBEDDING_TOKENS,
                        chunk_overlap_tokens=0,
                        chunk_strategy="fixed_token",
                        model_metadata=self.model_metadata if hasattr(self, 'model_metadata') else None,
                        chars_per_token=self.chars_per_token,
                    )
                    # Take only first chunk (truncates if needed)
                    chunks = [chunks[0]]

                # Store chunk data for processing
                for chunk_text, chunk_meta in chunks:
                    timestamp = int(datetime.now().timestamp())
                    chunk_id = f"chunk_{msg.id}_{chunk_meta['chunk_index']}_{timestamp}"

                    all_chunk_data.append((
                        msg,
                        sequence_no,
                        chunk_text,
                        chunk_id,
                        chunk_meta,
                    ))
                    all_chunk_texts.append(chunk_text)

            # Step 2: Batch embed all chunks
            if all_chunk_texts:
                embeddings = await get_embeddings_batch(
                    texts=all_chunk_texts,
                    embedding_model=self.embedding_model,
                    ext_context=ext_context
                )
            else:
                embeddings = []

            # Step 3: Store in Weaviate
            client = None
            try:
                client = ThreadMessageWeaviateClient()
                await client.connect()
                await client.setup_schema()

                # Track chunk_ids per message
                chunk_ids_by_message = {}

                for (msg, sequence_no, chunk_text, chunk_id, chunk_meta), embedding in zip(all_chunk_data, embeddings):
                    # Store chunk in Weaviate
                    await client.store_thread_message_chunk(
                        thread_id=thread_id,
                        node_id=node_id,
                        sequence_no=sequence_no,
                        message_id=msg.id,
                        embedding=embedding,
                        content=chunk_text[:1000],  # Limit content size
                        chunk_id=chunk_id,
                        chunk_index=chunk_meta.get("chunk_index"),
                        total_chunks=chunk_meta.get("total_chunks"),
                        overlaps_next=(chunk_meta.get("chunk_index", 0) < chunk_meta.get("total_chunks", 1) - 1),
                    )

                    # Track chunk_id for this message
                    if msg.id not in chunk_ids_by_message:
                        chunk_ids_by_message[msg.id] = []
                    chunk_ids_by_message[msg.id].append(chunk_id)

                # Step 4: Mark messages as ingested with their chunk_ids
                for msg in to_ingest:
                    chunk_ids = chunk_ids_by_message.get(msg.id, [f"chunk_{msg.id}"])
                    set_ingestion_metadata(msg, chunk_ids=chunk_ids, section_label=section_label)

                logger.info(f"Successfully ingested {len(to_ingest)} messages ({len(all_chunk_data)} chunks) to Weaviate")

            finally:
                if client:
                    await client.close()

        except Exception as e:
            # Log but don't fail - ingestion is optimization, not critical
            logger.warning(f"Weaviate ingestion failed (non-critical): {e}")
            # Mark as ingested anyway to avoid retry loops
            for msg in to_ingest:
                chunk_ids = [f"chunk_{msg.id}"]
                set_ingestion_metadata(msg, chunk_ids=chunk_ids, section_label=section_label)

        return messages

    def _validate_extraction_budget(
        self,
        extracted_messages: List[BaseMessage],
        budget: Optional[ContextBudget],
        model_metadata: ModelMetadata,
    ) -> List[BaseMessage]:
        """
        Validate extracted messages fit in budget (v2.1).

        Uses MessageTokenCache for O(n) token counting instead of O(n²).

        For EXTRACT_FULL strategy with hybrid expansion_mode, ensures full messages
        don't exceed expansion budget.

        Args:
            extracted_messages: Messages to validate
            budget: Context budget
            model_metadata: For token counting

        Returns:
            Validated messages (may be truncated if budget exceeded)
        """
        if not budget or self.construction_strategy != ExtractionStrategyType.EXTRACT_FULL:
            return extracted_messages

        # Calculate expansion budget (X% of summary limit)
        expansion_budget = int(budget.summary_limit * self.expansion_budget_pct)
        remaining_budget = expansion_budget

        # Create cache for extracted messages (count tokens once)
        token_cache = MessageTokenCache(extracted_messages, model_metadata)

        validated = []

        for i, msg in enumerate(extracted_messages):
            # Use cache for O(1) token lookup
            msg_tokens = token_cache.get_message_count(i)

            # Check if message exceeds max_expansion_tokens
            if msg_tokens > self.max_expansion_tokens:
                if self.expansion_mode == "hybrid":
                    # Try to fit in budget, but warn
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(
                        f"Message {msg.id} exceeds max_expansion_tokens "
                        f"({msg_tokens} > {self.max_expansion_tokens}), including anyway (hybrid mode)"
                    )
                    if msg_tokens <= remaining_budget:
                        validated.append(msg)
                        remaining_budget -= msg_tokens
                    else:
                        break  # Budget exhausted
                elif self.expansion_mode == "full_message":
                    # Always include (log warning)
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(
                        f"Message {msg.id} exceeds max_expansion_tokens "
                        f"({msg_tokens} > {self.max_expansion_tokens})"
                    )
                    if msg_tokens <= remaining_budget:
                        validated.append(msg)
                        remaining_budget -= msg_tokens
                    else:
                        break  # Budget exhausted
                else:  # top_chunks_only
                    # Skip large messages
                    continue
            else:
                # Normal size - include if fits
                if msg_tokens <= remaining_budget:
                    validated.append(msg)
                    remaining_budget -= msg_tokens
                else:
                    break  # Budget exhausted

        return validated

    def _check_and_handle_duplicates(
        self,
        chunk_id: str,
        existing_extractions: List[BaseMessage],
    ) -> List[BaseMessage]:
        """
        Check if chunk exceeds duplicate limit and handle overflow (v2.1).

        Args:
            chunk_id: ID of the chunk to check
            existing_extractions: List of existing extraction messages

        Returns:
            Updated list of extraction messages (with oldest removed if overflow)
        """
        from workflow_service.registry.nodes.llm.prompt_compaction.utils import (
            get_chunk_appearance_count,
            find_oldest_extraction_with_chunk,
        )

        if not self.allow_duplicate_chunks:
            # Duplicates not allowed, already filtered by deduplication
            return existing_extractions

        # Check appearance count
        appearance_count = get_chunk_appearance_count(existing_extractions, chunk_id)

        if appearance_count >= self.max_duplicate_appearances:
            # Overflow - need to handle
            if self.overflow_strategy == "remove_oldest":
                # Remove oldest extraction containing this chunk
                oldest = find_oldest_extraction_with_chunk(existing_extractions, chunk_id)
                if oldest:
                    # v2.1: Before removing, reattach its chunks to messages with them in deduplicated_chunk_ids
                    from workflow_service.registry.nodes.llm.prompt_compaction.utils import (
                        find_extractions_with_deduplicated_chunk,
                        move_deduplicated_to_chunk_ids,
                    )

                    removed_chunk_ids = get_extraction_chunk_ids(oldest)

                    # For each chunk in the removed extraction
                    for removed_chunk_id in removed_chunk_ids:
                        # Find extractions that have this chunk in deduplicated_chunk_ids
                        extractions_with_deduplicated = find_extractions_with_deduplicated_chunk(
                            existing_extractions, removed_chunk_id
                        )

                        # Reattach to those extractions
                        for extraction in extractions_with_deduplicated:
                            if extraction.id != oldest.id:  # Don't reattach to the one being removed
                                move_deduplicated_to_chunk_ids(extraction, [removed_chunk_id])

                    # Now remove the oldest extraction
                    existing_extractions = [msg for msg in existing_extractions if msg.id != oldest.id]

            elif self.overflow_strategy == "error":
                # Raise error
                raise CompactionError(
                    f"Chunk {chunk_id} exceeds max appearances ({self.max_duplicate_appearances})"
                )
            # "reduce_duplicates" or other strategies: allow but log warning
            # (Future enhancement)

        return existing_extractions

    async def _extract_relevant_messages(
        self,
        historical_messages: List[BaseMessage],
        recent_messages: List[BaseMessage],
        existing_marked: List[BaseMessage],
        existing_summaries: List[BaseMessage],
        model_metadata: ModelMetadata,
        ext_context: Any,
        thread_id: Optional[str] = None,
        node_id: Optional[str] = None,
        budget: Optional[ContextBudget] = None,
        runtime_config: Optional[Dict] = None,
    ) -> ExtractionResult:
        """
        Extract relevant messages using vector similarity (v2.1 with JIT ingestion and deduplication).

        v2.1: Includes oversized message handling, deduplication, and chunk reattachment.

        Args:
            existing_summaries: Existing extraction summaries for chunk deduplication
            historical_messages: Historical messages to extract from
            recent_messages: Recent messages to use as query
            existing_marked: Already marked/extracted messages
            model_metadata: Model metadata
            ext_context: External context manager
            thread_id: Workflow thread ID for Weaviate storage
            node_id: LLM node ID for Weaviate storage
            budget: Context budget for oversized detection (v2.1)

        Returns:
            ExtractionResult
        """
        # Import here to avoid circular dependencies
        from workflow_service.config.settings import settings
        from workflow_service.registry.nodes.llm.prompt_compaction.context_manager import (
            ContextBudgetConfig,
        )

        # v2.1: Check and handle oversized messages BEFORE extraction
        if budget:
            historical_messages = await check_and_handle_oversized_messages(
                messages=historical_messages,
                max_single_message_pct=0.6,
                budget=budget,
                model_metadata=model_metadata,
                ext_context=ext_context,
            )

        # Step 1: JIT Ingestion - ingest messages if not already ingested (v2.1)
        # Separate messages by original section for proper labeling
        historical_only = [
            msg for msg in historical_messages
            if not msg.additional_kwargs.get("originally_marked")
        ]
        marked_overflow = [
            msg for msg in historical_messages
            if msg.additional_kwargs.get("originally_marked")
        ]

        # Ingest with different section labels
        historical_only = await self._jit_ingest_messages(
            historical_only,
            ext_context,
            thread_id=thread_id,
            node_id=node_id,
            section_label="historical",
        )

        marked_overflow = await self._jit_ingest_messages(
            marked_overflow,
            ext_context,
            thread_id=thread_id,
            node_id=node_id,
            section_label="marked_overflow",
        )

        # Recombine for extraction
        historical_messages = historical_only + marked_overflow

        # Step 2: Deduplicate - filter out already extracted
        if self.deduplication:
            historical_messages = self._filter_already_extracted(
                messages=historical_messages,
                existing_marked=existing_marked,
            )

        if not historical_messages:
            return ExtractionResult(
                extracted_messages=[],
                removed_messages=[],
                cost=0.0,
            )

        # Step 2: Get embeddings using llm_utils (v2.1: with chunking support)
        from workflow_service.registry.nodes.llm.prompt_compaction.llm_utils import get_embeddings_batch
        from workflow_service.registry.nodes.llm.prompt_compaction.token_utils import chunk_message_for_embedding
        from collections import defaultdict

        # Chunk messages if enabled (v2.1: prevents embedding model overflow)
        if self.enable_message_chunking:
            # Chunk each message and track mapping
            message_chunks = []  # List[(msg, chunk_text, chunk_metadata)]
            for msg in historical_messages:
                chunks = chunk_message_for_embedding(
                    message=msg,
                    chunk_size_tokens=self.chunk_size_tokens,
                    chunk_overlap_tokens=self.chunk_overlap_tokens,
                    chunk_strategy=self.chunk_strategy,
                    model_metadata=model_metadata,
                    chars_per_token=self.chars_per_token,
                )
                for chunk_text, chunk_meta in chunks:
                    message_chunks.append((msg, chunk_text, chunk_meta))

            # Embed all chunks
            chunk_texts = [chunk_text for _, chunk_text, _ in message_chunks]
        else:
            # No chunking - but still need to respect embedding model's character limit
            # Use configured max_embedding_chars and chars_per_token from config
            message_chunks = []
            for msg in historical_messages:
                # Format message and truncate if needed
                msg_text = format_message_for_embedding(msg)
                
                # Truncate to configured char limit
                if len(msg_text) > self.max_embedding_chars:
                    msg_text = msg_text[:self.max_embedding_chars]
                
                # Estimate tokens using configured chars_per_token ratio
                estimated_tokens = len(msg_text) // self.chars_per_token
                
                message_chunks.append((msg, msg_text, {
                    "chunk_index": 0,
                    "total_chunks": 1,
                    "token_count": estimated_tokens,
                }))
            
            chunk_texts = [chunk_text for _, chunk_text, _ in message_chunks]

        # Filter out empty chunk texts (edge case: messages with no content)
        # Replace empty strings with single space to maintain index alignment
        chunk_texts = [text if text and text.strip() else " " for text in chunk_texts]

        # Embed recent messages as query
        query_text = format_messages_for_embedding(recent_messages)
        
        # Validate and truncate query text using configured max_embedding_chars
        if not query_text or not query_text.strip():
            # Edge case: no recent messages or all empty
            query_text = " "  # Use single space as fallback
        else:
            # Truncate by configured char limit
            if len(query_text) > self.max_embedding_chars:
                query_text = query_text[:self.max_embedding_chars]

        # Batch embed all texts (chunks + query)
        # All texts are validated: non-empty, character-limited
        all_texts = chunk_texts + [query_text]
        all_embeddings = await get_embeddings_batch(
            texts=all_texts,
            embedding_model=self.embedding_model,
            ext_context=ext_context,
        )

        # Split embeddings
        chunk_embeddings = all_embeddings[:-1]
        query_embedding = all_embeddings[-1]

        # Step 3: Compute similarities and aggregate by message (v2.1)
        message_similarities = defaultdict(list)

        for (msg, chunk_text, chunk_meta), chunk_embedding in zip(message_chunks, chunk_embeddings):
            score = cosine_similarity(query_embedding, chunk_embedding)
            message_similarities[msg.id].append((score, chunk_meta))

        # Aggregate chunk scores per message
        similarities = []
        for msg in historical_messages:
            chunk_scores = message_similarities[msg.id]

            if self.chunk_score_aggregation == "max":
                # Take highest score from any chunk (recommended for extraction)
                final_score = max(score for score, _ in chunk_scores)
            elif self.chunk_score_aggregation == "mean":
                # Average all chunk scores
                final_score = sum(score for score, _ in chunk_scores) / len(chunk_scores)
            elif self.chunk_score_aggregation == "weighted_mean":
                # Weight by chunk size
                total_weight = sum(meta["token_count"] for _, meta in chunk_scores)
                final_score = sum(
                    score * meta["token_count"] / total_weight
                    for score, meta in chunk_scores
                )
            else:
                # Default to max
                final_score = max(score for score, _ in chunk_scores)

            if final_score >= self.similarity_threshold:
                similarities.append((msg, final_score))

        # Step 4: Sort by relevance and take top-K
        similarities.sort(key=lambda x: x[1], reverse=True)
        top_k = similarities[:self.top_k]

        # Step 4.5: Collect existing chunk_ids for deduplication (v2.1)
        existing_chunk_ids = set()
        existing_extraction_by_chunk = {}  # chunk_id → extraction_message_id

        for summary in existing_summaries:
            # Get chunk_ids from extraction metadata
            chunk_ids = get_extraction_chunk_ids(summary)
            for chunk_id in chunk_ids:
                existing_chunk_ids.add(chunk_id)
                existing_extraction_by_chunk[chunk_id] = summary.id

        # Step 5: Construct extraction messages based on strategy (v2.1)
        cost = 0.0

        if self.construction_strategy == ExtractionStrategyType.DUMP:
            # Strategy (a): Dump all chunks as-is
            chunks_data = [
                {"id": f"chunk_{msg.id}", "text": format_message_for_embedding(msg),
                 "source_msg_id": msg.id, "score": score}
                for msg, score in top_k
            ]

            # v2.1: Separate new chunks vs duplicates
            new_chunk_ids = []
            new_chunks_text = []
            new_source_ids = []
            new_scores = []
            deduplicated_chunk_ids = []

            for chunk in chunks_data:
                if chunk["id"] in existing_chunk_ids:
                    # Skip duplicate, but track it
                    deduplicated_chunk_ids.append(chunk["id"])
                else:
                    # New chunk, include it
                    new_chunk_ids.append(chunk["id"])
                    new_chunks_text.append(chunk["text"])
                    new_source_ids.append(chunk["source_msg_id"])
                    new_scores.append(chunk["score"])

            extraction_msg = create_extraction_summary_message(
                content="\n\n---\n\n".join(new_chunks_text) if new_chunks_text else "[No new relevant content]",
                source_message_ids=new_source_ids,
                chunk_ids=new_chunk_ids,
                strategy=ExtractionStrategyType.DUMP,
                relevance_scores=new_scores,
            )

            # Add deduplicated chunks to metadata
            if deduplicated_chunk_ids:
                set_extraction_metadata(
                    extraction_msg,
                    chunk_ids=new_chunk_ids,
                    strategy=ExtractionStrategyType.DUMP,
                    relevance_scores=new_scores,
                    deduplicated_chunk_ids=deduplicated_chunk_ids,
                )

            extracted_messages = [extraction_msg]

        elif self.construction_strategy == ExtractionStrategyType.EXTRACT_FULL:
            # Strategy (b): Extract full messages (current behavior, now with metadata and deduplication)
            # v2.1: Strip tool calls from extracted messages to preserve pairing integrity
            extracted_messages = []
            for msg, score in top_k:
                chunk_id = f"chunk_{msg.id}"

                # v2.1: Check if this message's chunk is a duplicate
                if chunk_id in existing_chunk_ids:
                    # Skip this message, but could track it if needed
                    # (In EXTRACT_FULL, we typically wouldn't create an extraction with deduplicated_only)
                    continue

                # v2.1: Create extracted message WITHOUT tool calls to preserve pairing
                from workflow_service.registry.nodes.llm.prompt_compaction.utils import create_extracted_message
                extracted_msg = create_extracted_message(
                    original_message=msg,
                    relevance_score=score,
                    extraction_id=chunk_id,
                )
                
                # Add section labels and metadata
                set_section_label(extracted_msg, MessageSectionLabel.EXTRACTED_SUMMARY)
                add_graph_edge(extracted_msg, GraphEdgeType.EXTRACTION, full_history_msg_ids=[msg.id])
                set_extraction_metadata(
                    extracted_msg,
                    chunk_ids=[chunk_id],
                    strategy=ExtractionStrategyType.EXTRACT_FULL,
                    relevance_scores=[score]
                )
                extracted_messages.append(extracted_msg)

        elif self.construction_strategy == ExtractionStrategyType.LLM_REWRITE:
            # Strategy (c): LLM rewrite (v2.1: uses universal wrapper for overflow handling)
            from workflow_service.registry.nodes.llm.prompt_compaction.token_utils import (
                call_llm_with_batch_splitting,
            )
            from langchain_core.messages import HumanMessage

            # Format chunks with relevance scores
            chunks_text = "\n\n".join([
                f"[Chunk {i+1}, Relevance: {score:.2f}]\n{format_message_for_embedding(msg)}"
                for i, (msg, score) in enumerate(top_k)
            ])

            # Wrap as message for overflow handling
            chunks_message = HumanMessage(content=chunks_text)

            # Format recent messages for context
            recent_context = format_messages_for_embedding(recent_messages)

            prompt_template = """Given these relevant message chunks from conversation history:

{messages}

And the latest user query:
{recent_context}

Write a concise summary of the relevant context that would be useful for responding to the query. Focus on the most important information and preserve specific details."""

            # Create budget if not provided
            assert budget is not None, "Budget is required for LLM rewrite"

            result = await call_llm_with_batch_splitting(
                messages=[chunks_message],
                prompt_template=prompt_template,
                model_metadata=model_metadata,
                ext_context=ext_context,
                budget=budget,
                template_kwargs={"recent_context": recent_context},
                max_output_tokens=1000,
            )

            # v2.1: Separate new chunks vs duplicates
            new_chunk_ids = []
            new_source_ids = []
            new_scores = []
            deduplicated_chunk_ids = []

            for msg, score in top_k:
                chunk_id = f"chunk_{msg.id}"
                if chunk_id in existing_chunk_ids:
                    deduplicated_chunk_ids.append(chunk_id)
                else:
                    new_chunk_ids.append(chunk_id)
                    new_source_ids.append(msg.id)
                    new_scores.append(score)

            extraction_msg = create_extraction_summary_message(
                content=result["content"],
                source_message_ids=new_source_ids,
                chunk_ids=new_chunk_ids,
                strategy=ExtractionStrategyType.LLM_REWRITE,
                relevance_scores=new_scores,
                token_usage=result["token_usage"],
                cost=result["cost"],
            )

            # Add deduplicated chunks to metadata
            if deduplicated_chunk_ids:
                set_extraction_metadata(
                    extraction_msg,
                    chunk_ids=new_chunk_ids,
                    strategy=ExtractionStrategyType.LLM_REWRITE,
                    relevance_scores=new_scores,
                    deduplicated_chunk_ids=deduplicated_chunk_ids,
                )

            extracted_messages = [extraction_msg]
            cost += result["cost"]

        else:
            # Fallback to extract_full
            extracted_messages = []
            for msg, score in top_k:
                set_section_label(msg, MessageSectionLabel.EXTRACTED_SUMMARY)
                add_graph_edge(msg, GraphEdgeType.EXTRACTION, full_history_msg_ids=[msg.id])
                extracted_messages.append(msg)

        # v2.1: Validate extraction budget (ensure messages fit)
        extracted_messages = self._validate_extraction_budget(
            extracted_messages=extracted_messages,
            budget=budget,
            model_metadata=model_metadata,
        )

        # Calculate embedding cost
        num_embeddings = len(historical_messages) + 1  # Candidates + query
        # text-embedding-3-small pricing: $0.02 per 1M tokens (~1 token per char)
        estimated_chars = sum(len(str(msg.content)) for msg in historical_messages) + len(query_text)
        embedding_cost = (estimated_chars / 1_000_000) * 0.02

        # Total cost includes embeddings + any LLM rewrite cost
        total_cost = embedding_cost + cost

        # Assign position weights to extracted messages (v2.4)
        # Use full_history_indices instead of original_indices (v3.1: consistency with SummarizationStrategy)
        full_history_indices = runtime_config.get("full_history_indices", {}) if runtime_config else {}
        
        if full_history_indices:
            if self.construction_strategy == ExtractionStrategyType.EXTRACT_FULL:
                # Each extracted message gets weight from its original message
                for extracted_msg in extracted_messages:
                    # Find the original message ID from metadata
                    if hasattr(extracted_msg, 'id') and extracted_msg.id in full_history_indices:
                        set_message_metadata(extracted_msg, "position_weight", float(full_history_indices[extracted_msg.id]))
            else:  # DUMP or LLM_REWRITE
                # Single message gets average weight of all extracted source messages
                source_ids = []
                for msg, score in top_k:
                    if hasattr(msg, 'id') and msg.id:
                        source_ids.append(msg.id)
                
                weights = [full_history_indices[msg_id] for msg_id in source_ids if msg_id in full_history_indices]
                if weights and extracted_messages:
                    avg_weight = sum(weights) / len(weights)
                    for extracted_msg in extracted_messages:
                        set_message_metadata(extracted_msg, "position_weight", avg_weight)

        # Add verification metadata for extraction (v3.1: enhanced tracking, matching SummarizationStrategy pattern)
        for extracted_msg in extracted_messages:
            set_message_metadata(extracted_msg, "extraction_performed", True)
            set_message_metadata(extracted_msg, "embedding_model", self.embedding_model)
            set_message_metadata(extracted_msg, "construction_strategy", self.construction_strategy.value if isinstance(self.construction_strategy, ExtractionStrategyType) else str(self.construction_strategy))
            set_message_metadata(extracted_msg, "num_candidates", len(historical_messages))
            # avg_relevance_score is added to result metadata below
            # Additional extraction-specific metadata already set by set_extraction_metadata()

        return ExtractionResult(
            extracted_messages=extracted_messages,
            removed_messages=[m.id for m in historical_messages if m.id and m.id not in [em.id for em in extracted_messages]],
            cost=total_cost,
            metadata={
                "num_candidates": len(historical_messages),
                "num_extracted": len(extracted_messages),
                "avg_relevance_score": sum(score for _, score in top_k) / len(top_k) if top_k else 0,
                "construction_strategy": self.construction_strategy.value if isinstance(self.construction_strategy, ExtractionStrategyType) else str(self.construction_strategy),
            },
        )

    def _filter_already_extracted(
        self,
        messages: List[BaseMessage],
        existing_marked: List[BaseMessage],
    ) -> List[BaseMessage]:
        """
        Deduplicate: skip messages already extracted.

        Args:
            messages: Messages to filter
            existing_marked: Already marked/extracted messages

        Returns:
            Filtered messages
        """
        # Build set of extracted IDs
        extracted_ids = set()
        for msg in existing_marked:
            if get_message_metadata(msg, "extracted"):
                extracted_ids.add(msg.id)

        # Build set of extracted content hashes
        extracted_hashes = set()
        for msg in existing_marked:
            if get_message_metadata(msg, "extracted"):
                content_hash = hash_content(str(msg.content))
                extracted_hashes.add(content_hash)

        # Filter
        filtered = []
        for msg in messages:
            # Skip if ID already extracted
            if msg.id in extracted_ids:
                continue

            # Skip if content already extracted
            content_hash = hash_content(str(msg.content))
            if content_hash in extracted_hashes:
                continue

            filtered.append(msg)

        return filtered


class HybridStrategy(CompactionStrategy):
    """
    Hybrid compaction: extraction + summarization (v2.1).

    Process:
    1. Reserve extraction budget (5% default)
    2. Extract relevant messages (fast, preserves key facts)
    3. Summarize remaining historical messages (compress bulk)
    4. Combine: System + Summaries + Extracted + Marked + Latest Tools + Recent

    v2.1 Features:
    - Reserved extraction budget (configurable, default 5%)
    - Extraction extracts into marked section
    - Remaining budget goes to summarization

    Benefits:
    - Fast retrieval of relevant facts (extraction)
    - Compressed context from non-relevant history (summarization)
    - Best quality for complex workflows
    """

    def __init__(
        self,
        compaction_config: Optional["PromptCompactionConfig"] = None,
        extraction_pct: float = 0.05,
        extraction_strategy: ExtractionStrategy = None,
        summarization_strategy: SummarizationStrategy = None,
    ):
        """
        Initialize hybrid strategy.
        
        Args:
            compaction_config: Compaction configuration (optional for backward compatibility)
            extraction_pct: Percentage of budget for extraction
            extraction_strategy: Custom extraction strategy
            summarization_strategy: Custom summarization strategy
        """
        # Initialize parent class with compaction_config
        super().__init__(compaction_config)
        
        self.extraction_pct = extraction_pct
        self.extraction_strategy = extraction_strategy or ExtractionStrategy(compaction_config=compaction_config)
        self.summarization_strategy = summarization_strategy or SummarizationStrategy(compaction_config=compaction_config)

    async def compact(
        self,
        sections: Dict[str, List[BaseMessage]],
        budget: ContextBudget,
        model_metadata: ModelMetadata,
        ext_context: Any,
        runtime_config: Optional[Dict] = None,
    ) -> CompactionResult:
        """
        Hybrid compaction with reserved extraction budget (v2.1 with runtime_config).

        Args:
            sections: Classified message sections
            budget: Context budget
            model_metadata: Model metadata
            ext_context: External context manager
            runtime_config: Runtime configuration (thread_id, node_id, etc.)

        Returns:
            CompactionResult
        """
        # v2.1: Get full_history IDs for metadata filtering
        full_history_ids = _get_full_history_ids(runtime_config)

        historical = sections["historical"]
        recent = sections["recent"]
        marked = sections["marked"]
        existing_summaries = sections["summaries"]

        # Historical messages ready for hybrid compaction (v2.5: includes old tool sequences)
        messages_to_compact = historical

        if not messages_to_compact:
            # Nothing to compact - add section labels (v2.1)
            compacted_messages = []

            # System
            _add_section_messages_with_labels(compacted_messages, sections["system"], MessageSectionLabel.SYSTEM, full_history_ids)

            # Summaries (already have labels)
            compacted_messages.extend(existing_summaries)

            # Marked
            _add_section_messages_with_labels(compacted_messages, marked, MessageSectionLabel.MARKED, full_history_ids)

            # Recent (includes latest tool sequences if present - v2.5)
            _add_section_messages_with_labels(compacted_messages, recent, MessageSectionLabel.RECENT, full_history_ids)

            return CompactionResult(
                compacted_messages=compacted_messages,
                summary_messages=existing_summaries,
                compression_ratio=1.0,
                metadata={"strategy": "hybrid", "reason": "no_historical_messages"},
            )

        # v2.5: Calculate budgets
        # Sacred sections (always included - recent now includes latest tool sequences)
        sacred_tokens = count_tokens(
            sections["system"] + sections["marked"] + recent,
            model_metadata
        )
        available = budget.available_input_tokens - sacred_tokens

        # Reserve extraction budget (e.g., 5% of available)
        extraction_budget = int(available * self.extraction_pct)
        summarization_budget = available - extraction_budget

        # Extract thread_id and node_id from runtime_config (v2.1)
        thread_id = None
        node_id = None
        if runtime_config:
            thread_id = runtime_config.get("thread_id")
            node_id = runtime_config.get("node_id")

        # Phase 1: Extract relevant messages with extraction budget (v2.1: with JIT ingestion and deduplication)
        extraction_result = await self.extraction_strategy._extract_relevant_messages(
            historical_messages=messages_to_compact,
            recent_messages=recent,
            existing_marked=marked,
            existing_summaries=existing_summaries,  # v2.1: For chunk deduplication
            model_metadata=model_metadata,
            ext_context=ext_context,
            thread_id=thread_id,
            node_id=node_id,
            budget=budget,
            runtime_config=runtime_config,
        )

        extracted = extraction_result.extracted_messages

        # Phase 2: Summarize remaining historical messages with summarization budget
        remaining_historical = [
            msg for msg in messages_to_compact
            if msg.id not in [e.id for e in extracted]
        ]

        if remaining_historical:
            # Create temporary sections for summarization (v2.5: tools merged into recent/historical)
            sum_sections = {
                "system": sections["system"],
                "summaries": existing_summaries,
                "marked": marked,
                "recent": recent,
                "historical": remaining_historical,
            }

            summarization_result = await self.summarization_strategy.compact(
                sections=sum_sections,
                budget=budget,
                model_metadata=model_metadata,
                ext_context=ext_context,
                runtime_config=runtime_config,
            )

            all_summaries = summarization_result.summary_messages
            cost_summarization = summarization_result.cost
            token_usage_sum = summarization_result.token_usage
        else:
            all_summaries = existing_summaries
            cost_summarization = 0.0
            token_usage_sum = {}

        # Combine all sections with labels (v2.1)
        # Order: System + Summaries + Extracted + Marked + Latest Tools + Recent
        compacted_messages = []

        # System
        for msg in sections["system"]:
            if full_history_ids is None or (msg.id and msg.id in full_history_ids):
                set_section_label(msg, MessageSectionLabel.SYSTEM)
                add_graph_edge(msg, GraphEdgeType.PASSTHROUGH)
            compacted_messages.append(msg)

        # Summaries (from summarization, already have labels)
        for msg in all_summaries:
            compacted_messages.append(msg)

        # Extractions (from extraction, already have labels)
        for msg in extracted:
            compacted_messages.append(msg)

        # Marked
        _add_section_messages_with_labels(compacted_messages, marked, MessageSectionLabel.MARKED, full_history_ids)

        # Recent (includes latest tool sequences if present - v2.5)
        _add_section_messages_with_labels(compacted_messages, recent, MessageSectionLabel.RECENT, full_history_ids)

        # Assign position weights for chronological ordering (v2.5)
        # Use full_history_indices instead of original_indices
        full_history_indices = runtime_config.get("full_history_indices", {}) if runtime_config else {}
        if full_history_indices:
            from workflow_service.registry.nodes.llm.prompt_compaction.utils import assign_position_weights
            # For section messages from full_history
            system_in_history = [m for m in sections["system"] if m.id and m.id in full_history_indices]
            marked_in_history = [m for m in marked if m.id and m.id in full_history_indices]
            recent_in_history = [m for m in recent if m.id and m.id in full_history_indices]
            
            assign_position_weights(system_in_history, full_history_indices)
            assign_position_weights(marked_in_history, full_history_indices)
            assign_position_weights(recent_in_history, full_history_indices)

        # Calculate total cost
        total_cost = extraction_result.cost + cost_summarization

        # Calculate compression ratio (v2.5: tools now in recent/historical)
        original_count = (
            len(sections["system"]) +
            len(existing_summaries) +
            len(marked) +
            len(recent) +
            len(messages_to_compact)
        )
        compressed_count = len(compacted_messages)
        compression_ratio = original_count / compressed_count if compressed_count > 0 else 1.0

        # v2.4: Sort messages by position weight with configurable extraction placement
        from workflow_service.registry.nodes.llm.prompt_compaction.utils import sort_messages_by_weight, ExtractionPlacement
        extraction_placement = (
            self.compaction_config.hybrid.extraction_config.extraction_placement
            if self.compaction_config and hasattr(self.compaction_config, 'hybrid')
            else ExtractionPlacement.CHRONOLOGICAL
        )
        compacted_messages = sort_messages_by_weight(compacted_messages, extraction_placement=extraction_placement)

        return CompactionResult(
            compacted_messages=compacted_messages,
            summary_messages=all_summaries,
            extracted_messages=extracted,
            removed_message_ids=[
                m.id for m in messages_to_compact
                if m.id is not None and m.id not in [e.id for e in extracted if e.id is not None]
            ],
            token_usage={
                "extraction": extraction_result.metadata.get("num_candidates", 0),
                "summarization": token_usage_sum,
            },
            cost=total_cost,
            compression_ratio=compression_ratio,
            metadata={
                "strategy": "hybrid",
                "extraction_pct": self.extraction_pct,
                "extraction_budget": extraction_budget,
                "summarization_budget": summarization_budget,
                "num_extracted": len(extracted),
                "num_summarized": len(remaining_historical),
                "extraction_cost": extraction_result.cost,
                "summarization_cost": cost_summarization,
            },
        )
