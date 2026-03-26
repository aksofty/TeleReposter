from flask_appbuilder import ModelView
from app.models.base import Base
from app.models.source_rss import SourceRss
from app.models.source_tg import SourceTg
from app.models.source import AIPrompt, Filter
from flask_appbuilder.models.sqla.interface import SQLAInterface


class BaseView(ModelView):
    list_columns = ['name', 'cron']
    label_columns = {
        "name": "Название",
        "url": "Ссылка на rss",
        "source": "Исчтоник(н.п. @durov_channel)",
        "is_active": "Активность",
        "type": "Тип парсера",
        "target": "TG Канал(куда постим)",
        "cron": "Расписание (CronString)",
        "template": "Шаблон сообщения",
        "allowed_filter": "Разрешающий фильтр",
        "forbidden_filter": "Запрещающий фильтр",
        "ai_prompt": "AI Промпт",
        "limit": "Лимит записей за один раз",
        "parse_link": "Парсить html по ссылке",
        "ai_model": "AI модель для генерации",
        "last_post_url": "Ссылка на поледнюю обработанную запись",
        "reverse": "Обратная сортировка(обычно нужно устанавливать)"
    }


class SourceRssView(BaseView):
    datamodel = SQLAInterface(SourceRss) # type: ignore
    list_columns = BaseView.list_columns + ['is_active']

    add_columns = edit_columns = [
        'is_active', 'name', 'url', 'target', 'cron', 'limit', 
        'template', 'allowed_filter', 'forbidden_filter',
        'ai_prompt', 'ai_model', 'reverse', 'parse_link', 'last_post_url'
    ]

    
class SourceTgView(BaseView):
    datamodel = SQLAInterface(SourceTg) # type: ignore
    list_columns = BaseView.list_columns + ['is_active']
    readonly_columns = ['id']

    add_columns = edit_columns = [
        'is_active', 'name', 'source', 'target', 'cron', 
        'template', 'allowed_filter', 'forbidden_filter',
        'ai_prompt', 'ai_model', 'repost', 'drop_author', 'last_message_id'
    ]



class SourceFilterView(BaseView):
    list_columns = ['name', 'keywords']
    datamodel = SQLAInterface(Filter) # type: ignore


class SourceAIPromtView(BaseView):
    list_columns = ['name', 'prompt']
    datamodel = SQLAInterface(AIPrompt) # type: ignore
