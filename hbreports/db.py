"""Database interface.

Terms from HomeBank GUI are preferable for table and column
names beacuse they are already familiar to the user.

This schema doesn't support all data from HomeBank .xhb file. There
are tables and columns only for things that can be helpful for
building reports.
"""


from sqlalchemy import Column, ForeignKey, Integer, MetaData, String, Table


metadata = MetaData()


currency = Table(
    'currency',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String)
)


account = Table(
    'account',
    metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String),
    Column('currency_id', None, ForeignKey('currency.id')),
    # TODO: initial, type
)
