# test for wqflask/marker_regression/gemma_mapping.py
import unittest
import random
from unittest import mock
from wqflask.marker_regression.gemma_mapping import run_gemma
from wqflask.marker_regression.gemma_mapping import gen_pheno_txt_file
from wqflask.marker_regression.gemma_mapping import gen_covariates_file
from wqflask.marker_regression.gemma_mapping import parse_loco_output


class AttributeSetter:
    def __init__(self, obj):
        for key, val in obj.items():
            setattr(self, key, val)


class MockGroup(AttributeSetter):
    def get_samplelist(self):
        return None


class TestGemmaMapping(unittest.TestCase):

    @mock.patch("wqflask.marker_regression.gemma_mapping.parse_loco_output")
    def test_run_gemma_firstrun_set_false(self, mock_parse_loco):
        """add tests for gemma function where  first run is set to false"""
        dataset = AttributeSetter(
            {"group": AttributeSetter({"genofile": "genofile.geno"})})

        output_file = "file1"
        mock_parse_loco.return_value = []
        this_trait = AttributeSetter({"name": "t1"})

        result = run_gemma(this_trait=this_trait, this_dataset=dataset, samples=[], vals=[
        ], covariates="", use_loco=True, first_run=False, output_files=output_file)

        expected_results = ([], "file1")
        self.assertEqual(expected_results, result)

    @mock.patch("wqflask.marker_regression.gemma_mapping.webqtlConfig.GENERATED_IMAGE_DIR", "/home/user/img")
    @mock.patch("wqflask.marker_regression.gemma_mapping.GEMMAOPTS", "-debug")
    @mock.patch("wqflask.marker_regression.gemma_mapping.GEMMA_WRAPPER_COMMAND", "ghc")
    @mock.patch("wqflask.marker_regression.gemma_mapping.TEMPDIR", "/home/user/data/")
    @mock.patch("wqflask.marker_regression.gemma_mapping.parse_loco_output")
    @mock.patch("wqflask.marker_regression.gemma_mapping.flat_files")
    @mock.patch("wqflask.marker_regression.gemma_mapping.gen_covariates_file")
    @mock.patch("wqflask.marker_regression.run_mapping.random.choice")
    @mock.patch("wqflask.marker_regression.gemma_mapping.os")
    @mock.patch("wqflask.marker_regression.gemma_mapping.gen_pheno_txt_file")
    def test_run_gemma_firstrun_set_true(self, mock_gen_pheno_txt, mock_os, mock_choice, mock_gen_covar, mock_flat_files,mock_parse_loco):
        """add tests for run_gemma where first run is set to true"""
        this_chromosomes={}
        for i in range(1, 5):
            this_chromosomes[f'CH{i}']=(AttributeSetter({"name": f"CH{i}"}))
        chromosomes = AttributeSetter({"chromosomes": this_chromosomes})

        dataset_group = MockGroup(
            {"name": "GP1", "genofile": "file_geno"})
        dataset = AttributeSetter({"group": dataset_group, "name": "dataset1_name",
                                   "species": AttributeSetter({"chromosomes": chromosomes})})
        trait = AttributeSetter({"name": "trait1"})
        samples = []
        mock_gen_pheno_txt.return_value = None
        mock_os.path.isfile.return_value = True
        mock_gen_covar.return_value = None
        mock_choice.return_value = "R"
        mock_flat_files.return_value = "/home/genotype/bimbam"
        mock_parse_loco.return_value = []
        results = run_gemma(this_trait=trait, this_dataset=dataset, samples=[
        ], vals=[], covariates="", use_loco=True)
        self.assertEqual(mock_os.system.call_count,2)
        mock_gen_pheno_txt.assert_called_once()
        mock_parse_loco.assert_called_once_with(dataset, "GP1_GWA_RRRRRR",True)
        mock_os.path.isfile.assert_called_once_with(
            ('/home/user/imgfile_output.assoc.txt'))
        self.assertEqual(mock_flat_files.call_count, 4)
        self.assertEqual(results, ([], "GP1_GWA_RRRRRR"))

    @mock.patch("wqflask.marker_regression.gemma_mapping.TEMPDIR", "/home/user/data")
    def test_gen_pheno_txt_file(self):
        """add tests for generating pheno txt file"""
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
        """add tests for generating covariates files"""
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

        group = MockGroup({"name": "group_X", "samplelist": samplelist})
        this_dataset = AttributeSetter({"group": group})
        flat_files.return_value = "Home/Genenetwork"

        with mock.patch("builtins.open", mock.mock_open())as mock_open:
            gen_covariates_file(this_dataset=this_dataset, covariates=covariates,
                                samples=["x1", "x2", "X3"])

            create_dataset.assert_has_calls(
                [mock.call('X2'), mock.call('Y2'), mock.call('M3'), mock.call('V2')])
            mock_calls = []
            trait_names = ["X1", "Y1", "M1", "V1"]

            for i, trait in enumerate(create_trait_side_effect):
                mock_calls.append(
                    mock.call(dataset=trait, name=trait_names[i], cellid=None))

            create_trait.assert_has_calls(mock_calls)

            flat_files.assert_called_once_with('mapping')
            mock_open.assert_called_once_with(
                'Home/Genenetwork/group_X_covariates.txt', 'w')
            filehandler = mock_open()
            filehandler.write.assert_has_calls([mock.call(
                '-9\t'), mock.call('-9\t'), mock.call('-9\t'), mock.call('-9\t'), mock.call('\n')])

    @mock.patch("wqflask.marker_regression.gemma_mapping.TEMPDIR", "/home/tmp")
    @mock.patch("wqflask.marker_regression.gemma_mapping.os")
    @mock.patch("wqflask.marker_regression.gemma_mapping.json")
    def test_parse_loco_outputfile_found(self, mock_json, mock_os):
        """add tests for parse loco output file found"""
        mock_json.load.return_value = {
            "files": [["file_name", "user", "~/file1"],
                      ["file_name", "user", "~/file2"]]
        }
        return_file="""X/Y\tM1\t28.457155\tQ\tE\tA\tMMB\t23.3\tW\t0.9\t0.85\t
chr4\tM2\t12\tQ\tE\tMMB\tR\t24\tW\t0.87\t0.5
Y\tM4\t12\tQ\tE\tMMB\tR\t11.6\tW\t0.21\t0.7
X\tM5\t12\tQ\tE\tMMB\tR\t21.1\tW\t0.65\t0.6"""

        return_file_2 = """chr\tother\t21322\tQ\tE\tA\tP\tMMB\tCDE\t0.5\t0.4"""
        mock_os.path.isfile.return_value = True
        file_to_write = """{"files":["file_1","file_2"]}"""
        with mock.patch("builtins.open") as mock_open:

            handles = (mock.mock_open(read_data="gwas").return_value, mock.mock_open(
                read_data=return_file).return_value, mock.mock_open(read_data=return_file_2).return_value)
            mock_open.side_effect = handles
            results = parse_loco_output(
                this_dataset={}, gwa_output_filename=".xw/")
            expected_results= [
            {'name': 'M1', 'chr': 'X/Y', 'Mb': 2.8457155e-05, 'p_value': 0.85, 'additive': 23.3, 'lod_score': 0.07058107428570727},
            {'name': 'M2', 'chr': 4, 'Mb': 1.2e-05, 'p_value': 0.5, 'additive': 24.0, 'lod_score': 0.3010299956639812},
            {'name': 'M4', 'chr': 'Y', 'Mb': 1.2e-05, 'p_value': 0.7, 'additive': 11.6, 'lod_score': 0.1549019599857432},
            {'name': 'M5', 'chr': 'X', 'Mb': 1.2e-05, 'p_value': 0.6, 'additive': 21.1, 'lod_score': 0.22184874961635637}]

            self.assertEqual(expected_results, results)

    @mock.patch("wqflask.marker_regression.gemma_mapping.TEMPDIR", "/home/tmp")
    @mock.patch("wqflask.marker_regression.gemma_mapping.os")
    def test_parse_loco_outputfile_not_found(self, mock_os):
        """add tests for parse loco output where  output file not found"""

        mock_os.path.isfile.return_value = False
        file_to_write = """{"files":["file_1","file_2"]}"""

        with mock.patch("builtins.open", mock.mock_open(read_data=file_to_write)) as mock_open:
            results = parse_loco_output(
                this_dataset={}, gwa_output_filename=".xw/")
            self.assertEqual(results, [])
