import unittest
from unittest import mock
from wqflask.correlation.show_corr_results import get_header_fields
from wqflask.correlation.show_corr_results import generate_corr_json
from wqflask.correlation.show_corr_results import do_bicor


class Trait:
	def __init__(self,trait_obj):
		for key,value in trait_obj.items():
			setattr(self,key,value)

class TestShowCorrResults(unittest.TestCase):

	def test_process_samples(self):
		pass
	def test_get_header_fields(self):
		expected=[
		                    ['Index',
                                'Record',
                                'Symbol',
                                'Description',
                                'Location',
                                'Mean',
                                'Sample rho',
                                'N',
                                'Sample p(rho)',
                                'Lit rho',
                                'Tissue rho',
                                'Tissue p(rho)',
                                'Max LRS',
                                'Max LRS Location',
                                'Additive Effect'],

                            ['Index',
                                 'ID',
                                 'Location',
                                 'Sample r',
                                 'N',
                                 'Sample p(r)']

		]
		result1=get_header_fields("ProbeSet","spearman")
		result2=get_header_fields("Other","Other")
		self.assertEqual(result1,expected[0])
		self.assertEqual(result2,expected[1])




	def test_generate_corr_json(self):
		this_trait=Trait({"name":"trait_test"})
		dataset=Trait({"name":"the_name"})
		target_dataset=Trait({"type":"Publish"})
	
		trait_with_publish={
		"description_display":"Trait 2 description",
		"authors":"trait_2 ",
		"pubmed_id":"34n4nn31hn43",
		"lrs_location":"N/A",
		"additive":"",
		"sample_r":100,
		"num_overlap":3.2,
		"view":True,
		"name":"trait_1",
		"pubmed_text":"2016",
		"additive":"",
		"sample_r":10.5,
		"LRS_score_repr":"N/A",
		"LRS_location_repr":"N/A",
		"sample_p":5,
		"num_overlap":"num_1"



		}
		expected_results="""[{"trait_id": "trait_1", "description": "Trait 2 description", "authors": "trait_2 ", "pubmed_id": "34n4nn31hn43", "year": "2016", "lrs_score": "N/A", "lrs_location": "N/A", "additive": "N/A", "sample_r": "10.500", "num_overlap": "num_1", "sample_p": "5.000e+00"}]"""

		corr_results=[Trait(trait_with_publish)]
		results=generate_corr_json(corr_results=corr_results,this_trait=this_trait,dataset=dataset,target_dataset=target_dataset,for_api=True)
		self.assertEqual(results,expected_results)
		
		

	def test_generate_corr_json_view_false(self):
		trait=Trait({"view":False})
		corr_results=[trait]
		this_trait=Trait({"name":"trait_test"})
		dataset=Trait({"name":"the_name"})
		

		results_where_view_is_false=generate_corr_json(corr_results=corr_results,this_trait=this_trait,dataset={},target_dataset={},for_api=False)

		# self.assertEqual(results,[])
		self.assertEqual(results_where_view_is_false,"[]")