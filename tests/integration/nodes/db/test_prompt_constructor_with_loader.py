import unittest
import uuid
import asyncio
from typing import Dict, Any, Optional, List, Tuple, Type

# Pydantic imports
from pydantic import BaseModel, Field, create_model

# Node imports
from services.workflow_service.registry.nodes.llm.prompt import (
    PromptConstructorNode,
    PromptConstructorConfig,
    PromptTemplateDefinition,
    PromptTemplateLoadEntryConfig,
    PromptTemplatePathConfig,
    PromptConstructorOutput
)
from services.workflow_service.registry.nodes.core.dynamic_nodes import (
    DynamicSchema, BaseDynamicNode, ConstructDynamicSchema, DynamicSchemaFieldConfig
)

# Context and Service imports
from services.workflow_service.services.external_context_manager import (
    ExternalContextManager,
    get_external_context_manager_with_clients
)
from services.workflow_service.config.constants import (
    APPLICATION_CONTEXT_KEY,
    EXTERNAL_CONTEXT_MANAGER_KEY,
    OBJECT_PATH_REFERENCE_DELIMITER
)
from services.kiwi_app.workflow_app import crud as wf_crud
from services.kiwi_app.workflow_app.schemas import WorkflowRunJobCreate, PromptTemplateCreate
from db.session import get_async_db_as_manager

