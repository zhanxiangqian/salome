"""Test that the ASTER module can add cases by using CORBA
"""

import unittest as UT

import salome 

import aster_s
import ASTER


class TestCreateAnAsterStudy(UT.TestCase):

    def setUp(self):
        self.bld = aster_s.StudyBuilder()
        self.sstd = self.bld.create_salome_study("std", register=True).sstd

    def tearDown(self):
        self.bld.close_all()

    def test_retrieve_engine(self):
        ceng = salome.lcc.FindOrLoadComponent("FactoryServerPy", "ASTER")
        self.assert_(ceng)
        eng = ceng._narrow(ASTER.ASTER_Gen)
        self.assert_(eng)

    def test_attach_aster_study_to_salome_one(self):
        sstd = self.sstd
        ceng = salome.lcc.FindOrLoadComponent("FactoryServerPy", "ASTER")
        eng = ceng._narrow(ASTER.ASTER_Gen)
        self.assert_(sstd.FindComponent("ASTER") is None)
        std = eng.AttachTo(self.sstd)
        self.assert_(sstd.FindComponent("ASTER"))

    def test_not_create_study_entry_if_already_present(self):
        astd = self.bld.create("astd")

        ceng = salome.lcc.FindOrLoadComponent("FactoryServerPy", "ASTER")
        eng = ceng._narrow(ASTER.ASTER_Gen)
        std = eng.AttachTo(astd.sstd.sstd)
        self.assertEqual(std.GetEntry(), astd.node.entry)


class CorbaTest(UT.TestCase):

    def setUp(self):
        bld = aster_s.StudyBuilder()
        sstd = bld.create_salome_study("std", register=True)
        astd = bld.attach_to(sstd)

        ceng = salome.lcc.FindOrLoadComponent("FactoryServerPy", "ASTER")
        eng = ceng._narrow(ASTER.ASTER_Gen)
        cstd = eng.AttachTo(sstd.sstd)
        
        self.bld = bld
        self.sstd = sstd
        self.astd = astd
        self.cstd = cstd

    def tearDown(self):
        self.bld.close_all()


class TestAddStudyCases(CorbaTest):

    def test_add_study_case_from_command_file(self):
        ccase = self.cstd.AddCase("from-comm", ASTER.FromComm)
        cases = self.astd.get_all(aster_s.Case)
        self.assertEqual(len(cases), 1)
        self.assertEqual(ccase.GetEntry(), cases[0].node.entry)
        case = cases[0]
        data = case.get(aster_s.DataSection)

        ccase.UseStr(ASTER.WorkingDir, "/tmp/aster")
        self.assertEqual(data.get(aster_s.WorkingDir).read_dname(), "/tmp/aster")

        ccase.UseStr(ASTER.CommFile, "fname.comm")
        self.assertEqual(data.get(aster_s.CommFile).read_fname(), "fname.comm")

        ccase.UseStr(ASTER.MedFile, "fname.mmed")
        self.assertEqual(data.get(aster_s.MedFile).read_fname(), "fname.mmed")

    def test_add_study_case_from_export_file(self):
        ccase = self.cstd.AddCase("from-comm", ASTER.FromExport)
        case = self.astd.get(aster_s.Case)
        self.assertEqual(ccase.GetEntry(), case.node.entry)
        data = case.get(aster_s.DataSection)

        ccase.UseStr(ASTER.ExportFile, "f.export")
        self.assertEqual(data.get(aster_s.ExportFile).read_fname(), "f.export")


class TestManageCases(CorbaTest):

    def test_remove_rmed_file(self):
        ccase = self.cstd.AddCase("test-remove-rmed", ASTER.FromComm)
        case = self.astd.get(aster_s.Case)
        data = case.get(aster_s.DataSection)
       
        self.assert_(not data.get(aster_s.RemoveRmed))
        ccase.Use(ASTER.RemoveRmed)
        self.assert_(data.get(aster_s.RemoveRmed))

    def test_read_case_name(self):
        name = "A case added from CORBA"
        ccase = self.cstd.AddCase(name, ASTER.FromComm)
        self.assertEqual(ccase.ReadName(), name)

    def test_give_cases(self):
        names = ["a", "b", "c", "b"]
        for name in names:
            self.cstd.AddCase(name, ASTER.FromComm)

        ccases = self.cstd.GiveCases()
        self.assertEqual(len(ccases), 3)
        self.assertEqual(ccases[1].ReadName(), "b")
        self.assertEqual(ccases[0].ReadName(), "a")
        self.assertEqual(ccases[2].ReadName(), "c")


if __name__ == "__main__":
    UT.main()

