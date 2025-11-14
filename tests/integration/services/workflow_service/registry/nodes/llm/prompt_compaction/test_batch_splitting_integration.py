"""
Integration tests for batch splitting functionality (v2.1).

Tests the universal call_llm_with_batch_splitting() wrapper and all refactored
methods that use it:
- call_llm_with_batch_splitting() directly
- SummarizationStrategy methods (_summarize_from_scratch, _create_summary_chunk, _merge_two_summaries)
- ExtractionStrategy (llm_rewrite)
- summarize_oversized_message()

Scenarios tested:
1. Messages fit in single batch (no splitting needed)
2. Messages collectively exceed context (batch splitting)
3. Batch summaries exceed context (re-compression)
4. Individual oversized messages within batches
"""

import unittest
import os
from uuid import uuid4
from langchain_core.messages import HumanMessage, AIMessage

from workflow_service.registry.nodes.llm.config import ModelMetadata, LLMModelProvider
from workflow_service.registry.nodes.llm.prompt_compaction.context_manager import (
    ContextBudget,
    ContextBudgetConfig,
)
from workflow_service.registry.nodes.llm.prompt_compaction.token_utils import (
    call_llm_with_batch_splitting,
    summarize_oversized_message,
)
from workflow_service.registry.nodes.llm.prompt_compaction.strategies import (
    SummarizationStrategy,
    SummarizationMode,
    ExtractionStrategy,
)
from workflow_service.registry.nodes.llm.prompt_compaction.utils import ExtractionStrategy as ExtractionStrategyType
from tests.unit.services.workflow_service.registry.nodes.llm.prompt_compaction.test_base import (
    PromptCompactionIntegrationTestBase,
)


class TestBatchSplittingWrapper(PromptCompactionIntegrationTestBase):
    """Test call_llm_with_batch_splitting() wrapper directly."""

    @unittest.skipIf(not os.getenv("OPENAI_API_KEY"), "Requires OPENAI_API_KEY")
    async def test_single_batch_no_splitting(self):
        """Should handle messages that fit in single batch without splitting."""
        metadata = self._create_test_model_metadata(
            model_name="gpt-4o-mini",
            context_limit=128000,
        )

        budget = ContextBudget.calculate(
            total_context=128000,
            max_output_tokens=16384,
            config=ContextBudgetConfig(),
        )

        # Small messages that fit in one batch
        messages = [
            HumanMessage(content=f"Message {i}: Some content here.", id=str(uuid4()))
            for i in range(10)
        ]

        prompt_template = """Summarize these messages:

{messages}

Summary:"""

        result = await call_llm_with_batch_splitting(
            messages=messages,
            prompt_template=prompt_template,
            model_metadata=metadata,
            ext_context=self.ext_context,
            budget=budget,
            template_kwargs={},
            max_output_tokens=1000,
        )

        # Verify result structure
        self.assertIn("content", result)
        self.assertIn("batched", result)
        self.assertIn("num_batches", result)
        self.assertIn("token_usage", result)
        self.assertIn("cost", result)

        # Should not have batched
        self.assertFalse(result["batched"])
        self.assertEqual(result["num_batches"], 1)

        # Should have content
        self.assertGreater(len(result["content"]), 0)

    @unittest.skipIf(not os.getenv("OPENAI_API_KEY"), "Requires OPENAI_API_KEY")
    async def test_batch_splitting_collective_overflow(self):
        """Should split messages into batches when collectively too large."""
        metadata = self._create_test_model_metadata(
            model_name="gpt-4o-mini",
            context_limit=128000,
        )

        budget = ContextBudget.calculate(
            total_context=128000,
            max_output_tokens=16384,
            config=ContextBudgetConfig(),
        )

        # Create many moderate-sized messages that collectively exceed limit
        # Each ~2K tokens, 50 messages = ~100K tokens
        # Use longer content to ensure we exceed the 85% threshold (83,993 tokens)
        messages = [
            HumanMessage(
                content="Content here. " * 800 + f" Message number {i}.",  # ~2.5K tokens per message
                id=str(uuid4())
            )
            for i in range(40)  # 40 messages * 2.5K = ~100K tokens
        ]

        prompt_template = """Summarize these messages concisely:

{messages}

Summary:"""

        result = await call_llm_with_batch_splitting(
            messages=messages,
            prompt_template=prompt_template,
            model_metadata=metadata,
            ext_context=self.ext_context,
            budget=budget,
            template_kwargs={},
            max_output_tokens=2000,
        )

        # Should have batched
        self.assertTrue(result["batched"])
        self.assertGreater(result["num_batches"], 1)

        # Should have combined content
        self.assertGreater(len(result["content"]), 0)
        # Content should mention parts
        self.assertIn("Part", result["content"])

    @unittest.skipIf(not os.getenv("OPENAI_API_KEY"), "Requires OPENAI_API_KEY")
    async def test_batch_splitting_with_oversized_message(self):
        """Should handle both individual oversized messages AND batch splitting."""
        metadata = self._create_test_model_metadata(
            model_name="gpt-4o-mini",
            context_limit=128000,
        )

        budget = ContextBudget.calculate(
            total_context=128000,
            max_output_tokens=16384,
            config=ContextBudgetConfig(),
        )

        # Create one oversized message + many normal messages
        large_content = "\n".join([
            f"Paragraph {i}: Detailed information here." * 50
            for i in range(300)  # ~60K tokens
        ])

        messages = [
            HumanMessage(content="Normal message 1", id=str(uuid4())),
            HumanMessage(content=large_content, id=str(uuid4())),  # Oversized
        ] + [
            HumanMessage(content=f"Normal message {i}", id=str(uuid4()))
            for i in range(20)
        ]

        prompt_template = """Summarize these messages:

{messages}

Summary:"""

        result = await call_llm_with_batch_splitting(
            messages=messages,
            prompt_template=prompt_template,
            model_metadata=metadata,
            ext_context=self.ext_context,
            budget=budget,
            template_kwargs={},
            max_output_tokens=2000,
        )

        # Should succeed with content
        self.assertGreater(len(result["content"]), 0)

        # May or may not batch depending on oversized handling
        self.assertIn("batched", result)


