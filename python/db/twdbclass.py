# coding: utf8
import pymysql.cursors
import logging
import traceback
"""
This class is DB relation
You need to import pymysql

initialize example)

connect = {
    "host" : "localhost",
    "user" : "user name",
    "password" : "pw",
    "db" : "db name",
    "charset" : "charset",
    # Return format is dict, and default is taple
    "cursorclass" : pymysql.cursors.DictCursor
}



"""

class DatabaseClass(object):
    def __init__(self, setting):
        try:
            self.connection = pymysql.connect(**setting)
            logging.info("success insert")
        except Exception:
            logging.error("error in initalize")
            raise
    # account=(screen_name, attribute)
    def insert_account(self, account, table):
        try:
            text = "INSERT INTO {0} (screen_name, attribute) VALUES (%s, %s)".format(table)
            self._query(text, token=account)
        except Exception:
            logging.error("error insert_account")
            logging.error("query: {0}".format(account))
            logging.error(traceback.format_exc())
            raise
    # tweets=(screen_name, text, id_str)
    def insert_twdata(self, tweets, table):
        try:
            text = "INSERT INTO {0} (screen_name, text, id_str) VALUES".format(table)
            token = ()
            flag = 0
            for data in tweets:
                if flag == 1:
                    text += ","
                else:
                    flag = 1
                text += " (%s, %s, %s)"
                token += data[0], data[1], data[2]
            self._query(text, token=token)
            logging.info("success insert")
        except Exception:
            logging.error("error insert_twdata")
            logging.error(traceback.format_exc())

    def _query(self, q=None, token=None):
        try:
            if q is None:
                logging.error("query is None")
                raise Exception("Query is None")

            with self.connection as con:
                con.execute(q, token)
                logging.info("query is success")
        except Exception:
            logging.error("Error _query")
            logging.debug("{0}".format(tweets))
            raise

    def _get_query(self, q=None):
        try:
            if q is None:
                logging.error("query is None")
                raise
            with self.connection as con:
                con.execute(q)
                result = con.fetchall()

            return result
        except Exception:
            logging.error("get_query")
            raise






