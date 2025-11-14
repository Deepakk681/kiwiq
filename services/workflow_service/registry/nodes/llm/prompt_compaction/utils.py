"""
Shared utilities for prompt compaction.

Provides helper functions for:
- Message formatting
- Content hashing
- Time utilities
- Data structures
"""

import hashlib
import json
from datetime import datetime
from enum import Enum
from typing import List, Any, Dict, Optional
from uuid import uuid4

from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
    BaseMessage,
)


# ============================================================================
# Message Section Labels (v2.1)
# ============================================================================

class MessageSectionLabel(str, Enum):
    """Section labels for messages in compaction metadata."""
    SYSTEM = "system"
    MARKED = "marked"
    SUMMARY = "summary"
    SUMMARY_TOOLS = "summary_tools"  # Summary of oversized tool sequence (v2.3)
    EXTRACTED_SUMMARY = "extracted_summary"
    TOOL_CALL = "tool_call"
    TOOL_RESPONSE = "tool_response"
    RECENT = "recent"
    HISTORICAL = "historical"


class GraphEdgeType(str, Enum):
    """Types of edges in the bipartite graph."""
    SUMMARY = "summary"  # Message was summarized
    EXTRACTION = "extraction"  # Message was extracted
    PASSTHROUGH = "passthrough"  # Message passed through unchanged


class ExtractionStrategy(str, Enum):
    """Strategies for constructing extraction messages."""
    DUMP = "dump"  # Dump all chunks as-is
    EXTRACT_FULL = "extract_full"  # Expand chunks to full messages (default)
    LLM_REWRITE = "llm_rewrite"  # LLM rewrites chunks into summary


class ExtractionPlacement(str, Enum):
    """Strategies for placing extracted messages in final compacted output."""
    CHRONOLOGICAL = "chronological"  # Sort by position weight (default)
    END = "end"  # Place all extractions at the end
    BEFORE_LAST_TURN = "before_last_turn"  # Place before last human/AI/tool message


# ============================================================================
# Tool Sequence Conversion
# ============================================================================

def check_and_fix_orphaned_tool_responses(
    old_tools: List[BaseMessage],
    recent: List[BaseMessage],
    strategy_name: str = "COMPACTION"
) -> tuple[List[BaseMessage], List[BaseMessage]]:
    """
    Check if recent section has orphaned tool responses and fix by including them in old_tools.
    
    This prevents tool call pairing errors when old_tools are converted to text.
    If a tool response in 'recent' matches a tool call in 'old_tools', the response
    should be included in old_tools conversion to preserve the pairing.
    
    Args:
        old_tools: Messages in old_tools section (will be converted to text)
        recent: Messages in recent section
        strategy_name: Name of strategy for logging (SUMMARIZATION, EXTRACTION, HYBRID)
        
    Returns:
        Tuple of (updated_old_tools, updated_recent) with orphaned responses moved
        
    Example:
        old_tools = [TC1, TR1]
        recent = [HumanMsg, TC2, TR2]
        → No orphans, return as-is
        
        old_tools = [TC1, TR1, TC2]
        recent = [TR2, HumanMsg]  # TR2 is orphaned (TC2 in old_tools)
        → old_tools = [TC1, TR1, TC2, TR2], recent = [HumanMsg]
    """
    if not old_tools:
        return old_tools, recent
    
    # Collect all tool call IDs from old_tools
    old_tool_call_ids = set()
    for msg in old_tools:
        # OpenAI format: AIMessage with tool_calls attribute
        if isinstance(msg, AIMessage) and hasattr(msg, "tool_calls") and msg.tool_calls:
            for tc in msg.tool_calls:
                old_tool_call_ids.add(tc['id'])
        # Anthropic format: AIMessage with tool_use in content list
        elif isinstance(msg, AIMessage) and isinstance(msg.content, list):
            tool_uses = [c for c in msg.content if isinstance(c, dict) and c.get("type") == "tool_use"]
            for tu in tool_uses:
                if tu.get("id"):
                    old_tool_call_ids.add(tu["id"])
    
    # Check if recent has responses to old tool calls
    orphaned_responses = []
    for msg in recent:
        # OpenAI format: ToolMessage
        if isinstance(msg, ToolMessage) and hasattr(msg, 'tool_call_id') and msg.tool_call_id in old_tool_call_ids:
            orphaned_responses.append(msg)
        # Anthropic format: HumanMessage with tool_result
        elif isinstance(msg, HumanMessage) and isinstance(msg.content, list):
            tool_results = [c for c in msg.content if isinstance(c, dict) and c.get("type") == "tool_result"]
            for tr in tool_results:
                if tr.get("tool_use_id") in old_tool_call_ids:
                    orphaned_responses.append(msg)
                    break
    
    if orphaned_responses:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"[{strategy_name}] Found {len(orphaned_responses)} orphaned tool responses in recent. "
                      f"Including in old_tools conversion to preserve pairing.")
        updated_old_tools = old_tools + orphaned_responses
        updated_recent = [m for m in recent if m not in orphaned_responses]
        return updated_old_tools, updated_recent
    
    return old_tools, recent


