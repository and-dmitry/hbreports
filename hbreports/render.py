"""Rendering reports."""

from texttable import Texttable


class PlainTextRenderer:
    """Rendering in plain text."""

    def render_table(self, rows, stream):
        """Print table to file-like object."""
        # TODO: alignment, width
        table = Texttable()
        table.add_rows(rows)
        stream.write(table.draw())
