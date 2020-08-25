import enum

from sqlalchemy import create_engine
from config import Config


class GenderEnum(enum.Enum):
    Male = 1
    Female = 2
    Other = 3

    @staticmethod
    def to_enum(value):
        """
        Takes a value and turns it into a enumerated value.
        Value returned is Other if no match is made.

        :param value: Map value to enumerated value.
        :return: The enumerated value.
        """
        gender = GenderEnum.Other
        if value == 'male':
            gender = GenderEnum.Male
        elif value == 'female':
            gender = GenderEnum.Female

        return gender


engine = create_engine(Config.SQLALCHEMY_DATABASE_URI, convert_unicode=True)
