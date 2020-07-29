"""Test cases for wqflask.api.gen_menu"""
import unittest
import mock

from wqflask.api.gen_menu import get_species

class TestGenMenu(unittest.TestCase):
    """Tests for the gen_menu module"""

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
