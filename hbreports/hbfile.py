"""HomeBank file processing.

HomeBank uses custom file format - XHB (.xhb). This module implements
import of data from such files.

"""

import datetime
import enum
import xml.etree.ElementTree as ET

from hbreports.db import (
    account,
    category,
    currency,
    payee,
    split,
    txn,
    txn_tag,
)


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
    # TODO: How much memory does the parsing require for the largest
    # possible file? Try iterparse?
    tree = ET.parse(file_object)
    root = tree.getroot()

    import_order = ['cur', 'account', 'pay', 'cat', 'ope']
    for elem_name in import_order:
        for elem in root.findall(elem_name):
            _import_element(elem, dbc)


# TODO: create some sort of attr-column mapper?
# TODO: create importer classes?


def _import_currency(elem, dbc):
    dbc.execute(
        currency.insert().values(
            id=elem.attrib['key'],
            name=elem.attrib['name']))


def _import_account(elem, dbc):
    dbc.execute(
        account.insert().values(
            id=elem.attrib['key'],
            name=elem.attrib['name'],
            currency_id=elem.attrib['curr']))


def _import_payee(elem, dbc):
    dbc.execute(
        payee.insert().values(
            id=elem.attrib['key'],
            name=elem.attrib['name']))


def _import_category(elem, dbc):
    # TODO: Are subcategories of income categories explicitly marked
    # as income? We should mark anyway.
    flags = int(elem.get('flags', '0'))
    dbc.execute(category.insert().values(
        id=elem.attrib['key'],
        name=elem.attrib['name'],
        parent_id=elem.get('parent'),
        income=bool(flags & CategoryFlag.INCOME)))


def _import_transaction(elem, dbc):
    result = dbc.execute(txn.insert().values(
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
        dbc.execute(txn_tag.insert().values(
            txn_id=txn_id,
            name=tag
        ))
    if int(elem.get('flags', '0')) & TxnFlag.SPLIT:
        SPLIT_DELIMITER = '||'
        split_amounts = elem.attrib['samt'].split(SPLIT_DELIMITER)
        split_categories = [
            _get_category_id(cat)
            for cat in elem.attrib['scat'].split(SPLIT_DELIMITER)]
        split_memos = elem.attrib['smem'].split(SPLIT_DELIMITER)
        for split_amount, split_category, split_memo in zip(
                split_amounts,
                split_categories,
                split_memos):
            dbc.execute(split.insert().values(
                amount=split_amount,
                category_id=split_category,
                memo=split_memo,
                txn_id=txn_id))
    else:
        dbc.execute(split.insert().values(
            amount=elem.attrib['amount'],
            category_id=elem.get('category'),
            txn_id=txn_id))


def _get_category_id(file_category):
    """Get category_id from category read from file."""
    if file_category == '0':
        return None
    else:
        return int(file_category)


_import_mapping = {
    'cur': _import_currency,
    'account': _import_account,
    'pay': _import_payee,
    'cat': _import_category,
    'ope': _import_transaction,
}


def _import_element(elem, dbc):
    """Import arbitrary element."""
    _import_mapping[elem.tag](elem, dbc)
