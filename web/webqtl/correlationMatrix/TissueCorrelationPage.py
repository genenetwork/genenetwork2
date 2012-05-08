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
# user can search correlation value and P-Value by inputting one pair gene symbols or multiple gene symbols.

# Created by GeneNetwork Core Team 2010/07/07
# Last updated by NL, 2011/03/25

from htmlgen import HTMLgen2 as HT
import os
import sys
import time
import string
import pyXLWriter as xl
import cPickle

from base.templatePage import templatePage
from base import webqtlConfig
from base.webqtlTrait import webqtlTrait
from correlationMatrix.tissueCorrelationMatrix import tissueCorrelationMatrix
from utility import webqtlUtil
from utility.THCell import THCell
from utility.TDCell import TDCell


#########################################
#      Tissue Correlation Page
#########################################

class  TissueCorrelationPage(templatePage):

	def __init__(self, fd):

		templatePage.__init__(self, fd)
				
		if not self.openMysql():
			return	
		
		#read input fields
		self.action = fd.formdata.getvalue("action", "").strip()
		self.geneSymbols = fd.formdata.getvalue("geneSymbols","").strip()
		self.tissueProbeSetFeezeId = fd.formdata.getvalue("tissueProbeSetFeezeId", "").strip()
		self.recordReturnNum = fd.formdata.getvalue("recordReturnNum", "0").strip()
		self.calculateMethod = fd.formdata.getvalue("calculateMethod", "0").strip()
		
		TissueCorrMatrixObject = tissueCorrelationMatrix(tissueProbeSetFreezeId=self.tissueProbeSetFeezeId)
		
		if not self.geneSymbols:	
			# default page 
			
			Heading = HT.Paragraph("Tissue Correlation", Class="title")
			Intro = HT.Blockquote("This function computes correlations between transcript expression across different organs and tissues.")
			Intro.append(HT.BR(),"Select a data set from the pull-down menu and then compute correlations.")

			formName='searchTissueCorrelation'
			form = HT.Form(cgi= os.path.join(webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE), target='_blank',enctype='multipart/form-data', name= formName, submit=HT.Input(type='hidden'))
			form.append(HT.Input(type="hidden", name="FormID", value=""))
			form.append(HT.Input(type="hidden", name="action", value="disp"))
			
			# added by NL 10/12/2010, retreive dataSet info from TissueProbeSetFreeze to get all TissueProbeSetFreezeId, datasetName and FullName
			tissProbeSetFreezeIds,dataSetNames,dataSetfullNames = TissueCorrMatrixObject.getTissueDataSet()

			dataSetList=[]
			for i in range(len(tissProbeSetFreezeIds)):
				dataSetList.append((dataSetfullNames[i], tissProbeSetFreezeIds[i]))
			dataSetMenu = HT.Select(dataSetList,name="tissueProbeSetFeezeId")

			InfoFile =HT.Input(type="button", Class="button", value=" Info ", onClick="tissueDatasetInfo(this.form.tissueProbeSetFeezeId,%s);"%(dataSetNames))	
			form.append(HT.Strong("&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"),dataSetMenu,InfoFile,HT.BR());
			
			form.append(HT.BR(),HT.Strong("&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Please enter only one gene symbol/ENTREZ gene Id per line."),HT.BR(),HT.Strong("&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"),HT.Textarea(name="geneSymbols", rows=10, cols=50, text=""),HT.BR(),HT.BR())				
			# calculate method radio button
			calculateMethodMenu =HT.Input(type="radio", name="calculateMethod", value="0", checked="checked")
			calculateMethodMenu1 =HT.Input(type="radio", name="calculateMethod", value="1")
			# record Return method dropdown menu
			recordReturnMenu = HT.Select(name="recordReturnNum")
			recordReturnMenu.append(('Top 100','0'))
			recordReturnMenu.append(('Top 200','1'))
			recordReturnMenu.append(('Top 500','2'))
			recordReturnMenu.append(('Top 1000','3'))
			recordReturnMenu.append(('Top 2000','4'))
			recordReturnMenu.append(('All','5'))	
			
			# working for input symbol has only one; 
			form.append(HT.Strong("&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"),HT.Span("Return:", Class="ffl fwb fs12"),HT.Strong("&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"),recordReturnMenu,HT.BR());
			form.append(HT.BR(),HT.Strong("&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"),'Pearson',calculateMethodMenu,"&nbsp;"*3,'Spearman Rank',calculateMethodMenu1,HT.BR(),HT.BR());
			form.append(HT.Strong("&nbsp;&nbsp;&nbsp;"),HT.Input(type="button", value="&nbsp;Compute&nbsp;", Class="button",onClick="selectFormIdForTissueCorr('%s');"%formName))
			form.append(HT.Strong("&nbsp;&nbsp;&nbsp;&nbsp;"),HT.Input(type="button", Class="button", value="&nbsp;Make Default&nbsp;", onClick = "makeTissueCorrDefault(this.form);"))

			TD_LR = HT.TD(height=200,width="100%",bgcolor='#eeeeee',align="left")		
			TD_LR.append(Heading,Intro,form)
			self.content_type = 'text/html'
			self.dict['js1'] = '<SCRIPT SRC="/javascript/correlationMatrix.js"></SCRIPT><BR>'
			# get tissueProbesetFreezeId from cookie
			self.dict['js2'] = 'onload ="getTissueCorrDefault(\'searchTissueCorrelation\');"'
			self.dict['body'] = str(TD_LR)
			self.dict['title'] = "Tissue Correlation"
		elif self.action == 'disp':
			TissueCount =TissueCorrMatrixObject.getTissueCountofCurrentDataset()
	
			# add by NL for first Note part in the tissue correlation page. 2010-12-23
			note =""
			dataSetName=""
			datasetFullName=""
			dataSetName, datasetFullName= TissueCorrMatrixObject.getFullnameofCurrentDataset()

			noteURL = "../dbdoc/"+ dataSetName+".html"
			noteText = " was used to compute expression correlation across %s samples of tissues and organs.&nbsp["%TissueCount			
			# dataset download
			datasetURL = "../dbdoc/"+ dataSetName+".xls"
			datasetDownload =HT.Href(text="Download experiment data",url=datasetURL,Class='fs13',target="_blank")
			note = HT.Blockquote(HT.Href(text=datasetFullName,url=noteURL,Class='fs13',target="_blank"),noteText, datasetDownload,"]",HT.BR())
			
			geneSymbolLst = [] # gene Symbol list
			geneSymbolLst = TissueCorrMatrixObject.getGeneSymbolLst(self.geneSymbols)
			
			symbolCount = len(geneSymbolLst)			
			# The input symbol limit is 100.
			heading = "Tissue Correlation" 
			if symbolCount > 100:
				detail = ['The Gene symbols you have input are more than 100. Please limit them to 100.'] 
				self.error(heading=heading,detail=detail)
				return		
			elif symbolCount==0:
				detail = ['No Gene Symbol was input. No Tissue Correlation matrix generated.' ]
				self.error(heading=heading,detail=detail)
				return
			else:
				# search result page
				# The input symbols should be no less than 1.				
				self.content_type = 'text/html'				
				if symbolCount == 1:	
					self.displaySingleSymbolResultPage(primaryGeneSymbol=geneSymbolLst[0],datasetFullName=datasetFullName,tProbeSetFreezeId=self.tissueProbeSetFeezeId, TissueCorrMatrixObject =TissueCorrMatrixObject,recordReturnNum=self.recordReturnNum,method=self.calculateMethod, note=note,TissueCount =TissueCount)			
				else:	
					self.displayMultiSymbolsResultPage(geneSymbolLst=geneSymbolLst, symbolCount=symbolCount, tProbeSetFreezeId=self.tissueProbeSetFeezeId,TissueCorrMatrixObject =TissueCorrMatrixObject,note=note,TissueCount =TissueCount)

		else:
			heading = "Tissue Correlation"
			detail = ['There\'s something wrong with input gene symbol(s), or the value of parameter [action] is not right.' ]
			self.error(heading=heading,detail=detail)
			return
