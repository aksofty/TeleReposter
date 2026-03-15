from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

class RssSourceSchema(BaseModel):
    url: HttpUrl
    target: str

    header: str = Field("")
    footer: str = Field("")

    limit: int = Field(default=5, ge=1, le=100)
    
    allowed: list[str] = Field(default_factory=list) 
    forbidden: list[str] = Field(default_factory=list) 

    cron: str = Field("*/60 * * * *")

    reverse: bool = Field(True)

    last_identifier: str = Field("")


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

class RssSourceListSchema(BaseModel):
    rss: list[RssSourceSchema]

    model_config = ConfigDict(
        from_attributes=True, 
        str_strip_whitespace=True,
        extra='ignore')
