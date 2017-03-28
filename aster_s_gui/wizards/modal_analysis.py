# -*- coding: utf-8 -*-
"""Qt wizard on modal analysis study case
"""

from PyQt4 import QtGui as qt
from PyQt4 import QtCore as qtc
connect = qtc.QObject.connect
SIG = qtc.SIGNAL

import aster_s.salome_tree as ST
from aster_s.wizards import modal_analysis as MA

import aster_s_gui
import aster_s_gui.wizards.common as WC
import aster_s.wizards.common as WCD
from aster_s.utils import log_gui




def at_least_a_group_TOUT(exp, mesh, mod):
    """A valid mesh needs to have at least a 'TOUT' mesh groups"""
    is_valid = True
    if 'TOUT' not in exp.find_groups(mesh):
        mesh.Crea_Group_mesh()
    return is_valid

class SMeshExp(WC.CompoExp):
    """Modal analysis SMESH explorator
    """

    def __init__(self):
        WC.CompoExp.__init__(self)
        SMesh = ST.SMeshExplorator
        exp = SMesh()
        no_grp = exp.add_group(MA.GRP_NO)
        no_grp.register((1,2, 3), [SMesh.node])
        ma_grp = exp.add_group(MA.GRP_MA)
        ma_grp.register((1,2, 3), [SMesh.edge])
        ma_grp.register((1,2,3,), [SMesh.face, SMesh.volume])
        self.register("boundaries", exp)

    def validate(self, mesh, mod):
        """Validate the mesh"""
        return at_least_a_group_TOUT(self.give("boundaries"), mesh, mod)


class GeomExp(WC.CompoExp):
    """Modal analysis GEOM explorator
    """

    def __init__(self):
        WC.CompoExp.__init__(self)
        Geom = ST.GeomExplorator
        exp = Geom()
        no_grp = exp.add_group(MA.GRP_NO)
        no_grp.register((1,2, 3), [Geom.vertex])
        ma_grp = exp.add_group(MA.GRP_MA)
        ma_grp.register((1,2, 3), [Geom.edge])
        ma_grp.register((1,2,3,), [Geom.face, Geom.shell])
        self.register("boundaries", exp)

    def validate(self, mesh, mod):
        """Validate the mesh"""
        return at_least_a_group_TOUT(self.give("boundaries"), mesh, mod)


###################################################################################
#Add Model Page with New ComboBox (PAGE1)
###################################################################################
def add_model_Npage(wiz, choices):
        """Add the model selection page"""
        page = wiz.add_page(u"Model definition")
        lay = page.use(qt.QVBoxLayout())
        lay.addWidget(qt.QLabel(u"What kind of model do you want to work on?"))
        wfield = page.register("model", choices[0][0][0][0])
        lay.addWidget(NModelSelection(wfield, choices))


class MyComboBox(qt.QComboBox):
    """Combobox for selecting model """
    def __init__(self):
        super(MyComboBox,self).__init__()

        self.setView(qt.QTreeView())
        self.parent=qtc.QModelIndex()
        self.view().setHeaderHidden(True)
        self.view().setItemsExpandable(False)
        self.view().setRootIsDecorated(False)

    def showPopup(self):
        self.setRootModelIndex(qtc.QModelIndex())
        self.view().expandAll()
        qt.QComboBox.showPopup(self)


class NModelSelection(MyComboBox):
    """Allow to select an Aster model
    """

    def __init__(self, wfield, choices):
        MyComboBox.__init__(self)
        self._wfield = wfield
        self.model = qt.QStandardItemModel()
        self.addItems(self.model, choices)
        self.setModel(self.model)
        self._choices = choices
        connect(self, SIG("currentIndexChanged(QString)"), self._update_model)

    def addItems(self, parent, elements):

        for text, children in elements:
            item = qt.QStandardItem(text[0][1])
            item.setSelectable(text[1])
            parent.appendRow(item)
            if children:
                self.addItems(item, children)

    def _update_model(self, idx):
        """Update the Aster model type from user choice"""
        Choices = []
        for x, y in enumerate(self._choices):
            for yx,yy in enumerate(y):
                if yy !=[]:
                   for yyx,yyy in enumerate(yy):
                       if yyy!=True and yyy!=False :
                          if yyy[1]!=[]:
                             Choices.append(yyy)
                          else :
                             Choices.append(yyy[0][0])

        model = Choices[[y[1] for y in Choices].index(str(idx))][0]

        self._wfield.update(model)


###############################################################################
#Selecting the number of modes Page (PAGE 3)
###############################################################################
def add_cara_page(wiz):
    """Add the page for elementary characteristics"""
    title = qt.QApplication.translate("",u"Elementary characteristics",None,qt.QApplication.UnicodeUTF8)
    page = wiz.add_page(title, CaraPage())

dictdataCARA = {}
VAR_CARA_KEY = "MODE"
VAR_CARA_H_KEY = "VALUE"
VAR_CARA_H1_KEY = "VALUE1"
VAR_CARA_H2_KEY = "VALUE2"
VAR_CARA_H3_KEY = "VALUE3"
VAR_SECT_KEY = "SECTION"
minv = 1e-10
maxv = 1e10
nb_dec = 10
INT_MAX = 2147483647

