import os
import shutil
import time
import hashlib
import threading
import uuid

import pandas as pd

from flask import Flask, request, jsonify, Response, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

from config import Config

from db.common import engine, GenderEnum
from db.prepare import db_session, table
from db.setup import init_db
from db.tables import Conversion, Demographic, FileConversionAssociation, \
    MarkerMap, MotionCaptureData, MotionCaptureMetaData
from db.queries import marker_mapping_exists, conversion_id, marker_map_id, motion_capture_data_id, conversion_exists, \
    file_conversion_association_exists, conversions_associated_with, marker_map, marker_conversion_for, motion_capture_metadata_for, marker_map_ids_for_conversion, demographic
from db.queries import markers as get_markers
from db.upgrade import need_upgrade, upgrade

from trc import TRCData

from process.job_manager import create_job, send_job, get_job_state, list_jobs, remove_job
from process.manager import start_workflow_processor

ALLOWED_EXTENSIONS = {'trc'}

app = Flask(__name__)
app.config['WORK_DIR'] = Config.WORK_DIR
app.config['SQLALCHEMY_DATABASE_URI'] = Config.SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['CORS_HEADERS'] = 'Content-Type'
app.secret_key = Config.SECRET_KEY

CORS(app)
db = SQLAlchemy(app)

if not os.path.exists(Config.DATABASE_FILE):
    lock = threading.Lock()
    with lock:
        init_db()

if need_upgrade():
    upgrade()


@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def store_in_database(file_name, file_content):
    if file_name == '':
        return Response(f"{{message: 'Invalid file name', file_name: '{file_name}'}}",
                        status=400, mimetype='application/json')
    if file_content and allowed_file(file_name):
        readable_hash = hashlib.sha256(file_content.encode('utf-8')).hexdigest()
        data = TRCData()
        try:
            data.parse(file_content)
        except IOError:
            return Response(f"{{message: 'Invalid file content', file_name: '{file_name}'}}", status=400,
                            mimetype='application/json')
        marker_table = {'Frame#': data['Frame#'], 'Time': data['Time']}
        for marker in data['Markers']:
            marker_table[marker] = ['<sep>'.join(map(str, coordinates)) for coordinates in data[marker]]
        df = pd.DataFrame(marker_table)

        upload_status = 200
        upload_message = 'Content already exists in database.'
        if not engine.has_table(readable_hash):
            df.to_sql(readable_hash, con=engine)
            m = MotionCaptureData(file_name, readable_hash)
            db_session.add(m)
            joined_markers = '<sep>'.join(data['Markers'])
            md = MotionCaptureMetaData(readable_hash, data['PathFileType'], data['DataFormat'], data['FileName'],
                                       data_rate=data['DataRate'], camera_rate=data['CameraRate'],
                                       num_frames=data['NumFrames'], num_markers=data['NumMarkers'],
                                       units=data['Units'], orig_data_rate=data['OrigDataRate'],
                                       # orig_data_start_frame=data['OrigDataStartFrame'], orig_num_frames=data['OrigNumFrames'],
                                       markers=joined_markers)
            db_session.add(md)
            db_session.commit()
            upload_status = 201
            upload_message = 'Content added to database.'

        return Response(f"{{message: '{upload_message}',"
                        f" file_name: '{file_name}', file_hash: '{readable_hash}'}}",
                        status=upload_status,
                        mimetype='application/json')

    return Response(f"{{message: 'Invalid file content', file_name: '{file_name}'}}",
                    status=400, mimetype='application/json')


@app.route('/api/v1/upload', methods=['GET', 'POST'])
def upload_file():
    response = Response("{message: 'File upload error'}", status=400, mimetype='application/json')
    content = request.files.to_dict()
    if len(content) == 1 and 'file' in content:
        file_uploaded = content['file']
        file_name = file_uploaded.filename
        file_content = file_uploaded.read().decode('utf8')
        response = store_in_database(file_name, file_content)

    return response


