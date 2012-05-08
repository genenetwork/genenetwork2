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

# FUTURE PLANS:
# 1. Make the search species independent. Right now, it is fairly hard-coded to work with mouse only. Although it would not be too much trouble to add another species, at the time of writing, we have no
# variant data for anything except mice, so spending time fixing the code with respect to species independence is unnecessary. However, if you expand on the code, you should keep this in mind.
# 2. There needs to be some way to display mutliple strains in the InDel browser.
# 3. We need CNV and Transposon data. This should mostly come from Xusheng, at least for B vs. D, and it should be included in the Variants browser, which may have to either be restructured, or
# maybe just have columns added to it (if we're lucky).

#Code for the Variant Browser module. It's somewhat commented.

from mod_python import Cookie
from htmlgen import HTMLgen2 as HT

import string
import os
import piddle as pid
import time
import pyXLWriter as xl
from types import ListType
import re
import cPickle

#import snpBrowserUtils
from base import webqtlConfig
from base.GeneralObject import GeneralObject
from utility import Plot
from base.templatePage import templatePage
#from GeneListAnnot import GeneListAnnot
from utility import webqtlUtil
from utility.THCell import THCell
from utility.TDCell import TDCell     		
####################################################################
## SNP Browser
## Prints information about every SNP that lies in a specified range
####################################################################

