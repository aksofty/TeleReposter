from loguru import logger
from app.utils.common_utils import is_valid_content
from app.models.source import Source


def is_valid_source_content(source: Source, text: str) -> bool:
    allowed_str = source.allowed_filter.keywords\
        if source.allowed_filter else None
    forbidden_str = source.forbidden_filter.keywords \
        if source.forbidden_filter else None
        
    if not is_valid_content(text, allowed_str, forbidden_str):
        logger.error(f"Сообщение не прошло проверку по фильтрам")
        return False
    return True