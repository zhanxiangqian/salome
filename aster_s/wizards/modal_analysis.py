"""Wizard for creating an Aster study case on modal analysis
"""

import aster_s.wizards.common as WC
from aster_s.wizards.common import (
    Modelisation,
    GRP_MA,
    GRP_NO,
    Mode3D,
    PlaneStress,
    PlaneStrain,
    AxisSymmetric,
    YoungModulus,
    PoissonRatio,
    Density,
    DplFromName,
    )


class DplSection(WC.ConstraintSection):
    """Displacement constraints
    """

    def add_to(self, consts, writer):
        """Write the displacement section"""
        self.write_section("DDL_IMPO", consts, writer)


class BoundConstraints(WC.Constraints):
    """The part on boundary constraints
    """
    pattern_key = "bound_constraints_key"

    def __init__(self):
        WC.Constraints.__init__(self)
        self.dpl_impo = WC.Constraints.add(self, DplSection())
        self.has_const = False

    def add(self, const):
        """Add a constraint to the section"""
        self.has_const = True
        return self.dpl_impo.add(const)

    def add_to(self, writer):
        loading = ""
        if self.has_const:
            self.write_cmd("BLOCAGE=AFFE_CHAR_MECA(", "MODELE=MODELE,", writer) 
            loading = "CHARGE=BLOCAGE,"
        else:
            self.write_cmd("","", writer)
        writer.subs("loading_key", loading)


class FreqMaxNb(WC.PatternValue):
    """Maximum number of frequencies
    """

    def __init__(self, max_nb):
        WC.PatternValue.__init__(self, "freq_max_nb_key", max_nb)


class ModeDEF(WC.Constraints):
    """CALC_MODES
    """

    def __init__(self, option, modeList ):
        WC.Constraints.__init__(self)
        self._option = option
        self._modeList = modeList
        self.lines = None

    def add_to(self, writer):
        """Add the mechanical constraints"""
        lines = WC.Lines()
        self.lines = lines
        lines.add("MODES=CALC_MODES(MATR_RIGI=RIGIDITE,")
        nbl = len("MODES=CALC_MODES(")
        lines.init_idt = " "*nbl
        lines.add("MATR_MASS=MASSE,")

        lines.add("OPTION='"+self._option+"',")

        lines.init_idt = " "*nbl
        lines.add("CALC_FREQ=_F(")
        lines.init_idt = " "*(nbl+len("CALC_FREQ=_F("))

        if  self._option == "PLUS_PETITE":
            lines.add("NMAX_FREQ="+str(self._modeList[0])+",)")
        elif  self._option == "BANDE":
            lines.add("FREQ=("+str(self._modeList[0])+","+str(self._modeList[1])+"),)")
        else : # case "CENTRE"
            lines.add("FREQ="+str(self._modeList[0])+",")
            lines.add("NMAX_FREQ="+str(self._modeList[1])+",)")
        lines.init_idt = " "*nbl
        lines.add(");")


        writer.subs("calc_modes", lines.build_part())

class Cara(WC.Constraints):
    """Add Elementary Characteristics on boundary constraints
    """

    def __init__(self, dataCara):
        WC.Constraints.__init__(self)
        self._dataCara = dataCara
        self.lines = None

    def add_to(self, writer):
        lines = WC.Lines()
        self.lines = lines
        if str(self._dataCara[0]) in ["DKT", "DST", "COQUE_3D", "POU_D_E", "POU_D_T"]:
            lines.add("CARA_ELEM=CAREL,")

        writer.subs("Cara_Key", lines.build_part())

