import unittest
from unittest import  mock
from wqflask.marker_regression.qtlreaper_mapping import  gen_pheno_txt_file

#issues some methods in genofile object are not defined
#modify samples should equal to vals
class TestQtlReaperMapping(unittest.TestCase):
	@mock.patch("wqflask.marker_regression.qtlreaper_mapping.TEMPDIR", "/home/user/data")
	def  test_gen_pheno_txt_file(self):                   
		vals=["V1","x","V4","V3","x"]
		samples=["S1","S2","S3","S4","S5"]
		trait_filename="trait_file"
		with mock.patch("builtins.open", mock.mock_open())as mock_open:
			gen_pheno_txt_file(samples=samples,vals=vals,trait_filename=trait_filename)
			mock_open.assert_called_once_with("/home/user/data/gn2/trait_file.txt","w")
			filehandler=mock_open()
			write_calls= [mock.call('Trait\t'),mock.call('S1\tS3\tS4\n'),mock.call('T1\t'),mock.call('V1\tV4\tV3')]

			filehandler.write.assert_has_calls(write_calls)

	                                                                                                                    
