# -*- coding: utf-8 -*-
"""Create Aster study cases on the Salomé server.
"""
import os.path as osp

import aster_s
from aster_s.utils import Factory, find_factory, sha1, log
import aster_s.salome_tree as ST
import aster_s.astk as astk
import aster_s.components as AC

# Read from the studyManager
#STUDY = 'Aster'
#peter.zhang for MCrack
STUDY = 'Solver'


class Elt(object):
    """An element building the Aster study.
    Is defined by a line entry attached to a Salome tree node.
    Can perfom action on the astk configuration
    """

    def __init__(self, node, compo_cls, line=None):
        self.node = node
        self.compo_cls = compo_cls
        self.fact = find_factory(compo_cls)
        self.line = line or ST.Line(node)

    def read_name(self):
        """Read the element name in the object browser"""
        return self.line.read_name()

    def write_value(self, value):
        """Write the value in the object browser"""
        self.line.write_value(value)

    def read_value(self):
        """Read the value in the object browser"""
        return self.line.read_value()

    def give_aster_study(self):
        """Return the Aster study used for this element"""
        return Study(self.node.give_salome_study())

    def copy_to(self, dest):
        """Copy the element as a child of the destination node"""
        copy = self.fact.copy_to(dest, self)
        val = self.read_value()
        if val is not None:
            copy.write_value(val)
        return copy

    def remove(self):
        """Remove the element from the Aster study"""
        self.line.remove()

    def signature(self):
        """Return the signature of the element"""
        raise NotImplementedError


class File(Elt):
    """A file building the Aster case
    """

    def __init__(self, node, compo_cls, sfile):
        Elt.__init__(self, node, compo_cls, line=sfile)
        self.sfile = sfile

    def read_fname(self):
        """Read the filename in the object browser"""
        return self.sfile.read_fname()

    def signature(self):
        """Return the signature of the File"""
        return file_content_signature(self.read_fname())


class Directory(Elt):
    """A directory for the Aster case.
    """

    read_dname = Elt.read_value
    write_dname = Elt.write_value


class Reference(Elt):
    """An Aster element referencing another one in the Salomé
    object browser
    """

    def use_source(self, elt):
        """Use the source element"""
        self.node.use_source(elt.node)
        self.node.write_name(elt.read_name())


class FileReference(Reference):
    """A file reference in the object browser
    """

    def read_fname(self):
        """Read the source filename"""
        sfile = ST.File(self.node.give_source())
        return sfile.read_fname()

    def signature(self):
        """Return the signature of the referenced File"""
        return file_content_signature(self.read_fname())


class SMeshReference(Elt):
    """Reference from a mesh in the SMESH component
    """

    def __init__(self, node, compo_cls, mesh):
        Elt.__init__(self, node, compo_cls)
        self.mesh = mesh

    def signature(self):
        """Return the signature of the mesh referenced"""
        smesh = self.mesh.get_smesh()
        if not self.mesh.has_geom():
            return ""
        try:
            txt = str(smesh.GetMeshPtr())
            txt += str(smesh.NbGroups())
            lgr = smesh.GetGroups()
            for gr in lgr:
                txt += gr.GetName()
        except:
            txt = "no group"
        sign = sha1(txt).hexdigest()
        return sign


class AstkProfil(Elt):
    """An ASTK profil
    """

    def store_profil(self, profil):
        """Store the Astk profil"""
        self.line.write_value("ASTER PROFIL")
        self.line.store_attr("profil", profil)

    def load_profil(self):
        """Load the Astk profil"""
        return self.line.load_attr("profil")


class Section(Elt):
    """An Aster case section having children
    """

    def use(self, compo):
        """Add an element to the section"""
        return compo.build(self)

    def get(self, elt_type):
        """Return the first element matching the given type."""
        elts = self.get_all(elt_type)
        if elts:
            return elts[0]

    def get_all(self, compo_type):
        """Return all the element matching the element type"""
        elts = []
        for elt in self.get_all_elts():
            if issubclass(elt.compo_cls, compo_type):
                elts.append(elt)
        return elts

    def get_all_elts(self):
        """Return all the elements of the section"""
        elts = []
        for node in self.node.get_children():
            elt = load_elt_from_node(node)
            elts.append(elt)
        return elts

    def clear(self):
        """Remove all the elements from the section"""
        for elt in self.get_all_elts():
            elt.remove()

    def clear_only(self, elt_types):
        """Clear only element matching the given element types"""
        for elt_type in elt_types:
            elts = self.get_all(elt_type)
            for elt in elts:
                elt.remove()

    def remove(self):
        """Clear and remove the section"""
        self.clear()
        Elt.remove(self)