#############################
# functions
#############################

	# result page when input symbol has only one
	def displaySingleSymbolResultPage(self,primaryGeneSymbol=None, datasetFullName=None,tProbeSetFreezeId=None, TissueCorrMatrixObject =None,recordReturnNum=None,method=None,note=None,TissueCount =None):
		formName = webqtlUtil.genRandStr("fm_")
		form = HT.Form(cgi= os.path.join(webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE), enctype='multipart/form-data',name= formName, submit=HT.Input(type='hidden'))
		# the following hidden elements are required parameter in Class(PlotCorrelationPage). So we need to define them here. 
		form.append(HT.Input(type="hidden", name="action", value="disp"))
		form.append(HT.Input(type="hidden", name="FormID", value="dispSingleTissueCorrelation"))
		form.append(HT.Input(type="hidden", name="X_geneSymbol", value=""))
		form.append(HT.Input(type="hidden", name="Y_geneSymbol", value=""))
		form.append(HT.Input(type="hidden", name="ProbeSetID", value=""))
		# RISet is not using in Tissue correlation, but is a required parameter in Class(PlotCorrelationPage). So we set dummy value(BXD). 
		form.append(HT.Input(type="hidden", name="RISet", value="BXD"))
		form.append(HT.Input(type="hidden", name="ShowLine", value="1"))
		form.append(HT.Input(type="hidden", name="TissueProbeSetFreezeId", value=tProbeSetFreezeId))
		form.append(HT.Input(type="hidden", name="rankOrder", value=0))	
		
		traitList =[]
		try:
			symbolCorrDict, symbolPvalueDict = TissueCorrMatrixObject.calculateCorrOfAllTissueTrait(primaryTraitSymbol=primaryGeneSymbol,method=method)
		except:
			heading = "Tissue Correlation"
			detail = ['Please use the official NCBI gene symbol.' ]
			self.error(heading=heading,detail=detail)			
			return
		
		symbolList0,geneIdDict,dataIdDict,ChrDict,MbDict,descDict,pTargetDescDict=TissueCorrMatrixObject.getTissueProbeSetXRefInfo(GeneNameLst=[])					
		# In case, upper case and lower case issue of symbol, mappedByTargetList function will update input geneSymbolLst based on database search result
		tempPrimaryGeneSymbol =self.mappedByTargetList(primaryList=symbolList0,targetList=[primaryGeneSymbol])
		primaryGeneSymbol =tempPrimaryGeneSymbol[0]
		
		returnNum = self.getReturnNum(recordReturnNum)
		symbolListSorted=[]
		symbolList=[]
		# get key(list) of symbolCorrDict(dict) based on sorting symbolCorrDict(dict) by its' value in desc order
		symbolListSorted=sorted(symbolCorrDict, key=symbolCorrDict.get, reverse=True)
		symbolList = self.mappedByTargetList(primaryList=symbolList0,targetList=symbolListSorted)
		
		if returnNum==None:
			returnNum =len(symbolList0)
			IntroReturnNum ="All %d "%returnNum
		else:
			IntroReturnNum ="The Top %d" %returnNum
			
		symbolList = symbolList[:returnNum]

		pageTable = HT.TableLite(cellSpacing=0,cellPadding=0,width="100%", border=0, align="Left")
		
		##############
		# Excel file #
		##############
		filename= webqtlUtil.genRandStr("Corr_")								
		xlsUrl = HT.Input(type='button', value = 'Download Table', onClick= "location.href='/tmp/%s.xls'" % filename, Class='button')
		# Create a new Excel workbook
		workbook = xl.Writer('%s.xls' % (webqtlConfig.TMPDIR+filename))
		headingStyle = workbook.add_format(align = 'center', bold = 1, border = 1, size=13, fg_color = 0x1E, color="white")
		#There are 6 lines of header in this file. 
		worksheet = self.createExcelFileWithTitleAndFooter(workbook=workbook, datasetName=datasetFullName, returnNumber=returnNum)
		newrow = 6				
		pageTable.append(HT.TR(HT.TD(xlsUrl,height=40)))
		
		# get header part of result table and export excel file
		tblobj = {}
		tblobj['header'], worksheet = self.getTableHeader( method=method, worksheet=worksheet, newrow=newrow, headingStyle=headingStyle)
		newrow += 1

		# get body part of result table and export excel file
		tblobj['body'], worksheet = self.getTableBody(symbolCorrDict=symbolCorrDict, symbolPvalueDict=symbolPvalueDict,symbolList=symbolList,geneIdDict=geneIdDict,ChrDict=ChrDict,MbDict=MbDict,descDict=descDict,pTargetDescDict=pTargetDescDict,primarySymbol=primaryGeneSymbol,TissueCount=TissueCount, formName=formName, worksheet=worksheet, newrow=newrow,method=method)
		workbook.close()
		# creat object for result table for sort function
		objfile = open('%s.obj' % (webqtlConfig.TMPDIR+filename), 'wb')
		cPickle.dump(tblobj, objfile)
		objfile.close()	

		sortby = ("tissuecorr", "down")
		div = HT.Div(webqtlUtil.genTableObj(tblobj=tblobj, file=filename, sortby=sortby, tableID = "sortable", addIndex = "1"), Id="sortable")								
		
		if method =="0":
			IntroMethod="Pearson\'s r "
		else:
			IntroMethod="Spearman\'s rho "				
		Intro = HT.Blockquote('%s correlations ranked by the %s are displayed.' % (IntroReturnNum,IntroMethod),
				' You can resort this list using the small arrowheads in the top row.')	
		Intro.append(HT.BR(),' Click the correlation values to generate scatter plots. Select the symbol to open NCBI Entrez.')
				
		pageTable.append(HT.TR(HT.TD(div)))
		form.append(HT.P(), HT.P(),pageTable)
		corrHeading = HT.Paragraph('Tissue Correlation Table', Class="title")
		TD_LR = HT.TD(height=200,width="100%",bgcolor='#eeeeee',align="left")
		TD_LR.append(corrHeading,note,Intro, form, HT.P())

		self.dict['body'] =  str(TD_LR)
		self.dict['js1'] = '<SCRIPT SRC="/javascript/correlationMatrix.js"></SCRIPT><BR>'
		self.dict['title'] = 'Tissue Correlation Result'						
	
		return

	# result page when input symbols are more than 1	
	def displayMultiSymbolsResultPage(self, geneSymbolLst=None, symbolCount=None, tProbeSetFreezeId=None,TissueCorrMatrixObject=None,note=None,TissueCount =None):
		
		formName = webqtlUtil.genRandStr("fm_")
		form = HT.Form(cgi= os.path.join(webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE), enctype='multipart/form-data',name= formName, submit=HT.Input(type='hidden'))
		# the following hidden elements are required parameter in Class(PlotCorrelationPage). So we need to define them here. 
		form.append(HT.Input(type="hidden", name="action", value="disp"))
		form.append(HT.Input(type="hidden", name="FormID", value="dispMultiTissueCorrelation"))
		form.append(HT.Input(type="hidden", name="X_geneSymbol", value=""))
		form.append(HT.Input(type="hidden", name="Y_geneSymbol", value=""))
		form.append(HT.Input(type="hidden", name="ProbeSetID", value=""))
		# RISet is not using in Tissue correlation, but is a required parameter in Class(PlotCorrelationPage). So we set dummy value(BXD). 
		form.append(HT.Input(type="hidden", name="RISet", value="BXD"))
		form.append(HT.Input(type="hidden", name="ShowLine", value="1"))
		form.append(HT.Input(type="hidden", name="TissueProbeSetFreezeId", value=tProbeSetFreezeId))
		form.append(HT.Input(type="hidden", name="rankOrder", value=0))			

		# updated by NL, 2011-01-06, build multi list for later use to descrease access to db again
		symbolList,geneIdDict,dataIdDict,ChrDict,MbDict,descDict,pTargetDescDict = TissueCorrMatrixObject.getTissueProbeSetXRefInfo(GeneNameLst=geneSymbolLst)
		# In case, upper case and lower case issue of symbol, mappedByTargetList function will update input geneSymbolLst based on database search result
		geneSymbolLst =self.mappedByTargetList(primaryList=symbolList,targetList=geneSymbolLst)
		
		# Added by NL, 2011-01-06, get all shortNames, verboseNames, verboseNames2, verboseNames3, exportArray 
		# for Short Label, Long Label, Export functions			
		geneIdLst,shortNames, verboseNames, verboseNames2, verboseNames3, exportArray = self.getAllLabelsInfo(geneSymbolList =geneSymbolLst, geneIdDict=geneIdDict,ChrDict=ChrDict, MbDict=MbDict, descDict=descDict, pTargetDescDict=pTargetDescDict)
	
		heading = "Tissue Correlation Matrix" 
		
		#get correlation value and p value based on Gene Symbols list, and return the values in corrArray and pvArray seperately 
		corrArray,pvArray = TissueCorrMatrixObject.getTissueCorrPvArray(geneNameLst=geneSymbolLst,dataIdDict=dataIdDict)

		# in the matrix table, top right corner displays Spearman Rank Correlation's Values and P-Values for each pair of geneSymbols; 
		#                      left bottom displays Pearson Correlation values and P-Vlues for each pair of geneSymbols.
		tissueCorrMatrixHeading = HT.Paragraph(heading,Class="title")
		tcmTable = HT.TableLite(Class="collap", border=0, cellspacing=1, cellpadding=5, width='100%')	
		row1 = HT.TR(HT.TD(Class="fs14 fwb ffl b1 cw cbrb"),HT.TD('Spearman Rank Correlation (rho)' , Class="fs14 fwb ffl b1 cw cbrb", colspan= symbolCount+2,align="center"))
		col1 = HT.TR(HT.TD("P e a r s o n &nbsp;&nbsp;&nbsp; r", rowspan= symbolCount+1,Class="fs14 fwb ffl b1 cw cbrb", width=10,align="center"),HT.TD("Gene Symbol",Class="fs13 fwb cb b1", width=300))
		for i in range(symbolCount):
			GeneSymbol=geneSymbolLst[i].strip()
			geneId = geneIdLst[i]

			if geneId!=0:
				_url="http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?db=gene&cmd=Retrieve&dopt=Graphics&list_uids=%s" % geneId
				curURL = HT.Href(text=GeneSymbol,url=_url,Class='fs13',target="_blank")
			else:
				curURL = GeneSymbol
			col1.append(HT.TD(curURL,Class="b1", align="center"))				

		tcmTable.append(row1,col1)
		# to decide to whether to show note for "*" or not
		flag = 0
		for i in range(symbolCount):
			GeneSymbol=geneSymbolLst[i].strip()  
			geneId = geneIdLst[i]
			
			newrow = HT.TR()
			newrow.append(HT.Input(name="Symbol", value=GeneSymbol, type='hidden'))

			if geneId!=0:
				_url="http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?db=gene&cmd=Retrieve&dopt=Graphics&list_uids=%s" %geneId
				geneIdURL = HT.Href(text="%s "%GeneSymbol,url=_url,Class="b1",target="_blank")
			else:
				# flag =1 will show note for "*"
				flag = 1
				geneIdURL =HT.Italic("%s"%GeneSymbol,HT.Font('*', color='red'))				
			newrow.append(HT.TD(geneIdURL,shortNames[i],verboseNames[i],verboseNames2[i],verboseNames3[i], Class="b1", align="left",NOWRAP="ON"))

			for j in range(symbolCount):
				GeneSymbol2=geneSymbolLst[j].strip() 
				corr = corrArray[i][j]
				pValue = pvArray[i][j]
				Color=''

				if j==i:
					newrow.append(HT.TD(HT.Font(HT.Italic("n"),HT.BR(),str(TissueCount),Class="fs11 fwn b1",align="center", color="000000"), bgColor='#cccccc', align="center", Class="b1", NOWRAP="ON"))
					exportArray[i+1][j+1] = '%d/%d' % (TissueCount,TissueCount)
				else:
					if corr:
						corr = float(corr)
						tCorr = "%2.3f" % corr
						pValue = float(pValue)
						tPV = "%2.3f" % pValue

						# updated by NL, based on Rob's requirement: delete p value, 2010-02-14	
						# set color for cells by correlationValue
						if corr > 0.7:
							fontcolor="red"
						elif corr > 0.5:
							fontcolor="#FF6600"
						elif corr < -0.7:
							fontcolor="blue"
						elif corr < -0.5:
							fontcolor="#009900"
						else:
							fontcolor ="#000000"
							
						# set label for cells
						# if rank is equal to 0, pearson correlation plot will be the first one; 
						# if rank is equal to 1, spearman ran correlation plot will be the first one.
						if j>i:				
							exportArray[i+1][j+1] =tCorr+"/"+tPV
							rank =1
						elif j<i:
							exportArray[i+1][j+1] =tCorr+"/"+tPV
							rank =0
						
						tCorrStr= tCorr
						tPVStr = tPV 
						tCorrPlotURL = "javascript:showTissueCorrPlot('%s','%s','%s',%d)" %(formName,GeneSymbol, GeneSymbol2,rank) 					
						corrURL= HT.Href(text=HT.Font(tCorrStr,HT.BR(),color=fontcolor, Class="fs11 fwn"), url = tCorrPlotURL)						
					else:
						corr = 'N/A'
						corrURL= HT.Font(corr)
						exportArray[i+1][j+1] ="---/---"
						
					newrow.append(HT.TD(corrURL,bgColor=Color,Class="b1",NOWRAP="ON",align="middle"))

			tcmTable.append(newrow)

										
		
		Intro = HT.Blockquote('Lower left cells list Pearson ',HT.EM('r'),' values; upper right cells list Spearman rho values. Each cell also contains the n samples of tissues and organs. Values higher than 0.7 are displayed in ',HT.Font('red', color='red'),'; those between 0.5 and 0.7 in  ',HT.Font('orange', color='#FF6600'),'; Values lower than -0.7 are in ',HT.Font('blue', color='blue'),'; between -0.5 and -0.7 in ',HT.Font('green', color='#009900'),'.', HT.BR(),HT.BR(), HT.Strong('Make scatter plots by clicking on cell values '),'(', HT.EM('r'),' or rho). ', Class="fs13 fwn")
        		
		shortButton = HT.Input(type='button' ,name='dispShort',value=' Short Labels ', onClick="displayTissueShortName();",Class="button")
		verboseButton = HT.Input(type='button' ,name='dispVerbose',value=' Long Labels ', onClick="displayTissueVerboseName();", Class="button")
		exportbutton = HT.Input(type='button',  name='export', value='Export', onClick="exportTissueText(allCorrelations);",Class="button")
		lableNote = HT.Blockquote(HT.Italic(HT.Font('*', color='red',Class="fs9 fwn"), ' Symbol(s) can not be found in database.'))		
		
		# flag =1 will show note for "*", which means there's unidentified symbol.
		if flag==1:
			form.append(HT.Blockquote(tcmTable,lableNote,HT.P(),shortButton,verboseButton,exportbutton))
		else:
			form.append(HT.Blockquote(tcmTable,HT.P(),shortButton,verboseButton,exportbutton))
			
		exportScript = """
			<SCRIPT language=JavaScript>
			var allCorrelations = %s;
			</SCRIPT>
		"""
		exportScript = exportScript % str(exportArray)
		self.dict['js1'] = exportScript+'<SCRIPT SRC="/javascript/correlationMatrix.js"></SCRIPT><BR>'
		
		TD_LR = HT.TD(colspan=2,width="100%",bgcolor="#eeeeee")
		TD_LR.append(tissueCorrMatrixHeading,note,Intro,form,HT.P())
		self.dict['body'] = str(TD_LR)
		self.dict['title'] = 'Tissue Correlation Result'
		return

	# Added by NL, 2011-01-06, get all shortNames, verboseNames, verboseNames2, verboseNames3, exportArray 
	# for Short Label, Long Label, Export functions	
	def getAllLabelsInfo(self, geneSymbolList=None,geneIdDict=None,ChrDict=None,MbDict=None,descDict=None,pTargetDescDict=None):
	
		symbolCount= len(geneSymbolList)
		geneIdLst =[]
		exportArray = [([0] * (symbolCount+1))[:] for i in range(symbolCount+1)]
		exportArray[0][0] = 'Tissue Correlation'
		shortNames = []
		verboseNames = []
		verboseNames2 = []
		verboseNames3 = []	
		
		# added by NL, 2010-12-21, build DIV and array for short label, long label and export functions
		for i, geneSymbolItem in enumerate(geneSymbolList):
			geneSymbol =geneSymbolItem.lower()
			_shortName =HT.Italic("%s" %geneSymbolItem)
			_verboseName =''
			_verboseName2 = ''
			_verboseName3 = ''
			if geneIdDict.has_key(geneSymbol):
				geneIdLst.append(geneIdDict[geneSymbol])
			else:
				geneIdLst.append(0)
			if ChrDict.has_key(geneSymbol) and MbDict.has_key(geneSymbol):
				_verboseName = ' on Chr %s @ %s Mb' % (ChrDict[geneSymbol],MbDict[geneSymbol])
			if descDict.has_key(geneSymbol):
				_verboseName2 = '%s' % (descDict[geneSymbol])
			if pTargetDescDict.has_key(geneSymbol):
				_verboseName3 = '%s' % (pTargetDescDict[geneSymbol])         

			shortName = HT.Div(id="shortName_" + str(i), style="display:none")
			shortName.append('Symbol: ')
			shortName.append(_shortName)
			shortNames.append(shortName)
			
			verboseName = HT.Div(id="verboseName_" + str(i), style="display:none")
			verboseName.append(_shortName)
			verboseName.append(_verboseName)
			verboseNames.append(verboseName)
			verboseName2 = HT.Div(id="verboseName2_" + str(i), style="display:none")
			verboseName2.append(_verboseName2)
			verboseNames2.append(verboseName2)
			verboseName3 = HT.Div(id="verboseName3_" + str(i), style="display:none")
			verboseName3.append(_verboseName3)
			verboseNames3.append(verboseName3)
			
			# exportTissueText in webqtl.js is using '/' as delimilator; add '/', otherwise the last letter in geneSymbol will missing
			exportArray[i+1][0] =geneSymbolItem+ '/' + geneSymbolItem + '/' +geneSymbolItem + ':' + str(_verboseName) + ' : ' + str(_verboseName2) + ' : ' + str(_verboseName3)
			exportArray[0][i+1] =geneSymbolItem+ '/'	

		return geneIdLst,shortNames, verboseNames, verboseNames2, verboseNames3, exportArray


