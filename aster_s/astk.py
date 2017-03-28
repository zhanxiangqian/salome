# -*- coding: utf-8 -*-
"""Interface for running the Aster solver througth ASTK.
"""
import os
import os.path as osp
import subprocess as SP
from socket import gethostname
from platform import architecture
from time import sleep
import re
import tempfile

from aster_s import SALOME_MECA_VERSION, ASTER_REFVERSION
from aster_s.utils import Singleton, get_login, log, DEBUG


ASTK_CONF_DIR = ".astkrc_salome%s" % SALOME_MECA_VERSION


class FilePart(object):
    """A part of an ASTK export file.
    """

    def copy(self):
        """Copy the file part"""
        raise NotImplementedError

    def write_to(self, bld, last=False):
        """Write the part to the ExportFileBuilder"""
        raise NotImplementedError


class Line(FilePart):
    """A line with a value in the ASTK export file.
    """
    _pattern = "%(type)s %(key)s %(value)s"

    def __init__(self, astk_key, value=None):
        self._key = astk_key
        self.value = value

    def copy(self):
        """Copy the values of the line into a new object"""
        return self.__class__(self._key, self.value)

    def equal(self, line):
        """Test if two lines are equal"""
        return (self.value == line.value)

    def write_line(self, fid, astk_type, last=False):
        """Write a line with the given astk_type"""
        vals = {
            "type" : astk_type,
            "key" : self._key,
            "value" : self.value,
        }
        fid.write(self._pattern % vals)
        if not last:
            fid.write(os.linesep)


class FileLine(FilePart):
    """A line with a file in the ASTK export file
    """
    _pattern = "F %(key)s %(path)s%(fname)s %(ftype)s %(idx)i"

    def __init__(self, astk_key, aster_idx, fname=None):
        self._key = astk_key
        self.fname = fname
        self._idx = aster_idx
        print '--------------------------- astk.py FileLine ----------------------'
        print fname
        print '----------------------------------------------------------------------------'

    def copy(self):
        """Copy the values of the file line into a new object"""
        return self.__class__(self._key, self._idx, self.fname)

    def write_line(self, bld, ftype, last=False):
        """Write a file line having its own type and aster index"""
        vals = {
            "key" : self._key,
            "path" : bld.path,
            "fname" : self.fname,
            "ftype" : ftype,
            "idx" : self._idx
        }
        bld.fid.write(self._pattern % vals)
        if not last:
            bld.fid.write(os.linesep)


class DirLine(FilePart):
    """A line with a directory in the ASTK export file
    """
    _pattern = "R %(key)s %(path)s%(dname)s %(dtype)s %(idx)i"

    def __init__(self, astk_key, aster_idx, dname=None):
        self._key = astk_key
        self.dname = dname
        self._idx = aster_idx

    def copy(self):
        """Copy the values of the dir line into a new object"""
        return self.__class__(self._key, self._idx, self.dname)

    def write_line(self, bld, dtype, last):
        """Write a file line having its own type and aster index"""
        vals = {
            "key" : self._key,
            "path" : bld.path,
            "dname" : self.dname,
            "dtype" : dtype,
            "idx" : self._idx
        }
        bld.fid.write(self._pattern % vals)
        if not last:
            bld.fid.write(os.linesep)


class SingleValue(FilePart):
    """Object storing a single value
    """

    def __init__(self, value):
        self.value = value

    def copy(self):
        """Copy the given value"""
        return self.__class__(self.value)

    def equal(self, inst):
        """Test if two time objects are equal"""
        return (self.value == inst.value)


class Time(SingleValue):
    """Time in seconds creating an Astk parameter (tpsjob)
    and argument (tpmax).
    """

    def write_to(self, bld, last=False):
        """Write the time parameters to ExportFileBuilder"""
        time = self.value
        attrs = [Param("tpsjob", int(time / 60.)), Attr("tpmax", time)]
        for attr in attrs:
            attr.write_to(bld, last)


class Memory(SingleValue):
    """Memory in Mo creating an Astk parameter (memjob)
    and argument (memjeveux).
    """
    _arch = architecture()[0]

    def set_arch(self, arch):
        """Allow to adjust architecture according to server platform."""
        self._arch = arch

    def write_to(self, bld, last=False):
        """Write the time parameters to ExportFileBuilder"""
        mem = self.value
        fac = 4.
        if self._arch.startswith("64"):
            fac = 8.
        attrs = [Param("memjob", mem * 1024.), Attr("memjeveux", mem / fac)]
        for attr in attrs:
            attr.write_to(bld, last)


class Param(Line):
    """An ASTK parameter
    """

    def write_to(self, bld, last=False):
        """Write a line starting with P"""
        self.write_line(bld.fid, "P", last)

    def get_astk_key(self):
        return self._key

class Attr(Line):
    """An ASTK attribute
    """

    def write_to(self, bld, last=False):
        """Write a line starting with A"""
        self.write_line(bld.fid, "A", last)


class DataFile(FileLine):
    """An ASTK input file
    """

    def __init__(self, key, fname, idx):
        FileLine.__init__(self, key, idx)
        self.use_fname(fname)

    def use_fname(self, fname):
        """Use the given filename"""
        # we can't because we don't know if the case has to be run here
        #check_isfile(fname)
        self.fname = fname

    def write_to(self, bld, last=False):
        """Write a line starting with F and give the type D"""
        #peter.zhang, for cygwin
        self.fname = self.fname.replace(':', '')
        self.fname = self.fname.replace('\\', '/')
        self.fname = "/cygdrive/" + self.fname
        self.write_line(bld, "D", last)


class CommFile(DataFile):
    """An ASTK command file
    """

    def __init__(self, fname, idx=1):
        DataFile.__init__(self, "comm", fname, idx)


class MedFile(DataFile):
    """An ASTK command file
    """

    def __init__(self, fname, idx=20):
        DataFile.__init__(self, "mmed", fname, idx)


class RResultFile(FileLine):
    """An ASTK result file
    """

    def write_to(self, bld, last=False):
        """Write a line starting with F and give the type R"""
        if self.fname is None:
            self.fname = bld.pattern + "." + self._key
        #peter.zhang, for cygwin
        self.fname = self.fname.replace(':', '')
        self.fname = self.fname.replace('\\', '/')
        self.fname = "/cygdrive/" + self.fname
        self.write_line(bld, "R", last)


