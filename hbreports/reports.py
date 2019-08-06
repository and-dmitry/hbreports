"""Reports."""


class ReportResult:
    """Container for report results.

    When you call run() method on a report, you get an instance of
    this class. Basically is's just a table.
    """

    def __init__(self):
        self.rows = []


class AmcReport:
    """Average Monthly expenses by Category."""

    def __init__(self, from_year, to_year):
        self._from_year = from_year
        self._to_year = to_year

    def run(self, dbc):
        result = ReportResult()
        # We'll start with this:
        # select cat.name, count(*) as cnt, sum(amount) as s from 'transaction' as tr join split on split.transaction_id == tr.id left join category as subcat on subcat.id = split.category_id left join category as cat on cat.id = subcat.parent_id or cat.id = subcat.id and cat.parent_id is null group by cat.name order by cnt desc;
        result.rows = [[None] + [str(year) for year in range(self._from_year, self._to_year + 1)],
                       [None, 0.0]]
        return result
