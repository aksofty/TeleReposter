import os

from flask import current_app, request
from flask_appbuilder import BaseView, ModelView, expose, has_access
from app.models.base import Base
from app.models.source_rss import SourceRss
from app.models.source_tg import SourceTg
from app.models.source import AIPrompt, Filter
from flask_appbuilder.models.sqla.interface import SQLAInterface


class BaseBDView(ModelView):
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


class SourceRssView(BaseBDView):
    datamodel = SQLAInterface(SourceRss) # type: ignore
    list_columns = BaseBDView.list_columns + ['is_active']

    add_columns = edit_columns = [
        'is_active', 'name', 'url', 'target', 'cron', 'limit', 
        'template', 'allowed_filter', 'forbidden_filter',
        'ai_prompt', 'ai_model', 'reverse', 'parse_link', 'last_post_url'
    ]

    
class SourceTgView(BaseBDView):
    datamodel = SQLAInterface(SourceTg) # type: ignore
    list_columns = BaseBDView.list_columns + ['is_active']
    readonly_columns = ['id']

    add_columns = edit_columns = [
        'is_active', 'name', 'source', 'target', 'cron', 
        'template', 'allowed_filter', 'forbidden_filter',
        'ai_prompt', 'ai_model', 'repost', 'drop_author', 'last_message_id'
    ]



class SourceFilterView(BaseBDView):
    list_columns = ['name', 'keywords']
    datamodel = SQLAInterface(Filter) # type: ignore


class SourceAIPromtView(BaseBDView):
    list_columns = ['name', 'prompt']
    datamodel = SQLAInterface(AIPrompt) # type: ignore

class LogView(BaseView):
    default_vew = 'show_logs'

    @expose('/show/')
    @has_access
    def show_logs(self):
        log_file = "app/logs/all_logs.log"
        if os.path.exists(log_file):
            with open(log_file, "r") as f:
                content = f.readlines()[-200:]
            content = "\n".join(content)
        else:
            content = "file doesnt exist"

        if request.args.get('raw'):
            return content
        
        return self.render_template('logs.html', content=content.strip())
    
