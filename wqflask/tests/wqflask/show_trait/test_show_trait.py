"""test for wqflask/show_trait/test_show_trait.py"""
import unittest
from unittest import mock
from wqflask import app
from wqflask.show_trait.show_trait import check_if_attr_exists
from wqflask.show_trait.show_trait import get_ncbi_summary
from wqflask.show_trait.show_trait import has_num_cases
from wqflask.show_trait.show_trait import get_table_widths
from wqflask.show_trait.show_trait import get_categorical_variables
from wqflask.show_trait.show_trait import get_trait_units
from wqflask.show_trait.show_trait import get_nearest_marker
from wqflask.show_trait.show_trait import get_genotype_scales
from wqflask.show_trait.show_trait import requests
from wqflask.show_trait.show_trait import get_scales_from_genofile


class TraitObject:
    def __init__(self, obj):
        for key, value in obj.items():
            setattr(self, key, value)


class TestTraits(unittest.TestCase):
    def setUp(self):
        self.app_context = app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def test_check_if_attr_exists_truthy(self):
        """"test if attributes exists with true return"""
        trait_obj = TraitObject({"id_type": "id"})
        trait_obj2 = TraitObject({"sample_name": ['samp1']})
        results = check_if_attr_exists(trait_obj, "id_type")
        result2 = check_if_attr_exists(trait_obj2, "sample_name")
        self.assertIsInstance(trait_obj, TraitObject)
        self.assertTrue(results)
        self.assertTrue(result2)

    def test_check_if_attr_exists_empty_attr(self):
        """test if attributes exists with false return"""
        trait_obj = TraitObject({"sample": ""})
        trait_obj2 = TraitObject({"group": None})
        result = check_if_attr_exists(trait_obj, "sample")
        result2 = check_if_attr_exists(trait_obj, "group")
        self.assertFalse(result)
        self.assertFalse(result2)

    def test_check_if_attr_exists_falsey(self):
        """check if attribute exists with empty attributes"""
        trait_obj = TraitObject({})
        results = check_if_attr_exists(trait_obj, "any")
        self.assertFalse(results)

    @mock.patch("wqflask.show_trait.show_trait.requests.get")
    @mock.patch("wqflask.show_trait.show_trait.check_if_attr_exists")
    def test_get_ncbi_summary_request_success(self, mock_exists, mock_get):
        """test for getting ncbi summary with 
        successful request"""
        trait = TraitObject({"geneid": "id"})
        mock_exists.return_value = True
        content_json_string = """{
          "result":{
            "id":{
              "summary":"this is a summary of the geneid"
            }
          }
        }
        """
        get_return_obj = TraitObject({"content": content_json_string})
        mock_get.return_value = get_return_obj
        results = get_ncbi_summary(trait)
        mock_exists.assert_called_once()
        mock_get.assert_called_once_with(f"http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=gene&id={trait.geneid}&retmode=json")

        self.assertEqual(results, "this is a summary of the geneid")

    @mock.patch("wqflask.show_trait.show_trait.requests.get")
    @mock.patch("wqflask.show_trait.show_trait.check_if_attr_exists")
    def test_get_ncbi_summary_request_fail(self, mock_exists, mock_get_fail):
        """test for getting ncbi summary with request fail"""
        trait = TraitObject({"geneid": "id"})
        mock_exists.return_value = True
        mock_get_fail.side_effect = Exception("an error occurred")
        content_json_string = """{
          "result":{
            "id":{
              "summary":"this is a summary of the geneid"
            }
          }
        }
        """
        results = get_ncbi_summary(trait)
        self.assertEqual(results, None)

    def test_hash_num_cases_is_probeset(self):
        """test for hash num_cases with dataset.type set to Probeset"""
        create_dataset = TraitObject({"type": "ProbeSet"})
        create_trait = TraitObject({"dataset": create_dataset})
        self.assertFalse(has_num_cases(create_trait))

    def test_hash_num_cases_no_probeset(self):
        """test for hash num cases with dataset.type not Probeset"""
        create_dataset = TraitObject({"type": "Temp"})
        construct_data = {
            "nm1": TraitObject({"num_cases": False}),
            "nm2": TraitObject({"num_cases": True}),
            "nm3": TraitObject({"num_cases": False})
        }
        construct_data2 = {
            "nm1": TraitObject({"num_cases": False}),
            "nm2": TraitObject({"num_cases": False}),
            "nm3": TraitObject({"num_cases": False})
        }
        create_trait = TraitObject(
            {"dataset": create_dataset, "data": construct_data})
        create_trait2 = TraitObject(
            {"dataset": create_dataset, "data": construct_data2})

        results = has_num_cases(create_trait)
        self.assertTrue(has_num_cases(create_trait))
        self.assertFalse(has_num_cases(create_trait2))

    def test_get_table_widths(self):
        """test for getting table widths"""
        sample_groups = [TraitObject({'se_exists': True, "attributes": ["attr1", "attr2", "attr3"]}
                                     ), TraitObject(
            {"se_exists": False, "attributes": ["at1", "at2"]
             })]

        results_with_numcase = get_table_widths(sample_groups, True)
        result_no_numcase = get_table_widths(sample_groups, False)

        results_one_sample = get_table_widths(
            [TraitObject({"se_exists": True, "attributes": []})], True)
        expected_with_numcase = (450, "750px")
        expected_no_numcase = (450, "670px")
        expected_one_sample = (250, "540px")
        self.assertEqual(results_with_numcase, expected_with_numcase)
        self.assertEqual(result_no_numcase, expected_no_numcase)
        self.assertEqual(results_one_sample,
                         expected_one_sample)

    def test_get_categorical_variables_no_sample_attributes(self):
        """test for getting categorical variable names with no samples"""
        trait = TraitObject({})
        sample_list = TraitObject({"se_exists": True, "attributes": []})
        self.assertEqual(get_categorical_variables(trait, sample_list), [])

    def test_get_categorical_variables_with_sample_attributes(self):
        """test for getting categorical variable names with no samples"""
        this_trait = TraitObject({"data": {
            "Gene1": TraitObject({"extra_attributes": {"ex1": "ex1value"}}),
            "Gene2": TraitObject({"extra_attributes": {"ex2": "ex2value"}}),
            "Gene3": TraitObject({"extra_attributes": {"ex3": "ex3value"}})
        }})
        sample_list = TraitObject({"attributes": {
            "sample_attribute_1": TraitObject({"name": "ex1"}),
            "sample_attribute_2": TraitObject({"name": "ex2"}),
            "sample_attribute_3": TraitObject({"name": "ex3"}),
            "sample_attribute_4": TraitObject({"name": "not_in_extra_attributes"})
        }})
        results = get_categorical_variables(this_trait, sample_list)
        self.assertEqual(
            ["ex1", "ex2", "ex3", "not_in_extra_attributes"], results)

    def test_get_trait_units(self):
        """test for getting trait units"""
        trait = TraitObject(
            {"description_fmt": "[this is a description] another test [N/A]"})
        trait_no_unit_type = TraitObject({"description_fmt": ""})
        results = get_trait_units(trait)
        results_no_unit = get_trait_units(trait_no_unit_type)
        self.assertEqual(results, "this is a descriptionN/A")
        self.assertEqual(results_no_unit, "Value")

    @mock.patch("wqflask.show_trait.show_trait.g")
    def test_get_nearest_marker(self, mock_db):
        """test for getting nearest marker with non-empty db"""

        mock_db.db.execute.return_value.fetchall.return_value = [
            ["Geno1", "Geno2"], ["Geno3"]]

        trait = TraitObject({"locus_chr": "test_chr", "locus_mb": "test_mb"})
        group_name = TraitObject({"name": "group_name"})
        this_db = TraitObject({"group": group_name})
        results_with_item_db = get_nearest_marker(trait, this_db)
        called_with_value = """SELECT Geno.Name
               FROM Geno, GenoXRef, GenoFreeze
               WHERE Geno.Chr = 'test_chr' AND
                     GenoXRef.GenoId = Geno.Id AND
                     GenoFreeze.Id = GenoXRef.GenoFreezeId AND
                     GenoFreeze.Name = 'group_nameGeno'
               ORDER BY ABS( Geno.Mb - test_mb) LIMIT 1"""

        mock_db.db.execute.assert_called_with(called_with_value)

        self.assertEqual(results_with_item_db, "Geno1")

    @mock.patch("wqflask.show_trait.show_trait.g")
    def test_get_nearest_marker_empty_db(self, mock_db):
        """test for getting nearest marker with empty db"""
        mock_db.db.execute.return_value.fetchall.return_value = []
        trait = TraitObject({"locus_chr": "test_chr", "locus_mb": "test_mb"})
        group_name = TraitObject({"name": "group_name"})
        this_db = TraitObject({"group": group_name})
        results_empty_db = get_nearest_marker(trait, this_db)
        mock_db.db.execute.assert_called_once()
        self.assertEqual(results_empty_db, "")

    @mock.patch("wqflask.show_trait.show_trait.get_scales_from_genofile")
    def test_get_genotype_scales_with_genofile_is_list(self, mock_get_scales):
        """test for getting genotype scales with genofile as list """
        # where genofile is instance of list
        genofiles_list = [{"filename": "file1", "location": "~/data/files/f1"},
                          {"filename": "file2", "location": "~/data/files/f2"},
                          {"filename": "file3", "location": "~/data/files/f3"}]

        mock_get_scales.side_effect = [[["morgan", "cM"]],
                                       [["morgan", "cM"]],
                                       [["physic", "Mb"]]]

        results = get_genotype_scales(genofiles_list)
        expected_results = {
            "~/data/files/f1": [["morgan", "cM"]],
            "~/data/files/f2": [["morgan", "cM"]],
            "~/data/files/f3": [["physic", "Mb"]]
        }

        multiple_calls = [mock.call('~/data/files/f1'), mock.call('~/data/files/f2'),
                          mock.call('~/data/files/f3')]
        mock_get_scales.assert_has_calls(multiple_calls)
        self.assertEqual(results, expected_results)

    @mock.patch("wqflask.show_trait.show_trait.get_scales_from_genofile")
    def test_genotype_scales_with_genofile_other(self, mock_get_scales):
        """test for getting genotype scales with genofile as a string"""
        file_location = "~/another_file_location"
        mock_get_scales.return_value = [["physic", "Mb"]]
        expected_results = {f"{file_location}": [["physic", "Mb"]]}
        self.assertEqual(get_genotype_scales(file_location), expected_results)
        mock_get_scales.assert_called_once_with(file_location)


    @mock.patch("wqflask.show_trait.show_trait.locate_ignore_error")
    def test_get_scales_from_genofile_found(self, mock_ignore_location):
        """"add test for get scales from genofile where file is found"""
        mock_ignore_location.return_value = True
        geno_file = """
                #sample line    with no  @scales:other\n
                #sample line     @scales and :separated   by semicolon\n
                This attempts    to check whether\n
                """

        geno_file_string = "@line start with  @ and has @scale:morgan"

        file_location = "~/data/file.geno"

        mock_open_geno_file = mock.mock_open(read_data=geno_file)
        with mock.patch("builtins.open", mock_open_geno_file):
            results = get_scales_from_genofile(file_location)
            self.assertEqual(results, [["morgan", "cM"]])

        mock_open_string = mock.mock_open(read_data=geno_file_string)

        with mock.patch("builtins.open", mock_open_string):
            result2 = get_scales_from_genofile(file_location)
            self.assertEqual([['morgan', 'cM']], result2)

    @mock.patch("wqflask.show_trait.show_trait.locate_ignore_error")
    def test_get_scales_from_genofile_not_found(self, mock_location_ignore):
        mock_location_ignore.return_value = False

        expected_results = [["physic", "Mb"]]
        results = get_scales_from_genofile("~/data/file")
        mock_location_ignore.assert_called_once_with("~/data/file", "genotype")
        self.assertEqual(results, expected_results)
