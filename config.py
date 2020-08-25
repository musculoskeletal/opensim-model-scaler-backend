import os

_DB_FILE = os.environ.get("BACKEND_SQL_DATABASE", "/not/set/")


class Config(object):
    UPLOAD_DIR = os.environ.get("BACKEND_UPLOAD_DIR", "/not/set/")
    DATABASE_FILE = _DB_FILE
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{_DB_FILE}'
