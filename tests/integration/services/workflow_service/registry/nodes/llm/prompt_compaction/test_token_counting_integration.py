"""
Integration tests for token counting improvements (v2.1).

Tests real token counting with actual APIs:
- OpenAI model-specific tiktoken encoding
- Anthropic API token counting
- Accuracy validation
"""

import unittest
import os
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from workflow_service.registry.nodes.llm.config import ModelMetadata, LLMModelProvider
from workflow_service.registry.nodes.llm.prompt_compaction.token_utils import (
    get_encoder_for_model,
    count_tokens_anthropic,
    count_tokens,
    count_tokens_in_message,
)


class TestOpenAITokenCounting(unittest.TestCase):
    """Test OpenAI token counting with real tiktoken."""

    def test_gpt4o_encoding(self):
        """Should correctly count tokens for gpt-4o."""
        metadata = ModelMetadata(
            provider=LLMModelProvider.OPENAI,
            model_name="gpt-4o",
            context_limit=128000,
            output_token_limit=16384,
        )

        messages = [
            HumanMessage(content="What is the capital of France?"),
            AIMessage(content="The capital of France is Paris."),
        ]

        token_count = count_tokens(messages, metadata)

        # Should return a reasonable count (not mocked)
        self.assertGreater(token_count, 0)
        self.assertLess(token_count, 100)  # These messages are small

    def test_encoder_caching(self):
        """Should cache encoders for performance."""
        metadata = ModelMetadata(
            provider=LLMModelProvider.OPENAI,
            model_name="gpt-4o",
            context_limit=128000,
            output_token_limit=16384,
        )

        encoder1 = get_encoder_for_model(metadata)
        encoder2 = get_encoder_for_model(metadata)

        # Should return same cached instance
        self.assertIs(encoder1, encoder2)


class TestAnthropicTokenCounting(unittest.IsolatedAsyncioTestCase):
    """Test Anthropic API token counting with real API."""

    @unittest.skipIf(not os.getenv("ANTHROPIC_API_KEY"), "Requires ANTHROPIC_API_KEY")
    async def test_anthropic_api_token_counting(self):
        """Should use real Anthropic API for token counting."""
        metadata = ModelMetadata(
            provider=LLMModelProvider.ANTHROPIC,
            model_name="claude-sonnet-4-5-20250929",
            context_limit=200000,
            output_token_limit=8192,
        )

        messages = [
            HumanMessage(content="What is the capital of France?"),
            AIMessage(content="The capital of France is Paris."),
        ]

        token_count = count_tokens_anthropic(messages, metadata)

        # Should return real token count from API
        self.assertIsNotNone(token_count)
        self.assertGreater(token_count, 0)
        self.assertLess(token_count, 100)

    @unittest.skipIf(not os.getenv("ANTHROPIC_API_KEY"), "Requires ANTHROPIC_API_KEY")
    async def test_count_tokens_uses_anthropic_api(self):
        """Should automatically use Anthropic API for Anthropic models."""
        metadata = ModelMetadata(
            provider=LLMModelProvider.ANTHROPIC,
            model_name="claude-sonnet-4",
            context_limit=200000,
            output_token_limit=8192,
        )

        messages = [
            HumanMessage(content="Test message for token counting."),
        ]

        token_count = count_tokens(messages, metadata)

        # Should return real count from Anthropic API
        self.assertIsInstance(token_count, int)
        self.assertGreater(token_count, 0)


class TestTokenCountingAccuracy(unittest.TestCase):
    """Test token counting accuracy with real encoders."""

    def test_empty_messages_returns_zero(self):
        """Should return 0 for empty message list."""
        metadata = ModelMetadata(
            provider=LLMModelProvider.OPENAI,
            model_name="gpt-4o",
            context_limit=128000,
            output_token_limit=16384,
        )

        result = count_tokens([], metadata)
        self.assertEqual(result, 0)

    def test_count_includes_message_overhead(self):
        """Should include proper message formatting overhead."""
        metadata = ModelMetadata(
            provider=LLMModelProvider.OPENAI,
            model_name="gpt-4o",
            context_limit=128000,
            output_token_limit=16384,
        )

        # Single word should still have overhead
        msg = HumanMessage(content="Hello")
        token_count = count_tokens_in_message(msg, metadata)

        # "Hello" is 1 token, but with role/formatting overhead should be >= 4
        self.assertGreaterEqual(token_count, 4)

    def test_longer_messages_count_accurately(self):
        """Should accurately count tokens for longer messages."""
        metadata = ModelMetadata(
            provider=LLMModelProvider.OPENAI,
            model_name="gpt-4o",
            context_limit=128000,
            output_token_limit=16384,
        )

        # Longer message
        content = "This is a longer message with multiple sentences. " * 10
        messages = [HumanMessage(content=content)]

        token_count = count_tokens(messages, metadata)

        # Should be proportional to content length
        self.assertGreater(token_count, 50)
        self.assertLess(token_count, 500)


if __name__ == "__main__":
    unittest.main()
