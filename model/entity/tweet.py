from typing import List, Optional

import tweepy
from sqlalchemy import BigInteger, Column, String, ForeignKey, DateTime, Integer
from sqlalchemy.orm import relationship, backref

from database.db import Base
from ..types.int_list import IntList


class Tweet(Base):
    __tablename__ = "tweet"

    id = Column(BigInteger, primary_key=True, autoincrement=False)
    text = Column(String(512), nullable=False)
    edit_history_tweet_ids = Column(IntList, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)
    entities = Column(String(4096), nullable=False)
    retweet_count = Column(Integer, nullable=False)
    reply_count = Column(Integer, nullable=False)
    like_count = Column(Integer, nullable=False)
    quote_count = Column(Integer, nullable=False)

    author_id = Column(BigInteger, ForeignKey("user.id", use_alter=True), nullable=False)
    author = relationship("User", back_populates="tweets", foreign_keys=[author_id], lazy="joined")

    conversation_id = Column(BigInteger, ForeignKey("tweet.id", ondelete="SET NULL"), nullable=True)
    conversation = relationship("Tweet", backref=backref("all_replies"), foreign_keys=[conversation_id],
                                remote_side=[id], lazy="raise")
    all_replies: List['Tweet']  # Defined above using backref

    replied_tweet_id = Column(BigInteger, ForeignKey("tweet.id", ondelete="SET NULL"), nullable=True)
    replied_tweet = relationship("Tweet", backref=backref("replies"), foreign_keys=[replied_tweet_id], remote_side=[id],
                                 lazy="raise")
    replies: List['Tweet']  # Defined above using backref

    quoted_tweet_id = Column(BigInteger, ForeignKey("tweet.id", ondelete="SET NULL"), nullable=True)
    quoted_tweet = relationship("Tweet", backref=backref("quote_tweets"), foreign_keys=[quoted_tweet_id],
                                remote_side=[id], lazy="raise")
    quote_tweets: List['Tweet']

    # These are currently never set
    retweeted_tweet_id = Column(BigInteger, ForeignKey("tweet.id", ondelete="SET NULL"), nullable=True)
    retweeted_tweet = relationship("Tweet", backref=backref("retweets"), foreign_keys=[retweeted_tweet_id],
                                   remote_side=[id], lazy="raise")
    retweets: List['Tweet']

    media_files = relationship("Media", lazy="raise")

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