# Simple Mock User copied from test_prompt_template_loader.py
class MockUser(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    is_superuser: bool = False

# --- Test Class ---

class TestPromptConstructorWithLoader(unittest.IsolatedAsyncioTestCase):
    """
    Integration tests for PromptConstructorNode with dynamic template loading.

    Assumes a running database accessible via settings.
    Creates and deletes test prompt templates.
    Uses setup/teardown logic adapted from test_prompt_template_loader.py.
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
    tpl_name_user1: str = "pc_loader_user_template_org_1"
    tpl_version_user1_v1: str = "1.0"
    tpl_version_user1_v2: str = "1.1" # Add v2 for latest test
    tpl_name_sys1: str = "pc_loader_system_template_pub_1"
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
            "owner_org_id": self.test_org_id, # Use the generated org ID
        }
        self.run_job_regular = WorkflowRunJobCreate(
            **base_run_job_info, triggered_by_user_id=self.user_regular.id
        )

        self.external_context = await get_external_context_manager_with_clients()
        self.prompt_template_dao = self.external_context.daos.prompt_template

        self.runtime_config_regular = {
            "configurable": {
                APPLICATION_CONTEXT_KEY: {
                    "user": self.user_regular, # Use MockUser instance
                    "workflow_run_job": self.run_job_regular
                },
                EXTERNAL_CONTEXT_MANAGER_KEY: self.external_context
            }
        }

        # Clean templates before creating new ones
        await self._clean_test_data() # Clean first
        await self._create_test_templates()

    async def asyncTearDown(self):
        """Clean up test templates and close context."""
        await self._clean_test_data() # Clean templates only
        if self.external_context:
            await self.external_context.close()

    async def _create_test_templates(self):
        """Helper to create prompt templates needed for tests."""
        templates_to_create = [
            # Org-specific template, v1
            {
                "name": self.tpl_name_user1, "version": self.tpl_version_user1_v1,
                "template_content": f"Org template {self.tpl_name_user1} v{self.tpl_version_user1_v1}, input: {{var1}}",
                "input_variables": {"var1": "default_org_v1"},
                "owner_org_id": None,  # self.test_org_id, # Using the generated UUID directly
                "is_system_entity": True, "description": "Org v1", "is_public": True
            },
            # Org-specific template, v2 (newer)
             {
                "name": self.tpl_name_user1, "version": self.tpl_version_user1_v2,
                "template_content": f"Org template {self.tpl_name_user1} v{self.tpl_version_user1_v2}, input: {{var1}}, {{var2}}",
                "input_variables": {"var1": "default_org_v2", "var2": "new_default"},
                "owner_org_id": None,  # self.test_org_id, # Using the generated UUID directly
                "is_system_entity": True, "description": "Org v2", "is_public": True
            },
             # Public System template
            {
                "name": self.tpl_name_sys1, "version": self.tpl_version_sys1_v1,
                "template_content": f"System template {self.tpl_name_sys1} v{self.tpl_version_sys1_v1}, input: {{sys_var}}",
                "input_variables": {"sys_var": "default_sys_v1"},
                "owner_org_id": None, # System templates have no org owner
                "is_system_entity": True, "description": "System v1", "is_public": True
            },
        ]

        async with get_async_db_as_manager() as db:
            for template_data in templates_to_create:
                 # Ensure idempotency: Check and delete if exists
                owner_org_id_check = template_data.get("owner_org_id")
                existing = await self.prompt_template_dao.get_by_name_version(
                    db, name=template_data["name"], version=template_data["version"], owner_org_id=owner_org_id_check
                )
                if existing:
                    print(f"Warning: Test template {template_data['name']} v{template_data['version']} already exists, deleting before creation.")
                    await self.prompt_template_dao.remove(db, id=existing.id) # Use remove for commit handling

                try:
                    # Extract owner_org_id separately for the DAO call
                    owner_org_id_create = template_data.pop("owner_org_id", None)
                    # Create schema instance from the remaining data
                    prompt_create_schema = PromptTemplateCreate(**template_data)

                    # Call DAO create method with schema and owner_org_id
                    db_obj = await self.prompt_template_dao.create(
                        db=db,
                        obj_in=prompt_create_schema,
                        owner_org_id=owner_org_id_create
                    )
                    self.created_template_ids.append(db_obj.id)
                    print(f"Created test template {db_obj.name} v{db_obj.version} (ID: {db_obj.id}) for org '{owner_org_id_create}'")

                     # Put owner_org_id back for idempotency check on next potential run if needed
                    template_data["owner_org_id"] = owner_org_id_create

                except Exception as e:
                    print(f"Error creating test template {template_data.get('name', 'N/A')} v{template_data.get('version', 'N/A')}: {e}")
                    await db.rollback()
                    raise # Re-raise to fail the setup if template creation fails

    async def _clean_test_data(self):
        """Helper to delete prompt templates created during setup."""
        if not self.created_template_ids:
            # Fallback cleanup if IDs weren't stored
            templates_to_clean_by_name = [
                (self.tpl_name_user1, self.tpl_version_user1_v1, self.test_org_id),
                (self.tpl_name_user1, self.tpl_version_user1_v2, self.test_org_id), # Add v2
                (self.tpl_name_sys1, self.tpl_version_sys1_v1, None),
            ]
            async with get_async_db_as_manager() as db:
                 for name, version, org_id in templates_to_clean_by_name:
                      try:
                          template = await self.prompt_template_dao.get_by_name_version(db, name=name, version=version, owner_org_id=org_id)
                          if template:
                              print(f"Fallback cleanup: Deleting template {name} v{version} (ID: {template.id})")
                              await self.prompt_template_dao.remove(db, id=template.id)
                      except Exception as e:
                          print(f"Error during fallback cleanup for {name} v{version}: {e}")
                          await db.rollback()

        # Primary cleanup using stored IDs
        if self.created_template_ids:
            print(f"Cleaning up templates with IDs: {self.created_template_ids}")
            async with get_async_db_as_manager() as db:
                ids_to_delete = list(self.created_template_ids)
                self.created_template_ids = [] # Clear list before attempting deletion

                for template_id in reversed(ids_to_delete): # Delete in reverse order
                    try:
                        deleted_template = await self.prompt_template_dao.remove(db=db, id=template_id)
                        if deleted_template:
                             print(f"Deleted template ID: {template_id}")
                        else:
                             print(f"Template ID {template_id} not found for deletion (or already deleted).")
                    except Exception as e:
                        print(f"Error deleting template ID {template_id}: {e}")
                        await db.rollback()


    def _get_constructor_node(self, config: Dict[str, Any], output_fields: Dict[str, Dict[str, Any]]) -> PromptConstructorNode:
        """Instantiate PromptConstructorNode with config and dynamic output schema."""
        node_config = PromptConstructorConfig(**config)
        output_fields.pop("prompt_template_errors", None)
        output_fields.pop("load_errors", None)

        # -- Create dynamic output schema based on provided fields (similar to customer data tests) --
        dynamic_fields_def: Dict[str, Tuple[Type, Any]] = {}

        for field_name, field_conf in output_fields.items():
            type_str = field_conf.get("type", "str") # Default to string for prompts
            required = field_conf.get("required", False)
            default_value = ... if required else None

            # Map simple type strings to actual types
            type_map = {"str": str, "list": List, "dict": Dict, "any": Any}
            field_type = type_map.get(type_str.lower(), Any) # Default to Any if unknown

            # Handle Optional for non-required fields
            if not required:
                 field_type = Optional[field_type]

            # Pydantic Field configuration
            field_info = Field(default=default_value, description=f"Dynamically added output field '{field_name}'")
            dynamic_fields_def[field_name] = (field_type, field_info)

        # # Ensure 'load_errors' field definition if present in output_fields
        # if "load_errors" in output_fields:
        #      # Explicitly define type for load_errors
        #      dynamic_fields_def["load_errors"] = (Optional[List[Dict[str, Any]]], Field(default=None, description="Errors encountered during template loading"))

        # Create the dynamic model inheriting from DynamicSchema
        DynamicOutputModel = create_model(
            "TestDynamicPromptOutputSchema",
            __base__=PromptConstructorOutput,
            **dynamic_fields_def
        )
        # -------- End dynamic schema creation --------

        node = PromptConstructorNode(config=node_config, node_id="test-prompt-constructor")
        # Crucially, set the dynamically created schema class on the node instance
        node.__class__.output_schema_cls = DynamicOutputModel
        return node

    # --- Test Cases ---

    async def test_load_single_dynamic_template(self):
        """Test loading one template dynamically and constructing it."""
        output_key = "dynamic_org_prompt"
        node = self._get_constructor_node(
            config={
                "prompt_templates": {
                    output_key: { # Use output_key as the template definition ID
                        "id": output_key,
                        "variables": {"var1": "override_from_config"},
                        "template_load_config": {
                            "path_config": {
                                "static_name": self.tpl_name_user1,
                                "static_version": self.tpl_version_user1_v1
                            }
                        }
                    }
                }
            },
            output_fields={
                output_key: {"type": "str", "required": True},
                "prompt_template_errors": {"type": "list", "required": False} # Use correct error field name
            }
        )

        input_pydantic_obj = DynamicSchema()

        output_obj = await node.process(input_pydantic_obj, runtime_config=self.runtime_config_regular)
        self.assertIsInstance(output_obj, PromptConstructorOutput)

        # Validate output against the dynamic schema (already done implicitly by process return)
        output_instance = node.output_schema_cls(**output_obj.model_dump())

        # Assertions on the validated model instance
        self.assertTrue(hasattr(output_instance, output_key))
        self.assertFalse(output_instance.prompt_template_errors) # Expect no errors

        expected_prompt = f"Org template {self.tpl_name_user1} v{self.tpl_version_user1_v1}, input: override_from_config"
        self.assertEqual(getattr(output_instance, output_key), expected_prompt)


    async def test_mix_static_and_dynamic_load(self):
        """Test mixing a statically defined template and a dynamically loaded one."""
        static_key = "static_prompt"
        dynamic_key = "dynamic_sys_prompt"
        node = self._get_constructor_node(
            config={
                "prompt_templates": {
                    static_key: {
                        "id": static_key,
                        "template": "Static template with {static_var}",
                        "variables": {"static_var": "static_default"}
                    },
                    dynamic_key: {
                        "id": dynamic_key,
                        "variables": {"sys_var": "config_override_sys"},
                        "template_load_config": {
                            "path_config": {
                                "static_name": self.tpl_name_sys1,
                                "static_version": self.tpl_version_sys1_v1
                            }
                        }
                    }
                }
            },
             output_fields={
                static_key: {"type": "str", "required": True},
                dynamic_key: {"type": "str", "required": True},
                "prompt_template_errors": {"type": "list", "required": False}
            }
        )

        input_data = {"static_var": "input_override_static"}
        # Dynamically create input model for this test
        InputSchema = create_model("TestInputMix", static_var=(str, ...))
        input_pydantic_obj = InputSchema(**input_data)

        output_obj = await node.process(input_pydantic_obj, runtime_config=self.runtime_config_regular)
        self.assertIsInstance(output_obj, PromptConstructorOutput)

        # Validate output
        output_instance = node.output_schema_cls(**output_obj.model_dump())

        self.assertFalse(output_instance.prompt_template_errors)
        self.assertEqual(getattr(output_instance, static_key), "Static template with input_override_static")

        expected_dynamic_prompt = f"System template {self.tpl_name_sys1} v{self.tpl_version_sys1_v1}, input: config_override_sys"
        self.assertEqual(getattr(output_instance, dynamic_key), expected_dynamic_prompt)


    async def test_dynamic_load_with_input_override(self):
        """Test loading dynamically and overriding variables from node input."""
        output_key = "loaded_sys_prompt"
        node = self._get_constructor_node(
            config={
                "prompt_templates": {
                    output_key: {
                        "id": output_key,
                        "template_load_config": {
                             "path_config": {"static_name": self.tpl_name_sys1, "static_version": self.tpl_version_sys1_v1}
                        }
                        # No static variables defined here, relies on loaded defaults + input override
                    }
                }
            },
            output_fields={
                output_key: {"type": "str", "required": True},
                "prompt_template_errors": {"type": "list", "required": False}
            }
        )

        input_data = {"sys_var": "input_override_value"}
        InputSchema = create_model("TestInputOverride", sys_var=(str, ...))
        input_pydantic_obj = InputSchema(**input_data)

        output_obj = await node.process(input_pydantic_obj, runtime_config=self.runtime_config_regular)
        self.assertIsInstance(output_obj, PromptConstructorOutput)

        # Validate output
        output_instance = node.output_schema_cls(**output_obj.model_dump())

        self.assertFalse(output_instance.prompt_template_errors)
        expected_prompt = f"System template {self.tpl_name_sys1} v{self.tpl_version_sys1_v1}, input: input_override_value"
        self.assertEqual(getattr(output_instance, output_key), expected_prompt)


    async def test_dynamic_load_template_not_found(self):
        """Test error handling when a dynamically loaded template is not found."""
        failed_key = "failed_load_prompt"
        static_key = "static_ok_prompt"
        non_existent_name = "does_not_exist_pc"
        node = self._get_constructor_node(
            config={
                "prompt_templates": {
                    failed_key: {
                        "id": failed_key,
                        "template_load_config": {
                             "path_config": {"static_name": non_existent_name, "static_version": "1.0"}
                        }
                    },
                    static_key: {
                         "id": static_key,
                         "template": "Static works: {val}",
                         "variables": {"val": "yes"}
                    }
                }
            },
            output_fields={
                # Failed key should not be present in the output if load failed
                # static_key is required
                static_key: {"type": "str", "required": True},
                "prompt_template_errors": {"type": "list", "required": False} # Error field is optional
            }
        )

        input_pydantic_obj = DynamicSchema()

        output_obj = await node.process(input_pydantic_obj, runtime_config=self.runtime_config_regular)
        self.assertIsInstance(output_obj, PromptConstructorOutput)

        # Validate output
        output_instance = node.output_schema_cls(**output_obj.model_dump())

        # Check errors
        self.assertIsNotNone(output_instance.prompt_template_errors)
        self.assertEqual(len(output_instance.prompt_template_errors), 1)
        error_detail = output_instance.prompt_template_errors[0]
        self.assertEqual(error_detail.get("template_id"), failed_key)
        self.assertIn("not found", error_detail.get("error", ""))

        # Check failed key is NOT in output
        self.assertFalse(hasattr(output_instance, failed_key))

        # Check static key IS in output
        self.assertTrue(hasattr(output_instance, static_key))
        self.assertEqual(getattr(output_instance, static_key), "Static works: yes")


    async def test_construction_error_missing_variable(self):
        """Test error handling when a required variable is missing during construction."""
        error_key = "needs_var_prompt"
        node = self._get_constructor_node(
            config={
                "prompt_templates": {
                    error_key: {
                        "id": error_key,
                        "template": "This template requires {required_var}.",
                        "variables": {} # Missing 'required_var'
                    }
                }
            },
             output_fields={
                # Prompt construction fails, so this key won't be in output
                # error_key: {"type": "str", "required": False},
                "prompt_template_errors": {"type": "list", "required": False}
            }
        )

        input_pydantic_obj = DynamicSchema()

        output_obj = await node.process(input_pydantic_obj, runtime_config=self.runtime_config_regular)
        self.assertIsInstance(output_obj, PromptConstructorOutput)

        # Validate output
        output_instance = node.output_schema_cls(**output_obj.model_dump())

        # Check errors
        self.assertIsNotNone(output_instance.prompt_template_errors)
        self.assertEqual(len(output_instance.prompt_template_errors), 1)
        error_detail = output_instance.prompt_template_errors[0]
        self.assertEqual(error_detail.get("template_id"), error_key)
        self.assertIn("Prompt construction failed", error_detail.get("error", ""))
        self.assertIn("Missing required variables", error_detail.get("error", ""))
        self.assertIn("required_var", error_detail.get("error", ""))

        # Check error key is NOT in output
        self.assertFalse(hasattr(output_instance, error_key))

    # --- Additional Tests Inspired by test_prompt_template_loader.py ---

    async def test_load_fallback_static(self):
        """Load dynamically: uses static fallback when input path fails."""
        output_key = "fallback_static_load"
        node = self._get_constructor_node(
            config={
                "prompt_templates": {
                    output_key: {
                        "id": output_key,
                        "template_load_config": {
                            "path_config": {
                                "static_name": self.tpl_name_user1,
                                "static_version": self.tpl_version_user1_v1,
                                "input_name_field_path": "missing.path", # Will fail
                                "input_version_field_path": "missing.version" # Will fail
                            }
                        },
                        "variables": {"var1": "test_val"}
                    }
                }
            },
            output_fields={
                output_key: {"type": "str", "required": True},
                "prompt_template_errors": {"type": "list", "required": False}
            }
        )
        input_pydantic_obj = DynamicSchema()
        output_obj = await node.process(input_pydantic_obj, runtime_config=self.runtime_config_regular)
        output_instance = node.output_schema_cls(**output_obj.model_dump())

        self.assertFalse(output_instance.prompt_template_errors)
        self.assertTrue(hasattr(output_instance, output_key))
        expected_prompt = f"Org template {self.tpl_name_user1} v{self.tpl_version_user1_v1}, input: test_val"
        self.assertEqual(getattr(output_instance, output_key), expected_prompt)


    async def test_load_fallback_input_override(self):
        """Load dynamically: input path values override static values."""
        output_key = "input_override_load"
        node = self._get_constructor_node(
            config={
                "prompt_templates": {
                    output_key: {
                        "id": output_key,
                        "template_load_config": {
                            "path_config": {
                                "static_name": "wrong_name", # Should be overridden
                                "static_version": "wrong_version", # Should be overridden
                                "input_name_field_path": "prompt_details.name",
                                "input_version_field_path": "prompt_details.version"
                            }
                        },
                         "variables": {"sys_var": "test_sys_val"} # Variable for the sys template
                    }
                }
            },
            output_fields={
                output_key: {"type": "str", "required": True},
                "prompt_template_errors": {"type": "list", "required": False}
            }
        )
        input_data = {
             "prompt_details": {"name": self.tpl_name_sys1, "version": self.tpl_version_sys1_v1}
        }
        InputSchema = create_model("TestInputDetails", prompt_details=(Dict[str, str], ...))
        input_pydantic_obj = InputSchema(**input_data)

        output_obj = await node.process(input_pydantic_obj, runtime_config=self.runtime_config_regular)
        output_instance = node.output_schema_cls(**output_obj.model_dump())

        self.assertFalse(output_instance.prompt_template_errors)
        self.assertTrue(hasattr(output_instance, output_key))
        # Expects system template content with the variable override
        expected_prompt = f"System template {self.tpl_name_sys1} v{self.tpl_version_sys1_v1}, input: test_sys_val"
        self.assertEqual(getattr(output_instance, output_key), expected_prompt)

    async def test_load_by_name_only_latest(self):
        """Load dynamically using only name, expects latest version (v1.1)."""
        output_key = "load_latest_org_prompt"
        node = self._get_constructor_node(
            config={
                "prompt_templates": {
                    output_key: {
                        "id": output_key,
                        "template_load_config": {
                            "path_config": {
                                "static_name": self.tpl_name_user1
                                # No version specified
                            }
                        },
                        "variables": {"var1": "val1", "var2": "val2"} # Provide vars for v2
                    }
                }
            },
            output_fields={
                output_key: {"type": "str", "required": True},
                "prompt_template_errors": {"type": "list", "required": False}
            }
        )

        input_pydantic_obj = DynamicSchema()
        output_obj = await node.process(input_pydantic_obj, runtime_config=self.runtime_config_regular)
        output_instance = node.output_schema_cls(**output_obj.model_dump())

        self.assertFalse(output_instance.prompt_template_errors)
        self.assertTrue(hasattr(output_instance, output_key))
        # Check that content matches the LATEST version (v1.1)
        expected_prompt = f"Org template {self.tpl_name_user1} v{self.tpl_version_user1_v2}, input: val1, val2"
        self.assertEqual(getattr(output_instance, output_key), expected_prompt)

    async def test_load_path_resolution_failure_bad_type(self):
        """Test load failure when input path points to wrong data type."""
        output_key = "bad_type_load"
        node = self._get_constructor_node(
            config={
                 "prompt_templates": {
                    output_key: {
                        "id": output_key,
                        "template_load_config": {
                             "path_config": {
                                 "static_name": "fallback_name", # Provide static name
                                 "input_version_field_path": "bad_input.version", # Path to int
                                 # No static version - error expected
                             }
                        },
                        "variables": {}
                    }
                 }
            },
            output_fields={
                 output_key: {"type": "str", "required": False}, # Not required as load fails
                 "prompt_template_errors": {"type": "list", "required": False}
            }
        )
        input_data = {"bad_input": {"version": 123}} # Version is int
        InputSchema = create_model("TestBadInput", bad_input=(Dict[str, int], ...))
        input_pydantic_obj = InputSchema(**input_data)

        output_obj = await node.process(input_pydantic_obj, runtime_config=self.runtime_config_regular)
        output_instance = node.output_schema_cls(**output_obj.model_dump())

        self.assertIsNotNone(output_instance.prompt_template_errors)
        self.assertEqual(len(output_instance.prompt_template_errors), 1)
        error_detail = output_instance.prompt_template_errors[0]
        self.assertEqual(error_detail.get("template_id"), output_key)
        self.assertIn("Path resolution failed", error_detail.get("error", ""))
        self.assertIn("not a string", error_detail.get("error", ""))
        self.assertFalse(hasattr(output_instance, output_key) and bool(getattr(output_instance, output_key)))

    async def test_load_path_resolution_failure_missing_name(self):
        """Test load failure when no name source is provided."""
        output_key = "missing_name_load"
        # Config validation should catch this, but test node behavior just in case
        with self.assertRaisesRegex(ValueError, "Either static_name or input_name_field_path must be provided"):
            node = self._get_constructor_node(
                config={
                     "prompt_templates": {
                        output_key: {
                             "id": output_key,
                             "template_load_config": {
                                 "path_config": {
                                     # Missing static_name and input_name_field_path
                                     "static_version": "1.0"
                                 }
                             }
                        }
                     }
                },
                output_fields={
                     output_key: {"type": "str", "required": False},
                     "prompt_template_errors": {"type": "list", "required": False}
                }
            )
            # input_pydantic_obj = DynamicSchema()
            # output_obj = await node.process(input_pydantic_obj, runtime_config=self.runtime_config_regular)
            # # Expect error during processing or empty output with error
            # output_instance = node.output_schema_cls(**output_obj.model_dump())
            # self.assertIsNotNone(output_instance.prompt_template_errors)
            # self.assertIn("Path resolution failed", output_instance.prompt_template_errors[0].get("error", ""))


    async def test_load_context_missing_runtime_config(self):
        """Test load failure when runtime_config is missing."""
        output_key = "dynamic_load_no_context"
        node = self._get_constructor_node(
            config={
                 "prompt_templates": {
                     output_key: {
                         "id": output_key,
                         "template_load_config": {
                             "path_config": {"static_name": self.tpl_name_sys1, "static_version": "1.0"}
                         }
                     }
                 }
            },
            output_fields={
                 output_key: {"type": "str", "required": False},
                 "prompt_template_errors": {"type": "list", "required": False}
            }
        )
        input_pydantic_obj = DynamicSchema()
        output_obj = await node.process(input_pydantic_obj, runtime_config=None) # No runtime_config
        output_instance = node.output_schema_cls(**output_obj.model_dump())

        self.assertIsNotNone(output_instance.prompt_template_errors)
        self.assertEqual(len(output_instance.prompt_template_errors), 1)
        self.assertIn("Missing runtime_config", output_instance.prompt_template_errors[0].get("error", ""))
        self.assertFalse(hasattr(output_instance, output_key) and bool(getattr(output_instance, output_key)))

    async def test_load_context_missing_keys(self):
        """Test load failure when essential keys missing from runtime_config."""
        output_key = "dynamic_load_bad_context"
        node = self._get_constructor_node(
            config={
                 "prompt_templates": {
                     output_key: {
                         "id": output_key,
                         "template_load_config": {
                             "path_config": {"static_name": self.tpl_name_sys1, "static_version": "1.0"}
                         }
                     }
                 }
            },
            output_fields={
                 output_key: {"type": "str", "required": False},
                 "prompt_template_errors": {"type": "list", "required": False}
            }
        )
        bad_runtime_config = {"configurable": {}} # Missing keys
        input_pydantic_obj = DynamicSchema()
        output_obj = await node.process(input_pydantic_obj, runtime_config=bad_runtime_config)
        output_instance = node.output_schema_cls(**output_obj.model_dump())

        # print("output_instance.prompt_template_errors:", output_instance.prompt_template_errors)
        self.assertIsNotNone(output_instance.prompt_template_errors)
        # import ipdb; ipdb.set_trace()

        # self.assertEqual(len(output_instance.prompt_template_errors), 1)
        error_msg = output_instance.prompt_template_errors[0].get("error", "")
        self.assertIn("Missing required keys", error_msg)
        self.assertIn(APPLICATION_CONTEXT_KEY, error_msg)
        self.assertIn(EXTERNAL_CONTEXT_MANAGER_KEY, error_msg)
        self.assertFalse(hasattr(output_instance, output_key) and bool(getattr(output_instance, output_key)))


if __name__ == '__main__':
    unittest.main()
