# encoding: utf-8

import sys
from PyQt4 import QtGui
from PyQt4 import QtCore

from fissdialog_ui import FissDialog_UI
from fissdialog_ui import FissDialog_UIHP
from fissdialog_ui import FissDialog_UISG
from fissdialog_ui import FissDialog_UIHL
from functools import partial


class FissDialog(FissDialog_UI):
    
    def setupUi(self):
        FissDialog_UI.setupUi(self)
        self.handleAcceptWith(self.accept)
        self.handleRejectWith(self.reject)

    def handleAcceptWith(self,callbackFunction):
        """This defines the function to be connected to the signal 'accepted()' (click on Ok)"""
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), callbackFunction)
       

    def handleRejectWith(self,callbackFunction):
        """This defines the function to be connected to the signal 'rejected()' (click on Cancel)"""
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), callbackFunction)

    def handleApplyWith(self,callbackFunction):
        """This defines the function to be connected to the signal 'apply()' (click on Apply)"""
        button = self.buttonBox.button(QtGui.QDialogButtonBox.Apply)        
        QtCore.QObject.connect(button, QtCore.SIGNAL("clicked()"),callbackFunction)

    def accept(self):
        '''Callback function when dialog is accepted (click Ok)'''
        self._wasOk = True
        # We should test here the validity of values
        QtGui.QDialog.accept(self)

    def reject(self):
        '''Callback function when dialog is rejected (click Cancel)'''
        self._wasOk = False
        QtGui.QDialog.reject(self)

    def wasOk(self):
        return self._wasOk

    def setData(self, RMaj, RMin, Centerx, Centery, Centerz, VectXx,VectXy,VectXz, VectYx, VectYy,VectYz):
        self.txtRMaj.setText(str(RMaj))
        self.txtRMin.setText(str(RMin))
        self.txtCentery.setText(str(Centery))
        self.txtCenterx.setText(str(Centerx))
        self.txtCenterz.setText(str(Centerz))
        self.txtVectXx.setText(str(VectXx))
        self.txtVectXy.setText(str(VectXy))
        self.txtVectXz.setText(str(VectXz))
        self.txtVectYx.setText(str(VectYx))
        self.txtVectYy.setText(str(VectYy))
        self.txtVectYz.setText(str(VectYz))

    def getData(self):
        try:
            RMaj=eval(str(self.txtRMaj.text()))
            RMin=eval(str(self.txtRMin.text()))
            Centerx=eval(str(self.txtCenterx.text()))
            Centery=eval(str(self.txtCentery.text()))
            Centerz=eval(str(self.txtCenterz.text()))

            VectXx=eval(str(self.txtVectXx.text()))
            VectXy=eval(str(self.txtVectXy.text()))
            VectXz=eval(str(self.txtVectXz.text()))


            VectYx=eval(str(self.txtVectYx.text()))
            VectYy=eval(str(self.txtVectYy.text()))
            VectYz=eval(str(self.txtVectYz.text()))

        except:
            print "Definition problem"

        return RMaj, RMin, Centerx, Centery, Centerz, VectXx,VectXy,VectXz, VectYx, VectYy, VectYz


class FissDialogHP(FissDialog_UIHP):

    def setupUiHP(self):
        FissDialog_UIHP.setupUiHP(self)
        self.handleAcceptWith(self.accept)
        self.handleRejectWith(self.reject)

    def handleAcceptWith(self,callbackFunction):
        """This defines the function to be connected to the signal 'accepted()' (click on Ok)"""
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), callbackFunction)

    def handleRejectWith(self,callbackFunction):
        """This defines the function to be connected to the signal 'rejected()' (click on Cancel)"""
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), callbackFunction)

    def handleApplyWith(self,callbackFunction):
        """This defines the function to be connected to the signal 'apply()' (click on Apply)"""
        button = self.buttonBox.button(QtGui.QDialogButtonBox.Apply)        
        QtCore.QObject.connect(button, QtCore.SIGNAL("clicked()"), callbackFunction);

    def accept(self):
        '''Callback function when dialog is accepted (click Ok)'''
        self._wasOk = True
        # We should test here the validity of values
        QtGui.QDialog.accept(self)

    def reject(self):
        '''Callback function when dialog is rejected (click Cancel)'''
        self._wasOk = False
        QtGui.QDialog.reject(self)

    def wasOk(self):
        return self._wasOk

    def setData(self, PFONx, PFONy, PFONz, NORMx, NORMy, NORMz,DTANx,DTANy, DTANz):
        self.txtPFONx.setText(str(PFONx))
        self.txtPFONy.setText(str(PFONy))
        self.txtPFONz.setText(str(PFONz))
        self.txtNORMx.setText(str(NORMx))
        self.txtNORMy.setText(str(NORMy))
        self.txtNORMz.setText(str(NORMz))
        self.txtDTANx.setText(str(DTANx))
        self.txtDTANy.setText(str(DTANy))
        self.txtDTANz.setText(str(DTANz))

    def getData(self):
        try:
            PFONx=eval(str(self.txtPFONx.text()))
            PFONy=eval(str(self.txtPFONy.text()))
            PFONz=eval(str(self.txtPFONz.text()))
            NORMx=eval(str(self.txtNORMx.text()))
            NORMy=eval(str(self.txtNORMy.text()))
            NORMz=eval(str(self.txtNORMz.text()))
            DTANx=eval(str(self.txtDTANx.text()))
            DTANy=eval(str(self.txtDTANy.text()))
            DTANz=eval(str(self.txtDTANz.text()))
        except:
            print "Definition problem"

        return PFONx, PFONy, PFONz, NORMx, NORMy, NORMz,DTANx,DTANy, DTANz


