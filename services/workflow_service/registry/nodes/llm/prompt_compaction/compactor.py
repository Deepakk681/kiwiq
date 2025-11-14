"""
# docs/design_docs/workflow_service_docs/technical_design/prompt_compaction/CODE_FLOW_DIAGRAMS.md

Main orchestrator for prompt compaction (v2.5).

The PromptCompactor class coordinates the entire compaction process:
1. Calculate context budget with dynamic reallocation
2. Check if compaction is needed
3. Classify messages into sections (tools merged into recent/historical)
4. Enforce budget constraints with dynamic adjustment
5. Compact historical section only (recent always preserved)
6. Handle billing

v2.0 Features:
- Adaptive compression ratios (target 50% post-compaction)
- Dynamic budget reallocation (recent > summaries > marked)
- Single-call merge optimization (30% cost savings)

v2.1 Features:
- Bipartite graph metadata tracking (full history ↔ summarized messages)
- Dual message history (full + summarized)
- Enhanced extraction with 3 construction strategies (dump, extract_full, llm_rewrite)
- Hybrid strategy with reserved extraction budget (5% default)
- Atomic tool call sequence preservation
- Configurable model provider with tenacity retries
- Message section labels and ingestion metadata

v2.5 Features:
- Single-round compaction (tools handled via dynamic budget adjustment)
- Latest tools merged into recent section (never compressed)
- Old tools merged into historical section (compressed normally)
- Dynamic budget expansion for recent when containing latest tool sequence
"""

from typing import List, Dict, Any, Optional, Tuple, TYPE_CHECKING
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field, model_validator
from langchain_core.messages import AIMessage, BaseMessage

from workflow_service.registry.nodes.llm.config import ModelMetadata, LLMModelProvider
from workflow_service.registry.nodes.llm.prompt_compaction.context_manager import (
    ContextBudget,
    ContextBudgetConfig,
    MessageClassifier,
    BudgetEnforcer,
)
from workflow_service.registry.nodes.llm.prompt_compaction.strategies import (
    CompactionStrategy,
    CompactionStrategyType,
    SummarizationStrategy,
    SummarizationMode,
    ExtractionStrategy,
    HybridStrategy,
    NoOpStrategy,
    CompactionResult,
)
from workflow_service.registry.nodes.llm.prompt_compaction.token_utils import (
    count_tokens,
    MessageTokenCache,
)
from workflow_service.registry.nodes.llm.prompt_compaction.billing import (
    bill_summarization,
    bill_extraction,
    bill_hybrid,
)
from workflow_service.registry.nodes.llm.prompt_compaction.utils import (
    get_message_metadata,
    CompactionError,
    ExtractionStrategy as ExtractionStrategyType,
    ExtractionPlacement,
)

if TYPE_CHECKING:
    from kiwi_app.workflow_app.schemas import WorkflowRunJobCreate
    from workflow_service.registry.nodes.llm.llm_node import LLMModelConfig

class SummarizationConfig(BaseModel):
    """
    Summarization strategy configuration (v2.0).

    Controls how conversation history is summarized using LLM calls.
    Two modes available: FROM_SCRATCH (complete re-summarization) or
    CONTINUED (incremental summaries merged hierarchically).
    """

    mode: SummarizationMode = Field(
        default=SummarizationMode.CONTINUED,
        description=(
            "Summarization mode: FROM_SCRATCH (summarize all historical messages fresh) "
            "or CONTINUED (merge existing summaries with new messages for incremental updates). "
            "CONTINUED is more efficient for long conversations."
        ),
    )

    model: Optional[str] = Field(
        default=None,
        description=(
            "LLM model to use for summarization. If None, uses the main LLM model from llm_config. "
            "Example: 'gpt-4o-mini' for fast, cheap summarization."
        ),
    )

    provider: Optional[LLMModelProvider] = Field(
        default=None,
        description=(
            "LLM provider for summarization. If None, uses default_provider from llm_config. "
            "Options: openai, anthropic."
        ),
    )

    max_summary_tokens: int = Field(
        default=2000,
        description=(
            "Maximum tokens per summary message. Controls verbosity of generated summaries. "
            "Larger values preserve more detail but consume more context."
        ),
    )

    preserve_tool_calls: bool = Field(
        default=True,
        description=(
            "Whether to preserve tool call/response sequences atomically when summarizing. "
            "If True, tool sequences are kept together or excluded entirely (never split)."
        ),
    )

    preserve_structured_outputs: bool = Field(
        default=True,
        description=(
            "Whether to preserve structured outputs (JSON, code blocks) when summarizing. "
            "If True, structured content is extracted and included verbatim in summaries."
        ),
    )


