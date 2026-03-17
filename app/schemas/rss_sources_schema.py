from pydantic import BaseModel, ConfigDict, Field, HttpUrl
from schemas.base_source_schema import BaseSourceSchema

class RssSourceSchema(BaseSourceSchema):
    
    reverse: bool = Field(True)

    source: HttpUrl = Field(
        validation_alias='url',
        serialization_alias='url'
    )

    last_message_id: str = Field(
        validation_alias='last_identifier',
        serialization_alias='last_identifier'
    )

class RssSourceListSchema(BaseModel):
    rss: list[RssSourceSchema]

    model_config = ConfigDict(
        from_attributes=True, 
        str_strip_whitespace=True,
        extra='ignore')
