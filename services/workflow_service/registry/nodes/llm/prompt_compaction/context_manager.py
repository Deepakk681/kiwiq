"""
Context window allocation and message classification for prompt compaction (v2.1).

Provides:
- ContextBudget: Calculate and manage token budgets for different message sections
- MessageClassifier: Classify messages into sections (system, marked, recent, historical, etc.)
- BudgetEnforcer: Enforce budget constraints on classified messages

v2.1 Features:
- Atomic tool call sequence preservation (v2.1)
- Tool sequences are treated as indivisible units during retention/summarization/discard
"""

from typing import List, Dict, Tuple, Optional, TYPE_CHECKING
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from workflow_service.registry.nodes.llm.prompt_compaction.compactor import DynamicReallocationConfig

from langchain_core.messages import (
    BaseMessage,
    AIMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)

from workflow_service.registry.nodes.llm.config import ModelMetadata
from workflow_service.registry.nodes.llm.prompt_compaction.token_utils import (
    count_tokens,
    binary_search_message_count,
    split_messages_by_budget,
    MessageTokenCache,
)
from workflow_service.registry.nodes.llm.prompt_compaction.utils import (
    get_message_metadata,
    set_message_metadata,
    ContextBudgetError,
)


class ContextBudgetConfig(BaseModel):
    """
    Configuration for context window budget allocation (v2.5).

    Controls how available input tokens are distributed across message sections:
    - System prompts (instructions, tools, configuration)
    - Summary messages (compacted conversation history)
    - Marked messages (explicitly flagged for retention)
    - Recent messages (latest conversation turns, includes latest tool sequences)
    
    v2.5 changes:
    - Tools merged into recent/historical (no separate latest_tools/old_tools sections)
    - Dynamic budget: recent_limit += latest_tools_limit when recent has latest tool sequence
    - Simplified architecture with single tool boundary computation

    The percentages define maximum/minimum allocations, with the budget calculator
    dynamically adjusting based on actual usage.

    Usage Example:
        ```python
        # Default configuration (balanced)
        config = ContextBudgetConfig()

        # High-context mode (more history, less recent)
        config = ContextBudgetConfig(
            summary_max_pct=0.30,         # 30% for summaries
            recent_messages_min_pct=0.30  # 30% minimum for recent
        )

        # Tool-heavy mode (more system, less summaries)
        config = ContextBudgetConfig(
            system_prompt_max_pct=0.20,   # 20% for system/tools
            summary_max_pct=0.15          # 15% for summaries
        )

        # Create budget from config
        budget = ContextBudget.calculate(
            total_context=128000,
            max_output_tokens=16384,
            config=config
        )
        ```

    Cross-file Usage:
        - context_manager.py: ContextBudget.calculate() applies these percentages
        - compactor.py: PromptCompactor uses budget for compaction decisions
        - strategies.py: All strategies respect section limits
        - llm_node.py: LLM node creates budget for each invocation

    Budget Calculation Flow:
        1. Calculate safety buffer (buffer_pct * total_context)
        2. Calculate available input = total_context - max_output_tokens - buffer
        3. Allocate sections based on percentages:
           - system_limit = available_input * system_prompt_max_pct
           - summary_limit = available_input * summary_max_pct
           - marked_limit = available_input * marked_messages_max_pct
           - recent_limit = available_input * recent_messages_min_pct (guaranteed minimum)

    Edge Cases:
        - If percentages sum > 1.0: Sections may overlap, priority: recent > marked > summary > system
        - If system messages exceed limit: Truncated from beginning (keeps latest tools)
        - If marked messages exceed limit: Oldest marked messages dropped first
        - If summaries exceed limit: Triggers additional summarization
        - If recent messages < minimum: Compaction delayed until more messages

    Attributes:
        system_prompt_max_pct: Maximum percentage of input tokens for system messages
        summary_max_pct: Maximum percentage for summary messages
        marked_messages_max_pct: Maximum percentage for marked messages
        recent_messages_min_pct: Minimum percentage guaranteed for recent messages
        buffer_pct: Safety buffer percentage of total context
    """

    # Section allocations (as percentage of available input budget)
    system_prompt_max_pct: float = Field(
        default=0.20,
        ge=0.0,
        le=1.0,
        description=(
            "Maximum percentage of available input tokens for system prompts. "
            "Includes: system messages, tool definitions, configuration instructions. "
            "Edge cases: "
            "- If system messages exceed this limit, they are truncated from the beginning. "
            "- Tool call sequences are atomic and may push slightly over limit. "
            "- Very large tool schemas (>10K tokens) may consume most of this budget."
        ),
    )

    summary_max_pct: float = Field(
        default=0.20,
        ge=0.0,
        le=1.0,
        description=(
            "Maximum percentage for compacted summary messages. "
            "Controls total size of compacted conversation history. "
            "Used by: SummarizationStrategy, HybridStrategy. "
            "Edge cases: "
            "- If summaries exceed limit, triggers additional summarization (recursive). "
            "- Multiple summary generations (gen 0, 1, 2...) accumulate toward this limit. "
            "- Extraction strategy may store extracted messages instead of summaries. "
            "- Setting too low (<0.10) may trigger frequent re-summarization."
        ),
    )

    marked_messages_max_pct: float = Field(
        default=0.10,
        ge=0.0,
        le=1.0,
        description=(
            "Maximum percentage for explicitly marked messages. "
            "Marked messages bypass normal compaction (critical context retention). "
            "Edge cases: "
            "- If marked messages exceed limit, oldest marked messages dropped first. "
            "- Marked tool sequences kept atomic (all or nothing). "
            "- Setting to 0.0 disables marked message retention. "
            "- User can mark messages via metadata: mark_for_retention=True."
        ),
    )

    recent_messages_min_pct: float = Field(
        default=0.30,
        ge=0.0,
        le=1.0,
        description=(
            "Minimum percentage GUARANTEED for recent messages. "
            "This is a floor - actual allocation may be higher if other sections unused. "
            "Edge cases: "
            "- Compaction delayed if recent messages < this minimum. "
            "- Very long recent messages (e.g., 100K token response) may exceed this. "
            "- Tool sequences in recent section are atomic. "
            "- Setting too low (<0.30) may trigger premature compaction."
        ),
    )

    latest_tools_max_pct: float = Field(
        default=0.20,
        ge=0.0,
        le=1.0,
        description=(
            "Additional budget allocated to recent messages when containing latest tool sequence (v2.5). "
            "v2.5 behavior: Tools are no longer separate sections. Instead: "
            "- If 'recent' contains the last tool sequence (no AI messages after it), "
            "  recent_messages_limit is dynamically increased by this amount. "
            "- This ensures recent tool sequences get adequate space without truncation. "
            "- Tools that are not the latest are part of historical section (can be compacted). "
            "Includes: Tool calls + responses + interleaved HumanMessages (max span). "
            "Edge cases: "
            "- If no latest tools in recent, this budget is unused (not reallocated). "
            "- Never truncates tool responses (preserves complete tool execution context). "
            "- System prompt still has highest priority (must always fit)."
        ),
    )

    # Safety buffer (percentage of total context)
    buffer_pct: float = Field(
        default=0.10,
        ge=0.0,
        le=0.2,
        description=(
            "Safety buffer as percentage of total context window. "
            "Default: 0.10 (10%). "
            "Protects against: "
            "- Token counting inaccuracies (different tokenizers). "
            "- Message formatting overhead (role markers, separators). "
            "- Tool call response expansion. "
            "Edge cases: "
            "- Minimum recommended: 0.05 (5%) for OpenAI models with tiktoken. "
            "- Increase to 0.15 (15%) for Anthropic/Gemini (estimation-based counting). "
            "- Setting to 0.0 risks context overflow errors. "
            "- Maximum allowed: 0.2 (20%)."
        ),
    )

    # Trigger thresholds
    trigger_threshold_pct: float = Field(
        default=0.9,
        ge=0.0,
        le=1.0,
        description=(
            "Context usage percentage (0.0-1.0) at which to trigger compaction. "
            "Example: 0.80 = start compaction when messages reach 80% of available input budget. "
            "Recommended: 0.70-0.85."
        ),
    )

    warning_threshold_pct: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description=(
            "Context usage percentage (0.0-1.0) at which to log warnings. "
            "Example: 0.70 = warn when messages reach 70% of available input budget. "
            "Should be < trigger_threshold_pct."
        ),
    )

    # v2.0: Target 50% usage after compaction (not "free space")
    target_usage_pct: float = Field(
        default=0.50,
        ge=0.0,
        le=1.0,
        description=(
            "Target context usage percentage (0.0-1.0) after compaction completes. "
            "Example: 0.50 = aim for 50% usage after compaction (leaving 50% free). "
            "v2.0: Changed from 'target free space' to 'target usage'. "
            "Recommended: 0.40-0.60."
        ),
    )