class CaraPage(WC.WizardPage):
    """Page for selecting a mode
    """

    def __init__(self):
        WC.WizardPage.__init__(self)

    def cleanupPage(self):
        """Clean page in case of user navigation"""
        WC.WizardPage.cleanup(self)

    def initializePage(self):
        """Check that the mesh and model matches and check
        for mesh groups"""

        WC.WizardPage.initialize(self)



        if str(self.give_field("model")) in ["POU_D_E", "POU_D_T"]:
                lay = self.page.use(qt.QVBoxLayout())
                title = qt.QApplication.translate("",u"Section",None,qt.QApplication.UnicodeUTF8)
                lay.addWidget(qt.QLabel(title))
                cont01 = qt.QWidget()
                lay.addWidget(cont01)
                grid01 = qt.QGridLayout(cont01)
                self._ref01   = qt.QRadioButton(qt.QApplication.translate("",u"Solid section",None,qt.QApplication.UnicodeUTF8))
                self._ref02   = qt.QRadioButton(qt.QApplication.translate("",u"Hollow section ",None,qt.QApplication.UnicodeUTF8))
                grid01.addWidget(self._ref01, 0, 0)
                grid01.addWidget(self._ref02, 0, 1)
                self._ref01.setChecked(True)
                self._ref02.setEnabled(True)
                ############################################
                cont0 = qt.QWidget()
                lay.addWidget(cont0)
                grid0 = qt.QGridLayout(cont0)

                #######################################
                self._ref1   = qt.QRadioButton(qt.QApplication.translate("",u"Circle",None,qt.QApplication.UnicodeUTF8))
                self._ref2   = qt.QRadioButton(qt.QApplication.translate("",u"Square",None,qt.QApplication.UnicodeUTF8))
                self._ref3   = qt.QRadioButton(qt.QApplication.translate("",u"Rectangle ",None,qt.QApplication.UnicodeUTF8))



                ######## grid0 ########


                grid0.addWidget(self._ref1, 1, 1)
                grid0.addWidget(self._ref2, 2, 1)
                grid0.addWidget(self._ref3, 3, 1)
                self._ref1.setChecked(True)

                self._ref2.setEnabled(True)
                self._ref3.setEnabled(True)

                #############################
                self._H1 = WC.create_entry(WC.Double(minv, maxv,nb_dec ))


                self._H11 = qt.QLabel(u"Radius")


                grid0.addWidget(self._H1, 1, 3)
                grid0.addWidget(self._H11, 1, 2)

                self._H12 = WC.create_entry(WC.Double(minv, maxv,nb_dec))


                self._H112 = qt.QLabel(u"Thickness")


                grid0.addWidget(self._H12, 1, 5)
                grid0.addWidget(self._H112, 1, 4)
                #############################

                self._H2 = WC.create_entry(WC.Double(minv, maxv,nb_dec))

                self._H21 = qt.QLabel(u"Length")

                grid0.addWidget(self._H2, 2, 3)
                grid0.addWidget(self._H21, 2, 2)

                self._H22 = WC.create_entry(WC.Double(minv, maxv,nb_dec))

                self._H221 = qt.QLabel(u"Thickness")

                grid0.addWidget(self._H22, 2, 5)
                grid0.addWidget(self._H221, 2, 4)
                #############################
                self._H3 = WC.create_entry(WC.Double(minv, maxv,nb_dec))

                self._H31 = qt.QLabel(u"Length along Y")

                grid0.addWidget(self._H3, 3, 3)
                grid0.addWidget(self._H31, 3, 2)

                self._H33 = WC.create_entry(WC.Double(minv, maxv,nb_dec))

                self._H331 = qt.QLabel(u"Length along Z")

                grid0.addWidget(self._H33, 3, 5)
                grid0.addWidget(self._H331, 3, 4)

                self._H44 = WC.create_entry(WC.Double(minv, maxv,nb_dec))

                self._H441 = qt.QLabel(u"Thickness along Y")

                grid0.addWidget(self._H44, 4, 3)
                grid0.addWidget(self._H441, 4, 2)

                self._H55 = WC.create_entry(WC.Double(minv, maxv,nb_dec))

                self._H551 = qt.QLabel(u"Thickness along Z")

                grid0.addWidget(self._H55, 4, 5)
                grid0.addWidget(self._H551, 4, 4)

                ####################################

                self._H2.setEnabled(False)
                self._H21.setEnabled(False)
                self._H22.setEnabled(False)
                self._H221.setEnabled(False)
                self._H3.setEnabled(False)
                self._H31.setEnabled(False)
                self._H33.setEnabled(False)
                self._H331.setEnabled(False)
                self._H44.setEnabled(False)
                self._H441.setEnabled(False)
                self._H12.setEnabled(False)
                self._H112.setEnabled(False)
                self._H55.setEnabled(False)
                self._H551.setEnabled(False)
                #####################################
                qtc.QObject.connect(self._ref01, qtc.SIGNAL("clicked()"), self.check01)
                qtc.QObject.connect(self._ref02, qtc.SIGNAL("clicked()"), self.check02)
                qtc.QObject.connect(self._ref1, qtc.SIGNAL("clicked()"), self.check1)
                qtc.QObject.connect(self._ref2, qtc.SIGNAL("clicked()"), self.check2)
                qtc.QObject.connect(self._ref3, qtc.SIGNAL("clicked()"), self.check3)
        elif str(self.give_field("model")) in ["DKT","DST","COQUE_3D"]:
                lay = self.page.use(qt.QVBoxLayout())
                title = qt.QApplication.translate("",u"Shell thickness",None,qt.QApplication.UnicodeUTF8)
                lay.addWidget(qt.QLabel(title))
                cont0 = qt.QWidget()
                lay.addWidget(cont0)
                grid0 = qt.QGridLayout(cont0)
                self._Plaque = WC.create_entry(WC.Double(minv, maxv,nb_dec))
                self.page.register_qt_field("EPAIS*", self._Plaque)
                self._Plaque.setText("")
                grid0.addWidget(self._Plaque, 1, 3)

        else :
                lay = self.page.use(qt.QVBoxLayout())
                cont0 = qt.QWidget()
                lay.addWidget(cont0)
                if str(self.give_field("model")) == "3D":
                   title = qt.QApplication.translate("",u"For Volumetric elements, the use of quadratic mesh will lead to better results.",None,qt.QApplication.UnicodeUTF8)
                elif str(self.give_field("model")) =="C_PLAN" :
                   title = qt.QApplication.translate("",u"For Plane stress, the use of quadratic mesh will lead to better results.",None,qt.QApplication.UnicodeUTF8)
                elif str(self.give_field("model")) =="D_PLAN" :
                   title = qt.QApplication.translate("",u"For Plane strain, the use of quadratic mesh will lead to better results.",None,qt.QApplication.UnicodeUTF8)
                elif str(self.give_field("model")) =="AXIS" :
                   title = qt.QApplication.translate("",u"For Axis symmetric, the use of quadratic mesh will lead to better results.",None,qt.QApplication.UnicodeUTF8)
                lay.addWidget(qt.QLabel(title))

    def check01(self):
        """Check when you select the Solid section button"""
        if self._ref1.isChecked():
                self._H12.setEnabled(False)
                self._H112.setEnabled(False)
        if self._ref2.isChecked():
                self._H22.setEnabled(False)
                self._H221.setEnabled(False)
        if self._ref3.isChecked():
                self._H44.setEnabled(False)
                self._H441.setEnabled(False)
                self._H55.setEnabled(False)
                self._H551.setEnabled(False)

    def check02(self):
        """Check when you select the Hollow section button"""
        if self._ref1.isChecked():
                self._H12.setEnabled(True)
                self._H112.setEnabled(True)
        if self._ref2.isChecked():
                self._H22.setEnabled(True)
                self._H221.setEnabled(True)
        if self._ref3.isChecked():
                self._H44.setEnabled(True)
                self._H441.setEnabled(True)
                self._H55.setEnabled(True)
                self._H551.setEnabled(True)
    def check1(self):
        """Check when you select the Circle button"""
        self._H2.setEnabled(False)
        self._H21.setEnabled(False)
        self._H22.setEnabled(False)
        self._H221.setEnabled(False)
        self._H3.setEnabled(False)
        self._H31.setEnabled(False)
        self._H33.setEnabled(False)
        self._H331.setEnabled(False)
        self._H44.setEnabled(False)
        self._H441.setEnabled(False)
        self._H55.setEnabled(False)
        self._H551.setEnabled(False)

        if self._ref02.isChecked():
           self._H1.setEnabled(True)
           self._H11.setEnabled(True)
           self._H12.setEnabled(True)
           self._H112.setEnabled(True)
        if self._ref01.isChecked():
           self._H1.setEnabled(True)
           self._H11.setEnabled(True)
           self._H12.setEnabled(False)
           self._H112.setEnabled(False)

    def check2(self):
        """Check when you select the Square button"""
        self._H1.setEnabled(False)
        self._H11.setEnabled(False)
        self._H12.setEnabled(False)
        self._H112.setEnabled(False)
        self._H3.setEnabled(False)
        self._H31.setEnabled(False)
        self._H33.setEnabled(False)
        self._H331.setEnabled(False)
        self._H44.setEnabled(False)
        self._H441.setEnabled(False)
        self._H55.setEnabled(False)
        self._H551.setEnabled(False)
        if self._ref02.isChecked():
                self._H2.setEnabled(True)
                self._H21.setEnabled(True)
                self._H22.setEnabled(True)
                self._H221.setEnabled(True)
        if self._ref01.isChecked():
                self._H2.setEnabled(True)
                self._H21.setEnabled(True)
                self._H22.setEnabled(False)
                self._H221.setEnabled(False)


    def check3(self):
        """Check when you select the Rectangle button"""
        self._H2.setEnabled(False)
        self._H21.setEnabled(False)
        self._H22.setEnabled(False)
        self._H221.setEnabled(False)
        self._H1.setEnabled(False)
        self._H11.setEnabled(False)
        self._H12.setEnabled(False)
        self._H112.setEnabled(False)
        if self._ref02.isChecked():
                self._H3.setEnabled(True)
                self._H31.setEnabled(True)
                self._H33.setEnabled(True)
                self._H331.setEnabled(True)
                self._H44.setEnabled(True)
                self._H441.setEnabled(True)
                self._H55.setEnabled(True)
                self._H551.setEnabled(True)
        if self._ref01.isChecked():
                self._H3.setEnabled(True)
                self._H31.setEnabled(True)
                self._H33.setEnabled(True)
                self._H331.setEnabled(True)
                self._H44.setEnabled(False)
                self._H441.setEnabled(False)
                self._H55.setEnabled(False)
                self._H551.setEnabled(False)

    def validatePage(self):
        global dictdataCARA
        while 1:
                try :
                        if str(self.give_field("model")) in ["POU_D_E", "POU_D_T"]:
                           if self._ref02.isChecked():
                                dictdataCARA[VAR_SECT_KEY] = "Creuse"
                                if self._ref1.isChecked():
                                    dictdataCARA[VAR_CARA_KEY] = "CERCLE"
                                    dictdataCARA[VAR_CARA_H_KEY] = eval(str(self._H1.text()))
                                    dictdataCARA[VAR_CARA_H1_KEY] = eval(str(self._H12.text()))
                                    #test si la valeur est nulle
                                    if dictdataCARA[VAR_CARA_H_KEY]==0 or dictdataCARA[VAR_CARA_H1_KEY]==0:
                                        qt.QMessageBox.critical(self, "ERROR", qt.QApplication.translate("",u"Zero is not accepted" ,None,qt.QApplication.UnicodeUTF8), "Ok")
                                        return False
                                elif self._ref2.isChecked():
                                    dictdataCARA[VAR_CARA_KEY] = "CARRE"
                                    dictdataCARA[VAR_CARA_H_KEY] = eval(str(self._H2.text()))
                                    dictdataCARA[VAR_CARA_H1_KEY] = eval(str(self._H22.text()))
                                    #test si la valeur est nulle
                                    if dictdataCARA[VAR_CARA_H_KEY]==0 or dictdataCARA[VAR_CARA_H1_KEY]==0:
                                        qt.QMessageBox.critical(self, "ERROR", qt.QApplication.translate("",u"Zero is not accepted" ,None,qt.QApplication.UnicodeUTF8), "Ok")
                                        return False
                                else :
                                    dictdataCARA[VAR_CARA_KEY] = "RECTANGLE"
                                    dictdataCARA[VAR_CARA_H_KEY] = eval(str(self._H3.text()))
                                    dictdataCARA[VAR_CARA_H1_KEY] = eval(str(self._H33.text()))
                                    dictdataCARA[VAR_CARA_H2_KEY] = eval(str(self._H44.text()))
                                    dictdataCARA[VAR_CARA_H3_KEY] = eval(str(self._H55.text()))
                                    #test si la valeur est nulle
                                    if dictdataCARA[VAR_CARA_H_KEY]==0 or dictdataCARA[VAR_CARA_H1_KEY]==0 or dictdataCARA[VAR_CARA_H2_KEY]==0 or dictdataCARA[VAR_CARA_H3_KEY] == 0:
                                        qt.QMessageBox.critical(self, "ERROR", qt.QApplication.translate("",u"Zero is not accepted" ,None,qt.QApplication.UnicodeUTF8), "Ok")
                                        return False
                           if self._ref01.isChecked():
                                dictdataCARA[VAR_SECT_KEY] = "Pleine"
                                if self._ref1.isChecked():
                                    dictdataCARA[VAR_CARA_KEY] = "CERCLE"
                                    dictdataCARA[VAR_CARA_H_KEY] = eval(str(self._H1.text()))
                                    #test si la valeur est nulle
                                    if dictdataCARA[VAR_CARA_H_KEY]==0 :
                                        qt.QMessageBox.critical(self, "ERROR", qt.QApplication.translate("",u"Zero is not accepted" ,None,qt.QApplication.UnicodeUTF8), "Ok")
                                        return False
                                elif self._ref2.isChecked():
                                    dictdataCARA[VAR_CARA_KEY] = "CARRE"
                                    dictdataCARA[VAR_CARA_H_KEY] = eval(str(self._H2.text()))
                                    #test si la valeur est nulle
                                    if dictdataCARA[VAR_CARA_H_KEY]==0 :
                                        qt.QMessageBox.critical(self, "ERROR", qt.QApplication.translate("",u"Zero is not accepted" ,None,qt.QApplication.UnicodeUTF8), "Ok")
                                        return False
                                else :
                                    dictdataCARA[VAR_CARA_KEY] = "RECTANGLE"
                                    dictdataCARA[VAR_CARA_H_KEY] = eval(str(self._H3.text()))
                                    dictdataCARA[VAR_CARA_H1_KEY] = eval(str(self._H33.text()))
                                    #test si la valeur est nulle
                                    if dictdataCARA[VAR_CARA_H_KEY]==0 or dictdataCARA[VAR_CARA_H1_KEY]==0 :
                                        qt.QMessageBox.critical(self, "ERROR", qt.QApplication.translate("",u"Zero is not accepted" ,None,qt.QApplication.UnicodeUTF8), "Ok")
                                        return False

                        return True
                        break
                except :
                        qt.QMessageBox.critical(self, "ERROR", qt.QApplication.translate("",u"Please fill in the following fields",None,qt.QApplication.UnicodeUTF8), "Ok")
                        return False







