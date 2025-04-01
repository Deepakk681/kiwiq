"""
LLM Node using LangChain.

This module provides a LangChain-based LLM node implementation that supports multiple
model providers (OpenAI, Anthropic, Gemini) with structured output and tool calling.
"""
import json
import os
from enum import Enum
import time
from typing import Any, ClassVar, Dict, List, Optional, Type, Union, Literal

from pydantic import Field, field_validator
from pydantic import ConfigDict

from anthropic import Anthropic
from openai import OpenAI

from langchain_core.messages import (
    AIMessage, 
    HumanMessage, 
    SystemMessage, 
    ToolMessage,
    AnyMessage
)
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.tools import BaseTool
from langchain_core.runnables import Runnable
from langchain.chat_models import init_chat_model

from workflow_service.registry.registry import MockRegistry
from workflow_service.registry.nodes.core.base import BaseNode, BaseSchema
from workflow_service.registry.nodes.core.dynamic_nodes import ConstructDynamicSchema
from workflow_service.registry.nodes.llm.config import LLMModelProvider, PROVIDER_MODEL_MAP, AnthropicModels
from workflow_service.registry.schemas.base import create_dynamic_schema_with_fields


class MessageType(str, Enum):
    """Message types."""
    HUMAN = "human"
    AI = "ai"
    SYSTEM = "system"
    TOOL = "tool"


###########################
###### Input Schema ######
###########################

class LLMNodeInputSchema(BaseSchema):
    """Input schema for the LLM node."""
    # Messages input
    messages_history: List[AnyMessage] = Field(
        default_factory=list, 
        description="List of messages history in the conversation. Each message must have 'type' and 'content' keys."
    )
    user_prompt: Optional[str] = Field(
        None, 
        description="Simple text user prompt (alternative to messages). Will be converted to a HumanMessage."
    )
    system_prompt: Optional[str] = Field(
        None, 
        description="System message to prepend to the conversation if using prompt."
    )
    tool_outputs: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Dict of tool outputs to append to the conversation. Each tool output must have 'tool_name' and 'output' keys."
    )
###########################


###########################
###### Output Schema ######
###########################

class LLMMetadata(BaseSchema):
    """Metadata about the LLM response including token usage."""
    model_name: str = Field(description="Model name used for generation")
    token_usage: Dict[str, int] = Field(description="Token usage statistics. Input, Output, Thinking, Cached tokens.")
    # thinking_tokens: Optional[int] = Field(None, description="Number of thinking tokens (for models that support it)")
    finish_reason: Optional[str] = Field(None, description="Reason for finish (e.g., 'stop', 'length', 'tool_calls')")
    latency: Optional[float] = Field(None, description="Latency in seconds")
    cached: bool = Field(default=False, description="Whether the response was cached")


class ToolCall(BaseSchema):
    """Represents a tool call made by the model."""
    tool_name: str = Field(description="Name of the tool called")
    tool_input: Dict[str, Any] = Field(description="Input provided to the tool")
    tool_id: Optional[str] = Field(None, description="ID of the tool call (used by some providers)")


class LLMNodeOutputSchema(BaseSchema):
    """Output schema for the LLM node."""
    # content: str = Field(description="Text content of the response")
    metadata: LLMMetadata = Field(description="Metadata about the response")
    
    messages: List[AnyMessage] = Field(description="Updated message history with the new response")
    raw_response: Dict[str, Any] = Field(description="Raw response from the provider")
    # For structured output
    structured_output: Optional[Dict[str, Any]] = Field(
        None, 
        description="Structured output parsed from the response (if output_format was structured)"
    )
    # For tool calling
    tool_calls: Optional[List[ToolCall]] = Field(
        None,
        description="Tool calls made by the model (if any)"
    )
###########################


###########################
###### Config Schema ######
###########################


