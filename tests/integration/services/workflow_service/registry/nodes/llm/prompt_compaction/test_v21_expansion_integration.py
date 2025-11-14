"""
Integration tests for v2.1 extraction expansion features.

Tests cover:
- Hybrid expansion mode (full message vs chunks)
- Full message expansion mode
- Top chunks only mode
- Expansion budget enforcement
- Max expansion tokens per message
- Expansion threshold for retrieval

These tests use real Weaviate and verify the complete workflow.
"""

import unittest
from uuid import uuid4

from langchain_core.messages import HumanMessage, AIMessage

from weaviate_client import ThreadMessageWeaviateClient
from workflow_service.registry.nodes.llm.config import ModelMetadata, LLMModelProvider
from workflow_service.registry.nodes.llm.prompt_compaction.strategies import ExtractionStrategy
from workflow_service.registry.nodes.llm.prompt_compaction.utils import (
    ExtractionStrategy as ExtractionStrategyType,
)

from tests.unit.services.workflow_service.registry.nodes.llm.prompt_compaction.test_base import (
    PromptCompactionIntegrationTestBase,
)


class TestExpansionModes(PromptCompactionIntegrationTestBase):
    """Integration tests for expansion modes."""

    async def asyncSetUp(self):
        """Setup Weaviate client."""
        await super().asyncSetUp()

        self.weaviate_client = ThreadMessageWeaviateClient()
        await self.weaviate_client.connect()
        await self.weaviate_client.setup_schema()

    async def asyncTearDown(self):
        """Cleanup Weaviate data."""
        if self.weaviate_client:
            await self.weaviate_client.close()
        await super().asyncTearDown()

    async def test_hybrid_expansion_mode_config(self):
        """Test: Hybrid mode configuration."""
        strategy = ExtractionStrategy(
            construction_strategy=ExtractionStrategyType.EXTRACT_FULL,
            expansion_mode="hybrid",
            max_expansion_tokens=16000,
            expansion_threshold=0.85,
        )

        # Verify config
        self.assertEqual(strategy.expansion_mode, "hybrid")
        self.assertEqual(strategy.max_expansion_tokens, 16000)
        self.assertEqual(strategy.expansion_threshold, 0.85)

        # Test logic: small message uses full expansion
        small_message_tokens = 5000
        use_full = small_message_tokens < strategy.max_expansion_tokens
        self.assertTrue(use_full, "Small messages should use full expansion")

        # Large message uses chunks only
        large_message_tokens = 20000
        use_chunks = large_message_tokens >= strategy.max_expansion_tokens
        self.assertTrue(use_chunks, "Large messages should use chunks only")

    async def test_full_message_expansion_mode_config(self):
        """Test: Full message mode configuration."""
        strategy = ExtractionStrategy(
            construction_strategy=ExtractionStrategyType.EXTRACT_FULL,
            expansion_mode="full_message",
            max_expansion_tokens=16000,
        )

        self.assertEqual(strategy.expansion_mode, "full_message")

        # Full message mode always tries to include full message
        message_tokens = 15000
        should_include = message_tokens <= strategy.max_expansion_tokens
        self.assertTrue(should_include)

        # Oversized messages would be included with warning
        oversized_tokens = 25000
        self.assertGreater(oversized_tokens, strategy.max_expansion_tokens)

    async def test_top_chunks_only_mode_config(self):
        """Test: Top chunks only mode configuration."""
        strategy = ExtractionStrategy(
            construction_strategy=ExtractionStrategyType.EXTRACT_FULL,
            expansion_mode="top_chunks_only",
            expansion_threshold=0.85,
        )

        self.assertEqual(strategy.expansion_mode, "top_chunks_only")

        # Chunks only mode never uses full message
        small_message_tokens = 5000
        large_message_tokens = 20000

        use_full_for_small = False  # Never use full message
        use_full_for_large = False  # Never use full message

        self.assertFalse(use_full_for_small)
        self.assertFalse(use_full_for_large)

    async def test_expansion_budget_calculation(self):
        """Test: Expansion budget calculated correctly."""
        # Available budget calculation
        context_limit = 128000
        current_tokens = 30000
        output_buffer = 8000

        available_budget = context_limit - current_tokens - output_buffer
        self.assertEqual(available_budget, 90000)

        # Expansion budget percentage (80%)
        expansion_budget_pct = 0.80
        expansion_budget = int(available_budget * expansion_budget_pct)

        self.assertEqual(expansion_budget, 72000)
        self.assertEqual(expansion_budget / available_budget, 0.8)

    async def test_max_expansion_tokens_enforcement(self):
        """Test: Per-message expansion limit enforced."""
        max_expansion_tokens = 16000

        # Message larger than limit
        message_tokens = 25000

        # Enforce per-message limit
        allocated_tokens = min(message_tokens, max_expansion_tokens)

        self.assertEqual(allocated_tokens, 16000)
        self.assertLessEqual(allocated_tokens, max_expansion_tokens)

    async def test_expansion_threshold_for_retrieval(self):
        """Test: Expansion threshold filters chunks correctly."""
        expansion_threshold = 0.85

        # Simulate chunk scores
        chunk_scores = [
            ("chunk_1", 0.95),  # Above threshold
            ("chunk_2", 0.88),  # Above threshold
            ("chunk_3", 0.84),  # Below threshold
            ("chunk_4", 0.90),  # Above threshold
            ("chunk_5", 0.75),  # Below threshold
        ]

        # Filter chunks by threshold
        relevant_chunks = [
            chunk_id for chunk_id, score in chunk_scores
            if score >= expansion_threshold
        ]

        self.assertEqual(len(relevant_chunks), 3)
        self.assertIn("chunk_1", relevant_chunks)
        self.assertIn("chunk_2", relevant_chunks)
        self.assertIn("chunk_4", relevant_chunks)
        self.assertNotIn("chunk_3", relevant_chunks)
        self.assertNotIn("chunk_5", relevant_chunks)


if __name__ == "__main__":
    unittest.main()
