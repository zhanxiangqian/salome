"""Testing Astk parameters manipulation
"""
import os
import os.path as osp
import unittest as UT
from cStringIO import StringIO

import aster_s
import aster_s.astk as AS
from salome_aster_tests import get_data, TmpDir


class TestChangeAstkImplementation(UT.TestCase):

    def setUp(self):
        bld = AS.AstkBuilder
        self._impls = bld.astk_impl, bld.job_impl_type
        self.bld = bld

    def tearDown(self):
        bld = self.bld
        bld.astk_impl, bld.job_impl_type = self._impls

    def test_switch_astk_implementaion(self):
        bld = self.bld
        impl = object()
        self.assert_(bld.astk_impl is not impl)
        aster_s.use_astk(impl)
        self.assert_(bld.astk_impl is impl)

    def test_only_accept_given_job_implementation(self):
        bld = self.bld
        jtype = object()
        aster_s.use_job_impl(jtype)
        self.assertRaises(TypeError, bld.create_job_impl)


class TestHaveConfigForASTKexportfile(UT.TestCase):
    
    def test_allow_to_modify_only_added_parameters(self):
        cfg = AS.Cfg()
        cfg.add("aster-version", AS.Line("version", "10.0"))
        self.assertEqual(cfg["aster-version"].value, "10.0")

        self.assertRaises(KeyError, cfg.__getitem__, "proc-nb") 
        cfg.add("proc-nb", AS.Line("ncpus"))
        cfg["proc-nb"].value = 5
        self.assertEqual(cfg["proc-nb"].value, 5)

    def test_allow_to_add_only_one_time(self):
        cfg = AS.Cfg()
        cfg.add("a", AS.Line("a"))
        self.assertRaises(KeyError, cfg.add, "a", AS.Line("a"))

    def test_remove_a_parameter(self):
        cfg = AS.Cfg()
        cfg.add("p", AS.Line("proc"))
        self.assert_(cfg["p"].value is None)

        cfg.remove("p")
        try:
            val = cfg["p"]
            self.fail()
        except KeyError, exc:
            self.assertEqual(exc.args[0], AS.Cfg._mess % "p")

        self.assertRaises(KeyError, cfg.remove, "p")

    def test_remove_a_parameter_from_many(self):
        cfg = AS.Cfg()
        for key in ["a", "b", "c"]:
            cfg.add(key, AS.Line(key))
        lines = cfg.lines()

        cfg.remove("c")

        self.assertEqual(cfg.lines(), [lines[0], lines[1]])

    def test_give_default_config(self):
        cfg = AS.AstkBuilder().build_default_cfg()
        keys = [val[0] for val in AS.DCFG]
        for key in keys:
            try:
                self.assert_(cfg[key] is not None)
            except AssertionError:
                print "'%s' key not found in default config" % key
                raise

    def test_not_allow_default_config_modification(self):
        dcfg = AS.AstkBuilder().build_default_cfg()
        cfg = AS.AstkBuilder().build_default_cfg()
        self.assert_(cfg is not dcfg)
        self.assertEqual(cfg["mode"].value, "interactif")

        cfg["mode"].value = "bash"
        self.assertEqual(cfg["mode"].value, "bash")
        self.assertEqual(dcfg["mode"].value, "interactif")

    def test_check_two_configuration_equality(self):
        cfgs = [AS.Cfg() for idx in range(2)]
        for cfg in cfgs:
            cfg.add("v", AS.Param("v", "v1")) 
            cfg.add("p", AS.Attr("p", "p1")) 
        self.assert_(cfgs[0] is not cfgs[1])
        self.assert_(cfgs[0].equal(cfgs[1]))
        cfgs[0]["v"].value = "v2"
        self.assert_(not cfgs[0].equal(cfgs[1]))

    def test_copy_configuration_objects(self):
        copy = AS.Line("v", 128).copy()
        self.assertEqual(copy._key, "v")
        self.assertEqual(copy.value, 128)

        copy = AS.FileLine("comm", 20, "f").copy()
        self.assertEqual(copy._key, "comm")
        self.assertEqual(copy._idx, 20)
        self.assertEqual(copy.fname, "f")
        
    def test_copy_configuration(self):
        cfg = AS.Cfg()
        cfg.add("v", AS.Param("v", "v1"))
        cfg.add("c", AS.Attr("m", "f"))
        copy = cfg.copy()
        self.assert_(copy is not cfg)
        self.assert_(copy.equal(cfg))

        self.assert_(cfg["v"] is not copy["v"])
        self.assert_(cfg["c"] is not copy["c"])


