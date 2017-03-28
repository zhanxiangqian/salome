# -*- coding: utf-8 -*-
"""Functions for parametric cases.
"""

import os.path as osp
import re

import aster_s
import aster_s.astk as astk
from aster_s.utils import log

# OUTPUT_VALUES are searched on a single line...
regexp_outvalues = re.compile("^ *(OUTPUT_VALUES *= *.*)", re.MULTILINE)

def get_values_from_mess(mess_fname, varlist):
    """Return a list of the values calculated by the aster case."""
    if not osp.isfile(mess_fname):
        return []
    content = open(mess_fname, "r").read()
    mat = regexp_outvalues.search(content)
    assert mat is not None, "OUTPUT_VALUES not found in the '.mess' file."
    dc = {}
    exec mat.group(1) in dc
    values = dc["OUTPUT_VALUES"]
    if type(values) in (list, tuple):
        assert len(values) == len(varlist), \
            "Size mismatch between outputVarList and OUTPUT_VALUES."
        values = dict(zip(varlist, values))
    elif type(values) is dict:
        miss = set(varlist) - set(values.keys())
        assert len(miss) == 0, "Results %s are missing in OUTPUT_VALUES." \
            % ', '.join([repr(k) for k in miss])
    assert type(values) is dict, "Only dict and list are supported in OUTPUT_VALUES."
    msg = "OUTPUT_VALUES: invalid type for '%s': %s"
    for key, val in values.items():
        assert type(val) in (int, long, float), msg % (key, val)
    return values


def add_result_to_profil(profil, newdir='.', mode='batch'):
    """Build a new AsterProfil object from the deterministic one."""
    # build resudir value
    resudir = None
    lmess = profil.Get("R", "mess")
    if len(lmess) > 0:
        resudir = osp.dirname(lmess[0]["path"])
    assert resudir, "resudir not defined"
    resudir = osp.join(resudir, "param_results")
    # set repe=resudir if repe is not defined
    if len(profil.Get("R", "repe")) == 0:
        profil.Set("R", {
            "type" : "repe",
            "isrep" : True,
            "path" : resudir,
            "ul" : 0,
            "compr" : False,
        })
    # try to run in batch mode if it is supported
    profil.set_running_mode(mode)
    relocated = profil.copy()
    if mode == 'batch':
        relocated.relocate(serv=None, newdir=newdir)
        resudir = osp.join(newdir, osp.basename(resudir))
    return resudir, profil, relocated

def _get_profil_from_case(case):
    """Retreive the AsterProfil object from `case`."""
    case.remove(astk.InteractivFollowUp)
    export_file = case.get_export_file()
    return export_file.profil

def create_probabilistic_profil(case):
    """Create the AsterProfil object from the deterministic case."""
    in_profil = _get_profil_from_case(case)
    return add_result_to_profil(in_profil)

def create_new_profil(profil, resudir, values, caseId=None):
    """Create a new AsterProfil using the values."""
    from asrun.calcul import AsterCalcParametric
    run = aster_s.build_as_run()
    pid = caseId or run.get_pid()
    label = "calc_" + pid
    # Openturns is either running in interactive mode and Aster does the same,
    # or Openturns is running in batch and Aster must switch to the interactive
    # mode under the Openturns job.
    profil['mode'] = 'interactif'
    calc = AsterCalcParametric(run, label, prof=profil, pid=pid,
                               values=values, keywords={}, resudir=resudir)
    return calc.prof

def build_probabilistic_case(case, values, caseId=None, newdir=None, mode='batch'):
    """Build a new astk.Case using the dict of values provided."""
    if mode != 'batch':
        mode = 'interactif'
    in_profil = _get_profil_from_case(case)
    resudir, profil, relocated = add_result_to_profil(in_profil, newdir, mode)
    prof = create_new_profil(relocated, resudir, values, caseId)
    log.debug("New profile content :\n%s", prof)

    jobname = prof.get_jobname()
    new_acs = astk.FromProfil(jobname)
    new_acs.use_profil(prof)
    new_acs.use_fname(prof.get_filename())
    return new_acs


