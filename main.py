import asyncio
from datetime import datetime
from loguru import logger
from telethon import TelegramClient
from app import LOG_PATH
from app.config import Config
from app.utils.scheduler_utils import setup_active_jobs, sync_active_jobs
from app.utils.tg_utils import tg_auth_qr
from app.models.base import Base
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.database import engine, AsyncSessionLocal
from apscheduler.triggers.cron import CronTrigger

logger.remove()
logger.add(lambda msg: print(msg, end=""), level="DEBUG")
logger.add(LOG_PATH, rotation="1 MB")

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        logger.info(f"Связь с БД установлена")


async def main():
    await init_db()

    async with AsyncSessionLocal() as session:  
        logger.info(f"Стартуем {datetime.now()}")
        client = TelegramClient(
            Config.SESSION_NAME, int(Config.CLIENT_ID), str(Config.CLIENT_TOKEN))
        
        await client.connect() 
        await tg_auth_qr(client, True)
        logger.info(f"Авторизация в Телеграм прошла успешно!")

        scheduler = AsyncIOScheduler()
        await sync_active_jobs(
            scheduler, client, session, Config.GEN_API_KEY, "head_job")
        
        scheduler.start()
        logger.info(f"Все обработчики добавлены в расписание")

        try:
            await client.run_until_disconnected() # type: ignore
        except (KeyboardInterrupt, SystemExit):
            logger.warning("Получен сигнал остановки")
        finally:
            scheduler.shutdown()
            await client.disconnect() # type: ignore
            logger.info("Сервис остановлен!")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass