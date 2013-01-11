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

template = """
<?XML VERSION="1.0" ENCODING="UTF-8">
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN">
<HTML>
<HEAD>
<TITLE>%s</TITLE>

<META http-equiv=Content-Type content="text/html; charset=iso-8859-1">
<META NAME="keywords" CONTENT="genetics, bioinformatics, genome, phenome, gene expression, complex trait analysis, gene mapping, SNP, quantitative trait locus QTL, expression eQTL, WebQTL, Traitnet, Traitnetwork, personalized medicine">
<META NAME="description" CONTENT ="GeneNetwork is a free scientific web resource used to study relationships between differences in genes, environmental factors, phenotypes, and disease risk." >
<META NAME="author" CONTENT ="GeneNetwork developers" >
<META NAME="geo.placename" CONTENT ="Memphis, TN" >
<META NAME="geo.region" CONTENT="US-TN">
%s
<LINK REL="stylesheet" TYPE="text/css" HREF='/css/general.css'>
<LINK REL="stylesheet" TYPE="text/css" HREF='/css/menu.css'>
<link rel="stylesheet" media="all" type="text/css" href="/css/tabbed_pages.css" />
<LINK REL="apple-touch-icon" href="/images/ipad_icon3.png" />
<link type="text/css" href='/css/custom-theme/jquery-ui-1.8.12.custom.css' rel='Stylesheet' />
<link type="text/css" href='/css/tab_style.css' rel='Stylesheet' />

<script type="text/javascript" src="/javascript/jquery-1.5.2.min.js"></script>
<SCRIPT SRC="/javascript/webqtl.js"></SCRIPT>
<SCRIPT SRC="/javascript/dhtml.js"></SCRIPT>
<SCRIPT SRC="/javascript/tablesorter.js"></SCRIPT>
<SCRIPT SRC="/javascript/jqueryFunction.js"></SCRIPT>
<script src="/javascript/tabbed_pages.js" type="text/javascript"></script>
<script src="/javascript/jquery-ui-1.8.12.custom.min.js" type="text/javascript"></script>
%s

<script type="text/javascript">
  var _gaq = _gaq || [];
  _gaq.push(['_setAccount', 'UA-3782271-1']);
  _gaq.push(['_trackPageview']);
  (function() {
    var ga = document.createElement('script'); ga.type = 'text/javascript'; ga.async = true;
    ga.src = ('https:' == document.location.protocol ? 'https://ssl' : 'http://www') + '.google-analytics.com/ga.js';
    var s = document.getElementsByTagName('script')[0]; s.parentNode.insertBefore(ga, s);
  })();
</script>
</HEAD>
<BODY  bottommargin="2" leftmargin="2" rightmargin="2" topmargin="2" text=#000000 bgColor=#ffffff %s>
%s
<TABLE cellSpacing=5 cellPadding=4 width="100%%" border=0>
        <TBODY>
        <!-- Start of header -->
        <TR>
                %s
        </TR>
        <!-- End of header -->

        <!-- Start of body -->
        <TR>
                <TD  bgColor=#eeeeee class="solidBorder">
                <Table width= "100%%" cellSpacing=0 cellPadding=5>
                <TR>
                %s
                </TR>
                </TABLE>
                </TD>
        </TR>
        <!-- End of body -->

        <!-- Start of footer -->
        <TR>
                <TD align=center bgColor=#ddddff class="solidBorder">
                        <TABLE width="90%%">%s</table>
                </td>
        </TR>
        <!-- End of footer -->
</TABLE>

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
"""
