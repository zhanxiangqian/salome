# -*- coding: utf-8 -*-
"""Useful definitions for the aster package
"""
import os
import os.path as osp
import getpass
from salome.kernel.logger import Logger
from salome.kernel import termcolor
import logging
DEBUG = 1  # 0, 1, 2

log = Logger("ASTER",logging.DEBUG, color=termcolor.RED_FG)
log_gui = Logger("ASTERGUI",logging.DEBUG, color=termcolor.RED_FG)
if DEBUG > 0:
    log.showDebug()
    log_gui.showDebug()


class Singleton(object):
    """Singleton implementation in python.
    """
    _inst = None

    def __new__(cls):
        if cls._inst is None:
            inst = object.__new__(cls)
            inst.init()
            cls._inst = inst
        return cls._inst

    def init(self):
        """Initialize the singleton instance"""
        pass


class Factory(object):
    """Build an Aster element in Salome tree from user data.
    Use Salome tree data for building an Aster study case.
    """

    def __init__(self):
        self.compo_cls = None

    def load(self, node):
        """Load the element from a given node"""
        raise NotImplementedError

    def create_elt(self, parent_elt, compo):
        """Create the element object browser child of the parent element
        by using component user data"""
        raise NotImplementedError

    def copy_to(self, parent_elt, src_elt):
        """Copy the element object browser as a child of the parent element"""
        raise NotImplementedError


class FactoryStore(Singleton):
    """Store factories for every component building
    an Aster study case
    """

    def init(self):
        """Initialize the store"""
        self._store = {}

    def register(self, compo_cls, fctr):
        """Register a factory for a component class"""
        fctr.compo_cls = compo_cls
        self._store[compo_cls] = fctr

    def find(self, compo_cls):
        """Give the factory for an element type at a given node"""
        return self._store.get(compo_cls)


def find_factory(compo_cls):
    """Find the factory for the component class"""
    return FactoryStore().find(compo_cls)

def get_login():
    """Try to get the user login even if os.getlogin() fails (as
    seen from the Salome session)"""
    login = "unk"
    try:
        login = getpass.getuser()
    except OSError:
        try:
            login = os.environ["LOGNAME"]
        except KeyError:
            pass
    return login


class Resources(Singleton):
    """Find the Aster resources of the package
    """

    def init(self):
        """Find the resources path"""
        share_pth = os.sep.join([".."] * 6 + ["share"])
        self.path = osp.normpath(osp.join(__file__, share_pth))

    def get_path(self, *args):
        """Return the absolute path of an element stored in the package
        share directory"""
        return osp.join(self.path, *args)


def get_resource(*args):
    """Return the absolute path of a package resource"""
    return Resources().get_path(*args)


# hashlib only exists in python>=2.5
_sha1 = None
def sha1(s):
    global _sha1
    if _sha1 is None:
        try:
            import hashlib
            _sha1 = hashlib.sha1
        except ImportError:
            import sha
            _sha1 = sha.sha
    return _sha1(s)


