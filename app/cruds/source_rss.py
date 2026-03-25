from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from app.models.source import Source
from app.models.source_rss import SourceRss

def try_rss_type(rss_source: Source):
    if not isinstance(rss_source, SourceRss):
        error_msg = f"Ожидался SourceRss, но получен {type(rss_source).__name__}. Обновление last_post_url невозможно."
        logger.error(error_msg)
        raise TypeError(error_msg)

async def update_rss_source_last_post_url(
        session: AsyncSession, rss_source: Source, new_last_post_url: str):
    try_rss_type(rss_source)

    try:
        logger.debug(f"Обновление URL последнего поста для источника ID {rss_source.id}: {new_last_post_url}")
        rss_source.last_post_url = new_last_post_url
        await session.commit()
        await session.refresh(rss_source)
        logger.info(f"Успешно обновлен URL последнего поста для RSS-источника '{rss_source.name}' (ID: {rss_source.id})")
        return rss_source

    except SQLAlchemyError as e:
        await session.rollback()
        logger.error(f"Ошибка SQLAlchemy при обновлении RSS-источника ID {rss_source.id}: {str(e)}")
        raise 

    except Exception as e:
        await session.rollback()
        logger.exception(f"Непредвиденная ошибка при работе с RSS источником ID {rss_source.id}: {str(e)}")
        raise
  
