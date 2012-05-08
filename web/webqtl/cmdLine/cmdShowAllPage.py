# Copyright (C) University of Tennessee Health Science Center, Memphis, TN.
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License
# as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Affero General Public License for more details.
#
# This program is available from Source Forge: at GeneNetwork Project
# (sourceforge.net/projects/genenetwork/).
#
# Contact Drs. Robert W. Williams and Xiaodong Zhou (2010)
# at rwilliams@uthsc.edu and xzhou15@uthsc.edu
#
#
#
# This module is used by GeneNetwork project (www.genenetwork.org)
#
# Created by GeneNetwork Core Team 2010/08/10
#
# Last updated by GeneNetwork Core Team 2010/10/20

import os

from base import webqtlConfig
from base.templatePage import templatePage
from utility import webqtlUtil



class cmdShowAllPage(templatePage):

	def __init__(self,fd):

		templatePage.__init__(self, fd)

		filename = self.session("Generate Report", "Generating Report. Please be Patient")

		webqtlUtil.dump_session(fd, os.path.join(webqtlConfig.TMPDIR, filename +'.session'))

		url = webqtlConfig.REFRESHDIR  %  (webqtlConfig.CGIDIR, self.filename)

		os.system("%s %swebqtlCmdLine.py genreport %s >/dev/null 2>&1 &" % (webqtlConfig.PythonPath, webqtlConfig.CMDLINEDIR, filename))

		self.redirection = url