###############################################################################
#Add page on boundaries conditions (PAGE5)
################################################################################
def add_boundariesES_page(wiz):
    """Add page on boundary conditions"""
    page = wiz.add_page(u"Boundary conditions", BoundariesESPage())
    page.register("group-boundaries", None)



class BoundariesESPage(WC.WizardPage):
    """Wizard page on boundary conditions
    """

    def cleanupPage(self):
        """Clean page in case user navigates"""
        WC.WizardPage.cleanup(self)

    def initializePage(self):
        """Query the model and mesh for nodes and element groups"""
        WC.WizardPage.initialize(self)
        self.page.use(qt.QVBoxLayout())
        if str(self.give_field("model")) in ["POU_D_E", "POU_D_T","DKT","DST","COQUE_3D"]:
                dims = [("DX",""), ("DY",""), ("DZ",""),("DRX",""), ("DRY",""), ("DRZ","")]
        else :
                dims = [("DX", 0.), ("DY", 0.)]
                if self.give_field("model").dim == 3:
                        dims.append(("DZ", 0.))
        check = [False]*len(dims)
        exp = self.give_field("exp-store").give_exp("boundaries")
        lst = exp.find_groups(self.give_field("mesh"))
        tit = u"Adding imposed degrees of freedom on groups"

        add_condition_selectorES(self, lst, dims,check, "group-boundaries", tit)



