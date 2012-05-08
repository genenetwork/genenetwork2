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
# Created by GeneNetwork Core Team 2011/12/7
#
# Last updated by GeneNetwork Core Team 2011/12/7


from base.templatePage import templatePage
from htmlgen import HTMLgen2 as HT

import string
import os


class TissueAbbreviationPage (templatePage):

    def __init__(self,fd):
		templatePage.__init__(self, fd)
		
		shortName=fd.formdata.getfirst("shortTissueName", ',')
		fullName=fd.formdata.getfirst("fullTissueName", ',')
		shortNameList=[]
		fullNameList=[]
		
		if shortName:
			shortNameList=shortName.split(',')
			
		if fullName:
			fullNameList=fullName.split(',')
			
		tissueAbbrDict={}
		for i, item in enumerate(shortNameList):
			tissueAbbrDict[item]=fullNameList[i]	
			
		if tissueAbbrDict:
		
			# Creates the table for the fullname and shortname of Tissue
			tissueAbbrTable = HT.TableLite(border=1, cellspacing=5, cellpadding=3, Class="collap")
			shortNameList = tissueAbbrDict.keys()
			shortNameList.sort()
			abbrHeaderStyle="fs14 fwb ffl"
			abbrStyle="fs14 fwn ffl"
			
			tissueAbbrTable.append(HT.TR(HT.TD('Abbr&nbsp;&nbsp;', Class=abbrHeaderStyle, NOWRAP = 1),HT.TD('Full Name&nbsp;&nbsp;', Class=abbrHeaderStyle, NOWRAP = 1)))
			for item in shortNameList:
				thisTR = HT.TR(HT.TD(item, Class=abbrStyle, NOWRAP = 1))
				thisTR.append(HT.TD(tissueAbbrDict[item], Class=abbrStyle, NOWRAP = 1))

				tissueAbbrTable.append(thisTR)
				
			self.dict['body'] = HT.TD(HT.Paragraph("Tissue Abbreviation", Class="title"), HT.Blockquote(tissueAbbrTable))
			self.dict['title'] = "Tissue Abbreviation" 
		else:
			heading = "Tissue abbreviation"
			detail = ["Cannot found Tissue Abbreviation. Please try again later."]
			self.error(heading=heading,detail=detail)
			return			
           

