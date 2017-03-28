# encoding: utf-8

import sys
from PyQt4 import QtGui
from PyQt4 import QtCore

class FissDialog_UI(QtGui.QDialog):
    """
    This class defines the design of a Qt dialog box dedicated to the
    salome plugin examples. It presents a UI form that contains
    parameters for the spatial dimensions of geometrical object.  
    """

    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setupUi()

    def setupUi(self):
        self.setObjectName("Dialog")
        self.resize(400, 300)
        self.hboxlayout = QtGui.QHBoxLayout(self)
        self.hboxlayout.setMargin(9)
        self.hboxlayout.setSpacing(6)
        self.hboxlayout.setObjectName("hboxlayout")
        self.vboxlayout = QtGui.QVBoxLayout()
        self.vboxlayout.setMargin(0)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setObjectName("vboxlayout")
        self.hboxlayout1 = QtGui.QHBoxLayout()
        self.hboxlayout1.setMargin(0)
        self.hboxlayout1.setSpacing(6)
        self.hboxlayout1.setObjectName("hboxlayout1")
        self.vboxlayout1 = QtGui.QVBoxLayout()
        self.vboxlayout1.setMargin(0)
        self.vboxlayout1.setSpacing(6)
        self.vboxlayout1.setObjectName("vboxlayout1")
        self.lblRMaj = QtGui.QLabel(self)
        self.lblRMaj.setObjectName("lblRMaj")
        self.vboxlayout1.addWidget(self.lblRMaj)
        self.lblRMin = QtGui.QLabel(self)
        self.lblRMin.setObjectName("lblRMin")
        self.vboxlayout1.addWidget(self.lblRMin)
        self.lblCenter = QtGui.QLabel(self)
        self.lblCenter.setObjectName("lblCenter")
        self.vboxlayout1.addWidget(self.lblCenter)
        self.lblVectX = QtGui.QLabel(self)
        self.lblVectX.setObjectName("lblVectX")
        self.vboxlayout1.addWidget(self.lblVectX)
        self.lblVectY = QtGui.QLabel(self)
        self.lblVectY.setObjectName("lblVectY")
        self.vboxlayout1.addWidget(self.lblVectY)
        
        self.hboxlayout1.addLayout(self.vboxlayout1)
        self.vboxlayout2 = QtGui.QVBoxLayout()
        cont = QtGui.QWidget()
        self.vboxlayout2.addWidget(cont)
        grid = QtGui.QGridLayout(cont)
        self.vboxlayout2.setMargin(0)
        self.vboxlayout2.setSpacing(6)
        self.vboxlayout2.setObjectName("vboxlayout2")
        self.txtRMaj = QtGui.QLineEdit(self)
        self.txtRMaj.setObjectName("txtRMaj")
        grid.addWidget(self.txtRMaj, 0, 0)
        self.txtRMin = QtGui.QLineEdit(self)
        self.txtRMin.setObjectName("txtRMin")
        grid.addWidget(self.txtRMin, 1, 0)
        self.txtCenterx = QtGui.QLineEdit(self)
        self.txtCenterx.setObjectName("txtCenterx")
        grid.addWidget(self.txtCenterx, 2, 0)
        self.txtCentery = QtGui.QLineEdit(self)
        self.txtCentery.setObjectName("txtCentery")
        grid.addWidget(self.txtCentery, 2, 1)
        self.txtCenterz = QtGui.QLineEdit(self)
        self.txtCenterz.setObjectName("txtCenterz")
        grid.addWidget(self.txtCenterz, 2, 2)
        self.txtVectXx = QtGui.QLineEdit(self)
        self.txtVectXx.setObjectName("txtVectXx")
        grid.addWidget(self.txtVectXx, 3, 0)
        self.txtVectXy = QtGui.QLineEdit(self)
        self.txtVectXy.setObjectName("txtVectXy")
        grid.addWidget(self.txtVectXy, 3, 1)
        self.txtVectXz = QtGui.QLineEdit(self)
        self.txtVectXz.setObjectName("txtVectXy")
        grid.addWidget(self.txtVectXz, 3, 2)
        self.txtVectYx = QtGui.QLineEdit(self)
        self.txtVectYx.setObjectName("txtVectYx")
        grid.addWidget(self.txtVectYx, 4, 0)
        self.txtVectYy = QtGui.QLineEdit(self)
        self.txtVectYy.setObjectName("txtVectYy")
        grid.addWidget(self.txtVectYy, 4, 1)
        self.txtVectYz = QtGui.QLineEdit(self)
        self.txtVectYz.setObjectName("txtVectYz")
        grid.addWidget(self.txtVectYz, 4, 2)
        
        self.hboxlayout1.addLayout(self.vboxlayout2)
        self.vboxlayout.addLayout(self.hboxlayout1)
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.vboxlayout.addItem(spacerItem)
        self.buttonBox = QtGui.QDialogButtonBox(self)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.NoButton|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.vboxlayout.addWidget(self.buttonBox)
        self.hboxlayout.addLayout(self.vboxlayout)
        
