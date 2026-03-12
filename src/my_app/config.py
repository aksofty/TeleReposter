import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    CLIENT_ID = os.getenv("CLIENT_ID", 0)
    CLIENT_TOKEN = os.getenv("CLIENT_TOKEN", "")
    SESSION_NAME = os.getenv("SESSION_NAME", "app")

    @classmethod
    def validate(cls):
        if len(cls.CLIENT_TOKEN)==0 or int(cls.CLIENT_ID)==0:
            raise ValueError("Missing CLIENT_TOKEN or CLIENT_ID in environment variables")