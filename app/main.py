import asyncio
from datetime import datetime
import sys
from loguru import logger
from telethon import TelegramClient
from config import Config
from db.sources import Sources
from db.rss_sources import RssSources
from schemas.sources_schema import SourceSchema
from utils.rss_utils import post_new_rss_messages
from utils.tg_utils import repost_validated_messages, tg_auth_qr
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger.remove()
#logger.add(sys.stderr, level="DEBUG", colorize=True)
logger.add(lambda msg: print(msg, end=""), level="DEBUG")
logger.add(Config.LOG_FILE, rotation="1 MB")

async def main():
    logger.info(f"Starting app at {datetime.now()}")
    
    client = TelegramClient(
        Config.SESSION_NAME,
        int(Config.CLIENT_ID),
        str(Config.CLIENT_TOKEN)
    )

    await client.connect() 
    await tg_auth_qr(client, True)
    logger.info(f"Logged in to Telegram!")

    scheduler = AsyncIOScheduler()

    for source_id, source in enumerate(Sources.items):
        if not source.active:
            continue

        job_id = f"repost_{source_id}"
        scheduler.add_job(
            repost_validated_messages, 
            trigger=CronTrigger.from_crontab(source.cron),
            args = [
                client, 
                source_id, 
                str(Config.GEN_API_KEY), 
                str(Config.GEN_API_MODEL)
            ],
            id=job_id,
            replace_existing=True
        )          
        logger.debug(f"Job {job_id} scheduled with cron {source.cron}")

    for source_id, rss_source in enumerate(RssSources.rss):
        if not rss_source.active:
            continue

        job_id = f"repost_rss_{source_id}"
        scheduler.add_job(
            post_new_rss_messages, 
            trigger=CronTrigger.from_crontab(rss_source.cron),
            args = [
                client, 
                source_id,
                str(Config.GEN_API_KEY), 
                str(Config.GEN_API_MODEL)
            ],
            id=job_id,
            replace_existing=True
        )          
        logger.debug(f"Job rss {job_id} scheduled with cron {rss_source.cron}")
        
    scheduler.start()
    logger.info(f"Scheduler started")

    try:
        await client.run_until_disconnected() # type: ignore
    except (KeyboardInterrupt, SystemExit):
        logger.warning("Shutdown signal received")
    finally:
        scheduler.shutdown()
        await client.disconnect() # type: ignore
        logger.info("Service stopped")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass