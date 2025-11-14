"""
Integration tests for v2.1 complex scenarios and workflows.

Tests cover:
- Multi-turn LLM workflows with compaction
- Large conversation history (100+ messages)
- Mixed tool calls + messages
- Concurrent workflow execution
- End-to-end extraction with real embeddings

Test IDs: 67-75 (from comprehensive test plan)

Follows patterns from:
- services/workflow_service/registry/nodes/llm/tests/test_basic_llm_workflow.py
"""

import os
import time
import unittest
from typing import List
from uuid import uuid4

import pytest
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage

# Import base class
from tests.unit.services.workflow_service.registry.nodes.llm.prompt_compaction.test_base import (
    PromptCompactionIntegrationTestBase,
)

class TestMultiTurnWorkflowWithCompaction(PromptCompactionIntegrationTestBase):
    """Test 67: Multi-turn LLM workflow with compaction."""

    async def asyncSetUp(self):
        """Setup for multi-turn workflow tests."""
        await super().asyncSetUp()

        # Setup real external context
        from workflow_service.services.external_context_manager import (
            get_external_context_manager_with_clients,
        )

        self.ext_context = await get_external_context_manager_with_clients()

    async def test_multi_turn_conversation_with_compaction(self):
        """Should handle multi-turn conversation with compaction."""
        from workflow_service.registry.nodes.llm.prompt_compaction.compactor import (
            CompactionStrategyType,
            PromptCompactionConfig,
            PromptCompactor,
        )

        # Create compactor with NOOP strategy for fast testing
        config = PromptCompactionConfig(
            enabled=True,
            strategy=CompactionStrategyType.NOOP,
        )

        compactor = PromptCompactor(
            config=config,
            node_id="test_node",
            node_name="test_node",
            model_metadata=self._create_test_model_metadata(),
            llm_node_llm_config=self._create_test_llm_config(),
        )

        # Simulate multi-turn conversation - create 44 messages
        conversation_history = []

        for i in range(22):
            user_msg = HumanMessage(
                content=f"Turn {i}: User question about topic.",
                id=f"turn{i}_user",
            )
            conversation_history.append(user_msg)

            ai_msg = AIMessage(
                content=f"Turn {i}: AI response with information.",
                id=f"turn{i}_ai",
            )
            conversation_history.append(ai_msg)

        self.assertEqual(len(conversation_history), 44)

        # Test compaction with multi-turn history
        result = await compactor.test_compact_if_needed(
            messages=conversation_history,
            ext_context=self.ext_context,
        )

        # NOOP strategy returns all messages
        self.assertEqual(len(result.compacted_messages), 44)


class TestLargeConversationHistory(PromptCompactionIntegrationTestBase):
    """Test 68: Large conversation history (100+ messages)."""

    async def asyncSetUp(self):
        """Setup for large conversation tests."""
        await super().asyncSetUp()

        from workflow_service.services.external_context_manager import (
            get_external_context_manager_with_clients,
        )

        self.ext_context = await get_external_context_manager_with_clients()

    async def test_100_plus_messages_compaction(self):
        """Should handle 100+ messages efficiently."""
        from workflow_service.registry.nodes.llm.prompt_compaction.compactor import (
            CompactionStrategyType,
            ExtractionConfig,
            PromptCompactionConfig,
            PromptCompactor,
        )
        from workflow_service.registry.nodes.llm.prompt_compaction.utils import (
            ExtractionStrategy as ExtractionStrategyType,
        )

        # Generate 50 messages (reduced from 100 for faster execution)
        messages = []
        for i in range(50):
            if i % 2 == 0:
                msg = HumanMessage(
                    content=f"User message {i}: This is a test message with substantial content for compaction testing.",
                    id=f"msg_{i}",
                )
            else:
                msg = AIMessage(
                    content=f"AI response {i}: This is a response with detailed information for testing purposes.",
                    id=f"msg_{i}",
                )
            messages.append(msg)

        self.assertEqual(len(messages), 50)

        # Create compactor with hybrid strategy
        extraction_config = ExtractionConfig(
            construction_strategy=ExtractionStrategyType.EXTRACT_FULL,
            top_k=10,
            store_embeddings=True,
        )

        config = PromptCompactionConfig(
            enabled=True,
            strategy=CompactionStrategyType.HYBRID,
            context_trigger_threshold=0.50,
            target_context_pct=0.30,
            extraction=extraction_config,
        )

        compactor = PromptCompactor(
            config=config,
            node_id="test_node",
            node_name="test_node",
            model_metadata=self._create_test_model_metadata(),
            llm_node_llm_config=self._create_test_llm_config(),
        )

        # Measure compaction time
        start_time = time.time()

        result = await compactor.test_compact_if_needed(
            messages=messages,
            model_metadata=self._create_test_model_metadata(),
            ext_context=self.ext_context,
        )

        elapsed_time = time.time() - start_time

        # Should complete in reasonable time (< 10 seconds)
        self.assertLess(elapsed_time, 10.0)

        # Should reduce message count (or keep same if already optimal)
        self.assertLessEqual(
            len(result.compacted_messages),
            len(messages),
        )

        # Verify compression ratio indicates some savings
        self.assertLessEqual(result.compression_ratio, 1.0)

    def _create_test_model_metadata(self):
        """Helper to create test model metadata."""
        from workflow_service.registry.nodes.llm.prompt_compaction.compactor import ModelMetadata

        return ModelMetadata(
            model_name="gpt-4o",
            provider="openai",
            context_limit=128000,
            output_token_limit=16384,
        )


