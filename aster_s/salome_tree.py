# -*- coding: utf-8 -*-
"""Work with the Salomé study by adding elements to the Salomé object tree
"""
import os.path as osp
from pickle import dumps
from pickle import loads as ploads

from aster_s.utils import Singleton, log


def loads(pobj):
    """Return the object found in the string 'pobj' or None
    if the string can not be loaded"""
    try:
        obj = ploads(pobj)
    except (ValueError, EOFError):
        obj = None
    return obj


class AttrType(object):
    """A SALOMEDS attribute type for a browser node.

    See::

        >>> import SALOMEDS
        >>> [i for i in dir(SALOMEDS) if i.startswith("Attr")]

    """

    def __init__(self, sname, stype):
        self.sname = sname
        self.stype = stype
        self._sobj = None
        self._bld = None

    def attach_to(self, sobj, bld):
        """Attach an object to the attribute type and providing
        the Salome builder"""
        self._sobj = sobj
        self._bld = bld

    def get_attr(self):
        """Return the CORBA attr type"""
        attr = self._bld.FindOrCreateAttribute(self._sobj, self.sname)
        return attr._narrow(self.stype)


class ValueAttrType(AttrType):
    """An attribute having the 'SetValue' and 'Value' methods
    """

    def write(self, value):
        """Write the attribute value"""
        self.get_attr().SetValue(value)

    def read(self):
        """Read the attribute value"""
        return self.get_attr().Value()


class Name(ValueAttrType):
    """Wrap AttributeName
    """

    def __init__(self):
        from SALOMEDS import AttributeName
        ValueAttrType.__init__(self, "AttributeName", AttributeName)


class Value(ValueAttrType):
    """Wrap AttributeComment. The value of AttributeComment appears
    in the value column of the object tree.
    """

    def __init__(self):
        from SALOMEDS import AttributeComment
        ValueAttrType.__init__(self, "AttributeComment", AttributeComment)


class Type(ValueAttrType):
    """Use AttributeFileType for storing a Python class
    """

    def __init__(self):
        from SALOMEDS import AttributeFileType
        ValueAttrType.__init__(self, "AttributeFileType", AttributeFileType)

    def store(self, ftype):
        """Store the type (using pickle.dumps)"""
        self.get_attr().SetValue(dumps(ftype))

    def load(self):
        """Load the type (using pickle.loads)"""
        return loads(self.get_attr().Value())


class PythonAttrType(AttrType):
    """Store a Python attribute with its key and value
    """

    def __init__(self):
        from SALOMEDS import AttributePythonObject
        AttrType.__init__(self, "AttributePythonObject", AttributePythonObject)

    def load_attrs(self):
        """Load all of the attributes"""
        return loads(self.get_attr().GetObject()) or {}

    def store_attrs(self, attrs):
        """Store all of the attributes"""
        self.get_attr().SetObject(dumps(attrs), False)

    def store(self, key, obj):
        """Store the Python object (using pickle.dumps)"""
        attrs = self.load_attrs()
        attrs[key] = obj
        self.store_attrs(attrs)

    def load(self, key):
        """Load the Python object (using pickle.loads)"""
        return self.load_attrs().get(key)


class PixMapAttrType(AttrType):
    """Store a icon attribute
    """

    def __init__(self):
        from SALOMEDS import AttributePixMap
        AttrType.__init__(self, "AttributePixMap", AttributePixMap)

    def store(self, icon):
        """Store the icon path"""
        self.get_attr().SetPixMap(icon)


