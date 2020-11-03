"Integration tests for glossary"
import unittest

from bs4 import BeautifulSoup

from wqflask import app


class TestGenMenu(unittest.TestCase):
    """Tests for glossary"""

    def setUp(self):
        self.app = app.test_client()

    def tearDown(self):
        pass

    def test_glossary_page(self):
        """Test that the glossary page is rendered properly"""
        response = self.app.get('/glossary', follow_redirects=True)
        html_content = BeautifulSoup(response.data, "lxml")
        self.assertEqual(html_content.find("title").get_text(),
                         "Glossary GeneNetwork 2")
        self.assertEqual(
            html_content.find(
                'p',
                attrs={'id': 'mytest'}).get_text(),
            "Test")
