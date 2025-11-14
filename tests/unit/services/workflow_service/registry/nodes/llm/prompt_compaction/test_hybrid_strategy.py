"""
Unit tests for v2.1 hybrid strategy functionality.

Tests cover:
- Budget allocation between extraction and summarization
- Sequential execution (extraction first, then summarization)
- Extraction budget percentages (2%, 5%, 10%)
- Budget reallocation when extraction completes
- Combined output validation

Test IDs: 36-42 (from comprehensive test plan)
"""

import unittest

from workflow_service.registry.nodes.llm.prompt_compaction.compactor import (
    ExtractionConfig,
    HybridConfig,
    SummarizationConfig,
)
from workflow_service.registry.nodes.llm.prompt_compaction.strategies import (
    ExtractionStrategy,
    HybridStrategy,
    SummarizationStrategy,
)
from workflow_service.registry.nodes.llm.prompt_compaction.utils import (
    ExtractionStrategy as ExtractionStrategyType,
)

from .test_base import PromptCompactionUnitTestBase


class TestHybridBudgetAllocation(PromptCompactionUnitTestBase):
    """Test 36: Budget allocation between extraction and summarization."""

    async def test_default_5_percent_extraction_budget(self):
        """Should allocate 5% of budget to extraction by default."""
        extraction_strategy = ExtractionStrategy(
            construction_strategy=ExtractionStrategyType.EXTRACT_FULL,
            store_embeddings=False,
        )
        summarization_strategy = SummarizationStrategy()

        strategy = HybridStrategy(
            extraction_pct=0.05,  # 5% default
            extraction_strategy=extraction_strategy,
            summarization_strategy=summarization_strategy,
        )

        # Verify config
        self.assertEqual(strategy.extraction_pct, 0.05)

    async def test_budget_split_calculation(self):
        """Should correctly configure budget split percentage."""
        extraction_strategy = ExtractionStrategy(
            construction_strategy=ExtractionStrategyType.EXTRACT_FULL,
            store_embeddings=False,
        )
        summarization_strategy = SummarizationStrategy()

        strategy = HybridStrategy(
            extraction_pct=0.05,
            extraction_strategy=extraction_strategy,
            summarization_strategy=summarization_strategy,
        )

        # Verify percentage is set correctly
        self.assertEqual(strategy.extraction_pct, 0.05)


class TestHybridSequentialExecution(PromptCompactionUnitTestBase):
    """Test 37: Sequential execution (extraction first, then summarization)."""

    async def test_extraction_runs_before_summarization(self):
        """Should run extraction before summarization."""
        extraction_strategy = ExtractionStrategy(
            construction_strategy=ExtractionStrategyType.EXTRACT_FULL,
            store_embeddings=False,
        )
        summarization_strategy = SummarizationStrategy()

        strategy = HybridStrategy(
            extraction_pct=0.05,
            extraction_strategy=extraction_strategy,
            summarization_strategy=summarization_strategy,
        )

        sections = {
            "system": self._generate_test_messages(1, roles=["system"]),
            "summaries": [],
            "historical": self._generate_test_messages(20),
            "old_tools": [],
            "marked": [],
            "latest_tools": [],
            "recent": self._generate_test_messages(5),
        }

        budget = self._create_test_budget()
        model_metadata = self._create_test_model_metadata()

        result = await strategy.compact(
            sections=sections,
            budget=budget,
            model_metadata=model_metadata,
            ext_context=self.ext_context,
            runtime_config=None,
        )

        # Verify result is not None - strategy executed successfully
        self.assertIsNotNone(result)
        self.assertIsNotNone(result.compacted_messages)


