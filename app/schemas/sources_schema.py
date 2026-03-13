from pydantic import BaseModel, ConfigDict, Field, field_validator

class SourceSchema(BaseModel):
    source: str
    target: str

    limit: int = Field(default=5, ge=1, le=100)
    
    allowed: list[str] = Field(default_factory=list) 
    forbidden: list[str] = Field(default_factory=list) 

    cron: str = Field("*/60 * * * *")
    last_message_id: int =0

    model_config = ConfigDict(
        from_attributes=True, 
        str_strip_whitespace=True,
        extra='ignore'
    )

    @field_validator("allowed", "forbidden", mode="before")
    @classmethod
    def split_strings(cls,v):
        if isinstance(v, str):
            return [item.strip().lower() for item in v.split(",") if item.strip()]
        return v

class SourceListSchema(BaseModel):
    sources: list[SourceSchema]

    model_config = ConfigDict(
        from_attributes=True, 
        str_strip_whitespace=True,
        extra='ignore')
