from pydantic import BaseModel
from pydantic.config import ConfigDict

class ResponseBaseModel(BaseModel):
    model_config = ConfigDict(extra='allow')

    @classmethod
    def parse_response(cls, data: dict):
        return cls.model_construct(**data)