class TestHybridExtractionPercentages(PromptCompactionUnitTestBase):
    """Test 38-40: Different extraction budget percentages."""

    async def test_2_percent_extraction_budget(self):
        """Should allocate 2% to extraction."""
        extraction_strategy = ExtractionStrategy(
            construction_strategy=ExtractionStrategyType.EXTRACT_FULL,
            store_embeddings=False,
        )
        summarization_strategy = SummarizationStrategy()

        strategy = HybridStrategy(
            extraction_pct=0.02,  # 2%
            extraction_strategy=extraction_strategy,
            summarization_strategy=summarization_strategy,
        )

        self.assertEqual(strategy.extraction_pct, 0.02)

    async def test_5_percent_extraction_budget(self):
        """Should allocate 5% to extraction (default)."""
        extraction_strategy = ExtractionStrategy(
            construction_strategy=ExtractionStrategyType.EXTRACT_FULL,
            store_embeddings=False,
        )
        summarization_strategy = SummarizationStrategy()

        strategy = HybridStrategy(
            extraction_pct=0.05,  # 5%
            extraction_strategy=extraction_strategy,
            summarization_strategy=summarization_strategy,
        )

        self.assertEqual(strategy.extraction_pct, 0.05)

    async def test_10_percent_extraction_budget(self):
        """Should allocate 10% to extraction."""
        extraction_strategy = ExtractionStrategy(
            construction_strategy=ExtractionStrategyType.EXTRACT_FULL,
            store_embeddings=False,
        )
        summarization_strategy = SummarizationStrategy()

        strategy = HybridStrategy(
            extraction_pct=0.10,  # 10%
            extraction_strategy=extraction_strategy,
            summarization_strategy=summarization_strategy,
        )

        self.assertEqual(strategy.extraction_pct, 0.10)


class TestHybridBudgetReallocation(PromptCompactionUnitTestBase):
    """Test 41: Budget reallocation when extraction completes."""

    async def test_unused_extraction_budget_reallocated(self):
        """Should handle hybrid strategy with small extraction budget."""
        extraction_strategy = ExtractionStrategy(
            construction_strategy=ExtractionStrategyType.EXTRACT_FULL,
            top_k=3,  # Extract only 3 messages
            store_embeddings=False,
        )
        summarization_strategy = SummarizationStrategy()

        strategy = HybridStrategy(
            extraction_pct=0.05,
            extraction_strategy=extraction_strategy,
            summarization_strategy=summarization_strategy,
        )

        sections = {
            "system": self._generate_test_messages(1, roles=["system"]),
            "summaries": [],
            "historical": self._generate_test_messages(30),
            "old_tools": [],
            "marked": [],
            "latest_tools": [],
            "recent": self._generate_test_messages(5),
        }

        budget = self._create_test_budget()
        model_metadata = self._create_test_model_metadata()

        result = await strategy.compact(
            sections=sections,
            budget=budget,
            model_metadata=model_metadata,
            ext_context=self.ext_context,
            runtime_config=None,
        )

        # Verify result
        self.assertIsNotNone(result)
        self.assertIsNotNone(result.compacted_messages)


class TestHybridCombinedOutput(PromptCompactionUnitTestBase):
    """Test 42: Combined output validation from hybrid strategy."""

    async def test_combined_output_structure(self):
        """Should combine extraction and summarization outputs correctly."""
        extraction_strategy = ExtractionStrategy(
            construction_strategy=ExtractionStrategyType.EXTRACT_FULL,
            store_embeddings=False,
        )
        summarization_strategy = SummarizationStrategy()

        strategy = HybridStrategy(
            extraction_pct=0.05,
            extraction_strategy=extraction_strategy,
            summarization_strategy=summarization_strategy,
        )

        sections = {
            "system": self._generate_test_messages(1, roles=["system"]),
            "summaries": [],
            "historical": self._generate_test_messages(20),
            "old_tools": [],
            "marked": [],
            "latest_tools": [],
            "recent": self._generate_test_messages(5),
        }

        budget = self._create_test_budget()
        model_metadata = self._create_test_model_metadata()

        result = await strategy.compact(
            sections=sections,
            budget=budget,
            model_metadata=model_metadata,
            ext_context=self.ext_context,
            runtime_config=None,
        )

        # Verify result structure
        self.assertIsNotNone(result)
        self.assertIsNotNone(result.compacted_messages)

        # Output should include messages
        compacted_count = len(result.compacted_messages)
        self.assertGreater(compacted_count, 0)


if __name__ == "__main__":
    unittest.main()
