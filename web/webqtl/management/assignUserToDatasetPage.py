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
import string

from htmlgen import HTMLgen2 as HT

from base.templatePage import templatePage
from base import webqtlConfig

#XZ, 02/06/2009: Xiaodong created this class
class assignUserToDatasetPage(templatePage):

    def __init__(self, fd):

        templatePage.__init__(self, fd)

        if not self.openMysql():
            return


        ifVerified = fd.formdata.getvalue('ifVerified')

        if ifVerified != 'GN@UTHSC':
            heading = "Error page"
            detail = ["You are NoT verified as administrator."]
            self.error(heading=heading,detail=detail)
            return
        else:

            ProbeSetFreeze_FullName = fd.formdata.getvalue('ProbeSetFreeze_FullName')
            User_name = fd.formdata.getvalue('User_name')

            if ProbeSetFreeze_FullName and User_name:
                ProbeSetFreeze_FullName = string.strip(ProbeSetFreeze_FullName)
                User_name = string.strip(User_name)

                #XZ, check if the input dataset name exists.
                self.cursor.execute( 'select count(FullName) from ProbeSetFreeze where FullName="%s"' % ProbeSetFreeze_FullName )
                result = self.cursor.fetchone()
                if result:
                    row_count = result[0]
                    if row_count:
                        pass
                    else:
                        heading = "Error page"
                        detail = ["The dataset name %s does NOT exist in database." % ProbeSetFreeze_FullName]
                        self.error(heading=heading,detail=detail)
                        return
                else:
                    heading = "Error page"
                    detail = ["No sql result returned when check dataset name."]
                    self.error(heading=heading,detail=detail)
                    return

                #XZ, check if the input user name exists.
                self.cursor.execute( 'select count(name) from User where name="%s"' % User_name )
                result = self.cursor.fetchone()
                if result:
                    row_count = result[0]
                    if row_count:
                        pass
                    else:
                        heading = "Error page"
                        detail = ["The user name %s does NOT exist in database." % User_name]
                        self.error(heading=heading,detail=detail)
                        return
                else:
                    heading = "Error page"
                    detail = ["No sql result returned when check user name."]
                    self.error(heading=heading,detail=detail)
                    return

                self.cursor.execute( 'select AuthorisedUsers from ProbeSetFreeze where FullName="%s"' % ProbeSetFreeze_FullName )
                result = self.cursor.fetchone() # The FullName is unique.
                if result:
                    AuthorisedUsers = result[0]
                    if not AuthorisedUsers:
                        self.cursor.execute('update ProbeSetFreeze set AuthorisedUsers="%s" where FullName="%s"' %(User_name, ProbeSetFreeze_FullName) )
                    else:
                        AuthorisedUsersList=AuthorisedUsers.split(',')
                        if not AuthorisedUsersList.__contains__(User_name):
                            AuthorisedUsers = AuthorisedUsers + ',%s' % User_name
                            self.cursor.execute('update ProbeSetFreeze set AuthorisedUsers="%s" where FullName="%s"' %(AuthorisedUsers, ProbeSetFreeze_FullName) )
                else:
                    heading = "Error page"
                    detail = ["No sql result returned when query AuthorisedUsers."]
                    self.error(heading=heading,detail=detail)
                    return


            TD_LR = HT.TD(height=200,width="100%",bgColor='#eeeeee')

            dataHeading = HT.Paragraph('Confidential Dataset Table', Class="title")

            dataTable = HT.TableLite(border=1, cellpadding=0, cellspacing=0, Class="collap", width="100%")

            dataHeaderRow = HT.TR()
            dataHeaderRow.append(HT.TD("Dataset Id", Class='fs14 fwb ffl b1 cw cbrb'))
            dataHeaderRow.append(HT.TD("Dataset Full Name", Class='fs14 fwb ffl b1 cw cbrb'))
            dataHeaderRow.append(HT.TD("Authorised User", Class='fs14 fwb ffl b1 cw cbrb'))
            dataTable.append(dataHeaderRow)

            self.cursor.execute('select Id, FullName, AuthorisedUsers from ProbeSetFreeze where confidentiality=1 order by FullName,Id')

            result = self.cursor.fetchall()

            dataInfo = HT.Blockquote( 'There are %d confidential datasets.' % len(result) )


            for one_row in result:
                ProbeSetFreeze_Id, ProbeSetFreeze_FullName, ProbeSetFreeze_AuthorisedUsers = one_row
                dataRow = HT.TR()
                dataRow.append(HT.TD("%s" % ProbeSetFreeze_Id, Class='fs12 fwn ffl b1 c222'))
                dataRow.append(HT.TD("%s" % ProbeSetFreeze_FullName, Class='fs12 fwn ffl b1 c222'))
                dataRow.append(HT.TD("%s" % ProbeSetFreeze_AuthorisedUsers, Class='fs12 fwn ffl b1 c222'))
                dataTable.append(dataRow)

            assignUserForm = HT.Form(cgi= os.path.join(webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE), enctype='multipart/form-data', name='assignUserForm', submit=HT.Input(type='hidden'))
            assignUserForm.append(
                HT.Blockquote(
                              HT.Font('Dataset Full Name ', color='red'),
                              HT.Input(type='text' ,name='ProbeSetFreeze_FullName',value='', size=50,maxlength=200),
                              HT.Font('   User name ', color='red'),
                              HT.Input(type='text' ,name='User_name',value='', size=20,maxlength=20),
                              HT.Input(type='Submit', value='Submit', Class="button")),
                HT.Input(type='hidden',name='FormID',value='assignUserToDataset'),
                HT.Input(type='hidden',name='ifVerified',value='GN@UTHSC')
            )

            TD_LR.append(dataHeading, dataInfo, assignUserForm, dataTable, assignUserForm)

            self.dict['body'] =  str(TD_LR)
            self.dict['title'] =  'Confidential datasets'

