# -*- coding: utf-8 -*-
"""External graphical tools used from Salomé.
Allow to run Eficas and list groups on an Aster command file
with Eficas functionalities.
"""


def run_eficas(com_fname=None):
    """Run the Eficas editor without an optional command file"""
    import eficasSalome as ES
    ES.logger.hideDebug()
    ES.runEficas(code='ASTER', fichier=com_fname)


def list_groups_with_eficas(com_fname, version):
    """List groups found on an Aster command file"""
    from Editeur import session
    from InterfaceQT4 import qtEficas
    from InterfaceQT4 import ssIhm
    from InterfaceQT4 import readercata
    from InterfaceQT4 import editor

    code = "ASTER"
    session.parse([''])
    app = qtEficas.Appli(code, salome=1)
    parent = ssIhm.QWParentSSIhm(code, app, version)
    app.readercata = readercata.READERCATA(parent, app)
    jdc_editor = editor.JDCEditor(app, com_fname)
    all_grps = jdc_editor.cherche_Groupes()

    # Retablissement du module math sans surcharge d'eficas
    #from Extensions.param2 import originalMath
    #originalMath.toOriginal()
    #
    return all_grps


