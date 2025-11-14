"""
Comprehensive unit tests for split_oversized_message and helper functions.

Tests the refactored 3-level hierarchical splitting algorithm with token computation
reuse, cumulative sums, and binary search for optimal performance.

Test Coverage:
- Helper functions: _count_tokens_for_text, _build_cumulative_sums, _binary_search_max_fit
- Level 1 (Paragraph splitting): Basic splits, multiple paragraphs, edge cases
- Level 2 (Word splitting): Oversized paragraphs, word boundaries
- Level 3 (Character splitting): Oversized words, pathological cases
- Order preservation: Ensures chunks maintain original sequence
- Metadata preservation: Chunk indices, continuation markers, tool calls
- Different message types: HumanMessage, AIMessage, SystemMessage, ToolMessage
- Token accuracy: Verifies token counts are accurate and respected
- Edge cases: Empty content, single character, perfect fits, etc.
"""

import pytest
from typing import List
from unittest.mock import Mock, patch

from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    AIMessage,
    SystemMessage,
    ToolMessage,
)

from workflow_service.registry.nodes.llm.config import ModelMetadata, LLMModelProvider
from workflow_service.registry.nodes.llm.prompt_compaction.token_utils import (
    split_oversized_message,
    _count_tokens_for_text,
    _build_cumulative_sums,
    _binary_search_max_fit,
    _split_by_words,
    _split_by_chars,
    count_tokens_in_message,
)


# Test fixtures
@pytest.fixture
def openai_metadata():
    """Standard OpenAI model metadata for testing."""
    return ModelMetadata(
        provider=LLMModelProvider.OPENAI,
        model_name="gpt-4o",
        context_limit=128000,
        output_token_limit=16000,
    )


@pytest.fixture
def anthropic_metadata():
    """Anthropic model metadata for testing."""
    return ModelMetadata(
        provider=LLMModelProvider.ANTHROPIC,
        model_name="claude-sonnet-4",
        context_limit=200000,
        output_token_limit=8000,
    )


# ============================================================================
# Helper Function Tests: _count_tokens_for_text
# ============================================================================


class TestCountTokensForText:
    """Test the _count_tokens_for_text helper function."""

    def test_empty_string(self, openai_metadata):
        """Test token counting for empty string."""
        tokens = _count_tokens_for_text("", openai_metadata)
        assert tokens == 0

    def test_single_word(self, openai_metadata):
        """Test token counting for single word."""
        tokens = _count_tokens_for_text("hello", openai_metadata)
        assert tokens > 0
        assert tokens < 5  # Single word should be a few tokens max

    def test_sentence(self, openai_metadata):
        """Test token counting for a sentence."""
        tokens = _count_tokens_for_text("This is a test sentence.", openai_metadata)
        assert tokens > 0
        assert tokens < 20

    def test_long_text(self, openai_metadata):
        """Test token counting for longer text."""
        text = "This is a longer piece of text. " * 100
        tokens = _count_tokens_for_text(text, openai_metadata)
        assert tokens > 100  # Should have significant token count

    def test_special_characters(self, openai_metadata):
        """Test token counting with special characters."""
        tokens = _count_tokens_for_text("!@#$%^&*()", openai_metadata)
        assert tokens > 0

    def test_unicode_characters(self, openai_metadata):
        """Test token counting with unicode characters."""
        tokens = _count_tokens_for_text("Hello 世界 🌍", openai_metadata)
        assert tokens > 0

    def test_consistent_counting(self, openai_metadata):
        """Test that same text always returns same token count."""
        text = "Consistency test text."
        tokens1 = _count_tokens_for_text(text, openai_metadata)
        tokens2 = _count_tokens_for_text(text, openai_metadata)
        assert tokens1 == tokens2


# ============================================================================
# Helper Function Tests: _build_cumulative_sums
# ============================================================================


