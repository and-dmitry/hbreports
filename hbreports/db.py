"""Database interface.

Terms from HomeBank GUI are preferable for table and column
names beacuse they are already familiar to the user.

This schema doesn't support all data from HomeBank .xhb file. There
are tables and columns only for things that may be helpful for
building reports. It should be easy to create SELECT queries for this
schema. Other operations (especially UPDATE and DELETE), perfomance
and size are not as important in this case.
"""


from sqlalchemy import (Boolean,
                        Column,
                        Date,
                        ForeignKey,
                        Integer,
                        MetaData,
                        String,
                        Table)


metadata = MetaData()


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
    Column('account_id', None, ForeignKey('account.id'), nullable=False)
)
