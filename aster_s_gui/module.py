# -*- coding: utf-8 -*-
"""Define the Aster module graphical user interface for Salomé
"""
import os
import re
import traceback
import subprocess as SP

from PyQt4 import QtGui as qt
from PyQt4 import QtCore as qtc
connect = qtc.QObject.connect
SIG = qtc.SIGNAL

import salome
import salome_utils
import SalomePyQt as SQT

import aster_s
from aster_s.utils import Singleton, log_gui
import aster_s.study as AS
import aster_s.salome_tree as ST

import aster_s_gui
from aster_s_gui.common import (
    ERROR,
    INFO,
    )
from aster_s_gui.study_case_dialog import (
    StudyCaseCreator,
    StudyCaseEditor,
    RenameEditor,
    )
from aster_s_gui.job_supervision import RunningJobs

#import smeca_utils.gui_utils as SGU


class Actions(object):
    """Possible actions for the Aster module
    """
    start_idx = 10940

    def __init__(self, mod):
        self._mod = mod
        self._action_callbacks = {}
        self._actions = {}
        self._current_idx = self.start_idx

    def add(self, key, name, callback):
        """Create an action and store its callback.
        The callback function is supposed to have the following signature::

            callback(mod)

        mod being the Aster module.
        """
        idx = self._current_idx
        self._action_callbacks[idx] = callback
        self._current_idx += 1

        action = Action(idx, name)
        self._actions[key] = action
        return action

    def __getitem__(self, key):
        """Return the action from its key if found else return None"""
        return self._actions.get(key)

    def run(self, idx):
        """Run the action from its index"""
        self._action_callbacks[idx](self._mod)


class SalomeGuiCompo(object):
    """Salome gui component supposed to build a widget.
    """

    def build(self, sqt):
        """Build the Salomé widget"""
        raise NotImplementedError

    def add_to_popup(self, popup, sqt):
        """Add Salomé widget to the Qt popup menu"""
        popup.addAction(self.build(sqt))


class Action(SalomeGuiCompo):
    """A Salomé action
    """

    def __init__(self, sidx, name):
        self._sidx = sidx
        self._name = name
        self._tooltip = ""
        self._icon = None
        self._shortcut = None
        self._is_built = False

    def use_tooltip(self, tooltip):
        """Use the given tooltip on the action"""
        self._tooltip = tooltip

    def use_icon(self, icon):
        """Use the given icon for the action"""
        self._icon = icon

    def use_shortcut(self, shortcut):
        """Use the given shortcut for the action"""
        self._shortcut = shortcut

    def _build_widget(self, sqt):
        """Build the Salomé action widget"""
        if self._icon:
            sqt_action = sqt.createAction(self._sidx,
                                    self._name,
                                    self._name,
                                    self._tooltip,
                                    self._icon)
        else:
            sqt_action = sqt.createAction(self._sidx,
                                    self._name,
                                    self._name,
                                    self._tooltip)
        if self._shortcut:
            sqt_action.setShortcut(qt.QKeySequence(self._shortcut))
        return sqt_action

    def build(self, sqt):
        """Build the Salomé action"""
        if not self._is_built:
            self._is_built = True
            return self._build_widget(sqt)
        else:
            return sqt.action(self._sidx)


class Separator(SalomeGuiCompo):
    """A GUI separator
    """

    def build(self, sqt):
        """Build a Salomé separator"""
        return sqt.createSeparator()


SEP = Separator()

class Page():#added by zxq at 2017/1/9
    def __init__(self, page_name, group_name, action_names):#one page onlg have one group
        self._page_name = page_name
        self._group_name = group_name
        self._action_names = action_names

    def add_action(self, action):
        """Add an action to the menu"""
        self._actions.append(action)

    def build(self, sqt, actions):
        """Add a menu to the parent one"""
        pageid = sqt.createMenu(self._page_name, -1, -1, -1, 3)
        groupid = sqt.createMenu(self._group_name, pageid, -1)
        for name in self._action_names:
            salome_widget = actions.__getitem__(name).build(sqt)
            sqt.createMenu(salome_widget, groupid, -1, -1, 3)
        
class Menu(SalomeGuiCompo):
    """A submenu of the main menu
    """

    def __init__(self, sidx, name):
        self._sidx = sidx
        self._name = name
        self._actions = []

    def add_action(self, action):
        """Add an action to the menu"""
        self._actions.append(action)

    def build(self, sqt):
        """Add a menu to the parent one"""
        menu = sqt.createActionGroup(self._sidx)
        menu.setText(self._name)
        #menu.setUsesDropDown(True)
        for action in self._actions:
            menu.add(action.build(sqt))
        return menu


