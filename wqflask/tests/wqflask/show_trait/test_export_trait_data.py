import unittest
from wqflask.show_trait.export_trait_data import dict_to_sorted_list,cmp_samples
class TestDictionaryList(unittest.TestCase):
	def setUp(self):
		self.sample1={
		"other":"exp1",
		"name":"exp2"
		}
		self.sample2={
		'se':1,
		'num_cases':4,
		'value':6,
		"name":3

		}
		self.reversed={
		"name":3,
		'value':6,
		'num_cases':4,
		'se':1
		}
		self.oneItem={
		'item1':"one"
		}
	def  test_dict_to_sortedlist(self):
		'''Test for converting dict to sorted list'''
		
		self.assertEqual(['exp2','exp1'],dict_to_sorted_list(self.sample1))
		self.assertEqual([3, 6, 1, 4],dict_to_sorted_list(self.sample2))
		self.assertEqual([3, 6, 1, 4],dict_to_sorted_list(self.reversed))
		self.assertEqual(["one"],dict_to_sorted_list(self.oneItem))
		'''test that the func returns the values not the keys'''
		self.assertFalse(['other','name']==['exp2','exp1'])



class TestComparison(unittest.TestCase):
	def setUp(self):
		self.sampleA=[
		[
		('value','other'),
		('name','test_name')
		]
		]
		self.sampleB=[
		[
		('value','other'),
		('unknown','test_name')
		]
		]
		self.sampleC=[
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





	def test_cmp_samples(self):
		'''Test for func that does sample comparisons'''
	
		results=[cmp_samples(val[0],val[1]) for val in self.sampleA]
		resultB=[cmp_samples(val[0],val[1]) for val in self.sampleB]
		resultC=[cmp_samples(val[0],val[1]) for val in self.sampleC]
		self.assertEqual(1,*results)
		self.assertEqual(-1,*resultB)
		self.assertEqual([1, -1, 1, -1, -1, 1, -1, -1],resultC)



 

