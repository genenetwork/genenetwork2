import unittest
import datetime
from unittest import mock

from wqflask.marker_regression.run_mapping import get_genofile_samplelist
from wqflask.marker_regression.run_mapping import geno_db_exists
from wqflask.marker_regression.run_mapping import write_input_for_browser
from wqflask.marker_regression.run_mapping import export_mapping_results
from wqflask.marker_regression.run_mapping import trim_markers_for_figure


class AttributeSetter:
    def __init__(self, obj):
        for k, v in obj.items():
            setattr(self, k, v)


class MockDataSetGroup(AttributeSetter):

    def get_genofiles(self):
        return [{"location": "~/genofiles/g1_file", "sample_list": ["S1", "S2", "S3", "S4"]}]


class TestRunMapping(unittest.TestCase):
    def setUp(self):
        self.group = MockDataSetGroup(
            {"genofile": "~/genofiles/g1_file", "name": "GP1_", "species": "Human"})
        self.dataset = AttributeSetter(
            {"fullname": "dataser_1", "group": self.group, "type": "ProbeSet"})
        self.trait = AttributeSetter(
            {"symbol": "IGFI", "chr": "X1", "mb": 123313})

    def tearDown(self):
        self.dataset = AttributeSetter(
            {"group": {"location": "~/genofiles/g1_file"}})

    def test_get_genofile_samplelist(self):

        results_1 = get_genofile_samplelist(self.dataset)
        self.assertEqual(results_1, ["S1", "S2", "S3", "S4"])
        self.group.genofile = "~/genofiles/g2_file"
        result_2 = get_genofile_samplelist(self.dataset)
        self.assertEqual(result_2, [])

    @mock.patch("wqflask.marker_regression.run_mapping.data_set")
    def test_geno_db_exists(self, mock_data_set):
        mock_data_set.create_dataset.side_effect = [
            AttributeSetter({}), Exception()]
        results_no_error = geno_db_exists(self.dataset)
        results_with_error = geno_db_exists(self.dataset)

        self.assertEqual(mock_data_set.create_dataset.call_count, 2)
        self.assertEqual(results_with_error, "False")
        self.assertEqual(results_no_error, "True")

    def test_trim_markers_for_figure(self):

        markers = [{
            "name": "MK1",
            "chr": "C1",
            "cM": "1",
            "Mb": "12000",
            "genotypes": [],
            "dominance":"TT",
            "additive":"VA",
            "lod_score":0.5
        },
            {
            "name": "MK2",
            "chr": "C2",
            "cM": "15",
            "Mb": "10000",
            "genotypes": [],
            "lod_score":0.7
        },
            {
            "name": "MK1",
            "chr": "C3",
            "cM": "45",
            "Mb": "1",
            "genotypes": [],
            "dominance":"Tt",
            "additive":"VE",
            "lod_score":1
        }]

        marker_2 = [{
            "name": "MK1",
            "chr": "C1",
            "cM": "1",
            "Mb": "12000",
            "genotypes": [],
            "dominance":"TT",
            "additive":"VA",
            "p_wald":4.6
        }]
        results = trim_markers_for_figure(markers)
        result_2 = trim_markers_for_figure(marker_2)
        expected = [
            {
                "name": "MK1",
                "chr": "C1",
                "cM": "1",
                "Mb": "12000",
                "genotypes": [],
                "dominance":"TT",
                "additive":"VA",
                "lod_score":0.5
            },
            {
                "name": "MK1",
                "chr": "C3",
                "cM": "45",
                "Mb": "1",
                "genotypes": [],
                "dominance":"Tt",
                "additive":"VE",
                "lod_score":1
            }

        ]
        self.assertEqual(results, expected)
        self.assertEqual(result_2, marker_2)

    def test_export_mapping_results(self):
        datetime_mock = mock.Mock(wraps=datetime.datetime)
        datetime_mock.now.return_value = datetime.datetime(
            2019, 9, 1, 10, 12, 12)

        markers = [{
            "name": "MK1",
            "chr": "C1",
            "cM": "1",
            "Mb": "12000",
            "genotypes": [],
            "dominance":"TT",
            "additive":"VA",
            "lod_score":3
        },
            {
            "name": "MK2",
            "chr": "C2",
            "cM": "15",
            "Mb": "10000",
            "genotypes": [],
            "lod_score":7
        },
            {
            "name": "MK1",
            "chr": "C3",
            "cM": "45",
            "Mb": "1",
            "genotypes": [],
            "dominance":"Tt",
            "additive":"VE",
            "lod_score":7
        }]

        with mock.patch("builtins.open", mock.mock_open()) as mock_open:

            with mock.patch("wqflask.marker_regression.run_mapping.datetime.datetime", new=datetime_mock):
                export_mapping_results(dataset=self.dataset, trait=self.trait, markers=markers,
                                       results_path="~/results", mapping_scale="physic", score_type="-log(p)")

                write_calls = [
                    mock.call('Time/Date: 09/01/19 / 10:12:12\n'),
                    mock.call('Population: Human GP1_\n'), mock.call(
                        'Data Set: dataser_1\n'),
                    mock.call('Gene Symbol: IGFI\n'), mock.call(
                        'Location: X1 @ 123313 Mb\n'),
                    mock.call('\n'), mock.call('Name,Chr,'),
                    mock.call('Mb,-log(p)'), mock.call('Cm,-log(p)'),
                    mock.call(',Additive'), mock.call(',Dominance'),
                    mock.call('\n'), mock.call('MK1,C1,'),
                    mock.call('12000,'), mock.call('1,'),
                    mock.call('3'), mock.call(',VA'),
                    mock.call(',TT'), mock.call('\n'),
                    mock.call('MK2,C2,'), mock.call('10000,'),
                    mock.call('15,'), mock.call('7'),
                    mock.call('\n'), mock.call('MK1,C3,'),
                    mock.call('1,'), mock.call('45,'),
                    mock.call('7'), mock.call(',VE'),
                    mock.call(',Tt')

                ]
                mock_open.assert_called_once_with("~/results", "w+")
                filehandler = mock_open()
                filehandler.write.assert_has_calls(write_calls)


    @mock.patch("wqflask.marker_regression.run_mapping.random.choice")
    def test_write_input_for_browser(self,mock_choice):
    	mock_choice.side_effect=["F","i","l","e","s","x"]
    	with mock.patch("builtins.open",mock.mock_open()) as mock_open:
    		expected=['GP1__Filesx_GWAS', 'GP1__Filesx_ANNOT']

    		results=write_input_for_browser(this_dataset=self.dataset,gwas_results={},annotations={})
    		self.assertEqual(results,expected)
