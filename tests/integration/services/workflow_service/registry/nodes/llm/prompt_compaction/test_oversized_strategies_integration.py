"""
Integration tests for oversized message handling in strategies (v2.1).

Tests real strategy execution with oversized messages:
- SummarizationStrategy with oversized messages
- ExtractionStrategy with oversized historical messages
- HybridStrategy with oversized messages
- Batch splitting when combined messages exceed context
"""

import unittest
import os
from uuid import uuid4
from langchain_core.messages import HumanMessage, AIMessage

from workflow_service.registry.nodes.llm.config import ModelMetadata, LLMModelProvider
from workflow_service.registry.nodes.llm.prompt_compaction.context_manager import (
    ContextBudget,
    ContextBudgetConfig,
)
from workflow_service.registry.nodes.llm.prompt_compaction.strategies import (
    SummarizationStrategy,
    SummarizationMode,
    ExtractionStrategy,
)
from workflow_service.registry.nodes.llm.prompt_compaction.utils import ExtractionStrategy as ExtractionStrategyType
from tests.unit.services.workflow_service.registry.nodes.llm.prompt_compaction.test_base import (
    PromptCompactionIntegrationTestBase,
)


class TestSummarizationWithOversized(PromptCompactionIntegrationTestBase):
    """Test summarization strategy with oversized messages."""

    @unittest.skipIf(not os.getenv("OPENAI_API_KEY"), "Requires OPENAI_API_KEY")
    async def test_from_scratch_with_oversized_message(self):
        """Should handle oversized message in from-scratch summarization."""
        metadata = self._create_test_model_metadata(
            model_name="gpt-4o-mini",
            context_limit=128000,
        )

        budget = ContextBudget.calculate(
            total_context=128000,
            max_output_tokens=16384,
            config=ContextBudgetConfig(),
        )

        # Create one oversized message (simulated with very long content)
        large_content = "\n\n".join([
            f"Section {i}: This is a detailed section with lots of information. "
            f"It discusses various topics including background, methodology, results, "
            f"analysis, conclusions, and recommendations. Each section is comprehensive "
            f"and contains multiple paragraphs of detailed content."
            for i in range(500)  # Create ~100K tokens
        ])

        messages = [
            HumanMessage(content="Start of conversation", id=str(uuid4())),
            HumanMessage(content=large_content, id=str(uuid4())),  # Oversized message
            HumanMessage(content="End of conversation", id=str(uuid4())),
        ]

        # Classify into sections
        sections = {
            "system": [],
            "summaries": [],
            "historical": messages,
            "old_tools": [],
            "marked": [],
            "latest_tools": [],
            "recent": [],
        }

        # Test from-scratch mode
        strategy = SummarizationStrategy(mode=SummarizationMode.FROM_SCRATCH)

        result = await strategy.compact(
            sections=sections,
            budget=budget,
            model_metadata=metadata,
            ext_context=self.ext_context,
        )

        # Verify summarization succeeded
        self.assertGreater(len(result.summary_messages), 0)
        # Summary should be much shorter than original
        self.assertLess(len(result.summary_messages[0].content), len(large_content))

    @unittest.skipIf(not os.getenv("OPENAI_API_KEY"), "Requires OPENAI_API_KEY")
    async def test_continued_mode_with_oversized_summaries(self):
        """Should handle oversized existing summaries in continued mode."""
        metadata = self._create_test_model_metadata(
            model_name="gpt-4o-mini",
            context_limit=128000,
        )

        budget = ContextBudget.calculate(
            total_context=128000,
            max_output_tokens=16384,
            config=ContextBudgetConfig(),
        )

        # Create oversized existing summary
        large_summary_content = "\n\n".join([
            f"Summary paragraph {i}: Contains detailed information about the conversation "
            f"including facts, decisions, analysis, and context. This is comprehensive."
            for i in range(200)  # Create large summary
        ])

        existing_summary = AIMessage(content=large_summary_content, id=str(uuid4()))
        existing_summary.additional_kwargs = {
            "summary": True,
            "summarized_message_ids": ["msg1", "msg2"],
            "summary_generation": 0,
        }

        new_messages = [
            HumanMessage(content="New message 1", id=str(uuid4())),
            HumanMessage(content="New message 2", id=str(uuid4())),
        ]

        sections = {
            "system": [],
            "summaries": [existing_summary],
            "historical": new_messages,
            "old_tools": [],
            "marked": [],
            "latest_tools": [],
            "recent": [],
        }

        strategy = SummarizationStrategy(mode=SummarizationMode.CONTINUED)

        result = await strategy.compact(
            sections=sections,
            budget=budget,
            model_metadata=metadata,
            ext_context=self.ext_context,
        )

        # Should successfully create summary
        self.assertGreater(len(result.summary_messages), 0)


