import unittest
from unittest import mock
from wqflask import app
from wqflask.marker_regression.rqtl_mapping import get_trait_data_type
from wqflask.marker_regression.rqtl_mapping import sanitize_rqtl_phenotype
from wqflask.marker_regression.rqtl_mapping import sanitize_rqtl_names

class TestRqtlMapping(unittest.TestCase):

	def setUp(self):
		self.app_context=app.app_context()
		self.app_context.push()

	def tearDown(self):
		self.app_context.pop()


	@mock.patch("wqflask.marker_regression.rqtl_mapping.g")
	@mock.patch("wqflask.marker_regression.rqtl_mapping.logger")
	def test_get_trait_data(self,mock_logger,mock_db):
		"""test for getting trait data_type return True"""
		query_value="""SELECT value FROM TraitMetadata WHERE type='trait_data_type'"""
		mock_db.db.execute.return_value.fetchone.return_value=["""{"type":"trait_data_type","name":"T1","traid_id":"fer434f"}"""]
		results=get_trait_data_type("traid_id")
		mock_db.db.execute.assert_called_with(query_value)
		self.assertEqual(results,"fer434f")

	def test_sanitize_rqtl_phenotype(self):
		"""test for sanitizing rqtl phenotype"""
		vals=['f',"x","r","x","x"]
		results=sanitize_rqtl_phenotype(vals)
		expected_phenotype_string='c(f,NA,r,NA,NA)'

		self.assertEqual(results,expected_phenotype_string)

	def test_sanitize_rqtl_names(self):
		"""test for sanitzing rqtl names"""
		vals=['f',"x","r","x","x"]
		expected_sanitized_name="c('f',NA,'r',NA,NA)"
		results=sanitize_rqtl_names(vals)
		self.assertEqual(expected_sanitized_name,results)


		
		



