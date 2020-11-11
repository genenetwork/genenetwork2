"""Test functions in markdown utils"""

import unittest
from unittest import mock

from wqflask.markdown_routes import render_markdown


class MockRequests404:
    @property
    def status_code(self):
        return 404

class MockRequests200:
    @property
    def status_code(self):
        return 200

    @property
    def content(self):
        return b"""
# Glossary
This is some content

## Sub-heading
This is another sub-heading
        """

class TestMarkdownRoutesFunctions(unittest.TestCase):
    """Test cases for functions in markdown_routes"""

    @mock.patch('wqflask.markdown_routes.requests.get')
    def test_render_markdown_when_fetching_locally(self, requests_mock):
        requests_mock.return_value = MockRequests404()
        markdown_content = render_markdown("glossary.md")
        requests_mock.assert_called_with(
            "https://raw.githubusercontent.com"
            "/genenetwork/genenetwork2/"
            "wqflask/wqflask/static/"
            "glossary.md")
        self.assertRegexpMatches(markdown_content,
                                 "Glossary of Terms and Features")

    @mock.patch('wqflask.markdown_routes.requests.get')
    def test_render_markdown_when_fetching_remotely(self, requests_mock):
        requests_mock.return_value = MockRequests200()
        markdown_content = render_markdown("glossary.md")
        requests_mock.assert_called_with(
            "https://raw.githubusercontent.com"
            "/genenetwork/genenetwork2/"
            "wqflask/wqflask/static/"
            "glossary.md")
        self.assertEqual("""<h1>Glossary</h1>
<p>This is some content</p>
<h2>Sub-heading</h2>
<p>This is another sub-heading</p>
""",
                         markdown_content)
