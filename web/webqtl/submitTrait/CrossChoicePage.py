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

import glob
from htmlgen import HTMLgen2 as HT
import os

from base.templatePage import templatePage
from utility import webqtlUtil
from base import webqtlConfig

# XZ, 08/28/2008: From home, click "Enter Trait Data".
# XZ, 08/28/2008: This class generate what you see	
#########################################
#      CrossChoicePage
#########################################

class CrossChoicePage(templatePage):

	def __init__(self, fd):

		templatePage.__init__(self, fd)

		self.dict['title'] = 'Trait Submission'

		if not self.openMysql():
			return
		
		authorized = 0
		if webqtlConfig.USERDICT[self.privilege] >= webqtlConfig.USERDICT['user']:
			authorized = 1
	
		TD_LEFT = """
		<TD vAlign=top width="45%" bgColor=#eeeeee>
			<P class="title">Introduction</P>
			<BLOCKQUOTE>
				<P>The trait values that you enter are statistically compared 
				with verified genotypes collected at a set of microsatellite 
				markers in each RI set. The markers are drawn from a set of 
				over 750, but for each set redundant markers have been removed,
				preferentially retaining those that are most informative. </P>

				<P>These error-checked RI mapping data match theoretical 
				expectations for RI strain sets. The cumulative adjusted length
				of the RI maps are approximately 1400 cM, a value that matches 
				those of both MIT maps and Chromosome Committee Report maps. 
				See our <a Href="http://www.nervenet.org/papers/BXN.html" 
				class="normalsize"> full description</a> of the genetic data 
				collected as part of the WebQTL project. </P>

			</BLOCKQUOTE>
			<P class="title">About Your Data</P>
			<BLOCKQUOTE>
				<P>You can open a separate <a Href="RIsample.html" target="_blank" 
				class="normalsize"> window </a> giving the number of strains 
				for each data set and sample data. </P>
				<P>None of your submitted data is copied or stored by this 
				system except during the actual processing of your submission. 
				By the time the reply page displays in your browser, your 
				submission has been cleared from this system. </P>
			</BLOCKQUOTE>
		</TD>
		"""
		TD_RIGHT = HT.TD(valign="top",width="55%",bgcolor="#eeeeee")
		main_title = HT.Paragraph(" Trait Submission Form")
		main_title.__setattr__("class","title")

		#############################

		title1 = HT.Paragraph("&nbsp;&nbsp;1. Choose cross or RI set:")
		title1.__setattr__("class","subtitle")

		STEP1 = HT.TableLite(cellSpacing=2,cellPadding=0,width="90%",border=0)
		crossMenu = HT.Select(name='RISet', onChange='xchange()')
		allRISets = map(lambda x: x[:-5], glob.glob1(webqtlConfig.GENODIR, '*.geno'))
		allRISets.sort()
		if authorized:
			self.cursor.execute("select Name from InbredSet")
		else:
			self.cursor.execute("select Name from InbredSet where public > %d" % webqtlConfig.PUBLICTHRESH)
		results = map(lambda X:X[0], self.cursor.fetchall())
		allRISets = filter(lambda X:X in results, allRISets)
			
		specMenuSub1 = HT.Optgroup(label = 'MOUSE')
		specMenuSub2 = HT.Optgroup(label = 'RAT')
		specMenuSub3 = HT.Optgroup(label = 'ARABIDOPSIS')
		specMenuSub4 = HT.Optgroup(label = 'BARLEY')
		for item in allRISets:
			if item == 'HXBBXH':
				specMenuSub2.append(('HXB/BXH', 'HXBBXH'))
			elif item in ('BayXSha', 'ColXCvi', 'ColXBur'):
				specMenuSub3.append((item, item))
			elif item in ('SXM'):
				specMenuSub4.append((item, item))
			elif item == 'AXBXA':
				specMenuSub1.append(('AXB/BXA', 'AXBXA'))
			else:
				specMenuSub1.append(tuple([item,item]))
		crossMenu.append(specMenuSub1)
		crossMenu.append(specMenuSub2)
		crossMenu.append(specMenuSub3)
		crossMenu.append(specMenuSub4)
		crossMenu.selected.append('BXD')
		crossMenuText = HT.Paragraph('Select the cross or recombinant inbred \
		    set from the menu below. If you wish, paste data or select a data \
		    file in the next sections')
 		infoButton = HT.Input(type="button",Class="button",value="Info",\
 		    onClick="crossinfo2();")
		# NL, 07/27/2010. variable 'IMGSTEP1' has been moved from templatePage.py to webqtlUtil.py;
		TD1 = HT.TD(webqtlUtil.IMGSTEP1,width=58)
		TD2 = HT.TD()
		TD2.append(crossMenuText,crossMenu, infoButton)
		STEP1.append(HT.TR(TD1,TD2),HT.TR(HT.TD(colspan=2,height=20)))
		
		#############################
		title2 = HT.Paragraph("&nbsp;&nbsp;2. Enter Trait Data:")
		title2.__setattr__("class","subtitle")

		STEP2 = HT.TableLite(cellSpacing=2,cellPadding=0,width="90%",border=0)
		Para1 = HT.Paragraph()
		Para1.append(HT.Strong("From a File: "))
		Para1.append('You can enter data by entering a file name here. The file\
		    should contain a series of numbers representing trait values. The \
		    values can be on one line separated by spaces or tabs, or they can \
		    be on separate lines. Include one value for each progeny individual\
		    or recombinant inbred line. Represent missing values with a \
		    non-numeric character such as "x". If you have chosen a recombinant\
		    inbred set, when you submit your data will be displayed in a form \
		    where you can confirm and/or edit them. If you enter a file name \
		    here, any data that you paste into the next section will be ignored.')
		
		filebox = HT.Paragraph(HT.Input(type='file', name='traitfile', size=20))

		OR = HT.Paragraph(HT.Center(HT.Font(HT.Strong('OR'),color="red")))
		
		Para2 = HT.Paragraph()
		Para2.append(HT.Strong("By Pasting or Typing Multiple Values:"))
		Para2.append('You can enter data by pasting a series of numbers \
		    representing trait values into this area. The values can be on one\
		    line separated by spaces or tabs, or they can be on separate lines.\
		    Include one value for each progeny individual or recombinant inbred\
		    line. Represent missing values with a non-numeric character such \
		    as "x". If you have chosen a recombinant inbred set, when you submit\
		    your data will be displayed in a form where you can confirm and/or\
		    edit them. If you enter a file name in the previous section, any \
		    data that you paste here will be ignored. Check ', 
		    HT.Href(url="/RIsample.html", text="sample data", target="_blank", Class="normalsize"), 
		    ' for the correct format.')
		
		pastebox = HT.Paragraph(HT.Textarea(name='traitpaste', cols=45, rows=6))
		# NL, 07/27/2010. variable 'IMGSTEP2' has been moved from templatePage.py to webqtlUtil.py;		
		TD1 = HT.TD(webqtlUtil.IMGSTEP2,width=58)
		TD2 = HT.TD()
		TD2.append(Para1,filebox,OR,Para2,pastebox)
		STEP2.append(HT.TR(TD1,TD2),HT.TR(HT.TD(colspan=2,height=20)))
		
		#############################
		title3 = HT.Paragraph("&nbsp;&nbsp;3. Options:")
		title3.__setattr__("class","subtitle")

		STEP3 = HT.TableLite(cellSpacing=2,cellPadding=0,width="90%",border=0)
		
		########
		opt1 = HT.Paragraph(HT.Strong('Enable Use of Trait Variance: '))
		opt1.append(HT.Input(type='checkbox', Class='checkbox', name=\
		    'enablevariance', value='ON', onClick='xchange()'))
		opt1.append(HT.BR(),'You may use your trait variance data in WebQTL,\
		    if you check this box, you will be asked to submit your trait \
		    variance data later')
		
		########
		opt2 = HT.Paragraph(HT.Strong('Enable Use of Parents/F1: '))
		opt2.append(HT.Input(type='checkbox', name='parentsf1', value='ON'))
		opt2.append(HT.BR(),'Check this box if you wish to use Parents and F1 \
		    data in WebQTL')
		
		########
		opt3 = HT.Paragraph(HT.Strong("Name Your Trait ",HT.Font("(optional) ",\
		    color="red")))
		opt3.append(HT.Input(name='identification', size=12, maxlength=30))
		# NL, 07/27/2010. variable 'IMGSTEP3' has been moved from templatePage.py to webqtlUtil.py;
		TD1 = HT.TD(webqtlUtil.IMGSTEP3,width=58)
		TD2 = HT.TD()
		TD2.append(opt1,opt3)
		STEP3.append(HT.TR(TD1,TD2),HT.TR(HT.TD(colspan=2,height=20)))
		
		#########################################
		hddn = {'FormID':'crossChoice','submitID':'next', 'incparentsf1':'yes'}
		
		form = HT.Form(cgi= os.path.join(webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE), \
		    enctype= 'multipart/form-data', name='crossChoice', submit=\
		    HT.Input(type='hidden'))
		
		submit = HT.Input(type='button' ,name='next', value='Next',onClick=\
		    'showNext(this.form);', Class="button") 			
		reset = HT.Input(type='reset' ,name='reset' ,value='Reset',Class="button")
		
		sample = HT.Input(type='button' ,name='sample' ,value='Sample Data', \
			onClick='showSample(this.form);',Class="button")
		# NL, 07/27/2010. variable 'IMGNEXT' has been moved from templatePage.py to webqtlUtil.py;		
		form.append(title1,HT.Center(STEP1,webqtlUtil.IMGNEXT),title2,HT.Center(STEP2,\
		    webqtlUtil.IMGNEXT),title3,HT.Center(STEP3,webqtlUtil.IMGNEXT,HT.P(),submit,reset,sample))
			
		for key in hddn.keys():
			form.append(HT.Input(name=key, value=hddn[key], type='hidden'))
		
		TD_RIGHT.append(main_title,form)
		self.dict['body'] = TD_LEFT + str(TD_RIGHT)
		