# the following results should be merged
# with MessFile, ResuFile, RMedFile
class RMessFile(RResultFile):
    """The Aster mess file
    """

    def __init__(self, idx=6):
        RResultFile.__init__(self, "mess", idx)


class RResuFile(RResultFile):
    """The Aster resu file
    """

    def __init__(self, idx=8):
        RResultFile.__init__(self, "resu", idx)


class RRMedFile(RResultFile):
    """The Aster med result file
    """

    def __init__(self, idx=80):
        RResultFile.__init__(self, "rmed", idx)

    def write_to(self, bld, last=False):
        """Write the result med file"""
        if self.fname is None:
            self.fname = bld.pattern + ".rmed"
        RResultFile.write_to(self, bld, last)


class Base(DirLine):
    """An ASTK base
    """

    def __init__(self, idx=0):
        DirLine.__init__(self, "base", idx)

    def write_to(self, bld, last=False):
        """Write a line starting with R and give the type RC"""
        if self.dname is None:
            self.dname = bld.pattern + "." + self._key
        #peter.zhang, for cygwin
        self.dname = self.dname.replace(':', '')
        self.dname = self.dname.replace('\\', '/')
        self.dname = "/cygdrive/" + self.dname
        self.write_line(bld, "RC", last)


class StanleyBase(FilePart):
    """An existing base used for Stanley input.
    """
    pattern = "P special stanley%%NEXT%%R base %s DC 0"
    orb_pattern_mask = "A ORBInitRef NameService=corbaname::%s:%s"

    def __init__(self, name, server=None):
        self._name = name
        self._server = server
        self._path = ""

    def copy(self):
        """Copy the base"""
        return self.__class__(self._name)

    def write_to(self, bld, last=False):
        """Write the part to the ExportFileBuilder"""
        import salome_utils
        nshost = salome_utils.getHostFromORBcfg()
        nsport = salome_utils.getPortFromORBcfg()
        orb_pattern = self.orb_pattern_mask % (nshost, nsport)
        bld.fid.write(orb_pattern + os.linesep)
        bld.fid.write(self.pattern % (self._path + self._name))
        if not last:
            bld.fid.write(os.linesep)


class InteractivFollowUp(Param):
    """Allow to run a terminal following the Aster process.
    """
    _key = "follow_output"
    value = "yes"
    disp_pattern = "P display %s"

    def __init__(self):
        pass

    def write_to(self, bld, last=False):
        """Write the part to the ExportFileBuilder"""
        import salome_utils
        Param.write_to(self, bld, last)
        try:
            disp = os.environ["DISPLAY"]
            expr = re.compile("(:[0-9\.]+$)")
            if expr.sub("", disp) == "":
                ndisp = ":0"
                mat = expr.search(disp)
                if mat != None:
                    ndisp = mat.group(1)
                disp = salome_utils.getHostFromORBcfg() + mat.group(1)
        except KeyError:
            mess = "'DISPLAY' not found for following the Aster process"
            raise EnvironmentError(mess)
        else:
            bld.fid.write(self.disp_pattern % disp + os.linesep)


class Cfg(FilePart):
    """A configuration for writing a part of an ASTK export file.

    Lines are added to a list as the order is relevant for the final
    writing. Once a line is added, only its value can be changed by
    using its key.
    """
    _mess = "'%s' not found, a line should be added to the configuration"

    def __init__(self):
        self._keys = []
        self._data = {}

    def add(self, key, line, pos=None):
        """Add a line to the configuration"""
        if key not in self._data:
            if pos is not None:
                self._keys.insert(pos, key)
            else:
                self._keys.append(key)
            self._data[key] = line
        else:
            raise KeyError("Line with key '%s' already added" % key)

    def has(self, key):
        """Tell if the key has been added"""
        return (key in self._data)

    def __getitem__(self, key):
        """Return the line object for the given key"""
        if key not in self._data:
            raise KeyError(self._mess % key)
        return self._data[key]

    def keys(self):
        """Return the list of configuration keys"""
        return list(self._keys)

    def lines(self):
        """Return the list of lines"""
        return [self._data[key] for key in self._keys]

    def items(self):
        """Return the tuple key, line of the configuration"""
        return [(key, self._data[key]) for key in self._keys]

    def remove(self, key):
        """Remove a line from its key"""
        line = self[key]
        if line:
            self._keys.remove(key)
            del self._data[key]

    def equal(self, cfg):
        """Test if two configurations contains the same lines data"""
        res = False
        keys = self._keys
        data = self._data
        cdata = cfg._data
        if (keys == cfg._keys):
            for key in keys:
                if not data[key].equal(cdata[key]):
                    break
            else:
                res = True
        return res

    def copy(self):
        """Copy the configuration"""
        copy = self.__class__()
        for key in self._keys:
            line = self[key].copy()
            copy.add(key, line)
        return copy

    def write_to(self, bld, last=False):
        """Write lines to file"""
        if not self._keys:
            return
        if self.has("name"):
            name = self["name"]
            if name.value is None:
                name.value = bld.name
        lines = self.lines()
        for line in lines[:-1]:
            line.write_to(bld)
        lines[-1].write_to(bld, last)


# ExportFileBuilder should inherit from ExportFile
class ExportFileBuilder(object):
    """Build an Astk export file
    """
    _template = """P uclient %s
P mclient %s
""" % (get_login(), gethostname())

    def __init__(self, name="astk", suffix=".export"):
        self.name = name
        self._suffix = suffix
        self.working_dir = None
        self.pattern = None
        self.fid = None
        self.path = ""
        self._parts = []

    def use(self, part):
        """Use the given part to the export file. Remove any previous
        part of the same type."""
        self.remove(part.__class__)
        return self.add(part)

    def add(self, part):
        """Add a part of the export file"""
        self._parts.append(part)
        return part

    def get(self, part_type):
        """Return the first file part found from the given type"""
        parts = self.get_all(part_type)
        if parts:
            return parts[0]

    def get_all(self, part_type):
        """Return all the file parts found from the given type"""
        parts = []
        for part in self._parts:
            if isinstance(part, part_type):
                parts.append(part)
        return parts

    def remove(self, part_type):
        """Remove the file part from its type"""
        parts = self._parts
        for part in parts[:]:
            if isinstance(part, part_type):
                parts.remove(part)

    def _sort_parts(self):
        """Sort the file parts between data and results and
        put configuration at first."""
        conf, input, res  = [], [], []
        for part in self._parts:
            if isinstance(part, DataFile):
                input.append(part)
            elif isinstance(part, (RResultFile, Base)):
                res.append(part)
            else:
                conf.append(part)
        return conf + input + res

    def check_depends(self):
        """Check dependencies between export parts."""
        serv_arch = '32bit'
        cfg = self.get(Cfg)
        _check_cfg(cfg)
        # get server architecture
        if cfg.has("server"):
            serv_cfg = None
            for serv in find_servers():
                if cfg["server"].value == serv["nom_complet"]:
                    serv_cfg = serv
                    serv_arch = arch_from_platform(serv.get("plate-forme", ""))
                    break
            # fill server parameters
            change_server_cfg(cfg, cfg["server"].value)
        # architecture value is needed by memory parameter
        if cfg.has("memory"):
            mem = cfg["memory"]
            mem.set_arch(serv_arch)

    def write(self, alternate_working_dir=None, name=None):
        """Write the ASTK export file (into ``name`` if provided)."""
        if not self._parts:
            raise ValueError("Nothing to write")

        working_dir = self.working_dir or alternate_working_dir
        if working_dir is None and name is None:
            raise ValueError("A working directory needs to be given")

        pattern = osp.join(working_dir, self.name)
        if name is None:
            name = pattern + self._suffix
        fid = open(name, "w")
        self.pattern = pattern
        self.fid = fid
        fid.write(self._template)
        self.check_depends()
        cfg = self.get(Cfg)

        parts = self._sort_parts()
        for part in parts[:-1]:
            part.write_to(self)
        parts[-1].write_to(self, last=True)

        fid.close()
        return ExportFile(name)


class ResultType(object):
    """An ASTK result
    """

    def __init__(self, profil):
        self.profil = profil

    def build(self):
        """Build the instance results with data found in ASTK profil"""
        raise NotImplementedError

    def build_for(self, astk_key):
        """Build file with value found in path"""
        prof = self.profil
        cls = self.__class__

        results = []
        for data in prof.Get("R", astk_key):
            # Removing localhost information if present
            path = data["path"].split(":", 1)[-1]
            result = cls(prof, path)
            results.append(result)
        return results

    def build_first(self):
        """Build the first mess file found if any and stop"""
        results = self.build()
        if results:
            return results[0]


class ResultFile(ResultType):
    """An ASTK result file
    """

    def __init__(self, profil, fname=None):
        ResultType.__init__(self, profil)
        self.fname = fname

    def read(self):
        """Read the file content"""
        if self.fname:
            fid = open(self.fname)
            content = fid.read()
            fid.close()
            return content


class MessFile(ResultFile):
    """The message file produced by the Aster solver
    """

    def build(self):
        """Build for the 'mess' key"""
        return self.build_for("mess")


class ResuFile(ResultFile):
    """The result message file produced by the Aster solver
    """

    def build(self):
        """Build for the 'resu' key"""
        return self.build_for("resu")


class RMedFile(ResultFile):
    """The result med file produced by the Aster solver
    """
    def build(self):
        """Build the result for the 'rmed' key"""
        return self.build_for("rmed")


class BaseResult(ResultType):
    """The base results produced by the Aster solver
    """

    def __init__(self, profil, dname=None):
        self.profil = profil
        self.dname = dname

    def build(self):
        """Build for the 'base' key"""
        return self.build_for("base")


class ExportFile(object):
    """An Astk export file.
    Needs to give the job name and mode."""
    _mode_mess = "'P mode' line not found in export file '%s'"
    _nomjob_mess = "'P nomjob' line not found in export file '%s'"

    def __init__(self, fname):
        check_isfile(fname)
        self.profil = AstkBuilder().create_aster_profil(fname)
        if self.get_nomjob() is None:
            raise ValueError(self._nomjob_mess % fname)
        if self.get_mode() is None:
            raise ValueError(self._mode_mess % fname)
        self.fname = fname

    def get_param(self, key):
        """Return a parameter value from its key"""
        return self.profil[key]

    def get_val(self, key):
        """Return a parameter value from its key or None"""
        val = self.get_param(key)[0]
        if val:
            return val
        else:
            return None

    def get_nomjob(self):
        """Return the ASTK entry 'P nomjob' or None if not found"""
        return self.get_val("nomjob")

    def get_mode(self):
        """Return the ASTK entry 'P mode' or None if not found"""
        return self.get_val("mode")

    def get_result(self, result_type):
        """Return a Result object from the Aster solver"""
        result = result_type(self.profil)
        return result.build_first()

    def check(self):
        """Method to call before each run."""
        # retreive the configuration of the selected server.
        sname = self.get_val("serveur")
        if not sname:
            sname = get_default_server()
        # update self.profil
        sprof = init_profil_on_server(sname)
        sprof.update(self.profil)
        self.profil = sprof
        # check required keys
        miss = []
        _req_keys_ = (
            "serveur", "username", "aster_root", "proxy_dir",
            "protocol_exec", "protocol_copyto", "protocol_copyfrom",
        )
        for key in _req_keys_:
            if self.get_val(key) is None:
                log.warn("Key '%s' is missing in export file.", key)
                miss.append(key)
        if len(miss) > 0:
            mess = "These keys are missing in export file : %s", ', '.join(miss)
            raise EnvironmentError(mess)


AS_RUN_CMD = object()

class AstkImpl(object):
    """ASTK implementation contract.
    """
    rcdir = ASTK_CONF_DIR
    # see also refresh_time in job_supervision.py...
    refresh_delay = 2
    query_delay = 0

    def __init__(self):
        raise NotImplementedError

    def build_default_cfg(self):
        """Return the default configuration for running Aster"""
        raise NotImplementedError

    def create_job_impl(self, impl_type):
        """Build an ASTK job supervising an Aster running case according
        to the implementation: 'AS_RUN_CMD'."""
        raise NotImplementedError

    def create_aster_profil(self, fname=None, run=None):
        """Create an AsterProfil"""
        raise NotImplementedError

    def give_astk_cmd(self):
        """Should return the astk client command according to the ASTK
        implementation"""
        raise NotImplementedError

    def find_servers(self, force_refresh=False):
        """Should find servers for ASTK"""
        raise NotImplementedError


