import os
from os.path import isfile, join
import csv
import glob
import json
from flask import Flask, flash, request, redirect, url_for, jsonify, Response
from flask_cors import CORS
from werkzeug.utils import secure_filename
from flask import send_from_directory
import pprint
from pathlib import Path

UPLOAD_FOLDER = Path(os.getcwd() + "/" + "trcs/")
ALLOWED_EXTENSIONS = {'trc'}
DEFAULT_PATH = os.getcwd()

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
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
    fileName = content["fileName"]
    fileContent = content["fileContent"]    # if user does not select file, browser also
    # submit an empty part without filename
    if fileName == '':
        flash('No selected file')
        return Response("{'message': 'Invalid File Name'}", status=400, mimetype='application/json')
    if fileContent and allowed_file(fileName):
        filename = secure_filename(fileName)
        completeName = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        newFile = open(completeName, "w")
        newFile.write(fileContent)
        newFile.close()
        allowedResponse = Response("", status=201, mimetype='application/json')
        allowedResponse.location = url_for('uploaded_file', filename=filename)
        return allowedResponse

@app.route('/get', methods=['GET'])
def returnMarkerSet():
    trcFiles = []
    trcFolder = Path(DEFAULT_PATH + "/trcs/")
    for file in trcFolder.glob("*.trc"):
        trcFiles.append(file)
    for trc in trcFiles:
        with open(trc) as f:
            lis = [line.split() for line in f]   
    metaData = lis[6]
    metaData = metaData[2:]
    return jsonify({'markers': metaData})

@app.route('/markers', methods=["POST"])
def markers():
    markers = request.form.getlist('data[]')
    wd = Path(os.getcwd() + "/official/")
    fileList = os.listdir(wd)
    key = 0
    if len(fileList) == 0:
        with open(Path(os.getcwd() + "/official/" + "1.csv"), "w", newline="") as f:
            writer = csv.writer(f, delimiter='\t')
            writer.writerows(markers)
            key = 1
    else:
        keyList = []
        for marker in fileList:
            keyList.append(marker.replace('.csv', ''))
        keyList = list(map(int, keyList))
        key = max(keyList) + 1
        with open(Path(os.getcwd() + "/official/" + str(key)+ ".csv"), "w", newline="") as f:
            writer = csv.writer(f, delimiter='\t')
            writer.writerows(markers)
    return jsonify({'markers': markers})

@app.route('/unselected', methods=['POST'])
def unselected():
    unselected = request.form.getlist('data[]')
    wd = Path(os.getcwd() + '/unofficial/')
    fileList = os.listdir(wd)
    key = 0
    if len(fileList) == 0:
        with open(Path(os.getcwd() + '/unofficial/' + "1.csv"), "w", newline="") as f:
            writer = csv.writer(f, delimiter='\t')
            writer.writerows(unselected)
            key = 1
    else:
        keyList = []
        for marker in fileList:
            keyList.append(marker.replace('.csv', ''))
        keyList = list(map(int, keyList))
        key = max(keyList) + 1
        with open(Path(os.getcwd() + '/unofficial/' + str(key)+ ".csv"), "w", newline="") as f:
            writer = csv.writer(f, delimiter='\t')
            writer.writerows(unselected)
            
    response = jsonify()
    response.status_code = 201
    response.headers['location'] = '/unselected/' + str(key)
    response.autocorrect_location_header = False
    return response

@app.route('/tracking', methods=['POST'])
def tracking():
    tracking = request.form.getlist('data[]')
    wd = Path(os.getcwd() + '/tracking/')
    fileList = os.listdir(wd)
    key = 0
    if len(fileList) == 0:
        with open(Path(os.getcwd() + '/tracking/' + "1.csv"), "w", newline="") as f:
            writer = csv.writer(f, delimiter='\t')
            writer.writerows(tracking)
            key = 1
    else:
        keyList = []
        for marker in fileList:
            keyList.append(marker.replace('.csv', ''))
        keyList = list(map(int, keyList))
        key = max(keyList) + 1
        with open(Path(os.getcwd() + '/tracking/' + str(key) + ".csv"), "w", newline="") as f:
            writer = csv.writer(f, delimiter='\t')
            writer.writerows(tracking)
    response = jsonify()
    response.status_code = 201
    response.headers['location'] = '/tracking/' + str(key)
    response.autocorrect_location_header = False
    return response

@app.route('/demographics', methods=['POST', 'GET'])
def demographics():
    patientID = request.form['id']
    mass = request.form['mass']
    height = request.form['height']
    age = request.form['age']
    gender = request.form['gender']
    print([patientID, mass, height, age, gender])
    return redirect(request.referrer)
    