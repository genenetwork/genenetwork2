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
class createUserAccountPage(templatePage):

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

            user_name = fd.formdata.getvalue('user_name')
            password = fd.formdata.getvalue('password')
            retype_password = fd.formdata.getvalue('retype_password')

            if user_name or password or retype_password:
                user_name = string.strip(user_name)
                password = string.strip(password)
                retype_password = string.strip(retype_password)

                #XZ, check if the input user name exists.

                if len(user_name) == 0:
                    heading = "Error page"
                    detail = ["The user name can NOT be empty."]
                    self.error(heading=heading,detail=detail)
                    return

                self.cursor.execute( 'select count(name) from User where name="%s"' % user_name )
                result = self.cursor.fetchone()
                if result:
                    row_count = result[0]
                    if row_count:
                        heading = "Error page"
                        detail = ["The user name %s already exists in database. Please make up another user name." % user_name]
                        self.error(heading=heading,detail=detail)
                        return
                else:
                    heading = "Error page"
                    detail = ["No sql result returned when check user name."]
                    self.error(heading=heading,detail=detail)
                    return

                # check password
                if len(password) == 0 or len(retype_password) == 0:
                    heading = "Error page"
                    detail = ["The password can NOT be empty."]
                    self.error(heading=heading,detail=detail)
                    return
 
                if password != retype_password:
                    heading = "Error page"
                    detail = ["The passwords you entered are NOT consistent. Please go back and try again."]
                    self.error(heading=heading,detail=detail)
                    return

                #XZ, create new account
                self.cursor.execute( "insert into User (name, password, createtime, privilege) values ('%s', SHA('%s'), Now(), 'user')" % (user_name, password) )


            #show user table.
            TD_LR = HT.TD(height=200,width="100%",bgColor='#eeeeee')

            userHeading = HT.Paragraph('User Table', Class="title")

            self.cursor.execute( 'select id, name, privilege from User order by name' )

            result = self.cursor.fetchall()

            userInfo = HT.Blockquote( 'There are %d users.' % len(result) )

            userTable = HT.TableLite(border=0, cellpadding=0, cellspacing=0, Class="collap", width="100%")

            userHeaderRow = HT.TR()
            userHeaderRow.append(HT.TD("User Id", Class='fs14 fwb ffl b1 cw cbrb'))
            userHeaderRow.append(HT.TD("User name", Class='fs14 fwb ffl b1 cw cbrb'))
            userHeaderRow.append(HT.TD("User privilege", Class='fs14 fwb ffl b1 cw cbrb'))
            userTable.append(userHeaderRow)

            for one_row in result:
                User_Id, User_name, User_privilege = one_row
                userRow = HT.TR()
                userRow.append(HT.TD("%s" % User_Id, Class='fs12 fwn ffl b1 c222'))
                userRow.append(HT.TD("%s" % User_name, Class='fs12 fwn ffl b1 c222'))
                userRow.append(HT.TD("%s" % User_privilege, Class='fs12 fwn ffl b1 c222'))
                userTable.append(userRow)

            #add user form
            createUserAccountForm = HT.Form(cgi= os.path.join(webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE), enctype='multipart/form-data', name='createUserAccountForm', submit=HT.Input(type='hidden'))

            user_name = HT.Input(type='text' ,name='user_name',value='', size=20,maxlength=20)
            password = HT.Input(type='password' ,name='password',value='', size=20,maxlength=20)
            retype_password = HT.Input(type='password' ,name='retype_password',value='', size=20,maxlength=20)
            submit_button = HT.Input(type='Submit', value='Submit', Class="button")

            createUserAccountForm.append(
                HT.Blockquote( HT.Font('Create one new account:     User Name ', color='red'), user_name, HT.Font('   Password ', color='red'), password, HT.Font('   Retype Password ', color='red'), retype_password, submit_button ),
                HT.Input(type='hidden',name='FormID',value='createUserAccount'),
                HT.Input(type='hidden',name='ifVerified',value='GN@UTHSC')
            )

            """
            #manager form
            managerForm = HT.Form(cgi= os.path.join(webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE), enctype='multipart/form-data', name='managerForm', submit=HT.Input(type='hidden'))
            managerForm.append(
                HT.Input(type='Submit', value='Go to manager main page', Class="button"),
                HT.Input(type='hidden',name='FormID',value='managerMain'),
                HT.Input(type='hidden',name='ifVerified',value='GN@UTHSC')
            )
            """

            #TD_LR.append(managerForm, HT.BR(), userHeading, userInfo, HT.P(), createUserAccountForm, userTable, createUserAccountForm, HT.BR(), managerForm)
            TD_LR.append(userHeading, userInfo, HT.P(), createUserAccountForm, userTable, createUserAccountForm)

            self.dict['body'] =  str(TD_LR)
            self.dict['title'] = 'User account' 
