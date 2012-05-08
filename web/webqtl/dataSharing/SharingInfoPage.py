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

from base.templatePage import templatePage
from base import webqtlConfig
from dbFunction import webqtlDatabaseFunction
import SharingBody
import SharingInfo


#########################################
#      Sharing Info Page
#########################################
class SharingInfoPage(templatePage):

		def __init__(self, fd=None):
				templatePage.__init__(self, fd)
				GN_AccessionId = fd.formdata.getvalue('GN_AccessionId')
				InfoPageName = fd.formdata.getvalue('InfoPageName')
				cursor = webqtlDatabaseFunction.getCursor()
				if InfoPageName and not GN_AccessionId:
					sql = "select GN_AccesionId from InfoFiles where InfoPageName = %s"
					cursor.execute(sql, InfoPageName)
					GN_AccessionId = cursor.fetchone()
					url = webqtlConfig.CGIDIR + "main.py?FormID=sharinginfo&GN_AccessionId=%s" % GN_AccessionId
					self.redirection = url
				else:
					sharingInfoObject = SharingInfo.SharingInfo(GN_AccessionId, InfoPageName)
					self.dict['body'] = sharingInfoObject.getBody(infoupdate="")