def convert_tool_sequence_to_text(messages: List[BaseMessage]) -> List[BaseMessage]:
    """
    Convert tool call/response messages to plain text.
    
    This function strips tool call structures from old tool sequences,
    converting them to plain text descriptions. This prevents orphaned
    tool calls/responses in summarized content while preserving the
    information in a readable format.
    
    Handles both OpenAI format (ToolMessage) and Anthropic format 
    (HumanMessage with tool_result).
    
    Conversion rules:
    - AIMessage with tool_calls → AIMessage with text description of calls
    - ToolMessage → HumanMessage with text description of result
    - HumanMessage with tool_result (Anthropic) → HumanMessage with text
    
    Args:
        messages: List of messages potentially containing tool structures
        
    Returns:
        List of messages with tool structures converted to text.
        Preserves message IDs and metadata.
    """
    converted = []
    
    for msg in messages:
        # Handle AIMessage with tool_calls attribute
        if isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls') and msg.tool_calls:
            # Extract text content from message
            text_parts = []
            if msg.content:
                if isinstance(msg.content, list):
                    # Anthropic format - extract text content from content list
                    text_parts.extend([
                        c.get('text', '') for c in msg.content 
                        if isinstance(c, dict) and c.get('type') == 'text'
                    ])
                else:
                    # OpenAI format - content is string
                    text_parts.append(str(msg.content))
            
            # Add tool call description
            tool_names = [tc.get('name', 'unknown') for tc in msg.tool_calls]
            text_parts.append(f"[Tool calls: {', '.join(tool_names)}]")
            
            # Create new AIMessage without tool_calls attribute
            new_msg = AIMessage(
                content=[{'type': 'text', 'text': " ".join(text_parts)}],
                id=msg.id,
                additional_kwargs=msg.additional_kwargs,
                response_metadata=msg.response_metadata
            )
            converted.append(new_msg)
            
        # Handle ToolMessage (OpenAI format)
        elif isinstance(msg, ToolMessage):
            # Convert to HumanMessage with text description
            # content_preview = str(msg.content)[:500]
            # if len(str(msg.content)) > 500:
            #     content_preview += "..."
            
            new_msg = HumanMessage(
                content=[{'type': 'text', 'text': f"{msg.content}"}],
                id=msg.id,
                additional_kwargs=msg.additional_kwargs,
                response_metadata=msg.response_metadata
            )
            converted.append(new_msg)
            
        # Handle HumanMessage with tool_result in content (Anthropic format)
        elif isinstance(msg, HumanMessage) and isinstance(msg.content, list):
            tool_results = [
                c for c in msg.content 
                if isinstance(c, dict) and c.get("type") == "tool_result"
            ]
            
            if tool_results:
                # Convert tool results to text
                text_parts = []
                for tr in tool_results:
                    result_content = str(tr.get('content', ''))
                    text_parts.append(f"{result_content}")
                
                new_msg = HumanMessage(
                    content=[{'type': 'text', 'text': " ".join(text_parts)}],
                    id=msg.id,
                    additional_kwargs=msg.additional_kwargs,
                    response_metadata=msg.response_metadata
                )
                converted.append(new_msg)
            else:
                # No tool results, keep as-is
                converted.append(msg)
        else:
            # Not a tool message, keep as-is
            converted.append(msg)
    
    return converted


# ============================================================================
# Metadata Helper Functions (v2.1)
# ============================================================================

def set_compaction_metadata(message: BaseMessage, key: str, value: Any) -> None:
    """
    Set compaction metadata on a message.

    Stores metadata under response_metadata["compaction"][key] to avoid
    conflicts with LLM response metadata.

    Args:
        message: Message to set metadata on
        key: Metadata key within compaction namespace
        value: Metadata value
    """
    if "compaction" not in message.response_metadata:
        message.response_metadata["compaction"] = {}
    message.response_metadata["compaction"][key] = value


def get_compaction_metadata(
    message: BaseMessage,
    key: str,
    default: Any = None
) -> Any:
    """
    Get compaction metadata from a message.

    Args:
        message: Message to get metadata from
        key: Metadata key within compaction namespace
        default: Default value if key not found

    Returns:
        Metadata value or default
    """
    compaction = message.response_metadata.get("compaction", {})
    return compaction.get(key, default)


def add_graph_edge(
    message: BaseMessage,
    edge_type: GraphEdgeType,
    full_history_msg_ids: Optional[List[str]] = None,
    summarized_msg_id: Optional[str] = None,
) -> None:
    """
    Add bipartite graph edge to message metadata.

    For summarized messages: stores list of source full history message IDs
    For full history messages: stores the target summarized message ID

    Args:
        message: Message to add edge to
        edge_type: Type of edge (summary, extraction, passthrough)
        full_history_msg_ids: Source message IDs (for summarized messages)
        summarized_msg_id: Target message ID (for full history messages)
    """
    graph_edges = {
        "edge_type": edge_type.value if isinstance(edge_type, GraphEdgeType) else edge_type
    }

    if full_history_msg_ids is not None:
        graph_edges["full_history_msg_ids"] = full_history_msg_ids

    if summarized_msg_id is not None:
        graph_edges["summarized_msg_id"] = summarized_msg_id

    set_compaction_metadata(message, "graph_edges", graph_edges)


def set_section_label(message: BaseMessage, label: MessageSectionLabel) -> None:
    """
    Set the section label for a message.

    Args:
        message: Message to label
        label: Section label
    """
    label_value = label.value if isinstance(label, MessageSectionLabel) else label
    set_compaction_metadata(message, "section_label", label_value)


def get_section_label(message: BaseMessage) -> Optional[str]:
    """
    Get the section label from a message.

    Args:
        message: Message to get label from

    Returns:
        Section label or None
    """
    return get_compaction_metadata(message, "section_label")


def set_extraction_metadata(
    message: BaseMessage,
    chunk_ids: List[str],
    strategy: ExtractionStrategy,
    relevance_scores: Optional[List[float]] = None,
    deduplicated_chunk_ids: Optional[List[str]] = None,
    dedupe_source: Optional[str] = None,
) -> None:
    """
    Set extraction metadata on a message (v2.1).

    Args:
        message: Message to set metadata on
        chunk_ids: IDs of chunks extracted into this message
        strategy: Extraction strategy used
        relevance_scores: Relevance scores parallel to chunk_ids
        deduplicated_chunk_ids: (v2.1) Chunk IDs skipped due to deduplication
        dedupe_source: (v2.1) Which extraction message had the deduplicated chunks
    """
    extraction_metadata = {
        "chunk_ids": chunk_ids,
        "strategy": strategy.value if isinstance(strategy, ExtractionStrategy) else strategy,
    }

    if relevance_scores is not None:
        extraction_metadata["relevance_scores"] = relevance_scores

    if deduplicated_chunk_ids is not None:
        extraction_metadata["deduplicated_chunk_ids"] = deduplicated_chunk_ids

    if dedupe_source is not None:
        extraction_metadata["dedupe_source"] = dedupe_source

    set_compaction_metadata(message, "extraction", extraction_metadata)


def get_extraction_chunk_ids(message: BaseMessage) -> List[str]:
    """
    Get chunk IDs from extraction metadata.

    Args:
        message: Message to get chunk IDs from

    Returns:
        List of chunk IDs (empty if no extraction metadata)
    """
    extraction = get_compaction_metadata(message, "extraction", {})
    return extraction.get("chunk_ids", [])


def set_ingestion_metadata(
    message: BaseMessage,
    chunk_ids: List[str],
    ingested_at: Optional[str] = None,
    section_label: Optional[str] = None,
) -> None:
    """
    Set ingestion metadata on a full history message (v2.1).

    Args:
        message: Message to set metadata on
        chunk_ids: IDs of chunks created from this message
        ingested_at: ISO timestamp of ingestion (default: now)
        section_label: (v2.1) Section label for tracking (e.g., "historical", "marked_overflow")
    """
    ingestion_metadata = {
        "ingested": True,
        "chunk_ids": chunk_ids,
        "ingested_at": ingested_at or datetime.now().isoformat(),
    }

    if section_label is not None:
        ingestion_metadata["section_label"] = section_label

    set_compaction_metadata(message, "ingestion", ingestion_metadata)


def is_message_ingested(message: BaseMessage) -> bool:
    """
    Check if a message has been ingested for extraction.

    Args:
        message: Message to check

    Returns:
        True if ingested, False otherwise
    """
    ingestion = get_compaction_metadata(message, "ingestion", {})
    return ingestion.get("ingested", False)


def get_ingestion_chunk_ids(message: BaseMessage) -> List[str]:
    """
    Get chunk IDs created from a message during ingestion.

    Args:
        message: Message to get chunk IDs from

    Returns:
        List of chunk IDs (empty if not ingested)
    """
    ingestion = get_compaction_metadata(message, "ingestion", {})
    return ingestion.get("chunk_ids", [])


def track_chunk_extraction(message: BaseMessage, chunk_id: str) -> int:
    """
    Track that a chunk was extracted and return its appearance count (v2.1).

    Args:
        message: The extracted summary message
        chunk_id: ID of the chunk that was extracted

    Returns:
        Number of times this chunk has been extracted (including this time)
    """
    extraction = get_compaction_metadata(message, "extraction", {})
    appearance_counts = extraction.get("chunk_appearance_counts", {})

    # Increment count
    current_count = appearance_counts.get(chunk_id, 0)
    appearance_counts[chunk_id] = current_count + 1

    # Update metadata
    extraction["chunk_appearance_counts"] = appearance_counts
    set_compaction_metadata(message, "extraction", extraction)

    return appearance_counts[chunk_id]


def get_chunk_appearance_count(messages: List[BaseMessage], chunk_id: str) -> int:
    """
    Get total appearance count of a chunk across all extraction messages (v2.1).

    Args:
        messages: List of messages (typically summarized history)
        chunk_id: ID of the chunk to check

    Returns:
        Total number of times this chunk has been extracted
    """
    total = 0
    for msg in messages:
        extraction = get_compaction_metadata(msg, "extraction", {})
        if extraction.get("chunk_ids") and chunk_id in extraction.get("chunk_ids", []):
            # This extraction message contains the chunk
            appearance_counts = extraction.get("chunk_appearance_counts", {})
            total += appearance_counts.get(chunk_id, 1)  # Default to 1 if not tracked

    return total


def find_oldest_extraction_with_chunk(messages: List[BaseMessage], chunk_id: str) -> Optional[BaseMessage]:
    """
    Find the oldest extraction message containing a specific chunk (v2.1).

    Args:
        messages: List of messages (typically summarized history)
        chunk_id: ID of the chunk to find

    Returns:
        Oldest message containing the chunk, or None
    """
    candidates = []
    for msg in messages:
        extraction = get_compaction_metadata(msg, "extraction", {})
        if extraction.get("chunk_ids") and chunk_id in extraction.get("chunk_ids", []):
            # Get extraction timestamp
            section_label = get_section_label(msg)
            if section_label == MessageSectionLabel.EXTRACTED_SUMMARY:
                created_at = get_message_metadata(msg, "created_at", "")
                candidates.append((msg, created_at))

    if not candidates:
        return None

    # Sort by timestamp (oldest first)
    candidates.sort(key=lambda x: x[1])
    return candidates[0][0]


def get_deduplicated_chunk_ids(message: BaseMessage) -> List[str]:
    """
    Get deduplicated chunk IDs from extraction metadata (v2.1).

    These are chunks that were relevant but skipped during extraction due to
    already existing in another extraction message.

    Args:
        message: Message to get deduplicated chunk IDs from

    Returns:
        List of deduplicated chunk IDs (empty if none)
    """
    extraction = get_compaction_metadata(message, "extraction", {})
    return extraction.get("deduplicated_chunk_ids", [])


def find_extractions_with_deduplicated_chunk(messages: List[BaseMessage], chunk_id: str) -> List[BaseMessage]:
    """
    Find extraction messages that have a specific chunk in deduplicated_chunk_ids (v2.1).

    Used during reattachment: when an extraction is removed, find which extractions
    had skipped those chunks due to deduplication.

    Args:
        messages: List of messages (typically extraction summaries)
        chunk_id: ID of the chunk to find

    Returns:
        List of messages with this chunk in deduplicated_chunk_ids
    """
    results = []
    for msg in messages:
        deduplicated = get_deduplicated_chunk_ids(msg)
        if chunk_id in deduplicated:
            results.append(msg)

    return results