class Node(object):
    """A node entry for the Salomé object browser.

    A node exists only if its has a name (Salomé definition)
    """

    def __init__(self, std, bld, entry, parent=None, is_root=False):
        self._std = std
        self._bld = bld
        self.entry = entry
        self.is_root = is_root
        self._parent = parent

    def find_parent(self):
        """Find the parent node"""
        parent = self._parent
        if parent:
            return parent
        elif not self.is_root:
            psobj = self.get_sobj().GetFather()
            parent = self.__class__(self._std, self._bld, psobj.GetID())
            self._parent = parent
            return parent

    parent = property(find_parent)

    def get_std(self):
        """Return the Salomé study"""
        return self._std

    def get_bld(self):
        """Return the Salomé builder"""
        return self._bld

    def __eq__(self, node):
        """Test the equality of two nodes by testing their entry"""
        return (self.entry == node.entry)

    def get_sobj(self):
        """Return the Salome object corresponding to the browser entry"""
        return self._std.FindObjectID(self.entry)

    def add_node(self, name):
        """Add a children node. A node exists if its has a name."""
        for node in self.get_children():
            if node.read_name() == name:
                break
        else:
            root = self.get_sobj()
            sobj = self._bld.NewObject(root)
            node = self.__class__(self._std, self._bld, sobj.GetID(), self)
            node.write_name(name)
        return node

    def get_children(self):
        """Return the children nodes"""
        std = self._std
        bld = self._bld
        cls = self.__class__

        root = self.get_sobj()
        cit = std.NewChildIterator(root)
        cit.InitEx(0)

        children = []
        while cit.More():
            node = cls(std, bld, cit.Value().GetID(), self)
            if node.is_alive():
                children.append(node)
            cit.Next()
        return children

    def find_node(self, name):
        """Find a children node from its name"""
        for node in self.get_children():
            if node.read_name() == name:
                break
        else:
            node = None
        return node

    def get_subnode(self, tag):
        """Find a child node from its Salomé tag or return None"""
        sobj = self.get_sobj()
        res, sub_sobj = sobj.FindSubObject(tag)
        if res:
            return Node(self._std, self._bld, sub_sobj.GetID())

    def get_attr(self, attr_type):
        """Get a SALOMEDS attribute of the node"""
        attr = attr_type()
        attr.attach_to(self.get_sobj(), self._bld)
        return attr

    def read_name(self):
        """Convenient method for directly reading the Name attribute
        because a node is defined by its name. For others atttributes
        use 'get_attr'."""
        attr = self.get_attr(Name)
        return attr.read()

    def write_name(self, name):
        """Convenient method for directly writting the Name attribute
        because a node is defined by its name. For others attributes
        use 'get_attr'."""
        attr = self.get_attr(Name)
        attr.write(name)

    def use_source(self, src_node):
        """Use the given node as a source defining the current node."""
        self._bld.Addreference(self.get_sobj(), src_node.get_sobj())

    def give_source(self):
        """Return the node used as a source for defining the current node,
        if any."""
        has_src, src_sobj = self.get_sobj().ReferencedObject()
        if has_src:
            return self.__class__(self._std, self._bld, src_sobj.GetID())

    def find_references(self):
        """Return a list of nodes using this node as a source"""
        cls = self.__class__
        nodes = []
        for sobj in self._std.FindDependances(self.get_sobj()):
            nodes.append(cls(self._std, self._bld, sobj.GetID()))
        return nodes

    def give_salome_study(self):
        """Return the Salomé study used by this node"""
        return SalomeStudy(self.get_sobj().GetStudy())

    def destroy(self):
        """Destroy a node from the object browser"""
        for node in self.find_references():
            node.destroy()
        self._bld.RemoveObject(self.get_sobj())

    def is_alive(self):
        """Test if the node is alive by checking if it has a name"""
        return (self.read_name() != '')


def load_cls(node):
    """Load the class of the given node"""
    return node.get_attr(Type).load()