class ContextBudget(BaseModel):
    """
    Context window budget calculator (v2.1).

    Calculates and tracks token allocations for different message sections based on
    model capabilities and ContextBudgetConfig.

    The budget divides available input tokens into sections with hard limits:
    - System prompts: Tools, instructions (max allocation)
    - Recent messages: Latest conversation turns (guaranteed minimum)
    - Marked messages: Explicitly retained messages (max allocation)
    - Summary messages: Compacted history (max allocation)
    - Reserved: Flexible space for dynamic reallocation

    Usage Example:
        ```python
        from workflow_service.registry.nodes.llm.config import ModelMetadata
        from workflow_service.registry.nodes.llm.prompt_compaction.context_manager import (
            ContextBudget,
            ContextBudgetConfig,
        )

        # Calculate budget for gpt-4o
        budget = ContextBudget.calculate(
            total_context=128000,
            max_output_tokens=16384,
            config=ContextBudgetConfig()
        )

        # Check available space
        print(f"Available input: {budget.available_input_tokens} tokens")
        print(f"System limit: {budget.system_prompt_limit} tokens")
        print(f"Recent limit: {budget.recent_messages_limit} tokens")
        print(f"Summary limit: {budget.summary_limit} tokens")
        print(f"Reserved: {budget.reserved_tokens} tokens")

        # Use budget for compaction decisions
        if current_usage > budget.max_usage_before_compaction:
            # Trigger compaction
            compact_messages(budget)
        ```

    Budget Calculation (128K context example with defaults):
        ```
        Total context: 128,000 tokens
        - Max output: 16,384 tokens
        - Safety buffer: 12,800 tokens (10%)
        = Available input: 98,816 tokens

        Section allocations (% of available input):
        - System prompt: 9,881 tokens (10%)
        - Recent messages: 39,526 tokens (40% minimum)
        - Marked messages: 9,881 tokens (10%)
        - Summary messages: 19,763 tokens (20%)
        - Reserved: 19,765 tokens (remaining ~20%)

        Compaction thresholds:
        - Target after compaction: 44,467 tokens (45% of available)
        - Max before compaction: 79,052 tokens (80% of available)
        ```

    Cross-file Usage:
        - compactor.py: PromptCompactor.should_compact() checks max_usage_before_compaction
        - strategies.py: All strategies use section limits for filtering
        - context_manager.py: MessageClassifier uses limits to classify messages
        - llm_node.py: Creates budget before each LLM call

    Attributes:
        total_context_limit (int): Model's total context window (e.g., 128000 for gpt-4o)
        max_output_tokens (int): Maximum tokens allocated for LLM response
        safety_buffer (int): Safety margin for token counting inaccuracies
        available_input_tokens (int): Tokens available for input messages (context - output - buffer)

        system_prompt_limit (int): Maximum tokens for system messages/tools
        recent_messages_limit (int): Minimum guaranteed tokens for recent conversation
        marked_messages_limit (int): Maximum tokens for explicitly marked messages
        summary_limit (int): Maximum tokens for compacted summaries
        latest_tools_limit (int): Maximum tokens for latest tool sequence (HIGH PRIORITY)
        reserved_tokens (int): Flexible tokens not allocated to specific sections

        target_usage_after_compaction (int): Target token count post-compaction (45% of available)
        max_usage_before_compaction (int): Threshold to trigger compaction (80% of available)
    """

    # Total limits
    total_context_limit: int  # Model's total context window
    max_output_tokens: int  # Reserved for LLM response
    safety_buffer: int  # Token counting safety margin
    available_input_tokens: int  # total_context - max_output - buffer

    # Section limits (calculated from ContextBudgetConfig percentages)
    system_prompt_limit: int  # Max tokens for system/tools
    recent_messages_limit: int  # Min guaranteed tokens for recent msgs
    marked_messages_limit: int  # Max tokens for marked msgs
    summary_limit: int  # Max tokens for summaries
    latest_tools_limit: int  # Max tokens for latest tools (HIGH PRIORITY)
    reserved_tokens: int  # Flexible space for reallocation

    # Compaction thresholds (when to trigger/target)
    target_usage_after_compaction: int  # Goal: 45% of available input
    max_usage_before_compaction: int  # Trigger: 80% of available input

    @classmethod
    def calculate(
        cls,
        total_context: int,
        max_output_tokens: int,
        config: ContextBudgetConfig,
    ) -> "ContextBudget":
        """
        Calculate context budget with dynamic allocation.

        Allocation strategy:
        1. Reserve output tokens + safety buffer
        2. Allocate fixed percentages to sections
        3. Track remaining flexible space

        Args:
            total_context: Model's total context window size
            max_output_tokens: Maximum tokens for LLM output
            config: Budget configuration

        Returns:
            ContextBudget with calculated allocations
        """
        # Step 1: Calculate available input budget
        safety_buffer = int(total_context * config.buffer_pct)
        available_input = total_context - max_output_tokens - safety_buffer

        # Step 2: Allocate sections (hard limits)
        system_limit = int(available_input * config.system_prompt_max_pct)
        recent_limit = int(available_input * config.recent_messages_min_pct)
        marked_limit = int(available_input * config.marked_messages_max_pct)
        summary_limit = int(available_input * config.summary_max_pct)
        latest_tools_limit = int(available_input * config.latest_tools_max_pct)

        # Step 3: Calculate reserved/flex space
        allocated = system_limit + recent_limit + marked_limit + summary_limit + latest_tools_limit
        reserved = available_input - allocated

        assert reserved >= 0, "Reserved tokens cannot be negative"

        return cls(
            total_context_limit=total_context,
            max_output_tokens=max_output_tokens,
            safety_buffer=safety_buffer,
            available_input_tokens=available_input,

            # Section limits
            system_prompt_limit=system_limit,
            recent_messages_limit=recent_limit,
            marked_messages_limit=marked_limit,
            summary_limit=summary_limit,
            latest_tools_limit=latest_tools_limit,
            reserved_tokens=reserved,

            # Target after compaction: leave 50-60% free
            target_usage_after_compaction=int(available_input * config.target_usage_pct),
            max_usage_before_compaction=int(available_input * config.trigger_threshold_pct),
        )


