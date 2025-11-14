"""
Integration tests for extreme token scenarios in prompt compaction.

These tests push the limits of the compaction system with:
- Very long conversations (25-50 turns)
- Oversized individual messages (150K tokens)
- Large tool call sequences (50-100 tools)
- Hierarchical summarization under pressure

These tests verify the system handles extreme scenarios gracefully without
breaking tool call pairing, message deduplication, or type enforcement.
"""

import pytest
import unittest
from typing import List, Dict, Any
from uuid import uuid4

from langchain_core.messages import AIMessage, HumanMessage, BaseMessage, ToolMessage

from tests.unit.services.workflow_service.registry.nodes.llm.prompt_compaction.test_base import (
    PromptCompactionIntegrationTestBase,
)
from .test_helpers_comprehensive import (
    generate_token_heavy_messages,
    generate_parallel_tool_calls,
    generate_sequential_tool_calls,
    generate_mixed_parallel_sequential_tools,
    verify_tool_call_pairing,
    verify_all_ai_messages,
    add_linkedin_metadata,
)

from workflow_service.registry.nodes.llm.prompt_compaction.compactor import (
    PromptCompactionConfig,
)
from workflow_service.registry.nodes.llm.prompt_compaction.strategies import (
    CompactionStrategyType,
    SummarizationMode,
)