class Line(object):
    """A line in the object browser for a section.
    Only the value can be changed.
    """
    def __init__(self, node):
        self.node = node

    def read_name(self):
        """Read the node name from the object browser"""
        return self.node.read_name()

    def store_type(self, ptype):
        """Write the type on the object browser"""
        attr = self.node.get_attr(Type)
        attr.store(ptype)

    def load_type(self):
        """Read the type from the object browser"""
        attr = self.node.get_attr(Type)
        return attr.load()

    def store_attr(self, key, obj):
        """Store a Python object with its key"""
        attr = self.node.get_attr(PythonAttrType)
        attr.store(key, obj)

    def store_icon(self, icon_path):
        """Assign a icon"""
        attr = self.node.get_attr(PixMapAttrType)
        attr.store(icon_path)

    def load_attr(self, key):
        """Load a Python object from its key"""
        attr = self.node.get_attr(PythonAttrType)
        return attr.load(key)

    def write_value(self, value, visible_value=None):
        """Store a value on the object and write a visible value on the
        object browser. The visible value in the object browser tree will
        be converted to str type by default."""
        self.store_attr("value", value)
        attr = self.node.get_attr(Value)
        if visible_value is not None:
            attr.write(visible_value)
        else:
            attr.write(str(value))

    def read_value(self):
        """Read the value on the object browser"""
        return self.load_attr("value")

    def read_visible_value(self):
        """Read the visible value on the object browser"""
        attr = self.node.get_attr(Value)
        return attr.read()

    def remove(self):
        """Remove the line from the object browser"""
        self.node.destroy()


class File(Line):
    """A file entry in the object browser
    """

    def __init__(self, node):
        Line.__init__(self, node)

    def write_fname(self, fname):
        """Write the file name path on the object browser.
        Use the file name as the value of the name attribute"""
        self.node.write_name(osp.basename(fname))
        self.write_value(fname)

    def read_fname(self):
        """Read the filename from the object browser"""
        return self.read_value()


class VisuMedFile(File):
    """Med file displayed in the VISU component
    """
    display = True

    def show(self):
        """Add an entry in the PARAVIS component and add a reference
        to the current node"""
        # Used for testing because there is obviously no way back
        # from VISU_Gen.SetCurrentStudy
        if not self.display:
            return

        # Desactivation : Load the med file in the PARAVIS component
        #import smeca_utils.visu_utils as VU
        #log.info("Loading Paravis module...")
        #msg = VU.load_med_file(self.read_fname())
        #log.info(msg)

    def remove(self):
        """Remove the Med file from the object browser"""
        for ref_node in self.node.find_references():
            ref_node.destroy()
        File.remove(self)


def build_file(root, name, file_type, fname, file_cls=File):
    """Build a File from the given root node"""
    dfile = file_cls(root.add_node(name))
    dfile.store_type(file_type)
    dfile.write_fname(fname)
    return dfile


class GroupExplorator(object):
    """Gather component types into a group.
    """

    def __init__(self, exp, key):
        self._exp = exp
        self.key = key
        self._dct = {}

    def register(self, dims, compo_types):
        """Register the component types for the given dimensions"""
        dct = self._dct
        for dim in dims:
            ctypes = dct.setdefault(dim, [])
            ctypes.extend(compo_types)

    def find_groups(self, mesh):
        """Find the group names on the given mesh"""
        grps = []
        dim = mesh.give_dim()
        if dim:
            ctypes = self._dct[dim]
            grps = self._exp.find_groups_from_ctypes(mesh, ctypes)
        log.debug("GroupExplorator.find_groups for mesh %s returns %s with dim %s and dct %s", mesh, grps, dim, self._dct)
        return grps


class Explorator(object):
    """Explore a component for finding groups
    """

    def __init__(self):
        self._grps = {}

    def add_group(self, key):
        """Add a group with the given key"""
        grp = GroupExplorator(self, key)
        self._grps[key] = grp
        return grp

    def give_group(self, key):
        """Return the group explorator from its key"""
        return self._grps[key]

    def find_groups(self, mesh):
        """Find groups names on the given mesh by using all group
        explorators"""
        grp_names = []
        for grp in self._grps.values():
            grp_names.extend(grp.find_groups(mesh))
        return grp_names

    def find_groups_from_ctypes(self, mesh, ctypes):
        """Find the group names from the given component types"""
        raise NotImplementedError

    def give_group_key(self, mesh, grp_name):
        """Return the group key of the given group name"""
        grps = self._grps
        for key in grps:
            if grp_name in grps[key].find_groups(mesh):
                return key
        else:
            mess = "Group '%s' not found on the mesh '%s'"
            raise ValueError(mess % (grp_name, mesh.read_name()))


