import datetime

from sqlalchemy import Column, BigInteger, Integer, Index, Boolean, DateTime

from database.db import Base


class QueuedTweet(Base):
    __tablename__ = "queued_tweet"

    db_id = Column(Integer, primary_key=True, autoincrement=True)
    tweet_id = Column(BigInteger, index=True, nullable=False)
    priority = Column(Integer, index=True, nullable=False, default=0)
    tweet_failed = Column(Boolean, index=True, nullable=False, default=False)
    replies_failed = Column(Boolean, index=True, nullable=False, default=False)
    added = Column(DateTime, index=True, nullable=True)

    def __repr__(self):
        return f"QueuedTweet({self.db_id=}, {self.tweet_id=}, {self.priority=})"

    def __init__(self, tweet_id: int, priority: int = 0):
        self.tweet_id = tweet_id
        self.priority = priority
        self.added = datetime.datetime.utcnow()

Index("queued_tweet_tweet_id_priority_index", QueuedTweet.tweet_id, QueuedTweet.priority)
