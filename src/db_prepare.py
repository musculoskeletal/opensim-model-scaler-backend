from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from db_common import engine

db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()


def table(name):
    metadata = Base.metadata
    metadata.reflect(engine)

    return metadata.tables[name]


def tables():
    metadata = Base.metadata
    metadata.reflect(engine)

    return metadata.tables.keys()
