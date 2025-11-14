"""
Integration tests for HybridStrategy with v2.1 overflow handling.

Tests the combination of extraction + summarization with:
- Individual oversized messages
- Collective overflow requiring batch splitting
- End-to-end complex scenarios
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
    HybridStrategy,
    SummarizationStrategy,
    SummarizationMode,
    ExtractionStrategy,
)
from workflow_service.registry.nodes.llm.prompt_compaction.utils import ExtractionStrategy as ExtractionStrategyType
from tests.unit.services.workflow_service.registry.nodes.llm.prompt_compaction.test_base import (
    PromptCompactionIntegrationTestBase,
)


class TestHybridWithOversizedMessages(PromptCompactionIntegrationTestBase):
    """Test HybridStrategy handles individual oversized messages."""

    @unittest.skipIf(not os.getenv("OPENAI_API_KEY"), "Requires OPENAI_API_KEY")
    async def test_hybrid_with_oversized_messages(self):
        """Should handle individual oversized messages in historical data."""
        metadata = self._create_test_model_metadata(
            model_name="gpt-4o-mini",
            context_limit=128000,
        )

        budget = ContextBudget.calculate(
            total_context=128000,
            max_output_tokens=16384,
            config=ContextBudgetConfig(),
        )

        # Create 1 oversized message + 10 normal messages
        large_content = "\n\n".join([
            f"Section {i}: This is a very detailed section with lots of information. "
            f"It discusses various topics and provides comprehensive analysis. "
            f"Additional paragraphs provide more context and details."
            for i in range(300)  # ~60K tokens
        ])

        messages = [
            HumanMessage(content="Normal message 1", id=str(uuid4())),
            HumanMessage(content=large_content, id=str(uuid4())),  # Oversized
        ] + [
            HumanMessage(content=f"Normal message {i}", id=str(uuid4()))
            for i in range(2, 12)
        ]

        recent_messages = [
            HumanMessage(content="What are the key insights?", id=str(uuid4())),
        ]

        sections = {
            "system": [],
            "summaries": [],
            "historical": messages,
            "marked": [],
            "recent": recent_messages,
        }

        # Create hybrid strategy
        extraction_strategy = ExtractionStrategy(
            construction_strategy=ExtractionStrategyType.LLM_REWRITE,
            top_k=5,
            store_embeddings=False,  # Skip Weaviate for test
        )
        summarization_strategy = SummarizationStrategy(mode=SummarizationMode.FROM_SCRATCH)

        strategy = HybridStrategy(
            extraction_pct=0.05,
            extraction_strategy=extraction_strategy,
            summarization_strategy=summarization_strategy,
        )

        result = await strategy.compact(
            sections=sections,
            budget=budget,
            model_metadata=metadata,
            ext_context=self.ext_context,
        )

        # Verify result
        self.assertGreater(len(result.compacted_messages), 0)

        # Should have both extracted and summary messages
        self.assertGreater(len(result.extracted_messages), 0)
        self.assertGreater(len(result.summary_messages), 0)

        # Compression should have occurred
        self.assertGreater(result.compression_ratio, 1.0)

        # Cost should be tracked
        self.assertGreater(result.cost, 0.0)

        # Metadata should indicate hybrid strategy
        self.assertEqual(result.metadata["strategy"], "hybrid")


class TestHybridWithCollectiveOverflow(PromptCompactionIntegrationTestBase):
    """Test HybridStrategy handles many messages that collectively exceed context."""

    @unittest.skipIf(not os.getenv("OPENAI_API_KEY"), "Requires OPENAI_API_KEY")
    async def test_hybrid_with_collective_overflow(self):
        """Should handle many messages requiring batch splitting in summarization."""
        metadata = self._create_test_model_metadata(
            model_name="gpt-4o-mini",
            context_limit=128000,
        )

        budget = ContextBudget.calculate(
            total_context=128000,
            max_output_tokens=16384,
            config=ContextBudgetConfig(),
        )

        # Create 40 messages with ~2.5K tokens each = ~100K total
        messages = [
            HumanMessage(
                content="Message content here. " * 800 + f" Number {i}.",
                id=str(uuid4())
            )
            for i in range(40)
        ]

        recent_messages = [
            HumanMessage(content="Summarize the key themes discussed.", id=str(uuid4())),
        ]

        sections = {
            "system": [],
            "summaries": [],
            "historical": messages,
            "marked": [],
            "recent": recent_messages,
        }

        # Create hybrid strategy
        extraction_strategy = ExtractionStrategy(
            construction_strategy=ExtractionStrategyType.LLM_REWRITE,
            top_k=5,
            store_embeddings=False,
        )
        summarization_strategy = SummarizationStrategy(mode=SummarizationMode.FROM_SCRATCH)

        strategy = HybridStrategy(
            extraction_pct=0.05,
            extraction_strategy=extraction_strategy,
            summarization_strategy=summarization_strategy,
        )

        result = await strategy.compact(
            sections=sections,
            budget=budget,
            model_metadata=metadata,
            ext_context=self.ext_context,
        )

        # Verify extraction phase completed
        self.assertGreater(len(result.extracted_messages), 0)

        # Verify summarization phase completed (should have used batch splitting)
        self.assertGreater(len(result.summary_messages), 0)

        # Final result should fit in budget
        self.assertGreater(len(result.compacted_messages), 0)

        # Should have achieved significant compression
        self.assertGreater(result.compression_ratio, 2.0)

        # Cost tracking
        self.assertGreater(result.cost, 0.0)

        # Metadata
        self.assertEqual(result.metadata["strategy"], "hybrid")


class TestHybridEndToEndComplex(PromptCompactionIntegrationTestBase):
    """Test HybridStrategy in complex real-world scenarios."""

    @unittest.skipIf(not os.getenv("OPENAI_API_KEY"), "Requires OPENAI_API_KEY")
    async def test_hybrid_end_to_end_complex(self):
        """Should handle complex scenario with oversized + many messages."""
        metadata = self._create_test_model_metadata(
            model_name="gpt-4o-mini",
            context_limit=128000,
        )

        budget = ContextBudget.calculate(
            total_context=128000,
            max_output_tokens=16384,
            config=ContextBudgetConfig(),
        )

        # Create 1 oversized + 35 normal messages
        large_content = "\n\n".join([
            f"Detailed section {i}: This section contains extensive information "
            f"about various topics including technical details, analysis, and context. "
            f"It includes specific values, decisions made, and rationale."
            for i in range(300)  # ~60K tokens
        ])

        messages = [
            HumanMessage(content="Initial discussion point", id=str(uuid4())),
            HumanMessage(content=large_content, id=str(uuid4())),  # Oversized
        ] + [
            HumanMessage(
                content=f"Discussion point {i}: " + "Content here. " * 500,
                id=str(uuid4())
            )
            for i in range(2, 37)  # 35 more messages
        ]

        recent_messages = [
            HumanMessage(
                content="Based on everything discussed, what are the main takeaways?",
                id=str(uuid4())
            ),
        ]

        # Add system message
        system_messages = [
            HumanMessage(content="You are a helpful assistant.", id=str(uuid4()))
        ]

        sections = {
            "system": system_messages,
            "summaries": [],
            "historical": messages,
            "marked": [],
            "recent": recent_messages,
        }

        # Create hybrid strategy with explicit budget allocation
        extraction_strategy = ExtractionStrategy(
            construction_strategy=ExtractionStrategyType.LLM_REWRITE,
            top_k=8,  # Extract more chunks
            store_embeddings=False,
        )
        summarization_strategy = SummarizationStrategy(mode=SummarizationMode.FROM_SCRATCH)

        strategy = HybridStrategy(
            extraction_pct=0.05,  # 5% for extraction, 95% for summarization
            extraction_strategy=extraction_strategy,
            summarization_strategy=summarization_strategy,
        )

        result = await strategy.compact(
            sections=sections,
            budget=budget,
            model_metadata=metadata,
            ext_context=self.ext_context,
        )

        # Verify all sections present in final result
        self.assertGreater(len(result.compacted_messages), 0)

        # Should have system messages
        system_count = sum(1 for msg in result.compacted_messages
                          if msg.content == "You are a helpful assistant.")
        self.assertEqual(system_count, 1)

        # Should have extracted messages
        self.assertGreater(len(result.extracted_messages), 0)
        self.assertLessEqual(len(result.extracted_messages), 8)  # top_k=8

        # Should have summaries
        self.assertGreater(len(result.summary_messages), 0)

        # Compression ratio should be significant
        original_count = len(messages)
        compacted_count = len(result.summary_messages) + len(result.extracted_messages)
        self.assertLess(compacted_count, original_count)
        self.assertGreater(result.compression_ratio, 1.5)

        # Cost tracking should include both phases
        self.assertGreater(result.cost, 0.0)

        # Strategy should be hybrid
        self.assertEqual(result.metadata["strategy"], "hybrid")

        # Final messages should fit in budget (rough check)
        from workflow_service.registry.nodes.llm.prompt_compaction.token_utils import count_tokens
        total_tokens = count_tokens(result.compacted_messages, metadata)
        self.assertLess(total_tokens, budget.available_input_tokens)


class TestHybridMetadataIntegration(PromptCompactionIntegrationTestBase):
    """Test hybrid strategy preserves metadata from both extraction and summarization (v3.1)."""

    @unittest.skipIf(not os.getenv("OPENAI_API_KEY"), "Requires OPENAI_API_KEY")
    async def test_hybrid_preserves_both_strategy_metadata(self):
        """Verify hybrid strategy preserves metadata from both extraction and summarization."""
        from workflow_service.registry.nodes.llm.prompt_compaction.utils import get_message_metadata
        
        metadata = self._create_test_model_metadata(
            model_name="gpt-4o-mini",
            context_limit=128000,
        )

        budget = ContextBudget.calculate(
            total_context=128000,
            max_output_tokens=16384,
            config=ContextBudgetConfig(),
        )

        # Create messages
        messages = [
            HumanMessage(content=f"Message {i} with some content for testing", id=str(uuid4()))
            for i in range(15)
        ]

        recent_messages = [
            HumanMessage(content="What are the main themes?", id=str(uuid4())),
        ]

        sections = {
            "system": [],
            "summaries": [],
            "historical": messages,
            "marked": [],
            "recent": recent_messages,
        }

        # Create hybrid strategy
        extraction_strategy = ExtractionStrategy(
            construction_strategy=ExtractionStrategyType.EXTRACT_FULL,
            top_k=5,
            store_embeddings=False,
        )
        summarization_strategy = SummarizationStrategy(mode=SummarizationMode.FROM_SCRATCH)

        strategy = HybridStrategy(
            extraction_pct=0.05,
            extraction_strategy=extraction_strategy,
            summarization_strategy=summarization_strategy,
        )

        result = await strategy.compact(
            sections=sections,
            budget=budget,
            model_metadata=metadata,
            ext_context=self.ext_context,
        )

        # Verify extraction messages have extraction metadata (v3.1)
        if result.extracted_messages:
            for msg in result.extracted_messages:
                extraction_performed = get_message_metadata(msg, "extraction_performed")
                self.assertEqual(extraction_performed, True, "Extracted messages should have extraction_performed=True")
                
                embedding_model = get_message_metadata(msg, "embedding_model")
                self.assertIsNotNone(embedding_model, "Extracted messages should have embedding_model")
                
                construction_strategy = get_message_metadata(msg, "construction_strategy")
                self.assertIsNotNone(construction_strategy, "Extracted messages should have construction_strategy")

        # Verify result metadata contains both extraction and summarization costs
        self.assertIn("extraction_cost", result.metadata, "Result metadata should include extraction_cost")
        self.assertIn("summarization_cost", result.metadata, "Result metadata should include summarization_cost")
        self.assertEqual(result.metadata.get("strategy"), "hybrid", "Strategy should be hybrid")

    @unittest.skipIf(not os.getenv("OPENAI_API_KEY"), "Requires OPENAI_API_KEY")
    async def test_hybrid_with_different_construction_strategies(self):
        """Test hybrid strategy with DUMP and LLM_REWRITE construction strategies."""
        from workflow_service.registry.nodes.llm.prompt_compaction.utils import get_message_metadata
        
        for construction_type in [ExtractionStrategyType.DUMP, ExtractionStrategyType.LLM_REWRITE]:
            with self.subTest(construction_strategy=construction_type):
                metadata = self._create_test_model_metadata(
                    model_name="gpt-4o-mini",
                    context_limit=128000,
                )

                budget = ContextBudget.calculate(
                    total_context=128000,
                    max_output_tokens=16384,
                    config=ContextBudgetConfig(),
                )

                messages = [
                    HumanMessage(content=f"Content {i}", id=str(uuid4()))
                    for i in range(10)
                ]

                sections = {
                    "system": [],
                    "summaries": [],
                    "historical": messages,
                    "marked": [],
                    "recent": [HumanMessage(content="Query", id=str(uuid4()))],
                }

                extraction_strategy = ExtractionStrategy(
                    construction_strategy=construction_type,
                    top_k=3,
                    store_embeddings=False,
                )
                summarization_strategy = SummarizationStrategy(mode=SummarizationMode.FROM_SCRATCH)

                strategy = HybridStrategy(
                    extraction_pct=0.05,
                    extraction_strategy=extraction_strategy,
                    summarization_strategy=summarization_strategy,
                )

                result = await strategy.compact(
                    sections=sections,
                    budget=budget,
                    model_metadata=metadata,
                    ext_context=self.ext_context,
                )

                # Verify extraction messages have correct construction_strategy metadata
                if result.extracted_messages:
                    for msg in result.extracted_messages:
                        construction_strategy_meta = get_message_metadata(msg, "construction_strategy")
                        self.assertIsNotNone(construction_strategy_meta)
                        # Enum value is lowercase
                        self.assertIn(construction_type.value, str(construction_strategy_meta).lower(),
                                     f"Should reflect {construction_type.value} strategy")


if __name__ == "__main__":
    unittest.main()
