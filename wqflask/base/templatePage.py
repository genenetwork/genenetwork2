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

#templatePage.py
#
#--Genenetwork generates a lot of pages; this file is the generic version of them, defining routines they all use.
#
#Classes:
#templatePage
#
#Functions (of templatePage):
#__init__(...) -- class constructor, allows a more specific template to be used in addition to templatePage
#__str__(self) -- returns the object's elements as a tuple
#__del__(self) -- closes the current connection to MySQL, if there is one
#write -- explained below
#writefile -- explained below
#openMysql(self) -- opens a MySQL connection and stores the resulting cursor in the object's cursor variable
#updMysql(self) -- same as openMysql
#error -- explained below
#session -- explained below


import socket
import time
import shutil
import MySQLdb
import os

from htmlgen import HTMLgen2 as HT

import template
import webqtlConfig
import header
import footer
from utility import webqtlUtil



class templatePage:

    contents = ['title','basehref','js1','js2', 'layer', 'header', 'body', 'footer']

    # you can pass in another template here if you want
    def __init__(self, fd=None, template=template.template):

        # initiate dictionary
        self.starttime = time.time()
        self.dict = {}
        self.template = template

        for item in self.contents:
            self.dict[item] = ""

        self.dict['basehref'] = "" #webqtlConfig.BASEHREF
        self.cursor = None

        self.cookie = [] #XZ: list to hold cookies (myCookie object) being changed
        self.content_type = 'text/html'
        self.content_disposition = ''
        self.redirection = ''
        self.debug = ''
        self.attachment = ''

        #XZ: Holding data (new data or existing data being changed) that should be saved to session. The data must be picklable!!!
        self.session_data_changed = {}

        self.userName = 'Guest'
        self.privilege = 'guest'

        # Commenting this out for flask - we'll have to reimplement later - Sam
        #if fd.input_session_data.has_key('user'):
        #       self.userName = fd.input_session_data['user']
        #if fd.input_session_data.has_key('privilege'):
        #       self.privilege = fd.input_session_data['privilege']

    def __str__(self):

        #XZ: default setting
        thisUserName = self.userName
        thisPrivilege = self.privilege
        #XZ: user may just go through login or logoff page
        if self.session_data_changed.has_key('user'):
            thisUserName = self.session_data_changed['user']
        if self.session_data_changed.has_key('privilege'):
            thisPrivilege = self.session_data_changed['privilege']

        if thisUserName == 'Guest':
            userInfo = 'Welcome! <a href=/account.html><U>Login</U></a>'
        else:
            userInfo = 'Hi, %s! <a href=/webqtl/main.py?FormID=userLogoff><U>Logout</U></a>' % thisUserName

        reload(header)
        self.dict['header'] = header.header_string % userInfo

        serverInfo = "It took %2.3f second(s) for %s to generate this page" % (time.time()-self.starttime, socket.getfqdn())
        reload(footer)
        self.dict['footer'] = footer.footer_string % serverInfo

        slist = []
        for item in self.contents:
            slist.append(self.dict[item])
        return self.template % tuple(slist)


    def __del__(self):
        if self.cursor:
            self.cursor.close()

    def write(self):
        'return string representation of this object'

        if self.cursor:
            self.cursor.close()

        return str(self)

    def writeFile(self, filename):
        'save string representation of this object into a file'
        if self.cursor:
            self.cursor.close()

        try:
            'it could take a long time to generate the file, save to .tmp first'
            fp = open(os.path.join(webqtlConfig.TMPDIR, filename+'.tmp'), 'wb')
            fp.write(str(self))
            fp.close()
            path_tmp = os.path.join(webqtlConfig.TMPDIR, filename+'.tmp')
            path_html = os.path.join(webqtlConfig.TMPDIR, filename)
            shutil.move(path_tmp,path_html)
        except:
            pass

    def openMysql(self):
        try:
            self.con = MySQLdb.Connect(db=webqtlConfig.DB_NAME,host=webqtlConfig.MYSQL_SERVER, \
                                    user=webqtlConfig.DB_USER,passwd=webqtlConfig.DB_PASSWD)
            self.cursor = self.con.cursor()
            return 1
        except:
            heading = "Connect MySQL Server"
            detail = ["Can't connect to MySQL server on '"+ webqtlConfig.MYSQL_SERVER+"':100061. \
                            The server may be down at this time"]
            self.error(heading=heading,detail=detail,error="Error 2003")
            return 0

    def updMysql(self):
        try:
            self.con = MySQLdb.Connect(db=webqtlConfig.DB_UPDNAME,host=webqtlConfig.MYSQL_UPDSERVER, \
                                    user=webqtlConfig.DB_UPDUSER,passwd=webqtlConfig.DB_UPDPASSWD)
            self.cursor = self.con.cursor()
            return 1
        except:
            heading = "Connect MySQL Server"
            detail = ["update: Can't connect to MySQL server on '"+ webqtlConfig.MYSQL_UPDSERVER+"':100061. \
                            The server may be down at this time "]
            self.error(heading=heading,detail=detail,error="Error 2003")
            return 0

    def error(self,heading="",intro=[],detail=[],title="Error",error="Error"):
        'generating a WebQTL style error page'
        Heading = HT.Paragraph(heading)
        Heading.__setattr__("class","title")

        Intro = HT.Blockquote()
        if intro:
            for item in intro:
                Intro.append(item)
        else:
            Intro.append(HT.Strong('Sorry!'),' Error occurred while processing\
                    your request.', HT.P(),'The nature of the error generated is as\
                    follows:')

        Detail = HT.Blockquote()
        Detail.append(HT.Span("%s : " % error,Class="fwb cr"))
        if detail:
            Detail2 = HT.Blockquote()
            for item in detail:
                Detail2.append(item)
            Detail.append(HT.Italic(Detail2))

        #Detail.__setattr__("class","subtitle")
        TD_LR = HT.TD(height=200,width="100%",bgColor='#eeeeee',valign="top")
        TD_LR.append(Heading,Intro,Detail)
        self.dict['body'] = str(TD_LR)
        self.dict['title'] = title

    def session(self,mytitle="",myHeading=""):
        'generate a auto-refreshing temporary html file(waiting page)'
        self.filename = webqtlUtil.generate_session()
        self.dict['title'] = mytitle
        self.dict['basehref'] = webqtlConfig.REFRESHSTR % (webqtlConfig.CGIDIR, self.filename) + "" #webqtlConfig.BASEHREF

        TD_LR = HT.TD(align="center", valign="middle", height=200,width="100%", bgColor='#eeeeee')
        Heading = HT.Paragraph(myHeading, Class="fwb fs16 cr")
        # NL, 07/27/2010. variable 'PROGRESSBAR' has been moved from templatePage.py to webqtlUtil.py;
        TD_LR.append(Heading, HT.BR(), webqtlUtil.PROGRESSBAR)
        self.dict['body'] = TD_LR
        self.writeFile(self.filename + '.html')
        return self.filename