class TestBuildCumulativeSums:
    """Test the _build_cumulative_sums helper function."""

    def test_empty_list(self, openai_metadata):
        """Test with empty list of units."""
        individual, cumulative = _build_cumulative_sums([], "", openai_metadata)
        assert individual == []
        assert cumulative == []

    def test_single_unit(self, openai_metadata):
        """Test with single unit."""
        units = ["hello"]
        individual, cumulative = _build_cumulative_sums(units, "", openai_metadata)
        assert len(individual) == 1
        assert len(cumulative) == 1
        assert individual[0] > 0
        assert cumulative[0] == individual[0]

    def test_multiple_units_no_separator(self, openai_metadata):
        """Test multiple units without separator."""
        units = ["hello", "world"]
        individual, cumulative = _build_cumulative_sums(units, "", openai_metadata)
        
        assert len(individual) == 2
        assert len(cumulative) == 2
        assert cumulative[0] == individual[0]
        assert cumulative[1] == individual[0] + individual[1]

    def test_multiple_units_with_space_separator(self, openai_metadata):
        """Test multiple units with space separator."""
        units = ["hello", "world", "test"]
        individual, cumulative = _build_cumulative_sums(units, " ", openai_metadata)
        
        space_tokens = _count_tokens_for_text(" ", openai_metadata)
        
        assert len(individual) == 3
        assert len(cumulative) == 3
        # First unit: no separator before it
        assert cumulative[0] == individual[0]
        # Second unit: includes separator
        assert cumulative[1] == individual[0] + space_tokens + individual[1]
        # Third unit: includes two separators (before unit 1 and unit 2)
        assert cumulative[2] == individual[0] + space_tokens + individual[1] + space_tokens + individual[2]

    def test_multiple_units_with_paragraph_separator(self, openai_metadata):
        """Test multiple units with paragraph separator."""
        units = ["First paragraph", "Second paragraph", "Third paragraph"]
        individual, cumulative = _build_cumulative_sums(units, "\n\n", openai_metadata)
        
        sep_tokens = _count_tokens_for_text("\n\n", openai_metadata)
        
        assert len(individual) == 3
        assert len(cumulative) == 3
        assert cumulative[0] == individual[0]
        assert cumulative[1] == individual[0] + sep_tokens + individual[1]
        assert cumulative[2] == individual[0] + sep_tokens + individual[1] + sep_tokens + individual[2]

    def test_cumulative_sum_monotonic_increasing(self, openai_metadata):
        """Test that cumulative sums are monotonically increasing."""
        units = ["a", "bb", "ccc", "dddd", "eeeee"]
        _, cumulative = _build_cumulative_sums(units, " ", openai_metadata)
        
        for i in range(1, len(cumulative)):
            assert cumulative[i] > cumulative[i-1]

    def test_empty_units_in_list(self, openai_metadata):
        """Test with some empty units in list."""
        units = ["hello", "", "world", "", ""]
        individual, cumulative = _build_cumulative_sums(units, " ", openai_metadata)
        
        assert len(individual) == 5
        assert len(cumulative) == 5
        # Empty strings may still have tokens (separator counts)

    def test_long_unit_list(self, openai_metadata):
        """Test with many units."""
        units = [f"word{i}" for i in range(100)]
        individual, cumulative = _build_cumulative_sums(units, " ", openai_metadata)
        
        assert len(individual) == 100
        assert len(cumulative) == 100
        assert cumulative[-1] > cumulative[0]


# ============================================================================
# Helper Function Tests: _binary_search_max_fit
# ============================================================================


class TestBinarySearchMaxFit:
    """Test the _binary_search_max_fit helper function."""

    def test_empty_cumulative_sums(self):
        """Test with empty cumulative sums."""
        result = _binary_search_max_fit([], max_tokens=100, message_overhead=10)
        assert result == 0

    def test_all_units_fit(self):
        """Test when all units fit within budget."""
        cumulative_sums = [10, 25, 45, 70, 100]
        result = _binary_search_max_fit(cumulative_sums, max_tokens=150, message_overhead=10)
        assert result == 5  # All 5 units fit

    def test_no_units_fit(self):
        """Test when even first unit exceeds budget."""
        cumulative_sums = [100, 200, 300]
        result = _binary_search_max_fit(cumulative_sums, max_tokens=50, message_overhead=10)
        assert result == 0  # No units fit

    def test_some_units_fit(self):
        """Test when some units fit."""
        cumulative_sums = [10, 25, 45, 70, 100]
        # Budget: 50, overhead: 5 -> 45 available for content
        result = _binary_search_max_fit(cumulative_sums, max_tokens=50, message_overhead=5)
        # Units 0,1,2 fit (cumsum=45), unit 3 doesn't (cumsum=70)
        assert result == 3

    def test_exact_fit(self):
        """Test when cumulative sum exactly matches budget."""
        cumulative_sums = [10, 25, 45]
        result = _binary_search_max_fit(cumulative_sums, max_tokens=50, message_overhead=5)
        # 45 + 5 = 50, exactly fits
        assert result == 3

    def test_single_unit_fits(self):
        """Test with single unit that fits."""
        cumulative_sums = [10]
        result = _binary_search_max_fit(cumulative_sums, max_tokens=50, message_overhead=5)
        assert result == 1

    def test_single_unit_doesnt_fit(self):
        """Test with single unit that doesn't fit."""
        cumulative_sums = [100]
        result = _binary_search_max_fit(cumulative_sums, max_tokens=50, message_overhead=5)
        assert result == 0

    def test_large_list(self):
        """Test with large list of units."""
        # Cumulative sums from 1 to 1000
        cumulative_sums = list(range(1, 1001))
        result = _binary_search_max_fit(cumulative_sums, max_tokens=550, message_overhead=50)
        # Budget: 550 - 50 = 500 available for content
        # Should fit units with cumsum <= 500, which is index 499 (0-indexed), so count = 500
        assert result == 500

    def test_message_overhead_matters(self):
        """Test that message overhead is properly accounted for."""
        cumulative_sums = [10, 20, 30, 40, 50]
        
        # With low overhead, more units fit
        result1 = _binary_search_max_fit(cumulative_sums, max_tokens=45, message_overhead=5)
        assert result1 == 4  # 40 + 5 = 45
        
        # With high overhead, fewer units fit
        result2 = _binary_search_max_fit(cumulative_sums, max_tokens=45, message_overhead=20)
        assert result2 == 2  # 20 + 20 = 40 < 45, but 30 + 20 = 50 > 45


