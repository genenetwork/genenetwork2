"""Test cases for wqflask.api.gen_menu"""
import unittest
from unittest import mock

from wqflask.api.gen_menu import gen_dropdown_json
from wqflask.api.gen_menu import get_groups
from wqflask.api.gen_menu import get_types
from wqflask.api.gen_menu import get_datasets
from wqflask.api.gen_menu import phenotypes_exist
from wqflask.api.gen_menu import genotypes_exist
from wqflask.api.gen_menu import build_datasets
from wqflask.api.gen_menu import build_types


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

        self.test_type = {
            'mouse': {
                'H_T2': [('Phenotypes',
                          'Traits and Cofactors',
                          'Phenotypes'),
                         ('Genotypes',
                          'DNA Markers and SNPs',
                          'Genotypes'),
                         ['M', 'M', 'Molecular Trait Datasets']],
                'H_T1': [('Phenotypes',
                          'Traits and Cofactors',
                          'Phenotypes'),
                         ('Genotypes',
                          'DNA Markers and SNPs',
                          'Genotypes'),
                         ['M', 'M', 'Molecular Trait Datasets']]
            },
            'human': {
                'HLC': [('Phenotypes',
                         'Traits and Cofactors',
                         'Phenotypes'),
                        ('Genotypes',
                         'DNA Markers and SNPs',
                         'Genotypes'),
                        ['M', 'M', 'Molecular Trait Datasets']],
                'BXD': [('Phenotypes',
                         'Traits and Cofactors',
                         'Phenotypes'),
                        ('Genotypes',
                         'DNA Markers and SNPs',
                         'Genotypes'),
                        ['M', 'M', 'Molecular Trait Datasets']]
            }
        }

    def test_get_groups(self):
        """Test that species groups are grouped correctly"""
        db_mock = mock.MagicMock()
        with db_mock.cursor() as cursor:
            cursor.fetchall.side_effect = [
                # Mouse
                (('BXD', 'BXD', None),
                 ('HLC', ('Liver: Normal Gene Expression '
                          'with Genotypes (Merck)'),
                  'Test')),
                # Human
                (('H_T1', "H_T", "DescriptionA"),
                 ('H_T2', "H_T'", None))
            ]
            self.assertEqual(get_groups([["human", "Human"],
                                         ["mouse", "Mouse"]],
                                        db_mock),
                             self.test_group)

            for name in ["mouse", "human"]:
                cursor.execute.assert_any_call(
                    ("SELECT InbredSet.Name, InbredSet.FullName, "
                     "IFNULL(InbredSet.Family, 'None') "
                     "FROM InbredSet, Species WHERE Species.Name "
                     "= '{}' AND InbredSet.SpeciesId = Species.Id GROUP by "
                     "InbredSet.Name ORDER BY IFNULL(InbredSet.FamilyOrder, "
                     "InbredSet.FullName) ASC, IFNULL(InbredSet.Family, "
                     "InbredSet.FullName) ASC, InbredSet.FullName ASC, "
                     "InbredSet.MenuOrderId ASC").format(name)
                )

    def test_phenotypes_exist_called_with_correct_query(self):
        """Test that phenotypes_exist is called with the correct query"""
        db_mock = mock.MagicMock()
        with db_mock.cursor() as cursor:
            cursor.fetchone.return_value = None
            phenotypes_exist("test", db_mock)
            cursor.execute.assert_called_with(
                "SELECT Name FROM PublishFreeze "
                "WHERE PublishFreeze.Name = 'testPublish'"
            )

    def test_phenotypes_exist_with_falsy_values(self):
        """Test that phenotype check returns correctly when given
        a None value"""
        db_mock = mock.MagicMock()
        with db_mock.cursor() as cursor:
            for x in [None, False, (), [], ""]:
                cursor.fetchone.return_value = x
            self.assertFalse(phenotypes_exist("test", db_mock))

    def test_phenotypes_exist_with_truthy_value(self):
        """Test that phenotype check returns correctly when given Truthy"""
        db_mock = mock.MagicMock()
        with db_mock.cursor() as conn:
            with conn.cursor() as cursor:
                for x in ["x", ("result"), ["result"], [1]]:
                    cursor.fetchone.return_value = (x)
                self.assertTrue(phenotypes_exist("test", db_mock))

    def test_genotypes_exist_called_with_correct_query(self):
        """Test that genotypes_exist is called with the correct query"""
        db_mock = mock.MagicMock()
        with db_mock.cursor() as cursor:
            cursor.fetchone.return_value = None
            genotypes_exist("test", db_mock)
            cursor.execute.assert_called_with(
                "SELECT Name FROM GenoFreeze WHERE "
                "GenoFreeze.Name = 'testGeno'"
            )

    def test_genotypes_exist_with_falsy_values(self):
        """Test that genotype check returns correctly when given a None value

        """
        db_mock = mock.MagicMock()
        with db_mock.cursor() as cursor:
            for x in [None, False, (), [], ""]:
                cursor.fetchone.return_value = x
                self.assertFalse(genotypes_exist("test", db_mock))

    def test_genotypes_exist_with_truthy_value(self):
        """Test that genotype check returns correctly when given Truthy """
        db_mock = mock.MagicMock()
        with db_mock.cursor() as cursor:
            for x in ["x", ("result"), ["result"], [1]]:
                cursor.fetchone.return_value = (x)
                self.assertTrue(phenotypes_exist("test", db_mock))

    def test_build_datasets_with_type_phenotypes(self):
        """Test that correct dataset is returned for a phenotype type"""
        db_mock = mock.MagicMock()
        with db_mock.cursor() as cursor:
            cursor.fetchall.return_value = (
                (602, "BXDPublish", "BXD Published Phenotypes"),
            )
            self.assertEqual(build_datasets("Mouse", "BXD",
                                            "Phenotypes", db_mock),
                             [['602', "BXDPublish",
                               "BXD Published Phenotypes"]])
            cursor.execute.assert_called_with(
                "SELECT InfoFiles.GN_AccesionId, PublishFreeze.Name, "
                + "PublishFreeze.FullName FROM InfoFiles, PublishFreeze, "
                + "InbredSet WHERE InbredSet.Name = 'BXD' AND "
                + "PublishFreeze.InbredSetId = InbredSet.Id AND "
                + "InfoFiles.InfoPageName = PublishFreeze.Name "
                + "ORDER BY PublishFreeze.CreateTime ASC"
            )
            self.assertEqual(build_datasets("Mouse", "MDP",
                                            "Phenotypes", db_mock),
                             [['602', "BXDPublish",
                               "Mouse Phenome Database"]])

            cursor.fetchall.return_value = ()
            cursor.fetchone.return_value = (
                "BXDPublish", "Mouse Phenome Database"
            )
            self.assertEqual(build_datasets("Mouse", "MDP",
                                            "Phenotypes", db_mock),
                             [["None", "BXDPublish",
                               "Mouse Phenome Database"]])

    def test_build_datasets_with_type_phenotypes_and_no_results(self):
        """Test that correct dataset is returned for a phenotype type with no
        results

        """
        db_mock = mock.MagicMock()
        with db_mock.cursor() as cursor:
            cursor.fetchall.return_value = None
            cursor.fetchone.return_value = (121,
                                            "text value")
            self.assertEqual(build_datasets("Mouse", "BXD",
                                            "Phenotypes", db_mock),
                             [["None", "121",
                               "text value"]])
            cursor.execute.assert_called_with(
                "SELECT PublishFreeze.Name, PublishFreeze.FullName "
                "FROM PublishFreeze, InbredSet "
                "WHERE InbredSet.Name = 'BXD' AND "
                "PublishFreeze.InbredSetId = InbredSet.Id "
                "ORDER BY PublishFreeze.CreateTime ASC"
            )

    def test_build_datasets_with_type_genotypes(self):
        """Test that correct dataset is returned for a phenotype type"""
        db_mock = mock.MagicMock()
        with db_mock.cursor() as cursor:
            cursor.fetchone.return_value = (
                635, "HLCPublish", "HLC Published Genotypes"
            )
            self.assertEqual(build_datasets("Mouse", "HLC",
                                            "Genotypes", db_mock),
                             [["635", "HLCGeno", "HLC Genotypes"]])
            cursor.execute.assert_called_with(
                "SELECT InfoFiles.GN_AccesionId FROM InfoFiles, "
                "GenoFreeze, InbredSet WHERE InbredSet.Name = 'HLC' AND "
                "GenoFreeze.InbredSetId = InbredSet.Id AND "
                "InfoFiles.InfoPageName = GenoFreeze.ShortName "
                "ORDER BY GenoFreeze.CreateTime DESC"
            )
            cursor.fetchone.return_value = ()
            self.assertEqual(build_datasets("Mouse", "HLC",
                                            "Genotypes", db_mock),
                             [["None", "HLCGeno", "HLC Genotypes"]])

    def test_build_datasets_with_type_mrna(self):
        """Test that correct dataset is returned for a mRNA
        expression/ Probeset"""
        db_mock = mock.MagicMock()
        with db_mock.cursor() as cursor:
            cursor.fetchall.return_value = (
                (112, "HC_M2_0606_P",
                 "Hippocampus Consortium M430v2 (Jun06) PDNN"), )
            self.assertEqual(build_datasets("Mouse",
                                            "HLC", "mRNA", db_mock),
                             [["112", 'HC_M2_0606_P',
                               "Hippocampus Consortium M430v2 (Jun06) PDNN"
                               ]])
            cursor.execute.assert_called_once_with(
                "SELECT ProbeSetFreeze.Id, ProbeSetFreeze.Name, "
                "ProbeSetFreeze.FullName FROM ProbeSetFreeze, "
                "ProbeFreeze, InbredSet, Tissue, Species WHERE "
                "Species.Name = 'Mouse' AND Species.Id = "
                "InbredSet.SpeciesId AND InbredSet.Name = 'HLC' AND "
                "ProbeSetFreeze.ProbeFreezeId = ProbeFreeze.Id AND "
                "Tissue.Name = 'mRNA' AND ProbeFreeze.TissueId = "
                "Tissue.Id AND ProbeFreeze.InbredSetId = InbredSet.Id AND "
                "ProbeSetFreeze.public > 0 "
                "ORDER BY -ProbeSetFreeze.OrderList DESC, "
                "ProbeSetFreeze.CreateTime DESC")

    @mock.patch('wqflask.api.gen_menu.build_datasets')
    def test_build_types(self, datasets_mock):
        """Test that correct tissue metadata is returned"""
        db_mock = mock.MagicMock()
        datasets_mock.return_value = [
            ["112", 'HC_M2_0606_P',
                "Hippocampus Consortium M430v2 (Jun06) PDNN"]
        ]
        with db_mock.cursor() as cursor:
            cursor.fetchall.return_value = (
                ('Mouse Tissue'), ('Human Tissue'), ('Rat Tissue')
            )
            self.assertEqual(build_types('mouse', 'random group', db_mock),
                             [['M', 'M', 'Molecular Traits'],
                              ['H', 'H', 'Molecular Traits'],
                              ['R', 'R', 'Molecular Traits']])
            cursor.execute.assert_called_once_with(
                "SELECT DISTINCT Tissue.Name "
                "FROM ProbeFreeze, ProbeSetFreeze, InbredSet, "
                "Tissue, Species WHERE Species.Name = 'mouse' "
                "AND Species.Id = InbredSet.SpeciesId AND "
                "InbredSet.Name = 'random group' AND "
                "ProbeFreeze.TissueId = Tissue.Id AND "
                "ProbeFreeze.InbredSetId = InbredSet.Id AND "
                "ProbeSetFreeze.ProbeFreezeId = ProbeFreeze.Id "
                "ORDER BY Tissue.Name"
            )

    @mock.patch('wqflask.api.gen_menu.build_types')
    @mock.patch('wqflask.api.gen_menu.genotypes_exist')
    @mock.patch('wqflask.api.gen_menu.phenotypes_exist')
    def test_get_types_with_existing_genotype_and_phenotypes(
            self,
            phenotypes_exist_mock,
            genotypes_exist_mock,
            build_types_mock):
        """Test that build types are constructed correctly if phenotypes and genotypes
        exist

        """
        phenotypes_exist_mock.return_value = True
        genotypes_exist_mock.return_value = True

        expected_result = self.test_type

        build_types_mock.return_value = [
            ['M', 'M', 'Molecular Trait Datasets']
        ]
        self.assertEqual(get_types(self.test_group,
                                   mock.MagicMock()),
                         expected_result)

    @mock.patch('wqflask.api.gen_menu.build_types')
    @mock.patch('wqflask.api.gen_menu.genotypes_exist')
    @mock.patch('wqflask.api.gen_menu.phenotypes_exist')
    def test_get_types_with_buildtype_and_non_existent_genotype_and_phenotypes(
            self,
            phenotypes_exist_mock,
            genotypes_exist_mock,
            build_types_mock):
        """Test that build types are constructed correctly if phenotypes_exist and
        genotypes_exist are false but build_type is falsy

        """
        phenotypes_exist_mock.return_value = False
        genotypes_exist_mock.return_value = False

        build_types_mock.return_value = []
        self.assertEqual(get_types(self.test_group, mock.MagicMock()),
                         {'mouse': {}, 'human': {}})

    @mock.patch('wqflask.api.gen_menu.build_types')
    @mock.patch('wqflask.api.gen_menu.genotypes_exist')
    @mock.patch('wqflask.api.gen_menu.phenotypes_exist')
    def test_get_types_with_non_existent_genotype_phenotypes_and_buildtype(
            self,
            phenotypes_exist_mock,
            genotypes_exist_mock,
            build_types_mock):
        """Test that build types are constructed correctly if phenotypes_exist,
        genotypes_exist and build_types are truthy

        """
        phenotypes_exist_mock.return_value = False
        genotypes_exist_mock.return_value = False

        build_types_mock.return_value = [
            ['M', 'M', 'Molecular Trait Datasets']
        ]
        expected_result = {
            'mouse': {
                'H_T2': [['M', 'M', 'Molecular Trait Datasets']],
                'H_T1': [['M', 'M', 'Molecular Trait Datasets']]},
            'human': {
                'HLC': [['M', 'M', 'Molecular Trait Datasets']],
                'BXD': [['M', 'M', 'Molecular Trait Datasets']]}}
        self.assertEqual(get_types(self.test_group, mock.MagicMock()),
                         expected_result)

    @mock.patch('wqflask.api.gen_menu.build_datasets')
    def test_get_datasets_with_existent_datasets(self,
                                                 build_datasets_mock):
        """Test correct dataset is returned with existent build_datasets"""
        build_datasets_mock.return_value = "Test"
        expected_result = {
            'mouse': {
                'H_T2': {'Genotypes': 'Test',
                         'M': 'Test',
                         'Phenotypes': 'Test'},
                'H_T1': {'Genotypes': 'Test',
                         'M': 'Test',
                         'Phenotypes': 'Test'}},
            'human': {'HLC': {'Genotypes': 'Test',
                              'M': 'Test',
                              'Phenotypes': 'Test'},
                      'BXD': {'Genotypes': 'Test',
                              'M': 'Test',
                              'Phenotypes': 'Test'}}}
        self.assertEqual(get_datasets(self.test_type, mock.MagicMock()),
                         expected_result)

    @mock.patch('wqflask.api.gen_menu.build_datasets')
    def test_get_datasets_with_non_existent_datasets(self,
                                                     build_datasets_mock):
        """Test correct dataset is returned with non-existent build_datasets"""
        build_datasets_mock.return_value = None
        expected_result = {
            'mouse': {
                'H_T2': {},
                'H_T1': {}},
            'human': {'HLC': {},
                      'BXD': {}}}
        self.assertEqual(get_datasets(self.test_type, mock.MagicMock()),
                         expected_result)

    @mock.patch('wqflask.api.gen_menu.get_datasets')
    @mock.patch('wqflask.api.gen_menu.get_types')
    @mock.patch('wqflask.api.gen_menu.get_groups')
    @mock.patch('wqflask.api.gen_menu.get_all_species')
    def test_gen_dropdown_json(self,
                               species_mock,
                               groups_mock,
                               types_mock,
                               datasets_mock):
        "Test that the correct dictionary is constructed properly"
        species_mock.return_value = ("speciesA speciesB speciesC speciesD"
                                     .split(" "))
        datasets_mock.return_value = ("datasetA datasetB datasetC datasetD"
                                      .split(" "))
        groups_mock.return_value = ("groupA groupB groupC groupD"
                                    .split(" "))
        types_mock.return_value = ("typeA typeB typeC typeD"
                                   .split(" "))
        datasets_mock.return_value = ("datasetA datasetB datasetC datasetD"
                                      .split(" "))

        expected_result = {
            'datasets': ['datasetA', 'datasetB', 'datasetC', 'datasetD'],
            'types': ['typeA', 'typeB', 'typeC', 'typeD'],
            'groups': ['groupA', 'groupB', 'groupC', 'groupD'],
            'species': ['speciesA', 'speciesB', 'speciesC', 'speciesD']}

        self.assertEqual(gen_dropdown_json(mock.MagicMock()), expected_result)
