"""Test cases pbkdf2"""

import unittest
from wqflask.pbkdf2 import pbkdf2_hex


class TestPbkdf2(unittest.TestCase):
    def test_pbkdf2_hex(self):
        """
        Test pbkdf2_hex function
        """

        for password, salt, iterations, keylen, expected_value in [
                ('password', 'salt', 1, 20,
                 '0c60c80f961f0e71f3a9b524af6012062fe037a6'),
                ('password', 'salt', 2, 20,
                 'ea6c014dc72d6f8ccd1ed92ace1d41f0d8de8957'),
                ('password', 'salt', 4096, 20,
                 '4b007901b765489abead49d926f721d065a429c1'),
                ('passwordPASSWORDpassword',
                 'saltSALTsaltSALTsaltSALTsaltSALTsalt',
                 4096, 25,
                 '3d2eec4fe41c849b80c8d83662c0e44a8b291a964cf2f07038'),
                ('pass\x00word', 'sa\x00lt', 4096, 16,
                 '56fa6aa75548099dcc37d7f03425e0c3'),
                ('password', 'ATHENA.MIT.EDUraeburn', 1, 16,
                 'cdedb5281bb2f801565a1122b2563515'),
                ('password', 'ATHENA.MIT.EDUraeburn', 1, 32,
                 ('cdedb5281bb2f80'
                  '1565a1122b256351'
                  '50ad1f7a04bb9f3a33'
                  '3ecc0e2e1f70837')),
                ('password', 'ATHENA.MIT.EDUraeburn', 2, 16,
                 '01dbee7f4a9e243e988b62c73cda935d'),
                ('password', 'ATHENA.MIT.EDUraeburn', 2, 32,
                 ('01dbee7f4a9e243e9'
                  '88b62c73cda935da05'
                  '378b93244ec8f48a99'
                  'e61ad799d86')),
                ('password', 'ATHENA.MIT.EDUraeburn', 1200, 32,
                 ('5c08eb61fdf71e'
                  '4e4ec3cf6ba1f55'
                  '12ba7e52ddbc5e51'
                  '42f708a31e2e62b1e13')),
                ('X' * 64, 'pass phrase equals block size', 1200, 32,
                 ('139c30c0966bc32ba'
                  '55fdbf212530ac9c5'
                  'ec59f1a452f5cc9ad'
                  '940fea0598ed1')),
                ('X' * 65, 'pass phrase exceeds block size', 1200, 32,
                 ('9ccad6d468770cd'
                  '51b10e6a68721be6'
                  '11a8b4d282601db3'
                  'b36be9246915ec82a'))
        ]:
            self.assertEqual(
                pbkdf2_hex(data=password,
                           salt=salt,
                           iterations=iterations,
                           keylen=keylen),
                expected_value)
