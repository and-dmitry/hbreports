"""Database interface.

Terms from HomeBank GUI are preferable for table and column
names because they are already familiar to the user.

This schema doesn't support all data from HomeBank .xhb file. There
are tables and columns only for things that may be helpful for
building reports. It should be easy to create SELECT queries for this
schema. Other operations (especially UPDATE and DELETE), perfomance
and size are not as important in this case.

We're using double type for money. SQLAlchemy doesn't support Numeric
type with SQLite. HomeBank uses double internally. We're going to use
double too. This should be more than enough for purposes of this
application.
"""


from sqlalchemy import (
    Boolean,
    Column,
    Date,
    Float,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
    UniqueConstraint,
    create_engine,
    event,
)
from sqlalchemy.engine import Engine


metadata = MetaData()

# TODO: create a namespace for tables?

currency = Table(
    'currency',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String, nullable=False, unique=True)
)


account = Table(
    'account',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String, nullable=False, unique=True),
    Column('currency_id', None, ForeignKey('currency.id'), nullable=False),
    # TODO: initial, type
)


category = Table(
    'category',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String, nullable=False),
    Column('parent_id', None, ForeignKey('category.id')),
    Column('income', Boolean, nullable=False),
    UniqueConstraint('name', 'parent_id')
)


payee = Table(
    'payee',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String, nullable=False, unique=True)
)


# 'txn' for transaction (financial). Breaking a convension of using
# terms from HomeBank to avoid a long name and a clash with SQL
# keyword. Both things make it tedious to type in sqlite shell.
txn = Table(
    'txn',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('date', Date, nullable=False),
    Column('account_id', None, ForeignKey('account.id'), nullable=False),
    Column('status', Integer, nullable=False),
    Column('payee_id', None, ForeignKey('payee.id')),
    Column('memo', String),
    Column('info', String),
    # TODO: use 0 instead of null for 'no paymode'
    Column('paymode', Integer)
)


split = Table(
    'split',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('amount', Float, nullable=False),
    Column('category_id', None, ForeignKey('category.id')),
    Column('memo', String),
    Column('txn_id', None,
           ForeignKey('txn.id'), nullable=False)
)


# Using one-to-many approach for transaction tags. We will usually
# join transaction and tag tables. Tag information is almost useless on
# its own for our purposes. Using many-to-many scheme would just mean
# an additional join.
txn_tag = Table(
    'txn_tag',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('txn_id', None,
           ForeignKey('txn.id'), nullable=False),
    Column('name', String, nullable=False)
)


# Enable foreign key constraint. It's disabled in sqlite by default.
@event.listens_for(Engine, "connect")
def enable_foreign_keys(dbapi_connection, _):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def init_db(path=None):
    """Initialize database.

    Call to start working with new or existing database. Use in-memory
    db by default.
    """
    if path:
        url = 'sqlite:///' + path
    else:
        url = 'sqlite:///:memory:'
    engine = create_engine(url, echo=False)
    metadata.create_all(engine)
    return engine
