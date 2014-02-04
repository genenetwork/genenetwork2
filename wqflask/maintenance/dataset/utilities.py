import MySQLdb
import re

def get_cursor():
    host = 'localhost'
    user = 'webqtl'
    passwd = 'webqtl'
    db = 'db_webqtl'
    con = MySQLdb.Connect(db=db, host=host, user=user, passwd=passwd)
    cursor = con.cursor()
    return cursor
    
def clearspaces(s, default=None):
    if s:
        s = re.sub('\s+', ' ', s)
        s = s.strip()
        return s
    else:
        return default
