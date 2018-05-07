import uuid
import requests
from time import sleep
from wqflask import app
from parameterized import parameterized
from parametrized_test import ParametrizedTest

login_link_text = '<a id="login_in" href="/n/login">Sign in</a>'
logout_link_text = '<a id="login_out" title="Signed in as ." href="/n/logout">Sign out</a>'
uid = str(uuid.uuid4())

class TestLoginOrcid(ParametrizedTest):

    def setUp(self):
        super(TestLoginOrcid, self).setUp()
        data = {
            "user_id": uid
            , "name": "A. T. Est User"
            , "orcid": 345872
            , "user_url": "https://fake-orcid.org/atestuser"
            , "login_type": "orcid"
            , "organization": ""
            , "active": 1
            , "confirmed": 1
        }
        self.es.create(index="users", doc_type="local", body=data, id=uid)
        sleep(1)

    def tearDown(self):
        super(TestLoginOrcid, self).tearDown()
        self.es.delete(index="users", doc_type="local", id=uid)

    def testLoginUrl(self):
        login_button_text = '<input class="btn btn-primary" name="submit" type="submit" value="Sign in with ORCID">'
        result = requests.get(self.gn2_url+"/n/login")
        index = result.content.find(login_button_text)
        self.assertTrue(index >= 0, "Should have found `Login with ORCID` button")

    # It is no longer possible to test this directly with the reorganisation.
    #
    # @parameterized.expand([
    #     ("1234", login_link_text, "Login should have failed with non-existing user")
    #     , (uid, logout_link_text, "Login should have been successful with existing user")
    #     ])
    # def testLogin(self, test_uid, expected, message):
    #     url = self.gn2_url+"/n/login?type=orcid&uid="+test_uid
    #     result = requests.get(url)
    #     index = result.content.find(expected)
    #     self.assertTrue(index >= 0, message)
