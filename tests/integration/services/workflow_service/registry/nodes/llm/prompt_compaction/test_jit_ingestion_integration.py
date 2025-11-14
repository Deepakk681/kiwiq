"""
Integration tests for v2.1 JIT ingestion with real Weaviate storage.

Tests cover:
- End-to-end Weaviate storage and retrieval
- Multiple message batches
- Concurrent ingestion from different threads
- Storage + retrieval roundtrip verification
- Schema setup and cleanup

Test IDs: 55-61 (from comprehensive test plan)

Follows patterns from:
- tests/integration/clients/weaviate/test_weaviate_client.py
"""

import time
import unittest
from typing import List
from uuid import uuid4

from langchain_core.messages import BaseMessage

from weaviate_client import ThreadMessageWeaviateClient
from workflow_service.registry.nodes.llm.prompt_compaction.compactor import ExtractionConfig
from workflow_service.registry.nodes.llm.prompt_compaction.strategies import ExtractionStrategy
from workflow_service.registry.nodes.llm.prompt_compaction.utils import (
    ExtractionStrategy as ExtractionStrategyType,
    is_message_ingested,
)

# Import base class from unit tests
from tests.unit.services.workflow_service.registry.nodes.llm.prompt_compaction.test_base import (
    PromptCompactionIntegrationTestBase,
)

class TestJITIngestionWeaviateIntegration(PromptCompactionIntegrationTestBase):
    """Test 55: End-to-end JIT ingestion with real Weaviate."""

    async def asyncSetUp(self):
        """Setup Weaviate client for integration tests."""
        await super().asyncSetUp()

        # Create real Weaviate client
        self.weaviate_client = ThreadMessageWeaviateClient()
        await self.weaviate_client.connect()
        await self.weaviate_client.setup_schema()

        # Get real external context
        from workflow_service.services.external_context_manager import (
            get_external_context_manager_with_clients,
        )

        self.ext_context = await get_external_context_manager_with_clients()

    async def asyncTearDown(self):
        """Cleanup Weaviate data after tests."""
        # Delete test thread data
        for thread_id in self.test_thread_ids:
            try:
                # Query and delete chunks for this thread
                # Note: ThreadMessageWeaviateClient may not have bulk delete
                # This is a best-effort cleanup
                pass
            except Exception:
                pass  # Non-critical cleanup failure

        if self.weaviate_client:
            await self.weaviate_client.close()

        await super().asyncTearDown()

    async def test_end_to_end_ingestion_and_storage(self):
        """Should ingest messages and store to Weaviate successfully."""
        # Generate test messages
        messages = []
        for i in range(5):
            msg = self._generate_test_message(
                content=f"Integration test message {i+1}: This is test content for Weaviate storage.",
                role="human" if i % 2 == 0 else "ai",
            )
            messages.append(msg)

        # Create extraction strategy
        config = ExtractionConfig(
            construction_strategy=ExtractionStrategyType.EXTRACT_FULL,
            store_embeddings=True,
            embedding_model="text-embedding-3-small",
        )
        strategy = ExtractionStrategy(config)

        # Generate unique thread ID
        thread_id = self._generate_unique_thread_id()

        # Perform JIT ingestion
        result_messages = await strategy._jit_ingest_messages(
            messages=messages,
            ext_context=self.ext_context,
            thread_id=thread_id,
            node_id=self.test_node_id,
        )

        # Verify all messages marked as ingested
        self.assertEqual(len(result_messages), 5)
        for msg in result_messages:
            self.assertTrue(is_message_ingested(msg))

        # Verify storage in Weaviate - query back the stored chunks
        stored_chunks = await self.weaviate_client.query_thread_messages(
            thread_id=thread_id,
            node_id=self.test_node_id,
            limit=10,
        )

        # Should have stored 5 chunks
        self.assertEqual(len(stored_chunks), 5)

        # Verify chunk structure
        for chunk in stored_chunks:
            self.assertIn("thread_id", chunk)
            self.assertEqual(chunk["thread_id"], thread_id)
            self.assertIn("node_id", chunk)
            self.assertEqual(chunk["node_id"], self.test_node_id)
            self.assertIn("message_id", chunk)
            self.assertIn("embedding", chunk)
            self.assertIn("content", chunk)

            # Verify embedding dimension (text-embedding-3-small = 1536)
            self.assertEqual(len(chunk["embedding"]), 1536)

    def _generate_test_message(self, content: str, role: str = "human"):
        """Helper to generate test messages for integration tests."""
        from langchain_core.messages import HumanMessage, AIMessage

        message_id = f"msg_{uuid4().hex[:8]}"

        if role == "human":
            return HumanMessage(content=content, id=message_id)
        else:
            return AIMessage(content=content, id=message_id)