class DataSection(Section):
    """Store input data for running an Aster case
    """

    def fill_astk_case(self, astk_case, study_case):
        """Fill the ASTK case (aster.astk.Case) from input data
        stored in this object browser section."""
        for elt in self.get_all_elts():
            log.debug("add element to astk_case : %s", elt)
            elt.fact.add_to(astk_case, study_case, elt)


class AstkParams(Section):
    """Display ASTK configuration in the Salomé tree
    """

    def attach_cfg(self, astk_cfg):
        """Attach the given ASTK configuration to the section"""
        self.clear()
        for key, line in astk_cfg.items():
            self.use(AC.Value(key, line.value))
        self.line.store_attr("cfg", astk_cfg)

    def get_elt(self, key):
        """Return a child element from its key"""
        node = self.node.find_node(key)
        return load_elt_from_node(node)

    def __getitem__(self, key):
        """Read the element value from its key"""
        return self.get_elt(key).read_value()

    def __setitem__(self, key, value):
        """Write the element value for the given key"""
        return self.get_elt(key).write_value(value)

    def get_cfg(self):
        """Fill the Astk configuration (astk.aster.Cfg) with the values
        found in the object browser"""
        astk_cfg = self.line.load_attr("cfg")
        for elt in self.get_all_elts():
            key = elt.read_name()
            astk_cfg[key].value = elt.read_value()
        return astk_cfg

    def fill_astk_case(self, astk_case, study_case):
        """Fill the ASTK case with the configuration found in the object
        browser"""
        log.debug("AstkParams.fill_astk_case")
        astk_case.use(self.get_cfg())


class ResultsSection(Section):
    """The results produced by the Aster solver
    displayed in the Salomé object browser
    """

    def display_from(self, aster_case):
        """Find results on the Aster study case (astk.Case)"""
        self.fact.display_from(aster_case, self)


class Job(astk.Job):
    """Supervise the Aster job and communicate with Salomé
    """

    def __init__(self, astk_case, callback):
        astk.Job.__init__(self, astk_case)
        self._callback = callback

    def get_diag(self):
        """Just return the diagnostic"""
        # this allows to separate 'res_status' and the update of gui objects
        astk.Job.terminate(self)
        return self.res_status(), self.has_results()

    def terminate(self, status=None):
        """Terminate the Aster job supervision"""
        if status is None:
            status = self.get_diag()[0]
        self._callback(status)
        return status


class Case(Section):
    """An Aster study case
    """

    def __init__(self, node, compo_cls, inputs, outputs):
        Section.__init__(self, node, compo_cls)
        self.data = None
        self.results = None

        self._inputs = inputs
        self._outputs = outputs

        self._aster_case = None
        self.update_icon("NEW")


    def write_name(self, name):
        """Write the Aster study case name on the object browser"""
        self.node.write_name(name)

    def use(self, compo):
        """Use the given component"""
        compo_type = compo.__class__
        if compo_type not in self._inputs:
            mess = "The element type '%s' can not be used on this case"
            raise TypeError(mess % compo_type.__name__)
        return self.data.use(compo)

    def get_all(self, elt_type):
        """Return all the elements matching the element type"""
        if issubclass(elt_type, AC.Section):
            return Section.get_all(self, elt_type)
        elif elt_type in self._inputs:
            return self.data.get_all(elt_type)
        elif elt_type in self._outputs:
            all = []
            if self.results:
                all = self.results.get_all(elt_type)
            return all
        else:
            mess = "The element type '%s' can not be get on this case"
            raise TypeError(mess % elt_type.__name__)

    def _build_astk_case_for(self, astk_case_type):
        """Build the ASTK case (aster.astk.Case) for the given astk
        case type"""
        acs = astk.build_case(self.node.read_name(), astk_case_type)
        self.data.fill_astk_case(acs, self)
        self._aster_case = acs
        return acs

    def build_astk_case(self):
        """Build the ASTK case (aster.astk.Case)"""
        raise NotImplementedError

    def run(self):
        """Run the Aster case"""
        log.debug("study.Case.run")
        self.update_icon("PEND")
        log.debug("Case.run: build_astk_case")
        acs = self.build_astk_case()
        job = Job(acs, self._display_results)
        log.debug("Case.run: run case")
        acs.run(job)
        self._build_results()
        self.results.clear()
        self.results.use(AC.JobId(pid=job.pid))
        return job

    def _build_results(self):
        """Build the results section on first call."""
        self.results = AC.ResultsSection().build(self)

    def _display_results(self, status):
        """Display results in the Salome tree"""
        self.update_icon(status.from_astk)
        self.write_value(status.from_astk)
        self.results.display_from(self._aster_case)

    def reset_results(self):
        """Destroy the results and reset the status"""
        if self.results:
            self.results.remove()
            self.results = None
        self.write_value("")

    def get_result(self, result_type):
        """Return a Result object from the Aster solver. If many
        are present, return only the first one."""
        if self._aster_case:
            return self._aster_case.get_result(result_type)

    def copy(self):
        """Copy the Aster study case"""
        std = self.give_aster_study()
        return self.fact.copy_to(std, self)

    def update_icon(self, status):
        """Update icon to reflect the job status"""
        log.debug("AS.Case:update_icon: status=%s", status)
        icon_name = _icon_from_status(status)
        self.line.store_icon(icon_name)

    def signature(self):
        """Compute the signature of this case"""
        sign = ""
        mesh = self.get(aster_s.SMeshEntry)
        if mesh:
            sign += mesh.signature()
        # no mesh
        if sign == "":
            return sign
        comm = self.get(aster_s.CommFile) or self.get(aster_s.CommEntry)
        if comm:
            sign += comm.signature()
        return sign

    def has_changed(self):
        """Compute the new signature of the case and returns if
        it changed since last call."""
        cur_sign = self.line.load_attr("signature")
        new_sign = self.signature()
        log.debug("AS.Case.has_changed:")
        log.debug("old signature : %s", cur_sign)
        log.debug("new signature : %s", new_sign)
        if new_sign == "" or new_sign == cur_sign:
            return False
        self.line.store_attr("signature", new_sign)
        return True