########################################################################
# functions for display and download when input symbol has only one    #
########################################################################

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

	# build header of table when input symbol has only one
	def getTableHeader(self, method='0', worksheet=None, newrow=None, headingStyle=None):

		tblobj_header = []
		exportList=[]
		header=[]
		header = [THCell(HT.TD(' ', Class="fs13 fwb ffl b1 cw cbrb",nowrap='ON'), sort=0),
								  THCell(HT.TD('Symbol',HT.BR(),HT.BR(), Class="fs13 fwb ffl b1 cw cbrb"), text="symbol", idx=1),
								  THCell(HT.TD('Description',HT.BR(),HT.BR(), Class="fs13 fwb ffl b1 cw cbrb"), text="desc", idx=2),
								  THCell(HT.TD('Location',HT.BR(),'Chr and Mb ', Class="fs13 fwb ffl b1 cw cbrb"), text="location", idx=3),
								  THCell(HT.TD('N Cases',HT.BR(),HT.BR(), Class="fs13 fwb ffl b1 cw cbrb",nowrap='ON'), text="nstr", idx=4)]
		if method =="0":# Pearson Correlation		
			header.append(	THCell(HT.TD(HT.Href(
										text = HT.Span(' r ', HT.Sup('  ?', style="color:#f00"),HT.BR(),HT.BR(), Class="fs13 fwb ffl cw"),
										target = '_blank',
										url = "/correlationAnnotation.html#tissue_r"),
										Class="fs13 fwb ffl b1 cw cbrb", nowrap='ON'), text="tissuecorr", idx=5))
			header.append(	THCell(HT.TD(HT.Href(
										text = HT.Span(' p(r) ', HT.Sup('  ?', style="color:#f00"),HT.BR(),HT.BR(), Class="fs13 fwb ffl cw"),
										target = '_blank',
										url = "/correlationAnnotation.html#tissue_p_r"),
										Class="fs13 fwb ffl b1 cw cbrb", nowrap='ON'), text="tissuepvalue", idx=6))
							
			exportList =[ 'Gene ID',  'Symbol', 'Description', 'Location', 'N Cases', ' r ', ' p(r) ']
			
		else:# Spearman Correlation
			header.append(	THCell(HT.TD(HT.Href(
										text = HT.Span(' rho ', HT.Sup('  ?', style="color:#f00"),HT.BR(),HT.BR(), Class="fs13 fwb ffl cw"),
										target = '_blank',
										url = "/correlationAnnotation.html#tissue_rho"),
											   Class="fs13 fwb ffl b1 cw cbrb", nowrap='ON'), text="tissuecorr", idx=5))
			header.append(	THCell(HT.TD(HT.Href(
										text = HT.Span('p(rho)', HT.Sup('  ?', style="color:#f00"),HT.BR(), HT.BR(),Class="fs13 fwb ffl cw"),
										target = '_blank',
										url = "/correlationAnnotation.html#tissue_p_rho"),
										Class="fs13 fwb ffl b1 cw cbrb", nowrap='ON'), text="tissuepvalue", idx=6))
			exportList = ['Gene ID', 'Symbol', 'Description', 'Location', 'N Cases','rho', ' p(rho) ']											
		
		# build header of excel for download function
		for ncol, item in enumerate(exportList):
			worksheet.write([newrow, ncol], item, headingStyle)
			worksheet.set_column([ncol, ncol], 2*len(item))

		tblobj_header.append(header)

		return tblobj_header, worksheet

	# build body of table when input symbol has only one
	def getTableBody(self, symbolCorrDict={}, symbolPvalueDict={},symbolList=[],geneIdDict={},ChrDict={},MbDict={},descDict={},pTargetDescDict={},primarySymbol=None, TissueCount=None,formName=None, worksheet=None, newrow=None,method="0"):
		
		tblobj_body = []
		
		for symbolItem in symbolList:
			symbol =symbolItem.lower()
			if symbol:
				pass
			else:
				symbol ="N/A"
				
			if geneIdDict.has_key(symbol) and geneIdDict[symbol]:
				geneId = geneIdDict[symbol]
				ncbiUrl = HT.Href(text="NCBI",target='_blank',url=webqtlConfig.NCBI_LOCUSID % geneIdDict[symbol], Class="fs10 fwn")				
			else:
				geneId ="N/A"
				symbolItem =symbolItem.replace('"','') # some symbol is saved in ["symbol"]format
				ncbiUrl = HT.Href(text="NCBI",target='_blank',url="http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?CMD=search&DB=gene&term=%s" % symbol, Class="fs10 fwn")
			
			_Species="mouse"
			similarTraitUrl = "%s?cmd=sch&gene=%s&alias=1&species=%s" % (os.path.join(webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE), symbolItem, _Species)	
			gnUrl = HT.Href(text="GN",target='_blank',url=similarTraitUrl, Class="fs10 fwn")
			
			tr = []
			# updated by NL, 04/25/2011: add checkbox and highlight function
			# first column of table
			# updated by NL. 12-7-2011
			tr.append(TDCell(HT.TD(HT.Input(type="checkbox", Class="checkbox", name="tissueResult",value=symbol, onClick="highlight(this)"), align='right',Class="fs12 fwn b1 c222 fsI",nowrap='ON'),symbol,symbol))
			# updated by NL, 04/26/2011: add GN and NCBI links
			#gene symbol (symbol column)
			tr.append(TDCell(HT.TD(HT.Italic(symbolItem), HT.BR(),gnUrl,"&nbsp;&nbsp|&nbsp;&nbsp", ncbiUrl, Class="fs12 fwn b1 c222"),symbolItem, symbolItem))

			#description and probe target description(description column)
			description_string=''
			if descDict.has_key(symbol):
				description_string = str(descDict[symbol]).strip()
			if pTargetDescDict.has_key(symbol):
				target_string = str(pTargetDescDict[symbol]).strip()

			description_display = ''
			if len(description_string) > 1 and description_string != 'None':
				description_display = description_string
			else:
				description_display = symbolItem

			if len(description_display) > 1 and description_display != 'N/A' and len(target_string) > 1 and target_string != 'None':
				description_display = description_display + '; ' + target_string.strip()
		
			tr.append(TDCell(HT.TD(description_display, Class="fs12 fwn b1 c222"), description_display, description_display))

			#trait_location_value is used for sorting (location column)
			trait_location_repr = 'N/A'
			trait_location_value = 1000000

			if ChrDict.has_key(symbol) and MbDict.has_key(symbol):
				
				if ChrDict[symbol] and MbDict[symbol]:		
					mb = float(MbDict[symbol])
					try:
						trait_location_value = int(ChrDict[symbol])*1000 + mb
					except:
						if ChrDict[symbol].upper() == 'X':
							trait_location_value = 20*1000 + mb
						else:
							trait_location_value = ord(str(ChrDict[symbol]).upper()[0])*1000 + mb

					trait_location_repr = 'Chr%s: %.6f' % (ChrDict[symbol], mb )
				else:
					trait_location_repr="N/A"
					trait_location_value ="N/A"
					
			tr.append(TDCell(HT.TD(trait_location_repr, Class="fs12 fwn b1 c222", nowrap="on"), trait_location_repr, trait_location_value))
			
            # number of overlaped cases  (N Case column)
			tr.append(TDCell(HT.TD(TissueCount, Class="fs12 fwn ffl b1 c222", align='right'),TissueCount,TissueCount))
			
			#tissue correlation (Tissue r column)
			TCorr = 0.0
			TCorrStr = "N/A"
			if symbolCorrDict.has_key(symbol):				
				TCorr = symbolCorrDict[symbol]
				TCorrStr = "%2.3f" % TCorr
				symbol2 =symbolItem.replace('"','') # some symbol is saved in "symbol" format
				# add a new parameter rankOrder for js function 'showTissueCorrPlot'
				rankOrder = int(method)
				TCorrPlotURL = "javascript:showTissueCorrPlot('%s','%s','%s',%d)" %(formName, primarySymbol, symbol2,rankOrder)
				tr.append(TDCell(HT.TD(HT.Href(text=TCorrStr, url=TCorrPlotURL, Class="fs12 fwn ff1"), Class="fs12 fwn ff1 b1 c222", align='right'), TCorrStr, abs(TCorr)))
			else:
				tr.append(TDCell(HT.TD(TCorrStr, Class="fs12 fwn b1 c222", align='right'), TCorrStr, abs(TCorr)))

			#p value of tissue correlation (Tissue p(r) column)
			TPValue = 1.0
			TPValueStr = "N/A"
			if symbolPvalueDict.has_key(symbol):
				TPValue = symbolPvalueDict[symbol]
				#TPValueStr = "%2.3f" % TPValue
				TPValueStr=webqtlUtil.SciFloat(TPValue)
			tr.append(TDCell(HT.TD(TPValueStr, Class="fs12 fwn b1 c222", align='right'), TPValueStr, TPValue))

			tblobj_body.append(tr)
			# build body(records) of excel for download function			
			for ncol, item in enumerate([geneId, symbolItem, description_display, trait_location_repr,TissueCount, TCorr, TPValue]):
				worksheet.write([newrow, ncol], item)

			newrow += 1

		return tblobj_body, worksheet

		
	# get return number of records when input symbol has only one
	def getReturnNum(self,recordReturnNum="0"):
		if recordReturnNum=="0":
			returnNum=100
		elif recordReturnNum=="1":
			returnNum=200
		elif recordReturnNum=="2":
			returnNum=500
		elif recordReturnNum=="3":
			returnNum=1000
		elif recordReturnNum=="4":
			returnNum=2000
		elif recordReturnNum=="5":
			returnNum= None
			
		return returnNum
		
	# map list based on the order of target List
	# if item.lower() exist in both lists, then compare the difference of item's original value of two lists
	# if not equal, then replace the item in targetList by using the item  in primaryList(list from database) 
	
	def mappedByTargetList(self,primaryList=[],targetList=[]):

		tempPrimaryList =[x.lower() for x in primaryList]
		testTargetList =[y.lower() for y in targetList]
	
		for i, item in enumerate(tempPrimaryList):
			if item in testTargetList:
				index = testTargetList.index(item)
				if primaryList[i]!=targetList[index]:
					targetList[index]= primaryList[i]

		return	targetList		
