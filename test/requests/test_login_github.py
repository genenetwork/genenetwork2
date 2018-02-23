import uuid
import requests
from time import sleep
from parameterized import parameterized
from parametrized_test import ParametrizedTest

login_link_text = '<a id="login_in" href="/n/login">Sign in</a>'
logout_link_text = '<a id="login_out" title="Signed in as ." href="/n/logout">Sign out</a>'
uid = str(uuid.uuid4())

class TestLoginGithub(ParametrizedTest):

    def setUp(self):
        super(TestLoginGithub, self).setUp()
        data = {
            "user_id": uid
            , "name": "A. T. Est User"
            , "github_id": 693024
            , "user_url": "https://fake-github.com/atestuser"
            , "login_type": "github"
            , "organization": ""
            , "active": 1
            , "confirmed": 1
        }
        self.es.create(index="users", doc_type="local", body=data, id=uid)
        sleep(1)

    def tearDown(self):
        super(TestLoginGithub, self).tearDown()
        self.es.delete(index="users", doc_type="local", id=uid)

    @parameterized.expand([
        ("1234", login_link_text, "Login should have failed with non-existing user")
        , (uid, logout_link_text, "Login should have been successful with existing user")
        ])
    def testLogin(self, test_uid, expected, message):
        url = self.gn2_url+"/n/login?type=github&uid="+test_uid
        result = requests.get(url)
        index = result.content.find(expected)
        self.assertTrue(index >= 0, message)