class FissDialogSG(FissDialog_UISG):

    def setupUiSG(self):
        FissDialog_UISG.setupUiSG(self)
        self.handleAcceptWith(self.accept)
        self.handleRejectWith(self.reject)

    def handleAcceptWith(self,callbackFunction):
        """This defines the function to be connected to the signal 'accepted()' (click on Ok)"""
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"),callbackFunction)

    def handleRejectWith(self,callbackFunction):
        """This defines the function to be connected to the signal 'rejected()' (click on Cancel)"""
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), callbackFunction)

    def handleApplyWith(self,callbackFunction):
        """This defines the function to be connected to the signal 'apply()' (click on Apply)"""
        button = self.buttonBox.button(QtGui.QDialogButtonBox.Apply)
        QtCore.QObject.connect(button, QtCore.SIGNAL("clicked()"), callbackFunction);

    def accept(self):
        '''Callback function when dialog is accepted (click Ok)'''
        self._wasOk = True
        # We should test here the validity of values
        QtGui.QDialog.accept(self)

    def reject(self):
        '''Callback function when dialog is rejected (click Cancel)'''
        self._wasOk = False
        QtGui.QDialog.reject(self)

    def wasOk(self):
        return self._wasOk
    
    def setData(self, PFONOx, PFONOy, PFONOz,PFONEx, PFONEy, PFONEz):
        self.txtPFONOx.setText(str(PFONOx))
        self.txtPFONOy.setText(str(PFONOy))
        self.txtPFONOz.setText(str(PFONOz))
        self.txtPFONEx.setText(str(PFONEx))
        self.txtPFONEy.setText(str(PFONEy))
        self.txtPFONEz.setText(str(PFONEz))

    def getData(self):
        try:
            PFONOx=eval(str(self.txtPFONOx.text()))
            PFONOy=eval(str(self.txtPFONOy.text()))
            PFONOz=eval(str(self.txtPFONOz.text()))
            PFONEx=eval(str(self.txtPFONEx.text()))
            PFONEy=eval(str(self.txtPFONEy.text()))
            PFONEz=eval(str(self.txtPFONEz.text()))
        except:
            print "Definition problem"
        return PFONOx, PFONOy, PFONOz, PFONEx, PFONEy, PFONEz
        
    def SaveData(self):
        if  self.accept :
            PFONOx=eval(str(self.txtPFONOx.text()))
            PFONOy=eval(str(self.txtPFONOy.text()))
            PFONOz=eval(str(self.txtPFONOz.text()))
            PFONEx=eval(str(self.txtPFONEx.text()))
            PFONEy=eval(str(self.txtPFONEy.text()))
            PFONEz=eval(str(self.txtPFONEz.text()))
            return PFONOx, PFONOy, PFONOz, PFONEx, PFONEy, PFONEz


