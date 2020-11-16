import unittest
from unittest import mock
from wqflask.api.mapping import initialize_parameters


class AttributeSetter:
	def __init__(self,obj):
		for key,value in obj.items():
			setattr(self,key,value)

class MockGroup(AttributeSetter):
	def get_marker(self):
		return None
class TestMock(unittest.TestCase):
	
 #    @mock.patch("wqflask.api.mapping.gemma_mapping")
 #    @mock.patch("wqflask.api.mapping.nitialize_parameters")
 #    @mock.patch("wqflask.api.mapping.retrieve_sample_data")
 #    @mock.patch("wqflask.api.mapping.create_trait")
 #    @mock.patch("wqflask.api.mapping.data_set")
	# def test_do_mapping_for_api(self,mock_dataset,mock_create_trait,mock_retrieve_data,mock_gemma):

		# start_vars={
		# "db":"sql_uri/db_web1",
		# "trait_id":"idsui332rh3ui2t",
		# "limit_to":32.1,
		# }
		# group_samplelist=["S1","S2","S3","S4"]
		# dataset_group=MockGroup({"samplelist":group_samplelist})
		# dataset=AttributeSetter({"type":"Temp","group":dataset_group})

		# this_trait_data={
		#   "Item1":AttributeSetter({
		#     "name":"S1",
		#     "value":"V1"
		#   }),

		#   "Item2":AttributeSetter({
		#     "name":"S2",
		#     "value":"V2"
		#   }),

		#   "Item3":AttributeSetter({
		#     "name":"SX",
		#     "value":"VX"
		#   })
		# }

		# this_trait=AttributeSetter({"data":this_trait_data})


		# mock_dataset.create_dataset.return_value=dataset

		# mock_create_trait.return_value=this_trait
		# mock_retrieve_data.return_value=this_trait

		# mock_initialize_params={
		#  "format":"json",
		#   "limit_to":32.1,
		#   "mapping_method":"gemma",
		#   "maf":0.01,
		#   "use_loco":True,
		#   "num_perm":0,
		#   "perm_check":False

		# }

		# mock_gemma.return_value=[ ,"filename"]
		# pass

	def test_initialize_parameters(self):
		expected_results={
		 "format":"json",
		 "limit_to":False,
		 "mapping_method":"gemma",
		 "maf":0.01,
		 "use_loco":True,
		 "num_perm":0,
		 "perm_check":False
		}

		results=initialize_parameters(start_vars={},dataset={},this_trait={})
		self.assertEqual(results,expected_results)

		start_vars={
		"format":"F1",
		"limit_to":"1",
		"mapping_method":"rqtl",
		"control_marker":True,
		"pair_scan":"true",
		"interval_mapping":"true",
		"use_loco":"true",
		"num_perm":"14"

		}

		results_2=initialize_parameters(start_vars=start_vars,dataset={},this_trait={})
		expected_results={
		"format":"F1",
		"limit_to":1,
		"mapping_method":"gemma",
		"maf":0.01,
		"use_loco":True,
		"num_perm":14,
		"perm_check":"ON"
		}

		self.assertEqual(results_2,expected_results)
		





