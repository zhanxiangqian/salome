# -*- coding: utf-8 -*-
"""Manage Aster preferences on Salomé GUI
"""
import SalomePyQt as SQT

import aster_s_gui.module as AM


class PrefEntry(object):
    """A preference entry on the main page
    """

    def __init__(self, sqt, title):
        self._sqt = sqt
        self.title = title
        self.idx = None

    def build(self):
        """Build the root preference"""
        self.idx = self._sqt.addPreference(self.title)

    def add_frame(self, title):
        """Add a frame containing preferences"""
        pref = PrefEntry(self._sqt, title)
        pref.build_at(self.idx)
        return pref

    def build_at(self, parent_idx):
        """Build the preference at the given index"""
        self.idx = self._sqt.addPreference(self.title, parent_idx) 

    def add(self, preference_type):
        """Add a preference from its type"""
        pref = preference_type(self._sqt)
        pref.build_at(self.idx)
        return pref
   

class Preference(PrefEntry):
    """An Aster preference
    """
    ptype = None
    title = u"Preference"
    key = "pref"

    def __init__(self, sqt):
        PrefEntry.__init__(self, sqt, self.title)

    def build_at(self, parent_idx):
        """Build the preference at the given index"""
        self.idx = self._sqt.addPreference(self.title,
                                           parent_idx, 
                                           self.ptype,
                                           AM.AsterModule.name,
                                           self.key) 

    def find_setting(self):
        """Find the setting for the preference"""
        raise NotImplementedError


class BoolPreference(Preference):
    """A boolean preference
    """
    ptype = SQT.PT_Bool

    def find_setting(self):
        """Find the bool setting for the preference"""
        return self._sqt.boolSetting(AM.AsterModule.name, self.key)


class SaveBaseResult(BoolPreference):
    """Save the database of result produced by the Aster solver
    """
    title = u"Save results database"
    key = "save-base-result"


class InteractiveFollowUp(BoolPreference):
    """Interactive follow up
    """
    title = u"Interactive follow up"
    key = "interactive-follow-up"  


class FilePreference(Preference):
    """A file preference
    """
    ptype = SQT.PT_File

    def find_setting(self):
        """Find the string setting for the preference"""
        return str(self._sqt.stringSetting(AM.AsterModule.name, self.key))


class EditorCommand(FilePreference):
    """The editor command used for text files
    """
    title = u"Text editor"
    key = "text-editor"


class AsterPreferences(object):
    """The Aster module preferences
    """

    def __init__(self):
        self._sqt = AM.GuiBuilder().sqt

    def build_root(self, title):
        """Build the root preference"""
        root = PrefEntry(self._sqt, title)
        root.build()
        return root

    def get(self, pref_type):
        """Return the preference setting from its type"""
        pref = pref_type(self._sqt)
        return pref.find_setting()


