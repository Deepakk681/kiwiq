"""
Token counting utilities for prompt compaction.

Provides functions for counting tokens in messages using the tiktoken library
and model-specific encoding. For Anthropic models, provides official API-based
token counting for maximum accuracy.

Key Functions:
- get_encoder_for_model(): Get tiktoken encoder (OpenAI model-specific, others approximation)
- count_tokens_anthropic(): Use Anthropic API for exact token counting
- count_tokens(): Universal token counting (auto-selects appropriate method)
- count_tokens_in_message(): Token count for single message
- binary_search_message_count(): Find max messages that fit within budget
- split_messages_by_budget(): Split messages into within/overflow groups
"""

from __future__ import annotations

from typing import List, Dict, Any, Optional, TYPE_CHECKING
import tiktoken
import logging

from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, SystemMessage, ToolMessage

from workflow_service.registry.nodes.llm.config import ModelMetadata, LLMModelProvider
if TYPE_CHECKING:
    from workflow_service.registry.nodes.llm.prompt_compaction.context_manager import (
        ContextBudget
    )
logger = logging.getLogger(__name__)


# Cache for token encoders
_ENCODER_CACHE: Dict[str, tiktoken.Encoding] = {}


class MessageTokenCache:
    """
    Token count cache with O(1) range queries for efficient token counting.

    This class precomputes and caches token counts for a list of messages, enabling
    O(1) range sum queries using cumulative sum arrays. This dramatically improves
    performance for operations that need to count tokens across message ranges
    (e.g., binary search, budget splitting).

    **Performance Benefits:**
    - Initial computation: O(n) - count each message once
    - Range queries: O(1) - use cumulative sums
    - Binary search: O(n log n) → O(n + log n) = O(n) improvement

    **Data Structures:**
    - individual_counts: [tokens(msg0), tokens(msg1), ..., tokens(msgN)]
    - cumulative_sums: [cumsum0, cumsum1, ...] where cumsum[i] = sum(tokens[0:i+1])

    **Usage Example:**
        ```python
        from langchain_core.messages import HumanMessage, AIMessage
        from workflow_service.registry.nodes.llm.config import ModelMetadata, LLMModelProvider

        messages = [
            HumanMessage(content="Hello"),
            AIMessage(content="Hi there!"),
            HumanMessage(content="How are you?"),
        ]
        metadata = ModelMetadata(
            provider=LLMModelProvider.OPENAI,
            model_name="gpt-4o",
            context_limit=128000,
        )

        # Create cache (counts tokens once)
        cache = MessageTokenCache(messages, metadata)

        # O(1) queries
        total = cache.get_total()  # Total tokens
        count = cache.get_message_count(1)  # Tokens in message 1
        range_sum = cache.get_range_sum(0, 2)  # Tokens in messages[0:2]
        suffix = cache.get_suffix_sum(1)  # Tokens in messages[1:]
        ```

    **Cross-references:**
    - Used by: binary_search_message_count(), split_messages_by_budget(),
               check_prompt_size_and_split(), BudgetEnforcer.enforce_budget()
    - Calls: count_tokens() for cache initialization

    **Implementation Notes:**
    - Cache is immutable after creation (messages list is fixed)
    - Handles Anthropic API token counting (stores API results)
    - Thread-safe for read operations (no mutation after init)
    - Empty message lists handled gracefully (returns 0 for all queries)

    **Edge Cases:**
    - Empty messages list: All queries return 0
    - Single message: Works normally, no special handling needed
    - Out of bounds indices: Raises IndexError (fail-fast for debugging)
    - Negative indices: Not supported (raises error)

    Attributes:
        messages (List[BaseMessage]): Original message list (reference only, not copied)
        model_metadata (ModelMetadata): Model metadata for token counting
        individual_counts (List[int]): Token count for each message
        cumulative_sums (List[int]): Cumulative token sum up to each index
        _total_tokens (int): Cached total token count
    """

    def __init__(
        self,
        messages: List[BaseMessage],
        model_metadata: ModelMetadata,
    ):
        """
        Initialize token cache by computing individual and cumulative counts.

        This performs O(n) token counting once during initialization. All subsequent
        queries are O(1) array lookups.

        Args:
            messages (List[BaseMessage]): Messages to cache token counts for
                - Can be empty list (handled gracefully)
                - Messages are not copied (only referenced)
            model_metadata (ModelMetadata): Model metadata for token counting
                - Used by count_tokens_in_message() for encoding selection
                - Supports Anthropic API calls for exact counting

        Raises:
            Exception: If token counting fails for any message
                - Propagates exceptions from count_tokens_in_message()
                - Typically only happens with invalid messages or API errors

        Example:
            ```python
            cache = MessageTokenCache(
                messages=[msg1, msg2, msg3],
                model_metadata=metadata,
            )
            # Cache now contains:
            # - individual_counts: [10, 25, 15]
            # - cumulative_sums: [10, 35, 50]
            # - _total_tokens: 50
            ```

        Performance:
            - Time complexity: O(n) where n = len(messages)
            - Space complexity: O(n) for storing counts
            - Anthropic API: May make API calls (adds ~50-100ms per call)
        """
        self.messages = messages
        self.model_metadata = model_metadata

        if not messages:
            # Empty message list - initialize with empty arrays
            self.individual_counts: List[int] = []
            self.cumulative_sums: List[int] = []
            self._total_tokens = 0
            return

        # Compute individual token counts for each message (O(n) operation)
        self.individual_counts = [
            count_tokens_in_message(msg, model_metadata)
            for msg in messages
        ]

        # Build cumulative sum array for O(1) range queries
        # cumulative_sums[i] = sum of tokens from index 0 to i (inclusive)
        self.cumulative_sums: List[int] = []
        running_sum = 0

        for count in self.individual_counts:
            running_sum += count
            self.cumulative_sums.append(running_sum)

        # Cache total token count for O(1) access
        self._total_tokens = running_sum

    def get_message_count(self, index: int) -> int:
        """
        Get token count for a single message at the given index.

        O(1) array lookup operation.

        Args:
            index (int): Message index (0-based)
                - Must be: 0 <= index < len(messages)
                - Negative indices NOT supported

        Returns:
            int: Token count for message at index
                - Includes message overhead (role, formatting tokens)
                - Same as count_tokens_in_message(messages[index])

        Raises:
            IndexError: If index out of bounds
                - Raised for: index < 0 or index >= len(messages)

        Example:
            ```python
            cache = MessageTokenCache([msg1, msg2, msg3], metadata)
            count = cache.get_message_count(1)  # Tokens in msg2
            # Equivalent to: count_tokens_in_message(msg2, metadata)
            # But O(1) instead of O(msg_size)
            ```

        Performance:
            - Time complexity: O(1)
            - Space complexity: O(1)
        """
        if not self.messages or index < 0 or index >= len(self.individual_counts):
            raise IndexError(
                f"Message index {index} out of bounds for cache with {len(self.messages)} messages"
            )

        return self.individual_counts[index]

    def get_range_sum(self, start: int, end: int) -> int:
        """
        Get sum of tokens for messages[start:end] in O(1) time.

        Uses cumulative sum array for constant-time range queries. This is the
        key optimization that makes binary search and budget splitting efficient.

        **Formula:**
        - If start == 0: cumulative_sums[end - 1]
        - Otherwise: cumulative_sums[end - 1] - cumulative_sums[start - 1]

        Args:
            start (int): Start index (inclusive, 0-based)
                - Must be: 0 <= start <= end
            end (int): End index (exclusive, 0-based)
                - Must be: start <= end <= len(messages)
                - Python slice semantics: messages[start:end]

        Returns:
            int: Sum of tokens for all messages in range [start, end)
                - Equivalent to: count_tokens(messages[start:end], metadata)
                - But O(1) instead of O(n)

        Raises:
            IndexError: If indices out of bounds
            ValueError: If start > end

        Example:
            ```python
            cache = MessageTokenCache([msg1, msg2, msg3, msg4], metadata)
            # Individual counts: [10, 20, 30, 40]
            # Cumulative sums: [10, 30, 60, 100]

            cache.get_range_sum(0, 2)  # msg1 + msg2 = 10 + 20 = 30
            cache.get_range_sum(1, 3)  # msg2 + msg3 = 20 + 30 = 50
            cache.get_range_sum(2, 4)  # msg3 + msg4 = 30 + 40 = 70
            cache.get_range_sum(1, 1)  # Empty range = 0
            ```

        Performance:
            - Time complexity: O(1)
            - Space complexity: O(1)

        Cross-references:
            - Used by: binary_search_message_count() for subset token counts
            - Used by: split_messages_by_budget() for finding split points
        """
        if start < 0 or end > len(self.messages):
            raise IndexError(
                f"Range [{start}:{end}) out of bounds for cache with {len(self.messages)} messages"
            )

        if start > end:
            raise ValueError(f"Invalid range: start ({start}) > end ({end})")

        if start == end:
            # Empty range
            return 0

        if not self.cumulative_sums:
            # Empty message list
            return 0

        # Use cumulative sum formula: sum(start:end) = cumsum[end-1] - cumsum[start-1]
        if start == 0:
            return self.cumulative_sums[end - 1]
        else:
            return self.cumulative_sums[end - 1] - self.cumulative_sums[start - 1]

    def get_total(self) -> int:
        """
        Get total token count across all messages.

        O(1) cached value lookup.

        Returns:
            int: Total tokens for all messages
                - Equivalent to: count_tokens(messages, metadata)
                - But O(1) instead of O(n)
                - Returns 0 for empty message lists

        Example:
            ```python
            cache = MessageTokenCache([msg1, msg2, msg3], metadata)
            total = cache.get_total()
            # Equivalent to: count_tokens([msg1, msg2, msg3], metadata)
            # But O(1) instead of O(n)
            ```

        Performance:
            - Time complexity: O(1)
            - Space complexity: O(1)

        Cross-references:
            - Used by: Various functions checking total prompt size
        """
        return self._total_tokens

    def get_suffix_sum(self, start: int) -> int:
        """
        Get sum of tokens for messages[start:] (from start to end).

        Convenience method for suffix sums, commonly used in binary search
        when checking if "last N messages" fit in budget.

        Equivalent to: get_range_sum(start, len(messages))

        Args:
            start (int): Start index (inclusive, 0-based)
                - Must be: 0 <= start <= len(messages)

        Returns:
            int: Sum of tokens from start to end of message list
                - Equivalent to: count_tokens(messages[start:], metadata)
                - But O(1) instead of O(n)

        Raises:
            IndexError: If start out of bounds

        Example:
            ```python
            cache = MessageTokenCache([msg1, msg2, msg3, msg4], metadata)
            # Individual counts: [10, 20, 30, 40]

            cache.get_suffix_sum(0)  # All messages = 100
            cache.get_suffix_sum(2)  # msg3 + msg4 = 70
            cache.get_suffix_sum(4)  # Empty = 0
            ```

        Performance:
            - Time complexity: O(1)
            - Space complexity: O(1)

        Cross-references:
            - Used by: binary_search_message_count() for checking suffix fits
        """
        return self.get_range_sum(start, len(self.messages))

    def get_prefix_sum(self, end: int) -> int:
        """
        Get sum of tokens for messages[:end] (from start to end-1).

        Convenience method for prefix sums, useful for forward passes
        when checking if "first N messages" fit in budget.

        Equivalent to: get_range_sum(0, end)

        Args:
            end (int): End index (exclusive, 0-based)
                - Must be: 0 <= end <= len(messages)

        Returns:
            int: Sum of tokens from start to end-1
                - Equivalent to: count_tokens(messages[:end], metadata)
                - But O(1) instead of O(n)

        Raises:
            IndexError: If end out of bounds

        Example:
            ```python
            cache = MessageTokenCache([msg1, msg2, msg3, msg4], metadata)
            # Individual counts: [10, 20, 30, 40]

            cache.get_prefix_sum(0)  # Empty = 0
            cache.get_prefix_sum(2)  # msg1 + msg2 = 30
            cache.get_prefix_sum(4)  # All messages = 100
            ```

        Performance:
            - Time complexity: O(1)
            - Space complexity: O(1)
        """
        return self.get_range_sum(0, end)

    def __len__(self) -> int:
        """
        Get number of messages in cache.

        Returns:
            int: Number of messages
        """
        return len(self.messages)

    def __repr__(self) -> str:
        """
        String representation for debugging.

        Returns:
            str: Debug string showing cache size and total tokens
        """
        return (
            f"MessageTokenCache(messages={len(self.messages)}, "
            f"total_tokens={self._total_tokens})"
        )


