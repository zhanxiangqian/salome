
import os.path as osp
import unittest as UT

import salome

import aster_s
import ASTER

import salome_aster_tests as SAT
from aster_tests import build_srv


class TestRunCases(UT.TestCase):

    def setUp(self):
        bld = aster_s.StudyBuilder()
        sstd = bld.create_salome_study("std", register=True)
        astd = aster_s.Study(sstd)

        ceng = salome.lcc.FindOrLoadComponent("FactoryServerPy", "ASTER")
        eng = ceng._narrow(ASTER.ASTER_Gen)
        cstd = eng.AttachTo(sstd.sstd)

        self.bld = bld
        self.astd = astd
        self.cstd = cstd
        self.srv = build_srv()
        self.tmp_dir = SAT.TmpDir("run_cases_by_using_corba")

    def tearDown(self):
        self.tmp_dir.clean()
        self.srv.close()
        self.bld.close_all()

    def _bld_comm_job(self, rep, comm):
        case = self.cstd.AddCase('from-comm', ASTER.FromComm)
        case.UseStr(ASTER.CommFile, SAT.write_clt_comm(rep, comm, self.srv))
        case.Use(ASTER.RemoveRmed)
        job = case.Run()
        self.srv.wait_cnt()
        return job

    def test_run_case_from_comm_file(self):
        rep = self.tmp_dir.add("run_cases_from_comm")
        job = self._bld_comm_job(rep, ["cnt.wait_srv()"])

        self.assert_(job.Status() is ASTER.Running)
        self.srv.release_cnt()
        self.assert_(job.WaitResult() is ASTER.Success)
        self.assert_(job.Status() is ASTER.Ended)

    def test_run_case_from_export_file(self):
        from aster_s.astk import give_aster_version
        rep = self.tmp_dir.add("run_cases_from_export_file")
        export = osp.join(rep, "excase.export")
        data = {
            "version" : give_aster_version(),
            "comm" : SAT.write_clt_comm(rep, [], self.srv),
            "results" : osp.join(rep, "excase"),
        }
        fid = open(export, "w")
        fid.write("""\
        P actions make_etude
        P version %(version)s
        P nomjob forma01a
        P debug nodebug
        P mode interactif
        P ncpus 1
        A memjeveux 64
        A tpmax 120
        F comm %(comm)s D 1
        F mess %(results)s.mess R 6
        F resu %(results)s.resu R 8
        """ % data)
        fid.close()

        case = self.cstd.AddCase("from-export-file", ASTER.FromExport)
        case.UseStr(ASTER.ExportFile, export)
        job = case.Run()
        self.assert_(self.srv.wait_cnt())
        job.WaitResult()
        self.assert_(job.Status() is ASTER.Ended)
        self.assert_(job.ResStatus() is ASTER.Success)

    def test_generate_a_failure(self):
        rep = self.tmp_dir.add("generate_a_failure")
        job = self._bld_comm_job(rep, ["generate_a_failure"])
        job.WaitResult()
        self.assert_(job.ResStatus() is ASTER.Failure)

    def test_kill_a_case(self):
        rep = self.tmp_dir.add("kill_a_case")
        job = self._bld_comm_job(rep, ["cnt.wait_srv()"])

        self.assert_(job.Status() is ASTER.Running)
        job.Kill()
        self.assert_(job.Status() is ASTER.Ended)
        self.assert_(job.ResStatus() in (ASTER.Failure, ASTER.Unknown))


if __name__ == "__main__":
    UT.main()

