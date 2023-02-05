from enum import Enum

from sqlalchemy import Column, Integer, BigInteger, Enum as SqlEnum, Index

from database.db import Base


class ESavedTweetType(Enum):
    BOOKMARK = "bookmark",
    LIKE = "like"
    PIN = "Pin"

class SavedTweet(Base):
    __tablename__ = "saved_tweet"

    db_id = Column(Integer, primary_key=True, autoincrement=True)

    saved_type = Column(SqlEnum(ESavedTweetType), index=True, nullable=False)

    tweet_id = Column(BigInteger, index=True, nullable=False)
    user_id = Column(BigInteger, index=True, nullable=False)

    def __init__(self, tweet_id: int, user_id: int, saved_type: ESavedTweetType):
        self.tweet_id = tweet_id
        self.user_id = user_id
        self.saved_type = saved_type

    def __repr__(self):
        return f"SavedTweet({self.db_id=}, {self.tweet_id=}, {self.user_id=}, {self.saved_type=})"

Index("saved_tweet_tweet_user_index", SavedTweet.tweet_id, SavedTweet.user_id)
