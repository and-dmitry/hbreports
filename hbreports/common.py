import enum


# TxnStatus and Paymode values come from HomeBank file format. But we
# also use them in database schema. So they are placed in common
# module.


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
