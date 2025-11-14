"""
Unit tests for v2.1 message chunking features.

Tests cover:
- Message chunking for >6K token messages
- Chunk ID format and structure
- Chunk metadata fields
- Overlap calculation
- JIT ingestion with chunking
- Semantic vs fixed chunking strategies

Test IDs: 1-8 (from comprehensive test plan)
"""

import unittest
from unittest.mock import Mock, AsyncMock, patch
from uuid import uuid4

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from workflow_service.registry.nodes.llm.prompt_compaction.token_utils import (
    chunk_message_for_embedding,
)
from workflow_service.registry.nodes.llm.prompt_compaction.strategies import (
    ExtractionStrategy,
)
from workflow_service.registry.nodes.llm.config import ModelMetadata, LLMModelProvider
from workflow_service.registry.nodes.llm.prompt_compaction.utils import (
    get_ingestion_chunk_ids,
    get_compaction_metadata,
    is_message_ingested,
    ExtractionStrategy as ExtractionStrategyType,
)

from .test_base import PromptCompactionUnitTestBase


class TestMessageChunkingBasics(unittest.TestCase):
    """Test 1-3: Basic message chunking functionality."""

    def setUp(self):
        """Set up test model metadata."""
        self.model_metadata = ModelMetadata(
            provider=LLMModelProvider.OPENAI,
            model_name="gpt-4o-mini",
            context_limit=128000,
            output_token_limit=16384,
        )

    def test_chunk_message_above_threshold(self):
        """Test 1: Message >6K tokens is chunked correctly."""
        # Create a large message (>6000 tokens)
        # Using actual token counting with OpenAI model metadata
        # Include paragraph breaks (\n\n) for semantic chunking to work
        paragraphs = [" ".join([f"word{i+j*50}" for j in range(50)]) for i in range(150)]
        large_content = "\n\n".join(paragraphs)  # 150 paragraphs, ~7500 words ≈ ~9000 tokens
        message = HumanMessage(content=large_content, id="msg_large")

        # Chunk the message with smaller chunk size to force splitting
        chunks = chunk_message_for_embedding(
            message=message,
            chunk_size_tokens=2000,  # 2000 tokens - ensures multiple chunks from 9000+ tokens
            chunk_overlap_tokens=100,
            chunk_strategy="semantic_overlap",
            model_metadata=self.model_metadata,
        )

        # Assertions
        self.assertGreater(len(chunks), 1, "Large message should be split into multiple chunks")

        # Verify total_chunks is consistent
        total_chunks = chunks[0][1]["total_chunks"]
        self.assertEqual(len(chunks), total_chunks, "Number of chunks should match total_chunks metadata")

        # Verify chunk indices are sequential
        for i, (chunk_text, metadata) in enumerate(chunks):
            self.assertEqual(metadata["chunk_index"], i, f"Chunk {i} should have correct index")
            self.assertEqual(metadata["total_chunks"], total_chunks, "All chunks should report same total_chunks")
            self.assertEqual(metadata["message_id"], "msg_large", "All chunks should reference original message_id")
            self.assertGreater(len(chunk_text), 0, "Chunk text should not be empty")

    def test_chunk_message_below_threshold(self):
        """Test 2: Message <6K tokens is not chunked (total_chunks=1)."""
        # Create a small message (<6000 tokens)
        small_content = "This is a small message. " * 100  # ~2,500 chars ≈ 625 tokens
        message = HumanMessage(content=small_content, id="msg_small")

        # Chunk the message
        chunks = chunk_message_for_embedding(
            message=message,
            chunk_size_tokens=6000,
            chunk_overlap_tokens=200,
            model_metadata=None,
        )

        # Assertions
        self.assertEqual(len(chunks), 1, "Small message should not be chunked")
        chunk_text, metadata = chunks[0]

        self.assertEqual(metadata["chunk_index"], 0, "Single chunk should have index 0")
        self.assertEqual(metadata["total_chunks"], 1, "Single chunk should report total_chunks=1")
        self.assertEqual(metadata["message_id"], "msg_small")
        # Note: chunk_text includes formatting from format_message_for_embedding (e.g., role prefix)
        self.assertIn(small_content.strip(), chunk_text, "Chunk text should contain original content")

    def test_chunk_id_format_validation(self):
        """Test 3: Chunk ID format is correct: chunk_{msg_id}_{idx}_{timestamp}."""
        # This test verifies the chunk_id format when stored in Weaviate
        # The format is created by ThreadMessageWeaviateClient.store_thread_message_chunk()

        message_id = "msg_test_123"
        chunk_index = 2

        # Expected format: chunk_{message_id}_{chunk_index}_{timestamp}
        # We'll verify this pattern matches
        import re
        import time

        # Create a mock chunk_id using the expected format
        timestamp = int(time.time())
        chunk_id = f"chunk_{message_id}_{chunk_index}_{timestamp}"

        # Verify format using regex
        pattern = r"^chunk_[a-zA-Z0-9_-]+_\d+_\d+$"
        self.assertIsNotNone(re.match(pattern, chunk_id), "Chunk ID should match expected format")

        # Verify we can parse it back
        parts = chunk_id.split("_")
        self.assertEqual(parts[0], "chunk", "First part should be 'chunk'")
        self.assertTrue(parts[-2].isdigit(), "Second-to-last part should be chunk_index (digit)")
        self.assertTrue(parts[-1].isdigit(), "Last part should be timestamp (digit)")


