import os
import csv
import glob
from flask import Flask, flash, request, redirect, url_for, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from flask import send_from_directory

from config import Config


ALLOWED_EXTENSIONS = {'trc'}

app = Flask(__name__)
CORS(app)
app.config['UPLOAD_FOLDER'] = Config.UPLOAD_DIR


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)


@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    # check if the post request has the file part
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    file = request.files['file']
    # if user does not select file, browser also
    # submit an empty part without filename
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return redirect(url_for('uploaded_file',
                                filename=filename))


@app.route('/get', methods=['GET'])
def returnMarkerSet():
    trc_files = []
    for file in glob.glob("*.trc"):
        trc_files.append(file)
    for trc in trc_files:
        with open(trc) as f:
            lis = [line.split() for line in f]        # create a list of lists
    meta_data = lis[3]
    meta_data = meta_data[2:]
    return jsonify({'markers': meta_data})


@app.route('/markers', methods=["POST"])
def markers():
    markers_data = request.form.getlist('data[]')
    wd = os.getcwd() + '\\official'
    file_list = os.listdir(wd)
    if len(file_list) == 0:
        with open(wd + '\\' + "1.csv", "w", newline="") as f:
            writer = csv.writer(f, delimiter='\t')
            writer.writerows(markers_data)
    else:
        key_list = []
        for marker in file_list:
            key_list.append(marker.replace('.csv', ''))
        key_list = list(map(int, key_list))
        key = max(key_list) + 1
        print(wd + '\\' + str(key) + ".csv")
        with open(wd + '\\' + str(key) + ".csv", "w", newline="") as f:
            writer = csv.writer(f, delimiter='\t')
            writer.writerows(markers_data)
    return jsonify({'markers': markers_data})


@app.route('/unselected', methods=['POST'])
def unselected():
    unselected_data = request.form.getlist('data[]')
    wd = os.getcwd() + '\\unofficial'
    file_list = os.listdir(wd)
    if len(file_list) == 0:
        with open(wd + '\\' + "1.csv", "w", newline="") as f:
            writer = csv.writer(f, delimiter='\t')
            writer.writerows(unselected_data)
            key = 1
    else:
        key_list = []
        for marker in file_list:
            key_list.append(marker.replace('.csv', ''))
        key_list = list(map(int, key_list))
        key = max(key_list) + 1
        print(wd + '\\' + str(key) + ".csv")
        with open(wd + '\\' + str(key) + ".csv", "w", newline="") as f:
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
    wd = os.getcwd() + '\\tracking'
    file_list = os.listdir(wd)
    if len(file_list) == 0:
        with open(wd + '\\' + "1.csv", "w", newline="") as f:
            writer = csv.writer(f, delimiter='\t')
            writer.writerows(tracking_data)
    else:
        key_list = []
        for marker in file_list:
            key_list.append(marker.replace('.csv', ''))
        key_list = list(map(int, key_list))
        key = max(key_list) + 1
        print(wd + '\\' + str(key) + ".csv")
        with open(wd + '\\' + str(key) + ".csv", "w", newline="") as f:
            writer = csv.writer(f, delimiter='\t')
            writer.writerows(tracking_data)
    return jsonify('1')
