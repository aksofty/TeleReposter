import json
from loguru import logger
from schemas.sources_schema import SourceListSchema, SourceSchema

class Sources():
    items: list[SourceSchema]
    json_file: str

    @classmethod
    def init(cls, json_file: str):
        cls.json_file = json_file
        try:
            with open(cls.json_file, 'r') as f:
                data = json.load(f)
                cls.items = SourceListSchema(**data).sources
        except FileNotFoundError as e:
            logger.info(f"Ошибка загрузки файла источников: {e}")
            exit(1)
        
    @classmethod
    def commit(cls):
        try:
            source_list = SourceListSchema(sources = cls.items)
            with open(cls.json_file, "w", encoding="utf-8") as f:
                f.write(source_list.model_dump_json(indent=4))
        except ValueError as e:
            logger.info(f"Ошибка сохранения источника: {e}")

    @classmethod
    async def update_last_message_id(cls, source_id: int, message_id: int = 0):
        last_id = cls.items[source_id].last_message_id
        try:
            if last_id < message_id:
                cls.items[source_id].last_message_id = message_id
                cls.commit()
                logger.info(f"Обновлен last_id у сообщения №{message_id}")
            else:
                logger.info(f"last_id уже больше [текущий: {last_id}]")
        except ValueError as e:
            logger.info(f"Ошибка обновления источника: {e}")