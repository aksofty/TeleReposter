import json
from loguru import logger
from schemas.rss_sources_schema import RssSourceListSchema, RssSourceSchema

class RssSources():
    items: list[RssSourceSchema]
    json_file: str

    @classmethod
    def init(cls, json_file: str):
        cls.json_file = json_file
        try:
            with open(cls.json_file, 'r') as f:
                data = json.load(f)
                cls.items = RssSourceListSchema(**data).sources
        except FileNotFoundError as e:
            logger.info(f"Ошибка загрузкаи файла источников RSS: {e}")
            exit(1)
        
    @classmethod
    def commit(cls):
        try:
            rss_list = RssSourceListSchema(sources = cls.items)
            with open(cls.json_file, "w", encoding="utf-8") as f:
                f.write(rss_list.model_dump_json(indent=4, by_alias=True))
        except ValueError as e:
            logger.info(f"Ошибка сохранения: {e}")

    @classmethod
    async def update_last_identifier(cls, rss_source_id: int, link: str=""):
        try:
            cls.items[rss_source_id].last_message_id = link
            cls.commit()
            logger.info(f"Обновлен last_id {link}")

        except ValueError as e:
            logger.info(f"Ошибка обновления источника: {e}")