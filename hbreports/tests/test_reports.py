import datetime

import pytest
from sqlalchemy import create_engine

from hbreports import db
from hbreports.reports import (
    AmcReport,
    TtaReport,
)


# TODO: duplication with test_hbfile
@pytest.fixture
def db_engine():
    engine = create_engine('sqlite:///:memory:', echo=False)
    db.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def db_connection(db_engine):
    connection = db_engine.connect()
    yield connection
    connection.close()


# TTA report tests


def test_tta_empty_db(db_connection):
    """Test TTA with empty db."""
    report = TtaReport()
    table = report.run(db_connection)

    rows = list(table.rows)
    assert len(rows) == 1
    header = rows[0]
    assert isinstance(header[0], str)
    assert isinstance(header[1], str)


def test_tta_no_transactions(db_connection):
    # There are accounts, but no transactions
    currency_id = 1
    db_connection.execute(db.currency.insert().values(
        id=currency_id,
        name='currency1'))
    accounts = [
        {'name': '1 account', 'currency_id': currency_id},
        {'name': '2 account', 'currency_id': currency_id}
    ]
    db_connection.execute(db.account.insert(), accounts)

    report = TtaReport()
    table = report.run(db_connection)
    rows = list(table.rows)

    assert len(rows) == 3
    header, row1, row2 = table.rows
    assert list(row1) == [accounts[0]['name'], 0]
    assert list(row2) == [accounts[1]['name'], 0]


def test_tta_basic(db_connection):
    # TODO: creating these fixtures is tedious. Try factory boy or
    # something?
    currency_id = 1
    db_connection.execute(db.currency.insert().values(
        id=currency_id,
        name='currency1'))
    accounts = [
        {'id': 1, 'name': '1 account', 'currency_id': currency_id},
        {'id': 2, 'name': '2 account', 'currency_id': currency_id}
    ]
    db_connection.execute(db.account.insert(), accounts)
    trans = [{'account_id': accounts[0]['id'],
              'date': datetime.date(2019, 1, 1),
              'status': 0}] * 3
    db_connection.execute(db.transaction.insert(), trans)

    report = TtaReport()
    table = report.run(db_connection)
    header, row1, row2 = table.rows
    assert list(row1) == [accounts[0]['name'], len(trans)]
    assert list(row2) == [accounts[1]['name'], 0]


# AMC report tests


def test_amc_one_year(db_connection):
    year = 2018
    report = AmcReport(from_year=year,
                       to_year=year)
    table = report.run(db_connection)
    header, row = table.rows
    assert header[1] == str(year)
    # None represents 'no category', for now
    assert list(row) == [None, 0.0]


def test_amc_years_range(db_connection):
    from_year = 2017
    to_year = 2019
    report = AmcReport(from_year=from_year,
                       to_year=to_year)
    table = report.run(db_connection)
    header, row = table.rows
    assert header[1:] == [str(year)
                          for year in range(from_year, to_year + 1)]
