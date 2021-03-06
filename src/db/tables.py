from sqlalchemy import Column, Integer, String, Float, Enum, ForeignKey, Boolean
from sqlalchemy.orm import relationship, backref

from db.common import GenderEnum
from db.prepare import Base

__version__ = "0.1.0"


class Demographic(Base):
    __tablename__ = "demographics"

    id = Column(Integer, primary_key=True)
    demographic_id = Column(String)
    height = Column(Float)
    weight = Column(Float)
    age = Column(Float)
    gender = Column(Enum(GenderEnum))
    public = Column(Boolean)

    def __init__(self, _id, height, weight, age, gender, public):
        """"""
        self.demographic_id = _id
        self.height = height
        self.weight = weight
        self.age = age
        self.gender = gender
        self.public = public

    def __repr__(self):
        return f"<Demographic: {self.demographic_id} - {self.height} - {self.weight}" \
               f" - {self.age} - {self.gender} - {self.public}>"


class MotionCaptureData(Base):
    """"""
    __tablename__ = "motion_capture_data"

    id = Column(Integer, primary_key=True)
    title = Column(String)
    hash = Column(String)

    demographic_id = Column(Integer, ForeignKey("demographics.id"))
    demographic = relationship("Demographic", backref=backref(
        "motion_capture_data", order_by=id))

    def __init__(self, title, hash_):
        """"""
        self.title = title
        self.hash = hash_

    def __repr__(self):
        return f"<MotionCaptureData: {self.title} - {self.hash}>"


class MotionCaptureMetaData(Base):
    """"""
    __tablename__ = "motion_capture_meta_data"

    id = Column(Integer, primary_key=True)
    hash = Column(String)
    path_file_type = Column(String)
    data_format = Column(String)
    original_file_name = Column(String)
    data_rate = Column(Float)
    camera_rate = Column(Float)
    num_frames = Column(Integer)
    num_markers = Column(Integer)
    units = Column(String)
    orig_data_rate = Column(Float)
    orig_data_start_frame = Column(Integer)
    orig_num_frames = Column(Integer)
    markers = Column(String)

    def __init__(self, hash_, path_file_type, data_format, original_file_name,
                 data_rate=-1.0, camera_rate=-1.0, num_frames=-1, num_markers=-1, units='',
                 orig_data_rate=-1.0, orig_data_start_frame=-1, orig_num_frames=-1, markers=''):
        """"""
        self.hash = hash_
        self.path_file_type = path_file_type
        self.data_format = data_format
        self.original_file_name = original_file_name
        self.data_rate = data_rate
        self.camera_rate = camera_rate
        self.num_frames = num_frames
        self.num_markers = num_markers
        self.units = units
        self.orig_data_rate = orig_data_rate
        self.orig_data_start_frame = orig_data_start_frame
        self.orig_num_frames = orig_num_frames
        self.markers = markers

    def __repr__(self):
        return f"<MotionCaptureMetaData: {self.path_file_type} - {self.data_format} - {self.num_markers}>"


class DemographicMotionCaptureData(Base):
    """"""
    __tablename__ = 'demographic_motion_capture_data'

    id = Column(Integer, primary_key=True)
    demographic_id = Column(Integer, ForeignKey("demographics.id"))
    trc_id = Column(Integer, ForeignKey("motion_capture_data.id"))

    def __init__(self, demographic_id, trc_id):
        """"""
        self.demographic_id = demographic_id
        self.trc_id = trc_id

    def __repr__(self):
        return f"<ParticipantMotionCaptureData: {self.participant_id} - {self.trc_id}>"


# Added in version 0.1.0
class Version(Base):
    __tablename__ = "versions"

    id = Column(Integer, primary_key=True)
    version = Column(String)

    def __init__(self, version):
        self.version = version

    def __repr__(self):
        return f"<Version: {self.version}>"


class MarkerMap(Base):
    __tablename__ = "marker_map"

    id = Column(Integer, primary_key=True)
    source = Column(String)
    target = Column(String)

    def __init__(self, source, target):
        """"""
        self.source = source
        self.target = target

    def __repr__(self):
        return f"<Marker Map: '{self.source}' - '{self.target}'>"


class Conversion(Base):
    __tablename__ = "conversions"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    marker_map_ids = Column(String)

    def __init__(self, name, marker_map_ids):
        """"""
        self.name = name
        self.marker_map_ids = marker_map_ids

    def __repr__(self):
        return f"<Conversion: '{self.name}' - '{self.marker_map_ids}'>"


class FileConversionAssociation(Base):
    __tablename__ = "file_conversion_associations"

    id = Column(Integer, primary_key=True)
    conversion_id = Column(Integer, ForeignKey("conversions.id"))
    trc_id = Column(Integer, ForeignKey("motion_capture_data.id"))

    def __init__(self, conversion_id, trc_id):
        """"""
        self.conversion_id = conversion_id
        self.trc_id = trc_id

    def __repr__(self):
        return f"<File Conversion Association: '{self.conversion_id}' - '{self.trc_id}'>"