class GeomExplorator(Explorator):
    """Explore GEOM component for finding groups
    """
    vertex, \
    edge, \
    wire, \
    shell, \
    face, \
    solid, \
    compsolid = [object() for _ in range(7)]

    def __init__(self):
        import GEOM
        Explorator.__init__(self)
        self._ctypes = {
            self.vertex : GEOM.VERTEX,
            self.edge : GEOM.EDGE,
            self.wire : GEOM.WIRE,
            self.shell : GEOM.SHELL,
            self.face : GEOM.FACE,
            self.solid : GEOM.SOLID,
            self.compsolid : GEOM.COMPSOLID,
        }

    def find_groups_from_ctypes(self, mesh, gtypes):
        """Find the group names on a GEOM node according to types"""
        ctypes = [self._ctypes[gtype] for gtype in gtypes]
        grp_names = []
        for geom in mesh.give_geom().get_children():
            if geom.get_shape_type() in ctypes:
                grp_names.append(geom.read_name())
        return grp_names


class SMeshExplorator(Explorator):
    """Explore meshes in SMESH component for finding groups
    """
    # Group tags coming from SMESH module
    node, edge, face, volume = 11, 12, 13, 14

    def find_groups_from_ctypes(self, mesh, tags):
        """Find the group names on a SMESH node according to the
        given tags"""
        node = mesh.node
        grp_names = []
        for tag in tags:
            tag_node = node.get_subnode(tag)
            if not tag_node:
                continue
            for grp_node in tag_node.get_children():
                grp_names.append(grp_node.read_name())
        log.debug("SMeshExplorator.find_groups_from_ctypes returns %s", grp_names)
        return grp_names


class Geom(object):
    """A geometry object
    """

    def __init__(self, node):
        import GEOM
        self.node = node
        self._compound_types = {
        # Following GeomExplorator types defintion order
            7 : GEOM.VERTEX,
            6 : GEOM.EDGE,
            5 : GEOM.WIRE,
            3 : GEOM.SHELL,
            4 : GEOM.FACE,
            2 : GEOM.SOLID,
            1 : GEOM.COMPSOLID,
            }

    def read_name(self):
        """Read the geometry name"""
        return self.node.read_name()

    def get_sgeom(self):
        """Return the CORBA geometry object used in Salomé"""
        return self.node.get_sobj().GetObject()

    def get_children(self):
        """Give the children geometry objects"""
        children = []
        for node in self.node.get_children():
            children.append(Geom(node))
        return children

    def get_shape_type(self):
        """Return the CORBA primitive shape type. Try to find primitive type
        of a COMPOUND."""
        import GEOM
        sgeom = self.get_sgeom()
        shape_type = sgeom.GetShapeType()
        if shape_type is GEOM.COMPOUND:
            node = self.node
            geom_eng = node.get_sobj().GetFatherComponent().GetObject()
            ops = geom_eng.GetIGroupOperations(node.get_std()._get_StudyId())
            sidx = ops.GetType(sgeom)
            shape_type = self._compound_types.get(sidx, shape_type)
        return shape_type


