"""Command line interface for hbreports."""

import argparse
import os.path
import sys

from hbreports import db
from hbreports.hbfile import initial_import, DataImportError
from hbreports.reports import AnnualBalanceByCategory, TxnsByAccount
from hbreports.render import PlainTextRenderer


def handle_import_command(args):
    """Handle "import" command."""
    if not os.path.exists(args.xhb_path):
        sys.exit('Cannot perform import. '
                 f'HomeBank file "{args.xhb_path}" not found.')

    if os.path.exists(args.db_path):
        sys.exit('Cannot perform import. '
                 f'Database file "{args.db_path}" already exists')

    engine = db.init_db(args.db_path)
    try:
        with engine.begin() as dbc, open(args.xhb_path) as f:
            initial_import(f, dbc)
    except DataImportError as exc:
        # TODO: delete db
        sys.exit('Import failed: ' + str(exc))


def handle_report_command(args):
    """Handle "report" command."""
    # TODO: also support xhb (import to memory db)
    if not os.path.exists(args.db_path):
        sys.exit("Can't generate a report. "
                 f'Database file "{args.db_path}" not found.')

    engine = db.init_db(args.db_path)

    # TODO: factory
    # TODO: apply report params
    if args.report_name == 'tta':
        report_gen = TxnsByAccount()
    elif args.report_name == 'abc':
        report_gen = AnnualBalanceByCategory()
    else:
        sys.exit(f'Unknown report "{args.report_name}"')
    with engine.begin() as db_connection:
        report = report_gen.generate_report(db_connection)
    # TODO: select renderer
    renderer = PlainTextRenderer(sys.stdout)
    renderer.render(report)


def main(argv):
    # TODO: list supported reports with --help or with special command
    parser = argparse.ArgumentParser(prog='hbreports')
    subparsers = parser.add_subparsers(
        dest='command',  # without 'dest' it crashes (argparse bug)
        required=True,
        title='commands',
        description='run "hbreports <command> --help"'
        ' to learn arguments for specific command')

    import_parser = subparsers.add_parser(
        'import',
        help='import data from HomeBank file')
    import_parser.add_argument('xhb_path', help='path to HomeBank file (.xhb)')
    import_parser.add_argument('db_path', help='path to sqlite database file')
    import_parser.set_defaults(func=handle_import_command)

    report_parser = subparsers.add_parser(
        'report',
        help='compile a report')
    # TODO: move to parent or change to source (db/xhb)
    # TODO: this is a weird order - report db report_name. Change or use flags.
    report_parser.add_argument('db_path', help='path to sqlite database file')
    report_parser.add_argument('report_name', help='name of report')
    report_parser.set_defaults(func=handle_report_command)

    args = parser.parse_args(argv)
    # This is a standard way of handling (sub)commands
    args.func(args)


if __name__ == '__main__':
    main(sys.argv)
