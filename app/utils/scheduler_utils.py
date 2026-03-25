from apscheduler.triggers.cron import CronTrigger
from loguru import logger
from app.utils.source_tg_utils import post_handler_tg
from app.utils.source_rss_utils import post_handler_rss
from app.models.source import Source
from app.cruds.source import get_source_list

jobId = lambda source: f"{source.type}_{source.id}"

def get_handler_func(source_type: str):
    handler_func = None

    if source_type == "tg":
        handler_func = post_handler_tg
    elif source_type == "rss":
        handler_func = post_handler_rss

    return handler_func

async def sync_active_jobs(scheduler, client, session, api_key, head_job_name="head_job"):
    '''запуск всех активных источников и синхронизации с БД (для удаления и добавления)'''
    logger.debug(f"Синхронизация обработчиков...")
    scheduler.add_job(
        setup_active_jobs,
        trigger=CronTrigger.from_crontab("* * * * *"),
        args=[
            scheduler,
            client,
            session,
            api_key
        ],
        id=head_job_name,
        replace_existing=True
    )
    await setup_active_jobs(scheduler, client, session, api_key, head_job_name)

    
async def setup_active_jobs(scheduler, client, session, api_key, head_job_name="head_job"):
    '''Регистрация источников в расписании'''
    sources = await get_source_list(session, is_active=True, fields=[Source.id, Source.name, Source.type, Source.cron]) 
    
    # собираем множества текущих обработчиков и тех которые активны в базе на данный момент
    current_jobs = set({job.id for job in scheduler.get_jobs() if job.id != head_job_name})
    new_jobs = set({jobId(s) for s in sources})

    # ничего не делаем если нет изменений
    if current_jobs == new_jobs:
        #logger.debug(f"Изменений в списке обработчиков не найдено")
        return

    # собираем множества добавленных обработчиков и удаленных
    added_jobs = list(new_jobs - current_jobs) 
    removed_jobs = list(current_jobs - new_jobs)

    if removed_jobs:
        for job_id in removed_jobs:
            scheduler.remove_job(job_id)
            logger.info(f"Обработчик {job_id} удален из расписания")
    

    if added_jobs:
        for source in sources:
            job_id = jobId(source)
            if job_id in added_jobs:
                scheduler.add_job(
                    get_handler_func(source.type),
                    trigger=CronTrigger.from_crontab(source.cron),
                    args=[
                        client,
                        session,
                        source.id,
                        str(api_key)
                    ],
                    id=job_id,
                    replace_existing=True
                )
                logger.info(f"Новый обработчик {job_id}:{source.name} добавлен в расписание")