def move_deduplicated_to_chunk_ids(message: BaseMessage, chunk_ids_to_move: List[str]) -> None:
    """
    Move chunk IDs from deduplicated_chunk_ids to chunk_ids (v2.1 reattachment).

    When an extraction message is removed due to overflow, its chunks can be
    reattached to extraction messages that had them in deduplicated_chunk_ids.

    Args:
        message: Extraction message to update
        chunk_ids_to_move: Chunk IDs to move from deduplicated → active
    """
    extraction = get_compaction_metadata(message, "extraction", {})

    current_chunk_ids = extraction.get("chunk_ids", [])
    current_deduplicated = extraction.get("deduplicated_chunk_ids", [])

    # Move specified chunks
    new_chunk_ids = current_chunk_ids.copy()
    new_deduplicated = []

    for chunk_id in current_deduplicated:
        if chunk_id in chunk_ids_to_move:
            # Move to active chunk_ids
            if chunk_id not in new_chunk_ids:
                new_chunk_ids.append(chunk_id)
        else:
            # Keep in deduplicated
            new_deduplicated.append(chunk_id)

    # Update metadata
    extraction["chunk_ids"] = new_chunk_ids
    extraction["deduplicated_chunk_ids"] = new_deduplicated

    set_compaction_metadata(message, "extraction", extraction)


def hash_content(content: str) -> str:
    """
    Create a hash of message content for deduplication.

    Args:
        content: Message content

    Returns:
        SHA-256 hash of content
    """
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def format_message_for_display(message: BaseMessage, max_length: int = 100) -> str:
    """
    Format a message for display in logs.

    Args:
        message: Message to format
        max_length: Maximum length of content to display

    Returns:
        Formatted string
    """
    content = str(message.content)
    if len(content) > max_length:
        content = content[:max_length] + "..."

    msg_type = message.__class__.__name__
    return f"[{msg_type}] {content}"


def format_messages(messages: List[BaseMessage]) -> str:
    """
    Format multiple messages for LLM prompts (v3.1).
    
    Checks message metadata to identify summaries and marks them appropriately
    to provide context about summarized previous conversations.

    Args:
        messages: List of messages to format

    Returns:
        Formatted string with message history
    """
    formatted = []

    for i, msg in enumerate(messages):
        # Check if this message is a summary of previous conversation
        is_summary = get_message_metadata(msg, "is_summary", False)
        summarized_count = 0
        
        if is_summary:
            summarized_ids = get_message_metadata(msg, "summarized_message_ids", [])
            summarized_count = len(summarized_ids)
        
        if isinstance(msg, SystemMessage):
            formatted.append(f"[System]\n{msg.content}\n")
        elif isinstance(msg, HumanMessage):
            formatted.append(f"[User]\n{msg.content}\n")
        elif isinstance(msg, AIMessage):
            # Determine the message type label
            if is_summary:
                # This is a summary message
                label = f"[Summary of Previous Conversation - {summarized_count} messages]"
            elif msg.tool_calls:
                label = "[Assistant - Tool Calls]"
            else:
                label = "[Assistant]"
            
            formatted.append(f"{label}\n{msg.content}\n")
        elif isinstance(msg, ToolMessage):
            formatted.append(f"[Tool Response]\n{msg.content}\n")
        else:
            formatted.append(f"[{msg.__class__.__name__}]\n{msg.content}\n")

    return "\n".join(formatted)


async def compress_tool_sequence_to_summary(
    tool_sequence: List[BaseMessage],
    target_tokens: int,
    model_metadata: "ModelMetadata",  # type: ignore
    ext_context: Any,
) -> AIMessage:
    """
    Compress a tool call sequence into a comprehensive summary (v2.3).
    
    Creates a flowing narrative summary that preserves:
    - What tools were called and why (intent/purpose)
    - Key results from each tool response
    - Any errors or notable observations
    - The sequence/order of tool execution
    - Any user follow-up questions/requests
    
    This is the shared function used by both compactor and strategies for
    tool sequence summarization.
    
    Args:
        tool_sequence: Tool sequence to compress (calls, responses, interleaved msgs)
        target_tokens: Target token count for summary
        model_metadata: Model metadata for LLM call
        ext_context: External context manager
        
    Returns:
        Tool summary AIMessage with comprehensive metadata
    """
    from workflow_service.registry.nodes.llm.prompt_compaction.llm_utils import call_llm_for_compaction
    
    # Build comprehensive prompt
    prompt = f"""You are compressing a tool execution sequence from a conversation.

CONTEXT:
This is a sequence of tool calls and their responses that occurred in a conversation.
The LLM needs to understand what tools were called and what results were obtained to continue the conversation.

TOOL SEQUENCE:
{format_messages(tool_sequence)}

YOUR TASK:
Create a comprehensive summary that preserves:

1. WHAT tools were called and WHY (intent/purpose)
2. KEY RESULTS from each tool response (important data, not full details)
3. Any ERRORS or NOTABLE OBSERVATIONS
4. The SEQUENCE/ORDER of tool execution if relevant
5. Any user follow-up questions/requests

CRITICAL: The LLM will use this summary to generate its next response. Include enough detail
that the LLM can answer the user's question without access to the original tool outputs.

TARGET LENGTH: Approximately {target_tokens} tokens

OUTPUT FORMAT:
Write a flowing narrative summary (not a list). Be concise but preserve critical information.
"""
    
    # Call LLM
    result = await call_llm_for_compaction(
        prompt=prompt,
        model_metadata=model_metadata,
        ext_context=ext_context,
        max_tokens=target_tokens,
        temperature=0.0,
    )
    
    # Create tool summary message
    tool_summary = create_summary_message(
        content=result["content"],
        summarized_message_ids=[m.id for m in tool_sequence if hasattr(m, 'id') and m.id],
        generation=0,
        token_usage=result["token_usage"],
        cost=result["cost"],
        compression_ratio=len(tool_sequence),
    )
    
    # Add tool-specific metadata
    tool_summary.additional_kwargs.update({
        "tool_summary": True,
        "is_tool_summary": True,  # v2.3 flag
        "original_tool_count": len(tool_sequence),
        "compressed_from": tool_sequence[0].id if tool_sequence else None,
        "compressed_to": tool_sequence[-1].id if tool_sequence else None,
        "tool_sequence_compressed": True,
    })
    
    return tool_summary


