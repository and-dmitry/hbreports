"""Rendering reports."""

import shutil
from texttable import Texttable


# TODO: add HTML renderer and renderer abc


class PlainTextRenderer:
    """Plain-text renderer for reports.

    :param stream: file-like object
    """

    # TODO: allow width override (example: printing to a file)
    def __init__(self, stream):
        self._stream = stream
        self._width = shutil.get_terminal_size().columns

    def render(self, report):
        self._render_heading(report.name)
        self._render_table(report.table)

    def _render_heading(self, text):
        self._stream.write(f'\n*** ' + text + ' ***\n\n')

    def _render_table(self, table):
        # TODO: alignment
        text_table = Texttable(self._width)
        # TODO: this is not the right place for value formatting and
        # it doesn't print trailing zeros
        text_table.set_precision(2)
        # TODO: move alignment options to the Table?
        text_table.set_cols_align(['l'] + ['r'] * (table.width - 1))
        text_table.add_rows(list(table))
        self._stream.write(text_table.draw())
        self._stream.write('\n')
