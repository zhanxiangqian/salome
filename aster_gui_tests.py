# -*- coding: utf-8 -*-
"""Tools for easing Salomé tests on the GUI side
"""
import os
import os.path as osp
import subprocess as SP
import unittest as UT
from cStringIO import StringIO
from tempfile import mkstemp
from time import sleep

from PyQt4 import QtGui as qt
from PyQt4 import QtCore as qtc
connect = qtc.QObject.connect
SIG = qtc.SIGNAL

import aster_s
import aster_s.study as AS
import aster_s.astk as astk

from aster_s_gui import GuiBuilder
import aster_s_gui.study_case_dialog as AD
import aster_s_gui.job_supervision as JS
import aster_s_gui.module as AM

import salome_aster_tests as ST
import aster_mocker as MCK


def make_active(dkey):
    """Activate the module from its description key on the GUI side. 
    For example::
   
        make_active(u"Aster")

    """
    actions = GuiBuilder().give(qt.QToolBar)[1].actions()
    dkeys = [unicode(action.text()) for action in actions]
    action = actions[dkeys.index(dkey)]
    action.trigger()

def pyrun(lines, suffix="aster-gui-tests.py"):
    """Run the given lines in a subprocess Python script.
    """
    fid, fname = mkstemp(suffix)
    try:
        os.write(fid, os.linesep.join(lines))
        os.close(fid)
        popen = SP.Popen("python %s" % fname, shell=True)
        popen.wait()
    finally:
        os.remove(fname)


