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
# Last updated by Ning Liu 2011/01/11

import string
import piddle as pid
import os

from htmlgen import HTMLgen2 as HT

from utility import svg #Code using this module currently commented out
from utility import Plot
from base.webqtlTrait import webqtlTrait
from base.templatePage import templatePage
from utility import webqtlUtil
from base import webqtlConfig
from dbFunction import webqtlDatabaseFunction
from correlation import correlationFunction

#########################################
#      PlotCorrelationPage
#########################################
class PlotCorrelationPage(templatePage):
	corrMinInformative = 4
   
	def __init__(self, fd):

		templatePage.__init__(self, fd)

		self.initializeDisplayParameters(fd)

		if not fd.genotype:
			fd.readGenotype()

		if fd.allstrainlist:
			mdpchoice = fd.formdata.getvalue('MDPChoice')
			if mdpchoice == "1":
				strainlist = fd.f1list + fd.strainlist
			elif mdpchoice == "2":
				strainlist = []
				strainlist2 = fd.f1list + fd.strainlist
				for strain in fd.allstrainlist:
					if strain not in strainlist2:
						strainlist.append(strain)
				#So called MDP Panel
				if strainlist:
					strainlist = fd.f1list+fd.parlist+strainlist
			else:
				strainlist = fd.allstrainlist
			fd.readData(fd.allstrainlist)
		else:
			mdpchoice = None
			strainlist = fd.strainlist
			fd.readData()

		#if fd.allstrainlist:
		#	fd.readData(fd.allstrainlist)
		#	strainlist = fd.allstrainlist
		#else:
		#	fd.readData()
		#	strainlist = fd.strainlist
		
		
		if not self.openMysql():
			return

		isSampleCorr = 0 #XZ: initial value is false
		isTissueCorr = 0 #XZ: initial value is false

		#Javascript functions (showCorrelationPlot2, showTissueCorrPlot) have made sure the correlation type is either sample correlation or tissue correlation.
		if (self.database and (self.ProbeSetID != 'none')):
			isSampleCorr = 1
		elif (self.X_geneSymbol and self.Y_geneSymbol):
			isTissueCorr = 1
		else:
			heading = "Correlation Type Error"
			detail = ["For the input parameters, GN can not recognize the correlation type is sample correlation or tissue correlation."]
			self.error(heading=heading,detail=detail)
			return


        	TD_LR = HT.TD(colspan=2,height=200,width="100%",bgColor='#eeeeee', align="left", wrap="off")


		dataX=[]
		dataY=[]
		dataZ=[] # shortname
		fullTissueName=[]
		xlabel = ''
		ylabel = ''

		if isTissueCorr:
			dataX, dataY, xlabel, ylabel, dataZ, fullTissueName = self.getTissueLabelsValues(X_geneSymbol=self.X_geneSymbol, Y_geneSymbol=self.Y_geneSymbol, TissueProbeSetFreezeId=self.TissueProbeSetFreezeId)
			plotHeading = HT.Paragraph('Tissue Correlation Scatterplot')
			plotHeading.__setattr__("class","title")

		if isSampleCorr:
			plotHeading = HT.Paragraph('Sample Correlation Scatterplot')
                        plotHeading.__setattr__("class","title")

			#XZ: retrieve trait 1 info, Y axis
			trait1_data = [] #trait 1 data
			trait1Url = ''

			try:
				Trait1 = webqtlTrait(db=self.database, name=self.ProbeSetID, cellid=self.CellID, cursor=self.cursor)
				Trait1.retrieveInfo()
				Trait1.retrieveData()
			except:
				heading = "Retrieve Data"
				detail = ["The database you just requested has not been established yet."]
				self.error(heading=heading,detail=detail)
				return
	
			trait1_data = Trait1.exportData(strainlist)
			if Trait1.db.type == 'Publish' and Trait1.confidential:
				trait1Url = Trait1.genHTML(dispFromDatabase=1, privilege=self.privilege, userName=self.userName, authorized_users=Trait1.authorized_users)
			else:
				trait1Url = Trait1.genHTML(dispFromDatabase=1)
			ylabel = '%s : %s' % (Trait1.db.shortname, Trait1.name)
			if Trait1.cellid:
				ylabel += ' : ' + Trait1.cellid


			#XZ, retrieve trait 2 info, X axis
			traitdata2 = [] #trait 2 data
			_vals = [] #trait 2 data
			trait2Url = ''

			if ( self.database2 and (self.ProbeSetID2 != 'none') ):
				try:
					Trait2 = webqtlTrait(db=self.database2, name=self.ProbeSetID2, cellid=self.CellID2, cursor=self.cursor)
					Trait2.retrieveInfo()
					Trait2.retrieveData()
				except:
					heading = "Retrieve Data"
					detail = ["The database you just requested has not been established yet."]
					self.error(heading=heading,detail=detail)
					return

				if Trait2.db.type == 'Publish' and Trait2.confidential:
					trait2Url = Trait2.genHTML(dispFromDatabase=1, privilege=self.privilege, userName=self.userName, authorized_users=Trait2.authorized_users)
				else:
					trait2Url = Trait2.genHTML(dispFromDatabase=1)
				traitdata2 = Trait2.exportData(strainlist)
				_vals = traitdata2[:]
				xlabel = '%s : %s' % (Trait2.db.shortname, Trait2.name)
				if Trait2.cellid:
					xlabel += ' : ' + Trait2.cellid
			else:
				for item in strainlist:
					if fd.allTraitData.has_key(item):
						_vals.append(fd.allTraitData[item].val)
					else:
						_vals.append(None)

				if fd.identification:
					xlabel = fd.identification
				else:
					xlabel = "User Input Data"

				try:
					Trait2 = webqtlTrait(fullname=fd.formdata.getvalue('fullname'), cursor=self.cursor)
					trait2Url = Trait2.genHTML(dispFromDatabase=1)
				except:
					trait2Url = xlabel

			if (_vals and trait1_data):
				if len(_vals) != len(trait1_data):
					errors = HT.Blockquote(HT.Font('Error: ',color='red'),HT.Font('The number of traits are inconsistent, Program quit',color='black'))
					errors.__setattr__("class","subtitle")
					TD_LR.append(errors)
					self.dict['body'] = str(TD_LR)
					return

				for i in range(len(_vals)):
					if _vals[i]!= None and trait1_data[i]!= None:
						dataX.append(_vals[i])
						dataY.append(trait1_data[i])
						strainName = strainlist[i]
						if self.showstrains:
							dataZ.append(webqtlUtil.genShortStrainName(RISet=fd.RISet, input_strainName=strainName))
			else:
				heading = "Correlation Plot"
				detail = ['Empty Dataset for sample correlation, please check your data.']
				self.error(heading=heading,detail=detail)
				return


		#XZ: We have gotten all data for both traits.
		if len(dataX) >= self.corrMinInformative:

			if self.rankOrder == 0:
				rankPrimary = 0
				rankSecondary = 1
			else:
				rankPrimary = 1
				rankSecondary = 0

			lineColor = self.setLineColor();
			symbolColor = self.setSymbolColor();
			idColor = self.setIdColor();					
				
			c = pid.PILCanvas(size=(self.plotSize, self.plotSize*0.90))
			data_coordinate = Plot.plotXY(canvas=c, dataX=dataX, dataY=dataY, rank=rankPrimary, dataLabel = dataZ, labelColor=pid.black, lineSize=self.lineSize, lineColor=lineColor, idColor=idColor, idFont=self.idFont, idSize=self.idSize, symbolColor=symbolColor, symbolType=self.symbol, filled=self.filled, symbolSize=self.symbolSize, XLabel=xlabel, connectdot=0, YLabel=ylabel, title='', fitcurve=self.showline, displayR =1, offset= (90, self.plotSize/20, self.plotSize/10, 90), showLabel = self.showIdentifiers)
				
			if rankPrimary == 1:
				dataXlabel, dataYlabel = webqtlUtil.calRank(xVals=dataX, yVals=dataY, N=len(dataX))
			else:
				dataXlabel, dataYlabel = dataX, dataY
					
			gifmap1 = HT.Map(name='CorrelationPlotImageMap1')
				
			for i, item in enumerate(data_coordinate):
				one_rect_coordinate = "%d, %d, %d, %d" % (item[0] - 5, item[1] - 5, item[0] + 5, item[1] + 5)
				if isTissueCorr:
					one_rect_title = "%s (%s, %s)" % (fullTissueName[i], dataXlabel[i], dataYlabel[i])
				else:
					one_rect_title = "%s (%s, %s)" % (dataZ[i], dataXlabel[i], dataYlabel[i])
				gifmap1.areas.append(HT.Area(shape='rect',coords=one_rect_coordinate, title=one_rect_title) )

			filename= webqtlUtil.genRandStr("XY_")
			c.save(webqtlConfig.IMGDIR+filename, format='gif')
			img1=HT.Image('/image/'+filename+'.gif',border=0, usemap='#CorrelationPlotImageMap1')

			mainForm_1 = HT.Form( cgi= os.path.join(webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE), enctype='multipart/form-data', name='showDatabase', submit=HT.Input(type='hidden'))
			hddn = {'FormID':'showDatabase','ProbeSetID':'_','database':'_','CellID':'_','RISet':fd.RISet, 'ProbeSetID2':'_', 'database2':'_', 'CellID2':'_', 'allstrainlist':string.join(fd.strainlist, " "), 'traitList': fd.formdata.getvalue("traitList")}
			if fd.incparentsf1:
				hddn['incparentsf1'] = 'ON'		
			for key in hddn.keys():
				mainForm_1.append(HT.Input(name=key, value=hddn[key], type='hidden'))
			
			if isSampleCorr:
					mainForm_1.append(HT.P(), HT.Blockquote(HT.Strong('X axis:'),HT.Blockquote(trait2Url),HT.Strong('Y axis:'),HT.Blockquote(trait1Url), style='width: %spx;' % self.plotSize, wrap="hard"))
			
			graphForm = HT.Form(cgi= os.path.join(webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE), name='MDP_Form',submit=HT.Input(type='hidden'))
			graph_hddn = self.setHiddenParameters(fd, rankPrimary)
			webqtlUtil.exportData(graph_hddn, fd.allTraitData) #XZ: This is necessary to replot with different groups of strains
							
			for key in graph_hddn.keys():
				graphForm.append(HT.Input(name=key, value=graph_hddn[key], type='hidden'))			

			options = self.createOptionsMenu(fd, mdpchoice)	
			
			if (self.showOptions == '0'):
					showOptionsButton = HT.Input(type='button' ,name='optionsButton',value='Hide Options', onClick="showHideOptions();", Class="button")
			else:
					showOptionsButton = HT.Input(type='button' ,name='optionsButton',value='Show Options', onClick="showHideOptions();", Class="button")
					
			# updated by NL: 12-07-2011 add variables for tissue abbreviation page
			if isTissueCorr: 
				graphForm.append(HT.Input(name='shortTissueName', value='', type='hidden'))
				graphForm.append(HT.Input(name='fullTissueName', value='', type='hidden'))
				shortTissueNameStr=string.join(dataZ, ",")
				fullTissueNameStr=string.join(fullTissueName, ",")
		
				tissueAbbrButton=HT.Input(type='button' ,name='tissueAbbrButton',value='Show Abbreviations', onClick="showTissueAbbr('MDP_Form','%s','%s')" % (shortTissueNameStr,fullTissueNameStr), Class="button")
				graphForm.append(showOptionsButton,'&nbsp;&nbsp;&nbsp;&nbsp;',tissueAbbrButton, HT.BR(), HT.BR())
			else:
				graphForm.append(showOptionsButton, HT.BR(), HT.BR())

			graphForm.append(options, HT.BR())				
			graphForm.append(HT.HR(), HT.BR(), HT.P())
						
			TD_LR.append(plotHeading, HT.BR(),graphForm, HT.BR(), gifmap1, HT.P(), img1, HT.P(), mainForm_1)
			TD_LR.append(HT.BR(), HT.HR(color="grey", size=5, width="100%"))



			c = pid.PILCanvas(size=(self.plotSize, self.plotSize*0.90))
			data_coordinate = Plot.plotXY(canvas=c, dataX=dataX, dataY=dataY, rank=rankSecondary, dataLabel = dataZ, labelColor=pid.black,lineColor=lineColor, lineSize=self.lineSize, idColor=idColor, idFont=self.idFont, idSize=self.idSize, symbolColor=symbolColor, symbolType=self.symbol, filled=self.filled, symbolSize=self.symbolSize, XLabel=xlabel, connectdot=0, YLabel=ylabel,title='', fitcurve=self.showline, displayR =1, offset= (90, self.plotSize/20, self.plotSize/10, 90), showLabel = self.showIdentifiers)

			if rankSecondary == 1:
				dataXlabel, dataYlabel = webqtlUtil.calRank(xVals=dataX, yVals=dataY, N=len(dataX))
			else:
				dataXlabel, dataYlabel = dataX, dataY
				
			gifmap2 = HT.Map(name='CorrelationPlotImageMap2')
				
			for i, item in enumerate(data_coordinate):
				one_rect_coordinate = "%d, %d, %d, %d" % (item[0] - 6, item[1] - 6, item[0] + 6, item[1] + 6)
				if isTissueCorr:
					one_rect_title = "%s (%s, %s)" % (fullTissueName[i], dataXlabel[i], dataYlabel[i])
				else:
					one_rect_title = "%s (%s, %s)" % (dataZ[i], dataXlabel[i], dataYlabel[i])
					
				gifmap2.areas.append(HT.Area(shape='rect',coords=one_rect_coordinate, title=one_rect_title) )

			filename= webqtlUtil.genRandStr("XY_")
			c.save(webqtlConfig.IMGDIR+filename, format='gif')
			img2=HT.Image('/image/'+filename+'.gif',border=0, usemap='#CorrelationPlotImageMap2')

			mainForm_2 = HT.Form( cgi= os.path.join(webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE), enctype='multipart/form-data', name='showDatabase2', submit=HT.Input(type='hidden'))
			hddn = {'FormID':'showDatabase2','ProbeSetID':'_','database':'_','CellID':'_','RISet':fd.RISet, 'ProbeSetID2':'_', 'database2':'_', 'CellID2':'_', 'allstrainlist':string.join(fd.strainlist, " "), 'traitList': fd.formdata.getvalue("traitList")}
			if fd.incparentsf1:
				hddn['incparentsf1'] = 'ON'
			for key in hddn.keys():
				mainForm_2.append(HT.Input(name=key, value=hddn[key], type='hidden'))
				
			if isSampleCorr:
				mainForm_2.append(HT.P(), HT.Blockquote(HT.Strong('X axis:'),HT.Blockquote(trait2Url),HT.Strong('Y axis:'),HT.Blockquote(trait1Url), style='width:%spx;' % self.plotSize))

	
			TD_LR.append(HT.BR(), HT.P())
			TD_LR.append('\n', gifmap2, HT.P(), HT.P(), img2, HT.P(), mainForm_2)

			self.dict['body'] = str(TD_LR)
		else:
			heading = "Correlation Plot"
			detail = ['Fewer than %d strain data were entered for %s data set. No statitical analysis has been attempted.' % (self.corrMinInformative, fd.RISet)]
			self.error(heading=heading,detail=detail)
			return


	
	def initializeDisplayParameters(self, fd):
		"""
		Initializes all of the PlotCorrelationPage class parameters, 
		acquiring most values from the formdata (fd)
		"""
		
		rankOrderString = fd.formdata.getvalue('rankOrder')
        	if rankOrderString == "1":
            	    self.rankOrder = 1
        	else:
                    self.rankOrder = 0
            
                self.dict['title'] = 'Correlation X-Y Scatterplot'
		focusScript = "onLoad=\"document.getElementsByName('plotSize')[0].focus();\";"  
		self.dict['js2'] = focusScript        
		
		self.showstrains = fd.formdata.getvalue('ShowStrains')
		self.showline = fd.formdata.getvalue('ShowLine')
		self.X_geneSymbol = fd.formdata.getvalue('X_geneSymbol','')
		self.Y_geneSymbol = fd.formdata.getvalue('Y_geneSymbol','')
		self.TissueProbeSetFreezeId = fd.formdata.getvalue('TissueProbeSetFreezeId', '1')
		
		self.symbolColor = fd.formdata.getvalue('symbolColor', 'black')
		self.symbol = fd.formdata.getvalue('symbol', 'circle')
		self.filled = fd.formdata.getvalue('filled', 'yes')
		self.symbolSize = fd.formdata.getvalue('symbolSize', 'tiny')
		self.idColor = fd.formdata.getvalue('idColor', 'blue')
		self.idFont = fd.formdata.getvalue('idFont', 'arial')
		self.idSize = fd.formdata.getvalue('idSize', '14')
		self.lineColor = fd.formdata.getvalue('lineColor', 'grey')
		self.lineSize = fd.formdata.getvalue('lineSize', 'medium')
		self.showOptions = fd.formdata.getvalue('showOptions', '0')
		
		try:
			self.plotSize = int(fd.formdata.getvalue('plotSize', 900))
		except:
			self.plotSize = 900
		try:
            		self.showIdentifiers = int(fd.formdata.getvalue('showIdentifiers', 1))
        	except:
            		self.showIdentifiers = 1
            		
		self.database = fd.formdata.getvalue('database')
		self.ProbeSetID = fd.formdata.getvalue('ProbeSetID', 'none')
		self.CellID = fd.formdata.getvalue('CellID')
		
        	self.database2 = fd.formdata.getvalue('database2')
		self.ProbeSetID2 = fd.formdata.getvalue('ProbeSetID2', 'none')
		self.CellID2 = fd.formdata.getvalue('CellID2')	
	
	def createOptionsMenu(self, fd, mdpchoice):
		"""
		Create all the HTML for the options menu; the first if/else statements
		determine whether the Div container holding all the other html is visible
		or not.
		"""
		
		if (self.showOptions == '0'):
			options = HT.Div(name="options", id="options", style="display: none")
			self.showOptions = '1'
		else:
			options = HT.Div(name="options", id="options", style="display: ''")	
			self.showOptions = '0'
		
		if self.showIdentifiers:	
			containerTable = HT.TableLite(cellspacing=1, width=730, height=150, border=1)
		else:
			containerTable = HT.TableLite(cellspacing=1, width=730, height=130, border=1)		
		
		if self.showIdentifiers:	
			containerTable = HT.TableLite(cellspacing=1, width=730, height=150, border=1)
		else:
			containerTable = HT.TableLite(cellspacing=1, width=730, height=130, border=1)
		
		containerRow = HT.TR()
		containerCell = HT.TD(valign="middle", align="center")
		
		optionsTable = HT.TableLite(Class="collap", cellspacing=2, width=700)

		sizeOptions = HT.TR(align="right")
		tagOptions = HT.TR(align="right")
		markerOptions = HT.TR(align="right")
		lineOptions = HT.TR(align="right")
		replot_mdpOptions = HT.TR(align="right")

		sizeOptions.append(HT.TD(HT.Bold("Size: "), "&nbsp;"*1, HT.Input(type='text' ,name='plotSize', value=self.plotSize, style="background-color: #FFFFFF; width: 50px;", onChange="checkWidth();"), align="left"))

		idColorSel = HT.Select(name="idColorSel", onChange="changeIdColor(); submit();", selected=self.idColor)
		idColorSel.append(("blue", "blue"))
		idColorSel.append(("green", "green"))
		idColorSel.append(("red", "red"))
		idColorSel.append(("yellow", "yellow"))
		idColorSel.append(("white", "white"))
		idColorSel.append(("purple", "purple"))
		idColorSel.append(("brown", "brown"))
		idColorSel.append(("grey", "grey"))
		idColorSel.append(("black","black")) 

		idFontSel = HT.Select(name="idFontSel", onChange="changeIdFont(); submit();", selected=self.idFont)
		idFontSel.append(("Arial", "arial"))
		idFontSel.append(("Trebuchet", "trebuc"))
		idFontSel.append(("Verdana", "verdana"))
		idFontSel.append(("Georgia", "Georgia"))
		idFontSel.append(("Courier", "cour"))
		
		idSizeSel = HT.Select(name="idSizeSel", onChange="changeIdSize(); submit();", selected=self.idSize)
		idSizeSel.append(("10", "10"))
		idSizeSel.append(("12", "12"))
		idSizeSel.append(("14", "14"))
		idSizeSel.append(("16", "16"))
		idSizeSel.append(("18", "18"))

		if self.showIdentifiers:
			tagButton = HT.TD(HT.Input(type='button' ,name='',value='  Hide Tags  ',onClick="this.form.showIdentifiers.value=0;submit();", Class="button"), align="right")
		else:
			tagButton = HT.TD(HT.Input(type='button' ,name='',value='  Show Tags  ',onClick="this.form.showIdentifiers.value=1;submit();", Class="button"), align="right")

        	tagOptions.append(HT.TD(HT.Text(HT.Bold("Tag Settings: ")), align="left"))
        	tagOptions.append(HT.TD(HT.Text(text="Font: "), idFontSel))
		tagOptions.append(HT.TD(HT.Text(text="Color: "), idColorSel))
		tagOptions.append(HT.TD(HT.Text(text="Point: "), idSizeSel))
		tagOptions.append(tagButton)
		optionsTable.append(sizeOptions, tagOptions)
		
		if fd.allstrainlist and mdpchoice:
			allStrainList = HT.Input(name='allstrainlist', value=string.join(fd.allstrainlist, " "), type='hidden')
			mdpChoice = HT.Input(name='MDPChoice', value=mdpchoice, type='hidden')
			btn0 = HT.Input(type='button' ,name='',value='All Cases',onClick="this.form.MDPChoice.value=0;submit();", Class="button")
			btn1 = HT.Input(type='button' ,name='',value='%s Only' % fd.RISet,onClick="this.form.MDPChoice.value=1;submit();", Class="button")
			btn2 = HT.Input(type='button' ,name='',value='MDP Only', onClick="this.form.MDPChoice.value=2;submit();", Class="button")
                

    		colorSel = HT.Select(name="colorSel", onChange="changeSymbolColor(); submit();", selected=self.symbolColor)
    		colorSel.append(("red", "red"))
    		colorSel.append(("green", "green"))
    		colorSel.append(("blue", "blue"))
    		colorSel.append(("yellow", "yellow"))
    		colorSel.append(("purple", "purple"))
    		colorSel.append(("brown", "brown"))
    		colorSel.append(("grey", "grey"))
    		colorSel.append(("black","black")) 
    		
    		symbolSel = HT.Select(name="symbolSel", onChange="changeSymbol(); submit();", selected=self.symbol)
    		symbolSel.append(("4-star","4-star"))
    		symbolSel.append(("3-star","3-star"))
    		symbolSel.append(("cross", "cross"))
    		symbolSel.append(("circle","circle"))
            	symbolSel.append(("diamond", "diamond"))
    		symbolSel.append(("square", "square"))
    		symbolSel.append(("vert rect", "vertRect"))
    		symbolSel.append(("hori rect", "horiRect"))
    		
    		sizeSel = HT.Select(name="sizeSel", onChange="changeSize(); submit();", selected=self.symbolSize)
		sizeSel.append(("tiny","tiny"))
    		sizeSel.append(("small","small"))
    		sizeSel.append(("medium","medium"))
    		sizeSel.append(("large","large"))         

    		fillSel = HT.Select(name="fillSel", onChange="changeFilled(); submit();", selected=self.filled)
    		fillSel.append(("no","no"))
    		fillSel.append(("yes","yes"))
 
    		lineColorSel = HT.Select(name="lineColorSel", onChange="changeLineColor(); submit();", selected=self.lineColor)
    		lineColorSel.append(("red", "red"))
    		lineColorSel.append(("green", "green"))
    		lineColorSel.append(("blue", "blue"))
    		lineColorSel.append(("yellow", "yellow"))
    		lineColorSel.append(("purple", "purple"))
    		lineColorSel.append(("brown", "brown"))
    		lineColorSel.append(("grey", "grey"))
    		lineColorSel.append(("black","black")) 
    		
    		lineSizeSel = HT.Select(name="lineSizeSel", onChange="changeLineSize(); submit();", selected=self.lineSize)
    		lineSizeSel.append(("thin", "thin"))
    		lineSizeSel.append(("medium", "medium"))
    		lineSizeSel.append(("thick", "thick"))
    		
    		
    		markerOptions.append(HT.TD(HT.Text(HT.Bold("Marker Settings: ")), align="left"))
    		markerOptions.append(HT.TD(HT.Text(text="Marker: "), symbolSel))
    		markerOptions.append(HT.TD(HT.Text(text="Color: "), colorSel))
    		markerOptions.append(HT.TD(HT.Text(text="Fill: "), fillSel))
    		markerOptions.append(HT.TD(HT.Text(text="Size: "), sizeSel))
    		
    		lineOptions.append(HT.TD(HT.Text(HT.Bold("Line Settings: ")), align="left"))
    		lineOptions.append(HT.TD(HT.Text(text="Width: "), lineSizeSel))
    		lineOptions.append(HT.TD(HT.Text(text="Color: "), lineColorSel))
    	
		replotButton = HT.Input(type='button', name='', value='    Replot    ',onClick="checkWidth(); submit();", Class="button")
	
    		if fd.allstrainlist and mdpchoice:
                    replot_mdpOptions.append(HT.TD(replotButton, align="left"), HT.TD(allStrainList, mdpChoice, btn0, btn1, btn2, align="center", colspan=3))
		    optionsTable.append(markerOptions, lineOptions, HT.TR(HT.TD(HT.BR())), replot_mdpOptions )
                else:
                    replot_mdpOptions.append(HT.TD(replotButton, align="left"))
		    optionsTable.append(markerOptions, lineOptions, HT.TR(HT.TD(HT.BR())), replot_mdpOptions)
            
    		containerCell.append(optionsTable)
    		containerRow.append(containerCell)
    		containerTable.append(containerRow)
    		
    		options.append(containerTable)

		return options
	
	def setHiddenParameters(self, fd, rankPrimary):
		"""
		Create the dictionary of hidden form parameters from PlotCorrelationPage's class parameters
		"""
		
		graph_hddn = {'FormID':'showCorrelationPlot','RISet':fd.RISet, 'identification':fd.identification, "incparentsf1":1, "showIdentifiers":self.showIdentifiers}
		
		if self.database:	graph_hddn['database']=self.database
		if self.ProbeSetID:	graph_hddn['ProbeSetID']=self.ProbeSetID
		if self.CellID:	graph_hddn['CellID']=self.CellID
		if self.database2:	graph_hddn['database2']=self.database2
		if self.ProbeSetID2:	graph_hddn['ProbeSetID2']=self.ProbeSetID2
		if self.CellID2:	graph_hddn['CellID2']=self.CellID2
		if self.showstrains:	graph_hddn['ShowStrains']=self.showstrains
		if self.showline:	graph_hddn['ShowLine']=self.showline
		if self.X_geneSymbol: graph_hddn['X_geneSymbol']=self.X_geneSymbol
		if self.Y_geneSymbol: graph_hddn['Y_geneSymbol']=self.Y_geneSymbol
		if self.TissueProbeSetFreezeId: graph_hddn['TissueProbeSetFreezeId']=self.TissueProbeSetFreezeId
		if self.rankOrder:  graph_hddn['rankOrder'] = rankPrimary
		if fd.formdata.getvalue('fullname'):	graph_hddn['fullname']=fd.formdata.getvalue('fullname')
		if self.lineColor: graph_hddn['lineColor'] = self.lineColor
		if self.lineSize: graph_hddn['lineSize'] = self.lineSize
		if self.idColor: graph_hddn['idColor'] = self.idColor
		if self.idFont: graph_hddn['idFont'] = self.idFont
		if self.idSize: graph_hddn['idSize'] = self.idSize
		if self.symbolColor:   graph_hddn['symbolColor'] = self.symbolColor
		if self.symbol: graph_hddn['symbol'] = self.symbol
		if self.filled: graph_hddn['filled'] = self.filled
		if self.symbolSize: graph_hddn['symbolSize'] = self.symbolSize
		if self.showOptions: graph_hddn['showOptions'] = self.showOptions
	
		return graph_hddn
	
	def setIdColor(self):
		"""
		Set the plot tag/ID color based upon the value of the idColor class parameter
		"""
		
		if self.idColor == 'black':
			idColor = pid.black
		elif self.idColor == 'white':
			idColor = pid.white
		elif self.idColor == 'yellow':
			idColor = pid.yellow
		elif self.idColor == 'grey':
			idColor = pid.grey
		elif self.idColor == 'blue':
			idColor = pid.blue
		elif self.idColor == 'purple':
			idColor = pid.purple
		elif self.idColor == 'brown':
			idColor = pid.brown
		elif self.idColor == 'green':
			idColor = pid.green		
		else:
			idColor = pid.red
			
		return idColor	
	
	def setSymbolColor(self):
		"""
		Set the plot symbol color based upon the value of the symbolColor class parameter
		"""
		
		if self.symbolColor == 'black':
			symbolColor = pid.black
		elif self.symbolColor == 'grey':
			symbolColor = pid.grey
		elif self.symbolColor == 'yellow':
			symbolColor = pid.yellow
		elif self.symbolColor == 'blue':
			symbolColor = pid.blue
		elif self.symbolColor == 'purple':
			symbolColor = pid.purple
		elif self.symbolColor == 'brown':
			symbolColor = pid.brown
		elif self.symbolColor== 'green':
			symbolColor = pid.green		
		else:
			symbolColor = pid.red
			
		return symbolColor

	def setLineColor(self):
		"""
		Set the plot line color based upon the lineColor class parameter
		"""
		
		if self.lineColor == 'black':
			lineColor = pid.black
		elif self.lineColor == 'grey':
			lineColor = pid.grey
		elif self.lineColor == 'yellow':
			lineColor = pid.yellow
		elif self.lineColor == 'blue':
			lineColor = pid.blue
		elif self.lineColor == 'purple':
			lineColor = pid.purple
		elif self.lineColor == 'brown':
			lineColor = pid.brown
		elif self.lineColor== 'green':
			lineColor = pid.green		
		else:
			lineColor = pid.red
			
		return lineColor
		

	def getTissueLabelsValues(self, X_geneSymbol=None, Y_geneSymbol=None, TissueProbeSetFreezeId=None ):

	    dataX = []
	    dataY = []
	    data_fullLabel = []
	    data_shortLabel = []
		# updated by NL, 2011-01-11 using new function getTissueProbeSetXRefInfo to get dataId value
	    X_symbolList,X_geneIdDict,X_dataIdDict,X_ChrDict,X_MbDict,X_descDict,X_pTargetDescDict = correlationFunction.getTissueProbeSetXRefInfo(cursor=self.cursor,GeneNameLst=[X_geneSymbol],TissueProbeSetFreezeId=TissueProbeSetFreezeId)
	    Y_symbolList,Y_geneIdDict,Y_dataIdDict,Y_ChrDict,Y_MbDict,Y_descDict,Y_pTargetDescDict = correlationFunction.getTissueProbeSetXRefInfo(cursor=self.cursor,GeneNameLst=[Y_geneSymbol],TissueProbeSetFreezeId=TissueProbeSetFreezeId)
		# in dataIdDict, key is the lower cased geneSymbol
	    X_DataId = X_dataIdDict[X_geneSymbol.lower()]
	    Y_DataId = Y_dataIdDict[Y_geneSymbol.lower()]

	    self.cursor.execute("SELECT TissueID,value FROM  TissueProbeSetData WHERE Id = %d ORDER BY TissueID" % int(X_DataId) )
	    results = self.cursor.fetchall()
	    for item in results:
	        TissueID, Value = item
	        dataX.append(Value)
	        self.cursor.execute("SELECT Tissue.Name, Tissue.Short_Name FROM Tissue WHERE Id = %d" % int(TissueID) )
	        temp = self.cursor.fetchone()
	        data_fullLabel.append( temp[0] )
	        data_shortLabel.append( temp[1] )

	    self.cursor.execute("SELECT TissueID,value FROM  TissueProbeSetData WHERE Id = %d ORDER BY TissueID" % int(Y_DataId) )
	    results = self.cursor.fetchall()
	    for item in results:
	        TissueID, Value = item
	        dataY.append(Value)

	    X_label = "%s" % X_geneSymbol
	    Y_label = "%s" % Y_geneSymbol
		
	    return dataX, dataY, X_label, Y_label, data_shortLabel, data_fullLabel
