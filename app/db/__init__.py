from db.sources import Sources
from config import Config

Sources.init(Config.DB_SOURCES_FILE)
