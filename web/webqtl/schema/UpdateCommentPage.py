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


class UpdateCommentPage(templatePage):
    def __init__(self,fd):
        sys.stderr = sys.stdout
        templatePage.__init__(self, fd)
        body = HT.SimpleDocument()        

        if not self.updMysql():
        #{
            print 'Content-type: text/html\n'
            print 'Can not update the comment of %s' %(TableName)
            return
        #}


        Cursor_Comment=self.cursor
        TableName = fd.formdata.getfirst('TableName')
        Comment = fd.formdata.getfirst('Comment')

        ########################
        #update table's comment#
        ########################
        Cursor_Comment.execute('select * from TableComments where TableName=%s', (TableName))
        if Cursor_Comment.fetchall():
            Cursor_Comment.execute('update TableComments set Comment=%s where TableName=%s', (Comment, TableName))
        else:
            Cursor_Comment.execute('insert into TableComments values(%s,%s)', (TableName, Comment))


        #################################
        #update table fields' annotation#
        #################################
        try:
        #{
            Cursor_Comment.execute('desc %s' %(TableName))
            TableDesc = Cursor_Comment.fetchall()
            for i in range(0, len(TableDesc)):
            #{
                TableField = TableName+'.'+str(TableDesc[i][0])
                TableFieldForeignKey = TableField+'ForeignKey'
                TableFieldAnnotation = TableField+'Annotation'

                ForeignKey = fd.formdata.getfirst(TableFieldForeignKey)
                if ForeignKey == 'None':
                    ForeignKey=''
                Annotation = fd.formdata.getfirst(TableFieldAnnotation)
                if Annotation == 'None':
                    Annotation='&nbsp;'

                Cursor_Comment.execute('select * from TableFieldAnnotation where TableField=%s', (TableField))
                if Cursor_Comment.fetchall():
                    Cursor_Comment.execute('update TableFieldAnnotation set Foreign_Key=%s, Annotation=%s where TableField=%s', (ForeignKey, Annotation, TableField))
                else:
                    Cursor_Comment.execute('insert into TableFieldAnnotation values(%s,%s,%s)', (TableField, ForeignKey, Annotation))
            #}
        #}
        except:
            pass

        HtmlHref = HT.Href(webqtlConfig.CGIDIR+'main.py?FormID=schemaShowPage#%s' %(TableName), 'table')
        HtmlBlock = HT.Blockquote();
        HtmlBlock.append('This ')
        HtmlBlock.append(HtmlHref)
        HtmlBlock.append('\'s comment has been succesfully updated')

        body.append(HtmlBlock)
        self.dict['body'] = body