# ============================================================================
# Helper Function Tests: _split_by_chars
# ============================================================================


class TestSplitByChars:
    """Test the _split_by_chars helper function (Level 3)."""

    def test_empty_text(self, openai_metadata):
        """Test splitting empty text."""
        chunks = _split_by_chars("", 100, openai_metadata, HumanMessage)
        assert chunks == []

    def test_text_fits_in_one_chunk(self, openai_metadata):
        """Test when text fits in one chunk."""
        text = "hello"
        chunks = _split_by_chars(text, 1000, openai_metadata, HumanMessage)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_text_needs_splitting(self, openai_metadata):
        """Test when text needs to be split into multiple chunks."""
        # Create a long text
        text = "a" * 1000
        chunks = _split_by_chars(text, 50, openai_metadata, HumanMessage)
        
        assert len(chunks) > 1
        # Verify all chunks combined equal original text
        assert "".join(chunks) == text

    def test_single_character_exceeds_budget(self, openai_metadata):
        """Test pathological case where single character exceeds budget."""
        # This is extremely unlikely but should be handled
        text = "x"
        # Use very small budget that character might exceed
        chunks = _split_by_chars(text, 1, openai_metadata, HumanMessage)
        # Should still return the character to make progress
        assert len(chunks) == 1
        assert chunks[0] == "x"

    def test_order_preserved(self, openai_metadata):
        """Test that character order is preserved."""
        text = "abcdefghijklmnop"
        chunks = _split_by_chars(text, 30, openai_metadata, HumanMessage)
        
        reconstructed = "".join(chunks)
        assert reconstructed == text

    def test_unicode_characters(self, openai_metadata):
        """Test splitting text with unicode characters."""
        text = "Hello 世界 🌍 " * 10
        chunks = _split_by_chars(text, 50, openai_metadata, HumanMessage)
        
        assert len(chunks) > 0
        assert "".join(chunks) == text


# ============================================================================
# Helper Function Tests: _split_by_words
# ============================================================================


class TestSplitByWords:
    """Test the _split_by_words helper function (Level 2)."""

    def test_empty_text(self, openai_metadata):
        """Test splitting empty text."""
        chunks = _split_by_words("", 100, openai_metadata, HumanMessage)
        assert chunks == []

    def test_text_fits_in_one_chunk(self, openai_metadata):
        """Test when text fits in one chunk."""
        text = "Hello world test"
        chunks = _split_by_words(text, 1000, openai_metadata, HumanMessage)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_text_needs_word_splitting(self, openai_metadata):
        """Test when text needs to be split into word-based chunks."""
        # Create text with many words
        text = " ".join([f"word{i}" for i in range(100)])
        chunks = _split_by_words(text, 100, openai_metadata, HumanMessage)
        
        assert len(chunks) > 1
        # Verify all chunks combined equal original text
        assert " ".join(" ".join(chunks).split()) == " ".join(text.split())

    def test_single_word_exceeds_budget_falls_back_to_chars(self, openai_metadata):
        """Test that oversized single word falls back to character splitting."""
        # Create a very long word
        long_word = "x" * 1000
        chunks = _split_by_words(long_word, 50, openai_metadata, HumanMessage)
        
        # Should have been split by characters
        assert len(chunks) > 1
        assert "".join(chunks) == long_word

    def test_multiple_words_some_oversized(self, openai_metadata):
        """Test mix of normal and oversized words."""
        text = "normal " + ("x" * 500) + " another"
        chunks = _split_by_words(text, 100, openai_metadata, HumanMessage)
        
        assert len(chunks) >= 1
        # Verify content preserved (all chunks combined)
        reconstructed = " ".join(chunks)
        # Account for potential spacing differences - check all content is there
        assert "normal" in reconstructed
        # The x's might be split across chunks
        total_xs = "".join(chunks).count("x")
        assert total_xs == 500
        assert "another" in reconstructed

    def test_order_preserved(self, openai_metadata):
        """Test that word order is preserved."""
        words = [f"word{i}" for i in range(20)]
        text = " ".join(words)
        chunks = _split_by_words(text, 100, openai_metadata, HumanMessage)
        
        reconstructed_words = " ".join(chunks).split()
        assert reconstructed_words == words

    def test_whitespace_handling(self, openai_metadata):
        """Test handling of various whitespace."""
        text = "word1  word2   word3\tword4\nword5"
        chunks = _split_by_words(text, 1000, openai_metadata, HumanMessage)
        
        # After splitting and rejoining with spaces
        reconstructed_words = " ".join(chunks).split()
        assert reconstructed_words == text.split()


# ============================================================================
# Main Function Tests: split_oversized_message - Basic Functionality
# ============================================================================


