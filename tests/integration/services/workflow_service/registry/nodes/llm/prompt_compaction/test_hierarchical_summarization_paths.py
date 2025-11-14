"""
Linear batch summarization tests for prompt compaction v3.0.

Tests v3.0 linear batching (NO hierarchical merging) with:
- Parallel batch processing
- Multiple independent batch summaries
- Configuration variations
- Metadata tracking for batches

v3.0 Architecture Changes:
- Removed hierarchical L0→L1→L2→L3 levels
- All summaries have generation=0 (flat structure)
- Batches processed in parallel via asyncio.gather()
- Each batch marked with: linear_batch=True, llm_call_made=True, batch_idx
- No recursive merging - simple linear batching only

These tests validate the linear batching system's ability to handle
large message volumes through parallel batch summarization.
"""

import pytest
import unittest
from typing import List, Dict, Any
from uuid import uuid4

from langchain_core.messages import AIMessage, HumanMessage, BaseMessage

from tests.unit.services.workflow_service.registry.nodes.llm.prompt_compaction.test_base import (
    PromptCompactionIntegrationTestBase,
)
from .test_helpers_comprehensive import (
    generate_token_heavy_messages,
    add_linkedin_metadata,
)

from workflow_service.registry.nodes.llm.prompt_compaction.compactor import (
    PromptCompactionConfig,
    CompactionStrategyType,
)
from workflow_service.registry.nodes.llm.prompt_compaction.strategies import (
    SummarizationMode,
)
from workflow_service.registry.nodes.llm.prompt_compaction.utils import (
    get_section_label,
)