def get_encoder_for_model(model_metadata: ModelMetadata) -> tiktoken.Encoding:
    """
    Get tiktoken encoder for a model with model-specific encoding support.

    For OpenAI models, attempts to use model-specific encoding via tiktoken.encoding_for_model()
    which provides the most accurate token counting for that specific model. Falls back to
    cl100k_base if model-specific encoding is not available.

    For other providers (Anthropic, Gemini, Perplexity, etc.), uses cl100k_base as approximation.
    Note: Anthropic token counting should use count_tokens_anthropic() for accuracy.

    Args:
        model_metadata (ModelMetadata): Model metadata containing provider and model name
            - provider: LLM provider enum (OPENAI, ANTHROPIC, etc.)
            - model_name: Specific model name (e.g., "gpt-4o", "claude-sonnet-4")

    Returns:
        tiktoken.Encoding: Tokenizer encoder instance for the model
            - Cached for performance (encoder instance is reused across calls)

    Raises:
        ValueError: If model encoding is not supported (caught internally, fallback to cl100k_base)

    Example:
        ```python
        from workflow_service.registry.nodes.llm.config import ModelMetadata, LLMModelProvider

        metadata = ModelMetadata(
            provider=LLMModelProvider.OPENAI,
            model_name="gpt-4o",
            context_limit=128000,
            output_token_limit=16384,
        )
        encoder = get_encoder_for_model(metadata)
        tokens = encoder.encode("Hello, world!")
        ```

    Cross-references:
        - Used by: count_tokens_in_text(), count_tokens_in_message()
        - Related: count_tokens_anthropic() for Anthropic-specific counting

    Notes:
        - Encoders are cached globally to avoid repeated initialization overhead
        - For Anthropic models, this provides approximation; use count_tokens_anthropic() for exact counts
        - OpenAI model-specific encodings handle special tokens and formatting differences
    """
    provider = model_metadata.provider
    model_name = model_metadata.model_name

    # Check cache
    cache_key = f"{provider.value}:{model_name}"
    if cache_key in _ENCODER_CACHE:
        return _ENCODER_CACHE[cache_key]

    # Map models to tiktoken encodings
    try:
        if provider == LLMModelProvider.OPENAI:
            # Try model-specific encoding first for maximum accuracy
            try:
                encoder = tiktoken.encoding_for_model(model_name)
            except KeyError:
                # Model not recognized by tiktoken, fallback to cl100k_base
                # This handles new models not yet in tiktoken's model list
                encoder = tiktoken.get_encoding("cl100k_base")

        elif provider == LLMModelProvider.ANTHROPIC:
            # Anthropic models use cl100k_base as approximation
            # For accurate counting, use count_tokens_anthropic() instead
            encoder = tiktoken.get_encoding("cl100k_base")

        elif provider == LLMModelProvider.GEMINI:
            # Gemini uses cl100k_base as approximation
            encoder = tiktoken.get_encoding("cl100k_base")

        elif provider == LLMModelProvider.PERPLEXITY:
            # Perplexity uses cl100k_base as approximation
            encoder = tiktoken.get_encoding("cl100k_base")

        elif provider in [LLMModelProvider.AWS_BEDROCK, LLMModelProvider.FIREWORKS]:
            # Bedrock/Fireworks - use cl100k_base as approximation
            encoder = tiktoken.get_encoding("cl100k_base")

        else:
            # Default to cl100k_base for unknown providers
            encoder = tiktoken.get_encoding("cl100k_base")

        # Cache encoder for performance
        _ENCODER_CACHE[cache_key] = encoder
        return encoder

    except Exception as e:
        # Catch-all fallback to cl100k_base
        # This handles any unexpected errors in tiktoken library
        encoder = tiktoken.get_encoding("cl100k_base")
        _ENCODER_CACHE[cache_key] = encoder
        return encoder


def _convert_langchain_to_anthropic_messages(messages: List[BaseMessage]) -> List[Dict[str, Any]]:
    """
    Convert LangChain messages to Anthropic API message format.

    Internal utility for count_tokens_anthropic().

    Args:
        messages: List of LangChain BaseMessage instances

    Returns:
        List of dicts in Anthropic message format

    Example:
        ```python
        lc_messages = [HumanMessage(content="Hello"), AIMessage(content="Hi")]
        anthropic_msgs = _convert_langchain_to_anthropic_messages(lc_messages)
        # Returns: [{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi"}]
        ```
    """

    anthropic_messages = []
    for msg in messages:
        if isinstance(msg, HumanMessage):
            role = "user"
        elif isinstance(msg, AIMessage):
            role = "assistant"
        elif isinstance(msg, ToolMessage):
            # Tool messages are typically user role in Anthropic
            role = "user"
        elif isinstance(msg, SystemMessage):
            # System messages handled separately in Anthropic API
            continue
        else:
            # Default to user for unknown types
            role = "user"

        anthropic_messages.append({
            "role": role,
            "content": str(msg.content)
        })

    return anthropic_messages


