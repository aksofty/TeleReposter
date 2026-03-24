import os
from app.config import Config

basedir = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(basedir, 'data', Config.DB_NAME)
LOG_PATH = os.path.join(basedir, 'logs', Config.LOG_FILE)