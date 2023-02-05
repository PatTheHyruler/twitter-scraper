class TweetFetchFailedException(Exception):
    def __init__(self, tweet_id: int):
        super().__init__(f"Failed to fetch Tweet with ID '{tweet_id}'!")
        self.tweet_id = tweet_id