class ModelSpec(BaseSchema):
    """Combined model specification with provider and model name."""
    provider: LLMModelProvider = Field(
        default=LLMModelProvider.ANTHROPIC,
        description="The model provider to use"
    )
    model: str = Field(  # str  OR   OpenAIModels | AnthropicModels
        default=AnthropicModels.CLAUDE_3_7_SONNET.value,
        description="The model name to use"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            # "examples": [
            #     {"provider": "openai", "model": "gpt-4-turbo"},
            #     {"provider": "anthropic", "model": "claude-3-5-sonnet-20240620"},
            #     {"provider": "google_genai", "model": "gemini-2.0-flash"}
            # ],
            "allOf": [
                {
                    "if": {
                        "properties": {"provider": {"const": provider.value}}
                    },
                    "then": {
                        "properties": {
                            "model": {
                                "enum": [e.value for e in model_enum]
                            }
                        }
                    }
                }
                for provider, model_enum in PROVIDER_MODEL_MAP.items()
            ]
        }
    )
    
    @field_validator('model')
    def validate_model_for_provider(cls, v, info):
        """Validate that the model is appropriate for the selected provider."""
        provider = info.data.get('provider')
        
        # If no provider specified, we can't validate
        if not provider:
            return v
        
        # Get the model enum class for the specified provider
        if provider in PROVIDER_MODEL_MAP:
            model_enum = PROVIDER_MODEL_MAP[provider]
            valid_models = [e.value for e in model_enum]
            
            # Define prefix checks for each provider to allow custom models
            # prefix_checks = {
            #     ModelProvider.OPENAI: "gpt-",
            #     ModelProvider.ANTHROPIC: "claude-",
            #     ModelProvider.GEMINI: "gemini-",
            #     ModelProvider.FIREWORKS: "accounts/fireworks/models/"
            # }
            
            # Check if model is in the enum values or starts with the appropriate prefix
            # prefix = prefix_checks.get(provider, "")
            if v not in valid_models:  #  and not (prefix and v.startswith(prefix)):
                raise ValueError(f"Model '{v}' is not a valid {provider.value} model")
                
        return v


class SchemaFromRegistryConfig(BaseSchema):
    """Schema configuration."""
    schema_name: str = Field(description="Schema Unique name")
    schema_version: Optional[str] = Field(None, description="Schema version")


class LLMStructuredOutputSchema(BaseSchema):
    """Output format types."""
    schema_from_registry: Optional[SchemaFromRegistryConfig] = Field(None, description="Output schema from registry")
    # NOTE: if both are specified, fields from dynamic schema spec will overwrite fields from the schema from registry if same field name, 
    #     otherwise all schema from registry fields will be added to the dynamic schema, aside from new fields from the spec!
    dynamic_schema_spec: Optional[ConstructDynamicSchema] = Field(None, description="Dynamic Schema specification for the output")

    def is_output_str(self):
        return self.schema_from_registry is None and self.dynamic_schema_spec is None

    def get_schema(self, registry: MockRegistry = None, built_schema_name = None):
        """
        Get schema config from registry

        NOTE: dynamic schema spec ovewrite fields from registry schema
        """
        schema = None
        if self.schema_from_registry:
            assert registry is not None, "Registry must be provided if schema_from_registry is used"
            schema = registry.get_schema(self.schema_from_registry.schema_name, self.schema_from_registry.schema_version)
        if self.dynamic_schema_spec:
            dynamic_schema = self.dynamic_schema_spec.build_schema(schema_name=built_schema_name)
            if schema is not None:
                original_schema_fields = {k:None for k in schema.model_fields.keys()}
                for field_name, field_def in dynamic_schema.model_fields.items():
                    original_schema_fields[field_name] = (field_def.annotation, field_def)
                schema = create_dynamic_schema_with_fields(schema, fields=original_schema_fields)
            else:
                schema = dynamic_schema
        else:
            raise ValueError("No schema config provided")
        return schema


class ToolConfig(BaseSchema):
    """Configuration for a tool. (Pulled from ToolRegistry)
    NOTE: this tool is configured in the tool caller node and it has the config default / set by user. 
    This config in LLM node only receives input_overwrites so that it can determine which parts of the input schema go into the tool call.
    IMPORTANT NOTE: A tool node should have a verbose, descriptive input schema btw!
    """
    tool_name: str = Field(description="Tool name")
    version: Optional[str] = Field(None, description="Tool version")
    input_overwrites: Optional[Dict[str, Any]] = Field(None, description="Input overwrites for the tool. These fields are not passed to the LLM and are not filled!")
    additional_fields: Optional[ConstructDynamicSchema] = Field(None, description="Additional fields for the tool. They could contain additional config fields for the tool not part of standard input schema.")


