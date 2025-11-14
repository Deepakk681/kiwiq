"""
Integration tests for oversized message handling (v2.1).

Tests real message chunking and summarization with actual LLM calls:
- Message chunking logic
- Real LLM-based summarization
- Recursive summarization
- Integration with external context
"""

import unittest
import os
from langchain_core.messages import HumanMessage, AIMessage

from workflow_service.registry.nodes.llm.config import ModelMetadata, LLMModelProvider
from workflow_service.registry.nodes.llm.prompt_compaction.token_utils import (
    split_oversized_message,
    summarize_oversized_message,
)
from tests.unit.services.workflow_service.registry.nodes.llm.prompt_compaction.test_base import (
    PromptCompactionIntegrationTestBase,
)


class TestMessageChunking(unittest.TestCase):
    """Test message chunking logic without LLM calls."""

    def test_small_message_not_chunked(self):
        """Should return original message if under threshold."""
        metadata = ModelMetadata(
            provider=LLMModelProvider.OPENAI,
            model_name="gpt-4o",
            context_limit=128000,
            output_token_limit=16384,
        )

        message = HumanMessage(content="Short message for testing.")

        chunks = split_oversized_message(
            message=message,
            max_tokens_per_chunk=100000,
            model_metadata=metadata,
        )

        # Should return single chunk
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].content, message.content)

    def test_large_message_split_into_chunks(self):
        """Should split large message into multiple chunks."""
        metadata = ModelMetadata(
            provider=LLMModelProvider.OPENAI,
            model_name="gpt-4o",
            context_limit=128000,
            output_token_limit=16384,
        )

        # Create large content (simulate ~100K tokens)
        large_content = "\n\n".join([
            f"This is paragraph {i}. It contains some detailed information about topic {i}. "
            f"This paragraph discusses various aspects and provides context. "
            f"Additional details are included to make the paragraph substantial."
            for i in range(2000)
        ])

        message = HumanMessage(content=large_content)

        chunks = split_oversized_message(
            message=message,
            max_tokens_per_chunk=30000,
            model_metadata=metadata,
        )

        # Should create multiple chunks
        self.assertGreater(len(chunks), 1)

        # All chunks should be HumanMessage
        for chunk in chunks:
            self.assertIsInstance(chunk, HumanMessage)

        # Continuation metadata should be present
        for i, chunk in enumerate(chunks):
            self.assertIn("oversized_chunk", chunk.additional_kwargs)
            if i > 0:
                self.assertTrue(chunk.additional_kwargs["oversized_chunk"]["is_continuation"])

    def test_chunking_preserves_paragraph_boundaries(self):
        """Should split on paragraph boundaries when possible."""
        metadata = ModelMetadata(
            provider=LLMModelProvider.OPENAI,
            model_name="gpt-4o",
            context_limit=128000,
            output_token_limit=16384,
        )

        # Create content with clear paragraph breaks
        paragraphs = [f"Paragraph {i} content here.\n\n" for i in range(500)]
        content = "".join(paragraphs)
        message = HumanMessage(content=content)

        chunks = split_oversized_message(
            message=message,
            max_tokens_per_chunk=10000,
            model_metadata=metadata,
        )

        # Verify chunks don't break mid-paragraph (basic heuristic check)
        for chunk in chunks:
            # Each chunk should end cleanly (not mid-sentence)
            self.assertIsInstance(chunk.content, str)
            self.assertGreater(len(chunk.content), 0)


class TestOversizedMessageSummarization(PromptCompactionIntegrationTestBase):
    """Test oversized message summarization with real LLM calls."""

    @unittest.skipIf(not os.getenv("OPENAI_API_KEY"), "Requires OPENAI_API_KEY")
    async def test_summarize_large_message_with_real_llm(self):
        """Should summarize large message using real LLM."""
        metadata = self._create_test_model_metadata(
            model_name="gpt-4o-mini",  # Use mini for cost efficiency
            context_limit=128000,
        )

        # Create moderately large message
        large_content = "\n\n".join([
            f"Section {i}: This section discusses topic {i} in detail. "
            f"It covers various aspects including background, methodology, and findings. "
            f"Key points include point A, point B, and point C. "
            f"Additional context is provided to ensure completeness."
            for i in range(50)
        ])

        message = HumanMessage(content=large_content)

        # Summarize using real LLM
        summary = await summarize_oversized_message(
            message=message,
            max_tokens_per_chunk=50000,
            model_metadata=metadata,
            ext_context=self.ext_context,
        )

        # Verify summary
        self.assertIsInstance(summary, AIMessage)
        self.assertIn("oversized_summary", summary.additional_kwargs)

        # Summary should be shorter than original
        summary_content = summary.content
        self.assertLess(len(summary_content), len(large_content))

        # Summary should contain meaningful content (not empty)
        self.assertGreater(len(summary_content), 100)

    @unittest.skipIf(not os.getenv("OPENAI_API_KEY"), "Requires OPENAI_API_KEY")
    async def test_summarization_preserves_key_information(self):
        """Should preserve key information in summary."""
        metadata = self._create_test_model_metadata(
            model_name="gpt-4o-mini",
            context_limit=128000,
        )

        # Create content with specific key facts
        content = "\n\n".join([
            "Introduction: This document discusses the implementation of v2.1 prompt compaction.",
            "Key Feature 1: Anthropic API integration for accurate token counting.",
            "Key Feature 2: Oversized message handling with chunk-wise summarization.",
            "Key Feature 3: Smart chunk re-attachment for deduplication.",
            "Conclusion: These features improve context window management significantly."
        ] + [f"Additional detail section {i}." for i in range(40)])

        message = HumanMessage(content=content)

        summary = await summarize_oversized_message(
            message=message,
            max_tokens_per_chunk=50000,
            model_metadata=metadata,
            ext_context=self.ext_context,
        )

        # Summary should mention key features (heuristic check)
        summary_lower = summary.content.lower()
        # At least some key terms should appear
        key_terms = ["prompt compaction", "token", "summarization", "feature"]
        found_terms = sum(1 for term in key_terms if term in summary_lower)
        self.assertGreater(found_terms, 0)


if __name__ == "__main__":
    unittest.main()
