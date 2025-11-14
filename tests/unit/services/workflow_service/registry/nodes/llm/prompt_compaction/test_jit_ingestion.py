"""
Unit tests for v2.1 JIT (Just-In-Time) ingestion functionality.

Tests cover:
- Message filtering (ingested vs non-ingested)
- Ingestion metadata tracking
- Runtime config validation (thread_id, node_id)
- Embedding generation flow
- Weaviate storage flow
- Error handling (non-critical failures)
- Duplicate ingestion prevention

Test IDs: 1-9 (from comprehensive test plan)
"""

import unittest
from typing import List
from unittest.mock import AsyncMock, Mock, patch

from langchain_core.messages import BaseMessage, HumanMessage

from workflow_service.registry.nodes.llm.prompt_compaction.compactor import (
    CompactionStrategyType,
    ExtractionConfig,
)
from workflow_service.registry.nodes.llm.prompt_compaction.strategies import ExtractionStrategy
from workflow_service.registry.nodes.llm.prompt_compaction.utils import (
    is_message_ingested,
    set_ingestion_metadata,
    ExtractionStrategy as ExtractionStrategyType,
)

from .test_base import (
    PromptCompactionUnitTestBase,
    create_mock_embeddings_response,
    create_mock_weaviate_client,
)


class TestJITIngestionMessageFiltering(PromptCompactionUnitTestBase):
    """Test 1: JIT ingestion filters non-ingested messages correctly."""

    async def test_filters_non_ingested_messages(self):
        """Should only process messages that are not already ingested."""
        # Create messages - some ingested, some not
        msg1 = self._generate_test_message("Message 1")
        msg2 = self._generate_test_message("Message 2")
        msg3 = self._generate_test_message("Message 3")

        # Mark msg2 as already ingested
        set_ingestion_metadata(msg2, chunk_ids=["chunk_msg2"])

        messages = [msg1, msg2, msg3]

        # Create strategy with mocked dependencies
        config = ExtractionConfig(
            construction_strategy=ExtractionStrategyType.EXTRACT_FULL,
            store_embeddings=True,
        )
        strategy = ExtractionStrategy(
            construction_strategy=config.construction_strategy,
            store_embeddings=config.store_embeddings,
        )

        with patch(
            "workflow_service.registry.nodes.llm.prompt_compaction.llm_utils.get_embeddings_batch"
        ) as mock_embeddings, patch(
            "weaviate_client.ThreadMessageWeaviateClient"
        ) as mock_weaviate_class:

            # Setup mocks
            mock_embeddings.return_value = create_mock_embeddings_response(2)  # Only 2 messages
            mock_weaviate = create_mock_weaviate_client()
            mock_weaviate_class.return_value = mock_weaviate

            # Call JIT ingestion
            result_messages = await strategy._jit_ingest_messages(
                messages=messages,
                ext_context=self.ext_context,
                thread_id=self.test_thread_id,
                node_id=self.test_node_id,
            )

            # Verify only non-ingested messages were processed
            mock_embeddings.assert_called_once()
            call_args = mock_embeddings.call_args
            texts_embedded = call_args[1]["texts"]

            # Should only embed 2 messages (msg1 and msg3, skipping msg2)
            self.assertEqual(len(texts_embedded), 2)

            # Verify msg2 still has original metadata (unchanged)
            self.assertTrue(is_message_ingested(msg2))

            # Verify msg1 and msg3 were marked as ingested
            self.assertTrue(is_message_ingested(msg1))
            self.assertTrue(is_message_ingested(msg3))


class TestJITIngestionMetadata(PromptCompactionUnitTestBase):
    """Test 2: JIT ingestion sets correct metadata on messages."""

    async def test_sets_ingestion_metadata(self):
        """Should set ingestion metadata with chunk IDs and timestamp."""
        messages = self._generate_test_messages(count=3)

        config = ExtractionConfig(
            construction_strategy=ExtractionStrategyType.EXTRACT_FULL,
            store_embeddings=True,
        )
        strategy = ExtractionStrategy(
            construction_strategy=config.construction_strategy,
            store_embeddings=config.store_embeddings,
        )

        with patch(
            "workflow_service.registry.nodes.llm.prompt_compaction.llm_utils.get_embeddings_batch"
        ) as mock_embeddings, patch(
            "weaviate_client.ThreadMessageWeaviateClient"
        ) as mock_weaviate_class:

            mock_embeddings.return_value = create_mock_embeddings_response(3)
            mock_weaviate = create_mock_weaviate_client()
            mock_weaviate_class.return_value = mock_weaviate

            result_messages = await strategy._jit_ingest_messages(
                messages=messages,
                ext_context=self.ext_context,
                thread_id=self.test_thread_id,
                node_id=self.test_node_id,
            )

            # Verify all messages have ingestion metadata
            for msg in result_messages:
                self.assertMessageIngested(msg)

                # Verify metadata structure
                compaction_meta = msg.response_metadata["compaction"]
                ingestion_meta = compaction_meta["ingestion"]

                self.assertIn("ingested_at", ingestion_meta)
                self.assertIn("chunk_ids", ingestion_meta)
                self.assertIsInstance(ingestion_meta["chunk_ids"], list)
                self.assertGreater(len(ingestion_meta["chunk_ids"]), 0)


class TestJITIngestionRuntimeConfig(PromptCompactionUnitTestBase):
    """Test 3: JIT ingestion handles missing thread_id/node_id gracefully."""

    async def test_missing_thread_id(self):
        """Should log warning and mark as ingested without storage when thread_id missing."""
        messages = self._generate_test_messages(count=2)

        config = ExtractionConfig(
            construction_strategy=ExtractionStrategyType.EXTRACT_FULL,
            store_embeddings=True,
        )
        strategy = ExtractionStrategy(
            construction_strategy=config.construction_strategy,
            store_embeddings=config.store_embeddings,
        )

        with patch(
            "workflow_service.registry.nodes.llm.prompt_compaction.llm_utils.get_embeddings_batch"
        ) as mock_embeddings, patch(
            "weaviate_client.ThreadMessageWeaviateClient"
        ) as mock_weaviate_class:

            mock_embeddings.return_value = create_mock_embeddings_response(2)
            mock_weaviate = create_mock_weaviate_client()
            mock_weaviate_class.return_value = mock_weaviate

            # Call without thread_id
            result_messages = await strategy._jit_ingest_messages(
                messages=messages,
                ext_context=self.ext_context,
                thread_id=None,  # Missing thread_id
                node_id=self.test_node_id,
            )

            # Should not call embeddings or Weaviate
            mock_embeddings.assert_not_called()
            mock_weaviate_class.assert_not_called()

            # Messages should still be marked as ingested (fallback behavior)
            for msg in result_messages:
                self.assertMessageIngested(msg)

    async def test_missing_node_id(self):
        """Should log warning and mark as ingested without storage when node_id missing."""
        messages = self._generate_test_messages(count=2)

        config = ExtractionConfig(
            construction_strategy=ExtractionStrategyType.EXTRACT_FULL,
            store_embeddings=True,
        )
        strategy = ExtractionStrategy(
            construction_strategy=config.construction_strategy,
            store_embeddings=config.store_embeddings,
        )

        with patch(
            "workflow_service.registry.nodes.llm.prompt_compaction.llm_utils.get_embeddings_batch"
        ) as mock_embeddings, patch(
            "weaviate_client.ThreadMessageWeaviateClient"
        ) as mock_weaviate_class:

            mock_embeddings.return_value = create_mock_embeddings_response(2)
            mock_weaviate = create_mock_weaviate_client()
            mock_weaviate_class.return_value = mock_weaviate

            # Call without node_id
            result_messages = await strategy._jit_ingest_messages(
                messages=messages,
                ext_context=self.ext_context,
                thread_id=self.test_thread_id,
                node_id=None,  # Missing node_id
            )

            # Should not call embeddings or Weaviate
            mock_embeddings.assert_not_called()
            mock_weaviate_class.assert_not_called()

            # Messages should still be marked as ingested (fallback behavior)
            for msg in result_messages:
                self.assertMessageIngested(msg)


class TestJITIngestionStoreEmbeddingsFlag(PromptCompactionUnitTestBase):
    """Test 4: JIT ingestion respects store_embeddings flag."""

    async def test_skips_when_store_embeddings_false(self):
        """Should skip ingestion when store_embeddings=False."""
        messages = self._generate_test_messages(count=3)

        config = ExtractionConfig(
            construction_strategy=ExtractionStrategyType.EXTRACT_FULL,
            store_embeddings=False,  # Disabled
        )
        strategy = ExtractionStrategy(
            construction_strategy=config.construction_strategy,
            store_embeddings=config.store_embeddings,
        )

        with patch(
            "workflow_service.registry.nodes.llm.prompt_compaction.llm_utils.get_embeddings_batch"
        ) as mock_embeddings, patch(
            "weaviate_client.ThreadMessageWeaviateClient"
        ) as mock_weaviate_class:

            result_messages = await strategy._jit_ingest_messages(
                messages=messages,
                ext_context=self.ext_context,
                thread_id=self.test_thread_id,
                node_id=self.test_node_id,
            )

            # Should not call embeddings or Weaviate
            mock_embeddings.assert_not_called()
            mock_weaviate_class.assert_not_called()

            # Messages should not be marked as ingested
            for msg in result_messages:
                self.assertMessageNotIngested(msg)