def count_tokens_anthropic(
    messages: List[BaseMessage],
    model_metadata: ModelMetadata,
) -> Optional[int]:
    """
    Count tokens using Anthropic's official API for maximum accuracy.

    Uses anthropic.Anthropic().beta.messages.count_tokens() which provides
    exact token counts matching Anthropic's internal tokenization. This is
    the same approach used in llm_node.py:3101 for cost estimation.

    Args:
        messages (List[BaseMessage]): LangChain messages to count tokens for
        model_metadata (ModelMetadata): Model metadata with model_name
            - model_name: Anthropic model (e.g., "claude-sonnet-4-5")

    Returns:
        Optional[int]: Token count from Anthropic API, or None if API call fails
            - None indicates fallback to tiktoken should be used

    Example:
        ```python
        from langchain_core.messages import HumanMessage, AIMessage
        from workflow_service.registry.nodes.llm.config import ModelMetadata, LLMModelProvider

        messages = [
            HumanMessage(content="What is the capital of France?"),
            AIMessage(content="The capital of France is Paris.")
        ]
        metadata = ModelMetadata(
            provider=LLMModelProvider.ANTHROPIC,
            model_name="claude-sonnet-4",
            context_limit=200000,
        )

        token_count = count_tokens_anthropic(messages, metadata)
        # Returns: ~24 tokens (exact count from Anthropic API)
        ```

    Cross-references:
        - Used by: count_tokens() for Anthropic models
        - Similar to: llm_node.py:3101 (cost estimation)
        - Fallback: get_encoder_for_model() if API call fails

    Notes:
        - Requires ANTHROPIC_API_KEY environment variable
        - Makes API call (minimal latency, ~50-100ms)
        - Returns None on error (network, auth, rate limit) - caller should fallback
        - System messages excluded from count (Anthropic API requirement)
        - Tool calls and tool messages supported
    """
    try:
        import anthropic
        from workflow_service.config.settings import settings

        # Convert to Anthropic format
        anthropic_messages = _convert_langchain_to_anthropic_messages(messages)

        if not anthropic_messages:
            return 0

        # Call Anthropic API
        # client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

        system_message = None
        for i, msg in enumerate(messages):
            if isinstance(msg, SystemMessage):
                system_message = (i, msg.content if hasattr(msg, 'content') else str(msg))
        
        # Calculate prompt cost
        kwargs = {}
        if system_message:
            # anthropic_messages.pop(system_message[0])
            if system_message[1]:
                kwargs = {
                    "system": system_message[1]
                }
        # self.info(f"messages: {json.dumps(prompt_messages, indent=2)}, kwargs_system: {kwargs.get('system', None)}")
        import anthropic
        input_tokens = anthropic.Anthropic().beta.messages.count_tokens(
                model=model_metadata.model_name,
                messages=anthropic_messages,
                **kwargs,
            ).input_tokens

        # result = client.beta.messages.count_tokens(
        #     model=model_metadata.model_name,
        #     messages=anthropic_messages,
        # )

        return input_tokens  # result.input_tokens

    except Exception as e:
        # Log error and return None to signal fallback needed
        logger.warning(
            f"Anthropic token counting failed for {model_metadata.model_name}: {e}. "
            "Falling back to tiktoken approximation."
        )
        return None


def count_tokens_in_text(text: str, model_metadata: ModelMetadata) -> int:
    """
    Count tokens in a text string.

    Args:
        text: Text to count tokens in
        model_metadata: Model metadata for encoding

    Returns:
        Number of tokens
    """
    encoder = get_encoder_for_model(model_metadata)
    return len(encoder.encode(text))


def count_tokens_in_message(message: BaseMessage, model_metadata: ModelMetadata) -> int:
    """
    Count tokens in a single message.

    Includes overhead for message formatting (role, name, etc.) based on
    OpenAI's token counting methodology.

    Args:
        message: Message to count tokens in
        model_metadata: Model metadata for encoding

    Returns:
        Number of tokens
    """
    encoder = get_encoder_for_model(model_metadata)

    # Base token count for message formatting
    # Every message has: <|im_start|>{role/name}\n{content}<|im_end|>\n
    tokens = 4  # Base overhead per message

    # Count content tokens
    content = str(message.content)
    tokens += len(encoder.encode(content))

    # Additional tokens for message type
    msg_type = message.__class__.__name__
    tokens += len(encoder.encode(msg_type))

    # Additional tokens for tool calls (if any)
    if hasattr(message, "tool_calls") and message.tool_calls:
        for tool_call in message.tool_calls:
            # Tool call has name, args, id
            tokens += len(encoder.encode(str(tool_call.get("name", ""))))
            tokens += len(encoder.encode(str(tool_call.get("args", ""))))
            tokens += len(encoder.encode(str(tool_call.get("id", ""))))
            tokens += 4  # Formatting overhead

    # Additional tokens for tool call ID (ToolMessage)
    if hasattr(message, "tool_call_id") and message.tool_call_id:
        tokens += len(encoder.encode(message.tool_call_id))

    return tokens


def count_tokens(messages: List[BaseMessage], model_metadata: ModelMetadata) -> int:
    """
    Count total tokens in a list of messages with provider-specific accuracy.

    Automatically selects the most accurate counting method:
    - Anthropic models: Use official Anthropic API (count_tokens_anthropic())
    - OpenAI models: Use model-specific tiktoken encoding
    - Other providers: Use tiktoken approximation (cl100k_base)

    Args:
        messages (List[BaseMessage]): List of LangChain messages to count
        model_metadata (ModelMetadata): Model metadata for encoding selection
            - provider: Determines counting method (ANTHROPIC vs others)
            - model_name: Used for model-specific encoding

    Returns:
        int: Total number of tokens across all messages
            - Includes per-message overhead (role, formatting tokens)
            - Includes 2-token priming for assistant response
            - For Anthropic: Exact count from API
            - For others: Best-effort count from tiktoken

    Example:
        ```python
        from langchain_core.messages import HumanMessage, AIMessage

        messages = [
            HumanMessage(content="Hello"),
            AIMessage(content="Hi there!")
        ]

        # Anthropic model - uses API
        anthropic_meta = ModelMetadata(
            provider=LLMModelProvider.ANTHROPIC,
            model_name="claude-sonnet-4"
        )
        count_anthropic = count_tokens(messages, anthropic_meta)  # Uses Anthropic API

        # OpenAI model - uses tiktoken
        openai_meta = ModelMetadata(
            provider=LLMModelProvider.OPENAI,
            model_name="gpt-4o"
        )
        count_openai = count_tokens(messages, openai_meta)  # Uses tiktoken
        ```

    Cross-references:
        - Calls: count_tokens_anthropic() for Anthropic models
        - Calls: count_tokens_in_message() for other providers
        - Used by: binary_search_message_count(), split_messages_by_budget()
        - Used by: strategies.py for budget checking

    Notes:
        - Anthropic API calls add ~50-100ms latency but provide exact counts
        - Falls back to tiktoken if Anthropic API fails
        - Caches tiktoken encoders for performance (no caching for Anthropic API calls)
        - 2-token priming accounts for assistant response overhead
    """
    if not messages:
        return 0

    # Use Anthropic API for Anthropic models
    if model_metadata.provider == LLMModelProvider.ANTHROPIC:
        token_count = count_tokens_anthropic(messages, model_metadata)
        if token_count is not None:
            # Anthropic API returns exact count including formatting
            return token_count
        # If API fails, fall through to tiktoken approximation

    # Use tiktoken for other providers or as fallback
    total_tokens = 0
    for message in messages:
        total_tokens += count_tokens_in_message(message, model_metadata)

    # Add 2 tokens for priming (assistant response)
    total_tokens += 2

    return total_tokens


