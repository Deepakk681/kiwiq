"""
Comprehensive test helpers for prompt compaction integration tests.

This module provides specialized helper functions for testing:
1. Tool call bracket-style pairing verification
2. Message ID-based history deduplication
3. Loading real provider message histories
4. LinkedIn metadata management
5. AIMessage type enforcement
6. Weaviate cleanup utilities
7. Test data generators for complex scenarios

These helpers extend the base test classes and are designed to expose
implementation gaps in the prompt compaction system.
"""

import json
import os
from collections import defaultdict
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import uuid4

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)

from workflow_service.registry.nodes.llm.prompt_compaction.utils import (
    get_compaction_metadata,
    set_compaction_metadata,
)


# ============================================================================
# Tool Call Pairing Verification
# ============================================================================


def verify_tool_call_pairing(messages: List[BaseMessage]) -> List[str]:
    """
    Verify all tool calls have matching responses (bracket-style pairing).

    Tool calls are like opening brackets that MUST have corresponding responses
    (closing brackets). Unlike real brackets, they can close out of order
    (parallel tool calls allowed).

    Args:
        messages: List of messages to verify

    Returns:
        List of error messages. Empty list means all pairs valid.

    Examples:
        Valid patterns:
        - [TC1, TC2] → [TR1, TR2] (parallel, can close out of order)
        - TC1 → TR1 → TC2 → TR2 (sequential)
        - TC1 → TR1 (single pair)

        Invalid patterns:
        - TC1 → TC2 (TC2 has no response)
        - TR1 → TC1 (response before call)
        - TC1 → TR1 → TR2 (TR2 has no call)
    """
    errors = []

    # Track tool calls and their responses
    open_tool_calls: Dict[str, BaseMessage] = {}  # tool_call_id → AIMessage
    found_responses: Set[str] = set()  # tool_call_ids that have responses

    for idx, msg in enumerate(messages):
        # Check if this is an AI message with tool calls (OpenAI format or converted Anthropic)
        if isinstance(msg, AIMessage) and hasattr(msg, "tool_calls") and msg.tool_calls:
            for tool_call in msg.tool_calls:
                tool_call_id = tool_call.get("id")
                if tool_call_id:
                    if tool_call_id in open_tool_calls:
                        errors.append(
                            f"Duplicate tool call ID '{tool_call_id}' at index {idx}. "
                            f"First seen at index {messages.index(open_tool_calls[tool_call_id])}"
                        )
                    open_tool_calls[tool_call_id] = msg
        
        # Also check for Anthropic-style tool calls in content list (if not converted yet)
        elif isinstance(msg, AIMessage) and isinstance(msg.content, list):
            tool_uses = [c for c in msg.content if isinstance(c, dict) and c.get("type") == "tool_use"]
            for tool_use in tool_uses:
                tool_call_id = tool_use.get("id")
                if tool_call_id:
                    if tool_call_id in open_tool_calls:
                        errors.append(
                            f"Duplicate tool call ID '{tool_call_id}' at index {idx}. "
                            f"First seen at index {messages.index(open_tool_calls[tool_call_id])}"
                        )
                    open_tool_calls[tool_call_id] = msg

        # Check if this is a tool response (OpenAI format)
        elif isinstance(msg, ToolMessage):
            tool_call_id = msg.tool_call_id
            if tool_call_id not in open_tool_calls:
                errors.append(
                    f"Tool response at index {idx} has no matching tool call. "
                    f"tool_call_id={tool_call_id}"
                )
            else:
                found_responses.add(tool_call_id)
        
        # Check if this is a tool response (Anthropic format - HumanMessage with tool_result)
        elif isinstance(msg, HumanMessage) and isinstance(msg.content, list):
            tool_results = [c for c in msg.content if isinstance(c, dict) and c.get("type") == "tool_result"]
            for tool_result in tool_results:
                tool_call_id = tool_result.get("tool_use_id")
                if tool_call_id:
                    if tool_call_id not in open_tool_calls:
                        errors.append(
                            f"Tool response at index {idx} has no matching tool call. "
                            f"tool_call_id={tool_call_id}"
                        )
                    else:
                        found_responses.add(tool_call_id)

    # Check for unpaired tool calls
    unpaired = set(open_tool_calls.keys()) - found_responses
    if unpaired:
        for tool_call_id in unpaired:
            msg = open_tool_calls[tool_call_id]
            msg_idx = messages.index(msg)
            errors.append(
                f"Tool call at index {msg_idx} has no response. "
                f"tool_call_id={tool_call_id}"
            )

    return errors


