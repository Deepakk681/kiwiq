"""
Integration tests for compaction output message types.

These tests verify that ALL compaction strategy outputs return AIMessage types ONLY.
Expected failures until type enforcement is properly implemented.

Critical Requirements:
1. All summarization outputs → AIMessage only
2. All extraction outputs → AIMessage only
3. All hybrid outputs → AIMessage only
4. Never HumanMessage, SystemMessage, ToolMessage, or other types
"""

import pytest
import unittest
from typing import List, Dict, Any
from uuid import uuid4

from langchain_core.messages import AIMessage, HumanMessage, BaseMessage

from tests.unit.services.workflow_service.registry.nodes.llm.prompt_compaction.test_base import (
    PromptCompactionIntegrationTestBase,
)
from .test_helpers_comprehensive import (
    generate_token_heavy_messages,
    add_linkedin_metadata,
    verify_all_ai_messages,
)

from workflow_service.registry.nodes.llm.prompt_compaction.compactor import (
    PromptCompactionConfig,
)
from workflow_service.registry.nodes.llm.prompt_compaction.strategies import (
    CompactionStrategyType,
    SummarizationMode,
)


@pytest.mark.integration
@pytest.mark.slow
class TestCompactionOutputMessageTypes(PromptCompactionIntegrationTestBase):
    """
    Test that all compaction outputs are AIMessages only.
    """

    async def asyncSetUp(self):
        """Setup real external context for integration tests."""
        await super().asyncSetUp()

        from workflow_service.services.external_context_manager import (
            get_external_context_manager_with_clients,
        )

        self.ext_context = await get_external_context_manager_with_clients()

    # ========================================
    # Summarization Outputs (4 tests)
    # ========================================

    async def test_summarization_produces_ai_messages_only(self):
        """
        Test: Summarization strategy produces only AIMessages.

        All summary messages must be AIMessage type, never HumanMessage.
        """
        thread_id = f"test-summ-ai-only-{uuid4()}"
        self.test_thread_ids.append(thread_id)

        messages = generate_token_heavy_messages(count=20, tokens_per_message=250)
        messages = add_linkedin_metadata(messages)

        config = self._create_test_config(
            mode=SummarizationMode.FROM_SCRATCH,
            strategy=CompactionStrategyType.SUMMARIZATION,
            max_tokens=4000,
            target_tokens=2000,
        )

        result = await self._run_compaction(
            messages=messages,
            config=config,
            thread_id=thread_id,
        )

        summarized = result.get("summarized_messages", [])

        # Find summary messages (SUMMARY section)
        summary_msgs = [
            msg for msg in summarized
            if "SUMMARY" in msg.response_metadata.get("section_label", "")
        ]

        if summary_msgs:
            # Critical: All summary messages must be AIMessages
            verify_all_ai_messages(summary_msgs, "summarization output")

            # Explicitly check no HumanMessage, SystemMessage, etc.
            for msg in summary_msgs:
                self.assertIsInstance(
                    msg, AIMessage,
                    f"Summary message must be AIMessage, got {type(msg).__name__}"
                )

    async def test_hierarchical_summaries_are_ai_messages(self):
        """
        Test: Hierarchical summarization (L0→L1→L2) produces AIMessages.

        When summaries are too large and need recursive summarization,
        all levels must be AIMessages.
        """
        thread_id = f"test-hierarchical-ai-{uuid4()}"
        self.test_thread_ids.append(thread_id)

        # Create moderate message set to trigger hierarchical summarization (optimized for speed)
        messages = generate_token_heavy_messages(count=20, tokens_per_message=300)
        messages = add_linkedin_metadata(messages)

        config = self._create_test_config(
            mode=SummarizationMode.FROM_SCRATCH,
            strategy=CompactionStrategyType.SUMMARIZATION,
            max_tokens=8000,  # Reasonable budget for faster test execution
            target_tokens=5000,
        )

        result = await self._run_compaction(
            messages=messages,
            config=config,
            thread_id=thread_id,
        )

        summarized = result.get("summarized_messages", [])

        # Find all summary messages (L0, L1, L2, etc.)
        summary_msgs = [
            msg for msg in summarized
            if "SUMMARY" in msg.response_metadata.get("compaction", {}).get("section_label", "")
        ]

        if summary_msgs:
            # All hierarchical summaries must be AIMessages
            verify_all_ai_messages(summary_msgs, "hierarchical summarization")

            for msg in summary_msgs:
                self.assertIsInstance(
                    msg, AIMessage,
                    f"Hierarchical summary must be AIMessage, got {type(msg).__name__}"
                )

    async def test_from_scratch_summary_is_ai_message(self):
        """
        Test: FROM_SCRATCH mode summarization produces AIMessages.
        """
        thread_id = f"test-from-scratch-ai-{uuid4()}"
        self.test_thread_ids.append(thread_id)

        messages = generate_token_heavy_messages(count=15, tokens_per_message=300)
        messages = add_linkedin_metadata(messages)

        config = self._create_test_config(
            mode=SummarizationMode.FROM_SCRATCH,
            strategy=CompactionStrategyType.SUMMARIZATION,
            max_tokens=4000,
            target_tokens=2000,
        )

        result = await self._run_compaction(
            messages=messages,
            config=config,
            thread_id=thread_id,
        )

        summarized = result.get("summarized_messages", [])

        summary_msgs = [
            msg for msg in summarized
            if "SUMMARY" in msg.response_metadata.get("section_label", "")
        ]

        if summary_msgs:
            verify_all_ai_messages(summary_msgs, "FROM_SCRATCH summarization")

    async def test_continued_summary_is_ai_message(self):
        """
        Test: CONTINUED mode summarization produces AIMessages.

        When continuing from previous summary, new summary must be AIMessage.
        """
        thread_id = f"test-continued-ai-{uuid4()}"
        self.test_thread_ids.append(thread_id)

        # Turn 1: FROM_SCRATCH
        messages_turn1 = generate_token_heavy_messages(count=10, tokens_per_message=300)
        add_linkedin_metadata(messages_turn1)

        config = self._create_test_config(
            mode=SummarizationMode.FROM_SCRATCH,
            strategy=CompactionStrategyType.SUMMARIZATION,
            max_tokens=4000,
            target_tokens=2000,
        )

        result1 = await self._run_compaction(
            messages=messages_turn1,
            config=config,
            thread_id=thread_id,
        )

        history = result1.get("summarized_messages", [])

        # Turn 2: CONTINUED
        messages_turn2 = generate_token_heavy_messages(count=10, tokens_per_message=300)
        add_linkedin_metadata(messages_turn2)

        messages_combined = history + messages_turn2

        config.summarization.mode = SummarizationMode.CONTINUED
        result2 = await self._run_compaction(
            messages=messages_combined,
            config=config,
            thread_id=thread_id,
        )

        summarized = result2.get("summarized_messages", [])

        summary_msgs = [
            msg for msg in summarized
            if "SUMMARY" in msg.response_metadata.get("section_label", "")
        ]

        if summary_msgs:
            verify_all_ai_messages(summary_msgs, "CONTINUED summarization")

    # ========================================
    # Extraction Outputs (3 tests)
    # ========================================

    async def test_extraction_produces_ai_messages_only(self):
        """
        Test: Extraction strategy produces only AIMessages.

        Extracted messages must be AIMessages.
        """
        thread_id = f"test-extraction-ai-{uuid4()}"
        self.test_thread_ids.append(thread_id)

        messages = generate_token_heavy_messages(count=20, tokens_per_message=250)
        messages = add_linkedin_metadata(messages)

        config = self._create_test_config(
            mode=SummarizationMode.FROM_SCRATCH,
            strategy=CompactionStrategyType.EXTRACTIVE,
            max_tokens=4000,
            target_tokens=2000,
        )

        result = await self._run_compaction(
            messages=messages,
            config=config,
            thread_id=thread_id,
        )

        summarized = result.get("summarized_messages", [])

        # Find extracted messages (EXTRACTED section)
        extracted_msgs = [
            msg for msg in summarized
            if "EXTRACTED" in msg.response_metadata.get("section_label", "")
        ]

        if extracted_msgs:
            # Critical: All extracted messages must be AIMessages
            verify_all_ai_messages(extracted_msgs, "extraction output")

            for msg in extracted_msgs:
                self.assertIsInstance(
                    msg, AIMessage,
                    f"Extracted message must be AIMessage, got {type(msg).__name__}"
                )

    async def test_extraction_with_expansion_ai_messages(self):
        """
        Test: Extraction with chunk expansion produces AIMessages.

        When extracting chunks and expanding them, outputs must be AIMessages.
        """
        thread_id = f"test-extraction-expansion-ai-{uuid4()}"
        self.test_thread_ids.append(thread_id)

        # Create large messages to trigger chunking
        messages = []
        for i in range(10):
            large_content = f"Message {i}: " + ("X" * 7000)  # ~7K tokens
            msg = HumanMessage(content=large_content, id=f"msg_{i}")
            messages.append(msg)

        messages = add_linkedin_metadata(messages)

        config = self._create_test_config(
            mode=SummarizationMode.FROM_SCRATCH,
            strategy=CompactionStrategyType.EXTRACTIVE,
            max_tokens=10000,
            target_tokens=5000,
        )

        result = await self._run_compaction(
            messages=messages,
            config=config,
            thread_id=thread_id,
        )

        summarized = result.get("summarized_messages", [])

        extracted_msgs = [
            msg for msg in summarized
            if "EXTRACTED" in msg.response_metadata.get("section_label", "")
        ]

        if extracted_msgs:
            verify_all_ai_messages(extracted_msgs, "extraction with expansion")

    async def test_dump_strategy_extraction_ai_messages(self):
        """
        Test: Dump strategy (extraction fallback) produces AIMessages.

        When extraction uses dump strategy (no Weaviate), outputs must be AIMessages.
        """
        thread_id = f"test-dump-extraction-ai-{uuid4()}"
        self.test_thread_ids.append(thread_id)

        messages = generate_token_heavy_messages(count=15, tokens_per_message=300)
        messages = add_linkedin_metadata(messages)

        config = self._create_test_config(
            mode=SummarizationMode.FROM_SCRATCH,
            strategy=CompactionStrategyType.EXTRACTIVE,
            max_tokens=4000,
            target_tokens=2000,
        )

        result = await self._run_compaction(
            messages=messages,
            config=config,
            thread_id=thread_id,
        )

        summarized = result.get("summarized_messages", [])

        extracted_msgs = [
            msg for msg in summarized
            if "EXTRACTED" in msg.response_metadata.get("section_label", "")
        ]

        if extracted_msgs:
            verify_all_ai_messages(extracted_msgs, "dump strategy extraction")

    # ========================================
    # Hybrid Outputs (3 tests)
    # ========================================

    async def test_hybrid_strategy_produces_ai_messages(self):
        """
        Test: Hybrid strategy produces only AIMessages.

        Both extraction and summarization sections must be AIMessages.
        """
        thread_id = f"test-hybrid-ai-{uuid4()}"
        self.test_thread_ids.append(thread_id)

        messages = generate_token_heavy_messages(count=25, tokens_per_message=300)
        messages = add_linkedin_metadata(messages)

        config = self._create_test_config(
            mode=SummarizationMode.FROM_SCRATCH,
            strategy=CompactionStrategyType.HYBRID,
            max_tokens=6000,
            target_tokens=3000,
        )

        result = await self._run_compaction(
            messages=messages,
            config=config,
            thread_id=thread_id,
        )

        summarized = result.get("summarized_messages", [])

        # Find both extracted and summary messages
        compacted_msgs = [
            msg for msg in summarized
            if any(label in msg.response_metadata.get("section_label", "")
                   for label in ["EXTRACTED", "SUMMARY"])
        ]

        if compacted_msgs:
            # All hybrid outputs must be AIMessages
            verify_all_ai_messages(compacted_msgs, "hybrid strategy output")

            for msg in compacted_msgs:
                self.assertIsInstance(
                    msg, AIMessage,
                    f"Hybrid output must be AIMessage, got {type(msg).__name__}"
                )

    async def test_hybrid_extraction_section_ai_messages(self):
        """
        Test: Hybrid strategy extraction section is AIMessages.
        """
        thread_id = f"test-hybrid-extraction-ai-{uuid4()}"
        self.test_thread_ids.append(thread_id)

        messages = generate_token_heavy_messages(count=20, tokens_per_message=300)
        messages = add_linkedin_metadata(messages)

        config = self._create_test_config(
            mode=SummarizationMode.FROM_SCRATCH,
            strategy=CompactionStrategyType.HYBRID,
            max_tokens=5000,
            target_tokens=2500,
        )

        result = await self._run_compaction(
            messages=messages,
            config=config,
            thread_id=thread_id,
        )

        summarized = result.get("summarized_messages", [])

        extracted_msgs = [
            msg for msg in summarized
            if "EXTRACTED" in msg.response_metadata.get("section_label", "")
        ]

        if extracted_msgs:
            verify_all_ai_messages(extracted_msgs, "hybrid extraction section")

    async def test_hybrid_summary_section_ai_messages(self):
        """
        Test: Hybrid strategy summary section is AIMessages.
        """
        thread_id = f"test-hybrid-summary-ai-{uuid4()}"
        self.test_thread_ids.append(thread_id)

        messages = generate_token_heavy_messages(count=20, tokens_per_message=300)
        messages = add_linkedin_metadata(messages)

        config = self._create_test_config(
            mode=SummarizationMode.FROM_SCRATCH,
            strategy=CompactionStrategyType.HYBRID,
            max_tokens=5000,
            target_tokens=2500,
        )

        result = await self._run_compaction(
            messages=messages,
            config=config,
            thread_id=thread_id,
        )

        summarized = result.get("summarized_messages", [])

        summary_msgs = [
            msg for msg in summarized
            if "SUMMARY" in msg.response_metadata.get("section_label", "")
        ]

        if summary_msgs:
            verify_all_ai_messages(summary_msgs, "hybrid summary section")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
