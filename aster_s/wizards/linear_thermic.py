"""Wizard for creating an Aster study case on linear thermic
"""

import aster_s.wizards.common as WC
from aster_s.wizards.common import (
    Modelisation,
    Mode3D,
    Plane,
    GRP_MA,
    GRP_NO,
    )


class ThermalConductance(WC.PatternValue):
    """Thermal conductance coefficient, called lambda
    """

    def __init__(self, value):
        WC.PatternValue.__init__(self, "lambda_key", value)


class TempImpo(WC.ArgsConstraint):
    """A temperature for a group
    """

    def __init__(self, grp_type, name, value):
        WC.ArgsConstraint.__init__(self, [
            WC.Arg(grp_type, WC.quote(name)),
            WC.Arg("TEMP", value),
        ])


class TempConds(WC.ConstraintSection):
    """Temperature conditions
    """

    def add_to(self, th_consts, writer):
        """Add temperature conditions to command file"""
        self.write_section("TEMP_IMPO", th_consts, writer)


class NormalStream(WC.ArgsConstraint):
    """Stream normal to a face
    """

    def __init__(self, name, value):
        WC.ArgsConstraint.__init__(self, [
            WC.Arg("GROUP_MA", WC.quote(name)),
            WC.Arg("FLUN", value),
        ])


class NormalStreams(WC.ConstraintSection):
    """Streams normal to a face
    """

    def add_to(self, th_consts, writer):
        """Add normal streams to command file"""
        self.write_section("FLUX_REP", th_consts, writer)


class VolSource(WC.ArgsConstraint):
    """Volumic source
    """

    def __init__(self, name, value):
        WC.ArgsConstraint.__init__(self, [
            WC.Arg("GROUP_MA", WC.quote(name)),
            WC.Arg("SOUR", value),
        ])


class VolSources(WC.ConstraintSection):
    """Volumic sources
    """

    def add_to(self, th_consts, writer):
        """Add volumic sources to command file"""
        self.write_section("SOURCE", th_consts, writer)


class ThermalConstraints(WC.Constraints):
    """Thermal constraints for the command file
    """
    pattern_key = "thermal_constraints_key"

    def add_to(self, writer):
        """Add thermal constraints to the command file"""
        self.write_cmd("LOADING=AFFE_CHAR_THER(", "MODELE=MODEL,", writer)


class CommWriter(WC.CommWriter):
    """The Aster study case on linear thermic
    """
    _pattern = WC.load_pattern("linear_thermic_pattern.comm")



