from pydantic import BaseModel, ValidationInfo, field_validator, ValidationError

class MessageSchema(BaseModel):
    forbidden: str
    allowed: str
    content: str

    @field_validator('content')
    @classmethod
    def check_filter_in(cls, v: str, info: ValidationInfo):

        content_lower = v.lower()

        f_words = info.data.get('forbidden', '')
        if len(f_words)>0:
            forbidden_list = [s.strip() for s in f_words.split(',')]
            for word in forbidden_list:
                if word in content_lower:
                    raise ValueError(f"Текст содержит запрещенное слово: \"{word}\"")

        a_words = info.data.get('allowed', '')
        if len(a_words)>0:
            allowed_list = [s.strip() for s in a_words.split(',')]
            for word in allowed_list:
                if word in content_lower:
                    return

        raise ValueError(f"Текст не содержит содержит нужных слов")