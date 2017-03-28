"""Wizard for creating an Aster study case on crack XFEM
"""
import os
import os.path as osp


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


class PatternValueRef(WC.CommFilePart):
    """A value filling the pattern from a key
    """

    def __init__(self, pattern_key , value):
        self.pattern_key = pattern_key
        self.value = value

    def add_to(self, writer):
        """Add the value to the command file"""
        for i in range(len(self.pattern_key)):
            writer.subs(self.pattern_key[i], str(self.value[i]))


#####initial_size####################
class reffPage(WC.PatternValue):
    """initial_size
    """
    def __init__(self, value):
        list = "initial_size_key"
        WC.PatternValue.__init__(self, list, value)

#####IsRefined##################
class IsRefined(WC.PatternValue):
    """ mesh refined or not
    """
    def __init__(self, value):
        WC.PatternValue.__init__(self, "refinement_key", value)

#####H0Calculed##################
class H0Calculed(WC.PatternValue):
    """ H0 calculed or not
    """
    def __init__(self, value):
        WC.PatternValue.__init__(self, "h0_calculed_key", value)

#####Calcul de hc##################
class Coef_hc(WC.PatternValue):
    """ hc
    """
    def __init__(self, value):
        WC.PatternValue.__init__(self, "coefhc_key", value)

###### definition du champ DIAMETRE n+1####
class Diam(WC.PatternValue):
    """ Field DIAMETRE n+1
    """
    def __init__(self, value):
        WC.PatternValue.__init__(self, "diam_key", value)

###### definition du type du maillage n+1####
class Concept(WC.PatternValue):
    """ definition du type du maillage n+1
    """
    def __init__(self, value):
        WC.PatternValue.__init__(self, "concept_key", value)


class FissConds(WC.ConstraintSection):
    """Boundary conditions for mechanical constraints
    """

    def add_to(self, fiss_def, writer):
        """Add to mechanical constraints"""
        self.write_section("DEFI_FISS",fiss_def, writer)


class BoundConds(WC.ConstraintSection):
    """Boundary conditions for mechanical constraints
    """

    def add_to(self, mech_consts, writer):
        """Add to mechanical constraints"""
        self.write_section("DDL_IMPO", mech_consts, writer)


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


