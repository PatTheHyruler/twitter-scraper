from enum import Enum, auto
from typing import Optional

import tweepy
from sqlalchemy import Column, BigInteger, String, Integer, ForeignKey, Boolean, Enum as SqlEnum
from sqlalchemy.orm import relationship

from database.db import Base


class EMediaType(Enum):
    ANIMATED_GIF = auto()
    PHOTO = auto()
    VIDEO = auto()


class Media(Base):
    __tablename__ = "media"

    id = Column(String(32), primary_key=True, autoincrement=False)
    type = Column(SqlEnum(EMediaType), nullable=False)
    url = Column(String(1024), nullable=True)
    duration_ms = Column(Integer, nullable=True)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    view_count = Column(Integer, nullable=True)
    alt_text = Column(String(1024), nullable=True)

    tweet_id = Column(BigInteger, ForeignKey("tweet.id", ondelete="CASCADE"), nullable=True)
    tweet = relationship("Tweet", back_populates="media_files", lazy="raise")

    variants = relationship("VideoVersion", back_populates="video", lazy="joined")

    downloaded = Column(Boolean, nullable=False, default=False)
    file_path = Column(String(512), nullable=True)

    @property
    def media_key(self) -> str:
        return self.id

    @media_key.setter
    def media_key(self, value: str):
        self.id = value

    def __init__(self, media: tweepy.Media, tweet_id: Optional[int] = None):
        self.media_key = media.media_key
        self.type = media.type
        self.url = media.url
        self.duration_ms = media.duration_ms
        self.width = media.width
        self.height = media.height
        if media.public_metrics is not None:
            self.view_count = media.public_metrics['view_count']
        self.alt_text = media.alt_text
        self.tweet_id = tweet_id

    def __repr__(self) -> str:
        return f"Media({self.media_key, self.type})"
