import codecs

from flask import g

from utility.logger import getLogger
logger = getLogger(__name__)

class Docs(object):

    def __init__(self, entry, start_vars={}):
        sql = """
            SELECT Docs.title, CAST(Docs.content AS BINARY)
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
            self.content = result[1].decode("utf-8")


        self.editable = "false"
        # ZS: Removing option to edit to see if text still gets vandalized
        try:
            if g.user_session.record['user_email_address'] == "zachary.a.sloan@gmail.com" or g.user_session.record['user_email_address'] == "labwilliams@gmail.com":
                self.editable = "true"
        except:
            pass


def update_text(start_vars):
    content = start_vars['ckcontent']
    content = content.replace('%', '%%').replace('"', '\\"').replace("'", "\\'")

    try:
        if g.user_session.record['user_email_address'] == "zachary.a.sloan@gmail.com" or g.user_session.record['user_email_address'] == "labwilliams@gmail.com":
            sql = "UPDATE Docs SET content='{0}' WHERE entry='{1}';".format(content, start_vars['entry_type'])
            g.db.execute(sql)
    except:
        pass
