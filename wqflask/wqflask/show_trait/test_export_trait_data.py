import export_trait_data as trait_data
import unittest

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
	def  test_dict_to_sortedlist(self):
		'''Test for converting dict to sorted list'''
		
		self.assertEqual(['exp2','exp1'],trait_data.dict_to_sorted_list(self.sample1))
		self.assertEqual([3, 6, 1, 4],trait_data.dict_to_sorted_list(self.sample2))
		self.assertEqual([3, 6, 1, 4],trait_data.dict_to_sorted_list(self.reversed
))

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
			]
]



	def test_cmp_func(self):
		'''Test for func that does comparisons'''
	
		results=[trait_data.cmp_samples(val[0],val[1]) for val in self.sampleA]
		resultB=[trait_data.cmp_samples(val[0],val[1]) for val in self.sampleB]
		resultC=[trait_data.cmp_samples(val[0],val[1]) for val in self.sampleC]
		self.assertEqual(1,*results)
		self.assertEqual(-1,*resultB)
		self.assertEqual([1, -1, 1, -1, -1, 1, -1, -1],resultC)



 

