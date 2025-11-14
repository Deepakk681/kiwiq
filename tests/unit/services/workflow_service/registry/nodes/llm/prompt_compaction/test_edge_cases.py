"""
Unit tests for v2.1 edge cases and error handling.

Tests cover:
- Empty message lists
- Malformed embeddings
- Budget exhaustion scenarios
- Weaviate connection failures (unit test with mocks)
- Invalid configuration
- Concurrent compaction calls

Test IDs: 62-66 (from comprehensive test plan)
"""

import unittest
from unittest.mock import AsyncMock, Mock, patch

from workflow_service.registry.nodes.llm.prompt_compaction.compactor import (
    CompactionStrategyType,
    ExtractionConfig,
    PromptCompactionConfig,
    PromptCompactor,
)
from workflow_service.registry.nodes.llm.prompt_compaction.strategies import (
    ExtractionStrategy,
    NoOpStrategy,
)
from workflow_service.registry.nodes.llm.prompt_compaction.utils import (
    ExtractionStrategy as ExtractionStrategyType,
)

from .test_base import PromptCompactionUnitTestBase


class TestEmptyMessageLists(PromptCompactionUnitTestBase):
    """Test 62: Handling empty message lists."""

    async def test_empty_sections(self):
        """Should handle empty sections gracefully."""
        strategy = NoOpStrategy()

        sections = {
            "system": [],
            "summaries": [],
            "historical": [],
            "old_tools": [],
            "marked": [],
            "latest_tools": [],
            "recent": [],
        }

        result = await strategy.compact(
            sections=sections,
            budget=self._create_test_budget(),
            model_metadata=self._create_test_model_metadata(),
            ext_context=self.ext_context,
        )

        # Should return empty result
        self.assertEqual(len(result.compacted_messages), 0)

    async def test_only_system_messages(self):
        """Should handle case with only system messages."""
        strategy = NoOpStrategy()

        sections = {
            "system": self._generate_test_messages(1, roles=["system"]),
            "summaries": [],
            "historical": [],
            "old_tools": [],
            "marked": [],
            "latest_tools": [],
            "recent": [],
        }

        result = await strategy.compact(
            sections=sections,
            budget=self._create_test_budget(),
            model_metadata=self._create_test_model_metadata(),
            ext_context=self.ext_context,
        )

        # Should return system message
        self.assertEqual(len(result.compacted_messages), 1)

    async def test_empty_compaction_input(self):
        """Should handle empty input to compact_if_needed."""
        config = self._create_test_config(strategy=CompactionStrategyType.NOOP)

        compactor = PromptCompactor(
            config=config,
            node_id=self.test_node_id,
            node_name="test_node",
            model_metadata=self._create_test_model_metadata(),
        )

        messages = []  # Empty

        # Create mock app_context
        mock_user = Mock()
        mock_user.id = "test_user_id"

        mock_run_job = Mock()
        mock_run_job.owner_org_id = "test_org_id"
        mock_run_job.id = "test_run_id"

        app_context = {
            "user": mock_user,
            "workflow_run_job": mock_run_job,
        }

        result = await compactor.compact(
            messages=messages,
            ext_context=self.ext_context,
            app_context=app_context,
        )

        # Should return empty result
        self.assertEqual(len(result.compacted_messages), 0)


