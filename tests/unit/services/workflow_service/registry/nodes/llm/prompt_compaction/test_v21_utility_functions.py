"""
Unit tests for v2.1 utility functions.

Tests cover:
- set_ingestion_metadata with section_label parameter
- set_extraction_metadata with deduplicated_chunk_ids parameter
- get_deduplicated_chunk_ids returns empty list if none
- find_extractions_with_deduplicated_chunk finds matches
- move_deduplicated_to_chunk_ids moves correctly
- move_deduplicated_to_chunk_ids prevents duplicates

Test IDs: 50-55 (from comprehensive test plan)
"""

import unittest
from unittest.mock import Mock

from langchain_core.messages import HumanMessage, AIMessage

from workflow_service.registry.nodes.llm.prompt_compaction.utils import (
    set_ingestion_metadata,
    set_extraction_metadata,
    get_ingestion_chunk_ids,
    get_extraction_chunk_ids,
    get_deduplicated_chunk_ids,
    find_extractions_with_deduplicated_chunk,
    move_deduplicated_to_chunk_ids,
    get_compaction_metadata,
    MessageSectionLabel,
)


class TestIngestionMetadataUtilities(unittest.TestCase):
    """Test 50: Ingestion metadata utilities with section_label."""

    def test_set_ingestion_metadata_with_section_label(self):
        """Test 50: section_label parameter works in set_ingestion_metadata."""
        message = HumanMessage(content="Test message", id="msg_1")

        # Set ingestion metadata with section label
        set_ingestion_metadata(
            message,
            chunk_ids=["chunk_1", "chunk_2"],
            section_label=MessageSectionLabel.HISTORICAL,
        )

        # Verify metadata
        ingestion_meta = get_compaction_metadata(message, "ingestion", {})
        self.assertTrue(ingestion_meta.get("ingested"))
        self.assertEqual(ingestion_meta.get("section_label"), MessageSectionLabel.HISTORICAL)

        chunk_ids = get_ingestion_chunk_ids(message)
        self.assertEqual(set(chunk_ids), {"chunk_1", "chunk_2"})

        # Test with different section label
        message2 = HumanMessage(content="Marked message", id="msg_2")
        set_ingestion_metadata(
            message2,
            chunk_ids=["chunk_3"],
            section_label=MessageSectionLabel.MARKED,
        )

        ingestion_meta2 = get_compaction_metadata(message2, "ingestion", {})
        self.assertEqual(ingestion_meta2.get("section_label"), MessageSectionLabel.MARKED)


class TestExtractionMetadataUtilities(unittest.TestCase):
    """Test 51: Extraction metadata utilities with deduplicated_chunk_ids."""

    def test_set_extraction_metadata_with_deduplicated(self):
        """Test 51: deduplicated_chunk_ids parameter works in set_extraction_metadata."""
        extraction = AIMessage(content="Summary", id="extract_1")

        # Set extraction metadata with deduplicated chunks
        set_extraction_metadata(
            extraction,
            chunk_ids=["chunk_1", "chunk_2"],
            deduplicated_chunk_ids=["dup_1", "dup_2", "dup_3"],
            strategy="extract_full",
        )

        # Verify metadata
        extraction_meta = get_compaction_metadata(extraction, "extraction", {})
        self.assertIn("deduplicated_chunk_ids", extraction_meta)
        self.assertEqual(
            set(extraction_meta["deduplicated_chunk_ids"]),
            {"dup_1", "dup_2", "dup_3"}
        )

        # Verify utility functions
        chunk_ids = get_extraction_chunk_ids(extraction)
        deduplicated_ids = get_deduplicated_chunk_ids(extraction)

        self.assertEqual(set(chunk_ids), {"chunk_1", "chunk_2"})
        self.assertEqual(set(deduplicated_ids), {"dup_1", "dup_2", "dup_3"})