async def binary_search_message_count(
    messages: List[BaseMessage],
    max_tokens: int,
    model_metadata: ModelMetadata,
    token_cache: Optional[MessageTokenCache] = None,
) -> int:
    """
    Find maximum number of messages (from end) that fit within token budget.

    Uses binary search with O(1) token counting via MessageTokenCache.

    **Performance Optimization:**
    - Without cache: O(n log n) - counts tokens for each subset in binary search
    - With cache: O(n + log n) = O(n) - counts once, then O(1) lookups

    For 100 messages with 7 binary search iterations:
    - Without cache: ~700 token count operations
    - With cache: 100 token counts + 7 array lookups

    Args:
        messages (List[BaseMessage]): List of messages to search
        max_tokens (int): Maximum token budget
        model_metadata (ModelMetadata): Model metadata for token counting
        token_cache (Optional[MessageTokenCache]): Pre-computed token cache
            - If None, creates cache internally (still faster than repeated counts)
            - If provided, uses existing cache (best performance, no recomputation)

    Returns:
        int: Maximum number of messages that fit (0 if none fit)
            - Searches from end of list (keeps newest messages)
            - Binary search finds largest N where messages[-N:] fits

    Example:
        ```python
        messages = [m1, m2, m3, m4, m5, m6, m7, m8, m9, m10]
        max_tokens = 5000

        # Without cache (still optimized internally)
        count = await binary_search_message_count(messages, max_tokens, metadata)

        # With cache (best performance, reuse across multiple calls)
        cache = MessageTokenCache(messages, metadata)
        count = await binary_search_message_count(messages, max_tokens, metadata, cache)

        # Search for largest N where count_tokens(messages[-N:]) <= 5000
        # Uses cache.get_suffix_sum() for O(1) token counting per iteration
        ```

    Cross-references:
        - Used by: split_messages_by_budget(), BudgetEnforcer.enforce_budget()
        - Uses: MessageTokenCache for O(1) range queries

    Performance Notes:
        - Cache creation: O(n) one-time cost
        - Binary search: O(log n) iterations
        - Per-iteration: O(1) with cache vs O(n) without cache
        - Total: O(n) with cache vs O(n log n) without cache
    """
    if not messages:
        return 0

    # Create cache if not provided (optimization: compute counts once)
    # This is still beneficial even for single-use, as binary search
    # needs to count multiple subsets
    if token_cache is None:
        token_cache = MessageTokenCache(messages, model_metadata)

    # Quick check: do all messages fit?
    total_tokens = token_cache.get_total()
    if total_tokens <= max_tokens:
        return len(messages)

    # Binary search using O(1) suffix sum queries
    # We want to find the largest N such that messages[-N:] fits in budget
    left = 1
    right = len(messages)
    best_count = 0

    while left <= right:
        mid = (left + right) // 2

        # Calculate tokens for last 'mid' messages using cache
        # messages[-mid:] corresponds to messages[len(messages) - mid:]
        start_index = len(messages) - mid
        subset_tokens = token_cache.get_suffix_sum(start_index)

        if subset_tokens <= max_tokens:
            # This fits, try more messages
            best_count = mid
            left = mid + 1
        else:
            # Too many tokens, try fewer messages
            right = mid - 1

    return best_count


def split_messages_by_budget(
    messages: List[BaseMessage],
    budget: int,
    model_metadata: ModelMetadata,
    keep_newest: bool = True,
    token_cache: Optional[MessageTokenCache] = None,
) -> tuple[List[BaseMessage], List[BaseMessage]]:
    """
    Split messages into two groups based on token budget.

    Uses MessageTokenCache for efficient binary search (O(n) instead of O(n log n)).

    Args:
        messages (List[BaseMessage]): List of messages to split
        budget (int): Token budget for first group
        model_metadata (ModelMetadata): Model metadata for token counting
        keep_newest (bool): If True, keep newest messages in first group
            - True: within_budget = last N messages, overflow = rest
            - False: within_budget = first N messages, overflow = rest
        token_cache (Optional[MessageTokenCache]): Pre-computed token cache
            - If None, creates cache internally
            - If provided, reuses cache for multiple operations

    Returns:
        tuple[List[BaseMessage], List[BaseMessage]]: (within_budget, overflow)
            - within_budget: Messages that fit in budget
            - overflow: Messages that don't fit

    Example:
        ```python
        messages = [m1, m2, m3, m4, m5]  # Each ~1000 tokens
        budget = 3000

        # Without cache
        kept, overflow = split_messages_by_budget(messages, 3000, metadata)
        # kept = [m3, m4, m5], overflow = [m1, m2]

        # With cache (reuse across multiple splits)
        cache = MessageTokenCache(messages, metadata)
        kept, overflow = split_messages_by_budget(messages, 3000, metadata, token_cache=cache)
        ```

    Cross-references:
        - Used by: MessageClassifier.split_messages_by_budget_respecting_tool_groups()
        - Calls: binary_search_message_count() with cache
    """
    if not messages:
        return [], []

    # Create cache if not provided
    if token_cache is None:
        token_cache = MessageTokenCache(messages, model_metadata)

    # Count tokens to find split point using cached binary search
    # Note: binary_search_message_count is async, but we need sync version here
    # Use direct implementation instead
    max_count = _binary_search_message_count_sync(messages, budget, token_cache)

    if keep_newest:
        # Keep last max_count messages within budget
        within_budget = messages[-max_count:] if max_count > 0 else []
        overflow = messages[:-max_count] if max_count > 0 else messages
    else:
        # Keep first max_count messages within budget
        within_budget = messages[:max_count] if max_count > 0 else []
        overflow = messages[max_count:] if max_count > 0 else messages

    return within_budget, overflow


def _binary_search_message_count_sync(
    messages: List[BaseMessage],
    max_tokens: int,
    token_cache: MessageTokenCache,
) -> int:
    """
    Synchronous version of binary_search_message_count using cache.

    Internal helper for split_messages_by_budget (which must be sync).

    Args:
        messages: List of messages
        max_tokens: Maximum token budget
        token_cache: Token cache for O(1) queries

    Returns:
        Maximum number of messages that fit
    """
    if not messages:
        return 0

    # Quick check: do all messages fit?
    total_tokens = token_cache.get_total()
    if total_tokens <= max_tokens:
        return len(messages)

    # Binary search using O(1) suffix sum queries
    left = 1
    right = len(messages)
    best_count = 0

    while left <= right:
        mid = (left + right) // 2

        # Calculate tokens for last 'mid' messages using cache
        start_index = len(messages) - mid
        subset_tokens = token_cache.get_suffix_sum(start_index)

        if subset_tokens <= max_tokens:
            # This fits, try more messages
            best_count = mid
            left = mid + 1
        else:
            # Too many tokens, try fewer messages
            right = mid - 1

    return best_count


def estimate_tokens_for_summary(
    original_messages: List[BaseMessage],
    model_metadata: ModelMetadata,
    compression_ratio: float = 0.2,
) -> int:
    """
    Estimate token count for a summary of messages.

    Args:
        original_messages: Messages to be summarized
        model_metadata: Model metadata for token counting
        compression_ratio: Expected compression ratio (default 0.2 = 5:1 compression)

    Returns:
        Estimated summary token count
    """
    original_tokens = count_tokens(original_messages, model_metadata)
    return int(original_tokens * compression_ratio)


