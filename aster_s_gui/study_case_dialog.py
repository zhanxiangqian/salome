# -*- coding: utf-8 -*-
"""Dialogs for creating or editing a study case
"""

from PyQt4 import QtGui as qt
from PyQt4 import QtCore as qtc
connect = qtc.QObject.connect
SIG = qtc.SIGNAL
load_fname = qt.QFileDialog.getOpenFileName

import salome

import aster_s
import aster_s.astk as astk
import aster_s.salome_tree as ST

import aster_s_gui
import aster_s_gui.common as GC


class Param(object):
    """Parameter contract for building an Aster case
    """

    def __init__(self, key):
        self.key = key

    def add_to(self, row, suggested_column):
        """Add to the table row with a suggested column index"""
        raise NotImplementedError

    def set_default(self, cfg, pref):
        """Set the default value on the parameter by using the
        aster_s.astk.Cfg configuration of the aster_s_gui.AsterPreferences
        one"""
        raise NotImplementedError

    def build_case(self, std, case, cfg):
        """Build the Aster study case by adding its data"""
        pass

    def edit_case(self, case, cfg):
        """Display the Aster study case data for edition"""
        pass

    def update_case(self, std, case, cfg):
        """Update the Aster study case data after edition"""
        pass


class HiddenParam(Param):
    """Hidden param
    """
    _value = None

    def set_default(self, cfg, pref):
        pass

    def set_value(self, value):
        """Set the value of the parameter"""
        self._value = value

    def build_case(self, std, case, cfg):
        """Set its choice to the Astk configuration"""
        cfg[self.key] = self._value

    def update_case(self, std, case, cfg):
        """Update value"""
        self.build_case(std, case, cfg)


class SingleWidgetParam(Param):
    """A parameter with only one widget
    """

    def __init__(self, key, wid):
        Param.__init__(self, key)
        self._wid = wid

    def connect(self, signal, callback):
        """Connect the widget to the given callback"""
        connect(self._wid, signal, callback)

    def add_to(self, row, column):
        """Add widget to row"""
        return row.place(column, self._wid)


class ChoiceWidgetParam(SingleWidgetParam):
    """Choice widget parameter
    """

    def use(self, choice, default_idx=0):
        """Use the given choice"""
        idx = default_idx
        if idx == -1:
            idx = len(self._choices) - 1
        if choice in self._choices:
            idx = self._choices.index(choice)
        self._wid.setCurrentIndex(idx)

    def get_selected_value(self):
        """Return currently selected entry"""
        return str(self._wid.currentText())


class ChoiceParam(ChoiceWidgetParam):
    """Choice parameter for building Aster case
    """

    def __init__(self, key, choices):
        wid = qt.QComboBox()
        wid.addItems(choices)
        ChoiceWidgetParam.__init__(self, key, wid)
        connect(wid, SIG("currentIndexChanged(int)"), self._update)
        self._choices = choices
        self._enabled_wids = {}

    def register_enabled(self, cidx, wids):
        """Enabled the widgets for the given choice or disabled them
        otherwise"""
        self._enabled_wids[cidx] = wids

    def _update(self, cidx):
        """Update the widgets according to the choice"""
        ewids = self._enabled_wids
        for key in ewids:
            for wid in ewids[key]:
                wid.setEnabled(False)
        for wid in ewids.get(cidx, []):
            wid.setEnabled(True)

    def use_cidxs(self, cidxs):
        """Use only the given choices from their indexs"""
        wid = self._wid
        choices = [self._choices[cidx] for cidx in cidxs]
        wid.clear()
        wid.addItems(choices)

    def set_default(self, cfg, pref):
        """Set the default choice from ASTK configuration"""
        if cfg.has(self.key):
            cidx = self._choices.index(cfg[self.key].value)
            self._wid.setCurrentIndex(cidx)

    def build_case(self, std, case, cfg):
        """Set its choice to the Astk configuration"""
        cfg[self.key] = self._choices[self._wid.currentIndex()]

    def edit_case(self, case, cfg):
        """Display the choice from the Astk configuration for edition"""
        self._wid.setCurrentIndex(self._choices.index(cfg[self.key]))

    def update_case(self, std, case, cfg):
        """Update the choice"""
        self.build_case(std, case, cfg)


