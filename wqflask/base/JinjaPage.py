import logging
logging.basicConfig(filename="/tmp/gn_log", level=logging.INFO)
_log = logging.getLogger("search")

from pprint import pformat as pf

import templatePage

from utility import formatting

import jinja2
JinjaEnv = jinja2.Environment(loader=jinja2.FileSystemLoader('/gnshare/gn/web/webqtl/templates'))
JinjaEnv.globals['numify'] = formatting.numify


class JinjaPage(templatePage.templatePage):
    """Class derived from our regular templatePage, but uses Jinja2 instead.

    When converting pages from Python generated templates, change the base class from templatePage
    to JinjaPage

    """


    def write(self):
        """We override the base template write so we can use Jinja2."""
        _log.info(pf(self.__dict__))
        return self.jtemplate.render(**self.__dict__)