class ExtractionConfig(BaseModel):
    """
    Extractive strategy configuration (v2.1).

    Controls how relevant historical messages are extracted using semantic search.
    Extracts top-K most relevant chunks based on recent message context,
    optionally rewriting them for coherence.
    """

    # Message construction strategy
    construction_strategy: ExtractionStrategyType = Field(
        default=ExtractionStrategyType.EXTRACT_FULL,
        description=(
            "How to construct messages from extracted chunks: "
            "DUMP (concatenate chunks as-is), "
            "EXTRACT_FULL (expand chunks to include full original messages), "
            "LLM_REWRITE (summarize/rewrite chunks for coherence). "
            "EXTRACT_FULL preserves exact context, LLM_REWRITE is more compact."
        ),
    )

    # Retrieval settings
    top_k: int = Field(
        default=5,
        gt=0,
        description=(
            "Number of most relevant message chunks to extract. "
            "Higher values provide more context but consume more tokens. "
            "Typical: 3-10 depending on context budget."
        ),
    )

    similarity_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description=(
            "Minimum cosine similarity score (0.0-1.0) for extracted chunks. "
            "Chunks below this threshold are excluded even if within top_k. "
            "Higher values (0.8+) = stricter relevance, lower values (0.5-0.7) = broader context."
        ),
    )

    embedding_model: str = Field(
        default="text-embedding-3-small",
        description=(
            "OpenAI embedding model for semantic search. "
            "Options: text-embedding-3-small (fast, cheap), text-embedding-3-large (higher quality). "
            "Used to embed messages and query for similarity matching."
        ),
    )

    # Duplicate handling (v2.1)
    allow_duplicate_chunks: bool = Field(
        default=True,
        description=(
            "Whether to allow extracting the same chunk multiple times across compaction cycles. "
            "If True, highly relevant chunks can reappear; if False, enforces uniqueness."
        ),
    )

    max_duplicate_appearances: int = Field(
        default=3,
        description=(
            "Maximum times a chunk can be extracted across cycles (requires allow_duplicate_chunks=True). "
            "Prevents infinite re-extraction of the same content."
        ),
    )

    # Overflow handling (v2.1)
    overflow_strategy: str = Field(
        default="remove_oldest",
        description=(
            "How to handle when extracted chunks exceed budget: "
            "remove_oldest (drop oldest extractions first), "
            "reduce_duplicates (remove duplicate chunks first), "
            "error (raise CompactionError). "
            "remove_oldest is safest default."
        ),
    )

    # Advanced options
    extract_salient_points: bool = Field(
        default=False,
        description=(
            "Whether to extract salient points from chunks using LLM. "
            "Experimental feature - adds LLM call overhead."
        ),
    )

    salient_point_model: Optional[str] = Field(
        default=None,
        description=(
            "LLM model for salient point extraction. If None, uses main model. "
            "Only used if extract_salient_points=True."
        ),
    )

    use_reranking: bool = Field(
        default=False,
        description=(
            "Whether to rerank extracted chunks using a reranking model. "
            "Improves relevance but adds latency. Experimental feature."
        ),
    )

    reranking_model: Optional[str] = Field(
        default=None,
        description=(
            "Model for reranking chunks. If None, uses default reranker. "
            "Only used if use_reranking=True."
        ),
    )

    deduplication: bool = Field(
        default=True,
        description=(
            "Whether to deduplicate extracted chunks within a single compaction cycle. "
            "If True, identical chunks are merged before returning."
        ),
    )

    # Weaviate storage settings
    store_embeddings: bool = Field(
        default=True,
        description=(
            "Whether to store message embeddings in Weaviate ThreadMessageChunks collection. "
            "Required for extraction to work. Set False only for testing or if using external vector DB."
        ),
    )

    cleanup_old_threads_days: Optional[int] = Field(
        default=None,
        description=(
            "Auto-cleanup thread embeddings older than N days. If None, no cleanup. "
            "Recommended: 30-90 days to prevent Weaviate bloat."
        ),
    )

    # LLM rewrite settings (for llm_rewrite strategy)
    rewrite_model: Optional[str] = Field(
        default=None,
        description=(
            "LLM model for rewriting extracted chunks (construction_strategy=LLM_REWRITE). "
            "If None, uses main model. Example: 'gpt-4o-mini' for fast rewriting."
        ),
    )

    # Message chunking for embeddings (v2.1)
    enable_message_chunking: bool = Field(
        default=True,
        description=(
            "Whether to chunk oversized messages before embedding. "
            "Required when messages exceed embedding model's 8K token limit. "
            "Chunks are embedded separately and similarity scores are aggregated per message."
        ),
    )

    chunk_size_tokens: int = Field(
        default=1000,
        gt=0,
        description=(
            "Maximum tokens per message chunk for embedding. "
            "Should be below embedding model's limit (8192 for text-embedding-3-small). "
            "Recommended: 6000-7000 tokens to leave room for formatting overhead."
        ),
    )

    chunk_overlap_tokens: int = Field(
        default=50,
        ge=0,
        description=(
            "Number of tokens to overlap between consecutive chunks. "
            "Helps preserve context across chunk boundaries. "
            "Typical: 10-20% of chunk_size_tokens (e.g., 200 for 6000 chunk_size)."
        ),
    )

    chunk_strategy: str = Field(
        default="semantic_overlap",
        description=(
            "Chunking strategy: 'semantic_overlap' (split by paragraphs/sentences with overlap), "
            "'fixed_token' (fixed-size token chunks with overlap). "
            "semantic_overlap preserves meaning better."
        ),
    )

    # Character-to-token estimation (v2.1)
    chars_per_token: int = Field(
        default=3,
        gt=0,
        description=(
            "Conservative character-to-token ratio for chunking. "
            "3 chars = 1 token is safe for structured data (JSON/tool calls with special chars). "
            "4 chars = 1 token for plain text. Lower is safer but creates smaller chunks."
        ),
    )

    max_embedding_chars: int = Field(
        default=21000,
        gt=0,
        description=(
            "Maximum characters for embedding input (text-embedding-3-small has 8K token limit). "
            "Conservative: 21000 chars = ~7000 tokens with 3:1 ratio (well under 8K limit). "
            "This prevents embedding API errors for oversized inputs."
        ),
    )

    chunk_score_aggregation: str = Field(
        default="max",
        description=(
            "How to aggregate similarity scores from multiple chunks of same message: "
            "'max' (take highest score from any chunk - recommended for extraction), "
            "'mean' (average all chunk scores), "
            "'weighted_mean' (weight by chunk size)."
        ),
    )

    # Chunk expansion settings (v2.1)
    expansion_mode: str = Field(
        default="full_message",
        description=(
            "How to expand retrieved chunks to messages: "
            "'full_message' (expand chunk to full original message - preferred for context), "
            "'top_chunks_only' (use retrieved chunks directly - more compact), "
            "'hybrid' (full message if fits in budget, else top chunks)."
        ),
    )

    max_expansion_tokens: int = Field(
        default=50000,
        gt=0,
        description=(
            "Maximum tokens when expanding chunk → full message. "
            "If full message exceeds this, falls back to using top chunks only. "
            "Set to model's context limit or lower for safety."
        ),
    )

    max_chunks_per_message: int = Field(
        default=10,
        gt=0,
        description=(
            "Maximum number of chunks to include per message in final extracted result. "
            "Limits redundancy when multiple chunks from same message are retrieved. "
            "Typical: 5-10 chunks."
        ),
    )

    # Placement strategy (v2.4)
    extraction_placement: ExtractionPlacement = Field(
        default=ExtractionPlacement.CHRONOLOGICAL,
        description=(
            "How to place extracted messages in final compacted output: "
            "'chronological' (sort by position weight - default), "
            "'end' (place all extractions at the end), "
            "'before_last_turn' (place before last human/AI/tool message)."
        ),
    )


