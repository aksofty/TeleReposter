import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    CLIENT_ID = int(os.getenv("CLIENT_ID", 0))
    CLIENT_TOKEN = os.getenv("CLIENT_TOKEN", "")
    SESSION_NAME = os.getenv("SESSION_NAME", "app_session")

    DB_NAME=os.getenv("DB_NAME", "db.sqlite3")
    LOG_FILE = os.getenv("LOG_FILE", "all_logs.log")

    GEN_API_KEY=os.getenv("GEN_API_KEY", "")
    GEN_API_MODEL=os.getenv("GEN_API_MODEL", "")

    ADMIN_NAME=os.getenv("ADMIN_NAME", "admin")
    ADMIN_PASS=os.getenv("ADMIN_PASS", "123456")
    ADMIN_SECRET=os.getenv("ADMIN_SECRET", "my_secret_key")

    @classmethod
    def validate(cls):
        if not cls.CLIENT_TOKEN or int(cls.CLIENT_ID)==0:
            raise ValueError("Missing CLIENT_TOKEN or CLIENT_ID in environment variables")

Config.validate()