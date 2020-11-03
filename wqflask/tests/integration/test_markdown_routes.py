"Integration tests for markdown routes"
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
        pass
