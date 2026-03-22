from typing import Optional

from loguru import logger
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload, with_polymorphic
from sqlalchemy.ext.asyncio import AsyncSession
from models.source_rss import SourceRss
from models.source_tg import SourceTg
from models.source import Source

async def get_source_list(
        session: AsyncSession, type: str = "rss", is_active: bool | None = None, fields: list | None = None):
    stmt = select(*fields) if fields else select(Source) 
    stmt = stmt.where(Source.type == type)

    if is_active is not None:
        stmt = stmt.where(Source.is_active == is_active)

    result = await session.execute(stmt)

    if fields:
        return result.mappings().all()
    
    return result.scalars().all()


async def get_source(session: AsyncSession, id: int):
    entity = with_polymorphic(Source, [SourceRss, SourceTg])
    query = select(entity).where(entity.id == id)
    result = await session.execute(query)
    
    return result.scalar_one_or_none()