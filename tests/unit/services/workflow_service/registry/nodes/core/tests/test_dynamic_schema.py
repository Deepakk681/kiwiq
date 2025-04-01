"""
Tests for the ConstructDynamicSchema class.

This module contains tests for the ConstructDynamicSchema class, which is responsible
for building dynamic schemas from configurations using DynamicSchemaFieldConfig objects.

Tests cover:
1. Creating schemas with primitive types
2. Creating schemas with list fields
3. Creating schemas with dict fields
4. Creating schemas with dict fields containing list values
5. Schema validation
6. Optional fields and default values
7. Error handling for invalid configurations
"""

import unittest
from typing import Dict, List, Optional, Any
from datetime import datetime, date

from pydantic import ValidationError

from workflow_service.registry.nodes.core.dynamic_nodes import (
    ConstructDynamicSchema, 
    DynamicSchema,
    DynamicSchemaFieldConfig
)
from workflow_service.registry.schemas.base import BaseSchema


class TestConstructDynamicSchema(unittest.TestCase):
    """Test cases for the ConstructDynamicSchema class."""

    def test_create_schema_with_primitive_types(self):
        """Test creating a schema with primitive types."""
        # Define a schema with all supported primitive types
        schema_config = ConstructDynamicSchema(fields={
            "string_field": DynamicSchemaFieldConfig(type="str", required=True),
            "int_field": DynamicSchemaFieldConfig(type="int", default=0),
            "float_field": DynamicSchemaFieldConfig(type="float", required=False),
            "bool_field": DynamicSchemaFieldConfig(type="bool", default=False),
            "bytes_field": DynamicSchemaFieldConfig(type="bytes"),
            "date_field": DynamicSchemaFieldConfig(type="date"),
            "datetime_field": DynamicSchemaFieldConfig(type="datetime")
        })

        # Build the schema
        DynamicTestSchema = schema_config.build_schema("TestSchema")

        # Verify schema structure
        self.assertTrue(issubclass(DynamicTestSchema, BaseSchema))
        
        # Create a valid instance
        instance = DynamicTestSchema(
            string_field="test",
            float_field=3.14,
            bytes_field=b"test",
            date_field=date(2023, 1, 1),
            datetime_field=datetime(2023, 1, 1, 12, 0, 0)
        )
        
        # Verify field values
        self.assertEqual(instance.string_field, "test")
        self.assertEqual(instance.int_field, 0)  # Default value
        self.assertEqual(instance.float_field, 3.14)
        self.assertEqual(instance.bool_field, False)  # Default value
        self.assertEqual(instance.bytes_field, b"test")
        self.assertEqual(instance.date_field, date(2023, 1, 1))
        self.assertEqual(instance.datetime_field, datetime(2023, 1, 1, 12, 0, 0))

        # Test required field validation
        with self.assertRaises(ValueError):
            DynamicTestSchema(
                int_field=42,
                float_field=3.14,
                bytes_field=b"test"
                # Missing required string_field
            )
        # raise Exception("test")

    def test_create_schema_with_list_fields(self):
        """Test creating a schema with list fields."""
        # Define a schema with list fields
        schema_config = ConstructDynamicSchema(fields={
            "str_list": DynamicSchemaFieldConfig(type="list", items_type="str"),
            "int_list": DynamicSchemaFieldConfig(type="list", items_type="int", required=False),
            "float_list": DynamicSchemaFieldConfig(type="list", items_type="float", required=False),
            "bool_list": DynamicSchemaFieldConfig(type="list", items_type="bool", required=False)
        })

        # Build the schema
        DynamicListSchema = schema_config.build_schema("ListSchema")
        
        # Create a valid instance
        instance = DynamicListSchema(
            str_list=["a", "b", "c"],
            float_list=[1.1, 2.2, 3.3]
        )
        
        # Verify field values
        self.assertEqual(instance.str_list, ["a", "b", "c"])
        self.assertEqual(instance.int_list, [])  # Default value
        self.assertEqual(instance.float_list, [1.1, 2.2, 3.3])
        self.assertEqual(instance.bool_list, [])  # Default value

        # Test list item type validation
        with self.assertRaises(ValueError):
            DynamicListSchema(
                str_list=["a", "b", 3],  # Type error: int instead of str
                float_list=[1.1, 2.2, 3.3]
            )

    def test_create_schema_with_dict_fields(self):
        """Test creating a schema with dictionary fields."""
        # Define a schema with dict fields
        schema_config = ConstructDynamicSchema(fields={
            "str_dict": DynamicSchemaFieldConfig(type="dict", keys_type="str", values_type="str"),
            "int_dict": DynamicSchemaFieldConfig(
                type="dict", 
                keys_type="str", 
                values_type="int", 
                required=False,
                # default={"a": 1, "b": 2}
            ),
            "float_dict": DynamicSchemaFieldConfig(
                type="dict", 
                keys_type="str", 
                values_type="float", 
                required=False
            )
        })

        # Build the schema
        DynamicDictSchema = schema_config.build_schema("DictSchema")
        
        # Create a valid instance
        instance = DynamicDictSchema(
            str_dict={"key1": "value1", "key2": "value2"},
            float_dict={"x": 1.1, "y": 2.2}
        )
        
        # Verify field values
        self.assertEqual(instance.str_dict, {"key1": "value1", "key2": "value2"})
        self.assertEqual(instance.int_dict, {})  # Default value
        self.assertEqual(instance.float_dict, {"x": 1.1, "y": 2.2})

        # Test dict value type validation
        with self.assertRaises(ValueError):
            DynamicDictSchema(
                str_dict={"key1": "value1", "key2": 2},  # Type error: int instead of str
                float_dict={"x": 1.1, "y": 2.2}
            )

    def test_create_schema_with_dict_list_fields(self):
        """Test creating a schema with dictionary fields containing list values."""
        # Define a schema with dict fields containing list values
        schema_config = ConstructDynamicSchema(fields={
            "str_lists": DynamicSchemaFieldConfig(
                type="dict", 
                keys_type="str", 
                values_type="list", 
                values_items_type="str"
            ),
            "int_lists": DynamicSchemaFieldConfig(
                type="dict", 
                keys_type="str", 
                values_type="list", 
                values_items_type="int",
                required=False
                # default={"a": [1, 2], "b": [3, 4]}
            )
        })

        # Build the schema
        DynamicDictListSchema = schema_config.build_schema("DictListSchema")
        
        # Create a valid instance
        instance = DynamicDictListSchema(
            str_lists={
                "colors": ["red", "green", "blue"],
                "fruits": ["apple", "banana"]
            }
        )
        
        # Verify field values
        self.assertEqual(instance.str_lists["colors"], ["red", "green", "blue"])
        self.assertEqual(instance.str_lists["fruits"], ["apple", "banana"])
        self.assertEqual(instance.int_lists, {})  # Default value

        # Test nested value type validation
        with self.assertRaises(ValueError):
            DynamicDictListSchema(
                str_lists={
                    "colors": ["red", "green", 3],  # Type error: int instead of str
                    "fruits": ["apple", "banana"]
                }
            )

    def test_schema_field_validation(self):
        """Test validation of field definitions during schema creation."""
        # Missing type
        with self.assertRaises(ValueError):
            # Need to use Pydantic model directly with incorrect values
            # since validation will happen before our validate_fields
            DynamicSchemaFieldConfig(type=None)
            
        # Invalid type
        with self.assertRaises(ValueError) as cm:
            ConstructDynamicSchema(fields={
                "name": DynamicSchemaFieldConfig(type="invalid_type")
            })
        self.assertIn("Invalid field type", str(cm.exception))

        # List missing items_type
        # with self.assertRaises(ValueError) as cm:
        schema_spec = ConstructDynamicSchema(fields={
            "items": DynamicSchemaFieldConfig(type="list")
        })
        schema = schema_spec.build_schema("ListSchema")
        self.assertIs(schema.model_fields["items"].annotation, List[Any])
            # self.assertIn("missing 'items_type' property", str(cm.exception))
        

        # List with invalid items_type
        with self.assertRaises(ValueError) as cm:
            ConstructDynamicSchema(fields={
                "items": DynamicSchemaFieldConfig(type="list", items_type="invalid_type")
            })
        self.assertIn("Invalid items_type", str(cm.exception))

        # Dict missing keys_type
        schema_spec = ConstructDynamicSchema(fields={
            "dict_field": DynamicSchemaFieldConfig(type="dict", values_type="str")
        })
        schema = schema_spec.build_schema("DictSchema")
        self.assertIs(schema.model_fields["dict_field"].annotation, Dict[Any, str])

        # raise Exception("STOP")

        # Dict missing values_type
        schema_spec = ConstructDynamicSchema(fields={
            "dict_field": DynamicSchemaFieldConfig(type="dict", keys_type="str")
        })
        schema = schema_spec.build_schema("DictSchema")
        self.assertIs(schema.model_fields["dict_field"].annotation, Dict[str, Any])

        # Dict with invalid keys_type
        with self.assertRaises(ValueError) as cm:
            ConstructDynamicSchema(fields={
                "dict_field": DynamicSchemaFieldConfig(
                    type="dict", 
                    keys_type="invalid_type", 
                    values_type="str"
                )
            })
        self.assertIn("Invalid keys_type", str(cm.exception))

        # Dict with invalid values_type
        with self.assertRaises(ValueError) as cm:
            ConstructDynamicSchema(fields={
                "dict_field": DynamicSchemaFieldConfig(
                    type="dict", 
                    keys_type="str", 
                    values_type="invalid_type"
                )
            })
        self.assertIn("Invalid values_type", str(cm.exception))

        # Dict with list values missing values_items_type
        schema_spec = ConstructDynamicSchema(fields={
            "dict_field": DynamicSchemaFieldConfig(type="dict", keys_type="str", values_type="list")
        })
        schema = schema_spec.build_schema("DictSchema")
        self.assertIs(schema.model_fields["dict_field"].annotation, Dict[str, List[Any]])

        # Dict with list values with invalid values_items_type
        with self.assertRaises(ValueError) as cm:
            ConstructDynamicSchema(fields={
                "dict_field": DynamicSchemaFieldConfig(
                    type="dict", 
                    keys_type="str", 
                    values_type="list",
                    values_items_type="invalid_type"
                )
            })
        self.assertIn("Invalid values_items_type", str(cm.exception))

    def test_optional_fields_and_defaults(self):
        """Test handling of optional fields and default values."""
        # Define a schema with optional fields and defaults
        schema_config = ConstructDynamicSchema(fields={
            "required_field": DynamicSchemaFieldConfig(type="str", required=True),
            "optional_field": DynamicSchemaFieldConfig(type="str", required=False),
            "default_field": DynamicSchemaFieldConfig(type="int", default=42),
            "optional_with_default": DynamicSchemaFieldConfig(
                type="float", 
                required=False, 
                default=3.14
            ),
            "list_with_default": DynamicSchemaFieldConfig(
                type="list", 
                items_type="str", 
                required=False, 
                # default=["a", "b"]
            ),
            "dict_with_default": DynamicSchemaFieldConfig(
                type="dict", 
                keys_type="str", 
                values_type="int", 
                required=False,
                # default={"x": 1, "y": 2}
            )
        })

        # Build the schema
        DefaultsSchema = schema_config.build_schema("DefaultsSchema")
        
        # Test with minimal required fields
        instance1 = DefaultsSchema(required_field="test")
        
        # Verify defaults are applied
        self.assertEqual(instance1.required_field, "test")
        self.assertIsNone(instance1.optional_field)
        self.assertEqual(instance1.default_field, 42)
        self.assertEqual(instance1.optional_with_default, 3.14)
        self.assertEqual(instance1.list_with_default, [])
        self.assertEqual(instance1.dict_with_default, {})
        
        # Test overriding defaults
        instance2 = DefaultsSchema(
            required_field="test",
            optional_field="provided",
            default_field=100,
            optional_with_default=2.71,
            list_with_default=["c", "d"],
            dict_with_default={"z": 3}
        )
        
        # Verify overridden values
        self.assertEqual(instance2.optional_field, "provided")
        self.assertEqual(instance2.default_field, 100)
        self.assertEqual(instance2.optional_with_default, 2.71)
        self.assertEqual(instance2.list_with_default, ["c", "d"])
        self.assertEqual(instance2.dict_with_default, {"z": 3})

    def test_complex_schema_example(self):
        """Test creating and using a more complex schema with multiple field types."""
        # Define a complex schema
        schema_config = ConstructDynamicSchema(fields={
            "name": DynamicSchemaFieldConfig(
                type="str", 
                required=True,
                description="User's full name"
            ),
            "age": DynamicSchemaFieldConfig(
                type="int", 
                default=0,
                description="User's age in years"
            ),
            "is_active": DynamicSchemaFieldConfig(
                type="bool", 
                default=True,
                description="Whether the user account is active"
            ),
            "tags": DynamicSchemaFieldConfig(
                type="list", 
                items_type="str", 
                default=None,
                description="Tags associated with the user"
            ),
            "scores": DynamicSchemaFieldConfig(
                type="dict", 
                keys_type="str", 
                values_type="float", 
                default=None,
                description="Subject scores for the user"
            ),
            "preferences": DynamicSchemaFieldConfig(
                type="dict", 
                keys_type="str", 
                values_type="list", 
                values_items_type="str",
                default=None,
                description="User preferences by category"
            )
        })

        # Build the schema
        UserSchema = schema_config.build_schema("UserSchema")
        
        # Create a complete instance
        user = UserSchema(
            name="John Doe",
            age=30,
            is_active=True,
            tags=["user", "premium"],
            scores={"math": 95.5, "science": 87.0},
            preferences={
                "colors": ["blue", "green"],
                "foods": ["pizza", "sushi"]
            }
        )
        
        # Verify the complex instance
        self.assertEqual(user.name, "John Doe")
        self.assertEqual(user.age, 30)
        self.assertTrue(user.is_active)
        self.assertEqual(user.tags, ["user", "premium"])
        self.assertEqual(user.scores, {"math": 95.5, "science": 87.0})
        self.assertEqual(user.preferences["colors"], ["blue", "green"])
        self.assertEqual(user.preferences["foods"], ["pizza", "sushi"])
        
        # Verify JSON serialization works
        user_dict = user.model_dump()
        self.assertIn("name", user_dict)
        self.assertIn("preferences", user_dict)
        self.assertEqual(user_dict["preferences"]["colors"], ["blue", "green"])

    def test_create_schema_with_single_select_enum(self):
        """Test creating a schema with a single-select enum field."""
        # Define a schema with single-select enum field
        schema_config = ConstructDynamicSchema(fields={
            "status": DynamicSchemaFieldConfig(
                type="enum",
                enum_values=["pending", "active", "completed", 1, True],
                default="pending"
            )
        })

        # Build the schema
        EnumSchema = schema_config.build_schema("EnumSchema")
        
        # Create a valid instance
        instance = EnumSchema(status="active")
        
        # Verify field value
        self.assertEqual(instance.status.value, "active")
        
        # Test enum validation
        with self.assertRaises(ValueError):
            EnumSchema(status="invalid_status")  # Not in allowed values

    def test_create_schema_with_multi_select_enum(self):
        """Test creating a schema with a multi-select enum field."""
        # Define a schema with multi-select enum field
        schema_config = ConstructDynamicSchema(fields={
            "tags": DynamicSchemaFieldConfig(
                type="enum",
                enum_values=["work", "personal", "urgent", 1, True],
                multi_select=True,
                # default=[]
            )
        })

        # Build the schema
        MultiEnumSchema = schema_config.build_schema("MultiEnumSchema")
        
        # Create a valid instance
        instance = MultiEnumSchema(tags=["work", "urgent", True])
        
        # Verify field values - should be a list of enum members
        tag_values = [tag.value for tag in instance.tags]
        self.assertEqual(len(tag_values), 3)
        self.assertIn("work", tag_values)
        self.assertIn("urgent", tag_values)
        self.assertIn(True, tag_values)
        
        # Test enum validation
        with self.assertRaises(ValueError):
            MultiEnumSchema(tags=["work", "invalid_tag"])  # "invalid_tag" not in allowed values


if __name__ == "__main__":
    unittest.main() 