import pytest
from sqlalchemy import create_engine

from hbreports import db
from hbreports.reports import AmcReport


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


def test_amc_empty(db_connection):
    year = 2018
    report = AmcReport(from_year=year,
                       to_year=year)
    result = report.run(db_connection)
    # header
    assert result.rows[0][1] == str(year)
    # None represents 'no category', for now
    assert result.rows[1] == [None, 0.0]


def test_amc_years_range(db_connection):
    from_year = 2017
    to_year = 2019
    report = AmcReport(from_year=from_year,
                       to_year=to_year)
    result = report.run(db_connection)
    assert result.rows[0][1:] == [str(year)
                                  for year in range(from_year, to_year + 1)]


def test_amc_basic(db_connection):
    # TODO: fill db
    year = 2018
    report = AmcReport(from_year=year,
                       to_year=year)
    result = report.run(db_connection)
    # TODO: check sums
    assert result.rows[0][1] == str(year)
    assert result.rows[1] == [None, 0.0]