def add_condition_selectorES(wiz_page, grp_names, dims,check, field_name, title, new_grp="Group"):
    """Add condition selector on a wizard page for the given
    data groups. The wizard page must have a layout and a mesh"""
    wfield = wiz_page.page.give(field_name)
    sel = ConditionsSelectorES(title, wfield, grp_names,dims, check,new_grp)
    # Add a least a condition if the field is mandatory
    if field_name.endswith("*"):
        sel.add_cond()
    sel.add_to(wiz_page.layout())



class ConditionsSelectorES(WC.ConditionsSelector):
    """Allow to set conditions on proposed groups.
    The conditions are built in a list of lists given to the WizardField.
    """

    def __init__(self, title, wfield, grp_names, dims,check,  new_grp="Group"):
        WC.ConditionsSelector.__init__(self, title, wfield, grp_names, dims)
        self._title = title
        self._wfield = wfield

        self._tab = qt.QTableView()
        self._grp_names =grp_names
        self._check = check
        self._dims = dims

        self._grp_names = grp_names
        names = [new_grp] + [dim[0] for dim in self._dims]
        self._model = WC.ConditionsModel(self, names)
        dcond = None
        if grp_names:
           dcond = [grp_names[0]] + check

        self._default_cond = dcond
        self._conds = []
        self.build()

    def build(self):
        """Build the condition selector"""
        tab = self._tab
        tab.setModel(self._model)
        tab.horizontalHeader().setClickable(False)
        sig = SIG("sectionClicked(int)")
        connect(tab.verticalHeader(), sig, self.remove_cond)

        if self._grp_names :
           tab.setItemDelegateForColumn(0, WC.GroupDelegate(self, self._grp_names))
           for i in range(len(self._dims)):
               tab.setItemDelegateForColumn(i+1,CheckDelegate(self))


