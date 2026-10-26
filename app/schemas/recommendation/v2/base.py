from pydantic import BaseModel, ConfigDict

class ResponseModelV2(BaseModel):
    model_config = ConfigDict(populate_by_name=True, str_strip_whitespace=True)