class AstkBuilder(Singleton):
    """Build ASTK main instance (AS_RUN) or give 'as_run' command.
    This class is a Singleton as the ASTK main directory needs
    to be retrieved only one time.
    Several ASTK versions can be used, they are implemented
    through AstkImpl.
    """
    # Default implementation set at the module end
    astk_impl = AstkImpl
    job_impl_type = AS_RUN_CMD

    def init(self):
        """Initialize the singleton instance"""
        self._impl = self.astk_impl()

    def build_default_cfg(self):
        """Return the default configuration for running Aster"""
        return self._impl.build_default_cfg()

    def create_job_impl(self):
        """Build an ASTK job supervising an Aster running case."""
        itype = self.job_impl_type
        if itype is not AS_RUN_CMD:
            mess = "Wrong job implementation type, " \
                   "should be 'aster.AS_RUN_CMD'."
            raise TypeError(mess)
        return self._impl.create_job_impl(itype)

    def create_aster_profil(self, fname=None, run=None):
        """Create an ASTK profil called AsterProfil according
        to the Astk implementation"""
        return self._impl.create_aster_profil(fname, run)

    def build_as_run(self):
        """Return the run object of the ASTK implementation"""
        return self._impl.build_as_run()

    def give_astk_cmd(self):
        """Return the astk command according to the ASTK implementation"""
        return self._impl.give_astk_cmd()

    def find_servers(self, force_refresh=False):
        """Find servers for ASTK"""
        return self._impl.find_servers(force_refresh)

    def get_server_config(self, server_name):
        """Return a server configuration"""
        return self._impl.get_server_config(server_name)


def use_astk(astk_impl):
    """Switch the Astk implementation"""
    AstkBuilder.astk_impl = astk_impl

def set_refresh_delay(time):
    """Set the refresh delay when waiting for Astk process"""
    AstkBuilder.astk_impl.refresh_delay = time

def set_query_delay(time):
    """Set the delay before querying Astk"""
    AstkBuilder.astk_impl.query_delay = time

def use_job_impl(job_impl_type):
    """Switch the Aster job implementation"""
    AstkBuilder.job_impl_type = job_impl_type

def build_default_cfg():
    """Build the default Astk configuration"""
    return AstkBuilder().build_default_cfg()

def give_aster_version():
    """Return the Aster version used by default"""
    return build_default_cfg()["aster-version"].value

def build_aster_profil(fname=None, run=None):
    """Build an ASTK profil called AsterProfil. The returned
    profil will depend of the ASTK version used."""
    return AstkBuilder().create_aster_profil(fname, run)

def build_as_run():
    """Return the run object of the ASTK implementation"""
    return AstkBuilder().build_as_run()

def give_astk_cmd():
    """Return the astk client command according to the ASTK implementation"""
    return AstkBuilder().give_astk_cmd()

def find_servers(force_refresh=False):
    """Find servers for ASTK"""
    return AstkBuilder().find_servers(force_refresh)

def get_server_config(sname):
    log.debug("get_server_config")
    return AstkBuilder().get_server_config(sname)

def get_default_server():
    sname = None
    servs = find_servers()
    if servs:
        sname = servs[0]["nom_complet"]
    return sname

def get_pid():
    run = build_as_run()
    return run.get_pid()

class Status(object):
    """Represent the Astk status
    """

    def __init__(self, desc):
        self._desc = desc
        self.from_astk = None

    def get_desc(self):
        """Return the description status"""
        return self._desc

    def __repr__(self):
        return self.get_desc()


DESC_LST = ["Success", "Inexact", "Alarm", "Failure", "Running", "Pending", "Ended", "Unknown"]

(SUCCESS,
INEXACT,
ALARM,
FAILURE,
RUNNING,
PENDING,
ENDED,
UNKNOWN) = [Status(desc) for desc in DESC_LST]


class AstkError(Exception):
    """An Astk error"""


class JobImpl(object):
    """Interface for implementing an Aster job supervision
    """
    _status_from_astk = {}

    def __init__(self):
        self.pid = None

    def start(self, export_file):
        """Need to run an aster case from the ASTK export file"""
        raise NotImplementedError

    def wait_result(self):
        """Need to wait until the job is finished and return its final
        status"""
        raise NotImplementedError

    def _get_status(self, astk_status):
        """Return the status from the given ASTK status"""
        cod = astk_status
        mat = re.search('(<.>)', cod)
        if mat:
            cod = mat.group(1)
        try:
            res = self._status_from_astk[cod]
        except KeyError:
            res = UNKNOWN
        res.from_astk = astk_status
        return res

    def status(self):
        """Need to return the current status of the job."""
        raise NotImplementedError

    def res_status(self):
        """Need to return the result status."""
        raise NotImplementedError

    def kill(self):
        """Need to kill the running case"""
        raise NotImplementedError

    def has_results(self):
        """Test if the job has valid results"""
        raise NotImplementedError


class Job(object):
    """Supervise an Aster running case
    """

    def __init__(self, case):
        self._case = case
        self._impl = AstkBuilder().create_job_impl()
        self.pid = self._impl.pid

    def start(self, export_file):
        """Run the aster case from the ASTK export file"""
        log.debug("Job.start: export file = %s", export_file)
        self._impl.start(export_file)
        self.pid = self._impl.pid
        log.debug("Job.start: end")

    def wait_result(self):
        """Wait until the job is finished and return its final status"""
        log.debug("Job.wait_result: enter")
        res = self._impl.wait_result()
        log.debug("Job.wait_result: res=%s", res)
        self.terminate()
        log.debug("Job.wait_result: end")
        return res

    def status(self):
        """Return the current status of the job. Running, ended or
        may be unknown"""
        return self._impl.status()

    def res_status(self):
        """Return the result status. Could be success, failure or unknown
        if the case did not finish"""
        log.debug("Job.res_status: enter")
        res = self._impl.res_status()
        log.debug("Job.res_status: end")
        return res

    def has_results(self):
        """Test if the job has valid results"""
        return self._impl.has_results()

    def kill(self):
        """Kill the running case"""
        self._impl.kill()

    def terminate(self):
        """Terminate the running job by adding results on study case"""
        log.debug("Job.terminate: enter")
        if self.has_results():
            self._case.add_results()
        log.debug("Job.terminate: end")


