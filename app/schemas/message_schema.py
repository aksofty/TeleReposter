from typing import Any, List
from pydantic import BaseModel, Field, ValidationInfo, field_validator, model_validator

class MessageSchema(BaseModel):
    forbidden: List[str] = Field(default_factory=list)
    allowed: List[str] = Field(default_factory=list)
    content: str = Field(default="")

    @model_validator(mode='before')
    @classmethod
    def none_content(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if data.get('content') is None:
                data['content'] = ""
            if data.get('allowed') is None:
                data['allowed'] = []
            if data.get('forbidden') is None:
                data['forbidden'] = []
        return data


    
    def is_valid_content(self)->bool:
        text = self.content.strip().lower()
        if not text:
            return False
        
        if self.forbidden:
            f_list = [w.strip().lower() for w in self.forbidden if w.strip()]
            if any(word in text for word in f_list):
                return False
        
        if self.allowed:
            a_list = [w.strip().lower() for w in self.allowed if w.strip()]
            if a_list:
                return any(word in text for word in a_list)
                  
        return True