class CheckDelegate(qt.QStyledItemDelegate):
    """Allow to select a value in a table cell or None
    """

    def __init__(self, sel):
        qt.QStyledItemDelegate.__init__(self, sel)

        self._sel = sel

    def paint(self, painter, option, midx):
        '''
        Method to draw the model.

        @param[in] painter The painter to use to draw.
        @param[in] option The QStyleOptionViewItem defining the needed object option.
        @param[in] index The
        '''

        # Get item data
        if midx.column() in {1,2,3,4,5,6}:
                value = midx.data(qtc.Qt.DisplayRole).toBool()

                # fill style options with item data
                style = qt.QApplication.style()
                opt = qt.QStyleOptionButton()
                opt.state |= qt.QStyle.State_On if value else qt.QStyle.State_Off
                opt.state |= qt.QStyle.State_Enabled
                opt.text = ""
                opt.rect = option.rect

                # draw item data as CheckBox
                style.drawControl(qt.QStyle.CE_CheckBox, opt, painter)
                return
        qt.QStyledItemDelegate.paint(self, painter, option, midx)
    def createEditor(self, parent, options, midx):
        """Create QLineEdit with validator"""

        ledit = qt.QCheckBox("",parent)
        return ledit

    def setEditorData(self, ledit, midx):
        """Set the value from the model"""
        value = midx.data(qtc.Qt.DisplayRole).toBool()
        ledit.setChecked(value)

        qt.QAbstractItemDelegate.setEditorData(self, ledit, midx)
    def updateEditorGeometry(self, editor, option, midx):
        editor.setGeometry(option.rect)
    def setModelData(self, ledit, model, midx):
        """Store the value on the model"""
        sel = self._sel
        cond = sel.give_cond(midx.row())

        if ledit.checkState() == 2:

           cond[midx.column()] = True
        else :
           cond[midx.column()] = False

        sel.notify_wizard()

################################################################################
#MODE PAGE (PAGE6)
################################################################################

def add_mode_page(wiz):
    """Add the page for selecting the number of modes"""
    title = qt.QApplication.translate("",u"Number of modes",None,qt.QApplication.UnicodeUTF8)
    page = wiz.add_page(u"Number of modes", ModPage())

dictdataMod = {}
VAR_MODE_KEY = "MODE"
VAR_H_KEY = "VALUE"
VAR_H1_KEY = "VALUE1"
class ModPage(WC.WizardPage):
    """Page for selecting a mode
    """

    def __init__(self):
        WC.WizardPage.__init__(self)
        self._ref1  = qt.QRadioButton
        self._ref2  = qt.QRadioButton
        self._ref3  = qt.QRadioButton



        self._labellev = qt.QLabel
        self._labelh0 = qt.QLabel
        self._h0 = 0
        self._H = 0
        self._H1 = " "
        self._H2 = " "

    def cleanupPage(self):
        """Clean page in case of user navigation"""
        WC.WizardPage.cleanup(self)

    def initializePage(self):
        """Check that the mesh and model matches and check
        for mesh groups"""
        WC.WizardPage.initialize(self)
        lay = self.page.use(qt.QVBoxLayout())
        title = qt.QApplication.translate("",u"Criterion for the eigenmodes search ",None,qt.QApplication.UnicodeUTF8)
        lay.addWidget(qt.QLabel(title))
        #######################################
        self._ref1   = qt.QRadioButton( qt.QApplication.translate("",u"N first eigenmodes",None,qt.QApplication.UnicodeUTF8))
        self._ref2   = qt.QRadioButton( qt.QApplication.translate("",u"Frequency band",None,qt.QApplication.UnicodeUTF8))
        self._ref3   = qt.QRadioButton( qt.QApplication.translate("",u"Frequency centered ",None,qt.QApplication.UnicodeUTF8))



        ######## grid0 ########

        cont0 = qt.QWidget()
        lay.addWidget(cont0)
        grid0 = qt.QGridLayout(cont0)
        grid0.addWidget(self._ref1, 1, 0)
        grid0.addWidget(self._ref2, 2, 0)
        grid0.addWidget(self._ref3, 3, 0)
        self._ref1.setChecked(True)

        self._ref2.setEnabled(True)
        self._ref3.setEnabled(True)

        #############################
        self._H1 = WC.create_entry(WC.Int(0, int(maxv)))
        self._H1.setText("5")


        grid0.addWidget(self._H1, 1, 2)

        #############################

        self._H2 =  WC.create_entry(WC.Double(0., maxv,nb_dec))
        self._H2.setText("0")
        self._H21 = qt.QLabel(u"Lower frequency")

        grid0.addWidget(self._H2, 2, 2)
        grid0.addWidget(self._H21, 2, 1)

        self._H22 =  WC.create_entry(WC.Double(1.e-10, maxv,nb_dec))

        self._H221 = qt.QLabel(u"Upper frequency")

        grid0.addWidget(self._H22, 2, 4)
        grid0.addWidget(self._H221, 2, 3)
        #############################
        self._H3 =  WC.create_entry(WC.Double(0., maxv,nb_dec))

        self._H31 = qt.QLabel(u"Target frequency ")

        grid0.addWidget(self._H3, 3, 2)
        grid0.addWidget(self._H31, 3, 1)

        self._H33 = WC.create_entry(WC.Int(0, int(maxv)))
        self._H33.setText("10")
        self._H331 = qt.QLabel(u"Number of frequencies")

        grid0.addWidget(self._H33, 3, 4)
        grid0.addWidget(self._H331, 3, 3)

        ####################################

        self._H2.setEnabled(False)
        self._H21.setEnabled(False)
        self._H22.setEnabled(False)
        self._H221.setEnabled(False)
        self._H3.setEnabled(False)
        self._H31.setEnabled(False)
        self._H33.setEnabled(False)
        self._H331.setEnabled(False)

        #####################################

        qtc.QObject.connect(self._ref1, qtc.SIGNAL("clicked()"), self.check1)
        qtc.QObject.connect(self._ref2, qtc.SIGNAL("clicked()"), self.check2)
        qtc.QObject.connect(self._ref3, qtc.SIGNAL("clicked()"), self.check3)

    def check1(self):
        """Check when you select 'N first eigenmodes' button"""

        if self._ref1.isChecked():
            self._H2.setEnabled(False)
            self._H21.setEnabled(False)
            self._H22.setEnabled(False)
            self._H221.setEnabled(False)
            self._H3.setEnabled(False)
            self._H31.setEnabled(False)
            self._H33.setEnabled(False)
            self._H331.setEnabled(False)
            self._H1.setEnabled(True)



    def check2(self):
        """Check when you select 'Frequency band' button"""
        if self._ref2.isChecked():
            self._H1.setEnabled(False)
            self._H3.setEnabled(False)
            self._H31.setEnabled(False)
            self._H33.setEnabled(False)
            self._H331.setEnabled(False)
            self._H2.setEnabled(True)
            self._H21.setEnabled(True)
            self._H22.setEnabled(True)
            self._H221.setEnabled(True)

    def check3(self):
        """Check when you select 'Frequency centered' button"""
        if self._ref3.isChecked():
            self._H2.setEnabled(False)
            self._H21.setEnabled(False)
            self._H22.setEnabled(False)
            self._H221.setEnabled(False)
            self._H1.setEnabled(False)
            self._H3.setEnabled(True)
            self._H31.setEnabled(True)
            self._H33.setEnabled(True)
            self._H331.setEnabled(True)


    def validatePage(self):
        global dictdataMod
        while 1:
                try :
                        if self._ref1.isChecked():
                            dictdataMod[VAR_MODE_KEY] = "PLUS_PETITE"
                            dictdataMod[VAR_H_KEY] = eval(str(self._H1.text()))
                        elif self._ref2.isChecked():
                            dictdataMod[VAR_MODE_KEY] = "BANDE"
                            dictdataMod[VAR_H_KEY] = eval(str(self._H2.text()))
                            dictdataMod[VAR_H1_KEY] = eval(str(self._H22.text()))
                            #test si dictdataMod[VAR_H_KEY] < dictdataMod[VAR_H1_KEY]
                            if dictdataMod[VAR_H_KEY] >= dictdataMod[VAR_H1_KEY]:
                                qt.QMessageBox.critical(self, "ERROR", qt.QApplication.translate("",u"The following fields are not correct",None,qt.QApplication.UnicodeUTF8), "Ok")
                                return False
                        else :
                            dictdataMod[VAR_MODE_KEY] = "CENTRE"
                            dictdataMod[VAR_H_KEY] = eval(str(self._H3.text()))
                            dictdataMod[VAR_H1_KEY] = eval(str(self._H33.text()))
                        return True
                        break
                except :
                        qt.QMessageBox.critical(self, "ERROR", qt.QApplication.translate("",u"Please fill in the following fields",None,qt.QApplication.UnicodeUTF8), "Ok")
                        return False



