from pydantic import BaseModel, ConfigDict

class SourceSchema(BaseModel):
    source: str
    target: str
    limit: int
    allowed: str
    forbidden: str
    cron: str
    last_message_id: int

    model_config = ConfigDict(
        from_attributes=True, 
        str_strip_whitespace=True,
        extra='ignore')

class SourceListSchema(BaseModel):
    sources: list[SourceSchema]

    model_config = ConfigDict(
        from_attributes=True, 
        str_strip_whitespace=True,
        extra='ignore')