############ELLIPSE CYLINDER RECTANGLE##############
        self.setWindowTitle("Crack construction")
        self.lblRMaj.setText("SEMI MAJOR AXIS")
        self.lblRMin.setText("SEMI MINOR AXIS")
        self.lblCenter.setText("CENTER")
        self.lblVectX.setText("VECT_X")
        self.lblVectY.setText("VECT_Y")
##########HALF_PLANE############################


class FissDialog_UIHP(QtGui.QDialog):
    """
    This class defines the design of a Qt dialog box dedicated to the
    salome plugin examples. It presents a UI form that contains
    parameters for the spatial dimensions of geometrical object.  
    """
    
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setupUiHP()

    def setupUiHP(self):
        self.setObjectName("Dialog")
        self.resize(400, 300)
        self.hboxlayout = QtGui.QHBoxLayout(self)
        self.hboxlayout.setMargin(9)
        self.hboxlayout.setSpacing(6)
        self.hboxlayout.setObjectName("hboxlayout")
        self.vboxlayout = QtGui.QVBoxLayout()
        self.vboxlayout.setMargin(0)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setObjectName("vboxlayout")
        self.hboxlayout1 = QtGui.QHBoxLayout()
        self.hboxlayout1.setMargin(0)
        self.hboxlayout1.setSpacing(6)
        self.hboxlayout1.setObjectName("hboxlayout1")
        self.vboxlayout1 = QtGui.QVBoxLayout()
        self.vboxlayout1.setMargin(0)
        self.vboxlayout1.setSpacing(6)
        self.vboxlayout1.setObjectName("vboxlayout1")
        self.lblPFON = QtGui.QLabel(self)
        self.lblPFON.setObjectName("lblPFON")
        self.vboxlayout1.addWidget(self.lblPFON)
        self.lblNORMALE = QtGui.QLabel(self)
        self.lblNORMALE.setObjectName("lblNORMALE")
        self.vboxlayout1.addWidget(self.lblNORMALE)
        self.lblDTAN = QtGui.QLabel(self)
        self.lblDTAN.setObjectName("lblDTAN")
        self.vboxlayout1.addWidget(self.lblDTAN)
        self.hboxlayout1.addLayout(self.vboxlayout1)
        self.vboxlayout2 = QtGui.QVBoxLayout()
        cont = QtGui.QWidget()
        self.vboxlayout2.addWidget(cont)
        grid = QtGui.QGridLayout(cont)
        self.vboxlayout2.setMargin(0)
        self.vboxlayout2.setSpacing(6)
        self.vboxlayout2.setObjectName("vboxlayout2")
        self.txtPFONx = QtGui.QLineEdit(self)
        self.txtPFONx.setObjectName("txtPFONx")
        grid.addWidget(self.txtPFONx, 0, 0)
        self.txtPFONy = QtGui.QLineEdit(self)
        self.txtPFONy.setObjectName("txtPFONy")
        grid.addWidget(self.txtPFONy, 0, 1)
        self.txtPFONz= QtGui.QLineEdit(self)
        self.txtPFONz.setObjectName("txtPFONz")
        grid.addWidget(self.txtPFONz, 0, 2)
        
        self.txtNORMx = QtGui.QLineEdit(self)
        self.txtNORMx.setObjectName("txtNORMx")
        grid.addWidget(self.txtNORMx, 1, 0)
        self.txtNORMy = QtGui.QLineEdit(self)
        self.txtNORMy.setObjectName("txtNORMy")
        grid.addWidget(self.txtNORMy, 1, 1)
        self.txtNORMz= QtGui.QLineEdit(self)
        self.txtNORMz.setObjectName("txtNORMz")
        grid.addWidget(self.txtNORMz, 1, 2)
        
        self.txtDTANx = QtGui.QLineEdit(self)
        self.txtDTANx.setObjectName("txtDTANx")
        grid.addWidget(self.txtDTANx, 2, 0)
        self.txtDTANy = QtGui.QLineEdit(self)
        self.txtDTANy.setObjectName("txtDTANy")
        grid.addWidget(self.txtDTANy, 2, 1)
        self.txtDTANz= QtGui.QLineEdit(self)
        self.txtDTANz.setObjectName("txtDTANz")
        grid.addWidget(self.txtDTANz, 2, 2)
        
        self.setWindowTitle("Crack construction")
        self.lblPFON.setText("PFON")
        self.lblNORMALE.setText("NORMALE")
        self.lblDTAN.setText("DTAN")
        self.hboxlayout1.addLayout(self.vboxlayout2)
        self.vboxlayout.addLayout(self.hboxlayout1)
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.vboxlayout.addItem(spacerItem)
        self.buttonBox = QtGui.QDialogButtonBox(self)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.NoButton|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.vboxlayout.addWidget(self.buttonBox)
        self.hboxlayout.addLayout(self.vboxlayout)