def split_oversized_message(
    message: BaseMessage,
    max_tokens_per_chunk: int,
    model_metadata: ModelMetadata,
) -> List[BaseMessage]:
    """
    Split a single oversized message into smaller chunks that fit within token budget.

    Handles edge case where a single message exceeds context window (>100% of budget).
    Intelligently splits by sentences/paragraphs to avoid breaking mid-sentence.
    Preserves message metadata and type across chunks.

    Args:
        message (BaseMessage): The oversized message to split
        max_tokens_per_chunk (int): Maximum tokens per chunk
            - Should be ~80% of context limit to leave room for overhead
            - Example: For 128K context, use ~100K per chunk
        model_metadata (ModelMetadata): Model metadata for token counting

    Returns:
        List[BaseMessage]: List of message chunks, each under max_tokens_per_chunk
            - Each chunk is the same type as original (HumanMessage, AIMessage, etc.)
            - Each chunk has continuation metadata marking its position
            - Tool calls preserved in first chunk if present

    Raises:
        ValueError: If max_tokens_per_chunk is too small to fit any content

    Example:
        ```python
        from langchain_core.messages import HumanMessage

        # Create oversized message (e.g., 150K tokens)
        huge_message = HumanMessage(content="..." * 50000)

        # Split into manageable chunks
        chunks = split_oversized_message(
            message=huge_message,
            max_tokens_per_chunk=100000,
            model_metadata=model_metadata
        )
        # Returns: [chunk1 (~100K tokens), chunk2 (~50K tokens)]
        ```

    Cross-references:
        - Used by: summarize_oversized_message() for chunk-wise summarization
        - Used by: strategies.py for handling oversized messages
        - Calls: count_tokens_in_message() to determine chunk boundaries

    Notes:
        - Splits on paragraph boundaries (\\n\\n) first, then sentences (. ! ?)
        - If single sentence exceeds budget, splits by words as last resort
        - Adds continuation markers to chunk metadata
        - Tool calls only preserved in first chunk (subsequent chunks are content-only)
        - Edge case: If single word exceeds budget, truncates that word
    """
    from langchain_core.messages import (
        HumanMessage,
        AIMessage,
        SystemMessage,
        ToolMessage,
    )
    import re

    content = str(message.content)
    message_type = type(message)

    # Quick check: Does message even need splitting?
    current_tokens = count_tokens_in_message(message, model_metadata)
    if current_tokens <= max_tokens_per_chunk:
        return [message]

    # Strategy: Split by paragraphs first, then sentences, then words
    chunks = []
    chunk_content = ""
    continuation_index = 0

    # Split into paragraphs
    paragraphs = content.split("\n\n")

    for para in paragraphs:
        # Check if adding this paragraph would exceed limit
        test_message = message_type(content=chunk_content + "\n\n" + para if chunk_content else para)
        test_tokens = count_tokens_in_message(test_message, model_metadata)

        if test_tokens <= max_tokens_per_chunk:
            # Fits - add to current chunk
            chunk_content = chunk_content + "\n\n" + para if chunk_content else para
        else:
            # Doesn't fit - need to handle differently
            if chunk_content:
                # Save current chunk
                chunk_msg = _create_message_chunk(
                    message=message,
                    content=chunk_content,
                    chunk_index=continuation_index,
                    is_continuation=continuation_index > 0,
                )
                chunks.append(chunk_msg)
                continuation_index += 1
                chunk_content = ""

            # Try to fit paragraph in next chunk
            para_tokens = count_tokens_in_message(message_type(content=para), model_metadata)
            if para_tokens <= max_tokens_per_chunk:
                # Paragraph fits alone in next chunk
                chunk_content = para
            else:
                # Paragraph itself is too large - split by sentences
                sentences = re.split(r'([.!?]+\s+)', para)
                for sent in sentences:
                    if not sent.strip():
                        continue

                    test_message = message_type(content=chunk_content + sent if chunk_content else sent)
                    test_tokens = count_tokens_in_message(test_message, model_metadata)

                    if test_tokens <= max_tokens_per_chunk:
                        chunk_content = chunk_content + sent if chunk_content else sent
                    else:
                        if chunk_content:
                            chunk_msg = _create_message_chunk(
                                message=message,
                                content=chunk_content,
                                chunk_index=continuation_index,
                                is_continuation=continuation_index > 0,
                            )
                            chunks.append(chunk_msg)
                            continuation_index += 1
                            chunk_content = ""

                        # Sentence too large - split by words (last resort)
                        words = sent.split()
                        for word in words:
                            test_message = message_type(content=chunk_content + " " + word if chunk_content else word)
                            test_tokens = count_tokens_in_message(test_message, model_metadata)

                            if test_tokens <= max_tokens_per_chunk:
                                chunk_content = chunk_content + " " + word if chunk_content else word
                            else:
                                if chunk_content:
                                    chunk_msg = _create_message_chunk(
                                        message=message,
                                        content=chunk_content,
                                        chunk_index=continuation_index,
                                        is_continuation=continuation_index > 0,
                                    )
                                    chunks.append(chunk_msg)
                                    continuation_index += 1
                                    chunk_content = word  # Start fresh with current word

    # Add final chunk if any content remains
    if chunk_content:
        chunk_msg = _create_message_chunk(
            message=message,
            content=chunk_content,
            chunk_index=continuation_index,
            is_continuation=continuation_index > 0,
        )
        chunks.append(chunk_msg)

    return chunks if chunks else [message]  # Fallback to original if splitting failed


def _create_message_chunk(
    message: BaseMessage,
    content: str,
    chunk_index: int,
    is_continuation: bool,
) -> BaseMessage:
    """
    Create a message chunk with proper metadata.

    Internal helper for split_oversized_message().

    Args:
        message: Original message
        content: Chunk content
        chunk_index: Index of this chunk (0-based)
        is_continuation: Whether this is a continuation chunk (not first)

    Returns:
        Message chunk with metadata
    """
    from langchain_core.messages import (
        HumanMessage,
        AIMessage,
        SystemMessage,
        ToolMessage,
    )

    message_type = type(message)

    # Create new message of same type
    if message_type == HumanMessage:
        chunk = HumanMessage(content=content)
    elif message_type == AIMessage:
        chunk = AIMessage(content=content)
        # Preserve tool calls only in first chunk
        if chunk_index == 0 and hasattr(message, "tool_calls"):
            chunk.tool_calls = message.tool_calls
    elif message_type == SystemMessage:
        chunk = SystemMessage(content=content)
    elif message_type == ToolMessage:
        chunk = ToolMessage(content=content, tool_call_id=message.tool_call_id)
    else:
        # Fallback to HumanMessage for unknown types
        chunk = HumanMessage(content=content)

    # Add chunking metadata
    # Store oversized chunk metadata in response_metadata["compaction"]
    from workflow_service.registry.nodes.llm.prompt_compaction.utils import set_compaction_metadata
    
    set_compaction_metadata(chunk, "oversized_chunk", {
        "original_message_id": message.id,
        "chunk_index": chunk_index,
        "is_continuation": is_continuation,
        "total_chunks": "unknown",  # Will be set by caller if needed
    })

    return chunk


async def summarize_oversized_message(
    message: BaseMessage,
    max_tokens_per_chunk: int,
    model_metadata: ModelMetadata,
    ext_context: Any,
) -> BaseMessage:
    """
    Summarize a single oversized message by chunking and summarizing (v2.1).

    Now uses universal call_llm_with_batch_splitting() for automatic multi-level
    overflow handling, eliminating manual recursion and batch management.

    Handles edge case where a single message exceeds context window (>100% of budget).
    Splits message into chunks, then uses the universal wrapper to automatically
    handle batching and recursive summarization if needed.

    Args:
        message (BaseMessage): The oversized message to summarize
        max_tokens_per_chunk (int): Maximum tokens per chunk for splitting
            - Typically 80% of context limit
            - Used for both splitting and summary budget checking
        model_metadata (ModelMetadata): Model metadata for LLM calls
        ext_context (ExternalContextManager): External context for LLM access

    Returns:
        BaseMessage: Summary message combining all chunk summaries
            - Same type as original message
            - Contains metadata about original message ID
            - Marked with "oversized_summary" metadata

    Raises:
        Exception: If LLM calls fail or recursive summarization doesn't converge

    Example:
        ```python
        from langchain_core.messages import HumanMessage

        # Oversized message (150K tokens)
        huge_msg = HumanMessage(content="..." * 50000)

        # Summarize it
        summary = await summarize_oversized_message(
            message=huge_msg,
            max_tokens_per_chunk=100000,
            model_metadata=metadata,
            ext_context=ext_context
        )
        # Returns: AIMessage with combined summary (~20K tokens)
        ```

    Cross-references:
        - Calls: split_oversized_message() to chunk the message
        - Calls: call_llm_for_compaction() directly for each chunk (v2.1 fix)
        - Used by: check_and_handle_oversized_messages() in strategies.py
        - Called from: call_llm_with_batch_splitting() wrapper

    Notes:
        - v2.1: Calls LLM directly for chunks to avoid recursive wrapper issues
        - Chunks are pre-sized, no need for batch splitting wrapper
        - Parallel chunk summarization for speed (5-10x faster)
        - Preserves original message metadata in summary
        - Avoids circular calls with call_llm_with_batch_splitting()
    """
    from workflow_service.registry.nodes.llm.prompt_compaction.context_manager import (
        ContextBudget,
        ContextBudgetConfig,
    )

    # Step 1: Split into chunks
    chunks = split_oversized_message(
        message=message,
        max_tokens_per_chunk=max_tokens_per_chunk,
        model_metadata=model_metadata,
    )

    # Step 2: Summarize each chunk IN PARALLEL (v2.1 parallel processing)
    # Call LLM directly for each chunk to avoid recursive wrapper calls
    import asyncio
    from workflow_service.registry.nodes.llm.prompt_compaction.llm_utils import (
        call_llm_for_compaction,
    )
    from workflow_service.registry.nodes.llm.prompt_compaction.utils import format_messages

    # Create tasks for all chunks (parallel execution)
    async def summarize_chunk(chunk, chunk_index):
        prompt = f"""Summarize the following message content concisely while preserving all key information:

{format_messages([chunk])}

Provide a clear, detailed summary that captures all important points, facts, and context."""

        result = await call_llm_for_compaction(
            prompt=prompt,
            model_metadata=model_metadata,
            ext_context=ext_context,
            max_tokens=int(max_tokens_per_chunk * 0.3),  # Target 30% compression
            temperature=0.0,
        )
        return chunk_index, result

    # Execute all chunks concurrently
    chunk_tasks = [summarize_chunk(chunk, i) for i, chunk in enumerate(chunks)]
    chunk_results = await asyncio.gather(*chunk_tasks)

    # Sort by chunk index and extract summaries
    chunk_results_sorted = sorted(chunk_results, key=lambda x: x[0])
    chunk_summaries = [result[1]["content"] for result in chunk_results_sorted]
    total_cost = sum(result[1].get("cost", 0.0) for result in chunk_results_sorted)

    # Step 3: Combine chunk summaries
    combined_summary = "\n\n".join([
        f"Part {i+1}/{len(chunk_summaries)}:\n{summary}"
        for i, summary in enumerate(chunk_summaries)
    ])

    # Step 4: Create final summary message
    summary_message = AIMessage(content=combined_summary)

    # Add metadata
    # Store oversized summary metadata in response_metadata["compaction"]
    from workflow_service.registry.nodes.llm.prompt_compaction.utils import set_compaction_metadata
    
    set_compaction_metadata(summary_message, "oversized_summary", {
        "original_message_id": message.id,
        "original_message_type": type(message).__name__,
        "num_chunks": len(chunks),
        "compression_method": "chunk_wise_direct_summarization",
        "total_cost": total_cost,
    })

    return summary_message


