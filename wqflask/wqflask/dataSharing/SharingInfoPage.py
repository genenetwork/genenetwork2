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

from __future__ import print_function, division

from pprint import pformat as pf

import flask

from base.templatePage import templatePage
from base import webqtlConfig
from dbFunction import webqtlDatabaseFunction
import SharingBody
import SharingInfo


#########################################
#      Sharing Info Page
#########################################
class SharingInfoPage(templatePage):

    def __init__(self, fd):
        templatePage.__init__(self, fd)
        self.redirect_url = None   # Set if you want a redirect
        print("fd is:", pf(fd.__dict__))
        # Todo: Need a [0] in line below????d
        GN_AccessionId = fd.get('GN_AccessionId')   # Used under search datasharing
        InfoPageName = fd.get('database')  # Might need to add a [0]
        cursor = webqtlDatabaseFunction.getCursor()
        if InfoPageName and not GN_AccessionId:
            sql = "select GN_AccesionId from InfoFiles where InfoPageName = %s"
            cursor.execute(sql, InfoPageName)
            GN_AccessionId = cursor.fetchone()
            self.redirect_url = "http://23.21.59.238:5001/data_sharing?GN_AccessionId=%s" % GN_AccessionId
            #self.redirect_url = flask.url_for('data_sharing', GN_AccessionId=GN_AccessionId[0])
            print("set self.redirect_url")
            #print("before redirect")
            #return flask.redirect(url)
            #print("after redirect")
        else:
            CauseError