################################################################################
#FinalPage
################################################################################
class FinalPage(WC.FinalPage):
    """Build case
    """
    def validatePage(self):
        """Validate the wizard"""
        getf = self.give_field

        comm = MA.CommWriter()
        comm.use(MA.Modelisation(getf("model")))
        #################################AFFE_CARA_ELEM#####################################################
        dataCara = []
        dataCara.append(str(self.give_field("model")))
        if str(self.give_field("model")) in ["POU_D_E", "POU_D_T"]:

                dataCara.append(dictdataCARA[VAR_SECT_KEY])
                dataCara.append(dictdataCARA[VAR_CARA_KEY])
                dataCara.append(dictdataCARA[VAR_CARA_H_KEY])

                if dictdataCARA[VAR_SECT_KEY] == "Pleine":
                        if dictdataCARA[VAR_CARA_KEY] == "RECTANGLE":
                                dataCara.append(dictdataCARA[VAR_CARA_H1_KEY])
                else :
                        dataCara.append(dictdataCARA[VAR_CARA_H1_KEY])
                        if dictdataCARA[VAR_CARA_KEY] == "RECTANGLE":

                                dataCara.append(dictdataCARA[VAR_CARA_H2_KEY])
                                dataCara.append(dictdataCARA[VAR_CARA_H3_KEY])


        if str(self.give_field("model")) in ["DKT","DST","COQUE_3D"]:

                dataCara.append(self.get_float("EPAIS"))

        comm.use(MA.CaraELEM(dataCara))
        comm.use(MA.Cara(dataCara))
        ####################################MATERAIUX######################################################
        comm.use(MA.YoungModulus(self.get_float("young-modulus")))
        comm.use(MA.Density(self.get_float("density")))
        comm.use(MA.PoissonRatio(self.get_float("poisson-ratio")))
        ###################################AFFE_CHAR_MECA############################################
        bound_consts = comm.use(MA.BoundConstraints())
        mesh = getf("mesh")
        exp = getf("exp-store").give_exp("boundaries")


        if getf("group-boundaries"):
              for cond in getf("group-boundaries"):
                  gname = str(cond[0])
                  grp_type = exp.give_group_key(mesh, gname)
                  bound_consts.add(MA.DplFromCheckBox(grp_type, gname, *cond[1:]))
        else:
            mess = "Warning: You have not defined boundary conditions "
            self._mod.launch(aster_s_gui.INFO, mess)

        #############################NB of Modes############################################################
        dataMode = []
        dataMode.append(dictdataMod[VAR_H_KEY])
        if dictdataMod[VAR_MODE_KEY] != "PLUS_PETITE":
           dataMode.append(dictdataMod[VAR_H1_KEY])
        comm.use(MA.ModeDEF(dictdataMod[VAR_MODE_KEY],dataMode))

        comm.write(self.get_str("command-file"))

        self.add_case("modal-analysis-ES")
        return True