class MainMenu(object):
    """The main menu added to the MenuBar
    """
    menu_start_idx = 90

    def __init__(self, name):
        self._name = name
        self._menu_idx = self.menu_start_idx + 1
        self._components = []
        self._pages = []
    def add_action(self, action):
        """Add an action to the menu"""
        self._components.append(action)

    def add_menu(self, name):
        """Add a submenu"""
        menu = Menu(self._menu_idx, name)
        self._components.append(menu)
        self._menu_idx += 1
        return menu

    def add_page(self, page):
        self._pages.append(page)
        
    def build(self, sqt):
    	  for ipage in self._pages:
    	      ipage.build(sqt)
        #"""Build the menu in the activate process"""
        #midx = sqt.createMenu("Operations", -1, -1, -1, 3)
        #group = sqt.createMenu("Solver", midx, -1)
        #print self._components
        #for compo in self._components:
            #salome_widget = compo.build(sqt)
            #sqt.createMenu(salome_widget, group, -1, -1, 3)


class ToolBar(object):
    """The toolbar for Aster component
    """

    def __init__(self, name):
        self._name = name
        self._components = []

    def add(self, compo):
        """Add a Salomé widget to the toolbar"""
        self._components.append(compo)

    def build(self, sqt):
        """Build the toolbar in the activate process"""
        #tidx = sqt.createTool(self._name)
        #for compo in self._components:
        #    salome_widget = compo.build(sqt)
        #    sqt.createTool(salome_widget, tidx)


class PopupMenu(object):
    """Build a popup menu
    """

    def __init__(self):
        self._components = []

    def add(self, compo):
        """Add a component to the popup menu"""
        self._components.append(compo)

    def fill(self, popup, sqt):
        """Fill the Qt popup menu with Salome actions"""
        for compo in self._components:
            compo.add_to_popup(popup, sqt)


def create_popup_menu(compos):
    """Create a popup menu filled with the given components"""
    popup = PopupMenu()
    for compo in compos:
        popup.add(compo)
    return popup


class PopupMenuBuilder(object):
    """Build popup menus for a given class
    """

    def __init__(self):
        self._menus = {}

    def register(self, cls, pmenu):
        """Register a popup menu for a given class"""
        self._menus[cls] = pmenu

    def build_for(self, cls, popup, sqt):
        """Build the Qt popup menu for the given class if registered"""
        pmenu = self._menus.get(cls)
        if pmenu:
            pmenu.fill(popup, sqt)


class SelectedElementCallback(object):
    """Run the given callback by loading the selected element.
    """

    def __init__(self, stracker, clss, callback):
        self._stracker = stracker
        self._clss = clss
        self._callback = callback

    def __call__(self, mod):
        """Run the given callback"""
        node = self._stracker.give_node()
        if node and (ST.load_cls(node) in self._clss):
            self._callback(mod, AS.load_elt_from_node(node))


class SelectionTracker(object):
    """Track the object browser selection entries.
    """

    def __init__(self, mod):
        self._mod = mod

    def give_nodes(self):
        """Return the selected nodes from aster_s.salome_tree.Node"""
        sgs = salome.sg
        sstd = self._mod.give_salome_study()
        nodes = []
        for idx in xrange(sgs.SelectedCount()):
            entry = sgs.getSelected(idx)
            nodes.append(sstd.build_node_from_entry(entry))
        return nodes

    def give_node(self):
        """Return the selected node or None if many nodes are selected."""
        nodes = self.give_nodes()
        if len(nodes) == 1:
            return nodes[0]

    def wrap(self, clss, callback):
        """Wrap the given callback by passing the corresponding element.
        The callback will be run only if the selected node matchs the
        given classes. The callback signature needs to be::

            callback(mod, elt)

        """
        return SelectedElementCallback(self, clss, callback)


def add_study_case(mod):
    """Add an Aster study case"""
    creator = StudyCaseCreator(mod)
    creator.run()
    return creator

def edit(mod, case):
    """Edit study case"""
    if mod.running_jobs.is_busy(case.read_name()):
        return
    editor = StudyCaseEditor(mod, case)
    editor.run()
    return editor

