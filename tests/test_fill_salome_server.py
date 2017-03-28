# -*- coding: utf-8 -*-
"""Testing connection to the Salomé server and studies building. 
For all those tests, the server should be running, see the REAME.rst.
Moreover the server is supposed to be empty on start.
"""
import unittest as UT

import salome

import aster_s
from aster_s.study import STUDY

import aster_mocker as MCK


class TestConnectToSalomeServer(UT.TestCase):

    def test_initialize_life_cycle_corba(self):
        bld = aster_s.StudyBuilder()
        self.assert_(salome.lcc is not None)

    def test_keep_the_same_study_builder_for_every_study(self):
        bld = aster_s.StudyBuilder()
        self.assert_(aster_s.StudyBuilder() is bld)

    def test_avoid_opening_of_salome_study_on_start(self):
        bld = aster_s.StudyBuilder()

        mng = salome.myStudyManager
        self.assertEqual(mng.GetOpenStudies(), [])


class TestCreateAsterStudy(MCK.Test):

    def setUp(self):
        self.bld = aster_s.StudyBuilder()
        self.mng = salome.myStudyManager

    def tearDown(self):
        self.bld.close_all()

    def test_create_aster_study_attached_to_salome_one(self):
        std = self.bld.create("Aster study")
        self.assertEqual(self.mng.GetOpenStudies(), ["Aster study"])

        std.close()
        self.assertEqual(self.mng.GetOpenStudies(), [])

    def test_close_all_studies_created_by_builder(self):
        bld = self.bld
        mng = self.mng
        std1 = bld.create("S1")
        std2 = bld.create("S2")
        self.assertEqual(mng.GetOpenStudies(), ["S1", "S2"])

        bld.close_all()
        self.assertEqual(mng.GetOpenStudies(), [])

    def test_attach_aster_study_to_salome_one(self):
        sstd = self.bld.create_salome_study("Salome study", register=True)
        self.assertEqual(self.mng.GetOpenStudies(), ["Salome study"])
        astd = self.bld.attach_to(sstd)
        astd.close()
        self.assertEqual(self.mng.GetOpenStudies(), ["Salome study"])
        sstd.close()
        self.assertEqual(self.mng.GetOpenStudies(), [])

    def test_close_aster_study_first(self):
        bld = self.bld
        sstd = bld.create_salome_study("sstd", register=True)
        astd = bld.attach_to(sstd)

        # Following test will crash Salomé
        # sstd.close()
        # astd.close()
        msstd = self.mocker.patch(sstd)
        mastd = self.mocker.patch(astd)
        self.mocker.order()
        MCK.expect(mastd.close()).passthrough()
        MCK.expect(msstd.close_salome_study()).passthrough()
        self.mocker.replay()

        bld.close_all()

    def test_remove_closed_studies_from_lists(self):
        bld = self.bld
        stds = [bld.create_salome_study("sstd%i" % idx, register=True) \
                for idx in range(3)]
        astds = [bld.attach_to(std) for std in stds]
        astds[1].close()
        self.assert_(astds[1] not in bld._astds)

        stds[2].close()
        self.assert_(stds[2] not in bld._stds)

        self.assertEqual(bld._stds, [stds[0], stds[1]])
        self.assertEqual(bld._astds, [astds[0]])
        bld.close_all()
        self.assertEqual(bld._stds, [])
        self.assertEqual(bld._astds, [])

    def test_add_aster_component_on_study_creation(self):
        sstd = self.bld.create_salome_study("sstd", register=True)
        astd = self.bld.attach_to(sstd)
        self.assertEqual(astd.node.read_name(), STUDY)


if __name__ == "__main__":
    UT.main()

