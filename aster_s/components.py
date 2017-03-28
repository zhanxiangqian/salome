# -*- coding: utf-8 -*-
"""Components used from the user side for building an Aster study case.
"""

from aster_s.utils import find_factory
import aster_s.astk as astk


class Component(object):
    """Component transferring data from the Python memory to the
    Salomé study.
    """

    def build(self, parent):
        """Build the component from a parent element"""
        fact = find_factory(self.__class__)
        return fact.create_elt(parent, self)


class InputFile(Component):
    """An input file provided by the user
    """

    def __init__(self, fname):
        self.fname = fname


class Directory(Component):
    """A directory provided by the user
    """

    def __init__(self, dname):
        self.dname = dname


class Value(Component):
    """A value with its name provided by the user
    """

    def __init__(self, name, val):
        self.name = name
        self.value = val


class InteractivFollowUp(Component):
    """Allow to run a terminal following the Aster process.
    """


class CommFile(InputFile):
    """A command file for building the Aster case.
    """


class MedFile(InputFile):
    """A med file for building the Aster case.
    """


class WorkingDir(Directory):
    """The working directory for the Aster case.
    """


class RemoveRmed(Component):
    """Remove rmed file from the list of Aster results.
    """


class HasBaseResult(Component):
    """Add an ASTK base result to the Aster case results.
    """


class ExportFile(InputFile):
    """The Astk command file for running the Aster case.
    """


class ExportFname(InputFile):
    """The filename used for exporting the ASTK profil
    """


class Entry(Component):
    """An component build from a Salomé object browser entry
    """

    def __init__(self, entry):
        self.entry = entry


class CommEntry(Entry):
    """A command file found in the Salomé tree
    """


class MedEntry(Entry):
    """A med file found in the Salomé tree
    """


class SMeshEntry(Entry):
    """Use a mesh under the SMESH component in the Salomé object browser
    """


class AstkProfil(Component):
    """An ASTK profil
    """

    def __init__(self, profil):
        self.profil = profil


class JobId(Component):
    """Store the job processus identifiant when running the Aster case
    """

    def __init__(self, pid):
        self.pid = pid


class MessFile(InputFile):
    """Display the astk.MessFile in the object browser
    """


class ResuFile(InputFile):
    """Display the astk.ResuFile in the object browser
    """


class RMedFile(InputFile):
    """Display the astk.RMedFile in the object browser and add an entry
    in the VISU module by using salome_tree.MedFile
    """


class BaseResult(Directory):
    """An ASTK base result from Aster case outputs.
    """


class Section(Component):
    """An Aster case section with children elements
    """

    def __init__(self, name):
        self.name = name


class DataSection(Section):
    """Store input data for running an Aster case
    """

    def __init__(self):
        Section.__init__(self, "Data")


class AstkParams(Section):
    """Display ASTK configuration in the Salomé tree
    """

    def __init__(self, cfg):
        Section.__init__(self, "Astk parameters")
        self.cfg = cfg


class ResultsSection(Section):
    """The results produced by the Aster solver
    displayed in the Salomé object browser
    """

    def __init__(self):
        Section.__init__(self, "Results")


class Case(Section):
    """An aster study case
    """


class FromComm(Case):
    """An Aster study case built from at least a command file
    """


class FromExport(Case):
    """An Aster study case built from an Astk export file
    """


class FromProfil(Case):
    """An Aster study case built from an ASTK profil (AsterProfil)
    """


