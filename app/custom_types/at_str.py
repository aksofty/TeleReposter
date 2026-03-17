from typing import Annotated, Any
from pydantic import BeforeValidator

def add_at_prefix(v: Any) -> Any:
    if isinstance(v, str) and not v.startswith('@'):
        return f'@{v}'
    return v

AtStr = Annotated[str, BeforeValidator(add_at_prefix)]