import unittest
import asyncio
from typing import Dict, Any, List
import uuid
from unittest.mock import MagicMock, AsyncMock

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
from services.scraper_service.credit_calculator import credit_estimation

# Import for runtime context setup
from workflow_service.config.constants import APPLICATION_CONTEXT_KEY, EXTERNAL_CONTEXT_MANAGER_KEY
from kiwi_app.auth.models import User, Organization
from kiwi_app.workflow_app.schemas import WorkflowRunJobCreate
from kiwi_app.settings import settings as kiwi_settings

from sqlmodel.ext.asyncio.session import AsyncSession
from workflow_service.config.constants import (
    APPLICATION_CONTEXT_KEY,
    EXTERNAL_CONTEXT_MANAGER_KEY,
    DB_SESSION_KEY,
)
from db.session import get_async_session
# db_session = config.get(DB_SESSION_KEY)

# --- Test Cases ---

class TestLinkedInScrapingNodeTestMode(unittest.IsolatedAsyncioTestCase):
    """Test suite for LinkedInScrapingNode in test_mode=True."""

    def setUp(self):
        """Set up test environment."""
        # Mock user
        self.mock_user = MagicMock(spec=User)
        self.mock_user.id = uuid.uuid4()
        self.mock_user.email = "test@example.com"
        
        # Mock organization
        self.mock_org = MagicMock(spec=Organization)
        self.mock_org.id = uuid.uuid4()
        self.mock_org.name = "Test Organization"
        
        # Mock workflow run job
        self.mock_run_job = MagicMock(spec=WorkflowRunJobCreate)
        self.mock_run_job.run_id = str(uuid.uuid4())
        self.mock_run_job.owner_org_id = self.mock_org.id
        
        # Mock external context manager
        self.mock_ext_context = MagicMock()
        self.mock_ext_context.db_registry = MagicMock()
        self.mock_ext_context.customer_data_service = MagicMock()
        self.mock_ext_context.billing_service = None  # Not needed in test mode
        self.db_session = MagicMock(spec=AsyncSession)

    def _create_runtime_config(self) -> Dict[str, Any]:
        """Create runtime config with proper app context and external context."""
        return {
            "configurable": {
                APPLICATION_CONTEXT_KEY: {
                    "user": self.mock_user,
                    "workflow_run_job": self.mock_run_job,
                },
                EXTERNAL_CONTEXT_MANAGER_KEY: self.mock_ext_context,
                DB_SESSION_KEY: self.db_session,
            }
        }

    async def _calculate_expected_credits(self, scraping_request: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate expected credits for a scraping request using the credit calculator."""
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
        runtime_config = self._create_runtime_config()
        output = await node.process(input_data=input_data, config=runtime_config)

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
            "post_details": YesNoEnum.NO.value,
            "post_limit": None,
            'hashtag': None,
            'keyword': None,
            'url': None,
            'post_url_or_urn': None,
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

        # Check credit summary
        credit_summary = output.execution_summary.get("_credit_summary")
        self.assertIsNotNone(credit_summary)
        self.assertTrue(credit_summary["test_mode"])
        self.assertEqual(credit_summary["total_credits_consumed"], 0)  # No actual consumption in test mode
        self.assertEqual(credit_summary["total_dollar_cost"], 0.0)
        
        # Calculate expected credits for profile_info job
        expected_credits = await self._calculate_expected_credits(expected_config)
        self.assertEqual(credit_summary["total_potential_credits"], expected_credits["max_credits"])
        self.assertEqual(credit_summary["total_potential_dollar_cost"], round(expected_credits["dollar_cost"], 4))

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
        runtime_config = self._create_runtime_config()
        output = await node.process(input_data=input_data, config=runtime_config)

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

        # Check credit summary
        credit_summary = output.execution_summary.get("_credit_summary")
        self.assertIsNotNone(credit_summary)
        
        # Calculate expected credits
        expected_credits = await self._calculate_expected_credits({
            "type": "company",
            "entity_posts": "yes",
            "post_limit": 5,
            "post_comments": "yes",
            "comment_limit": 10,
            "post_reactions": "no",
            "reaction_limit": rapid_api_settings.DEFAULT_REACTION_LIMIT
        })
        
        self.assertEqual(credit_summary["total_potential_credits"], expected_credits["max_credits"])
        self.assertEqual(credit_summary["total_potential_dollar_cost"], round(expected_credits["dollar_cost"], 4))

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
        runtime_config = self._create_runtime_config()
        output = await node.process(input_data=input_data, config=runtime_config)

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

        # Check credit summary for expanded jobs
        credit_summary = output.execution_summary.get("_credit_summary")
        self.assertIsNotNone(credit_summary)
        # 3 profile info jobs = 3 credits
        self.assertEqual(credit_summary["total_potential_credits"], 3)
        self.assertEqual(credit_summary["total_potential_dollar_cost"], 0.03)

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
        runtime_config = self._create_runtime_config()
        output = await node.process(input_data=input_data, config=runtime_config)

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
        runtime_config = self._create_runtime_config()
        output = await node.process(input_data=input_data, config=runtime_config)

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
        runtime_config = self._create_runtime_config()
        output = await node.process(input_data=input_data, config=runtime_config)

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
        runtime_config = self._create_runtime_config()
        output = await node.process(input_data=input_data, config=runtime_config)

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

        # Check credit summary shows no credits for failed validation
        credit_summary = output.execution_summary.get("_credit_summary")
        self.assertIsNotNone(credit_summary)
        self.assertEqual(credit_summary["total_potential_credits"], 0)
        self.assertEqual(credit_summary["total_credits_consumed"], 0)

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
        runtime_config = self._create_runtime_config()
        output = await node.process(input_data=input_data, config=runtime_config)

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
        runtime_config = self._create_runtime_config()
        output = await node.process(input_data=input_data, config=runtime_config)

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
        runtime_config = self._create_runtime_config()
        output = await node.process(input_data=input_data, config=runtime_config)

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
        runtime_config = self._create_runtime_config()
        output = await node.process(input_data=input_data, config=runtime_config)

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
        runtime_config = self._create_runtime_config()
        output = await node.process(input_data=input_data, config=runtime_config)

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
        runtime_config = self._create_runtime_config()
        output = await node.process(input_data=input_data, config=runtime_config)

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

    async def test_static_url_profile_info(self):
        """Tests a single job definition using a static URL input for profile_info."""
        input_data = {} # No dynamic input needed
        test_url = "https://www.linkedin.com/in/static-url-user/"
        node_config_dict = {
            "test_mode": True,
            "jobs": [
                {
                    "output_field_name": "static_url_profile",
                    "job_type": {"static_value": JobTypeEnum.PROFILE_INFO.value},
                    "url": {"static_value": test_url},
                    # profile_info flag will be set automatically based on job_type
                }
            ]
        }
        node = LinkedInScrapingNode(node_id="test_scraping_node", config=LinkedInScrapingConfig(**node_config_dict))
        runtime_config = self._create_runtime_config()
        output = await node.process(input_data=input_data, config=runtime_config)

        # Assertions
        self.assertIsInstance(output, LinkedInScrapingOutput)
        self.assertIn("static_url_profile", output.scraping_results)
        result_config = output.scraping_results["static_url_profile"]
        self.assertIsInstance(result_config, dict)

        # The ScrapingRequest validator extracts username and type from the URL
        expected_config = {
            "job_type": JobTypeEnum.PROFILE_INFO.value,
            "url": test_url, # URL is passed through
            "username": "static-url-user", # Extracted by validator
            "type": EntityTypeEnum.PERSON.value, # Extracted by validator
            "profile_info": YesNoEnum.YES.value, # Aligned by node
            "entity_posts": YesNoEnum.NO.value,
            "activity_comments": YesNoEnum.NO.value,
            "activity_reactions": YesNoEnum.NO.value,
            "search_post_by_keyword": YesNoEnum.NO.value,
            "search_post_by_hashtag": YesNoEnum.NO.value,
            "post_details": YesNoEnum.NO.value,
            "post_limit": None,
            'hashtag': None,
            'keyword': None,
            "post_comments": YesNoEnum.NO.value,
            "comment_limit": rapid_api_settings.DEFAULT_COMMENT_LIMIT,
            "post_reactions": YesNoEnum.NO.value,
            "reaction_limit": rapid_api_settings.DEFAULT_REACTION_LIMIT,
        }
        # Check specific extracted fields first for clarity
        self.assertEqual(result_config.get("url"), test_url)
        self.assertEqual(result_config.get("username"), "static-url-user")
        self.assertEqual(result_config.get("type"), EntityTypeEnum.PERSON.value)
        self.assertEqual(result_config.get("profile_info"), YesNoEnum.YES.value)
        # Check the whole dictionary
        self.assertDictEqual(result_config, expected_config)

        summary = output.execution_summary["static_url_profile"]
        self.assertEqual(summary["jobs_triggered"], 1)
        self.assertEqual(summary["successful"], 1)
        self.assertEqual(summary["failed"], 0)
        self.assertEqual(len(summary["errors"]), 0)

    async def test_dynamic_url_company_posts(self):
        """Tests a job definition using a dynamic URL input for company posts."""
        test_url = "https://www.linkedin.com/company/dynamic-url-comp/"
        input_data = {
            "target_profile_url": test_url,
            "fetch_limit": 25
        }
        node_config_dict = {
            "test_mode": True,
            "jobs": [
                {
                    "output_field_name": "dynamic_url_posts",
                    "job_type": {"static_value": JobTypeEnum.ENTITY_POSTS.value},
                    "url": {"input_field_path": "target_profile_url"},
                    "post_limit": {"input_field_path": "fetch_limit"},
                    # entity_posts flag will be set automatically based on job_type
                }
            ]
        }
        node = LinkedInScrapingNode(node_id="test_scraping_node", config=LinkedInScrapingConfig(**node_config_dict))
        runtime_config = self._create_runtime_config()
        output = await node.process(input_data=input_data, config=runtime_config)

        # Assertions
        self.assertIn("dynamic_url_posts", output.scraping_results)
        result_config = output.scraping_results["dynamic_url_posts"]
        self.assertIsInstance(result_config, dict)

        # Check specific extracted fields
        self.assertEqual(result_config.get("url"), test_url)
        self.assertEqual(result_config.get("username"), "dynamic-url-comp") # Extracted
        self.assertEqual(result_config.get("type"), EntityTypeEnum.COMPANY.value) # Extracted
        self.assertEqual(result_config.get("entity_posts"), YesNoEnum.YES.value) # Aligned
        self.assertEqual(result_config.get("post_limit"), 25)

        summary = output.execution_summary["dynamic_url_posts"]
        self.assertEqual(summary["jobs_triggered"], 1)
        self.assertEqual(summary["successful"], 1)
        self.assertEqual(summary["failed"], 0)

    async def test_validation_url_and_username_conflict(self):
        """Tests validation failure when both URL and username are provided."""
        input_data = {"profile_url": "https://www.linkedin.com/in/conflict-user/"}
        node_config_dict = {
            "test_mode": True,
            "jobs": [
                {
                    "output_field_name": "url_username_conflict",
                    "job_type": {"static_value": JobTypeEnum.PROFILE_INFO.value},
                    "url": {"input_field_path": "profile_url"},
                    "username": {"static_value": "explicit_username"}, # Conflict
                    "type": {"static_value": EntityTypeEnum.PERSON.value}, # Conflict
                    # profile_info flag aligned by node
                }
            ]
        }
        node = LinkedInScrapingNode(node_id="test_scraping_node", config=LinkedInScrapingConfig(**node_config_dict))
        runtime_config = self._create_runtime_config()
        output = await node.process(input_data=input_data, config=runtime_config)

        # Assertions: Expecting validation error from ScrapingRequest
        self.assertIn("url_username_conflict", output.scraping_results)
        result = output.scraping_results["url_username_conflict"]
        self.assertIsInstance(result, dict)
        self.assertIn("error", result)
        # Error comes from ScrapingRequest.model_validate called within the node
        self.assertIn("Validation failed", result["error"])
        self.assertIn("'username' and 'type' cannot be provided if 'url' is provided", result["error"])

        summary = output.execution_summary["url_username_conflict"]
        self.assertEqual(summary["jobs_triggered"], 0) # Validation fails before trigger count increments ideally
        self.assertEqual(summary["successful"], 0)
        self.assertEqual(summary["failed"], 1)
        self.assertEqual(len(summary["errors"]), 1)
        self.assertIn("Validation failed", summary["errors"][0])

    # --- POST_DETAILS JOB TESTS ---

    async def test_static_post_details_basic(self):
        """Tests a single job definition with static post_url_or_urn for basic post details."""
        input_data = {}  # No dynamic input needed
        node_config_dict = {
            "test_mode": True,
            "jobs": [
                {
                    "output_field_name": "static_post_details",
                    "job_type": {"static_value": JobTypeEnum.POST_DETAILS.value},
                    "post_url_or_urn": {"static_value": "7335304292926451712"},
                    "post_details": {"static_value": YesNoEnum.YES.value},
                }
            ]
        }
        node = LinkedInScrapingNode(node_id="test_scraping_node", config=LinkedInScrapingConfig(**node_config_dict))
        runtime_config = self._create_runtime_config()
        output = await node.process(input_data=input_data, config=runtime_config)

        # Assertions
        self.assertIsInstance(output, LinkedInScrapingOutput)
        self.assertIn("static_post_details", output.scraping_results)
        self.assertIsInstance(output.scraping_results["static_post_details"], dict)

        expected_config = {
            "job_type": JobTypeEnum.POST_DETAILS.value,
            "type": EntityTypeEnum.POST.value,  # Automatically set by validator
            "post_url_or_urn": "7335304292926451712",
            "post_details": YesNoEnum.YES.value,
            "profile_info": YesNoEnum.NO.value,
            "entity_posts": YesNoEnum.NO.value,
            "activity_comments": YesNoEnum.NO.value,
            "activity_reactions": YesNoEnum.NO.value,
            "search_post_by_keyword": YesNoEnum.NO.value,
            "search_post_by_hashtag": YesNoEnum.NO.value,
            "post_limit": None,
            'hashtag': None,
            'keyword': None,
            'url': None,
            'username': None,
            "post_comments": YesNoEnum.NO.value,
            "comment_limit": rapid_api_settings.DEFAULT_COMMENT_LIMIT,
            "post_reactions": YesNoEnum.NO.value,
            "reaction_limit": rapid_api_settings.DEFAULT_REACTION_LIMIT,
        }
        self.assertDictEqual(output.scraping_results["static_post_details"], expected_config)

        summary = output.execution_summary["static_post_details"]
        self.assertEqual(summary["jobs_triggered"], 1)
        self.assertEqual(summary["successful"], 1)
        self.assertEqual(summary["failed"], 0)
        self.assertEqual(len(summary["errors"]), 0)

    async def test_static_post_details_with_url(self):
        """Tests post details with a full LinkedIn post URL."""
        input_data = {}
        node_config_dict = {
            "test_mode": True,
            "jobs": [
                {
                    "output_field_name": "post_details_url",
                    "job_type": {"static_value": JobTypeEnum.POST_DETAILS.value},
                    "post_url_or_urn": {"static_value": "https://www.linkedin.com/posts/username_post-activity-7335304292926451712-abcd"},
                    "post_details": {"static_value": YesNoEnum.YES.value},
                }
            ]
        }
        node = LinkedInScrapingNode(node_id="test_scraping_node", config=LinkedInScrapingConfig(**node_config_dict))
        runtime_config = self._create_runtime_config()
        output = await node.process(input_data=input_data, config=runtime_config)

        # Assertions
        self.assertIn("post_details_url", output.scraping_results)
        result_config = output.scraping_results["post_details_url"]
        self.assertIsInstance(result_config, dict)

        self.assertEqual(result_config["job_type"], JobTypeEnum.POST_DETAILS.value)
        self.assertEqual(result_config["type"], EntityTypeEnum.POST.value)
        self.assertEqual(result_config["post_url_or_urn"], "https://www.linkedin.com/posts/username_post-activity-7335304292926451712-abcd")
        self.assertEqual(result_config["post_details"], YesNoEnum.YES.value)

        summary = output.execution_summary["post_details_url"]
        self.assertEqual(summary["jobs_triggered"], 1)
        self.assertEqual(summary["successful"], 1)
        self.assertEqual(summary["failed"], 0)

    async def test_dynamic_post_details_with_enrichment(self):
        """Tests post details with dynamic inputs and comment/reaction enrichment."""
        input_data = {
            "target_post_urn": "7335304292926451712",
            "enrichment_settings": {
                "fetch_comments": "yes",
                "fetch_reactions": "yes",
                "comment_limit": 25,
                "reaction_limit": 150
            }
        }
        node_config_dict = {
            "test_mode": True,
            "jobs": [
                {
                    "output_field_name": "enriched_post_details",
                    "job_type": {"static_value": JobTypeEnum.POST_DETAILS.value},
                    "post_url_or_urn": {"input_field_path": "target_post_urn"},
                    "post_details": {"static_value": YesNoEnum.YES.value},
                    "post_comments": {"input_field_path": "enrichment_settings.fetch_comments"},
                    "comment_limit": {"input_field_path": "enrichment_settings.comment_limit"},
                    "post_reactions": {"input_field_path": "enrichment_settings.fetch_reactions"},
                    "reaction_limit": {"input_field_path": "enrichment_settings.reaction_limit"},
                }
            ]
        }
        node = LinkedInScrapingNode(node_id="test_scraping_node", config=LinkedInScrapingConfig(**node_config_dict))
        runtime_config = self._create_runtime_config()
        output = await node.process(input_data=input_data, config=runtime_config)

        # Assertions
        self.assertIn("enriched_post_details", output.scraping_results)
        result_config = output.scraping_results["enriched_post_details"]
        self.assertIsInstance(result_config, dict)

        self.assertEqual(result_config["job_type"], JobTypeEnum.POST_DETAILS.value)
        self.assertEqual(result_config["type"], EntityTypeEnum.POST.value)
        self.assertEqual(result_config["post_url_or_urn"], "7335304292926451712")
        self.assertEqual(result_config["post_details"], YesNoEnum.YES.value)
        self.assertEqual(result_config["post_comments"], YesNoEnum.YES.value)
        self.assertEqual(result_config["comment_limit"], 25)
        self.assertEqual(result_config["post_reactions"], YesNoEnum.YES.value)
        self.assertEqual(result_config["reaction_limit"], 150)

        summary = output.execution_summary["enriched_post_details"]
        self.assertEqual(summary["jobs_triggered"], 1)
        self.assertEqual(summary["successful"], 1)
        self.assertEqual(summary["failed"], 0)

    async def test_expand_list_post_urns(self):
        """Tests expanding a list of post URNs for multiple post details jobs."""
        input_data = {
            "post_urns": ["7335304292926451712", "7334567890123456789", "7333456789012345678"],
            "common_enrichment": {
                "get_comments": "yes",
                "comment_count": 10
            }
        }
        node_config_dict = {
            "test_mode": True,
            "jobs": [
                {
                    "output_field_name": "expanded_post_details",
                    "job_type": {"static_value": JobTypeEnum.POST_DETAILS.value},
                    "post_url_or_urn": {"input_field_path": "post_urns", "expand_list": True},
                    "post_details": {"static_value": YesNoEnum.YES.value},
                    "post_comments": {"input_field_path": "common_enrichment.get_comments"},
                    "comment_limit": {"input_field_path": "common_enrichment.comment_count"},
                }
            ]
        }
        node = LinkedInScrapingNode(node_id="test_scraping_node", config=LinkedInScrapingConfig(**node_config_dict))
        runtime_config = self._create_runtime_config()
        output = await node.process(input_data=input_data, config=runtime_config)

        # Assertions
        self.assertIn("expanded_post_details", output.scraping_results)
        results_list = output.scraping_results["expanded_post_details"]
        self.assertIsInstance(results_list, list)
        self.assertEqual(len(results_list), 3)

        # Check first post details
        self.assertEqual(results_list[0]["job_type"], JobTypeEnum.POST_DETAILS.value)
        self.assertEqual(results_list[0]["type"], EntityTypeEnum.POST.value)
        self.assertEqual(results_list[0]["post_url_or_urn"], "7335304292926451712")
        self.assertEqual(results_list[0]["post_details"], YesNoEnum.YES.value)
        self.assertEqual(results_list[0]["post_comments"], YesNoEnum.YES.value)
        self.assertEqual(results_list[0]["comment_limit"], 10)

        # Check other posts
        self.assertEqual(results_list[1]["post_url_or_urn"], "7334567890123456789")
        self.assertEqual(results_list[2]["post_url_or_urn"], "7333456789012345678")

        summary = output.execution_summary["expanded_post_details"]
        self.assertEqual(summary["jobs_triggered"], 3)
        self.assertEqual(summary["successful"], 3)
        self.assertEqual(summary["failed"], 0)

    async def test_mixed_post_urls_and_urns(self):
        """Tests expanding a list with mixed post URLs and URNs."""
        input_data = {
            "mixed_posts": [
                "7335304292926451712",  # URN
                "https://www.linkedin.com/posts/user_activity-7334567890123456789-xyz",  # URL
                "7333456789012345678"  # URN
            ]
        }
        node_config_dict = {
            "test_mode": True,
            "jobs": [
                {
                    "output_field_name": "mixed_post_formats",
                    "job_type": {"static_value": JobTypeEnum.POST_DETAILS.value},
                    "post_url_or_urn": {"input_field_path": "mixed_posts", "expand_list": True},
                    "post_details": {"static_value": YesNoEnum.YES.value},
                    "post_reactions": {"static_value": YesNoEnum.YES.value},
                    "reaction_limit": {"static_value": 50},
                }
            ]
        }
        node = LinkedInScrapingNode(node_id="test_scraping_node", config=LinkedInScrapingConfig(**node_config_dict))
        runtime_config = self._create_runtime_config()
        output = await node.process(input_data=input_data, config=runtime_config)

        # Assertions
        self.assertIn("mixed_post_formats", output.scraping_results)
        results_list = output.scraping_results["mixed_post_formats"]
        self.assertIsInstance(results_list, list)
        self.assertEqual(len(results_list), 3)

        # All should be valid POST_DETAILS jobs
        for i, result in enumerate(results_list):
            self.assertEqual(result["job_type"], JobTypeEnum.POST_DETAILS.value)
            self.assertEqual(result["type"], EntityTypeEnum.POST.value)
            self.assertEqual(result["post_details"], YesNoEnum.YES.value)
            self.assertEqual(result["post_reactions"], YesNoEnum.YES.value)
            self.assertEqual(result["reaction_limit"], 50)

        # Check specific post identifiers
        self.assertEqual(results_list[0]["post_url_or_urn"], "7335304292926451712")
        self.assertEqual(results_list[1]["post_url_or_urn"], "https://www.linkedin.com/posts/user_activity-7334567890123456789-xyz")
        self.assertEqual(results_list[2]["post_url_or_urn"], "7333456789012345678")

        summary = output.execution_summary["mixed_post_formats"]
        self.assertEqual(summary["jobs_triggered"], 3)
        self.assertEqual(summary["successful"], 3)
        self.assertEqual(summary["failed"], 0)

    async def test_post_details_validation_missing_url(self):
        """Tests validation failure when post_url_or_urn is missing for POST_DETAILS."""
        input_data = {"some_other_data": "value"}
        node_config_dict = {
            "test_mode": True,
            "jobs": [
                {
                    "output_field_name": "invalid_post_details",
                    "job_type": {"static_value": JobTypeEnum.POST_DETAILS.value},
                    "post_url_or_urn": {"input_field_path": "missing_post_url"},
                    "post_details": {"static_value": YesNoEnum.YES.value},
                }
            ]
        }
        node = LinkedInScrapingNode(node_id="test_scraping_node", config=LinkedInScrapingConfig(**node_config_dict))
        runtime_config = self._create_runtime_config()
        output = await node.process(input_data=input_data, config=runtime_config)

        # Assertions
        self.assertIn("invalid_post_details", output.scraping_results)
        result = output.scraping_results["invalid_post_details"]
        self.assertIsInstance(result, dict)
        self.assertIn("error", result)
        self.assertIn("Validation failed", result["error"])
        self.assertIn("'post_url_or_urn' is required", result["error"])

        summary = output.execution_summary["invalid_post_details"]
        self.assertEqual(summary["jobs_triggered"], 0)
        self.assertEqual(summary["successful"], 0)
        self.assertEqual(summary["failed"], 1)
        self.assertEqual(len(summary["errors"]), 1)
        self.assertIn("Validation failed", summary["errors"][0])

    async def test_post_details_empty_expansion_list(self):
        """Tests POST_DETAILS with empty expansion list."""
        input_data = {"empty_posts": []}
        node_config_dict = {
            "test_mode": True,
            "jobs": [
                {
                    "output_field_name": "empty_post_expansion",
                    "job_type": {"static_value": JobTypeEnum.POST_DETAILS.value},
                    "post_url_or_urn": {"input_field_path": "empty_posts", "expand_list": True},
                    "post_details": {"static_value": YesNoEnum.YES.value},
                }
            ]
        }
        node = LinkedInScrapingNode(node_id="test_scraping_node", config=LinkedInScrapingConfig(**node_config_dict))
        runtime_config = self._create_runtime_config()
        output = await node.process(input_data=input_data, config=runtime_config)

        # Assertions
        self.assertIn("empty_post_expansion", output.scraping_results)
        results_list = output.scraping_results["empty_post_expansion"]
        self.assertIsInstance(results_list, list)
        self.assertEqual(len(results_list), 0)

        summary = output.execution_summary["empty_post_expansion"]
        self.assertEqual(summary["jobs_triggered"], 0)
        self.assertEqual(summary["successful"], 0)
        self.assertEqual(summary["failed"], 0)

    async def test_static_url_profile_info(self):
        """Tests a single job definition using a static URL input for profile_info."""
        input_data = {} # No dynamic input needed
        test_url = "https://www.linkedin.com/in/static-url-user/"
        node_config_dict = {
            "test_mode": True,
            "jobs": [
                {
                    "output_field_name": "static_url_profile",
                    "job_type": {"static_value": JobTypeEnum.PROFILE_INFO.value},
                    "url": {"static_value": test_url},
                    # profile_info flag will be set automatically based on job_type
                }
            ]
        }
        node = LinkedInScrapingNode(node_id="test_scraping_node", config=LinkedInScrapingConfig(**node_config_dict))
        runtime_config = self._create_runtime_config()
        output = await node.process(input_data=input_data, config=runtime_config)

        # Assertions
        self.assertIsInstance(output, LinkedInScrapingOutput)
        self.assertIn("static_url_profile", output.scraping_results)
        result_config = output.scraping_results["static_url_profile"]
        self.assertIsInstance(result_config, dict)

        # The ScrapingRequest validator extracts username and type from the URL
        expected_config = {
            "job_type": JobTypeEnum.PROFILE_INFO.value,
            "url": test_url, # URL is passed through
            "username": "static-url-user", # Extracted by validator
            "type": EntityTypeEnum.PERSON.value, # Extracted by validator
            "profile_info": YesNoEnum.YES.value, # Aligned by node
            "entity_posts": YesNoEnum.NO.value,
            "activity_comments": YesNoEnum.NO.value,
            "activity_reactions": YesNoEnum.NO.value,
            "search_post_by_keyword": YesNoEnum.NO.value,
            "search_post_by_hashtag": YesNoEnum.NO.value,
            "post_details": YesNoEnum.NO.value,
            "post_url_or_urn": None,
            "post_limit": None,
            'hashtag': None,
            'keyword': None,
            "post_comments": YesNoEnum.NO.value,
            "comment_limit": rapid_api_settings.DEFAULT_COMMENT_LIMIT,
            "post_reactions": YesNoEnum.NO.value,
            "reaction_limit": rapid_api_settings.DEFAULT_REACTION_LIMIT,
        }
        # Check specific extracted fields first for clarity
        self.assertEqual(result_config.get("url"), test_url)
        self.assertEqual(result_config.get("username"), "static-url-user")
        self.assertEqual(result_config.get("type"), EntityTypeEnum.PERSON.value)
        self.assertEqual(result_config.get("profile_info"), YesNoEnum.YES.value)
        # Check the whole dictionary
        self.assertDictEqual(result_config, expected_config)

        summary = output.execution_summary["static_url_profile"]
        self.assertEqual(summary["jobs_triggered"], 1)
        self.assertEqual(summary["successful"], 1)
        self.assertEqual(summary["failed"], 0)
        self.assertEqual(len(summary["errors"]), 0)

    async def test_dynamic_url_company_posts(self):
        """Tests a job definition using a dynamic URL input for company posts."""
        test_url = "https://www.linkedin.com/company/dynamic-url-comp/"
        input_data = {
            "target_profile_url": test_url,
            "fetch_limit": 25
        }
        node_config_dict = {
            "test_mode": True,
            "jobs": [
                {
                    "output_field_name": "dynamic_url_posts",
                    "job_type": {"static_value": JobTypeEnum.ENTITY_POSTS.value},
                    "url": {"input_field_path": "target_profile_url"},
                    "post_limit": {"input_field_path": "fetch_limit"},
                    # entity_posts flag will be set automatically based on job_type
                }
            ]
        }
        node = LinkedInScrapingNode(node_id="test_scraping_node", config=LinkedInScrapingConfig(**node_config_dict))
        runtime_config = self._create_runtime_config()
        output = await node.process(input_data=input_data, config=runtime_config)

        # Assertions
        self.assertIn("dynamic_url_posts", output.scraping_results)
        result_config = output.scraping_results["dynamic_url_posts"]
        self.assertIsInstance(result_config, dict)

        # Check specific extracted fields
        self.assertEqual(result_config.get("url"), test_url)
        self.assertEqual(result_config.get("username"), "dynamic-url-comp") # Extracted
        self.assertEqual(result_config.get("type"), EntityTypeEnum.COMPANY.value) # Extracted
        self.assertEqual(result_config.get("entity_posts"), YesNoEnum.YES.value) # Aligned
        self.assertEqual(result_config.get("post_limit"), 25)

        summary = output.execution_summary["dynamic_url_posts"]
        self.assertEqual(summary["jobs_triggered"], 1)
        self.assertEqual(summary["successful"], 1)
        self.assertEqual(summary["failed"], 0)

    async def test_validation_url_and_username_conflict(self):
        """Tests validation failure when both URL and username are provided."""
        input_data = {"profile_url": "https://www.linkedin.com/in/conflict-user/"}
        node_config_dict = {
            "test_mode": True,
            "jobs": [
                {
                    "output_field_name": "url_username_conflict",
                    "job_type": {"static_value": JobTypeEnum.PROFILE_INFO.value},
                    "url": {"input_field_path": "profile_url"},
                    "username": {"static_value": "explicit_username"}, # Conflict
                    "type": {"static_value": EntityTypeEnum.PERSON.value}, # Conflict
                    # profile_info flag aligned by node
                }
            ]
        }
        node = LinkedInScrapingNode(node_id="test_scraping_node", config=LinkedInScrapingConfig(**node_config_dict))
        runtime_config = self._create_runtime_config()
        output = await node.process(input_data=input_data, config=runtime_config)

        # Assertions: Expecting validation error from ScrapingRequest
        self.assertIn("url_username_conflict", output.scraping_results)
        result = output.scraping_results["url_username_conflict"]
        self.assertIsInstance(result, dict)
        self.assertIn("error", result)
        # Error comes from ScrapingRequest.model_validate called within the node
        self.assertIn("Validation failed", result["error"])
        self.assertIn("'username' and 'type' cannot be provided if 'url' is provided", result["error"])

        summary = output.execution_summary["url_username_conflict"]
        self.assertEqual(summary["jobs_triggered"], 0) # Validation fails before trigger count increments ideally
        self.assertEqual(summary["successful"], 0)
        self.assertEqual(summary["failed"], 1)
        self.assertEqual(len(summary["errors"]), 1)
        self.assertIn("Validation failed", summary["errors"][0])

    # --- COMPREHENSIVE CREDIT CALCULATION TESTS ---

    async def test_credit_calculation_profile_info_simple(self):
        """Test credit calculation for simple profile info job."""
        input_data = {}
        node_config_dict = {
            "test_mode": True,
            "jobs": [
                {
                    "output_field_name": "profile_credit_test",
                    "job_type": {"static_value": JobTypeEnum.PROFILE_INFO.value},
                    "type": {"static_value": EntityTypeEnum.PERSON.value},
                    "username": {"static_value": "test_user"},
                    "profile_info": {"static_value": YesNoEnum.YES.value},
                }
            ]
        }
        node = LinkedInScrapingNode(node_id="test_node", config=LinkedInScrapingConfig(**node_config_dict))
        runtime_config = self._create_runtime_config()
        output = await node.process(input_data=input_data, config=runtime_config)

        credit_summary = output.execution_summary["_credit_summary"]
        # Profile info for person = 1 credit
        self.assertEqual(credit_summary["total_potential_credits"], 1)
        self.assertEqual(credit_summary["total_potential_dollar_cost"], 0.01)  # $0.01 per credit

    async def test_credit_calculation_company_posts_with_comments_reactions(self):
        """Test credit calculation for company posts with comments and reactions."""
        input_data = {}
        node_config_dict = {
            "test_mode": True,
            "jobs": [
                {
                    "output_field_name": "company_posts_full",
                    "job_type": {"static_value": JobTypeEnum.ENTITY_POSTS.value},
                    "type": {"static_value": EntityTypeEnum.COMPANY.value},
                    "username": {"static_value": "test_company"},
                    "entity_posts": {"static_value": YesNoEnum.YES.value},
                    "post_limit": {"static_value": 10},
                    "post_comments": {"static_value": YesNoEnum.YES.value},
                    "comment_limit": {"static_value": 20},
                    "post_reactions": {"static_value": YesNoEnum.YES.value},
                    "reaction_limit": {"static_value": 100},
                }
            ]
        }
        node = LinkedInScrapingNode(node_id="test_node", config=LinkedInScrapingConfig(**node_config_dict))
        runtime_config = self._create_runtime_config()
        output = await node.process(input_data=input_data, config=runtime_config)

        credit_summary = output.execution_summary["_credit_summary"]
        
        # Calculate expected credits based on credit_calculator.py logic:
        # For company entity posts:
        # 1. Base posts: 10 posts / 50 per batch = 1 batch = 1 credit
        # 2. Comments: 10 posts * 1 credit per post = 10 credits
        # 3. Reactions for company: 10 posts with 100 reactions each
        #    - First 49 reactions: 3 credits  
        #    - Remaining 51 reactions: ceil(51/49) = 2 batches * 2 credits = 4 credits
        #    - Total per post: 3 + 4 = 7 credits
        #    - Total for all posts: 10 * 7 = 70 credits
        # Total = 1 + 10 + 70 = 81 credits
        
        expected_credits = await self._calculate_expected_credits({
            "type": "company",
            "entity_posts": "yes",
            "post_limit": 10,
            "post_comments": "yes",
            "comment_limit": 20,
            "post_reactions": "yes",
            "reaction_limit": 100
        })
        
        self.assertEqual(credit_summary["total_potential_credits"], expected_credits["max_credits"])
        self.assertEqual(credit_summary["total_potential_credits"], 41)  # Explicit check
        self.assertEqual(credit_summary["total_potential_dollar_cost"], round(expected_credits["dollar_cost"], 4))
        self.assertEqual(credit_summary["total_potential_dollar_cost"], 0.41)  # $0.01 * 81
        
        # Verify no actual consumption in test mode
        self.assertEqual(credit_summary["total_credits_consumed"], 0)
        self.assertEqual(credit_summary["total_dollar_cost"], 0.0)
        self.assertTrue(credit_summary["test_mode"])

    async def test_credit_calculation_person_activity_comments_with_nested(self):
        """Test credit calculation for person activity comments with nested comments and reactions."""
        input_data = {}
        node_config_dict = {
            "test_mode": True,
            "jobs": [
                {
                    "output_field_name": "activity_comments_complex",
                    "job_type": {"static_value": JobTypeEnum.ACTIVITY_COMMENTS.value},
                    "username": {"static_value": "test_person"},
                    "activity_comments": {"static_value": YesNoEnum.YES.value},
                    "post_limit": {"static_value": 5},
                    "post_comments": {"static_value": YesNoEnum.YES.value},
                    "comment_limit": {"static_value": 10},
                    "post_reactions": {"static_value": YesNoEnum.YES.value},
                    "reaction_limit": {"static_value": 50},
                }
            ]
        }
        node = LinkedInScrapingNode(node_id="test_node", config=LinkedInScrapingConfig(**node_config_dict))
        runtime_config = self._create_runtime_config()
        output = await node.process(input_data=input_data, config=runtime_config)

        credit_summary = output.execution_summary["_credit_summary"]
        
        # Activity comments: 1 credit base
        # Comments: 5 posts * 1 credit = 5 credits  
        # Reactions: 5 posts * reactions per post
        #   For person activity: 50 reactions, first 49 = 3 credits, remaining 1 = 2 credits = 5 credits per post
        #   Total: 5 * 5 = 25 credits
        # Total = 1 + 5 + 25 = 31 credits
        
        expected_credits = await self._calculate_expected_credits({
            "type": "person",
            "activity_comments": "yes",
            "post_limit": 5,
            "post_comments": "yes", 
            "comment_limit": 10,
            "post_reactions": "yes",
            "reaction_limit": 50
        })
        
        self.assertEqual(credit_summary["total_potential_credits"], expected_credits["max_credits"])

    async def test_credit_calculation_expand_list_multiple_jobs(self):
        """Test credit calculation when expanding lists across multiple users."""
        input_data = {
            "users": ["user1", "user2", "user3", "user4", "user5"],
            "post_settings": {
                "limit": 20,
                "fetch_comments": "yes",
                "fetch_reactions": "yes",
                "reaction_limit": 75
            }
        }
        node_config_dict = {
            "test_mode": True,
            "jobs": [
                {
                    "output_field_name": "expanded_user_posts",
                    "job_type": {"static_value": JobTypeEnum.ENTITY_POSTS.value},
                    "type": {"static_value": EntityTypeEnum.PERSON.value},
                    "username": {"input_field_path": "users", "expand_list": True},
                    "entity_posts": {"static_value": YesNoEnum.YES.value},
                    "post_limit": {"input_field_path": "post_settings.limit"},
                    "post_comments": {"input_field_path": "post_settings.fetch_comments"},
                    "post_reactions": {"input_field_path": "post_settings.fetch_reactions"},
                    "reaction_limit": {"input_field_path": "post_settings.reaction_limit"},
                }
            ]
        }
        node = LinkedInScrapingNode(node_id="test_node", config=LinkedInScrapingConfig(**node_config_dict))
        runtime_config = self._create_runtime_config()
        output = await node.process(input_data=input_data, config=runtime_config)

        credit_summary = output.execution_summary["_credit_summary"]
        
        # Calculate for one user:
        # Posts: 20 posts / 50 per batch = 1 batch = 1 credit
        # Comments: 20 posts * 1 credit = 20 credits
        # Reactions: 20 posts * 75 reactions per post
        #   For person: first 49 = 1 credit, remaining 26 = ceil(26/49) = 1 batch = 1 credit = 2 credits per post
        #   Total: 20 * 2 = 40 credits
        # Total per user = 1 + 20 + 40 = 61 credits
        # Total for 5 users = 5 * 61 = 305 credits
        
        single_user_credits = await self._calculate_expected_credits({
            "type": "person",
            "entity_posts": "yes", 
            "post_limit": 20,
            "post_comments": "yes",
            "comment_limit": rapid_api_settings.DEFAULT_COMMENT_LIMIT,
            "post_reactions": "yes",
            "reaction_limit": 75
        })
        
        expected_total = single_user_credits["max_credits"] * 5
        self.assertEqual(credit_summary["total_potential_credits"], expected_total)
        self.assertEqual(credit_summary["total_potential_dollar_cost"], round(expected_total * 0.01, 4))

    async def test_credit_calculation_search_jobs(self):
        """Test credit calculation for search jobs (keyword and hashtag)."""
        input_data = {
            "keywords": ["AI", "machine learning", "data science"],
            "hashtags": ["tech", "innovation"]
        }
        node_config_dict = {
            "test_mode": True,
            "jobs": [
                {
                    "output_field_name": "keyword_searches",
                    "job_type": {"static_value": JobTypeEnum.SEARCH_POST_BY_KEYWORD.value},
                    "keyword": {"input_field_path": "keywords", "expand_list": True},
                    "search_post_by_keyword": {"static_value": YesNoEnum.YES.value},
                    "post_limit": {"static_value": 50},
                },
                {
                    "output_field_name": "hashtag_searches",
                    "job_type": {"static_value": JobTypeEnum.SEARCH_POST_BY_HASHTAG.value},
                    "hashtag": {"input_field_path": "hashtags", "expand_list": True},
                    "search_post_by_hashtag": {"static_value": YesNoEnum.YES.value},
                    "post_limit": {"static_value": 25},
                }
            ]
        }
        node = LinkedInScrapingNode(node_id="test_node", config=LinkedInScrapingConfig(**node_config_dict))
        runtime_config = self._create_runtime_config()
        output = await node.process(input_data=input_data, config=runtime_config)

        credit_summary = output.execution_summary["_credit_summary"]
        
        # Search jobs are now implemented in credit_calculator.py
        # Keyword searches: 3 searches * 50 posts each / 10 posts per page = 3 * 5 = 15 credits
        # Hashtag searches: 2 searches * 25 posts each / 45 posts per page = 2 * 1 = 2 credits
        # Total = 15 + 2 = 17 credits
        
        self.assertEqual(credit_summary["total_potential_credits"], 17)
        self.assertEqual(credit_summary["total_potential_dollar_cost"], 0.17)
        self.assertEqual(credit_summary["uncalculated_jobs_count"], 0)

    async def test_credit_calculation_search_jobs_detailed(self):
        """Test detailed credit calculation for search jobs with various post limits."""
        input_data = {}
        node_config_dict = {
            "test_mode": True,
            "jobs": [
                {
                    "output_field_name": "keyword_small",
                    "job_type": {"static_value": JobTypeEnum.SEARCH_POST_BY_KEYWORD.value},
                    "keyword": {"static_value": "python"},
                    "search_post_by_keyword": {"static_value": YesNoEnum.YES.value},
                    "post_limit": {"static_value": 5},  # Less than 1 page
                },
                {
                    "output_field_name": "keyword_medium",
                    "job_type": {"static_value": JobTypeEnum.SEARCH_POST_BY_KEYWORD.value},
                    "keyword": {"static_value": "data science"},
                    "search_post_by_keyword": {"static_value": YesNoEnum.YES.value},
                    "post_limit": {"static_value": 25},  # ~3 pages
                },
                {
                    "output_field_name": "hashtag_large",
                    "job_type": {"static_value": JobTypeEnum.SEARCH_POST_BY_HASHTAG.value},
                    "hashtag": {"static_value": "technology"},
                    "search_post_by_hashtag": {"static_value": YesNoEnum.YES.value},
                    "post_limit": {"static_value": 100},  # ~3 pages (45 per page)
                }
            ]
        }
        node = LinkedInScrapingNode(node_id="test_node", config=LinkedInScrapingConfig(**node_config_dict))
        runtime_config = self._create_runtime_config()
        output = await node.process(input_data=input_data, config=runtime_config)

        credit_summary = output.execution_summary["_credit_summary"]
        
        # Keyword small: 5 posts / 10 per page = 1 credit
        # Keyword medium: 25 posts / 10 per page = 3 credits
        # Hashtag large: 100 posts / 50 per page = 2 credits
        # Total = 1 + 3 + 2 = 6 credits
        
        self.assertEqual(credit_summary["total_potential_credits"], 6)
        self.assertEqual(credit_summary["total_potential_dollar_cost"], 0.06)

    async def test_credit_calculation_edge_case_zero_posts(self):
        """Test credit calculation edge case with zero posts."""
        input_data = {}
        node_config_dict = {
            "test_mode": True,
            "jobs": [
                {
                    "output_field_name": "zero_posts_job",
                    "job_type": {"static_value": JobTypeEnum.ENTITY_POSTS.value},
                    "type": {"static_value": EntityTypeEnum.PERSON.value},
                    "username": {"static_value": "test_user"},
                    "entity_posts": {"static_value": YesNoEnum.YES.value},
                    "post_limit": {"static_value": 0},
                    "post_comments": {"static_value": YesNoEnum.YES.value},
                    "post_reactions": {"static_value": YesNoEnum.YES.value},
                }
            ]
        }
        node = LinkedInScrapingNode(node_id="test_node", config=LinkedInScrapingConfig(**node_config_dict))
        runtime_config = self._create_runtime_config()
        output = await node.process(input_data=input_data, config=runtime_config)

        credit_summary = output.execution_summary["_credit_summary"]
        
        # With 0 posts, should still have base credits but no comment/reaction credits
        # Entity posts base: 0 posts / 50 = 0 batches = 0 credits  
        # Comments: 0 posts * 1 = 0 credits
        # Reactions: 0 posts * reactions = 0 credits
        # Total = 0 credits
        
        expected_credits = await self._calculate_expected_credits({
            "type": "person",
            "entity_posts": "yes",
            "post_limit": 0,
            "post_comments": "yes",
            "post_reactions": "yes",
            "reaction_limit": rapid_api_settings.DEFAULT_REACTION_LIMIT
        })
        
        self.assertEqual(credit_summary["total_potential_credits"], expected_credits["max_credits"])

    async def test_credit_calculation_high_volume_reactions(self):
        """Test credit calculation with very high reaction limits."""
        input_data = {}
        node_config_dict = {
            "test_mode": True,
            "jobs": [
                {
                    "output_field_name": "high_reactions_job",
                    "job_type": {"static_value": JobTypeEnum.ENTITY_POSTS.value},
                    "type": {"static_value": EntityTypeEnum.COMPANY.value},
                    "username": {"static_value": "popular_company"},
                    "entity_posts": {"static_value": YesNoEnum.YES.value},
                    "post_limit": {"static_value": 3},
                    "post_reactions": {"static_value": YesNoEnum.YES.value},
                    "reaction_limit": {"static_value": 500},  # Very high limit
                }
            ]
        }
        node = LinkedInScrapingNode(node_id="test_node", config=LinkedInScrapingConfig(**node_config_dict))
        runtime_config = self._create_runtime_config()
        output = await node.process(input_data=input_data, config=runtime_config)

        credit_summary = output.execution_summary["_credit_summary"]
        
        # Company with 500 reactions per post:
        # Posts: 3 posts / 50 = 1 batch = 1 credit
        # Reactions per post: first 49 = 3 credits, remaining 451 = ceil(451/49) = 10 batches * 2 = 20 credits
        # Total reactions: 3 posts * 23 credits = 69 credits
        # Total = 1 + 69 = 70 credits
        
        expected_credits = await self._calculate_expected_credits({
            "type": "company",
            "entity_posts": "yes",
            "post_limit": 3,
            "post_reactions": "yes",
            "reaction_limit": 500
        })
        
        self.assertEqual(credit_summary["total_potential_credits"], expected_credits["max_credits"])
        self.assertGreater(credit_summary["total_potential_dollar_cost"], 0.3)  # Should be > $0.50

    async def test_credit_calculation_mixed_job_types(self):
        """Test credit calculation with multiple different job types in one run."""
        input_data = {
            "company_name": "test_company",
            "person_username": "test_person",
            "search_keyword": "technology"
        }
        node_config_dict = {
            "test_mode": True,
            "jobs": [
                {
                    "output_field_name": "company_profile",
                    "job_type": {"static_value": JobTypeEnum.PROFILE_INFO.value},
                    "type": {"static_value": EntityTypeEnum.COMPANY.value},
                    "username": {"input_field_path": "company_name"},
                    "profile_info": {"static_value": YesNoEnum.YES.value},
                },
                {
                    "output_field_name": "person_posts",
                    "job_type": {"static_value": JobTypeEnum.ENTITY_POSTS.value},
                    "type": {"static_value": EntityTypeEnum.PERSON.value},
                    "username": {"input_field_path": "person_username"},
                    "entity_posts": {"static_value": YesNoEnum.YES.value},
                    "post_limit": {"static_value": 15},
                    "post_comments": {"static_value": YesNoEnum.YES.value},
                },
                {
                    "output_field_name": "keyword_search",
                    "job_type": {"static_value": JobTypeEnum.SEARCH_POST_BY_KEYWORD.value},
                    "keyword": {"input_field_path": "search_keyword"},
                    "search_post_by_keyword": {"static_value": YesNoEnum.YES.value},
                    "post_limit": {"static_value": 30},
                }
            ]
        }
        node = LinkedInScrapingNode(node_id="test_node", config=LinkedInScrapingConfig(**node_config_dict))
        runtime_config = self._create_runtime_config()
        output = await node.process(input_data=input_data, config=runtime_config)

        credit_summary = output.execution_summary["_credit_summary"]
        
        # Company profile: 1 credit
        # Person posts: 15 posts / 50 = 1 batch = 1 credit + 15 comments = 16 credits
        # Keyword search: 30 posts / 10 per page = 3 credits (conservative estimate)
        # Total = 1 + 16 + 3 = 20 credits
        
        self.assertEqual(credit_summary["total_potential_credits"], 20)
        self.assertEqual(credit_summary["total_potential_dollar_cost"], 0.20)
        
        # No uncalculated jobs now that search is implemented
        self.assertEqual(credit_summary["uncalculated_jobs_count"], 0)

    async def test_credit_calculation_validation_failures(self):
        """Test that credit calculation handles validation failures properly."""
        input_data = {
            "valid_users": ["user1", "user2"],
            "invalid_job_type": "not_a_real_job"
        }
        node_config_dict = {
            "test_mode": True,
            "jobs": [
                {
                    "output_field_name": "valid_job",
                    "job_type": {"static_value": JobTypeEnum.PROFILE_INFO.value},
                    "type": {"static_value": EntityTypeEnum.PERSON.value},
                    "username": {"input_field_path": "valid_users", "expand_list": True},
                    "profile_info": {"static_value": YesNoEnum.YES.value},
                },
                {
                    "output_field_name": "invalid_job",
                    "job_type": {"input_field_path": "invalid_job_type"},  # Will fail
                    "username": {"static_value": "test_user"},
                }
            ]
        }
        node = LinkedInScrapingNode(node_id="test_node", config=LinkedInScrapingConfig(**node_config_dict))
        runtime_config = self._create_runtime_config()
        output = await node.process(input_data=input_data, config=runtime_config)

        credit_summary = output.execution_summary["_credit_summary"]
        
        # Should still calculate credits for valid jobs
        # Valid job: 2 users * 1 credit = 2 credits
        # Invalid job: 0 credits (failed validation)
        
        self.assertEqual(credit_summary["total_potential_credits"], 2)
        self.assertEqual(credit_summary["total_potential_dollar_cost"], 0.02)
        
        # Check that invalid job failed
        invalid_summary = output.execution_summary["invalid_job"]
        self.assertEqual(invalid_summary["failed"], 1)
        self.assertEqual(invalid_summary["successful"], 0)

    async def test_credit_calculation_empty_expansion_list(self):
        """Test credit calculation when expanding an empty list."""
        input_data = {
            "empty_users": [],
            "empty_keywords": []
        }
        node_config_dict = {
            "test_mode": True,
            "jobs": [
                {
                    "output_field_name": "empty_profiles",
                    "job_type": {"static_value": JobTypeEnum.PROFILE_INFO.value},
                    "type": {"static_value": EntityTypeEnum.PERSON.value},
                    "username": {"input_field_path": "empty_users", "expand_list": True},
                    "profile_info": {"static_value": YesNoEnum.YES.value},
                },
                {
                    "output_field_name": "empty_searches",
                    "job_type": {"static_value": JobTypeEnum.SEARCH_POST_BY_KEYWORD.value},
                    "keyword": {"input_field_path": "empty_keywords", "expand_list": True},
                    "search_post_by_keyword": {"static_value": YesNoEnum.YES.value},
                }
            ]
        }
        node = LinkedInScrapingNode(node_id="test_node", config=LinkedInScrapingConfig(**node_config_dict))
        runtime_config = self._create_runtime_config()
        output = await node.process(input_data=input_data, config=runtime_config)

        credit_summary = output.execution_summary["_credit_summary"]
        
        # No jobs triggered, so no credits
        self.assertEqual(credit_summary["total_potential_credits"], 0)
        self.assertEqual(credit_summary["total_potential_dollar_cost"], 0.0)
        self.assertEqual(credit_summary["total_credits_consumed"], 0)

    async def test_credit_calculation_url_parsing(self):
        """Test credit calculation when using URLs that need parsing."""
        input_data = {}
        node_config_dict = {
            "test_mode": True,
            "jobs": [
                {
                    "output_field_name": "url_based_profile",
                    "job_type": {"static_value": JobTypeEnum.PROFILE_INFO.value},
                    "url": {"static_value": "https://www.linkedin.com/in/test-user-123/"},
                    "profile_info": {"static_value": YesNoEnum.YES.value},
                },
                {
                    "output_field_name": "url_based_company",
                    "job_type": {"static_value": JobTypeEnum.ENTITY_POSTS.value},
                    "url": {"static_value": "https://www.linkedin.com/company/test-company-456/"},
                    "entity_posts": {"static_value": YesNoEnum.YES.value},
                    "post_limit": {"static_value": 10},
                }
            ]
        }
        node = LinkedInScrapingNode(node_id="test_node", config=LinkedInScrapingConfig(**node_config_dict))
        runtime_config = self._create_runtime_config()
        output = await node.process(input_data=input_data, config=runtime_config)

        credit_summary = output.execution_summary["_credit_summary"]
        
        # Profile: 1 credit
        # Company posts: 10 posts / 50 = 1 batch = 1 credit
        # Total = 2 credits
        
        self.assertEqual(credit_summary["total_potential_credits"], 2)
        self.assertEqual(credit_summary["total_potential_dollar_cost"], 0.02)

    async def test_credit_calculation_uncalculated_jobs_tracking(self):
        """Test tracking of jobs where credit calculation fails."""
        # Use unittest.mock to properly patch the credit_estimation function
        from unittest.mock import patch, AsyncMock
        
        # Create a wrapper that fails for specific users
        async def failing_credit_estimation(req):
            if req.get("username") == "failing_user":
                raise Exception("Credit calculation error")
            # Call the real function for other cases
            from services.scraper_service.credit_calculator import credit_estimation as real_credit_estimation
            return await real_credit_estimation(req)
        
        # Patch the credit_estimation in the linkedin_scraping module
        with patch('services.workflow_service.registry.nodes.scraping.linkedin_scraping.credit_estimation', 
                   new=failing_credit_estimation):
            input_data = {
                "users": ["good_user", "failing_user", "another_good_user"]
            }
            node_config_dict = {
                "test_mode": True,
                "jobs": [
                    {
                        "output_field_name": "mixed_users",
                        "job_type": {"static_value": JobTypeEnum.PROFILE_INFO.value},
                        "type": {"static_value": EntityTypeEnum.PERSON.value},
                        "username": {"input_field_path": "users", "expand_list": True},
                        "profile_info": {"static_value": YesNoEnum.YES.value},
                    }
                ]
            }
            node = LinkedInScrapingNode(node_id="test_node", config=LinkedInScrapingConfig(**node_config_dict))
            runtime_config = self._create_runtime_config()
            output = await node.process(input_data=input_data, config=runtime_config)

            credit_summary = output.execution_summary["_credit_summary"]
            
            # Should track uncalculated jobs
            self.assertEqual(credit_summary["uncalculated_jobs_count"], 1)
            self.assertIn("mixed_users_1", credit_summary["uncalculated_jobs"])
            
            # Should still calculate credits for successful jobs
            self.assertEqual(credit_summary["total_potential_credits"], 2)  # 2 good users

    # --- POST_DETAILS CREDIT CALCULATION TESTS ---

    async def test_credit_calculation_post_details_basic(self):
        """Test credit calculation for basic post details without enrichment."""
        input_data = {}
        node_config_dict = {
            "test_mode": True,
            "jobs": [
                {
                    "output_field_name": "basic_post_details",
                    "job_type": {"static_value": JobTypeEnum.POST_DETAILS.value},
                    "post_url_or_urn": {"static_value": "7335304292926451712"},
                    "post_details": {"static_value": YesNoEnum.YES.value},
                }
            ]
        }
        node = LinkedInScrapingNode(node_id="test_node", config=LinkedInScrapingConfig(**node_config_dict))
        runtime_config = self._create_runtime_config()
        output = await node.process(input_data=input_data, config=runtime_config)

        credit_summary = output.execution_summary["_credit_summary"]
        
        # Basic post details = 1 credit
        self.assertEqual(credit_summary["total_potential_credits"], 1)
        self.assertEqual(credit_summary["total_potential_dollar_cost"], 0.01)
        
        # Verify no actual consumption in test mode
        self.assertEqual(credit_summary["total_credits_consumed"], 0)
        self.assertEqual(credit_summary["total_dollar_cost"], 0.0)
        self.assertTrue(credit_summary["test_mode"])

    async def test_credit_calculation_post_details_with_comments(self):
        """Test credit calculation for post details with comments enrichment."""
        input_data = {}
        node_config_dict = {
            "test_mode": True,
            "jobs": [
                {
                    "output_field_name": "post_with_comments",
                    "job_type": {"static_value": JobTypeEnum.POST_DETAILS.value},
                    "post_url_or_urn": {"static_value": "7335304292926451712"},
                    "post_details": {"static_value": YesNoEnum.YES.value},
                    "post_comments": {"static_value": YesNoEnum.YES.value},
                    "comment_limit": {"static_value": 100},  # Needs 2 pages (100/50)
                }
            ]
        }
        node = LinkedInScrapingNode(node_id="test_node", config=LinkedInScrapingConfig(**node_config_dict))
        runtime_config = self._create_runtime_config()
        output = await node.process(input_data=input_data, config=runtime_config)

        credit_summary = output.execution_summary["_credit_summary"]
        
        # Calculate expected credits
        expected_credits = await self._calculate_expected_credits({
            "post_details": "yes",
            "post_comments": "yes",
            "comment_limit": 100,
            "post_reactions": "no"
        })
        
        # Post details: 1 base + comments for 1 post
        self.assertEqual(credit_summary["total_potential_credits"], expected_credits["max_credits"])
        self.assertEqual(credit_summary["total_potential_dollar_cost"], round(expected_credits["dollar_cost"], 4))

    async def test_credit_calculation_post_details_with_reactions(self):
        """Test credit calculation for post details with reactions enrichment."""
        input_data = {}
        node_config_dict = {
            "test_mode": True,
            "jobs": [
                {
                    "output_field_name": "post_with_reactions",
                    "job_type": {"static_value": JobTypeEnum.POST_DETAILS.value},
                    "post_url_or_urn": {"static_value": "7335304292926451712"},
                    "post_details": {"static_value": YesNoEnum.YES.value},
                    "post_reactions": {"static_value": YesNoEnum.YES.value},
                    "reaction_limit": {"static_value": 150},  # Needs 3 pages (150/50)
                }
            ]
        }
        node = LinkedInScrapingNode(node_id="test_node", config=LinkedInScrapingConfig(**node_config_dict))
        runtime_config = self._create_runtime_config()
        output = await node.process(input_data=input_data, config=runtime_config)

        credit_summary = output.execution_summary["_credit_summary"]
        
        # Calculate expected credits
        expected_credits = await self._calculate_expected_credits({
            "post_details": "yes",
            "post_comments": "no",
            "post_reactions": "yes",
            "reaction_limit": 150
        })
        
        self.assertEqual(credit_summary["total_potential_credits"], expected_credits["max_credits"])
        self.assertEqual(credit_summary["total_potential_dollar_cost"], round(expected_credits["dollar_cost"], 4))

    async def test_credit_calculation_post_details_full_enrichment(self):
        """Test credit calculation for post details with both comments and reactions."""
        input_data = {}
        node_config_dict = {
            "test_mode": True,
            "jobs": [
                {
                    "output_field_name": "fully_enriched_post",
                    "job_type": {"static_value": JobTypeEnum.POST_DETAILS.value},
                    "post_url_or_urn": {"static_value": "7335304292926451712"},
                    "post_details": {"static_value": YesNoEnum.YES.value},
                    "post_comments": {"static_value": YesNoEnum.YES.value},
                    "comment_limit": {"static_value": 200},  # Needs 4 pages
                    "post_reactions": {"static_value": YesNoEnum.YES.value},
                    "reaction_limit": {"static_value": 300},  # Needs 6 pages
                }
            ]
        }
        node = LinkedInScrapingNode(node_id="test_node", config=LinkedInScrapingConfig(**node_config_dict))
        runtime_config = self._create_runtime_config()
        output = await node.process(input_data=input_data, config=runtime_config)

        credit_summary = output.execution_summary["_credit_summary"]
        
        # Calculate expected credits
        expected_credits = await self._calculate_expected_credits({
            "post_details": "yes",
            "post_comments": "yes",
            "comment_limit": 200,
            "post_reactions": "yes",
            "reaction_limit": 300
        })
        
        # Post details: 1 base + 4 comment pages + 6 reaction pages (first 2 + 4 more)
        self.assertEqual(credit_summary["total_potential_credits"], expected_credits["max_credits"])
        self.assertEqual(credit_summary["total_potential_dollar_cost"], round(expected_credits["dollar_cost"], 4))

    async def test_credit_calculation_post_details_expansion_multiple_posts(self):
        """Test credit calculation for expanded post details across multiple posts."""
        input_data = {
            "post_urns": ["7335304292926451712", "7334567890123456789", "7333456789012345678"],
            "enrichment": {
                "comments": "yes",
                "reactions": "yes",
                "comment_limit": 50,
                "reaction_limit": 100
            }
        }
        node_config_dict = {
            "test_mode": True,
            "jobs": [
                {
                    "output_field_name": "multiple_enriched_posts",
                    "job_type": {"static_value": JobTypeEnum.POST_DETAILS.value},
                    "post_url_or_urn": {"input_field_path": "post_urns", "expand_list": True},
                    "post_details": {"static_value": YesNoEnum.YES.value},
                    "post_comments": {"input_field_path": "enrichment.comments"},
                    "comment_limit": {"input_field_path": "enrichment.comment_limit"},
                    "post_reactions": {"input_field_path": "enrichment.reactions"},
                    "reaction_limit": {"input_field_path": "enrichment.reaction_limit"},
                }
            ]
        }
        node = LinkedInScrapingNode(node_id="test_node", config=LinkedInScrapingConfig(**node_config_dict))
        runtime_config = self._create_runtime_config()
        output = await node.process(input_data=input_data, config=runtime_config)

        credit_summary = output.execution_summary["_credit_summary"]
        
        # Calculate for one post
        single_post_credits = await self._calculate_expected_credits({
            "post_details": "yes",
            "post_comments": "yes",
            "comment_limit": 50,
            "post_reactions": "yes",
            "reaction_limit": 100
        })
        
        # 3 posts * credits per post
        expected_total = single_post_credits["max_credits"] * 3
        self.assertEqual(credit_summary["total_potential_credits"], expected_total)
        self.assertEqual(credit_summary["total_potential_dollar_cost"], round(expected_total * 0.01, 4))

    async def test_credit_calculation_mixed_post_details_and_other_jobs(self):
        """Test credit calculation with post details mixed with other job types."""
        input_data = {
            "post_urn": "7335304292926451712",
            "company_name": "test_company",
            "search_term": "AI"
        }
        node_config_dict = {
            "test_mode": True,
            "jobs": [
                {
                    "output_field_name": "post_data",
                    "job_type": {"static_value": JobTypeEnum.POST_DETAILS.value},
                    "post_url_or_urn": {"input_field_path": "post_urn"},
                    "post_details": {"static_value": YesNoEnum.YES.value},
                    "post_comments": {"static_value": YesNoEnum.YES.value},
                    "post_reactions": {"static_value": YesNoEnum.YES.value},
                },
                {
                    "output_field_name": "company_profile",
                    "job_type": {"static_value": JobTypeEnum.PROFILE_INFO.value},
                    "type": {"static_value": EntityTypeEnum.COMPANY.value},
                    "username": {"input_field_path": "company_name"},
                    "profile_info": {"static_value": YesNoEnum.YES.value},
                },
                {
                    "output_field_name": "keyword_search",
                    "job_type": {"static_value": JobTypeEnum.SEARCH_POST_BY_KEYWORD.value},
                    "keyword": {"input_field_path": "search_term"},
                    "search_post_by_keyword": {"static_value": YesNoEnum.YES.value},
                    "post_limit": {"static_value": 20},
                }
            ]
        }
        node = LinkedInScrapingNode(node_id="test_node", config=LinkedInScrapingConfig(**node_config_dict))
        runtime_config = self._create_runtime_config()
        output = await node.process(input_data=input_data, config=runtime_config)

        credit_summary = output.execution_summary["_credit_summary"]
        
        # Calculate expected credits for each job type
        post_details_credits = await self._calculate_expected_credits({
            "post_details": "yes",
            "post_comments": "yes",
            "post_reactions": "yes",
            "comment_limit": rapid_api_settings.DEFAULT_COMMENT_LIMIT,
            "reaction_limit": rapid_api_settings.DEFAULT_REACTION_LIMIT
        })
        
        company_profile_credits = await self._calculate_expected_credits({
            "type": "company",
            "profile_info": "yes"
        })
        
        search_credits = await self._calculate_expected_credits({
            "search_post_by_keyword": "yes",
            "post_limit": 20
        })
        
        expected_total = (post_details_credits["max_credits"] + 
                         company_profile_credits["max_credits"] + 
                         search_credits["max_credits"])
        
        self.assertEqual(credit_summary["total_potential_credits"], expected_total)
        self.assertEqual(credit_summary["total_potential_dollar_cost"], round(expected_total * 0.01, 4))

# Allow running the tests directly using python -m unittest path/to/test_file.py
if __name__ == "__main__":
    unittest.main()
