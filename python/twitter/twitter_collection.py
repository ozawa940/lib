# coding:utf-8
import logging
from twitter import *

"""
    このクラスの初期化にキーリストが必要です（Twitterのコンシュマーキーを要取得）
    例：
    keylist = {
        CONSUMER_KEY = "",
        CONSUMER_SECRET = "",
    }
    本クラスはTwitterAPIの制限の関係で便宜上、OAuth2を利用します
    よって、アクセストークンが必要な操作（自分のタイムラインの取得等）はできません
    詳しくはTwitter REST APIを確認

    <本クラスでできること>
    * 検索したツイートの、生のJSONデータを指定数取得
    * 指定したスクリーンネームのツイートの、生のJSONデータを3200件まで取得
    * TwitterSteamを使ってリアルタイムにツイートを取得

    各メソッドのcallに各JSONデータに対する処理を入れたコールバック関数を入れると
    処理の結果の配列を返します
    例：
    #テキストデータだけ取り出す
    f = lambda json: [data["text"] for data in json["statuses"]]
    method(thing1, call=f)


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
            self._create_bear_token()

            logging.info("create bear-token")

            auth = OAuth2(
                self.CONSUMER_KEY, self.CONSUMER_SECRET, self.BEARER_TOKEN)
            self.twitter = Twitter(auth=auth)
            logging.info("OAuth2 success")

        except Exception:
            logging.error("error in initalize")
            raise

    # デフォルトは500ツイートまで
    # target = "検索対象", count = 取得ツイート数(数値), call = コールバック関数
    def ret_collect_search_tweets(self, target=None, count=500, call=None):

        if target is None:
            logging.error("target is None")
            raise Exception("Nothing target. check arguments")
        if call is None:
            logging.debug("lambda is default")
            call = lambda json: json["statuses"]

        try:
            tmp_result = self.twitter.search.tweets(q=target, count=100)
            result = call(tmp_result)
            while len(result) < count:
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

    #選択したスクリーンネームのツイートをすべて取得  
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





    def _create_bear_token(self):
        try:

            self.BEARER_TOKEN = oauth2_dance(
                self.CONSUMER_KEY, self.CONSUMER_SECRET)

        except Exception:
            logging.error("_create_bear_token error")
            raise
