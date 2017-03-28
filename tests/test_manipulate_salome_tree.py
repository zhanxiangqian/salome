
import os.path as osp
import unittest as UT

import aster_s
import aster_s.salome_tree as ST


import salome_aster_tests as SAT


class MeshFile(object):
    """A Mesh file type"""
    pass


class TestManipulateSalomeBrowser(UT.TestCase):

    def setUp(self):
        bld = aster_s.StudyBuilder()
        self.std = bld.create_salome_study("s")
        self.pal_std = SAT.PalStudyBuilder().attach_to(self.std)

    def tearDown(self):
        self.std.close()

    def test_add_root_node(self):
        root = self.std.add_root("R")
        self.assert_(root.is_root)
        self.assert_(root.parent is None)

    def test_add_node_to_tree(self):
        engine_name, browser_name = "GEOM", "Geometry"
        geom = self.std.add_root(engine_name, browser_name)

        name = "Data"
        node = geom.add_node(name)

        pstd = self.pal_std
        self.assertEqual(pstd.getName(geom.entry), browser_name)
        self.assertEqual(pstd.getName(node.entry), name)

    def test_store_parent_when_adding_node(self):
        root = self.std.add_root("r")
        self.assert_(root.parent is None)

        nd1 = root.add_node("n1")
        self.assert_(nd1.parent is root)

        nd2 = root.add_node("n2")
        self.assert_(nd2.parent is root)

        nd1_1 = nd1.add_node("n1_1")
        self.assert_(nd1_1.parent is nd1)

    def test_test_entry_equality_on_two_nodes(self):
        node1 = ST.Node(None, None, "1")
        node1bis = ST.Node(None, None, "1")
        node2 = ST.Node(None, None, "2")
        self.assertEqual(node1, node1bis)
        self.assertNotEqual(node1, node2)

    def test_add_root_only_one_time(self):
        std = self.std
        root1 = std.add_root("G")
        root2 = std.add_root("G")
        self.assertEqual(root1.entry, root2.entry)
        self.assert_(root2.is_root)

    def test_add_node_only_one_time(self):
        root = self.std.add_root("G")
        node1 = root.add_node("n1")
        node2 = root.add_node("n2")
        node1bis = root.add_node("n1") 
        self.assertEqual(node1.entry, node1bis.entry)
        self.assertNotEqual(node1.entry, node2.entry)

    def test_add_value_attr_to_node(self):
        root = self.std.add_root("G")
        node = root.add_node("n")
        val = "/tmp/aster.comm"
        attr = node.get_attr(ST.Value)
        attr.write(val)

        pstd = self.pal_std
        self.assertEqual(pstd.getComment(node.entry), val)

    def test_raise_corba_bad_param_on_value_writting_not_of_str(self):
        from omniORB.CORBA import BAD_PARAM
        root = self.std.add_root("G")
        node = root.add_node("n")
        attr = node.get_attr(ST.Value)
        self.assertRaises(BAD_PARAM, attr.write, 256)

    def test_get_value_from_an_attr(self):
        root = self.std.add_root("G")
        node = root.add_node("n")
        val = "/tmp/aster.comm"
        sattr = node.get_attr(ST.Value)
        self.assertEqual(sattr.read(), '')
        sattr.write(val)
        
        gattr = node.get_attr(ST.Value)
        self.assert_(sattr is not gattr)
        self.assertEqual(gattr.read(), val)

    def test_manage_type_attr(self):
        node = self.std.add_root("R")
        attr = node.get_attr(ST.Type)
        self.assert_(attr.load() is None)
        attr.store(MeshFile)

        attr = node.get_attr(ST.Type)
        self.assert_(attr.load() is MeshFile)
        self.assert_(ST.load_cls(node) is MeshFile)
        self.assertEqual(self.pal_std.getTypeAndValue(node.entry)[0],
                         ST.dumps(MeshFile))

        attr.write("FICHIER_ASTER")
        self.assertEqual(attr.read(), "FICHIER_ASTER") 
        self.assert_(attr.load() is None)
        self.assert_(ST.load_cls(node) is None)

        attr.write("")
        self.assert_(attr.load() is None)

    def test_manage_python_attributes(self):
        root = self.std.add_root("R")
        node = root.add_node("n")
        attr = node.get_attr(ST.PythonAttrType)
        self.assert_(attr.load("val") is None)
        attr.store("val", 256)
        self.assertEqual(attr.load("val"), 256)
        attr.store("val", 12)
        self.assertEqual(attr.load("val"), 12)

    def test_use_a_node_as_a_source_and_find_references(self):
        std = self.std
        root = std.add_root("R")
        ref = root.add_node("ref")
        nd1 = root.add_node("n1")
        nd2 = root.add_node("n2")
        self.assertEqual(ref.find_references(), [])
        self.assert_(nd1.give_source() is None)

        nd2.use_source(ref)
        nd1.use_source(ref)

        sobjs = std.sstd.FindDependances(ref.get_sobj())
        self.assertEqual([sobj.GetID() for sobj in sobjs], 
                         [nd2.entry, nd1.entry])
        self.assertEqual(ref.find_references(), [nd2, nd1])
        self.assertEqual(nd1.give_source(), ref)

    def test_destroy_a_node(self):
        pstd = self.pal_std
        root = self.std.add_root("G")

        nd0 = root.add_node("n0")
        self.assertEqual(pstd.getName(nd0.entry), "n0")
        nd0.destroy()
        self.assert_(pstd.getName(nd0.entry) is None)

        nd1 = root.add_node("n1")
        nd1_0 = nd1.add_node("n1_0")
        nd1_1 = nd1.add_node("n1_1")
        self.assertEqual(pstd.getName(nd1_1.entry), "n1_1")
        nd1.destroy()
        self.assert_(pstd.getName(nd1_1.entry) is None)

    def test_destroy_a_node_with_references(self):
        root = self.std.add_root("R")
        ref = root.add_node("ref")
        nodes = [root.add_node("n%i" % idx) for idx in range(3)]
        for node in nodes:
            node.use_source(ref)
        ref.destroy()
        self.assertEqual(len(root.get_children()), 0)

    def test_know_if_a_node_is_alive(self):
        root = self.std.add_root("R")
        node = root.add_node("n")
        self.assert_(node.is_alive())
        node.destroy()
        self.assert_(not node.is_alive())

    def test_create_new_entry_if_the_node_has_been_destroyed(self):
        oroot = self.std.add_root("R")
        oroot.destroy()
        root = self.std.add_root("R")
        self.assertNotEqual(oroot.entry, root.entry)

        onode = root.add_node("n")
        onode.destroy()
        node = root.add_node("n")
        self.assertNotEqual(onode.entry, node.entry)

    def test_get_children_of_a_node(self):
        root = self.std.add_root("R")
        base = root.add_node("base")
        self.assertEqual(base.get_children(), [])

        nodes = [base.add_node("n%i" % idx) for idx in range(4)]
        nodes[-1].destroy()
        nodes = nodes[:-1]

        cnodes = base.get_children()
        self.assertNotEqual([id(node) for node in nodes],
                            [id(cnode) for cnode in cnodes])
        self.assertEqual([node.entry for node in nodes],
                         [node.entry for node in cnodes])

        self.assertEqual(nodes[0].parent, base)
        self.assertEqual(cnodes[0].parent, base)
        self.assertEqual(base.parent, root)

    def test_find_a_children_node_from_its_name(self):
        root = self.std.add_root("R")
        nodes = [root.add_node("n%i" % idx) for idx in range(20)]
        nd5 = root.find_node("n5")
        self.assertEqual(nodes[5].entry, nd5.entry)
        self.assert_(root.find_node("not found") is None)

    def test_build_node_from_an_entry(self):
        build = self.std.build_node_from_entry
        root = self.std.add_root("R")
        broot = build(root.entry)
        self.assertEqual(root, broot)
        self.assert_(broot.is_root)
        self.assert_(broot.parent is None)

        node = root.add_node("nd1")
        bnode = build(node.entry)
        self.assertEqual(node, bnode)
        self.assertEqual(node.parent, bnode.parent)

        self.assertRaises(ValueError, build, None)

    def test_give_salome_study(self):
        std = self.std
        root = std.add_root("R")
        rstd = root.give_salome_study()
        self.assertEqual(std.idx, rstd.idx)


