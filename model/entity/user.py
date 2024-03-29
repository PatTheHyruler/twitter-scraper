import tweepy
from sqlalchemy import BigInteger, Column, String, DateTime, Boolean, Integer

from database.db import Base


class User(Base):
    __tablename__ = "user"

    db_id = Column(Integer, primary_key=True, autoincrement=True)
    id = Column(BigInteger, index=True)
    name = Column(String(128), index=True, nullable=False)
    username = Column(String(64), index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)
    description = Column(String(512), nullable=True)
    entities = Column(String(4096), nullable=False)
    location = Column(String(256), nullable=True)
    profile_image_url = Column(String(1024), nullable=False)
    profile_image_downloaded = Column(Boolean, nullable=False, default=False)
    profile_image_file_path = Column(String(512), nullable=True)
    followers_count = Column(Integer, nullable=False)
    following_count = Column(Integer, nullable=False)
    tweet_count = Column(Integer, nullable=False)
    url = Column(String(1024), nullable=True)
    verified = Column(Boolean, nullable=False)
    def __init__(self, user: tweepy.User):
        self.id = user.id
        self.name = user.name
        self.username = user.username
        self.created_at = user.created_at
        self.description = user.description
        self.entities = str(user.entities)
        self.location = user.location
        self.profile_image_url = user.profile_image_url
        self.followers_count = user.public_metrics['followers_count']
        self.following_count = user.public_metrics['following_count']
        self.tweet_count = user.public_metrics['tweet_count']
        self.url = user.url
        self.verified = user.verified

    def __repr__(self) -> str:
        return f"User({self.id} {self.username})"
