"""
Integration tests for message ID-based history deduplication in prompt compaction.

These tests are designed to EXPOSE IMPLEMENTATION GAPS in message history merging.
Expected failures until ID-based deduplication is properly implemented.

Critical Requirements:
1. When merging current_messages into message history:
   - Check each message by message.id
   - If message.id exists: Replace at same position (NOT append)
   - If message.id is new: Append to end
   - Never create duplicates
   - Preserve chronological ordering
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
    merge_current_messages_into_history,
    verify_message_id_deduplication,
    generate_token_heavy_messages,
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
class TestMessageIDDeduplication(PromptCompactionIntegrationTestBase):
    """
    Test message ID-based history deduplication.
    EXPECTED TO EXPOSE IMPLEMENTATION GAPS.
    """

    # ========================================
    # Basic Deduplication (5 tests)
    # ========================================

    async def test_message_updated_replaces_at_same_position(self):
        """
        Test: Updated message replaces at same position, not appended.

        Setup:
        - Turn 1: msg_123 at position 5 in history
        - Turn 2: msg_123 gets metadata update → in current_messages
        - Merge: msg_123 should replace at position 5, NOT append

        Expected Failure: May append creating duplicate.
        """
        thread_id = f"test-replace-position-{uuid4()}"
        self.test_thread_ids.append(thread_id)

        # Create initial history
        initial_messages = [
            HumanMessage(content=f"Message {i}" + " " * 100, id=f"msg_{i}")
            for i in range(10)
        ]
        add_linkedin_metadata(initial_messages)

        # Run initial compaction (from scratch)
        config = self._create_test_config(
            mode=SummarizationMode.FROM_SCRATCH,
            strategy=CompactionStrategyType.SUMMARIZATION,
            max_tokens=5000,
            target_tokens=3000,
        )

        result1 = await self._run_compaction(
            messages=initial_messages,
            config=config,
            thread_id=thread_id,
        )

        history = result1.get("summarized_messages", [])
        current_msgs_1 = result1.get("current_messages", [])

        # Merge current_messages into history using correct logic
        history = merge_current_messages_into_history(history, current_msgs_1)

        # Track original position of msg_5
        msg_5_original_pos = None
        for i, msg in enumerate(history):
            if msg.id == "msg_5":
                msg_5_original_pos = i
                break

        self.assertIsNotNone(msg_5_original_pos, "msg_5 should exist in history")

        # Turn 2: Update msg_5 metadata
        # Simulate metadata update (e.g., section_label change)
        updated_msg_5 = None
        for msg in history:
            if msg.id == "msg_5":
                # Create updated version
                updated_msg_5 = AIMessage(
                    content=msg.content,
                    id=msg.id,
                    response_metadata={
                        **msg.response_metadata,
                        "section_label": "MARKED",  # New metadata
                        "updated_turn": 2,
                    }
                )
                break

        self.assertIsNotNone(updated_msg_5, "Should have created updated msg_5")

        # Simulate current_messages from turn 2 (contains only updated msg)
        current_msgs_2 = [updated_msg_5]

        # Merge again
        history = merge_current_messages_into_history(history, current_msgs_2)

        # Verify: msg_5 still at same position (replaced, not appended)
        msg_5_new_pos = None
        for i, msg in enumerate(history):
            if msg.id == "msg_5":
                msg_5_new_pos = i
                break

        self.assertEqual(
            msg_5_new_pos, msg_5_original_pos,
            f"msg_5 should stay at position {msg_5_original_pos}, not move to {msg_5_new_pos}"
        )

        # Verify no duplicates
        verify_message_id_deduplication(history)

        # Verify metadata was updated
        msg_5_final = history[msg_5_new_pos]
        self.assertEqual(
            msg_5_final.response_metadata.get("section_label"), "MARKED",
            "Metadata should be updated"
        )

    async def test_new_message_appends_to_history(self):
        """
        Test: New message appends to history.

        Setup:
        - Turn 1: msg_123, msg_456
        - Turn 2: msg_789 (new) in current_messages
        - Merge: msg_789 appends after msg_456
        """
        thread_id = f"test-append-new-{uuid4()}"
        self.test_thread_ids.append(thread_id)

        # Initial messages
        initial_messages = [
            HumanMessage(content="Message 1" + " " * 100, id="msg_1"),
            HumanMessage(content="Message 2" + " " * 100, id="msg_2"),
        ]
        add_linkedin_metadata(initial_messages)

        # Initial history
        history = initial_messages.copy()
        initial_length = len(history)

        # Turn 2: New message
        new_message = HumanMessage(content="New message 3" + " " * 100, id="msg_3")
        add_linkedin_metadata([new_message])

        current_msgs_2 = [new_message]

        # Merge
        history = merge_current_messages_into_history(history, current_msgs_2)

        # Verify: Length increased by 1
        self.assertEqual(
            len(history), initial_length + 1,
            "History should have 1 more message"
        )

        # Verify: New message is last
        self.assertEqual(
            history[-1].id, "msg_3",
            "New message should be appended to end"
        )

        # Verify no duplicates
        verify_message_id_deduplication(history)

    async def test_multiple_messages_replaced_preserve_order(self):
        """
        Test: Multiple updates preserve original positions.

        Setup:
        - History: [msg_1, msg_2, msg_3, msg_4, msg_5]
        - current_messages: [msg_2_updated, msg_4_updated]
        - Result: [msg_1, msg_2_updated, msg_3, msg_4_updated, msg_5]

        Positions 2 and 4 replaced in-place.
        """
        thread_id = f"test-multiple-replace-{uuid4()}"
        self.test_thread_ids.append(thread_id)

        # Initial history
        history = [
            HumanMessage(content=f"Message {i}" + " " * 100, id=f"msg_{i}")
            for i in range(1, 6)
        ]
        add_linkedin_metadata(history)

        # Store original positions
        original_positions = {msg.id: i for i, msg in enumerate(history)}

        # Update msg_2 and msg_4
        updated_msg_2 = AIMessage(
            content="Updated message 2" + " " * 100,
            id="msg_2",
            response_metadata={"updated": True}
        )
        updated_msg_4 = AIMessage(
            content="Updated message 4" + " " * 100,
            id="msg_4",
            response_metadata={"updated": True}
        )

        current_msgs = [updated_msg_2, updated_msg_4]

        # Merge
        history = merge_current_messages_into_history(history, current_msgs)

        # Verify: Still 5 messages (no new, no duplicates)
        self.assertEqual(len(history), 5, "Should still have 5 messages")

        # Verify: msg_2 and msg_4 at same positions
        for i, msg in enumerate(history):
            if msg.id in ["msg_2", "msg_4"]:
                expected_pos = original_positions[msg.id]
                self.assertEqual(
                    i, expected_pos,
                    f"{msg.id} should still be at position {expected_pos}"
                )

        # Verify: msg_2 and msg_4 have updated flag
        self.assertTrue(
            history[original_positions["msg_2"]].response_metadata.get("updated"),
            "msg_2 should have updated flag"
        )
        self.assertTrue(
            history[original_positions["msg_4"]].response_metadata.get("updated"),
            "msg_4 should have updated flag"
        )

        # Verify no duplicates
        verify_message_id_deduplication(history)

    async def test_mixed_updates_and_new_messages(self):
        """
        Test: Mix of updates and new messages.

        Setup:
        - History: [msg_1, msg_2, msg_3]
        - current_messages: [msg_2_updated, msg_4_new]
        - Result: [msg_1, msg_2_updated, msg_3, msg_4_new]

        msg_2 replaced at position 2, msg_4 appended.
        """
        thread_id = f"test-mixed-updates-{uuid4()}"
        self.test_thread_ids.append(thread_id)

        # Initial history
        history = [
            HumanMessage(content=f"Message {i}" + " " * 100, id=f"msg_{i}")
            for i in range(1, 4)
        ]
        add_linkedin_metadata(history)

        # Updated msg_2 and new msg_4
        updated_msg_2 = AIMessage(
            content="Updated message 2" + " " * 100,
            id="msg_2",
            response_metadata={"updated": True}
        )
        new_msg_4 = HumanMessage(content="New message 4" + " " * 100, id="msg_4")

        current_msgs = [updated_msg_2, new_msg_4]
        add_linkedin_metadata(current_msgs)

        # Merge
        history = merge_current_messages_into_history(history, current_msgs)

        # Verify: 4 messages total
        self.assertEqual(len(history), 4, "Should have 4 messages")

        # Verify: msg_2 updated at position 1
        self.assertEqual(history[1].id, "msg_2", "msg_2 should be at position 1")
        self.assertTrue(
            history[1].response_metadata.get("updated"),
            "msg_2 should be updated"
        )

        # Verify: msg_4 appended at end
        self.assertEqual(history[3].id, "msg_4", "msg_4 should be last")

        # Verify no duplicates
        verify_message_id_deduplication(history)

    async def test_no_duplicates_after_merge(self):
        """
        Test: Comprehensive duplicate detection.

        Verify no message ID appears twice after merge.
        """
        thread_id = f"test-no-duplicates-{uuid4()}"
        self.test_thread_ids.append(thread_id)

        # Create 20 messages
        history = [
            HumanMessage(content=f"Message {i}" + " " * 100, id=f"msg_{i}")
            for i in range(20)
        ]
        add_linkedin_metadata(history)

        # Update 10 random messages
        updates = []
        for i in [2, 5, 7, 11, 13, 15, 16, 18, 19, 9]:
            updated = AIMessage(
                content=f"Updated message {i}" + " " * 100,
                id=f"msg_{i}",
                response_metadata={"updated": True, "turn": 2}
            )
            updates.append(updated)

        # Merge
        history = merge_current_messages_into_history(history, updates)

        # Verify: Still 20 messages
        self.assertEqual(len(history), 20, "Should still have 20 messages")

        # Verify: No duplicates
        verify_message_id_deduplication(history)

        # Verify: All updated messages have updated flag
        updated_count = sum(
            1 for msg in history
            if msg.response_metadata.get("updated") == True
        )
        self.assertEqual(updated_count, 10, "Should have 10 updated messages")

    # ========================================
    # Multi-Turn Deduplication (5 tests)
    # ========================================

    async def test_message_updated_multiple_times_3_turns(self):
        """
        Test: Same message updated across 3 turns.

        Turn 1: msg_123 at position 3
        Turn 2: msg_123 updated → replace at position 3
        Turn 3: msg_123 updated again → still at position 3

        Always same position, never duplicated.
        """
        thread_id = f"test-3-turn-updates-{uuid4()}"
        self.test_thread_ids.append(thread_id)

        # Turn 1: Initial messages
        messages = [
            HumanMessage(content=f"Turn 1 msg {i}" + " " * 100, id=f"msg_{i}")
            for i in range(10)
        ]
        messages = add_linkedin_metadata(messages)

        config = self._create_test_config(
            mode=SummarizationMode.FROM_SCRATCH,
            strategy=CompactionStrategyType.SUMMARIZATION,
            max_tokens=5000,
            target_tokens=3000,
        )

        result1 = await self._run_compaction(
            messages=messages,
            config=config,
            thread_id=thread_id,
        )

        history = result1.get("summarized_messages", [])
        current_1 = result1.get("current_messages", [])
        history = merge_current_messages_into_history(history, current_1)

        # Find msg_3 position
        msg_3_pos = None
        for i, msg in enumerate(history):
            if msg.id == "msg_3":
                msg_3_pos = i
                break

        self.assertIsNotNone(msg_3_pos, "msg_3 should exist")

        # Turn 2: Update msg_3
        updated_msg_3_turn2 = AIMessage(
            content="Turn 2 update" + " " * 100,
            id="msg_3",
            response_metadata={"turn": 2, "section_label": "MARKED"}
        )

        current_2 = [updated_msg_3_turn2]
        history = merge_current_messages_into_history(history, current_2)

        # Verify: Still at same position
        self.assertEqual(history[msg_3_pos].id, "msg_3", "msg_3 should be at same position")
        self.assertEqual(
            history[msg_3_pos].response_metadata.get("turn"), 2,
            "Should have turn 2 metadata"
        )
        verify_message_id_deduplication(history)

        # Turn 3: Update msg_3 again
        updated_msg_3_turn3 = AIMessage(
            content="Turn 3 update" + " " * 100,
            id="msg_3",
            response_metadata={"turn": 3, "section_label": "RECENT", "ingested": True}
        )

        current_3 = [updated_msg_3_turn3]
        history = merge_current_messages_into_history(history, current_3)

        # Verify: STILL at same position
        self.assertEqual(history[msg_3_pos].id, "msg_3", "msg_3 should still be at same position")
        self.assertEqual(
            history[msg_3_pos].response_metadata.get("turn"), 3,
            "Should have turn 3 metadata"
        )
        verify_message_id_deduplication(history)

    async def test_progressive_metadata_accumulation_5_turns(self):
        """
        Test: Progressive metadata accumulation across 5 turns.

        Turn 1: msg_123 has section_label
        Turn 2: msg_123 gets graph_edges → in current_messages
        Turn 3: msg_123 gets ingestion metadata → in current_messages
        Turn 4: msg_123 gets extraction metadata → in current_messages
        Turn 5: msg_123 gets updated section_label → in current_messages

        Verify: Each turn replaces at same position, metadata accumulates.
        """
        thread_id = f"test-5-turn-metadata-{uuid4()}"
        self.test_thread_ids.append(thread_id)

        # Turn 1: Initialize
        msg = HumanMessage(
            content="Message that accumulates metadata" + " " * 200,
            id="msg_accumulate",
            response_metadata={"section_label": "RECENT"}
        )
        add_linkedin_metadata([msg])

        history = [msg]

        # Turn 2: Add graph_edges
        msg_turn2 = AIMessage(
            content=msg.content,
            id="msg_accumulate",
            response_metadata={
                "section_label": "RECENT",
                "graph_edges": ["edge1", "edge2"],
            }
        )
        history = merge_current_messages_into_history(history, [msg_turn2])
        self.assertEqual(len(history), 1, "Should still be 1 message")
        self.assertIn("graph_edges", history[0].response_metadata)

        # Turn 3: Add ingestion metadata
        msg_turn3 = AIMessage(
            content=msg.content,
            id="msg_accumulate",
            response_metadata={
                "section_label": "RECENT",
                "graph_edges": ["edge1", "edge2"],
                "ingested": True,
                "ingestion_timestamp": "2025-01-01T00:00:00Z",
            }
        )
        history = merge_current_messages_into_history(history, [msg_turn3])
        self.assertEqual(len(history), 1, "Should still be 1 message")
        self.assertTrue(history[0].response_metadata.get("ingested"))

        # Turn 4: Add extraction metadata
        msg_turn4 = AIMessage(
            content=msg.content,
            id="msg_accumulate",
            response_metadata={
                "section_label": "RECENT",
                "graph_edges": ["edge1", "edge2"],
                "ingested": True,
                "ingestion_timestamp": "2025-01-01T00:00:00Z",
                "extracted": True,
                "relevance_score": 0.95,
            }
        )
        history = merge_current_messages_into_history(history, [msg_turn4])
        self.assertEqual(len(history), 1, "Should still be 1 message")
        self.assertTrue(history[0].response_metadata.get("extracted"))

        # Turn 5: Update section_label
        msg_turn5 = AIMessage(
            content=msg.content,
            id="msg_accumulate",
            response_metadata={
                "section_label": "MARKED",  # Changed
                "graph_edges": ["edge1", "edge2"],
                "ingested": True,
                "ingestion_timestamp": "2025-01-01T00:00:00Z",
                "extracted": True,
                "relevance_score": 0.95,
            }
        )
        history = merge_current_messages_into_history(history, [msg_turn5])
        self.assertEqual(len(history), 1, "Should still be 1 message")
        self.assertEqual(
            history[0].response_metadata.get("section_label"), "MARKED",
            "Section label should be updated"
        )

        # Final verification
        verify_message_id_deduplication(history)

    async def test_bulk_update_10_messages_across_3_turns(self):
        """
        Test: Bulk updates of multiple messages across turns.

        Turn 1: 10 messages
        Turn 2: 5 messages updated → current_messages
        Turn 3: All 10 updated → current_messages

        Verify: Correct positions, no duplicates.
        """
        thread_id = f"test-bulk-updates-{uuid4()}"
        self.test_thread_ids.append(thread_id)

        # Turn 1: 10 initial messages
        messages = [
            HumanMessage(content=f"Message {i}" + " " * 100, id=f"msg_{i}")
            for i in range(10)
        ]
        messages = add_linkedin_metadata(messages)
        history = messages.copy()

        # Store original positions
        original_positions = {msg.id: i for i, msg in enumerate(history)}

        # Turn 2: Update 5 messages (0, 2, 4, 6, 8)
        updates_turn2 = [
            AIMessage(
                content=f"Updated message {i} turn 2" + " " * 100,
                id=f"msg_{i}",
                response_metadata={"turn": 2}
            )
            for i in [0, 2, 4, 6, 8]
        ]

        history = merge_current_messages_into_history(history, updates_turn2)
        self.assertEqual(len(history), 10, "Should still have 10 messages")
        verify_message_id_deduplication(history)

        # Verify positions unchanged
        for i, msg in enumerate(history):
            expected_pos = original_positions.get(msg.id)
            if expected_pos is not None:
                self.assertEqual(i, expected_pos, f"{msg.id} moved from position {expected_pos}")

        # Turn 3: Update all 10 messages
        updates_turn3 = [
            AIMessage(
                content=f"Updated message {i} turn 3" + " " * 100,
                id=f"msg_{i}",
                response_metadata={"turn": 3}
            )
            for i in range(10)
        ]

        history = merge_current_messages_into_history(history, updates_turn3)
        self.assertEqual(len(history), 10, "Should still have 10 messages")
        verify_message_id_deduplication(history)

        # Verify all have turn 3 metadata
        for msg in history:
            self.assertEqual(
                msg.response_metadata.get("turn"), 3,
                f"{msg.id} should have turn 3 metadata"
            )

    async def test_interleaved_updates_and_new_messages_5_turns(self):
        """
        Test: Interleaved updates and new messages across 5 turns.

        Each turn: Some existing updated, some new added.
        Verify: Chronological order maintained, no duplicates.
        """
        thread_id = f"test-interleaved-5-turns-{uuid4()}"
        self.test_thread_ids.append(thread_id)

        # Turn 1: 5 initial messages
        history = [
            HumanMessage(content=f"Turn 1 msg {i}" + " " * 100, id=f"msg_1_{i}")
            for i in range(5)
        ]
        add_linkedin_metadata(history)

        # Turn 2: Update 2, add 3 new
        updates_turn2 = [
            AIMessage(content="Updated 1_0" + " " * 100, id="msg_1_0", response_metadata={"turn": 2}),
            AIMessage(content="Updated 1_2" + " " * 100, id="msg_1_2", response_metadata={"turn": 2}),
        ]
        new_turn2 = [
            HumanMessage(content=f"Turn 2 new {i}" + " " * 100, id=f"msg_2_{i}")
            for i in range(3)
        ]
        add_linkedin_metadata(new_turn2)

        history = merge_current_messages_into_history(history, updates_turn2 + new_turn2)
        self.assertEqual(len(history), 8, "Should have 8 messages after turn 2")
        verify_message_id_deduplication(history)

        # Turn 3: Update 3, add 2 new
        updates_turn3 = [
            AIMessage(content="Updated 1_1" + " " * 100, id="msg_1_1", response_metadata={"turn": 3}),
            AIMessage(content="Updated 2_0" + " " * 100, id="msg_2_0", response_metadata={"turn": 3}),
            AIMessage(content="Updated 2_1" + " " * 100, id="msg_2_1", response_metadata={"turn": 3}),
        ]
        new_turn3 = [
            HumanMessage(content=f"Turn 3 new {i}" + " " * 100, id=f"msg_3_{i}")
            for i in range(2)
        ]
        add_linkedin_metadata(new_turn3)

        history = merge_current_messages_into_history(history, updates_turn3 + new_turn3)
        self.assertEqual(len(history), 10, "Should have 10 messages after turn 3")
        verify_message_id_deduplication(history)

        # Continue for turns 4 and 5...
        # Turn 4
        updates_turn4 = [
            AIMessage(content="Updated 1_3" + " " * 100, id="msg_1_3", response_metadata={"turn": 4}),
        ]
        new_turn4 = [
            HumanMessage(content="Turn 4 new" + " " * 100, id="msg_4_0")
        ]
        add_linkedin_metadata(new_turn4)

        history = merge_current_messages_into_history(history, updates_turn4 + new_turn4)
        self.assertEqual(len(history), 11, "Should have 11 messages after turn 4")
        verify_message_id_deduplication(history)

        # Turn 5
        updates_turn5 = [
            AIMessage(content="Updated 3_0" + " " * 100, id="msg_3_0", response_metadata={"turn": 5}),
            AIMessage(content="Updated 4_0" + " " * 100, id="msg_4_0", response_metadata={"turn": 5}),
        ]

        history = merge_current_messages_into_history(history, updates_turn5)
        self.assertEqual(len(history), 11, "Should still have 11 messages after turn 5")
        verify_message_id_deduplication(history)

    async def test_large_history_1000_messages_updates(self):
        """
        Test: Large history with 1000 messages, updating 100 scattered throughout.

        Verify: Correct positions, performance acceptable, no duplicates.
        """
        thread_id = f"test-1000-messages-{uuid4()}"
        self.test_thread_ids.append(thread_id)

        # Create 1000 messages
        history = [
            HumanMessage(content=f"Message {i}" + " " * 50, id=f"msg_{i}")
            for i in range(1000)
        ]
        add_linkedin_metadata(history)

        # Store original positions
        original_positions = {msg.id: i for i, msg in enumerate(history)}

        # Update 100 messages (every 10th message)
        updates = [
            AIMessage(
                content=f"Updated message {i}" + " " * 50,
                id=f"msg_{i}",
                response_metadata={"updated": True}
            )
            for i in range(0, 1000, 10)
        ]

        # Merge and time it
        import time
        start = time.time()
        history = merge_current_messages_into_history(history, updates)
        elapsed = time.time() - start

        # Verify: Still 1000 messages
        self.assertEqual(len(history), 1000, "Should still have 1000 messages")

        # Verify: No duplicates
        verify_message_id_deduplication(history)

        # Verify: Updated messages at correct positions
        for i in range(0, 1000, 10):
            msg_id = f"msg_{i}"
            expected_pos = original_positions[msg_id]
            actual_msg = history[expected_pos]
            self.assertEqual(actual_msg.id, msg_id, f"{msg_id} should be at position {expected_pos}")
            self.assertTrue(
                actual_msg.response_metadata.get("updated"),
                f"{msg_id} should have updated flag"
            )

        # Performance check (should be fast)
        self.assertLess(elapsed, 1.0, f"Merge took too long: {elapsed:.2f}s")

    # ========================================
    # Edge Cases (5 tests)
    # ========================================

    async def test_message_without_id_handling(self):
        """
        Test: Message with id=None or missing.

        Verify: Error or skip gracefully.
        """
        thread_id = f"test-no-id-{uuid4()}"
        self.test_thread_ids.append(thread_id)

        history = [
            HumanMessage(content="Message with ID" + " " * 100, id="msg_1"),
        ]

        # Message without ID
        msg_no_id = HumanMessage(content="Message without ID" + " " * 100)
        # Explicitly set id to None
        msg_no_id.id = None

        try:
            history = merge_current_messages_into_history(history, [msg_no_id])
            # If no error, verify handling
            # Message without ID should either be skipped or assigned a new ID
        except (ValueError, AssertionError) as e:
            # Expected: May raise error for missing ID
            self.assertIn("id", str(e).lower(), "Error should mention missing ID")

    async def test_duplicate_ids_in_current_messages(self):
        """
        Test: current_messages has duplicate IDs.

        Pattern: current_messages = [msg_1, msg_1] (same ID twice)
        Verify: Error or use last one.
        """
        thread_id = f"test-duplicate-current-{uuid4()}"
        self.test_thread_ids.append(thread_id)

        history = [
            HumanMessage(content="Original msg_1" + " " * 100, id="msg_1"),
            HumanMessage(content="Message 2" + " " * 100, id="msg_2"),
        ]

        # current_messages with duplicate ID
        current_msgs = [
            AIMessage(content="First update of msg_1" + " " * 100, id="msg_1", response_metadata={"version": 1}),
            AIMessage(content="Second update of msg_1" + " " * 100, id="msg_1", response_metadata={"version": 2}),
        ]

        history = merge_current_messages_into_history(history, current_msgs)

        # Verify: Only 2 messages (no duplicate)
        self.assertEqual(len(history), 2, "Should have 2 messages")

        # Verify: Last version used (version 2)
        self.assertEqual(
            history[0].response_metadata.get("version"), 2,
            "Should use last version when duplicates in current_messages"
        )

        verify_message_id_deduplication(history)

    async def test_all_messages_are_updates_no_new(self):
        """
        Test: current_messages only has updates, no new messages.

        Verify: All replaced, history length unchanged.
        """
        thread_id = f"test-all-updates-{uuid4()}"
        self.test_thread_ids.append(thread_id)

        # Initial history
        history = [
            HumanMessage(content=f"Message {i}" + " " * 100, id=f"msg_{i}")
            for i in range(10)
        ]
        add_linkedin_metadata(history)

        # Update all 10 messages
        updates = [
            AIMessage(
                content=f"Updated message {i}" + " " * 100,
                id=f"msg_{i}",
                response_metadata={"updated": True}
            )
            for i in range(10)
        ]

        history = merge_current_messages_into_history(history, updates)

        # Verify: Still 10 messages
        self.assertEqual(len(history), 10, "Should still have 10 messages")

        # Verify: All updated
        for msg in history:
            self.assertTrue(
                msg.response_metadata.get("updated"),
                f"{msg.id} should be updated"
            )

        verify_message_id_deduplication(history)

    async def test_all_messages_are_new_no_updates(self):
        """
        Test: current_messages only has new messages.

        Verify: All appended.
        """
        thread_id = f"test-all-new-{uuid4()}"
        self.test_thread_ids.append(thread_id)

        # Initial history
        history = [
            HumanMessage(content=f"Message {i}" + " " * 100, id=f"msg_{i}")
            for i in range(5)
        ]
        add_linkedin_metadata(history)

        # All new messages
        new_messages = [
            HumanMessage(content=f"New message {i}" + " " * 100, id=f"new_msg_{i}")
            for i in range(5)
        ]
        add_linkedin_metadata(new_messages)

        history = merge_current_messages_into_history(history, new_messages)

        # Verify: 10 messages total
        self.assertEqual(len(history), 10, "Should have 10 messages")

        # Verify: Last 5 are new messages
        for i in range(5):
            self.assertEqual(
                history[5 + i].id, f"new_msg_{i}",
                f"Position {5+i} should be new_msg_{i}"
            )

        verify_message_id_deduplication(history)

    async def test_empty_current_messages(self):
        """
        Test: current_messages is empty.

        Verify: History unchanged.
        """
        thread_id = f"test-empty-current-{uuid4()}"
        self.test_thread_ids.append(thread_id)

        # Initial history
        history = [
            HumanMessage(content=f"Message {i}" + " " * 100, id=f"msg_{i}")
            for i in range(5)
        ]
        add_linkedin_metadata(history)

        original_length = len(history)

        # Empty current_messages
        current_msgs = []

        history = merge_current_messages_into_history(history, current_msgs)

        # Verify: Unchanged
        self.assertEqual(len(history), original_length, "History should be unchanged")

        verify_message_id_deduplication(history)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
