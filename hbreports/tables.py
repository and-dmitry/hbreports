"""Tables for data produced by reports.

This module is for report tables, not database tables.
"""

from collections import defaultdict


# TODO: EmptyCell?
# TODO: abc for tables?


class SimpleTable:
    """Table with report results.

    This table is filled row by row.
    """

    def __init__(self):
        self._rows = []
        # Columns number
        self._width = None

    def add_row(self, iterable):
        row = tuple(iterable)
        if self._width and len(row) != self._width:
            raise ValueError('Wrong number of columns')
        else:
            self._width = len(row)
        self._rows.append(row)

    @property
    def rows(self):
        """Get iterator for table rows."""
        return iter(self._rows)


# TODO: convert it to TableBuilder?
# TODO: add sorting options?
class Table2d:
    """2D table.

    This table can be filled cell by cell.
    """

    def __init__(self):
        self._table = defaultdict(dict)
        self.corner_label = None

    def set_cell(self, row, column, value):
        self._table[row][column] = value

    @property
    def rows(self):
        """Get iterator for table rows."""
        column_names = sorted({column_name
                               for row in self._table.values()
                               for column_name in row.keys()})
        top_header = [self.corner_label] + column_names
        yield top_header
        for row_name in sorted(self._table.keys()):
            yield [row_name] + [self._table[row_name].get(column_name)
                                for column_name in column_names]
