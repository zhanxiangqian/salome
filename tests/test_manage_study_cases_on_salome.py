# -*- coding: utf-8 -*-
"""Testing Aster study cases manipulation on the Salomé server.
"""
import os.path as osp
import unittest as UT

import aster_mocker as MCK

import aster_s
import aster_s.salome_tree as ST
import aster_s.astk as astk
import aster_s.study as AS

import salome_aster_tests as SAT


class AsterStdTest(UT.TestCase):
    """Build an aster study for testing 
    """

    def setUp(self):
        self.bld = aster_s.StudyBuilder()
        self.std = self.bld.create("std")

    def tearDown(self):
        self.bld.close_all()


class TestStoreInputDataInSalomeTree(AsterStdTest):

    def test_store_params_into_section(self):
        cdata = aster_s.DataSection()
        data = cdata.build(self.std)

        self.assert_(data.get(aster_s.CommFile) is None)
        compo = aster_s.CommFile("file.txt")
        comm = data.use(compo)
        comm = ST.File(comm.node)
        self.assertEqual(comm.read_name(), "file.txt")
        self.assertEqual(comm.read_fname(), "file.txt")
        self.assert_(comm.load_type() is aster_s.CommFile)

        self.assert_(data.get(aster_s.MedFile) is None)
        fname = "/tmp/aster/mesh.mmed"
        med_fact = aster_s.MedFile(fname)
        med = data.use(med_fact)
        mmed = ST.File(med.node)
        self.assertEqual(mmed.read_name(), "mesh.mmed")
        self.assertEqual(mmed.read_fname(), fname)
        self.assert_(mmed.load_type() is aster_s.MedFile)

        self.assert_(data.get(aster_s.WorkingDir) is None)
        data.use(aster_s.WorkingDir("/tmp/aster"))
        rep = ST.Line(data.node.find_node("working-dir"))
        self.assertEqual(rep.read_value(), "/tmp/aster")

    def test_copy_study_case_building_objects(self):
        root = AS.Elt(self.std.node.add_node("root"), AS.Elt)
        dest = AS.Elt(self.std.node.add_node("dest"), AS.Elt)

        sfile_fact = aster_s.CommFile("fcomm")
        sfile = sfile_fact.build(root)
        copy = sfile.copy_to(dest)
        self.assert_(copy is not dest)
        self.assert_(copy.node.parent is dest.node)
        self.assertEqual(copy.read_name(), "fcomm")
        self.assertEqual(copy.read_fname(), "fcomm")
        self.assert_(copy.sfile.load_type() is aster_s.CommFile)
        self.assert_(isinstance(copy, AS.File))

        version = aster_s.Value("version", "STA10.0")
        velt = version.build(root)
        copy = velt.copy_to(dest)
        self.assert_(ST.load_cls(copy.node) is aster_s.Value)

        entry_compo = aster_s.CommEntry(sfile.node.entry)
        centry = entry_compo.build(root)
        copy = centry.copy_to(dest)
        self.assertEqual(copy.node.give_source().entry,
                         centry.node.give_source().entry)

    def test_copy_section(self):
        root = AS.Elt(self.std.node, AS.Elt)
        cdata = aster_s.DataSection()
        cdata.name = "stest"
        data = cdata.build(root)
        data.use(aster_s.CommFile("f"))
        data.use(aster_s.WorkingDir("r"))

        copy = data.copy_to(root)
        self.assert_(copy is not data)
        self.assert_(copy.node.parent is root.node)
        self.assertEqual(copy.read_name(), "stest")
        self.assertEqual(copy.get(aster_s.CommFile).read_fname(), 
                         data.get(aster_s.CommFile).read_fname())
        self.assert_(copy.get(aster_s.MedFile) is None)
        self.assertEqual(copy.get(aster_s.WorkingDir).read_value(),
                         data.get(aster_s.WorkingDir).read_value())

    def test_display_astk_parameters_for_solver(self):
        cfg = astk.Cfg()
        cfg.add("dbg", astk.Param("debug", "nodebug"))
        cfg.add("mem", astk.Attr("memory", 128))

        cparams = aster_s.AstkParams(cfg)
        cparams.name = "p"
        params = cparams.build(self.std)
        pnode = params.node
        self.assertEqual(params.read_name(), "p")
        params.attach_cfg(cfg)
        dbg = ST.Line(pnode.find_node("dbg"))
        self.assertEqual(dbg.read_name(), "dbg")
        self.assertEqual(dbg.read_value(), "nodebug")
        self.assertEqual(params["dbg"], "nodebug")

        mem = ST.Line(pnode.find_node("mem"))
        self.assertEqual(mem.read_value(), 128)
        self.assertEqual(mem.read_visible_value(), '128')
        params["mem"] = 256
        self.assertEqual(mem.read_value(), 256)
        self.assertEqual(mem.read_visible_value(), '256')
        
        params["dbg"] = "debug"
        astk_cfg = params.get_cfg()
        self.assertEqual(astk_cfg["mem"].value, 256)
        self.assertEqual(astk_cfg["dbg"].value, "debug")

    def test_clear_section_when_new_configuration_attached(self):
        cfg = astk.Cfg()
        cfg.add("mem", astk.Attr("memory", 128))
        parent = AS.Elt(self.std.node.add_node("p"), AS.Elt)

        cparams = aster_s.AstkParams(cfg)
        params = cparams.build(parent)
        mem = params.get_elt("mem")
        self.assert_(mem.node.is_alive())
        
        cfg = astk.Cfg()
        cfg.add("dbg", astk.Param("debug"))
        params.attach_cfg(cfg)
        self.assert_(not mem.node.is_alive())


