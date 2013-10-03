from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from wqflask import app

#engine = create_engine('sqlite:////tmp/test.db', convert_unicode=True)
engine = create_engine(app.config['DB_URI'], convert_unicode=True)

db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()

def init_db():
    # import all modules here that might define models so that
    # they will be registered properly on the metadata.  Otherwise
    # you will have to import them first before calling init_db()
    #import yourapplication.models
    import wqflask.model
    print("Creating all..")
    Base.metadata.create_all(bind=engine)
    print("Done creating all...")
    
init_db()