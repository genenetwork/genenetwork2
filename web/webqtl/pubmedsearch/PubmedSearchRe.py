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

#geneWikiPage.py
#
#This one's pretty self-evident from the title. If you use the GeneWiki module, this is what's behind it. -KA

# Xiaodong changed the dependancy structure

from htmlgen import HTMLgen2 as HT
import os
import string

from base.templatePage import templatePage
from base import webqtlConfig
from utility import webqtlUtil

#########################################
#########################################

class PubmedSearchRe(templatePage):

	def __init__(self, fd):
		templatePage.__init__(self, fd)
		self.content_type = 'text/html'
		Heading = HT.Paragraph("pubmed search", Class="title")
		Intro = HT.Blockquote("This is a description.")	
		
		table = HT.TableLite(border=0, cellpadding=0, cellspacing=0)
		
		TD_LR = HT.TD(height=200,width="100%",bgColor='#eeeeee',valign="top")
		TD_LR.append(Heading, Intro, HT.Center(form))
		self.dict['body'] = str(TD_LR)
		self.dict['title'] = "Pubmed Search"