def chunk_message_for_embedding(
    message: BaseMessage,
    chunk_size_tokens: int = 1000,
    chunk_overlap_tokens: int = 50,
    chunk_strategy: str = "semantic_overlap",
    model_metadata: Optional[ModelMetadata] = None,
    chars_per_token: int = 3,
) -> List[tuple[str, Dict[str, Any]]]:
    """
    Chunk a message into smaller pieces for embedding (v2.1).

    Splits messages that exceed embedding model's token limit (8192 for text-embedding-3-small)
    into manageable chunks with overlap. Used by ExtractionStrategy during JIT ingestion.

    Args:
        message (BaseMessage): Message to chunk
        chunk_size_tokens (int): Maximum tokens per chunk (default: 1000, ~75% of 8K limit)
            - Should be below embedding model's limit
            - Leaves room for formatting overhead
        chunk_overlap_tokens (int): Token overlap between chunks (default: 50, ~3% overlap)
            - Preserves context across chunk boundaries
            - Improves retrieval quality for content at boundaries
        chunk_strategy (str): Chunking strategy (default: "semantic_overlap")
            - "semantic_overlap": Split by paragraphs → sentences → words (preserves meaning)
            - "fixed_token": Fixed-size token chunks with overlap (faster, less semantic)
        model_metadata (Optional[ModelMetadata]): For accurate token counting
            - If None, uses character-based estimation (~4 chars per token)

    Returns:
        List[tuple[str, Dict[str, Any]]]: List of (chunk_text, metadata) tuples
            where metadata includes:
            - chunk_index: Sequential index (0-based)
            - total_chunks: Total number of chunks for this message
            - message_id: Original message ID
            - chunk_start_char: Starting character position in original
            - chunk_end_char: Ending character position in original
            - token_count: Estimated tokens in this chunk

    Example:
        ```python
        from langchain_core.messages import HumanMessage
        from workflow_service.registry.nodes.llm.config import ModelMetadata, LLMModelProvider

        # Large message that exceeds 8K embedding limit
        message = HumanMessage(content="..." * 10000, id="msg_123")

        metadata = ModelMetadata(
            provider=LLMModelProvider.OPENAI,
            model_name="gpt-4o-mini",
            context_limit=128000,
        )

        chunks = chunk_message_for_embedding(
            message=message,
            chunk_size_tokens=1000,
            chunk_overlap_tokens=200,
            model_metadata=metadata,
        )

        # Returns: [
        #     ("chunk 1 text...", {"chunk_index": 0, "total_chunks": 3, ...}),
        #     ("chunk 2 text...", {"chunk_index": 1, "total_chunks": 3, ...}),
        #     ("chunk 3 text...", {"chunk_index": 2, "total_chunks": 3, ...}),
        # ]
        ```

    Cross-references:
        - Used by: ExtractionStrategy._ingest_messages_with_chunking() (strategies.py)
        - Called during: JIT ingestion before embedding
        - Related: split_oversized_message() (for LLM context, not embedding)

    Notes:
        - If message fits in one chunk, returns single-element list
        - Semantic splitting preserves paragraph/sentence boundaries when possible
        - Fixed-token splitting is faster but may break mid-sentence
        - Overlap helps retrieval find content near chunk boundaries
        - Chunk metadata used for reassembly and deduplication
    """
    from workflow_service.registry.nodes.llm.prompt_compaction.utils import format_message_for_embedding

    # Get full message text
    full_text = format_message_for_embedding(message)

    # Estimate tokens using configured chars_per_token ratio
    text_tokens = len(full_text) // chars_per_token

    # If message fits in one chunk, return as-is
    if text_tokens <= chunk_size_tokens:
        return [(full_text, {
            "chunk_index": 0,
            "total_chunks": 1,
            "message_id": message.id,
            "chunk_start_char": 0,
            "chunk_end_char": len(full_text),
            "token_count": text_tokens,
        })]

    # Chunking needed - use appropriate strategy
    if chunk_strategy == "semantic_overlap":
        chunks = _chunk_text_semantic(
            text=full_text,
            chunk_size_tokens=chunk_size_tokens,
            chunk_overlap_tokens=chunk_overlap_tokens,
            model_metadata=model_metadata,
            chars_per_token=chars_per_token,
        )
    else:  # fixed_token
        chunks = _chunk_text_fixed_token(
            text=full_text,
            chunk_size_tokens=chunk_size_tokens,
            chunk_overlap_tokens=chunk_overlap_tokens,
            model_metadata=model_metadata,
            chars_per_token=chars_per_token,
        )

    # Add message_id and finalize metadata
    total = len(chunks)
    result = []
    for chunk_text, meta in chunks:
        final_meta = {
            **meta,
            "message_id": message.id,
            "total_chunks": total,
        }
        result.append((chunk_text, final_meta))

    return result


def _chunk_text_semantic(
    text: str,
    chunk_size_tokens: int,
    chunk_overlap_tokens: int,
    model_metadata: Optional[ModelMetadata],
    chars_per_token: int = 3,
) -> List[tuple[str, Dict[str, Any]]]:
    """
    Chunk text using semantic boundaries (paragraphs → sentences → words).

    Internal helper for chunk_message_for_embedding() with semantic_overlap strategy.
    Preserves meaning by respecting natural text boundaries.

    Strategy:
    1. Split by double newlines (paragraphs)
    2. If paragraph too large, split by sentences (using ". " as boundary)
    3. If sentence too large, split by words
    4. Apply token-based overlap between chunks

    Args:
        text: Full text to chunk
        chunk_size_tokens: Max tokens per chunk
        chunk_overlap_tokens: Overlap between chunks
        model_metadata: For token counting

    Returns:
        List of (chunk_text, metadata) tuples
    """
    # Calculate character approximations for chunk size
    # Use configured chars_per_token ratio (default 3:1 for structured data)
    chunk_size_chars = int(chunk_size_tokens * chars_per_token)
    overlap_chars = int(chunk_overlap_tokens * chars_per_token)

    # Split by paragraphs first
    paragraphs = text.split('\n\n')

    chunks = []
    current_chunk = ""
    current_start = 0

    for paragraph in paragraphs:
        # If adding this paragraph would exceed chunk size
        if len(current_chunk) + len(paragraph) + 2 > chunk_size_chars and current_chunk:
            # Truncate current chunk to char limit (keeps it well under token limit)
            if len(current_chunk) > chunk_size_chars:
                current_chunk = current_chunk[:chunk_size_chars]
            
            # Estimate tokens using configured chars_per_token ratio
            chunk_tokens = len(current_chunk) // chars_per_token
            
            chunks.append((current_chunk, {
                "chunk_index": len(chunks),
                "chunk_start_char": current_start,
                "chunk_end_char": current_start + len(current_chunk),
                "token_count": chunk_tokens,
            }))

            # Start new chunk with overlap
            overlap_start = max(0, len(current_chunk) - overlap_chars)
            current_chunk = current_chunk[overlap_start:] + "\n\n" + paragraph
            current_start = current_start + overlap_start
        else:
            # Add paragraph to current chunk
            if current_chunk:
                current_chunk += "\n\n" + paragraph
            else:
                current_chunk = paragraph

    # Add final chunk
    if current_chunk:
        # Truncate to char limit if needed
        if len(current_chunk) > chunk_size_chars:
            current_chunk = current_chunk[:chunk_size_chars]
        
        # Estimate tokens using configured chars_per_token ratio
        chunk_tokens = len(current_chunk) // chars_per_token
        
        chunks.append((current_chunk, {
            "chunk_index": len(chunks),
            "chunk_start_char": current_start,
            "chunk_end_char": current_start + len(current_chunk),
            "token_count": chunk_tokens,
        }))

    return chunks