class ChoiceEditParam(ChoiceWidgetParam):
    """Present choices or use the user input
    """

    def __init__(self, key):
        wid = qt.QComboBox()
        wid.setEditable(True)
        wid.setInsertPolicy(qt.QComboBox.NoInsert)
        ChoiceWidgetParam.__init__(self, key, wid)
        self._choices = None

    def use_choices(self, choices):
        """Use the given choices on the QComboBox"""
        self._choices = choices
        self._wid.addItems(choices)

    def clear(self):
        """Clear all the choices"""
        self._wid.clear()

    def set_default(self, cfg, pref):
        """Set the default value from ASTK configuration"""
        if cfg.has(self.key):
            self._wid.setEditText(cfg[self.key].value)

    def build_case(self, std, case, cfg):
        """Set the Aster solver version from a given server on the
        study case"""
        cfg[self.key] = self.get_selected_value()

    def edit_case(self, case, cfg):
        """Display the Aster solver version and the given server for 
        edition"""
        self._wid.setEditText(cfg[self.key])

    def update_case(self, std, case, cfg):
        """Update the Aster solver version"""
        self.build_case(std, case, cfg)


class IntParam(SingleWidgetParam):
    """Int parameter for building Aster case
    """

    def __init__(self, key, min=1, max=2**31 - 1):
        wid = qt.QSpinBox()
        wid.setRange(min, max)
        SingleWidgetParam.__init__(self, key, wid)

    def set_default(self, cfg, pref):
        """Set the default choice from ASTK configuration"""
        if cfg.has(self.key):
            self._wid.setValue(cfg[self.key].value)

    def build_case(self, std, case, cfg):
        """Set its value to the Astk configuration"""
        cfg[self.key] = self._wid.value()

    def edit_case(self, case, cfg):
        """Display the value from the Astk configuration for edition"""
        self._wid.setValue(cfg[self.key])

    def update_case(self, std, case, cfg):
        """Update the value"""
        self.build_case(std, case, cfg)


class CheckBox(qt.QCheckBox):
    """Convenient QCheckBox
    """
    check_states = [qtc.Qt.Unchecked, qtc.Qt.Checked]

    def checked(self, checked):
        """Change the Qt state and emit the 'stateChanged(int)' signal"""
        checked = int(checked)
        self.setCheckState(self.check_states[checked])
        self.emit(SIG("stateChanged(int)"), checked)


class SaveResultDatabase(Param):
    """Save result database for building the Aster case
    """

    def __init__(self, key):
        Param.__init__(self, key)
        self._wid = CheckBox("")

    def add_to(self, row, column):
        """Add a QCheckBox to row"""
        return row.place(column, self._wid)

    def set_default(self, cfg, pref):
        """Set the default choice from Salome preferences"""
        self._wid.checked(pref.get(aster_s_gui.SaveBaseResult))

    def build_case(self, std, case, cfg):
        """Tell the Aster case to produce the Stanley result base"""
        if self._wid.isChecked():
            case.use(aster_s.HasBaseResult())

    def edit_case(self, case, cfg):
        """Check the box if HasBaseResult found"""
        has_base = case.get(aster_s.HasBaseResult)
        if has_base:
            self._wid.checked(True)

    def update_case(self, std, case, cfg):
        """Update the study case on HasBaseResult"""
        case.clear_only([aster_s.HasBaseResult])
        self.build_case(std, case, cfg)


class InteractivFollowUp(Param):
    """Interactiv follow up with its check and terminal 
    command parameters
    """

    def __init__(self, key):
        Param.__init__(self, key)
        self._active = CheckBox("")

    def add_to(self, row, column):
        """Add a CheckBox to row"""
        return row.place(column, self._active)

    def set_default(self, cfg, pref):
        """Set the default choice from Salome preferences"""
        self._active.checked(pref.get(aster_s_gui.InteractiveFollowUp))

    def build_case(self, std, case, cfg):
        """Tell the Aster case to set an interactiv follow up"""
        if self._active.isChecked():
            case.use(aster_s.InteractivFollowUp())

    def edit_case(self, case, cfg):
        """Check the box and set the terminal command if
        InteractivFollowUp found"""
        if case.get(aster_s.InteractivFollowUp):
            self._active.checked(True)

    def update_case(self, std, case, cfg):
        """Remove the previous InteractivFollow up if found and build
        a new one"""
        case.clear_only([aster_s.InteractivFollowUp])
        self.build_case(std, case, cfg)


class SolverSelection(object):
    """Select the Aster solver version on a given server 
    by using ASTK
    """

    def __init__(self, server, login, version, mode):
        button = qt.QPushButton(u"Refresh servers")
        connect(button, SIG("clicked()"), self.query_astk_servers_with_refresh)
        server.connect(SIG("activated(int)"), self.server_changed)
        sig = SIG("editTextChanged(const QString&)")
        server.connect(sig, self.server_edited)

        self.button = button
        self._server = server
        self._login = login
        self._version = version
        self._mode = mode
        self._servs = None

    def server_changed(self, serv_idx):
        """Update the server dependant items"""
        serv = self._servs[serv_idx]
        self.show_aster_version(serv)
        self._login.set_value(serv['login'])
        self.update_modes(serv)

    def show_aster_version(self, serv):
        """Show the aster versions found for a given server"""
        combo = self._version
        prev = combo.get_selected_value()
        combo.clear()
        versions = serv.get("vers")
        if versions:
            versions = versions.split()
            combo.use_choices(versions)
            combo.use(prev, default_idx=-1)
    
    def update_modes(self, serv):
        """Update the mode choices according to the given server"""
        combo = self._mode
        prev = combo.get_selected_value()
        cidxs = [0]
        if serv.get("batch") == "oui":
            cidxs.append(1)
        combo.use_cidxs(cidxs)
        combo.use(prev, default_idx=0)

    def server_edited(self, text):
        """The server is manually edited, default choices must be enabled
        """
        self._mode.use_cidxs([0, 1])

    def query_astk_servers_with_refresh(self):
        """Query the Astk servers forcing refresh"""
        self.query_astk_servers(force_refresh=True)

    def query_astk_servers(self, force_refresh=False):
        """Query the Astk servers"""
        combos = [self._server, self._version]
        for combo in combos:
            combo.clear()
        servs = astk.find_servers(force_refresh=force_refresh)
        serv_names = [serv["nom_complet"] for serv in servs]
        combos[0].use_choices(serv_names)
        self._servs = servs
        
        serv_idx = 0
        if "localhost" in serv_names:
            serv_idx = serv_names.index("localhost")
            combos[0].use("localhost")
        if servs:
            self.server_changed(serv_idx)

    def check_depends(self):
        """Check fields consistency"""
        combo = self._server
        serv = combo.get_selected_value()
        serv_idx = 0
        if serv in combo._choices:
            serv_idx = combo._choices.index(serv)
        self.server_changed(serv_idx)


def create_loader(icon, callback, entry):
    """Create a loader made of a button and an entry for selecting data"""
    loader = qt.QWidget()
    lay = qt.QHBoxLayout(loader)
    lay.addWidget(GC.create_icon_button(icon, callback))
    lay.addWidget(entry)
    return loader


class DataBuilder(object):
    """Build Aster case data from selection
    """
    sel_mess = "The selected object browser entry '%(entry)s' " \
               "does not seem to hold a %(obj_desc)s" 

    def __init__(self, mod):
        self._mod = mod
        self.fname_entry = qt.QLineEdit()
        lab = qt.QLabel()
        lab.setFrameStyle(qt.QLabel.Panel)
        self.brw_entry = lab
        self._brw_node = None

    def load_fname(self):
        """Load a filename from disk"""
        qline_entry = self.fname_entry
        fname = load_fname(qline_entry, "Loading file from disk")
        if fname:
            qline_entry.setText(fname)

    def write_brw_entry(self, validate_node, mess, mess_desc):
        """Use the browser entry if valid"""
        mod = self._mod
        node = mod.stracker.give_node()
        if node:
            entry = node.entry
            if validate_node(node):
                self._brw_node = node
                self.brw_entry.setText(node.read_name())
            else:
                mess_desc["entry"] = entry
                mod.launch(GC.ERROR, mess % mess_desc)

    def load_brw_entry(self):
        """Load the selected node on the object browser"""
        raise NotImplementedError

    def build_case_from_fname(self, std, case):
        """Build the Aster case from a file from disk"""
        raise NotImplementedError

    def build_case_from_brw_entry(self, std, case):
        """Build the Aster case from an object browser entry"""
        raise NotImplementedError

    def edit_fname(self, case):
        """Display filename if found on Aster case"""
        raise NotImplementedError

    def edit_entry(self, case):
        """Display the browser entry if found and return True in that
        case"""
        raise NotImplementedError

    def update_case_from_fname(self, std, case):
        """Update the filename or add it to the case"""
        raise NotImplementedError

    def update_case_from_brw_entry(self, std, case):
        """Update the browser entry"""
        raise NotImplementedError


