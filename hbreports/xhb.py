"""XHB files processing.

HomeBank uses custom file format - XHB (.xhb). This module implements
data import from XHB files.

"""

import xml.etree.ElementTree as ET

from hbreports.db import currency


def initial_import(file_object, db_connection):
    """Import data from file for the first time."""
    # TODO: How much memory does the parsing require for the largest
    # possible file? Try iterparse?
    tree = ET.parse(file_object)
    root = tree.getroot()
    for elem in root.findall('cur'):
        db_connection.execute(currency.insert().values(
            id=elem.attrib['key'],
            name=elem.attrib['name']))