class MessageClassifier:
    """
    Classifies messages into sections for compaction.

    Sections:
    - system: System prompts (never compress)
    - marked: Marked as preserve/dont_summarize
    - summaries: Existing summary messages
    - tool_sequences: Tool call + response sequences
    - recent: Last N messages
    - historical: Everything else (compaction candidates)
    """

    def __init__(self, preserve_tool_call_sequences: bool = True):
        """
        Initialize classifier.

        Args:
            preserve_tool_call_sequences: Whether to preserve tool call sequences intact
        """
        self.preserve_tool_call_sequences = preserve_tool_call_sequences

    def classify(
        self,
        messages: List[BaseMessage],
        recent_message_count: int,
    ) -> Dict[str, List[BaseMessage]]:
        """
        Classify messages into sections (v2.5 - simplified tool handling).

        v2.5 changes:
        - Tools merged into recent/historical (no separate latest_tools/old_tools sections)
        - Single tool boundary computation reused throughout
        - Dynamic budget adjustment when recent contains last tool sequence
        - Respects tool boundaries when splitting recent/historical (atomic handling)

        Args:
            messages: All messages to classify
            recent_message_count: Number of recent messages to preserve (approximate)

        Returns:
            Dict mapping section names to message lists:
            - system: System messages
            - summaries: Existing summary messages
            - marked: Explicitly preserved messages
            - recent: Last N messages (including tools if present)
            - historical: Older messages (including tools if present)
        """
        sections = {
            "system": [],
            "marked": [],
            "summaries": [],
            "recent": [],
            "historical": [],
        }

        # Create original_indices map for position weight tracking (v2.4)
        # Maps message.id → original index in messages list
        # Store as instance variable so it can be passed to strategies
        self.original_indices = {}
        for idx, msg in enumerate(messages):
            if hasattr(msg, 'id') and msg.id:
                self.original_indices[msg.id] = idx

        # Extract tool sequence boundaries from FULL messages list (v2.5)
        # This is the single source of truth - cached for reuse in BudgetEnforcer
        if self.preserve_tool_call_sequences:
            self.tool_sequence_boundaries, last_is_latest = self._extract_tool_sequences(messages)
        else:
            self.tool_sequence_boundaries, last_is_latest = [], False

        # Initialize flag for dynamic budget adjustment
        self.has_latest_tool_in_recent = False

        # Pass 1: Extract special messages (system, summaries, marked)
        # Track which indices are "claimed" by special sections
        special_indices = set()
        
        for i, msg in enumerate(messages):
            # System messages (only first message)
            if isinstance(msg, SystemMessage) and (i == 0):
                sections["system"].append(msg)
                special_indices.add(i)
                continue

            # Summary messages
            if get_message_metadata(msg, "message_type") == "summary" or get_message_metadata(msg, "is_summary"):
                sections["summaries"].append(msg)
                special_indices.add(i)
                continue

            # Marked messages (preserve)
            if get_message_metadata(msg, "preserve") or get_message_metadata(msg, "dont_summarize"):
                sections["marked"].append(msg)
                special_indices.add(i)
                continue

        # Pass 2: Split remaining messages into recent/historical
        # Calculate initial split point (last N messages)
        recent_start = max(0, len(messages) - recent_message_count)
        
        # Adjust split point to respect tool boundaries (prefer keeping sequences in recent)
        # If split would break a tool sequence, move split earlier to keep entire sequence in recent
        for seq_start, seq_end in self.tool_sequence_boundaries:
            if seq_start < recent_start < seq_end:
                # Split would break this sequence - move earlier to keep it in recent
                recent_start = seq_start
                break
        
        # Check if recent contains the last tool sequence (for dynamic budget adjustment)
        if self.tool_sequence_boundaries and last_is_latest:
            last_seq_start, last_seq_end = self.tool_sequence_boundaries[-1]
            # Last sequence is in recent if its end is after recent_start
            self.has_latest_tool_in_recent = (last_seq_end > recent_start)
        
        # Split messages into recent and historical (excluding special messages)
        for i, msg in enumerate(messages):
            if i in special_indices:
                continue  # Skip system/summaries/marked
            
            if i >= recent_start:
                sections["recent"].append(msg)
            else:
                sections["historical"].append(msg)

        # Pass 3: Sort summaries by generation (oldest first)
        sections["summaries"].sort(
            key=lambda m: get_message_metadata(m, "summary_generation", 0)
        )

        return sections

    def _extract_tool_sequences(
        self,
        messages: List[BaseMessage],
    ) -> Tuple[List[Tuple[int, int]], bool]:
        """
        Extract tool call sequence boundaries with MAX SPAN grouping (v2.5).

        Returns ABSOLUTE indices (relative to the input messages list) of tool sequences.
        This is the single source of truth for tool boundary detection - used throughout
        classification and budget enforcement to avoid redundant computation.

        Unified algorithm for both OpenAI and Anthropic:
        1. AIMessage with non-empty tool_calls opens a sequence
        2. Collect all tool call IDs: call.get('id') for call in msg.tool_calls
        3. Immediate next messages are tool responses (adjacent, no gaps):
           - OpenAI: ToolMessage with tool_call_id field
           - Anthropic: HumanMessage with content list containing tool_result with tool_use_id
        4. After all tool responses, continue MAX SPAN (include HumanMessages until next AIMessage)
        5. Sequence ends when: next AIMessage arrives or end of messages

        v2.5 changes (tool simplification):
        - Now works on FULL messages list (not just unclassified)
        - Returns absolute indices that can be used directly for recent/historical splitting
        - Boundaries are cached in self.tool_sequence_boundaries for reuse in BudgetEnforcer
        
        v2.4 features:
        - Returns (indices, last_is_latest) tuple
        - Indices are (start, end) where end is EXCLUSIVE
        - last_is_latest=True if last sequence has NO AI messages after it
        - Simplified: tool calls always detected via msg.tool_calls (both providers)
        - Tool responses are ALWAYS adjacent to tool calls (no messages in between)
        
        Examples:
            [Sys, AIMsg(tc1), ToolResp1, Human] → ([(1, 4)], True) - absolute indices
            [Human, AIMsg(tc), ToolResp, AIMsg] → ([(1, 3)], False) - AI after

        Args:
            messages: Full messages list (not filtered - includes system/summaries/etc)

        Returns:
            Tuple of (indices_list, last_sequence_is_latest)
            - indices_list: List of (start_idx, end_idx) tuples where end_idx is EXCLUSIVE
              Indices are ABSOLUTE positions in the input messages list
            - last_sequence_is_latest: True if last sequence has no AI messages after it
              (this indicates the last tool sequence should get tool budget in recent)
        """
        sequence_indices = []
        current_start = None
        open_tool_call_ids = set()  # Set of tool_call_id strings waiting for responses
        tools_closed = False  # Track if we're in "all closed, collecting HumanMessages" state

        i = 0
        while i < len(messages):
            msg = messages[i]

            # Case 1: AIMessage with tool_calls - opens a new tool sequence
            if isinstance(msg, AIMessage) and hasattr(msg, "tool_calls") and msg.tool_calls:
                # If we were collecting post-tool HumanMessages, close that sequence first
                if current_start is not None and tools_closed:
                    # Validate completeness before adding
                    if MessageClassifier._is_tool_sequence_complete(messages[current_start:i]):
                        sequence_indices.append((current_start, i))
                    current_start = None
                    tools_closed = False
                    open_tool_call_ids.clear()
                
                # Start new sequence
                if current_start is None:
                    current_start = i

                # Collect all tool call IDs from this message (works for both providers)
                open_tool_call_ids = {
                    call.get('id') 
                    for call in msg.tool_calls 
                    if call.get('id')
                }

                i += 1
            
            # Case 2: AIMessage without tool calls - closes current sequence
            elif isinstance(msg, AIMessage):
                if current_start is not None:
                    # Validate completeness before adding
                    if MessageClassifier._is_tool_sequence_complete(messages[current_start:i]):
                        sequence_indices.append((current_start, i))
                    current_start = None
                    tools_closed = False
                    open_tool_call_ids.clear()
                i += 1

            # Case 3: ToolMessage - OpenAI tool response
            elif isinstance(msg, ToolMessage):
                if current_start is not None:
                    # Check if this is a response to one of our open tool calls
                    tool_call_id = getattr(msg, 'tool_call_id', None)
                    if tool_call_id and tool_call_id in open_tool_call_ids:
                        # Valid response - include in sequence
                        open_tool_call_ids.discard(tool_call_id)
                        
                        # If all tool calls closed, enter "collecting HumanMessages" state
                        if not open_tool_call_ids:
                            tools_closed = True
                    # else: orphaned tool response - ignore but don't close sequence yet
                i += 1

            # Case 4: HumanMessage - could be Anthropic tool response or regular message
            elif isinstance(msg, HumanMessage):
                if current_start is not None:
                    # Check if this is an Anthropic tool response (content is list with tool_result)
                    if isinstance(msg.content, list):
                        tool_results = [
                            c for c in msg.content 
                            if isinstance(c, dict) and c.get("type") == "tool_result"
                        ]
                        
                        if tool_results:
                            # This is an Anthropic tool response message
                            # Match tool results to open tool calls
                            for tr in tool_results:
                                tool_use_id = tr.get("tool_use_id")
                                if tool_use_id and tool_use_id in open_tool_call_ids:
                                    open_tool_call_ids.discard(tool_use_id)
                            
                            # If all tool calls closed, enter "collecting HumanMessages" state
                            if not open_tool_call_ids:
                                tools_closed = True
                            
                            i += 1
                        else:
                            # HumanMessage with list content but no tool_result
                            # Include in MAX SPAN if we're collecting post-tool messages
                            if tools_closed or open_tool_call_ids:
                                i += 1
                            else:
                                # Not part of sequence
                                i += 1
                    else:
                        # HumanMessage with string content
                        # MAX SPAN: Include if we're collecting post-tool messages
                        if tools_closed:
                            i += 1
                        else:
                            # Not part of sequence (still waiting for tool responses)
                            i += 1
                else:
                    # No active sequence
                    i += 1

            # Case 5: Other message types (SystemMessage, etc.)
            else:
                # Include in sequence if we're in MAX SPAN collection mode
                if current_start is not None and tools_closed:
                    i += 1
                else:
                    # Not part of sequence
                    i += 1

        # Don't forget last sequence
        if current_start is not None:
            # Validate completeness before adding
            if MessageClassifier._is_tool_sequence_complete(messages[current_start:]):
                sequence_indices.append((current_start, len(messages)))

        # Determine if last sequence is latest (no AI messages after it)
        # Last sequence is latest if it extends to end of messages OR has no AI after
        last_is_latest = False
        if sequence_indices:
            last_start, last_end = sequence_indices[-1]
            # Check if there are any AI messages after the last sequence
            has_ai_after = any(
                isinstance(msg, AIMessage)
                for msg in messages[last_end:]
            )
            last_is_latest = not has_ai_after

        return sequence_indices, last_is_latest

    @staticmethod
    def _is_tool_sequence_complete(sequence: List[BaseMessage]) -> bool:
        """
        Check if tool sequence is complete (all tool calls have responses) (v2.4).
        
        Used to prevent orphaned tool calls when old_tools are converted to text.
        If a sequence has unclosed tool calls, it should remain as regular messages.
        
        Unified approach (v2.4):
        - Tool calls detected via msg.tool_calls (both OpenAI and Anthropic)
        - OpenAI responses: ToolMessage with tool_call_id
        - Anthropic responses: HumanMessage with content list containing tool_result
        
        Args:
            sequence: List of messages in the tool sequence
            
        Returns:
            True if complete (all calls have responses), False otherwise
            
        Example:
            [AIMsg(tc1,tc2), ToolResp1, ToolResp2] → True (complete)
            [AIMsg(tc1,tc2), ToolResp1] → False (tc2 has no response)
            [AIMsg(tc1), ToolResp1, HumanMsg] → True (complete with trailing message)
        """
        open_call_ids = set()  # Set of tool_call_id strings waiting for responses
        
        for msg in sequence:
            # Track tool calls (unified: both providers use msg.tool_calls)
            if isinstance(msg, AIMessage) and hasattr(msg, "tool_calls") and msg.tool_calls:
                for call in msg.tool_calls:
                    call_id = call.get('id')
                    if call_id:
                        open_call_ids.add(call_id)
            
            # Track OpenAI responses (ToolMessage)
            elif isinstance(msg, ToolMessage):
                tool_call_id = getattr(msg, 'tool_call_id', None)
                if tool_call_id:
                    open_call_ids.discard(tool_call_id)
            
            # Track Anthropic responses (HumanMessage with tool_result)
            elif isinstance(msg, HumanMessage) and isinstance(msg.content, list):
                tool_results = [
                    c for c in msg.content 
                    if isinstance(c, dict) and c.get("type") == "tool_result"
                ]
                for tr in tool_results:
                    tool_use_id = tr.get("tool_use_id")
                    if tool_use_id:
                        open_call_ids.discard(tool_use_id)
        
        # Complete if no open calls remain
        return len(open_call_ids) == 0

    @staticmethod
    def trim_messages_respecting_tool_groups(
        messages: List[BaseMessage],
        keep_count: int,
        from_end: bool = True,
        pre_computed_boundaries: Optional[List[Tuple[int, int]]] = None,
    ) -> Tuple[List[BaseMessage], List[BaseMessage]]:
        """
        Trim messages to keep_count while respecting tool call atomic groups (v2.6).

        CRITICAL: Never exceeds keep_count. If trimming would split a tool call group,
        the entire group is excluded to respect the keep_count limit.

        v2.6: Fixed to never exceed keep_count (previously could expand to include groups).
        v2.5: Accepts pre-computed boundaries to avoid redundant tool detection.

        Args:
            messages: Messages to trim
            keep_count: MAXIMUM number of messages to keep (never exceeded)
            from_end: If True, keep last keep_count messages; if False, keep first keep_count
            pre_computed_boundaries: Optional pre-computed tool sequence boundaries
                - If provided, used directly (must have INCLUSIVE end indices)
                - If None, computes boundaries via _extract_tool_sequences

        Returns:
            Tuple of (kept_messages, overflow_messages)
            - len(kept_messages) <= keep_count (GUARANTEED)
            - May keep fewer than keep_count to avoid splitting tool groups
            
        Example (from_end=True):
            messages = [M0, M1, M2, TC_start, TC_mid, TC_end, M6, M7]  # 8 messages
            tool_group = [3, 4, 5]  # indices 3-5
            keep_count = 3
            
            Naive trim would keep: [TC_mid, TC_end, M6]  # BAD - splits tool group
            v2.5 (old) kept: [TC_start, TC_mid, TC_end, M6, M7]  # BAD - exceeds keep_count (5 > 3)
            v2.6 (new) keeps: [M6, M7]  # GOOD - respects keep_count, excludes entire group (2 <= 3)
            
        Example (from_end=False):
            messages = [M0, M1, TC_start, TC_mid, TC_end, M5, M6, M7]  # 8 messages
            tool_group = [2, 3, 4]  # indices 2-4
            keep_count = 4
            
            Naive trim would keep: [M0, M1, TC_start, TC_mid]  # BAD - splits tool group
            v2.5 (old) kept: [M0, M1, TC_start, TC_mid, TC_end]  # BAD - exceeds keep_count (5 > 4)
            v2.6 (new) keeps: [M0, M1]  # GOOD - respects keep_count, excludes entire group (2 <= 4)
        """
        if keep_count <= 0:
            return [], messages
        if keep_count >= len(messages):
            return messages, []

        # Get tool call group boundaries (use pre-computed if available)
        if pre_computed_boundaries is not None:
            tool_groups = pre_computed_boundaries
        else:
            # Compute boundaries - need to convert to INCLUSIVE end indices
            classifier = MessageClassifier()
            boundaries, _ = classifier._extract_tool_sequences(messages)
            # Convert EXCLUSIVE end to INCLUSIVE for backward compatibility
            tool_groups = [(start, end - 1) for start, end in boundaries]
        
        # Create a map of message_idx -> group_idx
        msg_to_group = {}
        for group_idx, (start, end) in enumerate(tool_groups):
            for i in range(start, end + 1):
                msg_to_group[i] = group_idx

        if from_end:
            # Keep last keep_count messages
            trim_point = len(messages) - keep_count
            
            # Check if trim point splits a tool group
            if trim_point in msg_to_group:
                group_idx = msg_to_group[trim_point]
                group_start, group_end = tool_groups[group_idx]
                
                # v2.6: Exclude entire group to never exceed keep_count
                # Move trim point to END of group (skip entire group)
                if trim_point > group_start:
                    # Trim point is in middle of group - move to end of group to exclude it
                    trim_point = group_end + 1
            
            kept = messages[trim_point:]
            overflow = messages[:trim_point]
        else:
            # Keep first keep_count messages
            trim_point = keep_count
            
            # Check if trim point splits a tool group
            if trim_point - 1 in msg_to_group:
                group_idx = msg_to_group[trim_point - 1]
                group_start, group_end = tool_groups[group_idx]
                
                # v2.6: Exclude entire group to never exceed keep_count
                # Move trim point to START of group (skip entire group)
                if trim_point <= group_end:
                    # Trim point is in middle of group - move to start of group to exclude it
                    trim_point = group_start
            
            kept = messages[:trim_point]
            overflow = messages[trim_point:]

        return kept, overflow

    @staticmethod
    async def split_messages_by_budget_respecting_tool_groups(
        messages: List[BaseMessage],
        budget: int,
        model_metadata: ModelMetadata,
        keep_newest: bool = True,
        token_cache: Optional[MessageTokenCache] = None,
        pre_computed_boundaries: Optional[List[Tuple[int, int]]] = None,
    ) -> Tuple[List[BaseMessage], List[BaseMessage]]:
        """
        Split messages by token budget while respecting tool call atomic groups (v2.5).

        Uses binary search with MessageTokenCache for O(n) efficiency instead of O(n log n).

        v2.5: Accepts pre-computed boundaries to avoid redundant tool detection.

        Args:
            messages: Messages to split
            budget: Token budget for first group
            model_metadata: Model metadata for token counting
            keep_newest: If True, keep newest messages in first group
            token_cache: Optional pre-computed token cache for efficiency
            pre_computed_boundaries: Optional pre-computed tool sequence boundaries
                - If provided, passed to trim_messages_respecting_tool_groups

        Returns:
            Tuple of (within_budget, overflow)
        """
        if not messages:
            return [], []

        # Create cache if not provided
        if token_cache is None:
            token_cache = MessageTokenCache(messages, model_metadata)

        # Find max messages that fit in budget using cache
        max_count = await binary_search_message_count(
            messages=messages,
            max_tokens=budget,
            model_metadata=model_metadata,
            token_cache=token_cache,
        )

        if max_count <= 0:
            return [], messages

        # Trim while respecting tool call groups (use pre-computed boundaries if available)
        if keep_newest:
            within_budget, overflow = MessageClassifier.trim_messages_respecting_tool_groups(
                messages=messages,
                keep_count=max_count,
                from_end=True,
                pre_computed_boundaries=pre_computed_boundaries,
            )
        else:
            within_budget, overflow = MessageClassifier.trim_messages_respecting_tool_groups(
                messages=messages,
                keep_count=max_count,
                from_end=False,
                pre_computed_boundaries=pre_computed_boundaries,
            )

        return within_budget, overflow


