# Module to initialize sqlalchemy with flask
import MySQLdb

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from utility.tools import SQL_URI

from flask import current_app


engine = create_engine(SQL_URI, encoding="latin1")

db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()

# Initialise the db
Base.metadata.create_all(bind=engine)


def database_connection():
    """Returns a database connection"""
    return MySQLdb.Connect(
        db=current_app.config.get("DB_NAME"),
        user=current_app.config.get("DB_USER"),
        passwd=current_app.config.get("DB_PASS"),
        host=current_app.config.get("DB_HOST"))
