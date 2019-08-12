"""HomeBank file processing.

HomeBank uses custom file format - XHB (.xhb). This module implements
import of data from such files.

"""

import datetime
import enum
import xml.etree.ElementTree as ET

from hbreports import db


class CategoryFlag(enum.IntFlag):
    SUB = 1
    INCOME = 2
    CUSTOM = 4
    BUDGET = 8
    FORCED = 16


class TxnFlag(enum.IntFlag):
    """Transaction flags."""
    # TODO: check meaning
    # deprecated since 5.x
    OLDVALID = 1
    INCOME = 1 << 1
    AUTO = 1 << 2
    # tmp flag?
    ADDED = 1 << 3
    # tmp flag?
    CHANGED = 1 << 4
    # deprecated since 5.x
    OLDREMIND = 1 << 5
    CHEQ2 = 1 << 6
    # scheduled?
    LIMIT = 1 << 7
    SPLIT = 1 << 8


# TODO: this is also used in db. Move to 'common' module?
class TxnStatus(enum.IntEnum):
    """Transaction status."""
    NONE = 0
    CLEARED = 1
    RECONCILED = 2
    REMIND = 3


class Paymode(enum.IntEnum):
    """Transaction paymode."""
    NONE = 0
    CREDIT_CARD = 1
    CHECK = 2
    CASH = 3
    TRANSFER = 4
    INTERNAL_TRANSFER = 5
    DEBIT_CARD = 6
    STANDING_ORDER = 7
    ELECTRONIC_PAYMENT = 8
    DEPOSIT = 9
    FEE = 10
    DIRECT_DEBIT = 11


def initial_import(file_object, dbc):
    """Import data from file for the first time.

    :param file_object: file-like object with XHB data
    :param sqlalchemy.engine.Connectable dbc: database connection
    """
    # HomeBamk XML file has no nested elements and forward
    # references. It's very easy to parse. Even an event-driven
    # implementation requires no additional effort.
    for event, elem in ET.iterparse(file_object, events=['start']):
        _process_element(elem, dbc)


# TODO: create some sort of attr-column mapper?
# TODO: create importer classes?
# TODO: check file version


def _process_currency(elem, dbc):
    dbc.execute(
        db.currency.insert().values(
            id=elem.attrib['key'],
            name=elem.attrib['name']))


def _process_account(elem, dbc):
    dbc.execute(
        db.account.insert().values(
            id=elem.attrib['key'],
            name=elem.attrib['name'],
            currency_id=elem.attrib['curr']))


def _process_payee(elem, dbc):
    dbc.execute(
        db.payee.insert().values(
            id=elem.attrib['key'],
            name=elem.attrib['name']))


def _process_category(elem, dbc):
    # TODO: Are subcategories of income categories explicitly marked
    # as income? We should mark anyway.
    flags = int(elem.get('flags', '0'))
    dbc.execute(db.category.insert().values(
        id=elem.attrib['key'],
        name=elem.attrib['name'],
        parent_id=elem.get('parent'),
        income=bool(flags & CategoryFlag.INCOME)))


def _process_transaction(elem, dbc):
    result = dbc.execute(db.txn.insert().values(
        date=datetime.date.fromordinal(int(elem.attrib['date'])),
        account_id=elem.attrib['account'],
        status=elem.get('st', '0'),
        payee_id=elem.get('payee'),
        memo=elem.get('wording'),
        info=elem.get('info'),
        # Paymode.NONE is the only value for 'no paymode'. NULL is not
        # allowed (to avoid ambiguity).
        paymode=elem.get('paymode', Paymode.NONE)
    ))
    txn_id = result.inserted_primary_key[0]

    # tags
    for tag in elem.attrib.get('tags', '').split():
        dbc.execute(db.txn_tag.insert().values(
            txn_id=txn_id,
            name=tag))

    if _is_multipart(elem):
        _process_multipart_transaction(elem, txn_id, dbc)
    else:
        _process_simple_transaction(elem, txn_id, dbc)


def _is_multipart(elem):
    """Is this a multipart (split) transaction?"""
    return bool(int(elem.get('flags', '0')) & TxnFlag.SPLIT)


def _process_multipart_transaction(elem, txn_id, dbc):
    DELIMITER = '||'

    amounts = elem.attrib['samt'].split(DELIMITER)
    categories = [
        _get_category_id(cat)
        for cat in elem.attrib['scat'].split(DELIMITER)
    ]
    memos = elem.attrib['smem'].split(DELIMITER)

    for amount, category, memo in zip(amounts, categories, memos):
        dbc.execute(db.split.insert().values(
            amount=amount,
            category_id=category,
            memo=memo,
            txn_id=txn_id))


def _process_simple_transaction(elem, txn_id, dbc):
    """Process simple transaction.

    This transaction has just one part.
    """
    dbc.execute(db.split.insert().values(
            amount=elem.attrib['amount'],
            category_id=elem.get('category'),
            txn_id=txn_id))


def _get_category_id(file_category):
    """Get category_id from category read from file."""
    if file_category == '0':
        return None
    else:
        return int(file_category)


element_mapping = {
    'cur': _process_currency,
    'account': _process_account,
    'pay': _process_payee,
    'cat': _process_category,
    'ope': _process_transaction,
}


def _process_element(elem, dbc):
    """Process arbitrary element."""
    try:
        func = element_mapping[elem.tag]
    except KeyError:
        # ignore unknown elements
        pass
    else:
        func(elem, dbc)