def check_isfile(fname):
    """Check that fname is a file"""
    if not osp.isfile(fname):
        log.info("Filename '%s' not found" % fname)     # very usefull using corba
        raise IOError("Filename '%s' not found" % fname)


class Case(object):
    """An ASTK case for running the Aster solver.
    """

    def __init__(self, name):
        self._name = name
        self.export_file = None

    def build_default(self):
        """Build default configuration on case"""
        pass

    def build_export_file(self, name=None):
        """Build the ASTK export file for running the Aster case"""
        raise NotImplementedError

    def run(self, job=None):
        """Run the Aster fonctionalities from the given configuration
        and input data."""
        # Allow to pass another kind of Job
        job = job or Job(self)
        job.start(self.build_export_file())
        return job

    def get_export_file(self):
        """Return the ASTK export file object . It will be built if
        necessary using a temporary file."""
        print '--------------------------- astk.py get_export_file 1----------------------'
        print '----------------------------------------------------------------------------'
        if self.export_file is None:
            fd, path = tempfile.mkstemp()
            print '--------------------------- astk.py get_export_file 2----------------------'
            print path
            print '----------------------------------------------------------------------------'
            os.close(fd)
            self.export_file = self.build_export_file(path)
            print '--------------------------- astk.py get_export_file 3----------------------'
            print self.export_file
            print '----------------------------------------------------------------------------'
            _remove_file(path)
        return self.export_file

    def _get_export_file(self):
        """Return the ASTK export file if built"""
        if self.export_file:
            return self.export_file
        else:
            raise ValueError("The case has not been run")

    def get_result(self, result_type):
        """Return a Result object from the Aster solver"""
        return self._get_export_file().get_result(result_type)

    def add_results(self):
        """Add results when the case terminate"""
        pass


class FromComm(Case):
    """An ASTK case built from a command file

    Is made of three parts:

        - the Aster solver parameters
        - the input files (made of DataFile)
        - the result files (made of ResultFile)

    """

    def __init__(self, name):
        Case.__init__(self, name)
        self.export_bld = ExportFileBuilder(name)
        self._result_types = [
            MessFile,
            ResuFile,
        ]

    def build_default(self):
        """Build the default Aster case"""
        bld = self.export_bld
        bld.add(AstkBuilder().build_default_cfg())
        bld.add(RMessFile())
        bld.add(RResuFile())
        bld.add(RRMedFile())

    def use_working_dir(self, rep):
        """Use the given working directory"""
        self.export_bld.working_dir = rep

    def use(self, part):
        """Use the given part building the Aster Case"""
        self.export_bld.use(part)

    def remove(self, part_type):
        """Remove the parts matching the given type"""
        self.export_bld.remove(part_type)

    def build_export_file(self, name=None):
        """Build the ASTK export file for running the Aster case"""
        bld = self.export_bld
        comm = bld.get(CommFile)
        if not comm:
            raise IOError("A command file needs to be given")
        # alternate_working_dir will also be used for mess, resu, rmed result files
        exf = bld.write(alternate_working_dir=osp.dirname(comm.fname), name=name)
        print '--------------------------- astk.py build_export_file ----------------------'
        print comm.fname
        print '----------------------------------------------------------------------------'
        self.export_file = exf
        return exf

    def add_results(self):
        """Add results when the case terminate"""
        self._result_types.extend([
            RMedFile,
            BaseResult,
        ])

    def get_result(self, result_type):
        """Return a Result object from the Aster solver"""
        if result_type in self._result_types:
            return Case.get_result(self, result_type)


class FromExport(Case):
    """An ASTK case built from an export file
    """

    def __init__(self, name):
        Case.__init__(self, name)

    def load_export(self, fname):
        """Load an ASTK export file for running the Aster study case"""
        print '--------------------------- astk.py load_export ----------------------'
        print fname
        print '----------------------------------------------------------------------------'
        self.export_file = ExportFile(fname)

    def build_export_file(self, name=None):
        """Build the ASTK export file for running the Aster case"""
        if not self.export_file:
            raise IOError("An export file needs to be given")
        return self.export_file


class FromProfil(Case):
    """An ASTK case built from an ASTK profil (AsterProfil)
    """
    _profil_mess = "An AsterProfil needs to be given"
    _fname_mess = "A filename for writting the export file needs to be given"

    def __init__(self, name):
        Case.__init__(self, name)
        self.profil = None
        self.fname = None

    def use_profil(self, profil):
        """Use an ASTK profil, AsterProfil instance"""
        self.profil = profil

    def use_fname(self, export_fname):
        """Use the given filename for writting the export file
        represented by the profile"""
        self.fname = export_fname
        print '--------------------------- astk.py use_fname ----------------------'
        print export_fname
        print '----------------------------------------------------------------------------'

    def build_export_file(self, name=None):
        """Build the ASTK export file for running the Aster case"""
        if not self.profil:
            raise ValueError(self._profil_mess)
        if not self.fname:
            raise ValueError(self._fname_mess)
        print '--------------------------- astk.py FromProfil build_export_file 1----------------------'
        print self.fname
        print '----------------------------------------------------------------------------'
        self.profil.WriteExportTo(self.fname)
        print '--------------------------- astk.py FromProfil build_export_file 2----------------------'
        print self.fname
        print '----------------------------------------------------------------------------'
        exf = ExportFile(self.fname)
        print '--------------------------- astk.py FromProfil build_export_file 3----------------------'
        print self.fname
        print '----------------------------------------------------------------------------'
        self.export_file = exf
        print '--------------------------- astk.py FromProfil build_export_file 4----------------------'
        print exf
        print '----------------------------------------------------------------------------'
        return exf


class RunStanley(Case):
    """A case for running Stanley
    """

    def __init__(self, name):
        Case.__init__(self, name)
        self._bld = ExportFileBuilder(name)

    def build_default(self):
        """Set default parameter"""
        self._bld.add(AstkBuilder().build_default_cfg())

    def use_working_dir(self, rep):
        """Use the given working directory"""
        self._bld.working_dir = rep

    def use_aster_version(self, aster_version):
        """Use the given ASTER version for running Stanley"""
        cfg = self._bld.get(Cfg)
        cfg["aster-version"].value = aster_version

    def use_aster_server(self, server):
        """Use the given ASTER server for running Stanley"""
        cfg = self._bld.get(Cfg)
        cfg["server"].value = server

    def use_mode(self, mode):
        """Use the given ASTER server for running Stanley"""
        cfg = self._bld.get(Cfg)
        cfg["mode"].value = mode

    def use(self, part):
        """Use the given part for building the Aster case"""
        self._bld.use(part)

    def build_export_file(self, name=None):
        """Build the ASTK export file for running the Aster case"""
        exf = self._bld.write(name=name)
        self.export_file = exf
        return exf



