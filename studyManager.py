# -*- coding: iso-8859-1 -*-
#
#  Copyright (C) 2007	 EDF R&D
# 
#    This file is part of PAL_SRC.
#
#    PAL_SRC is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    PAL_SRC is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with PAL_SRC; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
import os
import re
import string

from salome.kernel.logger import ExtLogger
logger=ExtLogger("PAL_SRC.salome.studyManager.py")

import salome

# IDL
import SALOMEDS
import GEOM
import SMESH
import VISU
                



# -----------------------------------------------------------------------------
#
#                           GENERALITE
#
# -----------------------------------------------------------------------------

# Nom des composants SALOME dans l'arbre d'étude ( ce que voit l'utilisateur 
# dans l'arbre d'étude )  
SMesh   = "Mesh"
SGeom   = "Geometry"
SVisu   = "Post-Pro"
SAster  = "Aster"
SEficas = "Eficas"

SIcon = {
    SAster  :"ICON_ASTER",
    SEficas :"ICON_EFICAS"
}

# Nom interne des composants ( engine ) SALOME
engineNames = {            
    SMesh:  "SMESH",
    SGeom:  "GEOM",
    SVisu:  "VISU",
    SAster: "ASTER",
    SEficas:"EFICAS"    
}

# Nom des container associé aux composant (engine )
containerNames = {            
    SMesh:  "FactoryServer",
    SGeom:  "FactoryServer",
    SVisu:  "FactoryServer",
    SAster: "FactoryServerPy",
    SEficas:"FactoryServerPy"
}    


# Liste valeurs de l'atribut 'AttributeFileType': permet de typer un objet de 
# l'arbre d'étude. L'attribut 'AttributeExternalFileDef' est généralement présent
# pour stocker la valeur associée.
ASTERCASE                   = "ASTERCASE"
ASTER_FILE_FOLDER           = "ASTER_FILE_FOLDER"
OPENTURNS_FILE_FOLDER       = "OPENTURNS_FILE_FOLDER"
FICHIER_EFICAS_ASTER        = "FICHIER_EFICAS_ASTER"
FICHIER_EFICAS_HOMARD       = "FICHIER_EFICAS_HOMARD"
FICHIER_EFICAS_HOMARD_CONF  = "FICHIER_EFICAS_HOMARD_CONF"
FICHIER_EFICAS_OPENTURNS    = "FICHIER_EFICAS_OPENTURNS"
FICHIERMED                  = "FICHIERMED"
FICHIER_RESU                = "FICHIER_RESU"
FICHIER_MESS                = "FICHIER_MESS"
FICHIER_OUT                 = "FICHIER_OUT"
FICHIER_RESU_MED            = "FICHIER_RESU_MED"
REPERTOIRE_BASE             = "REPERTOIRE_BASE"
REPERTOIRE_BASE_HDF         = "REPERTOIRE_BASE_HDF"




# -----------------------------------------------------------------------------
#
#                           GEOMETRIE
#
# -----------------------------------------------------------------------------

# Type des objets géométrique SALOME
VERTEX  = "VERTEX"
EDGE    = "EDGE"
WIRE    = "WIRE"    
FACE    = "FACE"
SHELL   = "SHELL"    
SOLID   = "SOLID"
COMPSOLID = "COMPSOLID"
COMPOUND  = "COMPOUND"


# les différents type de vue possible:
OCC_VIEW = 0
VTK_VIEW = 1


# Liste de couleurs pour visualisation
RED   = 255,0,0
GREEN = 0,255,0
BLUE  = 0,0,255

SANDY  = 255,0,128
ORANGE = 255,128,0
PURPLE = 128,0,255

DARK_RED   = 128,0,0
DARK_GREEN = 0,128,0
DARK_BLUE  = 0,0,128

YELLOW = 255,255,0
PINK   = 255,0,255
CYAN   = 0,255,255







# -----------------------------------------------------------------------------
#
#                           MAILLAGE
#
# -----------------------------------------------------------------------------


# Type des groupes d'un maillage SALOME
# ( les valeurs correspondent ici à leurs tag respectifs dans l'arbre ( cf SMESH.hxx ) )
NodeGroups = 11
EdgeGroups = 12
FaceGroups = 13
VolumeGroups = 14

# version des fichiers MED
MED_V2_1 = SMESH.MED_V2_1
MED_V2_2 = SMESH.MED_V2_2


