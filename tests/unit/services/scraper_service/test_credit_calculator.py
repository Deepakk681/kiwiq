"""
Test cases for the credit calculator to ensure accurate credit estimation.
Uses ScrapingRequest schema for validation to ensure test data matches real-world usage.
"""
import unittest
import asyncio
from typing import Dict, Any, List, Tuple
from unittest.mock import MagicMock, AsyncMock, patch

# Import necessary components
from services.scraper_service.credit_calculator import credit_estimation, calculate_post_enrichment_credits
from services.scraper_service.client.schemas.job_config_schema import ScrapingRequest, JobTypeEnum, EntityTypeEnum, YesNoEnum
from services.scraper_service.settings import rapid_api_settings
from kiwi_app.settings import settings as kiwi_settings
from pydantic import ValidationError


class TestCreditCalculator(unittest.IsolatedAsyncioTestCase):
    """Test suite for credit calculator functionality."""

    def setUp(self):
        """Set up test environment."""
        # Any necessary setup can go here
        pass

    async def _calculate_expected_credits(self, scraping_request: Dict[str, Any]) -> Dict[str, Any]:
        """Helper method to calculate expected credits for a scraping request."""
        # Map the fields to match what credit_calculator expects
        mapped_request = scraping_request.copy()
        
        # Ensure all required fields are present with defaults first
        mapped_request.setdefault("profile_info", "no")
        mapped_request.setdefault("entity_posts", "no")
        mapped_request.setdefault("activity_comments", "no")
        mapped_request.setdefault("activity_reactions", "no")
        mapped_request.setdefault("search_post_by_keyword", "no")
        mapped_request.setdefault("search_post_by_hashtag", "no")
        mapped_request.setdefault("post_comments", "no")
        mapped_request.setdefault("post_reactions", "no")
        mapped_request.setdefault("post_limit", 0)
        mapped_request.setdefault("comment_limit", rapid_api_settings.DEFAULT_COMMENT_LIMIT)
        mapped_request.setdefault("reaction_limit", rapid_api_settings.DEFAULT_REACTION_LIMIT)
        mapped_request.setdefault("type", "person")  # Default type if not specified
        
        # Now map entity_posts to post_scrap (credit_calculator expects this)
        mapped_request["post_scrap"] = mapped_request.pop("entity_posts", "no")
        
        credit_result = await credit_estimation(mapped_request)
        return {
            "max_credits": credit_result["max_credits"],
            "min_credits": credit_result["min_credits"],
            "dollar_cost": credit_result["max_credits"] * kiwi_settings.SCRAPING_CREDIT_PRICE
        }

    async def test_profile_info_person(self):
        """Test simple profile info for person."""
        job_config = {
            "job_type": JobTypeEnum.PROFILE_INFO,
            "type": EntityTypeEnum.PERSON,
            "profile_info": YesNoEnum.YES,
            "username": "test-user"
        }
        
        # Validate through schema
        validated_config = ScrapingRequest(**job_config)
        request_dict = validated_config.model_dump(mode="python", exclude_none=True)
        
        # Calculate credits
        result = await credit_estimation(request_dict)
        
        # Assertions
        self.assertEqual(result["min_credits"], 1)
        self.assertEqual(result["max_credits"], 1)

    async def test_company_info(self):
        """Test company info only."""
        job_config = {
            "job_type": JobTypeEnum.PROFILE_INFO,
            "type": EntityTypeEnum.COMPANY,
            "profile_info": YesNoEnum.YES,
            "username": "test-company"
        }
        
        validated_config = ScrapingRequest(**job_config)
        request_dict = validated_config.model_dump(mode="python", exclude_none=True)
        
        result = await credit_estimation(request_dict)
        
        self.assertEqual(result["min_credits"], 1)
        self.assertEqual(result["max_credits"], 1)

    async def test_entity_posts_single_batch(self):
        """Test entity posts - single batch (50 posts)."""
        job_config = {
            "job_type": JobTypeEnum.ENTITY_POSTS,
            "type": EntityTypeEnum.PERSON,
            "entity_posts": YesNoEnum.YES,
            "username": "test-user",
            "post_limit": 50
        }
        
        validated_config = ScrapingRequest(**job_config)
        request_dict = validated_config.model_dump(mode="python", exclude_none=True)
        
        # Map entity_posts to post_scrap for credit calculator
        request_dict["post_scrap"] = request_dict.get("entity_posts", "no")
        
        result = await credit_estimation(request_dict)
        
        self.assertEqual(result["min_credits"], 1)
        self.assertEqual(result["max_credits"], 1)

    async def test_entity_posts_multiple_batches(self):
        """Test entity posts - multiple batches (100 posts)."""
        job_config = {
            "job_type": JobTypeEnum.ENTITY_POSTS,
            "type": EntityTypeEnum.PERSON,
            "entity_posts": YesNoEnum.YES,
            "username": "test-user",
            "post_limit": 100
        }
        
        validated_config = ScrapingRequest(**job_config)
        request_dict = validated_config.model_dump(mode="python", exclude_none=True)
        
        # Map entity_posts to post_scrap for credit calculator
        request_dict["post_scrap"] = request_dict.get("entity_posts", "no")
        
        result = await credit_estimation(request_dict)
        
        self.assertEqual(result["min_credits"], 2)
        self.assertEqual(result["max_credits"], 2)

    async def test_entity_posts_with_comments(self):
        """Test entity posts with comments (default limit)."""
        job_config = {
            "job_type": JobTypeEnum.ENTITY_POSTS,
            "type": EntityTypeEnum.PERSON,
            "entity_posts": YesNoEnum.YES,
            "username": "test-user",
            "post_limit": 10,
            "post_comments": YesNoEnum.YES
        }
        
        validated_config = ScrapingRequest(**job_config)
        request_dict = validated_config.model_dump(mode="python", exclude_none=True)
        
        # Map entity_posts to post_scrap for credit calculator
        request_dict["post_scrap"] = request_dict.get("entity_posts", "no")
        
        result = await credit_estimation(request_dict)
        
        # 1 batch + 10 posts (1 page each)
        self.assertEqual(result["min_credits"], 11)
        self.assertEqual(result["max_credits"], 11)

    async def test_company_posts_with_comments_and_reactions(self):
        """Test company posts with comments and reactions."""
        job_config = {
            "job_type": JobTypeEnum.ENTITY_POSTS,
            "type": EntityTypeEnum.COMPANY,
            "entity_posts": YesNoEnum.YES,
            "username": "test-company",
            "post_limit": 5,
            "post_comments": YesNoEnum.YES,
            "comment_limit": 100,  # Needs 2 pages (100/50)
            "post_reactions": YesNoEnum.YES,
            "reaction_limit": 150  # Needs 3 pages (150/50)
        }
        
        validated_config = ScrapingRequest(**job_config)
        request_dict = validated_config.model_dump(mode="python", exclude_none=True)
        
        # Map entity_posts to post_scrap for credit calculator
        request_dict["post_scrap"] = request_dict.get("entity_posts", "no")
        
        result = await credit_estimation(request_dict)
        
        # 1 batch + 5 comments min + 5 reactions min (2 credits each)
        self.assertEqual(result["min_credits"], 16)  # 1 + 5 + 10
        # 1 batch + 5*2 comments + 5*(2+2) reactions (first page 2, then 2 more pages at 1 each)
        self.assertEqual(result["max_credits"], 31)  # 1 + 10 + 20

    async def test_activity_comments(self):
        """Test activity comments only."""
        job_config = {
            "job_type": JobTypeEnum.ACTIVITY_COMMENTS,
            "activity_comments": YesNoEnum.YES,
            "username": "test-user",
            "post_limit": 10
        }
        
        validated_config = ScrapingRequest(**job_config)
        request_dict = validated_config.model_dump(mode="python", exclude_none=True)
        
        result = await credit_estimation(request_dict)
        
        self.assertEqual(result["min_credits"], 1)
        self.assertEqual(result["max_credits"], 1)

    async def test_activity_comments_with_enrichment(self):
        """Test activity comments with full enrichment."""
        job_config = {
            "job_type": JobTypeEnum.ACTIVITY_COMMENTS,
            "activity_comments": YesNoEnum.YES,
            "username": "test-user",
            "post_limit": 5,
            "post_comments": YesNoEnum.YES,
            "comment_limit": 200,  # Needs 4 pages (200/50)
            "post_reactions": YesNoEnum.YES,
            "reaction_limit": 100  # Needs 2 pages (100/50)
        }
        
        validated_config = ScrapingRequest(**job_config)
        request_dict = validated_config.model_dump(mode="python", exclude_none=True)
        
        result = await credit_estimation(request_dict)
        
        # 1 base + 5 comments min + 5 reactions min (2 credits each)
        self.assertEqual(result["min_credits"], 16)  # 1 + 5 + 10
        # 1 base + 5*4 comments + 5*(2+1) reactions (first page 2, second page 1)
        self.assertEqual(result["max_credits"], 36)  # 1 + 20 + 15

    async def test_activity_reactions_single_batch(self):
        """Test activity reactions - single batch."""
        job_config = {
            "job_type": JobTypeEnum.ACTIVITY_REACTIONS,
            "activity_reactions": YesNoEnum.YES,
            "username": "test-user",
            "post_limit": 100
        }
        
        validated_config = ScrapingRequest(**job_config)
        request_dict = validated_config.model_dump(mode="python", exclude_none=True)
        
        result = await credit_estimation(request_dict)
        
        self.assertEqual(result["min_credits"], 1)
        self.assertEqual(result["max_credits"], 1)

    async def test_activity_reactions_with_enrichment(self):
        """Test activity reactions with enrichment."""
        job_config = {
            "job_type": JobTypeEnum.ACTIVITY_REACTIONS,
            "activity_reactions": YesNoEnum.YES,
            "username": "test-user",
            "post_limit": 50,
            "post_comments": YesNoEnum.YES,
            "post_reactions": YesNoEnum.YES
        }
        
        validated_config = ScrapingRequest(**job_config)
        request_dict = validated_config.model_dump(mode="python", exclude_none=True)
        
        result = await credit_estimation(request_dict)
        
        # 1 batch + 50 comments + 50 reactions (2 credits each)
        self.assertEqual(result["min_credits"], 151)  # 1 + 50 + 100
        self.assertEqual(result["max_credits"], 151)  # Same with default limits

    async def test_search_by_keyword(self):
        """Test search posts by keyword."""
        job_config = {
            "job_type": JobTypeEnum.SEARCH_POST_BY_KEYWORD,
            "search_post_by_keyword": YesNoEnum.YES,
            "keyword": "machine learning",
            "post_limit": 25
        }
        
        validated_config = ScrapingRequest(**job_config)
        request_dict = validated_config.model_dump(mode="python", exclude_none=True)
        
        result = await credit_estimation(request_dict)
        
        # 25 posts / 10 per page = 3 pages
        self.assertEqual(result["min_credits"], 3)
        self.assertEqual(result["max_credits"], 3)

    async def test_search_by_hashtag(self):
        """Test search posts by hashtag."""
        job_config = {
            "job_type": JobTypeEnum.SEARCH_POST_BY_HASHTAG,
            "search_post_by_hashtag": YesNoEnum.YES,
            "hashtag": "artificialintelligence",
            "post_limit": 75
        }
        
        validated_config = ScrapingRequest(**job_config)
        request_dict = validated_config.model_dump(mode="python", exclude_none=True)
        
        result = await credit_estimation(request_dict)
        
        # 75 posts / 50 per page = 2 pages
        self.assertEqual(result["min_credits"], 2)
        self.assertEqual(result["max_credits"], 2)

    async def test_post_details_basic(self):
        """Test basic post details without enrichment."""
        job_config = {
            "job_type": JobTypeEnum.POST_DETAILS,
            "post_details": YesNoEnum.YES,
            "post_url_or_urn": "https://www.linkedin.com/posts/username_post-activity-12345_abcdef"
        }
        
        validated_config = ScrapingRequest(**job_config)
        request_dict = validated_config.model_dump(mode="python", exclude_none=True)
        
        result = await credit_estimation(request_dict)
        
        # 1 credit for basic post details
        self.assertEqual(result["min_credits"], 1)
        self.assertEqual(result["max_credits"], 1)

    async def test_post_details_with_comments(self):
        """Test post details with comments only."""
        job_config = {
            "job_type": JobTypeEnum.POST_DETAILS,
            "post_details": YesNoEnum.YES,
            "post_url_or_urn": "https://www.linkedin.com/posts/username_post-activity-12345_abcdef",
            "post_comments": YesNoEnum.YES,
            "comment_limit": 100  # Needs 2 pages (100/50)
        }
        
        validated_config = ScrapingRequest(**job_config)
        request_dict = validated_config.model_dump(mode="python", exclude_none=True)
        
        result = await credit_estimation(request_dict)
        
        # 1 base + 1 comment min
        self.assertEqual(result["min_credits"], 2)
        # 1 base + 2 comment pages max
        self.assertEqual(result["max_credits"], 3)

    async def test_post_details_with_reactions(self):
        """Test post details with reactions only."""
        job_config = {
            "job_type": JobTypeEnum.POST_DETAILS,
            "post_details": YesNoEnum.YES,
            "post_url_or_urn": "https://www.linkedin.com/posts/username_post-activity-12345_abcdef",
            "post_reactions": YesNoEnum.YES,
            "reaction_limit": 150  # Needs 3 pages (150/50)
        }
        
        validated_config = ScrapingRequest(**job_config)
        request_dict = validated_config.model_dump(mode="python", exclude_none=True)
        
        result = await credit_estimation(request_dict)
        
        # 1 base + 2 reaction min (first page costs 2)
        self.assertEqual(result["min_credits"], 3)
        # 1 base + 1*(2+2) reactions (first page 2, then 2 more pages at 1 each)
        self.assertEqual(result["max_credits"], 5)

    async def test_post_details_with_full_enrichment(self):
        """Test post details with both comments and reactions."""
        job_config = {
            "job_type": JobTypeEnum.POST_DETAILS,
            "post_details": YesNoEnum.YES,
            "post_url_or_urn": "https://www.linkedin.com/posts/username_post-activity-12345_abcdef",
            "post_comments": YesNoEnum.YES,
            "comment_limit": 200,  # Needs 4 pages (200/50)
            "post_reactions": YesNoEnum.YES,
            "reaction_limit": 100  # Needs 2 pages (100/50)
        }
        
        validated_config = ScrapingRequest(**job_config)
        request_dict = validated_config.model_dump(mode="python", exclude_none=True)
        
        result = await credit_estimation(request_dict)
        
        # 1 base + 1 comment min + 2 reaction min
        self.assertEqual(result["min_credits"], 4)
        # 1 base + 4 comment pages + 3 reaction pages (2+1)
        self.assertEqual(result["max_credits"], 8)

    async def test_post_details_validation_missing_url(self):
        """Test that POST_DETAILS without post_url_or_urn causes validation error."""
        job_config = {
            "job_type": JobTypeEnum.POST_DETAILS,
            "post_details": YesNoEnum.YES
            # Missing post_url_or_urn
        }
        
        with self.assertRaises(ValidationError) as context:
            ScrapingRequest(**job_config)
        
        error_messages = str(context.exception)
        self.assertIn("post_url_or_urn", error_messages.lower())

    async def test_post_details_type_set_automatically(self):
        """Test that POST_DETAILS automatically sets type to POST."""
        job_config = {
            "job_type": JobTypeEnum.POST_DETAILS,
            "post_details": YesNoEnum.YES,
            "post_url_or_urn": "https://www.linkedin.com/posts/username_post-activity-12345_abcdef"
        }
        
        validated_config = ScrapingRequest(**job_config)
        request_dict = validated_config.model_dump(mode="python", exclude_none=True)
        
        # Verify type was set to POST automatically
        self.assertEqual(request_dict.get("type"), EntityTypeEnum.POST.value)

    async def test_post_details_with_urn_format(self):
        """Test post details with URN format instead of URL."""
        job_config = {
            "job_type": JobTypeEnum.POST_DETAILS,
            "post_details": YesNoEnum.YES,
            "post_url_or_urn": "7335304292926451712"  # Just the URN number
        }
        
        validated_config = ScrapingRequest(**job_config)
        request_dict = validated_config.model_dump(mode="python", exclude_none=True)
        
        result = await credit_estimation(request_dict)
        
        # 1 credit for basic post details
        self.assertEqual(result["min_credits"], 1)
        self.assertEqual(result["max_credits"], 1)
        
        # Verify type was set to POST automatically
        self.assertEqual(request_dict.get("type"), EntityTypeEnum.POST.value)

    async def test_validation_error_multiple_job_types(self):
        """Test that multiple job types cause validation error."""
        job_config = {
            "job_type": JobTypeEnum.PROFILE_INFO,
            "type": EntityTypeEnum.PERSON,
            "profile_info": YesNoEnum.YES,
            "entity_posts": YesNoEnum.YES,  # This should cause validation error
            "username": "test-user"
        }
        
        with self.assertRaises(ValidationError) as context:
            ScrapingRequest(**job_config)
        
        self.assertGreater(context.exception.error_count(), 0)

    async def test_edge_case_very_high_limits(self):
        """Test edge case with very high limits."""
        job_config = {
            "job_type": JobTypeEnum.ENTITY_POSTS,
            "type": EntityTypeEnum.PERSON,
            "entity_posts": YesNoEnum.YES,
            "username": "test-user",
            "post_limit": 1,
            "post_comments": YesNoEnum.YES,
            "comment_limit": 1000,  # 20 pages (1000/50)
            "post_reactions": YesNoEnum.YES,
            "reaction_limit": 500   # 10 pages (500/50)
        }
        
        validated_config = ScrapingRequest(**job_config)
        request_dict = validated_config.model_dump(mode="python", exclude_none=True)
        
        # Map entity_posts to post_scrap for credit calculator
        request_dict["post_scrap"] = request_dict.get("entity_posts", "no")
        
        result = await credit_estimation(request_dict)
        
        # 1 batch + 1 comment min + 1 reaction min (2 credits)
        self.assertEqual(result["min_credits"], 4)  # 1 + 1 + 2
        # 1 batch + 1*20 + 1*(2+9) reactions (first page 2, 9 more pages at 1 each)
        self.assertEqual(result["max_credits"], 32)  # 1 + 20 + 11

    async def test_credit_breakdown_feature(self):
        """Test the breakdown functionality of credit estimation."""
        # Create a complex scenario to test breakdown
        complex_job = ScrapingRequest(
            job_type=JobTypeEnum.ENTITY_POSTS,
            type=EntityTypeEnum.PERSON,
            entity_posts=YesNoEnum.YES,
            username="test-user",
            post_limit=25,
            post_comments=YesNoEnum.YES,
            comment_limit=100,
            post_reactions=YesNoEnum.YES,
            reaction_limit=75
        )
        
        request_dict = complex_job.model_dump(mode="python", exclude_none=True)
        
        # Map entity_posts to post_scrap for credit calculator
        request_dict["post_scrap"] = request_dict.get("entity_posts", "no")
        
        # Get estimation (breakdown is always included now)
        result = await credit_estimation(request_dict)
        
        # Verify breakdown exists
        self.assertIn('breakdown', result)
        breakdown = result['breakdown']
        
        # Verify components
        self.assertIn('profile_info', breakdown)
        self.assertIn('posts_fetching', breakdown)
        self.assertIn('comments_enrichment', breakdown)
        self.assertIn('reactions_enrichment', breakdown)
        self.assertIn('activity_fetching', breakdown)
        self.assertIn('search_operations', breakdown)
        self.assertIn('post_details', breakdown)
        
        # Verify breakdown adds up correctly
        total_max = (
            breakdown['profile_info'] +
            breakdown['posts_fetching'] +
            breakdown['comments_enrichment']['max'] +
            breakdown['reactions_enrichment']['max'] +
            breakdown['activity_fetching'] +
            breakdown['search_operations'] +
            breakdown['post_details']
        )
        
        self.assertEqual(total_max, result['max_credits'])

    async def test_enrichment_helper_function(self):
        """Test the calculate_post_enrichment_credits helper function."""
        # Test cases: (post_count, comments, reactions, comment_limit, reaction_limit, expected_min, expected_max)
        test_cases = [
            (10, True, True, 50, 50, 30, 30),        # Both fit in 1 page each (10 comments + 20 reactions)
            (10, True, True, 100, 100, 30, 50),      # Comments need 2 pages, reactions need 2 (10 + 20 min, 20 + 30 max)
            (10, True, True, 250, 150, 30, 90),      # Comments need 5 pages, reactions need 3 (10 + 20 min, 50 + 40 max)
            (5, True, False, 100, None, 5, 10),      # Comments only, 2 pages each
            (5, False, True, None, 200, 10, 25),     # Reactions only, 4 pages each (10 min, 5*(2+3) max)
            (10, False, False, None, None, 0, 0),    # Neither
            (0, True, True, 100, 100, 0, 0),         # Zero posts
        ]
        
        for post_count, comments, reactions, c_limit, r_limit, exp_min, exp_max in test_cases:
            result = calculate_post_enrichment_credits(
                post_count, comments, reactions, c_limit, r_limit
            )
            
            self.assertEqual(result["min_credits"], exp_min, 
                           f"Failed for case: posts={post_count}, comments={comments}, reactions={reactions}, c_limit={c_limit}, r_limit={r_limit}")
            self.assertEqual(result["max_credits"], exp_max,
                           f"Failed for case: posts={post_count}, comments={comments}, reactions={reactions}, c_limit={c_limit}, r_limit={r_limit}")

    async def test_enrichment_helper_breakdown(self):
        """Test enrichment helper breakdown functionality."""
        # Test breakdown (always included now)
        result = calculate_post_enrichment_credits(
            post_count=10,
            fetch_comments=True,
            fetch_reactions=True,
            comment_limit=100,  # 2 pages
            reaction_limit=150  # 3 pages
        )
        
        # Breakdown should always be present
        self.assertIn('breakdown', result)
        
        breakdown = result['breakdown']
        self.assertIn('comments', breakdown)
        self.assertIn('reactions', breakdown)
        
        # Verify breakdown adds up
        total_max = breakdown['comments']['max'] + breakdown['reactions']['max']
        total_min = breakdown['comments']['min'] + breakdown['reactions']['min']
        
        self.assertEqual(total_max, result['max_credits'])
        self.assertEqual(total_min, result['min_credits'])

    async def test_default_values_application(self):
        """Test that default values are applied correctly."""
        # Test with minimal config (should use defaults)
        minimal_job = ScrapingRequest(
            job_type=JobTypeEnum.ENTITY_POSTS,
            type=EntityTypeEnum.PERSON,
            entity_posts=YesNoEnum.YES,
            username="test-user"
            # No post_limit specified - should use default from credit calculator
        )
        
        request_dict = minimal_job.model_dump(mode="python", exclude_none=True)
        
        # Map entity_posts to post_scrap for credit calculator
        request_dict["post_scrap"] = request_dict.get("entity_posts", "no")
        
        result = await credit_estimation(request_dict)
        
        # The credit calculator always applies a default post_limit when post_scrap is "yes"
        # So we should always expect at least 1 credit for entity posts
        self.assertGreaterEqual(result['min_credits'], 1)
        self.assertGreaterEqual(result['max_credits'], 1)
        
        # Verify that posts_fetching breakdown shows at least 1 batch
        breakdown = result.get('breakdown', {})
        self.assertGreaterEqual(breakdown['posts_fetching'], 1)

    async def test_validation_with_url_parsing(self):
        """Test validation with URL parsing."""
        job_config = {
            "job_type": JobTypeEnum.PROFILE_INFO,
            "url": "https://www.linkedin.com/in/test-user-profile/",
            "profile_info": YesNoEnum.YES  # Need to set the job flag
        }
        
        # ScrapingRequest should extract username and type from URL
        validated_config = ScrapingRequest(**job_config)
        request_dict = validated_config.model_dump(mode="python", exclude_none=True)
        
        # Verify extraction worked
        self.assertEqual(request_dict.get("username"), "test-user-profile")
        self.assertEqual(request_dict.get("type"), EntityTypeEnum.PERSON.value)
        
        result = await credit_estimation(request_dict)
        self.assertEqual(result["min_credits"], 1)
        self.assertEqual(result["max_credits"], 1)

    async def test_validation_url_username_conflict(self):
        """Test validation error when both URL and username are provided."""
        job_config = {
            "job_type": JobTypeEnum.PROFILE_INFO,
            "url": "https://www.linkedin.com/in/test-user/",
            "username": "different-user",  # Conflict
            "type": EntityTypeEnum.PERSON,   # Conflict
            "profile_info": YesNoEnum.YES
        }
        
        with self.assertRaises(ValidationError) as context:
            ScrapingRequest(**job_config)
        
        # Check that validation error mentions the conflict
        error_messages = str(context.exception)
        self.assertIn("username", error_messages.lower())
        self.assertIn("url", error_messages.lower())


# Allow running the tests directly
if __name__ == "__main__":
    unittest.main() 