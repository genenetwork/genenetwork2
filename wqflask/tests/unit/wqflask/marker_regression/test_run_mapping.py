import unittest
import datetime
from unittest import mock

from wqflask.marker_regression.run_mapping import get_genofile_samplelist
from wqflask.marker_regression.run_mapping import geno_db_exists
from wqflask.marker_regression.run_mapping import write_input_for_browser
from wqflask.marker_regression.run_mapping import export_mapping_results
from wqflask.marker_regression.run_mapping import trim_markers_for_figure
from wqflask.marker_regression.run_mapping import get_perm_strata
from wqflask.marker_regression.run_mapping import get_chr_lengths


class AttributeSetter:
    def __init__(self, obj):
        for k, v in obj.items():
            setattr(self, k, v)


class MockGroup(AttributeSetter):

    def get_genofiles(self):
        return [{"location": "~/genofiles/g1_file", "sample_list": ["S1", "S2", "S3", "S4"]}]


class TestRunMapping(unittest.TestCase):
    def setUp(self):

        self.group = MockGroup(
            {"genofile": "~/genofiles/g1_file", "name": "GP1_", "species": "Human"})
        chromosomes = {
            "3": AttributeSetter({
                "name": "C1",
                "length": "0.04"
            }),
            "4": AttributeSetter({
                "name": "C2",
                "length": "0.03"
            }),
            "5": AttributeSetter({
                "name": "C4",
                "length": "0.01"
            })
        }
        self.dataset = AttributeSetter(
            {"fullname": "dataser_1", "group": self.group, "type": "ProbeSet"})

        self.chromosomes = AttributeSetter({"chromosomes": chromosomes})
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
    def test_if_geno_db_exists(self, mock_data_set):
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
        """test for exporting mapping results"""
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
                                       results_path="~/results", mapping_scale="physic", score_type="-log(p)",
                                       transform="qnorm", covariates="Dataset1:Trait1,Dataset2:Trait2", n_samples="100")

                write_calls = [
                    mock.call('Time/Date: 09/01/19 / 10:12:12\n'),
                    mock.call('Population: Human GP1_\n'), mock.call(
                        'Data Set: dataser_1\n'),
                    mock.call('N Samples: 100\n'), mock.call(
                        'Transform - Quantile Normalized\n'),
                    mock.call('Gene Symbol: IGFI\n'), mock.call(
                        'Location: X1 @ 123313 Mb\n'),
                    mock.call('Cofactors (dataset - trait):\n'),
                    mock.call('Trait1 - Dataset1\n'),
                    mock.call('Trait2 - Dataset2\n'),
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
    def test_write_input_for_browser(self, mock_choice):
        """test for writing input for browser"""
        mock_choice.side_effect = ["F", "i", "l", "e", "s", "x"]
        with mock.patch("builtins.open", mock.mock_open()) as mock_open:
            expected = ['GP1__Filesx_GWAS', 'GP1__Filesx_ANNOT']

            results = write_input_for_browser(
                this_dataset=self.dataset, gwas_results={}, annotations={})
            self.assertEqual(results, expected)

    def test_get_perm_strata(self):
        categorical_vars = ["C1", "C2", "W1"]
        used_samples = ["S1", "S2"]
        sample_list = AttributeSetter({"sample_attribute_values": {
            "S1": {
                "c1": "c1_value",
                "c2": "c2_value",
                "w1": "w1_value"

            },
            "S2": {
                "w1": "w2_value",
                "w2": "w2_value"

            },
            "S3": {

                "c1": "c1_value",
                "c2": "c2_value"

            },

        }})

        results = get_perm_strata(this_trait={}, sample_list=sample_list,
                                  categorical_vars=categorical_vars, used_samples=used_samples)
        self.assertEqual(results, [2, 1])

    def test_get_chr_length(self):
        """test for getting chromosome length"""
        chromosomes = AttributeSetter({"chromosomes": self.chromosomes})
        dataset = AttributeSetter({"species": chromosomes})
        results = get_chr_lengths(
            mapping_scale="physic", mapping_method="reaper", dataset=dataset, qtl_results=[])
        chr_lengths = []
        for key, chromo in self.chromosomes.chromosomes.items():
            chr_lengths.append({"chr": chromo.name, "size": chromo.length})

        self.assertEqual(chr_lengths, results)

        qtl_results = [{
            "chr": "16",
            "cM": "0.2"
        },
            {
            "chr": "12",
            "cM": "0.5"
        },
            {
            "chr": "18",
            "cM": "0.1"
        },
            {
            "chr": "22",
            "cM": "0.4"
        },
        ]

        result_with_other_mapping_scale = get_chr_lengths(
            mapping_scale="other", mapping_method="reaper", dataset=dataset, qtl_results=qtl_results)
        expected_value = [{'chr': '1', 'size': '0'}, {
            'chr': '16', 'size': '500000.0'}, {'chr': '18', 'size': '400000.0'}]

        self.assertEqual(result_with_other_mapping_scale, expected_value)
