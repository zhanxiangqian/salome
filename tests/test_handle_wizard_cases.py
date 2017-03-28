
import os
import os.path as osp
import unittest as UT

from aster_s.wizards import linear_static as LS
from aster_s.wizards import linear_thermic as LT
from aster_s.wizards import modal_analysis as MA

import salome_aster_tests as AT


LINEAR_STATIC = """\
DEBUT();

MA=DEFI_MATERIAU(ELAS=_F(E=1000,
                         NU=0.3,),);

MAIL=LIRE_MAILLAGE(FORMAT='MED',);

MAIL=MODI_MAILLAGE(reuse=MAIL,
                   MAILLAGE=MAIL,
                   ORIE_PEAU_2D=_F(GROUP_MA=('B', 'D'),),
                   );

MODE=AFFE_MODELE(MAILLAGE=MAIL,
                 AFFE=_F(TOUT='OUI',
                         PHENOMENE='MECANIQUE',
                         MODELISATION='C_PLAN',),);

MATE=AFFE_MATERIAU(MAILLAGE=MAIL,
                   AFFE=_F(TOUT='OUI',
                           MATER=MA,),);

CHAR=AFFE_CHAR_MECA(MODELE=MODE,
                    DDL_IMPO=(
                        _F(GROUP_MA='A',
                           DX=3,
                           DY=0,
                           DZ=1,),
                        _F(GROUP_NO='NA',
                           DX=2,
                           DY=1,
                           DZ=9,),
                        _F(GROUP_MA='B',
                           DX=5,
                           DY=2,
                           DZ=7,),
                        ),
                    PRES_REP=(
                        _F(GROUP_MA='B',
                           PRES=12,),
                        _F(GROUP_MA='D',
                           PRES=27,),
                        ),
                    );

RESU=MECA_STATIQUE(MODELE=MODE,
                   CHAM_MATER=MATE,
                   EXCIT=_F(CHARGE=CHAR,),);

RESU=CALC_ELEM(reuse=RESU,
               MODELE=MODE,
               CHAM_MATER=MATE,
               RESULTAT=RESU,
               OPTION=('SIGM_ELNO_DEPL','EQUI_ELNO_SIGM',),
               EXCIT=_F(
               CHARGE=CHAR,),);

RESU=CALC_NO(reuse=RESU,
             RESULTAT=RESU,
             OPTION=('SIGM_NOEU_DEPL', 'EQUI_NOEU_SIGM', ),);

IMPR_RESU(FORMAT='MED',
          UNITE=80,
          RESU=_F(MAILLAGE=MAIL,
                  RESULTAT=RESU,
                  NOM_CHAM=('SIGM_NOEU_DEPL','EQUI_NOEU_SIGM','DEPL',),),);

FIN();
"""

LINEAR_THERMIC = """\
DEBUT();

MESH=LIRE_MAILLAGE(UNITE=20,
                   FORMAT='MED',);

MATER=DEFI_MATERIAU(THER=_F(LAMBDA=0.9,),);

MODEL=AFFE_MODELE(MAILLAGE=MESH,
                  AFFE=_F(TOUT='OUI',
                          PHENOMENE='THERMIQUE',
                          MODELISATION='3D',),);

MATFIELD=AFFE_MATERIAU(MAILLAGE=MESH,
                       AFFE=_F(TOUT='OUI',
                               MATER=MATER,),);

LOADING=AFFE_CHAR_THER(MODELE=MODEL,
                       TEMP_IMPO=(
                           _F(GROUP_MA='AA',
                              TEMP=12,),
                           _F(GROUP_NO='BB',
                              TEMP=35,),
                           _F(GROUP_MA='CC',
                              TEMP=8,),
                           ),
                       FLUX_REP=(
                           _F(GROUP_MA='AA',
                              FLUN=47,),
                           ),
                       SOURCE=(
                           _F(GROUP_MA='DD',
                              SOUR=27,),
                           _F(GROUP_MA='BB',
                              SOUR=23,),
                           ),
                       );

TEMP=THER_LINEAIRE(MODELE=MODEL,
                   CHAM_MATER=MATFIELD,
                   EXCIT=_F(CHARGE=LOADING,),);

IMPR_RESU(FORMAT='MED',
          RESU=_F(RESULTAT=TEMP,),);

FIN();
"""