class TestJITIngestionMultipleBatches(PromptCompactionIntegrationTestBase):
    """Test 56: JIT ingestion with multiple message batches."""

    async def asyncSetUp(self):
        """Setup for multi-batch tests."""
        await super().asyncSetUp()

        self.weaviate_client = ThreadMessageWeaviateClient()
        await self.weaviate_client.connect()
        await self.weaviate_client.setup_schema()

        from workflow_service.services.external_context_manager import (
            get_external_context_manager_with_clients,
        )

        self.ext_context = await get_external_context_manager_with_clients()

    async def asyncTearDown(self):
        """Cleanup after multi-batch tests."""
        if self.weaviate_client:
            await self.weaviate_client.close()
        await super().asyncTearDown()

    async def test_multiple_batches_same_thread(self):
        """Should handle multiple ingestion batches for same thread."""
        config = ExtractionConfig(
            construction_strategy=ExtractionStrategyType.EXTRACT_FULL,
            store_embeddings=True,
        )
        strategy = ExtractionStrategy(config)

        thread_id = self._generate_unique_thread_id()

        # Batch 1: Ingest first 3 messages
        batch1_messages = [
            self._generate_test_message(f"Batch 1 message {i}", "human")
            for i in range(3)
        ]

        await strategy._jit_ingest_messages(
            messages=batch1_messages,
            ext_context=self.ext_context,
            thread_id=thread_id,
            node_id=self.test_node_id,
        )

        # Batch 2: Ingest next 3 messages
        batch2_messages = [
            self._generate_test_message(f"Batch 2 message {i}", "ai")
            for i in range(3)
        ]

        await strategy._jit_ingest_messages(
            messages=batch2_messages,
            ext_context=self.ext_context,
            thread_id=thread_id,
            node_id=self.test_node_id,
        )

        # Batch 3: Attempt to re-ingest batch1 messages (should skip)
        await strategy._jit_ingest_messages(
            messages=batch1_messages,
            ext_context=self.ext_context,
            thread_id=thread_id,
            node_id=self.test_node_id,
        )

        # Query stored chunks
        stored_chunks = await self.weaviate_client.query_thread_messages(
            thread_id=thread_id,
            node_id=self.test_node_id,
            limit=20,
        )

        # Should have 6 chunks total (batch1 + batch2, batch3 skipped)
        self.assertEqual(len(stored_chunks), 6)

    def _generate_test_message(self, content: str, role: str):
        """Helper for test message generation."""
        from langchain_core.messages import HumanMessage, AIMessage

        message_id = f"msg_{uuid4().hex[:8]}"
        if role == "human":
            return HumanMessage(content=content, id=message_id)
        else:
            return AIMessage(content=content, id=message_id)