class FromComm(Case):
    """An Aster study case built from at least a command file
    """
    def __init__(self, node, compo_cls, inputs, outputs):
        Case.__init__(self, node, compo_cls, inputs, outputs)
        self.params = None

    def write_name(self, name):
        """Write the name in the object browser and on the ASTK section
        if the element 'name' is found."""
        Case.write_name(self, name)
        astk_cfg = self.params.get_cfg()
        if astk_cfg.has("name"):
            self.params["name"] = name

    def use(self, elt):
        """Use the given element"""
        # XXX configuration should be added differently
        if isinstance(elt, AC.AstkParams):
            self.params.attach_cfg(elt.cfg)
            return self.params
        return Case.use(self, elt)

    def build_astk_case(self):
        """Build the ASTK case (aster.astk.Case) from values found in
        the object browser and retrieve Astk configuration"""
        acs = self._build_astk_case_for(astk.FromComm)
        self.params.fill_astk_case(acs, self)
        return acs


class FromExport(Case):
    """An Aster study case built from an Astk export file
    """

    def build_astk_case(self):
        """Build the ASTK case (aster.astk.Case) from values found in
        the object browser"""
        return self._build_astk_case_for(astk.FromExport)


class FromProfil(Case):
    """An Aster study case built from an ASTK profil (AsterProfil)
    """

    def build_astk_case(self):
        """Build the ASTK case (aster.astk.Case) from values found in
        the object browser"""
        return self._build_astk_case_for(astk.FromProfil)


class Study(Section):
    """The Aster study creating study cases.

    The Aster study is attached to a Salomé study on which it will add
    the Aster component and study cases.
    For testing, the Aster study may create a dedicated Salomé study
    (in this case 'own_std' is True).
    """

    def __init__(self, salome_std, bld=None, own_std=False):
        self.sstd = salome_std
        self._bld = bld
        self.own_std = own_std
        self.is_close = False
        node = salome_std.add_root("ASTER", STUDY, define_compo=True)
        Section.__init__(self, node, self.__class__)
        salome_std.register_on_close(self.close)
        self.line.store_icon("module.png")

    def add_case(self, name, case_type=AC.FromComm):
        """Add an Aster study case"""
        # demande à la partie python de construire l'objet salomé dans l'arbre
        # retourne une instance de study.Case
        return case_type(name).build(self)

    def load_elt_from_entry(self, entry):
        """Load an element from the given entry"""
        node = self.sstd.build_node_from_entry(entry)
        return load_elt_from_node(node)

    def close(self):
        """Close the Aster study on the Salomé server"""
        if not self.is_close:
            self.node.destroy()
            if self.own_std:
                self.sstd.close_salome_study()
            if self._bld:
                self._bld.remove(self)
            self.is_close = True


def load_elt_from_node(node):
    """Load an element from the given entry"""
    fact = find_factory(ST.load_cls(node))
    if fact:
        return fact.load(node)
    else:
        raise TypeError("No element found at the given node")

def attach_study_to(sstd):
    """Attach an Aster study to a Salomé study from SALOMEDS"""
    return Study(ST.SalomeStudy(sstd))

def file_content_signature(fname):
    """Return the signature of the File"""
    sign = ""
    if not osp.isfile(fname):
        return sign
    txt = open(fname, "rb").read()
    sign = sha1(fname+txt).hexdigest()
    return sign

def _icon_from_status(status):
    """Return the icon name from astk status."""
    dico = {}
    for st in ("NEW", "PEND", "RUN", "SUSP", "UNKNOWN", "ENDED", "OK"):
        st = st.lower()
        dico[st] = "status/%s.png" % st
    return dico.get(status.lower(), "unknown")