class Mesh(object):
    """A Mesh object
    """

    def __init__(self, node):
        self.node = node

    def read_name(self):
        """Read the mesh name"""
        return self.node.read_name()

    def has_geom(self):
        """Tell is the mesh is linked to a geometry"""
        return bool(self.give_geom())

    def give_geom(self):
        """Return a geometry object if found (None otherwise)"""
        sgeom = self.get_smesh().GetShapeToMesh()
        if sgeom:
            node = self.node
            gnode = Node(node.get_std(), node.get_bld(), sgeom.GetStudyEntry())
            return Geom(gnode)

    def get_smesh(self):
        """Return the Salomé Mesh object"""
        return self.node.get_sobj().GetObject()

    def dump_to(self, med_fname, auto_groups=False, med_version1=False):
        """Dump the mesh into a MED file.
        Use the MED version 2.2 by default, else can use version 2.1.
        """
        import SMESH
        med_version = SMESH.MED_V2_2
        if med_version1:
            med_version = SMESH.MED_V2_1
        self.get_smesh().ExportToMED(med_fname, auto_groups, med_version)

    def give_dim(self):
        """Give the mesh dimension or None if not found"""
        smesh = self.get_smesh()
        dim = None
        if smesh.NbNodes():
            if smesh.NbVolumes():
                dim = 3
            elif smesh.NbFaces():
                dim = 2
            elif smesh.NbEdges():
                dim =1
        elif self.has_geom():
            import GEOM
            stype = self.give_geom().get_shape_type()
            if stype in [GEOM.COMPSOLID, GEOM.SOLID]:
                dim = 3
            elif stype in [GEOM.SHELL, GEOM.FACE]:
                dim = 2
            elif stype in [GEOM.WIRE, GEOM.EDGE, GEOM.VERTEX]:
                dim = 1
        return dim

    def update_from(self, grp_names):
        """Update from the given group names if they are found
        on the geometry"""
        import GEOM, SMESH
        mesh_types = {
            GEOM.VERTEX : SMESH.NODE,
            GEOM.EDGE : SMESH.EDGE,
            GEOM.WIRE : SMESH.EDGE,
            GEOM.FACE : SMESH.FACE,
            GEOM.SHELL : SMESH.FACE,
            GEOM.SOLID : SMESH.VOLUME,
            GEOM.COMPSOLID : SMESH.VOLUME,
        }
        smesh = self.get_smesh()


        smesh_grps_MA = []
        smesh_grps_NO = []
        for grp in smesh.GetGroups() :
           if str(grp.GetType()) == 'NODE' :
               smesh_grps_NO.append(grp.GetName())
           else :
               smesh_grps_MA.append(grp.GetName())

        print smesh_grps_MA,smesh_grps_NO
        done = False
        for geom in self.give_geom().get_children():
            grp_name = geom.read_name()
            #if grp_name in smesh_grps:
            #   continue
            #Modif Fournier
            print grp_name
            if grp_name in grp_names[0]:
                if grp_name in smesh_grps_MA:
                    pass
                else :
                    mesh_type = mesh_types.get(geom.get_shape_type())
                    if mesh_type:
                    #smesh.CreateGroup(mesh_type, grp_name)
                        smesh.CreateGroupFromGEOM(mesh_type,grp_name,geom.get_sgeom())
                        done = True
            if grp_name in grp_names[1]:
                if grp_name in smesh_grps_NO:
                    continue
                #smesh.CreateGroup(SMESH.NODE,grp_name)
                smesh.CreateGroupFromGEOM(SMESH.NODE,grp_name,geom.get_sgeom())
                done = True
        return done

    def Crea_Group_mesh(self):
        "Create a group 'TOUT'"
        import SMESH
        mesh_types = {
           'EDGE' : SMESH.EDGE,
           'FACE' : SMESH.FACE,
           'VOLUME' : SMESH.VOLUME,
           }

        smesh = self.get_smesh()

        mesh_type = mesh_types.get(str(smesh.GetTypes()[-1]))
        exist_TOUT = False
        for g in smesh.GetGroups() :
            if str(g.GetType()) in mesh_types.keys() and g.GetName()=='TOUT':
               exist_TOUT = True 
        if not exist_TOUT :
           group = smesh.CreateGroup(mesh_type,'TOUT')
           group.AddFrom(smesh.GetMesh())

        return True


def attach_mesh(node):
    """Attach a mesh to the given node"""
    corba_obj = node.get_sobj().GetObject()
    if not corba_obj:
        mess = "No CORBA object found at the given node " \
               "for attaching a Mesh"
        raise TypeError(mess)
    from SMESH import SMESH_Mesh
    obj = corba_obj._narrow(SMESH_Mesh)
    if not obj:
        raise TypeError("The given node does not hold a Mesh")
    return Mesh(node)

def is_mesh(node):
    """Test it the given node hold a mesh from the SMESH component"""
    try:
        mesh = attach_mesh(node)
    except TypeError:
        return False
    else:
        return True