class LLMModelConfig(BaseSchema):
    """Configuration schema for the LLM model."""
    model_provider: LLMModelProvider = Field(
        default=LLMModelProvider.OPENAI,
        description="Model provider (openai, anthropic, gemini)"
    )
    model_name: str = Field(
        default="gpt-3.5-turbo",
        description="Model name (e.g., gpt-4, claude-3-opus-20240229, gemini-pro)"
    )
    max_tokens: Optional[int] = Field(
        None,
        description="Maximum number of tokens to generate"
    )
    temperature: float = Field(
        default=0.0,
        description="Temperature for sampling (0.0 = deterministic, 1.0 = creative)"
    )
    
    # reasoning config
    reasoning_effort_class: Optional[str] = Field(
        None,
        description="Class of reasoning effort to use"
    )
    reasoning_effort_range: Optional[List[int]] = Field(
        None,
        description="Range of reasoning effort to use"
    )
    reasoning_tokens_budget: Optional[int] = Field(
        None,
        description="Maximum number of tokens available for reasoning"
    )

    
    kwargs: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional keyword arguments to pass to the model"
    )
    # top_p: Optional[float] = Field(
    #     None,
    #     description="Top-p sampling parameter"
    # )


class ThinkingTokensInPrompt(Enum):
    """Enum for thinking tokens in prompt."""
    ALL = "all"
    LATEST = "latest_message"
    NONE = "none"


class ToolCallingConfig(BaseSchema):
    """Configuration for tool calling."""
    enable_tool_calling: bool = Field(
        default=False,
        description="Whether to enable tool calling"
    )
    tool_choice: Optional[str] = Field(
        None,
        description="Mode of tool calling"
    )
    parallel_tool_calls: bool = Field(
        default=True,
        description="Whether to enable parallel tool calls"
    )
    

class LLMNodeConfigSchema(BaseSchema):
    """Configuration schema for the LLM node."""
    # Model Config
    model_spec: Optional[ModelSpec] = Field(
        default=ModelSpec(),
        description="Model specification to use"
    )
    thinking_tokens_in_prompt: Optional[ThinkingTokensInPrompt] = Field(
        default=ThinkingTokensInPrompt.NONE,
        description="Whether to include thinking tokens in the prompt"
    )
    api_key_override: Optional[Dict[str, str]] = Field(
        None,
        description="Override API keys for specific providers"
    )
    cache_responses: bool = Field(
        default=True,
        description="Whether to cache responses"
    )

    # Output configuration
    output_schema: LLMStructuredOutputSchema = Field(
        default_factory=LLMStructuredOutputSchema,
        description="JSON schema for structured output (required if output_format is 'structured')"
    )
    stream: bool = Field(
        default=True,
        description="Whether to stream the response"
    )
    
    # Tool calling configuration
    tool_calling_config: ToolCallingConfig = Field(
        default_factory=ToolCallingConfig,
        description="Configuration for tool calling"
    )
    tools: Optional[List[ToolConfig]] = Field(
        None,
        description="List of tools to make available to the model"
    )
    
    @field_validator('tools')
    def validate_tools(cls, v, info):
        """Validate that tools are provided if tool calling is enabled."""
        if info.data.get('enable_tool_calling', False) and not v:
            raise ValueError("Tools must be provided when tool calling is enabled")
        return v

###########################


