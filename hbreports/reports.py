"""Reports.

There are reports and generators. Generators work with the database
and create reports. Reports just store results.
"""

from sqlalchemy import func
from sqlalchemy.sql import and_, or_, select

from hbreports.db import (
    account,
    category,
    split,
    txn,
)
from hbreports.hbfile import Paymode, TxnStatus
from hbreports.tables import FreeTableBuilder, Table


class Report:

    def __init__(self, name, table):
        self.name = name
        self.table = table
        self.description = None


# TODO: abc for report generators?


class TxnsByAccount:
    """Total Transactions by Account (TTA) report generator.

    This is the simpliest report possible. It's actual porpose is to
    help design the reports framework.
    """

    name = 'Total transactions quantity by account'
    description = 'TODO'

    def generate_report(self, dbc):
        report = Report(self.name, self._create_table(dbc))
        report.description = self.description
        return report

    def _create_table(self, dbc):
        table = Table()
        table.add_row(['Accounts', 'Transactions qty.'])
        result = dbc.execute(
            select([account.c.name,
                    func.count(txn.c.id)])
            .select_from(account.outerjoin(
                txn,
                # explicit on-clause seems better
                txn.c.account_id == account.c.id))
            .group_by(account.c.name)
            .order_by(account.c.name)
        )
        for row in result:
            table.add_row(row)
        return table


class AnnualBalanceByCategory:
    """Annual Balance by Category (ABC) report generator.

    Processes transactions in range [from_year, to_year] if these
    arguments are provided. Otherwise processes all transactions.
    """

    name = 'Annual balance by category'
    description = 'TODO'

    def __init__(self, from_year=None, to_year=None):
        self._from_year = from_year
        self._to_year = to_year
        # TODO: get from args
        self._currency_id = 1

    def generate_report(self, dbc):
        report = Report(self.name, self._get_table(dbc))
        report.description = self.description
        return report

    def _get_table(self, dbc):
        # TODO: this skips years and categories with no
        # transactions. It's fixable but do we really need them?
        #
        # TODO: Filter out closed and marked accounts?
        topcat = category.alias()
        subcat = category.alias()
        year = func.strftime('%Y', txn.c.date).label('year')
        query = (
            select([
                topcat.c.name,
                year,
                func.sum(split.c.amount)
            ])
            .select_from(
                txn
                .join(split, split.c.txn_id == txn.c.id)
                .join(account, account.c.id == txn.c.account_id)
                .outerjoin(subcat, subcat.c.id == split.c.category_id)
                .outerjoin(topcat,
                           or_(topcat.c.id == subcat.c.parent_id,
                               and_(topcat.c.id == subcat.c.id,
                                    topcat.c.parent_id == None)))  # noqa: E711
            )
            .where(account.c.currency_id == self._currency_id)
            .where(txn.c.status == TxnStatus.RECONCILED)
            .where(txn.c.paymode != Paymode.INTERNAL_TRANSFER)
            .group_by(topcat.c.name, 'year')
        )
        # Using year instead of date probably hurts perfomance a little
        if self._from_year:
            query = query.where(year >= str(self._from_year))
        if self._to_year:
            query = query.where(year <= str(self._from_year))
        result = dbc.execute(query)

        # TODO: set default value (0.0) for the table to avoid None
        builder = FreeTableBuilder()
        builder.corner_label = 'Category/Year'
        for row in result:
            builder.set_cell(row[0] or '<other>', row[1], row[2])
        return builder.table


# TODO: AMC - Average Monthly expenses by Category
