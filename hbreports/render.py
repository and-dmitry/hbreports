"""Rendering reports."""

from texttable import Texttable


class PlainTextRenderer:
    """Rendering in plain text."""

    # TODO: move stream to ctor
    def render_table(self, table, stream):
        """Print table to file-like object."""
        # TODO: alignment, width
        text_table = Texttable()
        text_table.add_rows(list(table))
        stream.write(text_table.draw())
        stream.write('\n')
