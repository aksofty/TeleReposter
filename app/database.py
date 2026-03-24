from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app import DB_PATH

engine = create_async_engine(f"sqlite+aiosqlite:///{DB_PATH}", echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)
