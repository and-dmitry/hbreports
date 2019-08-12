import datetime

import pytest

from hbreports import db
from hbreports.hbfile import Paymode, TxnStatus
from hbreports.reports import (
    AecReportGenerator,
    Report,
    TtaReportGenerator,
)
from hbreports.tables import Table


# TODO: duplication with test_hbfile
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


@pytest.fixture
def demo_db(db_connection):
    # WARNING: use same set of keys for all entries! Otherwise some
    # keys will be silently ignored.
    db_connection.execute(db.currency.insert(), [
        {'id': 1, 'name': 'currency1'},
    ])
    db_connection.execute(db.account.insert(), [
        {'id': 1, 'name': 'account1', 'currency_id': 1},
        {'id': 2, 'name': 'account2', 'currency_id': 1},
    ])
    db_connection.execute(db.category.insert(), [
        {'id': 1, 'name': 'expense_cat1', 'income': False}
    ])
    db_connection.execute(db.txn.insert(), [
        {'id': 1, 'account_id': 1, 'date': datetime.date(2017, 1, 10),
         'status': TxnStatus.RECONCILED, 'paymode': Paymode.NONE},
        {'id': 2, 'account_id': 1, 'date': datetime.date(2018, 1, 10),
         'status': TxnStatus.RECONCILED, 'paymode': Paymode.NONE},
    ])
    db_connection.execute(db.split.insert(), [
        {'txn_id': 1, 'amount': -10.0, 'category_id': None},
        {'txn_id': 2, 'amount': -15.0, 'category_id': None},
        {'txn_id': 2, 'amount': -1.1, 'category_id': 1},
    ])


def test_report_minimal():
    """Test minimal report."""
    name = 'test report'
    table = Table()
    report = Report(name, table)
    assert report.name == name
    assert report.table is table
    assert report.description is None


# total transaction by category report tests


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
              'paymode': Paymode.NONE,
              'status': 0}] * 3
    db_connection.execute(db.txn.insert(), trans)

    generator = TtaReportGenerator()
    report = generator.generate_report(db_connection)
    header, row1, row2 = report.table
    assert list(row1) == [accounts[0]['name'], len(trans)]
    assert list(row2) == [accounts[1]['name'], 0]


# Annual expenses by category report tests


def test_aec_defaults(db_connection, demo_db):
    """Test aec report with default parameters."""
    generator = AecReportGenerator()
    report = generator.generate_report(db_connection)

    rows = list(report.table)
    header = rows[0]
    assert '2017' in header
    assert '2018' in header


def test_aec_basic(db_connection, demo_db):
    year = 2018
    generator = AecReportGenerator(from_year=year,
                                   to_year=year)
    report = generator.generate_report(db_connection)
    assert isinstance(report.name, str)
    assert isinstance(report.description, str)

    rows = list(report.table)
    header = rows[0]
    assert isinstance(header[0], str), 'corner label is a must'
    assert list(header[1:]) == [str(year)], \
        'only selected years should be in header'
    categories = [row[0] for row in rows[1:]]
    assert '<other>' in categories
    assert 'expense_cat1' in categories
    assert isinstance(rows[1][1], float)


# TODO: real test for aec report
