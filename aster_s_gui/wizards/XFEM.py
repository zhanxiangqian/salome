#coding: utf-8 -*-
"""Qt wizard on XFEM study case
"""

from PyQt4 import QtGui as qt
from PyQt4 import QtCore as qtc

import aster_s.salome_tree as ST
import aster_s.wizards.XFEM as XF
import aster_s_gui
import aster_s_gui.wizards.common as WC
import aster_s.wizards.common as WCD
import aster_s_gui.common as GC

from aster_s.utils import log_gui
#from numpy import sqrt
from functools import partial
SLOT = qtc.SLOT
QNULL = qtc.QVariant()
QIndex = qtc.QModelIndex()

import preview.preview_ellipse as SPEL
import preview.preview_cylinder as SPCY
import preview.preview_rectangle as SPRC
import preview.preview_halfplane as SPHP
import preview.preview_segment as SPSG
import preview.preview_halfline as SPHL


def is_valid_mesh(cexp, mesh, mod):
    """A valid mesh needs to have groups for pressure"""
    is_valid = True
    log_gui.debug("is_valid_mesh %s / %s", mesh, mod)
    if not mesh:
        mess = "A mesh is required"
        mod.launch(aster_s_gui.ERROR, mess)
        is_valid = False
        return is_valid
    if not cexp.give("pressure").find_groups(mesh):
        mess = "At least a group without nodes need to be defined " \
               "on the selected object"
        mod.launch(aster_s_gui.ERROR, mess)
        is_valid = False
    return is_valid


class SMeshExp(WC.CompoExp):
    """Crack Analysis SMESH explorator
    """

    def __init__(self):
        WC.CompoExp.__init__(self)
        SMesh = ST.SMeshExplorator
        exp = SMesh()
        no_grp = exp.add_group(XF.GRP_NO)
        no_grp.register((2, 3), [SMesh.node])
        ma_grp = exp.add_group(XF.GRP_MA)
        ma_grp.register((2, 3), [SMesh.edge])
        ma_grp.register((3, ), [SMesh.face, SMesh.volume])
        self.register("boundaries", exp)
        self.register("pressure", ma_grp)
        self.register("GROUP_MA_ENRI", ma_grp)
        
    def validate(self, mesh, mod):
        """A valid mesh needs to have mesh groups for defining pressure"""
        return is_valid_mesh(self, mesh, mod)


class GeomExp(WC.CompoExp):
    """Crack Analysis GEOM explorator
    """
    
    def __init__(self):
        WC.CompoExp.__init__(self)
        Geom = ST.GeomExplorator
        exp = Geom()
        no_grp = exp.add_group(XF.GRP_NO)
        no_grp.register((2, 3), [Geom.vertex])
        ma_grp = exp.add_group(XF.GRP_MA)
        ma_grp.register((2, 3), [Geom.edge])
        ma_grp.register((3, ), [Geom.face, Geom.shell])
        self.register("boundaries", exp)
        self.register("pressure", ma_grp)
        self.register("GROUP_MA_ENRI", ma_grp)

    def validate(self, mesh, mod):
        """A valid geometry needs to have mesh groups for defining pressure"""
        return is_valid_mesh(self, mesh, mod)


#######################################
#PRESSURE  BOUNDARY CONDITIONS
########################################
class PressurePage(WC.WizardPage):
    """Wizard page on pressure loading
    """

    def cleanupPage(self):
        """Clean page in case user navigates"""
        WC.WizardPage.cleanup(self)

    def initializePage(self):
        """Query the model on meshes"""
        WC.WizardPage.initialize(self)
        self.page.use(qt.QVBoxLayout())
        exp = self.give_field("exp-store").give_exp("pressure")
        grps = exp.find_groups(self.give_field("mesh"))
        dims = [(u"Pressure", 1.)]
        tit = u"Adding pressure on meshes groups"
        # The last groups should be seen first
        grps.reverse()
        WC.add_condition_selector(self, grps,  dims, "pressure-loading*", tit)


def add_pressure_page(wiz):
    """Add page on pressure loading"""
    page = wiz.add_page(u"Boundaries conditions", PressurePage())
    page.register("pressure-loading*", None)


#######################################
#PRESSURE CRACK BOUNDARY CONDITIONS
########################################
class PressCrackPage(WC.WizardPage):
    """Wizard page on pressure crack loading
    """

    def cleanupPage(self):
        """Clean page in case user navigates"""
        WC.WizardPage.cleanup(self)

    def initializePage(self):
        """Query the model on meshes"""
        WC.WizardPage.initialize(self)
        self.page.use(qt.QVBoxLayout())
        exp = self.give_field("exp-store").give_exp("pressure")
        Fiss_name = []
        for cond in self.give_field("name-geom-loading"):
            Fiss_name.append(str(cond[0]))
        grps = Fiss_name
        dims = [(u"Pressure", 1.)]
        tit = u"Adding pressure on crack face"
        # The last groups should be seen first
        WC.add_condition_selector(self, grps,  dims, "pressure-crack-loading*", tit, "Crack")


def add_presscrack_page(wiz):
    """Add page on pressure loading"""
    page = wiz.add_page(u"Boundaries conditions", PressCrackPage())
    page.register("pressure-crack-loading*", None)


#######################################
#CRACK DEFINITION
#######################################
class CrackDef(WC.WizardPage):
    """Wizard page on pressure crack loading
    """

    def cleanupPage(self):
        """Clean page in case user navigates"""
        WC.WizardPage.cleanup(self)

    def initializePage(self):
        """Query the model on meshes"""
        WC.WizardPage.initialize(self)
        lay = self.page.use(qt.QVBoxLayout())
        exp = self.give_field("exp-store").give_exp("GROUP_MA_ENRI")
        grps1 = exp.find_groups(self.give_field("mesh"))
        #########################################
        if self.give_field("model").dim == 3:
            choices = [
                "Ellipse",
                "Cylinder",
                "Half_Plane",
                "Rectangle", ]
            self.page.register("modelcrack", choices[0][0])
            dims = []
            tit = u"Adding name, geometry and GROUP_MA_ENRI of the crack"
            grps1.append('None')
            grps1.reverse()
            grps = ['None', choices]
            WC.add_condition_selector(self, grps, dims, "name-geom-loading*", tit, "GROUP_MA_ENRI", "New_coln")
        elif self.give_field("model").dim == 2:
            choices = [
                "Segment",
                "Half_Line", ]
            self.page.register("modelcrack", choices[0][0])
            dims = []
            tit = u"Adding name, geometry and GROUP_MA_ENRI of the crack"
            grps1.append('None')
            grps1.reverse()
            grps = ['None', choices]
            WC.add_condition_selector(self, grps, dims, "name-geom-loading*", tit, "GROUP_MA_ENRI", "New_coln")

    def validatePage(self):
        lay = self.page.use(qt.QVBoxLayout())
        ind0 = [str(cond[0]) for cond in self.give_field("name-geom-loading")]
        list_count = [ind0.count(i) for i in ind0]
        if max(list_count) == 1:
            return True
        else:
            dim_mess = "The name of the crack is incorrect "
            qt.QMessageBox.critical(self, "Error", dim_mess)
            return False


def add_CrackDef_page(wiz):
    """Add the page defining Crack Definition"""
    page = wiz.add_page(u"Crack definition: non-meshed crack (X-FEM)", CrackDef())
    page.register("name-geom-loading*", None)


