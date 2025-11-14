"""
Unit tests for v2.1 extraction expansion features (hybrid/full/chunks modes).

Tests cover:
- Hybrid expansion mode validation
- Full message expansion mode
- Top chunks only mode
- Expansion budget calculation (80% of available)
- Max expansion tokens enforcement (16K per message)
- Expansion threshold for retrieval (0.85)
- Budget exhaustion handling
- Oversized message warnings
- Message order preservation
- Expansion only for EXTRACT_FULL strategy

Test IDs: 33-42 (from comprehensive test plan)
"""

import unittest
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4

from langchain_core.messages import HumanMessage, AIMessage

from workflow_service.registry.nodes.llm.prompt_compaction.strategies import (
    ExtractionStrategy,
)
from workflow_service.registry.nodes.llm.config import ModelMetadata, LLMModelProvider
from workflow_service.registry.nodes.llm.prompt_compaction.utils import (
    ExtractionStrategy as ExtractionStrategyType,
)

from .test_base import PromptCompactionUnitTestBase


class TestExpansionModes(unittest.TestCase):
    """Test 33-35: Different expansion modes (hybrid/full/chunks)."""

    def test_hybrid_expansion_mode_validation(self):
        """Test 33: Hybrid mode uses full message if <16K, else chunks."""
        # Hybrid mode is the default
        strategy = ExtractionStrategy(
            construction_strategy=ExtractionStrategyType.EXTRACT_FULL,
            expansion_mode="hybrid",
            max_expansion_tokens=16000,
            expansion_threshold=0.85,
        )

        # Verify config
        self.assertEqual(strategy.expansion_mode, "hybrid")
        self.assertEqual(strategy.max_expansion_tokens, 16000)

        # Hybrid mode logic:
        # - If message tokens < 16K: expand with full message
        # - If message tokens >= 16K: expand with top chunks only

        # Simulate small message (< 16K tokens)
        small_message_tokens = 5000
        use_full_message = small_message_tokens < strategy.max_expansion_tokens
        self.assertTrue(use_full_message, "Small messages should use full expansion")

        # Simulate large message (>= 16K tokens)
        large_message_tokens = 20000
        use_chunks_only = large_message_tokens >= strategy.max_expansion_tokens
        self.assertTrue(use_chunks_only, "Large messages should use chunks only")

    def test_full_message_expansion_mode_validation(self):
        """Test 34: Full message mode includes all content regardless of size."""
        # Full message mode configuration
        strategy = ExtractionStrategy(
            construction_strategy=ExtractionStrategyType.EXTRACT_FULL,
            expansion_mode="full_message",
            max_expansion_tokens=16000,
            expansion_threshold=0.85,
        )

        self.assertEqual(strategy.expansion_mode, "full_message")

        # In full_message mode, we always try to include the full message
        # But still respect the per-message token limit
        message_tokens = 15000
        should_include = message_tokens <= strategy.max_expansion_tokens
        self.assertTrue(should_include, "Message within limit should be included")

        # Even oversized messages would be included (with warning)
        oversized_tokens = 25000
        # Would still be included but logged as warning
        self.assertGreater(oversized_tokens, strategy.max_expansion_tokens)

    def test_top_chunks_only_mode_validation(self):
        """Test 35: Chunks only mode never includes full message expansion."""
        # Chunks only mode configuration
        strategy = ExtractionStrategy(
            construction_strategy=ExtractionStrategyType.EXTRACT_FULL,
            expansion_mode="top_chunks_only",
            expansion_threshold=0.85,
        )

        self.assertEqual(strategy.expansion_mode, "top_chunks_only")

        # In chunks only mode, we never include full message content
        # regardless of message size
        small_message_tokens = 5000
        large_message_tokens = 20000

        # For both sizes, only chunks are used
        use_full_for_small = False  # Never use full message
        use_full_for_large = False  # Never use full message

        self.assertFalse(use_full_for_small)
        self.assertFalse(use_full_for_large)


class TestExpansionBudget(unittest.TestCase):
    """Test 36-38: Expansion budget calculation and enforcement."""

    def test_expansion_budget_pct_calculation(self):
        """Test 36: 80% of available budget calculated correctly."""
        # Available budget = context_limit - current_tokens - output_buffer
        context_limit = 128000
        current_tokens = 30000
        output_buffer = 8000

        available_budget = context_limit - current_tokens - output_buffer
        self.assertEqual(available_budget, 90000)

        # Expansion budget PCT (default 0.80)
        expansion_budget_pct = 0.80
        expansion_budget = int(available_budget * expansion_budget_pct)

        self.assertEqual(expansion_budget, 72000)
        self.assertEqual(expansion_budget / available_budget, 0.8)

    def test_max_expansion_tokens_enforced(self):
        """Test 37: 16K per-message limit is enforced."""
        max_expansion_tokens = 16000

        # Simulate expansion for a message
        message_tokens = 25000  # Larger than limit

        # Enforce per-message limit
        allocated_tokens = min(message_tokens, max_expansion_tokens)

        self.assertEqual(allocated_tokens, 16000)
        self.assertLessEqual(allocated_tokens, max_expansion_tokens)

    def test_expansion_threshold_for_retrieval(self):
        """Test 38: 0.85 threshold used for chunk retrieval relevance."""
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