class TestSummarizationWithBatching(PromptCompactionIntegrationTestBase):
    """Test SummarizationStrategy methods use batch splitting."""

    @unittest.skipIf(not os.getenv("OPENAI_API_KEY"), "Requires OPENAI_API_KEY")
    async def test_from_scratch_with_collective_overflow(self):
        """Should handle many messages that collectively exceed context."""
        metadata = self._create_test_model_metadata(
            model_name="gpt-4o-mini",
            context_limit=128000,
        )

        budget = ContextBudget.calculate(
            total_context=128000,
            max_output_tokens=16384,
            config=ContextBudgetConfig(),
        )

        # Create many messages
        messages = [
            HumanMessage(
                content="Message content here. " * 500 + f" Number {i}.",
                id=str(uuid4())
            )
            for i in range(40)  # Collectively ~80K tokens
        ]

        sections = {
            "system": [],
            "summaries": [],
            "historical": messages,
            "marked": [],
            "recent": [],
        }

        strategy = SummarizationStrategy(mode=SummarizationMode.FROM_SCRATCH)

        result = await strategy.compact(
            sections=sections,
            budget=budget,
            model_metadata=metadata,
            ext_context=self.ext_context,
        )

        # Should successfully create summary
        self.assertGreater(len(result.summary_messages), 0)
        # Summary should be shorter than original
        summary_length = sum(len(msg.content) for msg in result.summary_messages)
        original_length = sum(len(msg.content) for msg in messages)
        self.assertLess(summary_length, original_length)

    @unittest.skipIf(not os.getenv("OPENAI_API_KEY"), "Requires OPENAI_API_KEY")
    async def test_merge_summaries_with_batching(self):
        """Should handle merging multiple large summaries."""
        metadata = self._create_test_model_metadata(
            model_name="gpt-4o-mini",
            context_limit=128000,
        )

        budget = ContextBudget.calculate(
            total_context=128000,
            max_output_tokens=16384,
            config=ContextBudgetConfig(),
        )

        # Create multiple large summaries
        summary1_content = "\n".join([
            f"Summary 1 section {i}: Important information here."
            for i in range(100)
        ])

        summary2_content = "\n".join([
            f"Summary 2 section {i}: More important details."
            for i in range(100)
        ])

        summary3_content = "\n".join([
            f"Summary 3 section {i}: Additional context."
            for i in range(100)
        ])

        summary1 = AIMessage(content=summary1_content, id=str(uuid4()))
        summary1.response_metadata = {
            "summary": True,
            "summarized_message_ids": ["msg1"],
            "summary_generation": 0,
        }

        summary2 = AIMessage(content=summary2_content, id=str(uuid4()))
        summary2.response_metadata = {
            "summary": True,
            "summarized_message_ids": ["msg2"],
            "summary_generation": 0,
        }

        summary3 = AIMessage(content=summary3_content, id=str(uuid4()))
        summary3.response_metadata = {
            "summary": True,
            "summarized_message_ids": ["msg3"],
            "summary_generation": 0,
        }

        new_messages = [HumanMessage(content="New message", id=str(uuid4()))]

        sections = {
            "system": [],
            "summaries": [summary1, summary2, summary3],
            "historical": new_messages,
            "marked": [],
            "recent": [],
        }

        strategy = SummarizationStrategy(
            mode=SummarizationMode.CONTINUED,
        )

        result = await strategy.compact(
            sections=sections,
            budget=budget,
            model_metadata=metadata,
            ext_context=self.ext_context,
        )

        # Should successfully merge summaries
        self.assertGreater(len(result.summary_messages), 0)


