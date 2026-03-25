from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from app.models.source import Source
from app.models.source_tg import SourceTg

def try_tg_type(tg_source: Source):
    if not isinstance(tg_source, SourceTg):
        error_msg = f"Ожидался SourceTg, но получен {type(tg_source).__name__}."
        logger.error(error_msg)
        raise TypeError(error_msg)

async def update_tg_source_last_message_id(
    session: AsyncSession, 
    tg_source: Source, 
    new_last_message_id: int
):
    try_tg_type(tg_source)

    try:
        logger.debug(f"Обновление ID последнего сообщения для источника ID {tg_source.id}: {new_last_message_id}")
        tg_source.last_message_id = new_last_message_id
        await session.commit()
        await session.refresh(tg_source)
        logger.info(f"Успешно обновлен ID последнего сообщения для источника '{tg_source.name}' (ID: {tg_source.id})")
        return tg_source

    except SQLAlchemyError as e:
        await session.rollback()
        logger.error(f"Ошибка SQLAlchemy при обновлении источника ID {tg_source.id}: {str(e)}")
        raise 

    except Exception as e:
        await session.rollback()
        logger.exception(f"Непредвиденная ошибка при работе с источником ID {tg_source.id}: {str(e)}")
        raise
  
