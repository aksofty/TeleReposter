import asyncio
from datetime import datetime
from loguru import logger
from telethon import TelegramClient
from config import Config
from db.sources import Sources
from schemas.sources_schema import SourceSchema
from utils.tg_function import repost_new_messages, tg_auth_qr
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger.add(Config.LOG_FILE, rotation="1 MB") 

async def main():
    print(datetime.now())
    
    client = TelegramClient(
        Config.SESSION_NAME, int(Config.CLIENT_ID), str(Config.CLIENT_TOKEN))
    await client.connect() 
    await tg_auth_qr(client)
    logger.info(f"Logged in!")

    scheduler = AsyncIOScheduler()
    for source_id, source in enumerate(Sources.items):
        '''scheduler.add_job(
            repost_new_messages, 
            'interval', 
            seconds=source.update_period,
            args = [client, source_id])'''
        scheduler.add_job(
            repost_new_messages, 
            trigger=CronTrigger.from_crontab(source.cron),
            args = [client, source_id])          
    scheduler.start()

    run = client.run_until_disconnected()
    if run is not None:
         await run

if __name__ == '__main__':
    asyncio.run(main())