class FissDialogHL(FissDialog_UIHL):

    def setupUiHL(self):
        FissDialog_UIHL.setupUiHL(self)
        self.handleAcceptWith(self.accept)
        self.handleRejectWith(self.reject)

    def handleAcceptWith(self,callbackFunction):
        """This defines the function to be connected to the signal 'accepted()' (click on Ok)"""
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), callbackFunction)
        

    def handleRejectWith(self,callbackFunction):
        """This defines the function to be connected to the signal 'rejected()' (click on Cancel)"""
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), callbackFunction)

    def handleApplyWith(self,callbackFunction):
        """This defines the function to be connected to the signal 'apply()' (click on Apply)"""
        button = self.buttonBox.button(QtGui.QDialogButtonBox.Apply)        
        QtCore.QObject.connect(button, QtCore.SIGNAL("clicked()"), callbackFunction);

    def accept(self):
        '''Callback function when dialog is accepted (click Ok)'''
        self._wasOk = True
        # We should test here the validity of values
        QtGui.QDialog.accept(self)

    def reject(self):
        '''Callback function when dialog is rejected (click Cancel)'''
        self._wasOk = False
        QtGui.QDialog.reject(self)

    def wasOk(self):
        return self._wasOk
    
    def setData(self, PFONx, PFONy, PFONz,DTANx, DTANy, DTANz):
        self.txtPFONx.setText(str(PFONx))
        self.txtPFONy.setText(str(PFONy))
        self.txtPFONz.setText(str(PFONz))
        self.txtDTANx.setText(str(DTANx))
        self.txtDTANy.setText(str(DTANy))
        self.txtDTANz.setText(str(DTANz))

    def getData(self):
        try:
            PFONx=eval(str(self.txtPFONx.text()))
            PFONy=eval(str(self.txtPFONy.text()))
            PFONz=eval(str(self.txtPFONz.text()))
            DTANx=eval(str(self.txtDTANx.text()))
            DTANy=eval(str(self.txtDTANy.text()))
            DTANz=eval(str(self.txtDTANz.text()))
        except:
            print "Definition problem"
        return PFONx, PFONy, PFONz, DTANx, DTANy, DTANz


class FissDialogOnTopWithApply(FissDialog):
    
    def setupUi(self):
        """
        This setupUi adds a button 'Apply' to execute a processing
        tasks (ex: preview), and set a flag that keeps the dialog on
        top of all windows.
        """
        FissDialog.setupUi(self)
        # Add a button "Apply"
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|
                                          QtGui.QDialogButtonBox.Apply|
                                          QtGui.QDialogButtonBox.Ok)

        # Keep the dialog on top of the windows
        self.setWindowFlags(self.windowFlags() |
                            QtCore.Qt.WindowStaysOnTopHint)
   

class FissDialogOnTopWithApplyHP(FissDialogHP):
    
    def setupUiHP(self):
        """
        This setupUi adds a button 'Apply' to execute a processing
        tasks (ex: preview), and set a flag that keeps the dialog on
        top of all windows.
        """
        FissDialogHP.setupUiHP(self)
        # Add a button "Apply"
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|
                                          QtGui.QDialogButtonBox.Apply|
                                          QtGui.QDialogButtonBox.Ok)

        # Keep the dialog on top of the windows
        self.setWindowFlags(self.windowFlags() |
                            QtCore.Qt.WindowStaysOnTopHint)


class FissDialogOnTopWithApplySG(FissDialogSG):
    
    def setupUiSG(self):
        """
        This setupUi adds a button 'Apply' to execute a processing
        tasks (ex: preview), and set a flag that keeps the dialog on
        top of all windows.
        """
        FissDialogSG.setupUiSG(self)
        # Add a button "Apply"
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|
                                          QtGui.QDialogButtonBox.Apply|
                                          QtGui.QDialogButtonBox.Ok)

        # Keep the dialog on top of the windows
        self.setWindowFlags(self.windowFlags() |
                            QtCore.Qt.WindowStaysOnTopHint)


class FissDialogOnTopWithApplyHL(FissDialogHL):

    def setupUiHL(self):
        """
        This setupUi adds a button 'Apply' to execute a processing
        tasks (ex: preview), and set a flag that keeps the dialog on
        top of all windows.
        """
        FissDialogHL.setupUiHL(self)
        # Add a button "Apply"
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|
                                          QtGui.QDialogButtonBox.Apply|
                                          QtGui.QDialogButtonBox.Ok)

        # Keep the dialog on top of the windows
        self.setWindowFlags(self.windowFlags() |
                            QtCore.Qt.WindowStaysOnTopHint)


#
# ======================================================================
# Unit test
# ======================================================================
#
def TEST_getData_synchrone():
    """This use case illustrates the MVC pattern on this simple dialog example""" 
    fissdialog = FissDialog()
    fissdialog.setData(10,50,3, 1, 1)
    fissdialog.exec_()
    if fissdialog.wasOk():
        rmaj, rmin, centerx,centery,centerz, vectXx,  vectXy, vectXz,vectYx,  vectYy, vectYz= fissedialog.getData()
        print rmaj, rmin, centerx,centery,centerz, vectXx,  vectXy, vectXz,vectYx,  vectYy, vectYz

def main( args ):
    a = QtGui.QApplication(sys.argv)
    TEST_getData_synchrone()
    sys.exit(0)

if __name__=="__main__":
    main(sys.argv)

