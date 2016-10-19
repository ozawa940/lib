# coding: utf-8

"""
 First I'm poor at English.

 This class need importing sixohsix/twitter and using python version 3.
 Please install it with pip.
 Example)
  pip install twitter

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
import signal
from datetime import datetime
from twitter import *



# Using kill_timer
class TimeoutException(Exception):
    pass

# This class is abstruct class
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
        # Create BEARER_TOKEN for OAuth2
        try:
            self.BEARER_TOKEN = oauth2_dance(
                    self.CONSUMER_KEY, self.CONSUMER_SECRET)
        except:
            logging.error(traceback.format_exc())
            raise
        logging.info("complete initalize")
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
                logging.info("complete OAuth")
                return
            elif version == 2:
                auth = OAuth2(bearer_token=self.BEARER_TOKEN)
                self.twitter = Twitter(auth=auth)
                logging.info("complete OAuth2")
                return
            elif version == 3:
                self.twitter = TwitterStream(auth=auth)
                logging.info("complete TwitterStream OAuth")
                return
            raise Exception("arguments error")
        except Exception:
            logging.error(traceback.format_exc())
            raise

    # This method is sleeping until rate limit of next reset.
    # If your account use up rate limit, calling sleep method.
    # Target is api name, and version is Oauth version.
    # Refer Oauth version into _managing_oauth.
    def _managing_rateLimit(self, target, version):
        try:
            self._managing_oauth(version=version)
            reset_time = self.twitter.application.rate_limit_status()["resources"][target[0]][target[1]]["reset"]
            diff = datetime.fromtimestamp(time.mktime(time.gmtime(reset_time))) - datetime.utcnow()
            logging.info("sleep time: {0}, time{1}".format(diff.total_seconds(), diff))
            time.sleep(diff.total_seconds() + 1)
        except:
            logging.error(traceback.format_exc())
            raise


    # This is decorator for killing process over time
    def kill_timer(self, limit):
        def __decorator(function):
            def hundler(signum, frame):
                logging.info("kill process")
                raise TimeoutException
            def __wrapper(*args, **kwargs):
                signal.signal(signal.SIGALRM, hundler) 
                signal.alarm(limit)
                result = function(*args, **kwargs)
                signal.alarm(0)
                return result
            return __wrapper
        return __decorator

    # This is decorator for resume process
    # If kill_timer run, continue process
    def resume(self, target, version):
        def __decorator(function):
            def __wrapper(*args, **kwargs):
                @self.kill_timer(15)
                def main_process():
                    # function must return finish flag
                    return function(*args, **kwargs)

                flag = "first"
                # Using function for resume
                self.resume_data = None

                while True:
                    try:
                        if main_process() == "finish":
                            tmp_data = self.resume_data
                            self.resume_data = None
                            return tmp_data
                        
                    except TimeoutException as e:
                        # For using kill_timer
                        signal.alarm(0)
                        logging.debug("raise TimeoutException")
                    except TwitterHTTPError as e:
                        logging.info("raise TwitterHTTPError:{0}".format(e.response_data))
                        signal.alarm(0)
                        if "errors" in e.response_data:
                            # error cede 88 is rate limit exceeded
                            if e.response_data["errors"][0]["code"] == 88:
                                self._managing_rateLimit(target, version)
                            # error code 34 is account is not exist
                            if e.response_data["errors"][0]["code"] == 34:
                                raise
                        elif "error" in e.response_data:
                            if e.response_data["error"].find("authorized") != 1:
                                logging.info(e.response_data["error"])
                        # no defined TwitterHTTPError is raise.
                        raise
                    except Exception:
                        logging.error("iregular error {0}".format(traceback.format_exc()))
                        raise

            return __wrapper
        return __decorator




# Using Twitter REST API
class TwitterREST(TwCollectionBase):
    # This method return tweet of targeting screen_name until 3200 tweets.
    def __init__(self, keylist):
        super(TwitterREST, self).__init__(keylist)
        self._managing_oauth(version=2)

    '''
     input type
     kwargs = {
             "screen_name" : screen_name,
             "count" : 100,
             "exclude_replies" : "false",
             "include_rts" : "false"
         }

     maybe happend stackover.
     if you want to change data type, add "callback" to kwargs.
     # kwargs = {"callback" : lambda json: [data["text"] for data in json["statuses"]]}
    '''

    def get_account_tweet(self, kwargs):
        self.account_kwargs = kwargs
        callback = lambda json: [(data["user"]["screen_name"], data["text"], data["id_str"]) for data in json]
        target = ("statuses", "/statuses/user_timeline")

        @self.resume(target, version=2)
        def process():
            if self.resume_data is None:
                self.resume_data = []
            tmp_result = self.twitter.statuses.user_timeline(**self.account_kwargs)
            self.resume_data += callback(tmp_result)
            logging.debug("loop {0},{1} tweets".format(kwargs["screen_name"], len(self.resume_data)))
            logging.debug("kwargs:{0}".format(self.account_kwargs))
            logging.debug("tmp_result length {0}".format(len(tmp_result)))
            # if there are tmp_result length small than 1, return finish flag 
            if len(tmp_result) <= 1:
                logging.info("no tweets of timeline")
                return "finish"
            # update max_id of kwargs
            self.account_kwargs["max_id"] = tmp_result[-1]["id"]
            return "still"
            
        # user_timeline
        return process()



    ''' input type example
        kwargs = {
            kwargs = {
                    "q" : "serach_target",
                    "count" : 200,
                    "result_type" : recent,
                }
        }
        if you want over 200 tweets, recall this method to add "max_id" to kwargs.
        if you want to change data type, add "callback" to kwargs.
        # kwargs = {"callback" : lambda json: [data["text"] for data in json["statuses"]]}
    '''
    def get_search_tweet(self, kwargs):
        self.account_kwargs = kwargs
        target = ("statuses", "/search/tweets")
        callback = lambda json: [(data["id_str"], data["created_at"], data["text"]) for data in json["statuses"]]
        # Countermeasure for rate limit
        @self.resume(target, version=2)
        def process():
            if self.resume_data is None:
                self.resume_data = []
            tmp_result = self.twitter.search.tweets(**self.account_kwargs)
            self.resume_data += callback(tmp_result)
            logging.info("loop {0},{1} tweets".format(kwargs["q"], len(self.resume_data)))
            logging.debug("kwargs:{0}".format(self.account_kwargs))
            logging.debug("tmp_result length {0}".format(len(tmp_result["statuses"])))
            if len(tmp_result["statuses"]) <= 1:
                logging.info("no tweets of timeline")
                return "finish"
            # update max_id of kwargs
            self.account_kwargs["max_id"] = tmp_result["statuses"][-1]["id"]
            return "still"
        # search
        return process()


# Using Twitter Stream API
class TwitterStream(TwCollectionBase):
    # This method is collecting account list from TwitterStream API,
    # and range is whole Japan.
    # Duplicate of account is deleted.
    def __init__(self, keylist):
        super(TwitterREST, self).__init__(keylist)
        self._managing_oauth(version=3)

    def account_list(self, count):
        now = 0
        kwargs = {
                "locations" : "129.5,30.8,137.7,34.5,132.8,31.7,144.2,42.4,139.5,42.1,148.6,45.6",
            }
        pass
        #for data in self.twitter.statuses.filter(**kwargs):
            









