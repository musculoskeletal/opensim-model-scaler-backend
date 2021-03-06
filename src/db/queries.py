from sqlalchemy.sql import exists, and_

from db.prepare import db_session
from db.tables import MarkerMap, Conversion, MotionCaptureData, FileConversionAssociation, MotionCaptureMetaData, Demographic


def marker_mapping_exists(marker_mapping):
    result = db_session.query(exists().where(and_(MarkerMap.source == marker_mapping['source'],
                                                  MarkerMap.target == marker_mapping['target']))).scalar()
    return result


def conversion_exists(name, marker_map_ids):
    result = db_session.query(exists().where(and_(Conversion.name == name,
                                                  Conversion.marker_map_ids == marker_map_ids))).scalar()
    return result


def file_conversion_association_exists(id_for_conversion, trc_id):
    result = db_session.query(exists().where(and_(FileConversionAssociation.conversion_id == id_for_conversion,
                                                  FileConversionAssociation.trc_id == trc_id))).scalar()
    return result


def conversion_id(name, marker_map_ids):
    result = db_session.query(Conversion.id).filter(and_(Conversion.name == name,
                                                         Conversion.marker_map_ids == marker_map_ids)).first()

    return result[0] if result else -1


def marker_map_id(marker_mapping):
    result = db_session.query(MarkerMap.id).filter(and_(MarkerMap.source == marker_mapping['source'],
                                                        MarkerMap.target == marker_mapping['target'])).first()

    return result[0] if result else -1


def marker_map(id_):
    result = db_session.query(MarkerMap.target, MarkerMap.source).filter(MarkerMap.id == id_).first()

    return [result.target, result.source] if result else None


def motion_capture_data_id(file_info):
    result = db_session.query(MotionCaptureData.id).filter(and_(MotionCaptureData.title == file_info['title'],
                                                                MotionCaptureData.hash == file_info['hash'])).first()

    return result[0] if result else -1


def marker_map_ids_for_conversion(name):
    result = Conversion.query.with_entities(Conversion.marker_map_ids).filter(Conversion.name == name).first()
    return result.marker_map_ids


def motion_capture_metadata_for(hash_):
    motion_capture_metadata = db_session.query(MotionCaptureMetaData).filter(MotionCaptureMetaData.hash == hash_).scalar()
    return motion_capture_metadata


def conversions_associated_with(title, hash_):
    motion_capture_id = db_session.query(MotionCaptureData.id).filter(and_(MotionCaptureData.title == title,
                                                                           MotionCaptureData.hash == hash_)).scalar()
    result = db_session.query(FileConversionAssociation.conversion_id). \
        filter(FileConversionAssociation.trc_id == motion_capture_id)
    conversions = []
    if result is not None:
        conversion_ids = [r.conversion_id for r in result]
        conversions = db_session.query(Conversion).filter(Conversion.id.in_(conversion_ids)).all()

    return conversions


def marker_conversion_for(hash_):
    motion_capture_id = db_session.query(MotionCaptureData.id).filter(MotionCaptureData.hash == hash_).scalar()
    result = db_session.query(FileConversionAssociation.conversion_id). \
        filter(FileConversionAssociation.trc_id == motion_capture_id)

    conversion = None
    if result is not None:
        conversion_ids = [r.conversion_id for r in result]
        conversions = db_session.query(Conversion).filter(Conversion.id.in_(conversion_ids)).all()
        conversion = conversions[0]

    return conversion


def markers(hash_):
    query_result = MotionCaptureMetaData.query. \
        with_entities(MotionCaptureMetaData.markers). \
        filter(MotionCaptureMetaData.hash == hash_). \
        first()
    markers_data = query_result[0].split('<sep>')
    return markers_data


def demographic(id_):
    return db_session.query(Demographic).filter(Demographic.demographic_id == id_).scalar()
