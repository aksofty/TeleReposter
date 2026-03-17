from typing import Annotated, Any
from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, field_validator

from custom_types.at_str import AtStr

class BaseSourceSchema(BaseModel):
    active: bool = Field(True)

    source: str
    target: AtStr

    ai_prompt: str = Field("")

    header: str = Field("")
    footer: str = Field("")

    limit: int = Field(default=5, ge=1, le=100)
    
    allowed: list[str] = Field(default_factory=list) 
    forbidden: list[str] = Field(default_factory=list) 

    cron: str = Field("*/60 * * * *")
    
    last_message_id: int = Field(0)

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