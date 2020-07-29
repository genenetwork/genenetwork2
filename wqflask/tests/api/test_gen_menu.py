"""Test cases for wqflask.api.gen_menu"""
import unittest
import mock

from wqflask.api.gen_menu import get_species
from wqflask.api.gen_menu import get_groups


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