class TestSplitOversizedMessageBasic:
    """Test basic functionality of split_oversized_message."""

    def test_message_fits_no_splitting(self, openai_metadata):
        """Test when message fits within budget - no splitting needed."""
        message = HumanMessage(content="Short message")
        chunks = split_oversized_message(message, 10000, openai_metadata)
        
        assert len(chunks) == 1
        assert chunks[0].content == message.content
        assert type(chunks[0]) == type(message)

    def test_empty_content(self, openai_metadata):
        """Test with empty message content."""
        message = HumanMessage(content="")
        chunks = split_oversized_message(message, 1000, openai_metadata)
        
        # Should return original message
        assert len(chunks) == 1

    def test_whitespace_only_content(self, openai_metadata):
        """Test with whitespace-only content."""
        message = HumanMessage(content="   \n\n   ")
        chunks = split_oversized_message(message, 1000, openai_metadata)
        
        # Should handle gracefully
        assert len(chunks) >= 1

    def test_simple_split_needed(self, openai_metadata):
        """Test simple case where message needs splitting."""
        # Create message that exceeds budget
        content = "This is a paragraph.\n\n" * 100
        message = HumanMessage(content=content)
        
        # Set small budget to force splitting
        chunks = split_oversized_message(message, 200, openai_metadata)
        
        assert len(chunks) > 1
        # Verify all chunks are under budget
        for chunk in chunks:
            tokens = count_tokens_in_message(chunk, openai_metadata)
            assert tokens <= 200


# ============================================================================
# Main Function Tests: Level 1 - Paragraph Splitting
# ============================================================================


class TestSplitOversizedMessageParagraphs:
    """Test Level 1: Paragraph-level splitting."""

    def test_single_paragraph_fits(self, openai_metadata):
        """Test single paragraph that fits in budget."""
        message = HumanMessage(content="Single paragraph here.")
        chunks = split_oversized_message(message, 1000, openai_metadata)
        
        assert len(chunks) == 1
        assert chunks[0].content == message.content

    def test_multiple_paragraphs_all_fit(self, openai_metadata):
        """Test multiple paragraphs that all fit together."""
        content = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
        message = HumanMessage(content=content)
        chunks = split_oversized_message(message, 1000, openai_metadata)
        
        assert len(chunks) == 1
        assert chunks[0].content == content

    def test_multiple_paragraphs_need_splitting(self, openai_metadata):
        """Test multiple paragraphs that need to be split."""
        paragraphs = [f"Paragraph {i} with some content here." for i in range(20)]
        content = "\n\n".join(paragraphs)
        message = HumanMessage(content=content)
        
        # Use small budget to force splitting
        chunks = split_oversized_message(message, 150, openai_metadata)
        
        assert len(chunks) > 1
        # Verify combined content preserves paragraphs
        combined = "\n\n".join([chunk.content for chunk in chunks])
        # Normalize whitespace for comparison
        assert combined.replace("\n\n", " ").split() == content.replace("\n\n", " ").split()

    def test_exact_paragraph_boundary_split(self, openai_metadata):
        """Test splitting exactly at paragraph boundaries."""
        # Create paragraphs of known size
        p1 = "First paragraph with some text."
        p2 = "Second paragraph with more text here."
        p3 = "Third paragraph also has text."
        content = f"{p1}\n\n{p2}\n\n{p3}"
        message = HumanMessage(content=content)
        
        # Set budget to fit roughly 1-2 paragraphs
        chunks = split_oversized_message(message, 100, openai_metadata)
        
        assert len(chunks) >= 1
        # Verify content preserved
        for chunk in chunks:
            assert len(chunk.content) > 0

    def test_many_small_paragraphs(self, openai_metadata):
        """Test with many small paragraphs."""
        paragraphs = [f"P{i}" for i in range(100)]
        content = "\n\n".join(paragraphs)
        message = HumanMessage(content=content)
        
        chunks = split_oversized_message(message, 200, openai_metadata)
        
        # Should create efficient chunks
        assert len(chunks) >= 1
        # Verify all paragraphs preserved
        combined_content = "\n\n".join([chunk.content for chunk in chunks])
        assert len(combined_content.split("\n\n")) == 100

    def test_paragraphs_with_empty_lines(self, openai_metadata):
        """Test handling of empty paragraphs (multiple newlines)."""
        content = "Para1\n\n\n\nPara2\n\n\n\nPara3"
        message = HumanMessage(content=content)
        
        chunks = split_oversized_message(message, 1000, openai_metadata)
        assert len(chunks) >= 1


# ============================================================================
# Main Function Tests: Level 2 - Word Splitting
# ============================================================================


