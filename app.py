import os
import time
import hashlib
import pandas as pd

from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

from db_common import engine, GenderEnum
from db_prepare import db_session, table
from db_setup import init_db
from db_tables import Conversion, Demographic, FileConversionAssociation, \
    MarkerMap, MotionCaptureData, MotionCaptureMetaData
from db_queries import marker_mapping_exists, conversion_id, marker_map_id, motion_capture_data_id, conversion_exists, \
    file_conversion_association_exists, conversions_associated_with, marker_map
from db_queries import markers as get_markers
from db_upgrade import need_upgrade, upgrade

from config import Config
from trc import TRCData

from backend.trcframe.trcframeselector import trc_frame_select

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


@app.route('/process', methods=["POST"])
def run_calculations():
    data = request.get_json()
    print(data)
    print(data['id'])
    print(data['file'])
    print(data['demographic'])
    print(data['essentialMarkers'])
    print(data['trackingMarkers'])
    # query_result = MotionCaptureData.query.filter(MotionCaptureData.hash == data['file']['hash'])

    # print(query_result)
    data_table = table(data['file']['hash'])
    # target_data = TRCData()
    # target_data.load('/Users/hsor001/Projects/musculoskeletal/dump/test_file_04.trc')
    # print(target_data)
    markers_ = get_markers(data['file']['hash'])

    query_result = Conversion.query.with_entities(Conversion.marker_map_ids).filter(Conversion.name == "unknown").first()
    marker_map_ids = query_result.marker_map_ids
    ids = marker_map_ids.split(',')
    mapping = [marker_map(int(id_)) for id_ in ids]
    landmarks = {}
    for map_ in mapping:
        landmarks[map_[0]] = map_[1]

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
    osim_out_dir = os.environ['OSIM_OUTPUT_DIR']
    generation_config = {'identifier': '', 'GUI': False, 'registration_mode': 'shapemodel', 'pcs_to_fit': '1',
                         'mweight': '0.1',
                         'knee_corr': False, 'knee_dof': True, 'marker_radius': '5.0', 'skin_pad': '5.0',
                         'landmarks': landmarks}

    geometry_config = {'identifier': '', 'GUI': False, 'scale_other_bodies': True, 'in_unit': 'mm', 'out_unit': 'm',
                       'osim_output_dir': osim_out_dir,
                       'write_osim_file': True, 'subject_mass': None, 'preserve_mass_distribution': False,
                       'adj_marker_pairs': {}}

    muscle_config = {'osim_output_dir': osim_out_dir, 'in_unit': 'cm',
                     'out_unit': 'm', 'write_osim_file': True, 'update_knee_splines': False, 'static_vas': False,
                     'update_max_iso_forces': True, 'subject_height': '169', 'subject_mass': '56'}

    trc_frame = trc_frame_select(trc_data, 3)
    model.main(trc_frame, generation_config, geometry_config, muscle_config)
    time.sleep(5)
    return jsonify({'message': 'Data processed successfully.', 'id': data['id']})
