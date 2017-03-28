# -*- coding: utf-8 -*-

import xalome

def deletePreviewShape(LIST_SHAPE_NAME,activeStudy, previewShapeEntry,DEFAULT_SHAPE_NAME):
    """This delete the shape currently being displayed as a preview"""
    for i in range(len(LIST_SHAPE_NAME)):
        if LIST_SHAPE_NAME[i] == DEFAULT_SHAPE_NAME:
            xalome.deleteShape(activeStudy, previewShapeEntry[i])
            previewShapeEntry[i] = None