#class SalomeStudy(   salomedsgui.guiDS ):
class SalomeStudy:
    """
    Classe de manipulation de l'arbre d'étude Salome. Cette classe permet à 
    l'utilisateur de manipuler les objets de 'arbre d'étude via leurs 
    identifiants( entry ).
    
    Attention : Par défaut les opérations réalisée par cette classe portent sur 
    une étude courante ( positionnée dans le constructeur ou par la méthode 
    setCurrentStudyID() )
    """    
    def __init__( self, studyID = salome.myStudyId ):        
        #salomedsgui.guiDS.__init__( self  )

        #spécifique gestion étude                
        self._myStudyId      = None
        self._myStudy        = None
        self._myStudyName    = None
        self._myBuilder      = None
        self.setCurrentStudyID( studyID )
        

        # spécifique méthode __getMeshType() :
        self.groupOp    = None
        self.geomEngine = None
        
        #spécifique méthode getRealShapeType
        self.groupIMeasureOp = None
        
        
        # spécifique méthode createMesh() :
        self.smeshEngine = None
        
        # 
        self.visuEngine = None
        
        
        #        
        self.withGUI = False

        
    # --------------------------------------------------------------------------
    #                           MEHTODES PRIVEES
    #
    # --------------------------------------------------------------------------
    def __waitCursor( self ):
        if self.withGUI:
            import qt
            qt.QApplication.setOverrideCursor( qt.QCursor.waitCursor )

    def __restoreCursor( self ):
        if self.withGUI:
            import qt
            qt.QApplication.restoreOverrideCursor()
    
    def __getCORBAObject( self,  entry ):         
        """
        Retourne l'objet CORBA correspondant à son identifiant ( entry ) dans 
        l'arbre d'étude.
        
        @type   entry : string
        @param  entry : objet Corba 
        
        @rtype  :  objet CORBA
        @return :  l'objet CORBA,   None si erreur.
        """
        object = None
        
        self.__waitCursor()
                        
        try:            
            mySO = self._myStudy.FindObjectID( entry )            
            if mySO:            
                object = mySO.GetObject()
                
                if not object: # l'objet n'a pas encore chargé
                    path          = self._myStudy.GetObjectPath( mySO )# recherche du nom du composant
                    sComponentName = ( path.split('/')[1] ).strip()

                    if sComponentName == SMesh:
                        strContainer, strComponentName = "FactoryServer", "SMESH"
                    elif sComponentName == SGeom:
                        strContainer, strComponentName = "FactoryServer", "GEOM"
                    elif sComponentName == SVisu:
                        strContainer, strComponentName = "FactoryServer", "VISU"
                    elif sComponentName == SAster:
                        strContainer, strComponentName = "FactoryServerPy", "ASTER"
                    else :
                        logger.debug('>>>>CS_Pbruno SalomeStudy.__getCORBAObject chargement du composant  %s non implémenté ' %sComponentName)
                        raise 'Erreur'                        
                                                                    
                    myComponent = salome.lcc.FindOrLoadComponent( strContainer, strComponentName )
                    SCom        = self._myStudy.FindComponent( strComponentName )
                    self._myBuilder.LoadWith( SCom , myComponent  )
                    object      = mySO.GetObject()                    
                    
        except:            
            logger.debug( '>>>>CS_Pbruno SalomeStudy.__getCORBAObject erreur recupération  objet corba ( entry = %s ) ' %entry )
            object = None
            
        self.__restoreCursor()
            
        return object
        
        
    def __getEntry( self, corbaObject ):
        """
        Retourne l'identifiant ( entry ) ds l'arbre d'étude de l'objet CORBA 
        passé en paramètre.
                
        @type     corbaObject : objet Corba
        @param  corbaObject   : objet Corba 
        
        @rtype  :  string
        @return :  identifiant ( entry ),    None si erreur.
        """
        entry        = None
        currentStudy = self._myStudy
                
        if corbaObject:
            ior = salome.orb.object_to_string( corbaObject )
            if ior:
                sObject = currentStudy.FindObjectIOR(  ior )                
                entry   = sObject.GetID()
        return entry
        
        
    def __setAttributeValue( self, sObject, strAttributeName, strAttributeValue ):
        """
        Fixe la valeur de l'attribut 'strAttributeName' de l'item sObject à la valeur strAttributeValue.       
        """        
        attrTypes = {
            "AttributeName":            SALOMEDS.AttributeName,
            "AttributeFileType":        SALOMEDS.AttributeFileType,
            "AttributeExternalFileDef": SALOMEDS.AttributeExternalFileDef,
            "AttributeComment":         SALOMEDS.AttributeComment,
            "AttributePixMap":          SALOMEDS.AttributePixMap
        }
            
        attrType = attrTypes[ strAttributeName ]
        A        = self._myBuilder.FindOrCreateAttribute( sObject, strAttributeName )
        attr     = A._narrow( attrType )
        if  strAttributeName == "AttributePixMap":
            attr.SetPixMap( strAttributeValue )       
        else:
            attr.SetValue( strAttributeValue )
        
        
        
        
        
    def __getAttributeValue( self, sObject, strAttributeName ):
        """
        Retourne la valeur de l'attribut 'strAttributeName' de l'item sObject        
        ( None si pas d'attribut).
        """        
        value      = None
        mySO       = None
        
        boo, RefSO = sObject.ReferencedObject()        
        if boo:
            mySO = RefSO
        else:
            mySO = sObject
            
        boo, attr =  self._myBuilder.FindAttribute( mySO, strAttributeName )        
        if boo:
            value = attr.Value()
            
        return value

        
    def __getMeshType( self, shapeEntry ):
        """
        Determination du type de maille en fonction de la géométrie pour les conditions aux limites.
        
        @type     shapeEntry : string
        @param  shapeEntry : identifiant de l'objet géométrique
        
        @rtype:   SMESH::ElementType ( voir SMESH_Mesh.idl )
        @return:  type de maillage, None si erreur.
        """ 
        result = None
        
        self.__waitCursor()
        
        try:        
            anObject = self.__getCORBAObject(  shapeEntry )
            shape    = anObject._narrow( GEOM.GEOM_Object )
            
            if shape: #Ok, c'est bien un objet géométrique
                tgeo = str( shape.GetShapeType() )
                
                meshTypeStr = {
                    "VERTEX" :         SMESH.NODE,
                    "EDGE":            SMESH.EDGE,
                    "WIRE":            SMESH.EDGE, 
                    "FACE":            SMESH.FACE,
                    "SHELL":           SMESH.FACE, 
                    "SOLID":           SMESH.VOLUME,
                    "COMPSOLID":       SMESH.VOLUME, 
                    "COMPOUND" :  None
                }
                result = meshTypeStr[ tgeo]
                if result == None:                    
                    if not self.geomEngine:                        
                        self.geomEngine = salome.lcc.FindOrLoadComponent( "FactoryServer", "GEOM" )                        
                    if not self.groupOp:                        
                        self.groupOp  = self.geomEngine.GetIGroupOperations(  salome.myStudyId )                        
                        
                    tgeo = self.groupOp.GetType( shape )
                    meshTypeInt = { #Voir le dictionnnaire ShapeType dans geompy.py pour les correspondances type - numero.
                        7:      SMESH.NODE, 
                        6:      SMESH.EDGE,
                        4:      SMESH.FACE,
                        2:      SMESH.VOLUME
                    }
                    if meshTypeInt.has_key(  int( tgeo ) ):
                        result = meshTypeInt[ tgeo]                    
        except:            
            logger.debug( '>>>>CS_Pbruno SalomeStudy.__getMeshType( shapeEntry  = %s ) ' %shapeEntry )            
            result = None
            
        self.__restoreCursor()            
            
        return result
        
        
    def __getGroupeNames( self, meshEntry, groupType ):
        names = []
                        
        tag = { SMESH.NODE : NodeGroups,
                SMESH.EDGE : EdgeGroups,
                SMESH.FACE : FaceGroups,
                SMESH.VOLUME : VolumeGroups }
        
        groupeEntry = self.getSubObjectID( meshEntry, tag[ groupType ] )
        
        if groupeEntry:
            sGroupe = self._myStudy.FindObjectID( groupeEntry )            
            if sGroupe:
                childIt = self._myStudy.NewChildIterator( sGroupe )                
                childIt.InitEx(0)
                                
                while childIt.More():
                    childSO = childIt.Value()
                    childID = childSO.GetID()
                    groupName = self.getName( childID )
                    names.append( groupName )
                    childIt.Next()
        
        
        return names

                
                
                
                
                
        
        
        
            
        
    # --------------------------------------------------------------------------
    #                               GENERALITE
    #
    #   fonctions de manipulation générale ( porte sur toute l'arbre d'étude )
    #
    # --------------------------------------------------------------------------
    def setCurrentStudyID( self, studyID ):
        """
        Fixe l'étude courante sur laquel vont opérer toutes les fonctions 
        de la classe.        
        """        
        salome.myStudy       = salome.myStudyManager.GetStudyByID( studyID )        
        salome.myStudyId     = studyID        
        salome.myStudyName   = salome.myStudy._get_Name()        
        
        
        self._myStudy       = salome.myStudy        
        self._myStudyId     = salome.myStudyId        
        self._myStudyName   = salome.myStudyName        
        self._myBuilder     = self._myStudy.NewBuilder( )        
        
        """
        print 50*'='
        print 'CS_pbruno setCurrentStudyID self ->', self
        print 'CS_pbruno setCurrentStudyID self._myStudyId->',self._myStudyId
        print 'CS_pbruno setCurrentStudyID self._myStudyName->',self._myStudyName
        print 50*'='
        """        
        
    
    def refresh( self ):        
        """
        Rafraichissement de l'arbre d'étude
        """
        salome.sg.updateObjBrowser(0)
        
        
    def addComponent( self, sComponentName, strIcon = None ):
        """
        Ajoute dans l'arbre d'étude courante, le nom du composant fourni en argument.
                
        @type   sComponentName: string
        @param  sComponentName: nom du composant dans l'arbre d'étude ( liste défini au début de ce fichier )
        
        @type   strIcon: string
        @param  strIcon: nom de l'icon du fichier 
        
        @rtype  :  string
        @return :  identifiant du composant dans l'arbre d'étude, None si erreur
        """
        logger.debug("addComponent: sComponentName = "+str(sComponentName))
        entry = None
        
        self.__waitCursor()        
        try:
            strEngineName    = engineNames[ sComponentName ]
            strContainerName = containerNames[ sComponentName ]            
            father = self._myStudy.FindComponent( strEngineName )

            if father is None:                
                import time
                logger.debug(70*'='+"strContainerName="+str(strContainerName)+" , strEngineName="+str(strEngineName))
                
                import LifeCycleCORBA
                lcc=LifeCycleCORBA.LifeCycleCORBA()
                engine=lcc.FindOrLoadComponent( strContainerName, strEngineName )
                
                step = 0

                while engine  == None and step < 50:
                    engine = lcc.FindOrLoadComponent( strContainerName, strEngineName )
                    step = step + 1
                    time.sleep(4)                
                father = self._myBuilder.NewComponent( strEngineName )
                
                A1 = self._myBuilder.FindOrCreateAttribute( father, "AttributeName" )
                FName = A1._narrow( SALOMEDS.AttributeName )
                FName.SetValue( sComponentName )
                                                
                if not strIcon and SIcon.has_key( sComponentName ):
                    strIcon = SIcon[ sComponentName ]                    
                if strIcon:
                    anAttr = self._myBuilder.FindOrCreateAttribute(father, "AttributePixMap")
                    AttributePixMap = anAttr._narrow( SALOMEDS.AttributePixMap )
                    AttributePixMap.SetPixMap( strIcon ) #"ICON_OBJBROWSER_Aster" )
                
                self._myBuilder.DefineComponentInstance( father, engine )

            entry = father.GetID()
        except:            
            logger.debug( '>>>>CS_Pbruno SalomeStudy.addComponent( sComponentName= %s )' %( sComponentName ) )            
            entry = None
            
        self.__restoreCursor()
            
        return entry
        
        
    def addItem( self, fatherItemEntry, itemName,
                       itemType = None, itemValue = None, itemComment = None, itemTag = None, itemIcon = None,
                       bDoublonCheck = False ):
        """
        Ajoute un élément dans l'arbre d'étude courante.
        
        @type   fatherItemEntry: string
        @param  fatherItemEntry: identifiant de l'élément père de l'objet qu'on souhaite ajouter.
                
        @type   itemName: string
        @param  itemName: nom de l'item ( attribut 'AttributeName' )
        
        @type   itemType: string
        @param  itemType: ( attribut 'AttributeFileType' )
        
        @type   itemValue: string
        @param  itemValue: ( attribut 'AttributeExternalFileDef' )
        
        @type   itemComment: string
        @param  itemComment: ( attribut 'AttributeComment' )
        
        @type   itemTag: entier
        @param  itemTag: tag 
        
        @rtype  :  string
        @return :  identifiant( entry ) de l'item crée dans l'arbre d'étude, None si erreur
        """        
        entry = None
        try:
            bDoublonFound  = False
            sItem       = None
            sFatherItem = self._myStudy.FindObjectID( fatherItemEntry )
            if itemTag: 
                ok, sItem = sFatherItem.FindSubObject( itemTag )                
                if not ok:                 
                    sItem = self._myBuilder.NewObjectToTag( sFatherItem, itemTag )
                    
            else:
                # recherche doublon
                if bDoublonCheck:
                    childIt = self._myStudy.NewChildIterator( sFatherItem )                
                    childIt.InitEx(0)
                                    
                    while childIt.More():
                        childSO = childIt.Value()
                        childID = childSO.GetID()                    
                        name          = self.__getAttributeValue( childSO, "AttributeName" )
                        fileType      = self.__getAttributeValue( childSO, "AttributeFileType" )
                        fileTypeValue = self.__getAttributeValue( childSO, "AttributeExternalFileDef" )
                        comment       = self.__getAttributeValue( childSO, "AttributeComment" )
                        print '( childID =%s, name=%s, fileType=%s, fileTypeValue=%s, comment =%s)' %( childID, name, fileType, fileTypeValue, comment )
                        if ( name, fileType, fileTypeValue, comment ) == ( itemName, itemType, itemValue, itemComment ):
                            bDoublonFound = True
                            sItem = childSO
                            break
                        childIt.Next()
                                    
                if not sItem:
                    sItem = self._myBuilder.NewObject( sFatherItem )                    
                
            if sItem and not bDoublonFound:
                self.__setAttributeValue( sItem, "AttributeName", str( itemName ) )
                if itemType:
                    self.__setAttributeValue( sItem, "AttributeFileType", str( itemType ) )
                if itemValue:
                    self.__setAttributeValue( sItem, "AttributeExternalFileDef", str( itemValue ) )
                if itemComment:
                    self.__setAttributeValue( sItem, "AttributeComment", str( itemComment ) )
                if itemIcon:
                    self.__setAttributeValue( sItem, "AttributePixMap", str( itemIcon ) )
                    
            entry= sItem.GetID()                                        
            
        except:            
            logger.debug( '>>>>CS_Pbruno SalomeStudy.addItem( fatherItemEntry= %s )' %( fatherItemEntry ) )
            entry = None
                
        return entry
    
            
    def setItem( self, itemEntry, itemName = None, itemType = None, itemValue = None, itemComment = None, itemIcon = None ):
        """
        Met à jours  un élément dans l'arbre d'étude courante.
        
        @type   itemEntry: string
        @param  itemEntry: identifiant de l'élément
                
        @type   itemName: string
        @param  itemName: nom de l'item ( attribut 'AttributeName' )
        
        @type   itemType: string
        @param  itemType: ( attribut 'AttributeFileType' )
        
        @type   itemValue: string
        @param  itemValue: ( attribut 'AttributeExternalFileDef' )
        
        @type   itemComment: string
        @param  itemComment: ( attribut 'AttributeComment' )
        
        @type   itemTag: entier
        @param  itemTag: tag 
        
        @rtype  :  boolean
        @return :  True si ok, False sinon
        """
        ok = False
        try:
            print 'CS_pbruno setItem'
            sItem = self._myStudy.FindObjectID( itemEntry )
            if sItem:
                print 'CS_pbruno if sItem'
                print 'CS_pbruno itemType ',itemType 
                print 'CS_pbruno itemValue ',itemValue
                print 'CS_pbruno itemIcon ',itemIcon 
                
                if itemName:                    
                    self.__setAttributeValue( sItem, "AttributeName", itemName )
                if itemType:
                    self.__setAttributeValue( sItem, "AttributeFileType", itemType )                            
                if itemValue:
                    self.__setAttributeValue( sItem, "AttributeExternalFileDef", itemValue )                
                if itemComment:
                    self.__setAttributeValue( sItem, "AttributeComment", itemComment )
                if itemIcon:
                    self.__setAttributeValue( sItem, "AttributePixMap", itemIcon )
                ok = True            
        except:            
            logger.debug( '>>>>CS_Pbruno SalomeStudy.setItem( itemEntry= %s )' %( itemEntry ) )
            ok = False
                
        return ok
        
        
    def removeItem( self, itemEntry, withChildren = False ):
        """
        Retire  un élément de l'arbre 
        
        note: CS_pbruno efface apparemment 'visuellement' l'item mais celui-ci subsiste dans l'étude
        
        @type   itemEntry: string
        @param  itemEntry: identifiant de l'élément
        
        @type   withChildren: boolean
        @param  withChildren: option ( True : retire les enfants également ) 
                
        @rtype  :  boolean
        @return :  True si ok, False sinon
        """
        ok = False
        try:
            sItem = self._myStudy.FindObjectID( itemEntry )
            if sItem:
                if withChildren: 
                    self._myBuilder.RemoveObjectWithChildren( sItem )
                else:
                    self._myBuilder.RemoveObject(sItem )
                ok = True
        except:            
            logger.debug( '>>>>CS_Pbruno SalomeStudy.removeItem( itemEntry= %s )' %( itemEntry ) )
            ok = False
                
        return ok    
        
        
        
    def setName( self, entry, name ):
        """
        Fixe le nom( la valeur de l'attribut 'AttributeName' ) d'un objet de l'arbre d'étude
        désigné par son identifiant( entry )
                
        @type   entry: string
        @param  entry: identifiant de l'objet dans l'arbre d'étude
        
        @type   name: string
        @param  name: nom à attribuer
        
        @rtype  :  boolean
        @return :  True si Ok, False sinon, None si erreur
        """
        result = False
        try:            
            sItem = self._myStudy.FindObjectID( entry )
            self.__setAttributeValue( sItem, "AttributeName", name )
            result = True            
        except:            
            logger.debug( '>>>>CS_Pbruno SalomeStudy.setName ( entry = %s, name = %s )' %( entry, name ) )            
            result = None
                        
        return result
        
        
        
    def getName( self, entry ):
        """
        Retourne le nom( 'AttributeName' ) d'un objet de l'arbre d'étude
        désigné par son identifiant( entry )
                
        @type   entry: string
        @param  entry: identifiant de l'objet dans l'arbre d'étude
        
        @rtype  :  string
        @return :  le nom, None si erreur.
        """
        name = None
        try:            
            sObject = self._myStudy.FindObjectID( entry )
            name = self.__getAttributeValue( sObject, "AttributeName" )
        except:            
            logger.debug( '>>>>CS_Pbruno SalomeStudy.getName( entry = %s)' %( entry ) )            
            name = None
        return name
    
            
    def getString( self, entry ):
        """
        Retourne le nom( 'AttributeString' ) d'un objet de l'arbre d'étude
        désigné par son identifiant( entry )
                
        @type   entry: string
        @param  entry: identifiant de l'objet dans l'arbre d'étude
        
        @rtype  :  string
        @return :  le nom, None si erreur.
        """
        name = None
        try:            
            sObject = self._myStudy.FindObjectID( entry )
            name = self.__getAttributeValue( sObject, "AttributeString" )
        except:            
            logger.debug( '>>>>CS_Pbruno SalomeStudy.getString( entry = %s)' %( entry ) )            
            name = None
        return name
                
    
    def getTypeAndValue( self, entry ):
        """
        Retourne le type( 'AttributeFileType' ) et la valeur ( 'AttributeExternalFileDef' )
        de l'objet de l'arbre d'étude désigné par son identifiant( entry ).
                        
        @type   entry: string
        @param  entry: identifiant de l'objet dans l'arbre d'étude
        
        @rtype  :  string, string
        @return :  le nom, ( None, None ) si erreur.
        """
        result = None, None        
        try:                     
            sObject      = self._myStudy.FindObjectID( entry )
            sObjectType  = self.__getAttributeValue( sObject, "AttributeFileType" )
            sObjectValue = self.__getAttributeValue( sObject, "AttributeExternalFileDef" )
            result = sObjectType, sObjectValue
        except:            
            logger.debug( '>>>>CS_Pbruno SalomeStudy.getTypeAndValue( entry = %s)' %( entry ) )            
            result= None, None
        return result
        
        
    def getComment( self, entry ):
        """
        Retourne la valeur du commentaire ( attribut 'AttributeComment' )
        de l'objet de l'arbre d'étude désigné par son identifiant( entry ).
                        
        @type   entry: string
        @param  entry: identifiant de l'objet dans l'arbre d'étude AttributeComment
        
        @rtype  :  string
        @return :  valeur du commentaire. '' si pas d'attribut . None si erreur
        """
        value = ''
        try:
            sObject = self._myStudy.FindObjectID( entry )
            value   = self.__getAttributeValue( sObject, "AttributeComment" )
            if not value:
                value = ''
        except:
            logger.debug( '>>>>CS_Pbruno SalomeStudy.getComment( entry = %s)' %( entry ) )
            value = None
        return value
        


    def getEntriesFromName( self, sComponentName, objectName ):
        """
        Retourne la liste des identifiants ( entries ) des objets de nom objectName du composant sComponentName
                
        @type   sComponentName: string
        @param  sComponentName: nom du composant Salome dans l'arbre d'étude
        
        @type   objectName: string
        @param  objectName: nom de l'objet 
        
        @rtype  :  liste
        @return :  la liste,  None si erreur
        """
        entries = []
        try:
            nom = {            
                SMesh:  "SMESH",
                SGeom:  "GEOM",
                SVisu:  "VISU",
                SAster: "ASTER"            
            }
            componentName = nom[ sComponentName ]            
            listSO  = self._myStudy.FindObjectByName( objectName, componentName )            
            for SObjet in listSO :
                entry = SObjet.GetID()
                entries.append( entry )                
                
        except:            
            logger.debug( '>>>>CS_Pbruno SalomeStudy.getEntriesFromName( sComponentName= %s, objectName = %s )' %( sComponentName, objectName ) )
            entries = None
            
        return entries
        
        
    def hasName( self, sComponentName, objectName ):
        """
        Vérifie si dans l'arbre d'étude le commposant de nom sComponentName
        possède un objet de nom objectName.
                
        @type   sComponentName: string
        @param  sComponentName: nom du composant Salome
        
        @type   objectName: string
        @param  objectName: nom de l'objet 
        
        @rtype  :  boolean
        @return :  True si Ok, False sinon,  None si erreur
        """
        result = False
        try:
            nom = {            
                SMesh:  "SMESH",
                SGeom:  "GEOM",
                SVisu:  "VISU",
                SAster: "ASTER"            
            }
            componentName = nom[ sComponentName ]            
            SObjects = self._myStudy.FindObjectByName( objectName, componentName )
            if len( SObjects ) > 0:
                result = True            
        except:            
            logger.debug( '>>>>CS_Pbruno SalomeStudy.hasName( sComponentName= %s, objectName = %s )' %( sComponentName, objectName ) )
            result = None
            
        return result
        
        
    # CS_pbruno à mettre au propre (debut)
    def getSubObjectID( self, fatherEntry, Tag ):
        SubObjectID = None
        fatherSO     = self._myStudy.FindObjectID( fatherEntry )        
        res, SubObject = fatherSO.FindSubObject (  Tag )
        
        print 'CS_pbruno  getSubObjectID res->', res
        
        if res:
            SubObjectID = SubObject.GetID()
        return SubObjectID
    
            
    def getReference(self,objectId):
        mySO = self._myStudy.FindObjectID(objectId)
        boo,RefSO = mySO.ReferencedObject()
        if boo:
            objectId=RefSO.GetID()
        return objectId        

    def addReference(self,fatherId,refId, tag = 1):
        result = False
        try:
        
            father = self._myStudy.FindObjectID(fatherId)
            ref = self._myStudy.FindObjectID(refId)
            res, newObj = father.FindSubObject (  tag )        
            if not res: 
                newObj  = self._myBuilder.NewObjectToTag(  father, tag )
                
            A1              =  self._myBuilder.FindOrCreateAttribute(ref,"AttributeName")
            FName           = A1._narrow(SALOMEDS.AttributeName)
            Name_ref        = FName.Value()        
            path_father , none = string.split(self._myStudy.GetObjectPath(ref),Name_ref)
            path_father , none = os.path.split(path_father)
    
            if self._myStudy.GetObjectPath(father) != path_father :
                self._myBuilder.Addreference(newObj,ref)
            result =True
                
        except:
            t = (fatherId,refId, tag )            
            logger.debug( '>>>>CS_Pbruno SalomeStudy.addReference( fatherId = %s,refId = %s, tag = %s)' %t)
            result = False
            
        return result                
                
            
                    
