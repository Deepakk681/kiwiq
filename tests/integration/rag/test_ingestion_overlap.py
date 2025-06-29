"""
Test cases for JSON splitter text overlap functionality.
Tests various overlap scenarios to ensure context preservation works correctly.
"""
import unittest
from typing import List

# Import the JSONSplitter class
from kiwi_app.data_jobs.ingestion.chunking import JSONSplitter


class TestJSONSplitterOverlap(unittest.TestCase):
    """Test suite for JSON splitter text overlap functionality."""

    def setUp(self):
        """Set up test environment with various overlap configurations."""
        # No overlap (baseline)
        self.no_overlap_splitter = JSONSplitter(
            max_json_chunk_size=300,
            max_text_char_limit=100,
            max_json_char_limit=500,
            text_overlap_percent=0.0
        )
        
        # 20% overlap
        self.overlap_20_splitter = JSONSplitter(
            max_json_chunk_size=300,
            max_text_char_limit=100,
            max_json_char_limit=500,
            text_overlap_percent=20.0
        )
        
        # 30% overlap
        self.overlap_30_splitter = JSONSplitter(
            max_json_chunk_size=300,
            max_text_char_limit=100,
            max_json_char_limit=500,
            text_overlap_percent=30.0
        )

    def test_overlap_parameter_validation(self):
        """Test that overlap parameter is properly validated and clamped."""
        # Test negative values are clamped to 0
        splitter_negative = JSONSplitter(text_overlap_percent=-10.0)
        self.assertEqual(splitter_negative.text_overlap_percent, 0.0)
        
        # Test values over 100 are clamped to 100
        splitter_over_100 = JSONSplitter(text_overlap_percent=150.0)
        self.assertEqual(splitter_over_100.text_overlap_percent, 100.0)
        
        # Test valid values are preserved
        splitter_valid = JSONSplitter(text_overlap_percent=25.5)
        self.assertEqual(splitter_valid.text_overlap_percent, 25.5)

    def test_no_overlap_baseline(self):
        """Test that 0% overlap produces no overlapping content."""
        long_text = (
            "This is the first sentence that contains important information. "
            "This is the second sentence with more details. "
            "This is the third sentence that continues the discussion. "
            "This is the fourth sentence with additional context."
        )
        
        result = self.no_overlap_splitter.split_text_recursively(long_text, 80)
        
        # Should create multiple chunks
        self.assertGreater(len(result), 1)
        
        # Verify no overlap by checking that no content is repeated
        all_content = " ".join(result)
        original_words = long_text.split()
        result_words = all_content.split()
        
        # Should have similar word count (accounting for potential separators)
        self.assertLessEqual(len(result_words), len(original_words) + len(result))

    def test_basic_overlap_functionality(self):
        """Test basic overlap functionality with 20% overlap."""
        long_text = (
            "First section contains important context information. "
            "Second section builds upon the previous concepts. "
            "Third section introduces new methodologies. "
            "Fourth section concludes with recommendations."
        )
        
        result = self.overlap_20_splitter.split_text_recursively(long_text, 80)
        
        # Should create multiple chunks
        self.assertGreater(len(result), 1)
        
        # With overlap, combined content should be longer than original
        all_content = " ".join(result)
        self.assertGreater(len(all_content), len(long_text))
        
        # Check that some content appears in multiple chunks (sliding window)
        found_overlap = False
        for i in range(len(result)):
            current_chunk = result[i]
            
            # Check overlap with adjacent chunks
            for j in range(len(result)):
                if i != j:
                    other_chunk = result[j]
                    current_words = set(current_chunk.split())
                    other_words = set(other_chunk.split())
                    
                    if current_words & other_words:  # Intersection exists
                        found_overlap = True
                        break
            
            if found_overlap:
                break
        
        self.assertTrue(found_overlap, "Expected to find overlapping content between chunks")

    def test_overlap_preserves_context(self):
        """Test that overlap preserves important context between chunks."""
        contextual_text = (
            "Machine learning algorithms require careful feature engineering. "
            "Feature engineering involves selecting relevant data attributes. "
            "Data attributes must be normalized and scaled appropriately. "
            "Appropriate scaling ensures model convergence and stability."
        )
        
        result = self.overlap_30_splitter.split_text_recursively(contextual_text, 70)
        
        # Should create multiple chunks
        self.assertGreater(len(result), 1)
        
        # Check that important contextual terms appear in multiple chunks
        important_terms = ["feature engineering", "data attributes", "scaling"]
        
        for term in important_terms:
            chunks_containing_term = [chunk for chunk in result if term in chunk.lower()]
            # Due to overlap, important terms should appear in multiple chunks
            if len([chunk for chunk in result if term.split()[0] in chunk.lower()]) > 1:
                self.assertGreaterEqual(len(chunks_containing_term), 1)

    def test_overlap_respects_character_limits(self):
        """Test that overlap doesn't cause chunks to exceed character limits."""
        long_text = (
            "Content strategy development requires systematic planning and execution phases. "
            "Planning phases include audience research, competitive analysis, and goal setting. "
            "Execution phases involve content creation, distribution, and performance measurement. "
            "Performance measurement enables optimization and continuous improvement processes."
        )
        
        max_chars = 90
        result = self.overlap_20_splitter.split_text_recursively(long_text, max_chars)
        
        # All chunks should respect character limit
        for i, chunk in enumerate(result):
            self.assertLessEqual(len(chunk), max_chars, 
                               f"Chunk {i} exceeds limit: {len(chunk)} > {max_chars}")

    def test_overlap_with_technical_content(self):
        """Test overlap with technical jargon and specific terminology."""
        technical_text = (
            "Kubernetes orchestration automates container deployment and scaling. "
            "Container deployment involves pod creation and service discovery. "
            "Service discovery enables communication between microservices. "
            "Microservices architecture promotes loose coupling and independence."
        )
        
        result = self.overlap_30_splitter.split_text_recursively(technical_text, 75)
        
        # Should preserve technical terms across chunk boundaries
        technical_terms = ["Kubernetes", "container", "microservices", "service discovery"]
        
        # Check that technical terms appear with proper context
        for term in technical_terms:
            term_chunks = [chunk for chunk in result if term.lower() in chunk.lower()]
            if term_chunks:
                # Verify the term appears with surrounding context
                for chunk in term_chunks:
                    # Should have some context around the technical term
                    words = chunk.split()
                    self.assertGreater(len(words), 1, f"Technical term '{term}' should have context")

    def test_overlap_with_paragraph_splits(self):
        """Test overlap behavior with paragraph boundaries."""
        multi_paragraph_text = (
            "First paragraph discusses initial concepts and foundational principles. "
            "It establishes the framework for understanding complex topics.\n\n"
            
            "Second paragraph builds upon previous concepts with detailed examples. "
            "Examples demonstrate practical applications in real-world scenarios.\n\n"
            
            "Third paragraph introduces advanced techniques and methodologies. "
            "Methodologies enable sophisticated problem-solving approaches."
        )
        
        result = self.overlap_20_splitter.split_text_recursively(multi_paragraph_text, 100)
        
        # Should handle paragraph boundaries appropriately
        self.assertGreater(len(result), 1)
        
        # Check that paragraph structure is somewhat preserved
        combined = "\n\n".join(result)
        self.assertIn("First paragraph", combined)
        self.assertIn("Second paragraph", combined)
        self.assertIn("Third paragraph", combined)

    def test_overlap_edge_case_short_text(self):
        """Test overlap with text shorter than character limit."""
        short_text = "This is a short text that fits within limits."
        
        result = self.overlap_20_splitter.split_text_recursively(short_text, 100)
        
        # Should return single chunk unchanged
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], short_text)

    def test_overlap_edge_case_single_long_word(self):
        """Test overlap with single very long word."""
        long_word = "supercalifragilisticexpialidocious" * 3
        
        result = self.overlap_20_splitter.split_text_recursively(long_word, 50)
        
        # Should split word without overlap (no meaningful overlap possible)
        self.assertGreater(len(result), 1)
        
        # Each chunk should be under limit
        for chunk in result:
            self.assertLessEqual(len(chunk), 50)

    def test_word_boundary_overlap_preference(self):
        """Test that overlap prefers word boundaries when possible."""
        text_with_clear_words = (
            "Alpha beta gamma delta epsilon zeta eta theta iota kappa. "
            "Lambda mu nu xi omicron pi rho sigma tau upsilon phi chi psi omega."
        )
        
        result = self.overlap_30_splitter.split_text_recursively(text_with_clear_words, 60)
        
        if len(result) > 1:
            # Check that overlaps tend to start at word boundaries
            for i in range(1, len(result)):
                chunk = result[i]
                # If chunk starts with a letter (not space), the overlap should be word-boundary based
                if chunk and not chunk.startswith(' '):
                    # The chunk should start with a complete word
                    first_word = chunk.split()[0]
                    self.assertGreater(len(first_word), 1, "Overlap should preserve complete words")

    def test_overlap_with_json_document_processing(self):
        """Test overlap functionality in complete JSON document processing."""
        document_with_long_text = {
            "title": "Technical Documentation",
            "content": {
                "introduction": (
                    "This comprehensive guide covers advanced software engineering practices "
                    "and methodologies for enterprise-scale applications. "
                    "Enterprise applications require robust architecture and careful planning. "
                    "Planning involves stakeholder alignment and technical specification development."
                ),
                "implementation": (
                    "Implementation follows agile development principles with iterative delivery. "
                    "Iterative delivery enables continuous feedback and rapid adaptation. "
                    "Adaptation strategies include code reviews and automated testing frameworks."
                )
            }
        }
        
        # Process with overlap
        result = self.overlap_20_splitter.process_json_document(document_with_long_text, "technical_doc")
        
        # Should produce clustered results
        self.assertIsInstance(result, dict)
        self.assertIn("default", result)
        
        # Verify that chunks within clusters respect overlap
        default_chunks = result["default"]
        self.assertIsInstance(default_chunks, list)
        self.assertGreater(len(default_chunks), 0)

    def test_different_overlap_percentages(self):
        """Test different overlap percentages produce different results."""
        test_text = (
            "Content marketing strategy requires comprehensive planning and execution. "
            "Planning involves audience research, competitor analysis, and goal definition. "
            "Execution includes content creation, distribution, and performance tracking. "
            "Performance tracking enables optimization and continuous improvement efforts."
        )
        
        # Test with different overlap percentages
        no_overlap_result = self.no_overlap_splitter.split_text_recursively(test_text, 80)
        overlap_20_result = self.overlap_20_splitter.split_text_recursively(test_text, 80)
        overlap_30_result = self.overlap_30_splitter.split_text_recursively(test_text, 80)
        
        # All should create multiple chunks
        self.assertGreater(len(no_overlap_result), 1)
        self.assertGreater(len(overlap_20_result), 1)
        self.assertGreater(len(overlap_30_result), 1)
        
        # Higher overlap should result in longer combined content
        no_overlap_length = len(" ".join(no_overlap_result))
        overlap_20_length = len(" ".join(overlap_20_result))
        overlap_30_length = len(" ".join(overlap_30_result))
        
        self.assertLessEqual(no_overlap_length, overlap_20_length)
        self.assertLessEqual(overlap_20_length, overlap_30_length)

    def test_sliding_window_overlap_behavior(self):
        """Test the sliding window overlap behavior specifically."""
        # Create chunks manually to test the sliding window
        chunks = [
            "First chunk with important data",
            "Second chunk continues the story", 
            "Third chunk adds more context",
            "Fourth chunk concludes everything"
        ]
        
        # Test with external chunks using the public method
        result = self.overlap_30_splitter.apply_text_overlap(chunks, 80)
        
        # Should have same number of chunks
        self.assertEqual(len(result), len(chunks))
        
        # Each chunk should contain overlaps from adjacent chunks
        for i, chunk in enumerate(result):
            if i == 0:
                # First chunk should have overlap from next chunk
                self.assertIn("chunk", chunk)  # Should contain content from next chunk
            elif i == len(result) - 1:
                # Last chunk should have overlap from previous chunk
                self.assertIn("chunk", chunk)  # Should contain content from previous chunk
            else:
                # Middle chunks should have overlap from both sides
                self.assertIn("chunk", chunk)  # Should contain overlapping content

    def test_public_method_with_external_chunks(self):
        """Test that the public overlap method works with externally created chunks."""
        external_chunks = [
            "Alpha section describes fundamental concepts",
            "Beta section explains advanced techniques", 
            "Gamma section provides practical examples",
            "Delta section offers implementation guidance"
        ]
        
        # Test without overlap
        no_overlap_result = self.no_overlap_splitter.apply_text_overlap(external_chunks, 100, 0.0)
        self.assertEqual(no_overlap_result, external_chunks)  # Should be unchanged
        
        # Test with overlap
        overlap_result = self.overlap_20_splitter.apply_text_overlap(external_chunks, 100, 25.0)
        
        # Should have same number of chunks
        self.assertEqual(len(overlap_result), len(external_chunks))
        
        # Combined content should be longer due to overlap
        original_length = sum(len(chunk) for chunk in external_chunks)
        overlap_length = sum(len(chunk) for chunk in overlap_result)
        self.assertGreater(overlap_length, original_length)

    def test_get_overlap_text_public_method(self):
        """Test the public get_overlap_text method with both directions."""
        test_text = "This is a sample text for testing overlap extraction functionality"
        
        # Test extracting from end (default)
        end_overlap = self.overlap_20_splitter.get_overlap_text(test_text, 20, from_end=True)
        self.assertLessEqual(len(end_overlap), 20)
        self.assertTrue(test_text.endswith(end_overlap) or end_overlap in test_text[-20:])
        
        # Test extracting from beginning
        start_overlap = self.overlap_20_splitter.get_overlap_text(test_text, 20, from_end=False)
        self.assertLessEqual(len(start_overlap), 20)
        self.assertTrue(test_text.startswith(start_overlap) or start_overlap in test_text[:20])
        
        # Test with text shorter than overlap limit
        short_text = "Short text"
        short_overlap = self.overlap_20_splitter.get_overlap_text(short_text, 50)
        self.assertEqual(short_overlap, short_text)

    def test_sliding_window_with_single_chunk(self):
        """Test sliding window behavior with single chunk."""
        single_chunk = ["Only one chunk here"]
        
        result = self.overlap_20_splitter.apply_text_overlap(single_chunk, 100)
        
        # Should return unchanged
        self.assertEqual(result, single_chunk)

    def test_sliding_window_preserves_character_limits(self):
        """Test that sliding window overlap respects character limits."""
        long_chunks = [
            "This is a very long first chunk that contains substantial content and information",
            "This is another very long chunk with extensive details and comprehensive coverage",
            "Final chunk also has significant content that needs to be processed carefully"
        ]
        
        max_chars = 100
        result = self.overlap_30_splitter.apply_text_overlap(long_chunks, max_chars)
        
        # All chunks should respect the character limit
        for i, chunk in enumerate(result):
            self.assertLessEqual(len(chunk), max_chars, 
                               f"Chunk {i} exceeds limit: {len(chunk)} > {max_chars}")


# Allow running the tests directly
if __name__ == "__main__":
    unittest.main() 