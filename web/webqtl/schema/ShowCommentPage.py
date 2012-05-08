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



class ShowCommentPage(templatePage):
    def __init__(self,fd):
        sys.stderr = sys.stdout

        templatePage.__init__(self, fd)

        if not self.openMysql():
        #{
            print 'Content-type: text/html\n'
            print 'Can not update the comment of %s' %(TableName)
            return
        #}

        Cursor_Comment = self.cursor
        TableName = fd.formdata.getfirst('TableName')

        SqlCmd = 'select Comment from TableComments where TableName=\'%s\'' %(TableName)
        Cursor_Comment.execute(SqlCmd)
        Comment = Cursor_Comment.fetchall()
        if Comment:
           Comment = Comment[0][0]
           if str(Comment)=='None':
              Comment=''
        else:
           Comment = ''

        ##########setup HtmlForm Comment##########
        HtmlInputHidden_TableName = HT.Input(type='hidden', name='TableName', value=TableName)
        HtmlInputHidden_ActionID = HT.Input(type='hidden', name='ActionID', value='UpdateComment')
        HtmlTextarea_Comment = HT.Textarea(name='Comment', text=Comment, rows=8, cols=100)

        HtmlForm_Comment = HT.Form(cgi=webqtlConfig.CGIDIR+'main.py?FormID=schemaUpdateComment')
        HtmlForm_Comment.append('<B>%s</B><BR><BR>' %(TableName))  #show table's name
        HtmlForm_Comment.append('<B><I>Comment:</I></B><BR>')           #show table's comment
        HtmlForm_Comment.append(HtmlTextarea_Comment)
        HtmlForm_Comment.append('<BR>')
        HtmlForm_Comment.append(HtmlInputHidden_TableName)
        HtmlForm_Comment.append(HtmlInputHidden_ActionID)

        ###########################
        #update fields' annotation#
        ###########################
        HtmlForm_Comment.append('<BR><BR>')

        try:
        #{
            HtmlTR_Annotation = []
            Cursor_Comment.execute('desc %s' %(TableName))
            TableDesc = Cursor_Comment.fetchall()
            for i in range(0, len(TableDesc)):
            #{
                TableField = TableName+'.'+str(TableDesc[i][0])
                TableFieldForeignKey = TableField+'ForeignKey'
                TableFieldAnnotation = TableField+'Annotation'
                HtmlText_ForeignKey = HT.Input(type='text', name=TableFieldForeignKey, size=20)
                HtmlText_Annotation = HT.Input(type='text', name=TableFieldAnnotation, size=80)


                Cursor_Comment.execute('select Annotation, Foreign_Key from TableFieldAnnotation where TableField=%s', (TableField))
                Annotation = Cursor_Comment.fetchone()
                if Annotation:
                #{
                    if str(Annotation[1]) != 'None':
                        HtmlText_ForeignKey.value=Annotation[1]
                    if str(Annotation[0]) != 'None':
                        HtmlText_Annotation.value=Annotation[0].replace('"', '&quot;')
                #}
                HtmlTD_Annotation = []
                HtmlTD_Annotation.append(TableField)
                HtmlTD_Annotation.append(HtmlText_ForeignKey)
                HtmlTD_Annotation.append(HtmlText_Annotation)
   
                HtmlTR_Annotation.append(HtmlTD_Annotation)
            #}

            HtmlTable_Annotation= HT.Table(border=0, width='0%', heading=['Field', 'Foreign_Key', 'Annotation'], body = HtmlTR_Annotation)
            HtmlForm_Comment.append(HtmlTable_Annotation)
        #}
        except:
            pass

        HtmlForm_Comment.submit.value='submit'
        HtmlForm_Comment.reset = HT.Input(type='reset', name='reset', value='reset')
        ##########end of HtmlForm##########

        self.dict['body'] = HtmlForm_Comment


