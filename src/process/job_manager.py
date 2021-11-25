import json
import os

from filelock import FileLock

from process import job_controls


def _load_queue():
    """
    Must have already claimed the queue before calling this function.
    """
    try:
        with open(job_controls.QUEUE_FILE, 'r') as f:
            content = json.load(f)
    except FileNotFoundError:
        content = []
    except json.decoder.JSONDecodeError:
        content = []

    return content


def _save_queue(queue):
    with open(job_controls.QUEUE_FILE, 'w') as f:
        json.dump(queue, f)


def create_job(job_id, job_info):
    return {
        "payload": job_info,
        "id": job_id,
        "source_pid": os.getpid(),
        "state": job_controls.JobState.QUEUED
    }


def list_jobs():
    jobs = []
    lock = FileLock(job_controls.QUEUE_LOCK_FILE)
    with lock:
        queue = _load_queue()
        for entry in queue:
            jobs.append({'id': entry['id'], 'state': entry['state']})

    return jobs


def remove_job(job_id):
    lock = FileLock(job_controls.QUEUE_LOCK_FILE)
    with lock:
        queue = _load_queue()
        remove_index = None
        for index, entry in enumerate(queue):
            if entry["id"] == job_id and entry["state"] != job_controls.JobState.RUNNING:
                remove_index = index
                break

        if remove_index is not None:
            del queue[remove_index]
            _save_queue(queue)
            return True

    return False


def send_job(job):
    lock = FileLock(job_controls.QUEUE_LOCK_FILE)
    with lock:
        queue = _load_queue()
        queue.append(job)
        _save_queue(queue)


def get_job_state(job_id):
    lock = FileLock(job_controls.QUEUE_LOCK_FILE)
    with lock:
        queue = _load_queue()
        for entry in queue:
            if entry["id"] == job_id:
                return entry["state"]

    return "unknown"


def receive_job():
    lock = FileLock(job_controls.QUEUE_LOCK_FILE)
    content = None
    with lock:
        queue = _load_queue()
        for entry in queue:
            if entry["state"] == job_controls.JobState.QUEUED:
                entry["state"] = job_controls.JobState.RUNNING
                content = entry
                _save_queue(queue)
                break

    return content


def mark_job_finished(message):
    lock = FileLock(job_controls.QUEUE_LOCK_FILE)
    with lock:
        queue = _load_queue()
        for entry in queue:
            if entry["id"] == message["id"] and entry["source_pid"] == message["source_pid"]:
                entry["state"] = job_controls.JobState.FINISHED
                _save_queue(queue)
                break


def mark_job_error(message):
    lock = FileLock(job_controls.QUEUE_LOCK_FILE)
    with lock:
        queue = _load_queue()
        for entry in queue:
            if entry["id"] == message["id"] and entry["source_pid"] == message["source_pid"]:
                entry["state"] = job_controls.JobState.ERROR
                _save_queue(queue)
                break


def is_job_finished(job_id):
    lock = FileLock(job_controls.QUEUE_LOCK_FILE)
    with lock:
        queue = _load_queue()
        for entry in queue:
            if entry["id"] == job_id:
                return entry["state"] == job_controls.JobState.FINISHED or entry["state"] == job_controls.JobState.ERROR

    return False


def clear_old_jobs():
    lock = FileLock(job_controls.QUEUE_LOCK_FILE)
    with lock:
        queue = _load_queue()
        refreshed_queue = []
        for entry in queue:
            if entry["state"] == job_controls.JobState.QUEUED or entry["state"] == job_controls.JobState.RUNNING:
                refreshed_queue.append(entry)

        _save_queue(refreshed_queue)