class HybridConfig(BaseModel):
    """
    Hybrid strategy configuration (v2.1).

    Combines extraction (retrieve relevant chunks) with summarization (compress remaining history).
    Provides best balance between preserving important context and managing token budget.
    """

    extraction_config: ExtractionConfig = Field(
        default_factory=ExtractionConfig,
        description=(
            "Configuration for extraction phase. Controls semantic search, top-K, "
            "construction strategy, and Weaviate storage."
        ),
    )

    summarization_config: SummarizationConfig = Field(
        default_factory=SummarizationConfig,
        description=(
            "Configuration for summarization phase. Controls LLM summarization mode, "
            "model selection, and hierarchical merging."
        ),
    )

    # Order: extract first, then summarize (based on design preference)
    extraction_first: bool = Field(
        default=True,
        description=(
            "Whether to extract relevant chunks before summarizing remaining messages. "
            "If True: extract → then summarize rest. If False: summarize → then extract from summaries. "
            "True is recommended to preserve exact relevant content."
        ),
    )

    # Extraction budget allocation (v2.1)
    extraction_pct: float = Field(
        default=0.05,
        ge=0.0,
        le=1.0,
        description=(
            "Percentage of summary budget allocated for extracted chunks (0.0-1.0). "
            "Example: 0.05 = 5% of summary_max_pct budget. Must not exceed summary_max_pct. "
            "Higher values allow more extracted context but less summarized history."
        ),
    )