def build_case(name, case_type=FromComm):
    """Build an Aster study case"""
    case = case_type(name)
    case.build_default()
    return case

def run_stanley(basename, aster_version=None, server=None, force_local=False):
    """Run Stanley on the existing base name"""
    log.debug("run_stanley with aster_version=%s, server=%s, local=%s",
              aster_version, server, force_local)
    if force_local:
        server = get_local_server_name()
    case = build_case("run_stanley", RunStanley)
    if aster_version:
        serv_cfg = get_server_config(server)
        log.debug("config server %s : %s", server, serv_cfg)
        versions = serv_cfg['vers']
        if versions:
            versions = versions.split()
        else:
            versions = []
        aster_version = choose_nearest_version(aster_version, versions)
        case.use_aster_version(aster_version)
    if server:
        case.use_aster_server(server)
    case.use_working_dir(osp.dirname(basename))
    case.use_mode("interactif")
    case.use(InteractivFollowUp())
    case.use(StanleyBase(basename))
    job = case.run()
    job.wait_result()


# default configuration for ASTK
DCFG = [
    ("astk-action", Param("actions", "make_etude")),
    ("aster-version", Param("version")),
    ("name", Param("nomjob", "salome-aster-job")),
    ("debug", Param("debug", "nodebug")),
    ("mode", Param("mode", "interactif")),
    ("proc-nb", Param("ncpus", 1)),
    ("memory", Memory(512)),
    ("time", Time(600)),
    ("login", Param("username", get_login())),
    ("server", Param("serveur", "localhost")),

    ("aster_root", Param("aster_root", "/aster")),
    ("protocol_exec", Param("protocol_exec", "asrun.plugins.server.SSHServer")),
    ("protocol_copyto", Param("protocol_copyto", "asrun.plugins.server.SCPServer")),
    ("protocol_copyfrom", Param("protocol_copyfrom", "asrun.plugins.server.SCPServer")),
    ("proxy_dir", Param("proxy_dir", "/tmp/")),

    ("build-script", Param("consbtc", "oui")),
    ("submit-script", Param("soumbtc", "oui")),
    ("origin", Param("origine", "salomemeca_asrun 1.10.0")),
]
SERVER_CFG_KEYS = (
    "aster_root", "login", "server",
    "protocol_exec", "protocol_copyto","protocol_copyfrom",
    "proxy_dir",
)

def _build_default_cfg(astk_impl):
    """Build the default configuration for ASTK"""
    cfg = Cfg()
    for key, line in DCFG:
        cfg.add(key, line.copy())
    log.debug("build_default_cfg keys : %s", cfg.keys())

    # Get default values from ASTK
    asr = astk_impl.build_as_run()
    cfg["aster-version"].value = asr.get("default_vers")
    if asr.get("batch") == "oui":
        cfg["mode"].value = "batch"
    sname = get_local_server_name()
    if sname:
        cfg["server"].value = sname
    return cfg

def get_local_server_name():
    """Return the local server as known in the servers configuration.
    Return the first one if localhost is not found,
    or None if the configuration contains no server."""
    locserv = None
    snames = [serv["nom_complet"] for serv in find_servers()]
    if snames:
        log.debug("available servers are : %s", snames)
        found = False
        for serv in snames:
            if is_local(serv):
                locserv = serv
                found = True
                break
        if not found:
            locserv = snames[0]
    return locserv

def _check_cfg(cfg):
    """Check that the parameters of the default configuration exist.
    Usefull when reading an old case."""
    for key, line in DCFG:
        if not cfg.has(key):
            cfg.add(key, line.copy())
            log.info("Parameter '%s' missed. It has been added.", key)

def change_server_cfg(cfg, sname):
    """Fill server parameters for server ``sname``.
    If the first attempt fails, refresh the servers list and try again."""
    ok = False
    try:
        _change_server_cfg(cfg, sname)
        ok = True
    except KeyError, exc:
        log.debug("KeyError getting configuration of '%s' : %s", sname, str(exc))
    if not ok:
        log.info("Force refresh of servers configuration.")
        find_servers(force_refresh=True)
        try:
            _change_server_cfg(cfg, sname)
            ok = True
        except KeyError, exc:
            log.warn("############################KeyError getting configuration of '%s' : %s",
                      sname, str(exc))
    if not ok:
        msg = ("Configuration of server '%s' is invalid. Please " + \
              "refresh the configuration manually and try again.") % sname
        log.error(msg)
        raise EnvironmentError(msg)

def _change_server_cfg(cfg, sname):
    """Fill server parameters for server ``sname``."""
    serv_cfg = get_server_config(sname)
    assert serv_cfg, "server not found : %s" % sname
    log.debug("config of %s : %s", sname, serv_cfg)
    for key in SERVER_CFG_KEYS:
        log.debug("cfg.has(%s)=%s", cfg[key].get_astk_key(), cfg.has(key))
    for key in SERVER_CFG_KEYS:
        #log.debug("cfg.has(%s)=%s", key, cfg.has(key))
        cfg[key].value = serv_cfg[cfg[key].get_astk_key()]

def init_profil_on_server(sname):
    """Build a new AsterProfil with the parameters of the server ``sname``."""
    from asrun.client.config import serv_infos_prof
    cfg = get_server_config(sname)
    log.debug("config server %s : %s", sname, cfg)
    #TODO check required keys
    prof = serv_infos_prof(cfg)
    return prof

