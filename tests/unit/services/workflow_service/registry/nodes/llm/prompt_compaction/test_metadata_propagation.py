"""
Unit tests for v2.1 metadata propagation features.

Tests the metadata change tracking utilities and messages_with_updated_metadata
functionality across all compaction strategies.
"""

import pytest
from datetime import datetime, timezone
from typing import List
from unittest.mock import AsyncMock, MagicMock, patch

from langchain_core.messages import (
    BaseMessage,
    SystemMessage,
    HumanMessage,
    AIMessage,
    ToolMessage,
)

from workflow_service.registry.nodes.llm.prompt_compaction.strategies import (
    _snapshot_message_metadata,
    _has_metadata_changed,
    _identify_messages_with_updated_metadata,
    NoOpStrategy,
    SummarizationStrategy,
    ExtractionStrategy,
    HybridStrategy,
    CompactionResult,
)
from workflow_service.registry.nodes.llm.prompt_compaction.compactor import (
    PromptCompactionConfig,
    SummarizationConfig,
    ExtractionConfig as ExtractionCompactionConfig,
    HybridConfig,
)
from workflow_service.registry.nodes.llm.prompt_compaction.utils import (
    set_compaction_metadata,
    get_compaction_metadata,
)

from .test_base import PromptCompactionUnitTestBase


# ============================================================================
# Test Utilities: Metadata Snapshot and Change Detection
# ============================================================================


class TestMetadataSnapshot:
    """Test _snapshot_message_metadata utility."""

    def test_snapshot_empty_metadata(self):
        """Test snapshotting a message with no compaction metadata."""
        msg = HumanMessage(content="Hello", id="msg1")

        snapshot = _snapshot_message_metadata(msg)

        assert snapshot == {
            "section_label": None,
            "graph_edges": [],
            "ingestion": {},
            "extraction": {},
        }

    def test_snapshot_section_label_only(self):
        """Test snapshotting a message with only section_label."""
        msg = HumanMessage(content="Hello", id="msg1")
        set_compaction_metadata(msg, "section_label", "RECENT")

        snapshot = _snapshot_message_metadata(msg)

        assert snapshot == {
            "section_label": "RECENT",
            "graph_edges": [],
            "ingestion": {},
            "extraction": {},
        }

    def test_snapshot_all_metadata_types(self):
        """Test snapshotting a message with all metadata types."""
        msg = HumanMessage(content="Hello", id="msg1")
        set_compaction_metadata(msg, "section_label", "HISTORICAL")
        set_compaction_metadata(msg, "graph_edges", ["SUMMARY", "PASSTHROUGH"])
        set_compaction_metadata(msg, "ingestion", {
            "ingested": True,
            "chunk_ids": ["chunk1", "chunk2"]
        })
        set_compaction_metadata(msg, "extraction", {
            "chunk_ids": ["chunk3"],
            "strategy": "extraction",
            "relevance_scores": [0.95]
        })

        snapshot = _snapshot_message_metadata(msg)

        assert snapshot == {
            "section_label": "HISTORICAL",
            "graph_edges": ["SUMMARY", "PASSTHROUGH"],
            "ingestion": {
                "ingested": True,
                "chunk_ids": ["chunk1", "chunk2"]
            },
            "extraction": {
                "chunk_ids": ["chunk3"],
                "strategy": "extraction",
                "relevance_scores": [0.95]
            },
        }

    def test_snapshot_preserves_message_immutability(self):
        """Test that snapshotting doesn't modify the original message."""
        msg = HumanMessage(content="Hello", id="msg1")
        set_compaction_metadata(msg, "section_label", "RECENT")

        original_metadata = msg.additional_kwargs.get("compaction_metadata", {}).copy()
        snapshot = _snapshot_message_metadata(msg)

        # Verify original metadata unchanged
        assert msg.additional_kwargs.get("compaction_metadata", {}) == original_metadata
        # Verify snapshot is independent
        assert snapshot["section_label"] == "RECENT"