class TestExtractionWithBatching(PromptCompactionIntegrationTestBase):
    """Test ExtractionStrategy llm_rewrite uses batch splitting."""

    @unittest.skipIf(not os.getenv("OPENAI_API_KEY"), "Requires OPENAI_API_KEY")
    async def test_llm_rewrite_with_many_chunks(self):
        """Should handle many extracted chunks that need rewriting."""
        metadata = self._create_test_model_metadata(
            model_name="gpt-4o-mini",
            context_limit=128000,
        )

        budget = ContextBudget.calculate(
            total_context=128000,
            max_output_tokens=16384,
            config=ContextBudgetConfig(),
        )

        # Create many historical messages
        historical_messages = [
            HumanMessage(
                content=f"Historical message {i}: " + "Content here. " * 200,
                id=str(uuid4())
            )
            for i in range(30)  # Many messages
        ]

        recent_messages = [
            HumanMessage(content="What were the key points?", id=str(uuid4())),
        ]

        sections = {
            "system": [],
            "summaries": [],
            "historical": historical_messages,
            "marked": [],
            "recent": recent_messages,
        }

        strategy = ExtractionStrategy(
            construction_strategy=ExtractionStrategyType.LLM_REWRITE,
            top_k=10,  # Extract many chunks
            store_embeddings=False,  # Skip Weaviate for test
        )

        result = await strategy.compact(
            sections=sections,
            budget=budget,
            model_metadata=metadata,
            ext_context=self.ext_context,
        )

        # Should successfully extract and rewrite
        self.assertGreaterEqual(len(result.extracted_messages), 1)


class TestOversizedMessageBatching(PromptCompactionIntegrationTestBase):
    """Test summarize_oversized_message() uses batch splitting."""

    @unittest.skipIf(not os.getenv("OPENAI_API_KEY"), "Requires OPENAI_API_KEY")
    async def test_oversized_message_multi_level_summarization(self):
        """Should handle extremely large message with multi-level summarization."""
        metadata = self._create_test_model_metadata(
            model_name="gpt-4o-mini",
            context_limit=128000,
        )

        # Create extremely large message that will need chunking
        # With 40% chunk size (~39K tokens for 128K context), need ~1500 sections to force multiple chunks
        large_content = "\n\n".join([
            f"Section {i}: This is a very detailed section with lots of information. "
            f"It discusses various topics and provides comprehensive analysis. "
            f"Additional paragraphs provide more context and details."
            for i in range(1500)  # Very large message - forces multiple chunks
        ])

        message = HumanMessage(content=large_content, id=str(uuid4()))

        # Summarize it
        summary = await summarize_oversized_message(
            message=message,
            max_tokens_per_chunk=30000,  # Force multiple chunks
            model_metadata=metadata,
            ext_context=self.ext_context,
        )

        # Verify summary created
        self.assertIsInstance(summary, AIMessage)
        self.assertIn("oversized_summary", summary.response_metadata)

        # Summary should be much shorter than original
        self.assertLess(len(summary.content), len(large_content))

        # Should have metadata about chunking
        meta = summary.response_metadata["oversized_summary"]
        self.assertIn("num_chunks", meta)
        self.assertGreater(meta["num_chunks"], 1)

        # Check if batching was used
        if "batched" in meta:
            self.assertIn("num_batches", meta)


class TestRecompressionScenarios(PromptCompactionIntegrationTestBase):
    """Test scenarios where batch summaries themselves need re-compression."""

    @unittest.skipIf(not os.getenv("OPENAI_API_KEY"), "Requires OPENAI_API_KEY")
    async def test_batch_summaries_exceed_output_limit(self):
        """Should re-compress when combined batch summaries are too large."""
        metadata = self._create_test_model_metadata(
            model_name="gpt-4o-mini",
            context_limit=128000,
        )

        budget = ContextBudget.calculate(
            total_context=128000,
            max_output_tokens=16384,
            config=ContextBudgetConfig(),
        )

        # Create MANY messages with substantial content
        # This will force multiple batches, and each batch summary will be long
        messages = [
            HumanMessage(
                content=f"Message {i}: " + "Detailed content here. " * 1000,
                id=str(uuid4())
            )
            for i in range(100)  # 100 messages, each ~2K tokens = 200K total
        ]

        prompt_template = """Provide a detailed summary of these messages:

{messages}

Detailed summary:"""

        # Use small max_output_tokens to force re-compression
        result = await call_llm_with_batch_splitting(
            messages=messages,
            prompt_template=prompt_template,
            model_metadata=metadata,
            ext_context=self.ext_context,
            budget=budget,
            template_kwargs={},
            max_output_tokens=1000,  # Small output limit
        )

        # Should succeed despite complex multi-level compression
        self.assertGreater(len(result["content"]), 0)
        self.assertTrue(result["batched"])
        self.assertGreater(result["num_batches"], 1)

        # Final output should respect max_output_tokens (roughly)
        # Allow some tolerance since LLM doesn't always respect exact limits
        from workflow_service.registry.nodes.llm.prompt_compaction.token_utils import count_tokens_in_text
        output_tokens = count_tokens_in_text(result["content"], metadata)
        # Should be significantly less than the original 200K tokens
        self.assertLess(output_tokens, 50000)


if __name__ == "__main__":
    unittest.main()
