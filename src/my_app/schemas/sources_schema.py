from pydantic import BaseModel, ConfigDict

class SourceSchema(BaseModel):
    source: str
    target: str
    limit: int
    update_period: int
    last_message_id: int
    filter_in: str
    filter_out: str

    model_config = ConfigDict(from_attributes=True)

class SourceListSchema(BaseModel):
    sources: list[SourceSchema]