##        A1 = self._myBuilder.FindOrCreateAttribute( newObj ,"AttributeExternalFileDef")
##        AFileName = A1._narrow(SALOMEDS.AttributeExternalFileDef)
##        AFileName.SetValue(' flksdjfl')        
                
    # CS_pbruno à mettre au propre (fin)        

    # -----------------------------------------------------------------------------
    #
    #                           GEOMETRIE
    #   fonctions de manipulation des objets géométriques dans l'arbre d'étude
    #   ( éléments contenu dans la sous-rubrique "Geometry' )
    #
    # -----------------------------------------------------------------------------
    def getShapeType( self, shapeEntry ):
	"""
	Retourne le type de l'objet géométrique désigné par l'identifiant ( entry ) passé en argument
        Si le type de l'objet est composé ( COMPOUND ) la fonction retournera le type réel ( CS_pbruno nouvelle fonction à crée )
	
	@type   shapeEntry : string
        @param  shapeEntry : identifiant de l'objet géométrique
        
        @rtype:   string
        @return:  type de l'objet géométrique, None si erreur ( l'identifiant ne désigne peut-être pas un objet géométrique )
	
	"""
	tgeo = None
	try:        
            anObject = self.__getCORBAObject(  shapeEntry )
            shape    = anObject._narrow( GEOM.GEOM_Object )
            
            if shape: #Ok, c'est bien un objet géométrique
                tgeo = str( shape.GetShapeType() )
	except:
            logger.debug( '>>>>CS_Pbruno SalomeStudy.getShapeType( shapeEntry = %s ) ' %shapeEntry )
            tgeo = None
           
        return tgeo
                
        
    def getRealShapeType( self, shapeEntry ):
	"""
	Par rapport à la fonction précédente, sii le type de l'objet est composé ( COMPOUND )
        la fonction retournera le type réel ( CS_pbruno à finir )
	
	@type   shapeEntry : string
        @param  shapeEntry : identifiant de l'objet géométrique
        
        @rtype:   string
        @return:  type de l'objet géométrique, None si erreur ( l'identifiant ne désigne peut-être pas un objet géométrique )
	
	"""
	tgeo = None
        
