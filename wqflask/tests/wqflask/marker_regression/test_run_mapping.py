import unittest
from unittest import mock
from wqflask.marker_regression.run_mapping import get_genofile_samplelist


class AttributeSetter:
	def __init__(self,obj):
		for k,v in obj.items():
			setattr(self,k,v)


class MockDataSetGroup(AttributeSetter):
	
	def get_genofiles(self):
		return [{"location":"~/genofiles/g1_file","sample_list":["S1","S2","S3","S4"]}]
class TestRunMapping(unittest.TestCase):
	def setUp(self):
		self.group=MockDataSetGroup({"genofile":"~/genofiles/g1_file"})
		self.dataset=AttributeSetter({"group":self.group})

	def tearDown(self):
		self.dataset=AttributeSetter({"group":{"location":"~/genofiles/g1_file"}})


	def test_get_genofile_samplelist(self):
		#location true and sample list true

		results_1=get_genofile_samplelist(self.dataset)
		self.assertEqual(results_1,["S1","S2","S3","S4"])
		#return empty array
		self.group.genofile="~/genofiles/g2_file"
		result_2=get_genofile_samplelist(self.dataset)
		self.assertEqual(result_2,[])