class TestHaveAnExportFileBuilder(UT.TestCase):

    def setUp(self):
        self.tmp_dir = TmpDir("export_file_builder")

    def tearDown(self):
        self.tmp_dir.clean()

    def test_build_export_file(self):
        rep = self.tmp_dir.add("build")
        comm = get_data("forma01a.comm")
        med = get_data("forma01a.comm")
        cfg = AS.Cfg()
        cfg.add("v", AS.Param("version", "STA10.0"))
        cfg.add("name", AS.Param("nomjob"))
        cfg.add("m", AS.Param("mode", "bash"))
        cfg.add("n", AS.Attr("nb-cpu", 2))

        bld = AS.ExportFileBuilder("forma01-case")
        bld.working_dir = rep
        bld.add(cfg)
        bld.add(AS.RMessFile())
        bld.add(AS.CommFile(comm))
        bld.add(AS.MedFile(med))
        bld.add(AS.RResuFile())
        bld.add(AS.RRMedFile())
        bld.add(AS.Base())

        fname = bld.write().fname

        fpat = osp.join(rep, "forma01-case")
        self.assertEqual(fname, fpat + ".export") 
        res = [
            "P version STA10.0",
            "P nomjob forma01-case",
            "P mode bash",
            "A nb-cpu 2",
            "F comm %s D 1" % comm,
            "F mmed %s D 20"% med,
            "F mess %s R 6" % (fpat + ".mess"),
            "F resu %s R 8" % (fpat + ".resu"),
            "F rmed %s R 80" % (fpat + ".rmed"),
            "R base %s RC 0" % (fpat + "base"),
            ]
        fid = open(fname)
        expf = fid.read()
        for line in res:
            self.assert_(line in expf, "not found : %s" % line)
        fid.close()

        
    def test_use_comm_file_rep_if_no_rep_given(self):
        rep = self.tmp_dir.add("no_rep_given")
        cfg = AS.Cfg()
        cfg.add("name", AS.Param("nomjob", "test"))
        cfg.add("mode", AS.Param("mode", "batch"))
        comm = osp.join(rep, "f.comm")
        open(comm, "w").close()
        case = AS.build_case("f")
        case.use(cfg)
        case.use(AS.CommFile(comm))
        
        fname = case.build_export_file().fname

        self.assert_(osp.isfile(fname))
        self.assertEqual(osp.dirname(fname), rep)
        self.assert_(case.export_bld.working_dir is None)

    def test_allow_interactiv_follow_up(self):
        wdir = self.tmp_dir.add("inter_follow_up")
        comm = __file__

        case = AS.FromComm("c")
        cfg = AS.Cfg()
        cfg.add("n", AS.Param("nomjob", "ifup"))
        cfg.add("m", AS.Param("mode", "batch"))
        case.use(cfg)
        case.use_working_dir(wdir)
        case.use(AS.InteractivFollowUp())
        case.use(AS.CommFile(comm))
        
        fname = case.build_export_file().fname
        
        res = [
            "P nomjob ifup",
            "P mode batch",
            "P follow_output yes",
            "F comm %s D 1" % comm,
            ]
        fid = open(fname)
        expf = fid.read()
        for line in res:
            self.assert_(line in expf, "not found : %s" % line)
        fid.close()


