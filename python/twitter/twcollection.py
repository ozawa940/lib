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
        pass





    # TODO
    # This method return bool.
    # If your account use up rate limit, calling sleep method.
    def _managing_rateLimit(self):
        pass





# Using Twitter REST API
class TwitterREST(TwCollectionBase):
    # This method return tweet of targeting screen_name until 3200 tweets.
    def get_account_tweet(self, screen_name):
        pass


# Using Twitter Stream API
class TwitterStream(TwCollectionBase):


    # This method is collecting account list from TwitterStream API,
    # and range is whole Japan.
    # Duplicate of account is deleted.
    def account_list(self, count):
        pass











