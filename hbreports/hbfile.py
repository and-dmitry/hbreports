"""HomeBank file processing.

HomeBank uses custom file format - XHB (.xhb). This module implements
import of data from such files.

"""

import collections
import datetime
import enum
import xml.etree.ElementTree as ET

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

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


class DataImportError(Exception):
    """Failed to import data from HomeBank file."""


def initial_import(file_object, dbc):
    """Import data from file for the first time.

    :param file_object: file-like object with XHB data
    :param sqlalchemy.engine.Connectable dbc: database connection
    """
    # HomeBamk XML file has no nested elements and forward
    # references. It's very easy to parse. Even an event-driven
    # implementation requires no additional effort.
    for event, elem in ET.iterparse(file_object, events=['start']):
        try:
            _process_element(elem, dbc)
        except SQLAlchemyError as exc:
            raise DataImportError(
                f'Failed to import data from "{elem.tag}" element '
                'due to a database error') from exc


# TODO: create some sort of attr-column mapper?
# TODO: create importer classes?
# TODO: check file version


def _process_currency(elem, dbc):
    dbc.execute(
        db.currency.insert().values(
            id=_get_attr(elem, 'key'),
            name=_get_attr(elem, 'name')))


def _process_account(elem, dbc):
    dbc.execute(
        db.account.insert().values(
            id=_get_attr(elem, 'key'),
            name=_get_attr(elem, 'name'),
            currency_id=_get_attr(elem, 'curr')))


def _process_payee(elem, dbc):
    dbc.execute(
        db.payee.insert().values(
            id=_get_attr(elem, 'key'),
            name=_get_attr(elem, 'name')))


def _process_category(elem, dbc):
    # TODO: Are subcategories of income categories explicitly marked
    # as income? We should mark anyway.
    flags = _get_attr(elem, 'flags')
    dbc.execute(db.category.insert().values(
        id=_get_attr(elem, 'key'),
        name=_get_attr(elem, 'name'),
        parent_id=_get_attr(elem, 'parent'),
        income=bool(flags & CategoryFlag.INCOME)))


def _process_transaction(elem, dbc):
    result = dbc.execute(db.txn.insert().values(
        date=_get_attr(elem, 'date'),
        account_id=_get_attr(elem, 'account'),
        status=_get_attr(elem, 'st'),
        payee_id=_get_attr(elem, 'payee'),
        memo=_get_attr(elem, 'wording'),
        info=_get_attr(elem, 'info'),
        paymode=_get_attr(elem, 'paymode')
    ))
    txn_id = result.inserted_primary_key[0]

    # tags
    for tag in _get_attr(elem, 'tags').split():
        dbc.execute(db.txn_tag.insert().values(
            txn_id=txn_id,
            name=tag))

    if _is_multipart(elem):
        _process_multipart_transaction(elem, txn_id, dbc)
    else:
        _process_simple_transaction(elem, txn_id, dbc)


def _is_multipart(elem):
    """Is this a multipart (split) transaction?"""
    return bool(_get_attr(elem, 'flags') & TxnFlag.SPLIT)


def _process_multipart_transaction(elem, txn_id, dbc):
    DELIMITER = '||'

    # TODO: type conversion
    # TODO: DRY
    amounts = _get_attr(elem, 'samt').split(DELIMITER)
    categories = [
        _get_split_category_id(cat)
        for cat in _get_attr(elem, 'scat').split(DELIMITER)
    ]
    memos = _get_attr(elem, 'smem').split(DELIMITER)

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
            amount=_get_attr(elem, 'amount'),
            category_id=_get_attr(elem, 'category'),
            txn_id=txn_id))


def _get_split_category_id(split_category):
    """Get category id from split."""
    # Split category with id=0 means category is not specified. This
    # is a split only quirk.
    if split_category == '0':
        return None
    else:
        return int(split_category)


# Attribute processing information
_AttrInfo = collections.namedtuple('_AttrInfo', [
    # function for type conversion
    'converter',
    # default value
    'default',
])


# Marker for required attributes. "None" is a viable default, so this
# special option was introduced.
_REQUIRED_ATTR = object()


# One mapping for all elements. Luckily, when attributes have the same
# name, they have the same purpose. Providing all the attribute
# processing information in declarative manner and in a single place
# seems like a good idea.
_ATTR_INFO_MAPPING = {
    # required attributes
    'key': _AttrInfo(int, _REQUIRED_ATTR),
    'name': _AttrInfo(str, _REQUIRED_ATTR),
    'curr': _AttrInfo(int, _REQUIRED_ATTR),  # currency_id
    'date': _AttrInfo(lambda v: datetime.date.fromordinal(int(v)),
                      _REQUIRED_ATTR),
    'account': _AttrInfo(int, _REQUIRED_ATTR),
    'samt': _AttrInfo(str, _REQUIRED_ATTR),
    'scat': _AttrInfo(str, _REQUIRED_ATTR),
    'smem': _AttrInfo(str, _REQUIRED_ATTR),
    'amount': _AttrInfo(float, _REQUIRED_ATTR),

    # optional attributes
    'flags': _AttrInfo(int, 0),
    'parent': _AttrInfo(int, None),
    'st': _AttrInfo(int, 0),
    'payee': _AttrInfo(int, None),
    'wording': _AttrInfo(str, None),
    'info': _AttrInfo(str, None),
    # Paymode.NONE is the only value for 'no paymode'. NULL is not
    # allowed (to avoid ambiguity).
    'paymode': _AttrInfo(int, Paymode.NONE),
    'category': _AttrInfo(int, None),
    'tags': _AttrInfo(str, ''),
}


def _get_attr(elem, attr_name):
    """Get attribute value from Element.

    This function also handles type convertion and default values.

    """
    assert attr_name in _ATTR_INFO_MAPPING, 'Unknown attribute info requested'
    info = _ATTR_INFO_MAPPING[attr_name]
    try:
        return info.converter(elem.attrib[attr_name])
    except KeyError:
        if info.default is _REQUIRED_ATTR:
            raise DataImportError(
                f'Required attribute "{elem.tag}.{attr_name}" not found')
        return info.default


_ELEMENT_MAPPING = {
    'cur': _process_currency,
    'account': _process_account,
    'pay': _process_payee,
    'cat': _process_category,
    'ope': _process_transaction,
}


def _process_element(elem, dbc):
    """Process arbitrary element."""
    try:
        func = _ELEMENT_MAPPING[elem.tag]
    except KeyError:
        # ignore unknown elements
        pass
    else:
        func(elem, dbc)