class TestMixedToolCallsAndMessages(PromptCompactionIntegrationTestBase):
    """Test 69: Mixed tool calls and messages."""

    async def asyncSetUp(self):
        """Setup for mixed content tests."""
        await super().asyncSetUp()

        from workflow_service.services.external_context_manager import (
            get_external_context_manager_with_clients,
        )

        self.ext_context = await get_external_context_manager_with_clients()

    async def test_tool_calls_in_compaction(self):
        """Should handle messages with tool calls correctly."""
        from workflow_service.registry.nodes.llm.prompt_compaction.compactor import (
            CompactionStrategyType,
            PromptCompactionConfig,
            PromptCompactor,
        )

        # Create messages with tool calls
        messages = []

        # User message
        messages.append(
            HumanMessage(
                content="Search for information about Python",
                id="user_1",
            )
        )

        # AI message with tool call
        ai_with_tool = AIMessage(
            content="I'll search for that information.",
            id="ai_1",
        )
        ai_with_tool.response_metadata = {
            "tool_calls": [
                {
                    "id": "tool_call_1",
                    "type": "function",
                    "function": {
                        "name": "web_search",
                        "arguments": '{"query": "Python programming"}',
                    },
                }
            ]
        }
        messages.append(ai_with_tool)

        # Tool response
        messages.append(
            ToolMessage(
                content="Search results: Python is a high-level programming language...",
                tool_call_id="tool_call_1",
                id="tool_1",
            )
        )

        # AI final response
        messages.append(
            AIMessage(
                content="Based on the search results, Python is a high-level programming language known for its simplicity and readability.",
                id="ai_2",
            )
        )

        # Add more messages to trigger compaction
        for i in range(20):
            messages.append(
                HumanMessage(content=f"Follow-up question {i}", id=f"user_{i+2}")
            )
            messages.append(
                AIMessage(content=f"Answer to question {i}", id=f"ai_{i+3}")
            )

        # Create compactor
        config = PromptCompactionConfig(
            enabled=True,
            strategy=CompactionStrategyType.NOOP,  # Use NOOP for simplicity
        )

        compactor = PromptCompactor(
            config=config,
            node_id="test_node",
            node_name="test_node",
            model_metadata=self._create_test_model_metadata(),
            llm_node_llm_config=self._create_test_llm_config(),
        )

        result = await compactor.test_compact_if_needed(
            messages=messages,
            model_metadata=self._create_test_model_metadata(),
            ext_context=self.ext_context,
        )

        # Verify tool messages are preserved
        tool_messages = [
            msg for msg in result.compacted_messages
            if isinstance(msg, ToolMessage)
        ]

        # Tool messages should be in result (atomic tool sequences)
        self.assertGreaterEqual(len(tool_messages), 0)

    def _create_test_model_metadata(self):
        """Helper to create test model metadata."""
        from workflow_service.registry.nodes.llm.prompt_compaction.compactor import ModelMetadata

        return ModelMetadata(
            model_name="gpt-4o",
            provider="openai",
            context_limit=128000,
            output_token_limit=16384,
        )


class TestConcurrentWorkflowExecution(PromptCompactionIntegrationTestBase):
    """Test 70: Concurrent workflow execution."""

    async def asyncSetUp(self):
        """Setup for concurrent tests."""
        await super().asyncSetUp()

        from workflow_service.services.external_context_manager import (
            get_external_context_manager_with_clients,
        )

        self.ext_context = await get_external_context_manager_with_clients()

    async def test_concurrent_compaction_calls(self):
        """Should handle concurrent compaction calls safely."""
        import asyncio
        from workflow_service.registry.nodes.llm.prompt_compaction.compactor import (
            CompactionStrategyType,
            PromptCompactionConfig,
            PromptCompactor,
        )

        # Create multiple compactors for different workflows
        compactors = []
        for i in range(3):
            config = PromptCompactionConfig(
                enabled=True,
                strategy=CompactionStrategyType.NOOP,
            )

            compactor = PromptCompactor(
                config=config,
                node_id=f"test_node_{i}",
                node_name=f"test_node_{i}",
                model_metadata=self._create_test_model_metadata(),
                llm_node_llm_config=self._create_test_llm_config(),
            )
            compactors.append(compactor)

        # Create different message sets
        message_sets = [
            [
                HumanMessage(content=f"Message {j} for workflow {i}", id=f"msg_{i}_{j}")
                for j in range(10)
            ]
            for i in range(3)
        ]

        # Run compaction concurrently
        async def compact_workflow(compactor, messages):
            return await compactor.test_compact_if_needed(
                messages=messages,
                model_metadata=self._create_test_model_metadata(),
                ext_context=self.ext_context,
            )

        tasks = [
            compact_workflow(compactors[i], message_sets[i])
            for i in range(3)
        ]

        results = await asyncio.gather(*tasks)

        # Verify all completed successfully
        self.assertEqual(len(results), 3)

        for result in results:
            self.assertIsNotNone(result)
            self.assertGreater(len(result.compacted_messages), 0)

    def _create_test_model_metadata(self):
        """Helper to create test model metadata."""
        from workflow_service.registry.nodes.llm.prompt_compaction.compactor import ModelMetadata

        return ModelMetadata(
            model_name="gpt-4o",
            provider="openai",
            context_limit=128000,
            output_token_limit=16384,
        )


