import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

class Config:
    CLIENT_ID = os.getenv("CLIENT_ID", 0)
    CLIENT_TOKEN = os.getenv("CLIENT_TOKEN", "")
    SESSION_NAME = os.getenv("SESSION_NAME", "app")
    DB_SOURCES_FILE = os.getenv("DB_SOURCES_FILE", "db_sources.json")
    LOG_FILE = os.getenv("LOG_FILE", "all_logs.log")

    @classmethod
    def validate(cls):
        if len(cls.CLIENT_TOKEN)==0 or int(cls.CLIENT_ID)==0:
            raise ValueError("Missing CLIENT_TOKEN or CLIENT_ID in environment variables")