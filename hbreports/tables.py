"""Tables for data produced by reports.

This module is for report tables, not database tables.
"""

from collections import defaultdict


# TODO: EmptyCell?


class Table:
    """Table with report results.

    Iterate over the table to get rows. Row is a tuple.
    """

    def __init__(self, rows_iterable=[]):
        self._rows = []
        # Columns number
        self._width = 0
        for row in rows_iterable:
            self.add_row(row)

    def add_row(self, iterable):
        row = tuple(iterable)

        if not row:
            raise ValueError('Empty rows not allowed')
        if self._width and len(row) != self._width:
            raise ValueError('Wrong number of columns')

        self._rows.append(row)

        if not self._width:
            self._width = len(row)

    @property
    def width(self):
        """Width / columns number."""
        return self._width

    @property
    def height(self):
        """Height / rows number."""
        return len(self._rows)

    def __iter__(self):
        """Iterate over table rows."""
        yield from self._rows

    def __bool__(self):
        """Empty table evaluates to False."""
        return bool(self._rows)


# TODO: add sorting options?
class FreeTableBuilder:
    """Easy-to-use table builder.

    This builder supports filling cells in arbitrary order.

    :param default: value to use for empty cells
    """

    def __init__(self, default=None):
        self._table = defaultdict(dict)
        # TODO: make corner_label a ctor arg
        # There is a special attribute to set content of left top
        # corner cell. You can't do it with set_cell().
        self.corner_label = None
        self._default = default

    def set_cell(self, row, column, value):
        self._table[row][column] = value

    @property
    def table(self):
        """Get table."""
        if not self._table:
            return Table()

        generated_table = Table()
        column_names = sorted({column_name
                               for row in self._table.values()
                               for column_name in row.keys()})
        # header
        generated_table.add_row([self.corner_label] + column_names)

        for row_name in sorted(self._table.keys()):
            generated_table.add_row(
                [row_name]
                + [self._table[row_name].get(column_name, self._default)
                   for column_name in column_names])

        return generated_table
