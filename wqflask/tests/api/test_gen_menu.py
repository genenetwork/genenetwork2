"""Test cases for wqflask.api.gen_menu"""
import unittest
import mock

from wqflask.api.gen_menu import get_species
from wqflask.api.gen_menu import get_groups
from wqflask.api.gen_menu import phenotypes_exist
from wqflask.api.gen_menu import genotypes_exist
from wqflask.api.gen_menu import build_datasets


class TestGenMenu(unittest.TestCase):
    """Tests for the gen_menu module"""

    def setUp(self):
        self.test_group = {
            'mouse': [
                ['H_T1',
                 'H_T',
                 'Family:DescriptionA'
                 ],
                ['H_T2', "H_T'", 'Family:None']
            ],
            'human': [
                ['BXD', 'BXD', 'Family:None'],
                ['HLC', 'Liver: Normal Gene Expression with Genotypes (Merck)',
                 'Family:Test']
            ]
        }

    @mock.patch('wqflask.api.gen_menu.g')
    def test_get_species(self, db_mock):
        """Test that assertion is raised when dataset and dataset_name are defined"""
        db_mock.db.execute.return_value.fetchall.return_value = (('human', 'Human'),
                                                                 ('mouse', 'Mouse'))
        self.assertEqual(get_species(),
                         [['human', 'Human'], ['mouse', 'Mouse']])
        db_mock.db.execute.assert_called_once_with(
            "SELECT Name, MenuName FROM Species ORDER BY OrderId"
        )

    @mock.patch('wqflask.api.gen_menu.g')
    def test_get_groups(self, db_mock):
        """Test that species groups are grouped correctly"""
        db_mock.db.execute.return_value.fetchall.side_effect = [
            # Mouse
            (('BXD', 'BXD', None),
             ('HLC', 'Liver: Normal Gene Expression with Genotypes (Merck)', 'Test')),
            # Human
            (('H_T1', "H_T", "DescriptionA"),
             ('H_T2', "H_T'", None))
        ]

        self.assertEqual(get_groups([["human", "Human"], ["mouse", "Mouse"]]),
                         self.test_group)

        for name in ["mouse", "human"]:
            db_mock.db.execute.assert_any_call(
                ("SELECT InbredSet.Name, InbredSet.FullName, " +
                 "IFNULL(InbredSet.Family, 'None') " +
                 "FROM InbredSet, Species WHERE Species.Name " +
                 "= '{}' AND InbredSet.SpeciesId = Species.Id GROUP by " +
                 "InbredSet.Name ORDER BY IFNULL(InbredSet.FamilyOrder, " +
                 "InbredSet.FullName) ASC, IFNULL(InbredSet.Family, " +
                 "InbredSet.FullName) ASC, InbredSet.FullName ASC, " +
                 "InbredSet.MenuOrderId ASC").format(name)
            )

    @mock.patch('wqflask.api.gen_menu.g')
    def test_phenotypes_exist_called_with_correct_query(self, db_mock):
        """Test that phenotypes_exist is called with the correct query"""
        db_mock.db.execute.return_value.fetchone.return_value = None
        phenotypes_exist("test")
        db_mock.db.execute.assert_called_with(
            "SELECT Name FROM PublishFreeze WHERE PublishFreeze.Name = 'testPublish'"
        )

    @mock.patch('wqflask.api.gen_menu.g')
    def test_phenotypes_exist_with_falsy_values(self, db_mock):
        """Test that phenotype check returns correctly when given a None value"""
        for x in [None, False, (), [], ""]:
            db_mock.db.execute.return_value.fetchone.return_value = x
            self.assertFalse(phenotypes_exist("test"))

    @mock.patch('wqflask.api.gen_menu.g')
    def test_phenotypes_exist_with_truthy_value(self, db_mock):
        """Test that phenotype check returns correctly when given Truthy """
        for x in ["x", ("result"), ["result"], [1]]:
            db_mock.db.execute.return_value.fetchone.return_value = (x)
            self.assertTrue(phenotypes_exist("test"))

    @mock.patch('wqflask.api.gen_menu.g')
    def test_genotypes_exist_called_with_correct_query(self, db_mock):
        """Test that genotypes_exist is called with the correct query"""
        db_mock.db.execute.return_value.fetchone.return_value = None
        genotypes_exist("test")
        db_mock.db.execute.assert_called_with(
            "SELECT Name FROM GenoFreeze WHERE GenoFreeze.Name = 'testGeno'"
        )

    @mock.patch('wqflask.api.gen_menu.g')
    def test_genotypes_exist_with_falsy_values(self, db_mock):
        """Test that genotype check returns correctly when given a None value"""
        for x in [None, False, (), [], ""]:
            db_mock.db.execute.return_value.fetchone.return_value = x
            self.assertFalse(genotypes_exist("test"))

    @mock.patch('wqflask.api.gen_menu.g')
    def test_genotypes_exist_with_truthy_value(self, db_mock):
        """Test that genotype check returns correctly when given Truthy """
        for x in ["x", ("result"), ["result"], [1]]:
            db_mock.db.execute.return_value.fetchone.return_value = (x)
            self.assertTrue(phenotypes_exist("test"))


    @mock.patch('wqflask.api.gen_menu.g')
    def test_build_datasets_with_type_phenotypes(self, db_mock):
        """Test that correct dataset is returned for a phenotype type"""
        db_mock.db.execute.return_value.fetchall.return_value = (
            (602, "BXDPublish", "BXD Published Phenotypes"),
        )
        self.assertEqual(build_datasets("Mouse", "BXD", "Phenotypes"),
                         [['602', "BXDPublish", "BXD Published Phenotypes"]])
        db_mock.db.execute.assert_called_with(
            "SELECT InfoFiles.GN_AccesionId, PublishFreeze.Name, " +
            "PublishFreeze.FullName FROM InfoFiles, PublishFreeze, " +
            "InbredSet WHERE InbredSet.Name = 'BXD' AND " +
            "PublishFreeze.InbredSetId = InbredSet.Id AND " +
            "InfoFiles.InfoPageName = PublishFreeze.Name " +
            "ORDER BY PublishFreeze.CreateTime ASC"
        )
        self.assertEqual(build_datasets("Mouse", "MDP", "Phenotypes"),
                         [['602', "BXDPublish", "Mouse Phenome Database"]])

        db_mock.db.execute.return_value.fetchall.return_value = ()
        db_mock.db.execute.return_value.fetchone.return_value = (
            "BXDPublish", "Mouse Phenome Database"
        )
        self.assertEqual(build_datasets("Mouse", "MDP", "Phenotypes"),
                         [["None", "BXDPublish", "Mouse Phenome Database"]])

    @mock.patch('wqflask.api.gen_menu.g')
    def test_build_datasets_with_type_genotypes(self, db_mock):
        """Test that correct dataset is returned for a phenotype type"""
        db_mock.db.execute.return_value.fetchone.return_value = (
            635, "HLCPublish", "HLC Published Genotypes"
        )

        self.assertEqual(build_datasets("Mouse", "HLC", "Genotypes"),
                         [["635", "HLCGeno", "HLC Genotypes"]])
        db_mock.db.execute.assert_called_with(
            "SELECT InfoFiles.GN_AccesionId FROM InfoFiles, GenoFreeze, InbredSet " +
            "WHERE InbredSet.Name = 'HLC' AND GenoFreeze.InbredSetId = InbredSet.Id AND " +
            "InfoFiles.InfoPageName = GenoFreeze.ShortName " +
            "ORDER BY GenoFreeze.CreateTime DESC"
        )
        db_mock.db.execute.return_value.fetchone.return_value = ()
        self.assertEqual(build_datasets("Mouse", "HLC", "Genotypes"),
                         [["None", "HLCGeno", "HLC Genotypes"]])

    @mock.patch('wqflask.api.gen_menu.g')
    def test_build_datasets_with_type_mrna(self, db_mock):
        """Test that correct dataset is returned for a mRNA expression/ Probeset"""
        db_mock.db.execute.return_value.fetchall.return_value = (
            (112, "HC_M2_0606_P",
             "Hippocampus Consortium M430v2 (Jun06) PDNN"), )
        self.assertEqual(build_datasets("Mouse", "HLC", "mRNA"), [[
            "112", 'HC_M2_0606_P', "Hippocampus Consortium M430v2 (Jun06) PDNN"
        ]])
        db_mock.db.execute.assert_called_once_with(
            "SELECT ProbeSetFreeze.Id, ProbeSetFreeze.Name, " +
            "ProbeSetFreeze.FullName FROM ProbeSetFreeze, " +
            "ProbeFreeze, InbredSet, Tissue, Species WHERE " +
            "Species.Name = 'Mouse' AND Species.Id = " +
            "InbredSet.SpeciesId AND InbredSet.Name = 'HLC' AND " +
            "ProbeSetFreeze.ProbeFreezeId = ProbeFreeze.Id and " +
            "Tissue.Name = 'mRNA' AND ProbeFreeze.TissueId = " +
            "Tissue.Id and ProbeFreeze.InbredSetId = InbredSet.Id " +
            "ORDER BY ProbeSetFreeze.CreateTime DESC")