class AdaptiveCompressionConfig(BaseModel):
    """
    Adaptive compression configuration (v2.0).

    Controls how aggressively messages are compressed based on context usage.
    Adaptive mode automatically calculates compression ratio to hit target_context_pct.
    """

    # Compression mode
    mode: str = Field(
        default="adaptive",
        description=(
            "Compression mode: adaptive (calculate ratio dynamically), "
            "fixed_ratio (use fixed_compression_ratio), or auto_bandwidth (use remaining budget). "
            "Adaptive is recommended for most use cases."
        ),
    )

    # Fixed ratio mode
    fixed_compression_ratio: Optional[float] = Field(
        default=None,
        description=(
            "Fixed compression ratio for fixed_ratio mode. Example: 10.0 = compress 10 messages into 1. "
            "Ignored if mode != 'fixed_ratio'."
        ),
    )

    # Adaptive mode bounds
    min_compression_ratio: float = Field(
        default=5.0,
        description=(
            "Minimum compression ratio (most aggressive). Never compress more than 1:min. "
            "Example: 5.0 = at most 5 messages compressed into 1 summary. "
            "Prevents over-compression that loses too much detail."
        ),
    )

    max_compression_ratio: float = Field(
        default=100.0,
        description=(
            "Maximum compression ratio (least aggressive). Never compress less than 1:max. "
            "Example: 100.0 = at least 100 messages needed for compression. "
            "Prevents under-compression that wastes LLM calls."
        ),
    )

    # Target context post-compaction
    target_context_pct: float = Field(
        default=50.0,
        description=(
            "Target context usage percentage after compaction (0-100). "
            "Adaptive mode compresses to hit this target. Example: 50.0 = aim for 50% usage. "
            "Lower values = more aggressive compaction."
        ),
    )

    # Auto bandwidth mode
    use_summary_bandwidth: bool = Field(
        default=False,
        description=(
            "Whether to calculate compression from remaining summary budget (auto_bandwidth mode). "
            "If True, uses available summary space to determine compression. "
            "Experimental - use with caution."
        ),
    )


class DynamicReallocationConfig(BaseModel):
    """
    Dynamic budget reallocation configuration (v2.0).

    Allows unused budget from one section (e.g., summaries) to be reallocated
    to other sections (e.g., recent messages) based on priority order.
    """

    enabled: bool = Field(
        default=True,
        description=(
            "Whether to enable dynamic budget reallocation. "
            "If True, unused tokens from lower-priority sections are redistributed. "
            "Recommended to keep True for flexible budget management."
        ),
    )

    reallocation_priority: List[str] = Field(
        default=["recent", "summaries", "marked"],
        description=(
            "Priority order for reallocating unused budget (highest to lowest priority). "
            "Example: ['recent', 'summaries', 'marked'] means recent gets first dibs on unused tokens. "
            "Determines which sections expand when others under-utilize their budgets. "
            "v2.5: Tools merged into recent/historical sections (no separate tool section)."
        ),
    )


class CompactionLLMConfig(BaseModel):
    """
    Configuration for LLM calls during compaction (v2.1).

    Controls which LLM provider and model to use for summarization, extraction,
    and other compaction-related LLM calls. Includes retry configuration.
    """

    # Default model for compaction LLM calls
    default_provider: str = Field(
        default="openai",
        description=(
            "Default LLM provider for compaction calls. Options: 'openai', 'anthropic'. "
            "Used for summarization unless overridden in strategy config. "
            "OpenAI is recommended for speed and cost (gpt-4o-mini)."
        ),
    )

    default_model: str = Field(
        default="gpt-4o-mini",
        description=(
            "Default LLM model for compaction calls. "
            "Recommended: 'gpt-4o-mini' (fast, cheap: $0.15/1M input), "
            "'gpt-4o' (better quality: $2.50/1M input), "
            "'claude-sonnet-4' (best quality: $3.00/1M input)."
        ),
    )

    # Provider-specific overrides
    perplexity_fallback_provider: str = Field(
        default="anthropic",
        description=(
            "Fallback provider when main LLM is Perplexity (which doesn't support compaction). "
            "Options: 'openai', 'anthropic'. Used to ensure compaction works with any main model."
        ),
    )

    perplexity_fallback_model: str = Field(
        default="claude-sonnet-4-5",
        description=(
            "Fallback model when main LLM is Perplexity. "
            "Used with perplexity_fallback_provider for compaction calls."
        ),
    )

    # Retry configuration (tenacity)
    max_retries: int = Field(
        default=3,
        description=(
            "Maximum number of retry attempts for failed LLM calls during compaction. "
            "Retries use exponential backoff. Recommended: 3-5 for production reliability."
        ),
    )

    retry_wait_exponential_multiplier: int = Field(
        default=1,
        description=(
            "Exponential backoff multiplier in seconds for retries. "
            "Wait time = multiplier * (2 ^ retry_number). Example: 1 = [1s, 2s, 4s, 8s]."
        ),
    )

    retry_wait_exponential_max: int = Field(
        default=10,
        description=(
            "Maximum wait time in seconds between retries. "
            "Caps exponential backoff to prevent excessive delays. Example: 10 = max 10s wait."
        ),
    )


