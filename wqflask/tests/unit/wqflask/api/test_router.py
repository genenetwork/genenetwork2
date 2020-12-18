import unittest
import json
import csv
from unittest import mock
from wqflask.api.router import app
from wqflask.api.router import get_group_id
from wqflask.api.router import get_samplelist
from wqflask.api.router import get_species_info
from wqflask.api.router import return_error
from wqflask.api.router import get_group_id_from_dataset
from wqflask.api.router import get_dataset_trait_ids


app.testing = True
app.debug=False
class TestRouter(unittest.TestCase):
    def setUp(self):
        self.app_context = app.app_context()
        self.app_context.push()


    def tearDown(self):
        self.app_context.pop()

    @mock.patch("wqflask.api.router.g")
    def test_get_species_list(self, mock_db):
        species = [["sdadhj343", "HM1", "Human", "TX1"]]
        mock_db.db.execute.return_value.fetchall.return_value = species
        with app.test_client() as client:
            response = app.test_client().get('/api/v_pre1/species')
            response_data = json.loads(response.data)
            expected_results = [
                {'FullName': 'Human', 'Id': 'sdadhj343', 'Name': 'HM1', 'TaxonomyId': 'TX1'}]

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response_data, expected_results)

    @mock.patch("wqflask.api.router.g")
    def test_get_species_info(self, mock_db):
        query_results = [["1", "Human", "Homo sapiens", "4d898354-9663-4981-96ec-5cdfae2ce15e"],
                         ["3", "Rat", "Rattus", "47fc7b31-2888-4451-9a9b-baebbb466ba0"]]
        mock_db.db.execute.return_value.fetchone.side_effect = query_results
        response1 = app.test_client().get("/api/v_pre1/species/rat/info")
        response2 = app.test_client().get("/api/v_pre1/species/human/info")
        response1_data = json.loads(response1.data)
        response2_data = json.loads(response2.data)
        expected_result1_data = {'FullName': 'Homo sapiens', 'Id': '1',
                                 'Name': 'Human', 'TaxonomyId': '4d898354-9663-4981-96ec-5cdfae2ce15e'}
        expected_result2_data = {'FullName': 'Rattus', 'Id': '3',
                                 'Name': 'Rat', 'TaxonomyId': '47fc7b31-2888-4451-9a9b-baebbb466ba0'}

        self.assertEqual(response1_data, expected_result1_data)
        self.assertEqual(response2_data, expected_result2_data)

    @mock.patch("wqflask.api.router.g")
    def test_get_groups_list(self, mock_db):
        query_results = [
            [1, "a5d6d274-e6b4-4908-bc8d-6817cc91a9e7", "GP1",
                "GP1", "Group_1", 1, "MP1", "Molecular"],
            [4, "a5d6d274-e6b4-4908-bc8d-6817cc91a9e7", "GP2",
                "GP2", "Group_2", 4, "MP1", "Molecular"],
            [2, "13d2b3ea-fc7d-4fef-ab20-a077f2199816", "GP3",
                "GP3", "Group_3", 2, "MP2", "Molecular"]
        ]
        expected_results = [
            {'DisplayName': 'GP1',
             'FullName': 'Group_1',
             'GeneticType': 'Molecular',
             'Id': 1,
             'MappingMethodId': 'MP1',
             'Name': 'GP1',
             'SpeciesId': 'a5d6d274-e6b4-4908-bc8d-6817cc91a9e7',
             'public': 1},

            {'DisplayName': 'GP2',
             'FullName': 'Group_2',
             'GeneticType': 'Molecular',
             'Id': 4,
             'MappingMethodId': 'MP1',
             'Name': 'GP2',
             'SpeciesId': 'a5d6d274-e6b4-4908-bc8d-6817cc91a9e7',
             'public': 4},
            {'DisplayName': 'GP3',
             'FullName': 'Group_3',
             'GeneticType': 'Molecular',
             'Id': 2,
             'MappingMethodId': 'MP2',
             'Name': 'GP3',
             'SpeciesId': '13d2b3ea-fc7d-4fef-ab20-a077f2199816',
             'public': 2}

        ]

        mock_db.db.execute.return_value.fetchall.return_value = query_results
        with app.test_client() as client:
            rv = client.get("/api/v_pre1/groups/human")
            rv_data = json.loads(rv.data)
            # self.assertEqual(query_results,rv_data)
            self.assertEqual(rv_data, expected_results)
            self.assertEqual(rv.status_code, 200)

    @mock.patch("wqflask.api.router.g")
    def test_get_groups_list_raise_204_error(self, mock_db):
        mock_db.db.execute.return_value.fetchall.return_value = None
        with app.test_client() as client:
            rv = client.get("/api/v_pre1/groups")
            rv_data = json.loads(rv.data)["errors"][0]
            self.assertEqual(rv_data["source"]
                             ["pointer"], '/api/v_pre1/groups')
            self.assertEqual(rv_data["status"], 204)

    def test_return_error(self):

        error_params = {
            "code": "500",
            "source": "/api/",
            "title": "internal server error",
            "details": ""
        }
        error_server_results = {
            "code": "500",
            "source": {"pointer": "/api/"},
            "title": "internal server error",
            "details": ""
        }

        results_not_found = json.loads(
            return_error(**error_params).data)["errors"][0]
        expected_results = {'detail': '', 'source': {
            'pointer': '/api/'}, 'status': '500', 'title': 'internal server error'}

        self.assertEqual(expected_results, results_not_found)

    @mock.patch("wqflask.api.router.g")
    def test_get_group_id(self, mock_db):
        query_results = ["sdfw232sdf2"]
        mock_db.db.execute.return_value.fetchone.side_effect = [
            query_results, []]
        result1 = get_group_id("GH1")
        result2 = get_group_id("GH2")
        self.assertEqual(result1, "sdfw232sdf2")
        self.assertEqual(result2, None)

    @mock.patch("wqflask.api.router.g")
    @mock.patch("wqflask.api.router.get_group_id_from_dataset")
    def test_get_samplelist(self, mock_group_id, mock_db):
        mock_group_id.side_effect = ["group_id_1"]
        mock_db.db.execute.return_value.fetchall.return_value = [
            ["S1"], ["S2"], ["S3"]]
        results = get_samplelist(dataset_name="DT-1")
        self.assertEqual(results, ["S1", "S2", "S3"])

    @mock.patch("wqflask.api.router.gen_menu")
    def test_gen_dropdown_menu(self, mock_gen):
        mock_gen.gen_dropdown_json.return_value = [{
            "id": "dfsdfsdf779sd99ssdfs",
            "options": ["OP1", "OP2", "OP3"]
        }]
        expected_results = [{
            "id": "dfsdfsdf779sd99ssdfs",
            "options": ["OP1", "OP2", "OP3"]
        }]

        with app.test_client() as client:
            rv = client.get("/api/v_pre1/gen_dropdown")
            rv_data = json.loads(rv.data)
            self.assertEqual(rv.status_code, 200)
            self.assertEqual(rv_data, expected_results)

    @mock.patch("wqflask.api.router.correlation.do_correlation")
    def test_get_corr_results(self, do_correlation):

        results = [{
            "trait": "T1",
            "sample_r": "R1",
            "#_strains": "strain_1",
            "p_value": "0.7",
            "symbol": "S2"
        },
            {
            "trait": "T2",
            "sample_r": "R2",
            "gene_id": "dewfjkf78f8re"
        }
        ]
        do_correlation.return_value = results
        with app.test_client() as client:
            rv = client.get("/api/v_pre1/correlation")
            rv_data = json.loads(rv.data)
            expected_results = [{'#_strains': 'strain_1', 'p_value': '0.7', 'sample_r': 'R1', 'symbol': 'S2', 'trait': 'T1'},
                                {'gene_id': 'dewfjkf78f8re', 'sample_r': 'R2', 'trait': 'T2'}]

            self.assertEqual(expected_results, rv_data)

    @mock.patch("wqflask.api.router.mapping.do_mapping_for_api")
    def test_get_mapping_results_json(self, mapping_api):

        mapping_api.return_value = ([{"mapping_method": "gemma", "use_loco": "True",
                                      "name": "nm1", "lod_score": "2312", "chr": "23", "Mb": "32"}], "json")
        expected_results = [{'Mb': '32', 'chr': '23', 'lod_score': '2312',
                             'mapping_method': 'gemma', 'name': 'nm1', 'use_loco': 'True'}]

        with app.test_client() as client:
            rv = client.get("/api/v_pre1/mapping")
            rv_data = json.loads(rv.data)
            self.assertEqual(expected_results, rv_data)
            self.assertEqual(rv.status_code, 200)

    @mock.patch("wqflask.api.router.mapping.do_mapping_for_api")
    def test_get_mapping_results_unsupported_format(self, mapping_api):
        mapping_api.return_value = ([{"mapping_method": "gemma"}], "txt")
        with app.test_client() as client:
            rv = client.get("api/v_pre1/mapping")
            rv_data = json.loads(rv.data)["errors"][0]
            self.assertEqual(rv_data["status"], 415)
            self.assertEqual(rv_data["title"], "Unsupported Format")

    @mock.patch("wqflask.api.router.mapping.do_mapping_for_api")
    def test_get_mapping_results_csv(self, mapping_api):
        mapping_api.return_value = ([["foo", "bar", "spam"],
                                     ["oof", "rab", "maps"],
                                     ["writerow", "isn't", "writerows"]], "csv")

        with app.test_client() as client:
            rv = client.get("api/v_pre1/mapping")
            rv_data = rv.data.decode("utf-8")

            csv_data = list(csv.reader(rv_data.splitlines(), delimiter=','))
            expected_results = [['foo', 'bar', 'spam'], [
                'oof', 'rab', 'maps'], ['writerow', "isn't", 'writerows']]
            self.assertEqual(expected_results, csv_data)

    @mock.patch("wqflask.api.router.g")
    def test_get_group_id_from_dataset(self,mock_db):
        mock_db.db.execute.return_value.fetchone.side_effect=[[22],[]]
        query = """
                    SELECT
                            InbredSet.Id
                    FROM
                            InbredSet, PublishFreeze
                    WHERE
                            PublishFreeze.InbredSetId = InbredSet.Id AND
                            PublishFreeze.Name = "BXDPublish"
                """

        results=get_group_id_from_dataset(dataset_name="BXDPublish")
        mock_db.db.execute.assert_called_once_with(query)
        empty_db=get_group_id_from_dataset(dataset_name="Other")
        self.assertEqual(results,22)
        self.assertEqual(empty_db,None)

    @mock.patch("wqflask.api.router.g")
    def  test_get_dataset_traits_ids(self,mock_db):
        start_vars={
        "limit_to":"L1",
        }
        mock_db.db.execute.return_value.fetchall.return_value=[(1,"T1",1001),(5,"T5",101)]

        query =    """
                            SELECT
                                GenoXRef.GenoId, Geno.Name, GenoXRef.GenoFreezeId
                            FROM
                                Geno, GenoXRef, GenoFreeze
                            WHERE
                                Geno.Id = GenoXRef.GenoId AND
                                GenoXRef.GenoFreezeId = GenoFreeze.Id AND
                                GenoFreeze.Name = "BXDGeno"
                            LIMIT L1
                        """

        results=get_dataset_trait_ids(dataset_name="BXDGeno",start_vars=start_vars)

        mock_db.db.execute.assert_called_once_with(query)
        self.assertEqual(results,([1,5],["T1","T5"],"Geno",1001))