class TestHaveALineObject(UT.TestCase):

    def setUp(self):
        bld = aster_s.StudyBuilder()
        self.std = bld.create_salome_study("s")

    def tearDown(self):
        self.std.close()

    def test_write_value_as_python_object_and_visible_value_as_str(self):
        root = self.std.add_root("r")
        node = root.add_node("n")
        line = ST.Line(node)
        self.assert_(line.read_value() is None)
        self.assertEqual(line.read_visible_value(), '')

        line.write_value(12)
        self.assertEqual(line.read_value(), 12)
        self.assertEqual(line.read_visible_value(), '12')
        
        lst, desc = range(4), "A list of numbers"
        line.write_value(lst, desc)
        self.assertEqual(line.read_value(), lst)
        self.assertEqual(line.read_visible_value(), desc)


def extract_med_mesh_data(mesh):
    """Extract data on a MED mesh into a dictionary for comparison"""
    import SALOME_MED as MED
    data = {
        "nodes-nb" : mesh.getNumberOfNodes(),
        "mesh-dim" : mesh.getMeshDimension(),
    }
    grps = (
        ("nodes", MED.MED_NODE),
        ("edges", MED.MED_EDGE),
        ("faces", MED.MED_FACE),
        ("cells", MED.MED_CELL),
    )
    for key, med_type in grps:
        names =  [grp.getName() for grp in mesh.getGroups(med_type)]
        data[key + "-grp-names"] = names
    return data