class TestAddCases(MCK.Test):

    def setUp(self):
        self.mod = AM.GuiBuilder().give_mod() 
        self.std = self.mod.give_aster_study()
        self.med_fname = ST.get_data("forma01a.mmed")

    def tearDown(self):
        cases = self.std.get_all(aster_s.Case)
        for case in cases:
            case.remove()

    def test_add_cases(self):
        for idx in range(3):
            creator = AM.add_study_case(self.mod)
            creator._name.setText("case%i" % idx)
            creator.build_case()
        self.assertEqual(len(self.std.get_all(aster_s.Case)), 3)

    def test_not_add_case_if_name_is_empty(self):
        parent = self.mod.give_qtwid()
        creator = AM.add_study_case(self.mod)
        creator._name.setText("")
        cnb = len(parent.children())
        creator.build_case()
        self.assertEqual(len(parent.children()), cnb + 1)
        self.assertEqual(len(self.std.get_all(aster_s.Case)), 0)

    def test_not_add_case_if_name_already_exists(self):
        creators = [AM.add_study_case(self.mod) for idx in range(2)]
        for creator in creators:
            creator._name.setText("case")
        creators[0].build_case()
        self.assertEqual(len(self.std.get_all(aster_s.Case)), 1)
        creators[1].build_case()
        self.assertEqual(len(self.std.get_all(aster_s.Case)), 1)
    
    def test_add_case_with_comm_and_mesh_files(self):
        creator = AM.add_study_case(self.mod)
        params = creator._params
        data = (
            ("comm", "/aster/f.comm"),
            ("mesh", "f.mmed"),
        )
        for key, val in data:
            params[key]._data_builder.fname_entry.setText(val)
        creator.build_case()
        case = self.std.get_all(aster_s.Case)[0]
        fnames = [case.get(ftype).read_fname() \
                  for ftype in (aster_s.CommFile, aster_s.MedFile)]
        self.assertEqual(fnames[0], "/aster/f.comm")
        self.assertEqual(fnames[1], "f.mmed")

    def test_add_case_with_comm_and_mesh_files(self):
        creator = AM.add_study_case(self.mod)
        params = creator._params
        data = (
            ("comm", "/aster/f.comm"),
            ("mesh", "f.mmed"),
        )
        for key, val in data:
            datas = params[key]
            datas._selector.setCurrentIndex(1)
            datas._data_builder.fname_entry.setText(val)
        creator.build_case()
        case = self.std.get_all(aster_s.Case)[0]
        fnames = [case.get(ftype).read_fname() \
                  for ftype in (aster_s.CommFile, aster_s.MedFile)]
        self.assertEqual(fnames[0], "/aster/f.comm")
        self.assertEqual(fnames[1], "f.mmed")

    def test_add_case_with_comm_and_mesh_entries(self):
        std = self.std
        comm = aster_s.CommFile("f.comm").build(std)
        mesh = std.sstd.load_meshes_from(self.med_fname)[0]
        data = (
            ("comm", comm.node),
            ("mesh", mesh.node),
        )
        creator = AM.add_study_case(self.mod)
        params = creator._params
        for key, node in data:
            params[key]._data_builder._brw_node = node
        creator.build_case()
        case = self.std.get_all(aster_s.Case)[0]
        self.assert_(case.get(aster_s.CommEntry))
        self.assert_(case.get(aster_s.SMeshEntry))

    def test_add_case_with_eficas_and_med_file_entry(self):
        import aster_s.salome_tree as stree
        std = self.std
        # Adding fake eficas file
        fname = "/aster/case1/eficas-file.comm"
        eficas_node = std.sstd.add_root("eficas-file")
        eficas_node.get_attr(stree.Value).write(fname)
        eficas_node.get_attr(stree.Type).write(stree.EficasFile.ftype)
        med = aster_s.MedFile("f.mmed").build(std)

        creator = AM.add_study_case(self.mod)
        blds = [creator._params[key]._data_builder for key in ("comm", "mesh")]
        blds[0]._brw_node = eficas_node
        blds[1]._brw_node = med.node
        creator.build_case()
        case = self.std.get_all(aster_s.Case)[0]
        comm = case.get(aster_s.CommFile)
        self.assert_(comm.read_fname(), fname)
        self.assert_(case.get(aster_s.MedEntry))

    def test_select_solvers(self):
        std = self.std
        find_servers = self.mocker.replace(astk.find_servers)
        data = (
            ("crater", "STA8.1 NEW9 STA10.1", "oui"),
            ("herc", "STA11.0", "non"),
        )
        servs = [
            {"nom_complet" : name, "vers" : vers, "batch" : batch}
            for name, vers, batch in data
        ]
        MCK.expect(find_servers()).result(servs).count(0, None)
        self.mocker.replay()

        creator = AM.add_study_case(self.mod)
        params = creator._params
        srv, vers, mode = [params[key] 
                           for key in ("server", "aster-version", "mode")]
        self.assertEqual(mode._wid.count(), 2)
        srv._wid.setCurrentIndex(1)
        srv._wid.emit(SIG("activated(int)"), 1)
        self.assertEqual(str(vers._wid.currentText()), "STA11.0")
        self.assertEqual(mode._wid.count(), 1)

        case = std.add_case("c")
        params.build_case(std, case)

        cfg = case.get(aster_s.AstkParams)
        self.assertEqual(cfg["server"], "herc")
        self.assertEqual(cfg["aster-version"], "STA11.0")

    def test_enable_widgets_according_to_choice(self):
        wids = [qt.QWidget() for idx in range(2)]
        cparam = AD.ChoiceParam("select", ["a", "b"])
        cparam.register_enabled(0, wids)

        self.assertEqual([wid.isEnabled() for wid in wids], [True, True])
        cparam._wid.emit(SIG("currentIndexChanged(int)"), 1)
        self.assertEqual([wid.isEnabled() for wid in wids], [False, False])
        cparam.use_cidxs([0])
        self.assertEqual([wid.isEnabled() for wid in wids], [True, True])

    def test_modify_astk_parameters(self):
        std = self.std

        creator = AM.add_study_case(self.mod)
        params = creator._params
        params["memory"]._wid.setValue(1024)
        params["mode"]._wid.setCurrentIndex(1)
        case = std.add_case("c")
        params.build_case(std, case)

        cfg = case.get(aster_s.AstkParams)
        self.assertEqual(cfg["memory"], 1024)
        self.assertEqual(cfg["mode"], "batch")

    def test_use_interactiv_and_base_result(self):
        std = self.std
        creator = AM.add_study_case(self.mod)
        params = creator._params
        boxes = [
            params["interactiv-follow-up"]._active,
            params["save-base"]._wid,
            ]
        for box in boxes:
            box.checked(True)

        case = std.add_case("c")
        params.build_case(std, case)
        
        self.assert_(case.get(aster_s.InteractivFollowUp))
        self.assert_(case.get(aster_s.HasBaseResult))


