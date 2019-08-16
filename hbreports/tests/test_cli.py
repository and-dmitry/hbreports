import pytest
from sqlalchemy import create_engine

from hbreports.cli import main


# TODO: use pytest-datadir or pytest-datafiles?
MINI_XHB = """<homebank v="1.3" d="050206">
<properties title="test owner" curr="1" auto_smode="1" auto_weekday="1"/>
<cur key="1" flags="0" iso="RUB" name="Russian Ruble" symb="₽" syprf="0"
     dchar="," gchar=" " frac="2" rate="0" mdate="0"/>
</homebank>
"""


def test_import_success(tmp_path):
    xhb_path = tmp_path / 'test.xhb'
    with xhb_path.open('w') as f:
        f.write(MINI_XHB)
    db_path = tmp_path / 'test.db'

    main(['import', str(xhb_path), str(db_path)])

    assert db_path.exists()

    # Not using hbreports.db module to keep it as simple as possible
    # for testing purposes.
    engine = create_engine(f'sqlite:///{db_path}')
    try:
        count = engine.execute('select count(*) from currency').scalar()
        assert count >= 1
    finally:
        engine.dispose()


def test_import_no_xhb_file(tmp_path):
    """Test import - XHB doesn't exist."""
    xhb_path = tmp_path / 'test.xhb'
    db_path = tmp_path / 'test.db'

    with pytest.raises(SystemExit, match='not found'):
        main(['import', str(xhb_path), str(db_path)])


def test_import_db_exists(tmp_path):
    """Test import - db already exists."""
    xhb_path = tmp_path / 'test.xhb'
    with xhb_path.open('w') as f:
        f.write(MINI_XHB)

    db_path = tmp_path / 'test.db'
    db_path.touch()

    with pytest.raises(SystemExit, match='exist'):
        main(['import', str(xhb_path), str(db_path)])


def test_import_non_xml_file(tmp_path):
    xhb_path = tmp_path / 'test.xhb'
    with xhb_path.open('w') as f:
        f.write('test')
    db_path = tmp_path / 'test.db'

    with pytest.raises(SystemExit, match='XML'):
        main(['import', str(xhb_path), str(db_path)])


def test_report_no_db(tmp_path):
    """Test report - db doesn't exist."""
    db_path = tmp_path / 'test.db'
    with pytest.raises(SystemExit, match='not found'):
        main(['report', str(db_path), 'abc'])


def test_report_unknown(tmp_path):
    """Test unknown report."""
    db_path = tmp_path / 'test.db'
    db_path.touch()
    report_name = 'badname'

    with pytest.raises(SystemExit) as exc_info:
        main(['report', str(db_path), report_name])

    exc_str = str(exc_info.value).lower()
    assert report_name in exc_str
    assert 'unknown' in exc_str
