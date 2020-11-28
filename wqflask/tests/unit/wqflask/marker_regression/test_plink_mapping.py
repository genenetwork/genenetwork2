# test for wqflask/marker_regression/plink_mapping.py
import unittest
from unittest import mock
from wqflask.marker_regression.plink_mapping import build_line_list
from wqflask.marker_regression.plink_mapping import get_samples_from_ped_file
from wqflask.marker_regression.plink_mapping import flat_files
from wqflask.marker_regression.plink_mapping import gen_pheno_txt_file_plink
from wqflask.marker_regression.plink_mapping import parse_plink_output


class AttributeSetter:
    def __init__(self, obj):
        for key, val in obj.items():
            setattr(self, key, val)
class TestPlinkMapping(unittest.TestCase):


    def test_build_line_list(self):
        """test for building line list"""
        line_1 = "this is line one test"
        irregular_line = "  this     is an, irregular line     "
        exp_line1 = ["this", "is", "line", "one", "test"]

        results = build_line_list(irregular_line)
        self.assertEqual(exp_line1, build_line_list(line_1))
        self.assertEqual([], build_line_list())
        self.assertEqual(["this", "is", "an,", "irregular", "line"], results)

    @mock.patch("wqflask.marker_regression.plink_mapping.flat_files")
    def test_get_samples_from_ped_file(self, mock_flat_files):
        """test for getting samples from ped file"""
        dataset = AttributeSetter({"group": AttributeSetter({"name": "n_1"})})
        file_sample = """Expected_1\tline test
Expected_2\there
  Expected_3\tthree"""
        mock_flat_files.return_value = "/home/user/"
        with mock.patch("builtins.open", mock.mock_open(read_data=file_sample)) as mock_open:
            results = get_samples_from_ped_file(dataset)
            mock_flat_files.assert_called_once_with("mapping")
            mock_open.assert_called_once_with("/home/user/n_1.ped", "r")
            self.assertEqual(
                ["Expected_1", "Expected_2", "Expected_3"], results)

    @mock.patch("wqflask.marker_regression.plink_mapping.TMPDIR", "/home/user/data/")
    @mock.patch("wqflask.marker_regression.plink_mapping.get_samples_from_ped_file")
    def test_gen_pheno_txt_file_plink(self, mock_samples):
        """test for getting gen_pheno txt file"""
        mock_samples.return_value = ["Expected_1", "Expected_2", "Expected_3"]

        trait = AttributeSetter({"name": "TX"})
        dataset = AttributeSetter({"group": AttributeSetter({"name": "n_1"})})
        vals = ["value=K1", "value=K2", "value=K3"]
        with mock.patch("builtins.open", mock.mock_open()) as mock_open:
            results = gen_pheno_txt_file_plink(this_trait=trait, dataset=dataset,
                                               vals=vals, pheno_filename="ph_file")
            mock_open.assert_called_once_with(
                "/home/user/data/ph_file.txt", "wb")
            filehandler = mock_open()
            calls_expected = [mock.call('FID\tIID\tTX\n'),
                              mock.call('Expected_1\tExpected_1\tK1\nExpected_2\tExpected_2\tK2\nExpected_3\tExpected_3\tK3\n')]

            filehandler.write.assert_has_calls(calls_expected)

            filehandler.close.assert_called_once()

    @mock.patch("wqflask.marker_regression.plink_mapping.TMPDIR", "/home/user/data/")
    @mock.patch("wqflask.marker_regression.plink_mapping.build_line_list")
    def test_parse_plink_output(self, mock_line_list):
        """test for parsing plink output"""
        chromosomes = [0, 34, 110, 89, 123, 23, 2]
        species = AttributeSetter(
            {"name": "S1", "chromosomes": AttributeSetter({"chromosomes": chromosomes})})

        fake_file = """0 AACCAT T98.6  0.89\n2  AATA  B45  0.3\n121  ACG  B56.4 NA"""

        mock_line_list.side_effect = [["0", "AACCAT", "T98.6", "0.89"], [
            "2", "AATA", "B45", "0.3"], ["121", "ACG", "B56.4", "NA"]]
        with mock.patch("builtins.open", mock.mock_open(read_data=fake_file)) as mock_open:
            parse_results = parse_plink_output(
                output_filename="P1_file", species=species)
            mock_open.assert_called_once_with(
                "/home/user/data/P1_file.qassoc", "rb")
            expected = (2, {'AACCAT': 0.89, 'AATA': 0.3})

            self.assertEqual(parse_results, expected)
