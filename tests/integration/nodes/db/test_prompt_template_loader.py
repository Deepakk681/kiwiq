import unittest
import uuid
import asyncio
from typing import Dict, Any, Optional, List, Tuple, Type

# Pydantic imports
from pydantic import BaseModel, Field, create_model

# Node imports
from workflow_service.registry.nodes.db.prompt_template_loader import (
    PromptTemplateLoaderNode,
    LoadPromptTemplatesConfig,
    PromptTemplateLoadEntry,
    PromptTemplatePathConfig,
    LoadPromptTemplatesOutput,
    LoadedPromptTemplateData
)

# Context and Service imports
from workflow_service.services.external_context_manager import (
    ExternalContextManager,
    get_external_context_manager_with_clients
)
from kiwi_app.workflow_app import crud as wf_crud
from kiwi_app.workflow_app.schemas import WorkflowRunJobCreate, PromptTemplateCreate
from db.session import get_async_db_as_manager

from services.workflow_service.config.constants import (
    APPLICATION_CONTEXT_KEY,
    EXTERNAL_CONTEXT_MANAGER_KEY,
    OBJECT_PATH_REFERENCE_DELIMITER,
    DB_SESSION_KEY,
)
from db.session import get_async_session

# Simple Mock User if real one is complex to import/instantiate
class MockUser(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    is_superuser: bool = False
    # Add other fields if DAO checks them, but keep minimal

# --- Test Class ---

class TestPromptTemplateLoaderNode(unittest.IsolatedAsyncioTestCase):
    """
    Integration tests for PromptTemplateLoaderNode.

    Assumes a running database accessible via settings.
    Creates and deletes test prompt templates.
    """
    test_org_id: uuid.UUID
    test_user_id: uuid.UUID
    user_regular: MockUser
    run_job_regular: WorkflowRunJobCreate
    runtime_config_regular: Dict[str, Any]
    external_context: ExternalContextManager
    prompt_template_dao: wf_crud.PromptTemplateDAO
    created_template_ids: List[uuid.UUID] = []

    # Test template names and versions
    tpl_name_user1: str = "test_user_template_1"
    tpl_version_user1_v1: str = "1.0"
    tpl_version_user1_v2: str = "1.1"
    tpl_name_sys1: str = "test_system_template_1"
    tpl_version_sys1_v1: str = "1.0"

    async def asyncSetUp(self):
        """Set up test-specific users, orgs, contexts, and templates."""
        self.test_org_id = uuid.uuid4()
        self.test_user_id = uuid.uuid4()
        self.created_template_ids = [] # Reset for each test

        self.user_regular = MockUser(id=self.test_user_id, is_superuser=False)

        base_run_job_info = {
            "run_id": uuid.uuid4(),
            "workflow_id": uuid.uuid4(),
            "owner_org_id": self.test_org_id,
        }
        self.run_job_regular = WorkflowRunJobCreate(
            **base_run_job_info, triggered_by_user_id=self.user_regular.id
        )

        self.external_context = await get_external_context_manager_with_clients()
        self.prompt_template_dao = self.external_context.daos.prompt_template
        self.db_session = await get_async_session()
        self.runtime_config_regular = {
            "configurable": {
                APPLICATION_CONTEXT_KEY: {
                    "user": self.user_regular,
                    "workflow_run_job": self.run_job_regular
                },
                EXTERNAL_CONTEXT_MANAGER_KEY: self.external_context,
                DB_SESSION_KEY: self.db_session
            }
        }

        # Clean before creating new templates
        await self._clean_test_data()
        await self._create_test_templates()

    async def asyncTearDown(self):
        """Clean up test templates and close context."""
        await self._clean_test_data()
        if self.external_context:
            await self.external_context.close()
        if self.db_session:
            await self.db_session.close()

    async def _create_test_templates(self):
        """Helper to create prompt templates needed for tests."""
        templates_to_create = [
            # User-specific template, v1
            {
                "name": self.tpl_name_user1, "version": self.tpl_version_user1_v1,
                "template_content": f"User template {self.tpl_name_user1} v{self.tpl_version_user1_v1}, inputs: {{var1}}",
                "input_variables": {"var1": None},
                "owner_org_id": None, # self.test_org_id,
                "is_system_entity": True, "description": "User v1", "is_public": True
            },
            # User-specific template, v2
            {
                "name": self.tpl_name_user1, "version": self.tpl_version_user1_v2,
                "template_content": f"User template {self.tpl_name_user1} v{self.tpl_version_user1_v2}, inputs: {{var1}}, {{var2}}",
                "input_variables": {"var1": None, "var2": None},
                "owner_org_id": None, # self.test_org_id,
                "is_system_entity": True, "description": "User v2", "is_public": True
            },
            # System template
            {
                "name": self.tpl_name_sys1, "version": self.tpl_version_sys1_v1,
                "template_content": f"System template {self.tpl_name_sys1} v{self.tpl_version_sys1_v1}, inputs: {{sys_var}}",
                "input_variables": {"sys_var": None},
                "owner_org_id": None, # None, # System templates have no org owner
                "is_system_entity": True, "description": "System v1", "is_public": True
            },
        ]

        async with get_async_db_as_manager() as db:
            for template_data in templates_to_create:
                # Check if it exists first (idempotency)
                existing = await self.prompt_template_dao.get_by_name_version(
                    db, name=template_data["name"], version=template_data["version"], owner_org_id=template_data.get("owner_org_id")
                )
                if existing:
                    print(f"Warning: Test template {template_data['name']} v{template_data['version']} already exists, skipping creation.")
                    await self.prompt_template_dao.delete(db, id=existing.id)
                    # self.created_template_ids.append(existing.id)
                    # continue

                try:
                    # Extract owner_org_id separately for the DAO call
                    owner_org_id = template_data.pop("owner_org_id", None)
                    # Create schema instance from the remaining data
                    prompt_create_schema = PromptTemplateCreate(**template_data)

                    # Call DAO create method with schema and owner_org_id
                    db_obj = await self.prompt_template_dao.create(
                        db=db,
                        obj_in=prompt_create_schema,
                        owner_org_id=owner_org_id
                    )
                    
                    
                    # asyncio.sleep(1)
                    # if prompt_create_schema.name == self.tpl_name_sys1:
                    #     template1 = await self.prompt_template_dao.get_by_name_version(db, name=prompt_create_schema.name, version=prompt_create_schema.version, owner_org_id=owner_org_id)
                    #     template2 = await self.prompt_template_dao.search_by_name_version(
                    #         db=db,
                    #         name=prompt_create_schema.name,
                    #         version=prompt_create_schema.version,
                    #         owner_org_id=None,
                    #         include_public=True,  # Include public templates
                    #         include_system_entities=False,  # Include system templates
                    #         include_public_system_entities=True,  # Include public system templates
                    #         is_superuser=self.user_regular.is_superuser  # Default to non-superuser access
                    #     )
                    #     print(f"template1: {template1}")
                    #     print(f"template2: {template2}")
                    #     # print(f"template2: {template2}")
                    #     # import ipdb; ipdb.set_trace()


                    self.created_template_ids.append(db_obj.id)
                    print(f"Created test template {db_obj.name} v{db_obj.version} (ID: {db_obj.id})")
                except Exception as e:
                    print(f"Error creating test template {template_data.get('name', 'N/A')} v{template_data.get('version', 'N/A')}: {e}")
                    await db.rollback() # Rollback on error for this template
                    raise # Re-raise to fail the setup

    async def _clean_test_data(self):
        """Helper to delete prompt templates created during setup."""
        if not self.created_template_ids:
            # print("No template IDs recorded for cleanup.")
            # Attempt cleanup by name/version as fallback, just in case
            templates_to_clean = [
                (self.tpl_name_user1, self.tpl_version_user1_v1, self.test_org_id),
                (self.tpl_name_user1, self.tpl_version_user1_v2, self.test_org_id),
                (self.tpl_name_sys1, self.tpl_version_sys1_v1, None), # System template owner_org_id is None
            ]
            async with get_async_db_as_manager() as db:
                for name, version, org_id in templates_to_clean:
                    try:
                        template = await self.prompt_template_dao.get_by_name_version(db, name=name, version=version, owner_org_id=org_id)
                        if template:
                            print(f"Cleaning up fallback template {name} v{version} (ID: {template.id})")
                            await db.delete(template)
                            await db.commit()
                    except Exception as e:
                        print(f"Error during fallback cleanup for {name} v{version}: {e}")
                        await db.rollback()

        # Primary cleanup using stored IDs
        if self.created_template_ids:
            print(f"Cleaning up templates with IDs: {self.created_template_ids}")
            async with get_async_db_as_manager() as db:
                for template_id in self.created_template_ids:
                    try:
                        template = await self.prompt_template_dao.get(db, id=template_id)
                        if template:
                            await db.delete(template)
                            await db.commit()
                            print(f"Deleted template ID: {template_id}")
                        else:
                            print(f"Template ID {template_id} not found for deletion.")
                    except Exception as e:
                        print(f"Error deleting template ID {template_id}: {e}")
                        await db.rollback()
            self.created_template_ids = [] # Clear list after attempting cleanup

    def _get_load_node(self, config: Dict[str, Any]) -> PromptTemplateLoaderNode:
        """Instantiate PromptTemplateLoaderNode with given config."""
        node_config = LoadPromptTemplatesConfig(**config)
        return PromptTemplateLoaderNode(config=node_config, node_id="test-load-prompts-node")

    # --- Test Cases ---

    async def test_load_single_static(self):
        """Test loading one template using static name/version."""
        node = self._get_load_node({
            "load_entries": [
                {
                    "path_config": {
                        "static_name": self.tpl_name_user1,
                        "static_version": self.tpl_version_user1_v1
                    }
                    # output_key_name defaults to template name
                }
            ]
        })
        output = await node.process({}, runtime_config=self.runtime_config_regular)

        self.assertEqual(len(output.loaded_templates), 1)
        self.assertEqual(len(output.load_errors), 0)
        self.assertIn(self.tpl_name_user1, output.loaded_templates)
        loaded_data = output.loaded_templates[self.tpl_name_user1]
        self.assertIsInstance(loaded_data, LoadedPromptTemplateData)
        self.assertIsNotNone(loaded_data.template)
        self.assertIn(self.tpl_version_user1_v1, loaded_data.template)
        self.assertEqual(list(loaded_data.input_variables.keys()), ["var1"])
        self.assertIsNotNone(loaded_data.id)
        self.assertIsNotNone(loaded_data.metadata)
        self.assertEqual(loaded_data.metadata.get("name"), self.tpl_name_user1)
        self.assertEqual(loaded_data.metadata.get("version"), self.tpl_version_user1_v1)

    async def test_load_single_dynamic_input(self):
        """Test loading one template using name/version from input data paths."""
        input_data = {
            "prompt_details": {
                "name_key": self.tpl_name_user1,
                "version_key": self.tpl_version_user1_v2
            }
        }
        node = self._get_load_node({
            "load_entries": [
                {
                    "path_config": {
                        "input_name_field_path": "prompt_details.name_key",
                        "input_version_field_path": "prompt_details.version_key"
                    },
                    "output_key_name": "dynamic_template"
                }
            ]
        })
        output = await node.process(input_data, runtime_config=self.runtime_config_regular)

        self.assertEqual(len(output.loaded_templates), 1)
        self.assertEqual(len(output.load_errors), 0)
        self.assertIn("dynamic_template", output.loaded_templates)
        loaded_data = output.loaded_templates["dynamic_template"]
        self.assertIsNotNone(loaded_data.template)
        self.assertIn(self.tpl_version_user1_v2, loaded_data.template)
        self.assertEqual(list(loaded_data.input_variables.keys()), ["var1", "var2"])
        self.assertIsNotNone(loaded_data.id)
        self.assertEqual(loaded_data.metadata.get("name"), self.tpl_name_user1)
        self.assertEqual(loaded_data.metadata.get("version"), self.tpl_version_user1_v2)

    async def test_load_fallback_static(self):
        """Load using static name/version when input path is provided but not found."""
        input_data = {"other_data": 123} # Missing prompt_details
        node = self._get_load_node({
            "load_entries": [
                {
                    "path_config": {
                        "static_name": self.tpl_name_user1, # Static fallback
                        "static_version": self.tpl_version_user1_v1, # Static fallback
                        "input_name_field_path": "prompt_details.name_key", # Will not be found
                        "input_version_field_path": "prompt_details.version_key" # Will not be found
                    },
                    "output_key_name": "fallback_static_load"
                }
            ]
        })
        output = await node.process(input_data, runtime_config=self.runtime_config_regular)

        self.assertEqual(len(output.loaded_templates), 1)
        self.assertEqual(len(output.load_errors), 0) # Fallback should succeed without error reported
        self.assertIn("fallback_static_load", output.loaded_templates)
        loaded_data = output.loaded_templates["fallback_static_load"]
        self.assertIn(self.tpl_version_user1_v1, loaded_data.template) # Check it loaded v1
        self.assertEqual(loaded_data.metadata.get("name"), self.tpl_name_user1)
        self.assertEqual(loaded_data.metadata.get("version"), self.tpl_version_user1_v1)

    async def test_load_fallback_input_override(self):
        """Load using input path value overriding static value."""
        input_data = {
            "prompt_details": {
                "name": self.tpl_name_user1, # Input name
                "version": self.tpl_version_user1_v2 # Input version (should override static v1)
            }
        }
        node = self._get_load_node({
            "load_entries": [
                {
                    "path_config": {
                        "static_name": self.tpl_name_sys1, # Static name (will be overridden)
                        "static_version": self.tpl_version_user1_v1, # Static version (will be overridden)
                        "input_name_field_path": "prompt_details.name",
                        "input_version_field_path": "prompt_details.version"
                    },
                    "output_key_name": "input_override_load"
                }
            ]
        })
        output = await node.process(input_data, runtime_config=self.runtime_config_regular)

        self.assertEqual(len(output.loaded_templates), 1)
        self.assertEqual(len(output.load_errors), 0)
        self.assertIn("input_override_load", output.loaded_templates)
        loaded_data = output.loaded_templates["input_override_load"]
        print(f"loaded_data: {loaded_data}")
        self.assertIn(self.tpl_version_user1_v2, loaded_data.template) # Check it loaded v2
        self.assertEqual(loaded_data.metadata.get("name"), self.tpl_name_user1)
        self.assertEqual(loaded_data.metadata.get("version"), self.tpl_version_user1_v2)

    async def test_load_system_template(self):
        """Test loading a template marked as is_system_entity."""
        node = self._get_load_node({
            "load_entries": [
                {
                    "path_config": {
                        "static_name": self.tpl_name_sys1,
                        "static_version": self.tpl_version_sys1_v1
                    },
                    "output_key_name": "loaded_system_template"
                }
            ]
        })
        # Regular user should be able to load system templates (DAO handles logic)
        output = await node.process({}, runtime_config=self.runtime_config_regular)

        self.assertEqual(len(output.loaded_templates), 1)
        self.assertEqual(len(output.load_errors), 0)
        self.assertIn("loaded_system_template", output.loaded_templates)
        loaded_data = output.loaded_templates["loaded_system_template"]
        self.assertIsNotNone(loaded_data.template)
        self.assertIn("System template", loaded_data.template)
        self.assertEqual(list(loaded_data.input_variables.keys()), ["sys_var"])
        self.assertTrue(loaded_data.metadata.get("is_system_entity"))
        self.assertEqual(loaded_data.metadata.get("name"), self.tpl_name_sys1)
        self.assertEqual(loaded_data.metadata.get("version"), self.tpl_version_sys1_v1)

    async def test_load_multiple_entries(self):
        """Load multiple templates in one node execution."""
        input_data = {"ver_for_user1": self.tpl_version_user1_v1}
        node = self._get_load_node({
            "load_entries": [
                { # Static user v2
                    "path_config": {"static_name": self.tpl_name_user1, "static_version": self.tpl_version_user1_v2},
                    "output_key_name": "user_v2_key"
                },
                { # Dynamic user v1
                    "path_config": {"static_name": self.tpl_name_user1, "input_version_field_path": "ver_for_user1"},
                    "output_key_name": "user_v1_key"
                },
                { # Static system v1 (default output key)
                    "path_config": {"static_name": self.tpl_name_sys1, "static_version": self.tpl_version_sys1_v1}
                }
            ]
        })
        output = await node.process(input_data, runtime_config=self.runtime_config_regular)

        self.assertEqual(len(output.loaded_templates), 3)
        self.assertEqual(len(output.load_errors), 0)

        # Check user v2
        self.assertIn("user_v2_key", output.loaded_templates)
        self.assertIn(self.tpl_version_user1_v2, output.loaded_templates["user_v2_key"].template)

        # Check user v1
        self.assertIn("user_v1_key", output.loaded_templates)
        self.assertIn(self.tpl_version_user1_v1, output.loaded_templates["user_v1_key"].template)

        # Check system v1 (key defaults to template name)
        self.assertIn(self.tpl_name_sys1, output.loaded_templates)
        self.assertTrue(output.loaded_templates[self.tpl_name_sys1].metadata.get("is_system_entity"))

    async def test_load_non_existent_template(self):
        """Attempt to load a template that doesn't exist; check load_errors."""
        non_existent_name = "does_not_exist"
        non_existent_version = "0.0"
        node = self._get_load_node({
            "load_entries": [
                {
                    "path_config": {
                        "static_name": non_existent_name,
                        "static_version": non_existent_version
                    },
                    "output_key_name": "failure_key"
                }
            ]
        })
        output = await node.process({}, runtime_config=self.runtime_config_regular)

        self.assertEqual(len(output.loaded_templates), 0)
        self.assertEqual(len(output.load_errors), 1)
        error_entry = output.load_errors[0]
        self.assertEqual(error_entry.get("entry_index"), 0)
        self.assertEqual(error_entry.get("resolved_name"), non_existent_name)
        self.assertEqual(error_entry.get("resolved_version"), non_existent_version)
        self.assertEqual(error_entry.get("output_key"), "failure_key")
        self.assertIn("not found", error_entry.get("error", ""))

    async def test_load_path_resolution_failure_no_static(self):
        """Fail resolution: input path not found, no static fallback."""
        input_data = {} # Missing input field
        node = self._get_load_node({
            "load_entries": [
                {
                    "path_config": {
                        # No static_name
                        "static_version": self.tpl_version_user1_v1,
                        "input_name_field_path": "missing_path.name"
                    },
                    "output_key_name": "res_fail_key"
                }
            ]
        })
        output = await node.process(input_data, runtime_config=self.runtime_config_regular)

        self.assertEqual(len(output.loaded_templates), 0)
        self.assertEqual(len(output.load_errors), 1)
        error_entry = output.load_errors[0]
        self.assertIn("Path resolution failed", error_entry.get("error", ""))
        self.assertIn("no static_name provided", error_entry.get("error", ""))
        self.assertEqual(error_entry.get("entry_index"), 0)

    async def test_load_mixed_success_failure(self):
        """Load multiple templates where some succeed and some fail."""
        input_data = {"ver": self.tpl_version_user1_v1}
        node = self._get_load_node({
            "load_entries": [
                { # Success: Static user v2
                    "path_config": {"static_name": self.tpl_name_user1, "static_version": self.tpl_version_user1_v2},
                    "output_key_name": "success1"
                },
                { # Fail: Non-existent template
                    "path_config": {"static_name": "non_existent", "static_version": "0"},
                    "output_key_name": "fail1"
                },
                { # Success: Dynamic user v1
                    "path_config": {"static_name": self.tpl_name_user1, "input_version_field_path": "ver"},
                    "output_key_name": "success2"
                },
                 { # Fail: Path resolution (bad type in input, no static fallback)
                    "path_config": {"input_name_field_path": "input_is_missing.name"},
                    "output_key_name": "fail2"
                 }
            ]
        })
        # Need static version for the last entry to fail name resolution only
        node.config.load_entries[3].path_config.static_version = "dummy_version"


        output = await node.process(input_data, runtime_config=self.runtime_config_regular)

        # Check successes
        self.assertEqual(len(output.loaded_templates), 2)
        self.assertIn("success1", output.loaded_templates)
        self.assertIn(self.tpl_version_user1_v2, output.loaded_templates["success1"].template)
        self.assertIn("success2", output.loaded_templates)
        self.assertIn(self.tpl_version_user1_v1, output.loaded_templates["success2"].template)

        # Check failures
        self.assertEqual(len(output.load_errors), 2)
        # Error 1: Not found
        self.assertEqual(output.load_errors[0].get("entry_index"), 1)
        self.assertEqual(output.load_errors[0].get("output_key"), "fail1")
        self.assertIn("not found", output.load_errors[0].get("error", ""))
        # Error 2: Resolution failure
        self.assertEqual(output.load_errors[1].get("entry_index"), 3)
        self.assertEqual(output.load_errors[1].get("output_key"), "fail2") # Output key determined before failure
        self.assertIn("Path resolution failed", output.load_errors[1].get("error", ""))




if __name__ == '__main__':
    unittest.main() 