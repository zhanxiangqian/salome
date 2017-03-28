"""Run the Aster solver and control the process execution.
"""
import os.path as osp
import unittest as UT
import subprocess as SP


import aster_s.astk as AS
import salome_aster_tests as ST
from aster_tests import build_srv
 

RUNNING, ENDED, UNKNOWN = [object() for idx in range(3)]


class Process(object):
    """Imitate an ASTK process
    """

    def __init__(self, fname):
        self._popen = SP.Popen("python %s" % fname, 
                               shell=True, stderr=SP.PIPE)

    def status(self):
        """Return the current status"""
        prc = self._popen
        if prc.poll() is None:
            return RUNNING
        elif prc.poll() == 0:
            return ENDED
        else:
            return UNKNOWN

    def wait(self):
        """Wait until the process terminates"""
        self._popen.wait()


class TestControlProcessThroughSockets(UT.TestCase):

    def setUp(self):
        self.srv = build_srv()
        self.tmp_dir = ST.TmpDir("test_aster_sockets")

    def tearDown(self):
        self.tmp_dir.clean()
        self.srv.close()

    def test_connect_a_client_socket_to_a_server(self):
        # Useful for checking that the Aster command file 
        # has been executed
        from aster_tests import Cnt
        srv = self.srv
        self.assert_(not srv.has_cnt())
        cnt = Cnt(srv.port)
        self.assert_(srv.wait_cnt())
        self.assert_(srv.has_cnt())
        cnt.close()

    def _start_clt(self, rep, lines, srv=None):
        srv = srv or self.srv
        comm = [
            "from aster_tests import Cnt",
            "cnt = Cnt(%i)" % srv.port,
            ] + lines + [
            "cnt.close()",
            ]
        fname = ST.write_comm(self.tmp_dir.add(rep), comm, "clt.py")
        return Process(fname)

    def test_control_client_process_by_breakpoints(self):
        lines = [
            "cnt.wait_srv()",
            "cnt.wait_srv()",
        ]
        proc = self._start_clt("control_client", lines)
        self.assert_(self.srv.wait_cnt())
        self.assert_(proc.status() is RUNNING)
        self.srv.release_cnt()
        self.assert_(proc.status() is RUNNING)
        self.srv.release_cnt()
        proc.wait()
        self.assert_(proc.status() is ENDED)

    def test_handle_several_process_status_correctly(self):
        comm = (
            ["cnt.wait_srv()", "create_failure"],
            ["cnt.wait_srv()"],
        )
        srvs = [build_srv() for idx in range(2)]
        procs = [self._start_clt("c%i" % idx, lines, srv) 
                 for idx, (lines, srv) in enumerate(zip(comm, srvs))]
        
        for srv in srvs:
            self.assert_(srv.wait_cnt())
        self.assert_(procs[1].status() is RUNNING)
        srvs[1].release_cnt()
        procs[1].wait()
        self.assert_(procs[1].status() is ENDED)

        self.assert_(procs[0].status() is RUNNING)
        srvs[0].release_cnt()
        procs[0].wait()
        self.assert_(procs[0].status() is UNKNOWN)


