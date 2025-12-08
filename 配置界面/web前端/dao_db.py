import pymysql
import pandas as pd

class DB:
    def __init__(self):
        self.conn = pymysql.connect(
            host="localhost",
            user="root",
            password="1234",
            database="test_db",
            charset="utf8mb4"
        )

    def query(self, sql):
        df = pd.read_sql(sql, self.conn)
        return df

    def execute(self, sql, params=None):
        cursor = self.conn.cursor()
        cursor.execute(sql, params)
        self.conn.commit()