class MAData():#modal analysis 模态分析模块数据 added by zxq
    def __init__(self,mod):
        self.modellist = WCD.Model_Type_List(WCD.Analysis_Type.Modal_Analysis)
        self.itemindex = "defult"
        
        self.mesh = None
        self.mod = mod
        exp_store = WC.ExpStore()
        exp_store.register(WC.ExpStore.smesh, SMeshExp())
        exp_store.register(WC.ExpStore.geom, GeomExp())
        self.exp_store = exp_store
        self.grouptypesel = 0
        
    def get_dim(self):
        return self.get_sel_itm().dim
        
    def get_sel_itm(self):
        return (self.modellist.get_item(self.itemindex))
        
    def get_group_dims(self):
        name = self.get_sel_itm().name
        if str(name) in [u"Euler Beam", u"Timoshenko Beam",u"Discrete Kirchhoff Theory",u"Discrete Shear Theory",u"Volumetric shell"]:
                dims = [(u"DX",u""), (u"DY",u""), (u"DZ",u""),(u"DRX",u""), (u"DRY",u""), (u"DRZ",u"")]
        else :
                dims = [(u"DX", 0.), (u"DY", 0.)]
                if self.get_dim == WCD.Dim_Type.Three_Dim:
                        dims.append((u"DZ", 0.))
        return dims
        
SIG = qtc.SIGNAL
connect = qtc.QObject.connect
class AstModeSel(WCD.AstObject):
    def __init__(self, data, parent):
        WCD.AstObject.__init__(self,parent)
        
        self.lay = qt.QVBoxLayout()
        title = qt.QApplication.translate("",u"Criterion for the eigenmodes search ",None,qt.QApplication.UnicodeUTF8)
        self.lay.addWidget(qt.QLabel(title))
        
        self._ref1   = qt.QRadioButton( qt.QApplication.translate("",u"N first eigenmodes",None,qt.QApplication.UnicodeUTF8))
        self._ref2   = qt.QRadioButton( qt.QApplication.translate("",u"Frequency band",None,qt.QApplication.UnicodeUTF8))
        self._ref3   = qt.QRadioButton( qt.QApplication.translate("",u"Frequency centered ",None,qt.QApplication.UnicodeUTF8))
        self._ref1.setChecked(True)
        
        hlay = qt.QVBoxLayout()
        btngroup = qt.QButtonGroup(self)
        for but in (self._ref1, self._ref2, self._ref3):
            btngroup.addButton(but)
            hlay.addWidget(but)
        self.lay.addLayout(hlay)
        connect(btngroup, SIG("buttonClicked(int)"), self.show_item)
        
        wdg = qt.QWidget(parent)
        gridlay = qt.QGridLayout()
        wdg.setLayout(gridlay)
        wdg.setContentsMargins(10,5,5,10)
        self._H1 = WC.create_entry(WC.Int(0, int(INT_MAX)))
        self._H1.setText("5")
        self._L1 = qt.QLabel(u"Eigenmodes")
        self._T1 = qt.QLabel(u"(N > 0)")
        gridlay.addWidget(self._L1,0,0)
        gridlay.addWidget(self._H1,0,1)
        gridlay.addWidget(self._T1,0,2)
        
        self._H2 =  WC.create_entry(WC.Double(0., maxv,nb_dec))
        self._H2.setText("0")
        self._L2 = qt.QLabel(u"Lower frequency")
        self._T2 = qt.QLabel(u"(Lf > 0)")
        gridlay.addWidget(self._L2,1,0)
        gridlay.addWidget(self._H2,1,1)
        gridlay.addWidget(self._T2,1,2)
        
        self._H3 =  WC.create_entry(WC.Double(1.e-10, maxv,nb_dec))
        self._L3 = qt.QLabel(u"Upper frequency")
        self._T3 = qt.QLabel(u"(Uf > 1.0)")
        gridlay.addWidget(self._L3,2,0)
        gridlay.addWidget(self._H3,2,1)
        gridlay.addWidget(self._T3,2,2)

        self._H4 =  WC.create_entry(WC.Double(0., maxv,nb_dec))
        self._L4 = qt.QLabel(u"Target frequency ")
        self._T4 = qt.QLabel(u"(Tf > 0)")
        gridlay.addWidget(self._L4,3,0)
        gridlay.addWidget(self._H4,3,1)
        gridlay.addWidget(self._T4,3,2)

        self._H5 = WC.create_entry(WC.Int(0, int(INT_MAX)))
        self._H5.setText("10")
        self._L5 = qt.QLabel(u"Number of frequencies")
        self._T5 = qt.QLabel(u"(N > 0)")
        gridlay.addWidget(self._L5,4,0)
        gridlay.addWidget(self._H5,4,1)
        gridlay.addWidget(self._T5,4,2)
        self.lay.addWidget(wdg)
        for item in (self._H1,self._H2,self._H3,self._H4,self._H5,self._L1,self._L2,self._L3,self._L4,self._L5,self._T1,self._T2,self._T3,self._T4,self._T5):
            item.hide()
        self.show_item(0)
           
    def show_item(self,refid):
        if (self._ref1.isChecked()):
           self._H1.show()
           self._L1.show()
           self._T1.show()
           for item in (self._H2,self._H3,self._H4,self._H5,self._L2,self._L3,self._L4,self._L5,self._T2,self._T3,self._T4,self._T5):
               item.hide()
        elif(self._ref2.isChecked()):
           self._H2.show()
           self._L2.show()
           self._H3.show()
           self._L3.show()
           self._T2.show()
           self._T3.show()
           for item in (self._H1,self._H4,self._H5,self._L1,self._L4,self._L5),self._T1,self._T4,self._T5:
               item.hide()
        elif(self._ref3.isChecked()):
           self._H4.show()
           self._L4.show()
           self._H5.show()
           self._L5.show()           
           self._T4.show()
           self._T5.show()
           for item in (self._H1,self._H2,self._H3,self._L1,self._L2,self._L3,self._T1,self._T2,self._T3):
               item.hide()
               
    def place(self,layout):
        layout.addLayout(self.lay)
               