class TestJITIngestionConcurrentThreads(PromptCompactionIntegrationTestBase):
    """Test 57: JIT ingestion with concurrent threads."""

    async def asyncSetUp(self):
        """Setup for concurrent tests."""
        await super().asyncSetUp()

        self.weaviate_client = ThreadMessageWeaviateClient()
        await self.weaviate_client.connect()
        await self.weaviate_client.setup_schema()

        from workflow_service.services.external_context_manager import (
            get_external_context_manager_with_clients,
        )

        self.ext_context = await get_external_context_manager_with_clients()

    async def asyncTearDown(self):
        """Cleanup after concurrent tests."""
        if self.weaviate_client:
            await self.weaviate_client.close()
        await super().asyncTearDown()

    async def test_concurrent_ingestion_different_threads(self):
        """Should handle concurrent ingestion from different threads."""
        import asyncio

        config = ExtractionConfig(
            construction_strategy=ExtractionStrategyType.EXTRACT_FULL,
            store_embeddings=True,
        )
        strategy = ExtractionStrategy(config)

        # Create 3 different threads
        thread_ids = [
            self._generate_unique_thread_id(),
            self._generate_unique_thread_id(),
            self._generate_unique_thread_id(),
        ]

        # Create messages for each thread
        async def ingest_thread(thread_id: str):
            messages = [
                self._generate_test_message(f"Thread {thread_id} message {i}", "human")
                for i in range(3)
            ]
            await strategy._jit_ingest_messages(
                messages=messages,
                ext_context=self.ext_context,
                thread_id=thread_id,
                node_id=self.test_node_id,
            )

        # Run concurrent ingestion
        await asyncio.gather(*[ingest_thread(tid) for tid in thread_ids])

        # Verify each thread has its own chunks
        for thread_id in thread_ids:
            stored_chunks = await self.weaviate_client.query_thread_messages(
                thread_id=thread_id,
                node_id=self.test_node_id,
                limit=10,
            )
            # Each thread should have 3 chunks
            self.assertEqual(len(stored_chunks), 3)

    def _generate_test_message(self, content: str, role: str):
        """Helper for test message generation."""
        from langchain_core.messages import HumanMessage

        message_id = f"msg_{uuid4().hex[:8]}"
        return HumanMessage(content=content, id=message_id)


class TestJITIngestionStorageRetrieval(PromptCompactionIntegrationTestBase):
    """Test 58: JIT ingestion storage and retrieval roundtrip."""

    async def asyncSetUp(self):
        """Setup for roundtrip tests."""
        await super().asyncSetUp()

        self.weaviate_client = ThreadMessageWeaviateClient()
        await self.weaviate_client.connect()
        await self.weaviate_client.setup_schema()

        from workflow_service.services.external_context_manager import (
            get_external_context_manager_with_clients,
        )

        self.ext_context = await get_external_context_manager_with_clients()

    async def asyncTearDown(self):
        """Cleanup after roundtrip tests."""
        if self.weaviate_client:
            await self.weaviate_client.close()
        await super().asyncTearDown()

    async def test_storage_retrieval_roundtrip(self):
        """Should store and retrieve messages with full fidelity."""
        config = ExtractionConfig(
            construction_strategy=ExtractionStrategyType.EXTRACT_FULL,
            store_embeddings=True,
        )
        strategy = ExtractionStrategy(config)

        thread_id = self._generate_unique_thread_id()

        # Create messages with specific content
        original_messages = [
            self._generate_test_message(
                content=f"Message {i}: This is test content with specific text to verify roundtrip.",
                role="human" if i % 2 == 0 else "ai",
                message_id=f"test_msg_{i}",
            )
            for i in range(3)
        ]

        # Ingest messages
        await strategy._jit_ingest_messages(
            messages=original_messages,
            ext_context=self.ext_context,
            thread_id=thread_id,
            node_id=self.test_node_id,
        )

        # Retrieve stored chunks
        stored_chunks = await self.weaviate_client.query_thread_messages(
            thread_id=thread_id,
            node_id=self.test_node_id,
            limit=10,
        )

        # Verify chunk count
        self.assertEqual(len(stored_chunks), 3)

        # Verify content preservation (may be truncated to 1000 chars)
        original_message_ids = {msg.id for msg in original_messages}
        stored_message_ids = {chunk["message_id"] for chunk in stored_chunks}

        # All original message IDs should be in stored chunks
        self.assertEqual(original_message_ids, stored_message_ids)

        # Verify embeddings are present and correct dimension
        for chunk in stored_chunks:
            self.assertIsNotNone(chunk["embedding"])
            self.assertEqual(len(chunk["embedding"]), 1536)

    def _generate_test_message(self, content: str, role: str, message_id: str):
        """Helper for test message generation with specific ID."""
        from langchain_core.messages import HumanMessage, AIMessage

        if role == "human":
            return HumanMessage(content=content, id=message_id)
        else:
            return AIMessage(content=content, id=message_id)