############################################
#PREVIEW
############################################
dictdataPrev = {}
class Preview(WC.WizardPage ):
    """Wizard page on pressure crack loading
    """

    def __init__(self):
        WC.WizardPage.__init__(self)
        self.LISTEL, self.LISTCY, self.LISTRC, self.LISTHP, self.LISTSG, self.LISTHL = {}, {}, {}, {}, {}, {}
        self.ind = []
        self.ind0 = []

    def cleanupPage(self):
        """Clean page in case user navigates"""
        WC.WizardPage.cleanup(self)

    def initializePage(self):
        """Query the model on meshes"""
        WC.WizardPage.initialize(self)
        lay = self.page.use(qt.QVBoxLayout())
        lay.addWidget(qt.QLabel(u"Geometry must be defined"))
        cont = qt.QWidget()
        lay.addWidget(cont)
        grid = qt.QGridLayout(cont)
        self.ind0 = [str(cond[0]) for cond in self.give_field("name-geom-loading")]
        self.ind = [str(cond[1]) for cond in self.give_field("name-geom-loading")]
        for i in range(len(self.ind)):
            label = "Geometry and Preview of %s(%s) Crack"
            if self.ind[i]  == "Ellipse":
                but = qt.QPushButton(label % (self.ind0[i], self.ind[i]))
                lay.addWidget(but)
                but.clicked.connect(partial(self.checkEL, self.ind0[i], self.ind0, self.ind[i]))
            if self.ind[i]  == "Cylinder":
                but = qt.QPushButton(label % (self.ind0[i], self.ind[i]))
                lay.addWidget(but)
                but.clicked.connect(partial(self.checkCY, self.ind0[i], self.ind0, self.ind[i]))
            if self.ind[i]  == "Rectangle":
                but = qt.QPushButton(label % (self.ind0[i], self.ind[i]))
                lay.addWidget(but)
                but.clicked.connect(partial(self.checkRC, self.ind0[i], self.ind0, self.ind[i]))
            if self.ind[i]  == "Half_Plane":
                but = qt.QPushButton(label % (self.ind0[i], self.ind[i]))
                lay.addWidget(but)
                but.clicked.connect(partial(self.checkHP, self.ind0[i], self.ind0, self.ind[i]))
            if self.ind[i]  == "Segment":
                but = qt.QPushButton(label % (self.ind0[i], self.ind[i]))
                lay.addWidget(but)
                but.clicked.connect(partial(self.checkSG, self.ind0[i], self.ind0, self.ind[i]))
            if self.ind[i]  == "Half_Line":
                but = qt.QPushButton(label % (self.ind0[i], self.ind[i]))
                lay.addWidget(but)
                but.clicked.connect(partial(self.checkHL, self.ind0[i], self.ind0, self.ind[i])) 

    def checkEL(self, ind0, ind0F,  ind1):
        SPEL.RECUP( ind0, ind0F, ind1 )
        
        SPEL.dialogWithApply.handleAcceptWith(SPEL.acceptCallback)
        SPEL.dialogWithApply.handleRejectWith(SPEL.rejectCallback)
        SPEL.dialogWithApply.handleApplyWith(SPEL.applyCallback)
        SPEL.dialogWithApply.exec_()
        if SPEL.dialogWithApply.wasOk():
            self.LISTEL[ind0] = SPEL.dialogWithApply.getData()

    def checkCY(self, ind0, ind0F,  ind1):
        SPCY.RECUP( ind0, ind0F, ind1 )
        
        SPCY.dialogWithApply.handleAcceptWith(SPCY.acceptCallback)
        SPCY.dialogWithApply.handleRejectWith(SPCY.rejectCallback)
        SPCY.dialogWithApply.handleApplyWith(SPCY.applyCallback)
        SPCY.dialogWithApply.exec_()
        if SPCY.dialogWithApply.wasOk():
            self.LISTCY[ind0] = SPCY.dialogWithApply.getData()

    def checkRC(self, ind0, ind0F,  ind1):
        SPRC.RECUP( ind0, ind0F, ind1 )
        
        SPRC.dialogWithApply.handleAcceptWith(SPRC.acceptCallback)
        SPRC.dialogWithApply.handleRejectWith(SPRC.rejectCallback)
        SPRC.dialogWithApply.handleApplyWith(SPRC.applyCallback)
        SPRC.dialogWithApply.exec_()
        if SPRC.dialogWithApply.wasOk():
            self.LISTRC[ind0] = SPRC.dialogWithApply.getData()

    def checkHP(self, ind0, ind0F,  ind1):
        SPHP.RECUP( ind0, ind0F, ind1 )
        
        SPHP.dialogWithApply.handleAcceptWith(SPHP.acceptCallback)
        SPHP.dialogWithApply.handleRejectWith(SPHP.rejectCallback)
        SPHP.dialogWithApply.handleApplyWith(SPHP.applyCallback)
        SPHP.dialogWithApply.exec_()
        if SPHP.dialogWithApply.wasOk():
            self.LISTHP[ind0] = SPHP.dialogWithApply.getData()

    def checkSG(self, ind0, ind0F,  ind1):
        SPSG.RECUP( ind0, ind0F, ind1 )
        SPSG.dialogWithApply.handleAcceptWith(SPSG.acceptCallback)
        SPSG.dialogWithApply.handleRejectWith(SPSG.rejectCallback)
        SPSG.dialogWithApply.handleApplyWith(SPSG.applyCallback)
        SPSG.dialogWithApply.exec_()
        if SPSG.dialogWithApply.wasOk():
            self.LISTSG[ind0] = SPSG.dialogWithApply.getData()

    def checkHL(self, ind0, ind0F,  ind1):
        SPHL.RECUP( ind0, ind0F, ind1 )
        SPHL.dialogWithApply.handleAcceptWith(SPHL.acceptCallback)
        SPHL.dialogWithApply.handleRejectWith(SPHL.rejectCallback)
        SPHL.dialogWithApply.handleApplyWith(SPHL.applyCallback)
        SPHL.dialogWithApply.exec_()
        if SPHL.dialogWithApply.wasOk():
            self.LISTHL[ind0] = SPHL.dialogWithApply.getData()

    def validatePage(self):
        self.ind0 = [str(cond[0]) for cond in self.give_field("name-geom-loading")]
        self.ind = [str(cond[1]) for cond in self.give_field("name-geom-loading")]
        for i in range(len(self.ind)):
            if self.ind[i] == 'Ellipse':
                ##SEMI MAJOR AXIS
                dictdataPrev[self.ind0[i]+"SEMI-MAJOR-AXIS-Ellipse"] = float(self.LISTEL[self.ind0[i]][0])
                ##SEMI MINOR AXIS
                dictdataPrev[self.ind0[i]+"SEMI-MINOR-AXIS-Ellipse"] = float(self.LISTEL[self.ind0[i]][1])
                ##CENTER
                dictdataPrev[self.ind0[i]+"CENTER_x_Ellipse"] = float(self.LISTEL[self.ind0[i]][2])
                dictdataPrev[self.ind0[i]+"CENTER_y_Ellipse"] = float(self.LISTEL[self.ind0[i]][3])
                dictdataPrev[self.ind0[i]+"CENTER_z_Ellipse"] = float(self.LISTEL[self.ind0[i]][4])
                ##VECT_X
                dictdataPrev[self.ind0[i]+"VECT_X_x_Ellipse"] = float(self.LISTEL[self.ind0[i]][5])
                dictdataPrev[self.ind0[i]+"VECT_X_y_Ellipse"] = float( self.LISTEL[self.ind0[i]][6])
                dictdataPrev[self.ind0[i]+"VECT_X_z_Ellipse"] = float( self.LISTEL[self.ind0[i]][7])
                ##VECT_X
                dictdataPrev[self.ind0[i]+"VECT_Y_x_Ellipse"] = float(self.LISTEL[self.ind0[i]][8])
                dictdataPrev[self.ind0[i]+"VECT_Y_y_Ellipse"] = float(self.LISTEL[self.ind0[i]][9])
                dictdataPrev[self.ind0[i]+"VECT_Y_z_Ellipse"] = float(self.LISTEL[self.ind0[i]][10])
            if self.ind[i] == 'Cylinder':
                ##SEMI MAJOR AXIS
                dictdataPrev[self.ind0[i]+"SEMI-MAJOR-AXIS-Cylinder"] = float(self.LISTCY[self.ind0[i]][0])
                ##SEMI MINOR AXIS
                dictdataPrev[self.ind0[i]+"SEMI-MINOR-AXIS-Cylinder"] = float(self.LISTCY[self.ind0[i]][1])
                ##CENTER
                dictdataPrev[self.ind0[i]+"CENTER_x_Cylinder"] = float(self.LISTCY[self.ind0[i]][2])
                dictdataPrev[self.ind0[i]+"CENTER_y_Cylinder"] = float(self.LISTCY[self.ind0[i]][3])
                dictdataPrev[self.ind0[i]+"CENTER_z_Cylinder"] = float(self.LISTCY[self.ind0[i]][4])
                ##VECT_X
                dictdataPrev[self.ind0[i]+"VECT_X_x_Cylinder"] = float(self.LISTCY[self.ind0[i]][5])
                dictdataPrev[self.ind0[i]+"VECT_X_y_Cylinder"] = float(self.LISTCY[self.ind0[i]][6])
                dictdataPrev[self.ind0[i]+"VECT_X_z_Cylinder"] = float(self.LISTCY[self.ind0[i]][7])
                ##VECT_X
                dictdataPrev[self.ind0[i]+"VECT_Y_x_Cylinder"] = float(self.LISTCY[self.ind0[i]][8])
                dictdataPrev[self.ind0[i]+"VECT_Y_y_Cylinder"] = float(self.LISTCY[self.ind0[i]][9])
                dictdataPrev[self.ind0[i]+"VECT_Y_z_Cylinder"] = float(self.LISTCY[self.ind0[i]][10])
            if self.ind[i] == 'Rectangle':
                ##SEMI MAJOR AXIS
                dictdataPrev[self.ind0[i]+"SEMI-MAJOR-AXIS-Rectangle"] = float(self.LISTRC[self.ind0[i]][0])
                ##SEMI MINOR AXIS
                dictdataPrev[self.ind0[i]+"SEMI-MINOR-AXIS-Rectangle"] = float(self.LISTRC[self.ind0[i]][1])
                ##CENTER
                dictdataPrev[self.ind0[i]+"CENTER_x_Rectangle"] = float(self.LISTRC[self.ind0[i]][2])
                dictdataPrev[self.ind0[i]+"CENTER_y_Rectangle"] = float(self.LISTRC[self.ind0[i]][3])
                dictdataPrev[self.ind0[i]+"CENTER_z_Rectangle"] = float(self.LISTRC[self.ind0[i]][4])
                ##VECT_X
                dictdataPrev[self.ind0[i]+"VECT_X_x_Rectangle"] = float(self.LISTRC[self.ind0[i]][5])
                dictdataPrev[self.ind0[i]+"VECT_X_y_Rectangle"] = float(self.LISTRC[self.ind0[i]][6])
                dictdataPrev[self.ind0[i]+"VECT_X_z_Rectangle"] = float(self.LISTRC[self.ind0[i]][7])
                ##VECT_X
                dictdataPrev[self.ind0[i]+"VECT_Y_x_Rectangle"] = float(self.LISTRC[self.ind0[i]][8])
                dictdataPrev[self.ind0[i]+"VECT_Y_y_Rectangle"] = float(self.LISTRC[self.ind0[i]][9])
                dictdataPrev[self.ind0[i]+"VECT_Y_z_Rectangle"] = float(self.LISTRC[self.ind0[i]][10])
            if self.ind[i] == 'Half_Plane': 
                ##PFON
                dictdataPrev[self.ind0[i]+"Pfon_x_Half_Plane"] = float(self.LISTHP[self.ind0[i]][0])
                dictdataPrev[self.ind0[i]+"Pfon_y_Half_Plane"] = float(self.LISTHP[self.ind0[i]][1])
                dictdataPrev[self.ind0[i]+"Pfon_z_Half_Plane"] = float(self.LISTHP[self.ind0[i]][2])
                ##NORMALE
                dictdataPrev[self.ind0[i]+"Norm_x_Half_Plane"] = float(self.LISTHP[self.ind0[i]][3])
                dictdataPrev[self.ind0[i]+"Norm_y_Half_Plane"] = float(self.LISTHP[self.ind0[i]][4])
                dictdataPrev[self.ind0[i]+"Norm_z_Half_Plane"] = float(self.LISTHP[self.ind0[i]][5])
                ##DTAN
                dictdataPrev[self.ind0[i]+"Dtan_x_Half_Plane"] = float(self.LISTHP[self.ind0[i]][6])
                dictdataPrev[self.ind0[i]+"Dtan_y_Half_Plane"] = float(self.LISTHP[self.ind0[i]][7])
                dictdataPrev[self.ind0[i]+"Dtan_z_Half_Plane"] = float(self.LISTHP[self.ind0[i]][8])
            if self.ind[i]  == 'Segment': 
                ##PFON_ORIG
                dictdataPrev[self.ind0[i]+"PFON_ORIG_x_Segment"] = float(self.LISTSG[self.ind0[i]][0])
                dictdataPrev[self.ind0[i]+"PFON_ORIG_y_Segment"] = float(self.LISTSG[self.ind0[i]][1])
                dictdataPrev[self.ind0[i]+"PFON_ORIG_z_Segment"] = float(self.LISTSG[self.ind0[i]][2])
                ##PFON_EXTR
                dictdataPrev[self.ind0[i]+"PFON_EXTR_x_Segment"] = float(self.LISTSG[self.ind0[i]][3])
                dictdataPrev[self.ind0[i]+"PFON_EXTR_y_Segment"] = float(self.LISTSG[self.ind0[i]][4])
                dictdataPrev[self.ind0[i]+"PFON_EXTR_z_Segment"] = float(self.LISTSG[self.ind0[i]][5])
            if self.ind[i] == 'Half_Line': 
                ##PFON
                dictdataPrev[self.ind0[i]+"Pfon_x_Half_Line"] = float(self.LISTHL[self.ind0[i]][0])
                dictdataPrev[self.ind0[i]+"Pfon_y_Half_Line"] = float(self.LISTHL[self.ind0[i]][1])
                dictdataPrev[self.ind0[i]+"Pfon_z_Half_Line"] = float(self.LISTHL[self.ind0[i]][2])
                ##DTAN
                dictdataPrev[self.ind0[i]+"Dtan_x_Half_Line"] = float(self.LISTHL[self.ind0[i]][3])
                dictdataPrev[self.ind0[i]+"Dtan_y_Half_Line"] = float(self.LISTHL[self.ind0[i]][4])
                dictdataPrev[self.ind0[i]+"Dtan_z_Half_Line"] = float(self.LISTHL[self.ind0[i]][5])
        return True


