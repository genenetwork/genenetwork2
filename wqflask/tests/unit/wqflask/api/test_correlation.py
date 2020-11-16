import unittest
from unittest import mock
from wqflask import app
from wqflask.api.correlation import init_corr_params
from wqflask.api.correlation import convert_to_mouse_gene_id
from wqflask.api.correlation import do_literature_correlation_for_all_traits


class AttributeSetter:
    def __init__(self, obj):
        for k, v in obj.items():
            setattr(self, k, v)


class TestCorrelations(unittest.TestCase):
    def setUp(self):
        self.app_context = app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def test_init_corr_params(self):
        start_vars = {
            "return_count": "3",
            "type": "T1",
            "method": "spearman"
        }

        corr_params_results = init_corr_params(start_vars=start_vars)
        expected_results = {
            "return_count": 3,
            "type": "T1",
            "method": "spearman"
        }

        self.assertEqual(corr_params_results, expected_results)

    @mock.patch("wqflask.api.correlation.g")
    def test_convert_to_mouse_gene_id(self, mock_db):

        results = convert_to_mouse_gene_id(species="Other", gene_id="")
        self.assertEqual(results, None)

        rat_species_results = convert_to_mouse_gene_id(
            species="rat", gene_id="GH1")

        mock_db.db.execute.return_value.fetchone.side_effect = [AttributeSetter({"mouse": "MG-1"}),AttributeSetter({"mouse":"MG-2"})]
                                          
        self.assertEqual(convert_to_mouse_gene_id(
            species="mouse", gene_id="MG-4"), "MG-4")
        self.assertEqual(convert_to_mouse_gene_id(
            species="rat", gene_id="R1"), "MG-1")
        self.assertEqual(convert_to_mouse_gene_id(
            species="human", gene_id="H1"), "MG-2")

    
    
    @mock.patch("wqflask.api.correlation.g")
    @mock.patch("wqflask.api.correlation.convert_to_mouse_gene_id")
    def test_do_literature_correlation_for_all_traits(self,mock_convert_to_mouse_geneid,mock_db):
    	mock_convert_to_mouse_geneid.side_effect=["MG-1","MG-2;","MG-3","MG-4"]
   

    	trait_geneid_dict={
    	 "TT-1":"GH-1",
    	 "TT-2":"GH-2",
    	 "TT-3":"GH-3"

    	}
    	mock_db.db.execute.return_value.fetchone.side_effect=[AttributeSetter({"value":"V1"}),AttributeSetter({"value":"V2"}),AttributeSetter({"value":"V3"})]


    	this_trait=AttributeSetter({"geneid":"GH-1"})

    	target_dataset=AttributeSetter({"group":AttributeSetter({"species":"rat"})})
    	results=do_literature_correlation_for_all_traits(this_trait=this_trait,target_dataset=target_dataset,trait_geneid_dict=trait_geneid_dict,corr_params={})

    	expected_results={'TT-1': ['GH-1', 0], 'TT-2': ['GH-2', 'V1'], 'TT-3': ['GH-3', 'V2']}
    	self.assertEqual(results,expected_results)



