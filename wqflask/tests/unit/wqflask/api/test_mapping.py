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
		





