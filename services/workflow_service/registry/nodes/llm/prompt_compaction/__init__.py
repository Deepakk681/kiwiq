"""
LLM Prompt Compaction System

This package provides intelligent prompt compaction for LLM nodes to handle context window
overflow. It supports multiple compaction strategies (summarization, extraction, hybrid) with
per-workflow, per-node isolation.

Key Features:
- Context window allocation model (10% system, 40% recent, 20% summaries, 10% marked, 10% buffer)
- Three compaction strategies: Summarization (continued/hierarchical), Extractive, Hybrid
- Message classification and preservation (system, marked, tool sequences, recent)
- Billing integration using existing infrastructure
- Embedding storage in Weaviate ThreadMessageChunks collection
- Per-node message history isolation

Architecture:
- compactor.py: Main orchestrator (PromptCompactor class)
- strategies.py: All strategy implementations
- context_manager.py: Context budget & message classification
- token_utils.py: Token counting wrappers
- billing.py: Billing integration helpers
- utils.py: Shared utilities (formatting, hashing, etc.)

Usage:
    from workflow_service.registry.nodes.llm.prompt_compaction import PromptCompactor

    compactor = PromptCompactor(
        config=prompt_compaction_config,
        model_metadata=model_metadata,
        node_id=node_id,
        node_name=node_name,
    )

    result = await compactor.compact(
        messages=messages,
        ext_context=ext_context,
        app_context=app_context,
    )
"""

from workflow_service.registry.nodes.llm.prompt_compaction.compactor import PromptCompactor
from workflow_service.registry.nodes.llm.prompt_compaction.context_manager import (
    ContextBudget,
    ContextBudgetConfig,
    MessageClassifier,
    BudgetEnforcer,
)
from workflow_service.registry.nodes.llm.prompt_compaction.strategies import (
    CompactionStrategy,
    SummarizationStrategy,
    ExtractionStrategy,
    HybridStrategy,
    NoOpStrategy,
    CompactionResult,
    SummarizationResult,
    ExtractionResult,
)

__all__ = [
    "PromptCompactor",
    "ContextBudget",
    "ContextBudgetConfig",
    "MessageClassifier",
    "BudgetEnforcer",
    "CompactionStrategy",
    "SummarizationStrategy",
    "ExtractionStrategy",
    "HybridStrategy",
    "NoOpStrategy",
    "CompactionResult",
    "SummarizationResult",
    "ExtractionResult",
]