def add_preview_page(wiz):
    """Add preview page"""
    page = wiz.add_page(u"Crack definition: non-meshed crack (X-FEM)", Preview())



##########################################
#ADD CRACK REFINEMENT
##########################################
dictdataRef = {}
VAR_MODE_KEY = "MODE"
VAR_H_KEY = "VALUE"

class refPage(WC.WizardPage):
    """Page for selecting a mesh
    """

    def __init__(self):
        qt.QWidget.__init__(self)
        self._noref  = qt.QRadioButton
        self._ref    = qt.QRadioButton
        self._ref1   = qt.QRadioButton
        self._ref2   = qt.QRadioButton
        self._ref3   = qt.QRadioButton
        self._ref4   = qt.QRadioButton
        self._h0auto = qt.QRadioButton
        self._h0man  = qt.QRadioButton

        self._customIsEnable = False
        self._labellev = qt.QLabel
        self._labelh0 = qt.QLabel
        self._h0 = 0
        self._H = 0
        self._H1 = "aa"
        self._H2 = "aaa"

    def cleanupPage(self):
        """Clean page in case of user navigation"""
        WC.WizardPage.cleanup(self)

    def initializePage(self):
        """Check that the mesh and model matches and check
        for mesh groups"""
        WC.WizardPage.initialize(self)
        lay = self.page.use(qt.QVBoxLayout())
        #######################################
        self._noref = qt.QRadioButton("No refinement")
        self._ref   = qt.QRadioButton("Automatic refinement")

        self._ref1 = qt.QRadioButton("Coarse")
        self._ref2 = qt.QRadioButton("Moderate")
        self._ref3 = qt.QRadioButton("Fine")
        self._ref4 = qt.QRadioButton("Custom")

        self._customIsEnable = False
        for cond in self.give_field("name-geom-loading"):
            if (str(cond[1]) in ('Half_Plane', 'Half_Line') ):
                self._customIsEnable = True
                break
        ######## grid0 ########

        cont0 = qt.QWidget()
        lay.addWidget(cont0)
        grid0 = qt.QGridLayout(cont0)
        grid0.addWidget(self._noref, 1, 0)
        grid0.addWidget(self._ref, 2, 0)
        self._noref.setEnabled(True)
        self._ref.setChecked(True)

        qtc.QObject.connect(self._noref, qtc.SIGNAL("clicked()"), self.checkref)
        qtc.QObject.connect(self._ref, qtc.SIGNAL("clicked()"), self.checkref)

        ######## grid1 ########

        title = u"Give the characteristic mesh size on the initial mesh near the crack(s)"
        lay.addWidget(qt.QLabel(title), 0)
        cont1 = qt.QWidget()
        lay.addWidget(cont1)
        grid1 = qt.QGridLayout(cont1)
        grid1.addWidget(qt.QLabel(u"Initial Characteristic Size (h) "), 1, 0)

        ##
        self._h0auto= qt.QRadioButton("Auto")
        self._h0man = qt.QRadioButton("Manual")

        grid1.addWidget(self._h0auto, 1, 1)
        grid1.addWidget(self._h0man, 2, 1)
        self._h0man.setEnabled(True)
        self._h0auto.setChecked(True)

        ##
        minv = 0.
        maxv = 10e100
        self._h0 = WC.create_entry(WC.Double(minv, maxv))
        self.page.register_qt_field("initial_size*", self._h0)
        self._h0.setText("1")
        self._labelh0 = qt.QLabel(u"(h > 0)")

        grid1.addWidget(self._h0, 2, 2)
        grid1.addWidget(self._labelh0, 2, 3)
        self._h0.setEnabled(False)
        self._labelh0.setEnabled(False)
        self.checkh0()

        ##
        qtc.QObject.connect(self._h0auto, qtc.SIGNAL("clicked()"), self.checkh0)
        qtc.QObject.connect(self._h0man, qtc.SIGNAL("clicked()"), self.checkh0)

        ######## grid2 ########

        cont2 = qt.QWidget()
        lay.addWidget(cont2)
        grid2 = qt.QGridLayout(cont2)

        ##
        self._labellev = qt.QLabel(u"Level Of Mesh Refinement")
        grid2.addWidget(self._labellev, 3, 0)
        grid2.addWidget(self._ref1, 4, 0)
        grid2.addWidget(self._ref2, 5, 0)
        grid2.addWidget(self._ref3, 6, 0)
        grid2.addWidget(self._ref4, 7, 0)

        ##
        self._H = WC.create_entry(WC.Double(minv, maxv))
        self._H.setText("1")
        self._H1 = qt.QLabel(u"Use size (H)")
        self._H2 = qt.QLabel(u"(H > 0)")

        grid2.addWidget(self._H, 7, 2)
        grid2.addWidget(self._H1, 7, 1)
        grid2.addWidget(self._H2, 7, 3)

        if self._customIsEnable:
            self._ref4.setChecked(True)
        else:
            self._ref2.setChecked(True)
        self.checklevel()

        ##
        qtc.QObject.connect(self._ref1, qtc.SIGNAL("clicked()"), self.check)
        qtc.QObject.connect(self._ref2, qtc.SIGNAL("clicked()"), self.check)
        qtc.QObject.connect(self._ref3, qtc.SIGNAL("clicked()"), self.check)
        qtc.QObject.connect(self._ref4, qtc.SIGNAL("clicked()"), self.check)

    def checklevel(self):
        if self._customIsEnable:
            self._ref1.setEnabled(False)
            self._ref2.setEnabled(False)
            self._ref3.setEnabled(False)
            self._ref4.setEnabled(True)
        else:
            self._ref1.setEnabled(True)
            self._ref2.setEnabled(True)
            self._ref3.setEnabled(True)
            self._ref4.setEnabled(True)
        self.check()

    def checkref(self):
        if self._noref.isChecked():
            self._labellev.setEnabled(False)
            self._ref1.setEnabled(False)
            self._ref2.setEnabled(False)
            self._ref3.setEnabled(False)
            self._ref4.setEnabled(False)
            self._H.setEnabled(False)
            self._H1.setEnabled(False)
            self._H2.setEnabled(False)
        else:
            self._labellev.setEnabled(True)
            self.checklevel()

    def checkh0(self):
        if self._h0auto.isChecked():
            h0IsCalculated = 1
            self._h0.setEnabled(False)
            self._labelh0.setEnabled(False)
        else:
            h0IsCalculated = 0
            self._h0.setEnabled(True)
            self._labelh0.setEnabled(True)
        self.page.register("h0_calculed", h0IsCalculated)

    def check(self):
        if not self._ref4.isChecked():
            self._H.setEnabled(False)
            self._H1.setEnabled(False)
            self._H2.setEnabled(False)
        else:
            self._H.setEnabled(True)
            self._H1.setEnabled(True)
            self._H2.setEnabled(True)

    def validatePage(self):
        global dictdataRef
        if self._ref4.isChecked():
            dictdataRef[VAR_MODE_KEY] = "CUSTOM"
            dictdataRef[VAR_H_KEY] = eval(str(self._H.text()))
        elif self._ref1.isChecked():
            dictdataRef[VAR_MODE_KEY] = "COARSE"
        elif self._ref2.isChecked():
            dictdataRef[VAR_MODE_KEY] = "MODERATE"
        elif self._ref3.isChecked():
            dictdataRef[VAR_MODE_KEY] = "FINE"
        if self._noref.isChecked():
            dictdataRef[VAR_MODE_KEY] = ""
        return True