class PromptCompactionConfig(BaseModel):
    """
    Main prompt compaction configuration (v2.1).

    Top-level configuration for the entire prompt compaction system.
    Controls strategy selection, budget allocation, and all sub-configurations.

    Quick start:
        config = PromptCompactionConfig()  # Use defaults (HYBRID strategy)

    Custom example:
        config = PromptCompactionConfig(
            strategy=CompactionStrategyType.SUMMARIZATION,
            context_budget=ContextBudgetConfig(
                summary_max_pct=0.30,
                recent_messages_min_pct=0.30,
            ),
        )
    """
    debug: bool = Field(
        default=False,
        description=(
            "Whether to enable debug mode. "
            "If True, will log detailed information about the compaction process. "
            "Disabled by default."
        ),
    )

    # Enable/disable
    enabled: bool = Field(
        default=True,
        description=(
            "Master switch to enable/disable prompt compaction. "
            "If False, all compaction is skipped and messages pass through unchanged. "
            "Enabled by default (v2.0+)."
        ),
    )

    # Billing control
    enable_billing: bool = Field(
        default=True,
        description=(
            "Enable/disable billing for compaction operations. "
            "If False, billing calls are skipped (useful for testing). "
            "Enabled by default in production."
        ),
    )

    # Strategy selection
    strategy: CompactionStrategyType = Field(
        default=CompactionStrategyType.SUMMARIZATION,
        description=(
            "Compaction strategy: SUMMARIZATION (LLM-based), EXTRACTIVE (semantic search), "
            "HYBRID (extract + summarize), or NOOP (disabled). "
            "HYBRID is recommended for balanced context preservation and compression (v2.0+ default)."
        ),
    )

    # Context budget allocation
    context_budget: ContextBudgetConfig = Field(
        default_factory=ContextBudgetConfig,
        description=(
            "Token budget allocation across message sections (system, summaries, marked, recent). "
            "Controls how available input tokens are distributed. "
            "See ContextBudgetConfig for field details."
        ),
    )

    # v2.0: Adaptive compression (always enabled)
    adaptive_compression: AdaptiveCompressionConfig = Field(
        default_factory=AdaptiveCompressionConfig,
        description=(
            "Adaptive compression configuration (v2.0). "
            "Controls how aggressively to compress based on context usage. "
            "Always enabled in v2.0+."
        ),
    )

    # v2.0: Dynamic reallocation (always enabled)
    dynamic_reallocation: DynamicReallocationConfig = Field(
        default_factory=DynamicReallocationConfig,
        description=(
            "Dynamic budget reallocation configuration (v2.0). "
            "Allows unused budget from one section to be redistributed to others. "
            "Always enabled in v2.0+."
        ),
    )

    # v2.1: LLM configuration for compaction calls
    llm_config: CompactionLLMConfig = Field(
        default_factory=CompactionLLMConfig,
        description=(
            "LLM provider and model configuration for compaction calls (v2.1). "
            "Controls which LLM is used for summarization and other compaction operations. "
            "Default: gpt-4o-mini for speed and cost."
        ),
    )

    # Strategy-specific configs
    summarization: SummarizationConfig = Field(
        default_factory=SummarizationConfig,
        description=(
            "Summarization strategy configuration. "
            "Used when strategy=SUMMARIZATION or strategy=HYBRID. "
            "Controls LLM summarization mode, model, and merging."
        ),
    )

    extraction: ExtractionConfig = Field(
        default_factory=ExtractionConfig,
        description=(
            "Extraction strategy configuration (v2.1). "
            "Used when strategy=EXTRACTIVE or strategy=HYBRID. "
            "Controls semantic search, top-K, construction, and Weaviate storage."
        ),
    )

    hybrid: HybridConfig = Field(
        default_factory=HybridConfig,
        description=(
            "Hybrid strategy configuration (v2.1). "
            "Used when strategy=HYBRID. "
            "Combines extraction and summarization for balanced context management."
        ),
    )

    # Message preservation
    recent_message_count: int = Field(
        default=10,
        description=(
            "Number of most recent messages to always preserve without compaction. "
            "These messages are never summarized or extracted, ensuring latest context is intact. "
            "v2.0: Increased from 5 to 10 for better recent context."
        ),
    )

    preserve_tool_call_sequences: bool = Field(
        default=True,
        description=(
            "Whether to preserve tool call sequences atomically (never split). "
            "If True, tool sequences [user → assistant tool call → tool result → user follow-up] "
            "are kept together or excluded entirely. v2.1: Atomic preservation."
        ),
    )

    @model_validator(mode='after')
    def validate_extraction_limits(self):
        """Validate that extraction_pct doesn't exceed summary_max_pct (v2.1)."""
        if self.strategy in [CompactionStrategyType.HYBRID, CompactionStrategyType.EXTRACTIVE]:
            extraction_pct = self.hybrid.extraction_pct if self.strategy == CompactionStrategyType.HYBRID else 0.05
            summary_max_pct = self.context_budget.summary_max_pct

            if extraction_pct > summary_max_pct:
                raise ValueError(
                    f"extraction_pct ({extraction_pct}) cannot exceed "
                    f"summary_max_pct ({summary_max_pct})"
                )
        return self


