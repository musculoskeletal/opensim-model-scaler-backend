import multiprocessing as mp
import os

import psutil

from filelock import FileLock

from process.workflow import main as workflow_main

_CONSUMER_PID_FILE = "workflow.pid"
_CONSUMER_PID_LOCK_FILE = _CONSUMER_PID_FILE + ".lock"


def _is_pid_active(pid):
    return psutil.pid_exists(pid)


def start_workflow_processor(process_python_exe, workflow_location, working_directory):
    mp.active_children()
    lock = FileLock(os.path.join(working_directory, _CONSUMER_PID_LOCK_FILE))
    with lock:
        try:
            with open(os.path.join(working_directory, _CONSUMER_PID_FILE)) as f:
                pid_str = f.read()
        except FileNotFoundError:
            pid_str = '-1'

        if not _is_pid_active(int(pid_str)):
            simulation_process = mp.Process(target=workflow_main, args=(process_python_exe, workflow_location, working_directory, ), daemon=True)
            simulation_process.start()
            pid = simulation_process.pid
            if pid is not None:
                with open(os.path.join(working_directory, _CONSUMER_PID_FILE), 'w') as f:
                    f.write(str(pid))