def add_Refi_page(wiz):
    """Add the mesh selection page"""
    page = wiz.add_page(u"Mesh refinement", refPage())


###########################################################################################
class FinalPage(WC.FinalPage):
    """Build case
    """

    def validatePage(self):
        """Validate the wizard"""

        getf = self.give_field
        dim = getf("model").dim
        comm = XF.CommWriter()
        comm.use(XF.Modelisation(getf("model")))
        comm.use(XF.YoungModulus(self.get_float("young-modulus")))
        comm.use(XF.PoissonRatio(self.get_float("poisson-ratio")))

        ###########################################
        h0IsCalculed = self.get_int("h0_calculed")
        comm.use(XF.H0Calculed(h0IsCalculed))
        h0 = 0.
        if not h0IsCalculed:
            h0 = self.get_float("initial_size")
        comm.use(XF.reffPage(h0))

        # DEFINITION OF CRACK
        ind0 = [str(cond[0]) for cond in self.give_field("name-geom-loading")]
        ind = [str(cond[1]) for cond in self.give_field("name-geom-loading")]

        comm.use(XF.FissDEF([ind0,ind], dictdataPrev, "in"))
        ###########################################
        comm.use(XF.ListFissName(ind0))

        ####################CONSTRUCTION OF HC####################
        refinementToDo = True
        hc_raf = 0.
        if dictdataRef[VAR_MODE_KEY] in ["COARSE","MODERATE","FINE"]:
            RMAJ, RMIN = [], []
            for i in range(len(ind0)):
                if ind[i] == "Ellipse":
                    RMAJ.append(dictdataPrev[ind0[i]+"SEMI-MAJOR-AXIS-Ellipse"])
                    RMIN.append(dictdataPrev[ind0[i]+"SEMI-MINOR-AXIS-Ellipse"])
                if ind[i] == "Cylinder":
                    RMAJ.append(dictdataPrev[ind0[i]+"SEMI-MAJOR-AXIS-Cylinder"])
                    RMIN.append(dictdataPrev[ind0[i]+"SEMI-MINOR-AXIS-Cylinder"])
                if ind[i] == "Rectangle":
                    RMAJ.append(dictdataPrev[ind0[i]+"SEMI-MAJOR-AXIS-Rectangle"])
                    RMIN.append(dictdataPrev[ind0[i]+"SEMI-MINOR-AXIS-Rectangle"])
                if  ind[i] == "Segment":
                    xa = dictdataPrev[ind0[i]+"PFON_ORIG_x_Segment"]
                    ya = dictdataPrev[ind0[i]+"PFON_ORIG_y_Segment"]
                    za = dictdataPrev[ind0[i]+"PFON_ORIG_z_Segment"]
                    xb = dictdataPrev[ind0[i]+"PFON_EXTR_x_Segment"]
                    yb = dictdataPrev[ind0[i]+"PFON_EXTR_y_Segment"]
                    zb = dictdataPrev[ind0[i]+"PFON_EXTR_z_Segment"]
                    long_SG = .0 #sqrt((float(xa) -float(xb))**2 + (float(ya)-float(yb))**2 +(float(za)-float(zb)**2))
            if dictdataRef[VAR_MODE_KEY] == "COARSE":
                for i in range(len(ind)):
                    if ind[i] in ("Ellipse", "Cylinder", "Rectangle"):
                        hc_raf = float(min(min(RMIN), min(RMAJ)))/10.
                    if ind[i] == "Segment":
                        hc_raf = long_SG / 10.
            if dictdataRef[VAR_MODE_KEY] == "MODERATE":
                for i in range(len(ind)):
                    if ind[i] in ("Ellipse", "Cylinder", "Rectangle"):
                        hc_raf = float(min(min(RMIN), min(RMAJ)))/20.
                    if ind[i] == "Segment":
                        hc_raf = long_SG / 20.
            if dictdataRef[VAR_MODE_KEY] == "FINE":
                for i in range(len(ind)):
                    if ind[i] in ("Ellipse", "Cylinder", "Rectangle"):
                        hc_raf = float(min(min(RMIN), min(RMAJ)))/40.
                    if ind[i] == "Segment":
                        hc_raf = long_SG / 40.
                
        elif dictdataRef[VAR_MODE_KEY] == "CUSTOM":
            hc_raf = dictdataRef[VAR_H_KEY]
        else:
            refinementToDo = False
        comm.use(XF.IsRefined(refinementToDo))
        #######################################################
        if (not h0IsCalculed and refinementToDo):
            if (hc_raf>h0):
                mess = "Warning:  Refined mesh size is greater than the initial mesh size. No mesh refinement will be made."
                self._mod.launch(aster_s_gui.INFO, mess)
        comm.use(XF.Coef_hc(hc_raf))
        #######################################################
        comm.use(XF.FissDEF([ind0,ind], dictdataPrev, "in2"))
        #######################################################
        comm.use(XF.Concept("'MA_%d' % (i_raff+1)"))
        #######################################################
        comm.use(XF.Diam("'DIAM_%d' % (i_raff+1)"))
        #######################################################
        comm.use(XF.FissDEF([ind0,ind], dictdataPrev))
        #######################################################
        comm.use(XF.FissPost(ind0,dim))
        #######################################################
        mech_consts = comm.use(XF.MechConstraints())
        bound_conds = mech_consts.add(XF.BoundConds())
        mesh = getf("mesh")
        exp = getf("exp-store").give_exp("boundaries")
        for cond in getf("group-boundaries"):
            gname = str(cond[0])
            grp_type = exp.give_group_key(mesh, gname)
            bound_conds.add(XF.DplFromName(grp_type, gname, *cond[1:]))
        pressure = mech_consts.add(XF.Pressure("out") )
        for gname, val in getf("pressure-loading"):
            pressure.add(XF.GrpPres(str(gname), val))
        comm.write(self.get_str("command-file"))
        self.add_case("Crack-Analysis")

        return True

