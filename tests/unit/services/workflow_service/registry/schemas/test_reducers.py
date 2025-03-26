import unittest
from typing import Dict, List, Optional, Any, Union, Annotated
import uuid

from langchain_core.messages import (
    HumanMessage, AIMessage, SystemMessage, BaseMessage, AnyMessage
)
from langgraph.graph.message import add_messages

from workflow_service.registry.schemas.reducers import (
    DefaultReducers, ReducerRegistry, ReducerType,
    replace, add, append_list
)
from workflow_service.registry.schemas.base import BaseSchema


class TestReducers(unittest.TestCase):
    """Test cases for reducer functions."""

    def test_replace(self):
        """Test replace reducer."""
        self.assertEqual(replace(1, 2), 2)
        self.assertEqual(replace("old", "new"), "new")
        self.assertEqual(replace([1, 2], [3, 4]), [3, 4])

    def test_add(self):
        """Test add reducer."""
        self.assertEqual(add(1, 2), 3)
        self.assertEqual(add(1.5, 2.5), 4.0)
        
    def test_append_list(self):
        """Test append_list reducer."""
        self.assertEqual(append_list([1, 2], [3, 4]), [1, 2, 3, 4])
        self.assertEqual(append_list([], [1, 2]), [1, 2])
        self.assertEqual(append_list([1, 2], []), [1, 2])

    def test_add_messages(self):
        """Test add_messages reducer for message lists."""
        # Test basic append functionality
        messages1 = [
            HumanMessage(content="Hello"),
            AIMessage(content="Hi there")
        ]
        
        messages2 = [
            SystemMessage(content="System instruction")
        ]
        
        combined = add_messages(messages1, messages2)
        self.assertEqual(len(combined), 3)
        self.assertEqual(combined[0].content, "Hello")
        self.assertEqual(combined[1].content, "Hi there")
        self.assertEqual(combined[2].content, "System instruction")
        
        # Test updating messages with matching IDs
        message_id = str(uuid.uuid4())
        messages1 = [
            HumanMessage(content="Original content", id=message_id)
        ]
        
        messages2 = [
            HumanMessage(content="Updated content", id=message_id)
        ]
        
        updated = add_messages(messages1, messages2)
        self.assertEqual(len(updated), 1)  # Should still be 1 message
        self.assertEqual(updated[0].content, "Updated content")  # Content should be updated
        
        # Test converting dictionary messages
        messages1 = [
            HumanMessage(content="Hello")
        ]
        
        dict_messages = [
            {"role": "assistant", "content": "AI response"},
            {"role": "system", "content": "System instruction"}
        ]
        
        combined = add_messages(messages1, dict_messages)
        self.assertEqual(len(combined), 3)
        self.assertEqual(combined[1].content, "AI response")
        self.assertEqual(combined[2].content, "System instruction")
        self.assertIsInstance(combined[1], AIMessage)
        self.assertIsInstance(combined[2], SystemMessage)

    def test_registry_get_reducer(self):
        """Test getting reducers from the registry."""
        # Test getting by enum value
        add_func = ReducerRegistry.get_reducer(ReducerType.ADD)
        self.assertEqual(add_func(1, 2), 3)
        
        # Test getting by string name
        add_func = ReducerRegistry.get_reducer("add")
        self.assertEqual(add_func(1, 2), 3)
        
        # Test case insensitivity
        add_func = ReducerRegistry.get_reducer("ADD")
        self.assertEqual(add_func(1, 2), 3)
        
        # Test getting message reducer
        msg_reducer = ReducerRegistry.get_reducer("add_messages")
        self.assertIsNotNone(msg_reducer)
        
        # Test getting non-existent reducer
        self.assertIsNone(ReducerRegistry.get_reducer("non_existent"))


class MessageState(BaseSchema):
    """Example schema with messages using the add_messages reducer."""
    messages: Annotated[List[AnyMessage], add_messages]
    user_id: str


class TestReducerWithSchema(unittest.TestCase):
    """Test cases for using reducers with schemas."""

    def test_message_state_with_reducer(self):
        """Test using the add_messages reducer with a schema."""
        # Create initial state
        state = MessageState(
            messages=[
                SystemMessage(content="Initial system message"),
                HumanMessage(content="Initial user message")
            ],
            user_id="user123"
        )
        
        # Create update with new messages
        update = MessageState(
            messages=[
                AIMessage(content="AI response")
            ],
            user_id="user123"
        )
        
        # Simulate reducer application (what would happen in langgraph)
        combined_messages = add_messages(state.messages, update.messages)
        new_state = MessageState(
            messages=combined_messages,
            user_id=update.user_id
        )
        
        # Verify combined state
        self.assertEqual(len(new_state.messages), 3)
        self.assertEqual(new_state.messages[0].content, "Initial system message")
        self.assertEqual(new_state.messages[1].content, "Initial user message")
        self.assertEqual(new_state.messages[2].content, "AI response")
        
        # Test updating an existing message
        message_id = str(uuid.uuid4())
        state = MessageState(
            messages=[
                HumanMessage(content="Original message", id=message_id),
                AIMessage(content="First response")
            ],
            user_id="user123"
        )
        
        update = MessageState(
            messages=[
                HumanMessage(content="Updated message", id=message_id)
            ],
            user_id="user123"
        )
        
        combined_messages = add_messages(state.messages, update.messages)
        new_state = MessageState(
            messages=combined_messages,
            user_id=update.user_id
        )
        
        # The original message should be updated, not appended
        self.assertEqual(len(new_state.messages), 2)
        self.assertEqual(new_state.messages[0].content, "Updated message")
        self.assertEqual(new_state.messages[1].content, "First response")


if __name__ == "__main__":
    unittest.main()