def identify_tool_call_groups(messages: List[BaseMessage]) -> List[List[int]]:
    """
    Identify atomic tool call groups (indices that must stay together).

    Returns a list of groups, where each group is a list of message indices
    that form an atomic unit.

    Parallel tool calls: [TC1, TC2] → [TR1, TR2] = one group (all 4 indices)
    Sequential tool calls: TC1 → TR1 | TC2 → TR2 = two groups

    Args:
        messages: List of messages

    Returns:
        List of groups (each group is list of indices)

    Example:
        messages = [Human, TC1, TC2, TR1, TR2, Human, TC3, TR3]
        returns = [[1, 2, 3, 4], [6, 7]]
        # First group: indices 1-4 (TC1, TC2, TR1, TR2)
        # Second group: indices 6-7 (TC3, TR3)
    """
    groups = []
    current_group_indices = []
    pending_tool_call_ids = set()

    for idx, msg in enumerate(messages):
        # Check if this is an AI message with tool calls
        if isinstance(msg, AIMessage) and hasattr(msg, "tool_calls") and msg.tool_calls:
            tool_call_ids = [tc.get("id") for tc in msg.tool_calls if tc.get("id")]
            if tool_call_ids:
                # Start or extend current group
                current_group_indices.append(idx)
                pending_tool_call_ids.update(tool_call_ids)

        # Check if this is a tool response
        elif isinstance(msg, ToolMessage):
            if msg.tool_call_id in pending_tool_call_ids:
                # Part of current group
                current_group_indices.append(idx)
                pending_tool_call_ids.remove(msg.tool_call_id)

                # If all tool calls in this group have responses, close the group
                if not pending_tool_call_ids:
                    groups.append(current_group_indices[:])
                    current_group_indices = []

        else:
            # Non-tool message
            # If we have an open group, close it (shouldn't happen if pairing is correct)
            if current_group_indices:
                groups.append(current_group_indices[:])
                current_group_indices = []
                pending_tool_call_ids = set()

    # Close any remaining group
    if current_group_indices:
        groups.append(current_group_indices[:])

    return groups


def verify_tool_groups_atomic(
    original_messages: List[BaseMessage],
    processed_messages: List[BaseMessage],
) -> List[str]:
    """
    Verify that tool call groups remain atomic after processing.

    Checks that messages within each tool group are still together
    (not split across sections or removed partially).

    Args:
        original_messages: Original message list
        processed_messages: Processed message list after compaction

    Returns:
        List of error messages
    """
    errors = []

    # Get tool groups from original messages
    original_groups = identify_tool_call_groups(original_messages)

    # Build ID mapping
    original_ids = {msg.id: idx for idx, msg in enumerate(original_messages) if msg.id}
    processed_ids = {msg.id: idx for idx, msg in enumerate(processed_messages) if msg.id}

    for group_indices in original_groups:
        # Get message IDs in this group
        group_msg_ids = [
            original_messages[idx].id
            for idx in group_indices
            if original_messages[idx].id
        ]

        # Check how many of these IDs are in processed messages
        present_ids = [mid for mid in group_msg_ids if mid in processed_ids]
        missing_ids = [mid for mid in group_msg_ids if mid not in processed_ids]

        if missing_ids and present_ids:
            # Partial removal - atomic group broken!
            errors.append(
                f"Tool call group broken: {len(present_ids)}/{len(group_msg_ids)} messages present. "
                f"Present IDs: {present_ids}, Missing IDs: {missing_ids}. "
                f"Original indices: {group_indices}"
            )

        # If all present, verify they're still contiguous
        if len(present_ids) == len(group_msg_ids):
            processed_indices = sorted([processed_ids[mid] for mid in present_ids])
            # Check contiguity
            for i in range(len(processed_indices) - 1):
                if processed_indices[i+1] - processed_indices[i] != 1:
                    errors.append(
                        f"Tool call group no longer contiguous. "
                        f"Original indices: {group_indices}, "
                        f"Processed indices: {processed_indices}"
                    )
                    break

    return errors


# ============================================================================
# Message ID Deduplication
# ============================================================================


