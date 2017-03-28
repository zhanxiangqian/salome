"""Wizard for creating an Aster study case on linear static
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
    DplFromName,
    )


class BoundConds(WC.ConstraintSection):
    """Boundary conditions for mechanical constraints
    """

    def add_to(self, mech_consts, writer):
        """Add to mechanical constraints"""
        self.write_section("DDL_IMPO", mech_consts, writer)

class ForceFaceArgs(WC.ArgsConstraint):
    """A group of pressure on elements
    """
    
    def __init__(self, name, vx,vy,vz):
        WC.ArgsConstraint.__init__(self, [
            WC.Arg("GROUP_MA", WC.quote(name)),
            WC.Arg("FX", vx),
            WC.Arg("FY", vy),
            WC.Arg("FZ", vz),
        ])
        self.name = name

    def add_to(self, pressures, writer):
        """Add to mechanical constraints"""
        WC.ArgsConstraint.add_to(self, pressures, writer)
        pressures.add_to_mesh_change(self.name)

class ForceNodaleArgs(WC.ArgsConstraint):
    """A group of pressure on elements
    """
    
    def __init__(self, name, vfx,vfy,vfz,vmx,vmy,vmz,dim):
        if dim == 3:
            WC.ArgsConstraint.__init__(self, [
                WC.Arg("GROUP_NO", WC.quote(name)),
                WC.Arg("FX", vfx),
                WC.Arg("FY", vfy),
                WC.Arg("FZ", vfz),
                WC.Arg("MX", vmx),
                WC.Arg("MY", vmy),
                WC.Arg("MZ", vmz),
            ])
        else:
            WC.ArgsConstraint.__init__(self, [
                WC.Arg("GROUP_NO", WC.quote(name)),
                WC.Arg("FX", vfx),
                WC.Arg("FY", vfy),
            ])
        self.name = name

    def add_to(self, pressures, writer):
        """Add to mechanical constraints"""
        WC.ArgsConstraint.add_to(self, pressures, writer)
        pressures.add_to_mesh_change(self.name)

class GrpPres(WC.ArgsConstraint):
    """A group of pressure on elements
    """
    
    def __init__(self, name, value):
        WC.ArgsConstraint.__init__(self, [
            WC.Arg("GROUP_MA", WC.quote(name)),
            WC.Arg("PRES", value),
        ])
        self.name = name

    def add_to(self, pressures, writer):
        """Add to mechanical constraints"""
        WC.ArgsConstraint.add_to(self, pressures, writer)
        pressures.add_to_mesh_change(self.name)


class Pressure(WC.ConstraintSection):
    """Pressure constraints
    """

    def __init__(self):
        WC.ConstraintSection.__init__(self)
        self._grp_names_for_mesh = []
        self.lines = None

    def add_to_mesh_change(self, name):
        """Add a group name to mesh change"""
        self._grp_names_for_mesh.append(name)

    def _write_mesh_change(self, writer):
        """Write the mesh change"""
        bloc = ""
        grps = self._grp_names_for_mesh
        model = writer.get(Modelisation)
        if grps and model: 
            lines = WC.Lines()
            cmd = "MAIL=MODI_MAILLAGE("
            lines.add(cmd + "reuse=MAIL,")
            lines.init_idt = " " * len(cmd)
            lines.add("MAILLAGE=MAIL,")
            opt = "ORIE_PEAU_%sD=_F(GROUP_MA=%s,),"
            lines.add(opt % (model.give_dim(), tuple(grps)))
            lines.add(");")
            bloc = lines.build_part()
        writer.subs("mesh_change_key", bloc)

    def add_to(self, mech_consts, writer):
        """Add to mechanical constraints"""
        self.lines = mech_consts.lines
        self.write_section("PRES_REP", self, writer)
        self._write_mesh_change(writer)

##########add by lxg begin
class ForceFace(WC.ConstraintSection):
    """ForceFace constraints
    """

    def __init__(self, Refxfem = ""):
        WC.ConstraintSection.__init__(self)
        self._grp_names_for_mesh = []
        self.lines = None
        self._Refxfem =Refxfem

    def add_to_mesh_change(self, name):
        """Add a group name to mesh change"""
        self._grp_names_for_mesh.append(name)

    def _write_mesh_change(self, writer):
        """Write the mesh change"""
        bloc = ""
        grps = self._grp_names_for_mesh
        model = writer.get(Modelisation)
        if grps and model: 
            lines = WC.Lines()
            if self._Refxfem == "out":
                cmd = "MA[i]=MODI_MAILLAGE("
                lines.add(cmd + "reuse=MA[i],")
                lines.init_idt = " " * len(cmd)
                lines.add("MAILLAGE=MA[i],")
            else :
                cmd = "MAIL=MODI_MAILLAGE("
                lines.add(cmd + "reuse=MAIL,")
                lines.init_idt = " " * len(cmd)
                lines.add("MAILLAGE=MAIL,")                
            opt = "ORIE_PEAU_%sD=_F(GROUP_MA=%s,),"
            lines.add(opt % (model.give_dim(), tuple(grps)))
            lines.add(");")
            bloc = lines.build_part()
        writer.subs("mesh_change_key", bloc)

    def add_to(self, mech_consts, writer):
        """Add to mechanical constraints"""
        self.lines = mech_consts.lines
        self.write_section("FORCE_FACE", self, writer)
        #self._write_mesh_change(writer)

##########
class ForceNodale(WC.ConstraintSection):
    """ForceNodale constraints
    """

    def __init__(self, Refxfem = ""):
        WC.ConstraintSection.__init__(self)
        self._grp_names_for_mesh = []
        self.lines = None
        self._Refxfem =Refxfem

    def add_to_mesh_change(self, name):
        """Add a group name to mesh change"""
        self._grp_names_for_mesh.append(name)

    def _write_mesh_change(self, writer):
        """Write the mesh change"""
        bloc = ""
        grps = self._grp_names_for_mesh
        model = writer.get(Modelisation)
        if grps and model: 
            lines = WC.Lines()
            if self._Refxfem == "out":
                cmd = "MA[i]=MODI_MAILLAGE("
                lines.add(cmd + "reuse=MA[i],")
                lines.init_idt = " " * len(cmd)
                lines.add("MAILLAGE=MA[i],")
            else :
                cmd = "MAIL=MODI_MAILLAGE("
                lines.add(cmd + "reuse=MAIL,")
                lines.init_idt = " " * len(cmd)
                lines.add("MAILLAGE=MAIL,")                
            opt = "ORIE_PEAU_%sD=_F(GROUP_MA=%s,),"
            lines.add(opt % (model.give_dim(), tuple(grps)))
            lines.add(");")
            bloc = lines.build_part()
        writer.subs("mesh_change_key", bloc)

    def add_to(self, mech_consts, writer):
        """Add to mechanical constraints"""
        self.lines = mech_consts.lines
        self.write_section("FORCE_NODALE", self, writer)
        #self._write_mesh_change(writer)


#####add by lxg end
class SectionPart(WC.CommFilePart):
    """Add several parts
    """
    _parts = []
    
    def add(self, part):
        self._parts.append(part)
        return part

    def add_part(self, writer):
        for part in self._parts:
            part.add_to(self, writer)
    def clear_part(self):#i do not know why it is not clear automatically
        self._parts =[]

class Contact(SectionPart):
    '''Contact define'''
    lines = None 
    pattern_key = "contact_definition_key"
    _group_pairs=None
    def __init__(self, group_pairs):
        self._group_pairs = group_pairs

    def add_to(self,writer):
        '''add the material'''
        if(len(self._group_pairs)):
            self.lines = WC.Lines()
            self.lines.add("CONTA=DEFI_CONTACT(MODELE= MODX,")
            self.lines.add("FORMULATION = 'CONTINUE',")
            self.lines.add("LISSAGE = 'OUI',")
            self.lines.add("FROTTEMENT = 'COULOMB',")
            self.lines.add("ZONE=(")
            for gp in self._group_pairs:
                self.lines.add("_F(")
                self.lines.add("COULOMB=%s,"%(gp[2]))
                self.lines.add("INTEGRATION='GAUSS',")
                self.lines.add("CONTACT_INIT='OUI',")
                self.lines.add("GROUP_MA_MAIT='%s',"%(gp[0]))
                self.lines.add("GROUP_MA_ESCL='%s',),"%(gp[1]))
            self.lines.add("));")
            writer.subs(self.pattern_key, self.lines.build_part())
        else:
            writer.subs(self.pattern_key, "")
        
        
class GrpMaterial(SectionPart):
    '''attach group with material'''
    lines = None 
    pattern_key = "material_key"

    def add_to(self,writer):
        '''add the material'''
        self.lines = WC.Lines()
        self.add_part(writer)
        writer.subs(self.pattern_key, self.lines.build_part())

class Material(WC.CommFilePart):
     '''     '''
     material_type = None
     def __init__(self,material):
        self.material_type = material

     def add_to(self,parent, writer):
        '''add the material part'''
        lines = parent.lines
        for m in self.material_type:
            material_name,material_e,material_nu = m
            par="%s=DEFI_MATERIAU(ELAS=_F("%(material_name)
            lines.add( "%s=DEFI_MATERIAU(ELAS=_F(E=%f," % ( material_name,material_e ) )
            init_idt = lines.init_idt
            lines.init_idt=" "*len(par)
            lines.add( "NU=%f,),);" % ( material_nu ) )
            lines.init_idt = init_idt 
        lines.add( "" )

class GroupMaterial(WC.CommFilePart):
     '''     '''
     ass = None
     def __init__(self,associate):
        self.ass = associate

     def add_to(self,parent, writer):
        '''add the GroupMaterial part     '''
        lines = parent.lines
        lines.add("MATE=AFFE_MATERIAU(MAILLAGE=MAIL,")
        init_idt = lines.init_idt
        lines.init_idt= ' '*len("MATE=AFFE_MATERIAU(")
        lines.add("AFFE=(")
        for a in self.ass:
            group_name,material_name = a
            lines.add("_F(GROUP_MA='%s',"%(group_name))
            lines.add("MATER=%s,),"%(material_name))
        lines.add("),);")

class BoundEnd(WC.CommFilePart):
    _spaces=0
    _mark=""
    def __init__(self,spaces,mark):
        self._spaces = spaces
        self._mark = mark
    def add_to(self,parent, writer):
        lines = parent.lines
        
        init_idt = lines.init_idt
        idt = lines.idt
        
        lines.init_idt =" "*self._spaces
        lines.idt = ""
        
        lines.add(self._mark)
        
        lines.idt=idt
        lines.init_idt = init_idt


class PressStart(WC.CommFilePart):
    _spaces=0
    _mark=""
    def __init__(self,spaces,mark):
        self._spaces = spaces
        self._mark = mark
    def add_to(self,parent, writer):
        lines = parent.lines
        init_idt = lines.init_idt
        idt = lines.idt
        
        lines.init_idt =" "*self._spaces
        lines.idt = ""
        
        lines.add(self._mark)
        
        lines.idt=idt
        lines.init_idt = init_idt

class BondContact(SectionPart):
    '''BOND Contact define'''
    lines = None
    pattern_key = "bond_contact_definition_key"
    _group_pairs=None
    def __init__(self, group_pairs):
        self._group_pairs = group_pairs

    def add_to(self,writer):
        '''add the material'''
        
        if(len(self._group_pairs)):
            self.lines = WC.Lines()
            self.lines.add("CHA3=AFFE_CHAR_MECA(")
            self.lines.add("MODELE=MODX,")
            self.lines.add("LIAISON_MAIL=(")
            for gp in self._group_pairs:
                self.lines.add("_F(")
                self.lines.add("GROUP_MA_MAIT='%s',"%(gp[0]))
                self.lines.add("GROUP_MA_ESCL='%s',"%(gp[1]))
                self.lines.add("TYPE_RACCORD='MASSIF',),")
            self.lines.add("));")
            writer.subs(self.pattern_key, self.lines.build_part())
        else:
            writer.subs(self.pattern_key, "")

class MechConstraints(WC.Constraints):
    """The part on mechanical constraints
    """
    pattern_key = "mechanical_constraints_key"

    def add_to(self, writer):
        """Add the mechanical constraints"""
        self.write_cmd("CHAR=AFFE_CHAR_MECA(", "MODELE=MODE,", writer)


class CommWriter(WC.CommWriter):
    """The Aster study case on linear static
    """
    _pattern = WC.load_pattern("linear_static_pattern.comm")

class CommWriter2(WC.CommWriter):
    """The Aster study case on linear static
    """
    _pattern = WC.load_pattern("nolinear_static_pattern.comm")