class TestMetadataChangeDetection:
    """Test _has_metadata_changed utility."""

    def test_no_change_empty_metadata(self):
        """Test detection when message has no metadata and snapshot is empty."""
        msg = HumanMessage(content="Hello", id="msg1")
        snapshot = {
            "section_label": None,
            "graph_edges": [],
            "ingestion": {},
            "extraction": {},
        }

        assert not _has_metadata_changed(msg, snapshot)

    def test_section_label_added(self):
        """Test detection when section_label is added."""
        msg = HumanMessage(content="Hello", id="msg1")
        set_compaction_metadata(msg, "section_label", "RECENT")

        snapshot = {
            "section_label": None,
            "graph_edges": [],
            "ingestion": {},
            "extraction": {},
        }

        assert _has_metadata_changed(msg, snapshot)

    def test_section_label_changed(self):
        """Test detection when section_label changes."""
        msg = HumanMessage(content="Hello", id="msg1")
        set_compaction_metadata(msg, "section_label", "HISTORICAL")

        snapshot = {
            "section_label": "RECENT",
            "graph_edges": [],
            "ingestion": {},
            "extraction": {},
        }

        assert _has_metadata_changed(msg, snapshot)

    def test_graph_edges_added(self):
        """Test detection when graph_edges are added."""
        msg = HumanMessage(content="Hello", id="msg1")
        set_compaction_metadata(msg, "graph_edges", ["SUMMARY"])

        snapshot = {
            "section_label": None,
            "graph_edges": [],
            "ingestion": {},
            "extraction": {},
        }

        assert _has_metadata_changed(msg, snapshot)

    def test_graph_edges_modified(self):
        """Test detection when graph_edges list changes."""
        msg = HumanMessage(content="Hello", id="msg1")
        set_compaction_metadata(msg, "graph_edges", ["SUMMARY", "EXTRACTION"])

        snapshot = {
            "section_label": None,
            "graph_edges": ["SUMMARY"],
            "ingestion": {},
            "extraction": {},
        }

        assert _has_metadata_changed(msg, snapshot)

    def test_ingestion_metadata_added(self):
        """Test detection when ingestion metadata is added."""
        msg = HumanMessage(content="Hello", id="msg1")
        set_compaction_metadata(msg, "ingestion", {
            "ingested": True,
            "chunk_ids": ["chunk1"]
        })

        snapshot = {
            "section_label": None,
            "graph_edges": [],
            "ingestion": {},
            "extraction": {},
        }

        assert _has_metadata_changed(msg, snapshot)

    def test_ingestion_metadata_modified(self):
        """Test detection when ingestion metadata changes."""
        msg = HumanMessage(content="Hello", id="msg1")
        set_compaction_metadata(msg, "ingestion", {
            "ingested": True,
            "chunk_ids": ["chunk1", "chunk2"]
        })

        snapshot = {
            "section_label": None,
            "graph_edges": [],
            "ingestion": {
                "ingested": False,
                "chunk_ids": []
            },
            "extraction": {},
        }

        assert _has_metadata_changed(msg, snapshot)

    def test_extraction_metadata_added(self):
        """Test detection when extraction metadata is added."""
        msg = HumanMessage(content="Hello", id="msg1")
        set_compaction_metadata(msg, "extraction", {
            "chunk_ids": ["chunk1"],
            "strategy": "extraction"
        })

        snapshot = {
            "section_label": None,
            "graph_edges": [],
            "ingestion": {},
            "extraction": {},
        }

        assert _has_metadata_changed(msg, snapshot)

    def test_multiple_metadata_types_changed(self):
        """Test detection when multiple metadata types change."""
        msg = HumanMessage(content="Hello", id="msg1")
        set_compaction_metadata(msg, "section_label", "HISTORICAL")
        set_compaction_metadata(msg, "graph_edges", ["SUMMARY"])
        set_compaction_metadata(msg, "ingestion", {"ingested": True})

        snapshot = {
            "section_label": "RECENT",
            "graph_edges": [],
            "ingestion": {},
            "extraction": {},
        }

        assert _has_metadata_changed(msg, snapshot)

    def test_no_change_when_metadata_identical(self):
        """Test no detection when all metadata is identical."""
        msg = HumanMessage(content="Hello", id="msg1")
        set_compaction_metadata(msg, "section_label", "RECENT")
        set_compaction_metadata(msg, "graph_edges", ["PASSTHROUGH"])
        set_compaction_metadata(msg, "ingestion", {"ingested": True})
        set_compaction_metadata(msg, "extraction", {"chunk_ids": ["c1"]})

        snapshot = {
            "section_label": "RECENT",
            "graph_edges": ["PASSTHROUGH"],
            "ingestion": {"ingested": True},
            "extraction": {"chunk_ids": ["c1"]},
        }

        assert not _has_metadata_changed(msg, snapshot)


