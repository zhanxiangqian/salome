# encoding: utf-8

from numpy import cross
import salome

##ELIIPSE RECTANGLE CYLINDER##############
DEFAULT_RMAJ = 1
DEFAULT_RMIN = 1
DEFAULT_CENTERX  = 0
DEFAULT_CENTERY  = 0
DEFAULT_CENTERZ  = 0

DEFAULT_VECTXX = 1
DEFAULT_VECTXY = 0
DEFAULT_VECTXZ = 0

DEFAULT_VECTYX = 0
DEFAULT_VECTYY = 1
DEFAULT_VECTYZ = 0
##HALF_PLANE########################
DEFAULT_PFONX = 1
DEFAULT_PFONY = 1
DEFAULT_PFONZ = 0

DEFAULT_NORMX = 0 
DEFAULT_NORMY = 0
DEFAULT_NORMZ = 1

DEFAULT_DTANX = 0 
DEFAULT_DTANY =1
DEFAULT_DTANZ = 0
##SEGMENT#########################
DEFAULT_PFONOX = 0
DEFAULT_PFONOY = 0
DEFAULT_PFONOZ = 0

DEFAULT_PFONEX = 1
DEFAULT_PFONEY = 1
DEFAULT_PFONEZ = 0
##################################
salome.salome_init()
study   = salome.myStudy
studyId = salome.myStudyId


from salome.geom import geomBuilder
geompy = geomBuilder.New(salome.myStudy)

def createGeometry(study, rmaj=DEFAULT_RMAJ, rmin=DEFAULT_RMIN, centerx=DEFAULT_CENTERX,  centery=DEFAULT_CENTERY,  \
                   centerz=DEFAULT_CENTERZ, vectXx=DEFAULT_VECTXX,vectXy=DEFAULT_VECTXY,vectXz=DEFAULT_VECTXZ, \
                   vectYx=DEFAULT_VECTYX, vectYy=DEFAULT_VECTYY, vectYz=DEFAULT_VECTYZ):
    '''
    This function creates the geometry on the specified study and with
    given parameters.
    '''
    centre = geompy.MakeVertex(float(centerx), float(centery), float(centerz))
    vectn1 = cross([float(vectXx),float(vectXy), float(vectXz)],[float(vectYx),float(vectYy), float(vectYz)])
    vectn =  geompy.MakeVectorDXDYDZ(float(vectn1[0]), float(vectn1[1]), float(vectn1[2]))
    vectmaj = geompy.MakeVectorDXDYDZ(float(vectXx),float(vectXy), float(vectXz))
    vectmin = geompy.MakeVectorDXDYDZ(float(vectYx),float(vectYy), float(vectYz))
    Ellipse = geompy.MakeEllipse(centre, vectn,rmaj,rmin, vectmaj)
    return Ellipse


########################################################"
def createGeometryEllipse(study, rmaj=DEFAULT_RMAJ, rmin=DEFAULT_RMIN, centerx=DEFAULT_CENTERX,  centery=DEFAULT_CENTERY,  \
                   centerz=DEFAULT_CENTERZ, vectXx=DEFAULT_VECTXX,vectXy=DEFAULT_VECTXY,vectXz=DEFAULT_VECTXZ, \
                   vectYx=DEFAULT_VECTYX, vectYy=DEFAULT_VECTYY, vectYz=DEFAULT_VECTYZ):
    '''
    This function creates the geometry on the specified study and with
    given parameters.
    '''
    centre = geompy.MakeVertex(float(centerx), float(centery), float(centerz))
    vectn1 = cross([float(vectXx),float(vectXy), float(vectXz)],[float(vectYx),float(vectYy), float(vectYz)])
    vectn =  geompy.MakeVectorDXDYDZ(float(vectn1[0]), float(vectn1[1]), float(vectn1[2]))
    vectmaj = geompy.MakeVectorDXDYDZ(float(vectXx),float(vectXy), float(vectXz))
    vectmin = geompy.MakeVectorDXDYDZ(float(vectYx),float(vectYy), float(vectYz))
    WireEllipse = geompy.MakeEllipse(centre, vectn,rmaj,rmin, vectmaj)
    Ellipse = geompy.MakeFace(WireEllipse, True)
    return Ellipse


############################################################
def createGeometryCylinder(study, rmaj=DEFAULT_RMAJ, rmin=DEFAULT_RMIN, centerx=DEFAULT_CENTERX,  centery=DEFAULT_CENTERY,  \
                   centerz=DEFAULT_CENTERZ, vectXx=DEFAULT_VECTXX,vectXy=DEFAULT_VECTXY,vectXz=DEFAULT_VECTXZ, \
                   vectYx=DEFAULT_VECTYX, vectYy=DEFAULT_VECTYY, vectYz=DEFAULT_VECTYZ):
    '''
    This function creates the geometry on the specified study and with
    given parameters.
    '''
    centre = geompy.MakeVertex(float(centerx), float(centery), float(centerz))
    vectn1 = cross([float(vectXx),float(vectXy), float(vectXz)],[float(vectYx),float(vectYy), float(vectYz)])
    vectn =  geompy.MakeVectorDXDYDZ(float(vectn1[0]), float(vectn1[1]), float(vectn1[2]))
    vectmaj = geompy.MakeVectorDXDYDZ(float(vectXx),float(vectXy), float(vectXz))
    vectmin = geompy.MakeVectorDXDYDZ(float(vectYx),float(vectYy), float(vectYz))
    Ellipse = geompy.MakeEllipse(centre, vectn,rmaj,rmin, vectmaj)
    Cylinder = geompy.MakePrismVecH(Ellipse, vectn, 100)
    return Cylinder


