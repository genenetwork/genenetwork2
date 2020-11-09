import unittest
from unittest import mock
from wqflask.marker_regression.run_mapping import get_genofile_samplelist
from wqflask.marker_regression.run_mapping import geno_db_exists

class AttributeSetter:
	def __init__(self,obj):
		for k,v in obj.items():
			setattr(self,k,v)


class MockDataSetGroup(AttributeSetter):
	
	def get_genofiles(self):
		return [{"location":"~/genofiles/g1_file","sample_list":["S1","S2","S3","S4"]}]
class TestRunMapping(unittest.TestCase):
	def setUp(self):
		self.group=MockDataSetGroup({"genofile":"~/genofiles/g1_file","name":"GP1_"})
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

	@mock.patch("wqflask.marker_regression.run_mapping.data_set")
	def test_geno_db_exists(self,mock_data_set):
		# mock_data_set.create_dataset_side_effect=None
		mock_data_set.create_dataset.side_effect=[AttributeSetter({}),Exception()]
		results_no_error=geno_db_exists(self.dataset)
		results_with_error=geno_db_exists(self.dataset)

		self.assertEqual(mock_data_set.create_dataset.call_count,2)
		self.assertEqual(results_with_error,"False")
		self.assertEqual(results_no_error,"True")








