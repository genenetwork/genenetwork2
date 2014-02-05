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
        
def to_dic(keys, values):
    dic = {}
    for i in range(len(keys)):
        key = keys[i]
        value = values[i]
        dic[key] = value
    return dic

def overlap(dic1, dic2):
    keys = []
    values1 = []
    values2 = []
    for key in dic1.keys():
        if key in dic2:
            value1 = dic1[key]
            value2 = dic2[key]
            if value1 and value2:
                keys.append(key)
                values1.append(value1)
                values2.append(value2)
    return keys, values1, values2
