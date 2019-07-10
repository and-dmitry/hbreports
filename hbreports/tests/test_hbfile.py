import datetime
import io

from sqlalchemy import create_engine
from sqlalchemy.sql import select

import pytest

from hbreports.hbfile import initial_import
from hbreports.db import (account,
                          category,
                          currency,
                          metadata,
                          payee,
                          transaction)


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
<pay key="1" name="payee1"/>
<pay key="2" name="payee2"/>
<cat key="1" name="category1"/>
<cat key="2" parent="1" flags="1" name="subcategory1-1"/>
<cat key="3" flags="2" name="income_category1"/>
<cat key="4" name="category2"/>
<ope date="737060" amount="-1" account="1"/>
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


def test_import_payees(std_xhb_file, db_connection):
    dbc = db_connection
    with dbc.begin():
        initial_import(std_xhb_file, dbc)

    rows = dbc.execute(
        select([payee])
        .order_by(payee.c.id)
    ).fetchall()
    assert rows == [(1, 'payee1'),
                    (2, 'payee2')]


def test_import_categories_main(std_xhb_file, db_connection):
    dbc = db_connection
    with dbc.begin():
        initial_import(std_xhb_file, dbc)

    c = category.c
    rows = dbc.execute(
        select([c.id, c.name, c.parent_id])
        .order_by(c.id)
    ).fetchall()[0:3]
    assert rows == [(1, 'category1', None),
                    (2, 'subcategory1-1', 1),
                    (3, 'income_category1', None)]


def test_import_categories_income(std_xhb_file, db_connection):
    dbc = db_connection
    with dbc.begin():
        initial_import(std_xhb_file, dbc)

    c = category.c
    rows = dbc.execute(
        select([c.income])
        .order_by(c.id)
    ).fetchall()[0:3]
    assert rows == [(False, ), (False, ), (True ,)]


def test_import_transaction_minimal(std_xhb_file, db_connection):
    dbc = db_connection
    with dbc.begin():
        initial_import(std_xhb_file, dbc)

    tc = transaction.c
    row = dbc.execute(
        select([tc.date, tc.account_id])
        .order_by(tc.id)
    ).first()
    assert row == (datetime.date(2019, 1, 1), 1)


# TODO:
# - non-xml file
# - not homebank file
# - unsupported file version
# - attr not found
# - elem not found
# - integrity error