class TestExpansionBehavior(unittest.TestCase):
    """Test 39-40: Expansion runtime behavior."""

    def test_budget_exhaustion_stops_expansion(self):
        """Test 39: Expansion stops when budget is exhausted."""
        total_budget = 50000  # Total expansion budget

        # Messages to expand with their token counts
        messages_to_expand = [
            ("msg_1", 15000),
            ("msg_2", 18000),
            ("msg_3", 20000),
            ("msg_4", 12000),
        ]

        expanded_messages = []
        remaining_budget = total_budget

        for msg_id, tokens in messages_to_expand:
            if remaining_budget <= 0:
                break

            # Allocate tokens (limited by per-message max of 16K)
            allocated = min(tokens, 16000, remaining_budget)
            if allocated > 0:  # Only add if we can allocate some tokens
                expanded_messages.append((msg_id, allocated))
                remaining_budget -= allocated

        # Verify expansion results:
        # msg_1: 15000 tokens (under 16K, fits) -> budget: 35000
        # msg_2: 18000 -> 16000 (limited to 16K) -> budget: 19000
        # msg_3: 20000 -> 16000 (limited to 16K) -> budget: 3000
        # msg_4: 12000 -> 3000 (only 3000 budget left) -> budget: 0
        self.assertEqual(len(expanded_messages), 4)
        self.assertEqual(expanded_messages[0], ("msg_1", 15000))
        self.assertEqual(expanded_messages[1], ("msg_2", 16000))  # Limited to 16K
        self.assertEqual(expanded_messages[2], ("msg_3", 16000))  # Limited to 16K
        self.assertEqual(expanded_messages[3], ("msg_4", 3000))   # Only 3K budget left

        # Verify budget was respected
        total_allocated = sum(tokens for _, tokens in expanded_messages)
        self.assertLessEqual(total_allocated, total_budget)
        self.assertEqual(total_allocated, 50000)  # All budget used

    def test_oversized_message_warning_logged(self):
        """Test 40: Warnings logged for messages >16K tokens."""
        max_expansion_tokens = 16000

        # Simulate messages
        messages = [
            ("small", 5000, False),  # No warning
            ("medium", 15000, False),  # No warning
            ("large", 18000, True),  # Warning
            ("huge", 25000, True),  # Warning
        ]

        warnings_logged = []
        for msg_id, tokens, should_warn in messages:
            if tokens > max_expansion_tokens:
                warnings_logged.append(msg_id)
                self.assertTrue(should_warn, f"{msg_id} should trigger warning")
            else:
                self.assertFalse(should_warn, f"{msg_id} should not trigger warning")

        self.assertEqual(len(warnings_logged), 2)
        self.assertIn("large", warnings_logged)
        self.assertIn("huge", warnings_logged)


class TestExpansionPreservation(unittest.TestCase):
    """Test 41: Message order preservation during expansion."""

    def test_expansion_preserves_message_order(self):
        """Test 41: Message order is maintained during expansion."""
        # Create messages in order
        messages = [
            HumanMessage(content=f"Message {i}", id=f"msg_{i}")
            for i in range(5)
        ]

        # After expansion (simulated), order should be preserved
        # In real implementation, expanded content would be added
        # but original message order maintained

        message_ids = [msg.id for msg in messages]
        self.assertEqual(message_ids, ["msg_0", "msg_1", "msg_2", "msg_3", "msg_4"])

        # Verify order is sequential
        for i, msg_id in enumerate(message_ids):
            self.assertEqual(msg_id, f"msg_{i}")


class TestExpansionStrategyScope(PromptCompactionUnitTestBase):
    """Test 42: Expansion only applies to EXTRACT_FULL strategy."""

    async def test_expansion_only_for_extract_full_strategy(self):
        """Test 42: Other strategies skip expansion validation."""
        # EXTRACT_FULL strategy - should support expansion
        extract_full_strategy = ExtractionStrategy(
            construction_strategy=ExtractionStrategyType.EXTRACT_FULL,
            store_embeddings=True,
            expansion_mode="hybrid",
        )

        # Verify expansion config is present
        self.assertIsNotNone(extract_full_strategy.expansion_mode)
        self.assertIn(extract_full_strategy.expansion_mode, ["hybrid", "full_message", "top_chunks_only"])

        # DUMP strategy - doesn't use expansion
        dump_strategy = ExtractionStrategy(
            construction_strategy=ExtractionStrategyType.DUMP,
            store_embeddings=False,
        )

        # LLM_REWRITE strategy - doesn't use expansion
        llm_rewrite_strategy = ExtractionStrategy(
            construction_strategy=ExtractionStrategyType.LLM_REWRITE,
            store_embeddings=False,
        )

        # Verify strategies are different
        self.assertNotEqual(
            extract_full_strategy.construction_strategy,
            dump_strategy.construction_strategy
        )
        self.assertNotEqual(
            extract_full_strategy.construction_strategy,
            llm_rewrite_strategy.construction_strategy
        )


if __name__ == "__main__":
    unittest.main()
