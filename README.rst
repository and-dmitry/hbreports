=========================================
 hbreports - custom reports for HomeBank
=========================================

HomeBank_ is a great personal finance software with a powerful report
system. However, that system has some limitations. *hbreports* goal is
to provide additional reports and analysis tools for HomeBank users.

*hbreports* Features:

1. Generate one of predefined reports:

   * Annual balance by category

   * More reports coming soon

2. *hbreports* converts your HomeBank file to SQLite database. Now you
   can process and analyze your data with SQL.

This application is still in early stages of development. `master`
branch is considered stable though.


Installation
============

You will need Python 3.7 and pipenv to install hbreports.

.. code-block::

   git clone https://github.com/and-dmitry/hbreports.git
   cd hbreports/
   pipenv install

   pipenv shell
   python -m hbreports.cli --help


Usage
=====

.. code-block::

   # import your data to SQLite database
   python -m hbreports.cli import my.xhb my.db

   # show Annual Balance by Category report
   python -m hbreports.cli report my.db abc

   # query your data with SQL
   sqlite3 my.db


Development
===========

.. code-block::

   git clone https://github.com/and-dmitry/hbreports.git
   cd hbreports/
   pipenv install --dev
   pipenv shell
   pytest


.. _HomeBank: http://homebank.free.fr