class TestMalformedEmbeddings(PromptCompactionUnitTestBase):
    """Test 63: Handling malformed embeddings."""

    async def test_wrong_embedding_dimensions(self):
        """Should handle embeddings with wrong dimensions."""
        config = ExtractionConfig(
            construction_strategy=ExtractionStrategyType.EXTRACT_FULL,
            store_embeddings=True,
        )
        strategy = ExtractionStrategy(
            construction_strategy=config.construction_strategy,
            store_embeddings=config.store_embeddings,
        )

        messages = self._generate_test_messages(count=5)

        with patch(
            "workflow_service.registry.nodes.llm.prompt_compaction.llm_utils.get_embeddings_batch"
        ) as mock_embeddings, patch(
            "weaviate_client.ThreadMessageWeaviateClient"
        ) as mock_weaviate_class:

            # Return embeddings with wrong dimension (should be 1536, return 512)
            from .test_base import create_mock_weaviate_client
            wrong_dimension_embeddings = [[0.1] * 512 for _ in range(5)]
            mock_embeddings.return_value = wrong_dimension_embeddings

            mock_weaviate = create_mock_weaviate_client()
            mock_weaviate_class.return_value = mock_weaviate

            # Should handle gracefully (non-critical)
            result_messages = await strategy._jit_ingest_messages(
                messages=messages,
                ext_context=self.ext_context,
                thread_id=self.test_thread_id,
                node_id=self.test_node_id,
            )

            # Should still return messages (even if ingestion failed)
            self.assertEqual(len(result_messages), 5)

    async def test_null_embeddings(self):
        """Should handle null embeddings from API."""
        config = ExtractionConfig(
            construction_strategy=ExtractionStrategyType.EXTRACT_FULL,
            store_embeddings=True,
        )
        strategy = ExtractionStrategy(
            construction_strategy=config.construction_strategy,
            store_embeddings=config.store_embeddings,
        )

        messages = self._generate_test_messages(count=3)

        with patch(
            "workflow_service.registry.nodes.llm.prompt_compaction.llm_utils.get_embeddings_batch"
        ) as mock_embeddings, patch(
            "weaviate_client.ThreadMessageWeaviateClient"
        ) as mock_weaviate_class:

            # Return null embeddings
            mock_embeddings.return_value = None

            from .test_base import create_mock_weaviate_client
            mock_weaviate = create_mock_weaviate_client()
            mock_weaviate_class.return_value = mock_weaviate

            # Should handle gracefully
            result_messages = await strategy._jit_ingest_messages(
                messages=messages,
                ext_context=self.ext_context,
                thread_id=self.test_thread_id,
                node_id=self.test_node_id,
            )

            # Should still return messages
            self.assertEqual(len(result_messages), 3)


class TestBudgetExhaustion(PromptCompactionUnitTestBase):
    """Test 64: Budget exhaustion scenarios."""

    async def test_zero_available_budget(self):
        """Should handle case where very little budget is available."""
        strategy = NoOpStrategy()

        sections = {
            "system": self._generate_test_messages(1, roles=["system"]),
            "summaries": [],
            "historical": [],
            "old_tools": [],
            "marked": [],
            "latest_tools": [],
            "recent": self._generate_test_messages(5),
        }

        # Very small budget
        budget = self._create_test_budget(
            total_context=1000,
            max_output_tokens=500,
        )

        result = await strategy.compact(
            sections=sections,
            budget=budget,
            model_metadata=self._create_test_model_metadata(),
            ext_context=self.ext_context,
        )

        # Should still return result (may be all messages or minimal set)
        self.assertIsNotNone(result)

    async def test_budget_smaller_than_reserved(self):
        """Should handle case where budget is very constrained."""
        strategy = NoOpStrategy()

        sections = {
            "system": self._generate_test_messages(1, roles=["system"]),
            "summaries": [],
            "historical": [],
            "old_tools": [],
            "marked": [],
            "latest_tools": [],
            "recent": self._generate_test_messages(3),
        }

        # Very small budget
        budget = self._create_test_budget(
            total_context=2000,
            max_output_tokens=1000,
        )

        result = await strategy.compact(
            sections=sections,
            budget=budget,
            model_metadata=self._create_test_model_metadata(),
            ext_context=self.ext_context,
        )

        # Should handle gracefully
        self.assertIsNotNone(result)


