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
import logging
import traceback
import time
from datetime import datetime
from twitter import *

# Using kill_timer
class TimeoutException(Exception):
    pass


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
                return
            elif version == 3:
                self.twitter = TwitterStream(auth=auth)
                return
            raise Exception("arguments error")
        except Exception:
            logging.error(traceback.format_exc())
            raise

    # TODO
    # This method is sleeping until rate limit of next reset.
    # If your account use up rate limit, calling sleep method.
    # Target is api name, and version is Oauth version.
    # Refer Oauth version into _managing_oauth.
    def _managing_rateLimit(self, target, version):
        self._managing_oauth(version=version)
        reset_time = self.twitter.application.rate_limit_status()["resources"][target[0]][target[1]]["reset"]
        diff = datetime.fromtimestamp(time.mktime(time.gmtime(reset_time))) - datetime.utcnow()
        logging.info("sleep time: {0}, time{1}".format(diff.total_seconds(), diff))
        time.sleep(diff.total_seconds())

# Using Twitter REST API
class TwitterREST(TwCollectionBase):
    # This method return tweet of targeting screen_name until 3200 tweets.
    def __init__(self, keylist):
        super(TwitterREST, self).__init__(keylist)
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
        def process_return_data(flag):
            if flag == "first":
                data = self._get_account_tweet_process(callback=callback, kwargs=kwargs)
                self.resume_data = None
                return data
            elif flag == "resume":
                data = self._get_account_tweet_process(callback=callback, resume=self.resume_data)
                self.resume_data = None
                return data
        try:
            return process_return_data("first")
        except TimeoutException as e:
            if self.resume_data is None:
                return process_return_data("first")
            else:
                return process_return_data("resume")
        except TwitterHTTPError as e:
            # error code 88 is rate limit exceeded
            if "errors" in e.response_data:
                if e.response_data["errors"][0]["code"] == 88:
                    self._managing_rateLimit()
                    if self.resume_data is None:
                        return process_return_data("first")
                    else:
                        return process_return_data("resume")
            elif "error" in e.response_data:
                return (kwargs["screen_name"] ,e.response_data)
            raise
        except Exception:
            logging.error("iregular error {0}".format(traceback.format_exc()))
            raise

    # This is decorator for killing process over time
    def kill_timer(self, limit):
        def __decorator(function):
            def hundler(signum, frame):
                logging.info("kill process")
                raise TimeoutException
            def __wrapper(*args, **kwargs):
                import signal
                signal.signal(signal.SIGALRM, hundler) 
                signal.alarm(limit)
                result = function(*args, **kwargs)
                signal.alarm(0)
                return result
            return __wrapper
        return __decorator
    # This method is process of get_account_tweet
    def _get_account_tweet_process(self, callback, kwargs=None, resume=None):
        # Using decorator
        @self.kill_timer(15)
        def user_timeline(**kwargs):
            return self.twitter.statuses.user_timeline(**kwargs)

        if resume is not None:
            logging.debug("Using resume")
            kwargs = resume[0]
            result = resume[1]
            tmp_result = user_timeline(**kwargs)
            result += callback(tmp_result)
        else:
            tmp_result = user_timeline(**kwargs)
            logging.info("initilaze {0},{1} tweets".format(kwargs["screen_name"], len(tmp_result)))
            logging.debug("kwargs:{0}".format(kwargs))
            result = callback(tmp_result)
            if len(tmp_result) <= 1:
                logging.info("no tweets of timeline")
                return result
        while True:
            logging.info("loop {0},{1} tweets".format(kwargs["screen_name"], len(result)))
            next_id = tmp_result[len(tmp_result) -1]["id"]
            kwargs["max_id"] = next_id
            # self.resume_data is for resuming
            self.resume_data = (kwargs, result)
            tmp_result = user_timeline(**kwargs)
            logging.debug("result length: {0}".format(len(tmp_result)))
            if len(tmp_result) <= 1:
                logging.info("no tweets of timeline")
                break
            result += callback(tmp_result)
        return result


# Using Twitter Stream API
class TwitterStream(TwCollectionBase):
    # This method is collecting account list from TwitterStream API,
    # and range is whole Japan.
    # Duplicate of account is deleted.
    def __init__(self, keylist):
        super(TwitterREST, self).__init__(keylist)
        self._managing_oauth(version=3)
    #TODO
    def account_list(self, count):
        now = 0
        kwargs = {
                "locations" : "129.5,30.8,137.7,34.5,132.8,31.7,144.2,42.4,139.5,42.1,148.6,45.6",
            }
        pass
        #for data in self.twitter.statuses.filter(**kwargs):
            









