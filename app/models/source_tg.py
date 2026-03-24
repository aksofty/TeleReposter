from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from .source import Source

class SourceTg(Source):
    __tablename__ = 'sources_tg'

    id: Mapped[int] = mapped_column(ForeignKey("sources.id"), primary_key=True)

    source: Mapped[str] = mapped_column(nullable=False)
    drop_author: Mapped[bool] =  mapped_column(nullable=True, default=False)
    repost: Mapped[bool] =  mapped_column(nullable=True, default=True)
    last_message_id: Mapped[int] =  mapped_column(nullable=True)

    __mapper_args__ = {
        "polymorphic_identity": "tg"
    }