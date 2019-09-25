from __future__ import absolute_import, print_function, division

from flask import g

from utility.logger import getLogger
logger = getLogger(__name__)

class Docs(object):

    def __init__(self, entry, start_vars={}):
        sql = """
            SELECT Docs.title, Docs.content
            FROM Docs
            WHERE Docs.entry LIKE %s
            """
        result = g.db.execute(sql, str(entry)).fetchone()
        self.entry = entry
        if result == None:
            self.title = self.entry.capitalize()
            self.content = ""
        else:
            self.title = result[0]
            self.content = result[1]

        if 'edit' in start_vars and start_vars['edit'] == "true":
            self.editable = "true"
        else:
            self.editable = "false"

def update_text(start_vars):
    content = start_vars['ckcontent']
    content = content.replace('%', '%%').replace('"', '\\"').replace("'", "\\'")

    sql = "UPDATE Docs SET content='{0}' WHERE entry='{1}';".format(content, start_vars['entry_type'])

    g.db.execute(sql)