def copy(mod, case):
    """Copy study case"""
    if mod.running_jobs.is_busy(case.read_name()):
        return
    case.copy()
    mod.update()

def remove(mod, case):
    """Remove study case"""
    if mod.running_jobs.is_busy(case.read_name()):
        return
    case.remove()
    mod.update()

def rename(mod, case):
    """Rename study case"""
    if mod.running_jobs.is_busy(case.read_name()):
        return
    dia = RenameEditor(mod, case)
    dia.show()

def run(mod, case):
    """Run study case"""
    name = case.read_name()
    log_gui.debug("run: case name=%s", name)
    if mod.running_jobs.is_busy(name):
        return
    comm = case.get(aster_s.CommFile) or case.get(aster_s.CommEntry)
    if comm is None:
        mod.launch(INFO, "This case has no command file!")
        return
    if case.has_changed():
        log_gui.info("The mesh is updating...")
        update_mesh(mod, case, silent=True)
    else:
        log_gui.debug("No mesh update required.")
    try:
        job = case.run()
        mod.running_jobs.add(name, job, refresh_time=2000.)
        case.write_value("RUNNING")
        mod.loginfo("Job '%s' submitted" % name)
    except EnvironmentError, error:
        job = None
        case.write_value("SUBMISSION ERROR")
        mod.loginfo("Submission failed")
        log_gui.debug("Traceback of failure:\n%s", traceback.format_exc())
    mod.update()
    return job

def stop(mod, case):
    """Stop study case"""
    rjobs = mod.running_jobs
    name = case.read_name()
    log_gui.debug("stop: case name=%s", name)
    if not rjobs.is_free(name):
        rjobs.stop(name)

def status(mod, case):
    """Ask study case status"""
    lines = []
    name = case.read_name()
    if mod.running_jobs.has(name):
        log_gui.debug("status: case name=%s is running", name)
        lines.append(u"The study case is running")
    else:
        lines.append(u"The study case is not running")
        astk_status = case.read_value()
        log_gui.debug("status: case name=%s is ended with status=%s", name, astk_status)
        if astk_status is not None:
            lines.append(u"The result given by ASTK is '%s'" % astk_status)
    mod.launch(INFO, os.linesep.join(lines))

def run_astk_tool(mod, case=None):
    """Run the ASTK client"""
    from_gui = salome_utils.getORBcfgInfo()[1:3]
    log_gui.debug("run_astk_tool: from_gui=%s", from_gui)
    aster_s.run_astk(case, from_gui)

def run_eficas_tool(mod, felt=None):
    """Run the Eficas editor"""
    fname = None
    if felt:
        fname = felt.read_fname()
    log_gui.debug("run_eficas_tool: filename=%s", fname)
    aster_s_gui.run_eficas(com_fname=fname)

def run_stanley_tool(mod, base_elt, force_local=True):
    """Run the Stanley explorator"""
    aster_version = None
    server = None
    res_node = base_elt.node.parent
    if res_node:
       case_node = res_node.parent
       if case_node:
           case = AS.load_elt_from_node(case_node)
           aster_version = case.get(aster_s.AstkParams)["aster-version"]
           server        = case.get(aster_s.AstkParams)["server"]
    dname = base_elt.read_dname()
    log_gui.debug("run_stanley_tool: dname=%s aster_version=%s server=%s",
                  dname, aster_version, server)
    if dname is not None:
        aster_s.run_stanley(dname, aster_version, server, force_local)

def _run_wiz(wiz_module, mod):
    """Create and run the given wizard"""
    wiz = wiz_module.create_wizard(mod)
    wiz.run()
    return wiz

def run_linear_elastic(mod):
    """Run wizard on linear elastic"""
    from aster_s_gui.wizards import linear_static as LS
    return _run_wiz(LS, mod)

def run_modal_analysis(mod):
    """Run wizard on modal analysis"""
    from aster_s_gui.wizards import modal_analysis as MA
    return _run_wiz(MA, mod)

def run_linear_thermic(mod):
    """Run wizard on linear thermic"""
    from aster_s_gui.wizards import linear_thermic as LT
    return _run_wiz(LT, mod)

def run_XFEM(mod):
    """Run wizard on XEFM"""
    from aster_s_gui.wizards import XFEM as XF
    return _run_wiz(XF, mod)

