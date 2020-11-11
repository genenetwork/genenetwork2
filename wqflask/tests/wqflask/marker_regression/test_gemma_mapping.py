# test for wqflask/marker_regression/gemma_mapping.py
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

    @mock.patch("wqflask.marker_regression.gemma_mapping.parse_loco_output")
    def test_run_gemma_first_run_loco_set_false(self, mock_parse_loco):
        """add tests for gemma function where  first run is set to false"""
        dataset = AttributeSetter(
            {"group": AttributeSetter({"genofile": "genofile.geno"})})

        output_files = "file1"
        use_loco = False
        mock_parse_loco.return_value = []
        this_trait = AttributeSetter({"name": "t1"})

        result = run_gemma(this_trait=this_trait, this_dataset=dataset, samples=[], vals=[
        ], covariates="", use_loco=True, first_run=False, output_files=output_files)

        expected_results = ([], "file1")
        self.assertEqual(expected_results, result)

    @mock.patch("wqflask.marker_regression.gemma_mapping.webqtlConfig.GENERATED_IMAGE_DIR", "/home/user/img")
    @mock.patch("wqflask.marker_regression.gemma_mapping.GEMMAOPTS", "-debug")
    @mock.patch("wqflask.marker_regression.gemma_mapping.GEMMA_WRAPPER_COMMAND", "ghc")
    @mock.patch("wqflask.marker_regression.gemma_mapping.TEMPDIR", "/home/user/data/")
    @mock.patch("wqflask.marker_regression.gemma_mapping.parse_loco_output")
    @mock.patch("wqflask.marker_regression.gemma_mapping.logger")
    @mock.patch("wqflask.marker_regression.gemma_mapping.flat_files")
    @mock.patch("wqflask.marker_regression.gemma_mapping.gen_covariates_file")
    @mock.patch("wqflask.marker_regression.run_mapping.random.choice")
    @mock.patch("wqflask.marker_regression.gemma_mapping.os")
    @mock.patch("wqflask.marker_regression.gemma_mapping.gen_pheno_txt_file")
    def test_run_gemma_first_run_set_true(self, mock_gen_pheno_txt, mock_os, mock_choice, mock_gen_covar, mock_flat_files, mock_logger, mock_parse_loco):
        """add tests for run_gemma where first run is set to true"""
        chromosomes = []
        for i in range(1, 5):
            chromosomes.append(AttributeSetter({"name": f"CH{i}"}))
        chromo = AttributeSetter({"chromosomes": chromosomes})
        dataset_group = MockDatasetGroup(
            {"name": "GP1", "genofile": "file_geno"})
        dataset = AttributeSetter({"group": dataset_group, "name": "dataset1_name",
                                   "species": AttributeSetter({"chromosomes": chromo})})
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
        system_calls = [mock.call('ghc --json -- -debug -g /home/genotype/bimbam/file_geno.txt -p /home/user/data//gn2/trait1_dataset1_name_pheno.txt -a /home/genotype/bimbam/file_snps.txt -gk > /home/user/data//gn2/GP1_K_RRRRRR.json'),
                        mock.call('ghc --json --input /home/user/data//gn2/GP1_K_RRRRRR.json -- -debug -a /home/genotype/bimbam/file_snps.txt -lmm 2 -g /home/genotype/bimbam/file_geno.txt -p /home/user/data//gn2/trait1_dataset1_name_pheno.txt > /home/user/data//gn2/GP1_GWA_RRRRRR.json')]
        mock_os.system.assert_has_calls(system_calls)
        mock_gen_pheno_txt.assert_called_once()
        mock_parse_loco.assert_called_once_with(dataset, "GP1_GWA_RRRRRR")
        mock_os.path.isfile.assert_called_once_with(
            ('/home/user/imgfile_output.assoc.txt'))
        self.assertEqual(mock_logger.debug.call_count, 2)
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

        group = MockDatasetGroup({"name": "group_X", "samplelist": samplelist})
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

    @mock.patch("wqflask.marker_regression.gemma_mapping.webqtlConfig.GENERATED_IMAGE_DIR", "/home/user/img/")
    def test_parse_gemma_output_obj_returned(self):
        """add test for generating gemma output with obj returned"""
        file = """X/Y\t gn2\t21\tQ\tE\tA\tP\tMMB\tCDE\t0.5
X/Y\tgn2\t21322\tQ\tE\tA\tP\tMMB\tCDE\t0.5
chr\tgn1\t12312\tQ\tE\tA\tP\tMMB\tCDE\t0.7
X\tgn7\t2324424\tQ\tE\tA\tP\tMMB\tCDE\t0.4
125\tgn9\t433575\tQ\tE\tA\tP\tMMB\tCDE\t0.67
"""
        with mock.patch("builtins.open", mock.mock_open(read_data=file)) as mock_open:
            results = parse_gemma_output(genofile_name="gema_file")
            expected = [{'name': ' gn2', 'chr': 'X/Y', 'Mb': 2.1e-05, 'p_value': 0.5, 'lod_score': 0.3010299956639812}, {'name': 'gn2', 'chr': 'X/Y', 'Mb': 0.021322, 'p_value': 0.5, 'lod_score': 0.3010299956639812},
                        {'name': 'gn7', 'chr': 'X', 'Mb': 2.324424, 'p_value': 0.4, 'lod_score': 0.3979400086720376}, {'name': 'gn9', 'chr': 125, 'Mb': 0.433575, 'p_value': 0.67, 'lod_score': 0.17392519729917352}]
            mock_open.assert_called_once_with(
                "/home/user/img/gema_file_output.assoc.txt")
            self.assertEqual(results, expected)

    @mock.patch("wqflask.marker_regression.gemma_mapping.webqtlConfig.GENERATED_IMAGE_DIR", "/home/user/img")
    def test_parse_gemma_output_empty_return(self):
        """add tests for parse gemma output where nothing returned"""
        output_file_results = """chr\t today"""
        with mock.patch("builtins.open", mock.mock_open(read_data=output_file_results)) as mock_open:
            results = parse_gemma_output(genofile_name="gema_file")
            self.assertEqual(results, [])

    @mock.patch("wqflask.marker_regression.gemma_mapping.TEMPDIR", "/home/tmp")
    @mock.patch("wqflask.marker_regression.gemma_mapping.os")
    def test_parse_loco_output_file_found(self, mock_os):
        """add tests for parse loco output file found"""
        mock_os.path.isfile.return_value = True
        file_to_write = """{"files":["file_1","file_2"]}"""
        pass

    @mock.patch("wqflask.marker_regression.gemma_mapping.TEMPDIR", "/home/tmp")
    @mock.patch("wqflask.marker_regression.gemma_mapping.os")
    def test_parse_loco_output_file_not_found(self, mock_os):
        """add tests for parse loco output file not found"""

        mock_os.path.isfile.return_value = False
        file_to_write = """{"files":["file_1","file_2"]}"""

        with mock.patch("builtins.open", mock.mock_open(read_data=file_to_write)) as mock_open:
            results = parse_loco_output(
                this_dataset={}, gwa_output_filename=".xw/")
            self.assertEqual(results, [])
