import io

from hbreports.render import PlainTextRenderer
from hbreports.reports import Report
from hbreports.tables import Table


def test_render_minimal_report_to_plain_text():
    stream = io.StringIO()
    renderer = PlainTextRenderer(stream)

    table = Table([['h1', 'h2'],
                   ['c11', 'c12']])
    report = Report('Report name', table)

    renderer.render(report)

    output = stream.getvalue()
    assert report.name in output
    for row in table:
        for cell in row:
            assert cell in output, 'cell value not found in stream'


# TODO: test empty table
