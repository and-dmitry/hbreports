"""HomeBank file processing.

HomeBank uses custom file format - XHB (.xhb). This module implements
import of data from such files.

"""

import datetime
import xml.etree.ElementTree as ET

from hbreports.db import account, category, currency, payee, transaction


def initial_import(file_object, dbc):
    """Import data from file for the first time.

    :param file_object: file-like object with XHB data
    :param sqlalchemy.engine.Connectable dbc: database connection
    """
    # TODO: How much memory does the parsing require for the largest
    # possible file? Try iterparse?
    tree = ET.parse(file_object)
    root = tree.getroot()

    # TODO: create some sort of attr-column mapper?

    # currencies
    for elem in root.findall('cur'):
        dbc.execute(currency.insert().values(
            id=elem.attrib['key'],
            name=elem.attrib['name']))

    # accounts
    for elem in root.findall('account'):
        dbc.execute(account.insert().values(
            id=elem.attrib['key'],
            name=elem.attrib['name'],
            currency_id=elem.attrib['curr']))

    # payees
    for elem in root.findall('pay'):
        dbc.execute(payee.insert().values(
            id=elem.attrib['key'],
            name=elem.attrib['name']))

    # categories
    for elem in root.findall('cat'):
        flags = int(elem.get('flags', 0))
        dbc.execute(category.insert().values(
            id=elem.attrib['key'],
            name=elem.attrib['name'],
            parent_id=elem.get('parent'),
            # 2 means it's income
            income=bool(flags & 2)))

    # transactions
    for elem in root.findall('ope'):
        dbc.execute(transaction.insert().values(
            date=datetime.date.fromordinal(int(elem.attrib['date'])),
            account_id=elem.attrib['account']))
