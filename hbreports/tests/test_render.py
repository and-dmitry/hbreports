import io

from hbreports.render import PlainTextRenderer


def test_render_table_plain_text_basic():
    """Test basic rendering to plain text."""
    renderer = PlainTextRenderer()
    # TODO: use Table!
    table = [['h1', 'h2'],
             ['c11', 'c12']]
    stream = io.StringIO()
    renderer.render_table(table, stream)

    output = stream.getvalue()
    for row in table:
        for cell in row:
            assert cell in output


# TODO: test empty table
