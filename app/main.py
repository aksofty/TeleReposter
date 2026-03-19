import asyncio
from datetime import datetime
from loguru import logger
from telethon import TelegramClient
from config import Config
from db.sources import Sources
from db.rss_sources import RssSources
from schemas.sources_schema import SourceSchema
from utils.scheduler_utils import setup_jobs
from utils.tg_utils import post_validated_messages, post_validated_rss_messages, tg_auth_qr
from apscheduler.schedulers.asyncio import AsyncIOScheduler

logger.remove()
logger.add(lambda msg: print(msg, end=""), level="DEBUG")
logger.add(Config.LOG_FILE, rotation="1 MB")

async def main():
    logger.info(f"Стартуем {datetime.now()}")
    
    client = TelegramClient(
        Config.SESSION_NAME, int(Config.CLIENT_ID), str(Config.CLIENT_TOKEN))

    await client.connect() 
    await tg_auth_qr(client, True)
    logger.info(f"Авторизация в Телеграм прошла успешно!")

    scheduler = AsyncIOScheduler()

    setup_jobs(
        scheduler, Sources.items, post_validated_messages, 
        "tg->tg", client, Config.GEN_API_KEY, Config.GEN_API_MODEL
    )
    setup_jobs(
        scheduler, RssSources.items, post_validated_rss_messages, 
        "rss->tg", client, Config.GEN_API_KEY, Config.GEN_API_MODEL
    )   
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