#         self.__waitCursor()
	try:        
            tgeo = self.getShapeType(  shapeEntry )
            if tgeo == COMPOUND:
                tgeo = None
                if not self.geomEngine:                    
                    self.geomEngine = salome.lcc.FindOrLoadComponent( "FactoryServer", "GEOM" )
                    
                    
                if not self.groupIMeasureOp:
                    self.groupIMeasureOp = self.geomEngine.GetIMeasureOperations(  salome.myStudyId )
                    
                shape = self.__getCORBAObject( shapeEntry )
                if shape:
                    strInfo =  self.groupIMeasureOp.WhatIs( shape )
                    
                    dictInfo = {}
                    l = strInfo.split('\n')                    
                    
                    for couple in l:
                        nom, valeur = couple.split(':')
                        dictInfo[ nom.strip() ] = valeur.strip()
                        
                    ordre = [ COMPSOLID, SOLID, SHELL, FACE, WIRE, EDGE, VERTEX ]
                    
                    for t in ordre:                        
                        if dictInfo[ t ] != '0':
                            tgeo = t
                            return tgeo                                                        
	except:            
            logger.debug( '>>>>CS_Pbruno SalomeStudy.getRealShapeType( entry = %s ) ' %shapeEntry  )
            tgeo = None
            
#         self.__restoreCursor()            
           
        return tgeo
    
        
        
    def isShape(  self,  entry ):
        """
        Teste si l'objet désigné par l'identifiant ( entry ) passé en argument 
        est bien un objet géométrique
                
        @type   entry: string
        @param  entry: identifiant de l'objet 
        
        @rtype:   boolean
        @return:  True si Ok, False sinon
        """
        result = False
        try:            
            anObject = self.__getCORBAObject(  entry )
            shape    = anObject._narrow( GEOM.GEOM_Object )            
            if shape:
                result = True                        
        except:            
            logger.debug( '>>>>CS_Pbruno SalomeStudy.isShape( entry = %s ) ' %entry )
            result = False            
        return result        
        
        
    
    def isMainShape(  self,  entry ):
        """
        Teste si l'objet désigné par l'identifiant ( entry ) passé en argument 
        est bien un objet géométrique principal.
                
        @type   entry: string
        @param  entry: identifiant de l'objet 
        
        @rtype:   boolean
        @return:  True si Ok, False sinon
        """
        result = False
        try:            
            anObject = self.__getCORBAObject(  entry )
            shape    = anObject._narrow( GEOM.GEOM_Object )            
            if shape.IsMainShape():
                result = True
        except:            
            logger.debug( '>>>>CS_Pbruno SalomeStudy.isMainShape( entry = %s ) ' %entry )
            result = False            
        return result
        
    
    def getMainShapeEntry(  self,  entry ):
        """
        Retourne l'identifiant de l'objet géométrique principal du sous-objet géométrique désigné par 
        l'identifiant ( entry ) passé en paramètre.
        
        @type   entry: string
        @param  entry: identifiant du sous-objet géométrique
        
        @rtype  :  string 
        @return :  identifiant de  l'objet géométrique principal, None si erreur.
        """
        result = None
        try:
#             if self.isMainShape( entry ):
#                 result = entry
#             else:
#                 anObject = self.__getCORBAObject(  entry )
#                 shape    = anObject._narrow( GEOM.GEOM_Object )
#                 objMain  = shape.GetMainShape()
#                 result   = self.__getEntry( objMain )

            # astuce: une main shape a une entry composé de 4 chiffres
            mainShapeEntry = entry.split(':')[:4]
            
            if len(mainShapeEntry) == 4:
                strMainShapeEntry = '%s:%s:%s:%s'%tuple(mainShapeEntry)
                if self.isMainShape(strMainShapeEntry):
                    result = strMainShapeEntry            
        except:
            logger.debug( '>>>>CS_Pbruno SalomeStudy.getMainShapeEntry( entry = %s ) ' %entry )
            result = None           
        return result
        
        
    def sameMainShape(  self,  shapeEntry1, shapeEntry2 ):
        """
        Détermine si les objets géometriques fournis en argument sont les 
        sous-objets d'une même géométrie principale
                
        @type   shapeEntry1: string
        @param  shapeEntry1: identifiant dans l'arbre d'étude d'un objet géométrique
        
        @type   shapeEntry2: string
        @param  shapeEntry2: identifiant dans l'arbre d'étude d'un objet géométrique
        
        @rtype  :  boolean
        @return :  True si même objet principal, False sinon, None si erreur.
        """
        result = None
        try :
            mainShape1 = self.getMainShapeEntry( shapeEntry1 )
            if mainShape1:
                mainShape2 = self.getMainShapeEntry( shapeEntry2 )
                if mainShape2:
                    result = mainShape1 == mainShape2
        except :
            logger.debug( '>>>>CS_Pbruno SalomeStudy.sameMainShape(  shapeEntry1 = %s , shapeEntry2 = %s )'%( shapeEntry1, shapeEntry2 ) )
            result = None
        return result
        
        
        
    def getSubShapes( self, shapeEntry, isMain = False ):
        """
        Retourne la liste des sous-objets géométrique d'une forme géométrique. 
        
        @type   shapeEntry: string
        @param  shapeEntry: identifiant dans l'arbre d'étude de l'objet géométrique
        
        @type   isMain: boolean
        @param  isMain: si True: on teste si l'objet géométrique est bien un objet principal
        
        @rtype  :  dictionnaire
        @return :  dictionnaire { clé  = identifiant du sous-objets géométrique, valeur = le nom }.  None si erreur.
        """
        subShapes = None
        try:
            if isMain and not self.isMainShape( shapeEntry ):
                return None
                                    
            sMainShape = self._myStudy.FindObjectID( shapeEntry )
            childIt    = self._myStudy.NewChildIterator( sMainShape )
            childIt.InitEx(1)                
            subShapes = {}
            while childIt.More():
                childSO = childIt.Value()
                childID = childSO.GetID()
                print ' CS_pbruno getSubShapes childID ->', childID                    
                childObject = self.__getCORBAObject( childID )
                if childObject:
                    childShape  = childObject._narrow( GEOM.GEOM_Object )
                    if childShape:
                        shapeName = self.getName( childID )
                        #subShapes[ childID ] = childShape.GetName() # marche pas??
                        subShapes[ childID ] = shapeName
                childIt.Next()
        except :
            logger.debug( '>>>>CS_Pbruno SalomeStudy.getSubShapes(  shapeEntry = %s )'%shapeEntry )            
            subShapes = None
           
        return subShapes
    
            
    def displayShapeByEntry( self, shapeEntry, color = None, displayMode = VTK_VIEW  ):
        """
        affiche la forme géométrique désignée par l'identifant fourni en parmamètre
        
        @type   shapeEntry: string
        @param  shapeEntry: identifiant dans l'arbre d'étude de l'objet géométrique
        
        @type   color: tuple ( triplet )
        @param  color: défini les composantes RGB
                
        @rtype  :  boolean
        @return :  True si ok False si erreur
        """
        ok = False
        try:
            anObject = self.__getCORBAObject( shapeEntry )
            if  anObject:
                shape    = anObject._narrow( GEOM.GEOM_Object )
                if shape:                
                    geomgui=salome.ImportComponentGUI("GEOM")            
                    geomgui.createAndDisplayGO( shapeEntry )
                    geomgui.setDisplayMode( shapeEntry, displayMode )
                    #geomgui.setColor(shapeEntry,RedGreenBlue[0],RedGreenBlue[1],RedGreenBlue[2] )
                    if color:
                        geomgui.setColor(shapeEntry, color[0], color[1], color[2]  )
                    ok = True
        except :            
            logger.debug( '>>>>CS_Pbruno SalomeStudy.displayShapeByEntry(  shapeEntry = %s )'%shapeEntry )
            ok = False
           
        return ok
        
    def displayShapeByName( self, shapeName, color = None, displayMode = VTK_VIEW ):
        """
        affiche la forme géométrique désignée par son nom
        
        @type   shapeName : string
        @param  shapeName : nom de la forme géométrique
        
        @type   color: tuple ( triplet )
        @param  color: défini les composantes RGB
                
        @rtype  :  boolean
        @return :  True si ok False si erreur
        """
        ok = False
        try:
            #if not self.geomEngine:
            #    self.geomEngine = salome.lcc.FindOrLoadComponent( "FactoryServer", "GEOM" )
            listSO = self._myStudy.FindObjectByName( shapeName ,"GEOM" )
            print 'CS_pbruno displayShapeByName listSO->', listSO 
	    for SObjet in listSO :
	       entry = SObjet.GetID()
               self.displayShapeByEntry( entry, color, displayMode )
            ok = True
        except :            
            logger.debug( '>>>>CS_Pbruno SalomeStudy.displayShapeByName(  shapeName = %s )'%shapeName )
            ok = False
        return ok    
    
        
        
        
    # -----------------------------------------------------------------------------
    #
    #                           MAILLAGE
    #   fonctions de manipulation des objets maillages  dans l'arbre d'étude
    #   ( éléments contenu dans la sous-rubrique 'Mesh' )
    #
    # -----------------------------------------------------------------------------
    def loadMeshesFromMED(self, medFilePath):
        """        
        Charge un fichier med dans le composant Mesh
        
        @type     medFilePath: string
        @param    medFilePath: chemin du fichier MED 
        
        @rtype:   list
        @return:  la liste des identifiants des mailages contenu dans le fichier MED. None en cas d'erreur
        """
        meshEntries = []
        
        