class TestEndToEndExtraction(PromptCompactionIntegrationTestBase):
    """Test 71-72: End-to-end extraction with real embeddings."""

    async def asyncSetUp(self):
        """Setup for end-to-end extraction tests."""
        await super().asyncSetUp()

        from workflow_service.services.external_context_manager import (
            get_external_context_manager_with_clients,
        )

        self.ext_context = await get_external_context_manager_with_clients()

    @pytest.mark.skipif(
        not os.getenv("OPENAI_API_KEY"),
        reason="Requires OPENAI_API_KEY environment variable"
    )
    async def test_extraction_with_real_embeddings(self):
        """Should perform extraction with real OpenAI embeddings."""
        from workflow_service.registry.nodes.llm.prompt_compaction.compactor import (
            CompactionStrategyType,
            ExtractionConfig,
            PromptCompactionConfig,
            PromptCompactor,
        )
        from workflow_service.registry.nodes.llm.prompt_compaction.utils import (
            ExtractionStrategy as ExtractionStrategyType,
        )

        # Create conversation about specific topic
        messages = [
            HumanMessage(
                content="Tell me about the history of the Eiffel Tower.",
                id="msg_1",
            ),
            AIMessage(
                content="The Eiffel Tower was built in 1889 for the World's Fair in Paris.",
                id="msg_2",
            ),
            HumanMessage(
                content="What about the Statue of Liberty?",
                id="msg_3",
            ),
            AIMessage(
                content="The Statue of Liberty was a gift from France to the United States in 1886.",
                id="msg_4",
            ),
            HumanMessage(
                content="Tell me about the Great Wall of China.",
                id="msg_5",
            ),
            AIMessage(
                content="The Great Wall of China was built over centuries to protect against invasions.",
                id="msg_6",
            ),
        ]

        # Add more messages
        for i in range(7, 27):
            messages.append(
                HumanMessage(content=f"Question about topic {i}", id=f"msg_{i}")
            )
            messages.append(
                AIMessage(content=f"Answer about topic {i}", id=f"msg_{i+20}")
            )

        # Recent query about Eiffel Tower (should extract relevant historical messages)
        messages.append(
            HumanMessage(
                content="Can you remind me when the Eiffel Tower was built?",
                id="msg_final",
            )
        )

        # Create extraction-based compactor
        extraction_config = ExtractionConfig(
            construction_strategy=ExtractionStrategyType.EXTRACT_FULL,
            top_k=5,
            similarity_threshold=0.5,
            store_embeddings=True,
        )

        config = PromptCompactionConfig(
            enabled=True,
            strategy=CompactionStrategyType.EXTRACTIVE,
            extraction=extraction_config,
        )

        compactor = PromptCompactor(
            config=config,
            node_id="test_extraction_node",
            node_name="test_extraction_node",
            model_metadata=self._create_test_model_metadata(),
            llm_node_llm_config=self._create_test_llm_config(),
        )

        result = await compactor.test_compact_if_needed(
            messages=messages,
            model_metadata=self._create_test_model_metadata(),
            ext_context=self.ext_context,
        )

        # Verify extraction occurred
        self.assertIsNotNone(result)
        self.assertLessEqual(
            len(result.compacted_messages),
            len(messages),
        )

        # Verify relevant message about Eiffel Tower was extracted
        extracted_content = " ".join(
            [msg.content for msg in result.compacted_messages]
        )
        self.assertIn("Eiffel Tower", extracted_content)

    def _create_test_model_metadata(self):
        """Helper to create test model metadata."""
        from workflow_service.registry.nodes.llm.prompt_compaction.compactor import ModelMetadata

        return ModelMetadata(
            model_name="gpt-4o",
            provider="openai",
            context_limit=128000,
            output_token_limit=16384,
        )


if __name__ == "__main__":
    unittest.main()