class TestJITIngestionEmbeddingGeneration(PromptCompactionUnitTestBase):
    """Test 5: JIT ingestion generates embeddings correctly."""

    async def test_embedding_generation_flow(self):
        """Should call get_embeddings_batch with correct parameters."""
        messages = self._generate_test_messages(count=5)

        config = ExtractionConfig(
            construction_strategy=ExtractionStrategyType.EXTRACT_FULL,
            store_embeddings=True,
            embedding_model="text-embedding-3-small",
        )
        strategy = ExtractionStrategy(
            construction_strategy=config.construction_strategy,
            store_embeddings=config.store_embeddings,
        )

        with patch(
            "workflow_service.registry.nodes.llm.prompt_compaction.llm_utils.get_embeddings_batch"
        ) as mock_embeddings, patch(
            "weaviate_client.ThreadMessageWeaviateClient"
        ) as mock_weaviate_class:

            mock_embeddings.return_value = create_mock_embeddings_response(5)
            mock_weaviate = create_mock_weaviate_client()
            mock_weaviate_class.return_value = mock_weaviate

            await strategy._jit_ingest_messages(
                messages=messages,
                ext_context=self.ext_context,
                thread_id=self.test_thread_id,
                node_id=self.test_node_id,
            )

            # Verify embeddings were requested
            mock_embeddings.assert_called_once()
            call_kwargs = mock_embeddings.call_args[1]

            # Verify parameters
            self.assertEqual(len(call_kwargs["texts"]), 5)
            self.assertEqual(call_kwargs["embedding_model"], "text-embedding-3-small")
            self.assertEqual(call_kwargs["ext_context"], self.ext_context)


class TestJITIngestionWeaviateStorage(PromptCompactionUnitTestBase):
    """Test 6: JIT ingestion stores to Weaviate correctly."""

    async def test_weaviate_storage_flow(self):
        """Should store messages to Weaviate with correct parameters."""
        messages = self._generate_test_messages(count=3)

        config = ExtractionConfig(
            construction_strategy=ExtractionStrategyType.EXTRACT_FULL,
            store_embeddings=True,
        )
        strategy = ExtractionStrategy(
            construction_strategy=config.construction_strategy,
            store_embeddings=config.store_embeddings,
        )

        with patch(
            "workflow_service.registry.nodes.llm.prompt_compaction.llm_utils.get_embeddings_batch"
        ) as mock_embeddings, patch(
            "weaviate_client.ThreadMessageWeaviateClient"
        ) as mock_weaviate_class:

            embeddings = create_mock_embeddings_response(3)
            mock_embeddings.return_value = embeddings
            mock_weaviate = create_mock_weaviate_client()
            mock_weaviate_class.return_value = mock_weaviate

            await strategy._jit_ingest_messages(
                messages=messages,
                ext_context=self.ext_context,
                thread_id=self.test_thread_id,
                node_id=self.test_node_id,
            )

            # Verify Weaviate client lifecycle
            mock_weaviate.connect.assert_called_once()
            mock_weaviate.setup_schema.assert_called_once()
            mock_weaviate.close.assert_called_once()

            # Verify storage calls
            self.assertEqual(mock_weaviate.store_thread_message_chunk.call_count, 3)

            # Verify storage parameters for first message
            first_call = mock_weaviate.store_thread_message_chunk.call_args_list[0]
            call_kwargs = first_call[1]

            self.assertEqual(call_kwargs["thread_id"], self.test_thread_id)
            self.assertEqual(call_kwargs["node_id"], self.test_node_id)
            self.assertEqual(call_kwargs["sequence_no"], 0)
            self.assertEqual(call_kwargs["message_id"], messages[0].id)
            self.assertEqual(call_kwargs["embedding"], embeddings[0])
            self.assertIn("content", call_kwargs)


