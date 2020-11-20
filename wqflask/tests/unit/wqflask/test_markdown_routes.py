"""Test functions in markdown utils"""

import unittest
from unittest import mock

from dataclasses import dataclass
from wqflask.markdown_routes import render_markdown


@dataclass
class MockRequests404:
    status_code: int = 404


@dataclass
class MockRequests200:
    status_code: int = 200
    content: str = b"""
# Glossary
This is some content

## Sub-heading
This is another sub-heading"""


class TestMarkdownRoutesFunctions(unittest.TestCase):
    """Test cases for functions in markdown_routes"""

    @mock.patch('wqflask.markdown_routes.requests.get')
    def test_render_markdown_when_fetching_locally(self, requests_mock):
        requests_mock.return_value = MockRequests404()
        markdown_content = render_markdown("general/glossary/glossary.md")
        requests_mock.assert_called_with(
            "https://raw.githubusercontent.com"
            "/genenetwork/gn-docs/"
            "master/general/"
            "glossary/glossary.md")
        self.assertRegexpMatches(markdown_content,
                                 "Content for general/glossary/glossary.md not available.")

    @mock.patch('wqflask.markdown_routes.requests.get')
    def test_render_markdown_when_fetching_remotely(self, requests_mock):
        requests_mock.return_value = MockRequests200()
        markdown_content = render_markdown("general/glossary/glossary.md")
        requests_mock.assert_called_with(
            "https://raw.githubusercontent.com"
            "/genenetwork/gn-docs/"
            "master/general/"
            "glossary/glossary.md")
        self.assertEqual("""<h1>Glossary</h1>
<p>This is some content</p>
<h2>Sub-heading</h2>
<p>This is another sub-heading</p>""",
                         markdown_content)
