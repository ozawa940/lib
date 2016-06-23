# coding: utf-8

"""
 This class need importing sixohsix/twitter and using python version 3.
 Please install it with pip.
 Example)
  pip install twitter

 This class is ADT(Abstruct Data Type) of Twitter relation.
 This class need to set keylist into **kw.

Example)

 keylist = {
        "CONSUMER_KEY" : "",
        "CONSUMER_SECRET" : "",
        "ACCESS_TOKEN" : "",
        "ACCESS_TOKEN_SECRET" : ""
     }


"""
import logging, traceback
from twitter import *

# ADT Class
class TwCollectionBase(object):

    def __init__(self, keylist):
        # _checker return args not existing dic
        _checker = lambda dic, *args: [index for index in args if not index in dic]
        _not_enough_args = _checker(keylist, 
                        "CONSUMER_KEY", 
                        "CONSUMER_SECRET", 
                        "ACCESS_TOKEN", 
                        "ACCESS_TOKEN_SECRET")

        if len(_not_enough_args) != 0:
            logging.error(traceback.format_exc())
            raise Exception(_not_enough_args + "don't exist in keylist")
        # Inserting keylist
        self.CONSUMER_KEY    = keylist["CONSUMER_KEY"]
        self.CONSUMER_SECRET = keylist["CONSUMER_SECRET"]
        self.ACCESS_TOKEN    = keylist["ACCESS_TOKEN"]
        self.ACCESS_TOKEN_SECRET = keylist["ACCESS_TOKEN_SECRET"]

        try:
            self.BEARER_TOKEN = oauth2_dance(
                    self.CONSUMER_KEY, self.CONSUMER_SECRET)
        except:
            logging.error(traceback.format_exc())
            raise
    # TODO
    # This method return Oauth
    # Version parameter means "1 = user-auth, 2 = app-auth, 3 = stream-auth"
    def _managing_oauth(self, version):
        try:
            auth = OAuth(
                    self.ACCESS_TOKEN,
                    self.ACCESS_TOKEN_SECRET,
                    self.CONSUMER_KEY,
                    self.CONSUMER_SECRET
                    )
            if version == 1:
                self.twitter = Twitter(auth=auth)
                return
            elif version == 2:
                auth = OAuth2(bearer_token=self.BEARER_TOKEN)
                self.twitter = Twitter(auth=auth)
        iregular        return
            elif version == 3:
                self.twitter = TwitterStream(auth=auth)
                return
            raise Exception("arguments error")
        except Exception:
            logging.error(traceback.format_exc())
            raise

    # TODO
    # This method return bool.
    # If your account use up rate limit, calling sleep method.
    def _managing_rateLimit(self):
        pass


# Using Twitter REST API
class TwitterREST(TwCollectionBase):
    # This method return tweet of targeting screen_name until 3200 tweets.
    def __init__(self):
        super(TwitterREST, self).__init__()
        self._managing_oauth(version=2)

    # input type
    # kwargs = {
    #         "screen_name" : screen_name,
    #         "count" : 200,
    #         "exclude_replies" : "false",
    #         "include_rts" : "false"
    #     }
    def get_account_tweet(self, kwargs):
        callback = lambda json: [(data["user"]["screen_name"], data["text"], data["id_str"]) for data in json]
        # Countermeasure for rate limit
        try:
            return self.get_account_tweet_process(callback=callback, kwargs=kwargs)
        except TwitterHTTPError as e:
            # error code 88 is rate limit exceeded
            if e.response_data["errors"][0]["code"] == 88:
                self._managing_rateLimit()
                return self.get_account_tweet_process(callback=callback, resume=self.resume_data)
            raise
        except Exception:
            logging.error("iregular error {0}".format(traceback.format_exc()))
            raise
    # This method is process of get_account_tweet
    def _get_account_tweet_process(self, callback, kwargs=None, resume=None)
        if resume is not None:
            kwargs = resume[0]
            result = resume[1]
            tmp_result = self.twitter.statuses.user_timeline(**kwargs)
            result += callback(tmp_result)
        else:
            tmp_result = self.twitter.statuses.user_timeline(**kwargs)
            result = callback(tmp_result)
        while True:
            logging.debug("{0},{1}".format(kwargs["screen_name"], len(result)))
            next_id = tmp_result[len(tmp_result) -1]["id"]
            kwargs["max_id"] = next_id
            # self.resume_data is for resuming
            self.resume_data = (kwargs, result)
            tmp_result = self.twitter.statuses.user_timeline(**kwargs)
            if len(tmp_result) == 1:
                logging.info("no tweets of timeline")
                break
            result += callback(tmp_result)
        return result


# Using Twitter Stream API
class TwitterStream(TwCollectionBase):
    # This method is collecting account list from TwitterStream API,
    # and range is whole Japan.
    # Duplicate of account is deleted.
    def __init__(self):
        super(TwitterREST, self).__init__()
        self._managing_oauth(version=3)
    #TODO
    def account_list(self, count):
        now = 0
        kwargs = {
                "locations" : "129.5,30.8,137.7,34.5,132.8,31.7,144.2,42.4,139.5,42.1,148.6,45.6",
            }
        pass
        #for data in self.twitter.statuses.filter(**kwargs):
            










