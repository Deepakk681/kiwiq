"""
Dynamic input and output nodes for workflows.

This module contains the implementation of dynamic input and output nodes,
which serve as the entry and exit points for workflows. Their schemas are
dynamically created based on the graph connections.
"""
from typing import Any, Dict, List, Optional, Type, ClassVar, cast, Callable, Union, get_origin, get_args
from typing_extensions import Annotated
from pydantic import Field, create_model, field_validator, BaseModel
from datetime import datetime, date
from enum import Enum


from abc import ABC, abstractmethod

# from workflow_service.registry.schemas.base import BaseModel


class DynamicSchema(BaseModel, ABC):
    """
    A dynamic schema that can be created at runtime.
    
    This is a placeholder class that will be replaced with dynamically
    created schemas based on the graph connections.
    """
    IS_DYNAMIC_SCHEMA: ClassVar[bool] = True


PRIMITIVE_TYPES = {
    "str": str,
    "int": int, 
    "float": float,
    "bool": bool,
    "bytes": bytes,
    "datetime": datetime,
    "date": date,
}

ALLOWED_FIELD_TYPES: Dict[str, Type] = PRIMITIVE_TYPES | {
        "any": Any
}

DEFAULT_NOT_SPECIFIED_VALUE = "@@@NOT_SPECIFIED_VALUE@@@"

class DynamicSchemaFieldConfig(BaseModel):
    """
    A configuration for a field in a dynamic schema.
    """
    # class vars constants
    TYPE_MAPPING: ClassVar[Dict[str, Type]] = ALLOWED_FIELD_TYPES
    PRIMITIVE_TYPES: ClassVar[Dict[str, Type]] = PRIMITIVE_TYPES

    # Instance fields
    type: str = Field(..., description="The type of the field")
    required: Optional[bool] = Field(None, description="Whether the field is required")
    default: Optional[Union[str, int, float, bool, bytes, datetime, date]] = Field(DEFAULT_NOT_SPECIFIED_VALUE, description="The default value of the field, only specified if type is primitive, not list / dict.")
    description: Optional[str] = Field(None, description="The description of the field")
    items_type: Optional[str] = Field(None, description="The type of the items in a list field")
    keys_type: Optional[str] = Field(None, description="The type of the keys in a dict field")
    values_type: Optional[str] = Field(None, description="The type of the values in a dict field")
    values_items_type: Optional[str] = Field(None, description="The type of the items in a list field")
    # Enum support
    enum_values: Optional[List[Union[str, int, float, bool, bytes, datetime, date]]] = Field(None, description="List of allowed values for an enum field")
    multi_select: Optional[bool] = Field(False, description="Whether multiple values can be selected from the enum (creates a List[Enum] type)")


