import sys
import inspect

from natsort import natsorted
from packaging import version

from db_common import engine
from db_prepare import db_session, Base
from db_tables import __version__, Version, MarkerMap, Conversion, FileConversionAssociation


def _get_version():
    current_version = "0.0.0"
    if engine.dialect.has_table(engine.connect(), "versions"):
        entry = db_session.query(Version).order_by(Version.id.desc()).first()
        current_version = entry.version

    return current_version


def need_upgrade():
    current_version = _get_version()
    if version.parse(current_version) < version.parse(__version__):
        return True

    return False


def _upgrade_to_0_1_0():
    print('Upgrading to 0.1.0')
    # Base.metadata.create_all(bind=engine, tables=[Version, MarkerMap, Conversion, FileConversionAssociation])
    Version.__table__.create(engine, checkfirst=True)
    MarkerMap.__table__.create(engine, checkfirst=True)
    Conversion.__table__.create(engine, checkfirst=True)
    FileConversionAssociation.__table__.create(engine, checkfirst=True)


def _upgrades_available():
    return [name for name, obj in inspect.getmembers(sys.modules[__name__])
            if (inspect.isfunction(obj) and
                name.startswith('_upgrade_to_'))]


def upgrade():
    db_version = _get_version()

    upgrades_available = _upgrades_available()
    upgrades_available = natsorted(upgrades_available)

    start_upgrade = f"_upgrade_to_{db_version.replace('.', '_')}"
    try:
        index = upgrades_available.index(start_upgrade)
        upgrades_to_apply = upgrades_available[index+1:]
    except ValueError:
        upgrades_to_apply = upgrades_available[:]

    for upgrade_to_apply in upgrades_to_apply:
        getattr(sys.modules[__name__], upgrade_to_apply)()

    v = Version(__version__)
    db_session.add(v)
    db_session.commit()

    # print('Initialised database: ', engine.table_names())
