import os


class Config(object):
    UPLOAD_DIR = os.environ.get("BACKEND_UPLOAD_DIR", "/not/set/")