@app.route('/api/v1/create/conversion', methods=['POST'])
def create_conversion():
    content = request.get_json()
    for marker_mapping in content['marker_maps']:
        if not marker_mapping_exists(marker_mapping):
            db_session.add(MarkerMap(marker_mapping['source'], marker_mapping['target']))

    db_session.commit()

    ids = []
    for marker_mapping in content['marker_maps']:
        ids.append(str(marker_map_id(marker_mapping)))

    marker_map_ids = ','.join(ids)
    if not conversion_exists(content['name'], marker_map_ids):
        db_session.add(Conversion(content['name'], marker_map_ids))
        db_session.commit()

    id_for_conversion = conversion_id(content['name'], marker_map_ids)

    trc_id = motion_capture_data_id(content['file'])
    if not file_conversion_association_exists(id_for_conversion, trc_id):
        fca = FileConversionAssociation(id_for_conversion, trc_id)
        db_session.add(fca)
        db_session.commit()

    return jsonify({'id': content['name'], 'public': True})


@app.route('/api/v1/create/demographic', methods=['POST'])
def create_demographic():
    content = request.get_json()
    public = content['visibility'] == 'public'
    gender = GenderEnum.to_enum(content['gender'])
    d = Demographic(content['id'], content['height'], content['mass'], content['age'], gender, public)
    db_session.add(d)
    db_session.commit()
    return jsonify({'id': content['id'], 'public': public})


@app.route('/api/v1/files', methods=['GET'])
def get_available_files():
    query_result = MotionCaptureData.query.all()
    trc_files = [{'title': r.title, 'hash': r.hash} for r in query_result]
    return jsonify({'files': trc_files})


@app.route('/api/v1/demographics', methods=['GET'])
def get_available_demographics():
    query_result = Demographic.query.filter(Demographic.public)
    demographics = [{'id': r.demographic_id} for r in query_result]
    return jsonify({'demographics': demographics})


@app.route('/api/v1/conversions', methods=['GET'])
def get_available_conversions():
    title = request.args.get('title', None)
    hash_ = request.args.get('hash', None)
    conversions = []
    if title is not None and hash_ is not None:
        query_result = conversions_associated_with(title, hash_)
        conversions = [{"id": o.id, "name": o.name} for o in query_result]

    return jsonify({'conversions': conversions})


@app.route('/api/v1/job/status', methods=['GET'])
def get_job_status():
    id_ = request.args.get('id', None)
    status = get_job_state(id_)

    return jsonify({'id': id_, 'status': status})


@app.route('/api/v1/job/download', methods=['POST'])
def get_job_download():
    content = request.get_json()
    id_ = content['id']

    try:
        return send_from_directory(os.path.join(Config.WORK_DIR, id_), filename='scaled_model.zip', as_attachment=True, cache_timeout=0)
    except FileNotFoundError:
        return Response(f"{{message: 'Could not find download for: {id_}'}}",
                        status=404, mimetype='application/json')


@app.route('/api/v1/job/list', methods=['GET'])
def get_job_listing():
    jobs = list_jobs()

    return jsonify({'message': 'success', 'jobs': jobs})


@app.route('/api/v1/job/remove', methods=['GET'])
def get_remove_job():
    id_ = request.args.get('id', None)
    status = remove_job(id_)
    if status:
        # Throws error on failure by default.
        try:
            shutil.rmtree(os.path.join(Config.WORK_DIR, id_))
        except FileNotFoundError:
            return Response(f"{{message: 'Could not remove job: {id_}'}}",
                            status=400, mimetype='application/json')
        return jsonify({'message': 'successfully removed job'})

    return Response(f"{{message: 'Could not remove job: {id_}'}}",
                    status=400, mimetype='application/json')


@app.route('/api/v1/markers/<string:hash_>', methods=["GET"])
def markers(hash_):
    return jsonify({'markers': get_markers(hash_)})


