import io

from sqlalchemy import create_engine
from sqlalchemy.sql import select

import pytest

from hbreports.xhb import initial_import
from hbreports.db import account, currency, metadata


# TODO: generate XHB to avoid duplication?


STANDARD_XHB = """<homebank v="1.3" d="050206">
<properties title="test owner" curr="1" auto_smode="1" auto_weekday="1"/>
<cur key="2" flags="0" iso="EUR" name="Euro" symb="€" syprf="1"
     dchar="," gchar=" " frac="2" rate="0" mdate="0"/>
<cur key="1" flags="0" iso="RUB" name="Russian Ruble" symb="₽" syprf="0"
     dchar="," gchar=" " frac="2" rate="0" mdate="0"/>
<account key="1" pos="1" type="1" curr="1" name="account1"
         number="n1" initial="0" minimum="0"/>
<account key="2" pos="2" type="2" curr="1" name="account2"
         initial="0" minimum="0"/>
<account key="3" pos="3" type="1" curr="2" name="account3"
         initial="0" minimum="0"/>
</homebank>
"""


@pytest.fixture
def std_xhb_file():
    """File-like object for the standard test-file."""
    return io.StringIO(STANDARD_XHB)


@pytest.fixture
def db_engine():
    engine = create_engine('sqlite:///:memory:', echo=True)
    metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def db_connection(db_engine):
    connection = db_engine.connect()
    yield connection
    connection.close()


def test_import_currencies(std_xhb_file, db_connection):
    dbc = db_connection
    with dbc.begin():
        initial_import(std_xhb_file, dbc)

    rows = dbc.execute(
        select([currency])
        .order_by(currency.c.id)
    ).fetchall()
    assert rows == [(1, 'Russian Ruble'),
                    (2, 'Euro')]


def test_import_accounts(std_xhb_file, db_connection):
    dbc = db_connection
    with dbc.begin():
        initial_import(std_xhb_file, dbc)

    rows = dbc.execute(
        select([account.c.id, account.c.name, account.c.currency_id])
        .where(account.c.id.in_((1, 3)))
        .order_by(account.c.id)
    ).fetchall()
    assert rows == [(1, 'account1', 1),
                    (3, 'account3', 2)]


# TODO:
# - non-xml file
# - bad format
# - attr not found
# - elem not found
# - integrity error
