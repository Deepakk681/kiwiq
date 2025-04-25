import unittest
import asyncio
from typing import Dict, Any, List

# Import necessary components from the node and schema files
from services.workflow_service.registry.nodes.scraping.linkedin_scraping import (
    LinkedInScrapingNode,
    LinkedInScrapingConfig,
    LinkedInScrapingOutput,
    JobDefinition,
    InputSource,
)
from services.scraper_service.client.schemas.job_config_schema import (
    ScrapingRequest, # Used implicitly for validation checks
    JobTypeEnum,
    EntityTypeEnum,
    YesNoEnum
)
from services.scraper_service.settings import rapid_api_settings # For checking defaults


# --- Test Cases ---

class TestLinkedInScrapingNodeTestMode(unittest.IsolatedAsyncioTestCase):
    """Test suite for LinkedInScrapingNode in test_mode=True."""

    async def test_static_profile_info(self):
        """Tests a single job definition with purely static inputs for profile_info."""
        input_data = {} # No dynamic input needed
        node_config_dict = {
            "test_mode": True,
            "jobs": [
                {
                    "output_field_name": "static_user_profile",
                    "job_type": {"static_value": JobTypeEnum.PROFILE_INFO.value},
                    "type": {"static_value": EntityTypeEnum.PERSON.value},
                    "username": {"static_value": "static_test_user"},
                    "profile_info": {"static_value": YesNoEnum.YES.value},
                    "entity_posts": {"static_value": YesNoEnum.NO.value},
                }
            ]
        }
        node = LinkedInScrapingNode(node_id="test_scraping_node", config=LinkedInScrapingConfig(**node_config_dict))
        output = await node.process(input_data=input_data)

        # Assertions
        self.assertIsInstance(output, LinkedInScrapingOutput)
        self.assertIn("static_user_profile", output.scraping_results)
        self.assertIsInstance(output.scraping_results["static_user_profile"], dict)

        expected_config = {
            "job_type": JobTypeEnum.PROFILE_INFO.value,
            "type": EntityTypeEnum.PERSON.value,
            "username": "static_test_user",
            "profile_info": YesNoEnum.YES.value,
            "entity_posts": YesNoEnum.NO.value,
            "activity_comments": YesNoEnum.NO.value,
            "activity_reactions": YesNoEnum.NO.value,
            "search_post_by_keyword": YesNoEnum.NO.value,
            "search_post_by_hashtag": YesNoEnum.NO.value,
            "post_limit": None,
            'hashtag': None,
            'keyword': None,
            "post_comments": YesNoEnum.NO.value,
            "comment_limit": rapid_api_settings.DEFAULT_COMMENT_LIMIT,
            "post_reactions": YesNoEnum.NO.value,
            "reaction_limit": rapid_api_settings.DEFAULT_REACTION_LIMIT,
        }
        self.assertDictEqual(output.scraping_results["static_user_profile"], expected_config)

        summary = output.execution_summary["static_user_profile"]
        self.assertEqual(summary["jobs_triggered"], 1)
        self.assertEqual(summary["successful"], 1)
        self.assertEqual(summary["failed"], 0)
        self.assertEqual(len(summary["errors"]), 0)

    async def test_dynamic_company_posts(self):
        """Tests a single job definition with dynamic inputs for company posts."""
        input_data = {
            "target_company": "dynamic-test-company",
            "limits": {"posts": 5, "comments": 10},
            "fetch_options": {"get_comments": "yes"}
        }
        node_config_dict = {
            "test_mode": True,
            "jobs": [
                {
                    "output_field_name": "dynamic_company_feed",
                    "job_type": {"static_value": JobTypeEnum.ENTITY_POSTS.value},
                    "type": {"static_value": EntityTypeEnum.COMPANY.value},
                    "username": {"input_field_path": "target_company"},
                    "post_limit": {"input_field_path": "limits.posts"},
                    "post_comments": {"input_field_path": "fetch_options.get_comments"},
                    "comment_limit": {"input_field_path": "limits.comments"},
                    "entity_posts": {"static_value": YesNoEnum.YES.value},
                }
            ]
        }
        node = LinkedInScrapingNode(node_id="test_scraping_node", config=LinkedInScrapingConfig(**node_config_dict))
        output = await node.process(input_data=input_data)

        # Assertions
        self.assertIn("dynamic_company_feed", output.scraping_results)
        result_config = output.scraping_results["dynamic_company_feed"]
        self.assertIsInstance(result_config, dict)

        self.assertEqual(result_config["job_type"], JobTypeEnum.ENTITY_POSTS.value)
        self.assertEqual(result_config["type"], EntityTypeEnum.COMPANY.value)
        self.assertEqual(result_config["username"], "dynamic-test-company")
        self.assertEqual(result_config["post_limit"], 5)
        self.assertEqual(result_config["post_comments"], YesNoEnum.YES.value)
        self.assertEqual(result_config["comment_limit"], 10)
        self.assertEqual(result_config["entity_posts"], YesNoEnum.YES.value)
        self.assertEqual(result_config["post_reactions"], YesNoEnum.NO.value) # Default

        summary = output.execution_summary["dynamic_company_feed"]
        self.assertEqual(summary["jobs_triggered"], 1)
        self.assertEqual(summary["successful"], 1)
        self.assertEqual(summary["failed"], 0)

    async def test_expand_list_usernames(self):
        """Tests expanding a list of usernames for profile info jobs."""
        input_data = {
            "user_list": ["user1", "user2", "user3"],
            "common_settings": {
                "job": JobTypeEnum.PROFILE_INFO.value,
                "entity": EntityTypeEnum.PERSON.value
            }
        }
        node_config_dict = {
            "test_mode": True,
            "jobs": [
                {
                    "output_field_name": "expanded_profiles",
                    "job_type": {"input_field_path": "common_settings.job"},
                    "type": {"input_field_path": "common_settings.entity"},
                    "username": {"input_field_path": "user_list", "expand_list": True},
                    "profile_info": {"static_value": YesNoEnum.YES.value},
                }
            ]
        }
        node = LinkedInScrapingNode(node_id="test_scraping_node", config=LinkedInScrapingConfig(**node_config_dict))
        output = await node.process(input_data=input_data)

        # Assertions
        self.assertIn("expanded_profiles", output.scraping_results)
        results_list = output.scraping_results["expanded_profiles"]
        self.assertIsInstance(results_list, list)
        self.assertEqual(len(results_list), 3)

        self.assertEqual(results_list[0]["job_type"], JobTypeEnum.PROFILE_INFO.value)
        self.assertEqual(results_list[0]["type"], EntityTypeEnum.PERSON.value)
        self.assertEqual(results_list[0]["username"], "user1")
        self.assertEqual(results_list[0]["profile_info"], YesNoEnum.YES.value)
        self.assertEqual(results_list[2]["username"], "user3")

        summary = output.execution_summary["expanded_profiles"]
        self.assertEqual(summary["jobs_triggered"], 3)
        self.assertEqual(summary["successful"], 3)
        self.assertEqual(summary["failed"], 0)

    async def test_expand_list_keywords_search(self):
        """Tests expanding a list of keywords for search jobs."""
        input_data = {
            "search_terms": ["ai", "ml", "data science"],
            "search_limit": 15
        }
        node_config_dict = {
            "test_mode": True,
            "jobs": [
                {
                    "output_field_name": "keyword_searches",
                    "job_type": {"static_value": JobTypeEnum.SEARCH_POST_BY_KEYWORD.value},
                    "keyword": {"input_field_path": "search_terms", "expand_list": True},
                    "post_limit": {"input_field_path": "search_limit"},
                    "search_post_by_keyword": {"static_value": YesNoEnum.YES.value},
                }
            ]
        }
        node = LinkedInScrapingNode(node_id="test_scraping_node", config=LinkedInScrapingConfig(**node_config_dict))
        output = await node.process(input_data=input_data)

        # Assertions
        self.assertIn("keyword_searches", output.scraping_results)
        results_list = output.scraping_results["keyword_searches"]
        self.assertIsInstance(results_list, list)
        self.assertEqual(len(results_list), 3)

        self.assertEqual(results_list[0]["job_type"], JobTypeEnum.SEARCH_POST_BY_KEYWORD.value)
        self.assertEqual(results_list[0]["keyword"], "ai")
        self.assertEqual(results_list[0]["post_limit"], 15)
        self.assertEqual(results_list[0]["search_post_by_keyword"], YesNoEnum.YES.value)

        self.assertEqual(results_list[1]["keyword"], "ml")
        self.assertEqual(results_list[2]["keyword"], "data science")

        summary = output.execution_summary["keyword_searches"]
        self.assertEqual(summary["jobs_triggered"], 3)
        self.assertEqual(summary["successful"], 3)
        self.assertEqual(summary["failed"], 0)

    async def test_mixed_static_dynamic_activity(self):
        """Tests a job with mixed static and dynamic inputs for user activity."""
        input_data = {
            "user_id": "activity_user",
            "max_activity": 3
        }
        node_config_dict = {
            "test_mode": True,
            "jobs": [
                {
                    "output_field_name": "user_reactions",
                    "job_type": {"static_value": JobTypeEnum.ACTIVITY_REACTIONS.value},
                    "username": {"input_field_path": "user_id"},
                    "post_limit": {"input_field_path": "max_activity"},
                    "activity_reactions": {"static_value": YesNoEnum.YES.value},
                    "post_comments": {"static_value": YesNoEnum.YES.value},
                    "comment_limit": {"static_value": 5},
                }
            ]
        }
        node = LinkedInScrapingNode(node_id="test_scraping_node", config=LinkedInScrapingConfig(**node_config_dict))
        output = await node.process(input_data=input_data)

        # Assertions
        self.assertIn("user_reactions", output.scraping_results)
        result_config = output.scraping_results["user_reactions"]
        self.assertIsInstance(result_config, dict)

        self.assertEqual(result_config["job_type"], JobTypeEnum.ACTIVITY_REACTIONS.value)
        self.assertEqual(result_config["username"], "activity_user")
        self.assertEqual(result_config["post_limit"], 3)
        self.assertEqual(result_config["activity_reactions"], YesNoEnum.YES.value)
        self.assertEqual(result_config["post_comments"], YesNoEnum.YES.value)
        self.assertEqual(result_config["comment_limit"], 5)
        self.assertEqual(result_config["post_reactions"], YesNoEnum.NO.value)

        summary = output.execution_summary["user_reactions"]
        self.assertEqual(summary["jobs_triggered"], 1)
        self.assertEqual(summary["successful"], 1)
        self.assertEqual(summary["failed"], 0)

    async def test_multiple_job_definitions(self):
        """Tests a config with two separate job definitions."""
        input_data = {
            "target_user": "multi_user",
            "target_hashtag": "multi_tag"
        }
        node_config_dict = {
            "test_mode": True,
            "jobs": [
                {
                    "output_field_name": "multi_user_out",
                    "job_type": {"static_value": JobTypeEnum.PROFILE_INFO.value},
                    "type": {"static_value": EntityTypeEnum.PERSON.value},
                    "username": {"input_field_path": "target_user"},
                    "profile_info": {"static_value": YesNoEnum.YES.value},
                },
                {
                    "output_field_name": "multi_hashtag_out",
                    "job_type": {"static_value": JobTypeEnum.SEARCH_POST_BY_HASHTAG.value},
                    "hashtag": {"input_field_path": "target_hashtag"},
                    "post_limit": {"static_value": 10},
                    "search_post_by_hashtag": {"static_value": YesNoEnum.YES.value},
                }
            ]
        }
        node = LinkedInScrapingNode(node_id="test_scraping_node", config=LinkedInScrapingConfig(**node_config_dict))
        output = await node.process(input_data=input_data)

        # Assertions for Job 1
        self.assertIn("multi_user_out", output.scraping_results)
        user_config = output.scraping_results["multi_user_out"]
        self.assertEqual(user_config["job_type"], JobTypeEnum.PROFILE_INFO.value)
        self.assertEqual(user_config["username"], "multi_user")
        self.assertEqual(user_config["profile_info"], YesNoEnum.YES.value)
        summary1 = output.execution_summary["multi_user_out"]
        self.assertEqual(summary1["jobs_triggered"], 1)
        self.assertEqual(summary1["successful"], 1)
        self.assertEqual(summary1["failed"], 0)

        # Assertions for Job 2
        self.assertIn("multi_hashtag_out", output.scraping_results)
        hashtag_config = output.scraping_results["multi_hashtag_out"]
        self.assertEqual(hashtag_config["job_type"], JobTypeEnum.SEARCH_POST_BY_HASHTAG.value)
        self.assertEqual(hashtag_config["hashtag"], "multi_tag")
        self.assertEqual(hashtag_config["post_limit"], 10)
        self.assertEqual(hashtag_config["search_post_by_hashtag"], YesNoEnum.YES.value)
        summary2 = output.execution_summary["multi_hashtag_out"]
        self.assertEqual(summary2["jobs_triggered"], 1)
        self.assertEqual(summary2["successful"], 1)
        self.assertEqual(summary2["failed"], 0)

    async def test_validation_missing_required_field(self):
        """Tests validation failure when a required field (username) cannot be resolved."""
        input_data = {"some_other_data": "value"}
        node_config_dict = {
            "test_mode": True,
            "jobs": [
                {
                    "output_field_name": "invalid_profile",
                    "job_type": {"static_value": JobTypeEnum.PROFILE_INFO.value},
                    "type": {"static_value": EntityTypeEnum.PERSON.value},
                    "username": {"input_field_path": "user_id"},
                    "profile_info": {"static_value": YesNoEnum.YES.value},
                }
            ]
        }
        node = LinkedInScrapingNode(node_id="test_scraping_node", config=LinkedInScrapingConfig(**node_config_dict))
        output = await node.process(input_data=input_data)

        # Assertions
        self.assertIn("invalid_profile", output.scraping_results)
        result = output.scraping_results["invalid_profile"]
        self.assertIsInstance(result, dict)
        self.assertIn("error", result)
        self.assertIn("Validation failed", result["error"])
        self.assertIn("'username' is required", result["error"])

        summary = output.execution_summary["invalid_profile"]
        self.assertEqual(summary["jobs_triggered"], 0)
        self.assertEqual(summary["successful"], 0)
        self.assertEqual(summary["failed"], 1)
        self.assertEqual(len(summary["errors"]), 1)
        self.assertIn("Validation failed", summary["errors"][0])

    async def test_validation_invalid_job_type(self):
        """Tests validation failure when job_type resolves to an invalid value."""
        input_data = {"job": "invalid_job_type_value"}
        node_config_dict = {
            "test_mode": True,
            "jobs": [
                {
                    "output_field_name": "bad_job_type",
                    "job_type": {"input_field_path": "job"},
                    "type": {"static_value": EntityTypeEnum.PERSON.value},
                    "username": {"static_value": "test"},
                }
            ]
        }
        node = LinkedInScrapingNode(node_id="test_scraping_node", config=LinkedInScrapingConfig(**node_config_dict))
        output = await node.process(input_data=input_data)

        # Assertions
        self.assertIn("bad_job_type", output.scraping_results)
        result = output.scraping_results["bad_job_type"]
        self.assertIsInstance(result, dict)
        self.assertIn("error", result)
        self.assertIn("Invalid job_type", result["error"])

        summary = output.execution_summary["bad_job_type"]
        self.assertEqual(summary["jobs_triggered"], 0)
        self.assertEqual(summary["successful"], 0)
        self.assertEqual(summary["failed"], 1)
        self.assertEqual(len(summary["errors"]), 1)
        self.assertIn("Invalid job_type", summary["errors"][0])

    async def test_validation_invalid_input_path(self):
        """Tests behavior when a non-required input_field_path is invalid."""
        input_data = {"target_user": "valid_user"}
        node_config_dict = {
            "test_mode": True,
            "jobs": [
                {
                    "output_field_name": "missing_limit_profile",
                    "job_type": {"static_value": JobTypeEnum.ENTITY_POSTS.value},
                    "type": {"static_value": EntityTypeEnum.PERSON.value},
                    "username": {"input_field_path": "target_user"},
                    "entity_posts": {"static_value": YesNoEnum.YES.value},
                    "post_limit": {"input_field_path": "non_existent.path"},
                }
            ]
        }
        node = LinkedInScrapingNode(node_id="test_scraping_node", config=LinkedInScrapingConfig(**node_config_dict))
        output = await node.process(input_data=input_data)

        # Assertions
        self.assertIn("missing_limit_profile", output.scraping_results)
        result_config = output.scraping_results["missing_limit_profile"]
        self.assertIsInstance(result_config, dict)
        self.assertEqual(result_config["job_type"], JobTypeEnum.ENTITY_POSTS.value)
        self.assertEqual(result_config["username"], "valid_user")
        self.assertIsNone(result_config["post_limit"]) # Default used
        self.assertEqual(result_config["entity_posts"], YesNoEnum.YES.value)

        summary = output.execution_summary["missing_limit_profile"]
        self.assertEqual(summary["jobs_triggered"], 1)
        self.assertEqual(summary["successful"], 1)
        self.assertEqual(summary["failed"], 0)

    async def test_expand_list_non_list_input(self):
        """Tests expand_list=True when the input path resolves to a non-list."""
        input_data = {"keywords": "single_keyword_string"}
        node_config_dict = {
            "test_mode": True,
            "jobs": [
                {
                    "output_field_name": "expand_non_list",
                    "job_type": {"static_value": JobTypeEnum.SEARCH_POST_BY_KEYWORD.value},
                    "keyword": {"input_field_path": "keywords", "expand_list": True},
                    "search_post_by_keyword": {"static_value": YesNoEnum.YES.value},
                }
            ]
        }
        node = LinkedInScrapingNode(node_id="test_scraping_node", config=LinkedInScrapingConfig(**node_config_dict))
        output = await node.process(input_data=input_data)

        # Assertions
        self.assertIn("expand_non_list", output.scraping_results)
        result_config = output.scraping_results["expand_non_list"]
        result_config = result_config[0]
        self.assertIsInstance(result_config, dict) # Treated as single item
        self.assertEqual(result_config["job_type"], JobTypeEnum.SEARCH_POST_BY_KEYWORD.value)
        self.assertEqual(result_config["keyword"], "single_keyword_string")

        summary = output.execution_summary["expand_non_list"]
        self.assertEqual(summary["jobs_triggered"], 1)
        self.assertEqual(summary["successful"], 1)
        self.assertEqual(summary["failed"], 0)

    async def test_expand_list_empty_list(self):
        """Tests expand_list=True when the input path resolves to an empty list."""
        input_data = {"hashtags": []}
        node_config_dict = {
            "test_mode": True,
            "jobs": [
                {
                    "output_field_name": "expand_empty",
                    "job_type": {"static_value": JobTypeEnum.SEARCH_POST_BY_HASHTAG.value},
                    "hashtag": {"input_field_path": "hashtags", "expand_list": True},
                    "search_post_by_hashtag": {"static_value": YesNoEnum.YES.value},
                }
            ]
        }
        node = LinkedInScrapingNode(node_id="test_scraping_node", config=LinkedInScrapingConfig(**node_config_dict))
        output = await node.process(input_data=input_data)

        # Assertions
        self.assertIn("expand_empty", output.scraping_results)
        results_list = output.scraping_results["expand_empty"]
        self.assertIsInstance(results_list, list)
        self.assertEqual(len(results_list), 0)

        summary = output.execution_summary["expand_empty"]
        self.assertEqual(summary["jobs_triggered"], 0)
        self.assertEqual(summary["successful"], 0)
        self.assertEqual(summary["failed"], 0)

    async def test_expand_list_path_not_found(self):
        """Tests expand_list=True when the input_field_path is not found."""
        input_data = {}
        node_config_dict = {
            "test_mode": True,
            "jobs": [
                {
                    "output_field_name": "expand_missing_path",
                    "job_type": {"static_value": JobTypeEnum.SEARCH_POST_BY_KEYWORD.value},
                    "keyword": {"input_field_path": "missing.keywords", "expand_list": True},
                    "search_post_by_keyword": {"static_value": YesNoEnum.YES.value},
                }
            ]
        }
        node = LinkedInScrapingNode(node_id="test_scraping_node", config=LinkedInScrapingConfig(**node_config_dict))
        output = await node.process(input_data=input_data)

        # Assertions
        self.assertIn("expand_missing_path", output.scraping_results)
        result = output.scraping_results["expand_missing_path"]
        result = result[0]
        self.assertIsInstance(result, dict)
        self.assertIn("error", result)
        self.assertIn("Validation failed", result["error"])
        self.assertIn("'keyword' is required", result["error"])

        summary = output.execution_summary["expand_missing_path"]
        self.assertEqual(summary["jobs_triggered"], 0)
        self.assertEqual(summary["successful"], 0)
        self.assertEqual(summary["failed"], 1)

    async def test_align_job_flags(self):
        """Tests that the node correctly aligns the YesNo flag based on resolved job_type."""
        input_data = {"target_user": "flag_test_user"}
        node_config_dict = {
            "test_mode": True,
            "jobs": [
                {
                    "output_field_name": "flag_alignment",
                    "job_type": {"static_value": JobTypeEnum.ACTIVITY_COMMENTS.value},
                    "username": {"input_field_path": "target_user"},
                    "profile_info": {"static_value": YesNoEnum.YES.value},
                    "activity_comments": {"static_value": YesNoEnum.NO.value},
                }
            ]
        }
        node = LinkedInScrapingNode(node_id="test_scraping_node", config=LinkedInScrapingConfig(**node_config_dict))
        output = await node.process(input_data=input_data)

        # Assertions
        self.assertIn("flag_alignment", output.scraping_results)
        result_config = output.scraping_results["flag_alignment"]
        self.assertIsInstance(result_config, dict)

        self.assertEqual(result_config["job_type"], JobTypeEnum.ACTIVITY_COMMENTS.value)
        self.assertEqual(result_config["username"], "flag_test_user")
        self.assertEqual(result_config["activity_comments"], YesNoEnum.YES.value) # Corrected
        self.assertEqual(result_config["profile_info"], YesNoEnum.NO.value) # Corrected

        summary = output.execution_summary["flag_alignment"]
        self.assertEqual(summary["jobs_triggered"], 1)
        self.assertEqual(summary["successful"], 1)
        self.assertEqual(summary["failed"], 0)

# Allow running the tests directly using python -m unittest path/to/test_file.py
if __name__ == "__main__":
    unittest.main()