class TestIdentifyMessagesWithUpdatedMetadata:
    """Test _identify_messages_with_updated_metadata utility."""

    def test_empty_messages_list(self):
        """Test with no messages."""
        result = _identify_messages_with_updated_metadata([], {}, [])
        assert result == []

    def test_all_new_messages(self):
        """Test when all messages are new (not in snapshot)."""
        msg1 = HumanMessage(content="Hello", id="msg1")
        msg2 = AIMessage(content="Hi", id="msg2")

        result = _identify_messages_with_updated_metadata([msg1, msg2], {}, [msg1, msg2])

        assert len(result) == 2
        assert result[0].id == "msg1"
        assert result[1].id == "msg2"

    def test_no_messages_changed(self):
        """Test when no messages have metadata changes."""
        msg1 = HumanMessage(content="Hello", id="msg1")
        msg2 = AIMessage(content="Hi", id="msg2")

        snapshots = {
            "msg1": {
                "section_label": None,
                "graph_edges": [],
                "ingestion": {},
                "extraction": {},
            },
            "msg2": {
                "section_label": None,
                "graph_edges": [],
                "ingestion": {},
                "extraction": {},
            },
        }

        result = _identify_messages_with_updated_metadata([msg1, msg2], snapshots, [])

        assert result == []

    def test_some_messages_changed(self):
        """Test when some messages have metadata changes."""
        msg1 = HumanMessage(content="Old", id="msg1")
        msg2 = HumanMessage(content="New", id="msg2")
        msg3 = AIMessage(content="Unchanged", id="msg3")

        # msg1: section label changed
        set_compaction_metadata(msg1, "section_label", "HISTORICAL")

        # msg2: new message
        set_compaction_metadata(msg2, "section_label", "RECENT")

        # msg3: no change

        snapshots = {
            "msg1": {
                "section_label": "RECENT",  # Changed to HISTORICAL
                "graph_edges": [],
                "ingestion": {},
                "extraction": {},
            },
            "msg3": {
                "section_label": None,  # Still None
                "graph_edges": [],
                "ingestion": {},
                "extraction": {},
            },
        }

        result = _identify_messages_with_updated_metadata([msg1, msg2, msg3], snapshots, [msg2])

        assert len(result) == 2
        assert result[0].id == "msg1"  # Changed
        assert result[1].id == "msg2"  # New

    def test_maintains_message_order(self):
        """Test that result maintains original message order."""
        messages = []
        snapshots = {}

        # Create 10 messages, mark odd-numbered ones as changed
        for i in range(10):
            msg = HumanMessage(content=f"Message {i}", id=f"msg{i}")
            messages.append(msg)

            if i % 2 == 1:  # Odd-numbered: changed
                set_compaction_metadata(msg, "section_label", "RECENT")
                snapshots[f"msg{i}"] = {
                    "section_label": None,  # Changed
                    "graph_edges": [],
                    "ingestion": {},
                    "extraction": {},
                }
            else:  # Even-numbered: unchanged
                snapshots[f"msg{i}"] = {
                    "section_label": None,  # Still None
                    "graph_edges": [],
                    "ingestion": {},
                    "extraction": {},
                }

        result = _identify_messages_with_updated_metadata(messages, snapshots, [])

        # Should have messages 1, 3, 5, 7, 9 in that order
        assert len(result) == 5
        assert [msg.id for msg in result] == ["msg1", "msg3", "msg5", "msg7", "msg9"]

    def test_mixed_new_and_changed_messages(self):
        """Test with mix of new messages and changed existing messages."""
        # Existing messages
        msg1 = HumanMessage(content="Old1", id="msg1")
        msg2 = HumanMessage(content="Old2", id="msg2")
        set_compaction_metadata(msg1, "section_label", "HISTORICAL")  # Changed

        # New messages
        msg3 = HumanMessage(content="New1", id="msg3")
        msg4 = AIMessage(content="New2", id="msg4")
        set_compaction_metadata(msg3, "section_label", "RECENT")

        snapshots = {
            "msg1": {
                "section_label": "RECENT",  # Changed to HISTORICAL
                "graph_edges": [],
                "ingestion": {},
                "extraction": {},
            },
            "msg2": {
                "section_label": None,  # Still None
                "graph_edges": [],
                "ingestion": {},
                "extraction": {},
            },
        }

        result = _identify_messages_with_updated_metadata(
            [msg1, msg2, msg3, msg4], snapshots, [msg3, msg4]
        )

        assert len(result) == 3
        assert result[0].id == "msg1"  # Changed
        assert result[1].id == "msg3"  # New
        assert result[2].id == "msg4"  # New


