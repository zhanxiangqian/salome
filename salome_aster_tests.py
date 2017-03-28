"""Used for finding the input data delivered with tests and 
removing temporary directories.
"""
import os
import os.path as osp
import tempfile
import shutil

from aster_s import Singleton, get_login, Resources


class PalStudyBuilder(Singleton):
    """Build a SalomeStudy from the module PAL, called PalStudy.
    This study is attached to a SalomeStudy from the aster module.
    """

    def init(self):
        """Import the studyManager (the package should be used without it)"""
        from studyManager import SalomeStudy as PalStudy
        from studyManager import logger
        # By default, do not activate debug
        logger.hideDebug()
        self.cls = PalStudy

    def attach_to(self, salome_study):
        """Create a PalStudy attached to a salome study"""
        return self.cls(salome_study.sstd._get_StudyId())


class TestDirs(Singleton):
    """Give directory paths for testing
    """

    def init(self):
        """Initialize singleton instance"""
        self._root_tmp = None

    def get_rtmp(self, *args):
        """Return a temporary directory for storing test results"""
        if self._root_tmp is None:
            rname = "salome-aster-tests-%s" % get_login()
            rep = osp.join(tempfile.gettempdir(), rname)
            if not osp.exists(rep):
                os.mkdir(rep)
            self._root_tmp = rep
        rep = osp.join(self._root_tmp, *args)
        if not osp.exists(rep):
            os.makedirs(rep)
        return rep


def get_data(*args):
    """Return the absolute path of an element stored in the data directory"""
    return Resources().get_path("aster", "data", *args)

def get_rtmp_dir(*args):
    """Return a temporary directory for storing test results used by
    Salome. This directory is always the same because data are supposed
    to be overwritten at each run. """
    return TestDirs().get_rtmp(*args)

def copy_data(target_dir, *args):
    """Copy the given test data to the target directory"""
    data = get_data(*args)
    if osp.isfile(data):
        shutil.copy(data, target_dir)
        return osp.join(target_dir, osp.basename(data))
    elif osp.isdir(data):
        rep = osp.join(target_dir, osp.basename(data))
        if osp.exists(rep):
            shutil.rmtree(rep)
        shutil.copytree(data, rep)
        return rep
    else:
        raise NotImplementedError

def write_comm(rep, lines, fname="astest.comm"):
    """Write the lines for a command file in the directory rep"""
    comm = osp.join(rep, fname)
    fid = open(comm, "w")
    fid.write(os.linesep.join(lines))
    fid.close()
    return comm

def write_clt_comm(rep, lines, srv):
    """Write a client command file"""
    return write_comm(rep, [
        "DEBUT()",
        "from sys import path",
        "path.append('%s')" % osp.dirname(__file__),
        "from aster_tests import Cnt",
        "cnt = Cnt(%i)" % srv.port,
        ] +  lines + [
        "cnt.close()",
        "FIN()",
    ])


class TmpDir(object):
    """Create a global temporary directory and add children directories.
    """

    def __init__(self, suffix):
        self._root = tempfile.mkdtemp(suffix)

    def add(self, name):
        """Add a children directory with the given name"""
        rep = osp.join(self._root, name)
        os.mkdir(rep)
        return rep

    def clean(self):
        """Clean the temporary directory and all its children"""
        shutil.rmtree(self._root)


