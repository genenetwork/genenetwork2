from __future__ import print_function, division, absolute_import

import sys
sys.path.append("../../..")

import sqlalchemy as sa
from sqlalchemy.dialects import mysql
from sqlalchemy.orm import scoped_session, sessionmaker, relationship, backref
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.ext.declarative import declarative_base

import zach_settings as zs

Engine = sa.create_engine(zs.SQLALCHEMY_DATABASE_URI,
                       #encoding='utf-8',
                       #client_encoding='utf-8',
                       #echo="debug",
                       )

Session = scoped_session(sessionmaker(bind=Engine)) #, extension=VersionedListener()))
#Xsession = Session()

Base = declarative_base(bind=Engine)
Metadata = sa.MetaData()
Metadata.bind = Engine


class ProbeSet(Base):
    __tablename__ = 'ProbeSet'
    __table_args__ = {'autoload': True}
    
#QuickSearch = sa.Table("QuickSearch", Metadata,
#                    sa.Column('table_name', sa.String),
#                    sa.Column('the_key', sa.String),
#                    sa.Column('terms', sa.String))

class QuickSearch(Base):
    table_name = Column(String)
    the_key = Column(String)
    terms = Column(String)
    
    def __init__(self, table_name, the_key, terms):
        self.table_name = table_name
        self.the_key = the_key
        self.terms = get_unique_terms(terms)

def get_unique_terms(*args):
    if not args:
        return None
    unique = set()
    for item in args:
        #print("locals:", locals())
        if not item:
            continue
        for token in item.split():
            if token.startswith(('(','[')):
                token = token[1:]
            if token.endswith((')', ']')):
                token = token[:-1]
            if len(token) > 2:
                unique.add(token)
    print("\nUnique terms are: {}\n".format(unique))
    return " ".join(unique)


def main():
    for ps in page_query(Session.query(ProbeSet)):   #all()
        terms = get_unique_terms(ps.Name,
                         ps.Symbol,
                         ps.description)
        
        
        
def page_query(q):
    """http://stackoverflow.com/a/1217947/1175849"""
    offset = 0
    while True:
        r = False
        for elem in q.limit(1000).offset(offset):
           r = True
           yield elem
        offset += 1000
        if not r:
            break

if __name__ == "__main__":
    main()