class TestManipulateMeshes(UT.TestCase):

    def setUp(self):
        import salome_aster_tests as ST
        bld = aster_s.StudyBuilder()
        self.std = bld.create_salome_study("std")
        self.med_fname = ST.get_data("forma01a.mmed")
        self.tmp_dir = ST.TmpDir("manipulate_meshes")

    def tearDown(self):
        self.tmp_dir.clean()
        self.std.close()

    def test_load_meshes_from_med_file(self):
        meshes = self.std.load_meshes_from(self.med_fname)
        self.assertEqual(len(meshes), 1)
        mesh_node = meshes[0].node
        self.assertEqual(mesh_node.read_name(), "MeshCoude")
        nodes_node, edges_node = mesh_node.get_children()
        self.assertEqual([node.read_name() for node in nodes_node.get_children()],
                         ["PA", "PB"])
        self.assertEqual([node.read_name() for node in edges_node.get_children()],
                         ['COUDE', 'TUYAU', 'TUY2', 'TUY1'])

    def test_attach_mesh_to_a_node(self):
        lmesh = self.std.load_meshes_from(self.med_fname)[0]
        cmesh = ST.attach_mesh(lmesh.node)
        self.assert_(cmesh.node is lmesh.node)

        node = lmesh.node.get_children()[0]
        self.assertRaises(TypeError, ST.attach_mesh, node)
        node = lmesh.node.parent
        self.assertRaises(TypeError, ST.attach_mesh, node)

    def check_mesh_in_files(self, mesh_name, fname1, fname2):
        from salome import lcc
        import SALOME_MED as MED
        ceng = lcc.FindOrLoadComponent("FactoryServer", "MED")
        eng = ceng._narrow(MED.MED_Gen)
        std_name = self.std.sstd._get_Name()
        datas = []
        for fname in [fname1, fname2]:
            med_mesh = eng.readMeshInFile(fname, std_name, mesh_name)
            datas.append(extract_med_mesh_data(med_mesh))
        res = {
            "nodes-nb" : 9,
            "mesh-dim" : 1,
            'nodes-grp-names': ['PA', 'PB'],
            'cells-grp-names': ['COUDE', 'TUY1', 'TUY2', 'TUYAU'],
            'edges-grp-names': [],
            'faces-grp-names': [],
        }
        self.assertEqual(datas[0], res)
        self.assertEqual(datas[0], datas[1])

    def test_export_mesh_to_med_file(self):
        mesh = self.std.load_meshes_from(self.med_fname)[0]
        exfname = osp.join(self.tmp_dir.add("export_to_med"), "mesh.med")
        mesh.dump_to(exfname)
        self.check_mesh_in_files(mesh.read_name(), self.med_fname, exfname)

    def test_find_mesh_dimension(self):
        mesh = self.std.load_meshes_from(self.med_fname)[0]
        self.assertEqual(mesh.give_dim(), 2)

    def test_give_nodes_and_mesh_groups(self):
        SMesh = ST.SMeshExplorator
        GNO, GMA = [object() for idx in range(2)]
        exp = SMesh()
        no_grp = exp.add_group(GNO)
        no_grp.register((2, 3), [SMesh.node])
        ma_grp = exp.add_group(GMA)
        ma_grp.register((2, 3), [SMesh.edge])
        ma_grp.register((3,), [SMesh.face, SMesh.volume])

        mesh = self.std.load_meshes_from(self.med_fname)[0]
        no_grp_names = ['PA', 'PB']
        ma_grp_names = ['COUDE', 'TUYAU', 'TUY2', 'TUY1']
        self.assertEqual(no_grp.find_groups(mesh), no_grp_names)
        self.assertEqual(ma_grp.find_groups(mesh), ma_grp_names)

        self.assertEqual(exp.find_groups(mesh), no_grp_names + ma_grp_names)
        self.assertEqual(exp.give_group_key(mesh, "PB"), GNO)
        self.assertEqual(exp.give_group_key(mesh, "TUYAU"), GMA)
        self.assertRaises(ValueError, exp.give_group_key, mesh, "NONE")

    def test_tell_if_geometry_present(self):
        mesh = self.std.load_meshes_from(self.med_fname)[0]
        self.assert_(not mesh.has_geom())


