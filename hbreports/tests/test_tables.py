import pytest

from hbreports.tables import Table2d, SimpleTable


def test_simple_table_empty():
    table = SimpleTable()
    assert list(table.rows) == []


def test_simple_table_add_row():
    table = SimpleTable()
    row = (1, 2, 3)
    iterable = iter(row)
    table.add_row(iterable)

    rows = list(table.rows)
    assert len(rows) == 1
    assert list(rows[0]) == list(row)


def test_simple_table_inconsistent_rows():
    """Test adding rows with different sizes."""
    table = SimpleTable()
    table.add_row([1, 2])
    with pytest.raises(ValueError):
        table.add_row([1])


def test_table2d_full():
    """Test 2D table with all elements."""
    table = Table2d()
    table.set_cell('r1', 'c1', 1)
    table.set_cell('r1', 'c2', 2)
    table.set_cell('r2', 'c1', 3)
    table.set_cell('r2', 'c2', 4)
    rows = [list(row) for row in table.rows]
    assert rows == [[None, 'c1', 'c2'],
                    ['r1', 1, 2],
                    ['r2', 3, 4]]


def test_table2d_with_gaps():
    """Test 2D table with some empty cells."""
    table = Table2d()
    table.set_cell('r1', 'c1', 1)
    table.set_cell('r2', 'c2', 4)
    rows = [list(row) for row in table.rows]
    assert rows == [[None, 'c1', 'c2'],
                    ['r1', 1, None],
                    ['r2', None, 4]]


def test_table2d_set_corner():
    """Test setting left corner label."""
    table = Table2d()
    table.set_cell('r1', 'c1', 1)
    label = 'Corner label'
    table.corner_label = label

    assert list(table.rows)[0][0] == label
