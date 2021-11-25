

QUEUE_FILE = "job_queue.json"
QUEUE_LOCK_FILE = QUEUE_FILE + ".lock"


class JobState(object):

    QUEUED = "queued"
    RUNNING = "running"
    FINISHED = "finished"
    ERROR = "error"