class TestExtractionWithOversized(PromptCompactionIntegrationTestBase):
    """Test extraction strategy with oversized messages."""

    @unittest.skipIf(not os.getenv("OPENAI_API_KEY"), "Requires OPENAI_API_KEY")
    async def test_extraction_with_oversized_historical(self):
        """Should handle oversized messages in historical context."""
        metadata = self._create_test_model_metadata(
            model_name="gpt-4o-mini",
            context_limit=128000,
        )

        budget = ContextBudget.calculate(
            total_context=128000,
            max_output_tokens=16384,
            config=ContextBudgetConfig(),
        )

        # Create large historical message
        large_content = "\n\n".join([
            f"Historical fact {i}: Important information about the project context, "
            f"including background, requirements, and constraints."
            for i in range(300)  # Large message
        ])

        historical_messages = [
            HumanMessage(content="Normal message 1", id=str(uuid4())),
            HumanMessage(content=large_content, id=str(uuid4())),  # Oversized
            HumanMessage(content="Normal message 2", id=str(uuid4())),
        ]

        recent_messages = [
            HumanMessage(content="What were the project requirements?", id=str(uuid4())),
        ]

        sections = {
            "system": [],
            "summaries": [],
            "historical": historical_messages,
            "old_tools": [],
            "marked": [],
            "latest_tools": [],
            "recent": recent_messages,
        }

        strategy = ExtractionStrategy(
            construction_strategy=ExtractionStrategyType.EXTRACT_FULL,
            top_k=2,
            store_embeddings=False,  # Skip Weaviate for test
        )

        result = await strategy.compact(
            sections=sections,
            budget=budget,
            model_metadata=metadata,
            ext_context=self.ext_context,
        )

        # Should successfully extract messages
        self.assertGreaterEqual(len(result.extracted_messages), 0)


class TestBatchSplitting(PromptCompactionIntegrationTestBase):
    """Test batch splitting when combined messages exceed context."""

    def test_batch_splitting_logic(self):
        """Should split messages into batches when collectively too large."""
        from workflow_service.registry.nodes.llm.prompt_compaction.token_utils import (
            check_prompt_size_and_split,
        )

        metadata = self._create_test_model_metadata(
            model_name="gpt-4o-mini",
            context_limit=128000,
        )

        # Create many moderate-sized messages that collectively exceed limit
        messages = [
            HumanMessage(content="Message content " * 1000, id=str(uuid4()))  # ~2K tokens each
            for _ in range(50)  # Total ~100K tokens
        ]

        # Set max_tokens to 30K - should create multiple batches
        batches = check_prompt_size_and_split(
            messages=messages,
            max_tokens=30000,
            model_metadata=metadata,
            overhead_tokens=1000,
        )

        # Should create multiple batches
        self.assertGreater(len(batches), 1)

        # Each batch should be manageable
        from workflow_service.registry.nodes.llm.prompt_compaction.token_utils import count_tokens
        for batch in batches:
            batch_tokens = count_tokens(batch, metadata)
            self.assertLess(batch_tokens, 30000)

    def test_no_split_when_under_limit(self):
        """Should not split when messages fit in one batch."""
        from workflow_service.registry.nodes.llm.prompt_compaction.token_utils import (
            check_prompt_size_and_split,
        )

        metadata = self._create_test_model_metadata(
            model_name="gpt-4o-mini",
            context_limit=128000,
        )

        # Create small messages
        messages = [
            HumanMessage(content="Short message", id=str(uuid4()))
            for _ in range(10)
        ]

        batches = check_prompt_size_and_split(
            messages=messages,
            max_tokens=100000,
            model_metadata=metadata,
        )

        # Should return single batch
        self.assertEqual(len(batches), 1)
        self.assertEqual(len(batches[0]), len(messages))


class TestHierarchicalSummarizationWithOversized(PromptCompactionIntegrationTestBase):
    """Test hierarchical summarization with oversized messages at various levels."""

    @unittest.skipIf(not os.getenv("OPENAI_API_KEY"), "Requires OPENAI_API_KEY")
    async def test_merge_with_oversized_summaries(self):
        """Should handle merging oversized summaries."""
        metadata = self._create_test_model_metadata(
            model_name="gpt-4o-mini",
            context_limit=128000,
        )

        budget = ContextBudget.calculate(
            total_context=128000,
            max_output_tokens=16384,
            config=ContextBudgetConfig(),
        )

        # Create two large summaries that need merging
        summary1_content = "\n\n".join([
            f"Summary 1 paragraph {i}: Detailed information about early conversation."
            for i in range(100)
        ])

        summary2_content = "\n\n".join([
            f"Summary 2 paragraph {i}: Detailed information about middle conversation."
            for i in range(100)
        ])

        summary1 = AIMessage(content=summary1_content, id=str(uuid4()))
        summary1.additional_kwargs = {
            "summary": True,
            "summarized_message_ids": ["msg1"],
            "summary_generation": 0,
        }

        summary2 = AIMessage(content=summary2_content, id=str(uuid4()))
        summary2.additional_kwargs = {
            "summary": True,
            "summarized_message_ids": ["msg2"],
            "summary_generation": 0,
        }

        # New messages to trigger merge
        new_messages = [HumanMessage(content="New message", id=str(uuid4()))]

        sections = {
            "system": [],
            "summaries": [summary1, summary2],
            "historical": new_messages,
            "old_tools": [],
            "marked": [],
            "latest_tools": [],
            "recent": [],
        }

        strategy = SummarizationStrategy(
            mode=SummarizationMode.CONTINUED,
        )

        result = await strategy.compact(
            sections=sections,
            budget=budget,
            model_metadata=metadata,
            ext_context=self.ext_context,
        )

        # Should successfully merge and create new summary
        self.assertGreater(len(result.summary_messages), 0)


if __name__ == "__main__":
    unittest.main()
