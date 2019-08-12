"""Rendering reports."""

from texttable import Texttable


# TODO: add HTML renderer and renderer abc


class PlainTextRenderer:
    """Plain-text renderer for reports.

    :param stream: file-like object
    """

    def __init__(self, stream):
        self._stream = stream

    def render(self, report):
        self._render_heading(report.name)
        self._render_table(report.table)

    def _render_heading(self, text):
        self._stream.write(f'\n*** ' + text + ' ***\n\n')

    def _render_table(self, table):
        # TODO: alignment, width
        text_table = Texttable()
        text_table.add_rows(list(table))
        self._stream.write(text_table.draw())
        self._stream.write('\n')
