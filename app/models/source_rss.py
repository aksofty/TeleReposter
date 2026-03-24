from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from .source import Source

class SourceRss(Source):
    __tablename__ = 'sources_rss'

    id: Mapped[int] = mapped_column(ForeignKey("sources.id"), primary_key=True)

    url: Mapped[str] = mapped_column(nullable=False)
    reverse: Mapped[bool] = mapped_column(nullable=True, default=True)
    last_post_url: Mapped[str] =  mapped_column(nullable=True)

    __mapper_args__ = {
        "polymorphic_identity": "rss"
    }