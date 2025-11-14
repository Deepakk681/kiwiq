"""
LLM calling utilities for prompt compaction (v2.1).

Reuses the existing LLM node infrastructure to call LLMs for summarization
without duplicating code or hardcoding models.

v2.1 Features:
- Model provider selection logic (Perplexity → Claude fallback)
- Tenacity retry decorators for resilient LLM calls
"""

from typing import Any, Dict, Optional, Tuple
from langchain_core.messages import HumanMessage, AIMessage
from openai import APIError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from workflow_service.registry.nodes.llm.config import ModelMetadata, LLMModelProvider
from workflow_service.config.settings import settings


def get_compaction_model(
    main_model_provider: str,
    llm_config: Any,  # CompactionLLMConfig
) -> Tuple[str, str]:
    """
    Determine which model to use for compaction LLM calls (v2.1).

    Args:
        main_model_provider: Provider of the main LLM model
        llm_config: CompactionLLMConfig instance

    Returns:
        Tuple of (provider, model) to use for compaction
    """
    # Perplexity → Claude fallback for summarization
    if main_model_provider.lower() == "perplexity":
        return (
            llm_config.perplexity_fallback_provider,
            llm_config.perplexity_fallback_model,
        )

    # Use configured default
    return (
        llm_config.default_provider,
        llm_config.default_model,
    )


def create_compaction_retry_decorator(llm_config: Any):
    """
    Create tenacity retry decorator from config (v2.1).

    Args:
        llm_config: CompactionLLMConfig instance

    Returns:
        Configured retry decorator
    """
    from openai import APIError, RateLimitError, APITimeoutError

    return retry(
        stop=stop_after_attempt(llm_config.max_retries),
        wait=wait_exponential(
            multiplier=llm_config.retry_wait_exponential_multiplier,
            max=llm_config.retry_wait_exponential_max,
        ),
        retry=retry_if_exception_type((APIError, RateLimitError, APITimeoutError, TimeoutError)),
        reraise=True,
    )

retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(
            # multiplier=llm_config.retry_wait_exponential_multiplier,
            # max=llm_config.retry_wait_exponential_max,
        ),
        retry=retry_if_exception_type(
            # (APIError, RateLimitError, APITimeoutError, TimeoutError)
            Exception
            ),
        reraise=True,
    )
