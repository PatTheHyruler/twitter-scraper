import tweepy
from sqlalchemy import BigInteger, Column, String, DateTime, Integer, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from database.db import Base
from ..types.int_list import IntList


class Tweet(Base):
    __tablename__ = "tweet"

    db_id = Column(Integer, primary_key=True, autoincrement=True)
    id = Column(BigInteger, index=True)
    text = Column(String(512), nullable=False)
    edit_history_tweet_ids = Column(IntList, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)
    entities = Column(String(4096), nullable=False)
    retweet_count = Column(Integer, nullable=False)
    reply_count = Column(Integer, nullable=False)
    like_count = Column(Integer, nullable=False)
    quote_count = Column(Integer, nullable=False)

    added_directly = Column(Boolean, nullable=False, default=False)
    last_fetched = Column(DateTime, nullable=False)

    author_id = Column(BigInteger, index=True, nullable=False)

    conversation_id = Column(BigInteger, index=True, nullable=False)

    replied_tweet_id = Column(BigInteger, index=True, nullable=True)

    quoted_tweet_id = Column(BigInteger, index=True, nullable=True)

    # These are currently never set
    retweeted_tweet_id = Column(BigInteger, index=True, nullable=True)

    def __init__(self, tweet: tweepy.Tweet):
        self.id = tweet.id
        self.text = tweet.text
        self.edit_history_tweet_ids = tweet.edit_history_tweet_ids
        self.created_at = tweet.created_at
        self.entities = str(tweet.entities)
        self.retweet_count = tweet.public_metrics['retweet_count']
        self.reply_count = tweet.public_metrics['reply_count']
        self.like_count = tweet.public_metrics['like_count']
        self.quote_count = tweet.public_metrics['quote_count']
        self.author_id = tweet.author_id
        self.conversation_id = tweet.conversation_id
        if tweet.referenced_tweets is not None:
            for ref_tweet in tweet.referenced_tweets:
                if ref_tweet['type'] == 'replied_to':
                    self.replied_tweet_id = int(ref_tweet['id'])
                    break
            for ref_tweet in tweet.referenced_tweets:
                if ref_tweet['type'] == 'quoted':
                    self.quoted_tweet_id = int(ref_tweet['id'])
                    break

    def __repr__(self) -> str:
        return f"Tweet({self.id} by {self.author_id})"
