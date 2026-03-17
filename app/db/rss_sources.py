import json
from loguru import logger
from schemas.rss_sources_schema import RssSourceListSchema, RssSourceSchema

class RssSources():
    rss: list[RssSourceSchema]
    json_file: str

    @classmethod
    def init(cls, json_file: str):
        cls.json_file = json_file
        try:
            with open(cls.json_file, 'r') as f:
                data = json.load(f)
                cls.rss = RssSourceListSchema(**data).rss
        except FileNotFoundError as e:
            logger.info(f"Error Source Init: {e}")
            exit(1)
        
    @classmethod
    def commit(cls):
        try:
            rss_list = RssSourceListSchema(rss = cls.rss)
            with open(cls.json_file, "w", encoding="utf-8") as f:
                f.write(rss_list.model_dump_json(indent=4, by_alias=True))
        except ValueError as e:
            logger.info(f"Commit error: {e}")

    @classmethod
    async def update_last_identifier(cls, rss_source_id: int, link: str=""):
        try:
            cls.rss[rss_source_id].last_message_id = link
            cls.commit()
            logger.info(f"Last RSS ID updated to {link}")

        except ValueError as e:
            logger.info(f"Update rss source error: {e}")