async def call_llm_for_compaction(
    prompt: str,
    model_metadata: ModelMetadata,
    ext_context: Any,  # ExternalContextManager
    max_tokens: int = 2000,
    temperature: float = 0.0,
    logger = None,
) -> Dict[str, Any]:
    """
    Call LLM for compaction tasks (summarization, salient point extraction, etc.).

    Reuses the LLM node's infrastructure to initialize and call the appropriate model.

    Args:
        prompt: Prompt text
        model_metadata: Model metadata (determines which provider/model to use)
        ext_context: External context manager
        max_tokens: Maximum tokens for response
        temperature: Temperature for generation (0.0 for deterministic)

    Returns:
        Dict with:
            - content: str - Response content
            - token_usage: Dict[str, int] - Token usage stats
            - cost: float - Cost in USD

    Raises:
        Exception: If LLM call fails
    """
    # Import here to avoid circular dependencies
    from workflow_service.registry.nodes.llm.llm_node import LLMNode
    from workflow_service.registry.nodes.llm.config import (
        OpenAIModels,
        AnthropicModels,
        GeminiModels,
    )

    # Create message for LLM
    messages = [HumanMessage(content=prompt)]

    # Initialize model using the same logic as LLMNode
    # We'll use a lightweight helper that reuses _init_model logic
    model = None

    try:
        if model_metadata.provider == LLMModelProvider.OPENAI:
            from langchain_openai import ChatOpenAI

            kwargs = {}
            if model_metadata.reasoning:
                kwargs["reasoning_effort"] = "minimal" if model_metadata.model_name.startswith("gpt-5") else "low"

            model = ChatOpenAI(
                model=model_metadata.model_name,
                api_key=settings.OPENAI_API_KEY,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs,
            )

        elif model_metadata.provider == LLMModelProvider.ANTHROPIC:
            from langchain_anthropic import ChatAnthropic

            model = ChatAnthropic(
                model=model_metadata.model_name,
                api_key=settings.ANTHROPIC_API_KEY,
                max_tokens=max_tokens,
                temperature=temperature,
            )

        elif model_metadata.provider == LLMModelProvider.GEMINI:
            from langchain_google_genai import ChatGoogleGenerativeAI

            model = ChatGoogleGenerativeAI(
                model=model_metadata.model_name,
                max_tokens=max_tokens,
                temperature=temperature,
            )

        else:
            # Fallback to OpenAI for unsupported providers
            from langchain_openai import ChatOpenAI

            model = ChatOpenAI(
                model="gpt-4o-mini",
                api_key=settings.OPENAI_API_KEY,
                max_tokens=max_tokens,
                temperature=temperature,
            )

        # Call model (non-streaming)
        response = await model.ainvoke(messages)

        # Extract token usage following the same pattern as llm_node.py
        # This properly handles cached tokens for both OpenAI and Anthropic
        response_metadata = getattr(response, 'response_metadata', {})
        usage_metadata = getattr(response, 'usage_metadata', {})
        
        # Merge metadata (usage_metadata takes precedence)
        if not response_metadata:
            response_metadata = usage_metadata
        elif usage_metadata and isinstance(usage_metadata, dict):
            response_metadata = {**response_metadata, **usage_metadata}
        
        # Extract token usage with provider-specific logic
        token_usage = {}
        if response_metadata:
            if model_metadata.provider == LLMModelProvider.OPENAI:
                # OpenAI format - extract cached tokens from input_token_details
                token_usage = {
                    "input_tokens": response_metadata.get("input_tokens", 0),
                    "output_tokens": response_metadata.get("output_tokens", 0),
                    "total_tokens": response_metadata.get("total_tokens", 0),
                    "cached_tokens": response_metadata.get("input_token_details", {}).get("cache_read", 0),
                }
            elif model_metadata.provider == LLMModelProvider.ANTHROPIC:
                # Anthropic format - extract cached tokens
                token_usage = {
                    "input_tokens": response_metadata.get("input_tokens", 0),
                    "output_tokens": response_metadata.get("output_tokens", 0),
                    "total_tokens": response_metadata.get("total_tokens", 0),
                    "cached_tokens": response_metadata.get("input_token_details", {}).get("cache_read", 0),
                }
            else:
                # Fallback for other providers (shouldn't happen for compaction)
                token_usage = {
                    "input_tokens": response_metadata.get("input_tokens", 0),
                    "output_tokens": response_metadata.get("output_tokens", 0),
                    "total_tokens": response_metadata.get("total_tokens", 0),
                    "cached_tokens": 0,
                }

        # Calculate cost using sophisticated tokencost library (same as main LLM node)
        # This handles cached tokens and provides accurate up-to-date pricing
        from workflow_service.registry.nodes.llm.prompt_compaction.cost_utils import calculate_compaction_llm_cost
        
        cost = calculate_compaction_llm_cost(
            token_usage=token_usage,
            provider=model_metadata.provider,
            model_name=model_metadata.model_name,
            model_metadata=model_metadata,
        )

        return {
            "content": response.content,
            "token_usage": token_usage,
            "cost": cost,
        }

    except Exception as e:
        # Log error and re-raise
        raise Exception(f"LLM call failed for compaction: {e}")


async def get_embeddings_batch(
    texts: list[str],
    embedding_model: str,
    ext_context: Any,  # ExternalContextManager
) -> list[list[float]]:
    """
    Get embeddings from OpenAI embeddings API.

    Uses the same patterns as the existing RAG ingestion pipeline.

    Args:
        texts: List of texts to embed
        embedding_model: Embedding model name (e.g., "text-embedding-3-small")
        ext_context: External context manager

    Returns:
        List of embedding vectors
    
    Note:
        Expects texts to be pre-truncated to fit within embedding model's token limit.
        Texts exceeding limit should be handled by chunking logic before calling this.
    """
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    # Batch embed for efficiency (max 2048 texts per request)
    batch_size = 2048
    all_embeddings = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]

        response = await client.embeddings.create(
            model=embedding_model,
            input=batch,
        )

        embeddings = [item.embedding for item in response.data]
        all_embeddings.extend(embeddings)

    return all_embeddings
