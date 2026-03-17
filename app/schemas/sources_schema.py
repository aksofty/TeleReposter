from pydantic import BaseModel, ConfigDict, Field, field_validator
from custom_types.at_str import AtStr
from schemas.base_source_schema import BaseSourceSchema

class SourceSchema(BaseSourceSchema):
    source: AtStr
    drop_author: bool = Field(False)


class SourceListSchema(BaseModel):
    sources: list[SourceSchema]

    model_config = ConfigDict(
        from_attributes=True, 
        str_strip_whitespace=True,
        extra='ignore')
