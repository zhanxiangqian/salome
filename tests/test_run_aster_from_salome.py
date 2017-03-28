# -*- coding: utf-8 -*-
import os.path as osp
import unittest as UT


import aster_s

import salome_aster_tests as AT


class TestRunAsterCase(UT.TestCase):

    def setUp(self):
        self.bld = aster_s.StudyBuilder()
        self.std = self.bld.create("s")
        self.aster_version = aster_s.build_default_cfg()["aster-version"].value
        self.tmp_dir = AT.TmpDir("run_aster_from_salome")

    def tearDown(self):
        self.tmp_dir.clean()
        self.bld.close_all()

    def test_run_comm_file_from_salome(self):
        fname = AT.write_comm(self.tmp_dir.add("comm_file_from_salome"), [
            "DEBUT()",
            "FIN()",
        ])

        case = self.std.add_case("c")
        case.use(aster_s.CommFile(fname))
        case.use(aster_s.RemoveRmed())
        self.check_status(case)

    def write_export_file(self, rep):
        comm = AT.write_comm(rep, [
            "DEBUT()",
            "FIN()",
        ])
        export = osp.join(rep, "test.export")
        fid = open(export, "w")
        data = {
            "version" : self.aster_version, 
            "comm" : comm,
            "resdir" : rep
            }
        fid.write("""\
        P actions make_etude
        P version %(version)s
        P nomjob test
        P debug nodebug
        P mode interactif
        P ncpus 1
        A memjeveux 8
        A tpmax 120
        F comm %(comm)s D 1
        F mess %(resdir)s/test.mess R 6
        F resu %(resdir)s/test.resu R 8
        """ % data)
        fid.close()
        return export

    def test_run_export_file_from_salome(self):
        rep = self.tmp_dir.add("export_file_from_salome")
        export = self.write_export_file(rep)
        
        case = self.std.add_case("c", aster_s.FromExport)
        case.use(aster_s.ExportFile(export))
        self.check_status(case)

    def test_run_astk_profil_case_from_salome(self):
        rep = self.tmp_dir.add("astk_profil_from_salome")
        profil = aster_s.build_aster_profil(self.write_export_file(rep))
        fname = osp.join(rep, "profil.export")
        
        case = self.std.add_case("c", aster_s.FromProfil)
        case.use(aster_s.AstkProfil(profil))
        case.use(aster_s.ExportFname(fname))
        self.check_status(case)

    def check_status(self, case):
        job = case.run()
        self.assert_(job.pid is not None)
        results = case.get(aster_s.ResultsSection)
        self.assert_(results)
        jobid = results.get(aster_s.JobId)
        self.assertEqual(jobid.read_value(), job.pid)

        job.wait_result()
        self.assert_(job.status() is aster_s.ENDED)
        self.assert_(job.res_status() is aster_s.SUCCESS)


if __name__ == "__main__":
    UT.main()