class PromptCompactor:
    """
    Main orchestrator for prompt compaction (v2.5).

    Coordinates the entire compaction process from classification to billing.

    v2.5 architecture:
    - Single-round compaction (tools handled via dynamic budget adjustment)
    - Latest tools merged into recent section (always preserved)
    - Old tools merged into historical section (compressed normally)
    - Dynamic budget reallocation
    - Adaptive compression ratios
    - Single-call merge optimization
    """

    def __init__(
        self,
        config: PromptCompactionConfig,
        model_metadata: ModelMetadata,
        llm_node_llm_config: "LLMModelConfig",
        node_id: str,
        node_name: str,
        logger = None,
    ):
        """
        Initialize prompt compactor.

        Args:
            config: Compaction configuration
            model_metadata: Model metadata for token counting
            llm_node_llm_config: LLM configuration for LLM Node
            node_id: Node ID
            node_name: Node name
            logger: Logger instance
        """
        self.config = config
        self.model_metadata = model_metadata
        self.llm_node_llm_config = llm_node_llm_config
        self.node_id = node_id
        self.node_name = node_name
        self.logger = logger
        # Initialize components
        self.classifier = MessageClassifier(
            preserve_tool_call_sequences=config.preserve_tool_call_sequences
        )
        self.budget_enforcer = BudgetEnforcer()

        # Initialize strategy
        self.strategy = self._create_strategy()

        # v2.1: Pending chunk re-attachment tracking for deduplication
        # Persists chunk IDs from removed extraction messages across compaction cycles
        # Key: chunk_id, Value: {original_extraction_id, removed_at, original_message_type}
        self.pending_chunk_reattachment: Dict[str, Dict[str, Any]] = {}

    def _create_strategy(self) -> CompactionStrategy:
        """
        Create compaction strategy based on configuration.

        Returns:
            CompactionStrategy instance
        """
        kwargs = {
            "compaction_config": self.config,
            "logger": self.logger,
        }
        if not self.config.enabled:
            return NoOpStrategy(**kwargs)
        if self.config.strategy == CompactionStrategyType.SUMMARIZATION:
            return SummarizationStrategy(
                mode=self.config.summarization.mode,
                **kwargs,
            )
        elif self.config.strategy == CompactionStrategyType.EXTRACTIVE:
            return ExtractionStrategy(
                top_k=self.config.extraction.top_k,
                similarity_threshold=self.config.extraction.similarity_threshold,
                embedding_model=self.config.extraction.embedding_model,
                extract_salient_points=self.config.extraction.extract_salient_points,
                use_reranking=self.config.extraction.use_reranking,
                deduplication=self.config.extraction.deduplication,
                chars_per_token=self.config.extraction.chars_per_token,
                max_embedding_chars=self.config.extraction.max_embedding_chars,
                **kwargs,
            )
        elif self.config.strategy == CompactionStrategyType.HYBRID:
            extraction = ExtractionStrategy(
                top_k=self.config.hybrid.extraction_config.top_k,
                similarity_threshold=self.config.hybrid.extraction_config.similarity_threshold,
                embedding_model=self.config.hybrid.extraction_config.embedding_model,
                extract_salient_points=self.config.hybrid.extraction_config.extract_salient_points,
                use_reranking=self.config.hybrid.extraction_config.use_reranking,
                deduplication=self.config.hybrid.extraction_config.deduplication,
                chars_per_token=self.config.hybrid.extraction_config.chars_per_token,
                max_embedding_chars=self.config.hybrid.extraction_config.max_embedding_chars,
                **kwargs,
            )
            summarization = SummarizationStrategy(
                mode=self.config.hybrid.summarization_config.mode,
                **kwargs,
            )
            return HybridStrategy(
                extraction_strategy=extraction,
                summarization_strategy=summarization,
                **kwargs,
            )
        else:  # NOOP
            return NoOpStrategy(**kwargs)

    async def compact(
        self,
        messages: List[BaseMessage],
        ext_context: Any,  # ExternalContextManager
        app_context: Dict[str, Any],
        full_history: Optional[List[BaseMessage]] = None,
        current_messages: Optional[List[BaseMessage]] = None,
    ) -> CompactionResult:
        """
        Master compaction algorithm (v2.5 with single-round architecture).

        Implements single-round compaction with dynamic budget adjustment and iterative summarization:
        1. Calculate context budget
        2. Identify new messages for JIT ingestion (avoid re-ingestion)
        3. Check if compaction needed
        4. Classify messages (tools merged into recent/historical)
        5. Enforce budget constraints with dynamic adjustment
        6. Compact historical section only (recent always preserved)
        7. Handle billing

        v2.5 changes: Tools are no longer separate sections. Latest tools are merged into
        recent (never compressed), old tools are merged into historical (compressed normally).
        Dynamic budget adjustment expands recent limit when it contains latest tool sequence.

        Args:
            messages: Messages to compact (can be previously summarized messages for iterative compaction)
            ext_context: External context manager
            app_context: Application context (user, run_job, etc.)
            full_history: Full uncompacted message history (for identifying new messages). If None, messages is treated as full history.
            current_messages: New messages from current turn (for JIT ingestion). If None, will be identified by comparing full_history with messages.

        Returns:
            CompactionResult with v2.1 metadata including ingestion status
        """
        # Extract context
        user = app_context.get("user")
        run_job: "WorkflowRunJobCreate" = app_context.get("workflow_run_job")
        org_id = run_job.owner_org_id
        user_id = user.id
        run_id = run_job.run_id

        # v2.1 Iterative Summarization: Identify current_messages if not provided
        if current_messages is None and full_history is not None:
            # Identify new messages by comparing full_history with messages
            # New messages are those in full_history but not in messages
            existing_ids = {msg.id for msg in messages if hasattr(msg, 'id') and msg.id}
            current_messages = [
                msg for msg in full_history
                if hasattr(msg, 'id') and msg.id and msg.id not in existing_ids
            ]
            if current_messages:
                self.info(
                    f"Identified {len(current_messages)} new messages for this turn "
                    f"(full_history: {len(full_history)}, summarized: {len(messages)})"
                )
        elif current_messages is None:
            # No full_history provided, treat all messages as current
            current_messages = []

        # Update recent_message_count based on current_messages
        self.config.recent_message_count = max(self.config.recent_message_count, len(current_messages))

        # Step 1: Calculate context budget
        budget = ContextBudget.calculate(
            total_context=self.model_metadata.context_limit,
            max_output_tokens=self.llm_node_llm_config.max_tokens,
            config=self.config.context_budget,
        )

        # Step 2: Create token cache for efficient token counting throughout compaction
        # This single cache will be passed to all operations, eliminating redundant token counting
        token_cache = MessageTokenCache(messages, self.model_metadata)
        total_tokens = token_cache.get_total()

        # Step 3: Check if compaction needed
        if total_tokens <= budget.target_usage_after_compaction:
            # Within budget, no compaction needed
            return CompactionResult(
                compacted_messages=messages,
                summary_messages=[],
                removed_message_ids=[],
                cost=0.0,
                compression_ratio=1.0,
                metadata={"compaction_skipped": True, "reason": "within_budget"},
            )

        # v2.1: Pass runtime_config for JIT ingestion and chunk re-attachment
        runtime_config = {
            "thread_id": run_job.thread_id,
            "node_id": self.node_id,
            "pending_chunk_reattachment": self.pending_chunk_reattachment,  # v2.1: For deduplication
            "current_messages": current_messages,  # v2.1: For re-ingestion prevention
            # "llm_config": self.config.llm_config,  # v2.1: For Perplexity fallback logic
            "original_indices": getattr(self.classifier, 'original_indices', {}),  # v2.4: For position weights
            "full_history": full_history,  # v2.1: For metadata filtering
            "full_history_indices": (  # v2.1: For position weights calculation
                {msg.id: idx for idx, msg in enumerate(full_history)}
                if full_history else {}
            ),
        }

        # v2.5: Single-round compaction (tools handled via dynamic budget adjustment)
        # Classify messages into sections (tools merged into recent/historical)
        sections = self.classifier.classify(
            messages=messages,
            recent_message_count=self.config.recent_message_count,
        )

        # Enforce budget constraints with dynamic reallocation
        sections = await self.budget_enforcer.enforce_budget(
            sections=sections,
            budget=budget,
            model_metadata=self.model_metadata,
            reallocation_config=self.config.dynamic_reallocation,
            token_cache=None,  # Let enforcer create per-section caches as needed
        )

        # Log final section-wise budget after enforcement
        if self.config.debug:
            from workflow_service.registry.nodes.llm.prompt_compaction.token_utils import count_tokens
            
            section_token_counts = {}
            for section_name, section_messages in sections.items():
                if section_messages:
                    section_token_counts[section_name] = count_tokens(
                        section_messages,
                        self.model_metadata
                    )
                else:
                    section_token_counts[section_name] = 0
            
            total_after_enforcement = sum(section_token_counts.values())
            
            self.logger.info(
                f"[{self.node_name}] Budget enforcement complete:\n"
                f"  Current total tokens: {total_after_enforcement}\n"
                f"  Target tokens (after compaction): {budget.target_usage_after_compaction}\n"
                f"  Available input tokens: {budget.available_input_tokens}\n"
                f"  Section-wise budget limits:\n"
                f"    - system_prompt_limit: {budget.system_prompt_limit} (actual: {section_token_counts.get('system', 0)})\n"
                f"    - recent_messages_limit: {budget.recent_messages_limit} (actual: {section_token_counts.get('recent', 0)})\n"
                f"    - marked_messages_limit: {budget.marked_messages_limit} (actual: {section_token_counts.get('marked', 0)})\n"
                f"    - summary_limit: {budget.summary_limit} (actual: {section_token_counts.get('summaries', 0)})\n"
                f"    - latest_tools_limit: {budget.latest_tools_limit} (actual: N/A - merged into recent/historical)\n"
                f"    - reserved_tokens: {budget.reserved_tokens}\n"
                f"    - historical: no hard limit (actual: {section_token_counts.get('historical', 0)})"
            )

        

        # Compact historical section only (recent section always passes through)
        result = await self.strategy.compact(
            sections=sections,
            budget=budget,
            model_metadata=self.model_metadata,
            ext_context=ext_context,
            runtime_config=runtime_config,
        )

        # Handle billing if compaction incurred costs
        if result.cost > 0:
            await self._bill_compaction(
                result=result,
                ext_context=ext_context,
                org_id=org_id,
                user_id=user_id,
                run_id=run_id,
            )
        
        tokens_after_compaction = count_tokens(
            result.compacted_messages,
            self.model_metadata
        )
        result.tokens_after_compaction = tokens_after_compaction
        
        if self.config.debug:
            self.logger.info(
                f"[{self.node_name}] Compaction result:\n"
                f"  Tokens before compaction: {total_tokens}\n"
                f"  Tokens after compaction: {result.tokens_after_compaction}\n"
                f"  Compression ratio: {tokens_after_compaction / total_tokens if total_tokens > 0 else 1:.2f}\n"
                f"  Cost: {result.cost}\n"
            )
            
        
        result.tokens_before_compaction = total_tokens

        return result

    async def test_compact_if_needed(
        self,
        messages: List[BaseMessage],
        ext_context: Any,
        model_metadata: Optional[ModelMetadata] = None,
    ) -> CompactionResult:
        """
        Convenience wrapper for compact() for testing and simple use cases.

        This method creates a minimal app_context, making it easier to test
        compaction without full workflow infrastructure.

        Args:
            messages: Messages to potentially compact
            ext_context: External context manager
            model_metadata: Ignored (uses self.model_metadata from __init__)

        Returns:
            CompactionResult
        """
        from uuid import uuid4

        # Create minimal test-compatible app_context
        class MockRunJob:
            def __init__(self):
                self.owner_org_id = uuid4()
                self.id = uuid4()
                self.run_id = uuid4()  # v2.1: Added for compact() compatibility
                self.thread_id = f"test_thread_{uuid4().hex[:8]}"

        class MockUser:
            def __init__(self):
                self.id = uuid4()

        app_context = {
            "user": MockUser(),
            "workflow_run_job": MockRunJob(),
        }

        return await self.compact(
            messages=messages,
            ext_context=ext_context,
            app_context=app_context,
        )

    async def _bill_compaction(
        self,
        result: CompactionResult,
        ext_context: Any,
        org_id: UUID,
        user_id: UUID,
        run_id: UUID,
    ) -> None:
        """
        Handle billing for compaction.

        Args:
            result: Compaction result
            ext_context: External context manager
            org_id: Organization ID
            user_id: User ID
            run_id: Run ID
        """
        strategy_type = result.metadata.get("strategy")

        if strategy_type == "summarization":
            # Bill for summarization
            token_usage = result.token_usage
            await bill_summarization(
                token_usage=token_usage,
                model_name="gpt-4o-mini",  # Default compaction model
                provider=LLMModelProvider.OPENAI,
                model_metadata=self.model_metadata,
                ext_context=ext_context,
                org_id=org_id,
                user_id=user_id,
                run_id=run_id,
                node_id=self.node_id,
                node_name=self.node_name,
                cost=result.cost,
                enable_billing=self.config.enable_billing,
            )

        elif strategy_type == "extraction":
            # Bill for extraction
            num_messages = result.metadata.get("num_candidates", 0)
            await bill_extraction(
                num_messages=num_messages,
                embedding_model=self.config.extraction.embedding_model,
                ext_context=ext_context,
                org_id=org_id,
                user_id=user_id,
                run_id=run_id,
                node_id=self.node_id,
                node_name=self.node_name,
                cost=result.cost,
                enable_billing=self.config.enable_billing,
            )

        elif strategy_type == "hybrid":
            # Bill for hybrid
            extraction_cost = result.metadata.get("extraction_cost", 0.0)
            summarization_cost = result.metadata.get("summarization_cost", 0.0)
            await bill_hybrid(
                extraction_cost=extraction_cost,
                summarization_cost=summarization_cost,
                ext_context=ext_context,
                org_id=org_id,
                user_id=user_id,
                run_id=run_id,
                node_id=self.node_id,
                node_name=self.node_name,
                metadata=result.metadata,
                enable_billing=self.config.enable_billing,
            )

    def should_compact(self, messages: List[BaseMessage]) -> Tuple[float, bool, bool]:
        """
        Check if compaction should be triggered.

        Args:
            messages: Messages to check

        Returns:
            Tuple[float, bool, bool]: (usage_percentage, is_approaching_threshold, is_triggering_threshold)
        """
        if not self.config.enabled:
            return 0.0, False, False

        # Calculate budget
        budget = ContextBudget.calculate(
            total_context=self.model_metadata.context_limit,
            max_output_tokens=self.llm_node_llm_config.max_tokens,
            config=self.config.context_budget,
        )

        # Count tokens
        total_tokens = count_tokens(messages, self.model_metadata)

        # Check threshold
        usage_pct = total_tokens / (budget.available_input_tokens if budget.available_input_tokens > 0 else 1.0)

        return usage_pct, usage_pct >= self.config.context_budget.warning_threshold_pct, usage_pct >= self.config.context_budget.trigger_threshold_pct
