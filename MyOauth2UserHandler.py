from tweepy import OAuth2UserHandler


class MyOauth2UserHandler(OAuth2UserHandler):
    # Using https://github.com/tweepy/tweepy/pull/1806 and https://github.com/tweepy/tweepy/discussions/1912

    def refresh_token(self, refresh_token):
        return super().refresh_token(
            token_url="https://api.twitter.com/2/oauth2/token",
            refresh_token=refresh_token,
            body=f"grant_type=refresh_token&client_id={self.client_id}",
        )
