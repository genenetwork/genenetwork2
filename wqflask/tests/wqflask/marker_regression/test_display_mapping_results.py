import unittest

from htmlgen import HTMLgen2 as HT
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
            ("""<IMG src="test.png" height="13" width="10" """
             """alt="random" border="0" """
             """usemap="#webqtlmap">""")
        )

    def test_create_form(self):
        """Test HT.Form method"""
        test_form = HtmlGenWrapper.create_form_tag(
            cgi="/testing/",
            enctype='multipart/form-data',
            name="formName",
            submit=HT.Input(type='hidden')
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
            ("""<FORM METHOD="POST" ACTION="/testing/" """
             """ENCTYPE="multipart/form-data" """
             """NAME="formName"><INPUT TYPE="hidden" """
             """NAME="Default_Name"></FORM>"""))
        hddn = {
            'FormID': 'showDatabase',
            'ProbeSetID': '_',
            'database': "TestGeno",
            'CellID': '_',
            'RISet': "Test",
            'incparentsf1': 'ON'
        }
        for key in hddn.keys():
            test_form.append(HT.Input(name=key, value=hddn[key],
                                      type='hidden'))
        test_form.append(test_image)
        self.assertEqual(str(test_form).replace("\n", ""), (
            """<FORM METHOD="POST" ACTION="/testing/" """
            """ENCTYPE="multipart/form-data" NAME="formName">"""
            """<INPUT TYPE="hidden" NAME="database" VALUE="TestGeno">"""
            """<INPUT TYPE="hidden" NAME="incparentsf1" VALUE="ON">"""
            """<INPUT TYPE="hidden" NAME="FormID" VALUE="showDatabase">"""
            """<INPUT TYPE="hidden" NAME="ProbeSetID" VALUE="_">"""
            """<INPUT TYPE="hidden" NAME="RISet" VALUE="Test">"""
            """<INPUT TYPE="hidden" NAME="CellID" VALUE="_">"""
            """<IMG src="test.png" height="13" width="10" alt="random" """
            """border="0" usemap="#webqtlmap">"""
            """<INPUT TYPE="hidden" NAME="Default_Name"></FORM>"""))

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
            """<P id="smallSize"></P>"""
        )
        test_p_element.append(HT.BR())
        test_p_element.append(par_text)
        self.assertEqual(
            str(test_p_element),
            """<P id="smallSize"><BR>{}</P>""".format(par_text)
        )

    def test_create_br_tag(self):
        """Test HT.BR() method"""
        self.assertEqual(str(HtmlGenWrapper.create_br_tag()),
                         "<BR>")

    def test_create_input_tag(self):
        """Test HT.Input method"""
        self.assertEqual(
            str(HtmlGenWrapper.create_input_tag(
                type="hidden",
                name="name",
                value="key",
                Class="trait trait_")).replace("\n", ""),
            ("""<INPUT TYPE="hidden" NAME="name" """
             """class="trait trait_" VALUE="key">"""))

    def test_create_map_tag(self):
        """Test HT.Map method"""
        self.assertEqual(str(HtmlGenWrapper.create_map_tag(
            name="WebqTLImageMap")).replace("\n", ""),
            """<MAP NAME="WebqTLImageMap"></MAP>""")
        gifmap = HtmlGenWrapper.create_map_tag(areas=[])
        gifmap.areas.append(HT.Area(shape="rect",
                                    coords='1 2 3', href='#area1'))
        gifmap.areas.append(HT.Area(shape="rect",
                                    coords='1 2 3', href='#area2'))
        self.assertEqual(
            str(gifmap).replace("\n", ""),
            ("""<MAP NAME="">"""
             """<AREA coords="1 2 3" """
             """href="#area1" shape="rect">"""
             """<AREA coords="1 2 3" href="#area2" shape="rect">"""
             """</MAP>"""))

    def test_create_area_tag(self):
        """Test HT.Area method"""
        self.assertEqual(
            str(HtmlGenWrapper.create_area_tag(
                shape="rect",
                coords="1 2",
                href="http://test.com",
                title="Some Title")).replace("\n", ""),
            ("""<AREA coords="1 2" href="http://test.com" """
             """shape="rect" title="Some Title">"""))

    def test_create_link_tag(self):
        """Test HT.HREF method"""
        self.assertEqual(
            str(HtmlGenWrapper.create_link_tag(
                "www.test.com", "test", target="_blank")).replace("\n", ""),
            """<A HREF="www.test.com" TARGET="_blank">test</A>""")
