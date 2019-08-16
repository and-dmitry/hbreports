"""HomeBank file processing.

HomeBank uses custom file format - XHB (.xhb). This module implements
import of data from such files.

"""

import collections
import datetime
import enum
from functools import partial
import xml.etree.ElementTree as ET

from sqlalchemy.exc import SQLAlchemyError

from hbreports import db


# Delimiter for samt, scat, smem (in XHB file)
_SPLIT_DELIMITER = '||'


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

    :raises DataImportError:
    """
    parser = _StreamParser(dbc)
    parser.parse(file_object)


class _StreamParser:

    """Stream parser for HomeBank files.

    HomeBamk XML file has no nested elements and forward
    references. So event-driven parsing is very easy to implement
    in this case.

    Define method named "_handle_TAG" to handle elements with tag
    "TAG".
    """

    _HANDLER_PREFIX = '_handle_'

    def __init__(self, db_connection):
        self._dbc = db_connection
        self._processed_homebank_element = False

    def parse(self, file_object):
        """Parse file.

        :raises DataImportError:
        """
        self._processed_homebank_element = False

        try:
            for event, elem in ET.iterparse(file_object, events=['start']):
                try:
                    self._do_handle_element(elem)
                except SQLAlchemyError as exc:
                    raise DataImportError(
                        f'Failed to import data from "{elem.tag}" element '
                        'due to a database error') from exc
        except ET.ParseError as exc:
            raise DataImportError(
                'XML parsing error.'
                ' This is probably not a HomeBank file.') from exc

        if not self._processed_homebank_element:
            raise DataImportError('This is not a HomeBank file.')

    def _do_handle_element(self, elem):
        """Handle XML element.

        Name is prefixed to avoid clash with custom handler methods.
        """
        try:
            handler = getattr(self, self._HANDLER_PREFIX + elem.tag)
        except AttributeError:
            # ignoring unknown elements
            pass
        else:
            handler(_ElementWrapper(elem))

    def _handle_homebank(self, elem):
        """Handle root element."""
        # TODO: check file version. This requires some additional
        # research on HomeBank format and actively used versions.
        self._processed_homebank_element = True

    def _handle_cur(self, elem):
        """Handle currency."""
        self._dbc.execute(
            db.currency.insert().values(
                id=elem.key,
                name=elem.name))

    def _handle_account(self, elem):
        self._dbc.execute(
            db.account.insert().values(
                id=elem.key,
                name=elem.name,
                initial=elem.initial,
                currency_id=elem.curr))

    def _handle_pay(self, elem):
        """Handle payee."""
        self._dbc.execute(
            db.payee.insert().values(
                id=elem.key,
                name=elem.name))

    def _handle_cat(self, elem):
        """Handle category."""
        # TODO: Are subcategories of income categories explicitly marked
        # as income? We should mark anyway.
        self._dbc.execute(
            db.category.insert().values(
                id=elem.key,
                name=elem.name,
                parent_id=elem.parent,
                income=bool(elem.flags & CategoryFlag.INCOME)))

    def _handle_ope(self, elem):
        """Handle operation (transaction)."""
        result = self._dbc.execute(
            db.txn.insert().values(
                date=elem.date,
                account_id=elem.account,
                status=elem.st,
                payee_id=elem.payee,
                memo=elem.wording,
                info=elem.info,
                paymode=elem.paymode))
        txn_id = result.inserted_primary_key[0]

        for tag in elem.tags:
            self._dbc.execute(db.txn_tag.insert().values(
                txn_id=txn_id,
                name=tag))

        if _is_multipart(elem):
            _process_multipart_transaction(elem, txn_id, self._dbc)
        else:
            _process_simple_transaction(elem, txn_id, self._dbc)


def _is_multipart(elem):
    """Is this a multipart (split) transaction?"""
    return bool(elem.flags & TxnFlag.SPLIT)


def _process_multipart_transaction(elem, txn_id, dbc):
    for amount, category, memo in zip(
            elem.samt,
            elem.scat,
            elem.smem):
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
            amount=elem.amount,
            category_id=elem.category,
            txn_id=txn_id))


def _convert_date(date_str):
    """Convert date from HomeBank file format.

    :rtype: datetime.date
    """
    return datetime.date.fromordinal(int(date_str))


def _convert_split_amounts(amounts_str):
    """Convert split amounts.

    :returns: list of floats
    """
    return [float(amount) for amount in amounts_str.split(_SPLIT_DELIMITER)]


def _convert_split_categories(categories_str):
    """Convert split categories.

    :returns: list of values - int id or None
    """
    # Split category with id=0 means category is not specified. This
    # is a split only quirk.
    return [None if category == '0' else int(category)
            for category in categories_str.split(_SPLIT_DELIMITER)]


# Marker for required attributes. "None" is a viable value, so this
# special option was introduced.
_ATTR_NO_DEFAULT = object()


# Attribute processing rule
_AttrRule = collections.namedtuple(
    '_AttrRule', [
        # function for type conversion
        'converter',
        # default value
        'default',
    ],
    defaults=[_ATTR_NO_DEFAULT],
)


# Map attribute names to processing rules. One mapping for all
# elements. Luckily, when attributes have the same name, they have the
# same purpose. Providing all the attribute processing information in
# declarative manner and in a single place seems like a good idea.
_ATTR_RULES_MAP = {
    # required attributes
    'key': _AttrRule(int),
    'name': _AttrRule(str),
    'curr': _AttrRule(int),  # currency_id
    'date': _AttrRule(_convert_date),
    'account': _AttrRule(int),
    'samt': _AttrRule(_convert_split_amounts),
    'scat': _AttrRule(_convert_split_categories),
    'smem': _AttrRule(partial(str.split, sep=_SPLIT_DELIMITER)),
    'amount': _AttrRule(float),
    'initial': _AttrRule(float),

    # optional attributes
    'flags': _AttrRule(int, 0),
    'parent': _AttrRule(int, None),
    'st': _AttrRule(int, 0),
    'payee': _AttrRule(int, None),
    'wording': _AttrRule(str, None),
    'info': _AttrRule(str, None),
    # Paymode.NONE is the only value for 'no paymode'. NULL is not
    # allowed (to avoid ambiguity).
    'paymode': _AttrRule(int, Paymode.NONE),
    'category': _AttrRule(int, None),
    # Tags are separated by spaces. Mutable default value shouldn't
    # cause problems in this case.
    'tags': _AttrRule(str.split, []),
}


class _ElementWrapper:
    """XML Element wrapper.

    This wrapper provides access to XML attributes through instance
    attributes. It handles default values and type conversion.
    """

    _attr_rules = _ATTR_RULES_MAP

    def __init__(self, elem):
        self._elem = elem

    def __getattr__(self, name):
        """XML attrbute access."""
        assert name in self._attr_rules, \
            'Unknown attribute rule requested'
        rule = self._attr_rules[name]
        try:
            return rule.converter(self._elem.attrib[name])
        except KeyError:
            if rule.default is _ATTR_NO_DEFAULT:
                raise DataImportError(
                    f'Required attribute "{self._elem.tag}.{name}" not found')
            return rule.default