def run_fatigue_analysis(mod):
    """Run wizard on fatigue analysis"""
    from aster_s_gui.wizards import fatigue_analysis as FA
    return _run_wiz(FA, mod)
    
def read_as_text(mod, sfile):
    """Read as a text file"""
    content = ""
    fname = sfile.read_fname()
    #peter.zhang, for cygwin
    fname = fname.replace('\\', '/')
    fname = fname.replace('/cygdrive/', '')
    if fname.find(':/') < 0:
        fname = fname.replace('/', ':/', 1)
    log_gui.debug("read_as_text: filename = %s", fname)
    if fname:
        fid = open(fname)
        content = fid.read()
        fid.close()

    dia = qt.QDialog(mod.give_qtwid())
    dia.setSizePolicy(qt.QSizePolicy.Maximum, qt.QSizePolicy.Maximum) #XXX does not work!
    lay = qt.QVBoxLayout(dia)

    brw = qt.QTextBrowser()
    brw.setPlainText(content)
    lay.addWidget(brw)

    but = qt.QPushButton("Close")
    connect(but, SIG("clicked()"), dia.deleteLater)
    lay.addWidget(but)
    #dia.resize(dia.size())
    dia.show()

def edit_as_text(mod, comm_file):
    """Edit as a text file"""
    fname = comm_file.read_fname()
    if fname:
        pref = aster_s_gui.AsterPreferences()
        editor_cmd = pref.get(aster_s_gui.EditorCommand)
        if editor_cmd == "":
            mess = u"The editor command is not defined " \
                   u"for the Aster module in File -> Preferences."
            mod.launch(ERROR, mess)
            return
        cmd = [editor_cmd, fname]
        try:
            popen = SP.Popen(cmd)
        except OSError:
            mess = u"The editor command '%s' has failed" % u" ".join(cmd)
            mod.launch(ERROR, mess)

def update_mesh(mod, case, silent=False):
    """Update mesh using eficas"""
    comm = case.get(aster_s.CommFile) or case.get(aster_s.CommEntry)
    if not comm:
        mod.launch(ERROR, "The case has no command file")
        return
    smesh = case.get(aster_s.SMeshEntry)
    if not smesh:
        mod.launch(ERROR, "The case has no SMESH object")
        return
    aster_version = case.get(aster_s.AstkParams)["aster-version"]
    grps = None
    prev = None
    for vers in (aster_version, aster_s.ASTER_REFVERSION):
        if prev is not None:
            log_gui.warn("update-mesh failed using version '%s', try with '%s'.", prev, vers)
        try:
            log_gui.debug("update_mesh: call list_groups_with_eficas(%s, %s)",
                          comm.read_fname(), vers)
            grps = aster_s_gui.list_groups_with_eficas(comm.read_fname(), vers)
        except Exception, e:
            # ignore all eficas failure
            print "Traceback of failure:\n%s" % e
            log_gui.debug("Traceback of failure:\n%s", traceback.format_exc())
        if grps is not None:
            break
        prev = vers
    if not grps:
        if not silent:
            mod.launch(INFO, "No groups found by Eficas on the command file")
        return
    mesh = smesh.mesh
    if not mesh.has_geom():
        mod.launch(ERROR, "The mesh has no geometry")
        return
    if mesh.update_from(grps):
        mod.update()
    else:
        if not silent:
            mod.launch(INFO, "No new group created")


def run_tests(mod):
    """Run all of the automatic tests"""
    from aster_gui_tests import run_tests
    run_tests(mod)


class GuiBuilder(Singleton):
    """Build a single SalomePyQt instance and store for each
    study the corresponding Aster module
    """

    def init(self):
        """Initialize the singleton"""
        sqt = SQT.SalomePyQt()
        if sqt.getDesktop() is None:
            mess = "This script needs to be run from the Salome GUI menu " \
                   "by using 'File -> Load Script'."
            raise ValueError(mess)
        self.sqt = sqt
        self._mods = {}

    def is_active(self, module):
        """Test if the given module is active"""
        return (module.name == str(self.sqt.getActiveComponent()))

    def give(self, qt_cls):
        """Return all widgets of the given qt class children of the
        main window"""
        win = self.sqt.getDesktop()
        return [wid for wid in win.children() if isinstance(wid, qt_cls)]

    def give_mod(self):
        """Return the Aster module for the current study"""
        mods = self._mods
        std_idx = self.sqt.getStudyId()   # current active salomé study
        mod = mods.get(std_idx)
        if not mod:
            mod = AsterModule(self.sqt)
            mods[std_idx] = mod
        return mod

    def activate(self):
        """Activate the Aster module for the current study"""
        return self.give_mod().activate()

    def run_action_from(self, action_idx):
        """Run an action on the Aster module for the current study"""
        self.give_mod().run_action_from(action_idx)

    def fill_popup_menu(self, popup):
        """Fill the popup menu for the Aster module of the current
        study"""
        self.give_mod().fill_popup_menu(popup)


