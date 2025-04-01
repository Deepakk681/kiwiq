from enum import Enum
from typing import Dict, Type, Any, Optional, List, Tuple
from pydantic import BaseModel
import json
from openai import OpenAI
from anthropic import Anthropic

from workflow_service.config.settings import settings

from fireworks.client import Fireworks

from langchain.chat_models import init_chat_model

class EnumWithAttr(Enum):
    """Enum with attributes."""
     
    def __new__(cls, value: Any, metadata: Any):
        member = cls.__new__(cls)
        member._value_ = value
        member.meta = metadata
        return member


class ModelMetadata(BaseModel):
    """Model metadata."""
    verbose_name: str = None
    context_limit: int
    rate_limits: Optional[Dict[str, Any]] = None
    
    # reasoning
    reasoning: bool = False
    reasoning_effort_class: Optional[List[str]] = None
    reasoning_effort_range: Optional[Tuple[int, int]] = (1, 2)
    reasoning_effort_tokens: bool = False
    
    streaming: bool = True
    tool_use: bool = True
    structured_output: bool = True

    multimodal: bool = False

    # price computed by tokencost library
    # price: Optional[Dict[str, float]] = None


GLOBAL_DEFAULT_METADATA = ModelMetadata(
        context_limit=100,
        rate_limits={
            "prompt_tokens": 100000,
            "completion_tokens": 100000,
            "total_tokens": 100000
        }
    )


class OpenAIModels(str, EnumWithAttr):
    """OpenAI model options."""
    _ignore_ = ["DEFAULT_METADATA"]
    DEFAULT_METADATA = ModelMetadata(
        context_limit=100,
        rate_limits={
            "prompt_tokens": 100000,
            "completion_tokens": 100000,
            "total_tokens": 100000
        }
    )

    O3_MINI = "o3-mini", ModelMetadata(**(DEFAULT_METADATA.model_dump() | {"context_limit": 100000}))
    GPT_4_5 = "gpt-4.5-preview", DEFAULT_METADATA
    GPT_4o = "gpt-4o", DEFAULT_METADATA
    GPT_4o_mini = "gpt-4o-mini", DEFAULT_METADATA
    O1_MINI = "o1-mini", DEFAULT_METADATA
    O1 = "o1", DEFAULT_METADATA
    # NOTE: O1-pro available via Requests API!


class AnthropicModels(str, EnumWithAttr):
    """Anthropic model options."""
    CLAUDE_3_7_SONNET = "claude-3-7-sonnet-20250219", GLOBAL_DEFAULT_METADATA
    CLAUDE_3_5_SONNET = "claude-3-5-sonnet-20241022", GLOBAL_DEFAULT_METADATA
    CLAUDE_3_5_HAIKU = "claude-3-5-haiku-20241022", GLOBAL_DEFAULT_METADATA
    CLAUDE_3_OPUS = "claude-3-opus-20240229", GLOBAL_DEFAULT_METADATA


class GeminiModels(str, EnumWithAttr):
    """Google Gemini model options."""
    GEMINI_2_5_PRO_EXP = "gemini-2.5-pro-exp-03-25", GLOBAL_DEFAULT_METADATA  # Enhanced thinking and reasoning, multimodal understanding, advanced coding
    GEMINI_2_0_FLASH = "gemini-2.0-flash", GLOBAL_DEFAULT_METADATA  # Next generation features, speed, thinking, realtime streaming, and multimodal generation
    GEMINI_2_0_FLASH_THINKING_EXP = "gemini-2.0-flash-thinking-exp-01-21", GLOBAL_DEFAULT_METADATA  # Experiment Thinking!
    GEMINI_2_0_FLASH_LITE = "gemini-2.0-flash-lite", GLOBAL_DEFAULT_METADATA  # Cost efficiency and low latency
    GEMINI_1_5_PRO = "gemini-1.5-pro", GLOBAL_DEFAULT_METADATA  # Long context window model with strong multimodal capabilities


class FireworksModels(str, EnumWithAttr):
    """Fireworks model options.
    Eg Output:
    content='<think>\nOkay, the user wrote "Hello, world!" That\'s a classic first program in many programming languages. Maybe they\'re just testing the response or starting to learn coding. I should acknowledge their message and offer help. Let me think of a friendly reply that invites them to ask questions or seek assistance.\n\nI should keep it simple and welcoming. Perhaps mention common uses of "Hello, world!" and ask if they need help with something specific. Make sure to encourage them to reach out if they have any questions. Avoid technical jargon unless they ask for it. Yeah, that sounds good.\n</think>\n\nHello, world! 👋 It looks like you\'re testing things out or maybe starting your journey into programming! If you have a question, need help with code, or want to explore a topic, feel free to ask. How can I assist you today? 😊' additional_kwargs={} response_metadata={'token_usage': {'prompt_tokens': 7, 'total_tokens': 184, 'completion_tokens': 177}, 'model_name': 'accounts/fireworks/models/deepseek-r1-basic', 'system_fingerprint': '', 'finish_reason': 'stop', 'logprobs': None} id='run-8c46e535-4545-4c9b-87c6-fec1c2ee9b39-0' usage_metadata={'input_tokens': 7, 'output_tokens': 177, 'total_tokens': 184}
    """
    DEEPSEEK_R1_FAST = "accounts/fireworks/models/deepseek-r1", GLOBAL_DEFAULT_METADATA
    DEEPSEEK_R1_BASIC = "accounts/fireworks/models/deepseek-r1-basic", GLOBAL_DEFAULT_METADATA  # NOTE: this faces a lot of server errors!!


class AWSBedrockModels(str, EnumWithAttr):
    """Bedrock Converse model options."""
    DEEPSEEK_R1 = "us.deepseek.r1-v1:0", GLOBAL_DEFAULT_METADATA
    # init_chat_model(model="us.deepseek.r1-v1:0", model_provider="bedrock_converse", aws_secret_access_key=settings.AWS_BEDROCK_SECRET_ACCESS_KEY, aws_access_key_id=settings.AWS_BEDROCK_ACCESS_KEY_ID, region_name="us-east-1")


AWS_REGION = "us-east-1"


class LLMModelProvider(str, Enum):
    """Supported model providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "google_genai"
    FIREWORKS = "fireworks"
    AWS_BEDROCK = "bedrock_converse"

PROVIDER_MODEL_MAP: Dict[LLMModelProvider, Type[Enum]] = {
    LLMModelProvider.OPENAI: OpenAIModels,
    LLMModelProvider.ANTHROPIC: AnthropicModels,
    LLMModelProvider.GEMINI: GeminiModels,
    LLMModelProvider.FIREWORKS: FireworksModels,
    LLMModelProvider.AWS_BEDROCK: AWSBedrockModels
}


def list_models(provider: LLMModelProvider):
    if provider == LLMModelProvider.ANTHROPIC:
        client = Anthropic(
            api_key=settings.ANTHROPIC_API_KEY,
        )
        models = client.models.list()
        print(json.dumps([model.id for model in models], indent=4))
    elif provider == LLMModelProvider.OPENAI:
        client = OpenAI(
            api_key = settings.OPENAI_API_KEY
        )
        models = client.models.list()
        print(json.dumps([model.id for model in models], indent=4))
    else:
        raise NotImplementedError("Gemini models are not supported in this context")
    return models