class LLMNode(BaseNode[LLMNodeInputSchema, LLMNodeOutputSchema, LLMNodeConfigSchema]):
    """
    LLM Node that processes requests using LangChain.
    
    This node provides a flexible interface to various LLM providers through LangChain,
    supporting different input formats, structured outputs, and tool calling capabilities.
    
    Additional options that could be implemented:
    - Request timeouts and retry logic
    - Dynamic model selection based on input complexity
    - Batched requests for processing multiple prompts
    - Custom prompt templates
    - Fallback models if primary model fails
    - Prompt optimization/compression
    - Response filtering/moderation
    - Caching with TTL settings
    - Cost tracking and budget limits
    - Response validators
    - Chained LLM calls (use output of one as input to another)
    - Parallel model calls with voting/ensemble
    - Context window management
    - Semantic caching for similar queries
    """
    node_name: ClassVar[str] = "llm"
    node_version: ClassVar[str] = "1.0.0"
    
    input_schema_cls: ClassVar[Type[LLMNodeInputSchema]] = LLMNodeInputSchema
    output_schema_cls: ClassVar[Type[LLMNodeOutputSchema]] = LLMNodeOutputSchema
    config_schema_cls: ClassVar[Type[LLMNodeConfigSchema]] = LLMNodeConfigSchema
    
    # instance config
    config: LLMNodeConfigSchema

    def process(self, input_data: LLMNodeInputSchema, config: Dict[str, Any], *args: Any, **kwargs: Any) -> LLMNodeOutputSchema:
        """
        Process input data through an LLM model and return the response.
        
        Args:
            input_data: Input data conforming to the LLMNodeInputSchema
            config: Configuration overrides
            
        Returns:
            LLMNodeOutputSchema: The LLM response and metadata
        """
        # Setup model parameters
        model_provider = input_data.model_provider
        model_name = input_data.model_name
        
        # Override from node config if specified
        if self.config:
            if self.config.default_model_provider:
                model_provider = self.config.default_model_provider
            if self.config.default_model_name:
                model_name = self.config.default_model_name
        
        # Prepare model configuration
        model_kwargs = {
            "temperature": input_data.temperature,
            "stream": input_data.stream,
        }
        
        if input_data.max_tokens:
            model_kwargs["max_tokens"] = input_data.max_tokens
        
        if input_data.top_p:
            model_kwargs["top_p"] = input_data.top_p
            
        # Add caching configuration
        if self.config and hasattr(self.config, "cache_responses"):
            model_kwargs["cache"] = self.config.cache_responses
        
        # Initialize the model
        try:
            chat_model = init_chat_model(
                model_name=model_name,
                model_provider=model_provider.value,
                **model_kwargs
            )
        except Exception as e:
            # Handle initialization errors
            raise ValueError(f"Failed to initialize model: {str(e)}")
        
        # Prepare messages
        messages = self._prepare_messages(input_data)
        
        # Configure the chain based on output format
        chain = self._build_chain(chat_model, input_data)
        
        # Execute the chain with error handling
        try:
            start_time = self._get_current_time_ms()
            response = chain.invoke({"messages": messages})
            end_time = self._get_current_time_ms()
            latency_ms = end_time - start_time
        except Exception as e:
            raise RuntimeError(f"Error during model execution: {str(e)}")
        
        # Parse the response based on the output type
        return self._parse_response(response, input_data, messages, latency_ms)
    
    def _prepare_messages(self, input_data: LLMNodeInputSchema) -> List[AnyMessage]:
        """
        Prepare the message list for the LLM from input data.
        
        Args:
            input_data: Input data with either messages or prompt
            
        Returns:
            List[AnyMessage]: List of LangChain message objects
        """
        # If messages are provided, convert them to LangChain messages
        if input_data.messages:
            return self._convert_messages(input_data.messages)
        
        # If prompt is provided, create a simple message list
        if input_data.prompt:
            messages = []
            if input_data.system_message:
                messages.append(SystemMessage(content=input_data.system_message))
            messages.append(HumanMessage(content=input_data.prompt))
            return messages
        
        # If neither messages nor prompt is provided, raise an error
        raise ValueError("Either 'messages' or 'prompt' must be provided")
    
    def _convert_messages(self, message_dicts: List[Dict[str, Any]]) -> List[AnyMessage]:
        """
        Convert message dictionaries to LangChain message objects.
        
        Args:
            message_dicts: List of message dictionaries
            
        Returns:
            List[AnyMessage]: List of LangChain message objects
        """
        messages = []
        for msg in message_dicts:
            msg_type = msg.get("type", "human").lower()
            content = msg.get("content", "")
            
            if msg_type == "human" or msg_type == "user":
                messages.append(HumanMessage(content=content))
            elif msg_type == "ai" or msg_type == "assistant":
                messages.append(AIMessage(content=content))
            elif msg_type == "system":
                messages.append(SystemMessage(content=content))
            elif msg_type == "tool" or msg_type == "function":
                tool_name = msg.get("tool_name", "") or msg.get("function_name", "")
                messages.append(ToolMessage(content=content, tool_call_id=msg.get("id"), name=tool_name))
        
        return messages
    
    def _build_chain(self, chat_model: Any, input_data: LLMNodeInputSchema) -> Runnable:
        """
        Build the LangChain processing chain based on the input configuration.
        
        Args:
            chat_model: Initialized chat model
            input_data: Input configuration
            
        Returns:
            Runnable: LangChain chain for processing
        """
        # Handle tool calling configuration
        if input_data.enable_tool_calling and input_data.tools:
            tools = self._prepare_tools(input_data.tools)
            chat_model = chat_model.bind(tools=tools)
        
        # Configure output parsing based on format
        if input_data.output_format == OutputFormatType.JSON:
            chain = chat_model | JsonOutputParser()
        elif input_data.output_format == OutputFormatType.STRUCTURED and input_data.output_schema:
            # Function/structured output requires different handling per provider
            # Here we'll use model-specific structured output capabilities
            if input_data.model_provider == LLMModelProvider.OPENAI:
                # For OpenAI, we can use function calling with a single function
                function_schema = {
                    "name": "extract_information",
                    "description": "Extract structured information from the input",
                    "parameters": input_data.output_schema
                }
                chat_model = chat_model.bind(functions=[function_schema])
            else:
                # For other providers, we'll use structured prompting
                system_message = (
                    "You are a helpful assistant that always responds in JSON format according to this schema: "
                    f"{json.dumps(input_data.output_schema)}"
                )
                chain = (
                    ChatPromptTemplate.from_messages([
                        ("system", system_message),
                        ("placeholder", "{messages}"),
                    ])
                    | chat_model
                    | JsonOutputParser()
                )
                return chain
        else:
            # Default to text output
            chain = chat_model
        
        return chain
    
    def _prepare_tools(self, tool_configs: List[ToolConfig]) -> List[Dict[str, Any]]:
        """
        Prepare tool definitions for the LLM.
        
        Args:
            tool_configs: List of tool configurations
            
        Returns:
            List[Dict[str, Any]]: Tool definitions in the provider's expected format
        """
        tools = []
        for tool in tool_configs:
            tool_def = {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.input_schema
            }
            tools.append(tool_def)
        return tools
    
    def _parse_response(self, response: Any, input_data: LLMNodeInputSchema, 
                        input_messages: List[AnyMessage], latency_ms: float) -> LLMNodeOutputSchema:
        """
        Parse the LLM response and extract all relevant information.
        
        Args:
            response: Raw response from the LLM
            input_data: Original input data
            input_messages: Messages sent to the model
            latency_ms: Execution latency in milliseconds
            
        Returns:
            LLMNodeOutputSchema: Parsed response with metadata
        """
        # Handle different response types
        if isinstance(response, AIMessage):
            # Extract model metadata
            token_usage = response.response_metadata.get("token_usage", {}) if hasattr(response, "response_metadata") else {}
            finish_reason = response.response_metadata.get("finish_reason", None) if hasattr(response, "response_metadata") else None
            model_name = response.response_metadata.get("model_name", input_data.model_name) if hasattr(response, "response_metadata") else input_data.model_name
            
            # Extract thinking tokens (Anthropic-specific)
            thinking_tokens = None
            if "completion_tokens_details" in token_usage and "reasoning_tokens" in token_usage["completion_tokens_details"]:
                thinking_tokens = token_usage["completion_tokens_details"]["reasoning_tokens"]
            
            # Extract content and tool calls
            content = response.content or ""
            tool_calls = None
            
            # Handle tool calls if present
            if hasattr(response, "tool_calls") and response.tool_calls:
                tool_calls = []
                for call in response.tool_calls:
                    tool_calls.append(ToolCall(
                        tool_name=call.name,
                        tool_input=call.args,
                        tool_id=call.id
                    ))
            
            # Create updated message history
            messages = list(input_messages)
            messages.append(response)
            
            # Prepare output
            metadata = LLMMetadata(
                model_name=model_name,
                token_usage=token_usage,
                finish_reason=finish_reason,
                latency_ms=latency_ms,
                thinking_tokens=thinking_tokens,
                cached=hasattr(response, "cached") and response.cached
            )
            
            return LLMNodeOutputSchema(
                content=content,
                metadata=metadata,
                raw_response=response.model_dump() if hasattr(response, "model_dump") else {"content": content},
                messages=messages,
                tool_calls=tool_calls,
                structured_output=response.additional_kwargs.get("function_call", {}).get("arguments", {}) 
                    if hasattr(response, "additional_kwargs") and "function_call" in response.additional_kwargs else None
            )
        elif isinstance(response, dict):
            # This is a parsed JSON response
            # Create an AI message to add to history
            ai_message = AIMessage(content=json.dumps(response))
            messages = list(input_messages)
            messages.append(ai_message)
            
            # Basic metadata since we don't have access to token usage
            metadata = LLMMetadata(
                model_name=input_data.model_name,
                token_usage={},
                latency_ms=latency_ms
            )
            
            return LLMNodeOutputSchema(
                content=json.dumps(response),
                metadata=metadata,
                raw_response=response,
                messages=messages,
                structured_output=response
            )
        else:
            # Handle string or other response types
            content = str(response)
            ai_message = AIMessage(content=content)
            messages = list(input_messages)
            messages.append(ai_message)
            
            metadata = LLMMetadata(
                model_name=input_data.model_name,
                token_usage={},
                latency_ms=latency_ms
            )
            
            return LLMNodeOutputSchema(
                content=content,
                metadata=metadata,
                raw_response={"content": content},
                messages=messages
            )
    
    def _get_current_time_ms(self) -> float:
        """Get the current time in milliseconds."""
        import time
        return time.time() * 1000
