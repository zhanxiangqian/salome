# encoding: utf-8

import fissbuilder
import fissdialog
import xalome
from common import deletePreviewShape
import salome

dialogWithApply = fissdialog.FissDialogOnTopWithApplySG()
dialogWithApply.setData(fissbuilder.DEFAULT_PFONOX,
                        fissbuilder.DEFAULT_PFONOY,
                        fissbuilder.DEFAULT_PFONOZ,
                        fissbuilder.DEFAULT_PFONEX,
                        fissbuilder.DEFAULT_PFONEY,
                        fissbuilder.DEFAULT_PFONEZ, )

activeStudy = salome.myStudy
previewShapeEntry = []
LIST_SHAPE_NAME = ["Fiss"]
DEFAULT_FOLDER_NAME="Crack Wizard"
PREVIEW_SHAPE_NAME="preview"
DEFAULT_SHAPE_NAME= "Fiss"
DEFAULT_CRACK_TYPE="Type" 

def acceptCallback():
    """Action called when click on Ok"""
    for i in range(len(LIST_SHAPE_NAME)) :
        if LIST_SHAPE_NAME[i] == DEFAULT_SHAPE_NAME:
            dialogWithApply.accept()
            if previewShapeEntry[i] is not None:
                deletePreviewShape(LIST_SHAPE_NAME,activeStudy, previewShapeEntry,DEFAULT_SHAPE_NAME)

            PFONOx, PFONOy, PFONOz,PFONEx, PFONEy, PFONEz = dialogWithApply.getData()
            shape = fissbuilder.createGeometrySegment(activeStudy,PFONOx, PFONOy, PFONOz,PFONEx, PFONEy, PFONEz )
            previewShapeEntry[i] = xalome.addToStudy(activeStudy, shape, DEFAULT_CRACK_TYPE +" : "+ DEFAULT_SHAPE_NAME, DEFAULT_FOLDER_NAME)
            xalome.displayShape(previewShapeEntry[i])
            LIST = [ PFONOx, PFONOy, PFONOz,  PFONEx, PFONEy, PFONEz]

def rejectCallback():
    """Action called when click on Cancel"""
    for i in range(len(LIST_SHAPE_NAME)) :
        if LIST_SHAPE_NAME[i] == DEFAULT_SHAPE_NAME:
            dialogWithApply.reject()
            if previewShapeEntry[i] is not None:
                deletePreviewShape(LIST_SHAPE_NAME,activeStudy, previewShapeEntry,DEFAULT_SHAPE_NAME)

import SALOMEDS
PREVIEW_COLOR=SALOMEDS.Color(1,0.6,1) # pink

def applyCallback():
    """Action called when click on Apply"""
    for i in range(len(LIST_SHAPE_NAME)) :
        if LIST_SHAPE_NAME[i] == DEFAULT_SHAPE_NAME:

            # We first have to destroy the currently displayed preview shape.
            if previewShapeEntry[i] is not None:
                deletePreviewShape(LIST_SHAPE_NAME,activeStudy, previewShapeEntry,DEFAULT_SHAPE_NAME)

            # Then we can create the new shape with the new parameter values
            PFONOx, PFONOy, PFONOz,PFONEx, PFONEy, PFONEz = dialogWithApply.getData()
            shape = fissbuilder.createGeometrySegment(activeStudy,PFONOx, PFONOy, PFONOz,PFONEx, PFONEy, PFONEz )
            # We apply a specific color on the shape for the preview state
            shape.SetColor(PREVIEW_COLOR)
            previewShapeEntry[i] = xalome.addToStudy(activeStudy, shape, PREVIEW_SHAPE_NAME, DEFAULT_FOLDER_NAME )
            xalome.displayShape(previewShapeEntry[i])

# Connection of callback functions to the dialog button click signals

def RECUP(d_shape_name,l_shape_name, d_crack_type):
    global DEFAULT_SHAPE_NAME, DEFAULT_CRACK_TYPE, LIST_SHAPE_NAME
    DEFAULT_SHAPE_NAME= d_shape_name
    DEFAULT_CRACK_TYPE = d_crack_type
    LIST_SHAPE_NAME = l_shape_name
    for i in range(len(l_shape_name)) :
        previewShapeEntry.append(None)

