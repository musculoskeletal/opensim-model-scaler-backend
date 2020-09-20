import os
import time
import hashlib
import pandas as pd

from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

from db_common import engine, GenderEnum
from db_prepare import db_session
from db_setup import init_db
from db_tables import Conversion, Demographic, FileConversionAssociation,\
    MarkerMap, MotionCaptureData, MotionCaptureMetaData
from db_queries import marker_mapping_exists, conversion_id, marker_map_id, motion_capture_data_id, conversion_exists, \
    file_conversion_association_exists, conversions_associated_with
from db_upgrade import need_upgrade, upgrade

from config import Config
from trc import TRCData

ALLOWED_EXTENSIONS = {'trc'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = Config.UPLOAD_DIR
app.config['SQLALCHEMY_DATABASE_URI'] = Config.SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['CORS_HEADERS'] = 'Content-Type'
app.secret_key = 'gf3r0199truelfkjlk'
CORS(app)
db = SQLAlchemy(app)

if not os.path.exists(Config.DATABASE_FILE):
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
                                       num_frames=data['NumFrames'], markers=joined_markers)
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


@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    response = Response("{message: 'File upload error'}", status=400, mimetype='application/json')
    content = request.files.to_dict()
    if len(content) == 1 and 'file' in content:
        file_uploaded = content['file']
        file_name = file_uploaded.filename
        file_content = file_uploaded.read().decode('utf8')
        response = store_in_database(file_name, file_content)

    return response


@app.route('/create/conversion', methods=['POST'])
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


@app.route('/create/demographic', methods=['POST'])
def create_demographic():
    content = request.get_json()
    public = content['visibility'] == 'public'
    gender = GenderEnum.to_enum(content['gender'])
    d = Demographic(content['id'], content['height'], content['mass'], content['age'], gender, public)
    db_session.add(d)
    db_session.commit()
    return jsonify({'id': content['id'], 'public': public})


@app.route('/files', methods=['GET'])
def get_available_files():
    query_result = MotionCaptureData.query.all()
    trc_files = [{'title': r.title, 'hash': r.hash} for r in query_result]
    return jsonify({'files': trc_files})


@app.route('/demographics', methods=['GET'])
def get_available_demographics():
    query_result = Demographic.query.filter(Demographic.public)
    demographics = [{'id': r.demographic_id} for r in query_result]
    return jsonify({'demographics': demographics})


@app.route('/conversions', methods=['GET'])
def get_available_conversions():
    title = request.args.get('title', None)
    hash_ = request.args.get('hash', None)
    conversions = []
    if title is not None and hash_ is not None:
        query_result = conversions_associated_with(title, hash_)
        conversions = [{"id": o.id, "name": o.name} for o in query_result]

    return jsonify({'conversions': conversions})


@app.route('/markers/<string:hash_>', methods=["GET"])
def markers(hash_):
    query_result = MotionCaptureMetaData.query.\
        with_entities(MotionCaptureMetaData.markers).\
        filter(MotionCaptureMetaData.hash == hash_).\
        first()
    markers_data = query_result[0].split('<sep>')
    return jsonify({'markers': markers_data})


@app.route('/process', methods=["POST"])
def run_calculations():
    data = request.get_json()
    # print(data)
    time.sleep(5)
    return jsonify({'message': 'Data processed successfully.', 'id': data['id']})
