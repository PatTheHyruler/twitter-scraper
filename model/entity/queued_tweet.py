from sqlalchemy import Column, BigInteger, Integer, Index

from database.db import Base


class QueuedTweet(Base):
    __tablename__ = "queued_tweet"

    db_id = Column(Integer, primary_key=True, autoincrement=True)
    tweet_id = Column(BigInteger, index=True, nullable=False)
    priority = Column(Integer, index=True, nullable=False, default=0)

    def __repr__(self):
        return f"QueuedTweet({self.db_id=}, {self.tweet_id=}, {self.priority=})"

    def __init__(self, tweet_id: int, priority: int = 0):
        self.tweet_id = tweet_id
        self.priority = priority

Index("queued_tweet_tweet_id_priority_index", QueuedTweet.tweet_id, QueuedTweet.priority)
