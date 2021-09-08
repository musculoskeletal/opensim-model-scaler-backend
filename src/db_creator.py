from sqlalchemy import ForeignKey
from sqlalchemy import Column, Integer, String, Float, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref

from db_common import GenderEnum, engine


Base = declarative_base()


class Participant(Base):
    __tablename__ = "participants"

    id = Column(Integer, primary_key=True)
    participant_id = Column(String)
    height = Column(Float)
    weight = Column(Float)
    age = Column(Float)
    gender = Column(Enum(GenderEnum))

    def __init__(self, _id, height, weight, age, gender):
        """"""
        self.participant_id = _id
        self.height = height
        self.weight = weight
        self.age = age
        self.gender = gender

    def __repr__(self):
        return f"<Participant: {self.participant_id} - {self.height} - {self.weight} - {self.age} - {self.gender}>"


class Trc(Base):
    """"""
    __tablename__ = "trcs"

    id = Column(Integer, primary_key=True)
    title = Column(String)
    hash = Column(String)

    participant_id = Column(Integer, ForeignKey("participants.id"))
    participant = relationship("Participant", backref=backref(
        "trcs", order_by=id))

    def __init__(self, title, hash_):
        """"""
        self.title = title
        self.hash = hash_


# create tables
Base.metadata.create_all(engine)