def format_message_for_embedding(message: BaseMessage) -> str:
    """
    Format a message for embedding generation.

    Includes message type and content in a structured format.

    Args:
        message: Message to format

    Returns:
        Formatted string for embedding
    """
    msg_type = "unknown"
    if isinstance(message, SystemMessage):
        msg_type = "system"
    elif isinstance(message, HumanMessage):
        msg_type = "user"
    elif isinstance(message, AIMessage):
        msg_type = "assistant"
    elif isinstance(message, ToolMessage):
        msg_type = "tool"

    content = str(message.content)
    return f"[{msg_type}] {content}"


def format_messages_for_embedding(messages: List[BaseMessage]) -> str:
    """
    Format multiple messages for embedding as a single query.

    Args:
        messages: List of messages

    Returns:
        Combined formatted string
    """
    return "\n\n".join([format_message_for_embedding(msg) for msg in messages])


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors.

    Args:
        vec1: First vector
        vec2: Second vector

    Returns:
        Cosine similarity score (0-1)
    """
    import math

    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    magnitude1 = math.sqrt(sum(a * a for a in vec1))
    magnitude2 = math.sqrt(sum(b * b for b in vec2))

    if magnitude1 == 0 or magnitude2 == 0:
        return 0.0

    return dot_product / (magnitude1 * magnitude2)


def parse_salient_points(response_text: str) -> List[Dict[str, Any]]:
    """
    Parse salient points from LLM response.

    Expected format: "[Message N] Point description"

    Args:
        response_text: LLM response text

    Returns:
        List of dicts with 'index' and 'text' keys
    """
    points = []
    lines = response_text.strip().split("\n")

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Try to extract message number and point text
        if line.startswith("[Message "):
            try:
                # Extract: "[Message 5] Point text"
                parts = line.split("]", 1)
                if len(parts) == 2:
                    index_str = parts[0].replace("[Message ", "").strip()
                    index = int(index_str) - 1  # Convert to 0-based index
                    text = parts[1].strip()

                    if text:
                        points.append({"index": index, "text": text})
            except (ValueError, IndexError):
                # If parsing fails, skip this line
                continue

    return points


def create_summary_message(
    content: str,
    summarized_message_ids: List[str],
    generation: int = 0,
    token_usage: Dict[str, int] = None,
    cost: float = 0.0,
    compression_ratio: float = 1.0,
) -> AIMessage:
    """
    Create a summary message with proper metadata (v2.1).

    Args:
        content: Summary content
        summarized_message_ids: IDs of messages this summarizes
        generation: Summary generation level (0=direct, 1=merged, etc.)
        token_usage: Token usage stats
        cost: Cost in USD
        compression_ratio: Compression ratio

    Returns:
        AIMessage with summary metadata and compaction metadata
    """
    msg = AIMessage(
        content=content,
        id=str(uuid4()),
    )

    # Store all metadata in response_metadata["compaction"]
    set_message_metadata(msg, "message_type", "summary")
    set_message_metadata(msg, "is_summary", True)
    set_message_metadata(msg, "summary_generation", generation)
    set_message_metadata(msg, "summarized_message_ids", summarized_message_ids)
    set_message_metadata(msg, "created_at", datetime.now().isoformat())
    set_message_metadata(msg, "compression_ratio", compression_ratio)
    set_message_metadata(msg, "token_usage", token_usage or {})
    set_message_metadata(msg, "cost", cost)

    # Add compaction metadata (v2.1)
    set_section_label(msg, MessageSectionLabel.SUMMARY)
    add_graph_edge(msg, GraphEdgeType.SUMMARY, full_history_msg_ids=summarized_message_ids)
    set_compaction_metadata(msg, "summary", {
        "generation": generation,
        "summarized_message_ids": summarized_message_ids,
        "compression_ratio": compression_ratio,
    })

    return msg


def create_extraction_summary_message(
    content: str,
    source_message_ids: List[str],
    chunk_ids: List[str],
    strategy: ExtractionStrategy,
    relevance_scores: Optional[List[float]] = None,
    token_usage: Dict[str, int] = None,
    cost: float = 0.0,
) -> AIMessage:
    """
    Create an extraction summary message with proper metadata (v2.1).

    Args:
        content: Extracted/summarized content
        source_message_ids: IDs of source messages
        chunk_ids: IDs of chunks extracted
        strategy: Extraction strategy used
        relevance_scores: Relevance scores parallel to chunk_ids
        token_usage: Token usage stats
        cost: Cost in USD

    Returns:
        AIMessage with extraction metadata
    """
    msg = AIMessage(
        content=content,
        id=str(uuid4()),
    )

    # Store all metadata in response_metadata["compaction"]
    set_message_metadata(msg, "message_type", "extracted_summary")
    set_message_metadata(msg, "is_extraction", True)
    set_message_metadata(msg, "created_at", datetime.now().isoformat())
    set_message_metadata(msg, "token_usage", token_usage or {})
    set_message_metadata(msg, "cost", cost)

    # Add compaction metadata (v2.1)
    set_section_label(msg, MessageSectionLabel.EXTRACTED_SUMMARY)
    add_graph_edge(msg, GraphEdgeType.EXTRACTION, full_history_msg_ids=source_message_ids)
    set_extraction_metadata(msg, chunk_ids, strategy, relevance_scores)

    return msg


def create_extracted_message(
    original_message: BaseMessage,
    relevance_score: float,
    extraction_id: str = None,
) -> BaseMessage:
    """
    Create an extracted message with preservation metadata.
    
    CRITICAL (v2.1): Tool calls are STRIPPED from extracted messages to preserve
    tool call pairing integrity. Extraction should only select relevant content,
    not executable tool calls that must remain paired with their responses.

    Args:
        original_message: Original message to mark as extracted
        relevance_score: Similarity/relevance score
        extraction_id: Unique extraction identifier

    Returns:
        Message with extraction metadata (tool calls stripped if present)
    """
    # Extract text content, stripping tool calls if present
    content = original_message.content
    had_tool_calls = False
    
    # Clone the message - ALWAYS create AIMessage for extracted content (no tool calls)
    if isinstance(original_message, AIMessage):
        # Strip tool calls - extract only text content
        had_tool_calls = bool(original_message.tool_calls)
        
        # Extract text from content (handle both string and list formats)
        if isinstance(content, list):
            # Anthropic format: list of content blocks
            # Filter out tool_use blocks (similar to llm_node.py lines 2405-2425)
            text_parts = []
            for block in content:
                if isinstance(block, dict):
                    # Skip tool_use blocks entirely - they break pairing
                    if block.get("type") == "tool_use":
                        continue
                    # Keep text blocks
                    if block.get("type") == "text":
                        text_parts.append(block.get("text", ""))
                elif isinstance(block, str):
                    text_parts.append(block)
            
            # Convert to string content (extracted messages don't need complex content format)
            content = "\n".join(text_parts) if text_parts else "[Extracted: content contained only tool calls]"
        
        # If content is empty after stripping tool calls, provide placeholder
        if not content or (isinstance(content, str) and not content.strip()):
            content = "[Extracted: content contained only tool calls]"
        
        # Create AIMessage WITHOUT tool calls - explicitly set to empty list
        extracted = AIMessage(
            content=content,  # Simple string content, no tool_use blocks
            id=original_message.id,
            tool_calls=[],  # Explicitly clear tool calls to preserve pairing integrity
        )
    elif isinstance(original_message, HumanMessage):
        # Human messages may contain tool results - extract only text
        if isinstance(content, list):
            text_parts = []
            for block in content:
                if isinstance(block, dict):
                    # Skip tool_result blocks entirely - they break pairing
                    if block.get("type") == "tool_result":
                        continue
                    # Keep text blocks
                    if block.get("type") == "text":
                        text_parts.append(block.get("text", ""))
                elif isinstance(block, str):
                    text_parts.append(block)
            
            # Convert to simple string content
            content = "\n".join(text_parts) if text_parts else "[Extracted: content contained only tool results]"
        
        # If content is empty after stripping, provide placeholder
        if not content or (isinstance(content, str) and not content.strip()):
            content = "[Extracted: content contained only tool results]"
        
        extracted = HumanMessage(
            content=content,  # Simple string content, no tool_result blocks
            id=original_message.id,
        )
    elif isinstance(original_message, SystemMessage):
        extracted = SystemMessage(
            content=content,
            id=original_message.id,
        )
    elif isinstance(original_message, ToolMessage):
        # Tool messages should not be extracted individually (breaks pairing)
        # Convert to AIMessage with text content only
        extracted = AIMessage(
            content=f"[Tool Result]: {content}",
            id=original_message.id,
            tool_calls=[],  # No tool calls in extracted tool messages
        )
    else:
        extracted = original_message

    # Add extraction metadata to response_metadata["compaction"]
    set_message_metadata(extracted, "extracted", True)
    set_message_metadata(extracted, "dont_summarize", True)
    set_message_metadata(extracted, "extraction_id", extraction_id or f"extract_{original_message.id}_{int(datetime.now().timestamp())}")
    set_message_metadata(extracted, "relevance_score", relevance_score)
    set_message_metadata(extracted, "extracted_at", datetime.now().isoformat())
    set_message_metadata(extracted, "tool_calls_stripped", had_tool_calls)  # Track if tool calls were removed

    return extracted


def get_message_metadata(message: BaseMessage, key: str, default: Any = None) -> Any:
    """
    Safely get metadata from a message.

    Args:
        message: Message to get metadata from
        key: Metadata key
        default: Default value if key not found

    Returns:
        Metadata value or default
    """
    if "compaction" not in message.response_metadata:
        return default
    return message.response_metadata["compaction"].get(key, default)


def set_message_metadata(message: BaseMessage, key: str, value: Any) -> None:
    """
    Set metadata on a message.

    Args:
        message: Message to set metadata on
        key: Metadata key
        value: Metadata value
    """
    if "compaction" not in message.response_metadata:
        message.response_metadata["compaction"] = {}
    if value is None and key in message.response_metadata["compaction"]:
        del message.response_metadata["compaction"][key]
    else:
        message.response_metadata["compaction"][key] = value


def assign_position_weights(
    messages: List[BaseMessage],
    original_indices: Dict[str, int],
) -> None:
    """
    Assign position weights to messages for chronological ordering.
    
    Args:
        messages: Messages to assign weights to
        original_indices: Map of message.id -> original index
    """
    for msg in messages:
        if hasattr(msg, 'id') and msg.id and msg.id in original_indices:
            set_message_metadata(msg, "position_weight", float(original_indices[msg.id]))


def sort_messages_by_weight(
    messages: List[BaseMessage],
    extraction_placement: ExtractionPlacement = ExtractionPlacement.CHRONOLOGICAL,
    full_history_indices: Optional[Dict[str, int]] = None,
) -> List[BaseMessage]:
    """
    Sort messages by position weight with configurable extraction placement.
    
    Args:
        messages: Messages to sort
        extraction_placement: How to place extracted messages (ExtractionPlacement.CHRONOLOGICAL, ExtractionPlacement.END, ExtractionPlacement.BEFORE_LAST_TURN)
        full_history_indices: Fallback indices for messages without position_weight
    
    Returns:
        Sorted messages
    """
    from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
    
    def get_weight(msg: BaseMessage) -> float:
        """Get message weight with fallback to full_history_indices."""
        # Try metadata first
        weight = get_message_metadata(msg, "position_weight", None)
        if weight is not None:
            return float(weight)
        
        # Fallback to full_history_indices if available
        if full_history_indices and hasattr(msg, 'id') and msg.id:
            if msg.id in full_history_indices:
                return float(full_history_indices[msg.id])
        
        # Last resort: infinity (places at end)
        return float('inf')
    
    if extraction_placement == ExtractionPlacement.CHRONOLOGICAL:
        # Simple sort by position weight
        return sorted(messages, key=get_weight)
    
    elif extraction_placement == ExtractionPlacement.END:
        # Separate extracted and non-extracted messages
        extracted = [m for m in messages if get_message_metadata(m, "extracted", False)]
        non_extracted = [m for m in messages if not get_message_metadata(m, "extracted", False)]
        
        # Sort non-extracted by weight
        non_extracted_sorted = sorted(non_extracted, key=get_weight)
        
        # Append extracted at the end
        return non_extracted_sorted + extracted
    
    elif extraction_placement == ExtractionPlacement.BEFORE_LAST_TURN:
        # Separate extracted and non-extracted messages
        extracted = [m for m in messages if get_message_metadata(m, "extracted", False)]
        non_extracted = [m for m in messages if not get_message_metadata(m, "extracted", False)]
        
        # Sort non-extracted by weight
        non_extracted_sorted = sorted(non_extracted, key=get_weight)
        
        # Find last human/AI/tool message index
        last_turn_idx = len(non_extracted_sorted)
        for i in range(len(non_extracted_sorted) - 1, -1, -1):
            msg = non_extracted_sorted[i]
            if isinstance(msg, (HumanMessage, AIMessage, ToolMessage)):
                last_turn_idx = i
                break
        
        # Insert extracted messages before last turn
        return non_extracted_sorted[:last_turn_idx] + extracted + non_extracted_sorted[last_turn_idx:]
    
    else:
        # Default to chronological
        return sorted(messages, key=lambda msg: get_message_metadata(msg, "position_weight", float('inf')))


class ContextBudgetError(Exception):
    """Raised when context budget constraints are violated."""
    pass


class CompactionError(Exception):
    """Raised when compaction fails."""
    pass


def calculate_adaptive_compression_ratio(
    current_usage: int,
    available_budget: int,
    target_pct: float = 50.0,
    min_ratio: float = 5.0,
    max_ratio: float = 100.0,
) -> float:
    """
    Calculate adaptive compression ratio based on current usage (v2.0).

    Formula:
    target_tokens = available_budget * (target_pct / 100)
    compression_ratio = current_usage / target_tokens

    Bounded by [min_ratio, max_ratio]

    Args:
        current_usage: Current token usage
        available_budget: Available input token budget
        target_pct: Target percentage of budget after compaction (default 50%)
        min_ratio: Minimum compression ratio (default 5.0 = 1:5)
        max_ratio: Maximum compression ratio (default 100.0 = 1:100)

    Returns:
        Compression ratio (e.g., 10.0 means compress to 1/10th of original size)
    """
    if current_usage <= 0 or available_budget <= 0:
        return 1.0

    # Calculate target tokens after compaction
    target_tokens = available_budget * (target_pct / 100.0)

    # Calculate required compression ratio
    ratio = current_usage / target_tokens if target_tokens > 0 else 1.0

    # Bound the ratio
    ratio = max(min_ratio, min(ratio, max_ratio))

    return ratio


def calculate_summary_bandwidth(
    available_budget: int,
    summary_limit: int,
    current_summary_usage: int,
) -> int:
    """
    Calculate available bandwidth for new summaries (v2.0).

    Used in auto_bandwidth mode for adaptive compression.

    Args:
        available_budget: Available input token budget
        summary_limit: Maximum tokens allocated for summaries
        current_summary_usage: Current summary token usage

    Returns:
        Available tokens for new summaries
    """
    remaining = summary_limit - current_summary_usage
    return max(0, remaining)


# ==================== CHUNK RE-ATTACHMENT TRACKING (v2.1) ====================


def track_removed_chunk_ids(
    removed_extraction: BaseMessage,
    pending_reattachment: Dict[str, Dict[str, Any]],
) -> None:
    """
    Track chunk IDs from a removed extraction message for future re-attachment (v2.1).

    When an extraction message is removed due to duplicate overflow, we track which
    chunk IDs were lost so they can be re-attached to the next extraction message
    that actually extracts those chunks again.

    This prevents context bloat from duplication while ensuring no chunks are permanently lost.

    Args:
        removed_extraction (BaseMessage): The extraction message being removed
            - Must have extraction metadata with chunk_ids
        pending_reattachment (Dict[str, Dict[str, Any]]): Dict to track pending chunks
            - Key: chunk_id
            - Value: Dict with metadata about removal

    Returns:
        None (modifies pending_reattachment in-place)

    Example:
        ```python
        # Extraction message being removed has chunks: ["chunk_1", "chunk_2", "chunk_3"]
        pending = {}

        track_removed_chunk_ids(old_extraction, pending)
        # pending now contains:
        # {
        #     "chunk_1": {"original_extraction_id": "msg_abc", "removed_at": "2025-11-10T..."},
        #     "chunk_2": {"original_extraction_id": "msg_abc", "removed_at": "2025-11-10T..."},
        #     "chunk_3": {"original_extraction_id": "msg_abc", "removed_at": "2025-11-10T..."},
        # }
        ```

    Cross-references:
        - Called by: strategies.py:_check_and_handle_duplicates() when removing old extraction
        - Used with: get_pending_chunks_for_reattachment() to retrieve pending chunks
        - Used with: attach_pending_chunks_to_extraction() to re-attach chunks

    Notes:
        - Chunks are tracked by their chunk_id from extraction metadata
        - Tracks removal timestamp and original extraction message ID
        - If chunk already in pending dict, updates metadata with latest removal
        - Thread-safe when used within single compaction cycle
    """
    from datetime import datetime

    chunk_ids = get_extraction_chunk_ids(removed_extraction)

    if not chunk_ids:
        return

    removal_timestamp = datetime.now().isoformat()

    for chunk_id in chunk_ids:
        pending_reattachment[chunk_id] = {
            "original_extraction_id": removed_extraction.id,
            "removed_at": removal_timestamp,
            "original_message_type": type(removed_extraction).__name__,
        }


def get_pending_chunks_for_reattachment(
    new_extraction_chunk_ids: List[str],
    pending_reattachment: Dict[str, Dict[str, Any]],
) -> List[str]:
    """
    Get list of pending chunk IDs that should be re-attached to a new extraction (v2.1).

    When creating a new extraction message, checks if any of the chunks being extracted
    are in the pending re-attachment list. Returns those chunk IDs so they can be
    added to the new extraction's metadata.

    This implements the "smart re-attachment" where chunks are only re-attached to
    extraction messages that actually extract those chunks again (not just the latest).

    Args:
        new_extraction_chunk_ids (List[str]): Chunk IDs in the new extraction message
        pending_reattachment (Dict[str, Dict[str, Any]]): Pending chunks awaiting re-attachment
            - Key: chunk_id
            - Value: Metadata about removal

    Returns:
        List[str]: Chunk IDs from pending list that appear in new extraction
            - Subset of new_extraction_chunk_ids
            - Only includes chunks that were previously removed

    Example:
        ```python
        pending = {
            "chunk_1": {...},
            "chunk_2": {...},
            "chunk_5": {...},
        }

        new_chunks = ["chunk_1", "chunk_3", "chunk_5"]

        reattach = get_pending_chunks_for_reattachment(new_chunks, pending)
        # Returns: ["chunk_1", "chunk_5"]  (intersection of new and pending)
        ```

    Cross-references:
        - Called by: strategies.py:_construct_extraction_message() when creating new extraction
        - Works with: track_removed_chunk_ids() for tracking
        - Works with: attach_pending_chunks_to_extraction() for re-attachment

    Notes:
        - Only returns chunks that are BOTH in new extraction AND in pending list
        - Does not modify pending_reattachment (read-only operation)
        - Returns empty list if no overlap between new and pending chunks
    """
    return [
        chunk_id
        for chunk_id in new_extraction_chunk_ids
        if chunk_id in pending_reattachment
    ]


def attach_pending_chunks_to_extraction(
    extraction_message: BaseMessage,
    pending_chunk_ids: List[str],
    pending_reattachment: Dict[str, Dict[str, Any]],
) -> None:
    """
    Attach pending chunk IDs to a new extraction message and clear from pending (v2.1).

    When a new extraction message is created and it extracts chunks that were previously
    removed, this function:
    1. Adds the pending chunks to the extraction message's metadata
    2. Removes those chunks from the pending re-attachment dict

    This completes the re-attachment cycle for those chunks.

    Args:
        extraction_message (BaseMessage): The new extraction message
            - Will have its metadata updated with re-attached chunks
        pending_chunk_ids (List[str]): Chunk IDs to re-attach
            - Should come from get_pending_chunks_for_reattachment()
        pending_reattachment (Dict[str, Dict[str, Any]]): Pending chunks dict
            - Chunks in pending_chunk_ids will be removed from this dict

    Returns:
        None (modifies extraction_message and pending_reattachment in-place)

    Example:
        ```python
        new_extraction = AIMessage(content="...")
        pending_chunks = ["chunk_1", "chunk_5"]
        pending = {
            "chunk_1": {"removed_at": "2025-11-10T...", ...},
            "chunk_5": {"removed_at": "2025-11-10T...", ...},
        }

        attach_pending_chunks_to_extraction(new_extraction, pending_chunks, pending)

        # new_extraction now has metadata:
        # extraction_metadata["reattached_chunks"] = {
        #     "chunk_1": {"original_extraction_id": "...", "removed_at": "...", "reattached_at": "..."},
        #     "chunk_5": {...},
        # }

        # pending is now empty: {}
        ```

    Cross-references:
        - Called by: strategies.py:_construct_extraction_message() after creating extraction
        - Works with: track_removed_chunk_ids() and get_pending_chunks_for_reattachment()

    Notes:
        - Adds "reattached_at" timestamp to metadata
        - Removes chunks from pending dict after re-attachment
        - If extraction metadata doesn't exist, creates it
        - Thread-safe within single compaction cycle
    """
    from datetime import datetime

    if not pending_chunk_ids:
        return

    # Get or create extraction metadata
    extraction = get_compaction_metadata(extraction_message, "extraction", {})

    if "reattached_chunks" not in extraction:
        extraction["reattached_chunks"] = {}

    reattachment_timestamp = datetime.now().isoformat()

    # Add each pending chunk to reattached_chunks metadata
    for chunk_id in pending_chunk_ids:
        if chunk_id in pending_reattachment:
            original_metadata = pending_reattachment[chunk_id]
            extraction["reattached_chunks"][chunk_id] = {
                **original_metadata,
                "reattached_at": reattachment_timestamp,
            }

            # Remove from pending now that it's been re-attached
            del pending_reattachment[chunk_id]

    # Update message metadata
    set_compaction_metadata(extraction_message, "extraction", extraction)
