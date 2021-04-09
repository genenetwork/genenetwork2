import unittest

import htmlgen as HT
from wqflask.marker_regression.display_mapping_results import (
    DisplayMappingResults,
    HtmlGenWrapper
)


class TestDisplayMappingResults(unittest.TestCase):
    """Basic Methods to test Mapping Results"""
    def test_pil_colors(self):
        """Test that colors use PILLOW color format"""
        self.assertEqual(DisplayMappingResults.CLICKABLE_WEBQTL_REGION_COLOR,
                         (245, 211, 211))


class TestHtmlGenWrapper(unittest.TestCase):
    """Test Wrapper around HTMLGen"""
    def test_create_image(self):
        """Test HT.Image method"""
        self.assertEqual(
            str(HtmlGenWrapper.create_image_tag(src="test.png",
                                                alt="random",
                                                border="0",
                                                width="10",
                                                height="13",
                                                usemap="#webqtlmap")),
            ("""<img alt="random" border="0" height="13" """
             """src="test.png" usemap="#webqtlmap" """
             """width="10"/>""")
        )

    def test_create_form(self):
        """Test HT.Form method"""
        test_form = HtmlGenWrapper.create_form_tag(
            cgi="/testing/",
            enctype='multipart/form-data',
            name="formName",
            submit=HtmlGenWrapper.create_input_tag(type_='hidden', name='Default_Name')
        )
        test_image = HtmlGenWrapper.create_image_tag(
            src="test.png",
            alt="random",
            border="0",
            width="10",
            height="13",
            usemap="#webqtlmap"
        )
        self.assertEqual(
            str(test_form).replace("\n", ""),
            ("""<form action="/testing/" enctype="multipart/form-data" """
             """method="POST" """
             """name="formName"><input name="Default_Name" """
             """type="hidden"/></form>"""))
        hddn = {
            'FormID': 'showDatabase',
            'ProbeSetID': '_',
            'database': "TestGeno",
            'CellID': '_',
            'RISet': "Test",
            'incparentsf1': 'ON'
        }
        for key in hddn.keys():
            test_form.append(
                HtmlGenWrapper.create_input_tag(
                    name=key,
                    value=hddn[key],
                    type_='hidden'))
        test_form.append(test_image)

        self.assertEqual(str(test_form).replace("\n", ""), (
            """<form action="/testing/" enctype="multipart/form-data" """
            """method="POST" name="formName">"""
            """<input name="Default_Name" type="hidden"/>"""
            """<input name="FormID" type="hidden" value="showDatabase"/>"""
            """<input name="ProbeSetID" type="hidden" value="_"/>"""
            """<input name="database" type="hidden" value="TestGeno"/>"""
            """<input name="CellID" type="hidden" value="_"/>"""
            """<input name="RISet" type="hidden" value="Test"/>"""
            """<input name="incparentsf1" type="hidden" value="ON"/>"""
            """<img alt="random" border="0" height="13" src="test.png" """
            """usemap="#webqtlmap" width="10"/>"""
            """</form>"""))

    def test_create_paragraph(self):
        """Test HT.Paragraph method"""
        test_p_element = HtmlGenWrapper.create_p_tag(id="smallSize")
        par_text = (
            "Mapping using genotype data as "
            "a trait will result in infinity LRS at one locus. "
            "In order to display the result properly, all LRSs "
            "higher than 100 are capped at 100."
        )
        self.assertEqual(
            str(test_p_element),
            """<p id="smallSize"></p>"""
        )
        test_p_element.append(HtmlGenWrapper.create_br_tag())
        test_p_element.append(par_text)
        self.assertEqual(
            str(test_p_element),
            """<p id="smallSize"><br/>{}</p>""".format(par_text)
        )

    def test_create_br_tag(self):
        """Test HT.BR() method"""
        self.assertEqual(str(HtmlGenWrapper.create_br_tag()),
                         "<br/>")

    def test_create_input_tag(self):
        """Test HT.Input method"""
        self.assertEqual(
            str(HtmlGenWrapper.create_input_tag(
                type_="hidden",
                name="name",
                value="key",
                Class="trait trait_")).replace("\n", ""),
            ("""<input class="trait trait_" name="name" """
             """type="hidden" value="key"/>"""))

    def test_create_map_tag(self):
        """Test HT.Map method"""
        self.assertEqual(str(HtmlGenWrapper.create_map_tag(
            name="WebqTLImageMap")).replace("\n", ""),
            """<map name="WebqTLImageMap"></map>""")
        gifmap = HtmlGenWrapper.create_map_tag(name="test")
        gifmap.append(HtmlGenWrapper.create_area_tag(shape="rect",
                                                     coords='1 2 3', href='#area1'))
        gifmap.append(HtmlGenWrapper.create_area_tag(shape="rect",
                                                     coords='1 2 3', href='#area2'))
        self.assertEqual(
            str(gifmap).replace("\n", ""),
            ("""<map name="test">"""
             """<area coords="1 2 3" """
             """href="#area1" shape="rect"/>"""
             """<area coords="1 2 3" href="#area2" shape="rect"/>"""
             """</map>"""))

    def test_create_area_tag(self):
        """Test HT.Area method"""
        self.assertEqual(
            str(HtmlGenWrapper.create_area_tag(
                shape="rect",
                coords="1 2",
                href="http://test.com",
                title="Some Title")).replace("\n", ""),
            ("""<area coords="1 2" href="http://test.com" """
             """shape="rect" title="Some Title"/>"""))

    def test_create_link_tag(self):
        """Test HT.HREF method"""
        self.assertEqual(
            str(HtmlGenWrapper.create_link_tag(
                "www.test.com", "test", target="_blank")).replace("\n", ""),
            """<a href="www.test.com" target="_blank">test</a>""")
