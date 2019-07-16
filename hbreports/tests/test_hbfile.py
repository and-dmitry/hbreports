import datetime
import io

import pytest
from sqlalchemy import create_engine
from sqlalchemy.sql import select

from hbreports.db import (
    account,
    category,
    currency,
    metadata,
    payee,
    split,
    transaction,
)
from hbreports.hbfile import initial_import

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
<ope date="737061" amount="-7.3300000000000001" account="1" paymode="4" st="2"
     payee="1" category="1" wording="full memo" info="info" tags="tag1 tag2"/>
<ope date="737249" amount="-10" account="1" dst_account="2" paymode="5" st="2"
     kxfer="1"/>
<ope date="737249" amount="10" account="2" dst_account="1" paymode="5"
     flags="2" kxfer="1"/>
<ope date="737249" amount="-3" account="1" st="2" flags="256"
     wording="split transaction" scat="1||4" samt="-1||-2"
     smem="split memo 1||split memo 2"/>
<ope date="737254" amount="-8" account="1" flags="256" scat="0||0"
     samt="-1||-7" smem="||"/>
</homebank>
"""


@pytest.fixture
def std_xhb_file():
    """File-like object for the standard test-file."""
    return io.StringIO(STANDARD_XHB)


@pytest.fixture
def db_engine():
    engine = create_engine('sqlite:///:memory:', echo=False)
    metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def db_connection(db_engine):
    connection = db_engine.connect()
    yield connection
    connection.close()


def test_import_currencies(std_xhb_file, db_connection):
    with db_connection.begin():
        initial_import(std_xhb_file, db_connection)

    rows = db_connection.execute(
        select([currency])
        .order_by(currency.c.id)
    ).fetchall()
    assert rows == [(1, 'Russian Ruble'),
                    (2, 'Euro')]


def test_import_accounts(std_xhb_file, db_connection):
    with db_connection.begin():
        initial_import(std_xhb_file, db_connection)

    rows = db_connection.execute(
        select([account.c.id, account.c.name, account.c.currency_id])
        .where(account.c.id.in_((1, 3)))
        .order_by(account.c.id)
    ).fetchall()
    assert rows == [(1, 'account1', 1),
                    (3, 'account3', 2)]


def test_import_payees(std_xhb_file, db_connection):
    with db_connection.begin():
        initial_import(std_xhb_file, db_connection)

    rows = db_connection.execute(
        select([payee])
        .order_by(payee.c.id)
    ).fetchall()
    assert rows == [(1, 'payee1'),
                    (2, 'payee2')]


def test_import_categories_main(std_xhb_file, db_connection):
    with db_connection.begin():
        initial_import(std_xhb_file, db_connection)

    c = category.c
    rows = db_connection.execute(
        select([c.id, c.name, c.parent_id])
        .order_by(c.id)
    ).fetchall()[0:3]
    assert rows == [(1, 'category1', None),
                    (2, 'subcategory1-1', 1),
                    (3, 'income_category1', None)]


def test_import_categories_income(std_xhb_file, db_connection):
    with db_connection.begin():
        initial_import(std_xhb_file, db_connection)

    c = category.c
    rows = db_connection.execute(
        select([c.income])
        .order_by(c.id)
    ).fetchall()[0:3]
    assert rows == [(False,), (False,), (True,)]


def test_import_transaction_minimal(std_xhb_file, db_connection):
    with db_connection.begin():
        initial_import(std_xhb_file, db_connection)

    row = db_connection.execute(
        select([transaction, split])
        .select_from(transaction.join(
            split,
            split.c.transaction_id == transaction.c.id))
        .where(transaction.c.id == 1)
    ).first()
    assert row.date == datetime.date(2019, 1, 1)
    assert row.account_id == 1
    assert row.status == 0
    assert round(row.amount, 2) == -1.0


def test_import_transaction_full(std_xhb_file, db_connection):
    with db_connection.begin():
        initial_import(std_xhb_file, db_connection)

    row = db_connection.execute(
        select([transaction, split])
        .select_from(transaction.join(
            split,
            split.c.transaction_id == transaction.c.id))
        .where(transaction.c.id == 2)
    ).first()
    assert row.date == datetime.date(2019, 1, 2)
    assert row.account_id == 1
    assert row.status == 2
    assert round(row.amount, 2) == -7.33
    assert row.payee_id == 1
    assert row[transaction.c.memo] == 'full memo'
    assert row.info == 'info'
    assert row.paymode == 4
    assert row.category_id == 1


def test_import_transaction_internal(std_xhb_file, db_connection):
    with db_connection.begin():
        initial_import(std_xhb_file, db_connection)

    rows = db_connection.execute(
        select([transaction, split])
        .select_from(transaction.join(
            split,
            split.c.transaction_id == transaction.c.id))
        .where(transaction.c.id.in_((3, 4)))
        .order_by(transaction.c.id)
    ).fetchall()
    assert rows[0].paymode == 5
    assert rows[1].paymode == 5
    assert rows[0].amount == -rows[1].amount


def test_import_transaction_split(std_xhb_file, db_connection):
    """Test import of split transaction."""
    with db_connection.begin():
        initial_import(std_xhb_file, db_connection)

    rows = db_connection.execute(
        select([transaction, split])
        .select_from(transaction.join(
            split,
            split.c.transaction_id == transaction.c.id))
        .where(transaction.c.id == 5)
        .order_by(split.c.id)
    ).fetchall()
    first, second = rows
    assert first[transaction.c.memo] == 'split transaction'
    assert second[transaction.c.memo] == first[transaction.c.memo]
    assert first[split.c.memo] == 'split memo 1'
    assert second[split.c.memo] == 'split memo 2'
    assert first.category_id == 1
    assert second.category_id == 4
    assert first.amount == -1
    assert second.amount == -2


def test_import_transaction_minimal_split(std_xhb_file, db_connection):
    """Test import of minimal split transaction."""
    with db_connection.begin():
        initial_import(std_xhb_file, db_connection)

    rows = db_connection.execute(
        select([transaction, split])
        .select_from(transaction.join(
            split,
            split.c.transaction_id == transaction.c.id))
        .where(transaction.c.id == 6)
        .order_by(split.c.id)
    ).fetchall()
    first, second = rows
    assert first[split.c.memo] == ''
    assert second[split.c.memo] == ''
    assert first.category_id is None
    assert second.category_id is None


# TODO:
# - non-xml file
# - not homebank file
# - unsupported file version
# - attr not found
# - elem not found
# - integrity error