class TestShowResultsInSalomeTree(MCK.Test):

    def setUp(self):
        self.bld = aster_s.StudyBuilder()
        self.std = self.bld.create("std")
        self._display_med_file = ST.VisuMedFile.display
        ST.VisuMedFile.display = False

    def tearDown(self):
        ST.VisuMedFile.display = self._display_med_file
        self.bld.close_all()

    def test_display_astk_results(self):
        astkc = self.mocker.mock(astk.Case) 
        astkc.get_result(astk.MessFile).fname
        self.mocker.result("/h/d1/f.mess")
        astkc.get_result(astk.ResuFile).fname
        self.mocker.result("f.resu")
        astkc.get_result(astk.RMedFile).fname
        self.mocker.result("rmed.med")
        astkc.get_result(astk.BaseResult).dname
        self.mocker.result("fbase")
        self.mocker.replay()

        case = self.bld.create("s").add_case("c")
        case._aster_case = astkc
        self.assert_(case.get(aster_s.MessFile) is None)
        status = astk.SUCCESS
        status.from_astk = "OK"
        case._build_results()
        case._display_results(status)

        self.assertEqual(case.results.read_name(), "Results")
        self.assertEqual(case.read_value(), "OK")
        self.assertEqual(case.get(aster_s.MessFile).read_fname(), "/h/d1/f.mess")
        self.assertEqual(case.get(aster_s.ResuFile).read_fname(), "f.resu")
        self.assertEqual(case.get(aster_s.RMedFile).read_fname(), "rmed.med")
        self.assertEqual(case.get(aster_s.BaseResult).read_dname(), "fbase")


