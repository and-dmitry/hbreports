"""Reports.

Using abbreviations for report names. Full names would be just
ridiculously long.
"""

from sqlalchemy import func
from sqlalchemy.sql import and_, or_, select

from hbreports.db import (
    account,
    category,
    split,
    txn,
)
from hbreports.tables import FreeTableBuilder, Table


class Report:

    def __init__(self, name, table):
        self.name = name
        self.table = table
        self.description = None


# TODO: abc for report generators?


class TtaReportGenerator:
    """TTA - Total Transactions by Account.

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


class AmcReportGenerator:

    """AMC - Average Monthly expenses by Category.

    Processes transactions in range [from_year, to_year] if these
    arguments are provided. Otherwise processes all transactions.
    """

    name = 'Average monthly expenses by category'
    description = 'TODO'

    def __init__(self, from_year=None, to_year=None):
        self._from_year = from_year
        self._to_year = to_year

    def generate_report(self, dbc):
        report = Report(self.name, self._get_table(dbc))
        report.description = self.description
        return report

    def _get_table(self, dbc):
        # TODO: It's not average monthly expenses. It's just annual
        # expenses.
        #
        # TODO: this skips years and categories with no
        # transactions. It's fixable but do we really need them?
        #
        # TODO: this is not working correctly yet: filter tr status,
        # income/expense category, internal xfers
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
                .outerjoin(subcat, subcat.c.id == split.c.category_id)
                .outerjoin(topcat,
                           or_(topcat.c.id == subcat.c.parent_id,
                               and_(topcat.c.id == subcat.c.id,
                                    topcat.c.parent_id == None)))  # noqa: E711
            )
            .group_by(topcat.c.name, 'year')
        )
        # Using year instead of date probably hurts perfomance a little
        if self._from_year:
            query = query.where(year >= str(self._from_year))
        if self._to_year:
            query = query.where(year <= str(self._from_year))
        result = dbc.execute(query)
        builder = FreeTableBuilder()
        # TODO: should be corner_label. test & fix
        builder.corner = 'Category/Year'
        for row in result:
            print(row)
            builder.set_cell(row[0], row[1], row[2])
        return builder.table
