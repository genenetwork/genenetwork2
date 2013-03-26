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
                       echo="debug",
                       )

Session = scoped_session(sessionmaker(bind=Engine)) #, extension=VersionedListener()))
#Xsession = Session()

Base = declarative_base(bind=Engine)
Metadata = sa.MetaData()
Metadata.bind = Engine


class ProbeSet(Base):
    __tablename__ = 'ProbeSet'
    __table_args__ = {'autoload': True}

def main():
    for ps in page_query(Session.query(ProbeSet)):   #all()
    #for ps in probe_sets:
        print("--->", ps)
        
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