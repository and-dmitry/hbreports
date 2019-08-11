import datetime

import pytest
from sqlalchemy import create_engine

from hbreports import db
from hbreports.reports import (
    AecReportGenerator,
    Report,
    TtaReportGenerator,
)
from hbreports.tables import Table


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


@pytest.fixture
def demo_db(db_connection):
    db_connection.execute(db.currency.insert(), [
        {'id': 1, 'name': 'currency1'},
    ])
    db_connection.execute(db.account.insert(), [
        {'id': 1, 'name': 'account1', 'currency_id': 1},
        {'id': 2, 'name': 'account2', 'currency_id': 1},
    ])
    db_connection.execute(db.txn.insert(), [
        {'account_id': 1, 'date': datetime.date(2018, 1, 1), 'status': 0},
    ])
    db_connection.execute(db.split.insert(), [
        {'txn_id': 1, 'amount': 10.0},
    ])


def test_report_minimal():
    """Test minimal report."""
    name = 'test report'
    table = Table()
    report = Report(name, table)
    assert report.name == name
    assert report.table is table
    assert report.description is None


# TTA report tests


def test_tta_empty_db(db_connection):
    """Test TTA with empty db."""
    generator = TtaReportGenerator()
    report = generator.generate_report(db_connection)
    assert isinstance(report.name, str)
    assert isinstance(report.description, str)

    assert report.table.height == 1
    rows = list(report.table)
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

    generator = TtaReportGenerator()
    report = generator.generate_report(db_connection)
    rows = list(report.table)

    assert len(rows) == 3
    header, row1, row2 = rows
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
    db_connection.execute(db.txn.insert(), trans)

    generator = TtaReportGenerator()
    report = generator.generate_report(db_connection)
    header, row1, row2 = report.table
    assert list(row1) == [accounts[0]['name'], len(trans)]
    assert list(row2) == [accounts[1]['name'], 0]


# AMC report tests


def test_aec_defaults(db_connection, demo_db):
    """Test aec report with default parameters."""
    generator = AecReportGenerator()
    report = generator.generate_report(db_connection)
    assert isinstance(report.name, str)
    assert isinstance(report.description, str)

    header, row = report.table
    assert header[1] == '2018'
    assert row[0] is None
    assert isinstance(row[1], float)


def test_aec_basic(db_connection, demo_db):
    year = 2018
    generator = AecReportGenerator(from_year=year,
                                   to_year=year)
    report = generator.generate_report(db_connection)
    assert isinstance(report.name, str)
    assert isinstance(report.description, str)

    header, row = report.table
    assert header[1] == str(year)
    # None represents 'no category', for now
    assert row[0] is None
    assert isinstance(row[1], float)


# TODO: real test for aec report
