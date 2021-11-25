from sqlalchemy.orm import sessionmaker

from db.prepare import Base
from db.common import engine


def init_db():
    import db.tables

    Base.metadata.create_all(bind=engine)

    session = sessionmaker(bind=engine)()
    v = db.tables.Version(db.tables.__version__)
    session.add(v)
    session.commit()
    # print('Initialised database: ', engine.table_names())
