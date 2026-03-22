from apscheduler.triggers.cron import CronTrigger
from loguru import logger
from utils.source_tg_utils import post_validated_messages
from utils.source_rss_utils import publish_rss_posts_on_telegram
from models.source import Source
from cruds.source import get_source_list

async def setup_rss_jobs(scheduler, client, session, api_key, api_model):
    sources = await get_source_list(
        session,
        type="rss",
        is_active=True, 
        fields=[Source.id, Source.cron]
        )
    
    await setup_jobs(
            scheduler, publish_rss_posts_on_telegram, 
            sources, "RSS_TG_", client, session, 
            api_key, api_model
        )  
    
async def setup_tg_jobs(scheduler, client, session, api_key, api_model):
    sources = await get_source_list(
        session,
        type="tg",
        is_active=True, 
        fields=[Source.id, Source.cron]
        )
    
    await setup_jobs(
            scheduler, post_validated_messages, 
            sources, "TG_TG_", client, session, 
            api_key, api_model
        )

async def setup_jobs(scheduler, handler_func, sources, prefix, client, session, api_key, api_model):
    for source in sources:
        job_id = f"{prefix}_{source.id}"
        scheduler.add_job(
            handler_func,
            trigger=CronTrigger.from_crontab(source.cron),
            args=[
                client,
                session,
                source.id,
                str(api_key), 
                str(api_model)
            ],
            id=job_id,
            replace_existing=True
        )
        logger.debug(f"Обработчик {job_id} добавлен в расписание cron: {source.cron}")