def merge_current_messages_into_history(
    history: List[BaseMessage],
    current_messages: List[BaseMessage],
) -> List[BaseMessage]:
    """
    Merge current_messages into history with ID-based deduplication.

    For each message in current_messages:
    - If message.id exists in history: Replace at same position
    - If message.id is new: Append to history

    This ensures no duplicate IDs and preserves chronological order.

    Args:
        history: Existing message history
        current_messages: New/updated messages from current turn

    Returns:
        Merged history with no duplicate IDs
    """
    # Build ID to index mapping for history
    id_to_index = {}
    for idx, msg in enumerate(history):
        if msg.id:
            id_to_index[msg.id] = idx

    # Create new history (copy)
    merged_history = history[:]

    # Process current_messages
    for msg in current_messages:
        if not msg.id:
            # Message has no ID, append (shouldn't happen but handle gracefully)
            merged_history.append(msg)
            continue

        if msg.id in id_to_index:
            # Replace at same position
            idx = id_to_index[msg.id]
            merged_history[idx] = msg
        else:
            # New message, append
            merged_history.append(msg)
            id_to_index[msg.id] = len(merged_history) - 1

    return merged_history


def verify_message_id_deduplication(messages: List[BaseMessage]) -> None:
    """
    Verify no duplicate message IDs in list.

    Raises:
        AssertionError: If duplicates found
    """
    seen_ids = {}
    duplicates = []

    for idx, msg in enumerate(messages):
        if msg.id:
            if msg.id in seen_ids:
                duplicates.append(
                    f"Duplicate ID '{msg.id}' at indices {seen_ids[msg.id]} and {idx}"
                )
            else:
                seen_ids[msg.id] = idx

    if duplicates:
        raise AssertionError(
            f"Found {len(duplicates)} duplicate message IDs:\n" +
            "\n".join(duplicates)
        )


# ============================================================================
# Provider Message History Loading
# ============================================================================


def load_sample_message_history(filename: str) -> List[BaseMessage]:
    """
    Load sample message history from JSON file.

    Args:
        filename: Filename in sample_data_message_histories/ directory

    Returns:
        List of LangChain BaseMessage objects
    """
    # Get path to sample data directory
    test_dir = os.path.dirname(__file__)
    sample_data_dir = os.path.join(test_dir, "sample_data_message_histories")
    filepath = os.path.join(sample_data_dir, filename)

    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Sample data file not found: {filepath}")

    with open(filepath, "r") as f:
        data = json.load(f)

    # Convert JSON to LangChain messages
    messages = []
    for msg_data in data:
        msg_type = msg_data.get("type")
        content = msg_data.get("content", "")
        msg_id = msg_data.get("id")
        additional_kwargs = msg_data.get("additional_kwargs", {})
        response_metadata = msg_data.get("response_metadata", {})

        if msg_type == "human":
            msg = HumanMessage(
                content=content,
                id=msg_id,
                additional_kwargs=additional_kwargs,
                response_metadata=response_metadata,
            )
        elif msg_type == "ai":
            msg = AIMessage(
                content=content,
                id=msg_id,
                additional_kwargs=additional_kwargs,
                response_metadata=response_metadata,
            )
        elif msg_type == "system":
            msg = SystemMessage(
                content=content,
                id=msg_id,
                additional_kwargs=additional_kwargs,
                response_metadata=response_metadata,
            )
        elif msg_type == "tool":
            tool_call_id = msg_data.get("tool_call_id")
            msg = ToolMessage(
                content=content,
                tool_call_id=tool_call_id,
                id=msg_id,
                additional_kwargs=additional_kwargs,
                response_metadata=response_metadata,
            )
        else:
            # Skip unknown types
            continue

        # Restore tool_calls if present
        if "tool_calls" in msg_data:
            msg.tool_calls = msg_data["tool_calls"]

        messages.append(msg)

    return messages


def add_linkedin_metadata(messages: List[BaseMessage]) -> List[BaseMessage]:
    """
    Add LinkedIn metadata to all messages (production pattern).

    Returns new list with modified messages since LangChain messages may be immutable.
    """
    result = []
    for msg in messages:
        linkedin_data = {
            "user_id": "test_linkedin_user",
            "company_id": "test_linkedin_company",
            "timestamp": "2025-11-11T00:00:00Z",
        }

        # Create new message with linkedin_data in additional_kwargs
        new_kwargs = dict(msg.additional_kwargs) if msg.additional_kwargs else {}
        if "linkedin_data" not in new_kwargs:
            new_kwargs["linkedin_data"] = linkedin_data

        # Create new message with the same type
        if isinstance(msg, HumanMessage):
            new_msg = HumanMessage(
                content=msg.content,
                id=msg.id,
                additional_kwargs=new_kwargs,
            )
        elif isinstance(msg, AIMessage):
            new_msg = AIMessage(
                content=msg.content,
                id=msg.id,
                additional_kwargs=new_kwargs,
                tool_calls=msg.tool_calls if hasattr(msg, 'tool_calls') else None,
            )
        elif isinstance(msg, SystemMessage):
            new_msg = SystemMessage(
                content=msg.content,
                id=msg.id,
                additional_kwargs=new_kwargs,
            )
        elif isinstance(msg, ToolMessage):
            new_msg = ToolMessage(
                content=msg.content,
                tool_call_id=msg.tool_call_id,
                id=msg.id,
                additional_kwargs=new_kwargs,
            )
        else:
            # Fallback: just use the message as is
            new_msg = msg

        result.append(new_msg)

    return result


# ============================================================================
# AIMessage Type Verification
# ============================================================================


def verify_all_ai_messages(messages: List[BaseMessage], context: str) -> None:
    """
    Verify all messages are AIMessages.

    Args:
        messages: Messages to check
        context: Context string for error messages

    Raises:
        AssertionError: If any message is not AIMessage
    """
    non_ai_messages = []

    for idx, msg in enumerate(messages):
        if not isinstance(msg, AIMessage):
            non_ai_messages.append(
                f"Index {idx}: {type(msg).__name__} (expected AIMessage)"
            )

    if non_ai_messages:
        raise AssertionError(
            f"{context}: Found {len(non_ai_messages)} non-AIMessage(s):\n" +
            "\n".join(non_ai_messages)
        )


# ============================================================================
# Weaviate Cleanup
# ============================================================================


async def cleanup_weaviate_thread(weaviate_client, thread_id: str) -> None:
    """
    Delete all indexed messages for a thread from Weaviate.

    Args:
        weaviate_client: ThreadMessageWeaviateClient instance
        thread_id: Thread ID to clean up
    """
    try:
        # This is a best-effort cleanup
        # The actual method name depends on the client implementation
        if hasattr(weaviate_client, "delete_by_thread_id"):
            await weaviate_client.delete_by_thread_id(thread_id)
        elif hasattr(weaviate_client, "delete_messages_by_thread"):
            await weaviate_client.delete_messages_by_thread(thread_id)
        else:
            # Fallback: try to get all messages and delete individually
            # This may not be available on all clients
            print(f"Warning: No bulk delete method found for thread {thread_id}")
    except Exception as e:
        # Non-critical cleanup failure
        print(f"Warning: Weaviate cleanup failed for thread {thread_id}: {e}")


# ============================================================================
# Test Data Generators
# ============================================================================


def generate_parallel_tool_calls(
    count: int,
    content_prefix: str = "Tool call",
) -> List[BaseMessage]:
    """
    Generate parallel tool calls + responses.

    Pattern: [TC1, TC2, ..., TCn] → [TR1, TR2, ..., TRn]
    Creates count separate AIMessages (each with 1 tool call) followed by count ToolMessages.

    Args:
        count: Number of tool calls to generate
        content_prefix: Prefix for content

    Returns:
        List with count*2 messages (TCs + TRs)
    """
    messages = []
    tool_call_ids = [f"tc_{uuid4().hex[:8]}" for _ in range(count)]

    # Generate all tool call AIMessages first (bracket opening)
    for i, tc_id in enumerate(tool_call_ids):
        ai_msg = AIMessage(
            content="",
            id=f"ai_{uuid4().hex[:8]}",
            tool_calls=[{
                "id": tc_id,
                "name": f"tool_{i}",
                "args": {"param": f"value_{i}"},
            }],
        )
        messages.append(ai_msg)

    # Then generate all tool responses (bracket closing)
    for i, tc_id in enumerate(tool_call_ids):
        tr_msg = ToolMessage(
            content=f"{content_prefix} {i} result: success",
            tool_call_id=tc_id,
            id=f"tr_{uuid4().hex[:8]}",
        )
        messages.append(tr_msg)

    return messages