class AsRunCmd(JobImpl):
    """Implement an Aster job supervision by using the ASTK 'as_run'
    command
    """
    # Equivalence between 'as_run --actu' and current module
    _status_from_astk = {
        "OK" : SUCCESS,
        "NOOK" : INEXACT,
        "<A>" : ALARM,
        "<S>" : FAILURE, "<E>" : FAILURE, "<F>" : FAILURE,
        "RUN" : RUNNING,
        "PEND" : PENDING,
        "ENDED" : ENDED,
    }

    def __init__(self, astk_impl):
        JobImpl.__init__(self)
        self._astk_impl = astk_impl
        self._actu_cmd = None
        self._del_cmd = None
        self._popen = None

    def start(self, export_file):
        """Start the Aster solver by using 'as_run --serv'"""
        log.debug("AsRunCmd.start: enter")
        from asrun.calcul import parse_submission_result
        as_run_cmd = self._astk_impl.give_as_run_cmd(export_file)
        #peter.zhang for remote connection
        export_file.fname = export_file.fname.replace('\\', '/')
        cmd = as_run_cmd + [
            "--serv",
            export_file.fname,
            ]
        popen = SP.Popen(cmd, stdout=SP.PIPE)
        self._popen = popen

        output = popen.communicate()[0]
        log.info("Output of command : %s\n%s", " ".join(cmd), output)
        res = parse_submission_result(output)
        jobid, queue = res[:2]
        if jobid == "?":
            mess = "Error occurs during submitting job"
            raise EnvironmentError(mess)

        self.pid = jobid
        name = export_file.get_nomjob()
        mode = export_file.get_mode()
        self._actu_cmd = as_run_cmd + [
            "--actu",
            jobid,
            name,
            mode,
            ]
        self._del_cmd = as_run_cmd + [
            "--del",
            jobid,
            name,
            mode,
            ]

    def wait_result(self):
        """Wait the process to terminate by asking periodically the job
        status with 'as_run'"""
        log.debug("AsRunCmd.wait_result: enter")
        refresh_delay = self._astk_impl.refresh_delay
        while True:
            sleep(refresh_delay)
            if self.status() is ENDED:
                break
        log.debug("AsRunCmd.wait_result: end")
        return self.res_status()

    def _get_var(self, idx):
        """Return the variable value given by 'as_run --actu'"""
        from asrun.job import parse_actu_result
        # Astk delay before querying
        sleep(self._astk_impl.query_delay)
        popen = SP.Popen(self._actu_cmd, stdout=SP.PIPE, stderr=SP.PIPE)
        out, err = popen.communicate()
        res = parse_actu_result(out)
        log.debug("Job status: %s", res)
        if popen.returncode != 0:
            log.debug("stderr :\n%s", err)
        return res[idx]

    def status(self):
        """Return the current job status by using the 'ETAT' variable
        given by 'as_run --actu'"""
        return self._get_status(self._get_var(0))

    def res_status(self):
        """Return the result status by using the 'DIAG' variable
        given by 'as_run --actu'"""
        return self._get_status(self._get_var(1))

    def kill(self):
        """Kill the running case by using 'as_run --del'"""
        popen = SP.Popen(self._del_cmd, stdout=SP.PIPE)
        popen.wait()

    def has_results(self):
        """Test if the job has valid results by using AsterRun.GetGrav"""
        status = self.res_status()
        aster_run = self._astk_impl.build_as_run()
        return (aster_run.GetGrav(status.from_astk) <= 4)

class AsRun1_10(JobImpl):
    """Implement an Aster job supervision by using an AsterCalcHandler
    object."""
    # Equivalence between 'as_run --actu' and current module
    _status_from_astk = {
        "OK" : SUCCESS,
        "NOOK" : INEXACT,
        "<A>" : ALARM,
        "<S>" : FAILURE, "<E>" : FAILURE, "<F>" : FAILURE,
        "RUN" : RUNNING,
        "PEND" : PENDING,
        "ENDED" : ENDED,
    }

    def __init__(self, astk_impl):
        JobImpl.__init__(self)
        self._astk_impl = astk_impl
        self._calcul = None

    def start(self, export_file):
        """Start the Aster solver by using 'as_run --serv'"""
        log.debug("AsRun1_10.start: enter")
        get_progress_file(reinit=True)
        export_file.check()
        self._calcul = self._astk_impl.build_calcul_handler(export_file)
        iret, output = self._calcul.start()
        log.debug("Output of submission (exit code %s)\n%s", iret, output)
        if iret != 0:
            mess = "Error occurs during submitting job"
            raise EnvironmentError(mess)

        self.pid = self._calcul.jobid
        log.info("Job submitted. JobID : %s, Queue : %s, StudyId : %s",
            self.pid, self._calcul.queue, self._calcul.studyid)

    def wait_result(self):
        """Wait the process to terminate by asking periodically the job
        status with 'as_run'"""
        log.debug("AsRun1_10.wait_result: enter")
        refresh_delay = self._astk_impl.refresh_delay
        self._calcul.wait(refresh_delay)
        log.debug("AsRun1_10.wait_result: end (%s)", self._calcul.diag)
        return self.res_status()

    def status(self):
        """Return the current job status."""
        return self._get_status(self._calcul.get_state()[0])

    def res_status(self):
        """Return the result status."""
        return self._get_status(self._calcul.get_diag()[0])

    def kill(self):
        """Kill the running case."""
        self._calcul.kill()

    def has_results(self):
        """Test if the job has valid results by using AsterRun.GetGrav"""
        status = self.res_status()
        aster_run = self._astk_impl.build_as_run()
        return (aster_run.GetGrav(status.from_astk) <= 4)


