"""conftest.py for pytest.

Put shared fixtures, plugins and hooks here.
"""

import pytest

from hbreports import db


@pytest.fixture
def db_engine():
    engine = db.init_db()
    yield engine
    engine.dispose()


@pytest.fixture
def db_connection(db_engine):
    connection = db_engine.connect()
    yield connection
    connection.close()
