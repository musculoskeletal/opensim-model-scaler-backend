
OpenSIM Model Scaler Backend
============================

This is the backend for scaling musculoskeletal models using motion capture data, GIAS3, and OpenSIM.
The backend is split into two parts, the Flask application which handles requests from the frontend,
and the processing application which processes scaling jobs.

Processing requests received from the frontend are queued with the processing application.
The processing application is setup to run one scaling job at a time as scaling a model is a rather processor hungry.
The processing application can be configured to run multiple jobs at once, if desired, the default though is one job at a time.

In theory, this should work on MS Windows but this has not been tested.

Flask Application
-----------------

The backend is a Flask application that defines API for performing services that the frontend requests.

Preparation
+++++++++++

To run the Flask application we can use gunicorn `gunicorn <https://gunicorn.org/>`_.
But before we do, we need to set some environment variables that the backend requires, these variables are::

 OMS_BACKEND_WORK_DIR
 OMS_BACKEND_SQL_DATABASE
 OMS_BACKEND_SECRET_KEY
 OMS_WORKFLOW_DIR
 OMS_PROCESSING_PYTHON_EXE

where:

 * OMS_BACKEND_WORK_DIR sets the working directory for running the scaling process.
 * OMS_BACKEND_SQL_DATABASE is the location of the SQL database for the parameters and TRC data.
 * OMS_BACKEND_SECRET_KEY is the secret key.
 * OMS_WORKFLOW_DIR is the directory of the MAP Client workflow.
 * OMS_PROCESSING_PYTHON_EXE is the python executable for running the MAP Client workflow.

A convenient way to setup the environment for the server is to create a file called *.env* and define the environment variables with their values.
In the *.env* file define each environment variable one per line with the format *NAME=VALUE* (no spaces).
As an example a line could be specified as::

 OMS_BACKEND_WORK_DIR=/path/to/working/directory

Then, to define the environment variables in the current environment run the following *bash* command::

 export $(grep -v '^#' .env | xargs)

Of course, this is only useful for a *bash* environment but hopefully transferable to other environments.

It is a good practice to run the Flask application in a virtual environment.
There are many ways to create a virtual environment, and we will give just one here.
With Python > 3.7 we can create a virtual environment with the command::

 python -m venv venv-oms-backend

This creates just the virtual environment.
Before we can run the Flask application we need to install Flask and its requirements.
We do this by activating the virtual environment and installing the application requirements.
We can do this with the following commands::

 source venv-oms-backend/bin/activate
 pip install -r requirements.txt

Again, these commands are suitable for a *bash* environment.
For a different environment modifications will need to be made, hopefully the changes will be obvious.

Running
+++++++

The Flask application can be started with the following command::

 gunicorn --bind localhost:6161 --workers 1

If you are developing the Flask application it is useful to add the *--reload** flag.
This will restart the server automatically when code changes are detected.