class Astk18(AstkImpl):
    """Implementation for ASTK 1.8
    """

    def __init__(self):
        self._as_run_inst = None
        self._client = None

    def build_as_run(self):
        """Create the AsterRun instance from the asrun package"""
        #import os
        #os.system("pause")
        from asrun.run import AsRunFactory
        if self._as_run_inst is None:
            run = AsRunFactory(rcdir=self.rcdir,
                               log_progress=get_progress_file(),
                               debug_stderr=(DEBUG >= 2))
            logf = "/tmp/salomemeca%s-%s.log" % (SALOME_MECA_VERSION, get_login())
            from asrun.core import magic
            magic.set_stderr(logf)
            log.debug("asrun debug log file is %s", logf)
            self._as_run_inst = run
        return self._as_run_inst

    def build_default_cfg(self):
        """Return the default configuration found for ASTK 1.8"""
        return _build_default_cfg(self)

    def _give_cmd(self, cmd_name):
        """Return the full path of the command name found in ASTER_ROOT/bin"""
        from asrun.installation import aster_root
        return [osp.join(aster_root, "bin/", cmd_name),]

    def give_as_run_cmd(self, export_file):
        """Return the 'as_run' command found in ASTER_ROOT/bin"""
        return self.build_as_run().get_as_run_cmd()

    def create_job_impl(self, impl_type):
        """Create the job implementation for ASTK 1.8"""
        return AsRunCmd(self)

    def create_aster_profil(self, fname=None, run=None):
        """Return asrun.profil.AsterProfil"""
        from asrun.profil import AsterProfil
        return AsterProfil(fname, run)

    def give_astk_cmd(self):
        """Return the 'astk' client command found in ASTER_ROOT/bin"""
        cmd = self._give_cmd("astk")
        cmd.append("--rcdir")  # not "=" sign for astk (tcl parser!)
        cmd.append(self.rcdir)
        return cmd

    def _give_as_client(self):
        """Build and return the ASTK client instance"""
        from asrun.client import ClientConfig
        if self._client is None:
            # make sure that asrun is initialized
            aster_run = self.build_as_run()
            self._client = ClientConfig(rcdir=aster_run.rcdir)
        return self._client

    def find_servers(self, force_refresh=False):
        """Find servers by using the client module"""
        client = self._give_as_client()
        log.debug("find_servers(force_refresh=%s)" % force_refresh)
        # force to read the configuration file because astk may change the parameters
        client.init_server_config(force=True, refresh=force_refresh)

        serv_names = client.get_server_list()
        servs = []
        for serv_name in serv_names:
            cfg = client.get_server_config(serv_name)
            if cfg["etat"] != "off":
                servs.append(cfg)
                #log.debug("Server '%s' : %s" % (serv_name, cfg))
        if force_refresh:
            client.save_server_config()
        return servs

    def get_server_config(self, server_name):
        """Return the configuration of ``server_name``."""
        client = self._give_as_client()
        dsrv = client.get_server_config(server_name, use_ip=True)
        dnew = client.with_export_keys(dsrv)
        return dnew

class Astk1_10(Astk18):
    """Implementation for ASTK 1.10 or newer."""

    def __init__(self):
        self._as_run_inst = None
        self._client = None

    def create_job_impl(self, impl_type):
        """Create the job implementation for ASTK 1.8"""
        return AsRun1_10(self)

    def build_calcul_handler(self, export_file):
        """Create the AsterCalcHandler instance from asrun"""
        from asrun.client import AsterCalcHandler
        prof = export_file.profil
        prof['studyid'] = "%s-%s" % (get_pid(), gethostname().split(".")[0])
        return AsterCalcHandler(prof)


use_astk(Astk1_10)


def run_astk(case=None, from_gui=None):
    """Run the ASTK client without argument or on the given aster.Case.
    from_gui allow to add the hostname and port of the Salomé platform
    from which ASTK is run"""
    cmd = give_astk_cmd()
    if case:
        try:
            acs = case.build_astk_case()
            exf = acs.build_export_file()
        #XXX add a particular exception when SMesh can be imported
        except NotImplementedError:
            log.error("Failure during exporting case")
        else:
            cmd.extend(["--import", exf.fname])
    if from_gui:
        assert type(from_gui) in (list, tuple) and len(from_gui) == 2, from_gui
        platform = "NameService=corbaname::%s:%s" % tuple(from_gui)
        cmd.extend(["--from_salome", platform])
    log.debug("run_astk: command = %s", " ".join(cmd))
    print "-------------- astk.py cmd -------------"
    print cmd
    print "-------------------------------------------------------"
    SP.Popen(cmd, shell=True)


def is_local(server):
    """Return if 'server' is the local server"""
    import salome_utils
    local_value = (
        None, "", "localhost",
        gethostname().split(".")[0], gethostname(),
        salome_utils.getHostFromORBcfg().split(".")[0], salome_utils.getHostFromORBcfg()
    )
    res = server in local_value or server.split(".")[0] in local_value
    log.debug("is_local: Is server=%s in %s ? %s", server, local_value, res)
    return res


def arch_from_platform(serv_platform):
    """Convert astk 'plate-forme' field (ex. LINUX64) to the value
    returned by platform.architecture() (32bit/64bit)."""
    arch = "32bit"
    if serv_platform.endswith("64"):
        arch = "64bit"
    return arch

def get_progress_file(reinit=False):
    """Return the file used to log the task progress."""
    dirname = osp.join(os.environ.get('HOME', '/tmp/'), ASTK_CONF_DIR)
    logprg = osp.join(dirname, "salomemeca.progress")
    if not osp.isdir(dirname):
        #peter.zhang, for cygwin
        dirname = dirname.replace('\\', '/')
        dirname = dirname.replace('/cygdrive/', '')
        if dirname.find(':/') < 0:
            dirname = dirname.replace('/', ':/', 1)
        os.makedirs(dirname)
    if reinit and osp.exists(logprg):
        _remove_file(logprg)
    log.debug("Progress logged into %s", logprg)
    return logprg

def _remove_file(path):
    """Remove a file without exceptions."""
    try:
        os.remove(path)
    except:
        pass

# slightly different in OMA
def choose_nearest_version(selvers, list_vers):
    """Return the nearest version of the prefered one.
    selvers : version currently selected in the case.
    list_vers : versions available on the server."""
    if selvers in list_vers:
        log.debug("version %s is available in %s", selvers, list_vers)
        return selvers
    if ASTER_REFVERSION in list_vers:
        list_vers.remove(ASTER_REFVERSION)
        list_vers.insert(0, ASTER_REFVERSION)
    # example search for STA9.8 :
    # - try to search "9.8", then "9"
    res = None
    for expr in (r"([A-Z]+[0-9]{1})", r"([0-9\.]+)", r"([0-9]+)"):
        mat = re.search(expr, selvers)
        if mat is not None:
            numvers = mat.group(1)
            lv = [vers for vers in list_vers if re.search(numvers, vers)]
            if len(lv) > 0:
                res = lv[0]
                break
    # - else return the first one!
    if res is None:
        res = list_vers[0]
    log.debug("search for version %s in %s : return %s", selvers, list_vers, res)
    return res

#list_vers = ['STA9.5', 'STA10.4', 'STA10.5', 'NEW11.0']
#assert choose_nearest_version('STA10', list_vers) == ASTER_REFVERSION
#assert choose_nearest_version('NEW9', list_vers) == 'STA9.5'
#assert choose_nearest_version('NEW11', list_vers) == 'NEW11.0'
#assert choose_nearest_version('STA10.4', list_vers) == 'STA10.4'