class TestPrepareASTKCase(UT.TestCase):

    def setUp(self):
        self.tmp_dir = TmpDir("manipulate_astk_parameters")

    def tearDown(self):
        self.tmp_dir.clean()

    def test_be_built_with_default_params(self):
        cfg_def = AS.AstkBuilder().build_default_cfg()
        case = AS.build_case("forma01a")
        case_cfg = case.export_bld.get(AS.Cfg)
        self.assert_(case_cfg is not cfg_def)
        self.assert_(case_cfg.equal(cfg_def))

    def test_add_existing_comm_and_med_files(self):
        case = AS.build_case("c")
        bld = case.export_bld
        comm = get_data("forma01a.comm")
        case.use(AS.CommFile(comm))
        self.assertEqual(bld.get(AS.CommFile).fname, comm)
        
        med = get_data("forma01a.mmed")
        case.use(AS.MedFile(med))
        self.assertEqual(bld.get(AS.MedFile).fname, med)

        self.assertRaises(IOError, AS.CommFile, "wrong-file") 
        self.assertRaises(IOError, AS.MedFile, "wrong-file") 

    def write_export_file(self, rep_name, lines):
        fname = osp.join(self.tmp_dir.add(rep_name), "astk.export")
        fid = open(fname, "w")
        fid.write(os.linesep.join(lines))
        fid.close()
        return fname

    def test_add_existing_export_file(self):
        case = AS.build_case("c", AS.FromExport)
        export = self.write_export_file("existing-file", [
        "P nomjob j",
        "P mode inter",
        ]) 
        case.load_export(export)
        self.assertEqual(case.export_file.fname, export)
        self.assertRaises(IOError, case.load_export, "wrong-file") 

    def test_build_case_for_astk_profil(self):
        source = self.write_export_file("astk-profil", [
        "P nomjob j",
        "P mode inter",
        "F comm /aster/case.comm D 1",
        "F mess /tmp/mess R 6",
        "F resu /tmp/resu R 8",
        ]) 
        prof = AS.build_aster_profil(source)
        prof["nomjob"] = "p"
        prof.Get("R", "resu")[0]["path"] = "/aster/case.resu"
        export = osp.join(osp.dirname(source), "profil.export")

        case = AS.build_case("c", AS.FromProfil)
        case.use_profil(prof)
        case.use_fname(export)
        exf = case.build_export_file()
        self.assertEqual(exf.fname, export)
        self.assertEqual(exf.get_nomjob(), "p")
        resu = exf.get_result(AS.ResuFile)
        self.assertEqual(resu.fname, "/aster/case.resu")

    def test_raise_error_if_no_profil_or_fname(self):
        FP = AS.FromProfil
        case = AS.build_case("c", FP)
        case.use_profil(AS.build_aster_profil())
        try:
            exf = case.build_export_file()
            self.fail()
        except ValueError, exc:
            self.assertEqual(exc.args[0], FP._fname_mess)

        case = AS.build_case("c", FP)
        case.use_fname(__file__)
        try:
            exf = case.build_export_file()
            self.fail()
        except ValueError, exc:
            self.assertEqual(exc.args[0], FP._profil_mess)

    def test_raise_error_if_comm_or_export_file_absent(self):
        case = AS.build_case("c")
        self.assertRaises(IOError, case.build_export_file)

    def test_find_nom_job_and_mode_from_export_file(self):
        fname = self.write_export_file("export_file", [
        "P nomjob astk-job",
        "P mode inter",
        ])
        exf = AS.ExportFile(fname)
        self.assertEqual(exf.get_nomjob(), "astk-job")
        self.assertEqual(exf.get_mode(), "inter")

    def test_not_accept_export_file_without_mode(self):
        ExpF = AS.ExportFile
        fname = self.write_export_file("export_file_without_mode", [
        "P nomjob astk-job",
        ])
        try:
            exf = ExpF(fname)
            self.fail()
        except ValueError, exc:
            self.assertEqual(exc.args[0], ExpF._mode_mess % fname)

    def test_not_accept_export_file_without_nomjob(self):
        ExpF = AS.ExportFile
        fname = self.write_export_file("export_file_without_nomjob", [
        "P mode inter",
        ])
        try:
            exf = ExpF(fname)
            self.fail()
        except ValueError, exc:
            self.assertEqual(exc.args[0], ExpF._nomjob_mess % fname)

    def test_give_results_files(self):
        resdir = self.tmp_dir.add("results")
        fnames = {
            "mess" : osp.join(resdir, "res.mess"),
            "resu" : osp.join(resdir, "res.resu"),
            "rmed" : osp.join(resdir, "res.mmed"),
        }
        contents = {
            "mess" : "Mess file",
            "resu" : "Resu file",
            "rmed" : "Med file",
        }
        for key in fnames:
            fid = open(fnames[key], "w")
            fid.write(contents[key])
            fid.close()

        fname = self.write_export_file("give_mess_result_file", [
        "P nomjob job",
        "P mode inter",
        "F mmed /input.med D 20",
        "F mess %s R 6" % fnames["mess"],
        "F resu %s R 8" % fnames["resu"],
        "F rmed %s R 80" % fnames["rmed"],
        ])
        exf = AS.ExportFile(fname)

        rtypes = (
            ("mess", AS.MessFile),
            ("resu", AS.ResuFile),
            ("rmed", AS.RMedFile),
        )
        for key, rtype in rtypes:
            res = exf.get_result(rtype)
            try:
                self.assertEqual(res.read(), contents[key])
            except AssertionError, exc:
                mess = "Error for key '%s': %s"
                raise AssertionError(mess % (key, exc.args[0]))


class TestPrepareCaseForStanley(UT.TestCase):

    def setUp(self):
        try:
            disp = os.environ["DISPLAY"]
        except KeyError:
            disp = None
        else:
            del os.environ["DISPLAY"]
        self._disp = disp
        self.tmp_dir = TmpDir("manipulate_stanley")

    def tearDown(self):
        if self._disp:
            os.environ["DISPLAY"] = self._disp
        self.tmp_dir.clean()

    def test_write_export_file_for_stanley(self):
        wdir = self.tmp_dir.add("write_stanley_export")
        basename = "/tmp/aster/base_dir"
        res = [
            "P nomjob stanley",
            "P mode bash",
            "P special stanley%%NEXT%%R base %s DC 0" % basename,
        ]
        cfg = AS.Cfg()
        cfg.add("name", AS.Param("nomjob", "stanley"))
        cfg.add("m", AS.Param("mode", "bash"))
        case = AS.build_case("run_stanley", AS.RunStanley)
        case.use_working_dir(wdir)
        case.use(cfg)
        case.use(AS.StanleyBase(basename))
        exf = case.build_export_file()
        fid = open(exf.fname)
        lines = fid.read().splitlines()
        for line in res:
            self.assert_(line in lines, line)
        fid.close()

if __name__ == "__main__":
    UT.main()

