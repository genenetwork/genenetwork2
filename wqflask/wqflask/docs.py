from __future__ import absolute_import, print_function, division

from flask import g

class Docs(object):

    def __init__(self, entry):
        sql = """
            SELECT Docs.title, Docs.content
            FROM Docs
            WHERE Docs.entry LIKE %s
            """
        result = g.db.execute(sql, str(entry)).fetchone()
        self.entry = entry
        self.title = result[0]
        self.content = result[1]