class FissDialog_UISG(QtGui.QDialog):
    """
    This class defines the design of a Qt dialog box dedicated to the
    salome plugin examples. It presents a UI form that contains
    parameters for the spatial dimensions of geometrical object.  
    """

    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setupUiSG()

    def setupUiSG(self):
        self.setObjectName("Dialog")
        self.resize(400, 300)
        self.hboxlayout = QtGui.QHBoxLayout(self)
        self.hboxlayout.setMargin(9)
        self.hboxlayout.setSpacing(6)
        self.hboxlayout.setObjectName("hboxlayout")
        self.vboxlayout = QtGui.QVBoxLayout()
        self.vboxlayout.setMargin(0)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setObjectName("vboxlayout")
        self.hboxlayout1 = QtGui.QHBoxLayout()
        self.hboxlayout1.setMargin(0)
        self.hboxlayout1.setSpacing(6)
        self.hboxlayout1.setObjectName("hboxlayout1")
        self.vboxlayout1 = QtGui.QVBoxLayout()
        self.vboxlayout1.setMargin(0)
        self.vboxlayout1.setSpacing(6)
        self.vboxlayout1.setObjectName("vboxlayout1")
        self.lblPFONO = QtGui.QLabel(self)
        self.lblPFONO.setObjectName("lblPFONO")
        self.vboxlayout1.addWidget(self.lblPFONO)
        self.lblPFONE = QtGui.QLabel(self)
        self.lblPFONE.setObjectName("lblPFONE")
        self.vboxlayout1.addWidget(self.lblPFONE)
        
        self.hboxlayout1.addLayout(self.vboxlayout1)
        self.vboxlayout2 = QtGui.QVBoxLayout()
        cont = QtGui.QWidget()
        self.vboxlayout2.addWidget(cont)
        grid = QtGui.QGridLayout(cont)
        self.vboxlayout2.setMargin(0)
        self.vboxlayout2.setSpacing(6)
        self.vboxlayout2.setObjectName("vboxlayout2")
        self.txtPFONOx = QtGui.QLineEdit(self)
        self.txtPFONOx.setObjectName("txtPFONOx")
        grid.addWidget(self.txtPFONOx, 0, 0)
        self.txtPFONOy = QtGui.QLineEdit(self)
        self.txtPFONOy.setObjectName("txtPFONOy")
        grid.addWidget(self.txtPFONOy, 0, 1)
        self.txtPFONOz= QtGui.QLineEdit(self)
        self.txtPFONOz.setObjectName("txtPFONOz")
        grid.addWidget(self.txtPFONOz, 0, 2)
        
        self.txtPFONEx = QtGui.QLineEdit(self)
        self.txtPFONEx.setObjectName("txtPFONEx")
        grid.addWidget(self.txtPFONEx, 1, 0)
        self.txtPFONEy = QtGui.QLineEdit(self)
        self.txtPFONEy.setObjectName("txtPFONEy")
        grid.addWidget(self.txtPFONEy, 1, 1)
        self.txtPFONEz= QtGui.QLineEdit(self)
        self.txtPFONEz.setObjectName("txtPFONEz")
        grid.addWidget(self.txtPFONEz, 1, 2)
        
        self.setWindowTitle("Crack construction")
        self.lblPFONO.setText("PFON_ORIG")
        self.lblPFONE.setText("PFON_EXTR")
        self.hboxlayout1.addLayout(self.vboxlayout2)
        self.vboxlayout.addLayout(self.hboxlayout1)
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.vboxlayout.addItem(spacerItem)
        self.buttonBox = QtGui.QDialogButtonBox(self)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.NoButton|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.vboxlayout.addWidget(self.buttonBox)
        self.hboxlayout.addLayout(self.vboxlayout)


