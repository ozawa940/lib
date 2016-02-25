# coding:utf-8
import logging
from twitter import *

"""
    このクラスの初期化にキーリストが必要です（Twitterのコンシュマーキーを要取得）
    例：
    keylist = {
        CONSUMER_KEY = "",
        CONSUMER_SECRET = "",
        # TwitterStreamを使う場合はアクセストークンを入れてください
        ACCESS_TOKEN = "",
        ACCESS_TOKEN_SECRET = ""
    }
    本クラスはTwitterAPIの制限の関係で便宜上、OAuth2を利用します
    TwitterStreamを利用する場合は、アクセストークン必須です
        詳しくはTwitter REST APIを確認

    <本クラスでできること>
    1. 検索したツイートを指定数取得：
        ret_collect_search_tweets(target="検索ワード", limit=3000)

    2. 指定したスクリーンネームのツイートを最大3200件まで取得 ：
        ret_collect_screen_tweets(screen_name="@test")

    3. TwitterSteamを使ってツイートを取得(日本全国) ：
        ret_collect_stream_tweet(limit=300)

    各メソッドのcallに各JSONデータに対する処理を入れたコールバック関数を入れると
    処理の結果の配列を返します
    例：

    #テキストデータだけ取り出す(1. の場合)
    f = lambda json: [data["text"] for data in json["statuses"]]
    method(arg, call=f)

    #テキストデータだけ取り出す(2. と3. の場合)
    f = lambda json: json["text"]
    method(arg, call=f)


"""


class TwitterCollection:

    def __init__(self, keylist=None):
        #ログ生成
        logging.basicConfig(
            level=logging.DEBUG,
            filename="twitter_log.txt",
            filemode="w",
            format="%(asctime)s %(levelname)s %(message)s")

        if keylist is None:
            logging.error("keylist is None")
            raise Exception("Nothing keylist. check arguments")

        try:
            self.CONSUMER_KEY = keylist["CONSUMER_KEY"]
            self.CONSUMER_SECRET = keylist["CONSUMER_SECRET"]
            if "ACCESS_TOKEN" in keylist:
                self.ACCESS_TOKEN = keylist["ACCESS_TOKEN"]
                self.ACCESS_TOKEN_SECRET = keylist["ACCESS_TOKEN_SECRET"]

            self._create_bear_token()
            logging.info("create bear-token")

            #OAuth2
            self._auth_tool()

        except Exception:
            logging.error("error in initalize")
            raise

    # デフォルトは500ツイートまで
    # target = "検索対象", limit = 取得ツイート数(数値), call = コールバック関数
    def ret_collect_search_tweets(self, target, limit=500, call=None):

        if call is None:
            logging.debug("lambda is default")
            call = lambda json: json["statuses"]

        try:
            tmp_result = self.twitter.search.tweets(q=target, count=100)
            result = call(tmp_result)
            while len(result) < limit:
                try:
                    logging.debug("{0} tweets".format(len(result)))
                    next_result = tmp_result["search_metadata"]["next_results"]
                #メタデータがない場合は終了
                except KeyError:
                    logging.info("Nothing next_result.")
                    break
                #次のツイートを取得するために、メタデータからキーワードを取得
                kwargs = dict(
                    [kv.split("=") for kv in next_result[1:].split("&")])
                kwargs["q"] = target
                tmp_result = self.twitter.search.tweets(**kwargs)
                result += call(tmp_result)
            return result

        except Exception:
            logging.error("ret_collect_search_tweets error")
            raise

    #選択したスクリーンネームのツイートを取得(TwitterAPIの関係上3200件まで)  
    #screen_name = "@dfsf", call = コールバック関数
    def ret_collect_screen_tweets(self, screen_name, call=None):
        
        if call is None:
            logging.debug("lambda is default")
            call = lambda json: json

        try:
            #検索キーワード
            kwargs = {
                "screen_name" : screen_name,
                "count" : 200,
                "exclude_replies" : "false",
                "include_rts" : "false"
            }
            tmp_result = self.twitter.statuses.user_timeline(**kwargs)
            result = call(tmp_result)
            #すべて取得するまで繰り返す
            while True:
                logging.debug("{0},{1}tweets".format(screen_name, len(result)))

                #取得した終端ツイートのidを取得
                next_id = tmp_result[len(tmp_result) - 1]["id"]
                #次の検索キーワード
                kwargs["max_id"] = next_id
                tmp_result = self.twitter.statuses.user_timeline(**kwargs)

                #ツイートがこれ以上ない場合
                if len(tmp_result) == 1:
                    logging.info("no tweets of timeline")
                    break

                result += call(tmp_result)

            return result

        except Exception:
            logging.error("ret_collect_screen_tweets error")
            raise

    #TwitterStreamを使って、指定数のツイートを取得
    #デフォルトで500ツイート
    # limit = 取得ツイート数, call = コールバック関数
    def ret_collect_stream_tweet(self, limit=300, call=None):
        #OAuthに変更
        self._auth_tool(version=1)

        if call is None:
            logging.debug("lambda is default")
            call = lambda json: json

        try:
            #日本全国のツイート
            kwargs = {
                "locations" : "129.5,30.8,137.7,34.5,132.8,31.7,144.2,42.4,139.5,42.1,148.6,45.6",
            }
            result = []
            for data in self.twitter.statuses.filter(**kwargs):
                #指定数に達したら終了
                if len(result) > limit :
                    logging.info("finish twitter stream")
                    break

                #NoneTypeObject対策
                if call(data):
                    result.append(call(data))

                logging.debug("{0} tweets".format(len(result)))

            #OAuth2に戻す
            self._auth_tool(version=2)
            return result

        except Exception:
            logging.error("ret_collect_stream_tweet")
            raise

    #OAuthとOAuth2の切り替え
    # version=1がOAuth, version=2がOAuth2
    def _auth_tool(self, version=2):
        try:
            
            if version == 1:
                auth = OAuth(
                    self.ACCESS_TOKEN,
                    self.ACCESS_TOKEN_SECRET,
                    self.CONSUMER_KEY,
                    self.CONSUMER_SECRET
                    )
                self.twitter = TwitterStream(auth=auth)
                logging.info("OAuth now")
                return
            elif version == 2:
                auth = OAuth2(bearer_token=self.BEARER_TOKEN)
                self.twitter = Twitter(auth=auth)
                logging.info("OAuth2 now")
                return
            raise Exception("version is invalid : {0}".format(version))
        except Exception:
            logging.error("_auth_tool error")
            raise

    #ベアラートークン作成
    def _create_bear_token(self):
        try:

            self.BEARER_TOKEN = oauth2_dance(
                self.CONSUMER_KEY, self.CONSUMER_SECRET)

        except Exception:
            logging.error("_create_bear_token error")
            raise
