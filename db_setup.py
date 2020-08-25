from db_prepare import Base
from db_common import engine


def init_db():
    import db_tables
    Base.metadata.create_all(bind=engine)
    # print('Initialised database: ', engine.table_names())
