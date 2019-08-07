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
from hbreports.tables import (
    SimpleTable,
    Table2d,
)


# TODO: abc for reports?


class TtaReport:
    """TTA - Total Transactions by Account.

    This is the simpliest report possible. It's actual porpose is to
    help design the reports framework.
    """

    name = 'Total transactions quantity by account'

    def run(self, dbc):
        table = SimpleTable()
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


class AmcReport:

    """AMC - Average Monthly expenses by Category."""

    name = 'Average monthly expenses by category'

    def __init__(self, from_year, to_year):
        self._from_year = from_year
        self._to_year = to_year

    def run(self, dbc):
        # TODO: this skips years and categories with no
        # transactions. It's fixable but do we really need them?
        #
        # TODO: this is not working correctly yet: filter tr status,
        # income/expense category, internal xfers
        topcat = category.alias()
        subcat = category.alias()
        year = func.strftime('%Y', txn.c.date).label('year')
        result = dbc.execute(
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
            # Using year instead of date probably hurts perfomance a little
            .where(year.between(str(self._from_year), str(self._to_year)))
            .group_by(topcat.c.name, 'year')
        )
        table = Table2d()
        table.corner = 'Category/Year'
        for row in result:
            print(row)
            table.set_cell(row[0], row[1], row[2])
        return table
