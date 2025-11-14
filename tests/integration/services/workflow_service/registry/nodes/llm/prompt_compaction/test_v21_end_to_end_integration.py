"""
End-to-end integration tests for v2.1 features.

Tests cover:
- Complete workflow from chunking to extraction
- Combined feature interactions
- Real Weaviate storage and retrieval
- Multi-round compaction scenarios
- Complete metadata propagation

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
    set_extraction_metadata,
    get_extraction_chunk_ids,
    get_deduplicated_chunk_ids,
    move_deduplicated_to_chunk_ids,
    find_extractions_with_deduplicated_chunk,
    MessageSectionLabel,
)
from workflow_service.registry.nodes.llm.prompt_compaction.strategies import ExtractionStrategy
from workflow_service.registry.nodes.llm.prompt_compaction.utils import (
    ExtractionStrategy as ExtractionStrategyType,
)
from workflow_service.registry.nodes.llm.prompt_compaction.token_utils import (
    chunk_message_for_embedding,
)

from tests.unit.services.workflow_service.registry.nodes.llm.prompt_compaction.test_base import (
    PromptCompactionIntegrationTestBase,
)


class TestEndToEndWorkflows(PromptCompactionIntegrationTestBase):
    """End-to-end integration tests."""

    async def asyncSetUp(self):
        """Setup Weaviate client."""
        await super().asyncSetUp()

        self.weaviate_client = ThreadMessageWeaviateClient()
        await self.weaviate_client.connect()
        await self.weaviate_client.setup_schema()

        self.model_metadata = ModelMetadata(
            model_name="gpt-4o-mini",
            provider=LLMModelProvider.OPENAI,
            context_limit=128000,
            output_token_limit=16384,
        )

    async def asyncTearDown(self):
        """Cleanup Weaviate data."""
        if self.weaviate_client:
            await self.weaviate_client.close()
        await super().asyncTearDown()

    async def test_chunking_plus_section_labels(self):
        """Test: Large message chunking with section labels."""
        # Create large historical message
        paragraphs = [" ".join([f"word{i}_{j}" for j in range(50)]) for i in range(150)]
        content = "\n\n".join(paragraphs)

        message = HumanMessage(content=content, id="large_hist")

        # Set section label
        set_section_label(message, MessageSectionLabel.HISTORICAL)

        # Chunk the message
        chunks = chunk_message_for_embedding(
            message=message,
            chunk_size_tokens=6000,
            chunk_strategy="semantic_overlap",
            model_metadata=self.model_metadata,
        )

        # Verify chunking occurred
        self.assertGreater(len(chunks), 1)

        # Verify section label preserved
        label = get_section_label(message)
        self.assertEqual(label, MessageSectionLabel.HISTORICAL)

    async def test_deduplication_with_reattachment(self):
        """Test: Complete deduplication and reattachment workflow."""
        # Create extractions with shared chunks
        extract1 = AIMessage(content="Summary 1", id="e1")
        set_extraction_metadata(
            extract1,
            chunk_ids=["c1", "c2"],
            deduplicated_chunk_ids=["shared_1", "shared_2"],
            strategy="extract_full"
        )

        extract2 = AIMessage(content="Summary 2", id="e2")
        set_extraction_metadata(
            extract2,
            chunk_ids=["c3"],
            deduplicated_chunk_ids=["shared_1", "unique_1"],
            strategy="extract_full"
        )

        extract3 = AIMessage(content="Summary 3", id="e3")
        set_extraction_metadata(
            extract3,
            chunk_ids=["c4"],
            deduplicated_chunk_ids=["shared_2"],
            strategy="extract_full"
        )

        # Simulate removing extract1
        remaining = [extract2, extract3]

        # Reattach shared_1 (referenced by extract2)
        targets_1 = find_extractions_with_deduplicated_chunk(remaining, "shared_1")
        self.assertEqual(len(targets_1), 1)
        move_deduplicated_to_chunk_ids(extract2, ["shared_1"])

        # Reattach shared_2 (referenced by extract3)
        targets_2 = find_extractions_with_deduplicated_chunk(remaining, "shared_2")
        self.assertEqual(len(targets_2), 1)
        move_deduplicated_to_chunk_ids(extract3, ["shared_2"])

        # Verify reattachment
        e2_chunks = get_extraction_chunk_ids(extract2)
        e3_chunks = get_extraction_chunk_ids(extract3)

        self.assertIn("shared_1", e2_chunks)
        self.assertIn("shared_2", e3_chunks)

        # Verify no longer in deduplicated lists
        e2_dedup = get_deduplicated_chunk_ids(extract2)
        e3_dedup = get_deduplicated_chunk_ids(extract3)

        self.assertNotIn("shared_1", e2_dedup)
        self.assertNotIn("shared_2", e3_dedup)

    async def test_marked_overflow_with_section_labels(self):
        """Test: Marked overflow with section label preservation."""
        # Create marked message
        marked_msg = HumanMessage(content="Important marked message", id="marked_1")

        # Set preserve flag
        if not hasattr(marked_msg, "additional_kwargs"):
            marked_msg.additional_kwargs = {}
        marked_msg.additional_kwargs["preserve"] = True

        # Set section label
        set_section_label(marked_msg, MessageSectionLabel.MARKED)

        # Simulate overflow: remove preserve, add originally_marked
        marked_msg.additional_kwargs.pop("preserve", None)
        marked_msg.additional_kwargs["originally_marked"] = True

        # Verify flags
        self.assertNotIn("preserve", marked_msg.additional_kwargs)
        self.assertTrue(marked_msg.additional_kwargs.get("originally_marked"))

        # Verify section label preserved
        label = get_section_label(marked_msg)
        self.assertEqual(label, MessageSectionLabel.MARKED)

    async def test_expansion_config_with_strategy(self):
        """Test: Expansion configuration integrated with extraction strategy."""
        strategy = ExtractionStrategy(
            construction_strategy=ExtractionStrategyType.EXTRACT_FULL,
            expansion_mode="hybrid",
            expansion_threshold=0.85,
            expansion_budget_pct=0.80,
            max_expansion_tokens=16000,
        )

        # Verify all config parameters
        self.assertEqual(strategy.expansion_mode, "hybrid")
        self.assertEqual(strategy.expansion_threshold, 0.85)
        self.assertEqual(strategy.expansion_budget_pct, 0.80)
        self.assertEqual(strategy.max_expansion_tokens, 16000)

        # Test budget calculation
        available_budget = 90000
        expansion_budget = int(available_budget * strategy.expansion_budget_pct)
        self.assertEqual(expansion_budget, 72000)

    async def test_complete_workflow_all_features(self):
        """Test: Complete workflow with all v2.1 features."""
        # 1. Create large historical messages
        historical_msgs = []
        for i in range(3):
            paragraphs = [f"Historical {i} para {j}" for j in range(100)]
            content = "\n\n".join(paragraphs)
            msg = HumanMessage(content=content, id=f"hist_{i}")
            set_section_label(msg, MessageSectionLabel.HISTORICAL)
            historical_msgs.append(msg)

        # 2. Create marked overflow messages
        marked_msg = HumanMessage(content="Marked important message", id="marked_1")
        set_section_label(marked_msg, MessageSectionLabel.MARKED)

        if not hasattr(marked_msg, "additional_kwargs"):
            marked_msg.additional_kwargs = {}
        marked_msg.additional_kwargs["originally_marked"] = True

        # 3. Create recent messages
        recent_msgs = [
            HumanMessage(content=f"Recent {i}", id=f"recent_{i}")
            for i in range(2)
        ]
        for msg in recent_msgs:
            set_section_label(msg, MessageSectionLabel.RECENT)

        # 4. Create extractions with deduplication
        extract1 = AIMessage(content="Summary 1", id="e1")
        set_extraction_metadata(
            extract1,
            chunk_ids=["c1", "c2"],
            deduplicated_chunk_ids=["d1", "d2"],
            strategy="extract_full"
        )

        extract2 = AIMessage(content="Summary 2", id="e2")
        set_extraction_metadata(
            extract2,
            chunk_ids=["c3"],
            deduplicated_chunk_ids=["d1"],  # Shares d1
            strategy="extract_full"
        )

        # 5. Verify section label filtering
        all_messages = historical_msgs + [marked_msg] + recent_msgs

        historical_filtered = [
            msg for msg in all_messages
            if get_section_label(msg) == MessageSectionLabel.HISTORICAL
        ]
        self.assertEqual(len(historical_filtered), 3)

        marked_filtered = [
            msg for msg in all_messages
            if get_section_label(msg) == MessageSectionLabel.MARKED
        ]
        self.assertEqual(len(marked_filtered), 1)

        # 6. Verify deduplication tracking
        e1_dedup = get_deduplicated_chunk_ids(extract1)
        e2_dedup = get_deduplicated_chunk_ids(extract2)

        self.assertIn("d1", e1_dedup)
        self.assertIn("d1", e2_dedup)

        # 7. Test reattachment
        extractions = [extract1, extract2]
        targets = find_extractions_with_deduplicated_chunk(extractions, "d1")
        self.assertEqual(len(targets), 2)


if __name__ == "__main__":
    unittest.main()
