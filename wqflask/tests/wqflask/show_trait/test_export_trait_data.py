import unittest
from wqflask.show_trait.export_trait_data import dict_to_sorted_list
from wqflask.show_trait.export_trait_data import cmp_samples

class TestExportTraits(unittest.TestCase):
	def test_dict_to_sortedlist(self):
		'''Test for conversion of dict to sorted list'''
		sample1={
		"other":"exp1",
		"name":"exp2"
		}
		sample2={
		'se':1,
		'num_cases':4,
		'value':6,
		"name":3

		}
		rever={
		"name":3,
		'value':6,
		'num_cases':4,
		'se':1
		}
		oneItem={
		'item1':"one"
		}


		self.assertEqual(['exp2','exp1'],dict_to_sorted_list(sample1))
		self.assertEqual([3, 6, 1, 4],dict_to_sorted_list(sample2))
		self.assertEqual([3, 6, 1, 4],dict_to_sorted_list(rever))
		self.assertEqual(["one"],dict_to_sorted_list(oneItem))
		'''test that the func returns the values not the keys'''
		self.assertFalse(['other','name']==dict_to_sorted_list(sample1))

	def test_cmp_samples(self):
		'''test for function that does comparisons of samples'''


		sampleA=[
		[
		('value','other'),
		('name','test_name')
		]
		]
		sampleB=[
		[
		('value','other'),
		('unknown','test_name')
		]
		]
		sampleC=[
			[('other',"value"),
			('name','value')
			],
			[
		    ('name',"value"),
		      ('value',"name")
			],
			[
			('other',"value"),
			('name','value'
			)],
			[
			('name',"name1"),
			('se',"valuex")
			],
			[(
			'value',"name1"),
			('se',"valuex")
			],
			[(
			'other',"name1"),
			('se',"valuex"
			)
			],
			[(
			'name',"name_val"),
			('num_cases',"num_val")
			],
			[(
			"other_a","val_a"),
			('other_b',"val"
			)
			]]
		results=[cmp_samples(val[0],val[1]) for val in sampleA]
		resultB=[cmp_samples(val[0],val[1]) for val in sampleB]
		resultC=[cmp_samples(val[0],val[1]) for val in sampleC]
		self.assertEqual(1,*results)
		self.assertEqual(-1,*resultB)
		self.assertEqual([1, -1, 1, -1, -1, 1, -1, -1],resultC)










 