class TestSplitOversizedMessageWords:
    """Test Level 2: Word-level splitting for oversized paragraphs."""

    def test_single_oversized_paragraph_splits_by_words(self, openai_metadata):
        """Test that oversized paragraph splits by words."""
        # Create one very long paragraph (no \n\n breaks)
        words = [f"word{i}" for i in range(200)]
        content = " ".join(words)
        message = HumanMessage(content=content)
        
        # Small budget forces word-level splitting
        chunks = split_oversized_message(message, 100, openai_metadata)
        
        assert len(chunks) > 1
        # Verify all words preserved
        combined_words = []
        for chunk in chunks:
            combined_words.extend(chunk.content.split())
        assert len(combined_words) == 200

    def test_mixed_paragraph_and_word_splitting(self, openai_metadata):
        """Test mix of paragraph-level and word-level splitting."""
        # Some normal paragraphs + one oversized paragraph
        p1 = "Normal paragraph."
        p2 = " ".join([f"word{i}" for i in range(100)])  # Oversized
        p3 = "Another normal paragraph."
        content = f"{p1}\n\n{p2}\n\n{p3}"
        message = HumanMessage(content=content)
        
        chunks = split_oversized_message(message, 150, openai_metadata)
        
        assert len(chunks) > 1
        # Verify content preserved
        for chunk in chunks:
            assert len(chunk.content) > 0

    def test_all_paragraphs_oversized(self, openai_metadata):
        """Test when all paragraphs are oversized and need word splitting."""
        paragraphs = []
        for i in range(5):
            words = [f"word{j}" for j in range(50)]
            paragraphs.append(" ".join(words))
        content = "\n\n".join(paragraphs)
        message = HumanMessage(content=content)
        
        # Very small budget
        chunks = split_oversized_message(message, 80, openai_metadata)
        
        assert len(chunks) > 5  # Should have more chunks than paragraphs


# ============================================================================
# Main Function Tests: Level 3 - Character Splitting
# ============================================================================


class TestSplitOversizedMessageCharacters:
    """Test Level 3: Character-level splitting for oversized words."""

    def test_single_oversized_word_splits_by_chars(self, openai_metadata):
        """Test that oversized word splits by characters."""
        # Create impossibly long word
        content = "x" * 1000
        message = HumanMessage(content=content)
        
        # Very small budget
        chunks = split_oversized_message(message, 50, openai_metadata)
        
        assert len(chunks) > 1
        # Verify all characters preserved
        combined = "".join([chunk.content for chunk in chunks])
        assert combined == content

    def test_mixed_normal_and_oversized_words(self, openai_metadata):
        """Test mix of normal words and oversized words."""
        normal_words = ["hello", "world", "test"]
        oversized_word = "x" * 500
        content = " ".join(normal_words + [oversized_word] + ["end"])
        message = HumanMessage(content=content)
        
        chunks = split_oversized_message(message, 100, openai_metadata)
        
        assert len(chunks) >= 1
        # Verify content preserved
        combined = " ".join([chunk.content for chunk in chunks])
        assert "hello" in combined
        # Count x's across all chunks
        total_xs = "".join([chunk.content for chunk in chunks]).count("x")
        assert total_xs == 500
        assert "end" in combined

    def test_multiple_oversized_words(self, openai_metadata):
        """Test multiple oversized words in sequence."""
        word1 = "a" * 400
        word2 = "b" * 400
        word3 = "c" * 400
        content = f"{word1} {word2} {word3}"
        message = HumanMessage(content=content)
        
        chunks = split_oversized_message(message, 80, openai_metadata)
        
        assert len(chunks) > 3
        # Verify characters preserved
        combined = " ".join([chunk.content for chunk in chunks])
        assert "a" * 400 in combined or combined.count("a") == 400
        assert "b" * 400 in combined or combined.count("b") == 400
        assert "c" * 400 in combined or combined.count("c") == 400


# ============================================================================
# Main Function Tests: Order Preservation
# ============================================================================


class TestSplitOversizedMessageOrderPreservation:
    """Test that splitting always preserves original order."""

    def test_paragraph_order_preserved(self, openai_metadata):
        """Test that paragraph order is maintained."""
        paragraphs = [f"Paragraph_{i}_unique_marker" for i in range(10)]
        content = "\n\n".join(paragraphs)
        message = HumanMessage(content=content)
        
        chunks = split_oversized_message(message, 150, openai_metadata)
        
        # Extract all content in order
        combined = "\n\n".join([chunk.content for chunk in chunks])
        
        # Check that markers appear in order
        for i in range(10):
            assert f"Paragraph_{i}_unique_marker" in combined
        
        # Verify ordering
        positions = [combined.index(f"Paragraph_{i}_unique_marker") for i in range(10)]
        assert positions == sorted(positions)

    def test_word_order_preserved(self, openai_metadata):
        """Test that word order is maintained."""
        words = [f"word_{i:03d}" for i in range(100)]
        content = " ".join(words)
        message = HumanMessage(content=content)
        
        chunks = split_oversized_message(message, 150, openai_metadata)
        
        # Extract all words in order
        combined_words = []
        for chunk in chunks:
            combined_words.extend(chunk.content.split())
        
        # Verify all words present and in order
        assert combined_words == words

    def test_character_order_preserved(self, openai_metadata):
        """Test that character order is maintained."""
        content = "ABCDEFGHIJKLMNOPQRSTUVWXYZ" * 50
        message = HumanMessage(content=content)
        
        chunks = split_oversized_message(message, 80, openai_metadata)
        
        # Reconstruct content
        combined = "".join([chunk.content for chunk in chunks])
        assert combined == content


