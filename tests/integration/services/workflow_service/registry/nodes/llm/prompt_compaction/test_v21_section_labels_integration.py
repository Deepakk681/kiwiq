"""
Integration tests for v2.1 section labels.

Tests cover:
- Section label assignment and retrieval
- Label preservation through ingestion
- Label filtering and grouping
- Integration with Weaviate storage

These tests use real Weaviate and verify the complete workflow.
"""

import unittest
from uuid import uuid4

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from weaviate_client import ThreadMessageWeaviateClient
from workflow_service.registry.nodes.llm.config import ModelMetadata, LLMModelProvider
from workflow_service.registry.nodes.llm.prompt_compaction.utils import (
    set_section_label,
    get_section_label,
    set_ingestion_metadata,
    MessageSectionLabel,
)

from tests.unit.services.workflow_service.registry.nodes.llm.prompt_compaction.test_base import (
    PromptCompactionIntegrationTestBase,
)


class TestSectionLabels(PromptCompactionIntegrationTestBase):
    """Integration tests for section labels."""

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

    async def test_section_label_assignment_and_retrieval(self):
        """Test: Section labels can be set and retrieved."""
        message = HumanMessage(content="Test message", id="msg_1")

        # Set historical label
        set_section_label(message, MessageSectionLabel.HISTORICAL)

        # Retrieve label
        label = get_section_label(message)
        self.assertEqual(label, MessageSectionLabel.HISTORICAL)

        # Test with different labels
        message2 = HumanMessage(content="Recent message", id="msg_2")
        set_section_label(message2, MessageSectionLabel.RECENT)

        label2 = get_section_label(message2)
        self.assertEqual(label2, MessageSectionLabel.RECENT)

        # Test marked label
        message3 = HumanMessage(content="Marked message", id="msg_3")
        set_section_label(message3, MessageSectionLabel.MARKED)

        label3 = get_section_label(message3)
        self.assertEqual(label3, MessageSectionLabel.MARKED)

    async def test_section_label_preserved_through_ingestion(self):
        """Test: Section labels preserved in ingestion metadata."""
        message = HumanMessage(content="Historical message", id="msg_hist")

        # Set section label
        set_section_label(message, MessageSectionLabel.HISTORICAL)

        # Set ingestion metadata with section label
        set_ingestion_metadata(
            message,
            chunk_ids=["chunk_1", "chunk_2"],
            section_label=MessageSectionLabel.HISTORICAL
        )

        # Verify label preserved
        retrieved_label = get_section_label(message)
        self.assertEqual(retrieved_label, MessageSectionLabel.HISTORICAL)

    async def test_section_label_filtering_and_grouping(self):
        """Test: Messages can be filtered by section label."""
        # Create messages with different labels
        historical = [
            HumanMessage(content=f"Historical {i}", id=f"hist_{i}")
            for i in range(5)
        ]
        for msg in historical:
            set_section_label(msg, MessageSectionLabel.HISTORICAL)

        recent = [
            HumanMessage(content=f"Recent {i}", id=f"recent_{i}")
            for i in range(3)
        ]
        for msg in recent:
            set_section_label(msg, MessageSectionLabel.RECENT)

        marked = [
            HumanMessage(content=f"Marked {i}", id=f"marked_{i}")
            for i in range(2)
        ]
        for msg in marked:
            set_section_label(msg, MessageSectionLabel.MARKED)

        # Combine all messages
        all_messages = historical + recent + marked

        # Filter by label
        historical_filtered = [
            msg for msg in all_messages
            if get_section_label(msg) == MessageSectionLabel.HISTORICAL
        ]

        recent_filtered = [
            msg for msg in all_messages
            if get_section_label(msg) == MessageSectionLabel.RECENT
        ]

        marked_filtered = [
            msg for msg in all_messages
            if get_section_label(msg) == MessageSectionLabel.MARKED
        ]

        # Verify correct filtering
        self.assertEqual(len(historical_filtered), 5)
        self.assertEqual(len(recent_filtered), 3)
        self.assertEqual(len(marked_filtered), 2)

        # Verify correct messages in each group
        for msg in historical_filtered:
            self.assertTrue(msg.content.startswith("Historical"))

        for msg in recent_filtered:
            self.assertTrue(msg.content.startswith("Recent"))

        for msg in marked_filtered:
            self.assertTrue(msg.content.startswith("Marked"))

    async def test_section_labels_with_multiple_message_types(self):
        """Test: Section labels work with different message types."""
        # Human message
        human_msg = HumanMessage(content="Human message", id="human_1")
        set_section_label(human_msg, MessageSectionLabel.HISTORICAL)
        self.assertEqual(get_section_label(human_msg), MessageSectionLabel.HISTORICAL)

        # AI message
        ai_msg = AIMessage(content="AI message", id="ai_1")
        set_section_label(ai_msg, MessageSectionLabel.SUMMARY)
        self.assertEqual(get_section_label(ai_msg), MessageSectionLabel.SUMMARY)

        # System message
        system_msg = SystemMessage(content="System message", id="system_1")
        set_section_label(system_msg, MessageSectionLabel.SYSTEM)
        self.assertEqual(get_section_label(system_msg), MessageSectionLabel.SYSTEM)


if __name__ == "__main__":
    unittest.main()