SIG = qtc.SIGNAL
connect = qtc.QObject.connect

            

class XFEMData():
    def __init__(self,mod):
        self.modellist = WCD.Model_Type_List(WCD.Analysis_Type.Crack_Analysis)
        self.itemindex = "defult"
        
        self.mesh = None
        self.mod = mod
        exp_store = WC.ExpStore()
        exp_store.register(WC.ExpStore.smesh, SMeshExp())
        exp_store.register(WC.ExpStore.geom, GeomExp())
        self.exp_store = exp_store
        self.grouptypesel = 0
        
        self.press_cond = [] #数据用于约束条件中的压力 
        self.degree_cond = [] #数据用于约束条件中的自由度
        self.ref_cond = [] #数据用于Crack name 表示定义的Crack名称及类型
        
        self.is_refinement = 0 
        self.characteristic_type = 0 #0表示Auto  1表示Manual
        self.characteristic_size = 0 #Manual设定的值 -1表示数据不可用
        self.refinement_level = 0  #0表示Coarse 1 表示Moderate 2表示Fine 3表示Custom  -1表示数据不可用
        self.custom_size = 0  #0 Custom level下设置的值 -1表示数据不可用
       
    def get_dim(self):
        return self.get_sel_itm().dim
        
    def get_sel_itm(self):
        return (self.modellist.get_item(self.itemindex))