class AstConditionsSelectorES(WC.AstConditionsSelector):#added by zxq 用于替换ConditionsSelectorES
    def __init__(self, data, condition_type, parent):#condition_type 0 表示用于自由度， 1 表示用于压力zxq 2017/2/9
        WC.AstConditionsSelector.__init__(self, data, condition_type, parent)
        
    def valid_by_group(self):
        if(self._data.grouptypesel != 0):
            cexp = self._data.exp_store
            exp = cexp.give_exp("pressure")
            mesh = self._data.mesh
            log_gui.debug("valid_by_group by group type %s, mesh %s", self._data.grouptypesel,mesh)
            grp_names = exp.find_groups(mesh)
            self._grp_names = grp_names
            self._valided = True
            dims = self._data.get_group_dims()
            head_names = [u"Group"] + [dim[0] for dim in dims]

            checklist = [False]*len(dims)
            self._default_cond = [grp_names[0]] + checklist
            
            if self._grp_names :
               #self._tab.setItemDelegateForColumn(0, WC.GroupDelegate(self, self._grp_names))
               for i in range(len(dims)):
                   self._tab.setItemDelegateForColumn(i+1,CheckDelegate(self))
               
            model = WC.AstConditionsModel(self, head_names)
            self._tab.setModel(model)
            self._tab.setEnabled(True)
            self._tab.horizontalHeader().setClickable(True)
            icolumn = 0
            for iname in head_names:
                width = 80
                if icolumn > 0:
                   width = 60
                self._tab.setColumnWidth(icolumn,width) 
                icolumn += 1
            self.is_reseted = False
        else:
            self._build()
            

class Create_MADock(qt.QDockWidget):
    def __init__(self, mod):
        desktop = mod.give_qtwid()
        qt.QDockWidget.__init__(self, desktop)
        self.data = MAData(mod)
        self.exp_store = self.data.exp_store
        
        self.setWindowTitle(u"Modal analysis")
        centralWidget = qt.QWidget(self)
        vlayout = qt.QVBoxLayout()
        centralWidget.setLayout(vlayout)
        label_for_model = qt.QLabel(u"What kind of model do you want to work on?",self)
        vlayout.addWidget(label_for_model)
        
        model_sel = WC.AstModelSel(self.data,self)
        model_sel.place(vlayout)
       
        vspacer = qt.QSpacerItem(20, 10, qt.QSizePolicy.Minimum, qt.QSizePolicy.Expanding)
        vlayout.addItem(vspacer)

        mesh_sel = WC.AstMeshSel(self.data,self)
        mesh_sel.place(vlayout)
        model_sel.add_related_component(mesh_sel)
        
        group_sel = WC.AstGroupTypeSel(self.data,self)
        connect(mesh_sel,SIG("mesh_valided"),group_sel.notify)
        model_sel.add_related_component(group_sel)

        group_sel.place(vlayout)
        
        vspacer = qt.QSpacerItem(20, 10, qt.QSizePolicy.Minimum, qt.QSizePolicy.Expanding)
        vlayout.addItem(vspacer)
        
        title = qt.QApplication.translate("",u"Elementary characteristics",None,qt.QApplication.UnicodeUTF8)
        log_gui.debug("title %s", title)
        
        grid = qt.QGridLayout()
        young = WC.YoungModulus()
        young.add_to(qt.QWidget(), grid, 0)
        
        dens = WC.Density()
        dens.add_to(qt.QWidget(), grid, 1)
        
        poisson = WC.PoissonRatio()
        poisson.add_to(qt.QWidget(), grid, 2)
        
        vlayout.addLayout(grid)
        
         
        vspacer = qt.QSpacerItem(20, 10, qt.QSizePolicy.Minimum, qt.QSizePolicy.Expanding)
        vlayout.addItem(vspacer)

        label_for_model = qt.QLabel(u"Adding imposed degrees of freedom on groups",self)
        vlayout.addWidget(label_for_model)
        
        degrees_sel = AstConditionsSelectorES(self.data,0,self)
        #connect(group_sel,SIG("group_valided"),degrees_sel.valid_by_group)
        degrees_sel.add_to(vlayout)
        
        vspacer = qt.QSpacerItem(20, 10, qt.QSizePolicy.Minimum, qt.QSizePolicy.Expanding)
        vlayout.addItem(vspacer)
        
        group_sel.add_related_component(degrees_sel)
        
        mode_sel = AstModeSel(self.data,self)
        mode_sel.place(vlayout)
        
        hlayout = qt.QHBoxLayout()
        hspacer = qt.QSpacerItem(27, 20, qt.QSizePolicy.Expanding, qt.QSizePolicy.Minimum)
        hlayout.addItem(hspacer)
        btnok = qt.QPushButton("OK",centralWidget)
        btncancel = qt.QPushButton("Cancel",centralWidget)
        hlayout.addWidget(btnok)
        hlayout.addWidget(btncancel)
        vlayout.addLayout(hlayout)
        self.setWidget(centralWidget)
       

#################################################################
def create_wizard(mod):
    """Create the modal analysis wizard"""
    wiz = WC.Wizard(u"Modal analysis", mod)

###################Page1##########################################

    add_model_Npage(wiz,[
        ((WC.Mode3DV,True),[]),
        ((WC.PlaneStress,True),[]),
        ((WC.PlaneStrain,True),[]),
        ((WC.AxisSymmetric,True),[]),
        ((WC.Ele_filaire,False), [((WC.POU_D_E ,True), []),((WC.POU_D_T,True), [])]),
        ((WC.Ele_surface,False), [((WC.DKT ,True), []),((WC.DST,True), []),((WC.COQUE_3D,True), [])]),
        ])


#################Page2#############################################
    exp_store = WC.ExpStore()
    exp_store.register(WC.ExpStore.smesh, SMeshExp())
    exp_store.register(WC.ExpStore.geom, GeomExp())

    WC.add_mesh_page(wiz, mod, exp_store)

################Page3##############################################
    add_cara_page(wiz)

################Page4##############################################
    title = qt.QApplication.translate("",u"Young's modulus, density and Poisson ratio definitions",None,qt.QApplication.UnicodeUTF8)
    WC.add_material_page(wiz, title, [
        WC.YoungModulus(),
        WC.Density(),
        WC.PoissonRatio(),
    ])
################Page5##############################################
    add_boundariesES_page(wiz)
################Page6##############################################
    add_mode_page(wiz)

    WC.add_command_file_page(wiz, FinalPage(mod))
    return wiz