class GrpCrack(WC.ArgsConstraint):
    """A group of pressure on elements
    """
    
    def __init__(self, name, value):
        WC.ArgsConstraint.__init__(self, [
            WC.Arg("FISSURE", WC.quote(name)),
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
                cmd = "MA[ind_mail]=MODI_MAILLAGE("
                lines.add(cmd + "reuse=MA[ind_mail],")
                lines.init_idt = " " * len(cmd)
                lines.add("MAILLAGE=MA[ind_mail],")
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

class MechConstraints(WC.Constraints):
    """The part on mechanical constraints
    """
    pattern_key = "mechanical_constraints_key"

    def add_to(self, writer):
        """Add the mechanical constraints"""
        self.write_cmd("CHAR=AFFE_CHAR_MECA(", "MODELE=MODX,", writer)


########DEFI_FISS_XFEM###########################
class FissDEF(WC.Constraints):
    """The part on mechanical constraints
    """

    def __init__(self,  crackList, crackDef , refPlace = ""):
        WC.Constraints.__init__(self)
        self._crackList = crackList
        self._crackDef = crackDef
        self._refPlace = refPlace
        self.pattern_key = None
        self.lines = None 

    def add_to(self, writer):
        """Add the mechanical constraints"""
        lines = WC.Lines()
        self.lines = lines
        if self._refPlace == "in" :
            distance = "dist"
            cond = "MAILLAGE=MAILLAGE,"
            self.pattern_key = "fissureXFEM_definition_key_in"
        elif self._refPlace == "in2" :
            distance = "distdist"
            cond = "MAILLAGE=MA[i_raff],"
            self.pattern_key = "fissureXFEM_definition_key_in2"
        else :
            distance = ""
            cond = "MAILLAGE=MA[ind_mail],"
            self.pattern_key = "fissureXFEM_definition_key"

        for i in range(len( self._crackList[0])):
            if  self._crackList[1][i] == "Ellipse":
                lines.init_idt = " "*len(distance)
                lines.add( self._crackList[0][i]+"=DEFI_FISS_XFEM(" + cond)
                lines.init_idt = " " * len("=DEFI_FISS_XFEM(")
                lines.add("DEFI_FISS=(")
                a = [self._crackDef[self._crackList[0][i]+"SEMI-MAJOR-AXIS-Ellipse"],self._crackDef[self._crackList[0][i]+"SEMI-MINOR-AXIS-Ellipse"],  \
                        (self._crackDef[self._crackList[0][i]+"CENTER_x_Ellipse"],self._crackDef[self._crackList[0][i]+"CENTER_y_Ellipse"], self._crackDef[self._crackList[0][i]+"CENTER_z_Ellipse"]),  \
                        (self._crackDef[self._crackList[0][i]+"VECT_X_x_Ellipse"],self._crackDef[self._crackList[0][i]+"VECT_X_y_Ellipse"], self._crackDef[self._crackList[0][i]+"VECT_X_z_Ellipse"]),  \
                        (self._crackDef[self._crackList[0][i]+"VECT_Y_x_Ellipse"],self._crackDef[self._crackList[0][i]+"VECT_Y_y_Ellipse"], self._crackDef[self._crackList[0][i]+"VECT_Y_z_Ellipse"])]
                self.const =  CrackAnalyisis("FORM_FISS",  self._crackList[1][i].upper(),*a)

                self.const.add_to(self, writer)
                lines.add("),);")

            elif  self._crackList[1][i] == "Cylinder":
                lines.init_idt = " "*len(distance)
                lines.add( self._crackList[0][i]+"=DEFI_FISS_XFEM(" + cond)
                lines.init_idt = " " * len("=DEFI_FISS_XFEM(")
                lines.add("DEFI_FISS=(")
                a = [self._crackDef[self._crackList[0][i]+"SEMI-MAJOR-AXIS-Cylinder"],self._crackDef[self._crackList[0][i]+"SEMI-MINOR-AXIS-Cylinder"],  \
                        (self._crackDef[self._crackList[0][i]+"CENTER_x_Cylinder"],self._crackDef[self._crackList[0][i]+"CENTER_y_Cylinder"], self._crackDef[self._crackList[0][i]+"CENTER_z_Cylinder"]),  \
                        (self._crackDef[self._crackList[0][i]+"VECT_X_x_Cylinder"],self._crackDef[self._crackList[0][i]+"VECT_X_y_Cylinder"], self._crackDef[self._crackList[0][i]+"VECT_X_z_Cylinder"]),  \
                        (self._crackDef[self._crackList[0][i]+"VECT_Y_x_Cylinder"],self._crackDef[self._crackList[0][i]+"VECT_Y_y_Cylinder"], self._crackDef[self._crackList[0][i]+"VECT_Y_z_Cylinder"])]
                self.const =  CrackAnalyisis("FORM_FISS",  "CYLINDRE",*a)

                self.const.add_to(self, writer)
                lines.add("),);")
            elif  self._crackList[1][i] == "Rectangle":
                lines.init_idt = " "*len(distance)
                lines.add( self._crackList[0][i]+"=DEFI_FISS_XFEM(" + cond)
                lines.init_idt = " " * len("=DEFI_FISS_XFEM(")
                lines.add("DEFI_FISS=(")
                a = [self._crackDef[self._crackList[0][i]+"SEMI-MAJOR-AXIS-Rectangle"],self._crackDef[self._crackList[0][i]+"SEMI-MINOR-AXIS-Rectangle"],  \
                        (self._crackDef[self._crackList[0][i]+"CENTER_x_Rectangle"],self._crackDef[self._crackList[0][i]+"CENTER_y_Rectangle"], self._crackDef[self._crackList[0][i]+"CENTER_z_Rectangle"]),  \
                        (self._crackDef[self._crackList[0][i]+"VECT_X_x_Rectangle"],self._crackDef[self._crackList[0][i]+"VECT_X_y_Rectangle"], self._crackDef[self._crackList[0][i]+"VECT_X_z_Rectangle"]),  \
                        (self._crackDef[self._crackList[0][i]+"VECT_Y_x_Rectangle"],self._crackDef[self._crackList[0][i]+"VECT_Y_y_Rectangle"], self._crackDef[self._crackList[0][i]+"VECT_Y_z_Rectangle"])]
                self.const =  CrackAnalyisis("FORM_FISS",  self._crackList[1][i].upper(),*a)

                self.const.add_to(self, writer)
                lines.add("),);")
            elif  self._crackList[1][i] == "Half_Plane":
                lines.init_idt = " "*len(distance)
                lines.add( self._crackList[0][i]+"=DEFI_FISS_XFEM(" + cond)
                lines.init_idt = " " * len("=DEFI_FISS_XFEM(")
                lines.add("DEFI_FISS=(")
                a = [(self._crackDef[self._crackList[0][i]+"Pfon_x_Half_Plane"],self._crackDef[self._crackList[0][i]+"Pfon_y_Half_Plane"], self._crackDef[self._crackList[0][i]+"Pfon_z_Half_Plane"]),  \
                        (self._crackDef[self._crackList[0][i]+"Norm_x_Half_Plane"],self._crackDef[self._crackList[0][i]+"Norm_y_Half_Plane"], self._crackDef[self._crackList[0][i]+"Norm_z_Half_Plane"]),  \
                        (self._crackDef[self._crackList[0][i]+"Dtan_x_Half_Plane"],self._crackDef[self._crackList[0][i]+"Dtan_y_Half_Plane"], self._crackDef[self._crackList[0][i]+"Dtan_z_Half_Plane"])]
                self.const =  CrackHalfPlane("FORM_FISS",  "DEMI_PLAN",*a)

                self.const.add_to(self, writer)
                lines.add("),);")
            elif  self._crackList[1][i] == "Half_Line":
                lines.init_idt = " "*len(distance)
                lines.add( self._crackList[0][i]+"=DEFI_FISS_XFEM(" + cond)
                lines.init_idt = " " * len("=DEFI_FISS_XFEM(")
                lines.add("DEFI_FISS=(")
                a = [(self._crackDef[self._crackList[0][i]+"Pfon_x_Half_Line"],self._crackDef[self._crackList[0][i]+"Pfon_y_Half_Line"], self._crackDef[self._crackList[0][i]+"Pfon_z_Half_Line"]),  \
                        (self._crackDef[self._crackList[0][i]+"Dtan_x_Half_Line"],self._crackDef[self._crackList[0][i]+"Dtan_y_Half_Line"], self._crackDef[self._crackList[0][i]+"Dtan_z_Half_Line"])]
                self.const =  CrackHalfLine("FORM_FISS", "DEMI_DROITE",*a)

                self.const.add_to(self, writer)
                lines.add("),);")
            elif  self._crackList[1][i] == "Segment":
                lines.init_idt = " "*len(distance)
                lines.add( self._crackList[0][i]+"=DEFI_FISS_XFEM(" + cond)
                lines.init_idt = " " * len("=DEFI_FISS_XFEM(")
                lines.add("DEFI_FISS=(")
                a = [(self._crackDef[self._crackList[0][i]+"PFON_ORIG_x_Segment"],self._crackDef[self._crackList[0][i]+"PFON_ORIG_y_Segment"], self._crackDef[self._crackList[0][i]+"PFON_ORIG_z_Segment"]),  \
                        (self._crackDef[self._crackList[0][i]+"PFON_EXTR_x_Segment"],self._crackDef[self._crackList[0][i]+"PFON_EXTR_y_Segment"], self._crackDef[self._crackList[0][i]+"PFON_EXTR_z_Segment"])]
                self.const =  CrackSegment("FORM_FISS",  self._crackList[1][i].upper(),*a)

                self.const.add_to(self, writer)
                lines.add("),);")
        writer.subs(self.pattern_key, lines.build_part())


class FissPost(WC.Constraints):
    """The part on mechanical constraints
    """
    
    pattern_key = "fissureXFEM_POST_key"
    def __init__(self, crackName, dim):
        WC.Constraints.__init__(self)
        self._crackName = crackName
        self._dim = dim
        self.lines = None 

    def add_to(self, writer):
        """Add the mechanical constraints"""
        lines = WC.Lines()
        self.lines = lines
        for j in range(len(self._crackName)):
                lines.init_idt = ""
                lines.add( "NB_FOND=RECU_TABLE(CO="+self._crackName[j] +",NOM_TABLE='NB_FOND_FISS')" )
                lines.add( "dict = NB_FOND.EXTR_TABLE().values()" )
                lines.add( "nb_fond = dict['NOMBRE'][0]" )
                lines.add( "DETRUIRE(CONCEPT=_F(NOM=NB_FOND),INFO=1)" )
                lines.add("")
                lines.add( "G"+str(j+1)+"= [None]*nb_fond")
                if self._dim == 3:
                    lines.add( "F_G_"+str(j+1)+"= [None]*nb_fond")
                    lines.add( "F_K1_"+str(j+1)+"= [None]*nb_fond")
                lines.add("")
                lines.add( "for i in range(nb_fond) :")
                lines.add("")
                lines.init_idt = " "*len("for")
                lines.add( "G"+str(j+1)+"[i]=CALC_G(THETA=_F(FISSURE="+self._crackName[j]+",")
                lines.init_idt = " "*len("   G2[i]=CALC_G(")
                lines.add( "NUME_FOND=i+1,")
                lines.add( "R_INF=2*h,")
                lines.add( "R_SUP=5*h,),")
                lines.init_idt = " "*len("   G2[i]=CA")
                lines.add( "RESULTAT=RESU,")
                lines.add( "OPTION='CALC_K_G')")
                lines.init_idt = " "*len("for")
                lines.add( "IMPR_TABLE(TABLE=G"+str(j+1) +"[i])")
                lines.add("")
                if self._dim == 3:
                    lines.init_idt = " "*len("for")
                    lines.add( "F_G_"+str(j+1) +"[i]=RECU_FONCTION(TABLE=G"+str(j+1) +"[i],PARA_X='ABSC_CURV',PARA_Y='G')")
                    lines.init_idt = " "*len("for")
                    lines.add( "F_K1_"+str(j+1) +"[i]=RECU_FONCTION(TABLE=G"+str(j+1) +"[i],PARA_X='ABSC_CURV',PARA_Y='K1')")
                    lines.init_idt = " "*len("for")
                    lines.add( "IMPR_FONCTION(FORMAT='XMGRACE',UNITE=29,COURBE=_F(FONCTION = F_G_"+str(j+1) +"[i],")
                    lines.init_idt = " "*len("   IMPR_FONCTION(")
                    lines.add( "LEGENDE= 'Crack "+self._crackName[j]+" Crack front #'+str(i+1)),")
                    lines.init_idt = " "*len("   IMPR_FONCTION(")
                    lines.add( "LEGENDE_X='S',LEGENDE_Y='G')")
                    lines.init_idt = " "*len("for")
                    lines.add( "IMPR_FONCTION(FORMAT='XMGRACE',UNITE=30,COURBE=_F(FONCTION = F_K1_"+str(j+1) +"[i],")
                    lines.init_idt = " "*len("   IMPR_FONCTION(")
                    lines.add( "LEGENDE= 'Crack "+self._crackName[j]+" Crack front #'+str(i+1)),")
                    lines.init_idt = " "*len("   IMPR_FONCTION(")
                    lines.add( "LEGENDE_X='S',LEGENDE_Y='K\sI')")
                    lines.add("")
        writer.subs(self.pattern_key, lines.build_part())


#####RECUPERER LA LISTE DES NOMS DE FISSURES##########

class ListFissName(WC.Constraints):
    """The part on mechanical constraints
    """
    pattern_key = "ListFissName_key"
    def __init__(self,  ListName):
        WC.Constraints.__init__(self)
        self._ListName = ListName
        self.lines = None 

    def add_to(self, writer):
        """Add the mechanical constraints"""
        lines = WC.Lines()
        self.lines = lines
        lines.add('['+','.join(self._ListName)+']')
        writer.subs(self.pattern_key, lines.build_part())


class CrackAnalyisis(WC.ArgsConstraint):
    """Displacement boundary condition of (Ellipse, Rectangle, Cylinder) Crack
    """
    _keys = ("DEMI_GRAND_AXE", "DEMI_PETIT_AXE", "CENTRE", "VECT_X", "VECT_Y")

    def __init__(self, grp_type, name, Rmai=None, Rmin=None, centre=None, vectx=None, vecty=None):
        
        args = [WC.Arg(grp_type, WC.quote(name))]
        for key, dpl in zip(self._keys, (Rmai, Rmin, centre, vectx, vecty)):
            if dpl is not None:
                args.append(WC.Arg(key, dpl))
        WC.ArgsConstraint.__init__(self, args)


class CrackHalfPlane(WC.ArgsConstraint):
    """Displacement boundary condition of HalfPlane Crack
    """
    _keys = ("PFON", "NORMALE", "DTAN")

    def __init__(self, grp_type, name, Pfon=None, Normal=None, Dtan=None):
        args = [WC.Arg(grp_type, WC.quote(name))]
        for key, dpl in zip(self._keys, (Pfon, Normal, Dtan)):
            if dpl is not None:
                args.append(WC.Arg(key, dpl))
        WC.ArgsConstraint.__init__(self, args)


class CrackSegment(WC.ArgsConstraint):
    """Displacement boundary condition of Segment Crack
    """
    _keys = ("PFON_ORIG", "PFON_EXTR")

    def __init__(self, grp_type, name, Pfon_O=None, Pfon_E=None):
        args = [WC.Arg(grp_type, WC.quote(name))]
        for key, dpl in zip(self._keys, (Pfon_O, Pfon_E)):
            if dpl is not None:
                args.append(WC.Arg(key, dpl))
        WC.ArgsConstraint.__init__(self, args)


class CrackHalfLine(WC.ArgsConstraint):
    """Displacement boundary condition of HalfLine Crack
    """
    _keys = ("PFON", "DTAN")

    def __init__(self, grp_type, name, Pfon=None, Dtan=None):
        args = [WC.Arg(grp_type, WC.quote(name))]
        for key, dpl in zip(self._keys, (Pfon, Dtan)):
            if dpl is not None:
                args.append(WC.Arg(key, dpl))
        WC.ArgsConstraint.__init__(self, args)


class CommWriter(WC.CommWriter):
    """The Aster study case on Crack Analysis
    """
    _pattern = WC.load_pattern("XFEM_pattern.comm")

class CommWriter2(WC.CommWriter):
    """The Aster study case on Crack Analysis
    """
    _pattern = WC.load_pattern("XFEM_pattern2.comm")

class CommWriter3(WC.CommWriter):
    """The Aster study case on Crack Analysis
    """
    _pattern = WC.load_pattern("refine_pro_pattern.comm")

