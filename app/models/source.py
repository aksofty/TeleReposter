from typing import List, Optional
from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base

class Source(Base):

    __tablename__ = 'sources'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    name: Mapped[str] = mapped_column()
    type: Mapped[str] = mapped_column(String(50))

    target: Mapped[str] = mapped_column()
    cron: Mapped[str] = mapped_column(default="* 1 * * *") 
    template: Mapped[str] = mapped_column(nullable=True)

    allowed_filter_id: Mapped[int] = mapped_column(ForeignKey("filters.id"), nullable=True)
    forbidden_filter_id: Mapped[int] = mapped_column(ForeignKey("filters.id"), nullable=True)

    limit: Mapped[int] = mapped_column(default=1)
    ai_prompt_id: Mapped[int] = mapped_column(ForeignKey("ai_prompts.id"), nullable=True)

    allowed_filter: Mapped["Filter"] = relationship("Filter", foreign_keys=[allowed_filter_id], lazy="selectin")
    forbidden_filter: Mapped["Filter"] = relationship("Filter", foreign_keys=[forbidden_filter_id], lazy="selectin")
    ai_prompt: Mapped["AIPrompt"] = relationship("AIPrompt", foreign_keys=[ai_prompt_id], lazy="selectin")

    __mapper_args__ = {
        "polymorphic_on": "type",
        "polymorphic_identity": "base"
    }


class Filter(Base):
    __tablename__ = 'filters'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    keywords: Mapped[str] = mapped_column(nullable=False)

    def __repr__(self):
        return f"Filter(id={self.id}, name='{self.name}', keywords='{self.keywords}')"
    

class AIPrompt(Base):
    __tablename__ = 'ai_prompts'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    prompt: Mapped[str] = mapped_column(nullable=False)

    def __repr__(self):
        return f"Prompt(id={self.id}, name='{self.name}', prompt='{self.prompt}')"