class TestEditCases(UT.TestCase):

    def setUp(self):
        self.mod = AM.GuiBuilder().give_mod() 
        self.std = self.mod.give_aster_study()
        bcase = self.std.add_case("Aster case")
        self.case = AS.load_elt_from_node(bcase.node)

    def tearDown(self):
        self.case.remove()

    def test_display_name(self):
        editor = AM.edit(self.mod, self.case)
        self.assertEqual(editor._name.text(), self.case.read_name())

    def test_edit_comm_and_med_files(self):
        case = self.case
        case.use(aster_s.CommFile("/aster/f.comm"))
        case.use(aster_s.MedFile("f.mmed"))
        editor = AM.edit(self.mod, case)
        sels = [editor._params[key] for key in ("comm", "mesh")]
        fnames = [sel._data_builder.fname_entry.text() for sel in sels]
        self.assertEqual(fnames, ["/aster/f.comm", "f.mmed"])
        idxs = [sel._selector.currentIndex() for sel in sels]
        self.assertEqual(idxs, [1, 1])

    def test_not_write_comm_and_med_files_if_none(self):
        case = self.case
        compos = [aster_s.CommFile(""), aster_s.MedFile("")]
        felts = [case.use(compo) for compo in compos]
        self.assert_([felt.read_fname() for felt in felts], [None, None])
        editor = AM.edit(self.mod, case)
        fnames = [editor._params[key]._data_builder.fname_entry.text()
                  for key in ("comm", "mesh")]
        self.assertEqual(fnames, ["", ""])

    def test_edit_comm_and_med_entries(self):
        case = self.case
        compos = (aster_s.CommFile("c"), aster_s.MedFile("m"))
        felts = [compo.build(self.std) for compo in compos]
        fentries = [felt.node.entry for felt in felts]
        case.use(aster_s.CommEntry(felts[0].node.entry))
        case.use(aster_s.MedEntry(felts[1].node.entry))
        editor = AM.edit(self.mod, case)
        sels = [editor._params[key] for key in ("comm", "mesh")]
        blds = [sel._data_builder for sel in sels]
        self.assertEqual([bld.brw_entry.text() for bld in blds], ["c", "m"])
        self.assertEqual([bld._brw_node.entry for bld in blds], fentries)
        idxs = [sel._selector.currentIndex() for sel in sels]
        self.assertEqual(idxs, [0, 0])

    def test_edit_mesh_entry(self):
        case = self.case
        med_fname = ST.get_data("forma01a.mmed") 
        mentry = self.std.sstd.load_meshes_from(med_fname)[0].node.entry
        case.use(aster_s.SMeshEntry(mentry))
        editor = AM.edit(self.mod, case)
        sels = [editor._params[key] for key in ("comm", "mesh")]
        bld = sels[1]._data_builder
        self.assertEqual(bld.brw_entry.text(), "MeshCoude")
        self.assertEqual(bld._brw_node.entry, mentry)
        idxs = [sel._selector.currentIndex() for sel in sels]
        self.assertEqual(idxs, [0, 0])

    def test_edit_astk_parameters(self):
        case = self.case
        cfg = case.get(aster_s.AstkParams)
        cfg["time"] = 350
        cfg["mode"] = "batch"
        cfg["server"] = "crater"
        cfg["aster-version"] = "STA8.4"

        editor = AM.edit(self.mod, case)
        params = editor._params
        self.assertEqual(params["time"]._wid.value(), 350)
        self.assertEqual(params["mode"]._wid.currentText(), "batch")
        self.assertEqual(params["server"]._wid.currentText(), "crater")
        self.assertEqual(params["aster-version"]._wid.currentText(), "STA8.4")

    def test_edit_interactiv_and_base_result(self):
        case = self.case
        case.use(aster_s.InteractivFollowUp())
        case.use(aster_s.HasBaseResult())

        editor = AM.edit(self.mod, case)
        data = [editor._params[key] 
                for key in ("interactiv-follow-up", "save-base")]
        self.assert_(data[0]._active.isChecked())
        self.assert_(data[1]._wid.isChecked())

    def test_update_case_without_removing_previous_files(self):
        case = self.case
        compos = [aster_s.CommFile("c"), aster_s.MedFile("m")]
        ufelts = [case.use(compo) for compo in compos]

        editor = AM.edit(self.mod, self.case)
        editor._name.setText("ucase")
        params = editor._params
        blds = [params[key]._data_builder for key in ("comm", "mesh")]
        blds[0].fname_entry.setText("uc")
        blds[1].fname_entry.setText("um")
        params["save-base"]._wid.checked(False)
        params["interactiv-follow-up"]._active.checked(True)
        editor.build_case()

        self.assertEqual(case.read_name(), "ucase")
        self.assert_(case.get(aster_s.InteractivFollowUp))
        self.assert_(not case.get(aster_s.HasBaseResult))
        felts = [case.get(compo.__class__) for compo in compos]
        self.assertEqual([felt.node.entry for felt in felts],
                         [ufelt.node.entry for ufelt in ufelts])
        self.assertEqual([felt.read_fname() for felt in felts], ["uc", "um"])

    def test_update_case_on_new_entries(self):
        std = self.std
        case = self.case
        comms = [aster_s.CommFile(name).build(std) for name in ("c1", "c2")]
        med_fname = ST.get_data("forma01a.mmed")
        mesh = std.sstd.load_meshes_from(med_fname)[0]
        case.use(aster_s.CommEntry(comms[0].node.entry))
        case.use(aster_s.MedFile("m"))

        editor = AM.edit(self.mod, self.case)
        datas = [editor._params[key] for key in ("comm", "mesh")]
        for data in datas:
            data._selector.setCurrentIndex(0)
        blds = [data._data_builder for data in datas]
        blds[0]._brw_node = comms[1].node
        blds[1]._brw_node = mesh.node
        editor.build_case()

        centry = case.get(aster_s.CommEntry)
        self.assertEqual(centry.node.give_source().entry, comms[1].node.entry)
        self.assert_(not case.get(aster_s.MedFile))
        self.assert_(case.get(aster_s.SMeshEntry))

    def test_update_astk_parameters(self):
        case = self.case
        editor = AM.edit(self.mod, case)
        params = editor._params
        params["server"]._wid.setEditText("crater")
        params["aster-version"]._wid.setEditText("STA8.4")
        params["mode"]._wid.setCurrentIndex(1)
        params["time"]._wid.setValue(350)
        editor.build_case()

        cfg = case.get(aster_s.AstkParams)
        self.assertEqual(cfg["time"], 350)
        self.assertEqual(cfg["mode"], "batch")
        self.assertEqual(cfg["server"], "crater")
        self.assertEqual(cfg["aster-version"], "STA8.4")


