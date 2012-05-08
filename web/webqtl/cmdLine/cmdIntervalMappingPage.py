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

#########################################
#      Interval Mapping Page
#########################################

class cmdIntervalMappingPage(templatePage):

	def __init__(self,fd):

		templatePage.__init__(self, fd)

		wtext = "Mapping "
		try:
			selectedChr = int(fd.formdata.getvalue('chromosomes')) + 1
			if selectedChr < 1:
				raise "ValueError"
			if selectedChr == 21 or (selectedChr == 20 and fd.RISet != 'HXBBXH'):
				selectedChr = 'X'
			wtext += 'chromosome %s ' % selectedChr
		except:
			wtext += 'whole genome '

		perm = 0
		if fd.formdata.getvalue('permCheck'):
			perm = 1
			wtext += 'with %d permutation tests ' % fd.nperm

		boot = 0
		if fd.formdata.getvalue('bootCheck'):
			boot = 1
			if perm:
				wtext += 'and %d bootstrap tests ' % fd.nboot
			else:
				wtext += 'with %d bootstrap tests ' % fd.nboot
		
		if boot == 0 and perm == 0:
			wtext +=  "without permutation or bootstrap tests"
		
		filename = self.session("Interval Mapping", wtext)
		webqtlUtil.dump_session(fd, os.path.join(webqtlConfig.TMPDIR, filename +'.session'))
		url = webqtlConfig.REFRESHDIR  %  (webqtlConfig.CGIDIR, self.filename)
		os.system("%s %swebqtlCmdLine.py interval %s >/dev/null 2>&1 &" % (webqtlConfig.PythonPath, webqtlConfig.CMDLINEDIR, filename))
		self.redirection = url