############################################################
def createGeometryRectangle(study, rmaj=DEFAULT_RMAJ, rmin=DEFAULT_RMIN, centerx=DEFAULT_CENTERX,  centery=DEFAULT_CENTERY,  \
                   centerz=DEFAULT_CENTERZ, vectXx=DEFAULT_VECTXX,vectXy=DEFAULT_VECTXY,vectXz=DEFAULT_VECTXZ, \
                   vectYx=DEFAULT_VECTYX, vectYy=DEFAULT_VECTYY, vectYz=DEFAULT_VECTYZ):
    '''
    This function creates the geometry on the specified study and with
    given parameters.
    '''
    centre = geompy.MakeVertex(float(centerx), float(centery), float(centerz))
    vectmaj = geompy.MakeVectorDXDYDZ(float(vectXx),float(vectXy), float(vectXz))
    vectmaj_inv= geompy.MakeMirrorByPoint(vectmaj, centre)
    vectmin = geompy.MakeVectorDXDYDZ(float(vectYx),float(vectYy), float(vectYz))
    vectmin_inv= geompy.MakeMirrorByPoint(vectmin, centre)
    pt_m = geompy.MakeTranslationVectorDistance(centre,vectmaj,float(rmaj))
    pt_m1 = geompy.MakeTranslationVectorDistance(pt_m,vectmin,float(rmin))
    pt_m2 = geompy.MakeTranslationVectorDistance(pt_m1,vectmaj_inv,2*float(rmaj))
    pt_m3 = geompy.MakeTranslationVectorDistance(pt_m2,vectmin_inv,2*float(rmin))
    pt_m4 = geompy.MakeTranslationVectorDistance(pt_m3,vectmaj,2*float(rmaj))
    Edge_1 = geompy.MakeEdge(pt_m1, pt_m2) 
    Edge_2 = geompy.MakeEdge(pt_m2, pt_m3) 
    Edge_3 = geompy.MakeEdge(pt_m3, pt_m4) 
    Edge_4 = geompy.MakeEdge(pt_m4, pt_m1) 
    Wire = geompy.MakeWire([Edge_1, Edge_2, Edge_3, Edge_4])
    Rectangle = geompy.MakeFace(Wire, True)
    return Rectangle


def createGeometryHalfplane(study, PFONx=DEFAULT_PFONX, PFONy=DEFAULT_PFONY, PFONz=DEFAULT_PFONZ,  NORMx=DEFAULT_NORMX,  \
                   NORMy=DEFAULT_NORMY, NORMz=DEFAULT_NORMZ,DTANx=DEFAULT_DTANX,DTANy=DEFAULT_DTANY, \
                   DTANz=DEFAULT_DTANZ):
    '''
    This function creates the geometry on the specified study and with
    given parameters.
    '''
    P_fond = geompy.MakeVertex(float(PFONx),float(PFONy) ,float(PFONz))
    vectn =  geompy.MakeVectorDXDYDZ(float(NORMx), float(NORMy), float(NORMz))
    dtan = geompy.MakeVectorDXDYDZ(float(DTANx), float(DTANy), float(DTANz))
    vect1 = cross([float(NORMx), float(NORMy), float(NORMz)],[float(DTANx), float(DTANy), float(DTANz)])
    vect_trans1 =  geompy.MakeVectorDXDYDZ( float(PFONx),  float(PFONy),  float(PFONz))
    vect_trans2 = geompy.MakeMirrorByPoint(vect_trans1, P_fond)
    vect_dtan = geompy.MakeMirrorByPoint(dtan, P_fond)
    point_trans1 = geompy.MakeTranslationVectorDistance(P_fond,vect_trans1, 50)
    point_trans2 = geompy.MakeTranslationVectorDistance(P_fond,vect_trans2, 50)     
    line = geompy.MakeLineTwoPnt(point_trans1, point_trans2)
    Half_plane = geompy.MakePrismVecH(line,vect_dtan, 100)
    return Half_plane


def createGeometrySegment(study, PFONOx=DEFAULT_PFONOX, PFONOy=DEFAULT_PFONOY, PFONOz=DEFAULT_PFONOZ, \
                          PFONEx=DEFAULT_PFONEX, PFONEy=DEFAULT_PFONEY, PFONEz=DEFAULT_PFONEZ):
    '''
    This function creates the geometry on the specified study and with
    given parameters.
    '''

    Pt_orig = geompy.MakeVertex(float(PFONOx),float(PFONOy) ,float(PFONOz))
    Pt_extr = geompy.MakeVertex(float(PFONEx),float(PFONEy) ,float(PFONEz))
    Segment = geompy.MakeLineTwoPnt(Pt_orig, Pt_extr)
    return Segment


def createGeometryHalfline(study, PFONx=DEFAULT_PFONX, PFONy=DEFAULT_PFONY, PFONz=DEFAULT_PFONZ, \
                          DTANx=DEFAULT_DTANX, DTANy=DEFAULT_DTANY, DTANz=DEFAULT_DTANZ):
    '''
    This function creates the geometry on the specified study and with
    given parameters.
    '''

    Pt_orig = geompy.MakeVertex(float(PFONx),float(PFONy) ,float(PFONz))
    Dtan_Vect = geompy.MakeVectorDXDYDZ(float(DTANx),float(DTANy) ,float(DTANz))
    Dtan_Vect_Inv= geompy.MakeMirrorByPoint(Dtan_Vect, Pt_orig)
    Half_Line = geompy.MakePrismVecH(Pt_orig,Dtan_Vect_Inv, 100)
    return Half_Line

    

#
# ===================================================================
# Use cases and test functions
# ===================================================================
#
def TEST_createGeometry():
    salome.salome_init()
    theStudy=salome.myStudy
    createGeometry(theStudy)