class FissDialog_UIHL(QtGui.QDialog):
    """
    This class defines the design of a Qt dialog box dedicated to the
    salome plugin examples. It presents a UI form that contains
    parameters for the spatial dimensions of geometrical object.  
    """
    
    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        self.setupUiHL()

    def setupUiHL(self):
        self.setObjectName("Dialog")
        self.resize(400, 300)
        self.hboxlayout = QtGui.QHBoxLayout(self)
        self.hboxlayout.setMargin(9)
        self.hboxlayout.setSpacing(6)
        self.hboxlayout.setObjectName("hboxlayout")
        self.vboxlayout = QtGui.QVBoxLayout()
        self.vboxlayout.setMargin(0)
        self.vboxlayout.setSpacing(6)
        self.vboxlayout.setObjectName("vboxlayout")
        self.hboxlayout1 = QtGui.QHBoxLayout()
        self.hboxlayout1.setMargin(0)
        self.hboxlayout1.setSpacing(6)
        self.hboxlayout1.setObjectName("hboxlayout1")
        self.vboxlayout1 = QtGui.QVBoxLayout()
        self.vboxlayout1.setMargin(0)
        self.vboxlayout1.setSpacing(6)
        self.vboxlayout1.setObjectName("vboxlayout1")
        self.lblPFON = QtGui.QLabel(self)
        self.lblPFON.setObjectName("lblPFON")
        self.vboxlayout1.addWidget(self.lblPFON)
        self.lblDTAN = QtGui.QLabel(self)
        self.lblDTAN.setObjectName("lblDTAN")
        self.vboxlayout1.addWidget(self.lblDTAN)
        
        self.hboxlayout1.addLayout(self.vboxlayout1)
        self.vboxlayout2 = QtGui.QVBoxLayout()
        cont = QtGui.QWidget()
        self.vboxlayout2.addWidget(cont)
        grid = QtGui.QGridLayout(cont)
        self.vboxlayout2.setMargin(0)
        self.vboxlayout2.setSpacing(6)
        self.vboxlayout2.setObjectName("vboxlayout2")
        self.txtPFONx = QtGui.QLineEdit(self)
        self.txtPFONx.setObjectName("txtPFONx")
        grid.addWidget(self.txtPFONx, 0, 0)
        self.txtPFONy = QtGui.QLineEdit(self)
        self.txtPFONy.setObjectName("txtPFONy")
        grid.addWidget(self.txtPFONy, 0, 1)
        self.txtPFONz= QtGui.QLineEdit(self)
        self.txtPFONz.setObjectName("txtPFONz")
        grid.addWidget(self.txtPFONz, 0, 2)
        
        self.txtDTANx = QtGui.QLineEdit(self)
        self.txtDTANx.setObjectName("txtDTANx")
        grid.addWidget(self.txtDTANx, 1, 0)
        self.txtDTANy = QtGui.QLineEdit(self)
        self.txtDTANy.setObjectName("txtDTANy")
        grid.addWidget(self.txtDTANy, 1, 1)
        self.txtDTANz= QtGui.QLineEdit(self)
        self.txtDTANz.setObjectName("txtDTANz")
        grid.addWidget(self.txtDTANz, 1, 2)
        
        self.setWindowTitle("Crack construction")
        self.lblPFON.setText("PFON")
        self.lblDTAN.setText("DTAN")
        self.hboxlayout1.addLayout(self.vboxlayout2)
        self.vboxlayout.addLayout(self.hboxlayout1)
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.vboxlayout.addItem(spacerItem)
        self.buttonBox = QtGui.QDialogButtonBox(self)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.NoButton|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.vboxlayout.addWidget(self.buttonBox)
        self.hboxlayout.addLayout(self.vboxlayout)

#
# ======================================================================
# Unit test
# ======================================================================
#
def main( args ):
    a = QtGui.QApplication(sys.argv)
    fissdialog = FissDialog_UI()
    sys.exit(fissdialog.exec_())

if __name__=="__main__":
    main(sys.argv)