class TestDeduplicationUtilityFunctions(unittest.TestCase):
    """Test 52-55: Deduplication utility function behavior."""

    def test_get_deduplicated_chunk_ids_returns_empty_list(self):
        """Test 52: Returns empty list if no deduplicated chunks."""
        # Message with no metadata
        msg_no_meta = HumanMessage(content="Test", id="msg_1")
        self.assertEqual(get_deduplicated_chunk_ids(msg_no_meta), [])

        # Message with extraction metadata but no deduplicated chunks
        msg_empty_dedup = AIMessage(content="Summary", id="msg_2")
        set_extraction_metadata(
            msg_empty_dedup,
            chunk_ids=["chunk_1"],
            deduplicated_chunk_ids=[],  # Explicitly empty
            strategy="extract_full",
        )
        self.assertEqual(get_deduplicated_chunk_ids(msg_empty_dedup), [])

    def test_find_extractions_with_deduplicated_chunk_finds_matches(self):
        """Test 53: Finds extractions containing a specific deduplicated chunk."""
        # Create extractions with various deduplicated chunks
        extract1 = AIMessage(content="Extract 1", id="e1")
        set_extraction_metadata(
            extract1,
            chunk_ids=["c1"],
            deduplicated_chunk_ids=["target_chunk", "other_chunk"],
            strategy="extract_full",
        )

        extract2 = AIMessage(content="Extract 2", id="e2")
        set_extraction_metadata(
            extract2,
            chunk_ids=["c2"],
            deduplicated_chunk_ids=["different_chunk"],
            strategy="extract_full",
        )

        extract3 = AIMessage(content="Extract 3", id="e3")
        set_extraction_metadata(
            extract3,
            chunk_ids=["c3"],
            deduplicated_chunk_ids=["target_chunk"],  # Also has target_chunk
            strategy="extract_full",
        )

        extractions = [extract1, extract2, extract3]

        # Find extractions with target_chunk
        found = find_extractions_with_deduplicated_chunk(extractions, "target_chunk")
        self.assertEqual(len(found), 2)
        self.assertIn(extract1, found)
        self.assertIn(extract3, found)
        self.assertNotIn(extract2, found)

        # Find extractions with different_chunk
        found_diff = find_extractions_with_deduplicated_chunk(extractions, "different_chunk")
        self.assertEqual(len(found_diff), 1)
        self.assertIn(extract2, found_diff)

        # Find non-existent chunk
        found_none = find_extractions_with_deduplicated_chunk(extractions, "nonexistent")
        self.assertEqual(len(found_none), 0)

    def test_move_deduplicated_to_chunk_ids_moves_correctly(self):
        """Test 54: Correctly moves chunks from deduplicated to chunk_ids list."""
        message = AIMessage(content="Extract", id="e1")

        # Setup initial state
        set_extraction_metadata(
            message,
            chunk_ids=["c1", "c2"],
            deduplicated_chunk_ids=["d1", "d2", "d3", "d4"],
            strategy="extract_full",
        )

        # Move d1 and d3
        move_deduplicated_to_chunk_ids(message, ["d1", "d3"])

        # Verify the move
        chunk_ids = get_extraction_chunk_ids(message)
        deduplicated_ids = get_deduplicated_chunk_ids(message)

        # d1 and d3 should be in chunk_ids
        self.assertIn("d1", chunk_ids)
        self.assertIn("d3", chunk_ids)

        # d1 and d3 should NOT be in deduplicated_ids
        self.assertNotIn("d1", deduplicated_ids)
        self.assertNotIn("d3", deduplicated_ids)

        # d2 and d4 should remain in deduplicated_ids
        self.assertIn("d2", deduplicated_ids)
        self.assertIn("d4", deduplicated_ids)

        # c1 and c2 should still be in chunk_ids
        self.assertIn("c1", chunk_ids)
        self.assertIn("c2", chunk_ids)

    def test_move_deduplicated_to_chunk_ids_no_duplicates(self):
        """Test 55: No duplicate chunk_ids are created during move."""
        message = AIMessage(content="Extract", id="e1")

        # Setup with some chunks in chunk_ids
        set_extraction_metadata(
            message,
            chunk_ids=["c1", "c2", "c3"],
            deduplicated_chunk_ids=["d1", "d2"],
            strategy="extract_full",
        )

        # Move d1
        move_deduplicated_to_chunk_ids(message, ["d1"])

        # Verify no duplicates
        chunk_ids = get_extraction_chunk_ids(message)
        self.assertEqual(len(chunk_ids), len(set(chunk_ids)), "chunk_ids should have no duplicates")

        # Try moving the same chunk again (should be no-op)
        move_deduplicated_to_chunk_ids(message, ["d1"])

        # Verify still no duplicates
        chunk_ids_after = get_extraction_chunk_ids(message)
        self.assertEqual(len(chunk_ids_after), len(set(chunk_ids_after)), "chunk_ids should still have no duplicates")

        # d1 should appear exactly once in chunk_ids
        self.assertEqual(chunk_ids_after.count("d1"), 1)


if __name__ == "__main__":
    unittest.main()