def is_valid_comm_file(node):
    """Validate if the given node holds a command file"""
    return (ST.load_cls(node) is aster_s.CommFile) or ST.is_eficas_file(node)


class CommBuilder(DataBuilder):
    """Command file builder
    """

    def load_brw_entry(self):
        """Use the given entry only if a Command file is selected """
        mess_desc = {"obj_desc" : "command file"}
        self.write_brw_entry(is_valid_comm_file, self.sel_mess, mess_desc)

    def build_case_from_fname(self, std, case):
        """Add a command file from disk to the Aster case"""
        fname = str(self.fname_entry.text())
        case.use(aster_s.CommFile(fname))

    def build_case_from_brw_entry(self, std, case):
        """Add a command file from the object browser to the Aster case"""
        node = self._brw_node
        if node:
            if ST.is_eficas_file(node):
                efile = ST.attach_eficas_file(node)
                case.use(aster_s.CommFile(efile.read_fname()))
            else:
                case.use(aster_s.CommEntry(node.entry))

    def edit_fname(self, case):
        """Display the command file if found"""
        comm = case.get(aster_s.CommFile)
        if comm:
            fname = comm.read_fname() or ""
            self.fname_entry.setText(fname)
            return True

    def edit_entry(self, case):
        """Display the command file entry if found"""
        comm = case.get(aster_s.CommEntry)
        if comm:
            node = comm.node.give_source()
            self._brw_node = node
            self.brw_entry.setText(node.read_name())
            return True

    def update_case_from_fname(self, std, case):
        """Update the command file or add it to the case"""
        case.clear_only([aster_s.CommEntry])
        comm = case.get(aster_s.CommFile)
        if comm:
            comm.sfile.write_fname(str(self.fname_entry.text()))
        else:
            self.build_case_from_fname(std, case)

    def update_case_from_brw_entry(self, std, case):
        """Clean and create a new command file entry"""
        case.clear_only([aster_s.CommEntry, aster_s.CommFile])
        self.build_case_from_brw_entry(std, case)


def is_valid_mesh(node):
    """Validate if the given node holds a mesh"""
    return ST.is_mesh(node) or (ST.load_cls(node) is aster_s.MedFile)


class MeshBuilder(DataBuilder):
    """Mesh file builder using a med file or a mesh from the SMESH
    component
    """

    def load_brw_entry(self):
        """Use the given entry only if a mesh is selected """
        mess_desc = {"obj_desc" : "mesh"}
        mess = self.sel_mess + " or the SMESH component must be activated"
        self.write_brw_entry(is_valid_mesh, mess, mess_desc)

    def build_case_from_fname(self, std, case):
        """Add a med file to the aster case"""
        fname = str(self.fname_entry.text())
        case.use(aster_s.MedFile(fname))

    def build_case_from_brw_entry(self, std, case):
        """Add a mesh from the object browser entry"""
        node = self._brw_node
        if not node:
            return
        # ST.load_cls(node) may not work when the node comes  
        # from the SMESH component because the SMESH component 
        # may store its own data in SALOMEDS.AttributeFileType
        if ST.is_mesh(node):
            case.use(aster_s.SMeshEntry(node.entry))
        else:
            case.use(aster_s.MedEntry(node.entry))

    def edit_fname(self, case):
        """Display the med file if found"""
        med = case.get(aster_s.MedFile)
        if med:
            fname = med.read_fname() or ""
            self.fname_entry.setText(fname)
            return True

    def edit_entry(self, case):
        """Display the mesh entry if found"""
        for elt_type in [aster_s.MedEntry, aster_s.SMeshEntry]:
            elt = case.get(elt_type)
            if elt:
                node = elt.node.give_source()
                self._brw_node = node
                self.brw_entry.setText(node.read_name())
                return True

    def update_case_from_fname(self, std, case):
        """Update the med file or add it to the case"""
        case.clear_only([aster_s.MedEntry, aster_s.SMeshEntry])
        med = case.get(aster_s.MedFile)
        if med:
            med.sfile.write_fname(str(self.fname_entry.text()))
        else:
            self.build_case_from_fname(std, case)

    def update_case_from_brw_entry(self, std, case):
        """Clean and create a new mesh entry"""
        case.clear_only([aster_s.MedEntry, aster_s.SMeshEntry, aster_s.MedFile])
        self.build_case_from_brw_entry(std, case)


