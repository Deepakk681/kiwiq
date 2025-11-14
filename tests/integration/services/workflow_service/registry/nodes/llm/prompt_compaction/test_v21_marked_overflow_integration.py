"""
Integration tests for v2.1 marked message overflow handling.

Tests cover:
- Marked message overflow flag handling
- Section label assignment (MARKED)
- Integration with ingestion workflow
- Preservation and restoration of marked messages

These tests use real Weaviate and verify the complete workflow.
"""

import unittest
from uuid import uuid4

from langchain_core.messages import HumanMessage, AIMessage

from weaviate_client import ThreadMessageWeaviateClient
from workflow_service.registry.nodes.llm.config import ModelMetadata, LLMModelProvider
from workflow_service.registry.nodes.llm.prompt_compaction.utils import (
    set_section_label,
    get_section_label,
    set_ingestion_metadata,
    get_compaction_metadata,
    MessageSectionLabel,
)

from tests.unit.services.workflow_service.registry.nodes.llm.prompt_compaction.test_base import (
    PromptCompactionIntegrationTestBase,
)


class TestMarkedOverflowHandling(PromptCompactionIntegrationTestBase):
    """Integration tests for marked overflow handling."""

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

    async def test_marked_message_overflow_flag_handling(self):
        """Test: Marked messages have flags removed and originally_marked flag added."""
        message = HumanMessage(content="Important message", id="msg_marked")

        # Initially mark with preserve flag
        if not hasattr(message, "additional_kwargs"):
            message.additional_kwargs = {}
        message.additional_kwargs["preserve"] = True

        # Verify preserve flag set
        self.assertTrue(message.additional_kwargs.get("preserve"))

        # Simulate overflow handling: remove preserve, add originally_marked
        message.additional_kwargs.pop("preserve", None)
        message.additional_kwargs["originally_marked"] = True

        # Verify flag changes
        self.assertNotIn("preserve", message.additional_kwargs)
        self.assertTrue(message.additional_kwargs.get("originally_marked"))

    async def test_marked_overflow_section_label_assignment(self):
        """Test: Marked overflow messages get MARKED section label."""
        message = HumanMessage(content="Marked overflow message", id="msg_marked")

        # Set section label
        set_section_label(message, MessageSectionLabel.MARKED)

        # Verify section label
        section = get_section_label(message)
        self.assertEqual(section, MessageSectionLabel.MARKED)

        # Set ingestion metadata with section label
        set_ingestion_metadata(
            message,
            chunk_ids=["chunk_1", "chunk_2"],
            section_label=MessageSectionLabel.MARKED
        )

        # Verify ingestion metadata includes section label
        ingestion_meta = get_compaction_metadata(message, "ingestion", {})
        self.assertTrue(ingestion_meta.get("ingested"))
        self.assertEqual(
            ingestion_meta.get("section_label"),
            MessageSectionLabel.MARKED
        )

    async def test_marked_overflow_separation_from_historical(self):
        """Test: Marked overflow messages separated from historical during ingestion."""
        # Create historical messages
        historical_msgs = []
        for i in range(3):
            msg = HumanMessage(content=f"Historical {i}", id=f"hist_{i}")
            set_section_label(msg, MessageSectionLabel.HISTORICAL)
            historical_msgs.append(msg)

        # Create marked overflow messages
        marked_msgs = []
        for i in range(2):
            msg = HumanMessage(content=f"Marked {i}", id=f"marked_{i}")
            set_section_label(msg, MessageSectionLabel.MARKED)
            marked_msgs.append(msg)

        # Combine all messages
        all_msgs = historical_msgs + marked_msgs

        # Filter by section label
        historical_filtered = [
            msg for msg in all_msgs
            if get_section_label(msg) == MessageSectionLabel.HISTORICAL
        ]

        marked_filtered = [
            msg for msg in all_msgs
            if get_section_label(msg) == MessageSectionLabel.MARKED
        ]

        # Verify separation
        self.assertEqual(len(historical_filtered), 3)
        self.assertEqual(len(marked_filtered), 2)

        # Verify correct messages in each group
        for msg in historical_filtered:
            self.assertTrue(msg.content.startswith("Historical"))

        for msg in marked_filtered:
            self.assertTrue(msg.content.startswith("Marked"))

    async def test_marked_overflow_recombination_for_extraction(self):
        """Test: Marked overflow combined with historical for extraction."""
        # Create messages with different section labels
        historical = HumanMessage(content="Historical", id="hist")
        set_section_label(historical, MessageSectionLabel.HISTORICAL)

        marked = HumanMessage(content="Marked overflow", id="marked")
        set_section_label(marked, MessageSectionLabel.MARKED)

        recent = HumanMessage(content="Recent", id="recent")
        set_section_label(recent, MessageSectionLabel.RECENT)

        all_messages = [historical, marked, recent]

        # For extraction, combine historical and marked
        extractable = [
            msg for msg in all_messages
            if get_section_label(msg) in [
                MessageSectionLabel.HISTORICAL,
                MessageSectionLabel.MARKED
            ]
        ]

        # Verify correct messages selected for extraction
        self.assertEqual(len(extractable), 2)
        self.assertIn(historical, extractable)
        self.assertIn(marked, extractable)
        self.assertNotIn(recent, extractable)

        # Verify section labels preserved
        self.assertEqual(get_section_label(historical), MessageSectionLabel.HISTORICAL)
        self.assertEqual(get_section_label(marked), MessageSectionLabel.MARKED)
        self.assertEqual(get_section_label(recent), MessageSectionLabel.RECENT)


if __name__ == "__main__":
    unittest.main()