# ============================================================================
# Test Strategy Integration: messages_with_updated_metadata
# ============================================================================


class TestNoOpStrategyMetadataPropagation(PromptCompactionUnitTestBase):
    """Test NoOpStrategy returns messages_with_updated_metadata."""

    async def test_noop_new_messages_all_updated(self):
        """Test NoOp strategy marks all new messages as updated."""
        strategy = NoOpStrategy()

        sections = {
            "system": [],
            "summaries": [],
            "historical": [],
            "old_tools": [],
            "marked": [],
            "latest_tools": [],
            "recent": self._generate_test_messages(2),
        }

        result = await strategy.compact(
            sections=sections,
            budget=self._create_test_budget(),
            model_metadata=self._create_test_model_metadata(),
            ext_context=self.ext_context,
        )

        # All messages should be in messages_with_updated_metadata (new messages)
        assert len(result.messages_with_updated_metadata) == 2

    async def test_noop_all_messages_get_metadata(self):
        """Test NoOp strategy adds metadata to all messages."""
        strategy = NoOpStrategy()

        sections = {
            "system": [],
            "summaries": [],
            "historical": [],
            "old_tools": [],
            "marked": [],
            "latest_tools": [],
            "recent": self._generate_test_messages(2),
        }

        result = await strategy.compact(
            sections=sections,
            budget=self._create_test_budget(),
            model_metadata=self._create_test_model_metadata(),
            ext_context=self.ext_context,
        )

        # All messages should have metadata added (section labels, graph edges)
        for msg in result.compacted_messages:
            assert get_compaction_metadata(msg, "section_label") is not None

        # All should be in messages_with_updated_metadata
        assert len(result.messages_with_updated_metadata) == 2


class TestSummarizationStrategyMetadataPropagation(PromptCompactionUnitTestBase):
    """Test SummarizationStrategy returns messages_with_updated_metadata."""

    async def test_summarization_messages_get_metadata(self):
        """Test summarization strategy adds metadata to messages."""
        strategy = SummarizationStrategy()

        sections = {
            "system": [],
            "summaries": [],
            "historical": [],
            "old_tools": [],
            "marked": [],
            "latest_tools": [],
            "recent": self._generate_test_messages(2),
        }

        result = await strategy.compact(
            sections=sections,
            budget=self._create_test_budget(),
            model_metadata=self._create_test_model_metadata(),
            ext_context=self.ext_context,
        )

        # All messages should have metadata
        for msg in result.compacted_messages:
            assert get_compaction_metadata(msg, "section_label") is not None

        # All should be in messages_with_updated_metadata
        assert len(result.messages_with_updated_metadata) == 2