class FakeRunningJob(JS.RunningJob):
    """Proof that automatic tests can not be done on job supervisions
    because the 'update' method is not called
    """

    def __init__(self, parent):
        self._parent = parent
        JS.RunningJob.__init__(self, None, self, None, None)
        self.has_run = False

    def give_qtwid(self):
        """Return the parent"""
        return self._parent

    def update(self):
        """A fake update for checking that the method is called"""
        self.has_run = True
        self._timer.stop()
        self._timer.deleteLater()


class TestRunCases(UT.TestCase):

    def test_not_run_qtimer_in_test_callback(self):
        parent = qt.QWidget()
        rjobs = [FakeRunningJob(parent) for idx in range(2)]

        rjobs[0]._timer.emit(SIG("timeout()"))
        self.assert_(rjobs[0].has_run)

        # Signal should be emitted after 200 milliseconds
        rjobs[1].start(refresh_time=200)
        # We wait one second but the signal is not emitted
        sleep(1)
        self.assert_(not rjobs[1].has_run)


class TestsResultOutput(qt.QDialog):
    """Redirect test output to QTextBrowser
    """

    def __init__(self):
        qt.QDialog.__init__(self)
        self.brw = qt.QTextBrowser()
        self.stream = StringIO()
        self.write = self.stream.write
        self.build_gui()

    def build_gui(self):
        """Build the GUI"""
        lay = qt.QVBoxLayout(self)
        lay.addWidget(self.brw)

        but = qt.QPushButton("Quit")
        connect(but, SIG("clicked()"), kill_salome)
        lay.addWidget(but)

    def show(self):
        """Show the test results on the GUI side"""
        self.brw.setPlainText(self.stream.getvalue())
        qt.QDialog.show(self)


def run_tests(mod):
    """Run all the tests in the Salomé GUI context of the Aster module"""
    load = UT.TestLoader().loadTestsFromTestCase
    suite = UT.TestSuite()
    for cls in [TestAddCases, TestEditCases, TestRunCases]:
        suite.addTests(load(cls))
    rout = TestsResultOutput()
    rout.setParent(mod.give_qtwid())
    runner = UT.TextTestRunner(stream=rout)
    runner.run(suite)
    rout.show()

def kill_salome():
    """Kill the Salomé GUI server"""
    import salome
    kroot = osp.abspath(osp.join(salome.__file__, *[".."] * 5))
    script = osp.join(kroot, "bin", "salome", "killSalome.py")
    popen = SP.Popen([script])
    popen.wait()