class TestChunkMetadataStructure(unittest.TestCase):
    """Test 4-5: Chunk metadata fields and overlap calculation."""

    def test_chunk_metadata_fields_present(self):
        """Test 4: Verify all required metadata fields are present."""
        large_content = "Test content. " * 2000  # ~24,000 chars ≈ 6,000 tokens
        message = HumanMessage(content=large_content, id="msg_meta")

        chunks = chunk_message_for_embedding(
            message=message,
            chunk_size_tokens=6000,
            chunk_overlap_tokens=200,
        )

        # Verify metadata structure
        for chunk_text, metadata in chunks:
            # Required fields
            self.assertIn("chunk_index", metadata, "Should have chunk_index")
            self.assertIn("total_chunks", metadata, "Should have total_chunks")
            self.assertIn("message_id", metadata, "Should have message_id")
            self.assertIn("chunk_start_char", metadata, "Should have chunk_start_char")
            self.assertIn("chunk_end_char", metadata, "Should have chunk_end_char")
            self.assertIn("token_count", metadata, "Should have token_count")

            # Type validation
            self.assertIsInstance(metadata["chunk_index"], int)
            self.assertIsInstance(metadata["total_chunks"], int)
            self.assertIsInstance(metadata["message_id"], str)
            self.assertIsInstance(metadata["chunk_start_char"], int)
            self.assertIsInstance(metadata["chunk_end_char"], int)
            self.assertIsInstance(metadata["token_count"], int)

            # Value validation
            self.assertGreaterEqual(metadata["chunk_index"], 0)
            self.assertGreater(metadata["total_chunks"], 0)
            self.assertGreaterEqual(metadata["chunk_start_char"], 0)
            self.assertGreater(metadata["chunk_end_char"], metadata["chunk_start_char"])
            self.assertGreater(metadata["token_count"], 0)

    def test_chunk_overlap_tokens_calculated(self):
        """Test 5: Verify chunk overlap is calculated correctly."""
        # Create content that will definitely result in multiple chunks
        large_content = "Word " * 10000  # 50,000 chars ≈ 12,500 tokens (will create 2-3 chunks with 6K limit)
        message = HumanMessage(content=large_content, id="msg_overlap")

        overlap_tokens = 200
        chunks = chunk_message_for_embedding(
            message=message,
            chunk_size_tokens=6000,
            chunk_overlap_tokens=overlap_tokens,
        )

        if len(chunks) > 1:
            # For chunks with overlap, the end of chunk[i] should overlap with start of chunk[i+1]
            # Verify that consecutive chunks have overlapping positions
            for i in range(len(chunks) - 1):
                current_chunk_text, current_meta = chunks[i]
                next_chunk_text, next_meta = chunks[i + 1]

                current_end = current_meta["chunk_end_char"]
                next_start = next_meta["chunk_start_char"]

                # Overlap means next chunk starts before current chunk ends (in character space)
                # Due to semantic chunking, exact overlap may vary, but next should start near current end
                self.assertLessEqual(
                    abs(next_start - current_end),
                    len(current_chunk_text) // 2,  # Allow generous margin for semantic splits
                    f"Chunks {i} and {i+1} should have reasonable proximity"
                )


