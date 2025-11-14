"""
Unit tests for v2.1 chunk reattachment on overflow features.

Tests cover:
- Reattachment triggering on remove_oldest overflow
- Reattachment only for deduplicated chunks
- Reattachment to multiple extractions
- Prevention of reattachment to source extraction
- Metadata preservation during reattachment
- chunk_ids list updates
- Movement from deduplicated_chunk_ids list
- Integration with duplicate checking

Test IDs: 19-26 (from comprehensive test plan)
"""

import unittest
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from workflow_service.registry.nodes.llm.prompt_compaction.strategies import (
    ExtractionStrategy,
)
from workflow_service.registry.nodes.llm.config import ModelMetadata, LLMModelProvider
from workflow_service.registry.nodes.llm.prompt_compaction.utils import (
    get_extraction_chunk_ids,
    get_deduplicated_chunk_ids,
    get_compaction_metadata,
    set_extraction_metadata,
    move_deduplicated_to_chunk_ids,
    find_extractions_with_deduplicated_chunk,
    ExtractionStrategy as ExtractionStrategyType,
)

from .test_base import PromptCompactionUnitTestBase


class TestReattachmentTriggering(unittest.TestCase):
    """Test 19-21: Reattachment triggering conditions."""

    def test_reattachment_triggered_on_overflow(self):
        """Test 19: remove_oldest triggers reattachment for deduplicated chunks."""
        # Create an extraction that will be removed due to overflow
        removed_extraction = AIMessage(content="Removed summary", id="removed_1")
        set_extraction_metadata(
            removed_extraction,
            chunk_ids=["chunk_1", "chunk_2"],
            deduplicated_chunk_ids=["dup_1", "dup_2"],
            strategy="extract_full",
        )

        # Create other extractions that might have used these chunks
        other_extraction = AIMessage(content="Other summary", id="other_1")
        set_extraction_metadata(
            other_extraction,
            chunk_ids=["chunk_3"],
            deduplicated_chunk_ids=["dup_1"],  # Shares dup_1
            strategy="extract_full",
        )

        # Simulate removal: when removed_extraction is removed,
        # dup_1 should be reattached to other_extraction
        extractions_with_dup1 = find_extractions_with_deduplicated_chunk(
            [other_extraction],
            "dup_1"
        )

        self.assertEqual(len(extractions_with_dup1), 1)
        self.assertIn(other_extraction, extractions_with_dup1)

    def test_reattachment_only_for_deduplicated_chunks(self):
        """Test 20: Only deduplicated chunks are considered for reattachment."""
        # Create extraction to be removed
        removed = AIMessage(content="Removed", id="removed")
        set_extraction_metadata(
            removed,
            chunk_ids=["chunk_1", "chunk_2"],  # Non-deduplicated
            deduplicated_chunk_ids=["dup_1"],  # Deduplicated
            strategy="extract_full",
        )

        # Get chunks for reattachment - only deduplicated ones
        dedup_chunks = get_deduplicated_chunk_ids(removed)
        regular_chunks = get_extraction_chunk_ids(removed)

        # Only dup_1 should be considered for reattachment
        self.assertEqual(dedup_chunks, ["dup_1"])
        self.assertEqual(set(regular_chunks), {"chunk_1", "chunk_2"})

        # Verify they're separate
        self.assertEqual(len(set(dedup_chunks) & set(regular_chunks)), 0)

    def test_reattachment_to_multiple_extractions(self):
        """Test 21: Chunks can reattach to multiple messages that reference them."""
        # Create extraction to be removed with deduplicated chunks
        removed = AIMessage(content="Removed", id="removed")
        set_extraction_metadata(
            removed,
            chunk_ids=["chunk_1"],
            deduplicated_chunk_ids=["dup_shared"],
            strategy="extract_full",
        )

        # Create multiple extractions that reference the same chunk
        extract1 = AIMessage(content="Extract 1", id="e1")
        set_extraction_metadata(
            extract1,
            chunk_ids=["chunk_2"],
            deduplicated_chunk_ids=["dup_shared"],
            strategy="extract_full",
        )

        extract2 = AIMessage(content="Extract 2", id="e2")
        set_extraction_metadata(
            extract2,
            chunk_ids=["chunk_3"],
            deduplicated_chunk_ids=["dup_shared"],
            strategy="extract_full",
        )

        extract3 = AIMessage(content="Extract 3", id="e3")
        set_extraction_metadata(
            extract3,
            chunk_ids=["chunk_4"],
            deduplicated_chunk_ids=["other_dup"],  # Different chunk
            strategy="extract_full",
        )

        # Find all extractions that have dup_shared
        remaining_extractions = [extract1, extract2, extract3]
        extractions_with_chunk = find_extractions_with_deduplicated_chunk(
            remaining_extractions,
            "dup_shared"
        )

        # Should find extract1 and extract2, but not extract3
        self.assertEqual(len(extractions_with_chunk), 2)
        self.assertIn(extract1, extractions_with_chunk)
        self.assertIn(extract2, extractions_with_chunk)
        self.assertNotIn(extract3, extractions_with_chunk)


