from __future__ import absolute_import, print_function, division
from flask import g

class News(object):

    def __init__(self):
        sql = """
            SELECT News.id, News.date, News.details
            FROM News
			order by News.date desc
            """
        self.title = "GeneNetwork News"
        self.newslist = g.db.execute(sql).fetchall()
