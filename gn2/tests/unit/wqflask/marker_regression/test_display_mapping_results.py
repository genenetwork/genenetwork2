import unittest

from gn2.wqflask.marker_regression.display_mapping_results import (
    DisplayMappingResults,
    _make_area
)


class TestDisplayMappingResults(unittest.TestCase):
    """Basic Methods to test Mapping Results"""

    def test_pil_colors(self):
        """Test that colors use PILLOW color format"""
        self.assertEqual(DisplayMappingResults.CLICKABLE_WEBQTL_REGION_COLOR,
                         (245, 211, 211))


class TestMakeArea(unittest.TestCase):
    """The image map areas the figure builds for its tooltips"""

    def test_area_tag(self):
        self.assertEqual(
            _make_area(coords="1 2 3 4", href="http://test.com",
                       title="Some Title"),
            ('<area shape="rect" coords="1 2 3 4" '
             'href="http://test.com" title="Some Title">'))

    def test_area_tag_without_title_or_target(self):
        self.assertEqual(
            _make_area(coords="1 2 3 4", href=""),
            '<area shape="rect" coords="1 2 3 4" href="">')

    def test_area_tag_with_target(self):
        self.assertEqual(
            _make_area(coords="1 2 3 4", href="/show_trait",
                       target="_blank"),
            ('<area shape="rect" coords="1 2 3 4" '
             'href="/show_trait" target="_blank">'))
