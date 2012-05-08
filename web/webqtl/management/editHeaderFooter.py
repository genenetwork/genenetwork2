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

from htmlgen import HTMLgen2 as HT
import os
import string
import urlparse

from base.templatePage import templatePage
from base import webqtlConfig

# 20100309 Lei Yan
class editHeaderFooter(templatePage):

        htmlPath = webqtlConfig.ChangableHtmlPath

        def __init__(self, fd):

                templatePage.__init__(self, fd)

                self.templateInclude = 1
                self.dict['title'] = "Editing HTML"

                if not self.updMysql():
                        return

                path = fd.formdata.getvalue('path')
                preview = fd.formdata.getvalue('preview')
                newHtmlCode = fd.formdata.getvalue('htmlSrc')
		hf = fd.formdata.getvalue('hf')

                if newHtmlCode:
                        newHtmlCode = string.replace(newHtmlCode,"&amp;", "&")
                if path and preview:
                        self.templateInclude = 0
			if hf=='h':
				tempH = newHtmlCode
				fp = open(self.htmlPath+'/footer.html', 'r')
				tempF = fp.read()
				fp.close()
			else:
				fp = open(self.htmlPath+'/header.html', 'r')
				tempH = fp.read()
				fp.close()
				tempF = newHtmlCode
			tempHtml = """
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN">
<HTML><HEAD><TITLE>Header Footer Test</TITLE>
<META http-equiv=Content-Type content="text/html; charset=iso-8859-1">
<LINK REL="stylesheet" TYPE="text/css" HREF='/css/general.css'>
<LINK REL="stylesheet" TYPE="text/css" HREF='/css/menu.css'>
<link rel="stylesheet" media="all" type="text/css" href="/css/tabbed_pages.css" />
<SCRIPT SRC="/javascript/webqtl.js"></SCRIPT>
<SCRIPT SRC="/javascript/tooltip.js"></SCRIPT>
<SCRIPT SRC="/javascript/dhtml.js"></SCRIPT>
<SCRIPT SRC="/javascript/beta2.js"></SCRIPT>
<script src="/javascript/tabbed_pages.js" type="text/javascript"></script>
</HEAD>
<BODY  bottommargin="2" leftmargin="2" rightmargin="2" topmargin="2" text=#000000 bgColor=#ffffff>
<TABLE cellSpacing=5 cellPadding=4 width="100%%" border=0>
        <TBODY>
        <TR>
		%s
        </TR>
        <TR>
                <TD  bgColor=#eeeeee class="solidBorder">
                <Table width= "100%%" cellSpacing=0 cellPadding=5>
                <TR>
                <!-- split from Here -->
                <!-- Body Start from Here -->
		<br><br><br><br><br><br><br><br><br><br><br><br>
		<center style="font-size:16px;font-family:verdana;color:red">Header Footer Test</center>
		<br><br><br><br><br><br><br><br><br><br><br><br>
                </TR></TABLE>
                </TD>
        </TR>
        <TR>
                <TD align=center bgColor=#ddddff class="solidBorder">
                <!--Start of footer-->
                <TABLE width="100%%">
			%s
                </TABLE>
                <!--End of footer-->
                </TD>
        </TR>
</TABLE>
<!-- /Footer -->
<!-- menu script itself. you should not modify this file -->
<script language="JavaScript" src="/javascript/menu_new.js"></script>
<!-- items structure. menu hierarchy and links are stored there -->
<script language="JavaScript" src="/javascript/menu_items.js"></script>
<!-- files with geometry and styles structures -->
<script language="JavaScript" src="/javascript/menu_tpl.js"></script>
<script language="JavaScript">
        <!--//
        // Note where menu initialization block is located in HTML document.
        // Don't try to position menu locating menu initialization block in
        // some table cell or other HTML element. Always put it before </body>
        // each menu gets two parameters (see demo files)
        // 1. items structure
        // 2. geometry structure
        new menu (MENU_ITEMS, MENU_POS);
        // make sure files containing definitions for these variables are linked to the document
        // if you got some javascript error like "MENU_POS is not defined", then you've made syntax
        // error in menu_tpl.js file or that file isn't linked properly.
        // also take a look at stylesheets loaded in header in order to set styles
        //-->
</script>
</BODY>
</HTML>
""" %(tempH, tempF)
                        self.debug = tempHtml
                elif path:
                        #edit result
                        fileName = self.htmlPath + path
                        
			fp1 = open(fileName, 'w')
                       	fp1.write(newHtmlCode)
                        fp1.close()

			fp1 = open(fileName, 'r')
			lines = fp1.readlines()
			fp1.close
			
			if 'h'==hf:
				fp2 = open(self.htmlPath + '/javascript/header.js', 'w')
			else:
				fp2 = open(self.htmlPath + '/javascript/footer.js', 'w')
			fp2.write("ctext = ''\r\n")
			fp2.flush()
			for line in lines:
				fp2.write("ctext += '%s'\r\n" %(line.rstrip()))
				fp2.flush()
			fp2.write('document.write(ctext)')
			fp2.flush()
			fp2.close()

                        TD_LR = HT.TD(valign="top",colspan=2,bgcolor="#eeeeee", height=200)
                        mainTitle = HT.Paragraph("Edit HTML", Class="title")
                        url = HT.Href(text = "page", url =path, Class = "normal")
                        intro = HT.Blockquote("This ",url, " has been succesfully modified. ")
                        TD_LR.append(mainTitle, intro)
                        self.dict['body'] = TD_LR
                elif fd.refURL:
                        #retrieve file to be edited
                        #refURL = os.environ['HTTP_REFERER']
                        addressing_scheme, network_location, path, parameters, query, fragment_identifier = urlparse.urlparse(fd.refURL)
			if 'h'==hf:
				path = "/header.html"
			else:
				path = "/footer.html"
                        fileName = self.htmlPath + path
                        fp = open(fileName,'r')
                        htmlCode = fp.read()
                        htmlCode = string.replace(htmlCode, "&","&amp;")
                        fp.close()
                        form = HT.Form(cgi= os.path.join(webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE), name='editHtml',submit=HT.Input(type='hidden'))
                        inputBox = HT.Textarea(name='htmlSrc', cols="100", rows=30,text=htmlCode)
                        hddn = {'FormID':'editHeaderFooter', 'path':path, 'preview':'', 'hf':hf}
                        for key in hddn.keys():
                                form.append(HT.Input(name=key, value=hddn[key], type='hidden'))
                        previewButton = HT.Input(type='button',name='previewhtml', value='Preview',Class="button", onClick= "editHTML(this.form, 'preview');")
                        submitButton = HT.Input(type='button',name='submitchange', value='Submit Change',Class="button", onClick= "editHTML(this.form, 'submit');")
                        resetButton = HT.Input(type='reset',Class="button")
                        form.append(HT.Center(inputBox, HT.P(), previewButton, submitButton, resetButton))
                        TD_LR = HT.TD(valign="top",colspan=2,bgcolor="#eeeeee")
                        mainTitle = HT.Paragraph("Edit HTML", Class="title")
                        intro = HT.Blockquote("You may edit the HTML source code in the editbox below, or you can copy the content of the editbox to your favorite HTML editor. ")
                        imgUpload = HT.Href(url="javascript:openNewWin('/upload.html', 'menubar=0,toolbar=0,location=0,resizable=0,status=1,scrollbars=1,height=400, width=600');", text="here", Class="normalsize")
                        intro2 = HT.Blockquote("Click ", imgUpload, " to upload Images. ")
                        TD_LR.append(mainTitle, intro, intro2, HT.Center(form))
                        self.dict['body'] = TD_LR
                else:
                        heading = "Editing HTML"
                        detail = ["Error occured while trying to edit the html file."]
                        self.error(heading=heading,detail=detail,error="Error")
                        return