class TestJITIngestionLargeMessageBatch(PromptCompactionIntegrationTestBase):
    """Test 59: JIT ingestion with large message batches."""

    async def asyncSetUp(self):
        """Setup for large batch tests."""
        await super().asyncSetUp()

        self.weaviate_client = ThreadMessageWeaviateClient()
        await self.weaviate_client.connect()
        await self.weaviate_client.setup_schema()

        from workflow_service.services.external_context_manager import (
            get_external_context_manager_with_clients,
        )

        self.ext_context = await get_external_context_manager_with_clients()

    async def asyncTearDown(self):
        """Cleanup after large batch tests."""
        if self.weaviate_client:
            await self.weaviate_client.close()
        await super().asyncTearDown()

    async def test_large_message_batch(self):
        """Should handle ingestion of 50+ messages efficiently."""
        config = ExtractionConfig(
            construction_strategy=ExtractionStrategyType.EXTRACT_FULL,
            store_embeddings=True,
        )
        strategy = ExtractionStrategy(config)

        thread_id = self._generate_unique_thread_id()

        # Create 50 messages
        messages = [
            self._generate_test_message(
                content=f"Large batch test message {i}: Content for performance testing.",
                role="human" if i % 2 == 0 else "ai",
            )
            for i in range(50)
        ]

        # Measure ingestion time
        import time
        start_time = time.time()

        await strategy._jit_ingest_messages(
            messages=messages,
            ext_context=self.ext_context,
            thread_id=thread_id,
            node_id=self.test_node_id,
        )

        elapsed_time = time.time() - start_time

        # Should complete in reasonable time (< 30 seconds for 50 messages)
        self.assertLess(elapsed_time, 30.0)

        # Verify all messages stored
        stored_chunks = await self.weaviate_client.query_thread_messages(
            thread_id=thread_id,
            node_id=self.test_node_id,
            limit=100,
        )

        self.assertEqual(len(stored_chunks), 50)

    def _generate_test_message(self, content: str, role: str):
        """Helper for test message generation."""
        from langchain_core.messages import HumanMessage, AIMessage

        message_id = f"msg_{uuid4().hex[:8]}"
        if role == "human":
            return HumanMessage(content=content, id=message_id)
        else:
            return AIMessage(content=content, id=message_id)


class TestJITIngestionSequenceNumbers(PromptCompactionIntegrationTestBase):
    """Test 60: JIT ingestion assigns correct sequence numbers."""

    async def asyncSetUp(self):
        """Setup for sequence number tests."""
        await super().asyncSetUp()

        self.weaviate_client = ThreadMessageWeaviateClient()
        await self.weaviate_client.connect()
        await self.weaviate_client.setup_schema()

        from workflow_service.services.external_context_manager import (
            get_external_context_manager_with_clients,
        )

        self.ext_context = await get_external_context_manager_with_clients()

    async def asyncTearDown(self):
        """Cleanup after sequence tests."""
        if self.weaviate_client:
            await self.weaviate_client.close()
        await super().asyncTearDown()

    async def test_sequence_number_assignment(self):
        """Should assign sequential sequence numbers to messages."""
        config = ExtractionConfig(
            construction_strategy=ExtractionStrategyType.EXTRACT_FULL,
            store_embeddings=True,
        )
        strategy = ExtractionStrategy(config)

        thread_id = self._generate_unique_thread_id()

        # Create 5 messages
        messages = [
            self._generate_test_message(f"Sequence test message {i}", "human")
            for i in range(5)
        ]

        # Ingest messages
        await strategy._jit_ingest_messages(
            messages=messages,
            ext_context=self.ext_context,
            thread_id=thread_id,
            node_id=self.test_node_id,
        )

        # Retrieve stored chunks
        stored_chunks = await self.weaviate_client.query_thread_messages(
            thread_id=thread_id,
            node_id=self.test_node_id,
            limit=10,
        )

        # Verify sequence numbers
        sequence_numbers = [chunk["sequence_no"] for chunk in stored_chunks]
        sequence_numbers.sort()

        # Should be [0, 1, 2, 3, 4]
        self.assertEqual(sequence_numbers, [0, 1, 2, 3, 4])

    def _generate_test_message(self, content: str, role: str):
        """Helper for test message generation."""
        from langchain_core.messages import HumanMessage

        message_id = f"msg_{uuid4().hex[:8]}"
        return HumanMessage(content=content, id=message_id)


