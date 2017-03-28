# -*- coding: utf-8 -*-

# XXX The CORBA definition of the Aster module should go here.
# This modules is automatically loaded by the server as an
# entry point

import sys
import os
import traceback
import inspect

import salome
import SALOME
from SALOME_ComponentPy import SALOME_ComponentPy_i as Component
from SALOME_DriverPy import SALOME_DriverPy_i as Driver
import SALOME_TYPES
from LifeCycleCORBA import LifeCycleCORBA

from salome.kernel.parametric.compo_utils import (
    create_input_dict,
    create_normal_parametric_output,
    create_error_parametric_output
    )


import ASTER_ORB__POA as AORB
from ASTER_ORB__POA import ASTER_Gen
from ASTER_ORB import (
    FromComm,
    FromExport,
    WorkingDir,
    CommFile,
    MedFile,
    SMeshEntry,
    RemoveRmed,
    ExportFile,
    MessFile,
    ResuFile,
    RMedFile,
    Running,
    Ended,
    Success,
    Alarm,
    Failure,
    Unknown,
    )

import aster_s
import aster_s.astk as astk
from aster_s.utils import log
from aster_s.parametric import (
    build_probabilistic_case,
    create_probabilistic_profil,
    get_values_from_mess
    )


class Elt(AORB.Elt):
    """A CORBA element building the Aster study case
    """

    def GetEntry(self):
        """Return the node entry"""
        return self.inst.node.entry


class Job(AORB.Job):
    """The job supervising the Aster process
    """
    _corba_status = {
        aster_s.RUNNING : Running,
        aster_s.ENDED : Ended,
        aster_s.SUCCESS : Success,
        aster_s.ALARM : Alarm,
        aster_s.FAILURE : Failure,
    }

    def __init__(self, inst):
        self.inst = inst

    def _get_corba_status(self, status):
        """Return the corba status from the given aster status"""
        try:
            cstatus = self._corba_status[status]
        except KeyError:
            cstatus = Unknown
        return cstatus

    def Status(self):
        """Return the current status of the job"""
        return self._get_corba_status(self.inst.status())

    def ResStatus(self):
        """Return the result status"""
        return self._get_corba_status(self.inst.res_status())

    def WaitResult(self):
        """Wait until the job is finished and return its final status"""
        status = self.inst.wait_result()
        return self._get_corba_status(status)

    def Kill(self):
        """Kill the running case"""
        self.inst.kill()


class StudyCase(AORB.StudyCase, Elt):
    """A CORBA study case
    """
    elt_types = {
        WorkingDir : aster_s.WorkingDir,
        CommFile : aster_s.CommFile,
        MedFile : aster_s.MedFile,
        SMeshEntry : aster_s.SMeshEntry,
        RemoveRmed : aster_s.RemoveRmed,
        ExportFile : aster_s.ExportFile,
        MessFile : aster_s.MessFile,
        ResuFile : aster_s.ResuFile,
        RMedFile : aster_s.RMedFile,
    }

    def __init__(self, inst):
        self.inst = inst
        self._jobs = []

    def _get_elt_type(self, corba_elt_type):
        """Return the Aster element type from the CORBA one"""
        return self.elt_types[corba_elt_type]

    def ReadName(self):
        """Return the case name"""
        return self.inst.read_name()

    def Use(self, corba_elt_type):
        """Use the given element type"""
        elt_type = self._get_elt_type(corba_elt_type)
        self.inst.use(elt_type())

    def UseStr(self, corba_elt_type, value):
        """Use the given element type with its string value"""
        elt_type = self._get_elt_type(corba_elt_type)
        self.inst.use(elt_type(value))

    def Run(self):
        """Run the Aster solver"""
        log.debug("StudyCase.Run: enter")
        try:
            job = Job(self.inst.run())
            self._jobs.append(job)
        except Exception, e:
            traceback.print_exc()
            _raiseSalomeException(e.__str__())
        return job._this()

    def ResultFileName(self, corba_elt_type):
        """Return the filename of the result of the given element type"""
        log.debug("StudyCase.ResultFileName: enter")
        elt_type = self._get_elt_type(corba_elt_type)
        elt = self.inst.get(elt_type)
        log.debug("found element is %s", elt)
        if elt is None:
            fname = ""
        else:
            fname = elt.read_fname()
        return fname