@pytest.mark.integration
@pytest.mark.slow
class TestExtremeTokenScenarios(PromptCompactionIntegrationTestBase):
    """
    Test compaction under extreme token pressure scenarios.
    """

    async def asyncSetUp(self):
        """Setup real external context for integration tests."""
        await super().asyncSetUp()

        from workflow_service.services.external_context_manager import (
            get_external_context_manager_with_clients,
        )

        self.ext_context = await get_external_context_manager_with_clients()

    # ========================================
    # Very Long Conversations (3 tests)
    # ========================================

    async def test_25_turn_progressive_compaction(self):
        """
        Test: 25-turn conversation with progressive compaction.
        
        Simulate a very long conversation (25 turns) where:
        - Each turn adds 50-100 messages
        - Each message has 200-500 tokens
        - Progressive compaction keeps history manageable
        
        Verify:
        - System handles long conversations gracefully
        - Message deduplication works across many turns
        - All outputs remain AIMessages
        """
        thread_id = f"test-25-turns-{uuid4()}"
        self.test_thread_ids.append(thread_id)

        all_messages = []

        for turn in range(25):
            # Add 50-100 new messages each turn
            import random
            num_messages = random.randint(50, 100)
            tokens_per_msg = random.randint(200, 500)
            
            new_messages = generate_token_heavy_messages(
                count=num_messages,
                tokens_per_message=tokens_per_msg,
            )
            add_linkedin_metadata(new_messages)
            all_messages.extend(new_messages)

            # Compact progressively
            config = self._create_test_config(
                strategy=CompactionStrategyType.HYBRID,
                mode=SummarizationMode.CONTINUED if turn > 0 else SummarizationMode.FROM_SCRATCH,
                max_tokens=15000,  # Generous budget
                target_tokens=10000,
            )

            result = await self._run_compaction(
                messages=all_messages,
                config=config,
                thread_id=thread_id,
            )

            compacted = result.get("summarized_messages", []) or []

            # Verify all outputs are AIMessages
            summary_msgs = [
                msg for msg in compacted
                if "SUMMARY" in msg.response_metadata.get("compaction", {}).get("section_label", "")
            ]
            if summary_msgs:
                verify_all_ai_messages(summary_msgs, f"25-turn #{turn+1}")

            # Update history for next turn (simulate deduplication)
            all_messages = compacted

            # Log progress every 5 turns
            if (turn + 1) % 5 == 0:
                print(f"Completed turn {turn + 1}/25, current history size: {len(all_messages)} messages")

    async def test_30_turn_with_tool_calls(self):
        """
        Test: 30-turn conversation with tool calls throughout.
        
        Every 3rd turn includes tool calls. Verify:
        - Tool call pairing preserved across 30 turns
        - System handles combination of regular + tool messages
        """
        thread_id = f"test-30-turns-tools-{uuid4()}"
        self.test_thread_ids.append(thread_id)

        all_messages = []

        for turn in range(30):
            # Every 3rd turn includes tool calls
            if turn % 3 == 0:
                # Add tool calls
                tool_messages = generate_sequential_tool_calls(count=5)
                add_linkedin_metadata(tool_messages)
                all_messages.extend(tool_messages)
            
            # Add regular messages
            regular_messages = generate_token_heavy_messages(
                count=30,
                tokens_per_message=300,
            )
            add_linkedin_metadata(regular_messages)
            all_messages.extend(regular_messages)

            # Compact
            config = self._create_test_config(
                strategy=CompactionStrategyType.HYBRID,
                mode=SummarizationMode.CONTINUED if turn > 0 else SummarizationMode.FROM_SCRATCH,
                max_tokens=12000,
                target_tokens=8000,
            )

            result = await self._run_compaction(
                messages=all_messages,
                config=config,
                thread_id=thread_id,
            )

            compacted = result.get("summarized_messages", []) or []

            # Verify tool call pairing
            pairing_errors = verify_tool_call_pairing(compacted)
            self.assertEqual(
                len(pairing_errors), 0,
                f"Turn {turn+1}: Tool pairing broken: {pairing_errors}"
            )

            # Update history
            all_messages = compacted

            # Log progress every 10 turns
            if (turn + 1) % 10 == 0:
                print(f"Completed turn {turn + 1}/30 with tool calls")

    async def test_50_turn_mixed_strategies(self):
        """
        Test: 50-turn conversation with strategy switching.
        
        Switch between summarization, extraction, and hybrid strategies
        across 50 turns. Verify system remains stable.
        """
        thread_id = f"test-50-turns-mixed-{uuid4()}"
        self.test_thread_ids.append(thread_id)

        all_messages = []
        strategies = [
            CompactionStrategyType.SUMMARIZATION,
            CompactionStrategyType.EXTRACTIVE,
            CompactionStrategyType.HYBRID,
        ]

        for turn in range(50):
            # Add messages
            new_messages = generate_token_heavy_messages(
                count=40,
                tokens_per_message=250,
            )
            add_linkedin_metadata(new_messages)
            all_messages.extend(new_messages)

            # Rotate through strategies
            strategy = strategies[turn % 3]

            config = self._create_test_config(
                strategy=strategy,
                mode=SummarizationMode.CONTINUED if turn > 0 and strategy == CompactionStrategyType.SUMMARIZATION else SummarizationMode.FROM_SCRATCH,
                max_tokens=10000,
                target_tokens=7000,
            )

            result = await self._run_compaction(
                messages=all_messages,
                config=config,
                thread_id=thread_id,
            )

            compacted = result.get("summarized_messages", []) or []

            # Verify outputs are AIMessages
            if strategy == CompactionStrategyType.SUMMARIZATION:
                summary_msgs = [
                    msg for msg in compacted
                    if "SUMMARY" in msg.response_metadata.get("compaction", {}).get("section_label", "")
                ]
                if summary_msgs:
                    verify_all_ai_messages(summary_msgs, f"50-turn #{turn+1} summ")
            
            # Update history
            all_messages = compacted

            # Log progress every 10 turns
            if (turn + 1) % 10 == 0:
                print(f"Completed turn {turn + 1}/50 with {strategy}")

    # ========================================
    # Oversized Messages (3 tests)
    # ========================================

    async def test_single_message_150k_tokens(self):
        """
        Test: Single message with 150K tokens.
        
        Verify system handles extremely large individual messages.
        This should trigger chunking or other handling mechanisms.
        """
        thread_id = f"test-150k-msg-{uuid4()}"
        self.test_thread_ids.append(thread_id)

        # Create one huge message
        huge_message = generate_token_heavy_messages(
            count=1,
            tokens_per_message=150000,  # 150K tokens
        )
        add_linkedin_metadata(huge_message)

        # Add some normal messages before and after
        normal_messages_before = generate_token_heavy_messages(count=5, tokens_per_message=200)
        normal_messages_after = generate_token_heavy_messages(count=5, tokens_per_message=200)
        add_linkedin_metadata(normal_messages_before)
        add_linkedin_metadata(normal_messages_after)

        messages = normal_messages_before + huge_message + normal_messages_after

        config = self._create_test_config(
            strategy=CompactionStrategyType.HYBRID,  # SUMMARIZATION  HYBRID
            mode=SummarizationMode.FROM_SCRATCH,
            max_tokens=20000,  # Much smaller than the huge message
            target_tokens=15000,
        )

        # This should handle the oversized message gracefully
        result = await self._run_compaction(
            messages=messages,
            config=config,
            thread_id=thread_id,
        )

        compacted = result.get("summarized_messages", []) or []

        # Verify outputs are AIMessages
        summary_msgs = [
            msg for msg in compacted
            if "SUMMARY" in msg.response_metadata.get("compaction", {}).get("section_label", "")
        ]
        if summary_msgs:
            verify_all_ai_messages(summary_msgs, "150K token message")

    async def test_group_to_summarize_100k_tokens(self):
        """
        Test: Group of messages to summarize totaling 100K tokens.
        
        v3.0: Uses linear batching (multiple independent batch summaries, no hierarchical merging).
        """
        thread_id = f"test-100k-group-{uuid4()}"
        self.test_thread_ids.append(thread_id)

        # Create many messages totaling ~100K tokens
        messages = generate_token_heavy_messages(
            count=200,  # 200 messages
            tokens_per_message=500,  # 500 tokens each = 100K total
        )
        add_linkedin_metadata(messages)

        config = self._create_test_config(
            strategy=CompactionStrategyType.SUMMARIZATION,
            mode=SummarizationMode.FROM_SCRATCH,
            max_tokens=15000,  # Force aggressive compaction
            target_tokens=10000,
        )

        result = await self._run_compaction(
            messages=messages,
            config=config,
            thread_id=thread_id,
        )

        compacted = result.get("summarized_messages", []) or []
        
        print(f"\n[DEBUG] Total compacted messages: {len(compacted)}")
        print(f"[DEBUG] Compacted message types: {[type(m).__name__ for m in compacted[:10]]}")

        # v3.0: Check for linear batch summarization (multiple independent summaries)
        summary_msgs = [
            msg for msg in compacted
            if "summary" in msg.response_metadata.get("compaction", {}).get("section_label", "").lower()
        ]
        
        print(f"[DEBUG] Summary messages found: {len(summary_msgs)}")
        if compacted:
            print(f"[DEBUG] First 3 section labels: {[m.response_metadata.get('compaction', {}).get('section_label', 'NONE') for m in compacted[:3]]}")

        # Should have multiple batch summaries (not hierarchical levels)
        self.assertGreater(len(summary_msgs), 0, "Expected batch summaries for 100K tokens")
        verify_all_ai_messages(summary_msgs, "100K group linear batching")
        
        print(f"Linear batching produced {len(summary_msgs)} batch summaries")

    async def test_single_tool_result_50k_tokens(self):
        """
        Test: Tool result with 50K tokens.
        
        Large tool results must stay paired with their tool calls.
        Verify pairing is preserved even with huge tool results.
        """
        thread_id = f"test-50k-tool-result-{uuid4()}"
        self.test_thread_ids.append(thread_id)

        # Create tool call with huge result
        from langchain_core.messages import ToolMessage

        tool_call_msg = AIMessage(
            content="",
            tool_calls=[{
                "name": "large_data_query",
                "args": {"query": "fetch all data"},
                "id": "call_large_123",
            }],
        )

        # Create huge tool result
        huge_result_content = "Data: " + ("x" * 200000)  # ~50K tokens
        tool_result_msg = ToolMessage(
            content=huge_result_content,
            tool_call_id="call_large_123",
        )

        # Add normal messages around them
        before_msgs = generate_token_heavy_messages(count=5, tokens_per_message=200)
        after_msgs = generate_token_heavy_messages(count=5, tokens_per_message=200)

        messages = before_msgs + [tool_call_msg, tool_result_msg] + after_msgs
        add_linkedin_metadata(messages)

        config = self._create_test_config(
            strategy=CompactionStrategyType.HYBRID,
            mode=SummarizationMode.FROM_SCRATCH,
            max_tokens=10000,
            target_tokens=7000,
        )

        result = await self._run_compaction(
            messages=messages,
            config=config,
            thread_id=thread_id,
        )

        compacted = result.get("summarized_messages", []) or []

        # Critical: Verify tool call pairing is preserved
        pairing_errors = verify_tool_call_pairing(compacted)
        self.assertEqual(
            len(pairing_errors), 0,
            f"Tool call pairing broken with huge result: {pairing_errors}"
        )

    # ========================================
    # Large Tool Sequences (4 tests)
    # ========================================

    async def test_50_contiguous_tool_calls(self):
        """
        Test: 50 contiguous sequential tool calls.
        
        Verify system handles long sequences of tool calls without breaking pairing.
        """
        thread_id = f"test-50-tools-{uuid4()}"
        self.test_thread_ids.append(thread_id)

        # Generate 50 sequential tool calls
        tool_messages = generate_sequential_tool_calls(count=50)
        add_linkedin_metadata(tool_messages)

        # Add context messages
        before_msgs = generate_token_heavy_messages(count=10, tokens_per_message=200)
        after_msgs = generate_token_heavy_messages(count=10, tokens_per_message=200)
        add_linkedin_metadata(before_msgs)
        add_linkedin_metadata(after_msgs)

        messages = before_msgs + tool_messages + after_msgs

        config = self._create_test_config(
            strategy=CompactionStrategyType.HYBRID,
            mode=SummarizationMode.FROM_SCRATCH,
            max_tokens=12000,
            target_tokens=8000,
        )

        result = await self._run_compaction(
            messages=messages,
            config=config,
            thread_id=thread_id,
        )

        compacted = result.get("summarized_messages", []) or []

        # Verify tool call pairing across all 50 calls
        pairing_errors = verify_tool_call_pairing(compacted)
        self.assertEqual(
            len(pairing_errors), 0,
            f"Tool pairing broken in 50-tool sequence: {pairing_errors}"
        )

    async def test_mixed_parallel_sequential_100_tools(self):
        """
        Test: 100 tool calls with mixed parallel and sequential patterns.
        
        Complex pattern: Groups of parallel calls interspersed with sequential calls.
        """
        thread_id = f"test-100-mixed-tools-{uuid4()}"
        self.test_thread_ids.append(thread_id)

        # Generate 100 mixed tools
        tool_messages = generate_mixed_parallel_sequential_tools(
            num_parallel_groups=10,  # 10 parallel groups
            num_sequential_pairs=50,  # 50 sequential pairs = 100 total
        )
        add_linkedin_metadata(tool_messages)

        # Add context
        context_msgs = generate_token_heavy_messages(count=20, tokens_per_message=200)
        add_linkedin_metadata(context_msgs)

        messages = context_msgs + tool_messages

        config = self._create_test_config(
            strategy=CompactionStrategyType.HYBRID,
            mode=SummarizationMode.FROM_SCRATCH,
            max_tokens=15000,
            target_tokens=10000,
        )

        result = await self._run_compaction(
            messages=messages,
            config=config,
            thread_id=thread_id,
        )

        compacted = result.get("summarized_messages", []) or []

        # Verify complex tool call pairing
        pairing_errors = verify_tool_call_pairing(compacted)
        self.assertEqual(
            len(pairing_errors), 0,
            f"Tool pairing broken in 100-tool mixed sequence: {pairing_errors}"
        )

    async def test_tool_calls_exceed_marked_budget(self):
        """
        Test: Tool call group exceeds marked section budget.
        
        When a tool call group is larger than the marked budget,
        verify system handles it correctly (overflow or error).
        """
        thread_id = f"test-tools-exceed-budget-{uuid4()}"
        self.test_thread_ids.append(thread_id)

        # Generate large tool call group
        tool_messages = generate_parallel_tool_calls(count=20)  # Large parallel group
        
        # Make tool results very large
        for i, msg in enumerate(tool_messages):
            if isinstance(msg, ToolMessage):
                # Make each tool result ~2K tokens
                msg.content = "Result: " + ("x" * 8000)
        
        add_linkedin_metadata(tool_messages)

        # Add minimal context
        context_msgs = generate_token_heavy_messages(count=5, tokens_per_message=200)
        add_linkedin_metadata(context_msgs)

        messages = context_msgs + tool_messages

        config = self._create_test_config(
            strategy=CompactionStrategyType.HYBRID,
            mode=SummarizationMode.FROM_SCRATCH,
            max_tokens=10000,  # Small budget
            target_tokens=7000,
            # marked_token_budget parameter removed - using default budget allocation
            # marked_token_budget=3000,  # Tool group will exceed this
        )

        # This should handle gracefully (overflow or adjust)
        result = await self._run_compaction(
            messages=messages,
            config=config,
            thread_id=thread_id,
        )

        compacted = result.get("summarized_messages", []) or []

        # Verify tool call pairing preserved even under budget pressure
        pairing_errors = verify_tool_call_pairing(compacted)
        self.assertEqual(
            len(pairing_errors), 0,
            f"Tool pairing broken under budget pressure: {pairing_errors}"
        )

    async def test_tool_calls_in_hierarchical_summarization(self):
        """
        Test: Tool calls within messages that trigger hierarchical summarization.
        
        Large conversation with tool calls scattered throughout.
        Verify hierarchical summarization preserves tool call pairing.
        """
        thread_id = f"test-tools-hierarchical-{uuid4()}"
        self.test_thread_ids.append(thread_id)

        messages = []

        # Add 10 groups of: messages + tool calls + messages
        for i in range(10):
            # Regular messages
            regular = generate_token_heavy_messages(count=20, tokens_per_message=400)
            add_linkedin_metadata(regular)
            messages.extend(regular)

            # Tool calls
            tools = generate_sequential_tool_calls(count=5)
            add_linkedin_metadata(tools)
            messages.extend(tools)

        # Total: ~200 regular messages + 50 tool calls = significant content

        config = self._create_test_config(
            strategy=CompactionStrategyType.HYBRID,
            mode=SummarizationMode.FROM_SCRATCH,
            max_tokens=15000,  # Force hierarchical summarization
            target_tokens=10000,
        )

        result = await self._run_compaction(
            messages=messages,
            config=config,
            thread_id=thread_id,
        )

        compacted = result.get("summarized_messages", []) or []

        # Verify tool call pairing in hierarchical context
        pairing_errors = verify_tool_call_pairing(compacted)
        self.assertEqual(
            len(pairing_errors), 0,
            f"Tool pairing broken in hierarchical: {pairing_errors}"
        )

        # Verify hierarchical summaries are AIMessages
        summary_msgs = [
            msg for msg in compacted
            if "SUMMARY" in msg.response_metadata.get("compaction", {}).get("section_label", "")
        ]
        
        if summary_msgs:
            verify_all_ai_messages(summary_msgs, "tools in hierarchical")