#         enum DriverMED_ReadStatus // in the order of severity
#         {
#             DRS_OK,
#             DRS_EMPTY,          // a MED file contains no mesh with the given name
#             DRS_WARN_RENUMBER,  // a MED file has overlapped ranges of element numbers,
#                                 // so the numbers from the file are ignored
#             DRS_WARN_SKIP_ELEM, // some elements were skipped due to incorrect file data
#             DRS_FAIL            // general failure (exception etc.)
#         };
        self.__waitCursor()

        try:
            if not self.smeshEngine:
                self.smeshEngine = salome.lcc.FindOrLoadComponent( "FactoryServer", "SMESH" )
            self.smeshEngine.SetCurrentStudy( salome.myStudy )
            
            allMeshes, readStatus= self.smeshEngine.CreateMeshesFromMED(medFilePath)

            if readStatus==SMESH.DRS_OK:
                for aMesh in allMeshes:                
                    meshEntry = self.__getEntry(aMesh)
                    sItem = self._myStudy.FindObjectID(meshEntry)
                    self.__setAttributeValue( sItem, "AttributeFileType", str(FICHIERMED) )
                    self.__setAttributeValue( sItem, "AttributeExternalFileDef", str(medFilePath) )
                    meshEntries.append(meshEntry)
        except:            
            logger.debug('>>>>CS_Pbruno loadMeshesFromMED( medFilePath = %s )'%medFilePath)            
            meshEntries = None
            
        self.__restoreCursor()            
                        
        return meshEntries
        
                
        
    def isMesh( self, entry ):
        """
        Teste si l'identifiant( entry ) fourni en paramètre designe bien un objet maillage
        @type     entry  : string
        @param    entry  : identifiant( entry ) de l'objet dans l'arbre d'étude
        
        @rtype:   boolean
        @return:  True si test ok, False Sinon , None en cas d'erreur
        
        """
        result = None
        
        try:
            anObject = self.__getCORBAObject( entry )
            if anObject:
                mesh     = anObject._narrow( SMESH.SMESH_Mesh  )                        
                if mesh: #Ok, c'est bien un objet maillage
                    result = True
                else:
                    result = False
        except:            
            logger.debug( '>>>>CS_Pbruno SalomeStudy.isMesh( entry = %s ) ' %entry )            
            result = None
                        
        return result
        
    
    def isMeshComputed( self, entry ):
        """
        Teste si l'identifiant( entry ) fourni en paramètre est bien un objet maillage déjà calculé
        @type     entry  : string
        @param    entry  : identifiant( entry ) de l'objet dans l'arbre d'étude
        
        @rtype:   boolean
        @return:  True si test ok, False Sinon , None en cas d'erreur        
        """
        result = None
        
        try:
            anObject = self.__getCORBAObject( entry )
            mesh     = anObject._narrow( SMESH.SMESH_Mesh  )                        
            if mesh: #Ok, c'est bien un objet maillage
                nbNodes = mesh.NbNodes()
                if nbNodes: # si (nbNodes == 0 ) -> maillage pas encore calculé
                    result = True            
        except:              
            logger.debug( '>>>>CS_Pbruno SalomeStudy.isMeshComputed( entry = %s ) ' %entry )            
            result = None
            
        return result
    
                    
    def exportToMED( self, meshEntry, exportedFilePath, medVersion = MED_V2_2 ):
        """
        Exporte l'objet maillage dans un fichier MED
        
        @type     meshEntry  : string
        @param    meshEntry  : identifiant( entry ) de l'objet maillage dans l'arbre d'étude
        
        @type     exportedFilePath  : string
        @param    exportedFilePath  : chemin du fichier MED exporté
        
        @type     medVersion  : 
        @param    medVersion  : numero de version du fichier MED exporté
        
        @rtype:   string 
        @return:  chemin du fichier MED exporté, None en cas d'erreur( maillage non calculé par ex )
        """
        result = None        
        try:
            anObject = self.__getCORBAObject( meshEntry )
            mesh     = anObject._narrow( SMESH.SMESH_Mesh  )                        
            if mesh: #Ok, c'est bien un objet maillage
                nbNodes = mesh.NbNodes()
                if nbNodes: # si (nbNodes == 0 ) -> maillage pas encore calculé
                    if not self.smeshEngine:
                        self.smeshEngine = salome.lcc.FindOrLoadComponent( "FactoryServer", "SMESH" )
                    self.smeshEngine.SetCurrentStudy( salome.myStudy )
                    mesh.ExportToMED( exportedFilePath, False, medVersion ) 
                    result = exportedFilePath
        except:            
            logger.debug( '>>>>CS_Pbruno SalomeStudy.exportToMED( meshEntry= %s ) ' %meshEntry )            
            result = None
            
        return result
    
            
        
    def getShapeFromMesh( self, meshEntry ):
        """
        Retourne l'identifiant de la géométrie référencée par le maillage d'identifiant fourni en argument.
        note:un maillage peut ne pas référencer une géométrie.
        
        @type     entry  : string
        @param    entry  : identifiant( entry ) du maillage  dans l'arbre d'étude.
        
        @rtype:   string
        @return:  identifiant( entry) de la géométrie, chaine vide s'il n'y en a pas. None en cas d'erreur        
        """
        shapeEntry = None
        
        try:
            anObject = self.__getCORBAObject( meshEntry )
            mesh     = anObject._narrow( SMESH.SMESH_Mesh  )                        
            if mesh: #Ok, c'est bien un objet maillage
                shape = mesh.GetShapeToMesh()
                if shape:                
                    shapeEntry = self.__getEntry( shape )
                else:
                    shapeEntry = ''
        except:            
            logger.debug( '>>>>CS_Pbruno SalomeStudy.getShapeFromMesh( meshEntry = %s ) ' %meshEntry )            
            shapeEntry = None
            
        return shapeEntry
        

        
    def isMeshGroup( self, entry ):
        """
        Teste si l'identifiant( entry ) fourni en paramètre designe bien un objet groupe de maille
        @type     entry  : string
        @param    entry  : identifiant( entry ) de l'objet dans l'arbre d'étude
        
        @rtype:   boolean
        @return:  True si test ok, False Sinon , None en cas d'erreur
        
        """
        result = None
        
        try:
            anObject = self.__getCORBAObject( entry )
            group    = anObject._narrow( SMESH.SMESH_GroupBase  )                        
            if group: #Ok, c'est bien un objet groupe de maille
                result = True
            else:
                result = False
        except:            
            logger.debug( '>>>>CS_Pbruno SalomeStudy.isMeshGroup( entry = %s ) ' %entry )            
            result = None
            
        return result
    
            
    def getMesh( self, meshGroupEntry ):
        """
        retourne l'identifiant du maillage auquel appartient le groupe de maille désigné en paramètre
        @type     meshGroupEntry: string.
        @param    meshGroupEntry: identifiant( entry ) du groupe de maille dans l'arbre d'étude.
        
        @rtype:   string
        @return:  identifiant( entry ) du maillage. None en cas d'erreur.        
        """
        meshEntry = None
        
        try:
            anObject = self.__getCORBAObject( meshGroupEntry )
            group    = anObject._narrow( SMESH.SMESH_GroupBase  )                        
            if group: #Ok, c'est bien un objet groupe de maille
                mesh  = group.GetMesh()
                meshEntry  = self.__getEntry( mesh )
        except:            
            logger.debug( '>>>>CS_Pbruno SalomeStudy.getMesh( meshGroupEntry = %s )'%meshGroupEntry  )            
            meshEntry  = None
            
        return meshEntry 
        
                
        
    def getAllMeshReferencingShape( self, shapeEntry, checkMainShape = False ):
        """
        Retourne une liste de tous les maillages construits à partir de l'objet
        géométrique passé en argument
        
        @type     shapeEntry : string
        @param    shapeEntry : identifiant( entry ) de l'objet  principal géométrique
        
        @type     checkMainShape : boolean
        @param    checkMainShape : True -> vérifie que l'objet géométrique est une géométrie principale, False -> pas de vérification
        
        @rtype:   list
        @return:  liste des identifiants( entry ) des maillages, liste vide si aucun , None si erreur.
        """
        result = []
        
        self.__waitCursor()        
        try:           
            if checkMainShape and not self.isMainShape(  shapeEntry ):
                result = None # c'est pas une mainShape !
            else:            
                #mainShapeSO = salome.IDToSObject( shapeEntry )
                mainShapeSO = self._myStudy.FindObjectID( shapeEntry )        
                print 50*'='                
                print 'BBBBBBBBBBBBBBBBB mainShapeSO ', mainShapeSO 
                print 50*'='
                SObjectList = self._myStudy.FindDependances( mainShapeSO )                
                if SObjectList: #Ok, il y a des objet référençant la mainShape
                    for SObject in SObjectList: # Recherche du type de chacun des objets
                        SFatherComponent = SObject.GetFatherComponent()
                        print '####  SFatherComponent = %s'%SFatherComponent 
                        if SFatherComponent.GetName() == SMesh: #Ok, l'objet est un objet du composant 'Mesh'
                            SFather = SObject.GetFather()
                            print '####  SFather= %s'%SFather
                            ##CorbaObject = SFather.GetObject()
                            FatherEntry = SFather.GetID()
                            CorbaObject  = self.__getCORBAObject(  FatherEntry )
                            print '####  CorbaObject = %s'%CorbaObject 
                            MeshObject = CorbaObject ._narrow( SMESH.SMESH_Mesh )
                            print '####  MeshObject = %s'%MeshObject 
                            if MeshObject : #Ok, l'objet est un objet 'maillage'
                                MeshObjectEntry = self.__getEntry( MeshObject )
                                print '####  MeshObjectEntry = %s'%MeshObjectEntry 
                                if MeshObjectEntry:
                                    result.append( MeshObjectEntry )  # On l'ajoute ds la liste résultat!            
        except :            
            logger.debug( '>>>>CS_Pbruno SalomeStudy.getAllMeshReferencingMainShape( shapeEntry  = %s ) ' %shapeEntry )            
            result = None
            
        self.__restoreCursor()            
            
        return result 

        
    def updateMesh( self,  meshEntry, groupeMaEntries, groupeNoEntries ):
        """
        Met à jours d'un objet maillage à partir d'une liste de sous-objet géométrique.
        L'opération consiste à créer des groupes dans le maillage correspondant 
        aux sous-objets géométrique de la liste.
        
        CS_pbruno Attention: ajoute des groupes sans vérifier si auparavant ils ont déjà été crées
        
        @type   meshEntry : string
        @param  meshEntry : identifiant du maillage
        
        @type   groupeMaEntries : liste de string
        @param  groupeMaEntries : liste contenant les identifiants ( entry ) des sous-objets géométriques
                                  sur lesquel on veut construire des groupes de face.

        @type   groupeNoEntries : liste de string
        @param  groupeNoEntries : liste contenant les identifiants ( entry ) des sous-objets géométriques
                                  sur lesquel on veut construire des groupes de noeuds.
        
        @rtype:   bool
        @return:  True si update OK, False en cas d'erreur
        """
        result = False
        
        self.__waitCursor()
        try:
            #print 'CS_pbruno updateMesh( self,  meshEntry=%s,   groupeMaEntries=%s )'%( meshEntry,   groupeMaEntries )
            corbaObject = self.__getCORBAObject(  meshEntry  )
            mesh        = corbaObject._narrow( SMESH.SMESH_Mesh )
            
            if mesh: # Ok, c'est bien un maillage
                shapeName = ""
                meshType  = None
                #liste des groupes déjà crée ( pour éviter les duplicata )                                            
                groupeNames = {}                
                groupeNames[ SMESH.NODE ] = self.__getGroupeNames( meshEntry, SMESH.NODE  )
                groupeNames[ SMESH.EDGE ] = self.__getGroupeNames( meshEntry, SMESH.EDGE  )
                groupeNames[ SMESH.FACE ] = self.__getGroupeNames( meshEntry, SMESH.FACE  )
                groupeNames[ SMESH.VOLUME ] = self.__getGroupeNames( meshEntry, SMESH.VOLUME )
                
                
                #création groupes de noeud
                for shapeEntry in groupeNoEntries:
                    anObject = self.__getCORBAObject(  shapeEntry )
                    shape    = anObject._narrow( GEOM.GEOM_Object )
                    if shape: #Ok, c'est bien un objet géométrique
                        shapeName = self.getName( shapeEntry )
                        
                        if not groupeNames.has_key( SMESH.NODE ):
                            groupeNames[ SMESH.NODE ] = self.__getGroupeNames( meshEntry, SMESH.NODE )
                        
                        if not ( shapeName in groupeNames[SMESH.NODE] ):
                            mesh.CreateGroupFromGEOM( SMESH.NODE, shapeName, shape )
                    else:
                        pass            # CS_pbruno au choix: 1)une seule erreur arrète l'intégralité de l'opération
                        #return False   #                    2)ou on continue et essaye les suivants ( choix actuel

                #création groupes de face
                for shapeEntry in groupeMaEntries:
                    meshType = self.__getMeshType( shapeEntry )
                    if meshType:                        
                        anObject = self.__getCORBAObject(  shapeEntry )
                        shape    = anObject._narrow( GEOM.GEOM_Object )
                        if shape: #Ok, c'est bien un objet géométrique                            
                            shapeName = self.getName( shapeEntry )
                            
                            if not groupeNames.has_key( meshType ):
                                groupeNames[ meshType ] = self.__getGroupeNames( meshEntry, meshType )
                            
                            if not ( shapeName in groupeNames[meshType] ):
                                mesh.CreateGroupFromGEOM( meshType, shapeName, shape )
                        else:
                            pass            #CS_pbruno au choix: 1)une seule erreur arrète l'intégralité de l'opération
                            #return False   #                    2)ou on continue et essaye les suivants ( choix actuel )
                    else:
                        pass            #CS_pbruno au choix: 1)une seule erreur arrète l'intégralité de l'opération 
                        #return False   #                    2)ou on continue et essaye les suivants ( choix actuel )

                result = True
                        
        except:            
            logger.debug( '>>>>CS_Pbruno SalomeStudy.updateMesh( meshEntry= %s,   groupeMaEntries = %s )' %( meshEntry, groupeMaEntries))            
            result = None
            
        self.__restoreCursor()
                    
        return result
        
        
        
    
        
        
    def createMesh( self, newMeshName, mainShapeEntry, groupeMaEntries, groupeNoEntries ):
        """
        Création d'un objet maillage à partir d'un objet géométrique principal
        Les groupes dans le maillage sont crée à partir des sous-objets géométriques
        contenu dans la liste fourni en paramètre d'entré.

        @type   newMeshName : string
        @param  newMeshName : nom du nouveau maillage
        
        @type   mainShapeEntry : string
        @param  mainShapeEntry : identifiant de l'objet géométrique principal        
        
        @type   groupeMaEntries : liste de string
        @param  groupeMaEntries : liste contenant les identifiants ( entry ) des sous-objets géométriques
                                  sur lesquel on veut construire des groupes de face.

        @type   groupeNoEntries : liste de string
        @param  groupeNoEntries : liste contenant les identifiants ( entry ) des sous-objets géométriques
                                  sur lesquel on veut construire des groupes de noeuds.
        
        @rtype:   string
        @return:  identifiant( entry ) dans l'arbre d'étude du nouveau maillage, None en cas d'erreur.
        """        
        newMeshEntry = None
                
        self.__waitCursor()
        try:
            #print 'CS_pbruno createMesh( self, newMeshName=%s, mainShapeEntry=%s, groupeMaEntries=%s )'%( newMeshName, mainShapeEntry, groupeMaEntries )
            newMesh = None
            anObject = self.__getCORBAObject(  mainShapeEntry )            
            shape    = anObject._narrow( GEOM.GEOM_Object )            
            if shape:
               
                # Création du nouveau maillage
                if not self.smeshEngine:                    
                    self.smeshEngine = salome.lcc.FindOrLoadComponent( "FactoryServer", "SMESH" )
                    
                self.smeshEngine.SetCurrentStudy( salome.myStudy )
                newMesh      = self.smeshEngine.CreateMesh( shape )
                newMeshEntry = self.__getEntry( newMesh )                                
                if newMeshEntry:                    
                    ok = self.setName( newMeshEntry, newMeshName )                    
                    if ok:
                        ok = self.updateMesh( newMeshEntry, groupeMaEntries, groupeNoEntries )
                    if not ok:
                        newMeshEntry = None                                       
        except:                                    
            logger.debug( '>>>>CS_Pbruno SalomeStudy.createMesh( self, newMeshName=%s, mainShapeEntry=%s, groupeMaEntries=%s )'%( newMeshName, mainShapeEntry, groupeMaEntries))            
            newMeshEntry = None
            
        self.__restoreCursor()
        return newMeshEntry


    def getGroupType(  self, groupEntry ):
        """
        Retourne le type du groupe fourni en paramètre.
                
        @type   groupEntry : string
        @param  groupEntry : identifiant dans l'arbre d'étude du groupe de maillage
        
        @rtype  :  type du groupe ( EdgeGroups, FaceGroups , NodeGroups, VolumeGroups )
        @return :  type du groupe ( EdgeGroups, FaceGroups , NodeGroups, VolumeGroups )
                   None si erreur.
        """
        groupType = None
        try:        
            groupObject = self.__getCORBAObject( groupEntry )
            if groupObject:
                aGroup = groupObject._narrow( SMESH.SMESH_GroupBase )
                print 'CS_pbruno getGroupType : aGroup  ->', aGroup
                if aGroup:
                    t = aGroup.GetType()
                    
                    conv = {
                        SMESH.NODE : NodeGroups , 
                        SMESH.EDGE : EdgeGroups ,
                        SMESH.FACE : FaceGroups ,
                        SMESH.VOLUME : VolumeGroups                    
                    }
                    groupType = conv[ t ]
                    print 'CS_pbruno getGroupType groupType  ->', groupType
                    
        except :            
            groupType= None           
        return groupType
                    
        
    def getGroups(  self,  meshEntry, groupeType ):
        """
        Retourne la liste des éléments du groupe du maillage fourni en paramètre.
                
        @type   meshEntry: string
        @param  meshEntry: identifiant dans l'arbre d'étude d'un objet maillage
        
        @type   groupeType: int
        @param  groupeType: type du groupe ( EdgeGroups, FaceGroups , NodeGroups, VolumeGroups )
        
        @rtype  :  dictionnaire
        @return :  dictionnaire : { clé = identifiants (entries) ds l'arbre du groupe, valeur = nom du groupe }
                   None si erreur.        
        """
        groups = None
        try:        
            if self.isMesh( meshEntry ):
                print 'CS_pbruno getGroups : self.isMesh'
                if groupeType in [ EdgeGroups , FaceGroups, NodeGroups, VolumeGroups ]:                    
                    GroupsEntry = self.getSubObjectID(  meshEntry, groupeType )                    
                    if GroupsEntry:                        
                        SOGroups = self._myStudy.FindObjectID( GroupsEntry )
                        groupIt = self._myStudy.NewChildIterator( SOGroups )
                        groupIt.InitEx(1)                
                        groups = {}
                        
                        print 'CS_pbruno groupIt ->', groupIt 
                        
                        while groupIt.More():
                            groupSO = groupIt.Value()
                            print 'CS_pbruno groupSO  ->', groupSO 
                            groupID = groupSO.GetID()
                            print 'CS_pbruno groupID  ->', groupID
                            groupObject = self.__getCORBAObject( groupID )
                            print 'CS_pbruno groupObject  ->', groupObject
                            if groupObject:
                                aGroup = groupObject._narrow( SMESH.SMESH_GroupBase )
                                print 'CS_pbruno aGroup  ->', aGroup
                                if aGroup:
                                    groups[ groupID ] = aGroup.GetName()
                                    print 'CS_pbruno groups[ groupID ] ->', groups[ groupID ]
                            groupIt.Next()
        except :
            logger.debug( '>>>>CS_Pbruno SalomeStudy.getGroups(  meshEntry = %s, groupeType = %s )'%( meshEntry, groupeType  ) )            
            groups = None           
        return groups
        
        
        
    def getMeshDimension(  self,  entry ):
        """
        Retourne la dimension du maillage.
        s'il n'est encore généré on considère que sa dimension est la même que celle de la géométrie sous-jacente
                        
        @type   entry: string
        @param  entry: identifiant dans l'arbre d'étude d'un objet maillage
        
        @rtype  :  int
        @return :  dimension du maillage. None si erreur.        
        """
        dimension = None
        try:
            anObject = self.__getCORBAObject( entry )
            mesh     = anObject._narrow( SMESH.SMESH_Mesh  )
            
            if mesh:
               isComputed = mesh.NbNodes()               
               if isComputed:
                    is3D = mesh.NbVolumes()
                    is2D = mesh.NbFaces()
                    
                    if is3D:
                        dimension = 3
                    elif is2D:
                        dimension = 2                    
                    #CS_pbruno à terminer pour dimension 1    
                                           
               else: # calcul dimension géométrie référencée
                    shape = mesh.GetShapeToMesh()                    
                    if shape:                        
                        shapeEntry = self.__getEntry( shape )
                        if shapeEntry:                            
                            tgeo = self.getRealShapeType( shapeEntry )
                                                        
                            if tgeo == COMPSOLID or tgeo == SOLID:
                                dimension = 3
                            elif tgeo == SHELL or tgeo == FACE:
                                dimension = 2
                            elif tgeo == WIRE or tgeo == EDGE or tgeo == VERTEX:
                                dimension = 1
        except :            
            logger.debug( '>>>>CS_Pbruno SalomeStudy.getMeshDimension(  meshEntry = %s )'%entry )
            dimension = None
           
        return dimension
        
        
        
        
        
        
        
        
        
        
    # -----------------------------------------------------------------------------
    #
    #                           POST-PRO
    #   fonctions de manipulation du module de post-pro de l'arbre d'étude
    #   ( éléments contenu dans la sous-rubrique ""Post-Pro"' )
    #
    # -----------------------------------------------------------------------------    
    def addRMedFile( self, rmedFilePath ):
        """
        Importe le fichier MED passé en argument dans le composant POST-PRO de SALOME
        @type     rmedFilePath: string.
        @param    rmedFilePath: chemin du fichier MED
        
        @rtype:   string
        @return:  identifiant( entry ) de l'objet crée. None en cas d'erreur.        
        """
        visuMEDentry = None
        self.__waitCursor()
        try:
            
            if not self.visuEngine:
                self.visuEngine = salome.lcc.FindOrLoadComponent( "FactoryServer", "VISU" )
            self.visuEngine.SetCurrentStudy( self._myStudy )
            
            object = self.visuEngine.ImportFile( rmedFilePath )
            if object:
                visuMEDentry = self.__getEntry( object )
                sItem = self._myStudy.FindObjectID(visuMEDentry)
                self.__setAttributeValue( sItem, "AttributeFileType", FICHIER_RESU_MED )
                self.__setAttributeValue( sItem, "AttributeExternalFileDef", rmedFilePath )
        except:            
            logger.debug( '>>>>CS_Pbruno SalomeStudy.visuMedFile( rmedFilePath = %s )'%rmedFilePath )            
            visuMEDentry = None
            
        self.__restoreCursor()
            
        return visuMEDentry
        
        
    def removeRMedFile( self, rmedEntry ):
        """
        Retire un objet résultat maillage du POST-PRO ( crée par la méthode addRMedFile  par ex)
        
        @type     rmedEntry : string.
        @param    rmedEntry : identifiant ( entry ) dans l'arbre de l'objet résultat maillage.
        
        @rtype:   boolean
        @return:  True si ok ( l'objet est supprimé ou l'identifiant rmedEntry ne désigne pas un objet de l'arbre d'étude )
                  False en cas d'erreur( l'identifiant rmedEntry  désigne bien un objet de l'arbre d'étude mais peut être pas un objet du POST-PRO )
        """
        ok = False
        
        self.__waitCursor()
            
        try:        
            if not self.visuEngine:
                self.visuEngine = salome.lcc.FindOrLoadComponent( "FactoryServer", "VISU" )
            self.visuEngine.SetCurrentStudy( self._myStudy )
            
            objet = self.__getCORBAObject( rmedEntry )
            if objet: # l'identifiant rmedEntry désigne un objet de l'arbre d'étude, on essaye de le supprimer en tant qu'objet du POST-PRO
                self.visuEngine.DeleteResult( objet )                
                ok = True
            else: # ok, l'identifiant rmedEntry ne désigne pas objet de l'arbre d'étude, pas besoin de supprimer
                ok = True                                               
        except:            
            logger.debug( '>>>>CS_Pbruno SalomeStudy.removeRMedFile( rmedEntry = %s )'%rmedEntry )            
            ok = False
            
        self.__restoreCursor()                        
        return ok
        
        
    def isRMed( self, entry ):
        """
        Teste si l'identifiant( entry ) fourni en paramètre designe bien un objet résultat med
        @type     entry  : string
        @param    entry  : identifiant( entry ) de l'objet dans l'arbre d'étude
        
        @rtype:   boolean
        @return:  True si test ok, False Sinon , None en cas d'erreur
        
        """
        result = None
        
        try:
            anObject = self.__getCORBAObject( entry )
            if anObject:
                rmed     = anObject._narrow( VISU.Result) # ok
                if rmed: #Ok, c'est bien un objet resultat med
                    result = True
                else:
                    result = False
        except:            
            logger.debug( '>>>>CS_Pbruno SalomeStudy.isRMed( entry = %s ) ' %entry )            
            result = None
                        
        return result
        
        
    def getRMedFilePath(self, entry):
        """
        Retourne le chemin du fichier med précédemment importé dans l'arbre d'étude
        désigné par son identifiant( entry )
                
        @type   entry: string
        @param  entry: identifiant de l'objet dans l'arbre d'étude
        
        @rtype  :  string
        @return :  le nom, None si erreur.
        """
        name = None
        try:
            comments = self.getString(entry)
            listOfComments = comments.split(";")
            for aComment in listOfComments:
                if "myFileName" in aComment:
                    typeOfComment, rmedFilePath = aComment.split("=")
                    break
            return rmedFilePath
        except:            
            logger.debug( '>>>>CS_Pbruno SalomeStudy.getRMedFilePath( entry = %s)' %( entry ) )            
            name = None
        return name        
        
        
    def getFieldTimeStamps(self, meshEntry):
        """
        Retourne les timestamps des champs du maillage fourni en entré
        
        @type     meshEntry: string.
        @param    meshEntry: identifiant ( entry ) dans l'arbre de l'objet résultat maillage.
        
        @rtype:   dictionnary
        @return:  dictionnaire contenant:
                    clé:        nom du champ
                    valeur:     liste des timestamps du champ
                    
                  None en cas d'erreur( l'identifiant meshEntry désigne bien un objet maillage du POST-PRO? )
        """
        timeStamps = {}
        
        self.__waitCursor()
        try:
#             fieldEntry = meshEntry + ':2'  #(astuce)                          
            sMesh = self._myStudy.FindObjectID(meshEntry)
                        
            if sMesh:
                childIt = self._myStudy.NewChildIterator(sMesh)
                childIt.InitEx(2) #1
                                
                
                while childIt.More():
                    try:
                        childSO = childIt.Value()
                        childID = childSO.GetID()                        
                        dChildInfo = {}
                        #lChildInfo = self.getComment(childID).split(';')
                        # avec Salome V3_2_6, il faut utiliser getString au lieu de getComment
                        lChildInfo = self.getString(childID).split(';')
                        for couple in lChildInfo:
                            nom, valeur = couple.split('=')                            
                            dChildInfo[nom] = valeur                        
                        if dChildInfo['myComment'] == 'FIELD':                            
                            timeStamps.setdefault(dChildInfo['myName'], [])
                        elif dChildInfo['myComment'] == 'TIMESTAMP':                            
                            timeValue=self.getName(childID).split(',')[0]                            
                            timeStamps[dChildInfo['myFieldName']].append(timeValue)                            
                    except:
                        pass                        
                    childIt.Next()

#         try:
#             fieldEntry = meshEntry + ':2'  #(astuce)
#                           
#             sField = self._myStudy.FindObjectID(fieldEntry)
#             if sField:
#                 childIt = self._myStudy.NewChildIterator(sField)
#                 childIt.InitEx(1) #1
#                                 
#                 while childIt.More():
#                     childSO = childIt.Value()
#                     childID = childSO.GetID()
#                     dChildInfo = {}
#                     lChildInfo = self.getComment(childID).split(';')
#                     for couple in lChildInfo:
#                         nom, valeur = couple.split('=')
#                         dChildInfo[nom] = valeur
#                     if dChildInfo['myComment'] == 'FIELD':
#                         timeStamps.setdefault(dChildInfo['myName'], [])
#                     elif dChildInfo['myComment'] == 'TIMESTAMP':
#                         timeValue=self.getName(childID).split(',')[0]                        
#                         timeStamps[dChildInfo['myFieldName']].append(timeValue)
#                     childIt.Next()
        except:            
            logger.debug( '>>>>CS_Pbruno SalomeStudy.getFields( meshEntry = %s )'%meshEntry)
            timeStamps = None
            
        self.__restoreCursor()                        
        return timeStamps
            
            
            
            
        
        
    # --------------------------------------------------------------------------
    #   fonctions de manipulation des objets eficas dans l'arbre d'étude
    #   ( éléments contenu dans la sous-rubrique "Eficas" )
    
    def addEficasItem( self, commFullPathName, eficasAttribute = FICHIER_EFICAS_ASTER ):
        """
        Ajoute un élément ( nom fichier de commande ) dans la partie eficas 
        
        @type   commFullPathName: string
        @param  commFullPathName: chemin complet du Jeu De Commande Eficas
        
        @type   eficasAttribute: string
        @param  eficasAttribute: permet de désigner le type de JDC ( ASTER ou HOMARD )
        
        @rtype:   string ou None.
        @return:  identifiant de l'item crée ds l'arbre, None si erreur.
        """
        commEntry    = None
        try:            
            EficasEntry  = self.addComponent(SEficas)            
            itemName     = re.split("/",commFullPathName)[-1]
            
            #commEntry = self.createItemInStudy( EficasEntry, itemName ) #CS_pbruno attention même nom possible, controle à faire            
            commEntry = self.addItem( EficasEntry, itemName = itemName, itemType = eficasAttribute, itemValue = commFullPathName )
            print 'addEficasItem  commEntry->', commEntry
            self.refresh()
        except :
            logger.debug( '>>>>CS_Pbruno SalomeStudy.addEficasItem(  commFullPathName = %s )'%commFullPathName )            
            commEntry = None
            
        return commEntry
        

        

# --------------------------------------------------------------------------
#   INIT

# gestionnaire d'étude commune aux composants PAL : ASTER_SRC, EFICAS_SRC
#palStudy = SalomeStudy()










    

"""
def setCurrentStudy(self,studyId):
        
def createFather(self,myModule):

def enregistre(self,myModule):

def createItemInStudy(self,fatherId,objectName):
"""