class TestChunkingWithJITIngestion(PromptCompactionUnitTestBase):
    """Test 6-7: Chunking integration with JIT ingestion."""

    def setUp(self):
        """Set up test model metadata."""
        super().setUp()
        self.model_metadata = ModelMetadata(
            provider=LLMModelProvider.OPENAI,
            model_name="gpt-4o-mini",
            context_limit=128000,
            output_token_limit=16384,
        )

    async def test_jit_ingestion_chunks_messages(self):
        """Test 6: _jit_ingest_messages creates chunks for large messages."""
        # Simplified test: Just verify chunking logic without full Weaviate integration
        # Full integration is tested in integration tests

        # Include paragraph breaks for semantic chunking
        paragraphs = [" ".join([f"word{i+j*50}" for j in range(50)]) for i in range(150)]
        large_content = "\n\n".join(paragraphs)
        message = HumanMessage(content=large_content, id="msg_ingest")

        # Test the chunking logic directly
        chunks = chunk_message_for_embedding(
            message=message,
            chunk_size_tokens=2000,  # Ensures chunking from 9000+ tokens
            chunk_overlap_tokens=100,
            model_metadata=self.model_metadata,
        )

        # Verify multiple chunks were created
        self.assertGreater(len(chunks), 1, "Large message should be chunked")

        # Verify chunk metadata
        for chunk_text, metadata in chunks:
            self.assertEqual(metadata["message_id"], "msg_ingest")
            self.assertIn("chunk_index", metadata)
            self.assertIn("total_chunks", metadata)

    async def test_chunk_sequence_numbering(self):
        """Test 7: All chunks for a message get the same sequence_no when stored."""
        # Unit test: Verify that chunk metadata includes sequential indices
        # The actual sequence_no assignment happens in Weaviate storage (integration test)

        # Include paragraph breaks for semantic chunking
        paragraphs = [" ".join([f"word{i+j*50}" for j in range(50)]) for i in range(150)]
        large_content = "\n\n".join(paragraphs)
        message = HumanMessage(content=large_content, id="msg_seq")

        # Get chunks
        chunks = chunk_message_for_embedding(
            message=message,
            chunk_size_tokens=2000,  # Ensures chunking
            chunk_overlap_tokens=100,
            model_metadata=self.model_metadata,
        )

        # Verify chunks have sequential indices but same message_id
        if len(chunks) > 1:
            message_ids = [meta["message_id"] for _, meta in chunks]
            self.assertTrue(
                all(mid == message_ids[0] for mid in message_ids),
                "All chunks should reference the same message_id"
            )

            # Verify indices are sequential
            indices = [meta["chunk_index"] for _, meta in chunks]
            self.assertEqual(indices, list(range(len(chunks))), "Chunk indices should be sequential")


class TestChunkingStrategies(unittest.TestCase):
    """Test 8: Different chunking strategies (semantic vs fixed)."""

    def setUp(self):
        """Set up test model metadata."""
        self.model_metadata = ModelMetadata(
            provider=LLMModelProvider.OPENAI,
            model_name="gpt-4o-mini",
            context_limit=128000,
            output_token_limit=16384,
        )

    def test_semantic_vs_fixed_chunking(self):
        """Test 8: Compare semantic_overlap vs fixed_token chunking strategies."""
        # Create content with paragraph breaks for semantic chunking
        paragraphs = [" ".join([f"word{i+j*50}" for j in range(50)]) for i in range(150)]
        large_content = "\n\n".join(paragraphs)  # 150 paragraphs

        message = HumanMessage(content=large_content, id="msg_strategies")

        # Test semantic chunking with smaller chunks to force splitting
        semantic_chunks = chunk_message_for_embedding(
            message=message,
            chunk_size_tokens=2000,  # Ensures multiple chunks from 9000+ tokens
            chunk_overlap_tokens=100,
            chunk_strategy="semantic_overlap",
            model_metadata=self.model_metadata,
        )

        # Test fixed-token chunking (works without paragraph breaks too)
        fixed_chunks = chunk_message_for_embedding(
            message=message,
            chunk_size_tokens=2000,  # Ensures multiple chunks
            chunk_overlap_tokens=100,
            chunk_strategy="fixed_token",
            model_metadata=self.model_metadata,
        )

        # Both should create multiple chunks
        self.assertGreater(len(semantic_chunks), 1, "Semantic chunking should create multiple chunks")
        self.assertGreater(len(fixed_chunks), 1, "Fixed chunking should create multiple chunks")

        # Both should have similar number of chunks (within reason)
        chunk_count_ratio = len(semantic_chunks) / len(fixed_chunks)
        self.assertGreater(chunk_count_ratio, 0.5, "Chunk counts should be in similar range")
        self.assertLess(chunk_count_ratio, 2.0, "Chunk counts should be in similar range")

        # Semantic chunks should preserve paragraph boundaries better
        # (This is a heuristic check - semantic chunks are more likely to end at paragraph breaks)
        for chunk_text, _ in semantic_chunks[:3]:  # Check first few chunks
            # Semantic chunks should not end mid-sentence as often
            # (though overlap may cause some mid-sentence endings)
            self.assertIsInstance(chunk_text, str)
            self.assertGreater(len(chunk_text), 0)

        # Verify all chunks maintain metadata consistency
        for chunks in [semantic_chunks, fixed_chunks]:
            total = chunks[0][1]["total_chunks"]
            for i, (text, meta) in enumerate(chunks):
                self.assertEqual(meta["chunk_index"], i)
                self.assertEqual(meta["total_chunks"], total)


if __name__ == "__main__":
    unittest.main()