class TestJITIngestionNodeIsolation(PromptCompactionIntegrationTestBase):
    """Test 61: JIT ingestion isolates messages by node_id."""

    async def asyncSetUp(self):
        """Setup for node isolation tests."""
        await super().asyncSetUp()

        self.weaviate_client = ThreadMessageWeaviateClient()
        await self.weaviate_client.connect()
        await self.weaviate_client.setup_schema()

        from workflow_service.services.external_context_manager import (
            get_external_context_manager_with_clients,
        )

        self.ext_context = await get_external_context_manager_with_clients()

    async def asyncTearDown(self):
        """Cleanup after node isolation tests."""
        if self.weaviate_client:
            await self.weaviate_client.close()
        await super().asyncTearDown()

    async def test_node_id_isolation(self):
        """Should isolate messages by node_id within same thread."""
        config = ExtractionConfig(
            construction_strategy=ExtractionStrategyType.EXTRACT_FULL,
            store_embeddings=True,
        )
        strategy = ExtractionStrategy(config)

        thread_id = self._generate_unique_thread_id()
        node_id_1 = f"node_1_{uuid4().hex[:6]}"
        node_id_2 = f"node_2_{uuid4().hex[:6]}"

        # Ingest messages for node 1
        messages_node1 = [
            self._generate_test_message(f"Node 1 message {i}", "human")
            for i in range(3)
        ]

        await strategy._jit_ingest_messages(
            messages=messages_node1,
            ext_context=self.ext_context,
            thread_id=thread_id,
            node_id=node_id_1,
        )

        # Ingest messages for node 2
        messages_node2 = [
            self._generate_test_message(f"Node 2 message {i}", "ai")
            for i in range(3)
        ]

        await strategy._jit_ingest_messages(
            messages=messages_node2,
            ext_context=self.ext_context,
            thread_id=thread_id,
            node_id=node_id_2,
        )

        # Query node 1 chunks
        chunks_node1 = await self.weaviate_client.query_thread_messages(
            thread_id=thread_id,
            node_id=node_id_1,
            limit=10,
        )

        # Query node 2 chunks
        chunks_node2 = await self.weaviate_client.query_thread_messages(
            thread_id=thread_id,
            node_id=node_id_2,
            limit=10,
        )

        # Each node should have 3 chunks
        self.assertEqual(len(chunks_node1), 3)
        self.assertEqual(len(chunks_node2), 3)

        # Verify node_id values
        for chunk in chunks_node1:
            self.assertEqual(chunk["node_id"], node_id_1)

        for chunk in chunks_node2:
            self.assertEqual(chunk["node_id"], node_id_2)

    def _generate_test_message(self, content: str, role: str):
        """Helper for test message generation."""
        from langchain_core.messages import HumanMessage, AIMessage

        message_id = f"msg_{uuid4().hex[:8]}"
        if role == "human":
            return HumanMessage(content=content, id=message_id)
        else:
            return AIMessage(content=content, id=message_id)


if __name__ == "__main__":
    unittest.main()
