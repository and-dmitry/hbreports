"""Command line interface for hbreports."""

import argparse
import os.path
import sys

from sqlalchemy import create_engine

from hbreports import db
from hbreports.hbfile import initial_import


def main():
    parser = argparse.ArgumentParser()
    # TODO: add commands
    # TODO: default name for db file?
    parser.add_argument('xhb_path', help='Path to HomeBank file (.xhb)')
    parser.add_argument('db_path', help='Path to sqlite database file')
    args = parser.parse_args()

    if not os.path.exists(args.xhb_path):
        print('Cannot perform import. '
              f'HomeBank file "{args.xhb_path}" not found', file=sys.stderr)
        return 1

    if os.path.exists(args.db_path):
        print('Cannot perform import. '
              f'Database file "{args.db_path}" already exists',
              file=sys.stderr)
        return 1

    engine = create_engine('sqlite:///' + args.db_path)
    db.metadata.create_all(engine)

    with engine.begin() as dbc, open(args.xhb_path) as f:
        initial_import(f, dbc)

    return 0


if __name__ == '__main__':
    sys.exit(main())
