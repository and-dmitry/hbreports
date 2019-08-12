"""Command line interface for hbreports."""

import argparse
import os.path
import sys

from hbreports import db
from hbreports.hbfile import initial_import
from hbreports.reports import AecReportGenerator, TtaReportGenerator
from hbreports.render import PlainTextRenderer


def handle_import_command(args):
    """Handle "import" command."""
    # TODO: exceptions?
    if not os.path.exists(args.xhb_path):
        print('Cannot perform import. '
              f'HomeBank file "{args.xhb_path}" not found', file=sys.stderr)
        return 1

    if os.path.exists(args.db_path):
        print('Cannot perform import. '
              f'Database file "{args.db_path}" already exists',
              file=sys.stderr)
        return 1

    engine = db.init_db(args.db_path)
    with engine.begin() as dbc, open(args.xhb_path) as f:
        initial_import(f, dbc)

    return 0


def handle_report_command(args):
    """Handle "report" command."""
    # TODO: also support xhb (import to memory db)
    if not os.path.exists(args.db_path):
        print("Can't do a report"
              f'Database file "{args.db_path}" not found', file=sys.stderr)
        return 1

    engine = db.init_db(args.db_path)

    # TODO: factory
    # TODO: apply report params
    if args.report_name == 'tta':
        report_gen = TtaReportGenerator()
    elif args.report_name == 'aec':
        report_gen = AecReportGenerator()
    else:
        print('Unknown report', file=sys.stderr)
        return 1
    with engine.begin() as db_connection:
        report = report_gen.generate_report(db_connection)
    # TODO: select renderer
    renderer = PlainTextRenderer()
    renderer.render_table(report.table, sys.stdout)
    return 0


def main():
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
    report_parser.add_argument('db_path', help='path to sqlite database file')
    report_parser.add_argument('report_name', help='name of report')
    report_parser.set_defaults(func=handle_report_command)

    args = parser.parse_args()
    # This is a standard way of handling (sub)commands
    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