class ConstructDynamicSchema(BaseModel):
    """
    A schema for constructing a dynamic schema from a JSON configuration.

    IMPORTANT NOTE For LLM structured outputs (especially for OPENAI): 
    While creating dynamic schemas for LLM structured outputs, all fields provided must be marked as required!
    https://platform.openai.com/docs/guides/structured-outputs/supported-schemas?api-mode=chat

    OpenAI also doesn't support schemas with fields defined as Dict --> Dict[str, Any] or Dict[str, str] etc.
    Eg invalid definitions for OpenAI:
    # "metadata": DynamicSchemaFieldConfig(type="dict",  required=True, description="Metadata of the response"),
    # "metadata": DynamicSchemaFieldConfig(type="dict",  required=True, description="Metadata of the response", keys_type="str", values_type="str"),
    NOTE: Anthropic supports Dict[str, Any] and Dict[str, str] etc.

    NOTE: Gemini supports Dict, but schema adherence is not guaranteed! It routinely outputs other non-dict objects to dict fields.
    List and other fields seem to work; To maye Dict work, a nested schema with well defined objects may be required!

    
    This class allows building dynamic schemas with fields of primitive types,
    as well as non-nested List and Dict types. The field configurations are specified
    using DynamicSchemaFieldConfig objects, which define properties like type, default values,
    and whether fields are required or optional.
    
    Example:
    ```python
    schema_config = ConstructDynamicSchema(fields={
        "name": DynamicSchemaFieldConfig(type="str", required=True),
        "age": DynamicSchemaFieldConfig(type="int", default=0),
        "tags": DynamicSchemaFieldConfig(type="list", items_type="str"),
        "metadata": DynamicSchemaFieldConfig(type="dict", keys_type="str", values_type="int"),
        "user_lists": DynamicSchemaFieldConfig(
            type="dict", 
            keys_type="str", 
            values_type="list", 
            values_items_type="str"
        )
    })
    ```
    """
    schema_name: Optional[str] = Field("DynamicSchema", description="The name of the schema to be created for the field")
    schema_description: Optional[str] = Field("", description="The description of the schema to be created for the field")
    fields: Dict[str, DynamicSchemaFieldConfig] = Field(
        ...,
        description="Dictionary of field definitions. Keys are field names, values are field configurations."
    )
    
    # Type mapping from string representation to actual Python types
    
    
    @field_validator('fields')
    def validate_fields(cls, field_defs: Dict[str, DynamicSchemaFieldConfig]) -> Dict[str, DynamicSchemaFieldConfig]:
        """
        Validate that the field definitions are properly structured.
        
        Args:
            field_defs: Dictionary of field definitions
            
        Returns:
            The validated field definitions
            
        Raises:
            ValueError: If field definitions are invalid
        """
        for field_name, field_def in field_defs.items():
            # Every field must have a type
            field_type = field_def.type
            
            # Validate enum type
            if field_type == "enum":
                if not field_def.enum_values:
                    raise ValueError(f"Enum field '{field_name}' is missing 'enum_values' property")
                
                if not all(isinstance(val, tuple(DynamicSchemaFieldConfig.PRIMITIVE_TYPES.values())) for val in field_def.enum_values):
                    raise ValueError(f"Enum values in field '{field_name}' must be of primitive types: {list(DynamicSchemaFieldConfig.TYPE_MAPPING.keys())}")
                
                # Check for duplicate values
                if len(field_def.enum_values) != len(set(str(val) for val in field_def.enum_values)):
                    raise ValueError(f"Enum field '{field_name}' contains duplicate values")
                
                continue
                
            # Validate primitive types
            elif field_type in DynamicSchemaFieldConfig.TYPE_MAPPING:
                continue
                
            # Validate list type
            elif field_type == "list":
                if field_def.items_type is None:
                    continue
                #     raise ValueError(f"List field '{field_name}' is missing 'items_type' property")

                    
                items_type = field_def.items_type
                if items_type not in DynamicSchemaFieldConfig.TYPE_MAPPING:
                    raise ValueError(f"Invalid items_type '{items_type}' for list field '{field_name}'. Must be a primitive type.")
                
            # Validate dict type
            elif field_type == "dict":
                # if not field_def.keys_type:
                #     raise ValueError(f"Dict field '{field_name}' is missing 'keys_type' property")
                # if not field_def.values_type:
                #     raise ValueError(f"Dict field '{field_name}' is missing 'values_type' property")
                    
                keys_type = field_def.keys_type
                if not ((keys_type is None) or (keys_type in DynamicSchemaFieldConfig.TYPE_MAPPING)):
                    raise ValueError(f"Invalid keys_type '{keys_type}' for dict field '{field_name}'. Must be a primitive type.")
                    
                values_type = field_def.values_type
                
                # Values can be primitive types
                if values_type in DynamicSchemaFieldConfig.TYPE_MAPPING or values_type is None:
                    continue
                    
                # Or values can be lists of primitives
                elif values_type == "list":
                    if field_def.values_items_type is None:
                        continue
                        # raise ValueError(f"Dict field '{field_name}' with values_type 'list' is missing 'values_items_type' property")
                        
                    values_items_type = field_def.values_items_type
                    if values_items_type not in DynamicSchemaFieldConfig.TYPE_MAPPING:
                        raise ValueError(f"Invalid values_items_type '{values_items_type}' for dict field '{field_name}'. Must be a primitive type.")
                else:
                    raise ValueError(f"Invalid values_type '{values_type}' for dict field '{field_name}'. Must be a primitive type or 'list'.")
            else:
                raise ValueError(f"Invalid field type '{field_type}' for field '{field_name}'. Must be one of {list(DynamicSchemaFieldConfig.TYPE_MAPPING.keys()) + ['list', 'dict', 'enum']}")
                
        return field_defs
    
    def build_schema(self, schema_name: str = None) -> Type[BaseModel]:
        """
        Build a dynamic schema from the configuration.
        
        Args:
            schema_name: Name for the created schema class
            
        Returns:
            Type[BaseModel]: A new BaseModel subclass with the defined fields
        """
        field_definitions = {}
        created_enums = {}

        # def get_python_primitive_type(field_type: str) -> Type[Any]:
        #     if field_type in DynamicSchemaFieldConfig.TYPE_MAPPING:
        #         return DynamicSchemaFieldConfig.TYPE_MAPPING[field_type]
        #     else:
        #         raise ValueError(f"Invalid field type '{field_type}' for field '{field_name}'. Must be a primitive type.")
        
        def get_list_python_type(items_type: Optional[str]) -> Type[Any]:
            if items_type in DynamicSchemaFieldConfig.TYPE_MAPPING:
                return List[DynamicSchemaFieldConfig.TYPE_MAPPING[items_type]]
            elif items_type == None:
                return List[Any]
            else:
                raise ValueError(f"Invalid items_type '{items_type}' for list field '{field_name}'. Must be a primitive type.")
        
        def get_dict_type(keys_type: Optional[str], values_type: Optional[str] = None, values_items_type: Optional[str] = None) -> Type[Any]:
            assert keys_type is None or keys_type in DynamicSchemaFieldConfig.TYPE_MAPPING, f"Invalid keys_type '{keys_type}' for dict field '{field_name}'. Must be a primitive type."
            keys_type = DynamicSchemaFieldConfig.TYPE_MAPPING[keys_type] if keys_type is not None else Any
            if values_type in DynamicSchemaFieldConfig.TYPE_MAPPING:
                values_type = DynamicSchemaFieldConfig.TYPE_MAPPING[values_type]
            elif values_type == "list":
                # Dict with list values
                values_items_type = field_def.values_items_type
                values_type = get_list_python_type(values_items_type)
            elif values_type == None:
                values_type = Any
            else:
                raise ValueError(f"Invalid values_type '{values_type}' for dict field '{field_name}'. Must be a primitive type or 'list'.")
            return Dict[keys_type, values_type]
        
        
        for field_name, field_def in self.fields.items():
            field_type = field_def.type
            required = field_def.required if field_def.required is not None else True
            default = field_def.default
            if not required:
                if default == DEFAULT_NOT_SPECIFIED_VALUE:
                    default = None
            description = field_def.description or f"Field {field_name}"
            
            # Create the appropriate field type
            if field_type == "enum":
                # Create a dynamic enum type if not already created
                enum_name = f"{schema_name}_{field_name}_Enum"
                if enum_name not in created_enums:
                    # Create an enum with string keys and the actual values
                    enum_dict = {f"VALUE_{i}": val for i, val in enumerate(field_def.enum_values)}
                    
                    # Create the enum class
                    created_enums[enum_name] = Enum(enum_name, enum_dict)
                
                enum_class = created_enums[enum_name]
                
                # Check if this is a multi-select enum
                multi_select = field_def.multi_select or False
                
                if multi_select:
                    # Multi-select enum - creates a List[Enum] type
                    python_type = List[enum_class]
                    
                else:
                    # Single-select enum
                    python_type = enum_class
                # Convert default values to enum members if provided
                kwargs = {"default": default} if not required else {}
                if default != DEFAULT_NOT_SPECIFIED_VALUE and default is not None:
                    kwargs["default"] = default
                else:
                    if multi_select:
                        kwargs["default"] = []
                
                field_definitions[field_name] = (
                    Optional[python_type] if not required else python_type,
                    Field(description=description, **kwargs)
                )
                continue
                
            elif field_type in DynamicSchemaFieldConfig.TYPE_MAPPING:
                # Primitive type
                python_type = DynamicSchemaFieldConfig.TYPE_MAPPING[field_type]
                kwargs = {}
                if default != DEFAULT_NOT_SPECIFIED_VALUE:
                    kwargs["default"] = default
                
            elif field_type == "list":
                
                # List type
                items_type = field_def.items_type
                python_type = get_list_python_type(items_type)
                
                kwargs = {}
                if default != DEFAULT_NOT_SPECIFIED_VALUE:
                    kwargs["default"] = default or []
                
            elif field_type == "dict":
                python_type = get_dict_type(field_def.keys_type, field_def.values_type, field_def.values_items_type)
                kwargs = {}
                if default != DEFAULT_NOT_SPECIFIED_VALUE:
                    kwargs["default"] = default or {}
            
            # NOTE: enum fields are handled above!
            if field_type != "enum":
                field_definitions[field_name] = (
                    Optional[python_type] if not required else python_type,
                    Field(description=description, **kwargs)
                )
        
        # Create and return the dynamic schema class
        return create_model(
            schema_name or self.schema_name,
            __base__=DynamicSchema,
            __doc__=self.schema_description,
            **field_definitions
        )

if __name__ == "__main__":
    schema_config = ConstructDynamicSchema(fields={
        "name": DynamicSchemaFieldConfig(type="str", required=True),
        "age": DynamicSchemaFieldConfig(type="int", default=0),
        "tags": DynamicSchemaFieldConfig(type="list", items_type="str"),
        "metadata": DynamicSchemaFieldConfig(type="dict", keys_type="str", values_type="int"),
        "user_lists": DynamicSchemaFieldConfig(
            type="dict", 
            keys_type="str", 
            values_type="list", 
            values_items_type="str"
        )
    })
    print(schema_config.model_dump_json(indent=2))