class DataSelection(Param):
    """Allow to select a file from the Object browser 
    or a QFileDialog
    """

    def __init__(self, key, data_builder):
        Param.__init__(self, key)
        self._data_builder = data_builder

        self._selector = qt.QComboBox()
        self._loaders = [
            create_loader("load-browser-entry.png",
                          data_builder.load_brw_entry,
                          data_builder.brw_entry),
            create_loader("load-file.png",
                          data_builder.load_fname,
                          data_builder.fname_entry),
        ]

    def add_to(self, row, column):
        """Add the selection widgets to the row"""
        selector = self._selector
        selector.addItems(["from object browser", "from disk"])
        connect(selector, SIG("activated(int)"), self._switch_loader)
        self._switch_loader(0)

        wid = qt.QWidget()
        lay = qt.QHBoxLayout(wid)
        lay.addWidget(selector)
        for loader in self._loaders:
            lay.addWidget(loader)
        return row.place(1, wid)

    def _switch_loader(self, idx):
        """Switch the data loader"""
        loaders = self._loaders
        for loader in loaders:
            loader.hide()
        loaders[idx].show()

    def set_default(self, cfg, pref):
        """Does nothing for files"""
        pass

    def build_case(self, std, case, cfg):
        """Add the data from the current loader"""
        bld = self._data_builder
        if self._selector.currentIndex():
            bld.build_case_from_fname(std, case)
        else:
            bld.build_case_from_brw_entry(std, case)

    def edit_case(self, case, cfg):
        """Display filename or browser entry for edition"""
        bld = self._data_builder
        bld.edit_entry(case)
        if bld.edit_fname(case):
            self._selector.setCurrentIndex(1)
            self._switch_loader(1)

    def update_case(self, std, case, cfg):
        """Update the filenames else destroy and build new entries"""
        bld = self._data_builder
        if self._selector.currentIndex():
            bld.update_case_from_fname(std, case)
        else:
            bld.update_case_from_brw_entry(std, case)


class Row(object):
    """Table row of the GroupBox
    """

    def __init__(self, ridx, grid_layout):
        self._ridx = ridx
        self._lay = grid_layout

    def place(self, cidx, wid, span=1):
        """Place the given widget at the column index"""
        self._lay.addWidget(wid, self._ridx, cidx, 1, span)
        return wid

    def place_label(self, cidx, label, span=1):
        """Place the label at the column index"""
        return self.place(cidx, qt.QLabel(label), span)

    def place_param(self, cidx, param):
        """Ask the given parameter to place itself into the row"""
        return param.add_to(self, cidx)


class GroupBox(object):
    """Group of parameters displayed in table rows 
    """

    def __init__(self, title):
        self._grp = qt.QGroupBox(title)
        self._lay = qt.QGridLayout(self._grp)
        self._rows_nb = 0

    def add_row(self):
        """Add a line to the given column"""
        row = Row(self._rows_nb, self._lay)
        self._rows_nb += 1
        return row

    def add_to(self, layout):
        """Add the group box to the parent layout"""
        layout.addWidget(self._grp)


