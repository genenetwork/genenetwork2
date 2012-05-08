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

from base.templatePage import templatePage
from utility import webqtlUtil
from base import webqtlConfig
		

# XZ, 09/09/2008: From home, click "Enter Trait Data".
# XZ, 09/09/2008: If user check "Enable Use of Trait Variance",
# XZ, 09/09/2008: this class generate what you see
#########################################
#      VarianceChoicePage
#########################################

class VarianceChoicePage(templatePage):

	def __init__(self, fd):

		templatePage.__init__(self, fd)

		self.dict['title'] = 'Variance Submission' 
		
		if not fd.genotype:
			fd.readData(incf1=1)
		
		TD_LEFT = """
		<TD vAlign=top width="45%" bgColor=#eeeeee>
			<P class="title">Introduction</P>
			<BLOCKQUOTE>
				<P>The variance values that you enter are statistically compared\
				with verified genotypes collected at a set of microsatellite \
				markers in each RI set. The markers are drawn from a set of \
				over 750, but for each set redundant markers have been removed,\
				preferentially retaining those that are most informative. </P>

				<P>These error-checked RI mapping data match theoretical \
				expectations for RI strain sets. The cumulative adjusted length\
				of the RI maps are approximately 1400 cM, a value that matches\
				those of both MIT maps and Chromosome Committee Report maps. \
				See our <a Href="http://www.nervenet.org/papers/BXN.html" \
				class="normalsize">full description</a> of the genetic data \
				collected as part of the WebQTL project. </P>

			</BLOCKQUOTE>
			<P class="title">About Your Data</P>
			<BLOCKQUOTE>
				<P>You can open a separate <a target="_blank" Href=\
				"RIsample.html" class="normalsize">window</a> giving the number\
				of strains for each data set and sample data. </P>

				<P>None of your submitted data is copied or stored by this \
				system except during the actual processing of your submission. \
				By the time the reply page displays in your browser, your \
				submission has been cleared from this system. </P>
			</BLOCKQUOTE>
		</TD>
		"""
		TD_RIGHT = HT.TD(valign="top",width="55%",bgcolor="#eeeeee")
		main_title = HT.Paragraph(" Variance Submission Form")
		main_title.__setattr__("class","title")

		#############################
		title2 = HT.Paragraph("&nbsp;&nbsp;1. Enter variance Data:")
		title2.__setattr__("class","subtitle")

		STEP2 = HT.TableLite(cellSpacing=2,cellPadding=0,width="90%",border=0)
		Para1 = HT.Paragraph()
		Para1.append(HT.Strong("From a File: "))
		Para1.append('You can enter data by entering a file name here. The file\
		should contain a series of numbers representing variance values. The \
		values can be on one line separated by spaces or tabs, or they can be \
		on separate lines. Include one value for each progeny individual or \
		recombinant inbred line. Represent missing values with a non-numeric \
		character such as "x". If you have chosen a recombinant inbred set, \
		when you submit your data will be displayed in a form where you can \
		confirm and/or edit them. If you enter a file name here, any data \
		that you paste into the next section will be ignored.')
		
		filebox = HT.Paragraph(HT.Input(type='file', name='variancefile', size=20))

		OR = HT.Paragraph(HT.Center(HT.Font(HT.Strong('OR'),color="red")))
		
		Para2 = HT.Paragraph()
		Para2.append(HT.Strong("By Pasting or Typing Multiple Values:"))
		Para2.append('You can enter data by pasting a series of numbers \
		representing variance values into this area. The values can be on one \
		line separated by spaces or tabs, or they can be on separate lines. \
		Include one value for each progeny individual or recombinant inbred \
		line. Represent missing values with a non-numeric character such as \
		"x". If you have chosen a recombinant inbred set, when you submit \
		your data will be displayed in a form where you can confirm and/or \
		edit them. If you enter a file name in the previous section, any data\
		that you paste here will be ignored.')
		
		pastebox = HT.Paragraph(HT.Textarea(name='variancepaste', cols=45, rows=6))
		# NL, 07/27/2010. variable 'IMGSTEP1' has been moved from templatePage.py to webqtlUtil.py;		
		TD1 = HT.TD(webqtlUtil.IMGSTEP1,width=58)
		TD2 = HT.TD()
		TD2.append(Para1,filebox,OR,Para2,pastebox)
		STEP2.append(HT.TR(TD1,TD2),HT.TR(HT.TD(colspan=2,height=20)))
		#########################################
		
		hddn = {'FormID':'varianceChoice','submitID':'next','RISet':fd.RISet}
		if fd.identification:
			hddn['identification'] = fd.identification
		if fd.enablevariance:
			hddn['enablevariance']='ON'
		
		if fd.incparentsf1:
			hddn['incparentsf1']='ON'
		
		for item, value in fd.allTraitData.items():
			if value.val:
				hddn[item] = value.val
		
		form = HT.Form(cgi= os.path.join(webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE), \
		enctype='multipart/form-data', name='crossChoice', submit=HT.Input(type=\
		'hidden'))
		
		submit = HT.Input(type='button' ,name='next', value='Next',onClick=\
		'showNext(this.form);',Class="button") 			
		reset = HT.Input(type='reset' ,name='reset' ,value='Reset',Class="button")
		
		#########################################
		title3 = HT.Paragraph("&nbsp;&nbsp;2. Submit:")
		title3.__setattr__("class","subtitle")

		STEP3 = HT.TableLite(cellSpacing=2,cellPadding=0,width="90%",border=0)
		
		# NL, 07/27/2010. variable 'IMGSTEP2' has been moved from templatePage.py to webqtlUtil.py;		
		TD1 = HT.TD(webqtlUtil.IMGSTEP2,width=58)
		TD2 = HT.TD()
		TD2.append(HT.Blockquote("Click the next button to submit your variance\
		data for editing and mapping."),HT.Center(submit,reset))
		STEP3.append(HT.TR(TD1,TD2),HT.TR(HT.TD(colspan=2,height=20)))
		
		#########################################
		
		# NL, 07/27/2010. variable 'IMGNEXT' has been moved from templatePage.py to webqtlUtil.py;
		form.append(title2,HT.Center(STEP2,webqtlUtil.IMGNEXT),title3,HT.Center(STEP3))
			
		for key in hddn.keys():
			form.append(HT.Input(name=key, value=hddn[key], type='hidden'))
		
		TD_RIGHT.append(main_title,form)
		
		self.dict['body'] = TD_LEFT + str(TD_RIGHT)
