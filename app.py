import os
import csv
from pathlib import Path

from flask import Flask, flash, request, redirect, url_for, jsonify, Response, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

from config import Config

ALLOWED_EXTENSIONS = {'trc'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = Config.UPLOAD_DIR
app.config['CORS_HEADERS'] = 'Content-Type'
app.secret_key = 'gf3r0199truelfkjlk'
CORS(app)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)


@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.data == '':
        flash('No file part')
        return Response("{'message': 'No File Uploaded'}", status=400, mimetype='application/json')

    content = request.get_json()
    file_name = content["fileName"]
    file_content = content["fileContent"]  # if user does not select file, browser also
    # submit an empty part without filename
    if file_name == '':
        flash('No file selected')
        return Response("{'message': 'Invalid File Name'}", status=400, mimetype='application/json')
    if file_content and allowed_file(file_name):
        filename = secure_filename(file_name)
        complete_name = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        with open(complete_name, "w") as new_file:
            new_file.write(file_content)
        allowed_response = Response("", status=201, mimetype='application/json')
        allowed_response.location = url_for('uploaded_file', filename=filename)
        return allowed_response


@app.route('/get', methods=['GET'])
def return_marker_set():
    trc_files = []
    trc_folder = Path(os.path.join(app.config['UPLOAD_FOLDER'], "/trcs/"))
    for file in trc_folder.glob("*.trc"):
        trc_files.append(file)
    for trc in trc_files:
        with open(trc) as f:
            lis = [line.split() for line in f]
    meta_data = lis[6]
    meta_data = meta_data[2:]
    return jsonify({'markers': meta_data})


@app.route('/markers', methods=["POST"])
def markers():
    markers_data = request.form.getlist('data[]')
    wd = Path(os.getcwd() + "/official/")
    file_list = os.listdir(wd)
    if len(file_list) == 0:
        with open(Path(os.getcwd() + "/official/" + "1.csv"), "w", newline="") as f:
            writer = csv.writer(f, delimiter='\t')
            writer.writerows(markers_data)
    else:
        key_list = []
        for marker in file_list:
            key_list.append(marker.replace('.csv', ''))
        key_list = list(map(int, key_list))
        key = max(key_list) + 1
        with open(Path(os.getcwd() + "/official/" + str(key) + ".csv"), "w", newline="") as f:
            writer = csv.writer(f, delimiter='\t')
            writer.writerows(markers_data)
    return jsonify({'markers': markers_data})


@app.route('/unselected', methods=['POST'])
def unselected():
    unselected_data = request.form.getlist('data[]')
    wd = Path(os.getcwd() + '/unofficial/')
    file_list = os.listdir(wd)
    if len(file_list) == 0:
        with open(Path(os.getcwd() + '/unofficial/' + "1.csv"), "w", newline="") as f:
            writer = csv.writer(f, delimiter='\t')
            writer.writerows(unselected_data)
            key = 1
    else:
        key_list = []
        for marker in file_list:
            key_list.append(marker.replace('.csv', ''))
        key_list = list(map(int, key_list))
        key = max(key_list) + 1
        with open(Path(os.getcwd() + '/unofficial/' + str(key) + ".csv"), "w", newline="") as f:
            writer = csv.writer(f, delimiter='\t')
            writer.writerows(unselected_data)

    response = jsonify()
    response.status_code = 201
    response.headers['location'] = '/unselected/' + str(key)
    response.autocorrect_location_header = False
    return response


@app.route('/tracking', methods=['POST'])
def tracking():
    tracking_data = request.form.getlist('data[]')
    wd = Path(os.getcwd() + '/tracking/')
    file_list = os.listdir(wd)
    if len(file_list) == 0:
        with open(Path(os.getcwd() + '/tracking/' + "1.csv"), "w", newline="") as f:
            writer = csv.writer(f, delimiter='\t')
            writer.writerows(tracking_data)
            key = 1
    else:
        key_list = []
        for marker in file_list:
            key_list.append(marker.replace('.csv', ''))
        key_list = list(map(int, key_list))
        key = max(key_list) + 1
        with open(Path(os.getcwd() + '/tracking/' + str(key) + ".csv"), "w", newline="") as f:
            writer = csv.writer(f, delimiter='\t')
            writer.writerows(tracking_data)
    response = jsonify()
    response.status_code = 201
    response.headers['location'] = '/tracking/' + str(key)
    response.autocorrect_location_header = False
    return response


@app.route('/demographics', methods=['POST', 'GET'])
def demographics():
    patient_id = request.form['id']
    mass = request.form['mass']
    height = request.form['height']
    age = request.form['age']
    gender = request.form['gender']
    print([patient_id, mass, height, age, gender])
    return redirect(request.referrer)