class Groups(object):
    """The list of groups
    """

    def __init__(self):
        self._grps = []

    def add(self, title):
        """Add a group"""
        grp = GroupBox(title)
        self._grps.append(grp)
        return grp

    def add_to(self, main_layout):
        """Add all the groups to the main layout"""
        container = qt.QWidget()
        lay = qt.QVBoxLayout(container) 
        for grp in self._grps:
            grp.add_to(lay)

        scroll = qt.QScrollArea()
        scroll.setFrameStyle(qt.QFrame.NoFrame)
        scroll.setWidgetResizable(True)
        scroll.setWidget(container)
        main_layout.addWidget(scroll)


class Parameters(object):
    """All the parameters building an Aster study case
    """

    def __init__(self):
        self._lst = []
        self._dct = {}

    def add(self, param):
        """Add a parameter, its key must be unique"""
        self._lst.append(param)
        self._dct[param.key] = param 

    def __getitem__(self, key):
        """Return a parameter from its key"""
        return self._dct[key]

    def set_default(self, cfg, pref):
        """Set the default value to every parameters group"""
        for param in self._lst:
            param.set_default(cfg, pref)

    def build_case(self, std, case):
        """Build the Aster study case for every parameter"""
        cfg = case.get(aster_s.AstkParams)
        for param in self._lst:
            param.build_case(std, case, cfg)

    def edit_case(self, case):
        """Edit the Aster study case"""
        cfg = case.get(aster_s.AstkParams)
        for param in self._lst:
            param.edit_case(case, cfg)

    def update_case(self, std, case):
        """Update the Aster study case after edition"""
        cfg = case.get(aster_s.AstkParams)
        for param in self._lst:
            param.update_case(std, case, cfg)


class StudyCaseDialog(qt.QDialog):
    """Dialog for a study case
    """

    def __init__(self, mod):
        # Setting the parent after, by setParent seems to give a different 
        # behavior as described in the documentation: 
        # 'The parent argument, if not None, causes self to be owned 
        # by Qt instead of PyQt'.
        qt.QDialog.__init__(self, mod.give_qtwid())
        self._mod = mod
        params = Parameters()
        self._params = params
        self._define_params()
        self._slv_selection = SolverSelection(
                                params["server"],
                                params["login"],
                                params["aster-version"],
                                params["mode"], 
                                )
        self._name = qt.QLineEdit()
        self._build_gui()

    def _define_params(self):
        """Define the parameters building the Aster case"""
        mod = self._mod
        params = self._params

        params.add(DataSelection("comm", CommBuilder(mod)))
        params.add(DataSelection("mesh", MeshBuilder(mod)))

        params.add(ChoiceEditParam("server"))
        params.add(HiddenParam("login"))
        params.add(ChoiceEditParam("aster-version"))
        params.add(ChoiceParam("mode", ["interactif", "batch"]))
        params.add(InteractivFollowUp("interactiv-follow-up"))

        params.add(IntParam("memory"))
        params.add(IntParam("time"))
        params.add(IntParam("proc-nb"))
        params.add(SaveResultDatabase("save-base"))

    def _build_gui(self):
        """Build its gui interface"""
        params = self._params
        mlay = qt.QVBoxLayout(self)
        
        grps = Groups()
        grp = grps.add(u"Study case definition")
        row = grp.add_row()
        row.place_label(0, u"Name")
        row.place(1, self._name)
        row = grp.add_row()
        row.place_label(0, u"Command file")
        row.place_param(1, params["comm"])
        row = grp.add_row()
        row.place_label(0, u"Mesh")
        row.place_param(1, params["mesh"])

        grp = grps.add(u"ASTK services")
        row = grp.add_row()
        row.place_label(0, u"Server")
        row.place_param(1, params["server"])
        row.place_label(2, u"Aster version")
        row.place_param(3, params["aster-version"])
        row.place(4, self._slv_selection.button)
        row = grp.add_row()
        row.place_label(0, u"Execution mode")
        mode = params["mode"]
        row.place_param(1, mode)
        lab = row.place_label(2, u"Interactive follow up")
        wid = row.place_param(3, params["interactiv-follow-up"])
        mode.register_enabled(0, [lab, wid])

        grp = grps.add(u"Solver prameters")
        row = grp.add_row()
        row.place_label(0, u"Total memory (MB)")
        row.place_param(1, params["memory"])
        row.place_label(2, u"Time (s)")
        row.place_param(3, params["time"])
        row = grp.add_row()
        row.place_label(0, u"CPU number")
        row.place_param(1, params["proc-nb"])
        row.place_label(2, u"Save result database")
        row.place_param(3, params["save-base"])

        DBox = qt.QDialogButtonBox
        bbox = DBox()
        for but_type in [DBox.Ok, DBox.Cancel]:
            bbox.addButton(but_type)
        connect(bbox, SIG("accepted()"), self.build_case)
        connect(bbox, SIG("rejected()"), self.deleteLater)

        grps.add_to(mlay)
        mlay.addWidget(bbox)

    def check_depends(self):
        """Check dependencies between fields"""
        self._slv_selection.check_depends()

    def give_name(self):
        """Return the given study case name"""
        mod = self._mod
        name = str(self._name.text())
        if not name:
            mod.launch(GC.ERROR, u"Empty case name not accepted")
            return
        std = mod.give_aster_study()
        names = [case.read_name() for case in std.get_all(aster_s.Case)]
        if name in names:
            mod.launch(GC.ERROR, u"Case '%s' already exists" % name)
            return
        return name

    def build_case(self):
        """Build a study case from given data"""
        raise NotImplementedError

    def run(self):
        """Run the dialog and register it as a module children"""
        mod = self._mod
        if not mod.testing:
            self.show()

    def destroy(self):
        """Update GUI and destroy the dialog"""
        self._mod.update()
        self.deleteLater()