class AstrefSel(WCD.AstObject):
    """Page for selecting a mesh
    """

    def __init__(self,data,parent):
        WCD.AstObject.__init__(self,parent)
        self._data = data
        self.initialize()
        self.checklevel()
        
    #def reset(self):
    #    self._noref.setChecked(True)
    #    self.setdata();
    def initialize(self):
        #######################################
        self._noref = qt.QRadioButton("No refinement")
        self._ref   = qt.QRadioButton("Automatic refinement")
        btngrp = qt.QButtonGroup(self)
        btngrp.addButton(self._noref)
        btngrp.addButton(self._ref)
        self._ref.setChecked(True)

        self._ref_invalided = qt.QRadioButton("")#该项永远不显示，由于使用buttonGroup必须有选定的radiobutton，故此采用隐藏的按钮来模拟一个radiobutton都没有被选定的状态
        self._ref_invalided.hide()
        self._ref1 = qt.QRadioButton("Coarse")
        self._ref2 = qt.QRadioButton("Moderate")
        self._ref3 = qt.QRadioButton("Fine")
        self._ref4 = qt.QRadioButton("Custom")
        
        btngrp1 = qt.QButtonGroup(self)
        btngrp1.addButton(self._ref1)
        btngrp1.addButton(self._ref2)
        btngrp1.addButton(self._ref3)
        btngrp1.addButton(self._ref4)
        btngrp1.addButton(self._ref_invalided)
        self._ref4.setChecked(True)

        ######## grid0 ########
        lay = qt.QVBoxLayout()
        self._lay = lay
        title = u"Mesh refinement"
        lay.addWidget(qt.QLabel(title))
        
        hlay1 = qt.QHBoxLayout()
        hlay1.addWidget(self._noref)
        hlay1.addWidget(self._ref)
        lay.addLayout(hlay1)
        
        qtc.QObject.connect(self._noref, qtc.SIGNAL("clicked()"), self.checkref)
        qtc.QObject.connect(self._ref, qtc.SIGNAL("clicked()"), self.checkref)

        ######## grid1 ########

        #title = u"Give the characteristic mesh size on the initial mesh near the crack(s)"
        #lay.addWidget(qt.QLabel(title))
        lay.addWidget(qt.QLabel(u"Initial Characteristic Size (h) "))

        ##
        hlay2 = qt.QHBoxLayout()
        self._h0auto= qt.QRadioButton("Auto")
        self._h0man = qt.QRadioButton("Manual")
        btngrp2 = qt.QButtonGroup(self)
        btngrp2.addButton(self._h0auto)
        btngrp2.addButton(self._h0man)


        lay.addWidget(self._h0auto)
        hlay2.addWidget(self._h0man)
        self._h0man.setEnabled(True)
        self._h0auto.setChecked(True)

        ##
        minv = 0.
        maxv = 10e100
        self._h0 = WC.create_entry(WC.Double(minv, maxv))
        self._h0.setText("1")
        self._labelh0 = qt.QLabel(u"(h > 0)")
        hlay2.addWidget(self._h0)
        hlay2.addWidget(self._labelh0)
        
        lay.addLayout(hlay2)
        #lay.addLayout(hlay3)
        self.checkh0()

        qtc.QObject.connect(self._h0, qtc.SIGNAL("textChanged(const QString &)"), self.setdata)
        qtc.QObject.connect(self._h0auto, qtc.SIGNAL("clicked()"), self.checkh0)
        qtc.QObject.connect(self._h0man, qtc.SIGNAL("clicked()"), self.checkh0)

        self._labellev = qt.QLabel(u"Level Of Mesh Refinement")
        lay.addWidget(self._labellev)
        
        hlay4 = qt.QHBoxLayout()
        hlay4.addWidget(self._ref1)
        hlay4.addWidget(self._ref2)
        hlay4.addWidget(self._ref3)
        lay.addLayout(hlay4)
        
        hlay5 = qt.QHBoxLayout()
        hlay5.addWidget(self._ref4)
        self._H = WC.create_entry(WC.Double(minv, maxv))
        self._H.setText("1")
        self._H1 = qt.QLabel(u"Use size (H)")
        self._H2 = qt.QLabel(u"(H > 0)")

        hlay5.addWidget(self._H1)
        hlay5.addWidget(self._H)
        hlay5.addWidget(self._H2)
        lay.addLayout(hlay5)
        ##
        qtc.QObject.connect(self._H, qtc.SIGNAL("textChanged(const QString &)"), self.setdata)
        qtc.QObject.connect(self._ref1, qtc.SIGNAL("clicked()"), self.check)
        qtc.QObject.connect(self._ref2, qtc.SIGNAL("clicked()"), self.check)
        qtc.QObject.connect(self._ref3, qtc.SIGNAL("clicked()"), self.check)
        qtc.QObject.connect(self._ref4, qtc.SIGNAL("clicked()"), self.check)

    def place(self, lay):
        lay.addLayout(self._lay)
        
    def checkref(self):
        if(self._noref.isChecked()):
           self._ref4.hide()
           self._H.hide()
           self._H1.hide()
           self._H2.hide()
           self._labellev.hide()
           self._ref1.hide()
           self._ref2.hide()
           self._ref3.hide()

        elif(self._ref.isChecked()):
           self._ref4.show()
           self._H.show()
           self._H1.show()
           self._labellev.show()
           self._H2.show()
           self.checklevel()

    def reset(self):
        self.checkref()

    def checklevel(self):
 
        self._customIsEnable = False
        for cond in self._data.ref_cond:
            if (str(cond[1]) in ('Half_Plane', 'Half_Line') ):
                self._customIsEnable = True
                break
        if (self._customIsEnable):
           self._ref1.show()
           self._ref2.show()
           self._ref3.show()
        else:
           self._ref1.hide()
           self._ref2.hide()
           self._ref3.hide()
        
        log_gui.debug("checklevel : update Astref with  %s", self._customIsEnable)

    def checkh0(self):
        if self._h0auto.isChecked():
            self._h0.hide()
            self._labelh0.hide()
        else:
            self._h0.show()
            self._labelh0.show()
        self.setdata()
        
    def setdata(self):
        if (self._noref.isChecked()):
            self.is_refinement = 0
            self._data.characteristic_size = -1 #Manual设定的值 -1表示数据不可用
            self._data.refinement_level = -1  #0表示Coarse 1 表示Moderate 2表示Fine 3表示Custom  -1表示数据不可用
            self._data.custom_size = -1  #0 Custom level下设置的值 -1表示数据不可用
        elif (self._ref.isChecked()):
            self.is_refinement = 0
        elif (self._h0auto.isChecked()):
            self._data.characteristic_type = 0 #0表示Auto  1表示Manual
            self._data.characteristic_size = -1 #0表示Auto  1表示Manual
        elif (self._h0man.isChecked()):
            self._data.characteristic_type = 1 #0表示Auto  1表示Manual
        elif (self._ref1.isChecked()):
            self._data.refinement_level = 0
        elif (self._ref2.isChecked()):
            self._data.refinement_level = 1
        elif (self._ref3.isChecked()):
            self._data.refinement_level = 2
        elif (self._ref4.isChecked()):
            self._data.refinement_level = 3
        elif (self._ref4.isChecked()):
            self._data.refinement_level = 3
        else:
            self._data.characteristic_size = self._h0.text().todouble()
            self._data.custom_size = self._H.text().todouble()
        self.emit_datachanged()
        
    def check(self):
        if self._ref4.isChecked():
            self._H.show()
            self._H1.show()
            self._H2.show()
        else:
            self._H.hide()
            self._H1.hide()
            self._H2.hide()
        self.setdata()


