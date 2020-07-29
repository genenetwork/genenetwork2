"""Test cases for wqflask.api.gen_menu"""
import unittest
import mock

from wqflask.api.gen_menu import get_species
from wqflask.api.gen_menu import get_groups
from wqflask.api.gen_menu import phenotypes_exist
from wqflask.api.gen_menu import genotypes_exist


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

