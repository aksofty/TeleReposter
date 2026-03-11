import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    CLIENT_ID = os.getenv("CLIENT_ID")
    CLIENT_TOKEN = os.getenv("CLIENT_TOKEN")
    SESSION_NAME = os.getenv("SESSION_NAME", "app")

    @classmethod
    def validate(cls):
        if not cls.CLIENT_TOKEN or not cls.CLIENT_ID:
            raise ValueError("Missing CLIENT_TOKEN or CLIENT_ID in environment variables")