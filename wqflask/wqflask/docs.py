import codecs

from flask import g
from wqflask.database import database_connection

class Docs:

    def __init__(self, entry, start_vars={}):
        results = None
        with database_connection() as conn, conn.cursor() as cursor:
            cursor.execute("SELECT Docs.title, CAST(Docs.content AS BINARY) "
                           "FROM Docs WHERE Docs.entry LIKE %s", (str(entry),))
            result = cursor.fetchone()
        self.entry = entry
        if result:
            self.title = result[0]
            self.content = result[1].decode("utf-8")
        else:
            self.title = self.entry.capitalize()
            self.content = ""
        self.editable = "false"
        # ZS: Removing option to edit to see if text still gets vandalized
        try:
            if g.user_session.record['user_email_address'] == "zachary.a.sloan@gmail.com" or g.user_session.record['user_email_address'] == "labwilliams@gmail.com":
                self.editable = "true"
        except:
            pass


def update_text(start_vars):
    content = start_vars['ckcontent']
    content = content.replace('%', '%%').replace(
        '"', '\\"').replace("'", "\\'")
    try:
        if g.user_session.record.get('user_email_address') in ["zachary.a.sloan@gmail.com", "labwilliams@gmail.com"]:
            with database_connection() as conn, conn.cursor() as cursor:
                cursor.execute("UPDATE Docs SET content=%s WHERE entry=%s",
                               (content, start_vars.get("entry_type"),))
    except:
        pass