class EficasFile(object):
    """Eficas file coming from the EFICAS component
    """
    ftype = "FICHIER_EFICAS_ASTER"

    def __init__(self, node):
        self.node = node

    def read_name(self):
        """Read the eficas file name"""
        return self.node.read_name()

    def read_fname(self):
        """Read the command file name defined by Eficas"""
        return self.node.get_attr(Value).read()

    def read_type(self):
        """Read the eficas file type"""
        return self.node.get_attr(Type).read()


def is_eficas_file(node):
    """Test if the node hold an Eficas file"""
    return (node.get_attr(Type).read() == EficasFile.ftype)

def attach_eficas_file(node):
    """Attach an eficas file at the given node"""
    if is_eficas_file(node):
        return EficasFile(node)
    else:
        mess = "No eficas file found at the given entry '%s'" % node.entry
        raise TypeError(mess)


class SalomeStudy(object):
    """Interface to a Salomé study.

    This class is supposed to wrap the PAL module
    """

    def __init__(self, sstd, bld=None):
        self.is_close = False
        self._bld = bld

        self.sstd = sstd
        assert sstd is not None
        self.sbld = sstd.NewBuilder()

        self._action_on_close = None

    def give_idx(self):
        """Give the index attributed by Salomé"""
        return self.sstd._get_StudyId()

    idx = property(give_idx)

    def add_root(self, engine_name, browser_name=None, define_compo=False):
        """Add a root node on the object browser describing a Salome engine.
        This node can be defined as a component having a CORBA interface
        written in Python."""
        browser_name = browser_name or engine_name
        std = self.sstd
        bld = self.sbld
        compo = std.FindComponent(engine_name)
        if compo is None:
            compo = bld.NewComponent(engine_name)
            node = Node(std, bld, compo.GetID(), is_root=True)
            node.write_name(browser_name)
            if define_compo:
                from salome import lcc
                eng = lcc.FindOrLoadComponent("FactoryServerPy", engine_name)
                bld.DefineComponentInstance(compo, eng)
        else:
            node = Node(std, bld, compo.GetID(), is_root=True)
        return node

    def build_node_from_entry(self, entry):
        """Build a node from the Salomé object browser entry"""
        if entry is None:
            mess = "Object browser entry expected, %s found" % entry
            raise ValueError(mess)
        node = Node(self.sstd, self.sbld, entry)
        sobj = node.get_sobj()
        if sobj.GetID() == sobj.GetFatherComponent().GetID():
           node = Node(self.sstd, self.sbld, entry, is_root=True)
        return node

    def attach_mesh_from(self, smesh_obj):
        """Build a Mesh from the SMESH object"""
        sstd = self.sstd
        sobj = sstd.FindObjectIOR(sstd.ConvertObjectToIOR(smesh_obj))
        node = self.build_node_from_entry(sobj.GetID())
        return Mesh(node)

    def load_meshes_from(self, med_fname):
        """Load meshes from a MED file"""
        from salome import lcc
        from SMESH import SMESH_Gen
        sstd = self.sstd
        ceng = lcc.FindOrLoadComponent("FactoryServer", "SMESH")
        eng = ceng._narrow(SMESH_Gen)
        eng.SetCurrentStudy(sstd)
        cmeshes = eng.CreateMeshesFromMED(med_fname)[0]
        meshes = []
        for cmesh in cmeshes:
            meshes.append(self.attach_mesh_from(cmesh))
        return meshes

    def register_on_close(self, action):
        """Register an action to be performed before closing"""
        self._action_on_close = action

    def close_salome_study(self):
        """Close the Salomé study without performing any action"""
        if not self.is_close:
            self.sstd.Close()
            if self._bld:
                self._bld.remove_salome_study(self)
            self.is_close = True

    def close(self):
        """Close the Salomé study"""
        if not self.is_close:
            if self._action_on_close:
                self._action_on_close()
            self.close_salome_study()


def create_salome_study(name, bld=None):
    """Create a new Salomé study with the given name"""
    # Import salome only when needed
    from salome import myStudyManager as std_mng
    return SalomeStudy(std_mng.NewStudy(name), bld=bld)