def generate_sequential_tool_calls(
    count: int,
    content_prefix: str = "Tool call",
) -> List[BaseMessage]:
    """
    Generate sequential tool calls: TC1 → TR1 → TC2 → TR2 → ...

    Args:
        count: Number of tool call pairs to generate
        content_prefix: Prefix for content

    Returns:
        List with count*2 messages
    """
    messages = []

    for i in range(count):
        tc_id = f"tc_{uuid4().hex[:8]}"

        # Tool call
        ai_msg = AIMessage(
            content="",
            id=f"ai_{uuid4().hex[:8]}",
            tool_calls=[{
                "id": tc_id,
                "name": f"tool_{i}",
                "args": {"param": f"value_{i}"},
            }],
        )
        messages.append(ai_msg)

        # Tool response
        tr_msg = ToolMessage(
            content=f"{content_prefix} {i} result: success",
            tool_call_id=tc_id,
            id=f"tr_{uuid4().hex[:8]}",
        )
        messages.append(tr_msg)

    return messages


def generate_token_heavy_messages(
    count: int,
    tokens_per_message: int,
) -> List[BaseMessage]:
    """
    Generate messages with specific token counts.

    Args:
        count: Number of messages
        tokens_per_message: Approximate tokens per message

    Returns:
        List of messages
    """
    messages = []

    # Rough estimate: 1 token ≈ 4 characters
    chars_per_message = tokens_per_message * 4

    for i in range(count):
        # Alternate between human and AI
        content = "x" * chars_per_message

        if i % 2 == 0:
            msg = HumanMessage(
                content=content,
                id=f"msg_{i}_{uuid4().hex[:8]}",
            )
        else:
            msg = AIMessage(
                content=content,
                id=f"msg_{i}_{uuid4().hex[:8]}",
            )

        messages.append(msg)

    return messages


def generate_mixed_parallel_sequential_tools(
    num_parallel_groups: int,
    num_sequential_pairs: int,
) -> List[BaseMessage]:
    """
    Generate mixed pattern of parallel and sequential tool calls.

    Pattern: [TC1, TC2] → [TR1, TR2] → TC3 → TR3 → [TC4, TC5] → [TR4, TR5] → ...

    Args:
        num_parallel_groups: Number of parallel tool call groups
        num_sequential_pairs: Number of sequential pairs between each parallel group

    Returns:
        List of messages
    """
    messages = []

    for _ in range(num_parallel_groups):
        # Add parallel group (2 tool calls)
        messages.extend(generate_parallel_tool_calls(2, "Parallel"))

        # Add sequential pairs
        messages.extend(generate_sequential_tool_calls(num_sequential_pairs, "Sequential"))

    return messages


# ============================================================================
# Verification Utilities
# ============================================================================


def verify_compaction_result_complete(result: Dict[str, Any]) -> List[str]:
    """
    Comprehensive verification of compaction result.

    Checks:
    1. Required fields present
    2. All compaction outputs are AIMessages
    3. Tool call pairing maintained
    4. No duplicate message IDs

    Args:
        result: Compaction result dictionary

    Returns:
        List of error messages (empty if all checks pass)
    """
    errors = []

    # Check required fields
    if "current_messages" not in result:
        errors.append("Missing 'current_messages' field")

    # Check summarized_messages if present
    if "summarized_messages" in result and result["summarized_messages"]:
        summarized = result["summarized_messages"]

        # Verify AIMessages
        try:
            verify_all_ai_messages(summarized, "summarized_messages")
        except AssertionError as e:
            errors.append(str(e))

        # Verify tool pairing
        pairing_errors = verify_tool_call_pairing(summarized)
        errors.extend(pairing_errors)

        # Verify no duplicate IDs
        try:
            verify_message_id_deduplication(summarized)
        except AssertionError as e:
            errors.append(str(e))

    return errors


def print_message_summary(messages: List[BaseMessage], title: str = "Messages"):
    """
    Print summary of messages for debugging.

    Args:
        messages: Messages to summarize
        title: Title for the summary
    """
    print(f"\n{'='*60}")
    print(f"{title}: {len(messages)} messages")
    print(f"{'='*60}")

    for idx, msg in enumerate(messages):
        msg_type = type(msg).__name__
        msg_id = msg.id or "NO_ID"
        content_preview = msg.content[:50] if msg.content else "NO_CONTENT"

        # Check for tool calls
        has_tool_calls = ""
        if isinstance(msg, AIMessage) and hasattr(msg, "tool_calls") and msg.tool_calls:
            has_tool_calls = f" [TC: {len(msg.tool_calls)}]"
        elif isinstance(msg, ToolMessage):
            has_tool_calls = f" [TR: {msg.tool_call_id}]"

        print(f"[{idx:3d}] {msg_type:15s} {msg_id:30s} {has_tool_calls:20s} {content_preview}")

    print(f"{'='*60}\n")