class TestRunAsterCase(UT.TestCase):
    """Contract that a JobBehavior must implement
    """

    def setUp(self):
        self.srv = build_srv()
        self.tmp_dir = ST.TmpDir("run_aster_solver")

    def tearDown(self):
        self.tmp_dir.clean()
        self.srv.close()

    def check(self, cond, callback):
        """Call the callback if the condition is false"""
        try:
            self.assert_(cond)
        except:
            callback()
            raise

    def _write_comm(self, rep, lines, srv=None):
        """Write an Aster command file especially for tests"""
        srv = srv or self.srv
        return ST.write_clt_comm(rep, lines, srv)

    def _bld_case(self, rep, lines, name="c", srv=None):
        """Build an Aster case especially for tests"""
        case_rep = self.tmp_dir.add(rep)
        case = AS.build_case(name)
        case.use(AS.CommFile(self._write_comm(case_rep, lines, srv)))
        case.remove(AS.RRMedFile)
        return case

    def test_run_an_aster_command_file(self):
        case = self._bld_case("run_aster", [])

        job = case.run()

        self.assert_(self.srv.wait_cnt())
        def see():
            print case.get_result(AS.MessFile).read()
        self.check(job.wait_result() is AS.SUCCESS, see)
        self.assert_(AS.RMedFile in case._result_types)

    def write_forma01a(self, rep):
        export = osp.join(rep, "forma01a.export")
        data = {
            "version" : AS.give_aster_version(),
            "comm" : self._write_comm(rep, []),
            "results" : osp.join(rep, "forma01a"),
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
        return export

    def test_run_from_astk_export_file(self):
        rep = self.tmp_dir.add("from_astk_export_file")
        export = self.write_forma01a(rep)

        case = AS.build_case("from-export", AS.FromExport)
        case.load_export(export)
        job = case.run()
        self.assert_(self.srv.wait_cnt())
        self.assert_(job.wait_result() is AS.SUCCESS)

    def test_run_from_aster_profil(self):
        rep = self.tmp_dir.add("from_astk_profil")
        prof = AS.build_aster_profil(self.write_forma01a(rep))
        export = osp.join(rep, "profil.export")

        case = AS.build_case("from-profil", AS.FromProfil)
        case.use_profil(prof)
        case.use_fname(export)
        job = case.run()
        self.assert_(self.srv.wait_cnt())
        self.assert_(job.wait_result() is AS.SUCCESS)

    def test_simulate_a_failure(self):
        case = self._bld_case("simulate_aster_failure", [
            "generate_failure",
        ])

        job = case.run()

        self.assert_(self.srv.wait_cnt())
        self.assert_(job.wait_result() is AS.FAILURE)
        self.assert_("'generate_failure' is not defined" in \
                     case.get_result(AS.MessFile).read())
        self.assert_(AS.RMedFile not in case._result_types)

    def test_query_status_during_process(self):
        case = self._bld_case("query_status", [
            # Imitate a long calcul
            "cnt.wait_srv()",
            "cnt.wait_srv()",
        ])

        job = case.run()
        status = job.status()
        self.assert_(status is AS.RUNNING)
        self.assertEqual(status.from_astk, "RUN")
        self.assert_(self.srv.wait_cnt())
        self.assert_(job.status() is AS.RUNNING)
        self.srv.release_cnt()
        self.assert_(job.status() is AS.RUNNING)
        self.srv.release_cnt()
        self.assert_(job.wait_result() is AS.SUCCESS)
        status = job.status()
        self.assert_(status is AS.ENDED)
        self.assertEqual(status.from_astk, "ENDED")

    def test_kill_a_job(self):
        case = self._bld_case("kill_a_job", [
            # A long calcul without end
            "cnt.wait_srv()",
        ])

        job = case.run()

        self.assert_(self.srv.wait_cnt())
        self.assert_(job.status() is AS.RUNNING)
        job.kill()
        self.assert_(job.status() is AS.ENDED)
        status = job.res_status()
        self.assert_(status in (AS.FAILURE, AS.UNKNOWN))
        self.assert_(status.from_astk in ("<F>_ERROR", "_"))

    def test_handle_several_jobs_status_correctly(self):
        comms = (
            # A long calcul that is going to be killed
            ["cnt.wait_srv()"],
            # A failure after some work
            ["cnt.wait_srv()", "generate_failure"],
            # A success after some work
            ["cnt.wait_srv()"],
        )
        srvs = [build_srv() for idx in range(3)]
        cases = [self._bld_case("jstatus%i" % idx, lines, "c%i" % idx, srv) 
                 for idx, (lines, srv) in enumerate(zip(comms, srvs))]

        jobs = [case.run() for case in cases]

        for srv in srvs:
            self.assert_(srv.wait_cnt())
        self.assert_(jobs[1].status() is AS.RUNNING)
        srvs[1].release_cnt()

        self.assert_(jobs[2].status() is AS.RUNNING)
        srvs[2].release_cnt()
        jobs[2].wait_result()
        self.assert_(jobs[2].status() is AS.ENDED)
        self.assert_(jobs[2].res_status() is AS.SUCCESS)

        jobs[1].wait_result()
        self.assert_(jobs[1].status() is AS.ENDED)
        self.assert_(jobs[1].res_status() is AS.FAILURE)

        self.assert_(jobs[0].status() is AS.RUNNING)
        jobs[0].kill()
        self.assert_(jobs[0].status() is AS.ENDED)
        self.assert_(jobs[0].res_status() in (AS.FAILURE, AS.UNKNOWN))


if __name__ == "__main__":
    UT.main()