def process_trc_db_data(db_data, markers_):
    index = getattr(db_data, 'Frame#')
    time_ = getattr(db_data, 'Time')
    coordinates = []
    data_dict = {'Frame#': index, 'Time': time_}
    for marker in markers_:
        parts = getattr(db_data, marker).split('<sep>')
        data_dict[marker] = [float(p) for p in parts]

    return data_dict


def _populate_trc_metadata(db_data, metadata):
    db_data['PathFileType'] = metadata.path_file_type
    db_data['DataFormat'] = metadata.data_format
    db_data['FileName'] = metadata.original_file_name

    db_data['DataRate'] = metadata.data_rate
    db_data['CameraRate'] = metadata.camera_rate
    db_data['NumFrames'] = metadata.num_frames
    db_data['NumMarkers'] = metadata.num_markers
    db_data['Units'] = metadata.units
    db_data['OrigDataRate'] = metadata.orig_data_rate
    db_data['OrigDataStartFrame'] = metadata.orig_data_start_frame
    db_data['OrigNumFrames'] = metadata.orig_num_frames


@app.route('/api/v1/process', methods=["POST"])
def run_calculations():
    data = request.get_json()
    if not os.path.exists(app.config['WORK_DIR']):
        return Response(f"{{message: 'Invalid server setup, directory does not exist: {app.config['WORK_DIR']}'}}",
                        status=400, mimetype='application/json')

    demographic_data = demographic(data['demographic']['id'])
    data_table = table(data['file']['hash'])

    motion_capture_metadata = motion_capture_metadata_for(data['file']['hash'])
    marker_map_ids = marker_map_ids_for_conversion(data['conversion']['name'])
    ids = marker_map_ids.split(',')
    mapping = [marker_map(int(id_)) for id_ in ids]
    landmarks = {}
    for map_ in mapping:
        landmarks[map_[0]] = map_[1]

    markers_ = get_markers(data['file']['hash'])
    trc_db_data = db_session.query(data_table).all()
    trc_data = {}
    for frame in [process_trc_db_data(o, markers_) for o in trc_db_data]:
        marker_coordinates = [None] * len(markers_)
        for key in frame:
            if key in markers_:
                index = markers_.index(key)
                marker_coordinates[index] = frame[key]

            if key in trc_data:
                trc_data[key].append(frame[key])
            else:
                trc_data[key] = [frame[key]]

        trc_data[frame['Frame#']] = (frame['Time'], marker_coordinates)

    trc_data['Markers'] = markers_
    _populate_trc_metadata(trc_data, motion_capture_metadata)

    trc_in = TRCData()
    trc_in.update(trc_data)
    job_id = str(uuid.uuid4())

    job_working_directory = os.path.join(Config.WORK_DIR, job_id)
    trc_in_dir = os.path.join(job_working_directory, 'input')
    os.makedirs(trc_in_dir, exist_ok=True)
    osim_out_dir = os.path.join(job_working_directory, 'model')
    os.makedirs(osim_out_dir, exist_ok=True)

    trc_file = os.path.join(trc_in_dir, 'input.trc')
    trc_in.save(trc_file)

    input_config = {
        "Location": trc_file,
    }
    generation_config = {
        'landmarks': landmarks
    }

    subject_weight = str(demographic_data.weight)
    subject_height = str(demographic_data.height)
    geometry_config = {'in_unit': 'mm', 'out_unit': 'm', 'osim_output_dir': osim_out_dir, 'subject_mass': subject_weight, 'adj_marker_pairs': {}}
    muscle_config = {'in_unit': 'mm', 'out_unit': 'm', 'osim_output_dir': osim_out_dir, 'subject_mass': subject_weight, 'subject_height': subject_height}

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
    start_workflow_processor(Config.PROCESSING_PYTHON_EXE, Config.WORKFLOW_DIR, Config.WORK_DIR)
    return jsonify({'message': 'Model processing started successfully.', 'id': job_id})