class AstPreviewModel(WC.AstConditionsModel):
    def __init__(self, sel, header_names):
        WC.AstConditionsModel.__init__(self,sel,header_names)
          
    def flags(self, midx):
        """Tell to Qt mechanism that each cell is enabled and editable"""
        flags = qtc.Qt.ItemIsEditable | qtc.Qt.ItemIsEnabled
        if (midx.row() + 1 == self.rowCount(QIndex) or midx.column() + 1 == self.columnCount(QIndex)):
            flags = qtc.Qt.ItemIsSelectable
        return flags
        
    def setbtnstate(self, midx, state):
        self._sel.set_btnstyle(midx.row(),state)
        
    def getcond(self, row):
        return self._sel.give_cond(row)
        
    def data(self, midx, role):
        """Provide data for each cell in the display role"""
        res = QNULL
        #log_gui.debug("UserRole : style  %d", self._sel.give_btnstyle(midx.row()))
        if(role == qtc.Qt.TextAlignmentRole):
           res = qtc.QVariant(qtc.Qt.AlignHCenter | qtc.Qt.AlignVCenter)
        elif role in (qtc.Qt.DisplayRole, qtc.Qt.EditRole):
           """if ( midx.row() + 1 == self.rowCount(QIndex) ):
              vallist = self._sel.give_default_val()
              res = qtc.QVariant("----")
           elif( midx.column() + 1 == self.columnCount(QIndex) ):
              res = QNULL
           else:
              cond = self._sel.give_cond(midx.row())
              res = qtc.QVariant(cond[midx.column()])"""
              
           if ( midx.column() + 1 == self.columnCount(QIndex) and midx.row() + 1 != self.rowCount(QIndex)):
              res = QNULL
           elif( midx.row() + 1 == self.rowCount(QIndex) ):
              res = qtc.QVariant("----")
           else:
              cond = self._sel.give_cond(midx.row())
              res = qtc.QVariant(cond[midx.column()])
              #log_gui.debug("displayrole : row : %d column : %d with cond %s", midx.row(), midx.column(),cond)
        elif(role  == qtc.Qt.UserRole):
              if( midx.row() + 1 == self.rowCount(QIndex) ):
                res = qt.QStyle.State_Enabled
              else:
                res = self._sel.give_btnstyle(midx.row())
        return res

class ButtonDelegate(qt.QStyledItemDelegate):
    def __init__(self, parent, model):
          self.LISTEL, self.LISTCY, self.LISTRC, self.LISTHP, self.LISTSG, self.LISTHL = {}, {}, {}, {}, {}, {}

          qt.QStyledItemDelegate.__init__(self,parent)
          self._model = model
    def paint(self, painter, option, mindex):
          model = self._model
          if (model.rowCount(QIndex) != mindex.row() + 1):
             btnop = qt.QStyleOptionButton()
             btnop.rect = option.rect.adjusted(3, 3, -3, -3)
             btnop.text = "Preview"
             if (model != None):
               flag = model.data(mindex,qtc.Qt.UserRole)
               #btnop.state = qt.QStyle.StateFlag( flag)
               btnop.state = flag
               btnop.state |= qt.QStyle.State_Enabled
               #log_gui.debug("ButtonDelegate::paintbutton with rowCount : %s and cur row : %s  flag: %s, state: %0x type: %s", model.rowCount(QIndex),  mindex.row() + 1, flag, btnop.state, type(model))
             else:
               #btnop.state = qt.QStyle.State
               btnop.state |= qt.QStyle.State_Enabled
             self.parent().style().drawControl(qt.QStyle.CE_PushButton, btnop, painter)
          else:
             super(ButtonDelegate,self).paint(painter, option, mindex)
    
    def editorEvent(self, event, model, option, mindex):
          if(event.type() == qtc.QEvent.MouseButtonPress):
            model.setbtnstate(mindex, qt.QStyleOptionButton().state | qt.QStyle.State_Sunken)
            self.onbtnclicked(model, mindex)
            return True
          elif(event.type() == qtc.QEvent.MouseButtonRelease):
            model.setbtnstate(mindex, qt.QStyleOptionButton().state & (~qt.QStyle.State_Sunken))
            return True
          else:
            return super(ButtonDelegate,self).editorEvent(event, model, option, mindex)
            


class AstConditionsSelectorXFEM(WC.AstConditionsSelector):#added by zxq 温度条件
    def __init__(self, data, condition_type, parent):#condition_type  0 表示用于自由度  1 用于压力  2 用于CrackDef  zxq 2017/2/9
        WC.AstConditionsSelector.__init__(self, data, condition_type, parent, True)
        self.LISTEL, self.LISTCY, self.LISTRC, self.LISTHP, self.LISTSG, self.LISTHL = {}, {}, {}, {}, {}, {}
        
    def valid_by_group(self):
        if(self._data.grouptypesel != 0):
            self._conds = self._data.ref_cond
            grp_names = []
            exp = self._data.exp_store.give_exp("GROUP_MA_ENRI")
            grps1 = exp.find_groups(self._data.mesh)
            if (self._data.get_dim() == 3):
               grp_names = ["Ellipse","Cylinder","Half_Plane","Rectangle"]
               grps1.append('None')
               grps1.reverse()
            elif (self._data.get_dim() == 2):
               grp_names = ["Segment","Half_Line"]
               grps1.append('None')
               grps1.reverse()
               
            log_gui.debug("valid_by_group with grp_names with dim = %d", self._data.get_dim())
            log_gui.debug(grp_names)            
            if len(grp_names):
               self._grp_names = grp_names
               head_names = [u"Crack Name", u"Crack Geometry", u""]
               self._default_cond = ["Fiss_01", self._grp_names[0]]
               model = AstPreviewModel(self, head_names)
               self._tab.setModel(model)
               self._tab.setItemDelegate(WC.TextDelegate(self))
               #self._tab.setItemDelegateForColumn(1, WC.GroupDelegate(self,self._grp_names))
               #self._tab.setItemDelegateForColumn(2, ButtonDelegate(self._tab, model))
               
               self._tab.setEnabled(True)
               self._tab.horizontalHeader().setClickable(True)
               icolumn = 0
               for iname in head_names:
                   width = 80
                   if icolumn == 1:
                      width = 110 
                   elif icolumn == 2:
                      width = 65
                   self._tab.setColumnWidth(icolumn,width) 
                   icolumn += 1
               self.add_cond()
               self.is_reseted = False
            else:
               return 
        else:
            self._build()
            
    def preview(self):
        model = self._tab.model()
        mindex = self._tab.currentIndex()
        ind0 = [model.getcond(i)[0] for i in range(model.rowCount(QIndex) - 1)]
        ind1 = model.getcond(mindex.row())[1]
        log_gui.debug("Preview with crack name : %s type : %s", ind0, ind1)

        if ind1  == "Ellipse":
                self.checkEL(ind0[mindex.row()], ind0, ind1)
        elif ind1  == "Cylinder":
                self.checkCY(ind0[mindex.row()], ind0, ind1)
        elif ind1  == "Rectangle":
                self.checkRC(ind0[mindex.row()], ind0, ind1)

        elif ind1  == "Half_Plane":
                self.checkHP(ind0[mindex.row()], ind0, ind1)

        elif ind1  == "Segment":
                self.checkSG(ind0[mindex.row()], ind0, ind1)

        elif ind1  == "Half_Line":
                self.checkHL(ind0[mindex.row()], ind0, ind1)

    def checkEL(self, ind0, ind0F,  ind1):
        SPEL.RECUP( ind0, ind0F, ind1 )
        
        SPEL.dialogWithApply.handleAcceptWith(SPEL.acceptCallback)
        SPEL.dialogWithApply.handleRejectWith(SPEL.rejectCallback)
        SPEL.dialogWithApply.handleApplyWith(SPEL.applyCallback)
        SPEL.dialogWithApply.exec_()
        if SPEL.dialogWithApply.wasOk():
            self.LISTEL[ind0] = SPEL.dialogWithApply.getData()

    def checkCY(self, ind0, ind0F,  ind1):
        SPCY.RECUP( ind0, ind0F, ind1 )
        
        SPCY.dialogWithApply.handleAcceptWith(SPCY.acceptCallback)
        SPCY.dialogWithApply.handleRejectWith(SPCY.rejectCallback)
        SPCY.dialogWithApply.handleApplyWith(SPCY.applyCallback)
        SPCY.dialogWithApply.exec_()
        if SPCY.dialogWithApply.wasOk():
            self.LISTCY[ind0] = SPCY.dialogWithApply.getData()

    def checkRC(self, ind0, ind0F,  ind1):
        SPRC.RECUP( ind0, ind0F, ind1 )
        
        SPRC.dialogWithApply.handleAcceptWith(SPRC.acceptCallback)
        SPRC.dialogWithApply.handleRejectWith(SPRC.rejectCallback)
        SPRC.dialogWithApply.handleApplyWith(SPRC.applyCallback)
        SPRC.dialogWithApply.exec_()
        if SPRC.dialogWithApply.wasOk():
            self.LISTRC[ind0] = SPRC.dialogWithApply.getData()

    def checkHP(self, ind0, ind0F,  ind1):
        SPHP.RECUP( ind0, ind0F, ind1 )
        
        SPHP.dialogWithApply.handleAcceptWith(SPHP.acceptCallback)
        SPHP.dialogWithApply.handleRejectWith(SPHP.rejectCallback)
        SPHP.dialogWithApply.handleApplyWith(SPHP.applyCallback)
        SPHP.dialogWithApply.exec_()
        if SPHP.dialogWithApply.wasOk():
            self.LISTHP[ind0] = SPHP.dialogWithApply.getData()

    def checkSG(self, ind0, ind0F,  ind1):
        SPSG.RECUP( ind0, ind0F, ind1 )
        SPSG.dialogWithApply.handleAcceptWith(SPSG.acceptCallback)
        SPSG.dialogWithApply.handleRejectWith(SPSG.rejectCallback)
        SPSG.dialogWithApply.handleApplyWith(SPSG.applyCallback)
        SPSG.dialogWithApply.exec_()
        if SPSG.dialogWithApply.wasOk():
            self.LISTSG[ind0] = SPSG.dialogWithApply.getData()

    def checkHL(self, ind0, ind0F,  ind1):
        SPHL.RECUP( ind0, ind0F, ind1 )
        SPHL.dialogWithApply.handleAcceptWith(SPHL.acceptCallback)
        SPHL.dialogWithApply.handleRejectWith(SPHL.rejectCallback)
        SPHL.dialogWithApply.handleApplyWith(SPHL.applyCallback)
        SPHL.dialogWithApply.exec_()
        if SPHL.dialogWithApply.wasOk():
           self.LISTHL[ind0] = SPHL.dialogWithApply.getData()
           