class AsterModule(object):
    """The Aster module for the GUI part
    """
    name = "ASTER"
    desc = "Aster"
    testing = False
    _message_types = {
        ERROR : (u"Error", qt.QMessageBox.critical),
        INFO : (u"Information", qt.QMessageBox.information),
    }

    def __init__(self, sqt):
        """Initialize the singleton"""
        self.sqt = sqt
        self.actived = False
        self.actions = Actions(self)
        self.menu = MainMenu(self.desc)
        self.toolbar = ToolBar(self.desc)
        self.popup_menu_bld = PopupMenuBuilder()
        self.stracker = SelectionTracker(self)
        self.running_jobs = RunningJobs(self)
        self._case_sign = {}

        self._build_actions()
        self._build_main_menu()
        self._build_toolbar()
        self._build_popup_menus()

    def _build_actions(self):
        """Build the possible actions for the Aster module"""
        actions = self.actions
        stracker = self.stracker
        actions_desc = [
            ("add", "Add study case", add_study_case,
             "Add an Aster study case", "setaster.png"),

            ("edit", "Edit",
             stracker.wrap([aster_s.FromComm], edit),
             "Edit the current study case", "actions/edit-case.png"),
            ("copy", "Copy",
             stracker.wrap([aster_s.FromComm], copy),
             "Copy the current study case", "actions/copy-case.png"),
            ("remove", "Delete",
             stracker.wrap([aster_s.FromComm], remove),
             "Remove the current study case", "actions/delete-case.png", "Del"),
            ("rename", "Rename",
             stracker.wrap([aster_s.FromComm], rename),
             "Rename the current study case", "actions/rename-case.png", "F2"),
            ("run", "Run",
             stracker.wrap([aster_s.FromComm], run),
             "Run the current study case", "actions/run-case.png"),
            ("stop", "Stop",
              stracker.wrap([aster_s.FromComm], stop),
             "Stop the current study case", "actions/stop-case.png"),
            ("status", "Status",
              stracker.wrap([aster_s.FromComm], status),
             "Ask the current study case status", "actions/get-status.png"),

            ("run-astk", "Run ASTK", run_astk_tool,
             "Run the ASTK client", "actions/run-astk.png"),
            ("run-astk-on-case", "Export to ASTK",
             stracker.wrap([aster_s.FromComm], run_astk_tool),
             "Run the ASTK client on the given study case", "actions/run-astk.png"),
            ("run-eficas", "Run Eficas", run_eficas_tool,
             "Run the Eficas editor", "actions/run-eficas.png"),
            ("run-eficas-on-comm", "Run Eficas",
             stracker.wrap([aster_s.CommFile], run_eficas_tool),
             "Run the Eficas editor on the given command file",
             "actions/run-eficas.png"),
            ("run-stanley", "Open Stanley on localhost",
             stracker.wrap([aster_s.BaseResult], run_stanley_tool),
             "Run the Stanley explorator on the local host", "actions/run-stanley.png"),

            ("linear-elastic", "Static structural", run_linear_elastic,
             "Wizard on linear elastic problem", "actions/run-linear-elastic.png"),
            ("modal-analysis", "Modal analysis", run_modal_analysis,
             "Wizard on modal analysis problem", "actions/run-modal-analysis.png"),
            ("linear-thermic", "Linear thermic", run_linear_thermic,
             "Wizard on linear thermic problem", "actions/run-linear-thermic.png"),
            ("Crack-analysis", "Crack analysis", run_XFEM,
             "Wizard on XFEM problem", "actions/run-crack-analysis.png"),
            ("read-text", "Read as text",
             stracker.wrap([aster_s.CommFile,
                            aster_s.MessFile,
                            aster_s.ResuFile], read_as_text),
             "Read as a text file", "actions/read-text.png"),
            ("edit-text", "Edit as text",
             stracker.wrap([aster_s.CommFile,
                            aster_s.MessFile,
                            aster_s.ResuFile], edit_as_text),
             "Edit as a text file", "pencil.png"),
            ("update-mesh", "Update mesh",
             stracker.wrap([aster_s.FromComm], update_mesh),
             "Update mesh by using Eficas", "actions/mesh_update.png"),
             #added by zxq at 2017/2/7
            ("linear-static-model-define", "Model define", run_linear_static_model_define,
             "Select a kind of model to work on", "actions/edit-case.png"),
             
            ("linear-static-mesh-selection", "Mesh selection", run_linear_static_mesh_selection,
             "Select a mesh", "actions/edit-case.png"),
             
            ("linear-static-material-properties", "Material properies", run_linear_static_material_properties,
             "Material properties definitions", "actions/edit-case.png"),
             
            ("linear-static-boundaries-degrees-conditions", "Boundaries degrees conditions", run_linear_static_boundaries_degrees_conditions,
             "Add imposed degrees of freedom on groups", "actions/edit-case.png"),
             
            ("linear-static-boundaries-pressure-conditions", "Boundaries pressure conditions", run_linear_static_boundaries_pressure_conditions,
             "Add pressure on meshes groups", "actions/edit-case.png"),
             
            ("linear-thermic-model-define", "Model define", run_linear_thermic_model_define,
             "Select a kind of model to work on", "actions/edit-case.png"),
             
            ("linear-thermic-mesh-selection", "Mesh selection", run_linear_thermic_mesh_selection,
             "Select a mesh", "actions/edit-case.png"),
             
            ("linear-thermic-material-properties", "Material properies", run_linear_thermic_material_properties,
             "Material properties definitions", "actions/edit-case.png"),
             
            ("linear-thermic-boundaries-degrees-conditions", "Boundaries degrees conditions", run_linear_thermic_boundaries_degrees_conditions,
             "Add imposed degrees of freedom on groups", "actions/edit-case.png"),
             
            ("linear-thermic-boundaries-pressure-conditions", "Boundaries pressure conditions", run_linear_thermic_boundaries_pressure_conditions,
             "Add pressure on meshes groups", "actions/edit-case.png"),
             
             ("modal-analysis-model-define", "Model define", run_modal_analysis_thermic_model_define,
             "Select a kind of model to work on", "actions/edit-case.png"),
             
            ("modal-analysis-mesh-selection", "Mesh selection", run_modal_analysis_mesh_selection,
             "Select a mesh", "actions/edit-case.png"),
            
            ("modal-analysis-elementary-characteristics", "Elementary characteristics", run_modal_analysis_elementary_characteristics,
             "Elementary characteristics", "actions/edit-case.png"),
 
            ("modal-analysis-material-properties", "Material properies", run_modal_analysis_material_properties,
             "Material properties definitions", "actions/edit-case.png"),
             
            ("modal-analysis-boundaries-conditions", "Boundaries conditions", run_modal_analysis_boundaries_conditions,
             "Added imposed degrees of freedom on groups", "actions/edit-case.png"),
             
            ("modal-analysis-number-of-modes", "Number of modes", run_modal_analysis_number_of_modes,
             "Number of modes", "actions/edit-case.png"),
             #added 
        ]
        if self.testing:
            actions_desc.append(
                ("run-tests", "Run tests", run_tests,
                 "Run automatic testst concerning the GUI", "actions/run-stanley.png")
                )
        for args in actions_desc:
            key, name, callback, tooltip, icon = args[:5]
            shortcut = None
            if len(args) > 5:
                shortcut = args[5]
            action = actions.add(key, name, callback)
            action.use_tooltip(tooltip)
            if icon:
                action.use_icon(icon)
            if shortcut:
                action.use_shortcut(shortcut)

    def _build_main_menu(self):
        """Build the main menu"""
        actions = self.actions
        main_menu = self.menu

        """menus_desc = (
            ("Current study case",
             ["update-mesh", "edit", "copy", "rename", "remove", "run", "stop", "status"]),
            ("Tools",
             ["run-astk", "run-eficas"]),
            ("Wizards",
             ["linear-elastic", "modal-analysis", "linear-thermic", "Crack-analysis"]),
        )
        for menu_title, actions_keys in menus_desc:
            menu = main_menu.add_menu(menu_title)
            #peter.zhang, add seperator
            main_menu.add_action(SEP)
            for key in actions_keys:
                #peter.zhang, add menu items directly.
                #menu.add_action(actions[key])
                main_menu.add_action(actions[key])"""
        menus_desc = ["add","update-mesh", "edit", "copy", "rename", "remove", "run", "stop", "status", "run-astk", "run-eficas"]
        pagename =   ["linear-elastic", "modal-analysis", "linear-thermic", "Crack-analysis"]
        linear_static_page_actions = ["linear-static-model-define", "linear-static-mesh-selection", "linear-static-material-properties", "linear-static-boundaries-degrees-conditions", "linear-static-boundaries-pressure-conditions"]
        modal_analysis_page_actions = ["modal-analysis-model-define", "modal-analysis-mesh-selection", "modal-analysis-elementary-characteristics", "modal-analysis-material-properties", "modal-analysis-boundaries-conditions", "modal-analysis-number-of-modes"]
        linear_thermic_page_actions = ["linear-thermic-model-define", "linear-thermic-mesh-selection", "linear-thermic-material-properties", "linear-thermic-boundaries-degrees-conditions", "linear-thermic-boundaries-pressure-conditions"]
        
        op_page = Page("Operations","Solver", menus_desc)
        op_page.build(self.sqt, actions)
        
        ms_page = Page("Modal analysis", "Sets", modal_analysis_page_actions)
        ms_page.build(self.sqt, actions)
        
        lt_page = Page("Linear thermic", "Sets", linear_thermic_page_actions)
        lt_page.build(self.sqt, actions)
        
        le_page = Page("linear-elastic","Sets", linear_static_page_actions)
        le_page.build(self.sqt, actions)

    def _build_toolbar(self):
        """Build the toolbar"""
        actions = self.actions
        tbar = self.toolbar

        compos = [
            actions["add"],
            SEP,
            actions["edit"],
            actions["copy"],
            actions["remove"],
            actions["run"],
            actions["stop"],
            actions["status"],
            SEP,
            actions["run-astk"],
            actions["run-eficas"],
            SEP,
            actions["linear-elastic"],
            actions["modal-analysis"],
            actions["linear-thermic"],
            actions["Crack-analysis"],
            actions["Fatigue-analysis"],
            ]
        if self.testing:
            compos.extend([
                SEP,
                actions["run-tests"],
                ])
        for compo in compos:
            tbar.add(compo)

    def _build_popup_menus(self):
        """Build the popup menus"""
        actions = self.actions
        register = self.popup_menu_bld.register

        case_popup = create_popup_menu([
            actions["update-mesh"],
            SEP,
            actions["run"],
            actions["status"],
            actions["stop"],
            SEP,
            actions["edit"],
            actions["copy"],
            actions["rename"],
            actions["remove"],
            SEP,
            actions["run-astk-on-case"],
        ])
        register(aster_s.FromComm, case_popup)
        register(aster_s.FromExport, case_popup)

        comm_popup = create_popup_menu([
            actions["read-text"],
            actions["edit-text"],
            actions["run-eficas-on-comm"],
        ])
        register(aster_s.CommFile, comm_popup)

        rpopup = create_popup_menu([
            actions["read-text"],
            actions["edit-text"],
        ])
        register(aster_s.MessFile, rpopup)
        register(aster_s.ResuFile, rpopup)

        base_popup = create_popup_menu([actions["run-stanley"]])
        register(aster_s.BaseResult, base_popup)

    def give_qtwid(self):
        """Give the main qt widget identifying the Aster module"""
        return self.sqt.getDesktop()

    def give_salome_study(self):
        """Return the Salomé study handled by the module"""
        sstd = salome.myStudyManager.GetStudyByID(self.sqt.getStudyId())
        return ST.SalomeStudy(sstd)

    def give_aster_study(self):
        """Return the Aster study attached to the current Salomé one"""
        return aster_s.Study(self.give_salome_study())

    def launch(self, mess_type, message):
        """Launch an error dialog"""
        title, launch_mess = self._message_types[mess_type]
        parent = self.give_qtwid()
        if not self.testing:
            launch_mess(parent, title, message)
        else:
            dia = qt.QMessageBox(parent)
            dia.setText(title)
            dia.setInformativeText(message)

    def activate(self):
        """Activate the Aster module. Is done in another processus so
        objects created in that function can not be shared."""
        if not self.actived:
            self.menu.build(self.sqt)
            self.toolbar.build(self.sqt)
        self.actived = True
        return True

    def run_action_from(self, action_idx):
        """Run an action from its index"""
        try:
            self.actions.run(action_idx)
        except TypeError, err:
            log_gui.debug("Traceback of failure:\n%s", traceback.format_exc())
            corba_mesh_error = re.search("corba.*mesh", str(err), re.IGNORECASE) != None
            if corba_mesh_error:
                mess = "You must activate the SMESH component before using " \
                       "this case which refers to a Mesh object."
                self.launch(ERROR, mess)
            raise TypeError(err)

    def fill_popup_menu(self, popup):
        """Fill the popup menu according to the selection"""
        node = self.stracker.give_node()
        if node:
            self.popup_menu_bld.build_for(ST.load_cls(node), popup, self.sqt)

    def update(self):
        """Update the module GUI"""
        self.sqt.updateObjBrowser()

    '''def notify_job_ended(self, name, res, has_results):
        """Called when a job is ended"""
        #Desactivation PARAVIS
        #import salome_pyutils.visu_utils as VU
        #open_pv, study = VU.can_open_paravis()
        msg = ["Job '%s' ended with status '%s'." % (name, res)]
        if has_results:
            txtpv = "If there is a MED file as result, " \
                    "You have to import manually the result file in Paravis."
            msg.extend([txtpv])
        msg = '\n'.join(msg)
        self.loginfo(msg)
        SGU.notify_info_timeout(self.sqt, msg, timeout=8*1000)'''

    def load_mesh_from_selection(self):
        """Return a Mesh from the current selection if found or None
        otherwise"""
        mesh = None
        node = self.stracker.give_node()
        if node:
            try:
                mesh = ST.attach_mesh(node)
            except TypeError:
                pass
        return mesh

    def loginfo(self, text):
        """Write an information in "Message Log window"."""
        self.sqt.message(text)

