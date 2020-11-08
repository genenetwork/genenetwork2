#test for wqflask/marker_regression/gemma_mapping.py
import unittest
import random
from unittest import mock
from wqflask.marker_regression.gemma_mapping import run_gemma
from wqflask.marker_regression.gemma_mapping import gen_pheno_txt_file
from wqflask.marker_regression.gemma_mapping import gen_covariates_file
from wqflask.marker_regression.gemma_mapping import parse_gemma_output
from wqflask.marker_regression.gemma_mapping import parse_loco_output


class AttributeSetter:
    def __init__(self, obj):
        for key, val in obj.items():
            setattr(self, key, val)


class MockDatasetGroup(AttributeSetter):
    def get_samplelist(self):
        return None


class TestGemmaMapping(unittest.TestCase):
    # def test_fail(self):
    #     self.assertEqual(2,3)

    @mock.patch("wqflask.marker_regression.gemma_mapping.TEMPDIR", "/home/user/data")
    def setUp(self):
    	pass

    @mock.patch("wqflask.marker_regression.gemma_mapping.gen_pheno_txt_file")
    @mock.patch("wqflask.marker_regression.gemma_mapping.os")
    def test_run_gemma_first_run_set_true(self, mock_gen_pheno, mock_os):
        chromosomes = AttributeSetter({"chromosomes": "SA"})
        covariates = "XI:X2,X4:X3,X6:X7"
        dataset_group = MockDatasetGroup({"genofile": "fileX"})
        dataset = AttributeSetter(
            {"group": dataset_group, "name": "dataset1_name", "species": chromosomes})
        trait = AttributeSetter({"name": "trait1"})
        mock_gen_pheno.side_effect = None
        mock_gen_pheno.return_value = None
        mock_os.path.isfile.return_value = True

    @mock.patch("wqflask.marker_regression.gemma_mapping.parse_loco_output")
    def test_run_gemma_first_run_loco_set_false(self, mock_parse_loco):
        dataset = AttributeSetter(
            {"group": AttributeSetter({"genofile": "genofile.geno"})})

        output_files = "file1"
        use_loco = False
        mock_parse_loco.side_effect = None
        mock_parse_loco.return_value = []
        this_trait = AttributeSetter({"name": "t1"})

        result = run_gemma(this_trait=this_trait, this_dataset=dataset, samples=[], vals=[
        ], covariates="", use_loco=True, first_run=False, output_files=output_files)

        expected_results = ([], "file1")
        self.assertEqual(expected_results, result)

    @mock.patch("wqflask.marker_regression.gemma_mapping.TEMPDIR", "/home/user/data")
    def test_gen_pheno_txt_file(self):
        with mock.patch("builtins.open", mock.mock_open())as mock_open:
            gen_pheno_txt_file(this_dataset={}, genofile_name="", vals=[
                               "x", "w", "q", "we", "R"], trait_filename="fitr.re")

            mock_open.assert_called_once_with(
                '/home/user/data/gn2/fitr.re.txt', 'w')
            filehandler = mock_open()
            values = ["x", "w", "q", "we", "R"]
            write_calls = [mock.call('NA\n'), mock.call('w\n'), mock.call(
                'q\n'), mock.call('we\n'), mock.call('R\n')]

            filehandler.write.assert_has_calls(write_calls)

    @mock.patch("wqflask.marker_regression.gemma_mapping.flat_files")
    @mock.patch("wqflask.marker_regression.gemma_mapping.create_trait")
    @mock.patch("wqflask.marker_regression.gemma_mapping.create_dataset")
    def test_gen_covariates_file(self, create_dataset, create_trait, flat_files):
        covariates = "X1:X2,Y1:Y2,M1:M3,V1:V2"
        samplelist = ["X1", "X2", "X3", "X4"]
        create_dataset_side_effect = []
        create_trait_side_effect = []

        for i in range(4):
            create_dataset_side_effect.append(AttributeSetter({"name": f'name_{i}'}))
            create_trait_side_effect.append(
                AttributeSetter({"data": [f'data_{i}']}))

        create_dataset.side_effect = create_trait_side_effect
        create_trait.side_effect = create_trait_side_effect

        group = MockDatasetGroup({"name": "group_X", "samplelist": samplelist})
        this_dataset = AttributeSetter({"group": group})
        flat_files.return_value = "Home/Genenetwork"

        with mock.patch("builtins.open", mock.mock_open())as mock_open:
            gen_covariates_file(this_dataset=this_dataset, covariates=covariates,
                                samples=["x1", "x2", "X3"])
            # test mocked methods

            create_dataset.assert_has_calls(
                [mock.call('X2'), mock.call('Y2'), mock.call('M3'), mock.call('V2')])
            mock_calls = []
            trait_names = ["X1", "Y1", "M1", "V1"]

            for i, trait in enumerate(create_trait_side_effect):
                mock_calls.append(
                    mock.call(dataset=trait, name=trait_names[i], cellid=None))

            create_trait.assert_has_calls(mock_calls)

            # test writing of covariates.txt

            flat_files.assert_called_once_with('mapping')
            mock_open.assert_called_once_with(
                'Home/Genenetwork/group_X_covariates.txt', 'w')
            filehandler = mock_open()
            # expected all-9
            filehandler.write.assert_has_calls([mock.call(
                '-9\t'), mock.call('-9\t'), mock.call('-9\t'), mock.call('-9\t'), mock.call('\n')])

    @mock.patch("wqflask.marker_regression.gemma_mapping.webqtlConfig.GENERATED_IMAGE_DIR", "/home/user/img/")
    def test_parse_gemma_output_obj_returned(self):
        file = """X/Y\t gn2\t21\tQ\tE\tA\tP\tMMB\tCDE\t0.5
X/Y\tgn2\t21322\tQ\tE\tA\tP\tMMB\tCDE\t0.5
chr\tgn1\t12312\tQ\tE\tA\tP\tMMB\tCDE\t0.7
X\tgn7\t2324424\tQ\tE\tA\tP\tMMB\tCDE\t0.4
125\tgn9\t433575\tQ\tE\tA\tP\tMMB\tCDE\t0.67
"""
        with mock.patch("builtins.open", mock.mock_open(read_data=file)) as mock_open:
            results = parse_gemma_output(genofile_name="gema_file")
            expected =  [{'name': ' gn2', 'chr': 'X/Y', 'Mb': 2.1e-05, 'p_value': 0.5, 'lod_score': 0.3010299956639812}, {'name': 'gn2', 'chr': 'X/Y', 'Mb': 0.021322, 'p_value': 0.5, 'lod_score': 0.3010299956639812}, {'name': 'gn7', 'chr': 'X', 'Mb': 2.324424, 'p_value': 0.4, 'lod_score': 0.3979400086720376}, {'name': 'gn9', 'chr': 125, 'Mb': 0.433575, 'p_value': 0.67, 'lod_score': 0.17392519729917352}]

            mock_open.assert_called_once_with(
                "/home/user/img/gema_file_output.assoc.txt")

            self.assertEqual(results, expected)

    @mock.patch("wqflask.marker_regression.gemma_mapping.webqtlConfig.GENERATED_IMAGE_DIR", "/home/user/img")
    def test_xparse_gemma_output_empty_return(self):
        output_file_results = """chr\t today"""
        with mock.patch("builtins.open", mock.mock_open(read_data=output_file_results)) as mock_open:
            results = parse_gemma_output(genofile_name="gema_file")
            self.assertEqual(results, [])

    @mock.patch("builtins.open", mock.mock_open(read_data="chr\t"))
    def test_parse_gemma_output_empty_return(self):
    	#duplicate
        string_read = parse_gemma_output(genofile_name="hdf")
        # print(string_read)

    @mock.patch("wqflask.marker_regression.gemma_mapping.TEMPDIR", "/home/tmp")
    @mock.patch("wqflask.marker_regression.gemma_mapping.os")
    def test_parse_loco_output_file_found(self, mock_os):
        mock_os.path.isfile.return_value = False
        file_to_write = """{"files":["file_1","file_2"]}"""


    @mock.patch("wqflask.marker_regression.gemma_mapping.TEMPDIR", "/home/tmp")
    @mock.patch("wqflask.marker_regression.gemma_mapping.os")
    def test_parse_loco_output_file_not_found(self, mock_os):

        mock_os.path.isfile.return_value = False
        file_to_write = """{"files":["file_1","file_2"]}"""

        with mock.patch("builtins.open", mock.mock_open(read_data=file_to_write)) as mock_open:
            results = parse_loco_output(
                this_dataset={}, gwa_output_filename=".xw/")
            self.assertEqual(results, [])
