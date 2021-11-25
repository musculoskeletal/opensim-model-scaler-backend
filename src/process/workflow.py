import json
import os
import shutil
import subprocess
import time

from process.job_manager import receive_job, mark_job_finished, mark_job_error


def apply_config(config, file):
    with open(file) as f:
        loaded_config = json.load(f)

    loaded_config.update(config)

    with open(file, 'w') as f:
        f.write(json.dumps(loaded_config))


def main(process_python_exe, workflow_location, working_directory):
    # Set the number of attempts to read a message before shutting down.
    max_attempts = 3
    attempts = 0

    # Map the configuration received from the application to the configuration in the workflow.
    map_app_config_to_workflow_config = {
        'input': 'TRC_Source.conf',
        'generation': 'llgen1.conf',
        'geometry': 'geom_cust.conf',
        'muscle': 'musc_cust.conf'
    }

    while attempts < max_attempts:
        time.sleep(0.2)
        attempts += 1
        content = receive_job()

        if content is not None:
            # Apply config
            payload = content['payload']
            for config in payload:
                if config in map_app_config_to_workflow_config.keys():
                    apply_config(payload[config], os.path.join(workflow_location, map_app_config_to_workflow_config[config]))

            job_working_directory = payload['working_directory']
            # Run pipeline
            result = subprocess.run([process_python_exe, '-m', 'mapclient.application', '-x', '--headless', '-w', workflow_location], cwd=job_working_directory)
            # result = subprocess.run(['ls', job_working_directory])
            if result.returncode == 0:
                zip_file = os.path.join(job_working_directory, 'scaled_model')
                shutil.make_archive(zip_file, format='zip', base_dir='model', root_dir=job_working_directory)
                mark_job_finished(content)
            else:
                mark_job_error(content)
            # Reset attempt count after processing job.
            attempts = 0


if __name__ == "__main__":
    main('python that can process workflow', 'workflow directory')
