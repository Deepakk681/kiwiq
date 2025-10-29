from typing import Dict, List, Any, Optional, Union, Tuple
import json


class JSONSplitter:
    """
    A comprehensive JSON splitter that handles document clustering based on JSON paths,
    recursive JSON splitting, and text splitting with character limits.
    
    This class provides functionality to:
    1. Map JSON paths to information clusters based on predefined mappings
    2. Split JSON documents using LangChain's RecursiveJsonSplitter
    3. Recursively split text content to meet character limits
    4. Manage JSON value splitting while respecting overall JSON character limits
    """
    
    def __init__(self, 
                 max_json_chunk_size: int = 700,
                 max_text_char_limit: int = 700,
                 max_json_char_limit: int = 700,
                 text_overlap_percent: float = 20.0):
        """
        Initialize the JSON splitter with configurable limits.
        
        Args:
            max_json_chunk_size: Maximum size for JSON chunks in RecursiveJsonSplitter
            max_text_char_limit: Maximum character limit for individual text splits
            max_json_char_limit: Maximum character limit for complete JSON objects
            text_overlap_percent: Percentage (0-100) of text to overlap between chunks for context
        """
        self.max_json_chunk_size = max_json_chunk_size
        self.max_text_char_limit = max_text_char_limit
        self.max_json_char_limit = max_json_char_limit
        self.text_overlap_percent = max(0.0, min(100.0, text_overlap_percent))  # Clamp between 0-100
        self._space_model_available = True
        self.nlp = None  # Initialize nlp attribute
    
    def _load_spacy_model(self):
        """
        Load the spaCy model for sentence splitting.
        """
        if self.nlp is not None or not self._space_model_available:
            return
        
        import spacy
        
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            # Fallback if model not available - user will need to install it
            print("Warning: spaCy model 'en_core_web_sm' not found. Please install it with: python -m spacy download en_core_web_sm")
            self.nlp = None
            self._space_model_available = False
    
    def get_cluster_mapping(self, doc_type: str) -> Optional[Dict[str, str]]:
        """
        Get the cluster mapping for a specific document type.
        
        This method should be extended to support different document types
        and their corresponding cluster mappings. Currently includes a sample
        mapping structure.
        
        Args:
            doc_type: The type of document to get cluster mapping for
            
        Returns:
            Dictionary mapping JSON paths to cluster names, or None if no mapping exists
            
        Design Decision:
            - Using a method rather than a static dict to allow for dynamic mapping
            - Future enhancement could load mappings from a configuration file or database
        """
        cluster_map = None
        # Sample cluster mapping - can be extended for different doc types
        # sample_cluster_map = {
        #     # Metadata (not in any cluster spec)
        #     "title": "metadata",
            
        #     # Current content understanding cluster
        #     "content_pillars": "current_content_understanding",
        #     "content_pillars.name": "current_content_understanding", 
        #     "content_pillars.pillar": "current_content_understanding",
        #     "content_pillars.sub_topic": "current_content_understanding",
            
        #     # Add more mappings as needed for different document types
        # }
        if doc_type == "content_strategy_doc":
            cluster_map = {
                # ─────────── metadata (not in any cluster spec) ───────────
                "title": "metadata",                 # top-level strategy title

                # ─────────── current_content_understanding ───────────
                "content_pillars.name": "current_content_understanding",
                "content_pillars.pillar": "current_content_understanding",
                "content_pillars.sub_topic": "current_content_understanding",

                "post_performance_analysis.current_engagement": "current_content_understanding",
                "post_performance_analysis.content_that_resonates": "current_content_understanding",
                "post_performance_analysis.audience_response": "current_content_understanding",

                # ─────────── user_related_information ───────────
                "target_audience.primary": "user_related_information",
                "target_audience.secondary": "user_related_information",
                "target_audience.tertiary": "user_related_information",

                "foundation_elements.expertise": "user_related_information",
                "foundation_elements.core_beliefs": "user_related_information",
                "foundation_elements.objectives": "user_related_information",

                "core_perspectives": "user_related_information",

                # ─────────── content_goals ───────────

                "implementation.thirty_day_targets.goal": "content_goals",
                "implementation.thirty_day_targets.method": "content_goals",
                "implementation.thirty_day_targets.targets": "content_goals",

                "implementation.ninety_day_targets.goal": "content_goals",
                "implementation.ninety_day_targets.method": "content_goals",
                "implementation.ninety_day_targets.targets": "content_goals"
            }
        elif doc_type == "user_dna_doc":
            cluster_map = {
                # ─────────────────── writing_style_information ───────────────────
                "brand_voice_and_style.communication_style": "writing_style_information",
                "brand_voice_and_style.tone_preferences": "writing_style_information",
                "brand_voice_and_style.vocabulary_level": "writing_style_information",
                "brand_voice_and_style.sentence_structure_preferences": "writing_style_information",
                "brand_voice_and_style.content_format_preferences": "writing_style_information",
                "brand_voice_and_style.emoji_usage": "writing_style_information",
                "brand_voice_and_style.hashtag_usage": "writing_style_information",
                "brand_voice_and_style.storytelling_approach": "writing_style_information",

                "analytics_insights.optimal_content_length": "writing_style_information",
                "analytics_insights.audience_geographic_distribution": "writing_style_information",
                "analytics_insights.engagement_time_patterns": "writing_style_information",
                "analytics_insights.keyword_performance_analysis": "writing_style_information",
                "analytics_insights.competitor_benchmarking": "writing_style_information",
                "analytics_insights.growth_rate_metrics": "writing_style_information",

                # ─────────────────── personal_context_information ───────────────────
                "professional_identity.full_name": "personal_context_information",
                "professional_identity.job_title": "personal_context_information",
                "professional_identity.industry_sector": "personal_context_information",
                "professional_identity.company_name": "personal_context_information",
                "professional_identity.company_size": "personal_context_information",
                "professional_identity.years_of_experience": "personal_context_information",
                "professional_identity.professional_certifications": "personal_context_information",
                "professional_identity.areas_of_expertise": "personal_context_information",
                "professional_identity.career_milestones": "personal_context_information",
                "professional_identity.professional_bio": "personal_context_information",

                "linkedin_profile_analysis.follower_count": "personal_context_information",
                "linkedin_profile_analysis.connection_count": "personal_context_information",
                "linkedin_profile_analysis.profile_headline_analysis": "personal_context_information",
                "linkedin_profile_analysis.about_section_summary": "personal_context_information",
                "linkedin_profile_analysis.top_performing_content_pillars": "personal_context_information",
                "linkedin_profile_analysis.content_posting_frequency": "personal_context_information",
                "linkedin_profile_analysis.content_types_used": "personal_context_information",
                "linkedin_profile_analysis.network_composition": "personal_context_information",

                "personal_context.personal_values": "personal_context_information",
                "personal_context.professional_mission_statement": "personal_context_information",
                "personal_context.content_creation_challenges": "personal_context_information",
                "personal_context.personal_story_elements_for_content": "personal_context_information",
                "personal_context.notable_life_experiences": "personal_context_information",
                "personal_context.inspirations_and_influences": "personal_context_information",
                "personal_context.books_resources_they_reference": "personal_context_information",
                "personal_context.quotes_they_resonate_with": "personal_context_information",

                # ─────────────────── content_information ───────────────────
                "success_metrics.content_performance_kpis": "content_information",
                "success_metrics.engagement_quality_metrics": "content_information",
                "success_metrics.conversion_goals": "content_information",
                "success_metrics.brand_perception_goals": "content_information",
                "success_metrics.timeline_for_expected_results": "content_information",
                "success_metrics.benchmarking_standards": "content_information",

                "content_strategy_goals.primary_goal": "content_information",
                "content_strategy_goals.secondary_goals": "content_information",
                "content_strategy_goals.target_audience_demographics": "content_information",
                "content_strategy_goals.ideal_reader_personas": "content_information",
                "content_strategy_goals.audience_pain_points": "content_information",
                "content_strategy_goals.value_proposition_to_audience": "content_information",
                "content_strategy_goals.call_to_action_preferences": "content_information",
                "content_strategy_goals.content_pillar_themes": "content_information",
                "content_strategy_goals.topics_of_interest": "content_information",
                "content_strategy_goals.topics_to_avoid": "content_information",

                "linkedin_profile_analysis.engagement_metrics.average_likes_per_post": "content_information",
                "linkedin_profile_analysis.engagement_metrics.average_comments_per_post": "content_information",
                "linkedin_profile_analysis.engagement_metrics.average_shares_per_post": "content_information",
            }
        
        return cluster_map
    
    def flatten_json(self, json_obj: Dict[str, Any], parent_path: str = "") -> Dict[str, Any]:
        """
        Flatten a nested JSON object into path:value pairs.
        
        Args:
            json_obj: The JSON object to flatten
            parent_path: The parent path for recursive calls
            
        Returns:
            Dictionary with flattened paths as keys and values as values
            
        Example:
            Input: {"a": {"b": {"c": 1}}}
            Output: {"a.b.c": 1}
        """
        flattened = {}
        
        for key, value in json_obj.items():
            # Construct the full path
            current_path = f"{parent_path}.{key}" if parent_path else key
            
            if isinstance(value, dict):
                # Recursively flatten nested dictionaries
                flattened.update(self.flatten_json(value, current_path))
            elif isinstance(value, list):
                # Handle lists by indexing each element
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        flattened.update(self.flatten_json(item, f"{current_path}.{i}"))
                    else:
                        flattened[f"{current_path}.{i}"] = item
            else:
                # Leaf value
                flattened[current_path] = value
        
        return flattened
    
    def group_paths_by_clusters(self, 
                               flattened_json: Dict[str, Any], 
                               cluster_mapping: Optional[Dict[str, str]]) -> Dict[str, Dict[str, Any]]:
        """
        Group flattened JSON paths into clusters based on the provided mapping.
        
        Args:
            flattened_json: Dictionary of flattened JSON paths and values
            cluster_mapping: Mapping of JSON paths to cluster names
            
        Returns:
            Dictionary with cluster names as keys and grouped path:value pairs as values
            
        Logic:
            - If cluster_mapping is provided, group paths according to mapping
            - Unmapped paths go to "default" cluster
            - If no mapping provided, all paths go to "default" cluster
        """
        if not cluster_mapping:
            return {"default": flattened_json}
        
        clusters = {}
        
        for path, value in flattened_json.items():
            cluster_name = "default"  # Default cluster for unmapped paths
            
            # Try exact match first
            if path in cluster_mapping:
                cluster_name = cluster_mapping[path]
            else:
                # Try to match by removing numeric array indices
                # "content_pillars.0.name" should match "content_pillars.name"
                normalized_path = self._normalize_path_for_matching(path)
                
                if normalized_path in cluster_mapping:
                    cluster_name = cluster_mapping[normalized_path]
                else:
                    # Try prefix matching for both original and normalized paths
                    for mapped_path, mapped_cluster in cluster_mapping.items():
                        if self._is_path_match(path, mapped_path) or self._is_path_match(normalized_path, mapped_path):
                            cluster_name = mapped_cluster
                            break
            
            # Initialize cluster if not exists
            if cluster_name not in clusters:
                clusters[cluster_name] = {}
            
            clusters[cluster_name][path] = value
        
        return clusters
    
    def _normalize_path_for_matching(self, path: str) -> str:
        """
        Normalize a path by removing numeric array indices.
        
        Args:
            path: Original path like "content_pillars.0.name"
            
        Returns:
            Normalized path like "content_pillars.name"
        """
        if '.' not in path:
            return path
        
        parts = path.split('.')
        normalized_parts = [part for part in parts if not part.isdigit()]
        return '.'.join(normalized_parts)
    
    def _is_path_match(self, path: str, mapped_path: str) -> bool:
        """
        Check if a path matches a mapped path as a prefix.
        
        Args:
            path: The actual path to check
            mapped_path: The mapped path pattern
            
        Returns:
            True if path matches mapped_path as a prefix
        """
        if not path.startswith(mapped_path):
            return False
        
        # Ensure it's a proper prefix match (followed by . or end of string)
        return len(path) == len(mapped_path) or path[len(mapped_path)] == '.'
    
    def reconstruct_json_from_paths(self, flattened_paths: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively reconstruct a JSON object from flattened paths.
        
        This method groups paths by their first level and recursively processes
        nested structures. It properly handles both dictionary keys and array indices.
        
        Args:
            flattened_paths: Dictionary of flattened paths and values
            
        Returns:
            Reconstructed JSON object
            
        Algorithm:
            1. Group paths by their first component (before first dot/bracket)
            2. For simple paths (no nesting), add directly to result
            3. For nested paths, recursively process child paths
            4. Handle arrays by detecting numeric indices and creating lists
        """
        if not flattened_paths:
            return {}
        
        return self._reconstruct_recursive(flattened_paths)
    
    def _reconstruct_recursive(self, paths: Dict[str, Any]) -> Union[Dict[str, Any], List[Any]]:
        """
        Helper method for recursive JSON reconstruction.
        
        Args:
            paths: Dictionary of paths and their values
            
        Returns:
            Reconstructed object (dict or list)
        """
        if not paths:
            return {}
        
        # Group paths by their first component
        grouped_paths = self._group_paths_by_first_component(paths)
        
        # Check if we should create a list (all keys are numeric AND continuous)
        should_be_list = self._should_create_list(grouped_paths.keys())
        
        if should_be_list:
            # Create a list with continuous numeric indices
            numeric_keys = [int(k) for k in grouped_paths.keys() if k.isdigit()]
            max_index = max(numeric_keys)
            result = [None] * (max_index + 1)
            
            for key_str, sub_paths in grouped_paths.items():
                index = int(key_str)
                if len(sub_paths) == 1 and list(sub_paths.keys())[0] == "":
                    # Direct value (empty remaining path)
                    result[index] = list(sub_paths.values())[0]
                else:
                    # Nested structure - recurse
                    result[index] = self._reconstruct_recursive(sub_paths)
            
            return result
        else:
            # Create a dictionary
            result = {}
            
            for key, sub_paths in grouped_paths.items():
                if len(sub_paths) == 1 and list(sub_paths.keys())[0] == "":
                    # Direct value (empty remaining path)
                    result[key] = list(sub_paths.values())[0]
                else:
                    # Nested structure - recurse
                    result[key] = self._reconstruct_recursive(sub_paths)
            
            return result
    
    def _should_create_list(self, keys) -> bool:
        """
        Determine if keys represent a continuous numeric sequence that should be a list.
        
        Args:
            keys: Collection of keys to check
            
        Returns:
            True if all keys are numeric and form a continuous sequence starting from 0
        """
        if not keys:
            return False
        
        # Check if all keys are numeric
        numeric_keys = []
        for key in keys:
            if not key.isdigit():
                return False
            numeric_keys.append(int(key))
        
        # Check if numeric keys form a continuous sequence starting from 0
        numeric_keys.sort()
        expected_sequence = list(range(len(numeric_keys)))
        
        return numeric_keys == expected_sequence
    
    def _group_paths_by_first_component(self, paths: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """
        Group paths by their first component (before first dot or bracket).
        
        Args:
            paths: Dictionary of flattened paths and values
            
        Returns:
            Dictionary where keys are first components and values are
            dictionaries of remaining paths and values
            
                 Examples:
             Input: {
                 "a.b.c": 1,
                 "a.b.d": 2,
                 "content_pillars.0.name": "Tech",
                 "title": "test"
             }
             Output: {
                 "a": {
                     "b.c": 1,
                     "b.d": 2
                 },
                 "content_pillars": {
                     "0.name": "Tech"
                 },
                 "title": {
                     "": "test"
                 }
             }
        """
        grouped = {}
        
        for path, value in paths.items():
            # Find the first component
            first_component, remaining_path = self._split_first_component(path)
            
            if first_component not in grouped:
                grouped[first_component] = {}
            
            # Add to the group with remaining path
            grouped[first_component][remaining_path] = value
        
        return grouped
    
    def _split_first_component(self, path: str) -> Tuple[str, str]:
        """
        Split a path into its first component and the remaining path.
        
        Since flattening now uses dot notation for everything (including arrays),
        this method simply splits on the first dot.
        
        Args:
            path: The full path string
            
        Returns:
            Tuple of (first_component, remaining_path)
            
        Examples:
            "a.b.c" -> ("a", "b.c")
            "content_pillars.0.name" -> ("content_pillars", "0.name")  
            "title" -> ("title", "")
        """
        if not path:
            return "", ""
        
        dot_pos = path.find('.')
        
        if dot_pos == -1:
            # No nesting - single component
            return path, ""
        else:
            # Split on first dot
            return path[:dot_pos], path[dot_pos + 1:]
    
    def split_text_recursively(self, text: str, max_chars: int) -> List[str]:
        """
        Recursively split text to meet character limits with optional overlap.
        
        Splitting Strategy:
        1. First split by paragraphs (\n\n)
        2. Then by sentences using spaCy
        3. Then by words, dividing recursively
        4. Finally split individual words if needed
        5. Apply overlap between chunks if configured
        
        Args:
            text: The text to split
            max_chars: Maximum character limit per chunk
            
        Returns:
            List of text chunks that meet the character limit with overlap applied
        """
        if len(text) <= max_chars:
            return [text]
        
        chunks = []
        
        # Step 1: Split by paragraphs
        paragraphs = text.split('\n\n')
        
        for paragraph in paragraphs:
            if len(paragraph) <= max_chars:
                chunks.append(paragraph)
            else:
                # Step 2: Split by sentences using spaCy
                sentence_chunks = self._split_by_sentences(paragraph, max_chars)
                chunks.extend(sentence_chunks)
        
        # Apply overlap if configured
        if self.text_overlap_percent > 0 and len(chunks) > 1:
            chunks = self.apply_text_overlap(chunks, max_chars)
        
        return chunks
    
    def apply_text_overlap(self, chunks: List[str], max_chars: int, overlap_percent: Optional[float] = None) -> List[str]:
        """
        Apply text overlap between chunks using a sliding window approach for context preservation.
        
        Args:
            chunks: List of text chunks to apply overlap to
            max_chars: Maximum character limit per chunk
            overlap_percent: Percentage (0-100) of text to overlap. If None, uses instance setting.
            
        Returns:
            List of chunks with sliding window overlap applied
        """
        if len(chunks) <= 1:
            return chunks
        
        # Use provided overlap_percent or fall back to instance setting
        effective_overlap_percent = overlap_percent if overlap_percent is not None else self.text_overlap_percent
        
        if effective_overlap_percent == 0:
            return chunks
        
        overlap_chars = int(max_chars * (effective_overlap_percent / 100))
        if overlap_chars == 0:
            return chunks
        
        overlapped_chunks = []
        
        for i in range(len(chunks)):
            current_chunk = chunks[i]
            
            # Calculate max overlap limits for prev and next
            max_prev_overlap = overlap_chars // 2 if i > 0 and i < len(chunks) - 1 else overlap_chars
            max_next_overlap = overlap_chars // 2 if i > 0 and i < len(chunks) - 1 else overlap_chars
            
            # Get actual overlaps
            prev_overlap = ""
            next_overlap = ""
            
            if i > 0:
                prev_available = min(max_prev_overlap, len(chunks[i - 1]))
                prev_overlap = self.get_overlap_text(chunks[i - 1], prev_available, from_end=True)
            
            if i < len(chunks) - 1:
                next_available = min(max_next_overlap, len(chunks[i + 1]))
                next_overlap = self.get_overlap_text(chunks[i + 1], next_available, from_end=False)
            
            # Redistribute unused overlap space
            if len(prev_overlap) < max_prev_overlap and next_overlap:
                # Give unused prev space to next
                extra_next = max_prev_overlap - len(prev_overlap)
                total_next_limit = min(max_next_overlap + extra_next, len(chunks[i + 1]))
                next_overlap = self.get_overlap_text(chunks[i + 1], total_next_limit, from_end=False)
            
            elif len(next_overlap) < max_next_overlap and prev_overlap:
                # Give unused next space to prev
                extra_prev = max_next_overlap - len(next_overlap)
                total_prev_limit = min(max_prev_overlap + extra_prev, len(chunks[i - 1]))
                prev_overlap = self.get_overlap_text(chunks[i - 1], total_prev_limit, from_end=True)
            
            # Build final chunk
            parts = []
            if prev_overlap:
                parts.append(prev_overlap)
            parts.append(current_chunk)
            if next_overlap:
                parts.append(next_overlap)
            
            combined_chunk = self._join_text_parts(parts)
            
            # Truncate if too long
            if len(combined_chunk) > max_chars:
                combined_chunk = self._truncate_to_fit(combined_chunk, current_chunk, max_chars)
            
            overlapped_chunks.append(combined_chunk)
        
        return overlapped_chunks
    
    def get_overlap_text(self, text: str, overlap_chars: int, from_end: bool = True) -> str:
        """
        Extract overlap text from either end of a chunk, preferring word boundaries.
        
        Args:
            text: Source text to extract overlap from
            overlap_chars: Maximum number of characters to extract
            from_end: If True, extract from end of text. If False, extract from beginning.
            
        Returns:
            Overlap text that respects word boundaries when possible
        """
        if len(text) <= overlap_chars:
            return text
        
        if from_end:
            # Extract from end of text
            candidate_text = text[-overlap_chars:]
            
            # Look for word boundary by finding the first space
            space_index = candidate_text.find(' ')
            if space_index > 0:
                # Found a space, use text from that point onwards
                return candidate_text[space_index + 1:]
            else:
                # No good word boundary found, use character-based split
                return candidate_text
        else:
            # Extract from beginning of text
            candidate_text = text[:overlap_chars]
            
            # Look for word boundary by finding the last space
            space_index = candidate_text.rfind(' ')
            if space_index > 0:
                # Found a space, use text up to that point
                return candidate_text[:space_index]
            else:
                # No good word boundary found, use character-based split
                return candidate_text
    
    def _join_text_parts(self, parts: List[str]) -> str:
        """
        Join text parts with appropriate separators.
        
        Args:
            parts: List of text parts to join
            
        Returns:
            Combined text with proper spacing
        """
        if not parts:
            return ""
        
        if len(parts) == 1:
            return parts[0]
        
        result = parts[0]
        
        for i in range(1, len(parts)):
            current_part = parts[i]
            
            # Add separator if needed
            separator = ""
            if (result and current_part and 
                not result.endswith(' ') and not current_part.startswith(' ') and
                not result.endswith('\n') and not current_part.startswith('\n')):
                separator = " "
            
            result += separator + current_part
        
        return result
    
    def _truncate_to_fit(self, combined_chunk: str, core_chunk: str, max_chars: int) -> str:
        """
        Truncate a combined chunk to fit within character limit, preserving the core chunk.
        
        Args:
            combined_chunk: The full combined chunk with overlaps
            core_chunk: The core chunk that must be preserved
            max_chars: Maximum character limit
            
        Returns:
            Truncated chunk that fits within the limit
        """
        if len(combined_chunk) <= max_chars:
            return combined_chunk
        
        # If core chunk itself is too long, truncate it
        if len(core_chunk) >= max_chars:
            return core_chunk[:max_chars]
        
        # Simple truncation - just cut off the excess
        return combined_chunk[:max_chars]
    
    def _split_by_sentences(self, text: str, max_chars: int) -> List[str]:
        """
        Split text by sentences using spaCy, with fallback to simple splitting.
        
        Args:
            text: Text to split
            max_chars: Maximum character limit
            
        Returns:
            List of sentence-based chunks
        """
        self._load_spacy_model()
        if self.nlp is None:
            # Fallback to simple sentence splitting
            return self._split_by_words(text, max_chars) # TODO: this is a hack to get around the fact that spaCy is not installed
        
        doc = self.nlp(text)
        sentences = [sent.text.strip() for sent in doc.sents]
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk + sentence) <= max_chars:
                current_chunk += sentence + " "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                
                # If single sentence is too long, split by words
                if len(sentence) > max_chars:
                    word_chunks = self._split_by_words(sentence, max_chars)
                    chunks.extend(word_chunks)
                    current_chunk = ""
                else:
                    current_chunk = sentence + " "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _split_by_words(self, text: str, max_chars: int) -> List[str]:
        """
        Split text by words recursively.
        
        Args:
            text: Text to split
            max_chars: Maximum character limit
            
        Returns:
            List of word-based chunks
        """
        words = text.split()
        
        if not words:
            return []
        
        chunks = []
        current_chunk = ""
        
        for word in words:
            if len(current_chunk + word + " ") <= max_chars:
                current_chunk += word + " "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                
                # If single word is too long, split the word
                if len(word) > max_chars:
                    word_chunks = self._split_word(word, max_chars)
                    chunks.extend(word_chunks)
                    current_chunk = ""
                else:
                    current_chunk = word + " "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _split_word(self, word: str, max_chars: int) -> List[str]:
        """
        Split a single word into chunks of maximum character limit.
        
        Args:
            word: Word to split
            max_chars: Maximum character limit
            
        Returns:
            List of word chunks
        """
        if len(word) <= max_chars:
            return [word]
        
        chunks = []
        for i in range(0, len(word), max_chars):
            chunks.append(word[i:i + max_chars])
        
        return chunks
    
    def split_json_values_with_char_limit(self, 
                                        json_obj: Dict[str, Any], 
                                        max_json_chars: int) -> List[Dict[str, Any]]:
        """
        Split JSON object values to meet overall JSON character limits.
        
        Algorithm:
        1. First flatten the JSON to get path:value pairs
        2. Split large text values and create indexed paths
        3. Group flattened pairs into chunks that fit character limit
        4. Reconstruct each chunk back to JSON format
        
        Args:
            json_obj: JSON object to split
            max_json_chars: Maximum character limit for JSON objects
            
        Returns:
            List of JSON objects that meet the character limit
        """
        # Quick check - if JSON already fits, return as is
        if len(json.dumps(json_obj)) <= max_json_chars:
            return [json_obj]
        
        # Step 1: Flatten the JSON
        flattened_json = self.flatten_json(json_obj)
        
        # Step 2: Split large text values in flattened format
        processed_flat_pairs = {}
        
        for path, value in flattened_json.items():
            if isinstance(value, str) and len(value) > self.max_text_char_limit:
                # Split the text value
                text_chunks = self.split_text_recursively(value, self.max_text_char_limit)
                
                if len(text_chunks) == 1:
                    # Single chunk, keep original path
                    processed_flat_pairs[path] = text_chunks[0]
                else:
                    # Multiple chunks, create indexed paths
                    for i, chunk in enumerate(text_chunks):
                        indexed_path = f"{path}_{i}"
                        processed_flat_pairs[indexed_path] = chunk
            else:
                # Keep value as is
                processed_flat_pairs[path] = value
        
        # Step 3: Group flattened pairs into chunks that fit character limit
        json_chunks = []
        current_flat_chunk = {}
        current_chars = 2  # Account for "{}"
        
        for path, value in processed_flat_pairs.items():
            # Calculate character count for this path:value pair
            value_str = json.dumps(value) if not isinstance(value, str) else f'"{value}"'
            path_value_chars = 6 + len(path) + len(value_str)  # 6 for quotes, colon, comma, spaces
            
            # Check if this pair fits in current chunk
            if current_chars + path_value_chars <= max_json_chars:
                current_flat_chunk[path] = value
                current_chars += path_value_chars
            else:
                # Current chunk is full, save it and start new one
                if current_flat_chunk:
                    json_chunks.append(current_flat_chunk.copy())
                
                # Start new chunk
                current_flat_chunk = {path: value}
                current_chars = 2 + path_value_chars
        
        # Add final chunk if it has content
        if current_flat_chunk:
            json_chunks.append(current_flat_chunk)
        
        # return json_chunks
        
        # Step 4: Reconstruct each flattened chunk back to JSON format
        reconstructed_chunks = []
        for flat_chunk in json_chunks:
            reconstructed_json = self.reconstruct_json_from_paths(flat_chunk)
            reconstructed_chunks.append(reconstructed_json)
        
        return reconstructed_chunks
    
    def process_json_document(self, 
                            json_data: Dict[str, Any], 
                            doc_type: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Main method to process a JSON document through the complete splitting pipeline.
        
        Process Flow:
        1. Get cluster mapping for document type
        2. Flatten JSON into path:value pairs
        3. Group paths into clusters
        4. Apply RecursiveJsonSplitter to each cluster
        5. Apply text splitting with character limits
        
        Args:
            json_data: The JSON document to process
            doc_type: The type of document for cluster mapping
            
        Returns:
            Dictionary with cluster names as keys and lists of processed JSON chunks as values
            
        Key Design Decisions:
        - Each cluster is processed independently to maintain logical grouping
        - Character limits are applied at multiple levels for fine-grained control
        - Fallback mechanisms ensure processing continues even if some steps fail
        """
        from langchain_text_splitters import RecursiveJsonSplitter
        
        # Step 1: Get cluster mapping
        cluster_mapping = self.get_cluster_mapping(doc_type)
        
        # Step 2: Flatten JSON
        flattened_json = self.flatten_json(json_data)
        
        # Step 3: Group into clusters
        clusters = self.group_paths_by_clusters(flattened_json, cluster_mapping)
        
        # Step 4 & 5: Process each cluster
        processed_clusters = {}
        
        for cluster_name, cluster_paths in clusters.items():
            # Reconstruct JSON object for this cluster
            cluster_json = self.reconstruct_json_from_paths(cluster_paths)
            
            # Apply RecursiveJsonSplitter
            splitter = RecursiveJsonSplitter(max_chunk_size=self.max_json_chunk_size)
            try:
                json_chunks = splitter.split_json(json_data=cluster_json)
                
                # # Convert chunks back to dictionaries if they're not already
                # if json_chunks and not isinstance(json_chunks[0], dict):
                #     json_chunks = [json.loads(chunk) if isinstance(chunk, str) else chunk for chunk in json_chunks]
                
            except Exception as e:
                # Fallback: use original cluster JSON if splitter fails
                print(f"Warning: RecursiveJsonSplitter failed for cluster {cluster_name}: {e}")
                json_chunks = [cluster_json]
            
            # Apply character limit splitting to each chunk
            final_chunks = []
            for chunk in json_chunks:
                split_chunks = self.split_json_values_with_char_limit(chunk, self.max_json_char_limit)
                final_chunks.extend(split_chunks)
            
            processed_clusters[cluster_name] = final_chunks
        
        return processed_clusters


# Example usage function
def example_usage():
    """
    Example demonstrating how to use the JSONSplitter class.
    
    This function shows a complete workflow from document input to clustered output.
    """
    # Sample JSON document
    sample_document = {
        "title": "Content Strategy Document",
        "content_pillars": [
            {
                "name": "Technical Expertise",
                "pillar": "Authority Building",
                "sub_topic": "Advanced development techniques and best practices for modern software engineering"
            },
            {
                "name": "Industry Insights", 
                "pillar": "Thought Leadership",
                "sub_topic": "Analysis of emerging trends in technology and their impact on business transformation"
            }
        ],
        "additional_context": "This document provides comprehensive guidance for content creation strategies focused on technical authority and industry leadership."
    }
    
    # Initialize splitter with text overlap for context preservation
    splitter = JSONSplitter(
        max_json_chunk_size=300,
        max_text_char_limit=200,
        max_json_char_limit=800,
        text_overlap_percent=20.0  # 20% overlap between text chunks
    )
    
    # Process document
    result = splitter.process_json_document(sample_document, "content_strategy")
    
    # Display results
    for cluster_name, chunks in result.items():
        print(f"\n=== Cluster: {cluster_name} ===")
        for i, chunk in enumerate(chunks):
            print(f"Chunk {i + 1}: {json.dumps(chunk, indent=2)}")
    
    return result


if __name__ == "__main__":
    # Run example when script is executed directly
    example_usage()
