from apscheduler.triggers.cron import CronTrigger
from loguru import logger

def setup_jobs(scheduler, sources, handler_func, prefix, client, api_key, api_model):
    """
    Добавляет задачи в планировщик. 
    Все внешние зависимости (конфиг, клиент) передаются явно.
    """
    for source_id, source in enumerate(sources):
        if not source.active:
            continue

        job_id = f"{prefix}_{source_id}"
        scheduler.add_job(
            handler_func,
            trigger=CronTrigger.from_crontab(source.cron),
            args=[
                client,
                source_id,
                str(api_key), 
                str(api_model)
            ],
            id=job_id,
            replace_existing=True
        )
        logger.debug(f"Обработчик {job_id} добавлен в расписание cron: {source.cron}")