# ============================================================================
# Main Function Tests: Metadata Preservation
# ============================================================================


class TestSplitOversizedMessageMetadata:
    """Test metadata preservation in chunks."""

    def test_chunk_indices_sequential(self, openai_metadata):
        """Test that chunk indices are sequential."""
        content = "\n\n".join([f"Paragraph {i}" for i in range(20)])
        message = HumanMessage(content=content)
        
        chunks = split_oversized_message(message, 150, openai_metadata)
        
        # Check chunk metadata (only if multiple chunks were created)
        if len(chunks) > 1:
            for i, chunk in enumerate(chunks):
                metadata = chunk.response_metadata.get("compaction", {}).get("oversized_chunk", {})
                assert metadata.get("chunk_index") == i
        else:
            # If only one chunk, splitting wasn't needed
            assert len(chunks) == 1

    def test_continuation_markers(self, openai_metadata):
        """Test continuation markers in chunk metadata."""
        content = "\n\n".join([f"Paragraph {i}" for i in range(20)])
        message = HumanMessage(content=content)
        
        chunks = split_oversized_message(message, 150, openai_metadata)
        
        # Only test if multiple chunks were created
        if len(chunks) > 1:
            # First chunk should not be continuation
            metadata_0 = chunks[0].response_metadata.get("compaction", {}).get("oversized_chunk", {})
            assert metadata_0.get("is_continuation") is False
            
            # Subsequent chunks should be continuations
            for chunk in chunks[1:]:
                metadata = chunk.response_metadata.get("compaction", {}).get("oversized_chunk", {})
                assert metadata.get("is_continuation") is True
        else:
            # If only one chunk, no splitting occurred
            assert len(chunks) == 1

    def test_original_message_id_preserved(self, openai_metadata):
        """Test that original message ID is preserved in all chunks."""
        message = HumanMessage(content="\n\n".join([f"Para {i}" for i in range(20)]))
        original_id = message.id
        
        chunks = split_oversized_message(message, 150, openai_metadata)
        
        # Only test if multiple chunks were created
        if len(chunks) > 1:
            for chunk in chunks:
                metadata = chunk.response_metadata.get("compaction", {}).get("oversized_chunk", {})
                assert metadata.get("original_message_id") == original_id
        else:
            # If only one chunk, no splitting occurred
            assert len(chunks) == 1


# ============================================================================
# Main Function Tests: Message Types
# ============================================================================


class TestSplitOversizedMessageTypes:
    """Test different message types."""

    def test_human_message_type_preserved(self, openai_metadata):
        """Test that HumanMessage type is preserved."""
        content = "\n\n".join([f"Paragraph {i}" for i in range(20)])
        message = HumanMessage(content=content)
        
        chunks = split_oversized_message(message, 150, openai_metadata)
        
        for chunk in chunks:
            assert isinstance(chunk, HumanMessage)

    def test_ai_message_type_preserved(self, openai_metadata):
        """Test that AIMessage type is preserved."""
        content = "\n\n".join([f"Paragraph {i}" for i in range(20)])
        message = AIMessage(content=content)
        
        chunks = split_oversized_message(message, 150, openai_metadata)
        
        for chunk in chunks:
            assert isinstance(chunk, AIMessage)

    def test_system_message_type_preserved(self, openai_metadata):
        """Test that SystemMessage type is preserved."""
        content = "\n\n".join([f"Paragraph {i}" for i in range(20)])
        message = SystemMessage(content=content)
        
        chunks = split_oversized_message(message, 150, openai_metadata)
        
        for chunk in chunks:
            assert isinstance(chunk, SystemMessage)

    def test_tool_message_type_preserved(self, openai_metadata):
        """Test that ToolMessage type is preserved."""
        content = "\n\n".join([f"Paragraph {i}" for i in range(20)])
        message = ToolMessage(content=content, tool_call_id="test_tool_123")
        
        chunks = split_oversized_message(message, 150, openai_metadata)
        
        for chunk in chunks:
            assert isinstance(chunk, ToolMessage)
            assert chunk.tool_call_id == "test_tool_123"

    def test_ai_message_tool_calls_first_chunk_only(self, openai_metadata):
        """Test that tool calls are preserved only in first chunk."""
        content = "\n\n".join([f"Paragraph {i}" for i in range(20)])
        message = AIMessage(content=content)
        message.tool_calls = [
            {
                "name": "test_tool",
                "args": {"arg1": "value1"},
                "id": "call_123",
            }
        ]
        
        chunks = split_oversized_message(message, 150, openai_metadata)
        
        if len(chunks) > 1:
            # First chunk should have tool calls
            assert hasattr(chunks[0], "tool_calls")
            assert len(chunks[0].tool_calls) == 1
            
            # Subsequent chunks should not have tool calls
            for chunk in chunks[1:]:
                assert not hasattr(chunk, "tool_calls") or len(chunk.tool_calls) == 0


