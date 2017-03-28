# -*- coding: utf-8 -*-
"""Build studies on the Salomé server and keep track of created objects.
"""
# surtout pour les tests
import sys
from cStringIO import StringIO

from aster_s.utils import Singleton, log
from aster_s.salome_tree import create_salome_study, SalomeStudy
from aster_s.study import Study


class StudyBuilder(Singleton):
    """The communication with the Salomé server.

    Initialize the corba connection to the server on start.  The same life
    cycle corba (salome.lcc) used by Salomé is then used for every study.

    Can create a Aster study in two manners:

        - create a new Salomé study attached to a new Aster study
        - attach an existing Salomé study to a new Aster study

    This class is a singleton.
    """
    orb_init_ref = "NameService=corbaname::localhost:2810"
    quiet = True

    def init(self):
        from omniORB import CORBA
        import salome
        """Initialize the singleton instance"""
        argv = None
        if "-ORBInitRef" not in sys.argv:
            argv = list(sys.argv) + ["-ORBInitRef", self.orb_init_ref]
        StudyBuilder._cnx = CORBA.ORB_init(argv, CORBA.ORB_ID)
        if self.quiet:
            stdout = sys.stdout
            sys.stdout = StringIO()
        salome.salome_init()
        if self.quiet:
            sys.stdout = stdout
        #salome.myStudy.Close()
        self._stds = []
        self._astds = []

    def create_salome_study(self, name, register=False):
        """Factory for creating a salome study.
        In case 'register' is True, the builder will close it
        on 'close_all()' (convenient for testing)."""
        sstd = create_salome_study(name, bld=self)
        if register:
            self._stds.append(sstd)
        return sstd

    def remove_salome_study(self, sstd):
        """Remove a Salome study from the registration list if found."""
        if sstd in self._stds:
            self._stds.remove(sstd)

    def create(self, name):
        """Create a new Aster study attached to a new Salomé study"""
        sstd = self.create_salome_study(name, register=True)
        astd = Study(sstd, bld=self, own_std=True)
        self._astds.append(astd)
        return astd

    def attach_to(self, salome_std):
        """Create a new Aster study attached to the given SalomeStudy"""
        astd = Study(salome_std, bld=self)
        self._astds.append(astd)
        return astd

    def attach_to_study_id(self, salome_std_idx):
        """Attach to a Salomé study from its index"""
        from salome import myStudyManager as mng
        std = mng.GetStudyByID(salome_std_idx)
        log.debug("ASTER: study %s (%s)", std, type(std))
        sstd = SalomeStudy(std)
        log.debug("ASTER: SalomeStudy %s (%s)", sstd, type(sstd))
        return self.attach_to(sstd)
        #return self.attach_to(SalomeStudy(mng.GetStudyByID(salome_std_idx)))

    def remove(self, astd):
        """Remove an Aster study from the creation list"""
        self._astds.remove(astd)

    def close_all(self):
        """Close all created Aster studies on the server side"""
        for astd in self._astds[:]:
            astd.close()
        for std in self._stds[:]:
            std.close_salome_study()


def load_case_from_studyId_and_entry(salome_std_Id, entry):
    """Return a study Case from its entry and a Salome study id"""
    bld = StudyBuilder()
    astd = bld.attach_to_study_id(salome_std_Id)
    case = astd.load_elt_from_entry(entry)
    return case

