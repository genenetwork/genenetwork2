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

import sys

from htmlgen import HTMLgen2 as HT

from base.templatePage import templatePage
from base import webqtlConfig
from utility import webqtlUtil



###################################################
#Description: show the schema of webqtl's database#
#Author: Hongqiang Li                             #
#Version: 1.0                                     #
###################################################

class ShowSchemaPage(templatePage):
    def __init__(self,fd):
	cookies = fd.cookies
        sys.stderr = sys.stdout
        templatePage.__init__(self, fd)
        body = HT.SimpleDocument()

        ###############################################################################
        #get user's privilege from cookie, if the user doesn't have enough privilege, #
        #he won't see the update comment icon                                         #
        ###############################################################################
        ShowUpdateIcon = False 

        if not self.openMysql():
           return

        Cursor_WebQtl = Cursor_Comment = self.cursor

        if webqtlConfig.USERDICT[self.privilege] >= webqtlConfig.USERDICT['user']:
			ShowUpdateIcon = True

        ##################
        #show description#
        ##################
        body.append('<BR>')
        body.append('<H1>')
        body.append('Description of Schema')
        if ShowUpdateIcon:
        #{
            # Modified by Hongqiang Li
            # Image_Update = HT.Image('http://web2qtl.utmem.edu/images/modify.gif')
            Image_Update = HT.Image('/images/modify.gif')
            #
            Href_Update = HT.Href(webqtlConfig.CGIDIR+'main.py?FormID=schemaShowComment&TableName=Description_of_Schema', Image_Update)
            body.append(Href_Update)
        #}
        body.append('</H1>')
         
        Cursor_WebQtl.execute('select Comment from TableComments where TableName=\'Description_of_Schema\'')
        Comment = Cursor_WebQtl.fetchone();
        if Comment:
            if str(Comment[0])!='None':
                body.append(Comment[0])

        body.append('<HR WIDTH=100%>')
        body.append('<H2>Tables</H2>')

        ##################
        #show table names#
        ##################
        Cursor_WebQtl.execute('show tables')
        Tables=Cursor_WebQtl.fetchall()
        BlockedTables = ['User', 'TableComments', 'TableFieldAnnotation', 'ProbeSetXRef_TEMP', 'DBList', 'DBType', 'HumanGene', 'LCorr', 'Temp', 'TempData']
        for i in range(0, len(Tables)):
        #{
            TableName = Tables[i][0]
            if TableName in BlockedTables: #skip the table who is blocked
                continue

            HrefTable_Schema = HT.Href(webqtlConfig.CGIDIR+'main.py?FormID=schemaShowPage#'+TableName, TableName)
            body.append(str(HrefTable_Schema)+'<BR>')
        #}
        body.append('<hr width=100%>')
    
        for i in range(0, len(Tables)):
        #{
            TableName = Tables[i][0]
            if TableName in BlockedTables: #skip the table who is blocked
                continue

            #####################
            #get table's comment#
            #####################
            SqlCmd = 'select Comment from TableComments where TableName=\'%s\'' %(TableName)
            Cursor_WebQtl.execute(SqlCmd)
            Comment = Cursor_WebQtl.fetchall()

            ####################################
            #get the content of a table's schma#
            ####################################
            Cursor_WebQtl.execute('desc %s' %(TableName))
            TableDesc = Cursor_WebQtl.fetchall();

            HtmlTR_Schema = []
            for row in range(0, len(TableDesc)):
            #{
                HtmlTD_Schema = []
                for col in range(0, len(TableDesc[row])):
                    if str(TableDesc[row][col])=='None' or str(TableDesc[row][col])=='': #just means I don't want show 'None' *_^
                       HtmlTD_Schema.append('&nbsp;')
                    else:
                       HtmlTD_Schema.append(TableDesc[row][col])

                ##############################
                #get table fileds' annotation#
                ##############################
                TableField = TableName+'.'+TableDesc[row][0]
                Cursor_WebQtl.execute('select Annotation, Foreign_Key from TableFieldAnnotation where TableField=%s', (TableField))
                Annotation = Cursor_WebQtl.fetchone();
                if Annotation:
                #{
                    if str(Annotation[1])=='None' or str(Annotation[1])=='':
                        HtmlTD_Schema.append('&nbsp;')
                    else:
                        HtmlTD_Schema.append(Annotation[1])
                    if str(Annotation[0])=='None' or str(Annotation[0])=='':
                        HtmlTD_Schema.append('&nbsp;')
                    else:
                        HtmlTD_Schema.append(Annotation[0])
                #}
                else:
                #{
                    HtmlTD_Schema.append('&nbsp;')
                    HtmlTD_Schema.append('&nbsp;')
                #}

            	HtmlTR_Schema.append(HtmlTD_Schema)
            #}

            ###############################
            #Html code of a table's schema#
            ###############################
            body.append(HT.NAME(TableName, TableName))
            if ShowUpdateIcon:
            #{
                # Modified by Hongqiang Li
                #Image_Update = HT.Image('http://web2qtl.utmem.edu/images/modify.gif')
                Image_Update = HT.Image('/images/modify.gif')
                #
                Href_Update = HT.Href(webqtlConfig.CGIDIR+'main.py?FormID=schemaShowComment&TableName=%s' %(TableName), Image_Update)
                body.append(Href_Update)
            #}
            body.append('<BR><BR>')

            body.append('<B>Comment:</B><BR>')
            #body.append("<I>")
            if Comment:
                if str(Comment[0][0])!='None':
                    for content in Comment[0][0].split('\n'):
                        body.append(content)
                        body.append('<BR>')
            #body.append("</I>")

            HtmlTable_Schema = HT.Table(width='0%', heading=['Field', 'Type', 'Null', 'Key', 'Default', 'Extra', 'Foreign_Key', 'Annotation'], body = HtmlTR_Schema)
            body.append(HtmlTable_Schema)
            body.append('<hr width=100%>')
        #}

        self.dict['body'] = body