class BudgetEnforcer:
    """
    Enforces token budgets for each section (v2.5).

    Priority order:
    1. System prompt (highest - fail if exceeds)
    2. Recent messages (includes tools, gets dynamic budget adjustment)
    3. Marked messages (compress oldest if exceeds)
    4. Summaries (compress/merge if exceeds)

    v2.5: Tools merged into recent/historical, dynamic budget when recent has latest tool.
    v2.0: Supports dynamic budget reallocation.
    """

    def __init__(self, classifier: Optional[MessageClassifier] = None):
        """
        Initialize BudgetEnforcer.

        Args:
            classifier: MessageClassifier instance with pre-computed tool boundaries
                       Used to reuse tool sequence detection and access flags
        """
        self.classifier = classifier

    def reallocate_budget(
        self,
        budget: ContextBudget,
        actual_usage: Dict[str, int],
        reallocation_config: "DynamicReallocationConfig",
    ) -> ContextBudget:
        """
        Dynamically reallocate budget based on actual usage (v2.5).

        v2.5: Tools merged into recent section, no separate latest_tools allocation.

        Args:
            budget: Original budget allocation
            actual_usage: Actual token usage per section
            reallocation_config: Dynamic reallocation configuration

        Returns:
            Reallocated budget
        """
        if not reallocation_config.enabled:
            return budget

        # Calculate surplus and deficit
        section_allocations = {
            "system": budget.system_prompt_limit,
            "recent": budget.recent_messages_limit,
            "marked": budget.marked_messages_limit,
            "summaries": budget.summary_limit,
        }

        surplus = {}
        deficit = {}

        for section, allocated in section_allocations.items():
            actual = actual_usage.get(section, 0)
            if actual < allocated:
                surplus[section] = allocated - actual
            elif actual > allocated:
                deficit[section] = actual - allocated

        # Calculate sacred buffer (never reallocate)

        # Total available for reallocation (surplus - sacred buffer)
        total_surplus = sum(surplus.values())
        available_for_reallocation = max(0, total_surplus)

        if available_for_reallocation <= 0 or not deficit:
            return budget

        # Reallocate based on priority order
        priority_map = {name: i for i, name in enumerate(reallocation_config.reallocation_priority)}
        deficit_sections = sorted(deficit.keys(), key=lambda s: priority_map.get(s, 999))

        # Distribute available surplus proportionally to deficit
        total_deficit = sum(deficit.values())
        reallocated = {}

        for section in deficit_sections:
            if available_for_reallocation <= 0:
                break

            # Proportional share of available surplus
            section_deficit = deficit[section]
            allocation = min(
                section_deficit,
                int(available_for_reallocation * (section_deficit / total_deficit))
            )

            reallocated[section] = allocation
            available_for_reallocation -= allocation

        # Create new budget with reallocated limits
        return ContextBudget(
            total_context_limit=budget.total_context_limit,
            max_output_tokens=budget.max_output_tokens,
            safety_buffer=budget.safety_buffer,
            available_input_tokens=budget.available_input_tokens,

            # Reallocated limits
            system_prompt_limit=budget.system_prompt_limit + reallocated.get("system", 0),
            latest_tools_limit=budget.latest_tools_limit,  # Keep original (tools now in recent)
            recent_messages_limit=budget.recent_messages_limit + reallocated.get("recent", 0),
            marked_messages_limit=budget.marked_messages_limit + reallocated.get("marked", 0),
            summary_limit=budget.summary_limit + reallocated.get("summaries", 0),
            reserved_tokens=budget.reserved_tokens,

            target_usage_after_compaction=budget.target_usage_after_compaction,
            max_usage_before_compaction=budget.max_usage_before_compaction,
        )

    async def enforce_budget(
        self,
        sections: Dict[str, List[BaseMessage]],
        budget: ContextBudget,
        model_metadata: ModelMetadata,
        reallocation_config: Optional["DynamicReallocationConfig"] = None,
        token_cache: Optional[MessageTokenCache] = None,
    ) -> Dict[str, List[BaseMessage]]:
        """
        Enforce budget constraints on classified messages (v2.5).

        v2.5 changes:
        - Dynamic budget: if recent contains latest tool sequence, adds latest_tools_limit
        - No separate latest_tools section handling
        - Uses pre-computed tool boundaries from classifier for efficiency

        Uses MessageTokenCache for O(n) token counting across all sections instead of
        counting each section separately (eliminates redundant token counting).

        Args:
            sections: Classified message sections
            budget: Context budget
            model_metadata: Model metadata for token counting
            reallocation_config: Dynamic reallocation configuration (v2.0)
            token_cache: Optional pre-computed token cache for all messages
                - If None, creates caches per section as needed
                - If provided, should contain ALL messages across ALL sections

        Returns:
            Sections with budget enforced

        Raises:
            ContextBudgetError: If system prompt exceeds limit
        """
        # v2.5: Dynamic budget adjustment - if recent contains latest tool sequence, add tool budget
        if self.classifier and getattr(self.classifier, 'has_latest_tool_in_recent', False):
            # Create new budget with expanded recent limit
            budget = ContextBudget(
                **budget.model_dump()
            )
            budget.recent_messages_limit = budget.recent_messages_limit + budget.latest_tools_limit

        # Create individual token caches for each section if master cache not provided
        # This avoids redundant token counting within each section's operations
        section_caches = {}
        if token_cache is None:
            # Count tokens for each section and create cache
            for section, messages in sections.items():
                if messages:
                    section_caches[section] = MessageTokenCache(messages, model_metadata)
        
        # Count tokens for each section (using cache if available)
        token_counts = {}
        for section, messages in sections.items():
            if not messages:
                token_counts[section] = 0
            elif section in section_caches:
                token_counts[section] = section_caches[section].get_total()
            else:
                # Fallback to regular counting if no cache
                token_counts[section] = count_tokens(messages, model_metadata)

        # v2.0: Dynamic budget reallocation
        if reallocation_config and reallocation_config.enabled:
            actual_usage = {
                "system": token_counts.get("system", 0),
                "recent": token_counts.get("recent", 0),
                "marked": token_counts.get("marked", 0),
                "summaries": token_counts.get("summaries", 0),
            }
            budget = self.reallocate_budget(budget, actual_usage, reallocation_config)

        # 1. Enforce system prompt limit (hard fail)
        if token_counts["system"] > budget.system_prompt_limit:
            raise ContextBudgetError(
                f"System prompt ({token_counts['system']} tokens) exceeds "
                f"limit ({budget.system_prompt_limit} tokens). "
                f"Reduce system prompt size or increase context window."
            )

        # 2. Enforce recent messages limit (includes tools, dynamic budget already applied)
        if token_counts["recent"] > budget.recent_messages_limit:
            # Binary search to find max messages that fit (use cache if available)
            recent_cache = section_caches.get("recent")
            max_count = await binary_search_message_count(
                messages=sections["recent"],
                max_tokens=budget.recent_messages_limit,
                model_metadata=model_metadata,
                token_cache=recent_cache,
            )

            if max_count > 0:
                # v2.2: Trim while respecting tool call atomic groups
                sections["recent"], overflow = MessageClassifier.trim_messages_respecting_tool_groups(
                    messages=sections["recent"],
                    keep_count=max_count,
                    from_end=True,  # Keep most recent
                )
                # Move overflow to historical for summarization
                sections["historical"].extend(overflow)
            else:
                # Can't fit even 1 recent message
                sections["historical"].extend(sections["recent"])
                sections["recent"] = []

        # 4. Enforce marked messages limit (compress oldest)
        if token_counts["marked"] > budget.marked_messages_limit:
            # v2.2: Split while respecting tool call atomic groups (use cache if available)
            marked_cache = section_caches.get("marked")
            kept_marked, overflow = await MessageClassifier.split_messages_by_budget_respecting_tool_groups(
                messages=sections["marked"],
                budget=budget.marked_messages_limit,
                model_metadata=model_metadata,
                keep_newest=True,  # Preserve recent marked messages
                token_cache=marked_cache,
            )

            # v2.1: Prepare overflowed marked messages for compaction
            for msg in overflow:
                # Remove preservation flags so they can be ingested/compacted
                if get_message_metadata(msg, "preserve"):
                    set_message_metadata(msg, "preserve", None)
                if get_message_metadata(msg, "dont_summarize"):
                    set_message_metadata(msg, "dont_summarize", None)

                # Mark as originally marked for tracking
                set_message_metadata(msg, "originally_marked", True)
                set_message_metadata(msg, "needs_compression", True)

            sections["marked"] = kept_marked
            # Add overflow to historical for compaction
            sections["historical"].extend(overflow)

        # 5. Enforce summary limit (will be handled by strategies)
        # Strategies are responsible for merging summaries if they exceed limit

        return sections
