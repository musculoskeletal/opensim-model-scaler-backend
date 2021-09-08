from sqlalchemy.orm import sessionmaker

from db_prepare import Base
from db_common import engine


def init_db():
    import db_tables

    Base.metadata.create_all(bind=engine)

    session = sessionmaker(bind=engine)()
    v = db_tables.Version(db_tables.__version__)
    session.add(v)
    session.commit()
    # print('Initialised database: ', engine.table_names())