class TestJITIngestionErrorHandling(PromptCompactionUnitTestBase):
    """Test 7: JIT ingestion handles errors gracefully (non-critical)."""

    async def test_embedding_error_handling(self):
        """Should log warning but not fail when embeddings fail."""
        messages = self._generate_test_messages(count=2)

        config = ExtractionConfig(
            construction_strategy=ExtractionStrategyType.EXTRACT_FULL,
            store_embeddings=True,
        )
        strategy = ExtractionStrategy(
            construction_strategy=config.construction_strategy,
            store_embeddings=config.store_embeddings,
        )

        with patch(
            "workflow_service.registry.nodes.llm.prompt_compaction.llm_utils.get_embeddings_batch"
        ) as mock_embeddings, patch(
            "weaviate_client.ThreadMessageWeaviateClient"
        ) as mock_weaviate_class:

            # Simulate embedding failure
            mock_embeddings.side_effect = Exception("OpenAI API error")
            mock_weaviate = create_mock_weaviate_client()
            mock_weaviate_class.return_value = mock_weaviate

            # Should not raise exception
            result_messages = await strategy._jit_ingest_messages(
                messages=messages,
                ext_context=self.ext_context,
                thread_id=self.test_thread_id,
                node_id=self.test_node_id,
            )

            # Should still return messages
            self.assertEqual(len(result_messages), 2)

            # Messages should be marked as ingested (fallback)
            for msg in result_messages:
                self.assertMessageIngested(msg)

            # Weaviate should not be called
            mock_weaviate_class.assert_not_called()

    async def test_weaviate_error_handling(self):
        """Should log warning but not fail when Weaviate fails."""
        messages = self._generate_test_messages(count=2)

        config = ExtractionConfig(
            construction_strategy=ExtractionStrategyType.EXTRACT_FULL,
            store_embeddings=True,
        )
        strategy = ExtractionStrategy(
            construction_strategy=config.construction_strategy,
            store_embeddings=config.store_embeddings,
        )

        with patch(
            "workflow_service.registry.nodes.llm.prompt_compaction.llm_utils.get_embeddings_batch"
        ) as mock_embeddings, patch(
            "weaviate_client.ThreadMessageWeaviateClient"
        ) as mock_weaviate_class:

            mock_embeddings.return_value = create_mock_embeddings_response(2)

            # Simulate Weaviate connection failure
            mock_weaviate = create_mock_weaviate_client()
            mock_weaviate.connect.side_effect = Exception("Weaviate connection error")
            mock_weaviate_class.return_value = mock_weaviate

            # Should not raise exception
            result_messages = await strategy._jit_ingest_messages(
                messages=messages,
                ext_context=self.ext_context,
                thread_id=self.test_thread_id,
                node_id=self.test_node_id,
            )

            # Should still return messages
            self.assertEqual(len(result_messages), 2)

            # Messages should be marked as ingested (fallback)
            for msg in result_messages:
                self.assertMessageIngested(msg)


class TestJITIngestionDuplicatePrevention(PromptCompactionUnitTestBase):
    """Test 8: JIT ingestion prevents duplicate ingestion."""

    async def test_avoids_re_ingestion(self):
        """Should not re-ingest messages that are already ingested."""
        messages = self._generate_test_messages(count=3)

        # Mark all messages as already ingested
        for msg in messages:
            set_ingestion_metadata(msg, chunk_ids=[f"chunk_{msg.id}"])

        config = ExtractionConfig(
            construction_strategy=ExtractionStrategyType.EXTRACT_FULL,
            store_embeddings=True,
        )
        strategy = ExtractionStrategy(
            construction_strategy=config.construction_strategy,
            store_embeddings=config.store_embeddings,
        )

        with patch(
            "workflow_service.registry.nodes.llm.prompt_compaction.llm_utils.get_embeddings_batch"
        ) as mock_embeddings, patch(
            "weaviate_client.ThreadMessageWeaviateClient"
        ) as mock_weaviate_class:

            result_messages = await strategy._jit_ingest_messages(
                messages=messages,
                ext_context=self.ext_context,
                thread_id=self.test_thread_id,
                node_id=self.test_node_id,
            )

            # Should not call embeddings or Weaviate (all messages already ingested)
            mock_embeddings.assert_not_called()
            mock_weaviate_class.assert_not_called()

            # All messages should still be marked as ingested
            for msg in result_messages:
                self.assertMessageIngested(msg)


class TestJITIngestionEmptyMessageList(PromptCompactionUnitTestBase):
    """Test 9: JIT ingestion handles empty message lists."""

    async def test_empty_message_list(self):
        """Should handle empty message list gracefully."""
        messages = []

        config = ExtractionConfig(
            construction_strategy=ExtractionStrategyType.EXTRACT_FULL,
            store_embeddings=True,
        )
        strategy = ExtractionStrategy(
            construction_strategy=config.construction_strategy,
            store_embeddings=config.store_embeddings,
        )

        with patch(
            "workflow_service.registry.nodes.llm.prompt_compaction.llm_utils.get_embeddings_batch"
        ) as mock_embeddings, patch(
            "weaviate_client.ThreadMessageWeaviateClient"
        ) as mock_weaviate_class:

            result_messages = await strategy._jit_ingest_messages(
                messages=messages,
                ext_context=self.ext_context,
                thread_id=self.test_thread_id,
                node_id=self.test_node_id,
            )

            # Should return empty list
            self.assertEqual(len(result_messages), 0)

            # Should not call embeddings or Weaviate
            mock_embeddings.assert_not_called()
            mock_weaviate_class.assert_not_called()


if __name__ == "__main__":
    unittest.main()
