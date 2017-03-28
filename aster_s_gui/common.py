# -*- coding: utf-8 -*-
"""Common function for the GUI module
"""

from PyQt4 import QtGui as qt
from PyQt4 import QtCore as qtc
connect = qtc.QObject.connect
SIG = qtc.SIGNAL

import aster_s


ERROR, INFO = [object() for idx in range(2)]


def load_icon(name):
    """Return the Qt icon from the filename stored in aster module
    ressources"""
    fname = aster_s.get_resource("salome", "resources", "aster", name)
    return qt.QIcon(fname)

def create_icon_button(icon_name, callback, text=""):
    """Create a QPushButton from a resource filename"""
    but = qt.QPushButton(load_icon(icon_name), text)
    connect(but, SIG("clicked()"), callback)
    return but