class TestLoadDataFromObjectBrowser(AsterStdTest):

    def setUp(self):
        AsterStdTest.setUp(self)
        self.tmp_dir = SAT.TmpDir("load_data_from_object_browser")

    def tearDown(self):
        self.tmp_dir.clean()
        AsterStdTest.tearDown(self)
    
    def test_give_aster_study(self):
        std = self.std
        elt = AS.Elt(std.node.add_node("test"), AS.Elt)
        estd = elt.give_aster_study()
        self.assertEqual(estd.sstd.idx, std.sstd.idx)

    def test_load_element_from_entry(self):
        std = self.std
        fact = aster_s.CommFile("fname.comm")
        elt = fact.build(std)
        lelt = std.load_elt_from_entry(elt.node.entry)
        self.assert_(ST.load_cls(elt.node) is aster_s.CommFile)
        self.assertEqual(lelt.node, elt.node)

    def test_build_astk_case(self):
        acfg = astk.Cfg()
        acfg.add("name", astk.Param("n")) 
        comm = __file__
        mmed = UT.__file__

        case = self.std.add_case("a")
        case.use(aster_s.AstkParams(acfg))
        case.use(aster_s.CommFile(comm))
        acs = case.build_astk_case()
        bld = acs.export_bld
        self.assert_(bld.working_dir is None)
        cfg = bld.get(astk.Cfg)
        self.assert_(cfg.equal(acfg))
        self.assertEqual(bld.name, "a")
        self.assertEqual(bld.get(astk.CommFile).fname, comm)
        self.assert_(not bld.get(astk.MedFile))

        case.use(aster_s.WorkingDir("/tmp/a"))
        acs = case.build_astk_case()
        self.assertEqual(acs.export_bld.working_dir, "/tmp/a")

        case.use(aster_s.MedFile(mmed))
        case.write_name("c")
        acs = case.build_astk_case()
        bld = acs.export_bld
        self.assertEqual(bld.name, "c")
        self.assertEqual(bld.get(astk.MedFile).fname, mmed)

        case.use(aster_s.HasBaseResult())
        acs = case.build_astk_case()
        bld = acs.export_bld
        self.assert_(bld.get(astk.Base))

        comm_file = case.get(aster_s.CommFile)
        med_file = case.get(aster_s.MedFile)
        case = self.std.add_case("d")
        case.use(aster_s.CommEntry(comm_file.node.entry))
        case.use(aster_s.MedEntry(med_file.node.entry))
        acs = case.build_astk_case()
        bld = acs.export_bld
        self.assertEqual(bld.get(astk.CommFile).fname, comm)
        self.assertEqual(bld.get(astk.MedFile).fname, mmed)

    def test_build_med_file_from_smesh_entry_for_astk_case(self):
        std = self.std
        mesh = std.sstd.load_meshes_from(SAT.get_data("forma01a.mmed"))[0]
        wdir = self.tmp_dir.add("mesh_file_for_astk")
        med_fname = osp.join(wdir, "%s.mmed")
        
        cases = []
        for idx in range(3):
            case = std.add_case("c%i" % idx)
            case._aster_case = astk.build_case("acs")
            cases.append(case)
        cases[0].use(aster_s.CommFile(osp.join(wdir, "fname.comm")))
        cases[1].use(aster_s.WorkingDir(wdir))
        fact = AS.find_factory(aster_s.SMeshEntry)
        for case in cases[:-1]:
            mesh_ref = case.use(aster_s.SMeshEntry(mesh.node.entry))
            fact.add_to(case._aster_case, case, mesh_ref)
            bld = case._aster_case.export_bld
            self.assertEqual(bld.get(astk.MedFile).fname, 
                             med_fname % case.read_name()) 

        case = cases[-1]
        mentry = case.use(aster_s.SMeshEntry(mesh.node.entry))
        self.assertRaises(ValueError, fact.add_to, case._aster_case, case, mentry)


