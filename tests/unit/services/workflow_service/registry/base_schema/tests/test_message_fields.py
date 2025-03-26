"""
Tests for BaseSchema with AnyMessage fields and reducers.

This module tests:
1. Validation of various AnyMessage field combinations
2. Serialization and deserialization of message fields
3. Schema generation and diffing with message fields
4. Use of reducers with message fields
"""

import unittest
from typing import Dict, List, Optional, Any, Union, Annotated
from enum import Enum
from datetime import datetime
from copy import deepcopy

from pydantic import Field, field_validator
from pydantic.json_schema import SkipJsonSchema
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages

from langchain_core.messages import (
    AnyMessage,
    HumanMessage,
    AIMessage,
    SystemMessage,
    ToolMessage,
    FunctionMessage,
)

from workflow_service.registry.schemas.base import BaseSchema
from workflow_service.registry.schemas.reducers import (
    append_list,
    replace,
    add,
    ReducerRegistry,
    ReducerType,
)

from pydantic import TypeAdapter
adapter = TypeAdapter(AnyMessage)


# Test schemas with various AnyMessage field combinations
class SingleMessageSchema(BaseSchema):
    """Schema with a single AnyMessage field."""
    message: Optional[AnyMessage] = None


class MessageListSchema(BaseSchema):
    """Schema with a list of AnyMessage fields."""
    messages: List[AnyMessage]


class AnnotatedMessageListSchema(BaseSchema):
    """Schema with an annotated list of AnyMessage fields using add_messages reducer."""
    messages: Annotated[List[AnyMessage], add_messages]


class OptionalMessageSchema(BaseSchema):
    """Schema with an optional AnyMessage field."""
    message: Optional[AnyMessage] = None


class MessageDictSchema(BaseSchema):
    """Schema with a dictionary of AnyMessage fields."""
    message_dict: Dict[str, AnyMessage]


class MessageListDictSchema(BaseSchema):
    """Schema with a dictionary mapping to lists of AnyMessage fields."""
    message_list_dict: Dict[str, List[AnyMessage]]


class ComplexMessageSchema(BaseSchema):
    """Schema with multiple message field types and nested structures."""
    primary_message: Optional[AnyMessage] = None
    message_history: Annotated[List[AnyMessage], add_messages]
    optional_message: Optional[AnyMessage] = None
    message_by_id: Dict[str, AnyMessage] = Field(default_factory=dict)
    message_groups: Dict[str, List[AnyMessage]] = Field(default_factory=dict)
    internal_message: SkipJsonSchema[Optional[AnyMessage]] = None
    deprecated_message: Optional[AnyMessage] = Field(
        default_factory=lambda: SystemMessage(content="Deprecated"),
        **{BaseSchema.DEPRECATED_FIELD_KEY: True}
    )
    

class NestedMessageSchema(BaseSchema):
    """Schema with nested message schemas."""
    title: str
    single_message_schema: SingleMessageSchema
    message_list_schema: MessageListSchema
    optional_schemas: List[OptionalMessageSchema] = Field(default_factory=list)
    schema_dict: Dict[str, MessageDictSchema] = Field(default_factory=dict)


class MessageWithMetadataSchema(BaseSchema):
    """Schema with messages that have additional metadata."""
    message: Optional[AnyMessage] = None
    metadata: Dict[str, str] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    message_type: str = Field(default="unknown")


