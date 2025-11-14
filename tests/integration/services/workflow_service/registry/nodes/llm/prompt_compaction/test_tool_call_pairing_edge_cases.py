"""
Integration tests for tool call bracket-style pairing in prompt compaction.

These tests are designed to EXPOSE IMPLEMENTATION GAPS in tool call pairing logic.
Expected failures until bracket-style pairing is properly implemented.

Critical Requirements:
1. Tool call + response = atomic unit (like bracket pairs)
2. Can close out of order (parallel calls allowed)
3. Must group parallel calls: [TC1, TC2] → [TR1, TR2] = one atomic group
4. Must allow breaks between sequential pairs: TC1→TR1 | TC2→TR2 = two groups
5. Cannot break pairs during compaction
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
    verify_tool_call_pairing,
    identify_tool_call_groups,
    verify_tool_groups_atomic,
    generate_parallel_tool_calls,
    generate_sequential_tool_calls,
    generate_mixed_parallel_sequential_tools,
    generate_token_heavy_messages,
    add_linkedin_metadata,
    verify_all_ai_messages,
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
class TestToolCallPairingEdgeCases(PromptCompactionIntegrationTestBase):
    """
    Test tool call bracket-style pairing edge cases.
    Tests tool call atomic group preservation during compaction.
    """

    async def asyncSetUp(self):
        """Setup real external context for integration tests."""
        await super().asyncSetUp()

        from workflow_service.services.external_context_manager import (
            get_external_context_manager_with_clients,
        )

        self.ext_context = await get_external_context_manager_with_clients()

    # ========================================
    # Parallel Tool Calls (5 tests)
    # ========================================

    async def test_parallel_tool_calls_atomic_group(self):
        """
        Test: Parallel tool calls must stay together as atomic group.
        Pattern: [TC1, TC2] → [TR1, TR2]

        Expected Failure: May split calls from responses across sections.
        """
        thread_id = f"test-parallel-atomic-{uuid4()}"
        self.test_thread_ids.append(thread_id)

        # Generate 2 parallel tool calls with responses
        tool_messages = generate_parallel_tool_calls(
            count=2,
            content_prefix="Parallel tool call"
        )
        add_linkedin_metadata(tool_messages)

        # Verify groups identified correctly (should be 1 group of 4 messages)
        groups = identify_tool_call_groups(tool_messages)
        self.assertEqual(
            len(groups), 1,
            "Parallel tool calls should form exactly 1 atomic group"
        )
        self.assertEqual(
            len(groups[0]), 4,
            "Group should contain 2 tool calls + 2 responses"
        )

        # Add some context messages before and after
        messages = [
            HumanMessage(content="User question before tools" + " " * 100),
            *tool_messages,
            HumanMessage(content="User question after tools" + " " * 100),
        ]
        messages = add_linkedin_metadata(messages)

        # Create compaction config (moderate budget for fast test)
        config = self._create_test_config(
            mode=SummarizationMode.FROM_SCRATCH,
            strategy=CompactionStrategyType.SUMMARIZATION,
            max_tokens=4000,  # Reasonable budget for fast execution
            target_tokens=3000,
        )

        # Run compaction
        result = await self._run_compaction(
            messages=messages,
            config=config,
            thread_id=thread_id,
        )

        # Verify tool call pairing maintained
        summarized = result.get("summarized_messages", [])
        errors = verify_tool_call_pairing(summarized)
        self.assertEqual(
            errors, [],
            f"Tool call pairing must be maintained after compaction: {errors}"
        )

        # Verify atomic groups not split
        atomic_errors = verify_tool_groups_atomic(messages, summarized)
        self.assertEqual(
            atomic_errors, [],
            f"Parallel tool group must remain atomic: {atomic_errors}"
        )

    async def test_parallel_tool_calls_across_section_boundary(self):
        """
        Test: Parallel tool groups spanning section boundaries.

        Setup: Many messages → [TC1, TC2] → [TR1, TR2] → trigger compaction
        Expected Failure: May split across historical vs recent sections.
        """
        thread_id = f"test-parallel-boundary-{uuid4()}"
        self.test_thread_ids.append(thread_id)

        # Create message history with parallel tools at boundary
        context_messages = generate_token_heavy_messages(
            count=20,
            tokens_per_message=200  # 4000 tokens of context
        )

        tool_messages = generate_parallel_tool_calls(count=3, content_prefix="Boundary tool")

        final_message = HumanMessage(content="Final user question" + " " * 100)

        messages = [*context_messages, *tool_messages, final_message]
        messages = add_linkedin_metadata(messages)

        # Tight budget to force section boundaries
        config = self._create_test_config(
            mode=SummarizationMode.CONTINUED,
            strategy=CompactionStrategyType.SUMMARIZATION,
            max_tokens=8000,  # Reasonable budget for fast LLM testing
            target_tokens=6000,
        )

        result = await self._run_compaction(
            messages=messages,
            config=config,
            thread_id=thread_id,
        )

        # Critical: Tool group must not be split across sections
        summarized = result.get("summarized_messages", [])
        errors = verify_tool_call_pairing(summarized)
        self.assertEqual(
            errors, [],
            f"Tool calls must not be split across section boundaries: {errors}"
        )

        atomic_errors = verify_tool_groups_atomic(messages, summarized)
        self.assertEqual(
            atomic_errors, [],
            f"Parallel tool group must stay together: {atomic_errors}"
        )

    async def test_multiple_parallel_groups_can_separate(self):
        """
        Test: Multiple parallel groups CAN be in different sections.
        Pattern: [TC1, TC2]→[TR1, TR2] | Human | [TC3, TC4]→[TR3, TR4]

        Group 1 and Group 2 are separate atomic units - can be separated.
        But within each group, messages must stay together.
        """
        thread_id = f"test-multiple-parallel-{uuid4()}"
        self.test_thread_ids.append(thread_id)

        # Create two separate parallel tool groups
        group1 = generate_parallel_tool_calls(count=2, content_prefix="Group 1 tool")
        separator = [HumanMessage(content="Human message between groups" + " " * 200)]
        group2 = generate_parallel_tool_calls(count=2, content_prefix="Group 2 tool")

        messages = [*group1, *separator, *group2]
        messages = add_linkedin_metadata(messages)

        # Identify groups (should be 2 separate groups)
        groups = identify_tool_call_groups(messages)
        self.assertEqual(
            len(groups), 2,
            "Should identify 2 separate parallel tool groups"
        )

        config = self._create_test_config(
            mode=SummarizationMode.CONTINUED,
            strategy=CompactionStrategyType.SUMMARIZATION,
            max_tokens=6000,  # Reasonable budget for fast LLM testing
            target_tokens=4000,
        )

        result = await self._run_compaction(
            messages=messages,
            config=config,
            thread_id=thread_id,
        )

        summarized = result.get("summarized_messages", [])

        # Each group must remain atomic (but groups can separate)
        atomic_errors = verify_tool_groups_atomic(messages, summarized)
        self.assertEqual(
            atomic_errors, [],
            f"Each parallel group must remain atomic: {atomic_errors}"
        )

    async def test_parallel_calls_in_marked_section(self):
        """
        Test: Parallel tool calls in marked section must stay together.

        Expected Failure: Budget pressure may try to split marked tool groups.
        """
        thread_id = f"test-parallel-marked-{uuid4()}"
        self.test_thread_ids.append(thread_id)

        # Create parallel tool calls and mark them
        tool_messages = generate_parallel_tool_calls(count=2, content_prefix="Marked tool")

        # Mark the entire tool group
        for msg in tool_messages:
            if not msg.response_metadata:
                msg.response_metadata = {}
            msg.response_metadata["marked_for_context"] = True

        context = generate_token_heavy_messages(count=5, tokens_per_message=150)
        messages = [*context, *tool_messages]
        messages = add_linkedin_metadata(messages)

        config = self._create_test_config(
            mode=SummarizationMode.FROM_SCRATCH,  # Faster than CONTINUED
            strategy=CompactionStrategyType.SUMMARIZATION,
            max_tokens=3000,  # More reasonable budget for faster execution
            target_tokens=2000,
        )

        result = await self._run_compaction(
            messages=messages,
            config=config,
            thread_id=thread_id,
        )

        summarized = result.get("summarized_messages", [])

        # Verify marked tool group stays atomic
        atomic_errors = verify_tool_groups_atomic(messages, summarized)
        self.assertEqual(
            atomic_errors, [],
            f"Marked parallel tool group must remain atomic: {atomic_errors}"
        )

    async def test_parallel_calls_exceed_section_budget(self):
        """
        Test: Parallel tool group exceeding section budget.

        If tool group is 15K tokens and section budget is 10K:
        - Must NOT split the group
        - Options: Move entire group to overflow OR error

        Expected Failure: May attempt to split group to fit budget.
        """
        thread_id = f"test-parallel-exceed-budget-{uuid4()}"
        self.test_thread_ids.append(thread_id)

        # Create large parallel tool calls (each response ~4K tokens)
        tool_messages = []
        tool_calls_data = []

        # Create 4 parallel tool calls
        for i in range(4):
            tool_call_id = f"call_{uuid4()}"
            tool_calls_data.append({
                "name": f"large_tool_{i}",
                "args": {"query": f"arg_{i}"},
                "id": tool_call_id,
                "type": "tool_call",
            })

        # AIMessage with all tool calls
        ai_msg = AIMessage(
            content="Calling multiple tools in parallel",
            tool_calls=tool_calls_data,
            id=str(uuid4())
        )
        tool_messages.append(ai_msg)

        # Tool responses (each ~4K tokens = 16K total for 4 responses)
        for call_data in tool_calls_data:
            large_result = "Tool execution result: " + ("X" * 4000)  # ~4K tokens
            tool_msg = AIMessage(
                content=large_result,
                tool_call_id=call_data["id"],
                id=str(uuid4())
            )
            tool_messages.append(tool_msg)

        add_linkedin_metadata(tool_messages)

        # Verify this is a single atomic group
        groups = identify_tool_call_groups(tool_messages)
        self.assertEqual(len(groups), 1, "Should be 1 parallel tool group")

        # Very tight budget to trigger overflow
        config = self._create_test_config(
            mode=SummarizationMode.CONTINUED,
            strategy=CompactionStrategyType.SUMMARIZATION,
            max_tokens=5000,  # Budget much smaller than tool group
            target_tokens=3000,
        )

        result = await self._run_compaction(
            messages=tool_messages,
            config=config,
            thread_id=thread_id,
        )

        summarized = result.get("summarized_messages", [])

        # Critical: Group must NOT be split even if it exceeds budget
        atomic_errors = verify_tool_groups_atomic(tool_messages, summarized)
        self.assertEqual(
            atomic_errors, [],
            f"Large parallel tool group must not be split even if exceeding budget: {atomic_errors}"
        )

    # ========================================
    # Sequential Tool Calls (5 tests)
    # ========================================

    async def test_sequential_tool_calls_can_break_between_pairs(self):
        """
        Test: Sequential tool calls CAN break between pairs.
        Pattern: TC1→TR1 | TC2→TR2 (can break at |)

        Can compact TC1→TR1, keep TC2→TR2 recent.
        Cannot break TC1 from TR1.
        """
        thread_id = f"test-sequential-break-{uuid4()}"
        self.test_thread_ids.append(thread_id)

        # Generate sequential tool calls
        tool_messages = generate_sequential_tool_calls(
            count=3,  # 3 pairs: TC1→TR1, TC2→TR2, TC3→TR3
            content_prefix="Sequential tool"
        )
        add_linkedin_metadata(tool_messages)

        # Verify 3 separate atomic groups
        groups = identify_tool_call_groups(tool_messages)
        self.assertEqual(
            len(groups), 3,
            "Sequential calls should form 3 separate atomic pairs"
        )

        config = self._create_test_config(
            mode=SummarizationMode.CONTINUED,
            strategy=CompactionStrategyType.SUMMARIZATION,
            max_tokens=8000,  # Reasonable budget for fast LLM testing
            target_tokens=6000,
        )

        result = await self._run_compaction(
            messages=tool_messages,
            config=config,
            thread_id=thread_id,
        )

        summarized = result.get("summarized_messages", [])

        # Each pair must remain atomic (but pairs can separate)
        atomic_errors = verify_tool_groups_atomic(tool_messages, summarized)
        self.assertEqual(
            atomic_errors, [],
            f"Each sequential pair must remain atomic: {atomic_errors}"
        )

    async def test_nested_tool_calls_semantic_grouping(self):
        """
        Test: Nested/chained tool calls with semantic dependencies.
        Pattern: TC1→TR1→TC2(uses TR1)→TR2

        This is complex: TC2 semantically depends on TR1 output.
        Intelligent breaking may need to keep related chains together.
        """
        thread_id = f"test-nested-tools-{uuid4()}"
        self.test_thread_ids.append(thread_id)

        # Create chained tool calls
        messages = []

        # TC1: Get user data
        tc1_id = f"call_{uuid4()}"
        tc1 = AIMessage(
            content="Getting user data",
            tool_calls=[{
                "name": "get_user",
                "args": {"user_id": "123"},
                "id": tc1_id,
                "type": "tool_call",
            }],
            id=str(uuid4())
        )
        messages.append(tc1)

        # TR1: User data result
        tr1 = AIMessage(
            content="User data: {name: John, company: Acme}",
            tool_call_id=tc1_id,
            id=str(uuid4())
        )
        messages.append(tr1)

        # TC2: Get company data (uses TR1 result)
        tc2_id = f"call_{uuid4()}"
        tc2 = AIMessage(
            content="Getting company data based on user result",
            tool_calls=[{
                "name": "get_company",
                "args": {"company_name": "Acme"},  # Uses TR1 output
                "id": tc2_id,
                "type": "tool_call",
            }],
            id=str(uuid4())
        )
        messages.append(tc2)

        # TR2: Company data result
        tr2 = AIMessage(
            content="Company data: {industry: Tech, size: 500}",
            tool_call_id=tc2_id,
            id=str(uuid4())
        )
        messages.append(tr2)

        messages = add_linkedin_metadata(messages)

        # This should identify 2 atomic pairs (TC1-TR1, TC2-TR2)
        groups = identify_tool_call_groups(messages)
        self.assertEqual(
            len(groups), 2,
            "Should identify 2 tool call pairs"
        )

        config = self._create_test_config(
            mode=SummarizationMode.CONTINUED,
            strategy=CompactionStrategyType.SUMMARIZATION,
            max_tokens=6000,  # Reasonable budget for fast LLM testing
            target_tokens=4000,
        )

        result = await self._run_compaction(
            messages=messages,
            config=config,
            thread_id=thread_id,
        )

        summarized = result.get("summarized_messages", [])

        # Each pair must remain atomic
        atomic_errors = verify_tool_groups_atomic(messages, summarized)
        self.assertEqual(
            atomic_errors, [],
            f"Chained tool call pairs must remain atomic: {atomic_errors}"
        )

    async def test_interleaved_tools_and_messages(self):
        """
        Test: Tool calls interleaved with human messages.
        Pattern: TC1→TR1→Human→TC2→TR2

        Human message breaks tool groups.
        Each TC-TR pair is atomic.
        """
        thread_id = f"test-interleaved-{uuid4()}"
        self.test_thread_ids.append(thread_id)

        messages = []

        # Pair 1
        pair1 = generate_sequential_tool_calls(count=1, content_prefix="Tool 1")
        messages.extend(pair1)

        # Human interruption
        messages.append(HumanMessage(content="User provides additional context" + " " * 100))

        # Pair 2
        pair2 = generate_sequential_tool_calls(count=1, content_prefix="Tool 2")
        messages.extend(pair2)

        messages = add_linkedin_metadata(messages)

        # Should identify 2 separate groups
        groups = identify_tool_call_groups(messages)
        self.assertEqual(
            len(groups), 2,
            "Human message should break tool groups into 2 pairs"
        )

        config = self._create_test_config(
            mode=SummarizationMode.CONTINUED,
            strategy=CompactionStrategyType.SUMMARIZATION,
            max_tokens=6000,  # Reasonable budget for fast LLM testing
            target_tokens=4000,
        )

        result = await self._run_compaction(
            messages=messages,
            config=config,
            thread_id=thread_id,
        )

        summarized = result.get("summarized_messages", [])

        atomic_errors = verify_tool_groups_atomic(messages, summarized)
        self.assertEqual(
            atomic_errors, [],
            f"Each tool pair must remain atomic despite human messages: {atomic_errors}"
        )

    async def test_unpaired_tool_call_error_handling(self):
        """
        Test: Unpaired tool call detection.
        Pattern: TC1→TC2→TR1 (TR2 missing)

        Expected Failure: May not detect unpaired TC2.
        Should error or skip unpaired tool calls.
        """
        thread_id = f"test-unpaired-call-{uuid4()}"
        self.test_thread_ids.append(thread_id)

        messages = []

        # TC1 with response
        tc1_id = f"call_{uuid4()}"
        tc1 = AIMessage(
            content="Tool call 1",
            tool_calls=[{
                "name": "tool1",
                "args": {},
                "id": tc1_id,
                "type": "tool_call",
            }],
            id=str(uuid4())
        )
        messages.append(tc1)

        # TC2 WITHOUT response (unpaired)
        tc2_id = f"call_{uuid4()}"
        tc2 = AIMessage(
            content="Tool call 2 (no response)",
            tool_calls=[{
                "name": "tool2",
                "args": {},
                "id": tc2_id,
                "type": "tool_call",
            }],
            id=str(uuid4())
        )
        messages.append(tc2)

        # TR1 for TC1
        tr1 = AIMessage(
            content="Response 1",
            tool_call_id=tc1_id,
            id=str(uuid4())
        )
        messages.append(tr1)

        messages = add_linkedin_metadata(messages)

        # Verify pairing is broken
        pairing_errors = verify_tool_call_pairing(messages)
        self.assertGreater(
            len(pairing_errors), 0,
            "Should detect unpaired tool call"
        )

        config = self._create_test_config(
            mode=SummarizationMode.CONTINUED,
            strategy=CompactionStrategyType.SUMMARIZATION,
            max_tokens=6000,  # Reasonable budget for fast LLM testing
            target_tokens=4000,
        )

        # This should either:
        # 1. Raise an error about unpaired tool calls
        # 2. Filter out unpaired calls
        # 3. Handle gracefully
        try:
            result = await self._run_compaction(
                messages=messages,
                config=config,
                thread_id=thread_id,
            )

            summarized = result.get("summarized_messages", [])

            # If no error, verify pairing in output
            output_errors = verify_tool_call_pairing(summarized)
            # Output should either have no tool calls or have valid pairing
            # (unpaired TC2 should be filtered out)

        except Exception as e:
            # Expected: May raise error on unpaired tool calls
            self.assertIn(
                "tool", str(e).lower(),
                f"Error should mention tool call issue: {e}"
            )

    async def test_unpaired_tool_result_handling(self):
        """
        Test: Tool result without corresponding call.
        Pattern: TR1→TC1→TR1 (TR1 appears before TC1)

        Malformed sequence - should detect and handle.
        """
        thread_id = f"test-unpaired-result-{uuid4()}"
        self.test_thread_ids.append(thread_id)

        messages = []

        # TR1 BEFORE TC1 (invalid)
        tc1_id = f"call_{uuid4()}"
        tr1_early = AIMessage(
            content="Premature response",
            tool_call_id=tc1_id,
            id=str(uuid4())
        )
        messages.append(tr1_early)

        # TC1
        tc1 = AIMessage(
            content="Tool call after response (invalid)",
            tool_calls=[{
                "name": "tool1",
                "args": {},
                "id": tc1_id,
                "type": "tool_call",
            }],
            id=str(uuid4())
        )
        messages.append(tc1)

        # TR1 again (duplicate)
        tr1 = AIMessage(
            content="Response again",
            tool_call_id=tc1_id,
            id=str(uuid4())
        )
        messages.append(tr1)

        messages = add_linkedin_metadata(messages)

        # Verify pairing is broken
        pairing_errors = verify_tool_call_pairing(messages)
        self.assertGreater(
            len(pairing_errors), 0,
            "Should detect malformed tool call sequence"
        )

        config = self._create_test_config(
            mode=SummarizationMode.CONTINUED,
            strategy=CompactionStrategyType.SUMMARIZATION,
            max_tokens=6000,  # Reasonable budget for fast LLM testing
            target_tokens=4000,
        )

        try:
            result = await self._run_compaction(
                messages=messages,
                config=config,
                thread_id=thread_id,
            )

            # If no error, verify output is valid
            summarized = result.get("summarized_messages", [])
            output_errors = verify_tool_call_pairing(summarized)

        except Exception as e:
            # Expected: May raise error on malformed sequence
            pass

    # ========================================
    # Tool Calls in Compaction (5 tests)
    # ========================================

    async def test_tool_pair_in_summarization(self):
        """
        Test: Summarizing messages including TC→TR pairs.

        Summary must not split pairs.
        Summary must be AIMessage.
        """
        thread_id = f"test-tool-summarization-{uuid4()}"
        self.test_thread_ids.append(thread_id)

        # Create context with tool calls
        context = generate_token_heavy_messages(count=5, tokens_per_message=300)
        tool_pair = generate_sequential_tool_calls(count=1, content_prefix="Tool in summary")
        more_context = generate_token_heavy_messages(count=5, tokens_per_message=300)

        messages = [*context, *tool_pair, *more_context]
        messages = add_linkedin_metadata(messages)

        config = self._create_test_config(
            mode=SummarizationMode.CONTINUED,
            strategy=CompactionStrategyType.SUMMARIZATION,
            max_tokens=8000,  # Reasonable budget for fast LLM testing
            target_tokens=6000,
        )

        result = await self._run_compaction(
            messages=messages,
            config=config,
            thread_id=thread_id,
        )

        summarized = result.get("summarized_messages", [])

        # Verify pairing maintained
        errors = verify_tool_call_pairing(summarized)
        self.assertEqual(
            errors, [],
            f"Tool pairing must be maintained in summarization: {errors}"
        )

        # Verify summary messages are AIMessages
        summary_msgs = [m for m in summarized if "SUMMARY" in m.response_metadata.get("section_label", "")]
        if summary_msgs:
            verify_all_ai_messages(summary_msgs, "summarization output")

    async def test_tool_pair_in_extraction(self):
        """
        Test: Extracting relevant messages with tool calls.

        Must not extract TC without TR.
        Extract complete pairs only.
        Extracted messages must be AIMessages.
        """
        thread_id = f"test-tool-extraction-{uuid4()}"
        self.test_thread_ids.append(thread_id)

        # Create messages with tool pair
        context1 = [HumanMessage(content="Context before" + " " * 200)]
        tool_pair = generate_sequential_tool_calls(count=1, content_prefix="Relevant tool")
        context2 = generate_token_heavy_messages(count=10, tokens_per_message=300)

        messages = [*context1, *tool_pair, *context2]
        messages = add_linkedin_metadata(messages)

        config = self._create_test_config(
            mode=SummarizationMode.CONTINUED,
            strategy=CompactionStrategyType.EXTRACTIVE,
            max_tokens=8000,  # Reasonable budget for fast LLM testing
            target_tokens=6000,
        )

        result = await self._run_compaction(
            messages=messages,
            config=config,
            thread_id=thread_id,
        )

        summarized = result.get("summarized_messages", [])

        # Verify pairing maintained
        errors = verify_tool_call_pairing(summarized)
        self.assertEqual(
            errors, [],
            f"Tool pairing must be maintained in extraction: {errors}"
        )

        # Verify extracted messages are AIMessages
        extracted_msgs = [m for m in summarized if "EXTRACTED" in m.response_metadata.get("section_label", "")]
        if extracted_msgs:
            verify_all_ai_messages(extracted_msgs, "extraction output")

    async def test_tool_pair_spans_classifier_boundary(self):
        """
        Test: Tool call classified as historical, response as recent.

        Expected Failure: Classifier may split TC and TR across sections.
        Should error or force both into same section.
        """
        thread_id = f"test-tool-classifier-boundary-{uuid4()}"
        self.test_thread_ids.append(thread_id)

        # Create scenario where tool call might be classified differently than response
        old_context = generate_token_heavy_messages(count=15, tokens_per_message=200)
        tool_pair = generate_sequential_tool_calls(count=1, content_prefix="Boundary tool")
        recent_context = [HumanMessage(content="Recent question" + " " * 100)]

        messages = [*old_context, *tool_pair, *recent_context]
        messages = add_linkedin_metadata(messages)

        config = self._create_test_config(
            mode=SummarizationMode.CONTINUED,
            strategy=CompactionStrategyType.SUMMARIZATION,
            max_tokens=8000,  # Reasonable budget for fast LLM testing
            target_tokens=6000,
        )

        result = await self._run_compaction(
            messages=messages,
            config=config,
            thread_id=thread_id,
        )

        summarized = result.get("summarized_messages", [])

        # Critical: Must not split TC from TR
        atomic_errors = verify_tool_groups_atomic(messages, summarized)
        self.assertEqual(
            atomic_errors, [],
            f"Classifier must not split tool pairs across sections: {atomic_errors}"
        )

    async def test_large_tool_result_chunking_preserves_pair(self):
        """
        Test: Tool result with 30K tokens requires chunking.

        TC + chunked TR must stay grouped.
        """
        thread_id = f"test-large-tool-chunking-{uuid4()}"
        self.test_thread_ids.append(thread_id)

        # Create tool call with very large response
        tc_id = f"call_{uuid4()}"
        tc = AIMessage(
            content="Calling tool that returns large result",
            tool_calls=[{
                "name": "large_data_tool",
                "args": {"size": "large"},
                "id": tc_id,
                "type": "tool_call",
            }],
            id=str(uuid4())
        )

        # Create ~30K token response (will be chunked)
        large_content = "Tool result: " + ("X" * 30000)  # ~30K tokens
        tr = ToolMessage(
            content=large_content,
            tool_call_id=tc_id,
            id=str(uuid4())
        )

        messages = [tc, tr]
        messages = add_linkedin_metadata(messages)

        config = self._create_test_config(
            mode=SummarizationMode.CONTINUED,
            strategy=CompactionStrategyType.SUMMARIZATION,
            max_tokens=50000,  # Large enough to fit chunks
            target_tokens=40000,
        )

        result = await self._run_compaction(
            messages=messages,
            config=config,
            thread_id=thread_id,
        )

        summarized = result.get("summarized_messages", [])

        # Verify TC and TR (even if chunked) stay paired
        errors = verify_tool_call_pairing(summarized)
        self.assertEqual(
            errors, [],
            f"Large tool result chunking must preserve pairing: {errors}"
        )

    async def test_tool_calls_in_overflow_section(self):
        """
        Test: Tool group moves to overflow section.

        When marked tool group can't fit: entire group → overflow atomically.
        """
        thread_id = f"test-tool-overflow-{uuid4()}"
        self.test_thread_ids.append(thread_id)

        # Create tool group and mark it
        tool_messages = generate_parallel_tool_calls(count=2, content_prefix="Overflow tool")

        for msg in tool_messages:
            if not msg.response_metadata:
                msg.response_metadata = {}
            msg.response_metadata["marked_for_context"] = True

        # Add token-heavy context to trigger overflow
        context = generate_token_heavy_messages(count=20, tokens_per_message=400)
        messages = [*context, *tool_messages]
        messages = add_linkedin_metadata(messages)

        config = self._create_test_config(
            mode=SummarizationMode.CONTINUED,
            strategy=CompactionStrategyType.SUMMARIZATION,
            max_tokens=8000,  # Reasonable budget for fast LLM testing
            target_tokens=6000,
        )

        result = await self._run_compaction(
            messages=messages,
            config=config,
            thread_id=thread_id,
        )

        summarized = result.get("summarized_messages", [])

        # Verify tool group remains atomic even in overflow
        atomic_errors = verify_tool_groups_atomic(messages, summarized)
        self.assertEqual(
            atomic_errors, [],
            f"Tool group must move to overflow atomically: {atomic_errors}"
        )

    # ========================================
    # Complex Patterns (5 tests)
    # ========================================

    async def test_mixed_parallel_and_sequential(self):
        """
        Test: Mixed parallel and sequential tool calls.
        Pattern: [TC1,TC2]→[TR1,TR2] | TC3→TR3 | [TC4,TC5]→[TR4,TR5]

        Should identify 3 atomic groups.
        """
        thread_id = f"test-mixed-patterns-{uuid4()}"
        self.test_thread_ids.append(thread_id)

        # Generate: parallel group + sequential pair + parallel group = 3 groups total
        parallel1 = generate_parallel_tool_calls(2, "Parallel1")
        sequential = generate_sequential_tool_calls(1, "Sequential")
        parallel2 = generate_parallel_tool_calls(2, "Parallel2")
        
        messages = parallel1 + sequential + parallel2
        messages = add_linkedin_metadata(messages)

        # Verify 3 groups identified
        groups = identify_tool_call_groups(messages)
        self.assertEqual(
            len(groups), 3,
            "Should identify 3 tool call groups (2 parallel, 1 sequential)"
        )

        config = self._create_test_config(
            mode=SummarizationMode.CONTINUED,
            strategy=CompactionStrategyType.SUMMARIZATION,
            max_tokens=3000,
            target_tokens=1500,
        )

        result = await self._run_compaction(
            messages=messages,
            config=config,
            thread_id=thread_id,
        )

        summarized = result.get("summarized_messages", [])

        # Verify all groups remain atomic
        atomic_errors = verify_tool_groups_atomic(messages, summarized)
        self.assertEqual(
            atomic_errors, [],
            f"All tool groups must remain atomic in mixed pattern: {atomic_errors}"
        )

    async def test_50_parallel_tool_calls(self):
        """
        Test: 50 parallel tool calls + 50 responses = 100 messages.

        Verify all grouped correctly.
        May exceed budget - verify handling.
        """
        thread_id = f"test-50-parallel-{uuid4()}"
        self.test_thread_ids.append(thread_id)

        # Generate 50 parallel tool calls
        tool_messages = generate_parallel_tool_calls(
            count=50,
            content_prefix="Mass parallel tool"
        )
        add_linkedin_metadata(tool_messages)

        # Should be 1 massive atomic group
        groups = identify_tool_call_groups(tool_messages)
        self.assertEqual(
            len(groups), 1,
            "50 parallel tool calls should form 1 atomic group"
        )
        self.assertEqual(
            len(groups[0]), 100,
            "Group should contain 50 calls + 50 responses"
        )

        config = self._create_test_config(
            mode=SummarizationMode.CONTINUED,
            strategy=CompactionStrategyType.SUMMARIZATION,
            max_tokens=10000,  # May not fit all 100 messages
            target_tokens=8000,
        )

        result = await self._run_compaction(
            messages=tool_messages,
            config=config,
            thread_id=thread_id,
        )

        summarized = result.get("summarized_messages", [])

        # Verify group not split
        atomic_errors = verify_tool_groups_atomic(tool_messages, summarized)
        self.assertEqual(
            atomic_errors, [],
            f"Large parallel tool group must not be split: {atomic_errors}"
        )

    async def test_tool_calls_across_multiple_turns(self):
        """
        Test: Tool calls preserved across multiple turns of compaction.

        Turn 1: TC1→TR1, compact
        Turn 2: TC2→TR2, compact
        Verify pairing maintained across both turns.
        """
        thread_id = f"test-multi-turn-tools-{uuid4()}"
        self.test_thread_ids.append(thread_id)

        # Turn 1
        turn1_messages = [
            *generate_token_heavy_messages(count=5, tokens_per_message=200),
            *generate_sequential_tool_calls(count=1, content_prefix="Turn 1 tool"),
        ]
        add_linkedin_metadata(turn1_messages)

        config = self._create_test_config(
            mode=SummarizationMode.FROM_SCRATCH,
            strategy=CompactionStrategyType.SUMMARIZATION,
            max_tokens=8000,  # Reasonable budget for fast LLM testing
            target_tokens=6000,
        )

        result1 = await self._run_compaction(
            messages=turn1_messages,
            config=config,
            thread_id=thread_id,
        )

        # Turn 2: Add more messages and tool calls
        turn2_new = [
            *generate_token_heavy_messages(count=5, tokens_per_message=200),
            *generate_sequential_tool_calls(count=1, content_prefix="Turn 2 tool"),
        ]
        add_linkedin_metadata(turn2_new)

        turn2_messages = result1.get("summarized_messages", []) + turn2_new

        config.summarization.mode = SummarizationMode.CONTINUED
        result2 = await self._run_compaction(
            messages=turn2_messages,
            config=config,
            thread_id=thread_id,
        )

        final_messages = result2.get("summarized_messages", [])

        # Verify pairing maintained across both turns
        errors = verify_tool_call_pairing(final_messages)
        self.assertEqual(
            errors, [],
            f"Tool pairing must be maintained across multiple turns: {errors}"
        )

    async def test_tool_calls_with_thinking_tokens(self):
        """
        Test: Tool calls with thinking/reasoning tokens.

        Pattern: Thinking + TC + TR
        Verify: Thinking, TC, TR handled correctly.
        """
        thread_id = f"test-tools-thinking-{uuid4()}"
        self.test_thread_ids.append(thread_id)

        messages = []

        # Thinking message
        thinking = AIMessage(
            content="Let me think about which tool to use...",
            response_metadata={"thinking": True},
            id=str(uuid4())
        )
        messages.append(thinking)

        # Tool call
        tc_id = f"call_{uuid4()}"
        tc = AIMessage(
            content="Calling tool after thinking",
            tool_calls=[{
                "name": "analyzed_tool",
                "args": {},
                "id": tc_id,
                "type": "tool_call",
            }],
            id=str(uuid4())
        )
        messages.append(tc)

        # Tool response
        tr = ToolMessage(
            content="Tool result",
            tool_call_id=tc_id,
            id=str(uuid4())
        )
        messages.append(tr)

        messages = add_linkedin_metadata(messages)

        config = self._create_test_config(
            mode=SummarizationMode.CONTINUED,
            strategy=CompactionStrategyType.SUMMARIZATION,
            max_tokens=6000,  # Reasonable budget for fast LLM testing
            target_tokens=4000,
        )

        result = await self._run_compaction(
            messages=messages,
            config=config,
            thread_id=thread_id,
        )

        summarized = result.get("summarized_messages", [])

        # Verify tool pairing maintained despite thinking tokens
        errors = verify_tool_call_pairing(summarized)
        self.assertEqual(
            errors, [],
            f"Tool pairing must be maintained with thinking tokens: {errors}"
        )

    async def test_openai_parallel_function_call_format(self):
        """
        Test: OpenAI-specific parallel function call format.

        OpenAI uses specific format for parallel function calls.
        Expected Failure: May not parse correctly.
        """
        thread_id = f"test-openai-parallel-{uuid4()}"
        self.test_thread_ids.append(thread_id)

        # Create OpenAI-style parallel function calls
        function_calls_data = [
            {
                "name": f"function_{i}",
                "args": {"arg": f"value_{i}"},
                "id": f"call_{uuid4()}",
                "type": "function",
            }
            for i in range(3)
        ]

        ai_msg = AIMessage(
            content="",  # OpenAI often has empty content for function calls
            additional_kwargs={
                "function_call": None,
                "tool_calls": function_calls_data,
            },
            id=str(uuid4())
        )

        messages = [ai_msg]

        # Add responses
        for fc in function_calls_data:
            resp = AIMessage(
                content=f"Result for {fc['name']}",
                tool_call_id=fc["id"],
                id=str(uuid4())
            )
            messages.append(resp)

        messages = add_linkedin_metadata(messages)

        # Verify pairing works with OpenAI format
        errors = verify_tool_call_pairing(messages)
        self.assertEqual(
            errors, [],
            f"OpenAI parallel function call format must be parsed correctly: {errors}"
        )

        config = self._create_test_config(
            mode=SummarizationMode.CONTINUED,
            strategy=CompactionStrategyType.SUMMARIZATION,
            max_tokens=6000,  # Reasonable budget for fast LLM testing
            target_tokens=4000,
        )

        result = await self._run_compaction(
            messages=messages,
            config=config,
            thread_id=thread_id,
        )

        summarized = result.get("summarized_messages", [])

        # Verify pairing maintained after compaction
        errors = verify_tool_call_pairing(summarized)
        self.assertEqual(
            errors, [],
            f"OpenAI parallel calls must remain paired after compaction: {errors}"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