#added by zxq 
def run_linear_static_model_define(mod):
    from aster_s_gui.wizards import linear_static as LS
    dock = LS.Create_Dock(mod)
    mod.give_qtwid().addDockWidget(qtc.Qt.RightDockWidgetArea,dock)
    
def run_linear_static_mesh_selection(mod):
    from aster_s_gui.wizards import modal_analysis as MA
    dock = MA.Create_MADock(mod)
    mod.give_qtwid().addDockWidget(qtc.Qt.RightDockWidgetArea,dock)

def run_linear_static_material_properties(mod):
    from aster_s_gui.wizards import linear_thermic as LT
    dock = LT.Create_LTDock(mod)
    mod.give_qtwid().addDockWidget(qtc.Qt.RightDockWidgetArea,dock)


def run_linear_static_boundaries_degrees_conditions(mod):
    from aster_s_gui.wizards import XFEM as XFEM
    dock = XFEM.Create_XFEMDock(mod)
    mod.give_qtwid().addDockWidget(qtc.Qt.RightDockWidgetArea,dock)

def run_linear_static_boundaries_pressure_conditions(mod):
    from aster_s_gui.wizards import XFEM as XFEM
    dock = XFEM.create_wizard(mod)
    dock.run()



def run_linear_thermic_model_define(mod):
    from aster_s_gui.wizards import linear_static as LS
    return 0

def run_linear_thermic_mesh_selection(mod):
    from aster_s_gui.wizards import linear_static as LS
    return 0
    
def run_linear_thermic_material_properties(mod):
    from aster_s_gui.wizards import linear_static as LS
    return 0

def run_linear_thermic_boundaries_degrees_conditions(mod):
    from aster_s_gui.wizards import linear_static as LS
    return 0
    
def run_linear_thermic_boundaries_pressure_conditions(mod):
    from aster_s_gui.wizards import linear_static as LS
    return 0


def run_modal_analysis_thermic_model_define(mod):
    from aster_s_gui.wizards import linear_static as LS
    return 0

def run_modal_analysis_mesh_selection(mod):
    from aster_s_gui.wizards import linear_static as LS
    return 0

def run_modal_analysis_elementary_characteristics(mod):
    from aster_s_gui.wizards import linear_static as LS
    return 0

def run_modal_analysis_material_properties(mod):
    from aster_s_gui.wizards import linear_static as LS
    return 0

def run_modal_analysis_boundaries_conditions(mod):
    from aster_s_gui.wizards import linear_static as LS
    return 0

def run_modal_analysis_number_of_modes(mod):
    from aster_s_gui.wizards import linear_static as LS
    return 0
