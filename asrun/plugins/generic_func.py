# coding: utf-8

# ==============================================================================
# COPYRIGHT (C) 1991 - 2015  EDF R&D                  WWW.CODE-ASTER.ORG
# THIS PROGRAM IS FREE SOFTWARE; YOU CAN REDISTRIBUTE IT AND/OR MODIFY
# IT UNDER THE TERMS OF THE GNU GENERAL PUBLIC LICENSE AS PUBLISHED BY
# THE FREE SOFTWARE FOUNDATION; EITHER VERSION 2 OF THE LICENSE, OR
# (AT YOUR OPTION) ANY LATER VERSION.
#
# THIS PROGRAM IS DISTRIBUTED IN THE HOPE THAT IT WILL BE USEFUL, BUT
# WITHOUT ANY WARRANTY; WITHOUT EVEN THE IMPLIED WARRANTY OF
# MERCHANTABILITY OR FITNESS FOR A PARTICULAR PURPOSE. SEE THE GNU
# GENERAL PUBLIC LICENSE FOR MORE DETAILS.
#
# YOU SHOULD HAVE RECEIVED A COPY OF THE GNU GENERAL PUBLIC LICENSE
# ALONG WITH THIS PROGRAM; IF NOT, WRITE TO EDF R&D CODE_ASTER,
#    1 AVENUE DU GENERAL DE GAULLE, 92141 CLAMART CEDEX, FRANCE.
# ==============================================================================

"""
This module provides generic functions to write plugins.
"""

from math import ceil
from asrun.core import magic


def iceil(x):
    """Return the ceiling of x as int"""
    return int(ceil(x))

def getCpuParameters(physical_proc, core_per_proc, prof):
    """Adjust the number of processors, nodes to optimize the
    utilization of resources and performances.
    Returns: the optimal number of cpu_mpi, node_mpi and number of threads
    :physical_proc: number of physical processors per node
    :core_per_proc: number of cores on each processor
    """
    try:
        cpu_openmp = int(prof['ncpus'][0] or 1)
    except ValueError:
        cpu_openmp = 1
    cpu_openmp = max(cpu_openmp, 1)
    try:
        cpu_mpi = int(prof['mpi_nbcpu'][0] or 1)
    except ValueError:
        cpu_mpi = 1
    cpu_mpi = max(cpu_mpi, 1)
    node_mpi = 999999
    try:
        node_mpi = int(prof['mpi_nbnoeud'][0]) or node_mpi
    except ValueError:
        pass
    return adjust_cpu_parameters(physical_proc, core_per_proc,
                                 cpu_mpi, node_mpi, cpu_openmp)


def adjust_cpu_parameters(physical_proc, core_per_proc,
                          cpu_mpi, node_mpi, cpu_openmp):
    """Adjust the number of processors, nodes to optimize the
    utilization of resources and performances.
    Returns: the optimal number of cpu_mpi, node_mpi and number of threads"""
    magic.run.DBG(">>> Requested ({0} cpu_mpi/{1} node /{2} openmp)".format(cpu_mpi, node_mpi, cpu_openmp))

    cpu_per_node = iceil(1. * cpu_mpi / node_mpi)
    # use at least physical_proc procs per node
    if cpu_per_node < physical_proc:
        cpu_per_node = physical_proc
    # do not allocate more nodes than necessary
    if node_mpi > 1. * cpu_mpi / cpu_per_node:
        node_mpi = iceil(1. * cpu_mpi / cpu_per_node)
    # because the nodes are exclusive, use all the processors (if cpu_mpi > 1)
    if cpu_mpi > 1 and cpu_mpi < node_mpi * physical_proc:
        cpu_mpi = node_mpi * physical_proc
    # recommandations
    if cpu_per_node > physical_proc:
        magic.run.Mess("Warning: more MPI processors per node ({0}) than "
            "physical processors ({1}).".format(cpu_per_node, physical_proc),
            "<I>_ALARM")
    # threads
    thread_per_cpu = physical_proc * core_per_proc / cpu_per_node
    blas_thread = max(thread_per_cpu / cpu_openmp, 1)
    if cpu_openmp * blas_thread * cpu_per_node > physical_proc * core_per_proc:
        magic.run.Mess("Warning: more threads ({0}) than cores ({1})."\
            .format(cpu_openmp * blas_thread * cpu_per_node,
                    physical_proc * core_per_proc),
            "<I>_ALARM")
    magic.run.DBG("returns: {0} cpu_mpi/{1} node/{2} cpu_per_node/{3} openmp"
        " /{4} blas".format(cpu_mpi, node_mpi, cpu_per_node,
                             cpu_openmp, blas_thread))
    return cpu_mpi, node_mpi, cpu_openmp, blas_thread


# unittest
if __name__ == '__main__':
    from asrun.run import AsRunFactory
    magic.run = AsRunFactory(debug=False)
    from functools import partial
    adjust = partial(adjust_cpu_parameters, 2, 12)

    res = adjust(1, 5, 1)  # seq
    assert res == (1, 1, 1, 12), res
    res = adjust(8, 999999, 1)
    assert res == (8, 4, 1, 12), res
    res = adjust(12, 3, 1)
    assert res == (12, 3, 1, 6), res
    res = adjust(13, 8, 1)
    assert res == (14, 7, 1, 12), res
    res = adjust(11, 11, 1)
    assert res == (12, 6, 1, 12), res
    res = adjust(9, 2, 4)
    assert res == (9, 2, 4, 1), res
    res = adjust(9, 2, 1)
    assert res == (9, 2, 1, 4), res
    res = adjust(17, 3, 2)
    assert res == (17, 3, 2, 2), res
    res = adjust(8, 2, 1)
    assert res == (8, 2, 1, 6), res
    res = adjust(8, 2, 2)
    assert res == (8, 2, 2, 3), res
    res = adjust(8, 2, 4)
    assert res == (8, 2, 4, 1), res
    res = adjust(8, 2, 6)
    assert res == (8, 2, 6, 1), res
    res = adjust(8, 2, 12)
    assert res == (8, 2, 12, 1), res
