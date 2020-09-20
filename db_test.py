from db_common import engine
from db_queries import conversions_associated_with
from db_tables import Conversion, MarkerMap, FileConversionAssociation, MotionCaptureData

from db_upgrade import need_upgrade, upgrade, _get_version

print('Table names: ', engine.table_names())


def print_table(table):
    query_result = table.query.all()
    print(query_result)


def clear_table(table):
    table.__table__.drop(engine)
    table.__table__.create(engine, checkfirst=True)


print_conversion = True
if print_conversion:
    print_table(Conversion)

print_marker_map = True
if print_marker_map:
    print_table(MarkerMap)

print_file_conversion_association = True
if print_file_conversion_association:
    print_table(FileConversionAssociation)

print_motion_capture_data = True
if print_motion_capture_data:
    print_table(MotionCaptureData)

clear_conversion = False
if clear_conversion:
    clear_table(Conversion)

clear_marker_map = False
if clear_marker_map:
    clear_table(MarkerMap)

clear_file_conversion_association = False
if clear_file_conversion_association:
    clear_table(FileConversionAssociation)

run_conversion_associated_with = True
if run_conversion_associated_with:
    print('run_conversion_associated_with')
    result = conversions_associated_with('test_file_04.trc',
                                         '9b59b173e8c119a5f1306e6e917f96dc7bb364f96aa37dffcfdfaa27905867f2')
    [print(f"id: {o.id}, name: {o.name}") for o in result]