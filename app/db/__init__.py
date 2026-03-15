from db.rss_sources import RssSources
from db.sources import Sources
from config import Config

Sources.init(Config.DB_SOURCES_FILE)
RssSources.init(Config.DB_RSS_SOURCES_FILE)
