import os

NOT_SET_FLAG = "<not-set>"
_DB_FILE = os.environ.get("OMS_BACKEND_SQL_DATABASE", NOT_SET_FLAG)


class Config(object):
    WORK_DIR = os.environ.get("OMS_BACKEND_WORK_DIR", NOT_SET_FLAG)
    DATABASE_FILE = _DB_FILE
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{_DB_FILE}'
    SECRET_KEY = os.environ.get("OMS_BACKEND_SECRET_KEY", "not-the-secret-key")
    WORKFLOW_DIR = os.environ.get("OMS_WORKFLOW_DIR", NOT_SET_FLAG)
    PROCESSING_PYTHON_EXE = os.environ.get("OMS_PROCESSING_PYTHON_EXE", NOT_SET_FLAG)