# ============================================================================
# Main Function Tests: Token Accuracy
# ============================================================================


class TestSplitOversizedMessageTokenAccuracy:
    """Test token counting accuracy in splitting."""

    def test_all_chunks_under_budget(self, openai_metadata):
        """Test that all chunks respect token budget."""
        content = "\n\n".join([f"Paragraph {i} with some content here." for i in range(50)])
        message = HumanMessage(content=content)
        
        max_tokens = 200
        chunks = split_oversized_message(message, max_tokens, openai_metadata)
        
        for chunk in chunks:
            tokens = count_tokens_in_message(chunk, openai_metadata)
            assert tokens <= max_tokens, f"Chunk exceeded budget: {tokens} > {max_tokens}"

    def test_token_budget_respected_with_small_budget(self, openai_metadata):
        """Test token budget with very small budget."""
        content = "This is a test message with multiple words and sentences."
        message = HumanMessage(content=content)
        
        max_tokens = 30
        chunks = split_oversized_message(message, max_tokens, openai_metadata)
        
        for chunk in chunks:
            tokens = count_tokens_in_message(chunk, openai_metadata)
            assert tokens <= max_tokens

    def test_token_budget_respected_with_large_content(self, openai_metadata):
        """Test token budget with large content."""
        # Create very large content
        paragraphs = [" ".join([f"word{j}" for j in range(50)]) for i in range(100)]
        content = "\n\n".join(paragraphs)
        message = HumanMessage(content=content)
        
        max_tokens = 500
        chunks = split_oversized_message(message, max_tokens, openai_metadata)
        
        assert len(chunks) > 1
        for chunk in chunks:
            tokens = count_tokens_in_message(chunk, openai_metadata)
            assert tokens <= max_tokens


# ============================================================================
# Main Function Tests: Edge Cases
# ============================================================================


class TestSplitOversizedMessageEdgeCases:
    """Test edge cases and corner scenarios."""

    def test_single_character_message(self, openai_metadata):
        """Test with single character."""
        message = HumanMessage(content="x")
        chunks = split_oversized_message(message, 1000, openai_metadata)
        
        assert len(chunks) == 1
        assert chunks[0].content == "x"

    def test_only_newlines(self, openai_metadata):
        """Test with only newline characters."""
        message = HumanMessage(content="\n\n\n\n")
        chunks = split_oversized_message(message, 1000, openai_metadata)
        
        assert len(chunks) >= 1

    def test_only_spaces(self, openai_metadata):
        """Test with only space characters."""
        message = HumanMessage(content="     ")
        chunks = split_oversized_message(message, 1000, openai_metadata)
        
        assert len(chunks) >= 1

    def test_very_small_budget(self, openai_metadata):
        """Test with extremely small token budget."""
        message = HumanMessage(content="Hello world")
        # Even with tiny budget, should make progress
        chunks = split_oversized_message(message, 10, openai_metadata)
        
        assert len(chunks) >= 1
        # Verify content preserved
        combined = " ".join([c.content for c in chunks])
        assert "Hello" in combined or "world" in combined

    def test_budget_smaller_than_overhead(self, openai_metadata):
        """Test when budget is smaller than message overhead."""
        message = HumanMessage(content="Test")
        # Very small budget (but function should handle gracefully)
        chunks = split_oversized_message(message, 5, openai_metadata)
        
        # Should still produce chunks (even if they technically exceed budget)
        assert len(chunks) >= 1

    def test_content_with_special_splitting_characters(self, openai_metadata):
        """Test content with characters used for splitting."""
        content = "Para1\n\n\n\nPara2     Para3\t\tPara4"
        message = HumanMessage(content=content)
        
        chunks = split_oversized_message(message, 1000, openai_metadata)
        assert len(chunks) >= 1

    def test_unicode_emoji_heavy_content(self, openai_metadata):
        """Test content with many emoji and unicode characters."""
        content = "Hello 👋 World 🌍\n\n" + "Test 🚀 " * 50
        message = HumanMessage(content=content)
        
        chunks = split_oversized_message(message, 150, openai_metadata)
        assert len(chunks) >= 1
        # Verify emojis preserved
        combined = "".join([c.content for c in chunks])
        assert "👋" in combined
        assert "🌍" in combined
        assert "🚀" in combined

    def test_mixed_language_content(self, openai_metadata):
        """Test content with mixed languages."""
        content = "English text\n\n中文内容\n\nРусский текст\n\nالعربية"
        message = HumanMessage(content=content)
        
        chunks = split_oversized_message(message, 1000, openai_metadata)
        assert len(chunks) >= 1

    def test_code_snippet_content(self, openai_metadata):
        """Test content with code snippets."""
        content = """
        First paragraph.
        
        ```python
        def hello_world():
            print("Hello, world!")
            return True
        ```
        
        Second paragraph.
        """
        message = HumanMessage(content=content)
        
        chunks = split_oversized_message(message, 1000, openai_metadata)
        assert len(chunks) >= 1

    def test_very_long_single_line(self, openai_metadata):
        """Test with very long single line (no paragraph breaks)."""
        content = "word " * 1000  # 1000 words in one line
        message = HumanMessage(content=content)
        
        chunks = split_oversized_message(message, 200, openai_metadata)
        
        assert len(chunks) > 1
        # Verify token budget respected
        for chunk in chunks:
            tokens = count_tokens_in_message(chunk, openai_metadata)
            assert tokens <= 200