MODAL_ANALYSIS = """\
DEBUT();

MAIL=LIRE_MAILLAGE(UNITE=20,
                   FORMAT='MED',);

MODELE=AFFE_MODELE(MAILLAGE=MAIL,
                   AFFE=_F(TOUT='OUI',
                           PHENOMENE='MECANIQUE',
                           MODELISATION='AXIS',),);

MAT=DEFI_MATERIAU(ELAS=_F(E=6000,
                          NU=0.35,
                          RHO=0.975,),);

CHMAT=AFFE_MATERIAU(MAILLAGE=MAIL,
                    AFFE=_F(TOUT='OUI',
                            MATER=MAT,),);

BLOCAGE=AFFE_CHAR_MECA(MODELE=MODELE,
                       DDL_IMPO=(
                           _F(GROUP_NO='NA',
                              DX=2,
                              DY=10,
                              DZ=0,),
                           _F(GROUP_NO='NZ',
                              DX=0,
                              DY=0,
                              DZ=0,),
                           _F(GROUP_MA='ME',
                              DX=4,
                              DY=3,
                              DZ=7,),
                           ),
                       );

MACRO_MATR_ASSE(MODELE=MODELE,
                CHAM_MATER=CHMAT,
                CHARGE=BLOCAGE,
                NUME_DDL=CO('NUMEDDL'),
                MATR_ASSE=(_F(MATRICE=CO('RIGIDITE'),
                              OPTION='RIGI_MECA',),
                           _F(MATRICE=CO('MASSE'),
                              OPTION='MASS_MECA',),
                           ),
                );

MODES=MODE_ITER_SIMULT(MATR_A=RIGIDITE,
                       MATR_B=MASSE,
                       CALC_FREQ=_F(OPTION='PLUS_PETITE',
                                    NMAX_FREQ=15,),
                       );

IMPR_RESU(MODELE=MODELE,
          FORMAT='MED',
          RESU=_F(MAILLAGE=MAIL,
                  RESULTAT=MODES,
                  NOM_CHAM='DEPL',),);

FIN();
"""


class TestHaveWizardCases(UT.TestCase):

    def setUp(self):
        self.tmp_dir = AT.TmpDir("wizard_cases")

    def tearDown(self):
        self.tmp_dir.clean()

    def check_content(self, fname, res):
        self.assert_(osp.isfile(fname))
        fid = open(fname)
        content = fid.read()
        try:
            self.assertEqual(content, res)
        except AssertionError:
            lines = [cont.split(os.linesep) for cont in (content, res)]
            for line, rline in zip(lines[0], lines[1]):
                if line != rline:
                    diff = ["", "> %s" % line, "< %s" % rline, ""]
                    raise AssertionError(os.linesep.join(diff))
            else:
                raise
        fid.close()

    def test_build_linear_static_case(self):
        comm = LS.CommWriter()
        comm.use(LS.YoungModulus(10**3))
        comm.use(LS.PoissonRatio(0.3))
        comm.use(LS.Modelisation(LS.PlaneStress))

        mech_consts = comm.use(LS.MechConstraints())
        bound_conds = mech_consts.add(LS.BoundConds())
        bound_conds.add(LS.DplFromName(LS.GRP_MA, "A", 3, 0, 1))
        bound_conds.add(LS.DplFromName(LS.GRP_NO, "NA", 2, 1, 9))
        bound_conds.add(LS.DplFromName(LS.GRP_MA, "B", 5, 2, 7))
        pressure = mech_consts.add(LS.Pressure())
        pressure.add(LS.GrpPres("B", 12))
        pressure.add(LS.GrpPres("D", 27))

        fname = osp.join(self.tmp_dir.add("linear_static"), "fname.comm")
        comm.write(fname)
        self.check_content(fname, LINEAR_STATIC)

    def test_build_linear_thermic_case(self):
        comm = LT.CommWriter()
        comm.use(LT.Modelisation(LT.Mode3D))
        comm.use(LT.ThermalConductance(0.9))

        th_consts = comm.use(LT.ThermalConstraints())
        temp_conds = th_consts.add(LT.TempConds())
        temps_impo = (
            (LT.GRP_MA, "AA", 12),
            (LT.GRP_NO, "BB", 35),
            (LT.GRP_MA, "CC", 8)
        )
        for grp, name, val in temps_impo:
            temp_conds.add(LT.TempImpo(grp, name, val))
        nstreams = th_consts.add(LT.NormalStreams())
        nstreams.add(LT.NormalStream("AA", 47))
        srcs = th_consts.add(LT.VolSources())
        srcs.add(LT.VolSource('DD', 27))
        srcs.add(LT.VolSource('BB', 23))

        fname = osp.join(self.tmp_dir.add("linear_thermic"), "fname.comm")
        comm.write(fname)
        self.check_content(fname, LINEAR_THERMIC)

    def test_build_modal_analysis_case(self):
        comm = MA.CommWriter()
        comm.use(MA.Modelisation(MA.AxisSymmetric))
        comm.use(MA.YoungModulus(6000))
        comm.use(MA.PoissonRatio(0.35))
        comm.use(MA.Density(0.975))
        bound_consts = comm.use(MA. BoundConstraints())
        bound_consts.add(MA.DplFromName(LS.GRP_NO, "NA", 2, 10, 0))
        bound_consts.add(MA.DplFromName(LS.GRP_NO, "NZ", 0, 0, 0))
        bound_consts.add(MA.DplFromName(LS.GRP_MA, "ME", 4, 3, 7))
        comm.use(MA.FreqMaxNb(15))

        fname = osp.join(self.tmp_dir.add("modal_analysis"), "fname.comm")
        comm.write(fname)
        self.check_content(fname, MODAL_ANALYSIS)


if __name__ == "__main__":
    UT.main()