class TestExtractionStrategyMetadataPropagation(PromptCompactionUnitTestBase):
    """Test ExtractionStrategy returns messages_with_updated_metadata."""

    async def test_extraction_messages_get_metadata(self):
        """Test extraction strategy adds metadata to messages."""
        from workflow_service.registry.nodes.llm.prompt_compaction.utils import ExtractionStrategy as ExtractionStrategyType

        strategy = ExtractionStrategy(
            construction_strategy=ExtractionStrategyType.EXTRACT_FULL,
            store_embeddings=False,
        )

        sections = {
            "system": [],
            "summaries": [],
            "historical": [],
            "old_tools": [],
            "marked": [],
            "latest_tools": [],
            "recent": self._generate_test_messages(2),
        }

        result = await strategy.compact(
            sections=sections,
            budget=self._create_test_budget(),
            model_metadata=self._create_test_model_metadata(),
            ext_context=self.ext_context,
        )

        # All messages should have metadata
        for msg in result.compacted_messages:
            assert get_compaction_metadata(msg, "section_label") is not None

        # All should be in messages_with_updated_metadata
        assert len(result.messages_with_updated_metadata) == 2


class TestHybridStrategyMetadataPropagation(PromptCompactionUnitTestBase):
    """Test HybridStrategy returns messages_with_updated_metadata."""

    async def test_hybrid_messages_get_metadata(self):
        """Test hybrid strategy adds metadata to messages."""
        strategy = HybridStrategy()

        sections = {
            "system": [],
            "summaries": [],
            "historical": [],
            "old_tools": [],
            "marked": [],
            "latest_tools": [],
            "recent": self._generate_test_messages(2),
        }

        result = await strategy.compact(
            sections=sections,
            budget=self._create_test_budget(),
            model_metadata=self._create_test_model_metadata(),
            ext_context=self.ext_context,
        )

        # All messages should have metadata
        for msg in result.compacted_messages:
            assert get_compaction_metadata(msg, "section_label") is not None

        # All should be in messages_with_updated_metadata
        assert len(result.messages_with_updated_metadata) == 2


# ============================================================================
# Test Edge Cases
# ============================================================================


class TestMetadataPropagationEdgeCases(PromptCompactionUnitTestBase):
    """Test edge cases for metadata propagation."""

    def test_message_without_id(self):
        """Test handling of messages without IDs."""
        msg = HumanMessage(content="No ID")  # No id set

        # Should still work (use None as key)
        snapshot = _snapshot_message_metadata(msg)
        assert snapshot is not None

    def test_deeply_nested_metadata_changes(self):
        """Test detection of changes in deeply nested metadata structures."""
        msg = HumanMessage(content="Test", id="msg1")
        set_compaction_metadata(msg, "extraction", {
            "chunk_ids": ["c1", "c2"],
            "strategy": "extraction",
            "relevance_scores": [0.9, 0.8],
            "deduplicated_chunk_ids": ["c1"]
        })

        snapshot = {
            "section_label": None,
            "graph_edges": [],
            "ingestion": {},
            "extraction": {
                "chunk_ids": ["c1"],  # Different
                "strategy": "extraction",
                "relevance_scores": [0.9, 0.8],
                "deduplicated_chunk_ids": ["c1"]
            },
        }

        assert _has_metadata_changed(msg, snapshot)

    def test_empty_vs_none_metadata_distinction(self):
        """Test that empty dict/list is treated differently from None."""
        msg = HumanMessage(content="Test", id="msg1")
        set_compaction_metadata(msg, "ingestion", {})  # Empty dict

        snapshot = {
            "section_label": None,
            "graph_edges": [],
            "ingestion": {},  # Also empty
            "extraction": {},
        }

        # Should NOT be considered changed
        assert not _has_metadata_changed(msg, snapshot)

    async def test_compaction_with_duplicate_message_ids(self):
        """Test handling when multiple messages share the same ID (edge case)."""
        strategy = NoOpStrategy()

        # Create sections with messages with duplicate IDs (not realistic but edge case)
        msg1 = self._generate_test_message("First message", "human", "msg1")
        msg2 = self._generate_test_message("Second message", "human", "msg1")  # Same ID

        sections = {
            "system": [],
            "summaries": [],
            "historical": [],
            "old_tools": [],
            "marked": [],
            "latest_tools": [],
            "recent": [msg1, msg2],
        }

        result = await strategy.compact(
            sections=sections,
            budget=self._create_test_budget(),
            model_metadata=self._create_test_model_metadata(),
            ext_context=self.ext_context,
        )

        # Should handle gracefully (last message with that ID wins in snapshot)
        assert len(result.messages_with_updated_metadata) >= 1