class Study(AORB.Study, Elt):
    """A CORBA Aster study
    """
    _case_types = {
        FromComm : aster_s.FromComm,
        FromExport : aster_s.FromExport,
    }

    def __init__(self, sstd):
        self.inst = aster_s.attach_study_to(sstd)
        self._study_cases = []

    def AddCase(self, name, corba_case_type):
        """Add an Aster study case"""
        study_cases = self._study_cases
        names = [scase.ReadName() for scase in study_cases]
        if name not in names:
            case = self.inst.add_case(name, self._case_types[corba_case_type])
            study_case = StudyCase(case)
            study_cases.append(study_case)
            log.debug("AddCase: new CORBA StudyCase created, name = %s", name)
        else:
            study_case = study_cases[names.index(name)]
            log.debug("AddCase: existing CORBA StudyCase returned, name = %s", name)
        return study_case._this()

    def GiveCases(self):
        """Return the added cases"""
        return [scase._this() for scase in self._study_cases]


class ASTER(ASTER_Gen, Component, Driver):
    """Allow to load the ASTER component
    """

    def __init__(self, orb, poa, cid, cname, instn, intfn):
        log.debug("ASTER.__init__ called")
        Component.__init__(self, orb, poa, cid, cname, instn, intfn, 0)
        self._astds = {}
        # attributes for OpenTurns interface
        self._otcase = None
        if salome.lcc is None:
            salome.lcc = LifeCycleCORBA(orb)

    def AttachTo(self, sstd):
        """Return an Aster study"""
        astds = self._astds
        sidx = sstd._get_StudyId()
        if sidx not in astds:
            astd = Study(sstd)
            astds[sidx] = astd
            log.debug("AttachTo: new CORBA Study created, study id is %s", sidx)
        else:
            astd = astds[sidx]
            log.debug("AttachTo: existing CORBA Study returned, study id is %s", sidx)
        return astd._this()

    def GiveAsterVersion(self):
        """Return the Aster version used by default.
        """
        return astk.give_aster_version()

    # --- BEGIN - OpenTurns interface
    def Init(self, studyId, caseEntry):
        """This method is an implementation for the ASTER interface.
        It sets the component with some deterministic parametrization.
        """
        log.debug("ASTER.Init: enter")
        log.debug("ASTER.Init: studyId = %d - caseEntry = %s",
                  studyId, caseEntry)
        # load aster case
        try:
            self._otcase = aster_s.load_case_from_studyId_and_entry(studyId, caseEntry)
        except Exception:
            traceback.print_exc()
            log.error("[ERROR] can not load Aster case from study Id = %s"
                      " and case entry = %s", studyId, caseEntry)
            self._raiseSalomeError()
        log.debug("ASTER.Init: exit")

    def Exec(self, paramInput):
        """This method is an implementation for the ASTER interface.
        It runs the component with some new parameters compared with the deterministic ones.
        """
        log.debug("ASTER.Exec: enter")
        if self._otcase is None :
            log.error("ASTER.Exec: Init not run")
            self._raiseSalomeError()
        log.debug("ASTER.Exec: inputVarList: %s" % paramInput.inputVarList)
        log.debug("ASTER.Exec: outputVarList: %s" % paramInput.outputVarList)
        log.debug("ASTER.Exec: inputValues: %s" % paramInput.inputValues)
        wrkdir = os.getcwd()
        log.debug("ASTER.Exec: workdir: %s" % wrkdir)
        values = create_input_dict({}, paramInput)
        log.debug("ASTER.Exec: dict of values: %s" % values)
        caseId = None
        mode = 'batch'
        for parameter in paramInput.specificParameters:
            log.debug("ASTER p.nam : %s : %s", parameter.name, parameter.value)
            if parameter.name == "id":
                caseId = parameter.value
            if parameter.name == "executionMode":
                mode = parameter.value
        log.debug("ASTER.Exec: caseId: %s" % caseId)

        try:
            log.debug("ASTER.Exec: build astk case from %s", self._otcase)
            acs = self._otcase.build_astk_case()
            log.debug("ASTER.Exec: build probabilistic case from %s and values (%s)", acs, values)
            new_acs = build_probabilistic_case(acs, values, caseId, wrkdir, mode)
            jobname = new_acs._name
        except Exception:
            traceback.print_exc()
            return create_error_parametric_output("[ERROR] unabled to build the probabilistic case")

        try:
            log.debug("ASTER.Exec: start job %s", jobname)
            job = new_acs.run()
            log.debug("ASTER.Exec: waiting result...")
            job.wait_result()
            log.debug("ASTER.Exec: job %s ended", jobname)
        except Exception:
            traceback.print_exc()
            return create_error_parametric_output("[ERROR] unabled to run the probabilistic case")

        try:
            log.debug("ASTER.Exec: status %s", job.status())
            log.debug("ASTER.Exec: res_status %s", job.res_status())
            assert job.status() is aster_s.ENDED
            assert job.res_status() in (aster_s.SUCCESS, aster_s.ALARM)
        except AssertionError:
            return create_error_parametric_output("[ERROR] case %s ends with status %s" \
                % (jobname, job.res_status()))

        computedValues = {}
        try:
            mess = new_acs.get_result(astk.MessFile)
            log.debug("ASTER.Exec: reading %s", mess.fname)
            varlist = paramInput.outputVarList
            try:
                computedValues = get_values_from_mess(mess.fname, varlist)
            except AssertionError, exc:
                log.error("[ERROR] %s", str(exc))
                self._raiseSalomeError()
            log.info("[OK] Job %s successfully ended", jobname)
            log.info("INPUT  : %s", paramInput.inputValues)
            paramOutput = create_normal_parametric_output(computedValues, paramInput)
            log.info("OUTPUT: %s", paramOutput.outputValues)
            return paramOutput
        except Exception:
            traceback.print_exc()
            return create_error_parametric_output("[ERROR] unable to extract output value(s)")

    def Finalize(self):
        """This method is an implementation for the ASTER interface.
        It cleans everything set so far.
        """
        log.debug("ASTER.Finalize : pass")
        return
    
    def GetFilesToTransfer(self, studyId, caseEntry):
        """This method is an implementation for the ASTER interface.
        This method can be used to specify files to transfer to the
        computation resource.
        """
        log.debug("ASTER.GetFilesToTransfer: studyId = %d - caseEntry = %s",
                  studyId, caseEntry)
        try:
            case = aster_s.load_case_from_studyId_and_entry(studyId, caseEntry)
            acs = case.build_astk_case()
            resudir, prof, relocated = create_probabilistic_profil(acs)
            log.info("GetFilesToTransfer:\n%s", prof)
            log.debug("resudir: %s", resudir)
            inputFiles = [entry.path for entry in prof.get_data()]
            outputFiles = [entry.path for entry in relocated.get_type('repe').get_result()]
            log.info("GetFilesToTransfer:\ninputs : %s\n outputs : %s", inputFiles, outputFiles)
            return inputFiles, outputFiles
        except:
            log.critical("Check that the deterministic calculation is valid (runnable)")
            self._raiseSalomeError()

    def _raiseSalomeError(self):
        message = "Error in component %s running in container %s." % (self._instanceName, self._containerName)
        log.exception(message)
        message += " " + traceback.format_exc()
        exc = SALOME.ExceptionStruct(SALOME.INTERNAL_ERROR, message,
                                     inspect.stack()[1][1], inspect.stack()[1][2])
        raise SALOME.SALOME_Exception(exc)
    # --- END - OpenTurns interface


def _raiseSalomeException(userMessage):
    """
    This function throws a SALOME exception based on the last exception raised,
    and with the specified message as user information to be displayed.
    """
    exc_type, exc_obj, exc_tb = sys.exc_info()
    filename   = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    linenumber = exc_tb.tb_lineno
    logmessage=(exc_type, filename, linenumber)
    log.debug("An exception is raised "+str(logmessage)+": "+str(userMessage))

    raise SALOME.SALOME_Exception(SALOME.ExceptionStruct(
                                  SALOME.INTERNAL_ERROR,
                                  userMessage,
                                  filename,
                                  linenumber))