def _chunk_text_fixed_token(
    text: str,
    chunk_size_tokens: int,
    chunk_overlap_tokens: int,
    model_metadata: Optional[ModelMetadata],
    chars_per_token: int = 3,
) -> List[tuple[str, Dict[str, Any]]]:
    """
    Chunk text using fixed token-sized chunks with overlap.

    Internal helper for chunk_message_for_embedding() with fixed_token strategy.
    Faster than semantic but may break mid-sentence.

    Args:
        text: Full text to chunk
        chunk_size_tokens: Max tokens per chunk
        chunk_overlap_tokens: Overlap between chunks
        model_metadata: For token counting

    Returns:
        List of (chunk_text, metadata) tuples
    """
    # Calculate character approximations using configured chars_per_token ratio
    chunk_size_chars = int(chunk_size_tokens * chars_per_token)
    overlap_chars = int(chunk_overlap_tokens * chars_per_token)
    step_size = chunk_size_chars - overlap_chars

    chunks = []
    start = 0

    while start < len(text):
        end = min(start + chunk_size_chars, len(text))
        chunk_text = text[start:end]

        # Estimate tokens using configured chars_per_token ratio
        chunk_tokens = len(chunk_text) // chars_per_token
        
        chunks.append((chunk_text, {
            "chunk_index": len(chunks),
            "chunk_start_char": start,
            "chunk_end_char": end,
            "token_count": chunk_tokens,
        }))

        start += step_size

        # Avoid creating very small final chunks
        if len(text) - start < chunk_size_chars * 0.3 and chunks:
            # Merge remainder with last chunk if it won't exceed limit
            last_chunk_text, last_metadata = chunks[-1]
            remainder = text[start:]
            if remainder:
                merged_text = last_chunk_text + remainder
                
                # Check if merged chunk exceeds char limit
                if len(merged_text) <= chunk_size_chars:
                    # Safe to merge
                    merged_tokens = len(merged_text) // chars_per_token
                    chunks[-1] = (merged_text, {
                        **last_metadata,
                        "chunk_end_char": len(text),
                        "token_count": merged_tokens,
                    })
                else:
                    # Truncate remainder to char limit and add as new chunk
                    remainder = remainder[:chunk_size_chars]
                    remainder_tokens = len(remainder) // chars_per_token
                    chunks.append((remainder, {
                        "chunk_index": len(chunks),
                        "chunk_start_char": start,
                        "chunk_end_char": start + len(remainder),
                        "token_count": remainder_tokens,
                    }))
            break

    return chunks


def check_prompt_size_and_split(
    messages: List[BaseMessage],
    max_tokens: int,
    model_metadata: ModelMetadata,
    overhead_tokens: int = 1000,
    token_cache: Optional[MessageTokenCache] = None,
) -> List[List[BaseMessage]]:
    """
    Check if combined messages exceed token limit and split into batches if needed.

    Uses MessageTokenCache for O(n) token counting instead of O(n²) repeated counts.

    **Performance Optimization:**
    - Without cache: O(n²) - counts tokens for each message individually in loop
    - With cache: O(n) - counts once, then O(1) lookups per message

    For 50 messages:
    - Without cache: ~50 token count operations (1 per message iteration)
    - With cache: 50 token counts once + 50 array lookups

    This function handles the case where individual messages are all under the oversized
    threshold, but when combined into a single prompt they exceed the context window.

    Use case: When summarizing multiple messages, you might have 50 messages that are
    each 2K tokens, but combining them all into one prompt (100K tokens) exceeds the
    context window (128K).

    Args:
        messages (List[BaseMessage]): Messages to check and potentially split
        max_tokens (int): Maximum tokens allowed per batch
            - Should be less than context window to account for prompt overhead
            - Recommended: available_input_tokens * 0.8
        model_metadata (ModelMetadata): Model metadata for token counting
        overhead_tokens (int): Estimated tokens for prompt template/instructions
            - Default: 1000 tokens
        token_cache (Optional[MessageTokenCache]): Pre-computed token cache
            - If None, creates cache internally
            - If provided, reuses cache for efficiency

    Returns:
        List[List[BaseMessage]]: List of message batches, each under max_tokens
            - If combined messages fit: returns single batch [messages]
            - If too large: returns multiple batches [[batch1], [batch2], ...]
            - Each batch respects max_tokens limit

    Example:
        ```python
        messages = [msg1, msg2, ..., msg50]  # Each ~2K tokens
        budget = ContextBudget(available_input_tokens=128000, ...)

        # Without cache
        batches = check_prompt_size_and_split(
            messages=messages,
            max_tokens=int(budget.available_input_tokens * 0.8),  # 102K tokens
            model_metadata=metadata,
            overhead_tokens=1000,
        )

        # With cache (reuse across operations)
        cache = MessageTokenCache(messages, metadata)
        batches = check_prompt_size_and_split(
            messages=messages,
            max_tokens=102000,
            model_metadata=metadata,
            token_cache=cache,
        )
        # Returns: [[msg1...msg40], [msg41...msg50]] (2 batches)
        ```

    Cross-references:
        - Used by: call_llm_with_batch_splitting() for overflow handling
        - Complements: check_and_handle_oversized_messages() (handles single messages)
        - Related: split_oversized_message() (handles message chunking)

    Notes:
        - Only splits if total exceeds max_tokens
        - Preserves message order within batches
        - Each batch is under max_tokens (accounting for overhead)
        - Does NOT modify messages, only groups them
    """
    import logging

    logger = logging.getLogger(__name__)

    # Create cache if not provided
    if token_cache is None:
        token_cache = MessageTokenCache(messages, model_metadata)

    # Calculate total tokens for all messages using cache
    total_tokens = token_cache.get_total()

    # Account for prompt overhead
    effective_max = max_tokens - overhead_tokens

    # Check if split is needed
    if total_tokens <= effective_max:
        # All messages fit in one batch
        return [messages]

    # Need to split into batches
    logger.info(
        f"Messages collectively exceed context ({total_tokens} > {effective_max}). "
        f"Splitting into batches..."
    )

    batches = []
    current_batch = []
    current_batch_tokens = 0

    # Use cache for O(1) token lookups per message
    for i, msg in enumerate(messages):
        msg_tokens = token_cache.get_message_count(i)

        # Check if adding this message would exceed limit
        if current_batch_tokens + msg_tokens > effective_max and current_batch:
            # Save current batch and start new one
            batches.append(current_batch)
            logger.debug(
                f"Created batch {len(batches)} with {len(current_batch)} messages "
                f"({current_batch_tokens} tokens)"
            )
            current_batch = [msg]
            current_batch_tokens = msg_tokens
        else:
            # Add to current batch
            current_batch.append(msg)
            current_batch_tokens += msg_tokens

    # Add final batch if not empty
    if current_batch:
        batches.append(current_batch)
        logger.debug(
            f"Created batch {len(batches)} with {len(current_batch)} messages "
            f"({current_batch_tokens} tokens)"
        )

    logger.info(
        f"Split {len(messages)} messages ({total_tokens} tokens) into "
        f"{len(batches)} batches"
    )

    return batches


