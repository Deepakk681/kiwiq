# Prompt Compaction v2.1 - Implementation Reference

**Version:** 2.1
**Last Updated:** 2025-11-11
**Status:** Production Ready - All Features Implemented and Tested

---

## Overview

This document provides a comprehensive implementation reference for the Prompt Compaction system, including file structure, class hierarchies, key methods, code patterns, and integration points.

**Key Features:**
- **v2.0**: Adaptive compression, dynamic reallocation, tool compression
- **v2.1**: Message chunking, deduplication, chunk expansion, overflow handling

---

## Table of Contents

1. [File Structure](#file-structure)
2. [Configuration Classes](#configuration-classes)
3. [Core Classes and Methods](#core-classes-and-methods)
4. [Implementation Patterns](#implementation-patterns)
5. [Metadata System](#metadata-system)
6. [Integration Points](#integration-points)
7. [Testing Infrastructure](#testing-infrastructure)

---

## File Structure

### Core Implementation Files

```
services/workflow_service/registry/nodes/llm/prompt_compaction/
├── __init__.py                  # Public API exports (74 lines)
├── compactor.py                 # Main orchestrator (1362 lines)
│   ├── PromptCompactionConfig   # Main configuration
│   ├── PromptCompactor          # Main orchestrator class
│   └── 9 config classes         # SummarizationConfig, ExtractionConfig, etc.
├── strategies.py                # Strategy implementations (2344 lines)
│   ├── CompactionStrategy       # Abstract base class
│   ├── NoOpStrategy             # Pass-through (no compaction)
│   ├── SummarizationStrategy    # **v3.0 LINEAR BATCHING** summarization (NO hierarchical merge)
│   ├── ExtractionStrategy       # Vector-based extraction (v2.1)
│   └── HybridStrategy           # Extract + summarize (v2.1)
├── context_manager.py           # Budget & classification (1246 lines)
│   ├── ContextBudgetConfig      # Budget allocation config
│   ├── ContextBudget            # Calculated budgets
│   ├── MessageClassifier        # Message section classification with **v2.3 MAX SPAN** tool grouping
│   └── BudgetEnforcer           # Budget enforcement with dynamic reallocation
├── utils.py                     # Shared utilities (1355 lines)
│   ├── Metadata helpers         # v2.1 bipartite graph metadata system
│   ├── Message creation         # create_summary_message(), create_extraction_summary_message()
│   ├── **v2.3 Tool conversion** # convert_tool_sequence_to_text(), check_and_fix_orphaned_tool_responses()
│   └── **v2.3 Compression**     # compress_tool_sequence_to_summary() - Tool sequence summarization
├── llm_utils.py                 # LLM calling utilities (239 lines)
│   ├── get_compaction_model()   # Model provider selection (Perplexity fallback)
│   ├── create_compaction_retry_decorator()  # Tenacity retries with exponential backoff
│   ├── call_llm_for_compaction()  # LLM calling with proper cost tracking
│   └── get_embeddings_batch()   # Batch embedding generation
├── token_utils.py               # Token counting (1581 lines)
│   ├── get_encoder_for_model()  # Model-specific tiktoken encoders
│   ├── count_tokens_anthropic() # Anthropic API token counting
│   ├── count_tokens()           # Universal token counting
│   ├── chunk_message_for_embedding()  # Message chunking (v2.1)
│   ├── binary_search_message_count()  # Budget-aware message fitting
│   └── call_llm_with_batch_splitting()  # Oversized message handling
└── billing.py                   # Billing integration (205 lines)
    ├── bill_summarization()     # LLM summarization cost tracking
    ├── bill_extraction()        # Embedding cost tracking
    └── bill_hybrid()            # Combined cost tracking

libs/src/weaviate_client/
├── base_client.py               # Base Weaviate client
├── docchunk_client.py           # Document chunks
└── thread_message_client.py     # Thread message chunks (v2.1)
```

### Test Files

**Unit Tests (16 files, 177 tests total):**
```
tests/unit/services/workflow_service/registry/nodes/llm/prompt_compaction/
├── test_base.py (1 test)
├── test_dual_history.py (13 tests)
├── test_edge_cases.py (13 tests)
├── test_extraction_strategy.py (13 tests)
├── test_hybrid_strategy.py (8 tests)
├── test_jit_ingestion.py (11 tests)
├── test_metadata_propagation.py (29 tests)
├── test_metadata.py (16 tests)
├── test_runtime_config.py (18 tests)
├── test_v21_chunking.py (8 tests)
├── test_v21_config_parameters.py (7 tests)
├── test_v21_deduplication.py (10 tests)
├── test_v21_expansion.py (10 tests)
├── test_v21_marked_overflow.py (6 tests)
├── test_v21_reattachment.py (8 tests)
└── test_v21_utility_functions.py (6 tests)
```

**Integration Tests (24 files, 195 tests total):**
```
tests/integration/services/workflow_service/registry/nodes/llm/prompt_compaction/
├── test_batch_splitting_integration.py (8 tests)
├── test_compaction_output_message_types.py (10 tests)
├── test_complex_scenarios.py (5 tests)
├── test_comprehensive_multi_turn_workflows.py (18 tests)
├── test_cross_provider_compaction.py (12 tests)
├── test_current_messages_metadata_flow.py (12 tests)
├── test_extreme_token_scenarios.py (10 tests)
├── test_hybrid_strategy_integration.py (3 tests)
├── test_jit_ingestion_integration.py (7 tests)
├── test_message_id_deduplication.py (15 tests)
├── test_multi_turn_iterative_compaction.py (10 tests)
├── test_oversized_messages_integration.py (5 tests)
├── test_oversized_strategies_integration.py (6 tests)
├── test_real_provider_message_histories.py (15 tests)
├── test_simple_batch_splitting.py (2 tests)
├── test_token_counting_integration.py (7 tests)
├── test_tool_call_pairing_edge_cases.py (20 tests)
├── test_v21_chunking_integration.py (6 tests)
├── test_v21_deduplication_integration.py (5 tests)
├── test_v21_end_to_end_integration.py (5 tests)
├── test_v21_expansion_integration.py (6 tests)
├── test_v21_marked_overflow_integration.py (4 tests)
└── test_v21_section_labels_integration.py (4 tests)
```

---

## Configuration Classes

### Complete Configuration Hierarchy (compactor.py)

#### 1. ContextBudgetConfig (context_manager.py:40)
```python
class ContextBudgetConfig(BaseModel):
    """Token budget allocation percentages."""
    system_prompt_max_pct: float = 0.10        # 10% for system/tools
    summary_max_pct: float = 0.20              # 20% for summaries
    marked_messages_max_pct: float = 0.10      # 10% for marked
    recent_messages_min_pct: float = 0.40      # 40% for recent (guaranteed)
    buffer_pct: float = 0.10                   # 10% safety buffer
```

#### 2. SummarizationConfig (compactor.py:68)
```python
class SummarizationConfig(BaseModel):
    """Summarization strategy configuration."""
    mode: SummarizationMode = CONTINUED        # FROM_SCRATCH | CONTINUED
    model: Optional[str] = None                # LLM model override
    provider: Optional[LLMModelProvider] = None
    max_summary_tokens: int = 2000             # Max per summary
    preserve_tool_calls: bool = True           # Atomic tool sequences
    preserve_structured_outputs: bool = True   # JSON/code blocks
    max_summary_chunks: int = 5                # Hierarchical merge threshold
    merge_threshold: float = 0.8               # 80% budget triggers merge
```

#### 3. ExtractionConfig (compactor.py:148) - v2.1
```python
class ExtractionConfig(BaseModel):
    """Extraction strategy configuration (v2.1 enhanced)."""
    # Basic extraction
    construction_strategy: ExtractionStrategyType = EXTRACT_FULL
    top_k: int = 5
    similarity_threshold: float = 0.7
    embedding_model: str = "text-embedding-3-small"

    # Message chunking (v2.1)
    enable_message_chunking: bool = True       # For >6K messages
    chunk_size_tokens: int = 6000
    chunk_overlap_tokens: int = 200
    chunk_strategy: str = "semantic_overlap"   # semantic_overlap | fixed_token
    chunk_score_aggregation: str = "max"       # max | mean | weighted_mean

    # Chunk expansion (v2.1)
    expansion_mode: str = "full_message"       # full_message | top_chunks_only | hybrid
    max_expansion_tokens: int = 50000
    max_chunks_per_message: int = 10

    # Deduplication (v2.1)
    deduplication: bool = True                 # Within-cycle
    allow_duplicate_chunks: bool = True        # Cross-cycle
    max_duplicate_appearances: int = 3

    # Overflow handling (v2.1)
    overflow_strategy: str = "remove_oldest"   # remove_oldest | reduce_duplicates | error

    # Storage
    store_embeddings: bool = True
    cleanup_old_threads_days: Optional[int] = None
```

#### 4. HybridConfig (compactor.py:377) - v2.1
```python
class HybridConfig(BaseModel):
    """Hybrid strategy configuration (v2.1)."""
    extraction_config: ExtractionConfig = Field(default_factory=ExtractionConfig)
    summarization_config: SummarizationConfig = Field(default_factory=SummarizationConfig)
    extraction_first: bool = True              # Extract before summarize
    extraction_pct: float = 0.05               # 5% of budget for extraction (v2.1)
```

#### 5. AdaptiveCompressionConfig (compactor.py:424)
```python
class AdaptiveCompressionConfig(BaseModel):
    """Adaptive compression configuration (v2.0)."""
    mode: str = "adaptive"                     # adaptive | fixed_ratio | auto_bandwidth
    fixed_compression_ratio: Optional[float] = None
    min_compression_ratio: float = 5.0         # Min 1:5
    max_compression_ratio: float = 100.0       # Max 1:100
    target_context_pct: float = 50.0           # Target 50% post-compaction
    use_summary_bandwidth: bool = False
```

#### 6. DynamicReallocationConfig (compactor.py:491)
```python
class DynamicReallocationConfig(BaseModel):
    """Dynamic budget reallocation (v2.0)."""
    enabled: bool = True
    reallocation_priority: List[str] = ["summaries", "recent", "marked", "tools"]
    min_sacred_buffer_pct: float = 20.0        # Never reallocate
    system_prompts_excluded: bool = True
```

#### 7. ToolCompressionConfig (compactor.py:536)
```python
class ToolCompressionConfig(BaseModel):
    """Tool compression configuration (v2.0)."""
    enabled: bool = True
    tool_exception_threshold_pct: float = 30.0  # Allow 80% if tools < 30%
    max_context_with_tools_pct: float = 80.0
    include_user_msg_after_tool: bool = True
    min_cooldown_messages: int = 5
```

#### 8. CompactionLLMConfig (compactor.py:590)
```python
class CompactionLLMConfig(BaseModel):
    """LLM configuration for compaction (v2.1)."""
    default_provider: str = "openai"
    default_model: str = "gpt-4o-mini"
    perplexity_fallback_provider: str = "anthropic"
    perplexity_fallback_model: str = "claude-sonnet-4-5"
    max_retries: int = 3
    retry_wait_exponential_multiplier: int = 1
    retry_wait_exponential_max: int = 10
```

#### 9. PromptCompactionConfig (compactor.py:661)
```python
class PromptCompactionConfig(BaseModel):
    """Main prompt compaction configuration."""
    enabled: bool = True
    strategy: CompactionStrategyType = HYBRID

    # Budget allocation
    context_budget: ContextBudgetConfig = Field(default_factory=ContextBudgetConfig)

    # Strategy configs
    summarization: SummarizationConfig = Field(default_factory=SummarizationConfig)
    extraction: ExtractionConfig = Field(default_factory=ExtractionConfig)
    hybrid: HybridConfig = Field(default_factory=HybridConfig)

    # v2.0 features
    adaptive_compression: AdaptiveCompressionConfig = Field(default_factory=AdaptiveCompressionConfig)
    dynamic_reallocation: DynamicReallocationConfig = Field(default_factory=DynamicReallocationConfig)
    tool_compression: ToolCompressionConfig = Field(default_factory=ToolCompressionConfig)

    # v2.1 features
    llm_config: CompactionLLMConfig = Field(default_factory=CompactionLLMConfig)

    # Message preservation
    recent_message_count: int = 8
    preserve_tool_call_sequences: bool = True

    # Triggers
    trigger_threshold_pct: float = 0.80        # Compact at 80%
    warning_threshold_pct: float = 0.70        # Warn at 70%
    target_usage_pct: float = 0.50             # Target 50% post-compaction
```

---

## Core Classes and Methods

### PromptCompactor (compactor.py)

Main orchestrator for prompt compaction.

**Key Methods:**

```python
def should_compact(
    messages: List[BaseMessage],
    model_metadata: ModelMetadata,
) -> Tuple[bool, Dict[str, Any]]:
    """Check if compaction needed (>80% usage)."""
    # Returns: (should_compact, usage_info)

async def test_compact_if_needed(
    messages: List[BaseMessage],
    model_metadata: ModelMetadata,
    ext_context: Any,
) -> CompactionResult:
    """Main entry point: compact if threshold exceeded."""
    # v2.5 Single-round compaction:
    # - Classify messages (tools merged into recent/historical)
    # - Dynamic budget adjustment (expand recent if has latest tools)
    # - Compact historical only (recent always preserved)

async def compact(
    messages: List[BaseMessage],
    model_metadata: ModelMetadata,
    ext_context: Any,
    force: bool = False,
) -> CompactionResult:
    """Execute compaction strategy."""
    # Steps:
    # 1. Calculate budget
    # 2. Classify messages
    # 3. Enforce budget
    # 4. Execute strategy
    # 5. Track billing
```

**Location:** `services/workflow_service/registry/nodes/llm/prompt_compaction/compactor.py`

---

### Strategies (strategies.py)

#### BaseStrategy (strategies.py:45)
```python
class BaseStrategy(ABC):
    """Abstract base for compaction strategies."""

    @abstractmethod
    async def compact(
        self,
        sections: Dict[str, List[BaseMessage]],
        budget: ContextBudget,
        model_metadata: ModelMetadata,
        ext_context: Any,
    ) -> CompactionResult:
        """Execute compaction strategy."""
        pass
```

#### SummarizationStrategy (strategies.py:442-959)

**v3.0 LINEAR BATCHING** summarization (NO hierarchical merge).

**Key Methods:**
- `compact()`: Main entry point
- `_summarize_continued()`: **v3.0 linear batching** - parallel batch summarization with equal budget distribution
- `_summarize_single_batch()`: Summarize one batch with target token limit
- `_calculate_compression_ratio()`: Adaptive compression (v2.0)

**v3.0 Architecture Change:**
- ❌ **Removed**: Hierarchical merging (caused infinite loops)
- ✅ **New**: Linear batching with `target_tokens = budget / num_batches`
- ✅ **Benefit**: Predictable LLM call count (exactly N calls for N batches)
- ✅ **Benefit**: No infinite loop risks

**v2.1 Enhancements:**
- Section labels on all outputs
- Passthrough graph edges for non-summarized messages

#### ExtractionStrategy (strategies.py:621) - v2.1

Vector-based extraction with semantic search.

**Key Methods (v2.1):**
```python
async def compact(...) -> CompactionResult:
    """Main extraction flow."""
    # 1. JIT ingestion (if needed)
    # 2. Extract relevant chunks
    # 3. Apply deduplication
    # 4. Expand to full messages or use chunks
    # 5. Handle overflow
    # 6. Add section labels

async def _jit_ingest_messages(...) -> List[BaseMessage]:
    """Ingest messages to Weaviate (v2.1)."""
    # Check is_message_ingested()
    # Chunk if enable_message_chunking=True
    # Embed chunks
    # Store in Weaviate

async def _extract_relevant_messages(...) -> List[AIMessage]:
    """Extract using semantic search (v2.1)."""
    # Query recent messages
    # Retrieve top-K chunks
    # Apply construction strategy:
    #   - DUMP: Concatenate chunks
    #   - EXTRACT_FULL: Expand to full messages
    #   - LLM_REWRITE: Rewrite with LLM

def _check_and_handle_duplicates(...) -> List[AIMessage]:
    """Handle overflow from duplicate chunks (v2.1)."""
    # Track appearance_count
    # Remove oldest if exceeds max_duplicate_appearances
```

**Construction Strategies (strategies.py:1183-1254):**
- **DUMP** (1183-1195): Concatenate chunks as-is
- **EXTRACT_FULL** (1197-1233): Expand chunks to full messages (default)
- **LLM_REWRITE** (1235-1254): LLM rewrites chunks

**Location:** `services/workflow_service/registry/nodes/llm/prompt_compaction/strategies.py:621-1262`

#### HybridStrategy (strategies.py:1264) - v2.1

Combines extraction + summarization with budget allocation.

**Key Method (v2.1):**
```python
async def compact(...) -> CompactionResult:
    """Hybrid: Extract first, then summarize remainder."""
    # Calculate budgets
    extraction_budget = available * self.extraction_pct  # v2.1
    summarization_budget = available - extraction_budget

    # Phase 1: Extract relevant context
    extraction_result = await self.extraction_strategy.compact(...)

    # Phase 2: Summarize remaining
    summarization_result = await self.summarization_strategy.compact(...)

    # Combine with section labels (v2.1)
    # System → Summaries → Extracted → Marked → Tools → Recent
```

**Location:** `services/workflow_service/registry/nodes/llm/prompt_compaction/strategies.py:1264-1565`

---

### MessageClassifier (context_manager.py:372-474)

Classifies messages into sections with **v2.3 MAX SPAN** tool sequence grouping.

**Key Method:**
```python
def classify_messages(
    self,
    messages: List[BaseMessage],
    context_budget: ContextBudget,
    config: PromptCompactionConfig,
) -> Dict[str, List[BaseMessage]]:
    """Classify messages into 8 sections (v2.3 MAX SPAN)."""
    # Returns:
    # {
    #     "system": [...],           # System messages + full tool definitions
    #     "summaries": [...],        # Existing summaries
    #     "historical": [...],       # Old messages to compact
    #     "old_tools": [...],        # Old tool sequences
    #     "marked": [...],           # Marked for retention
    #     "latest_tools": [...],     # Recent tool sequences (atomic, MAX SPAN)
    #     "recent": [...],           # Recent messages
    # }
```

**v2.3 MAX SPAN Tool Grouping:**
- **Captures maximum span** between opening and closing brackets
- **Includes ALL message types** within tool execution (not just tool-specific)
- **Preserves conversational context** (user follow-up questions, etc.)
- **Latest tools**: Last contiguous tool sequence (MAX SPAN)
- **Old tools**: All other tool sequences (eligible for compaction)

**Location:** `services/workflow_service/registry/nodes/llm/prompt_compaction/context_manager.py:372-474`

---

### BudgetEnforcer (context_manager.py:268)

Enforces section budget limits with dynamic reallocation (v2.0).

**Key Method:**
```python
def enforce_budget(
    self,
    sections: Dict[str, List[BaseMessage]],
    budget: ContextBudget,
    model_metadata: ModelMetadata,
    config: PromptCompactionConfig,
) -> Dict[str, List[BaseMessage]]:
    """Enforce budget limits with dynamic reallocation (v2.0)."""
    # 1. Truncate over-budget sections
    # 2. Calculate surplus from under-utilized sections
    # 3. Reallocate surplus to priority sections
    # Priority: summaries > recent > marked
```

**Location:** `services/workflow_service/registry/nodes/llm/prompt_compaction/context_manager.py:268-366`

---

## Implementation Patterns

### Pattern 1: Adding v2.1 Metadata to Messages

**When:** Creating any message in compaction output
**Where:** All strategy classes

```python
from workflow_service.registry.nodes.llm.prompt_compaction.utils import (
    set_section_label,
    add_graph_edge,
    MessageSectionLabel,
    GraphEdgeType,
)

# System messages
for msg in sections["system"]:
    set_section_label(msg, MessageSectionLabel.SYSTEM)
    add_graph_edge(msg, GraphEdgeType.PASSTHROUGH)

# Summaries (already have metadata from create_summary_message())
for msg in summaries:
    # Metadata already added by create_summary_message()
    pass

# Extracted messages
for msg in extracted:
    set_section_label(msg, MessageSectionLabel.EXTRACTED_SUMMARY)
    add_graph_edge(msg, GraphEdgeType.EXTRACTION, source_ids=[...])
```

**Location:** `utils.py:64-119` (metadata helpers), used across all strategies

---

### Pattern 2: JIT Ingestion for Extraction (v2.1)

**When:** First extraction call in ExtractionStrategy
**Where:** `ExtractionStrategy._jit_ingest_messages()`

```python
async def _jit_ingest_messages(
    self,
    messages: List[BaseMessage],
    ext_context: Any,
) -> List[BaseMessage]:
    """Ingest messages to Weaviate if not already ingested (v2.1)."""
    messages_to_ingest = [msg for msg in messages if not is_message_ingested(msg)]

    if not messages_to_ingest:
        return messages

    # Chunk large messages (v2.1)
    if self.enable_message_chunking:
        all_chunks = []
        for msg in messages_to_ingest:
            chunks = self._chunk_message(msg)  # Split into ~6K token chunks
            all_chunks.extend(chunks)

    # Generate embeddings
    texts = [format_message_for_embedding(chunk) for chunk in all_chunks]
    embeddings = await get_embeddings_batch(texts, self.embedding_model, ext_context)

    # Store in Weaviate
    for chunk, embedding in zip(all_chunks, embeddings):
        await ext_context.thread_message_client.add_message_chunk(
            thread_id=ext_context.thread_id,
            message_id=chunk.parent_message_id,
            chunk_id=chunk.id,
            text=chunk.text,
            embedding=embedding,
        )
        set_ingestion_metadata(chunk.parent_message, [chunk.id])

    return messages
```

**Location:** `strategies.py:1032-1064`

---

### Pattern 3: Deduplication & Overflow (v2.1)

**When:** After extraction, before returning results
**Where:** `ExtractionStrategy._check_and_handle_duplicates()`

```python
def _check_and_handle_duplicates(
    self,
    new_extraction: AIMessage,
    existing_extractions: List[AIMessage],
) -> List[AIMessage]:
    """Check and handle duplicate chunk overflow (v2.1)."""
    new_chunk_ids = get_extraction_chunk_ids(new_extraction)

    # Track appearances
    for chunk_id in new_chunk_ids:
        appearance_count = track_chunk_extraction(new_extraction, chunk_id)

        if appearance_count > self.max_duplicate_appearances:
            # Overflow! Apply strategy
            if self.overflow_strategy == "remove_oldest":
                # Find oldest extraction with this chunk
                oldest_msg = find_oldest_extraction_with_chunk(chunk_id, existing_extractions)
                existing_extractions.remove(oldest_msg)
            elif self.overflow_strategy == "error":
                raise CompactionError(f"Chunk {chunk_id} exceeded max appearances")

    return existing_extractions + [new_extraction]
```

**Location:** `strategies.py:1066-1108`, `utils.py:244-317` (tracking helpers)

---

### Pattern 4: Chunk Expansion (v2.1)

**When:** After extracting chunks, before final output
**Where:** `ExtractionStrategy._expand_chunks()`

```python
def _expand_chunks(
    self,
    chunks: List[Dict],  # {id, text, source_msg_id, score}
    all_messages: List[BaseMessage],
    budget: int,
) -> List[BaseMessage]:
    """Expand chunks to full messages based on expansion_mode (v2.1)."""
    if self.expansion_mode == "top_chunks_only":
        # Use chunks as-is (most compact)
        return [create_extraction_summary_message(
            content="\n\n".join([c["text"] for c in chunks]),
            source_message_ids=[c["source_msg_id"] for c in chunks],
            chunk_ids=[c["id"] for c in chunks],
        )]

    elif self.expansion_mode == "full_message":
        # Expand to full messages (maximum context)
        msg_map = {msg.id: msg for msg in all_messages}
        unique_msg_ids = list(set(c["source_msg_id"] for c in chunks))

        expanded = []
        for msg_id in unique_msg_ids:
            msg = msg_map[msg_id]
            if count_tokens([msg], model_metadata) <= self.max_expansion_tokens:
                add_graph_edge(msg, GraphEdgeType.EXTRACTION)
                expanded.append(msg)
        return expanded

    elif self.expansion_mode == "hybrid":
        # Try full message, fallback to chunks if over budget
        full_expanded = self._expand_chunks(..., expansion_mode="full_message")
        if count_tokens(full_expanded, model_metadata) <= budget:
            return full_expanded
        else:
            return self._expand_chunks(..., expansion_mode="top_chunks_only")
```

**Location:** `strategies.py:1100-1180` (implied from expansion config)

---

## Metadata System

### v2.1 Metadata Schema

All compacted messages have metadata in `response_metadata["compaction"]`:

```python
response_metadata = {
    "compaction": {
        # Section label (v2.1)
        "section_label": "summary" | "extracted_summary" | "system" | "marked" | "tool_call" | "tool_response" | "recent" | "historical",

        # Bipartite graph edges (v2.1)
        "graph_edges": {
            "edge_type": "summary" | "extraction" | "passthrough",
            "full_history_msg_ids": ["msg_1", "msg_2", ...],  # Source messages
            "target_msg_id": "summary_msg_123",                # This message (if summary/extraction)
        },

        # Extraction metadata (v2.1, only for extracted summaries)
        "extraction": {
            "chunk_ids": ["chunk_msg_1", "chunk_msg_2"],
            "strategy": "dump" | "extract_full" | "llm_rewrite",
            "relevance_scores": [0.95, 0.87],
            "deduplicated_chunk_ids": ["chunk_x", "chunk_y"],  # Seen this cycle
        },

        # Ingestion metadata (v2.1, on original messages)
        "ingestion": {
            "chunk_ids": ["chunk_123", "chunk_124"],
            "timestamp": "2025-11-11T10:00:00Z",
        },

        # Summary metadata (v2.0, on summary messages)
        "summary": {
            "generation": 0,  # L0, L1, L2 (hierarchical)
            "token_usage": {...},
            "cost": 0.001,
        },
    }
}
```

**Metadata Helpers (utils.py:64-242):**
- `set_compaction_metadata(msg, key, value)`: Set any metadata
- `get_compaction_metadata(msg, key)`: Get metadata safely
- `set_section_label(msg, label)`: Set section label
- `get_section_label(msg)`: Get section label
- `add_graph_edge(msg, edge_type, source_ids)`: Add bidirectional edge
- `set_extraction_metadata(msg, chunk_ids, strategy, scores)`: Set extraction info
- `get_extraction_chunk_ids(msg)`: Get chunk IDs
- `set_ingestion_metadata(msg, chunk_ids)`: Mark as ingested
- `is_message_ingested(msg)`: Check if ingested
- `track_chunk_extraction(msg, chunk_id)`: Track appearances (v2.1)
- `get_chunk_appearance_count(chunk_id, extractions)`: Get total appearances
- `find_oldest_extraction_with_chunk(chunk_id, extractions)`: Find oldest

**Location:** `services/workflow_service/registry/nodes/llm/prompt_compaction/utils.py:64-317`

---

## Integration Points

### 1. LLM Node Integration

**When:** LLM node prepares messages for API call
**Where:** `services/workflow_service/registry/nodes/llm/llm_node.py`

**Current Integration (v2.0):**
```python
class LLMNode:
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        messages = state.get("messages", [])

        # Check if compaction needed
        if self.compactor.should_compact(messages, self.model_metadata):
            compaction_result = await self.compactor.test_compact_if_needed(
                messages=messages,
                model_metadata=self.model_metadata,
                ext_context=self.ext_context,
            )
            messages = compaction_result.compacted_messages

        # Call LLM with compacted messages
        response = await self._call_llm(messages)
        return {"messages": [response]}
```

**v2.1 Dual History Integration (Not Yet Implemented):**
```python
# Proposed v2.1 enhancement
class WorkflowState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]  # Full history (append reducer)
    summarized_messages: List[BaseMessage]                # Compacted history (replace reducer)

class LLMNode:
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        full_messages = state.get("messages", [])
        summarized_messages = state.get("summarized_messages")

        # Use summarized if available, otherwise full
        messages_to_send = summarized_messages if summarized_messages else full_messages

        # Check if compaction needed
        if self.compactor.should_compact(messages_to_send, self.model_metadata):
            compaction_result = await self.compactor.compact(
                messages=full_messages,  # Always compact from full history
                model_metadata=self.model_metadata,
                ext_context=self.ext_context,
            )
            messages_to_send = compaction_result.compacted_messages
            # Store new summarized history
            new_summarized = compaction_result.compacted_messages
        else:
            new_summarized = None

        # Call LLM
        response = await self._call_llm(messages_to_send)

        # Return with dual history
        output = {"messages": [response]}  # Appended to full history
        if new_summarized:
            output["summarized_messages"] = new_summarized  # Replace summarized
        return output
```

---

### 2. Weaviate Integration (v2.1)

**When:** Extraction strategy needs to store/retrieve message chunks
**Where:** `libs/src/weaviate_client/thread_message_client.py`

**Key Operations:**
```python
class ThreadMessageClient:
    async def add_message_chunk(
        self,
        thread_id: str,
        message_id: str,
        chunk_id: str,
        text: str,
        embedding: List[float],
    ) -> None:
        """Store message chunk with embedding."""
        # Store in ThreadMessageChunks collection

    async def search_similar_chunks(
        self,
        thread_id: str,
        query_embedding: List[float],
        top_k: int = 5,
        similarity_threshold: float = 0.7,
    ) -> List[Dict]:
        """Retrieve similar chunks."""
        # Vector similarity search
        # Returns: [{id, text, source_msg_id, score}, ...]
```

**Location:** `libs/src/weaviate_client/thread_message_client.py`

---

### 3. Billing Integration

**When:** After compaction completes
**Where:** `services/workflow_service/registry/nodes/llm/prompt_compaction/billing.py`

**Key Function:**
```python
def track_compaction_cost(
    ext_context: Any,
    compaction_result: CompactionResult,
    strategy: str,
) -> None:
    """Track compaction costs for billing."""
    # Extract costs from metadata
    total_cost = compaction_result.metadata.get("cost", 0)

    # Track via billing client
    ext_context.billing_client.add_usage(
        user_id=ext_context.user_id,
        workflow_id=ext_context.workflow_id,
        operation="prompt_compaction",
        cost=total_cost,
        metadata={
            "strategy": strategy,
            "compression_ratio": compaction_result.compression_ratio,
        },
    )
```

**Location:** `services/workflow_service/registry/nodes/llm/prompt_compaction/billing.py`

---

## Testing Infrastructure

### Test Organization

**Unit Tests (55 tests):**
- `test_v21_chunking.py` (8): Message chunking >6K tokens
- `test_v21_deduplication.py` (10): Within/cross-cycle dedup
- `test_v21_reattachment.py` (8): Overflow reattachment
- `test_v21_marked_overflow.py` (6): Marked message overflow
- `test_v21_expansion.py` (10): Chunk expansion modes
- `test_v21_config_parameters.py` (7): Config validation
- `test_v21_utility_functions.py` (6): Metadata helpers

**Integration Tests (30 tests):**
- `test_v21_chunking_integration.py` (6): End-to-end chunking
- `test_v21_deduplication_integration.py` (5): Real Weaviate dedup
- `test_v21_marked_overflow_integration.py` (4): Overflow scenarios
- `test_v21_expansion_integration.py` (6): Expansion with budget
- `test_v21_section_labels_integration.py` (4): Metadata propagation
- `test_v21_end_to_end_integration.py` (5): Multi-round compaction

### Running Tests

```bash
# All unit tests
PYTHONPATH=$(pwd):$(pwd)/services poetry run pytest tests/unit/.../prompt_compaction/ -v

# All integration tests
PYTHONPATH=$(pwd):$(pwd)/services poetry run pytest tests/integration/.../prompt_compaction/ -v

# Specific v2.1 feature
PYTHONPATH=$(pwd):$(pwd)/services poetry run pytest -k "chunking" -v

# With coverage
PYTHONPATH=$(pwd):$(pwd)/services poetry run pytest --cov=services/workflow_service/registry/nodes/llm/prompt_compaction --cov-report=term-missing
```

### Test Patterns

**Unit Test Example:**
```python
@pytest.mark.asyncio
async def test_message_chunking():
    """Test message chunking for large messages (v2.1)."""
    # Create large message (15K tokens)
    large_message = create_large_message(15000)

    # Configure chunking
    config = ExtractionConfig(
        enable_message_chunking=True,
        chunk_size_tokens=6000,
        chunk_overlap_tokens=200,
    )

    # Chunk message
    strategy = ExtractionStrategy(config=config)
    chunks = strategy._chunk_message(large_message)

    # Assertions
    assert len(chunks) == 3  # 15K / 6K = 3 chunks
    assert all(count_tokens([c]) <= 6000 for c in chunks)
    # Check overlap
    assert chunks[1].text[:200] == chunks[0].text[-200:]
```

**Integration Test Example:**
```python
@pytest.mark.asyncio
async def test_end_to_end_extraction(weaviate_client, ext_context):
    """Test full extraction cycle with Weaviate (v2.1)."""
    # Create messages
    messages = create_test_messages(100)

    # Configure extraction
    config = PromptCompactionConfig(
        strategy=CompactionStrategyType.EXTRACTIVE,
        extraction=ExtractionConfig(
            enable_message_chunking=True,
            expansion_mode="full_message",
        ),
    )

    # Compact
    compactor = PromptCompactor(config=config)
    result = await compactor.compact(messages, model_metadata, ext_context)

    # Assertions
    assert result.compacted_messages is not None
    assert result.compression_ratio > 1.0
    # Check metadata
    for msg in result.compacted_messages:
        assert get_section_label(msg) is not None
```

---

## Summary

This implementation reference provides:
- ✅ Complete file structure and responsibilities
- ✅ All configuration classes with defaults
- ✅ Core classes and key methods
- ✅ v2.1 implementation patterns
- ✅ Metadata system documentation
- ✅ Integration points (LLM node, Weaviate, billing)
- ✅ Testing infrastructure (85 tests)

**For more details:**
- **Configuration:** See `V2.1_CONFIGURATION_GUIDE.md`
- **Design & Architecture:** See `DESIGN_AND_ARCHITECTURE.md`
- **Test Coverage:** See `TEST_COVERAGE.md`

**Key Implementation Files:**
- `compactor.py:661` - PromptCompactionConfig
- `strategies.py:621` - ExtractionStrategy (v2.1)
- `strategies.py:1264` - HybridStrategy (v2.1)
- `utils.py:64` - Metadata helpers (v2.1)
- `context_manager.py:40` - Budget configuration

---

*Last Updated: 2025-11-11*
*Version: 2.1*
*Status: Production Ready*