class TestCreateCaseFromDifferentSources(AsterStdTest):

    def test_add_study_case_from_comm_file(self):
        std = self.std
        
        comm_file = __file__
        med_file = UT.__file__
        case = std.add_case("Aster case")
        self.assertEqual(case.read_name(), "Aster case")

        # Configuration
        cfg = case.get(aster_s.AstkParams)
        dcfg = astk.build_default_cfg()
        dcfg["name"].value = case.read_name()
        self.assert_(cfg.get_cfg().equal(dcfg))
        astk_cfg = astk.Cfg()
        cfg = aster_s.AstkParams(astk_cfg)
        case.use(cfg)
        self.assert_(case.get(aster_s.AstkParams).get_cfg().equal(astk_cfg))

        # Comm and med files
        Comm = aster_s.CommFile
        Med = aster_s.MedFile
        case.use(Comm(comm_file))
        case.use(Med(med_file))
        med = case.get(Med)
        self.assertEqual(med.read_fname(), med_file)
        comm = case.get(Comm)
        self.assertEqual(comm.read_fname(), comm_file)

        # Working directory
        Elt = aster_s.WorkingDir
        self.assert_(case.get(Elt) is None)
        case.use(Elt("/tmp/a"))
        self.assertEqual(case.get(Elt).read_value(), "/tmp/a")

        # Has rmed result
        Elt = aster_s.RemoveRmed
        # XXX should be removed
        self.assert_(case.get(Elt) is None)
        case.use(Elt())
        self.assert_(case.get(Elt).read_value())

        # Has base result 
        Elt = aster_s.HasBaseResult
        self.assert_(case.get(Elt) is None)
        case.use(Elt())
        self.assert_(case.get(Elt).read_value())

    def test_add_study_case_from_export_file(self):
        case = self.std.add_case("c", aster_s.FromExport)
        self.assertEqual(case.node.get_children(), [case.data.node])

        Elt = aster_s.ExportFile
        self.assert_(case.get(Elt) is None)
        case.use(Elt("f.export"))
        export = case.get(Elt)
        self.assertEqual(export.read_fname(), "f.export")
        self.assertEqual(case.data.node.get_children(), [export.node])

    def test_add_study_case_from_aster_profil(self):
        case = self.std.add_case("c", aster_s.FromProfil)
        self.assertEqual(case.node.get_children(), [case.data.node])

        Elt = aster_s.ExportFname
        self.assert_(not case.get(Elt))
        case.use(Elt("/tmp/profil.export"))
        expf = case.get(Elt)
        self.assertEqual(expf.read_name(), "profil.export")

        aprof = {"version" : "STA8.3"}
        Elt = aster_s.AstkProfil
        self.assert_(not case.get(Elt))
        case.use(Elt(aprof))
        prof = case.get(Elt)
        self.assertEqual(prof.read_value(), "ASTER PROFIL")
        profil = prof.load_profil()
        self.assert_(profil is not aprof)
        self.assertEqual(profil, aprof)

        self.assertEqual(case.data.node.get_children(), 
                         [expf.node, prof.node])

    def test_add_study_case_from_element_entry(self):
        std = self.std
        case = std.add_case("from-elt-file")
        comm_file = case.use(aster_s.CommFile("fname.comm"))

        case = std.add_case("from-elt-entry")
        comm_ref = case.use(aster_s.CommEntry(comm_file.node.entry))
        self.assertEqual(comm_ref.node.give_source(), comm_file.node)
        self.assertEqual(comm_ref.read_name(), comm_file.read_name())

        med_entry = aster_s.MedEntry(comm_file.node.entry)
        self.assertRaises(TypeError, case.use, med_entry)

    def test_add_study_case_from_smesh_entry(self):
        std = self.std
        smesh = std.sstd.load_meshes_from(SAT.get_data("forma01a.mmed"))[0]
        case = std.add_case("from-smesh-entry")
        mesh_entry = case.use(aster_s.SMeshEntry(smesh.node.entry))
        self.assertEqual(mesh_entry.node.give_source(), smesh.node)
        self.assertEqual(mesh_entry.read_name(), smesh.read_name())


class TestManageCasesFromStudy(AsterStdTest):

    def test_add_study_cases(self):
        std = self.std
        self.assertEqual(std.node.get_children(), [])

        cases = [std.add_case("c%i" % idx) for idx in range(3)]
        self.assertEqual(len(std.node.get_children()), 3)
        std.close()

    def test_give_cases(self):
        std = self.std
        cases = [
            std.add_case("c1", aster_s.FromComm),
            std.add_case("c2", aster_s.FromProfil),
            std.add_case("c3", aster_s.FromExport),
            std.add_case("c4", aster_s.FromComm),
            ]
        gcases = std.get_all(aster_s.Case)
        self.assertEqual(len(gcases), 4)
        gcase = gcases[0]
        self.assertEqual(gcase.node, cases[0].node)

        self.assertEqual(std.get(aster_s.FromComm).node, cases[0].node)
        self.assertEqual(std.get(aster_s.FromExport).node, cases[2].node)
        self.assertEqual(std.get(aster_s.FromProfil).node, cases[1].node)

    def test_remove_a_case(self):
        std = self.std
        cases = [std.add_case("c%i" % idx) for idx in range(3)]
        cases[1].remove()
        self.assertEqual(len(std.node.get_children()), 2)

    def test_remove_all_cases_when_study_close(self):
        std = self.std
        cases = [std.add_case("c%i" % idx) for idx in range(3)]
        # Allow to check that cases have been removed 
        std.own_std = False
        std.close()
        for case in cases:
            self.assert_(not case.node.is_alive())
        # close as if it was 'own_std = True'
        std.sstd.close_salome_study()