class Create_XFEMDock(qt.QDockWidget):
    def __init__(self, mod):
        desktop = mod.give_qtwid()
        qt.QDockWidget.__init__(self, desktop)
        self.data = XFEMData(mod)
        self.exp_store = self.data.exp_store
        
        self.setWindowTitle(u"Crack Analysis")
        centralWidget = qt.QWidget(self)
        vlayout = qt.QVBoxLayout()
        centralWidget.setLayout(vlayout)
        label_for_model = qt.QLabel(u"What kind of model do you want to work on?",self)
        vlayout.addWidget(label_for_model)
        
        model_sel = WC.AstModelSel(self.data,centralWidget)
        model_sel.place(vlayout)
       
        mesh_sel = WC.AstMeshSel(self.data,centralWidget)
        mesh_sel.place(vlayout)
        model_sel.add_related_component(mesh_sel)
        
        group_sel = WC.AstGroupTypeSel(self.data,centralWidget)
        connect(mesh_sel,SIG("mesh_valided"),group_sel.notify)
        model_sel.add_related_component(group_sel)

        group_sel.place(vlayout)
        
        vspacer = qt.QSpacerItem(20, 10, qt.QSizePolicy.Minimum, qt.QSizePolicy.Expanding)
        vlayout.addItem(vspacer)
       
        """grid = qt.QGridLayout()
        tc = ThermalConductance()
        tc.add_to(qt.QWidget(), grid, 0)
        vlayout.addLayout(grid)
         
        vspacer = qt.QSpacerItem(20, 10, qt.QSizePolicy.Minimum, qt.QSizePolicy.Expanding)
        vlayout.addItem(vspacer)"""

        label_for_model = qt.QLabel(u"Adding name, geometry and GROUP_MA_ENRI of the crack",centralWidget)
        vlayout.addWidget(label_for_model)
        
        preview_sel = AstConditionsSelectorXFEM(self.data,2,centralWidget)
        connect(group_sel,SIG("group_valided"),preview_sel.valid_by_group)
        preview_sel.add_to(vlayout)
        
        vspacer = qt.QSpacerItem(20, 10, qt.QSizePolicy.Minimum, qt.QSizePolicy.Expanding)
        vlayout.addItem(vspacer)
        
        ref_sel = AstrefSel(self.data, centralWidget)
        ref_sel.place(vlayout)
        preview_sel.add_related_component(ref_sel)

        grid = qt.QGridLayout()
        young = WC.YoungModulus()
        young.add_to(qt.QWidget(), grid, 0)
        
        poisson = WC.PoissonRatio()
        poisson.add_to(qt.QWidget(), grid, 1)
        vlayout.addLayout(grid)

        label_for_model = qt.QLabel(u"Adding imposed degrees of freedom on groups",centralWidget)
        vlayout.addWidget(label_for_model)
        
        degrees_sel = WC.AstConditionsSelector(self.data,0,centralWidget)
        connect(group_sel,SIG("group_valided"),degrees_sel.valid_by_group)
        degrees_sel.add_to(vlayout)
        
        vspacer = qt.QSpacerItem(20, 10, qt.QSizePolicy.Minimum, qt.QSizePolicy.Expanding)
        vlayout.addItem(vspacer)
        
        label_for_model = qt.QLabel(u"Adding pressure on meshes groups",centralWidget)
        vlayout.addWidget(label_for_model)
        
        pressure_sel = WC.AstConditionsSelector(self.data,1,centralWidget)
        connect(group_sel,SIG("group_valided"),pressure_sel.valid_by_group)
        pressure_sel.add_to(vlayout)
        
        group_sel.add_related_component(degrees_sel)
        group_sel.add_related_component(pressure_sel)
        group_sel.add_related_component(preview_sel)
        
        hlayout = qt.QHBoxLayout()
        hspacer = qt.QSpacerItem(27, 20, qt.QSizePolicy.Expanding, qt.QSizePolicy.Minimum)
        hlayout.addItem(hspacer)
        btnok = qt.QPushButton("OK",centralWidget)
        btncancel = qt.QPushButton("Cancel",centralWidget)
        hlayout.addWidget(btnok)
        hlayout.addWidget(btncancel)
        vlayout.addLayout(hlayout)
        self.setWidget(centralWidget)
        
def create_wizard(mod):
    """Create the Crack Analysis wizard"""
    wiz = WC.Wizard(u"Crack Analysis", mod)
#################################Page 1################################
    WC.add_model_page(wiz, [
        WC.Mode3D,
        WC.PlaneStress,
        WC.PlaneStrain,
        WC.AxisSymmetric,
        ])
###############################Page 2##################################
    exp_store = WC.ExpStore()
    exp_store.register(WC.ExpStore.smesh, SMeshExp())
    exp_store.register(WC.ExpStore.geom, GeomExp())
    WC.add_mesh_page(wiz, mod, exp_store)

###############################Page 3##################################
    add_CrackDef_page(wiz)
###############################Page 4##################################
    add_preview_page(wiz)
###############################Page 5##################################
    add_Refi_page(wiz)
###############################Page 6###################################
    title = u"Young's modulus and Poisson ratio definitions"
    WC.add_material_page(wiz, title, [
        WC.YoungModulus(),
        WC.PoissonRatio(),
    ])

##################################Page 7###################################
    WC.add_boundaries_page(wiz)
##################################Page 8###################################
    add_pressure_page(wiz)
##################################Page 9###################################

    WC.add_command_file_page(wiz, FinalPage(mod))

    return wiz