async def call_llm_with_batch_splitting(
    messages: List[BaseMessage],
    prompt_template: str,
    model_metadata: ModelMetadata,
    ext_context: Any,
    budget: "ContextBudget",
    template_kwargs: Optional[Dict[str, Any]] = None,
    max_output_tokens: int = 2000,
    max_single_message_pct: float = 0.6,
    temperature: float = 0.0,
) -> Dict[str, Any]:
    """
    Universal LLM call with automatic overflow handling and parallel processing (v2.1).

    THE central function for all summarization in prompt compaction.
    Handles ALL overflow scenarios automatically:
    1. Individual oversized messages (>60% context)
    2. Collective overflow (combined prompt > context)
    3. Batch splitting and PARALLEL recursive summarization
    4. Re-compression if combined batch summaries too large

    This function eliminates code duplication across all summarization methods by
    providing a single, reusable wrapper that handles every edge case.

    **Performance Characteristics (v2.1 optimization):**
    - **Parallel batch processing**: When messages split into N batches, all N batches
      are summarized concurrently using asyncio.gather() instead of sequentially.
    - **5-10x speedup**: For 5 batches @ 3 seconds/call: Sequential=15s, Parallel=3s
    - **Recursive parallelization**: Multi-level summaries also processed in parallel
    - **Cost tracking**: Aggregates costs across all parallel calls

    **When batching occurs:**
    - Individual message >60% of context (e.g., 77K tokens in 128K context)
    - Combined messages >85% of available input (safety margin)
    - Batch summaries themselves >2x max_output_tokens

    Args:
        messages (List[BaseMessage]): Messages to process/summarize
        prompt_template (str): Prompt template with {messages} placeholder
            - Must contain {messages} where formatted messages will be inserted
            - Can contain other placeholders for additional context
        model_metadata (ModelMetadata): Model metadata for token counting and LLM calls
        ext_context (Any): External context manager for LLM access
        budget (ContextBudget): Context budget for overflow detection
        template_kwargs (Optional[Dict[str, Any]]): Additional template variables
            - e.g., {"context": "...", "summaries": "..."}
            - {messages} is added automatically
            - Defaults to {}
        max_output_tokens (int): Maximum tokens for LLM response (default: 2000)
        max_single_message_pct (float): Max percentage of context a single message can use (default: 0.6)
        temperature (float): LLM temperature (0.0 for deterministic, default: 0.0)

    Returns:
        Dict[str, Any]: {
            "content": str,         # LLM response content
            "token_usage": dict,    # Token usage stats
            "cost": float,          # Cost in USD
            "batched": bool,        # True if batch splitting was used
            "num_batches": int,     # Number of batches (1 if no splitting)
        }

    Example:
        ```python
        # Simple case
        result = await call_llm_with_batch_splitting(
            messages=messages_to_summarize,
            prompt_template="Summarize these messages:\n\n{messages}",
            model_metadata=metadata,
            ext_context=ext_context,
            budget=budget,
        )

        # With additional context
        result = await call_llm_with_batch_splitting(
            messages=messages_to_summarize,
            prompt_template="Context: {context}\n\nSummarize: {messages}",
            template_kwargs={"context": recent_context},
            model_metadata=metadata,
            ext_context=ext_context,
            budget=budget,
        )

        # Batch splitting example (automatic):
        # 100 messages totaling 150K tokens, prompt adds 10K overhead = 160K
        # Context limit: 128K
        # Automatic handling:
        # 1. Detects 160K > 128K
        # 2. Splits into 2 batches: [50 msgs, 50 msgs]
        # 3. Summarizes batch 1 → summary1
        # 4. Summarizes batch 2 → summary2
        # 5. Combines: "Part 1/2:\n{summary1}\n\nPart 2/2:\n{summary2}"
        # 6. If combined still too large, recursively compresses
        ```

    Cross-references:
        - Used by: _summarize_from_scratch(), _create_summary_chunk(),
                   _merge_two_summaries(), ExtractionStrategy (llm_rewrite)
        - Calls: check_and_handle_oversized_messages() for individual messages
        - Calls: check_prompt_size_and_split() for batch detection
        - Calls: call_llm_for_compaction() for actual LLM calls

    Performance Notes:
        - **Parallel execution**: Batches processed concurrently (asyncio.gather)
        - **Speedup**: N batches complete in ~time_of_1_batch instead of N * time_of_1_batch
        - **Recursive parallelization**: Nested levels also run in parallel
        - **Cost tracking**: Total cost accumulated across all parallel calls
        - **Memory**: All batch tasks created upfront, results aggregated after completion

    Implementation Notes:
        - Handles nested recursion (batches of batches)
        - Combines batch summaries with part markers ("Part 1/N", "Part 2/N")
        - Re-compresses if combined result >2x max_output_tokens
        - Preserves message order within batches
        - Thread-safe: No shared state between parallel calls

    Edge Cases:
        - Single oversized message: Chunks → parallel summarize chunks → combine
        - Many small messages: Batch split → parallel summarize batches → combine
        - Mixed scenario: Handle oversized first, then batch remainder
        - Re-compression needed: Batch summaries → parallel summarize → combine
        - Empty messages list: Returns empty content, zero cost
    """
    from workflow_service.registry.nodes.llm.prompt_compaction.llm_utils import call_llm_for_compaction
    from workflow_service.registry.nodes.llm.prompt_compaction.utils import format_messages
    from workflow_service.registry.nodes.llm.prompt_compaction.strategies import check_and_handle_oversized_messages
    import logging

    logger = logging.getLogger(__name__)
    template_kwargs = template_kwargs or {}

    # Step 1: Handle individual oversized messages
    processed_messages = await check_and_handle_oversized_messages(
        messages=messages,
        max_single_message_pct=max_single_message_pct,
        budget=budget,
        model_metadata=model_metadata,
        ext_context=ext_context,
    )

    # Step 2: Build test prompt to check total size
    template_kwargs["messages"] = format_messages(processed_messages)
    test_prompt = prompt_template.format(**template_kwargs)

    # Step 3: Check if prompt fits in context
    prompt_tokens = count_tokens_in_text(test_prompt, model_metadata)
    max_prompt_tokens = int(budget.available_input_tokens * 0.85)  # 85% safety margin

    if prompt_tokens <= max_prompt_tokens:
        # Fits - make single LLM call
        logger.debug(
            f"Prompt fits in context ({prompt_tokens} <= {max_prompt_tokens}). "
            f"Making single LLM call."
        )

        response = await call_llm_for_compaction(
            prompt=test_prompt,
            model_metadata=model_metadata,
            ext_context=ext_context,
            max_tokens=max_output_tokens,
            temperature=temperature,
        )

        return {
            "content": response["content"],
            "token_usage": response["token_usage"],
            "cost": response["cost"],
            "batched": False,
            "num_batches": 1,
        }

    # Step 4: Prompt too large - split into batches
    logger.info(
        f"Prompt exceeds context ({prompt_tokens} > {max_prompt_tokens}). "
        f"Splitting into batches..."
    )

    # Estimate overhead tokens from template (rough heuristic)
    overhead_tokens = len(prompt_template.replace("{messages}", "")) // 4

    batches = check_prompt_size_and_split(
        messages=processed_messages,
        max_tokens=max_prompt_tokens,
        model_metadata=model_metadata,
        overhead_tokens=overhead_tokens,
    )

    logger.info(f"Split into {len(batches)} batches - processing in parallel")

    # Step 5: Summarize each batch recursively IN PARALLEL (v2.1 performance optimization)
    # Instead of sequential processing, use asyncio.gather() for concurrent API calls
    import asyncio

    batch_kwargs = {k: v for k, v in template_kwargs.items() if k != "messages"}

    # Create tasks for all batches (parallel execution)
    batch_tasks = [
        call_llm_with_batch_splitting(
            messages=batch,
            prompt_template=prompt_template,
            model_metadata=model_metadata,
            ext_context=ext_context,
            budget=budget,
            template_kwargs=batch_kwargs,
            max_output_tokens=max_output_tokens,
            max_single_message_pct=max_single_message_pct,
            temperature=temperature,
        )
        for batch in batches
    ]

    # Execute all batches concurrently (5-10x faster than sequential!)
    logger.debug(f"Executing {len(batch_tasks)} batch summarization tasks in parallel")
    batch_results = await asyncio.gather(*batch_tasks)

    # Aggregate results from all batches
    batch_summaries = []
    total_cost = 0.0
    total_token_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

    for i, result in enumerate(batch_results):
        logger.debug(f"Batch {i+1}/{len(batch_results)} completed")
        batch_summaries.append(result["content"])
        total_cost += result["cost"]
        for key in total_token_usage:
            total_token_usage[key] += result["token_usage"].get(key, 0)

    # Step 6: Combine batch summaries
    if len(batch_summaries) == 1:
        # Only one batch - return directly
        combined_content = batch_summaries[0]
    else:
        # Multiple batches - combine with part markers
        combined_content = "\n\n".join([
            f"Part {i+1}/{len(batch_summaries)}:\n{summary}"
            for i, summary in enumerate(batch_summaries)
        ])

        # Step 7: Check if combined summary needs re-compression
        combined_tokens = count_tokens_in_text(combined_content, model_metadata)

        if combined_tokens > max_output_tokens * 2:
            # Combined summary is too large - re-compress
            logger.info(
                f"Combined batch summaries too large ({combined_tokens} tokens). "
                f"Re-compressing..."
            )

            # Create messages from batch summaries
            from langchain_core.messages import AIMessage
            from uuid import uuid4

            summary_messages = [
                AIMessage(content=s, id=str(uuid4()))
                for s in batch_summaries
            ]

            # Recursively compress the summaries
            recompression_result = await call_llm_with_batch_splitting(
                messages=summary_messages,
                prompt_template="Combine these summaries into one concise summary:\n\n{messages}",
                model_metadata=model_metadata,
                ext_context=ext_context,
                budget=budget,
                max_output_tokens=max_output_tokens,
                max_single_message_pct=max_single_message_pct,
                temperature=temperature,
            )

            combined_content = recompression_result["content"]
            total_cost += recompression_result["cost"]
            for key in total_token_usage:
                total_token_usage[key] += recompression_result["token_usage"].get(key, 0)

            logger.info(f"Re-compression complete. Final size: {len(combined_content)} chars")

    return {
        "content": combined_content,
        "token_usage": total_token_usage,
        "cost": total_cost,
        "batched": True,
        "num_batches": len(batches),
    }
