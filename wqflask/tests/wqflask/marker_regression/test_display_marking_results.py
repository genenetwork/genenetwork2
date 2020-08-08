import unittest

from wqflask.marker_regression.display_mapping_results import DisplayMappingResults

class TestDisplayMappingResults(unittest.TestCase):
    def test_pil_colors(self):
        """Test that colors use PILLOW color format"""
        self.assertEqual(DisplayMappingResults.CLICKABLE_WEBQTL_REGION_COLOR,
                         (245, 211, 211))
