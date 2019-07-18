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
    Column('name', String, nullable=False, unique=True),
    Column('parent_id', None, ForeignKey('currency.id')),
    Column('income', Boolean, nullable=False)
)


payee = Table(
    'payee',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String, nullable=False, unique=True)
)


transaction = Table(
    'transaction',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('date', Date, nullable=False),
    Column('account_id', None, ForeignKey('account.id'), nullable=False),
    Column('status', Integer, nullable=False),
    Column('payee_id', None, ForeignKey('payee.id')),
    Column('memo', String),
    Column('info', String),
    Column('paymode', Integer)
)


split = Table(
    'split',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('amount', Float, nullable=False),
    Column('category_id', None, ForeignKey('category.id')),
    Column('memo', String),
    Column('transaction_id', None,
           ForeignKey('transaction.id'), nullable=False)
)


# Using one-to-many approach for transaction tags. We will usually
# join transaction and tag tables. Tag information is almost useless on
# its own for our purposes. Using many-to-many scheme would just mean
# an additional join.
transaction_tag = Table(
    'transaction_tag',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('transaction_id', None,
           ForeignKey('transaction.id'), nullable=False),
    Column('name', String, nullable=False)
)


# Enable foreign key constraint. It's disabled in sqlite by default.
@event.listens_for(Engine, "connect")
def enable_foreign_keys(dbapi_connection, _):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