class TestManipulateGeomFromMesh(UT.TestCase):

    def setUp(self):
        import GEOM
        import SMESH
        import salome
        bld = aster_s.StudyBuilder()
        std = bld.create_salome_study("std")
        sidx = std.idx
        sstd = std.sstd

        geng = salome.lcc.FindOrLoadComponent("FactoryServer", "GEOM")
        basic_ops = geng.GetIBasicOperations(sidx)
        prim_ops = geng.GetI3DPrimOperations(sidx)
        sgeom = prim_ops.MakeBoxDXDYDZ(5, 5, 5)
        geng.AddInStudy(sstd, sgeom, "3D", None)

        seng = salome.lcc.FindOrLoadComponent("FactoryServer", "SMESH")
        seng.SetCurrentStudy(sstd)
        mesh = std.attach_mesh_from(seng.CreateMesh(sgeom))
        
        self.std = std
        self.sstd = sstd
        self.geng = geng
        self.basic_ops = basic_ops
        self.prim_ops = prim_ops
        self.sgeom = sgeom
        self.mesh = mesh

    def tearDown(self):
        self.std.close()

    def test_give_dimension(self):
        self.assertEqual(self.mesh.give_dim(), 3)

    def test_find_geom_groups_from_mesh(self):
        grp_no_names = ["VA", "VB"]
        for idx, name in enumerate(grp_no_names):
            vert = self.basic_ops.MakePointXYZ(idx, idx, idx)
            self.geng.AddInStudy(self.sstd, vert, name, self.sgeom)
        grp_ma_names = ["Ma", "Mb", "Mc"]
        for idx, name in enumerate(grp_ma_names):
            box = self.prim_ops.MakeBoxDXDYDZ(idx + 1, idx + 1, idx + 1)
            self.geng.AddInStudy(self.sstd, box, name, self.sgeom)
        
        mesh = self.mesh
        Geom = ST.GeomExplorator
        exp = Geom()
        grp_no = exp.add_group("NO")
        grp_no.register((2, 3), [Geom.vertex])
        grp_ma = exp.add_group("MA")
        grp_ma.register((2, 3), [Geom.solid])

        self.assertEqual(grp_no.find_groups(mesh), grp_no_names)
        self.assertEqual(grp_ma.find_groups(mesh), grp_ma_names)
        self.assertEqual(exp.find_groups(mesh), grp_ma_names + grp_no_names)
        self.assertEqual(exp.give_group_key(mesh, "VB"), "NO")
        self.assertEqual(exp.give_group_key(mesh, "Mc"), "MA")


class TestManipulateEficasFile(UT.TestCase):

    def setUp(self):
        bld = aster_s.StudyBuilder()
        std = bld.create("std")

        # Creating fake Eficas file because the 
        # EFICAS component does not offer an interface
        name = "eficas-file.comm"
        ftype = ST.EficasFile.ftype
        fname = "/aster/case1/eficas-file.comm"
        node = std.node.add_node(name)
        node.get_attr(ST.Type).write(ftype)
        node.get_attr(ST.Value).write(fname)

        self.std = std
        self.fdata = {
            "node" : node,
            "name" : name,
            "ftype" : ftype,
            "fname" : fname,
        }

    def tearDown(self):
        self.std.close()

    def test_tell_if_node_is_eficas_file(self):
        self.assert_(ST.is_eficas_file(self.fdata["node"]))
        self.assert_(not ST.is_eficas_file(self.std.node))

    def test_attach_eficas_file(self):
        fdata = self.fdata
        efile = ST.attach_eficas_file(fdata["node"])
        self.assertEqual(efile.node.entry, fdata["node"].entry)
        self.assertEqual(efile.read_name(), fdata["name"])
        self.assertEqual(efile.read_fname(), fdata["fname"])
        self.assertEqual(efile.read_type(), fdata["ftype"])
        self.assert_(ST.load_cls(efile.node) is None)

        self.assertRaises(TypeError, ST.attach_eficas_file, self.std.node)


if __name__ == "__main__":
    UT.main()