class StudyCaseCreator(StudyCaseDialog):
    """Build a new study case
    """

    def __init__(self, mod):
        StudyCaseDialog.__init__(self, mod)
        self._name.setText("new_case")
        self._params.set_default(aster_s.build_default_cfg(), 
                                 aster_s_gui.AsterPreferences())
        self._slv_selection.query_astk_servers()

    def build_case(self):
        """Build a new study case from dialog data"""
        name = self.give_name()
        if name:
            std = self._mod.give_aster_study()
            case = std.add_case(name)
            self._params.build_case(std, case)
            salome.sg.updateObjBrowser(0)
            self.destroy()


class StudyCaseEditor(StudyCaseDialog):
    """Edit a study case
    """

    def __init__(self, mod, case):
        StudyCaseDialog.__init__(self, mod)
        self._case = case
        self._name.setText(case.read_name())
        self._slv_selection.query_astk_servers()
        self._params.edit_case(case)
        self.check_depends()

    def build_case(self):
        """Build the case by replacing old data with dialog ones"""
        case = self._case
        case.reset_results()
        name = str(self._name.text())
        # name has been edited
        if name != case.read_name():
            name = self.give_name()
        if name:
            case.write_name(name)
            std = self._mod.give_aster_study()
            self._params.update_case(std, case)
            #salome.sg.updateObjBrowser(0)
            self.destroy()


class RenameEditor(qt.QDialog):
    """Rename a study case"""
    def __init__(self, mod, case):
        self._mod = mod
        self._case = case
        qt.QDialog.__init__(self, mod.give_qtwid())
        self.setWindowTitle(self.tr("TLT_RENAME"))
        vlay = qt.QVBoxLayout(self)
        ledit = qt.QLineEdit()
        ledit.setText(case.read_name())
        but = qt.QDialogButtonBox(qt.QDialogButtonBox.Ok | qt.QDialogButtonBox.Cancel)
        wid = qt.QWidget()
        hlay = qt.QHBoxLayout(wid)
        hlay.addWidget(qt.QLabel("Name:"))
        hlay.addWidget(ledit)
        vlay.addWidget(wid)
        vlay.addWidget(but)
        self.ledit = ledit
        connect(but, SIG("accepted()"), self.set_newname)
        connect(but, SIG("rejected()"), self.deleteLater)

    def set_newname(self):
        """Change name"""
        new = str(self.ledit.text())
        self._case.write_name(new)
        self._mod.update()
        self.deleteLater()