class TestModifyTestCases(AsterStdTest):

    def test_change_a_case_name_with_nom_job(self):
        case = self.std.add_case("a")
        cfg = case.get(aster_s.AstkParams)
        self.assertEqual(case.read_name(), "a")
        self.assertEqual(cfg["name"], "a")
        case.write_name("b")
        self.assertEqual(case.read_name(), "b")
        self.assertEqual(cfg["name"], "b")

    def test_change_the_case_working_dir(self):
        case = self.std.add_case("c")
        case.use(aster_s.WorkingDir("a"))
        self.assertEqual(case.get(aster_s.WorkingDir).read_value(), "a")
        case = case.copy()
        case.use(aster_s.WorkingDir("b"))
        self.assertEqual(case.get(aster_s.WorkingDir).read_value(), "b")

    def test_allow_interactiv_follow_up(self):
        bcase = self.std.add_case("c")
        bcase.use(aster_s.InteractivFollowUp())

        case = AS.load_elt_from_node(bcase.node)
        fup = case.get(aster_s.InteractivFollowUp)
        self.assert_(fup.line.load_attr("value"))

        acs = case.build_astk_case()
        afup = acs.export_bld.get(astk.InteractivFollowUp)
        self.assertEqual(afup.value, "yes")

        cfup = fup.copy_to(self.std)
        self.assert_(cfup.line.load_attr("value"))


class TestCopyStudyCases(AsterStdTest):

    def test_copy_study_case(self):
        std = self.std
        cfg = astk.Cfg()
        case = std.add_case("c")
        case.use(aster_s.WorkingDir("/tmp/a"))
        case.use(aster_s.AstkParams(cfg))
        case.use(aster_s.CommFile("f"))
        case.use(aster_s.RemoveRmed())
        case._build_results()
        case.results.use(aster_s.MessFile("f.mess"))
        
        copy = case.copy()
        # New node used
        self.assertEqual([case.node.entry, copy.node.entry],
                         [node.entry for node in std.node.get_children()])
        # Data section
        self.assert_(copy.data.node.parent is copy.node)
        comms = copy.get_all(aster_s.CommFile)
        self.assertEqual(len(comms), 1)
        self.assertEqual(comms[0].read_fname(), "f")
        # Astk parameters 
        self.assert_(copy.params.node.parent is copy.node)
        pcfg = copy.params.get_cfg()
        self.assert_(pcfg is not cfg)
        self.assert_(pcfg.equal(cfg))
        # Results
        self.assert_(copy.results.node.parent is copy.node)
        mess = copy.get_all(aster_s.MessFile)
        self.assertEqual(len(mess), 1)
        self.assertEqual(mess[0].read_fname(), "f.mess")
        # Others
        self.assert_(copy.get(aster_s.RemoveRmed).read_value())

    def test_copy_study_case_several_times(self):
        case = self.std.add_case("c")
        case.use(aster_s.CommFile("c"))
        case.use(aster_s.MedFile("m"))
        case = AS.load_elt_from_node(case.node)
        case.copy()
        case = AS.load_elt_from_node(case.node)
        case.copy()
        data = case.get(aster_s.DataSection)
        self.assertEqual(len(data.get_all_elts()), 2)

    def test_change_name_when_copying_study_case(self):
        root = self.std.add_case("c")
        root = AS.load_elt_from_node(root.node)
        case = root.copy()
        self.assertEqual(case.node.read_name(), "c-copy")
        root = AS.load_elt_from_node(root.node)
        case = root.copy()
        self.assertEqual(case.node.read_name(), "c-copy1")
        case = AS.load_elt_from_node(case.node)
        copy = case.copy()
        self.assertEqual(copy.node.read_name(), "c-copy1-copy")


if __name__ == "__main__":
    UT.main()