class CaraELEM(WC.Constraints):
    """Elementary Characteristics
    """

    def __init__(self, dataCara):
        WC.Constraints.__init__(self)
        self._dataCara = dataCara
        self.lines = None

    def add_to(self, writer):
        lines = WC.Lines()
        self.lines = lines
        if str(self._dataCara[0]) in ["DKT", "DST", "COQUE_3D"]:
            lines.add("CAREL=AFFE_CARA_ELEM(MODELE=MODELE,")
            lines.init_idt = " "*len("CAREL=AFFE_CARA_ELEM(")
            lines.add("COQUE=_F(GROUP_MA = 'TOUT',")
            lines.init_idt = " "*len("CAREL=AFFE_CARA_ELEM(COQUE=_F(")
            lines.add("EPAIS = "+str(self._dataCara[1])+ "),")
            lines.init_idt = " "*len("CAREL=AFFE_CARA_ELEM(")
            lines.add(");")
        elif str(self._dataCara[0]) in ["POU_D_E", "POU_D_T"]:
            lines.add("CAREL=AFFE_CARA_ELEM(MODELE=MODELE,")
            lines.init_idt = " "*len("CAREL=AFFE_CARA_ELEM(")
            lines.add("POUTRE=_F(GROUP_MA = 'TOUT',")
            lines.init_idt = " "*len("CAREL=AFFE_CARA_ELEM(POUTRE=_F(")
            # lines.init_idt = " "*len("POUTRE = _F(")

            if str(self._dataCara[1]) == 'Pleine':
                if str(self._dataCara[2]) == 'RECTANGLE':
                    lines.add("SECTION = 'RECTANGLE',")
                    lines.add("CARA = ('HY', 'HZ',),")
                    lines.add("VALE = ("+str(self._dataCara[3])+","+str(self._dataCara[4])+"),)")
                elif str(self._dataCara[2]) == 'CARRE':
                    lines.add("SECTION = 'RECTANGLE',")
                    lines.add("CARA = 'H',")
                    lines.add("VALE = "+str(self._dataCara[3])+",)")
                else :
                    lines.add("SECTION = 'CERCLE',")
                    lines.add("CARA = 'R',")
                    lines.add("VALE = "+str(self._dataCara[3])+",)")
            else :
                if str(self._dataCara[2]) == 'RECTANGLE':
                    lines.add("SECTION = 'RECTANGLE',")
                    lines.add("CARA = ( 'HY', 'HZ', 'EPY', 'EPZ',),")
                    lines.add("VALE = ("+str(self._dataCara[3])+","+str(self._dataCara[4])+","+str(self._dataCara[5])+","+str(self._dataCara[6])+"),)")
                elif str(self._dataCara[2]) == 'CARRE':
                    lines.add("SECTION = 'RECTANGLE',")
                    lines.add("CARA = ('H', 'EP',),")
                    lines.add("VALE = ("+str(self._dataCara[3])+","+str(self._dataCara[4])+"),)")
                else :
                    lines.add("SECTION = 'CERCLE',")
                    lines.add("CARA = ('R', 'EP',),")
                    lines.add("VALE = ("+str(self._dataCara[3])+","+str(self._dataCara[4])+"),)")
            lines.init_idt = " "*len("CAREL=AFFE_CARA_ELEM(")
            lines.add(");")

        else :
             lines.add("")

        writer.subs("Cara_Elem", lines.build_part())

class DplFromCheckBox(WC.ArgsConstraint):
    """Displacement boundary condition
    """
    _keys = ("DX", "DY", "DZ", "DRX", "DRY", "DRZ")

    def __init__(self, grp_type, name, dplx=False, dply=False, dplz=False, dplrx=False, dplry=False, dplrz=False):
        args = [WC.Arg(grp_type, WC.quote(name))]
        for key, dpl in zip(self._keys, (dplx, dply, dplz, dplrx, dplry, dplrz)):
            if dpl is not False:
                args.append(WC.Arg(key, 0.))
        WC.ArgsConstraint.__init__(self, args)

class CommWriter(WC.CommWriter):
    """The Aster study case on modal analysis
    """
    _pattern = WC.load_pattern("modal_analysis_pattern.comm")