class TestMessageFields(unittest.TestCase):
    """Test cases for BaseSchema with AnyMessage fields."""

    def setUp(self):
        """Set up test fixtures."""
        # Create test messages of various types
        self.human_message = HumanMessage(content="Hello from human")
        self.ai_message = AIMessage(content="Hello from AI")
        self.system_message = SystemMessage(content="System instruction")
        self.tool_message = ToolMessage(content="Tool result", tool_call_id="123")
        self.function_message = FunctionMessage(content="Function result", name="test_func")
        
        # Message with additional kwargs
        self.message_with_kwargs = HumanMessage(
            content="Message with kwargs",
            additional_kwargs={"custom_field": "value", "tags": ["tag1", "tag2"]}
        )
        
        # Message with special characters and Unicode
        self.special_chars_message = AIMessage(content="Special: !@#$%^&*()_+<>?,./;'[]\\")
        self.unicode_message = HumanMessage(content="Unicode: こんにちは 你好 مرحبا שלום")
        
        # Empty message
        self.empty_message = SystemMessage(content="")
        
        # Very long message
        self.long_message = AIMessage(content="Long " * 1000)
        
        # Message list
        self.message_list = [
            self.human_message,
            self.ai_message,
            self.system_message,
            self.tool_message,
            self.function_message
        ]

    def test_single_message_validation(self):
        """Test validation of single message fields."""
        # Test valid messages of different types
        for msg in [
            self.human_message,
            self.ai_message,
            self.system_message,
            self.tool_message,
            self.function_message
        ]:
            schema = SingleMessageSchema(message=msg)
            self.assertEqual(schema.message, msg)
        
        # Test message with additional kwargs
        schema = SingleMessageSchema(message=self.message_with_kwargs)
        self.assertEqual(schema.message.additional_kwargs, {"custom_field": "value", "tags": ["tag1", "tag2"]})
        
        # Test special characters and Unicode
        schema = SingleMessageSchema(message=self.special_chars_message)
        self.assertEqual(schema.message.content, "Special: !@#$%^&*()_+<>?,./;'[]\\")
        
        schema = SingleMessageSchema(message=self.unicode_message)
        self.assertEqual(schema.message.content, "Unicode: こんにちは 你好 مرحبا שלום")
        
        # Test empty message
        schema = SingleMessageSchema(message=self.empty_message)
        self.assertEqual(schema.message.content, "")
        
        # Test long message
        schema = SingleMessageSchema(message=self.long_message)
        self.assertEqual(schema.message.content, "Long " * 1000)
        
        # Test invalid message (not an AnyMessage)
        with self.assertRaises(TypeError):
            SingleMessageSchema(message="Not a message")
        # Test dictionary representation (should pass because it's converted to a message)
        msg_dict = {"type": "human", "content": "Dictionary message"}
        schema = SingleMessageSchema(message=msg_dict)
        # self.assertIsInstance(schema.message, AnyMessage)
        adapter.validate_python(schema.message)
        self.assertEqual(schema.message.content, "Dictionary message")

    def test_message_list_validation(self):
        """Test validation of message list fields."""
        # Test with a valid list of messages
        schema = MessageListSchema(messages=self.message_list)
        self.assertEqual(len(schema.messages), 5)
        self.assertEqual(schema.messages[0], self.human_message)
        
        # Test with an empty list
        schema = MessageListSchema(messages=[])
        self.assertEqual(schema.messages, [])
        
        # Test with a list containing a non-message item
        with self.assertRaises(TypeError):
            MessageListSchema(messages=[self.human_message, "Not a message"])
            
        # Test with a list of dictionaries (should pass as they're converted)
        dict_list = [
            {"type": "human", "content": "User message"},
            {"type": "ai", "content": "AI response"}
        ]
        schema = MessageListSchema(messages=dict_list)
        self.assertEqual(len(schema.messages), 2)
        # self.assertIsInstance(schema.messages[0], AnyMessage)
        adapter.validate_python(schema.messages[0])
        self.assertEqual(schema.messages[0].content, "User message")
        self.assertEqual(schema.messages[1].content, "AI response")

    def test_annotated_message_list(self):
        """Test message list fields with add_messages reducer."""
        # Test initialization
        schema = AnnotatedMessageListSchema(messages=[self.human_message])
        self.assertEqual(len(schema.messages), 1)
        
        # Test to ensure the Annotated type is preserved in the schema
        schema_def = AnnotatedMessageListSchema.get_schema_for_db()
        self.assertIn("messages", schema_def)
        
        # We should simulate how add_messages works with this field
        # In a real scenario, this would be handled by langgraph's reducer system
        # Here we're just checking the field is properly annotated
        field_validation = AnnotatedMessageListSchema._get_field_validation_result("messages")
        self.assertEqual(field_validation.core_type_class, AnyMessage)
        
        # Test add_messages functionality (simulating what would happen in langgraph)
        initial = AnnotatedMessageListSchema(messages=[self.human_message])
        update = AnnotatedMessageListSchema(messages=[self.ai_message])
        
        # Manually apply the reducer (this is what langgraph would do)
        combined_messages = add_messages(initial.messages, update.messages)
        updated_schema = AnnotatedMessageListSchema(messages=combined_messages)
        
        self.assertEqual(len(updated_schema.messages), 2)
        self.assertEqual(updated_schema.messages[0], self.human_message)
        self.assertEqual(updated_schema.messages[1], self.ai_message)

    def test_optional_message(self):
        """Test optional message fields."""
        # Test with message provided
        schema = OptionalMessageSchema(message=self.human_message)
        self.assertEqual(schema.message, self.human_message)
        
        # Test without message
        schema = OptionalMessageSchema()
        self.assertIsNone(schema.message)
        
        # Test with None explicitly provided
        schema = OptionalMessageSchema(message=None)
        self.assertIsNone(schema.message)

    def test_message_dict(self):
        """Test dictionary of message fields."""
        # Test with valid message dictionary
        message_dict = {
            "user": self.human_message,
            "assistant": self.ai_message,
            "system": self.system_message
        }
        schema = MessageDictSchema(message_dict=message_dict)
        self.assertEqual(schema.message_dict["user"], self.human_message)
        self.assertEqual(schema.message_dict["assistant"], self.ai_message)
        self.assertEqual(schema.message_dict["system"], self.system_message)
        
        # Test with empty dictionary
        schema = MessageDictSchema(message_dict={})
        self.assertEqual(schema.message_dict, {})
        
        # Test with invalid value
        with self.assertRaises(TypeError):
            MessageDictSchema(message_dict={"user": "Not a message"})
            
        # Test with dictionary of dictionaries (should pass after conversion)
        dict_of_dicts = {
            "user": {"type": "human", "content": "User message"},
            "assistant": {"type": "ai", "content": "AI response"}
        }
        schema = MessageDictSchema(message_dict=dict_of_dicts)
        # AnyMessage is type annotation so can't be used like this!
        # self.assertIsInstance(schema.message_dict["user"], AnyMessage)
        self.assertEqual(schema.message_dict["user"].content, "User message")
        self.assertEqual(schema.message_dict["assistant"].content, "AI response")

    def test_message_list_dict(self):
        """Test dictionary mapping to lists of messages."""
        # Test with valid message list dictionary
        message_list_dict = {
            "chat1": [self.human_message, self.ai_message],
            "chat2": [self.system_message, self.human_message, self.ai_message]
        }
        schema = MessageListDictSchema(message_list_dict=message_list_dict)
        self.assertEqual(len(schema.message_list_dict["chat1"]), 2)
        self.assertEqual(len(schema.message_list_dict["chat2"]), 3)
        self.assertEqual(schema.message_list_dict["chat1"][0], self.human_message)
        
        # Test with empty dictionary
        schema = MessageListDictSchema(message_list_dict={})
        self.assertEqual(schema.message_list_dict, {})
        
        # Test with invalid value in list
        with self.assertRaises(TypeError):
            MessageListDictSchema(message_list_dict={
                "chat1": [self.human_message, "Not a message"]
            })

    def test_complex_message_schema(self):
        """Test schema with multiple message field types and nested structures."""
        # Create a complex message schema instance
        schema = ComplexMessageSchema(
            primary_message=self.human_message,
            message_history=[self.system_message, self.human_message],
            optional_message=self.ai_message,
            message_by_id={
                "msg1": self.human_message,
                "msg2": self.ai_message
            },
            message_groups={
                "group1": [self.human_message, self.ai_message],
                "group2": [self.system_message]
            },
            internal_message=self.tool_message
        )
        
        # Verify all fields
        self.assertEqual(schema.primary_message, self.human_message)
        self.assertEqual(len(schema.message_history), 2)
        self.assertEqual(schema.optional_message, self.ai_message)
        self.assertEqual(len(schema.message_by_id), 2)
        self.assertEqual(len(schema.message_groups), 2)
        self.assertEqual(schema.internal_message, self.tool_message)
        self.assertIsInstance(schema.deprecated_message, SystemMessage)
        
        # Test model_dump
        dumped = schema.model_dump()
        self.assertIn("primary_message", dumped)
        self.assertIn("message_history", dumped)
        self.assertIn("internal_message", dumped)  # Internal fields included in regular model_dump
        
        # Test model_dump_only_user_editable
        user_editable = schema.model_dump_only_user_editable()
        self.assertIn("primary_message", user_editable)
        self.assertIn("message_history", user_editable)
        self.assertNotIn("internal_message", user_editable)  # Internal fields excluded
        
        # Test with include_deprecated=False
        no_deprecated = schema.model_dump_only_user_editable(include_deprecated=False)
        self.assertNotIn("deprecated_message", no_deprecated)
        
        # Test serialized
        serialized = schema.model_dump_only_user_editable(serialize_values=True)
        self.assertIsInstance(serialized["primary_message"], dict)
        self.assertEqual(serialized["primary_message"]["content"], "Hello from human")
        
        # Test add_messages functionality with message_history
        update = ComplexMessageSchema(
            message_history=[self.ai_message]
        )
        
        # Manually apply the reducer (simulating langgraph behavior)
        combined_messages = add_messages(schema.message_history, update.message_history)
        self.assertEqual(len(combined_messages), 3)
        self.assertEqual(combined_messages[0], self.system_message)
        self.assertEqual(combined_messages[1], self.human_message)
        self.assertEqual(combined_messages[2], self.ai_message)

    def test_nested_message_schema(self):
        """Test schema with nested message schemas."""
        # Create nested schema components
        single_schema = SingleMessageSchema(message=self.human_message)
        list_schema = MessageListSchema(messages=[self.ai_message, self.system_message])
        optional_schema1 = OptionalMessageSchema(message=self.tool_message)
        optional_schema2 = OptionalMessageSchema()  # No message
        dict_schema = MessageDictSchema(message_dict={"key": self.function_message})
        
        # Create the nested schema
        nested = NestedMessageSchema(
            title="Test Nested Schema",
            single_message_schema=single_schema,
            message_list_schema=list_schema,
            optional_schemas=[optional_schema1, optional_schema2],
            schema_dict={"schema1": dict_schema}
        )
        
        # Verify nested fields
        self.assertEqual(nested.title, "Test Nested Schema")
        self.assertEqual(nested.single_message_schema.message, self.human_message)
        self.assertEqual(len(nested.message_list_schema.messages), 2)
        self.assertEqual(len(nested.optional_schemas), 2)
        self.assertEqual(nested.optional_schemas[0].message, self.tool_message)
        self.assertIsNone(nested.optional_schemas[1].message)
        self.assertEqual(len(nested.schema_dict), 1)
        self.assertEqual(
            nested.schema_dict["schema1"].message_dict["key"],
            self.function_message
        )
        
        # Test model_dump_only_user_editable with nested structures
        dumped = nested.model_dump_only_user_editable()
        self.assertIn("single_message_schema", dumped)
        self.assertIn("message", dumped["single_message_schema"])
        self.assertIn("messages", dumped["message_list_schema"])
        self.assertEqual(len(dumped["optional_schemas"]), 2)
        
        # Test serialized nested structure
        serialized = nested.model_dump_only_user_editable(serialize_values=True)
        self.assertIsInstance(serialized["single_message_schema"]["message"], dict)
        self.assertEqual(
            serialized["single_message_schema"]["message"]["content"],
            "Hello from human"
        )

    def test_schema_diff_with_messages(self):
        """Test schema diffing with message fields."""
        # Get current schema
        schema_def = ComplexMessageSchema.get_schema_for_db()
        
        # Test no changes
        diff = ComplexMessageSchema.diff_from_provided_schema(schema_def)
        self.assertEqual(len(diff["added"]), 0)
        self.assertEqual(len(diff["removed"]), 0)
        self.assertEqual(len(diff["modified_type"]), 0)
        
        # Modify schema
        modified = deepcopy(schema_def)
        
        # Add new field
        modified["new_message"] = {
            "_type": "AnyMessage",
            "_default": None,
            "_deprecated": False,
            "_user_editable": True
        }
        
        # Remove field
        del modified["optional_message"]
        
        # Modify type
        modified["message_history"]["_type"] = "list[HumanMessage]"  # Change from AnyMessage
        
        # Get diff
        diff = ComplexMessageSchema.diff_from_provided_schema(modified, self_is_base_for_diff=True)
        
        # Check changes
        self.assertIn("new_message", diff["added"])
        self.assertIn("optional_message", diff["removed"])
        self.assertIn("message_history._type", diff["modified_type"])

    def test_json_schema_with_messages(self):
        """Test JSON schema generation with message fields."""
        # Generate schema
        schema = ComplexMessageSchema.model_json_schema()
        
        # Check message field types
        properties = schema["properties"]
        self.assertIn("primary_message", properties)
        self.assertIn("message_history", properties)
        
        # Check that internal fields are excluded
        self.assertNotIn("internal_message", properties)
        
        # Generate schema with skipped fields
        full_schema = ComplexMessageSchema.model_json_schema_with_skipped_fields()
        
        # Check that internal fields are included
        full_properties = full_schema["properties"]
        self.assertIn("internal_message", full_properties)

    def test_message_with_metadata(self):
        """Test schema combining messages with metadata."""
        # Create schema with metadata
        now = datetime.now()
        schema = MessageWithMetadataSchema(
            message=self.ai_message,
            metadata={
                "source": "test",
                "confidence": "0.95",
                "tags": "important"
            },
            created_at=now,
            message_type="assistant"
        )
        
        # Verify fields
        self.assertEqual(schema.message, self.ai_message)
        self.assertEqual(schema.metadata["source"], "test")
        self.assertEqual(schema.metadata["confidence"], "0.95")
        self.assertEqual(schema.created_at, now)
        self.assertEqual(schema.message_type, "assistant")
        
        # Test serialization
        serialized = schema.model_dump_only_user_editable(serialize_values=True)
        self.assertIsInstance(serialized["message"], dict)
        self.assertEqual(serialized["message_type"], "assistant")
        self.assertIsInstance(serialized["created_at"], str)  # Date serialized to string
        
        # Test JSON schema
        json_schema = MessageWithMetadataSchema.model_json_schema()
        self.assertIn("message", json_schema["properties"])
        self.assertIn("metadata", json_schema["properties"])
        self.assertIn("created_at", json_schema["properties"])
        self.assertIn("message_type", json_schema["properties"])


if __name__ == '__main__':
    unittest.main()