"""Reports.

Using abbreviations for report names. Full names would be just
ridiculously long.
"""

from sqlalchemy import func
from sqlalchemy.sql import select

from hbreports.db import (
    account,
    transaction,
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
                    func.count(transaction.c.id)])
            .select_from(account.outerjoin(
                transaction,
                # explicit on-clause seems better
                transaction.c.account_id == account.c.id))
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
        table = SimpleTable()
        # We'll start with this:
        # select cat.name, count(*) as cnt, sum(amount) as s from 'transaction' as tr join split on split.transaction_id == tr.id left join category as subcat on subcat.id = split.category_id left join category as cat on cat.id = subcat.parent_id or cat.id = subcat.id and cat.parent_id is null group by cat.name order by cnt desc;
        return table