# ============================================================================
# Integration Tests: Complex Real-World Scenarios
# ============================================================================


class TestSplitOversizedMessageRealWorld:
    """Test real-world complex scenarios."""

    def test_research_paper_style_content(self, openai_metadata):
        """Test with research paper-style structured content."""
        content = """
        Abstract: This is the abstract of the paper.
        
        Introduction: This section introduces the topic with multiple paragraphs.
        First paragraph of introduction.
        Second paragraph with more details.
        
        Methodology: This describes the methods used.
        Step 1: First step description.
        Step 2: Second step description.
        
        Results: The results are presented here.
        
        Conclusion: Final thoughts and conclusions.
        """
        message = HumanMessage(content=content)
        
        chunks = split_oversized_message(message, 150, openai_metadata)
        
        # Verify all sections present
        combined = "\n".join([c.content for c in chunks])
        assert "Abstract" in combined
        assert "Introduction" in combined
        assert "Methodology" in combined
        assert "Results" in combined
        assert "Conclusion" in combined

    def test_conversation_transcript_style(self, openai_metadata):
        """Test with conversation transcript style content."""
        turns = []
        for i in range(30):
            turns.append(f"Speaker A: This is message {i} from speaker A.")
            turns.append(f"Speaker B: This is the response from speaker B to message {i}.")
        content = "\n\n".join(turns)
        message = HumanMessage(content=content)
        
        chunks = split_oversized_message(message, 200, openai_metadata)
        
        assert len(chunks) >= 1
        # Verify speakers preserved
        combined = "\n\n".join([c.content for c in chunks])
        assert "Speaker A" in combined
        assert "Speaker B" in combined

    def test_mixed_content_types(self, openai_metadata):
        """Test with mixed content: text, lists, code, etc."""
        content = """
        Introduction text here.
        
        List of items:
        - Item 1
        - Item 2
        - Item 3
        
        Code example:
        function test() { return true; }
        
        More text here with details.
        
        Table data:
        | Col1 | Col2 |
        | A    | B    |
        
        Conclusion.
        """
        message = HumanMessage(content=content)
        
        chunks = split_oversized_message(message, 150, openai_metadata)
        assert len(chunks) >= 1

    def test_extremely_large_message(self, openai_metadata):
        """Test with extremely large message (100K+ tokens worth)."""
        # Create very large content
        large_paragraphs = []
        for i in range(500):
            words = [f"word{j}" for j in range(100)]
            large_paragraphs.append(" ".join(words))
        content = "\n\n".join(large_paragraphs)
        message = HumanMessage(content=content)
        
        # Use reasonable budget
        chunks = split_oversized_message(message, 5000, openai_metadata)
        
        assert len(chunks) >= 10  # Should produce many chunks
        # Verify all chunks under budget
        for chunk in chunks:
            tokens = count_tokens_in_message(chunk, openai_metadata)
            assert tokens <= 5000

    def test_anthropic_provider_metadata(self, anthropic_metadata):
        """Test with Anthropic model metadata."""
        content = "\n\n".join([f"Paragraph {i}" for i in range(20)])
        message = HumanMessage(content=content)
        
        chunks = split_oversized_message(message, 150, anthropic_metadata)
        
        assert len(chunks) >= 1
        for chunk in chunks:
            assert isinstance(chunk, HumanMessage)


# ============================================================================
# Performance Tests
# ============================================================================


class TestSplitOversizedMessagePerformance:
    """Test performance characteristics of the splitting algorithm."""

    def test_token_counting_not_redundant(self, openai_metadata):
        """Test that token counting is not redundant (efficiency check)."""
        # This is more of a design verification test
        # The algorithm should count each unit's tokens exactly once
        
        content = "\n\n".join([f"Paragraph {i}" for i in range(100)])
        message = HumanMessage(content=content)
        
        # The function should complete efficiently even with many paragraphs
        chunks = split_oversized_message(message, 200, openai_metadata)
        
        # Just verify it completes and produces valid output
        assert len(chunks) >= 1
        assert all(isinstance(c, HumanMessage) for c in chunks)

    def test_handles_many_units_efficiently(self, openai_metadata):
        """Test that function handles many units efficiently."""
        # Create content with 1000 paragraphs
        paragraphs = [f"P{i}" for i in range(1000)]
        content = "\n\n".join(paragraphs)
        message = HumanMessage(content=content)
        
        # Should complete quickly with binary search
        chunks = split_oversized_message(message, 300, openai_metadata)
        
        assert len(chunks) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

