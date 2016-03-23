# coding utf-8
import pymysql.cursors
import logging


'''
このクラスの初期値にDB接続のための設定が必要です
動作環境はPython3,ライブラリのPyMySQL/PyMySQLを使っています



conect = {
    "host" : "localhost",
    "user" : "ユーザ名",
    "password" : "パスワード",
    "db" : "データベース名",
    "charset" : "utf8mb4",
    # 辞書型で返す、デフォルトはタプル
    # pymysql.cursor のインポートが必要
    "cursorclass" : pymysql.cursors.DictCursor
}



'''


class DatabaseClass:

    def __init__(self, **setting):
        #ログ生成
        logging.basicConfig(
            level=logging.DEBUG,
            filename="db_query_log.txt",
            filemode="w",
            format="%(asctime)s %(levelname)s %(message)s")

        if setting is None:
            logging.error("setting is None")
            raise Exception("Nothing setting. check argument")

        try:
            #DBコネクション
            self.connection = pymysql.connect(**setting)

        except Exception:
            logging.error("error in initalize")
            logging.debug("setting = {0}".format(setting))
            raise

    #INSERT系のクエリ
    # query(q="CREATE TABLE test (data  varchar(20)")
    # countは、繰り返し回数
    def query(self, q=None, count=1) :
        if q is None:
            logging.error("query is None")
            raise Exception("Query Error")

        with self.connection as con:
            while count > 0:
                con.execute(q)
                logging.info("query is success")
                count -= 1