#get current file path
current_file_name = __file__
pathname = os.path.dirname( current_file_name )
abs_path = os.path.abspath(pathname)
class snpBrowserPage(templatePage):

	MAXSNPRETURN = 5000 # This can take an awful long time to load. If there are more than 5000 SNPs, then it loads the SNP density graph instead (which is much faster, but doesn't show the exact data).
	MAXMB = 50 # Clips the graph to (Start Mb through Start+50 Mb) if someone searches for a larger region than that
	_scriptfile = "main.py?FormID=SnpBrowserResultPage"
	
	def __init__(self, fd):

		templatePage.__init__(self,fd)
		if not self.openMysql():
			return

		self.remote_ip = fd.remote_ip
		self.formdata = fd.formdata # This is for passing the VARIANT TYPE to the table creation process
		self.snp_list = None
		submitStatus = self.formdata.getfirst("submitStatus", "")
		opt = GeneralObject()
		self.initializeDisplayParameters(fd,opt)
		info_line=""
		snpTable=""

		if submitStatus: # For SnpBrowser result page
			opt.xls = 1	
			try:
				# for sortable columns, need to build dict for genTableObj function
				tblobj = {}
				filename= webqtlUtil.genRandStr("snpBrowser_")
				snpMatches, tblobj = self.genSnpTable(opt)
				
				if snpMatches >0 and snpMatches <=self.MAXSNPRETURN:
					# creat object for result table for sort function
					objfile = open('%s.obj' % (webqtlConfig.TMPDIR+filename), 'wb')
					cPickle.dump(tblobj, objfile)
					objfile.close()	

					sortby = ("Index", "down")
					snpTable = HT.Div(webqtlUtil.genTableObj(tblobj=tblobj, file=filename, sortby=sortby, tableID = "sortable", addIndex = "1"), Id="sortable")		
				else:
					#updated by NL 07-11-2011: density map can not be cPickled
					snpTable=tblobj
					
				# This writes the info at top above the search criteria.
				strainText = " - among all available strains in the group"			
				info_line = HT.Paragraph("%d %s(s) on Chr %s: %0.6f - %0.6f (Mb, mm9" % (snpMatches, opt.variant,opt.chromosome, opt.startMb, opt.endMb), 
						 Class="fs14 fwb ffl black")
				if self.snp_list:
				   info_line.contents[0]+= ", SNP: %s)" % opt.geneName
				elif opt.geneName:
					info_line.contents[0]+= ", Gene: %s)" % opt.geneName
				else:
					info_line.contents[0]+= ")" 
			except:
				heading = "Variant Browser"
				detail = ["No gene or %s record was found that matches %s." % (opt.variant,opt.geneName)]
				self.error(heading=heading,detail=detail)
				return
		else:
			opt.use_custom = True
			opt.diffAlleles=True

		# SnpBrowser default display part 
		info_link = HT.Input(type="button", value="Info", Class="button", onClick="javascript:openNewWin('/snpbrowser.html');")
		if opt.xslFilename:
			xlsDownloadButton= HT.Input(type="button", name="submitStatus",value=" Download Table ",onClick= "location.href='/tmp/%s'" % opt.xslFilename, Class='button')		
			title = HT.Paragraph("Variant Browser ",  info_link, "&nbsp;&nbsp;",xlsDownloadButton,  Class="title")
		else:		
			title = HT.Paragraph("Variant Browser ",  info_link,  Class="title")
		newPaddingForm = self.genBrowserForm(opt)
		descriptionTable = HT.TableLite(border=0, cellpadding=0, cellspacing=0)
		
		descriptionTable.append(HT.TR(HT.TD(info_line, colspan=3)),
								HT.TR(HT.TD("", height="20", colspan=3)),
								HT.TR(HT.TD(newPaddingForm,Class="doubleBorder", valign="top", colspan=3)),
								HT.TR(HT.TD("", height="20", colspan=3)), 
								HT.TR(HT.TD(snpTable, colspan=3)))
		
		self.dict['body'] = HT.TD(title, HT.Blockquote(descriptionTable, HT.P()),valign="top",height="200", width="100%")
		self.dict['title'] = "Variant Browser"	
		pass
	
	################################################################
	#	Initializes all of the snpBrowserPage class parameters, 
	#	acquiring most values from the formdata (fd)
	################################################################
	def initializeDisplayParameters(self, fd,opt):
	
		# COLUMN 1: items in paddingTab1		
		opt.variant = self.formdata.getfirst("variant","SNP")		
		opt.geneName = string.strip(self.formdata.getfirst("geneName", ""))		
		opt.chromosome = self.formdata.getfirst("chr", "19") 
		startMb, endMb =self.initialMb()
		opt.startMb = startMb
		opt.endMb = endMb
		# COLUMN 2: items in paddingTab2
		opt.allStrainNamesPair = self.getStrainNamePair()
		opt.allStrainNameList=[v[0] for v in opt.allStrainNamesPair]	
		opt.customStrain = self.formdata.getfirst("customStrain",None)
		if opt.customStrain:
		   opt.use_custom = True
		else:
		   opt.use_custom = False
		
		chosenStrains = self.formdata.getfirst("chosenStrains")
		strainList=[]
		# chosen strain selectbox incudes all strains that will be displayed in the search results if the "Limit to" checkbox is checked.
		# by default, chosen strain selectbox includes 9 strains. 
		# All strains in chosen strain selectbox will be saved into cookie after clicking 'Search' button.
		# chosen strain selectbox is set as single choice.
		# The original chosenStrains parameter is string type (chosenStrains = self.formdata.getfirst("chosenStrains")), 
                # then we split it into list if it is not empty ( chosenStrains = list(string.split(chosenStrains,',')) )
		# Case 1, no item is in selected status in chosen strain selectbox. chosenStrains is None. No converting to list. 
		# Case 2, user might have added one strain into chosen strain selectbox or clicked one item in chosen strain selectbox. 
		# After converting to list type, the chosenStrains list has one item.
		# Case 3, other classes might have called snpBrowserPage, such as from ProbeInfoPage,the strains will be passed via 'chosenStrains' parameter.
		# After converting to list type, the chosenStrains list has two items. 

		# In case 1 and 2, we will get the chosen strains from cookie or by using default value of 'chosenStrains'.
		opt.chosenStrains = self.retrieveCustomStrains(fd)
			
		# in case 3, get strain names from 'chosenStrains' parameter		
		if chosenStrains:
			if (not (type(chosenStrains) is ListType)):
				chosenStrains = list(string.split(chosenStrains,','))			
			if len(chosenStrains)>1 : 	
				for item in chosenStrains:
					strainList.append((item,item))	
				opt.chosenStrains=strainList			

		opt.diffAlleles =self.formdata.getfirst("diffAlleles", None)
		if opt.diffAlleles:
			opt.diffAlleles = True
		else:
			opt.diffAlleles = False
			
		# COLUMN 3: items in paddingTab3		
		opt.domain = self.formdata.getfirst("domain")
		if opt.domain == None or len(opt.domain) == 0:
			opt.domain = [""]
		elif not type(opt.domain) is ListType:
			opt.domain = [opt.domain]
		opt.function = self.formdata.getfirst("exonfunction")
		if opt.function == None or len(opt.function) == 0:
			opt.function = [""]
		elif not type(opt.function) is ListType:
			opt.function = [opt.function]
		
		opt.chosenSource=self.getSource()
		opt.source = self.formdata.getfirst("source")	
		if opt.source == None or len(opt.source) == 0:
			opt.source = [""]
		elif not type(opt.source) is ListType:
			opt.source = [opt.source]

		opt.conservationCriteria = self.formdata.getfirst("criteria",">=")
		opt.score = self.formdata.getfirst("score","0.0")
		opt.redundant = self.formdata.getfirst("redundant", None)
		if opt.redundant:
			opt.redundant_checked = True
		else:
			opt.redundant_checked = False

		# initial xsl file name
		opt.xslFilename=""
		opt.alleleValueList=[]
	
	# SnpBrowser page top part			
	def genBrowserForm(self, opt):	
		# COLUMN 1: items in paddingTab1
		variantSelect = HT.Select(name="variant", Class="typeDropdownWidth",data=[("SNP", "SNP"), ("InDel", "InDel")], selected=[opt.variant])
		geneBox = HT.Input(type="text", Class="typeDropdownWidth",name="geneName", value=opt.geneName, size="12")
		selectChrBox = HT.Select(name="chr",Class="typeDropdownWidth", data=[(1,'1'), (2,'2'), (3,'3'), (4,'4'), (5,'5'), (6,'6'), (7,'7'), (8,'8'), (9,'9'), (10,'10'), (11,'11'), (12,'12'), (13,'13'), (14,'14'), (15,'15'), (16,'16'), (17,'17'), (18,'18'), (19,'19'), ('X', 'X')], selected=[opt.chromosome], onChange = "Javascript:this.form.geneName.value=''")
		mbStartBox = HT.Input(type="text", Class="typeDropdownWidth",name="start", size="10", value=opt.startMb, onChange = "Javascript:this.form.geneName.value=''")
		mbEndBox = HT.Input(type="text", Class="typeDropdownWidth",name="end", value=opt.endMb, size="10", onChange = "Javascript:this.form.geneName.value=''")
		submitButton = HT.Input(type="submit", name="submitStatus",value="&nbsp;Search&nbsp;", Class="button")
		
		# COLUMN 2: items in paddingTab2
		div4 = HT.Div(Id='menu_s3')
		strainBox3 = HT.Select(name="s3", data=opt.allStrainNamesPair, Class="customBoxWidth")
		div4.append(strainBox3)
		addStrainButton = HT.Input(type="button", value="Add", Class="button", onClick="addToList(this.form.s3.options[this.form.s3.selectedIndex].text, this.form.s3.options[this.form.s3.selectedIndex].value, this.form.chosenStrains); this.form.chosenStrains.selectedIndex++")
		customStrainBox = HT.Input(type="checkbox", name="customStrain", checked=opt.use_custom, size="100")
		customStrainSelect = HT.Select(name="chosenStrains",data=opt.chosenStrains, multiple=False, Class="customBoxWidth", size=11)
		removeStrainButton = HT.Input(type="button", value=" Cut ", Class="button", onClick="removeFromList(this.form.chosenStrains.selectedIndex, this.form.chosenStrains)") 	
		diffAlleles = HT.Input(type="checkbox", name="diffAlleles", checked=opt.diffAlleles)
		

		# COLUMN 3: items in paddingTab3
		domainBox = HT.Select(name="domain", Class="domainDropdownWidth",data=[("All", ""),("Exon","Exon"),("&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;5' UTR","5' UTR"),
													("&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Coding Region","Coding"),("&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;3' UTR","3' UTR"),
													("Intron", "Intron"), ("&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Splice Site", "Splice Site"),("&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Nonsplice Site", "Nonsplice Site"), 
													("Upstream","Upstream"),("Downstream","Downstream"), ("Intergenic","Intergenic")], selected=opt.domain,
								 multiple=True,size=4,onChange = "Javascript:snpbrowser_function_refresh()")
		functionBox = HT.Select(name="exonfunction", data=[("All", ""),("Nonsynonymous","Nonsynonymous"),("Synonymous","Synonymous"),("Start Gained", "Start Gained"),("Start Lost", "Start Lost"),("Stop Gained", "Stop Gained"),("Stop Lost", "Stop Lost")],
									 selected=opt.function,multiple=True, size=3, Class="domainDropdownWidth",
											 onChange="Javascript:snpbrowser_domain_refresh()")
		filterBox = HT.Select(name="criteria", data=[(">=", ">="), ("=", "=="), ("<=","<=")], selected=[opt.conservationCriteria])
		sourceBox = HT.Select(name="source", data=opt.chosenSource, selected=opt.source,Class="domainDropdownWidth")
		scoreBox = HT.Input(type="text", name="score", value=opt.score, size="5")
		redundantBox = HT.Input(type="checkbox", name="redundant", checked=opt.redundant_checked)

		# This is where the actual table is structured, and it displays the variables initialized above
		paddingTable = HT.TableLite(border=0)
		paddingTab1 = HT.TableLite(border=0)
		paddingTab2 = HT.TableLite(border=0)
		paddingTab3 = HT.TableLite(border=0)

		# COLUMN 1
		paddingTab1.append(
				            HT.TR(HT.TD("Type :", Class="fwb", align="right", NOWRAP=1), HT.TD(variantSelect, NOWRAP=1)),
						    HT.TR(HT.TD("Gene or ID :", Class="fwb", align="right", NOWRAP=1),HT.TD(geneBox, NOWRAP=1)),					 
						    HT.TR(HT.TD("&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Or select", Class="fwb cr", colspan=3, align="LEFT")),
						    HT.TR(HT.TD("Chr :", Class="fwb", align="right", NOWRAP=1), HT.TD(selectChrBox, NOWRAP=1)),HT.TR(HT.TD("Mb :", Class="fwb", align="right", NOWRAP=1), HT.TD(mbStartBox)),
							HT.TR(HT.TD(HT.Font("&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;to", size=-1,),HT.TD(mbEndBox, NOWRAP=1))),
						    HT.TR(HT.TD(HT.HR(width="99%"), colspan=3, height=10)),
						    HT.TR(HT.TD(HT.TD(submitButton, NOWRAP=1)))
						    )
		# COLUMN 2
		paddingTab2.append(
							HT.TR(HT.TD("Strains:", Class="fwb", align="right", NOWRAP=1), HT.TD(width=10),HT.TD(div4),HT.TD(addStrainButton)),
							HT.TR(HT.TD("Limit to:", customStrainBox, Class="fwb  cr", align="right", NOWRAP=1),HT.TD(width=0),HT.TD(customStrainSelect),HT.TD(removeStrainButton))
							)
		# COLUMN 3
		paddingTab3.append(
							HT.TR(HT.TD("Domain:", Class="fwb", align="right", NOWRAP=1),
								HT.TD(width=10), HT.TD(domainBox, NOWRAP=1)),
							HT.TR(HT.TD("Function:", Class="fwb", align="right", NOWRAP=1),
								HT.TD(width=10), HT.TD(functionBox, NOWRAP=1)),	
							HT.TR(HT.TD("Source:", Class="fwb", align="right", NOWRAP=1),
								HT.TD(width=4), HT.TD(sourceBox, NOWRAP=1)),									
							HT.TR(HT.TD("ConScore:", Class="fwb", align="right", NOWRAP=1),
								HT.TD(width=4), HT.TD(filterBox, scoreBox, NOWRAP=1)),								
							HT.TR(HT.TD(redundantBox, align="right", NOWRAP=1), HT.TD(width=10), HT.TD("Non-redundant SNP Only", NOWRAP=1)),
							HT.TR(HT.TD(diffAlleles, align="right", NOWRAP=1),HT.TD(width=10), HT.TD("Different Alleles Only", NOWRAP=1))
							)

		paddingTable.append(
							HT.TR(HT.TD(paddingTab1), HT.TD("", width="0"), HT.TD(paddingTab2),HT.TD(width=0), HT.TD(paddingTab3), valign="top")
							)
		newPaddingForm = HT.Form(cgi=os.path.join(webqtlConfig.CGIDIR, self._scriptfile), enctype="multipart/form-data", name="newSNPPadding", submit=HT.Input(type="hidden"), onSubmit="Javascript:set_customStrains_cookie();")       
		newPaddingForm.append(paddingTable)
		
		return newPaddingForm
        
	# This grabs the data from MySQL for display in the table, allowing different sorting options based on the options chosen by the user.
	# The base option is what kind of variant the user is looking for; the other options are nested within that base option here.
	def genSnpTable(self, opt):
		# Grabs the Gene info, regardless of the variant type searched. This means you can display it for InDels, Snps, Etc.
		# initialize variables
		tblobj={}	# build dict for genTableObj function; keys include header and body	
		tblobj_header = [] # value of key 'header'
		tblobj_body=[]	# value of key 'body'
		snpHeaderRow=[]	# header row list for tblobj_header (html part)
		headerList=[] # includes all headers' name except for strain's value
		strainNameRow=[] # header row list for strain names
		strainList=[] # includes all strains' value
		strainNameList0=[]
		strainNameList=[]
		geneNameList=[] # for SNP's Gene column
		geneIdNameDict={}
		domain2=''
		
		headerStyle="fs13 fwb ffl b1 cw cbrb"# style of the header 
		cellColorStyle = "fs13 b1 fwn c222" # style of the cells 

		if opt.geneName:
			self.cursor.execute("SELECT geneSymbol, chromosome, txStart, txEnd from GeneList where SpeciesId= 1 and geneSymbol = %s", opt.geneName)
			result = self.cursor.fetchone()
			if result:
				opt.geneName, opt.chromosome, opt.startMb, opt.endMb = result		
			else:
				# If GeneName doesn't turn up results, then we'll start looking through SnpAll or Variants to check for other search types (e.g. Rs#, SnpName, or InDel Name)
				if opt.variant == "SNP":
					if opt.geneName[:2] == 'rs':
						self.cursor.execute("SELECT Id, Chromosome, Position, Position+0.000001 from SnpAll where Rs = %s", opt.geneName) 
					else: 
						self.cursor.execute("SELECT Id, Chromosome, Position, Position+0.000001 from SnpAll where SpeciesId= 1 and SnpName=%s",opt.geneName)
					result_snp = self.cursor.fetchall()
					if result_snp:
						self.snp_list = [v[0] for v in result_snp]
						opt.chromosome = result_snp[0][1];
						opt.startMb = result_snp[0][2]
						opt.endMb = result_snp[0][3]
					else:
						return

				# Searches through indels by the InDel name.		   
				elif opt.variant == "InDel":
					if opt.geneName[0] == 'I':
						self.cursor.execute("SELECT Id,  Chromosome, Mb_start, Mb_end FROM IndelAll WHERE SpeciesId=1 AND Name=%s", opt.geneName)
					result_snp = self.cursor.fetchall()
					if result_snp:
						self.snp_list = [v[0] for v in result_snp]
						opt.chromosome = result_snp[0][1];
						opt.startMb = result_snp[0][2]
						opt.endMb = result_snp[0][3]
					else:
						return

		if (opt.variant == "SNP"):
			#NL 05/13/2010: update query based on new db structure in SnpAll and SnpPattern
			query1 = """
					SELECT
						a.*,b.* 					
					from 
						SnpAll a, SnpPattern b
					where 
						a.SpeciesId = 1 and a.Chromosome = '%s' AND 
						a.Position >= %.6f and a.Position < %.6f AND 
						a.Id = b.SnpId 
						order by a.Position
				""" 		
			
		elif (opt.variant == "InDel"):
			query1 = """
				SELECT 
					distinct a.Name, a.Chromosome, a.SourceId, a.Mb_start, a.Mb_end, a.Strand, a.Type, a.Size, a.InDelSequence, b.Name 
				from 
					IndelAll a, SnpSource b
				where 
					a.SpeciesId = '1' and a.Chromosome = '%s' AND 
					a.Mb_start >= %2.6f and a.Mb_start < (%2.6f+.0010) AND
					b.Id = a.SourceId 
					order by a.Mb_start
			""" 		
		
		self.cursor.execute(query1 % (opt.chromosome, opt.startMb, opt.endMb))
		results_all = self.cursor.fetchall()

		# This executes the query if CHR, MB_START, MB_END are chosen as the search terms and Gene/SNP is not used
		results = self.filterResults(results_all, opt)
		# output xls file's name
		opt.xslFilename = "SNP_Chr%s_%2.6f-%2.6f" % (opt.chromosome, opt.startMb, opt.endMb)	
		
		nnn = len(results)		
		if nnn == 0:
			return nnn, ""
		elif nnn > self.MAXSNPRETURN: 
			gifmap=self.snpDensityMap(opt,query1,results_all)
			#07-28-2011 updated by NL: added info part for snp density map
			Info="Because the number of results exceeds the limit of 5000, the selected region could not be displayed. "
			Info2="Please select a smaller region by clicking the rectangle corresponding with its location in the map below."
			densityMap =HT.Span(Info,HT.BR(),Info2,HT.BR(),HT.BR(),gifmap, HT.Image('/image/'+opt.xslFilename+'.png', border=0, usemap='#SNPImageMap'),Class='fwb fs14') 
		
			return nnn, densityMap		
		else:
			pass


		##############
		# Excel file #
		##############
		# This code is for making the excel output file	
		if opt.xls:

			opt.xslFilename += ".xls"
			# Create a new Excel workbook
			workbook = xl.Writer(os.path.join(webqtlConfig.TMPDIR, opt.xslFilename))
			worksheet = workbook.add_worksheet()
			titleStyle = workbook.add_format(align = 'left', bold = 0, size=18, border = 1, border_color="gray")
			headingStyle = workbook.add_format(align = 'center', bold = 1, size=13, fg_color = 0x1E, color="white", border = 1, border_color="gray")
			headingStyle2 = workbook.add_format(align = 'center', bold = 1, size=13, fg_color = 0x1E, color="white", rotation = 2, border = 1, border_color="gray")
			XLSBASECOLORS0 = {"A": "red", "C": 0x18, 
					"T": 0x22, "G": "green",
					"-": 0x21, "":0x2F}
			XLSBASECOLORS = {}
			for key in XLSBASECOLORS0.keys():
				XLSBASECOLORS[key] = workbook.add_format(align = 'center', size=12, fg_color = XLSBASECOLORS0[key], border = 1, border_color="gray")
			
			##Write xls's title Info
			worksheet.write([0, 0], "GeneNetwork Variant Browser", titleStyle)
			worksheet.write([1, 0], "%s%s" % (webqtlConfig.PORTADDR, os.path.join(webqtlConfig.CGIDIR, self._scriptfile)))
			worksheet.write([2, 0], "Date : %s" % time.strftime("%B %d, %Y", time.gmtime()))
			worksheet.write([3, 0], "Time : %s GMT" % time.strftime("%H:%M ", time.gmtime()))
			worksheet.write([4, 0], "Search by : %s" % self.remote_ip)
			if opt.geneName:
				worksheet.write([5, 0], "Search term : %s" % opt.geneName)
			else:
				worksheet.write([5, 0], "view region : Chr %s %2.6f - %2.6f Mb" % (opt.chromosome, opt.startMb, opt.endMb))			
			nTitleRow = 7			
						
		#NL: new way to get header info for each variant
		# The next line determines which columns HEADERS show up in the table, depending on which Variant is selected to search the table for. This is for the column HEADERS ONLY; not the data displayed (that comes later).
		if (opt.variant == "SNP"):	
			headerList=['Index','SNP ID','Chr','Mb','Alleles','Source','ConScore','Gene','Transcript','Exon','Domain 1','Domain 2','Function','Details']
		elif (opt.variant == "InDel"):
			headerList=['Index','ID','Type','InDel Chr','Mb Start','Mb End','Strand','Size','Sequence','Source']		
			
		if headerList:
			for ncol, item in enumerate(headerList):
				if ncol==0:
					snpHeaderRow.append(THCell(HT.TD(item, Class=headerStyle, valign='bottom',nowrap='ON'),sort=0))
				elif item=="Details" or item=="Function" :
					snpHeaderRow.append(THCell(HT.TD(HT.Href(text = HT.Span(item, HT.Sup('  ?', style="color:#f00"),Class=headerStyle),
										target = '_blank',url = "/snpbrowser.html#%s"%item),
										Class=headerStyle, valign='bottom',nowrap='ON'), text=item, idx=ncol))							
				else:
					snpHeaderRow.append(THCell(HT.TD(item, Class=headerStyle, valign='bottom',nowrap='ON'),text=item, idx=ncol))
				#excel file for table headers' names
				worksheet.write([nTitleRow, ncol], item, headingStyle)

		# This writes the strain column names for the SNPs. The other variants only have data for C57BL6 and DBA2J, so they don't need this information.
		if (opt.variant == "SNP"):		
			if opt.customStrain:
				strainNameList = [v for v in opt.chosenStrains] 
				strainNameList = filter((lambda x: x[0]>=0),strainNameList)
			else:
				strainNameList=opt.allStrainNamesPair
				
			for j, item in enumerate(strainNameList):
				_contents = []
				for char in item[0]:
					_contents += [char, HT.BR()]

				if j % 5 == 0:
					strainNameRow.append(THCell(HT.TD(contents =_contents, Class="fs12 fwn ffl b1 cw cbrb", width=2, align="Center", valign="bottom", style="border-left:2px solid black"),sort=0))
				else:
					strainNameRow.append(THCell(HT.TD(contents =_contents, Class="fs12 fwn ffl b1 cw cbrb", width=2, align="Center", valign="bottom"),sort=0))
				
				#excel file
				ncol += 1
				worksheet.write([nTitleRow, ncol], item[0], headingStyle2)
				worksheet.set_column([ncol, ncol], 3)
			
			snpHeaderRow.extend(strainNameRow)	

		tblobj_header.append(snpHeaderRow)
		tblobj['header']=tblobj_header		
		
		#Changes text color of SNP label background. The colors here (e.g. cbgdull) are defined in ../css/general.css
		BASECOLORS = {"A": "cbrdull", "C": "cbbdull", "T": "cbydull", "G": "cbgdull", "-": "cbpdull", "":"cbccc","t": "cbg22t", "c": "cbg22c", "a": "cbg22a", "g": "cbg22g"}
		
		# # Code for determining if SNPs are identical (if the location of one SNP is the same as the SNP after it)
		try:
			self.cursor.execute(query1 % (opt.chromosome, 0, opt.startMb) + " desc limit 1") 
			firstMb = self.cursor.fetchone()
		except:
			firstMb =0
			
		if firstMb:
			lastMb = firstMb[5]
		else:
			lastMb = 0
		
		# get geneId Name pair for SNP result
		if opt.variant == "SNP":
			for item in results:
				if item[5]:
					geneName=item[5][1]
					# eliminate the duplicate geneName 
					if geneName and (geneName not in geneNameList): 
						geneNameList.append(geneName)
			if len(geneNameList)>0:
				geneIdNameDict=self.getGeneIdNameDict(geneNameList)

		# This pulls out the 'results' variable and splits it into the sequence of results.
		for seq, result in enumerate(results):		
			result = list(result)	

			if opt.variant == "SNP":
				SnpName, Rs, Chromosome, Mb, Alleles, gene, transcript, exon, domainList, function, functionDetails,SnpSource,ConScore,SnpId = result[:14]			
				strainNameList=result[14:]
				#if domain is intergenic, there's no gene, transcript,exon,function,functionDetails info				
				if Rs:
					SnpHref = HT.Href(text=Rs, url=webqtlConfig.DBSNP % (Rs), target="_blank")
					SnpName = Rs
				else:
					startBp=int(Mb*1000000 -100)
					endBp=int(Mb*1000000 +100)
					positionInfo="chr%s:%d-%d"%(Chromosome,startBp,endBp)
					SnpHref = HT.Href(text=SnpName,url=webqtlConfig.GENOMEBROWSER_URL % (positionInfo), Class="fs12 fwn",target="_blank")

				Mb=float(Mb)
				MbFormatted = "%2.6f" % Mb
				
				if SnpSource=='Sanger/UCLA':
					sourceURL1="http://www.sanger.ac.uk/resources/mouse/genomes/"
					sourceURL2="http://mouse.cs.ucla.edu/mousehapmap/beta/wellcome.html"
					SnpSourceLink=HT.Href(text="Sanger", url=sourceURL1, Class="fs12 fwn",target="_blank")
					SnpSourceLink1= HT.Href(text="UCLA", url=sourceURL2, Class="fs12 fwn",target="_blank")				
				else:
					SnpSourceLink=""
					
				if not ConScore:
					ConScore=''	

				if gene:
					geneName=gene[1]
					# if geneName has related geneId, then use geneId for NCBI search
					if geneIdNameDict.has_key(geneName) and geneIdNameDict[geneName]:					
						geneId=geneIdNameDict[gene[1]]
						ncbiUrl = HT.Href(text="NCBI",target='_blank',url=webqtlConfig.NCBI_LOCUSID % geneId, Class="fs10 fwn")				
					else:# if geneName can not find related geneId, then use geneName for NCBI search
						ncbiUrl = HT.Href(text="NCBI",target='_blank',url="http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?CMD=search&DB=gene&term=%s" % geneName, Class="fs10 fwn")
					
					#GN similar trait link
					_Species="mouse"
					similarTraitUrl = "%s?cmd=sch&gene=%s&alias=1&species=%s" % (os.path.join(webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE), geneName, _Species)	
					gnUrl = HT.Href(text="GN",target='_blank',url=similarTraitUrl, Class="fs10 fwn")								
				else:
					geneName=''
					ncbiUrl=''
					gnUrl=''
					
				if geneName:
					geneNameCol=HT.TD(HT.Italic(geneName), HT.BR(),gnUrl,"&nbsp;|&nbsp;", ncbiUrl, Class=cellColorStyle,nowrap='ON')
				else:
					geneNameCol=HT.TD(Class=cellColorStyle,nowrap='ON')
										
				if transcript:
					transcriptHref=HT.Href(text=transcript, url=webqtlConfig.ENSEMBLETRANSCRIPT_URL % (transcript), Class="fs12 fwn",target="_blank")
				else:
					transcriptHref=transcript

				if exon:
					exon=exon[1]#exon[0] is exonId;exon[1] is exonRank
				else:
					exon=''
				
				if domainList:
					domain=domainList[0]
					domain2=domainList[1]
					if domain=='Exon':
						domain=domain+" "+exon				

				
				funcList=[]
				if functionDetails:
					funcList=string.split(string.strip(functionDetails),',')
					funcList=map(string.strip,funcList)
					funcList[0]=funcList[0].title()
					functionDetails=', '.join(item for item in funcList)
					functionDetails=functionDetails.replace("_", " ");
					functionDetails=functionDetails.replace("/", " -> ");
					if functionDetails=="Biotype: Protein Coding":
						functionDetails =functionDetails+", Coding Region Unknown"

				# build SnpRow for SNP basic information\
				SnpRow=[]
				# first column of table
				SnpRow.append(TDCell(HT.TD(HT.Input(type="checkbox", Class="checkbox", name="index",value=seq+1, onClick="highlight(this)"), align='right',Class=cellColorStyle,nowrap='ON'),text=seq+1))	
				SnpRow.append(TDCell(HT.TD(SnpHref, Class=cellColorStyle,nowrap='ON'),SnpName, SnpName))
				SnpRow.append(TDCell(HT.TD(Chromosome, Class=cellColorStyle, align="center",nowrap='ON'),Chromosome, Chromosome))
				SnpRow.append(TDCell(HT.TD(MbFormatted, Class=cellColorStyle, align="center",nowrap='ON'),MbFormatted, MbFormatted))
				SnpRow.append(TDCell(HT.TD(Alleles, Class=cellColorStyle, align="center",nowrap='ON'),Alleles, Alleles))
				if SnpSource=='Sanger/UCLA':
					SnpRow.append(TDCell(HT.TD(SnpSourceLink,'/',SnpSourceLink1, Class=cellColorStyle,nowrap='ON'),SnpSource, SnpSource))
				else:
					SnpRow.append(TDCell(HT.TD(SnpSource, Class=cellColorStyle,nowrap='ON'),SnpSource, SnpSource))

					
				SnpRow.append(TDCell(HT.TD(ConScore, Class=cellColorStyle,align="center",nowrap='ON'),ConScore, ConScore))
				SnpRow.append(TDCell(geneNameCol,geneName, geneName))
				SnpRow.append(TDCell(HT.TD(transcriptHref, Class=cellColorStyle,nowrap='ON'),transcript, transcript))
				SnpRow.append(TDCell(HT.TD(exon, Class=cellColorStyle,align="center",nowrap='ON'),exon, exon))
				SnpRow.append(TDCell(HT.TD(domain, Class=cellColorStyle, align="center",nowrap='ON'),domain, domain))
				SnpRow.append(TDCell(HT.TD(domain2, Class=cellColorStyle, align="center",nowrap='ON'),domain2, domain2))
				SnpRow.append(TDCell(HT.TD(function, Class=cellColorStyle,nowrap='ON'),function, function))
				SnpRow.append(TDCell(HT.TD(functionDetails, Class=cellColorStyle,nowrap='ON'),functionDetails, functionDetails))				

				# excel file		
				worksheet.write([nTitleRow+seq+1, 0], seq+1)
				worksheet.write([nTitleRow+seq+1, 1], SnpName)
				worksheet.write([nTitleRow+seq+1, 2], Chromosome)
				worksheet.write([nTitleRow+seq+1, 3], MbFormatted)
				worksheet.write([nTitleRow+seq+1, 4], Alleles)
				worksheet.write([nTitleRow+seq+1, 5], SnpSource)
				worksheet.write([nTitleRow+seq+1, 6], ConScore)
				worksheet.write([nTitleRow+seq+1, 7], geneName)
				worksheet.write([nTitleRow+seq+1, 8], transcript)
				worksheet.write([nTitleRow+seq+1, 9], exon)
				worksheet.write([nTitleRow+seq+1, 10], domain)
				worksheet.write([nTitleRow+seq+1, 11], domain2)
				worksheet.write([nTitleRow+seq+1, 12], function)
				worksheet.write([nTitleRow+seq+1, 13], functionDetails)
				#ncol here should be the last ncol + 1
				ncol = 14
			
				# This puts the Allele data into the table if SNP is selected
				BASE=""
				bcolor = 'fs13 b1 cbw c222'	
				for j , item in enumerate(strainNameList):
					if item:
						BASE =item
						bcolor = BASECOLORS[BASE] + " b1"
					else:
						BASE = ""
						bcolor = 'fs13 b1 cbeee c222' #This changes text color of SNPs
						
					if j % 5 == 0:
						SnpRow.append(TDCell(HT.TD(BASE, Class=bcolor, align="center", style="border-left:2px solid black"),BASE,BASE))
					else:
						SnpRow.append(TDCell(HT.TD(BASE, Class=bcolor, align="center"),BASE,BASE))

					# #excel for strains' value	
					if BASE in XLSBASECOLORS.keys():
						xbcolor = XLSBASECOLORS[BASE]
					else:
						xbcolor = XLSBASECOLORS[""]
					worksheet.write([nTitleRow+seq+1, ncol], BASE, xbcolor)
					ncol += 1
					
				tblobj_body.append(SnpRow)	
				lastMb = Mb 
				
			elif opt.variant == "InDel":
				indelName, indelChr, indelMb_s, indelMb_e, indelStrand, indelType, indelSize, indelSequence, sourceName = result

				# build SnpRow for Indel basic information\
				SnpRow=[]
				# first column of table
				SnpRow.append(TDCell(HT.TD(HT.Input(type="checkbox", Class="checkbox", name="index",value=seq+1, onClick="highlight(this)"), align='right',Class=cellColorStyle,nowrap='ON'),text=seq+1))	
				SnpRow.append(TDCell(HT.TD(indelName, Class=cellColorStyle,nowrap='ON'),indelName, indelName))# Name of the InDel (e.g. Indel_1350)
				SnpRow.append(TDCell(HT.TD(indelType, Class=cellColorStyle, align="center",nowrap='ON'),indelType, indelType))# E.g. Insertion or Deletion
				SnpRow.append(TDCell(HT.TD(indelChr, Class=cellColorStyle, align="center",nowrap='ON'),indelChr, indelChr))# Indel Chromosome (e.g. 1)
				SnpRow.append(TDCell(HT.TD(indelMb_s, Class=cellColorStyle, align="center",nowrap='ON'),indelMb_s, indelMb_s))
				SnpRow.append(TDCell(HT.TD(indelMb_e, Class=cellColorStyle, align="center",nowrap='ON'),indelMb_e, indelMb_e))
				SnpRow.append(TDCell(HT.TD(indelStrand, Class=cellColorStyle, align="center",nowrap='ON'),indelStrand, indelStrand))
				SnpRow.append(TDCell(HT.TD(indelSize, Class=cellColorStyle,align="center",nowrap='ON'),indelSize, indelSize))
				SnpRow.append(TDCell(HT.TD(indelSequence, Class=cellColorStyle,align="center",nowrap='ON'),indelSequence, indelSequence))
				SnpRow.append(TDCell(HT.TD(sourceName, Class=cellColorStyle,nowrap='ON'),sourceName, sourceName))				

				if opt.xls:
					worksheet.write([nTitleRow+seq+1,0], seq+1)
					worksheet.write([nTitleRow+seq+1,1], indelName)
					worksheet.write([nTitleRow+seq+1,2], indelType)
					worksheet.write([nTitleRow+seq+1,3], indelChr)
					worksheet.write([nTitleRow+seq+1,4], indelMb_s)
					worksheet.write([nTitleRow+seq+1,5], indelMb_e)
					worksheet.write([nTitleRow+seq+1,6], indelStrand)
					worksheet.write([nTitleRow+seq+1,7], indelSize)
					worksheet.write([nTitleRow+seq+1,8], indelSequence)
					worksheet.write([nTitleRow+seq+1,9], sourceName)
					
				tblobj_body.append(SnpRow)
			else:
				pass
		
		
		tblobj['body']=tblobj_body
		workbook.close() # close here is important, otherwise xls file will not be generated
		
		return len(results), tblobj

	# initialize the value of start Mb and end Mb
	def initialMb(self):
		try:
			startMb = abs(float(self.formdata.getfirst("start", "30.1")))
			endMb = abs(float(self.formdata.getfirst("end", "30.12")))
		except:
			startMb = endMb = 30.0
		
		if startMb > endMb:
			temp = endMb
			endMb = startMb
			startMb = temp
		if startMb == endMb:
			endMb = startMb + 2 # DO NOT MAKE THIS LESS THAN 2 MB. YOU WILL BREAK EVERYTHING BECAUSE NO DEFAULT VARIANT IS SELECTED
		
		if endMb - startMb > self.MAXMB:
			endMb = self.MAXMB + startMb
		
		return startMb,endMb
		
	# get customStrains from cookie
	def retrieveCustomStrains(self,fd):
		cookie = fd.cookies
			
		custom_strains = []
		if cookie.has_key('customstrains1') and cookie['customstrains1']:
			strain_cookie = cookie['customstrains1']
			alloptions = string.split(strain_cookie,',')
			for one in alloptions:
			  sname_value = string.split(one,':')
			  if len(sname_value) == 2:
				 custom_strains.append( (sname_value[0],sname_value[0]))
		else:
			custom_strains=[('C57BL/6J', 'C57BL/6J'),('DBA/2J','DBA/2J'),('A/J','A/J'),('129S1/SvImJ','129S1/SvImJ'),('NOD/ShiLtJ','NOD/ShiLtJ'),('NZO/HlLtJ','NZO/HlLtJ'),('WSB/EiJ','WSB/EiJ'),('PWK/PhJ','PWK/PhJ'),('CAST/EiJ','CAST/EiJ')]
		
		return custom_strains   

	# get geneId Name pair, key is geneName, value is geneId
	def getGeneIdNameDict(self, geneNameList):
		geneIdNameDict={}
		if len(geneNameList)==0:
			return ""
		geneNameStrList =["'"+geneName+"'" for geneName in geneNameList]
		geneNameStr=string.join(geneNameStrList,',')
		
		query = """
				   SELECT geneId, geneSymbol from GeneList 
					where SpeciesId=1 and geneSymbol in (%s)
				""" % geneNameStr
		self.cursor.execute(query)
		results = self.cursor.fetchall()
		
		if len(results)>0:
			for item in results:
				geneIdNameDict[item[1]]=item[0]
		else:
			pass
				
		return geneIdNameDict

	# This grabs the mySQL query results and filters them for use when SNP Variants are searched for.
	def filterResults(self, results, opt):
	
		filtered = []
		strainIdexList=[]		
		last_mb = -1

		if opt.customStrain and opt.chosenStrains:
			for item in opt.chosenStrains:
				index =opt.allStrainNameList.index(item[0])
				strainIdexList.append(index)	
		
		for seq, result in enumerate(results):
			result = list(result)
			
			if opt.variant == "SNP":
				displayStains=[]
				# The order of variables here is the order they are selected from in genSnpTable				
				SnpId,SpeciesId,SnpName, Rs, Chromosome, Mb, Alleles, SnpSource,ConservationScore = result[:9]

				effct =result[9:25]
				#result[25] is SnpId; 
				opt.alleleValueList =result[26:]

				if opt.customStrain and opt.chosenStrains:
					for index in strainIdexList:
						displayStains.append(result[26+index])
					opt.alleleValueList =displayStains
					
				effectInfoDict=self.getEffectInfo(effct)
				codingDomainList=['Start Gained','Start Lost','Stop Gained','Stop Lost','Nonsynonymous','Synonymous']
				intronDomainList=['Splice Site','Nonsplice Site']

								
				for key in effectInfoDict:
					if key in codingDomainList:
						domain=['Exon','Coding']
					elif key in ['3\' UTR','5\' UTR']:
						domain=['Exon',key]
					elif key in ['Unknown Effect In Exon']:
						domain=['Exon','']
					elif key in intronDomainList:
						domain=['Intron',key]
					else:
						domain =[key,'']

					if 'Intergenic' in domain:
						gene=''
						transcript=''
						exon=''
						function=''
						functionDetails=''
						
						if not opt.redundant  or last_mb != Mb:    # filter redundant or not	
							if self.filterIn(domain, function,SnpSource, ConservationScore,opt):
								generalInfoList =[SnpName, Rs, Chromosome, Mb, Alleles, gene,transcript,exon,domain,function,functionDetails,SnpSource,ConservationScore,SnpId]
								generalInfoList.extend(opt.alleleValueList)
								filtered.append(generalInfoList)
						last_mb = Mb
					else:
						geneList,transcriptList,exonList,functionList,functionDetailsList=effectInfoDict[key]							
						for index, item in enumerate(geneList):
							gene=item
							transcript=transcriptList[index]
							if exonList:
								exon=exonList[index]
							else:
								exon=""

							if functionList:
								function=functionList[index]
								if function=='Unknown Effect In Exon':
									function="Unknown"
							else:
								function=""
								
							if functionDetailsList:
								functionDetails='Biotype: '+functionDetailsList[index]
							else:
								functionDetails=""
								
							if not opt.redundant  or last_mb != Mb:    # filter redundant or not		
								if self.filterIn(domain, function,SnpSource, ConservationScore,opt):	
									generalInfoList =[SnpName, Rs, Chromosome, Mb, Alleles, gene,transcript,exon,domain,function,functionDetails,SnpSource,ConservationScore,SnpId]
									generalInfoList.extend(opt.alleleValueList)
									filtered.append(generalInfoList)							
							last_mb = Mb	
				

			elif opt.variant =="InDel":
				# The ORDER of variables here IS IMPORTANT.
				# THIS IS FOR ANYTHING YOU BRING OUT OF THE VARIANT TABLE USING InDel
				indelName, indelChr, sourceId, indelMb_s, indelMb_e, indelStrand, indelType, indelSize, indelSequence, sourceName = result

				indelType=indelType.title()	
				if not opt.redundant  or last_mb != indelMb_s:    # filter redundant or not
					gene = "No Gene"
					domain = ConservationScore = SnpId = SnpName = Rs = flank3 =flank5 = ncbi =function = ''
					if self.filterIn(domain, function,sourceName , ConservationScore, opt):
						filtered.append([indelName, indelChr, indelMb_s, indelMb_e, indelStrand, indelType, indelSize, indelSequence, sourceName])
				last_mb = indelMb_s
			else:
				filtered.append(result)
			
		return filtered
		
	# decide whether need to add this record or not
	def filterIn(self, domain, function, SnpSource,ConservationScore,opt):
		domainSatisfied = True
		functionSatisfied = True
		differentAllelesSatisfied = True
		sourceSatisfied= True

		if domain:
			if len(domain) == 0:
				if opt.domain[0] != "":       # unknown and not searching for "All"
					domainSatisfied = False #True
			else:
				domainSatisfied = False
				for onechoice in opt.domain:
					if domain[0].startswith(onechoice) or domain[1].startswith(onechoice):
						domainSatisfied = True
		else:
			if opt.domain[0] != "":    # when the info is unknown but the users is not searching for "All"
				domainSatisfied = False

		if SnpSource:
			if len(SnpSource) ==0:   # not available
				if len(opt.source[0]) > 0:     # and not searching for "All"
					sourceSatisfied = False #True
			else:
				sourceSatisfied = False
				for choice in opt.source:
					if SnpSource.startswith(choice):
						sourceSatisfied = True
		else:
			if len(opt.source[0]) > 0:  # when the source is unknown but the users is not searching for "All"
				sourceSatisfied = False				
				
		if function:
			if len(function) ==0:   # not available
				if len(opt.function[0]) > 0:     # and not searching for "All"
					functionSatisfied = False #True
			else:
				functionSatisfied = False
				for choice in opt.function:
					if function.startswith(choice):
						functionSatisfied = True
		else:
			if len(opt.function[0]) > 0:  # when the function is unknown but the users is not searching for "All"
				functionSatisfied = False

				
		if ConservationScore: 
			con_score = float(ConservationScore)
			if len(opt.score) > 0:
				opt_score_float = float(opt.score)	
			else: 
				opt_score_float = 0.0         
			if opt.conservationCriteria == '>=':
				if con_score >= opt_score_float: 
					scoreSatisfied = True
				else:
					scoreSatisfied = False
			elif opt.conservationCriteria == '==':
				if con_score == opt_score_float:
					scoreSatisfied = True
				else:
					scoreSatisfied = False
			elif opt.conservationCriteria == '<=':
				if con_score <= opt_score_float:
					scoreSatisfied = True
				else:
					scoreSatisfied = False
		else:
			if float(opt.score)>0:
				scoreSatisfied = False
			else:
				scoreSatisfied = True              # allow null value

		# when diffAlleles function has been chose;
		# decide whether need to show this record based on strains' allele value
		if opt.variant == "SNP" and opt.diffAlleles:
			totalCount =0
			aList=[]
			
			for x in opt.alleleValueList:
				if x and (x.lower() not in aList) and ( x != "-"):
					aList.append(x.lower())

			totalCount= len(aList)
			if totalCount <= 1:
				differentAllelesSatisfied= False
			else:
				differentAllelesSatisfied= True			
		else:
			differentAllelesSatisfied = True
		
		return domainSatisfied and functionSatisfied and sourceSatisfied and scoreSatisfied and differentAllelesSatisfied

	#snpDensityMap will display when the max return is greater than default value
	# pay attention to the order of drawing canvas, the latter one will overlap the former one
	def snpDensityMap(self,opt,query,results):

		snpCanvas = pid.PILCanvas(size=(900,200))
		xLeftOffset, xRightOffset, yTopOffset, yBottomOffset = (30, 30, 40, 50)
		cWidth = snpCanvas.size[0]
		cHeight = snpCanvas.size[1]
		plotWidth = cWidth - xLeftOffset - xRightOffset
		plotHeight = cHeight - yTopOffset - yBottomOffset
		yZero = yTopOffset + plotHeight/2
		
		plotXScale = plotWidth/(opt.endMb - opt.startMb)
		
		#draw clickable map
		#Image map
		gifmap = HT.Map(name='SNPImageMap')
		NCLICK = 80.0
		clickStep = plotWidth/NCLICK
		clickMbStep = (opt.endMb - opt.startMb)/NCLICK
		
		for i in range(NCLICK):
			#updated by NL 07-11-2011: change the parameters to make clickable function work properly.
			HREF = os.path.join(webqtlConfig.CGIDIR, "%s&submitStatus=1&diffAlleles=True&customStrain=True"%self._scriptfile) + \
			"&chr=%s&start=%2.6f&end=%2.6f" % (opt.chromosome, opt.startMb+i*clickMbStep, opt.startMb+(i+1)*clickMbStep)
			
			COORDS0 = (xLeftOffset+i*clickStep, yTopOffset-18, xLeftOffset+(i+1)*clickStep-2, yTopOffset+plotHeight)
			snpCanvas.drawRect(COORDS0[0],COORDS0[1],COORDS0[2],COORDS0[3], edgeColor=pid.white)
			COORDS0 = "%d,%d,%d,%d" % COORDS0
			Areas1 = HT.Area(shape='rect',coords=COORDS0,href=HREF)
			gifmap.areas.append(Areas1)
			
			COORDS = (xLeftOffset+i*clickStep, yTopOffset-18, xLeftOffset+(i+1)*clickStep-2, yTopOffset-10)
			snpCanvas.drawRect(COORDS[0],COORDS[1],COORDS[2],COORDS[3]+5, edgeColor=pid.wheat, fillColor=pid.wheat)
			COORDS = "%d,%d,%d,%d" % COORDS
			
			Areas = HT.Area(shape='rect',coords=COORDS)
			
			gifmap.areas.append(Areas)
			
		snpCanvas.drawString("Click to view the corresponding section of the SNP map", 
				xLeftOffset, yTopOffset-25, font=pid.Font(ttf="verdana", size=14, bold=0), color=pid.black)
		
					
		###draw SNPs
		snpCounts = []
		stepMb = 1.0/plotXScale
		startMb = opt.startMb

		for i in range(plotWidth):
			
			self.cursor.execute(query % (opt.chromosome, startMb, startMb + stepMb))
			snpCounts.append(len(self.cursor.fetchall()))
			startMb += stepMb
		
		maxCounts = max(snpCounts)
		sfactor = plotHeight/(2.0*maxCounts)
		for i in range(plotWidth):
			sheight = sfactor*snpCounts[i]
			snpCanvas.drawLine(i+xLeftOffset, yZero-sheight, i+xLeftOffset, yZero+sheight, color = pid.orange)	
			
		###draw X axis
		snpCanvas.drawLine(xLeftOffset, yZero, xLeftOffset+plotWidth, yZero, color=pid.black)
		
		XScale = Plot.detScale(opt.startMb, opt.endMb)
		XStart, XEnd, XStep = XScale
		if XStep < 8:
			XStep *= 2
		spacingAmtX = spacingAmt = (XEnd-XStart)/XStep
		j = 0
		while  abs(spacingAmtX -int(spacingAmtX)) >= spacingAmtX/100.0 and j < 6:
			j += 1
			spacingAmtX *= 10
		formatStr = '%%2.%df' % j
		
		MBLabelFont = pid.Font(ttf="verdana", size=12, bold=0)
		NUM_MINOR_TICKS = 5
		xMinorTickHeight = 4
		xMajorTickHeight = 5
		for counter, _Mb in enumerate(Plot.frange(XStart, XEnd, spacingAmt / NUM_MINOR_TICKS)):
			if _Mb < opt.startMb or _Mb > opt.endMb:
				continue
			Xc = xLeftOffset + plotXScale*(_Mb - opt.startMb)
			if counter % NUM_MINOR_TICKS == 0: # Draw a MAJOR mark, not just a minor tick mark
				snpCanvas.drawLine(Xc, yZero, Xc, yZero+xMajorTickHeight, width=2, color=pid.black) # Draw the MAJOR tick mark
				labelStr = str(formatStr % _Mb) # What Mbase location to put on the label
				strWidth = snpCanvas.stringWidth(labelStr, font=MBLabelFont)
				drawStringXc = (Xc - (strWidth / 2.0))
				snpCanvas.drawString(labelStr, drawStringXc, yZero +20, font=MBLabelFont, angle=0, color=pid.black)
			else:
				snpCanvas.drawLine(Xc, yZero, Xc, yZero+xMinorTickHeight, color=pid.black) # Draw the MINOR tick mark
			# end else
		
		xLabelFont = pid.Font(ttf="verdana", size=20, bold=0)
		xLabel = "SNP Density Map : Chr%s %2.6f-%2.6f Mb" % (opt.chromosome, opt.startMb, opt.endMb)
		snpCanvas.drawString(xLabel, xLeftOffset + (plotWidth -snpCanvas.stringWidth(xLabel, font=xLabelFont))/2,
			yTopOffset +plotHeight +30, font=xLabelFont, color=pid.black)
		
		snpCanvas.save(os.path.join(webqtlConfig.IMGDIR, opt.xslFilename), format='png')
		return gifmap
			
		
	#NL 05-13-2011: rewrite to get field_names in query	
	def getStrainNamePair(self):
		# add by NL ^-^ 05-13/2011
		# get field_names in query
		strainNamePair=[]
		query ='SELECT * FROM SnpPattern limit 1'
		self.cursor.execute(query)

		num_fields = len(self.cursor.description)
		field_names = [i[0] for i in self.cursor.description]
		strainsNameList=field_names[1:]
		
		# index for strain name starts from 1
		for index, name in enumerate(strainsNameList):
			strainNamePair.append((name,name))

		return strainNamePair			
	
	def getEffectDetailsByCategory(self, effectName=None, effectValue=None):
		geneList=[]
		transcriptList=[]
		exonList=[]
		funcList=[]
		funcDetailList=[]
		tmpList=[]		
			
		geneGroupList =['Upstream','Downstream','Splice Site','Nonsplice Site','3\' UTR']
		biotypeGroupList=['Unknown Effect In Exon','Start Gained','Start Lost','Stop Gained','Stop Lost','Nonsynonymous','Synonymous']
		newCodonGroupList=['Start Gained']
		codonEffectGroupList=['Start Lost','Stop Gained','Stop Lost','Nonsynonymous','Synonymous']
		
		# split data in effect by using '|'  into groups
		effectDetailList = string.split(string.strip(effectValue),'|')
		effectDetailList = map(string.strip, effectDetailList)
		
		# if there are more than one group of data, then traversing each group and retrieve each item in the group
		for index, item in enumerate(effectDetailList):
			itemList =string.split(string.strip(item),',')
			itemList = map(string.strip, itemList)
			
			geneId=itemList[0]
			geneName=itemList[1]
			geneList.append([geneId,geneName])
			transcriptList.append(itemList[2])			
									
			if effectName not in geneGroupList:
				exonId=itemList[3]
				exonRank=itemList[4]
				exonList.append([exonId,exonRank])
				
			if effectName in biotypeGroupList:
				biotype=itemList[5]
				funcList.append(effectName)
	
				if effectName in newCodonGroupList:
					newCodon=itemList[6]
					tmpList=[biotype,newCodon]					
					funcDetailList.append(string.join(tmpList, ", "))
					
				elif effectName in codonEffectGroupList:
					old_new_AA=itemList[6]
					old_new_Codon=itemList[7]
					codon_num=itemList[8]
					tmpList=[biotype,old_new_AA,old_new_Codon,codon_num]
					funcDetailList.append(string.join(tmpList, ", "))
				else:
					funcDetailList.append(biotype)

		return [geneList,transcriptList,exonList,funcList,funcDetailList]
			
	def getEffectInfo(self, effectList):
		Domain=''
		effectDetailList=[]
		effectInfoDict={}
		
		Prime3_UTR,Prime5_UTR,Upstream,Downstream,Intron,Nonsplice_Site,Splice_Site,Intergenic=effectList[:8]
		Exon,Non_Synonymous_Coding,Synonymous_Coding,Start_Gained,Start_Lost,Stop_Gained,Stop_Lost,Unknown_Effect_In_Exon=effectList[8:]

		if Intergenic:
			Domain='Intergenic'
			effectInfoDict[Domain]=''
		else:
			# if not Exon:
			# get geneList, transcriptList info.
			if Upstream:
				Domain='Upstream'
				effectDetailList=self.getEffectDetailsByCategory(effectName='Upstream', effectValue=Upstream)
				effectInfoDict[Domain]=effectDetailList
			if Downstream:
				Domain='Downstream'
				effectDetailList=self.getEffectDetailsByCategory(effectName='Downstream', effectValue=Downstream)
				effectInfoDict[Domain]=effectDetailList			
			if Intron:
				if Splice_Site:						
					Domain='Splice Site'
					effectDetailList=self.getEffectDetailsByCategory(effectName='Splice Site', effectValue=Splice_Site)
					effectInfoDict[Domain]=effectDetailList
				if Nonsplice_Site:
					Domain='Nonsplice Site'
					effectDetailList=self.getEffectDetailsByCategory(effectName='Nonsplice Site', effectValue=Nonsplice_Site)
					effectInfoDict[Domain]=effectDetailList					
			# get gene, transcriptList and exon info.
			if Prime3_UTR:
				Domain='3\' UTR'
				effectDetailList=self.getEffectDetailsByCategory(effectName='3\' UTR', effectValue=Prime3_UTR)
				effectInfoDict[Domain]=effectDetailList	
			if Prime5_UTR:
				Domain='5\' UTR'
				effectDetailList=self.getEffectDetailsByCategory(effectName='5\' UTR', effectValue=Prime5_UTR)
				effectInfoDict[Domain]=effectDetailList	
					
			if Start_Gained:
				Domain='5\' UTR'
				effectDetailList=self.getEffectDetailsByCategory(effectName='Start Gained', effectValue=Start_Gained)
				effectInfoDict[Domain]=effectDetailList	

			if Unknown_Effect_In_Exon:
				Domain='Unknown Effect In Exon'
				effectDetailList=self.getEffectDetailsByCategory(effectName='Unknown Effect In Exon', effectValue=Unknown_Effect_In_Exon)
				effectInfoDict[Domain]=effectDetailList				
			if Start_Lost:
				Domain='Start Lost'
				effectDetailList=self.getEffectDetailsByCategory(effectName='Start Lost', effectValue=Start_Lost)
				effectInfoDict[Domain]=effectDetailList	
			if Stop_Gained:
				Domain='Stop Gained'
				effectDetailList=self.getEffectDetailsByCategory(effectName='Stop Gained', effectValue=Stop_Gained)
				effectInfoDict[Domain]=effectDetailList			
			if Stop_Lost:
				Domain='Stop Lost'
				effectDetailList=self.getEffectDetailsByCategory(effectName='Stop Lost', effectValue=Stop_Lost)
				effectInfoDict[Domain]=effectDetailList	
				
			if Non_Synonymous_Coding:
				Domain='Nonsynonymous'
				effectDetailList=self.getEffectDetailsByCategory(effectName='Nonsynonymous', effectValue=Non_Synonymous_Coding)
				effectInfoDict[Domain]=effectDetailList		
			if Synonymous_Coding:
				Domain='Synonymous'
				effectDetailList=self.getEffectDetailsByCategory(effectName='Synonymous', effectValue=Synonymous_Coding)
				effectInfoDict[Domain]=effectDetailList		
	
		return effectInfoDict
	
	
	def getSortedStrainList(self, strainList):
		sortedStrainList=[]
		removeList=['C57BL/6J','DBA/2J']
		for item in removeList:
			strainList.remove(item)
		
		sortedStrainList=removeList+strainList
		return sortedStrainList
	
	# build header and footer parts for export excel file
	def createExcelFileWithTitleAndFooter(self, workbook=None, datasetName=None,returnNumber=None):

		worksheet = workbook.add_worksheet()
		titleStyle = workbook.add_format(align = 'left', bold = 0, size=14, border = 1, border_color="gray")

		##Write title Info
		worksheet.write([1, 0], "Citations: Please see %s/reference.html" % webqtlConfig.PORTADDR, titleStyle)
		worksheet.write([2, 0], "Dataset : %s" % datasetName, titleStyle)
		worksheet.write([3, 0], "Date : %s" % time.strftime("%B %d, %Y", time.gmtime()), titleStyle)
		worksheet.write([4, 0], "Time : %s GMT" % time.strftime("%H:%M ", time.gmtime()), titleStyle)
		worksheet.write([5, 0], "Status of data ownership: Possibly unpublished data; please see %s/statusandContact.html for details on sources, ownership, and usage of these data." % webqtlConfig.PORTADDR, titleStyle)
		#Write footer info
		worksheet.write([8 + returnNumber, 0], "Funding for The GeneNetwork: NIAAA (U01AA13499, U24AA13513), NIDA, NIMH, and NIAAA (P20-DA21131), NCI MMHCC (U01CA105417), and NCRR (U01NR 105417)", titleStyle)
		worksheet.write([9 + returnNumber, 0], "PLEASE RETAIN DATA SOURCE INFORMATION WHENEVER POSSIBLE", titleStyle)

		return worksheet
		
	def getSource(self):
		sourceQuery ="select distinct Source from SnpAll"
		self.cursor.execute(sourceQuery)
		result =self.cursor.fetchall()
		sourceList=[("All", "")]
		
		try: 
			for item in result:
				item=item[0]
				sourceList.append((item,item))
				
		except:
			sourceList=[]
		
		return sourceList
				
		