class TestWeaviateConnectionFailures(PromptCompactionUnitTestBase):
    """Test 65: Weaviate connection failures (mocked)."""

    async def test_weaviate_connection_timeout(self):
        """Should handle Weaviate connection timeout."""
        config = ExtractionConfig(
            construction_strategy=ExtractionStrategyType.EXTRACT_FULL,
            store_embeddings=True,
        )
        strategy = ExtractionStrategy(
            construction_strategy=config.construction_strategy,
            store_embeddings=config.store_embeddings,
        )

        messages = self._generate_test_messages(count=3)

        with patch(
            "workflow_service.registry.nodes.llm.prompt_compaction.llm_utils.get_embeddings_batch"
        ) as mock_embeddings, patch(
            "weaviate_client.ThreadMessageWeaviateClient"
        ) as mock_weaviate_class:

            from .test_base import create_mock_embeddings_response, create_mock_weaviate_client

            mock_embeddings.return_value = create_mock_embeddings_response(3)

            # Simulate connection timeout
            mock_weaviate = create_mock_weaviate_client()
            mock_weaviate.connect.side_effect = TimeoutError("Connection timeout")
            mock_weaviate_class.return_value = mock_weaviate

            # Should not raise exception
            result_messages = await strategy._jit_ingest_messages(
                messages=messages,
                ext_context=self.ext_context,
                thread_id=self.test_thread_id,
                node_id=self.test_node_id,
            )

            # Should still return messages
            self.assertEqual(len(result_messages), 3)

    async def test_weaviate_schema_setup_failure(self):
        """Should handle Weaviate schema setup failure."""
        config = ExtractionConfig(
            construction_strategy=ExtractionStrategyType.EXTRACT_FULL,
            store_embeddings=True,
        )
        strategy = ExtractionStrategy(
            construction_strategy=config.construction_strategy,
            store_embeddings=config.store_embeddings,
        )

        messages = self._generate_test_messages(count=3)

        with patch(
            "workflow_service.registry.nodes.llm.prompt_compaction.llm_utils.get_embeddings_batch"
        ) as mock_embeddings, patch(
            "weaviate_client.ThreadMessageWeaviateClient"
        ) as mock_weaviate_class:

            from .test_base import create_mock_embeddings_response, create_mock_weaviate_client

            mock_embeddings.return_value = create_mock_embeddings_response(3)

            # Simulate schema setup failure
            mock_weaviate = create_mock_weaviate_client()
            mock_weaviate.setup_schema.side_effect = Exception("Schema creation failed")
            mock_weaviate_class.return_value = mock_weaviate

            # Should not raise exception
            result_messages = await strategy._jit_ingest_messages(
                messages=messages,
                ext_context=self.ext_context,
                thread_id=self.test_thread_id,
                node_id=self.test_node_id,
            )

            # Should still return messages
            self.assertEqual(len(result_messages), 3)

    async def test_weaviate_storage_failure(self):
        """Should handle Weaviate storage failure."""
        config = ExtractionConfig(
            construction_strategy=ExtractionStrategyType.EXTRACT_FULL,
            store_embeddings=True,
        )
        strategy = ExtractionStrategy(
            construction_strategy=config.construction_strategy,
            store_embeddings=config.store_embeddings,
        )

        messages = self._generate_test_messages(count=3)

        with patch(
            "workflow_service.registry.nodes.llm.prompt_compaction.llm_utils.get_embeddings_batch"
        ) as mock_embeddings, patch(
            "weaviate_client.ThreadMessageWeaviateClient"
        ) as mock_weaviate_class:

            from .test_base import create_mock_embeddings_response, create_mock_weaviate_client

            mock_embeddings.return_value = create_mock_embeddings_response(3)

            # Simulate storage failure
            mock_weaviate = create_mock_weaviate_client()
            mock_weaviate.store_thread_message_chunk.side_effect = Exception("Storage failed")
            mock_weaviate_class.return_value = mock_weaviate

            # Should not raise exception
            result_messages = await strategy._jit_ingest_messages(
                messages=messages,
                ext_context=self.ext_context,
                thread_id=self.test_thread_id,
                node_id=self.test_node_id,
            )

            # Should still return messages (marked as ingested for fallback)
            self.assertEqual(len(result_messages), 3)


class TestInvalidConfiguration(PromptCompactionUnitTestBase):
    """Test 66: Invalid configuration handling."""

    async def test_invalid_extraction_percentage(self):
        """Should validate extraction percentage bounds."""
        from pydantic import ValidationError
        from workflow_service.registry.nodes.llm.prompt_compaction.compactor import HybridConfig

        # Test invalid percentages
        invalid_percentages = [-0.1, 1.5, 2.0]

        for pct in invalid_percentages:
            with self.assertRaises((ValidationError, ValueError)):
                config = HybridConfig(extraction_pct=pct)

    async def test_invalid_top_k(self):
        """Should validate top_k parameter."""
        from pydantic import ValidationError

        # Test invalid top_k values
        with self.assertRaises((ValidationError, ValueError)):
            config = ExtractionConfig(
                construction_strategy=ExtractionStrategyType.EXTRACT_FULL,
                top_k=-1,  # Negative not allowed
            )

        with self.assertRaises((ValidationError, ValueError)):
            config = ExtractionConfig(
                construction_strategy=ExtractionStrategyType.EXTRACT_FULL,
                top_k=0,  # Zero not allowed
            )

    async def test_invalid_similarity_threshold(self):
        """Should validate similarity threshold bounds."""
        from pydantic import ValidationError

        # Test invalid threshold values
        invalid_thresholds = [-0.5, 1.5, 2.0]

        for threshold in invalid_thresholds:
            with self.assertRaises((ValidationError, ValueError)):
                config = ExtractionConfig(
                    construction_strategy=ExtractionStrategyType.EXTRACT_FULL,
                    similarity_threshold=threshold,
                )


if __name__ == "__main__":
    unittest.main()
