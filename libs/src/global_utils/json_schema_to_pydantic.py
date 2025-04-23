import json
import logging
import types
from typing import Type, Union
from typing import *
import uuid
from pydantic import *
from datamodel_code_generator import DataModelType, PythonVersion
from datamodel_code_generator.model import get_data_model_types
from datamodel_code_generator.parser.jsonschema import JsonSchemaParser
from pydantic import BaseModel
from datamodel_code_generator.parser.base import (
    title_to_class_name
)


logger = logging.getLogger(__name__)

def convert_json_schema_to_pydantic_in_memory(
    json_schema: Union[str, dict]
) -> Type[BaseModel]:
    """
    1) Parses the JSON Schema into Pydantic model code
    2) exec()s that code into a fresh module namespace
    3) Finds and returns the root BaseModel subclass
    """
    if isinstance(json_schema, str):
        json_schema_object = json.loads(json_schema)
        json_schema_str = json_schema
    else:
        json_schema_object = json_schema
        json_schema_str = json.dumps(json_schema)

    main_model_name = json_schema_object.get("title", json_schema_object.get("name", None))
    if not main_model_name:
        raise ValueError("JSON Schema must have a 'title' or 'name' property")
    if "title" not in json_schema_object:
        json_schema_object.pop("name")
        json_schema_object["title"] = main_model_name

    # 1) Prepare the parser
    data_model_types = get_data_model_types(
        DataModelType.PydanticV2BaseModel,
        target_python_version=PythonVersion.PY_311
    )
    parser = JsonSchemaParser(
        json_schema_str,
        data_model_type=data_model_types.data_model,
        data_model_root_type=data_model_types.root_model,
        data_model_field_type=data_model_types.field_model,
        data_type_manager_type=data_model_types.data_type_manager,
        dump_resolve_reference_action=data_model_types.dump_resolve_reference_action,
        # use_title_as_name=True
    )

    # print(main_model_name)
    if not parser.model_resolver.validate_name(main_model_name):
        main_model_name = title_to_class_name(main_model_name)
    # print(main_model_name)

    # 2) Generate the model code (as one big string)
    try:
        model_code = parser.parse()
    except Exception as e:
        logger.error(f"Error parsing JSON Schema: {e}", exc_info=True)
        return None

    # print(model_code)

    # # 3) Exec it into a brand‑new module
    # module = types.ModuleType("generated_models")
    # exec(model_code, module.__dict__)
    code_obj = compile(model_code, "<string>", "exec")
    exec(code_obj)
    # import ipdb; ipdb.set_trace()
    model = locals().get(main_model_name)
    model.model_rebuild()
    # print(model)
    # import ipdb; ipdb.set_trace()

    # # 4) Discover all BaseModel subclasses defined there
    # all_models = [
    #     obj for obj in module.__dict__.values()
    #     if isinstance(obj, type)
    #     and issubclass(obj, BaseModel)
    #     and obj is not BaseModel
    # ]

    # # 5) Pick out the “root” model:
    # #    - If your schema had a "title", its class will have that name.
    # #    - Otherwise the generator uses class name "Model".
    # model = next(m for m in all_models if m.__name__ == main_model_name)

    # model.model_rebuild()

    # # 6) (Optional) Show its schema and/or parse sample JSON
    # print(f"\n--- Generated Pydantic model ({model.__name__}) schema: ---")
    # print(json.dumps(model.model_json_schema(), indent=2))

    # if sample_json:
    #     instance = model.parse_raw(sample_json)
    #     print(f"\n--- Parsed instance of {model.__name__}: ---")
    #     print(instance)
    #     print("\nAs JSON:")
    #     print(instance.model_dump_json(indent=2))

    return model


if __name__ == "__main__":
    # Example schema (no "title" ⇒ root class ⇒ Model)
    json_schema = """
    {
      "title": "Address",
      "type": "object",
      "properties": {
        "number":      {"type": "number"},
        "street_name": {"type": "string"},
        "street_type": {
          "type": "string",
          "enum": ["Street", "Avenue", "Boulevard"]
        }
      }
    }
    """
    json_schema_obj = json.loads(json_schema)

    json_schema = {'properties': {'answer': {'description': 'The answer.', 'title': 'Answer', 'type': 'string'}, 'confidence': {'anyOf': [{'type': 'number'}, {'type': 'null'}], 'default': None, 'description': 'Confidence score (0.0-1.0).', 'title': 'Confidence'}}, 'required': ['answer'], 'title': 'OpenAIDynamicSchema', 'type': 'object'}

    schema_name = f"test_db_schema_{uuid.uuid4()}"
    schema_version = "1.0"
    json_schema = {
        "title": schema_name,
        "description": "Schema fetched from DB for testing.",
        "type": "object",
        "properties": {
            "person_name": {"type": "string", "description": "Name of the person"},
            "person_age": {"type": "integer", "description": "Age of the person"}
        },
        "required": ["person_name", "person_age"]
    }

    model = convert_json_schema_to_pydantic_in_memory(json_schema)
    print(model)
    # import ipdb; ipdb.set_trace()


    # sample_json = json.dumps({
    #     "number": 123,
    #     "street_name": "Main",
    #     "street_type": "Boulevard"
    # })

    # # Generates `StreetType` Enum + `Model` class,
    # # then parses the sample into a `Model` instance.
    # model = convert_json_schema_to_pydantic_in_memory(json_schema)
    # model2 = convert_json_schema_to_pydantic_in_memory(json_schema_obj)
    # instance = model.parse_raw(sample_json)
    # instance2 = model2.parse_raw(sample_json)
    # print("model", instance)
    # print("model2", instance2)
