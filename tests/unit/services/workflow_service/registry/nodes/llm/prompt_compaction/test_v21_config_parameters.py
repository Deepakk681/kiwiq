"""
Unit tests for v2.1 configuration parameters.

Tests cover:
- expansion_threshold default value (0.85)
- expansion_budget_pct default value (0.80)
- chunk_score_aggregation default ("weighted_mean")
- expansion_mode default value ("hybrid")
- max_expansion_tokens default (16000)
- All config parameters in ExtractionStrategy
- Config parameters stored correctly

Test IDs: 43-49 (from comprehensive test plan)
"""

import unittest
from unittest.mock import Mock

from workflow_service.registry.nodes.llm.prompt_compaction.strategies import (
    ExtractionStrategy,
)
from workflow_service.registry.nodes.llm.prompt_compaction.utils import (
    ExtractionStrategy as ExtractionStrategyType,
)


class TestConfigDefaults(unittest.TestCase):
    """Test 43-47: Default values for v2.1 config parameters."""

    def test_expansion_threshold_default_value(self):
        """Test 43: expansion_threshold defaults to 0.85."""
        strategy = ExtractionStrategy(
            construction_strategy=ExtractionStrategyType.EXTRACT_FULL,
        )

        # Default should be 0.85
        self.assertEqual(strategy.expansion_threshold, 0.85)

    def test_expansion_budget_pct_default_value(self):
        """Test 44: expansion_budget_pct defaults to 0.80."""
        strategy = ExtractionStrategy(
            construction_strategy=ExtractionStrategyType.EXTRACT_FULL,
        )

        # Default should be 0.80 (80% of available budget)
        self.assertEqual(strategy.expansion_budget_pct, 0.80)

    def test_chunk_score_aggregation_default(self):
        """Test 45: chunk_score_aggregation defaults to 'weighted_mean'."""
        strategy = ExtractionStrategy(
            construction_strategy=ExtractionStrategyType.EXTRACT_FULL,
        )

        # Default should be "weighted_mean"
        self.assertEqual(strategy.chunk_score_aggregation, "weighted_mean")

    def test_expansion_mode_default_value(self):
        """Test 46: expansion_mode defaults to 'hybrid'."""
        strategy = ExtractionStrategy(
            construction_strategy=ExtractionStrategyType.EXTRACT_FULL,
        )

        # Default should be "hybrid"
        self.assertEqual(strategy.expansion_mode, "hybrid")

    def test_max_expansion_tokens_default(self):
        """Test 47: max_expansion_tokens defaults to 16000."""
        strategy = ExtractionStrategy(
            construction_strategy=ExtractionStrategyType.EXTRACT_FULL,
        )

        # Default should be 16000
        self.assertEqual(strategy.max_expansion_tokens, 16000)


class TestConfigStructure(unittest.TestCase):
    """Test 48-49: Config parameter structure and storage."""

    def test_all_config_parameters_in_extraction_config(self):
        """Test 48: All v2.1 config parameters are accessible in ExtractionStrategy."""
        strategy = ExtractionStrategy(
            construction_strategy=ExtractionStrategyType.EXTRACT_FULL,
            expansion_mode="full_message",
            expansion_threshold=0.90,
            expansion_budget_pct=0.75,
            max_expansion_tokens=20000,
            chunk_score_aggregation="max",
        )

        # Verify all parameters are accessible
        self.assertTrue(hasattr(strategy, 'expansion_mode'))
        self.assertTrue(hasattr(strategy, 'expansion_threshold'))
        self.assertTrue(hasattr(strategy, 'expansion_budget_pct'))
        self.assertTrue(hasattr(strategy, 'max_expansion_tokens'))
        self.assertTrue(hasattr(strategy, 'chunk_score_aggregation'))

        # Verify values
        self.assertEqual(strategy.expansion_mode, "full_message")
        self.assertEqual(strategy.expansion_threshold, 0.90)
        self.assertEqual(strategy.expansion_budget_pct, 0.75)
        self.assertEqual(strategy.max_expansion_tokens, 20000)
        self.assertEqual(strategy.chunk_score_aggregation, "max")

    def test_config_parameters_stored_correctly(self):
        """Test 49: Parameters are stored as instance attributes correctly."""
        # Test with custom values
        custom_strategy = ExtractionStrategy(
            construction_strategy=ExtractionStrategyType.EXTRACT_FULL,
            expansion_mode="top_chunks_only",
            expansion_threshold=0.88,
            expansion_budget_pct=0.85,
            max_expansion_tokens=18000,
            chunk_score_aggregation="mean",
        )

        # Verify instance attributes match constructor args
        self.assertEqual(custom_strategy.expansion_mode, "top_chunks_only")
        self.assertEqual(custom_strategy.expansion_threshold, 0.88)
        self.assertEqual(custom_strategy.expansion_budget_pct, 0.85)
        self.assertEqual(custom_strategy.max_expansion_tokens, 18000)
        self.assertEqual(custom_strategy.chunk_score_aggregation, "mean")

        # Test with defaults
        default_strategy = ExtractionStrategy(
            construction_strategy=ExtractionStrategyType.EXTRACT_FULL,
        )

        # Verify defaults are set
        self.assertIsNotNone(default_strategy.expansion_mode)
        self.assertIsNotNone(default_strategy.expansion_threshold)
        self.assertIsNotNone(default_strategy.expansion_budget_pct)
        self.assertIsNotNone(default_strategy.max_expansion_tokens)
        self.assertIsNotNone(default_strategy.chunk_score_aggregation)


if __name__ == "__main__":
    unittest.main()
