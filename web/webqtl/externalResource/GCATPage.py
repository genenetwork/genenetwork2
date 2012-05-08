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

#GCATPage.py

from htmlgen import HTMLgen2 as HT

from base.webqtlTrait import webqtlTrait
from base.templatePage import templatePage
    

#Implemented by Xiaodong
class GCATPage(templatePage):

    def __init__(self,fd):

        self.theseTraits = []
        TD_LR = HT.TD(height=200,width="100%",bgColor='#eeeeee',valign="middle")

        templatePage.__init__(self, fd)

        if not self.openMysql():
            return

        self.searchResult = fd.formdata.getvalue('searchResult', [])
        if type("1") == type(self.searchResult):
            self.searchResult = [self.searchResult]

        for item in self.searchResult:
            try:
                thisTrait = webqtlTrait(fullname=item, cursor=self.cursor)
                thisTrait.retrieveInfo(QTL=1)
                if thisTrait.db.type == "ProbeSet":
                    self.theseTraits.append(thisTrait)
            except:
                pass

        if self.theseTraits:
            pass
        else:
            templatePage.__init__(self, fd)
            heading = 'GCAT'
            detail = ['You need to select at least one microarray trait to submit to GCAT.']
            self.error(heading=heading,detail=detail)
            return

        geneSymbolList = self.getGeneSymbolList()

        geneSymbolSet = set(geneSymbolList)

        if ( len(geneSymbolSet) < 500 ):
            temp = '+'.join(geneSymbolSet)
            GCATurl = "http://binf1.memphis.edu/gcat/?organism=mouse&subset=all&year=2010&geneInput=%s" % temp

            self.dict['js1'] = """
                <SCRIPT LANGUAGE="JavaScript">
                setTimeout( 'window.location = "%s"', 2000 );
                </SCRIPT>
            """ % GCATurl

            TD_LR.append(HT.Paragraph("Your selection of %d genes is being submitted to GCAT" % len(geneSymbolSet), Class="cr fs16 fwb", align="Center"))
        else:
            TD_LR.append(HT.Paragraph("Your selection of %d genes exceeds the limit of 500. Please reduce your gene number to below the limit." % len(geneSymbolSet), Class="cr fs16 fwb", align="Center"))


        self.dict['body'] = TD_LR


    def getGeneSymbolList(self):
        geneList = []

        for item in self.theseTraits:
            item.retrieveInfo()
            geneList.append(str(item.symbol))
		
        return geneList

                 
