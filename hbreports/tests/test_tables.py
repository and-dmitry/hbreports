import pytest

from hbreports.tables import FreeTableBuilder, Table


def test_table_empty():
    table = Table()
    assert list(table) == []


def test_table_add_row():
    table = Table()
    row = (1, 2, 3)
    iterable = iter(row)
    table.add_row(iterable)

    rows = list(table)
    assert len(rows) == 1
    assert rows[0] == row


def test_add_empty_row():
    table = Table()
    with pytest.raises(ValueError):
        table.add_row([])


def test_table_inconsistent_rows():
    """Test adding rows with different sizes."""
    table = Table()
    table.add_row([1, 2])
    with pytest.raises(ValueError):
        table.add_row([1])


def test_table_dimensions():
    table = Table()
    assert table.width == 0
    assert table.height == 0

    table.add_row([1, 2, 3])
    table.add_row([3, 4, 5])
    assert table.width == 3
    assert table.height == 2


def test_table_bool():
    table = Table()
    assert bool(table) == False  # noqa
    table.add_row([1])
    assert bool(table) == True  # noqa


def test_table_from_itarable():
    data = [[1, 2, 3],
            [4, 5, 6]]
    table = Table(iter(data))
    assert [list(row) for row in table] == data


def test_free_builder_empty():
    builder = FreeTableBuilder()
    table = builder.table
    assert list(table) == []


def test_free_builder_full():
    """Test free builder without empty cells."""
    builder = FreeTableBuilder()
    builder.set_cell('r1', 'c1', 1)
    builder.set_cell('r1', 'c2', 2)
    builder.set_cell('r2', 'c1', 3)
    builder.set_cell('r2', 'c2', 4)
    table = builder.table
    rows = [list(row) for row in table]
    assert rows == [[None, 'c1', 'c2'],
                    ['r1', 1, 2],
                    ['r2', 3, 4]]


def test_free_builder_with_gaps():
    """Test free builder with some empty cells."""
    builder = FreeTableBuilder()
    builder.set_cell('r1', 'c1', 1)
    builder.set_cell('r2', 'c2', 4)
    table = builder.table
    rows = [list(row) for row in table]
    assert rows == [[None, 'c1', 'c2'],
                    ['r1', 1, None],
                    ['r2', None, 4]]


def test_free_builder_set_corner():
    """Test setting left corner label with free builder."""
    builder = FreeTableBuilder()
    builder.set_cell('r1', 'c1', 1)
    label = 'Corner label'
    builder.corner_label = label
    table = builder.table
    assert list(table)[0][0] == label
