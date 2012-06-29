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
import SharingBody
import SharingInfo


#########################################
#      Sharing Info Edit Page
#########################################
class SharingInfoEditPage(templatePage):

		def __init__(self, fd=None):
				templatePage.__init__(self, fd)
				if webqtlConfig.USERDICT[self.privilege] >= webqtlConfig.USERDICT['admin']:
						pass
				else:
						heading = "Editing Info"
						detail = ["You don't have the permission to edit this dataset"]
						self.error(heading=heading,detail=detail,error="Error")
						return
				GN_AccessionId = fd.formdata.getvalue('GN_AccessionId')
				InfoPageName = fd.formdata.getvalue('InfoPageName')
				sharingInfoObject = SharingInfo.SharingInfo(GN_AccessionId, InfoPageName)
				info, filelist = sharingInfoObject.getInfo()
				self.dict['body'] = SharingBody.sharinginfoedit_body_string % (info[31], info[0], info[11], info[12], info[13], info[14], info[15], info[16], info[17], info[18], info[19], info[20], info[21], info[22], info[6], info[5], info[35], info[36], info[37], info[38], info[39], info[7], info[8], info[9], info[40], info[32], info[31], info[1], info[2], info[3], info[30], info[4], info[10], info[23], info[25], info[33], info[26], info[27], info[28], info[24], info[34], info[41])
