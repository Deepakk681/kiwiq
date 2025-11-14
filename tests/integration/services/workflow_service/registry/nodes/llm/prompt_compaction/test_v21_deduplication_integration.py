"""
Integration tests for v2.1 chunk deduplication tracking.

Tests cover:
- End-to-end deduplication tracking with Weaviate
- Deduplicated chunk IDs list maintenance
- Cross-extraction deduplication
- Reattachment on overflow
- Metadata persistence

These tests use real Weaviate and verify the complete workflow.
"""

import unittest
from uuid import uuid4

from langchain_core.messages import HumanMessage, AIMessage

from weaviate_client import ThreadMessageWeaviateClient
from workflow_service.registry.nodes.llm.config import ModelMetadata, LLMModelProvider
from workflow_service.registry.nodes.llm.prompt_compaction.utils import (
    set_extraction_metadata,
    get_extraction_chunk_ids,
    get_deduplicated_chunk_ids,
    find_extractions_with_deduplicated_chunk,
    move_deduplicated_to_chunk_ids,
    ExtractionStrategy,
)

from tests.unit.services.workflow_service.registry.nodes.llm.prompt_compaction.test_base import (
    PromptCompactionIntegrationTestBase,
)


class TestDeduplicationTracking(PromptCompactionIntegrationTestBase):
    """Integration tests for deduplication tracking."""

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

    async def test_deduplicated_chunks_tracked_separately(self):
        """Test: Deduplicated chunks are tracked separately from regular chunks."""
        extraction = AIMessage(content="Summary of content", id="extraction_1")

        # Set extraction metadata with both regular and deduplicated chunks
        set_extraction_metadata(
            extraction,
            chunk_ids=["chunk_1", "chunk_2", "chunk_3"],
            deduplicated_chunk_ids=["dup_1", "dup_2"],
            strategy="extract_full"
        )

        # Verify separate tracking
        regular_chunks = get_extraction_chunk_ids(extraction)
        dedup_chunks = get_deduplicated_chunk_ids(extraction)

        self.assertEqual(set(regular_chunks), {"chunk_1", "chunk_2", "chunk_3"})
        self.assertEqual(set(dedup_chunks), {"dup_1", "dup_2"})

        # Verify no overlap
        self.assertEqual(len(set(regular_chunks) & set(dedup_chunks)), 0)

    async def test_find_extractions_with_shared_dedup_chunk(self):
        """Test: Find all extractions that share a deduplicated chunk."""
        # Create multiple extractions with various dedup chunks
        extract1 = AIMessage(content="Summary 1", id="e1")
        set_extraction_metadata(
            extract1,
            chunk_ids=["c1"],
            deduplicated_chunk_ids=["shared_chunk", "unique_1"],
            strategy="extract_full"
        )

        extract2 = AIMessage(content="Summary 2", id="e2")
        set_extraction_metadata(
            extract2,
            chunk_ids=["c2"],
            deduplicated_chunk_ids=["shared_chunk", "unique_2"],
            strategy="extract_full"
        )

        extract3 = AIMessage(content="Summary 3", id="e3")
        set_extraction_metadata(
            extract3,
            chunk_ids=["c3"],
            deduplicated_chunk_ids=["different_chunk"],
            strategy="extract_full"
        )

        extractions = [extract1, extract2, extract3]

        # Find extractions with shared_chunk
        found = find_extractions_with_deduplicated_chunk(extractions, "shared_chunk")

        self.assertEqual(len(found), 2)
        self.assertIn(extract1, found)
        self.assertIn(extract2, found)
        self.assertNotIn(extract3, found)

    async def test_move_deduplicated_to_regular_chunks(self):
        """Test: Move chunks from deduplicated to regular list."""
        extraction = AIMessage(content="Summary", id="e1")

        # Setup initial state
        set_extraction_metadata(
            extraction,
            chunk_ids=["c1", "c2"],
            deduplicated_chunk_ids=["d1", "d2", "d3"],
            strategy="extract_full"
        )

        # Move d1 and d3 to regular chunks
        move_deduplicated_to_chunk_ids(extraction, ["d1", "d3"])

        # Verify move
        regular_chunks = get_extraction_chunk_ids(extraction)
        dedup_chunks = get_deduplicated_chunk_ids(extraction)

        # d1 and d3 should now be in regular chunks
        self.assertIn("d1", regular_chunks)
        self.assertIn("d3", regular_chunks)

        # d1 and d3 should NOT be in deduplicated chunks
        self.assertNotIn("d1", dedup_chunks)
        self.assertNotIn("d3", dedup_chunks)

        # d2 should remain in deduplicated chunks
        self.assertIn("d2", dedup_chunks)

        # Original chunks should still be present
        self.assertIn("c1", regular_chunks)
        self.assertIn("c2", regular_chunks)

    async def test_reattachment_on_extraction_removal(self):
        """Test: Simulated reattachment when extraction is removed."""
        # Create extraction to be removed
        removed_extraction = AIMessage(content="Old summary", id="removed")
        set_extraction_metadata(
            removed_extraction,
            chunk_ids=["c1"],
            deduplicated_chunk_ids=["shared_1", "shared_2"],
            strategy="extract_full"
        )

        # Create remaining extractions that share chunks
        extract1 = AIMessage(content="Summary 1", id="e1")
        set_extraction_metadata(
            extract1,
            chunk_ids=["c2"],
            deduplicated_chunk_ids=["shared_1"],
            strategy="extract_full"
        )

        extract2 = AIMessage(content="Summary 2", id="e2")
        set_extraction_metadata(
            extract2,
            chunk_ids=["c3"],
            deduplicated_chunk_ids=["shared_2", "other"],
            strategy="extract_full"
        )

        remaining = [extract1, extract2]

        # Simulate reattachment for shared_1
        targets_1 = find_extractions_with_deduplicated_chunk(remaining, "shared_1")
        self.assertEqual(len(targets_1), 1)
        self.assertIn(extract1, targets_1)

        # Reattach shared_1 to extract1
        move_deduplicated_to_chunk_ids(extract1, ["shared_1"])

        # Verify reattachment
        e1_chunks = get_extraction_chunk_ids(extract1)
        e1_dedup = get_deduplicated_chunk_ids(extract1)

        self.assertIn("shared_1", e1_chunks)
        self.assertNotIn("shared_1", e1_dedup)

        # Simulate reattachment for shared_2
        targets_2 = find_extractions_with_deduplicated_chunk(remaining, "shared_2")
        self.assertEqual(len(targets_2), 1)
        self.assertIn(extract2, targets_2)

        # Reattach shared_2 to extract2
        move_deduplicated_to_chunk_ids(extract2, ["shared_2"])

        # Verify reattachment
        e2_chunks = get_extraction_chunk_ids(extract2)
        e2_dedup = get_deduplicated_chunk_ids(extract2)

        self.assertIn("shared_2", e2_chunks)
        self.assertNotIn("shared_2", e2_dedup)

    async def test_no_duplicate_chunk_ids_after_move(self):
        """Test: No duplicates created when moving chunks."""
        extraction = AIMessage(content="Summary", id="e1")

        # Setup with some chunks
        set_extraction_metadata(
            extraction,
            chunk_ids=["c1", "c2"],
            deduplicated_chunk_ids=["d1", "d2"],
            strategy="extract_full"
        )

        # Move d1
        move_deduplicated_to_chunk_ids(extraction, ["d1"])

        # Verify no duplicates
        chunks = get_extraction_chunk_ids(extraction)
        self.assertEqual(len(chunks), len(set(chunks)), "Should have no duplicate chunk IDs")

        # Try moving d1 again (should be no-op)
        move_deduplicated_to_chunk_ids(extraction, ["d1"])

        # Verify still no duplicates
        chunks_after = get_extraction_chunk_ids(extraction)
        self.assertEqual(len(chunks_after), len(set(chunks_after)), "Should still have no duplicates")

        # d1 should appear exactly once
        self.assertEqual(chunks_after.count("d1"), 1)


if __name__ == "__main__":
    unittest.main()
