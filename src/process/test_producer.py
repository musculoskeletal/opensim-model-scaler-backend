import os.path
import random
import time
import uuid

from job_manager import send_job, create_job, is_job_finished
from manager import start_workflow_processor


def main():

    job_id = str(uuid.uuid4())
    processing_python = '<map-client-python>/python'
    workflow_directory = '<workflow-directory>/workflow/'
    workflow_working_directory = '<working-directory>/working/'
    job_working_directory = os.path.join(workflow_working_directory, job_id)
    osim_out_dir = os.path.join(job_working_directory, 'model')
    trc_in = '<input-file>/input.trc'
    os.makedirs(osim_out_dir, exist_ok=True)

    input_config = {
        "Location": trc_in,
    }
    generation_config = {
        'landmarks': {
            "femur-LEC-l": "LLFC",
            "femur-LEC-r": "RLFC",
            "femur-MEC-l": "LMFC",
            "femur-MEC-r": "RMFC",
            "pelvis-LASIS": "LASI",
            "pelvis-LPSIS": "LPSI",
            "pelvis-RASIS": "RASI",
            "pelvis-RPSIS": "RPSI",
            "tibiafibula-LM-l": "LLMAL",
            "tibiafibula-LM-r": "RLMAL",
            "tibiafibula-MM-l": "LMMAL",
            "tibiafibula-MM-r": "RMMAL"
        }
    }
    geometry_config = {'in_unit': 'mm', 'out_unit': 'm', 'osim_output_dir': osim_out_dir, 'subject_mass': '73', 'adj_marker_pairs': {}}
    muscle_config = {'in_unit': 'mm', 'out_unit': 'm', 'osim_output_dir': osim_out_dir, 'subject_mass': '75', 'subject_height': '181'}

    job_config = {
        'working_directory': job_working_directory,
        'input': input_config,
        'generation': generation_config,
        'geometry': geometry_config,
        'muscle': muscle_config
    }

    job = create_job(job_id, job_config)
    # Start consumer when a job is sent.
    send_job(job)
    start_workflow_processor(processing_python, workflow_directory, workflow_working_directory)
    while not is_job_finished(job_id):
        # Wait before sending next job.
        pause = random.randint(7, 12)
        time.sleep(pause)

    print("Producer finished.")


if __name__ == "__main__":
    main()
