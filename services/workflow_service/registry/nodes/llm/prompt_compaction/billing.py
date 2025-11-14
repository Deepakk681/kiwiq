"""
Billing integration for prompt compaction.

Provides billing helpers for tracking compaction costs separately from main LLM calls.
Reuses existing billing infrastructure with new event types:
- llm_prompt_compaction_summarization
- llm_prompt_compaction_extraction
"""

from typing import Dict, Any
from uuid import UUID

from workflow_service.registry.nodes.llm.config import ModelMetadata, LLMModelProvider
from workflow_service.config.settings import settings
from kiwi_app.billing.models import CreditType
from db.session import get_async_db_as_manager


async def bill_summarization(
    token_usage: Dict[str, int],
    model_name: str,
    provider: LLMModelProvider,
    model_metadata: ModelMetadata,
    ext_context: Any,  # ExternalContextManager
    org_id: UUID,
    user_id: UUID,
    run_id: UUID,
    node_id: str,
    node_name: str,
    cost: float,
    enable_billing: bool = True,
) -> float:
    """
    Bill for LLM-based summarization.

    Uses existing LLM cost calculation and billing infrastructure.

    Args:
        token_usage: Token usage stats (input_tokens, output_tokens, etc.)
        model_name: Model name used for summarization
        provider: LLM provider
        model_metadata: Model metadata
        ext_context: External context manager
        org_id: Organization ID
        user_id: User ID
        run_id: Workflow run ID
        node_id: Node ID
        node_name: Node name
        cost: Calculated cost in USD
        enable_billing: If False, skip billing (for testing)

    Returns:
        Cost in USD
    """
    # Skip billing if disabled
    if not enable_billing:
        return 0.0

    # Apply markup
    cost = cost * settings.LLM_TOKEN_COST_MARKUP_FACTOR

    # Deduct credits
    async with get_async_db_as_manager() as db_session:
        await ext_context.billing_service.allocate_credits_for_operation(
            db=db_session,
            org_id=org_id,
            user_id=user_id,
            operation_id=run_id,
            credit_type=CreditType.DOLLAR_CREDITS,
            estimated_credits=cost,
            event_type="llm_prompt_compaction_summarization",
            metadata={
                "model_name": model_name,
                "provider": provider.value,
                "node_id": node_id,
                "node_name": node_name,
                "token_usage": token_usage,
                "compaction_type": "summarization",
            }
        )

    return cost


async def bill_extraction(
    num_messages: int,
    embedding_model: str,
    ext_context: Any,  # ExternalContextManager
    org_id: UUID,
    user_id: UUID,
    run_id: UUID,
    node_id: str,
    node_name: str,
    cost: float,
    enable_billing: bool = True,
) -> float:
    """
    Bill for vector-based extraction.

    Fixed costs based on number of messages and operations.

    Args:
        num_messages: Number of messages embedded
        embedding_model: Embedding model used
        ext_context: External context manager
        org_id: Organization ID
        user_id: User ID
        run_id: Workflow run ID
        node_id: Node ID
        node_name: Node name
        cost: Calculated cost in USD
        enable_billing: If False, skip billing (for testing)

    Returns:
        Cost in USD
    """
    # Skip billing if disabled
    if not enable_billing:
        return 0.0

    # Apply markup
    cost = cost * settings.LLM_TOKEN_COST_MARKUP_FACTOR

    # Deduct credits
    async with get_async_db_as_manager() as db_session:
        await ext_context.billing_service.allocate_credits_for_operation(
            db=db_session,
            org_id=org_id,
            user_id=user_id,
            operation_id=run_id,
            credit_type=CreditType.DOLLAR_CREDITS,
            estimated_credits=cost,
            event_type="llm_prompt_compaction_extraction",
            metadata={
                "node_id": node_id,
                "node_name": node_name,
                "num_messages": num_messages,
                "embedding_model": embedding_model,
                "compaction_type": "extraction",
            }
        )

    return cost


async def bill_hybrid(
    extraction_cost: float,
    summarization_cost: float,
    ext_context: Any,  # ExternalContextManager
    org_id: UUID,
    user_id: UUID,
    run_id: UUID,
    node_id: str,
    node_name: str,
    metadata: Dict[str, Any],
    enable_billing: bool = True,
) -> float:
    """
    Bill for hybrid compaction (extraction + summarization).

    Combines costs from both operations.

    Args:
        extraction_cost: Cost of extraction in USD
        summarization_cost: Cost of summarization in USD
        ext_context: External context manager
        org_id: Organization ID
        user_id: User ID
        run_id: Workflow run ID
        node_id: Node ID
        node_name: Node name
        metadata: Additional metadata
        enable_billing: If False, skip billing (for testing)

    Returns:
        Total cost in USD
    """
    # Skip billing if disabled
    if not enable_billing:
        return 0.0

    total_cost = extraction_cost + summarization_cost

    # Deduct credits
    async with get_async_db_as_manager() as db_session:
        await ext_context.billing_service.allocate_credits_for_operation(
            db=db_session,
            org_id=org_id,
            user_id=user_id,
            operation_id=run_id,
            credit_type=CreditType.DOLLAR_CREDITS,
            estimated_credits=total_cost,
            event_type="llm_prompt_compaction_hybrid",
            metadata={
                "node_id": node_id,
                "node_name": node_name,
                "extraction_cost": extraction_cost,
                "summarization_cost": summarization_cost,
                "compaction_type": "hybrid",
                **metadata,
            }
        )

    return total_cost
