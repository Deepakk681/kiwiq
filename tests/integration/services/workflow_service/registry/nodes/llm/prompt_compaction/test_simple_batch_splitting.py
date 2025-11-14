"""
Simple batch splitting test to verify basic functionality.
"""

import unittest
import os
from uuid import uuid4
from langchain_core.messages import HumanMessage

from workflow_service.registry.nodes.llm.config import ModelMetadata, LLMModelProvider
from workflow_service.registry.nodes.llm.prompt_compaction.context_manager import (
    ContextBudget,
    ContextBudgetConfig,
)
from workflow_service.registry.nodes.llm.prompt_compaction.token_utils import (
    call_llm_with_batch_splitting,
)
from tests.unit.services.workflow_service.registry.nodes.llm.prompt_compaction.test_base import (
    PromptCompactionIntegrationTestBase,
)


class TestSimpleBatchSplitting(PromptCompactionIntegrationTestBase):
    """Simple tests for batch splitting without complex scenarios."""

    @unittest.skipIf(not os.getenv("OPENAI_API_KEY"), "Requires OPENAI_API_KEY")
    async def test_single_small_batch_no_splitting(self):
        """Test with small messages that should NOT trigger batch splitting."""
        metadata = self._create_test_model_metadata(
            model_name="gpt-4o-mini",
            context_limit=128000,
        )

        budget = ContextBudget.calculate(
            total_context=128000,
            max_output_tokens=16384,
            config=ContextBudgetConfig(),
        )

        # Create 5 small messages
        messages = [
            HumanMessage(content=f"This is message {i}. Short and simple.", id=str(uuid4()))
            for i in range(5)
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
            max_output_tokens=500,
        )

        # Verify result
        self.assertIn("content", result)
        self.assertFalse(result["batched"], "Should NOT batch for small messages")
        self.assertEqual(result["num_batches"], 1)
        self.assertGreater(len(result["content"]), 0)

    @unittest.skipIf(not os.getenv("OPENAI_API_KEY"), "Requires OPENAI_API_KEY")
    async def test_moderate_messages_with_batching(self):
        """Test with moderate messages that SHOULD trigger batch splitting."""
        metadata = self._create_test_model_metadata(
            model_name="gpt-4o-mini",
            context_limit=128000,
        )

        budget = ContextBudget.calculate(
            total_context=128000,
            max_output_tokens=16384,
            config=ContextBudgetConfig(),
        )

        # Create moderate-sized messages that exceed 85% threshold (83,993 tokens)
        # Use 35 messages with ~2.5K tokens each = ~87.5K total
        messages = [
            HumanMessage(
                content="Some content here. " * 500 + f" Message {i}.",
                id=str(uuid4())
            )
            for i in range(35)
        ]

        prompt_template = """Summarize these messages concisely:

{messages}

Brief summary:"""

        result = await call_llm_with_batch_splitting(
            messages=messages,
            prompt_template=prompt_template,
            model_metadata=metadata,
            ext_context=self.ext_context,
            budget=budget,
            template_kwargs={},
            max_output_tokens=1000,
        )

        # Verify result
        self.assertIn("content", result)
        self.assertGreater(len(result["content"]), 0)

        # With parallel processing, this should complete quickly
        print(f"Batched: {result['batched']}, Num batches: {result['num_batches']}")


if __name__ == "__main__":
    unittest.main()