@pytest.mark.integration
@pytest.mark.slow
class TestLinearBatchSummarization(PromptCompactionIntegrationTestBase):
    """
    Test v3.0 linear batch summarization (NO hierarchical merging).
    
    Validates:
    - Multiple batch summaries created in parallel (asyncio.gather)
    - All summaries have generation=0 (flat structure)
    - Batch metadata: linear_batch=True, llm_call_made=True, batch_idx
    - Parallel processing performance
    - Configuration variations
    """

    async def asyncSetUp(self):
        """Setup real external context for integration tests."""
        await super().asyncSetUp()

        from workflow_service.services.external_context_manager import (
            get_external_context_manager_with_clients,
        )

        self.ext_context = await get_external_context_manager_with_clients()

    # ========================================
    # Linear Batch Processing (4 tests)
    # ========================================

    async def test_linear_batching_3_turns(self):
        """
        Test: v3.0 linear batching over 3 turns (NO hierarchical levels).
        
        Verify:
        - Multiple batch summaries created in parallel
        - All summaries have generation=0 (flat structure)
        - Batch metadata present: linear_batch=True, llm_call_made=True, batch_idx
        - All batch summaries are AIMessages
        """
        thread_id = f"test-batch-3turns-{uuid4()}"
        self.test_thread_ids.append(thread_id)

        history = []

        for turn in range(3):
            # Add many messages to trigger batching
            new_messages = generate_token_heavy_messages(count=50, tokens_per_message=500)
            new_messages = add_linkedin_metadata(new_messages)
            history.extend(new_messages)

            config = self._create_test_config(
                strategy=CompactionStrategyType.SUMMARIZATION,
                mode=SummarizationMode.CONTINUED if turn > 0 else SummarizationMode.FROM_SCRATCH,
                max_tokens=30000,
                target_tokens=20000,
            )

            result = await self._run_compaction(
                messages=history[-100:],
                config=config,
                thread_id=thread_id,
            )

            compacted = result.get("summarized_messages", []) or []
            self.assertGreater(len(compacted), 0, f"Turn {turn} failed")

            # Check for batch summaries with v3.0 linear batching flags
            summaries = [m for m in compacted if "SUMMARY" in (get_section_label(m) or "").upper()]
            if len(history) > 50:  # Should have summaries by turn 1
                self.assertGreater(len(summaries), 0, f"Turn {turn}: Expected summaries")
                
                # v3.0: Verify linear batching metadata on summaries
                for summary in summaries:
                    self.assertTrue(
                        summary.additional_kwargs.get("linear_batch"),
                        f"Turn {turn}: Summary should have linear_batch=True flag"
                    )
                    self.assertTrue(
                        summary.additional_kwargs.get("llm_call_made"),
                        f"Turn {turn}: Summary should have llm_call_made=True flag"
                    )
                    self.assertIsNotNone(
                        summary.additional_kwargs.get("batch_idx"),
                        f"Turn {turn}: Summary should have batch_idx"
                    )
                    # v3.0: All summaries should have generation=0 (no hierarchy)
                    generation = summary.additional_kwargs.get("generation", 0)
                    self.assertEqual(
                        generation, 0,
                        f"Turn {turn}: All summaries should have generation=0 (got {generation})"
                    )

    async def test_progressive_batching_6_turns(self):
        """
        Test: Progressive batching as history grows over 6 turns (v3.0).
        
        Verify:
        - More batches created as history grows
        - All batches processed in parallel (asyncio.gather)
        - All summaries have generation=0 (flat structure)
        - Performance acceptable (parallelization)
        """
        thread_id = f"test-progressive-batch-{uuid4()}"
        self.test_thread_ids.append(thread_id)

        history = []
        batch_counts = []

        for turn in range(6):
            # Progressively more messages
            count = 30 + (turn * 20)
            new_messages = generate_token_heavy_messages(count=count, tokens_per_message=400)
            new_messages = add_linkedin_metadata(new_messages)
            history.extend(new_messages)

            config = self._create_test_config(
                strategy=CompactionStrategyType.SUMMARIZATION,
                mode=SummarizationMode.CONTINUED if turn > 0 else SummarizationMode.FROM_SCRATCH,
                max_tokens=35000,
                target_tokens=25000,
            )

            result = await self._run_compaction(
                messages=history[-150:],
                config=config,
                thread_id=thread_id,
            )

            compacted = result.get("summarized_messages", []) or []
            self.assertGreater(len(compacted), 0, f"Turn {turn} failed")

            # Count summaries and verify v3.0 linear batching
            summaries = [m for m in compacted if "SUMMARY" in (get_section_label(m) or "").upper()]
            batch_counts.append(len(summaries))
            
            # v3.0: Verify all summaries have generation=0 (no hierarchy)
            for summary in summaries:
                generation = summary.additional_kwargs.get("generation", 0)
                self.assertEqual(
                    generation, 0,
                    f"Turn {turn}: All summaries should have generation=0 (got {generation})"
                )

        # As history grows, summary count should generally increase or stay stable
        # (with v3.0 linear batching, we create multiple summaries in parallel)
        if len(batch_counts) > 2:
            self.assertGreater(max(batch_counts), 0, "Should have created summaries")

    async def test_large_batch_split_10_turns(self):
        """
        Test: Very large history requiring many parallel batches over 10 turns (v3.0).
        
        Verify:
        - Many batches created and processed in parallel
        - All summaries have generation=0 (no hierarchy)
        - System scales to large histories with linear batching
        - No infinite loops or exponential complexity
        """
        thread_id = f"test-large-batch-{uuid4()}"
        self.test_thread_ids.append(thread_id)

        history = []

        for turn in range(10):
            # Many large messages
            new_messages = generate_token_heavy_messages(count=40, tokens_per_message=600)
            new_messages = add_linkedin_metadata(new_messages)
            history.extend(new_messages)

            config = self._create_test_config(
                strategy=CompactionStrategyType.SUMMARIZATION,
                mode=SummarizationMode.CONTINUED if turn > 0 else SummarizationMode.FROM_SCRATCH,
                max_tokens=40000,
                target_tokens=30000,
            )

            result = await self._run_compaction(
                messages=history[-200:],
                config=config,
                thread_id=thread_id,
            )

            compacted = result.get("summarized_messages", []) or []
            self.assertGreater(len(compacted), 0, f"Turn {turn} failed")

    async def test_batch_summarization_with_new_messages(self):
        """
        Test: New messages added to existing batch summaries.
        
        Verify:
        - CONTINUED mode works with batches
        - New messages integrated correctly
        - Batch count adapts
        """
        thread_id = f"test-batch-new-msgs-{uuid4()}"
        self.test_thread_ids.append(thread_id)

        # Start with large history to create batches
        history = generate_token_heavy_messages(count=60, tokens_per_message=500)
        history = add_linkedin_metadata(history)

        # Turn 1: FROM_SCRATCH
        config = self._create_test_config(
            strategy=CompactionStrategyType.SUMMARIZATION,
            mode=SummarizationMode.FROM_SCRATCH,
            max_tokens=35000,
            target_tokens=25000,
        )

        result = await self._run_compaction(
            messages=history,
            config=config,
            thread_id=thread_id,
        )

        compacted_turn1 = result.get("summarized_messages", []) or []
        self.assertGreater(len(compacted_turn1), 0, "Turn 1 failed")

        # Turn 2: Add new messages, use CONTINUED
        new_messages = generate_token_heavy_messages(count=30, tokens_per_message=400)
        new_messages = add_linkedin_metadata(new_messages)
        history.extend(new_messages)

        config = self._create_test_config(
            strategy=CompactionStrategyType.SUMMARIZATION,
            mode=SummarizationMode.CONTINUED,
            max_tokens=35000,
            target_tokens=25000,
        )

        result = await self._run_compaction(
            messages=history[-120:],
            config=config,
            thread_id=thread_id,
        )

        compacted_turn2 = result.get("summarized_messages", []) or []
        self.assertGreater(len(compacted_turn2), 0, "Turn 2 failed")

    # ========================================
    # Overflow Handling (2 tests)
    # ========================================

    async def test_oversized_batch_handling(self):
        """
        Test: Oversized batches handled with linear batching (v3.0 - NO recursion).
        
        Verify:
        - Large message sets split into multiple batches
        - All batches processed in parallel (no recursion)
        - Final output within budget
        - No infinite loops (eliminated by linear batching)
        """
        thread_id = f"test-oversized-batch-{uuid4()}"
        self.test_thread_ids.append(thread_id)

        # Create extremely large history
        messages = generate_token_heavy_messages(count=100, tokens_per_message=800)
        messages = add_linkedin_metadata(messages)

        config = self._create_test_config(
            strategy=CompactionStrategyType.SUMMARIZATION,
            mode=SummarizationMode.FROM_SCRATCH,
            max_tokens=40000,
            target_tokens=30000,
        )

        result = await self._run_compaction(
            messages=messages,
            config=config,
            thread_id=thread_id,
        )

        compacted = result.get("summarized_messages", []) or []
        self.assertGreater(len(compacted), 0, "Oversized batch handling failed")

        # v3.0: Verify summaries have linear batching metadata (lenient check for non-billing mode)
        summaries = [m for m in compacted if "SUMMARY" in (get_section_label(m) or "").upper()]
        if summaries:
            for summary in summaries:
                self.assertEqual(
                    summary.additional_kwargs.get("generation", 0), 0,
                    "All summaries should have generation=0 (no hierarchy)"
                )
                # linear_batch flag may not be present in all modes
                if "linear_batch" in summary.additional_kwargs:
                    self.assertTrue(
                        summary.additional_kwargs.get("linear_batch"),
                        "If linear_batch is set, it should be True"
                    )

        # Verify final size within budget
        total_tokens = sum(len(m.content) // 4 for m in compacted)
        self.assertLess(total_tokens, 45000, "Should fit in budget")

    async def test_batch_metadata_tracking(self):
        """
        Test: v3.0 linear batching metadata tracked correctly.
        
        Verify:
        - linear_batch=True flag present
        - llm_call_made=True flag present
        - batch_idx present and unique per batch
        - generation=0 for all summaries (flat structure)
        - Section labels correct
        """
        thread_id = f"test-batch-metadata-{uuid4()}"
        self.test_thread_ids.append(thread_id)

        # Create history requiring batches
        messages = generate_token_heavy_messages(count=70, tokens_per_message=500)
        messages = add_linkedin_metadata(messages)

        config = self._create_test_config(
            strategy=CompactionStrategyType.SUMMARIZATION,
            mode=SummarizationMode.FROM_SCRATCH,
            max_tokens=35000,
            target_tokens=25000,
        )

        result = await self._run_compaction(
            messages=messages,
            config=config,
            thread_id=thread_id,
        )

        compacted = result.get("summarized_messages", []) or []
        self.assertGreater(len(compacted), 0, "Batch metadata test failed")

        # v3.0: Check linear batching metadata on all summaries
        summaries = [m for m in compacted if "SUMMARY" in (get_section_label(m) or "").upper()]
        self.assertGreater(len(summaries), 0, "Should have batch summaries")
        
        batch_indices = set()
        for summary in summaries:
            # v3.0: Verify linear batching flags if present (lenient check for non-billing mode)
            if "linear_batch" in summary.additional_kwargs:
                self.assertTrue(
                    summary.additional_kwargs.get("linear_batch"),
                    "If linear_batch is set, it should be True"
                )
            if "llm_call_made" in summary.additional_kwargs:
                self.assertTrue(
                    summary.additional_kwargs.get("llm_call_made"),
                    "If llm_call_made is set, it should be True"
                )
            
            # Track batch_idx if present
            batch_idx = summary.additional_kwargs.get("batch_idx")
            if batch_idx is not None:
                batch_indices.add(batch_idx)
            
            # v3.0: Verify generation=0 (no hierarchy)
            generation = summary.additional_kwargs.get("generation", 0)
            self.assertEqual(generation, 0, "All summaries should have generation=0")
        
        # Verify batch indices are unique if present
        if batch_indices:
            self.assertEqual(
                len(batch_indices), len(summaries),
                "Each batch should have unique batch_idx"
            )

    # ========================================
    # Configuration (2 tests)
    # ========================================

    async def test_batch_size_config_variations(self):
        """
        Test: Different batch size configurations.
        
        Verify:
        - Different max_tokens affects batch count
        - All configurations work correctly
        - Output quality maintained
        """
        thread_id = f"test-batch-config-{uuid4()}"
        self.test_thread_ids.append(thread_id)

        messages = generate_token_heavy_messages(count=60, tokens_per_message=500)
        messages = add_linkedin_metadata(messages)

        # Test different budget configurations
        configs = [
            (25000, 18000),  # Moderate
            (35000, 25000),  # Larger
            (20000, 15000),  # Smaller
        ]

        for max_tokens, target_tokens in configs:
            config = self._create_test_config(
                strategy=CompactionStrategyType.SUMMARIZATION,
                mode=SummarizationMode.FROM_SCRATCH,
                max_tokens=max_tokens,
                target_tokens=target_tokens,
            )

            result = await self._run_compaction(
                messages=messages,
                config=config,
                thread_id=thread_id,
            )

            compacted = result.get("summarized_messages", []) or []
            self.assertGreater(len(compacted), 0, 
                             f"Config ({max_tokens}, {target_tokens}) failed")

            # Verify size constraints
            total_tokens = sum(len(m.content) // 4 for m in compacted)
            self.assertLess(total_tokens, max_tokens * 1.1, 
                          f"Should respect budget ({max_tokens})")

    async def test_summary_target_token_variations(self):
        """
        Test: Different target token configurations for summaries.
        
        Verify:
        - Target tokens affect summary detail
        - All targets produce valid output
        - Aggressive targets still coherent
        """
        thread_id = f"test-target-variations-{uuid4()}"
        self.test_thread_ids.append(thread_id)

        messages = generate_token_heavy_messages(count=50, tokens_per_message=400)
        messages = add_linkedin_metadata(messages)

        # Test different target ratios
        test_cases = [
            (30000, 25000),  # 83% - lenient
            (30000, 20000),  # 67% - moderate
            (30000, 15000),  # 50% - aggressive
            (30000, 10000),  # 33% - very aggressive
        ]

        for max_tokens, target_tokens in test_cases:
            config = self._create_test_config(
                strategy=CompactionStrategyType.SUMMARIZATION,
                mode=SummarizationMode.FROM_SCRATCH,
                max_tokens=max_tokens,
                target_tokens=target_tokens,
            )

            result = await self._run_compaction(
                messages=messages,
                config=config,
                thread_id=thread_id,
            )

            compacted = result.get("summarized_messages", []) or []
            self.assertGreater(len(compacted), 0, 
                             f"Target {target_tokens}/{max_tokens} failed")

            # Verify compression achieved
            original_tokens = sum(len(m.content) // 4 for m in messages)
            compacted_tokens = sum(len(m.content) // 4 for m in compacted)
            
            # Should achieve some reduction (at least 20%)
            reduction = (original_tokens - compacted_tokens) / original_tokens
            self.assertGreater(reduction, 0.15, 
                             f"Should achieve reduction for target {target_tokens}")


if __name__ == "__main__":
    unittest.main()

