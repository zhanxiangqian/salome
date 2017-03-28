# -*- coding: utf-8 -*-
"""Import objects defining the aster module.

The 'StudyBuilder' allows to build studies on the Salomé server.
The 'Study' allows to add Aster study cases.
The Aster solver status are provided.
"""
SALOME_MECA_VERSION = "2012.2"
# reference version - may be used as default one (for example, when calling eficas)
ASTER_REFVERSION = "stable"

# Register all the factories building Aster components for Salomé
import aster_s.factories
aster_s.factories.register_all()

# Aster components for building a study case
from aster_s.components import (
    CommFile,
    CommEntry,
    MedEntry,
    MedFile,
    SMeshEntry,
    WorkingDir,
    RemoveRmed,
    HasBaseResult,
    InteractivFollowUp,
    ExportFile,
    AstkProfil,
    ExportFname,
    JobId,
    MessFile,
    ResuFile,
    RMedFile,
    BaseResult,
    DataSection,
    AstkParams,
    ResultsSection,
    Case,
    FromComm,
    FromExport,
    FromProfil,
    Value,
    )

# Allow to build studies on Salomé server (need salome)
from aster_s.study_builder import (
    StudyBuilder,
    load_case_from_studyId_and_entry,
    )

# Allow to manipulate the Salomé study (need salome)
from aster_s.salome_tree import SalomeStudy

# Add Aster study cases to Salomé studies (need salome)
from aster_s.study import (
    Study,
    attach_study_to,
    )

# Run the Aster solver (need astk)
import aster_s.astk
from aster_s.astk import (
    use_astk,
    use_job_impl,
    build_default_cfg,
    build_aster_profil,
    build_as_run,
    AS_RUN_CMD,
    SUCCESS,
    ALARM,
    INEXACT,
    FAILURE,
    RUNNING,
    PENDING,
    ENDED,
    UNKNOWN,
    run_astk,
    run_stanley,
    )

from aster_s.utils import (
    Singleton,
    get_login,
    Resources,
    get_resource,
    )