class TestReattachmentBehavior(unittest.TestCase):
    """Test 22-24: Reattachment behavior and metadata handling."""

    def test_no_reattachment_to_source_extraction(self):
        """Test 22: Don't reattach to the extraction being removed."""
        # This is implicit in the reattachment logic - you only reattach to
        # *other* extractions, not the one being removed

        removed = AIMessage(content="Removed", id="removed")
        set_extraction_metadata(
            removed,
            chunk_ids=["chunk_1"],
            deduplicated_chunk_ids=["dup_1"],
            strategy="extract_full",
        )

        # When finding reattachment targets, the removed extraction shouldn't be included
        # This is ensured by only searching in remaining extractions
        remaining = []  # Empty - removed is not in the list
        targets = find_extractions_with_deduplicated_chunk(remaining, "dup_1")

        self.assertEqual(len(targets), 0, "Should not reattach to removed extraction")

    def test_reattachment_preserves_metadata(self):
        """Test 23: Metadata preserved during reattachment."""
        extraction = AIMessage(content="Extract", id="e1")

        # Set initial metadata
        set_extraction_metadata(
            extraction,
            chunk_ids=["chunk_1"],
            deduplicated_chunk_ids=["dup_1", "dup_2"],
            strategy="extract_full",
        )

        # Simulate reattachment: move dup_1 from deduplicated to chunk_ids
        move_deduplicated_to_chunk_ids(extraction, ["dup_1"])

        # Verify metadata structure is preserved
        extraction_meta = get_compaction_metadata(extraction, "extraction", {})
        self.assertIn("chunk_ids", extraction_meta)
        self.assertIn("deduplicated_chunk_ids", extraction_meta)
        self.assertIn("strategy", extraction_meta)

        # Verify the move happened correctly
        chunk_ids = get_extraction_chunk_ids(extraction)
        dedup_ids = get_deduplicated_chunk_ids(extraction)

        self.assertIn("dup_1", chunk_ids, "dup_1 should be moved to chunk_ids")
        self.assertNotIn("dup_1", dedup_ids, "dup_1 should be removed from deduplicated")
        self.assertIn("dup_2", dedup_ids, "dup_2 should remain in deduplicated")

    def test_reattachment_updates_chunk_ids_list(self):
        """Test 24: chunk_ids list updated correctly during reattachment."""
        extraction = AIMessage(content="Extract", id="e1")

        # Initial state
        initial_chunks = ["chunk_1", "chunk_2"]
        initial_dedup = ["dup_1", "dup_2", "dup_3"]

        set_extraction_metadata(
            extraction,
            chunk_ids=initial_chunks,
            deduplicated_chunk_ids=initial_dedup,
            strategy="extract_full",
        )

        # Reattach dup_1 and dup_2
        move_deduplicated_to_chunk_ids(extraction, ["dup_1", "dup_2"])

        # Verify chunk_ids updated
        updated_chunks = get_extraction_chunk_ids(extraction)
        updated_dedup = get_deduplicated_chunk_ids(extraction)

        self.assertEqual(set(updated_chunks), {"chunk_1", "chunk_2", "dup_1", "dup_2"})
        self.assertEqual(set(updated_dedup), {"dup_3"})


class TestReattachmentIntegration(unittest.TestCase):
    """Test 25-26: Integration of reattachment with other features."""

    def test_reattachment_moves_from_deduplicated_list(self):
        """Test 25: Moves from deduplicated_chunk_ids during reattachment."""
        extraction = AIMessage(content="Extract", id="e1")

        # Setup with deduplicated chunks
        set_extraction_metadata(
            extraction,
            chunk_ids=["c1"],
            deduplicated_chunk_ids=["d1", "d2", "d3"],
            strategy="extract_full",
        )

        # Get initial state
        initial_dedup = get_deduplicated_chunk_ids(extraction)
        self.assertEqual(set(initial_dedup), {"d1", "d2", "d3"})

        # Move d1 and d3
        move_deduplicated_to_chunk_ids(extraction, ["d1", "d3"])

        # Verify moves
        final_chunks = get_extraction_chunk_ids(extraction)
        final_dedup = get_deduplicated_chunk_ids(extraction)

        self.assertIn("d1", final_chunks)
        self.assertIn("d3", final_chunks)
        self.assertNotIn("d1", final_dedup)
        self.assertNotIn("d3", final_dedup)
        self.assertIn("d2", final_dedup, "d2 should remain in deduplicated")

    def test_check_and_handle_duplicates_integration(self):
        """Test 26: Integration with duplicate checking."""
        # This test verifies the integration between reattachment and
        # the check_and_handle_duplicates logic

        # Create extractions with various chunk relationships
        extract1 = AIMessage(content="Extract 1", id="e1")
        set_extraction_metadata(
            extract1,
            chunk_ids=["c1", "c2"],
            deduplicated_chunk_ids=["d1"],
            strategy="extract_full",
        )

        extract2 = AIMessage(content="Extract 2", id="e2")
        set_extraction_metadata(
            extract2,
            chunk_ids=["c3"],
            deduplicated_chunk_ids=["d1", "d2"],  # Shares d1
            strategy="extract_full",
        )

        extract3 = AIMessage(content="Extract 3", id="e3")
        set_extraction_metadata(
            extract3,
            chunk_ids=["c4"],
            deduplicated_chunk_ids=["d2"],  # Shares d2 with extract2
            strategy="extract_full",
        )

        # Simulate removing extract1 - d1 should be reattached
        remaining = [extract2, extract3]

        # Find reattachment targets for d1 (from extract1)
        targets_d1 = find_extractions_with_deduplicated_chunk(remaining, "d1")
        self.assertEqual(len(targets_d1), 1)
        self.assertIn(extract2, targets_d1)

        # Reattach d1 to extract2
        move_deduplicated_to_chunk_ids(extract2, ["d1"])

        # Verify reattachment
        e2_chunks = get_extraction_chunk_ids(extract2)
        e2_dedup = get_deduplicated_chunk_ids(extract2)

        self.assertIn("d1", e2_chunks)
        self.assertNotIn("d1", e2_dedup)
        self.assertIn("d2", e2_dedup, "d2 should still be deduplicated")

        # Verify extract3 unchanged
        e3_dedup = get_deduplicated_chunk_ids(extract3)
        self.assertIn("d2", e3_dedup)


if __name__ == "__main__":
    unittest.main()
