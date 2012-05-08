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

import string
import piddle as pid
import os
import math

from htmlgen import HTMLgen2 as HT

from utility import svg
from base import webqtlConfig
from utility import Plot
from utility import webqtlUtil
from base.webqtlDataset import webqtlDataset
from base.templatePage import templatePage


######################################### 
#      Genome Scan PAGE
#########################################
class cmdGenomeScanPage(templatePage):
	def __init__(self,fd):
		templatePage.__init__(self,fd)
		if not self.openMysql():
			return
		self.database = fd.formdata.getvalue('database', '')
		db = webqtlDataset(self.database, self.cursor)

		try:
			self.openURL = webqtlConfig.CGIDIR + webqtlConfig.SCRIPTFILE + \
				'?FormID=showDatabase&database=%s&incparentsf1=1&ProbeSetID=' % self.database
				
			if db.type != "ProbeSet" or not db.id:
				raise DbNameError
			
			self.cursor.execute("""
				Select 
					InbredSet.Name
				From
					ProbeSetFreeze, ProbeFreeze, InbredSet
				whERE
					ProbeSetFreeze.ProbeFreezeId = ProbeFreeze.Id AND
					ProbeFreeze.InbredSetId = InbredSet.Id AND
					ProbeSetFreeze.Id = %d
				""" % db.id)
			thisRISet = self.cursor.fetchone()[0]
			if thisRISet =='BXD300':
				thisRISet = 'BXD'

			##################################################
			#  exon data is too huge for GenoGraph, skip it  #
			##################################################
			self.cursor.execute('select count(*) from ProbeSetXRef where ProbeSetFreezeId=%d' % db.id)
			amount = self.cursor.fetchall()
			if amount:
				amount = amount[0][0]
				if amount>100000:
					heading = "Whole Transcriptome Mapping"
					detail = ["Whole Transcriptome Mapping is not available for this data set."]
					self.error(heading=heading,detail=detail)
					return

			self.cursor.execute("""
				Select 
					ProbeSet.Id, ProbeSet.Name, ProbeSet.Chr, ProbeSet.Mb, ProbeSetXRef.Locus, ProbeSetXRef.pValue
				From
					ProbeSet, ProbeSetXRef
				whERE
					ProbeSetXRef.ProbeSetFreezeId = %d AND
					ProbeSetXRef.ProbeSetId = ProbeSet.Id AND
					ProbeSetXRef.Locus is not NULL 
				""" % db.id)
			results = self.cursor.fetchall()

			if results:
				self.mouseChrLengthDict, sum = self.readMouseGenome(thisRISet)
				
				import reaper
				markerGMb = {}
				genotype_1 = reaper.Dataset()
				genotype_1.read(os.path.join(webqtlConfig.GENODIR, thisRISet + '.geno'))
				for chr in genotype_1:
					chrlen = self.mouseChrLengthDict[chr.name]

					for locus in chr:	
						markerGMb[locus.name] = locus.Mb + chrlen
  				
				try:
					FDR = float(fd.formdata.getvalue("fdr", ""))
				except:
					FDR = 0.2
				self.grid = fd.formdata.getvalue("grid", "")
				
				NNN = len(results)
				results = list(results)
				results.sort(self.cmppValue)

				MbCoord = []
				MbCoord2 = []

				for j in range(NNN, 0, -1):
					if results[j-1][-1] <= (FDR*j)/NNN:
						break

				if j > 0:
					for i in range(j-1, -1, -1):
						_Id, _probeset, _chr, _Mb, _marker, _pvalue = results[i]
						try:
							MbCoord.append([markerGMb[_marker], _Mb+self.mouseChrLengthDict[string.strip(_chr)], _probeset, _chr, _Mb, _marker, _pvalue])
						except:
							pass
          	
				filename=webqtlUtil.genRandStr("gScan_")
				canvas = pid.PILCanvas(size=(1280,880))
				self.drawGraph(canvas, MbCoord, cLength=sum)
		
				canvas.save(os.path.join(webqtlConfig.IMGDIR, filename), format='png')
	
				canvasSVG = self.drawSVG(MbCoord, cLength=sum, size=(1280,880))
				canvasSVG.toXml(os.path.join(webqtlConfig.IMGDIR, filename+'.svg')) #and write it to file
				
				img  = HT.Embed(src='/image/'+filename+'.png', width=1280, height=880, border=0, alt='Genome Scan')
				img2 = HT.Embed(src='/image/'+filename+'.svg', width=1280, height=880, border=0)
				TD_LR = HT.TD(colspan=2,height=200,width="100%",bgColor='#eeeeee')
				
				heading = HT.Paragraph('Whole Transcriptome Mapping')
				heading.__setattr__("class","title")
				intro = HT.Blockquote()
				intro.append('The plot below is the Whole Transcriptome Mapping of Database ') 
				intro.append(HT.Href(text=db.fullname, url = webqtlConfig.INFOPAGEHREF % db.name ,target='_blank',Class="normalsize"))
				intro.append(". %d from a total of %d ProbeSets were utilized to generate this graph." % (len(MbCoord), len(results)))
				
				mainfm = HT.Form(cgi = os.path.join(webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE),  enctype='multipart/form-data', \
					name=webqtlUtil.genRandStr("fm_"), submit=HT.Input(type='hidden'))
				mainfm.append(HT.Input(name='database', value=self.database, type='hidden'))
				mainfm.append(HT.Input(name='FormID', value='transciptMapping', type='hidden'))
				
				mainfm.append("<BLOCKQUOTE>")
				mainfm.append("0 < FDR <= 1.0 ")
				mainfm.append(HT.Input(name='fdr', value=FDR, type='text'))
			
				mainfm.append(HT.Input(name='submit', value='Redraw Graph', type='submit', Class='button'))
				mainfm.append("</BLOCKQUOTE>")
				mainfm.append("""
<center>
<div id="gallery">
<div class="on"  title="img1"><span>Static</span></div>
<div class="off" title="img2"><span>Interactive</span></div>
</div>

<div id="img1" class="show">
""")           
				mainfm.append(img)
				mainfm.append("""
</div>

<div id="img2" class="hide">
""")
				mainfm.append(img2)
				mainfm.append("""
</div>
</center>
""")

				TD_LR.append(heading, intro, HT.Paragraph(mainfm))
				
				self.dict['title'] = 'Whole Transcriptome Mapping'
				self.dict['body'] = TD_LR
			else:
				heading = "Whole Transcriptome Mapping"
				detail = ["Database calculation is not finished."]
				self.error(heading=heading,detail=detail)
				return
		except:
			heading = "Whole Transcriptome Mapping"
			detail = ["Whole Transcriptome Mapping only apply to Microarray database."]
			self.error(heading=heading,detail=detail)
			return
			
	def drawSVG(self, data, cLength = 2500, offset= (80, 160, 60, 60), size=(1280,880), 
			XLabel="Marker GMb", YLabel="Transcript GMb"):
		entities = {
				"colorText" : "fill:darkblue;",
				"strokeText" : ";stroke:none;stroke-width:0;",
				"allText" : "font-family:Helvetica;", 
				"titleText" : "font-size:22;font-weight:bold;", 
				"subtitleText" : "font-size:18;font-weight:bold;", 
				"headlineText" : "font-size:14;font-weight:bold;", 
				"normalText" : "font-size:12;", 
				"legendText" : "font-size:11;text-anchor:end;", 
				"valuesText" : "font-size:12;", 
				"boldValuesText" : "font-size:12;font-weight:bold;", 
				"smallText" : "font-size:10;", 
				"vText" : "writing-mode:tb-rl",
				"rightText" : "text-anchor:end;", 
				"middleText" : "text-anchor:middle;", 
				"bezgrenzstyle" : "fill:none;stroke:#11A0FF;stroke-width:40;stroke-antialiasing:true;", 
				"rectstyle" : "fill:lightblue;stroke:none;opacity:0.2;", 
				"fillUnbebaut" : "fill:#CCFFD4;stroke:none;", 
				"fillNodata" : "fill:#E7E7E7;stroke:black;stroke-width:2;stroke-antialiasing:true;", 
				"fillNodataLegend" : "fill:#E7E7E7;stroke:black;stroke-width:0.5;stroke-antialiasing:true;", 
				"grundzeitstyle" : "fill:none;stroke:#E00004;stroke-width:60;stroke-antialiasing:true;", 
				"bezgrenzstyle" : "fill:none;stroke:#11A0FF;stroke-width:40;stroke-antialiasing:true;", 
				"mapAuthor" : "A. Neumann", 
				}
		cWidth, cHeight = size		
		canvasSVG = svg.drawing(entities) #create a drawing
		drawSpace=svg.svg((0, 0, cWidth, cHeight), cWidth, cHeight, xml__space="preserve", 
			zoomAndPan="disable", onload="initMap(evt);", 
			xmlns__a3="http://ns.adobe.com/AdobeSVGViewerExtensions/3.0/",
			a3__scriptImplementation="Adobe") #create a svg drawingspace
		canvasds=svg.description('Genome Graph') #define a description
		drawSpace.addElement(canvasds) #add the description to the svg
		
		#need to be modified or deleted
		xLeftOffset, xRightOffset, yTopOffset, yBottomOffset = offset
		plotWidth = cWidth - xLeftOffset - xRightOffset
		plotHeight = cHeight - yTopOffset - yBottomOffset
		drawSpace.addElement(svg.script("", language="javascript", xlink__href="/javascript/svg.js"))
		
		#add defs
		defs = svg.defs()
		symbol1= svg.symbol(id="magnifyer", overflow="visible", 
			style="fill:white;stroke:orange;stroke-width:2;")
		symbol1.addElement(svg.line(0, 0, -8, 20))
		symbol1.addElement(svg.circle(0, 0, 8))
		symbol1.addElement(svg.line(-4, 0, 4, 0, style="stroke:orange;stroke-width:2;"))
		defs.addElement(symbol1)
		symbol2= svg.symbol(id="magnifyerZoomIn",overflow="visible")
		symbol2.addElement(svg.use(link="#magnifyer", id="zoomIn"))
		symbol2.addElement(svg.line(0, -4, 0, 4, style="stroke:orange;stroke-width:2;"))
		defs.addElement(symbol2)
		drawSpace.addElement(defs)
		
		symbol3= svg.symbol(id="msgbox", overflow="visible", 
			style="fill:white;stroke:orange;stroke-width:1;opacity:0.8;")
		symbol3.addElement(svg.rect(-80, -190, 300, 150, rx=10, ry=10))
		symbol3.addElement(svg.line(21, -40, 58, -40, style="stroke:white;"))
		symbol3.addElement(svg.polyline([[20, -40], [0, 0], [60, -40]]))
		symbol3.addElement(svg.text(-60, -160, "ProbeSet ", style="&colorText; &allText; &subtitleText; &strokeText;"))
		symbol3.addElement(svg.text(-60, -125, "Marker ", style="&colorText; &allText; &subtitleText; &strokeText;"))
		symbol3.addElement(svg.text(-60, -90, "LRS ", style="&colorText; &allText; &subtitleText; &strokeText;"))
		symbol3.addElement(svg.text(-60, -55, "P value ", style="&colorText; &allText; &subtitleText; &strokeText;"))
		defs.addElement(symbol3)
		
		g = svg.group("title")
		g.addElement(svg.text(cWidth-40, 30, "Genome Graph", style="&colorText; &allText; &titleText; &rightText;"))
		g.addElement(svg.text(cWidth-40, 50, "Whole Transcriptome Mapping", style="&colorText; &allText; &subtitleText; &rightText;"))
		drawSpace.addElement(g)
		
		#draw Main display area border
		mainSquare = cHeight-60
		cordZOOM = 10
		drawSpace.addElement(svg.rect(8, 8, mainSquare+4, mainSquare+4,'none',"orange",0.5, rx="5", ry="5"))
		drawSpace.addElement(svg.text(10+mainSquare/2, 40+mainSquare,'Marker GMb', 
			style="&colorText; &allText; &titleText; &middleText;", id="XLabel"))
		drawSpace.addElement(svg.text(mainSquare + 80, 10+mainSquare/2,'Transcript GMb', 
			style="&colorText; &allText; &titleText; &middleText; &vText;", id="YLabel"))
		
		#draw overview display area
		drawSpace.addElement(svg.rect(cWidth-40-260, 60, 260, 260,'none',"orange",0.5, rx="5", ry="5"))
		drawSpaceThumb= svg.svg(id="overviewPlot",x=cWidth-40-260,y="60",width="260",
			height="260",viewBox=(0, 0, mainSquare*cordZOOM, mainSquare*cordZOOM))
		g = svg.group(style="&bezgrenzstyle;")
		g.addElement(svg.use("#grid"))
		drawSpaceThumb.addElement(g)
		drawSpaceThumb.addElement(svg.rect(id="overviewRect",style="&rectstyle;",
			x="0",y="0",width=mainSquare*cordZOOM,height=mainSquare*cordZOOM, 
			onmouseover="statusChange('click and drag rectangle to change extent');",
			onmousedown="beginPan(evt);", onmousemove="doPan(evt);", 
			onmouseup="endPan();", onmouseout="endPan();"))
		drawSpace.addElement(drawSpaceThumb)
		
		#draw navigator
		g = svg.group(id="navigatorElements")
		g.addElement(svg.use("#magnifyerZoomIn", id="zoomIn", transform="translate(%d,350)" % (cWidth-40-130-20), 
			onmouseover="magnify(evt,1.3,'in');", onmouseout="magnify(evt,1,'in');", onclick="zoomIt('in');"))
		g.addElement(svg.use("#magnifyer", id="zoomOut", transform="translate(%d,350)" % (cWidth-40-130+20),
			onmouseover="magnify(evt,1.3,'out');",onmouseout="magnify(evt,1,'out');", onclick="zoomIt('out');"))
		
		drawSpace.addElement(g)
		
		g = svg.group(id="statusBar")
		g.addElement(svg.text(cWidth-40-260, 360, "ZOOM: 100%", style="fill:orange; font-size:14;", id="zoomValueObj"))
		g.addElement(svg.text(cWidth-40-260, 380, "Status:", style="&colorText; &allText; &smallText;"))
		g.addElement(svg.text(cWidth-40-260, 395, "Loading Plot", style="&colorText; &allText; &smallText;", id="statusText"))
		drawSpace.addElement(g)
		
		#draw main display area
		drawSpaceMain= svg.svg((0, 0, mainSquare*cordZOOM, mainSquare*cordZOOM), mainSquare, mainSquare, 
			id="mainPlot",x="10",y="10")
		mPlotWidth = mPlotHeight = 0.8*mainSquare*cordZOOM
		
		drawSpaceMain.addElement(svg.rect(mainSquare*cordZOOM*0.1, mainSquare*cordZOOM*0.1, mPlotWidth, mPlotHeight,style="fill:white",
			onmousemove="showChr(evt);", onmouseover="showChr(evt);", onmouseout="showNoChr(evt);"))
		#draw grid
		g = svg.group("grid", style="stroke:lightblue;stroke-width:3", 
			transform="translate(%d,%d)" % (mainSquare*cordZOOM*0.1, mainSquare*cordZOOM*0.1))
			
		if 1: #self.grid == "on":
			js = [] 
			for key in self.mouseChrLengthDict.keys():
				length = self.mouseChrLengthDict[key]
				js.append(mPlotWidth*length/cLength)
				if length != 0:
					yCoord = mPlotHeight*(1.0-length/cLength)
					l = svg.line(0,yCoord ,mPlotWidth, yCoord)
					g.addElement(l)	
					xCoord = mPlotWidth*length/cLength
					l = svg.line(xCoord, 0 ,xCoord, mPlotHeight)
					g.addElement(l)
			js.sort()
			drawSpace.addElement(svg.script("",language="javascript", cdata="var openURL=\"%s\";\nvar chrLength=%s;\n" % (self.openURL, js)))
		
		g.addElement(svg.rect(0, 0, mPlotWidth, mPlotHeight,'none','black',10))
		drawSpaceMain.addElement(g)
		
		#draw Scale
		g = svg.group("scale", style="stroke:black;stroke-width:0", 
			transform="translate(%d,%d)" % (mainSquare*cordZOOM*0.1, mainSquare*cordZOOM*0.1))
		i = 100
		scaleFontSize = 11*cordZOOM
		while i < cLength:
			yCoord = mPlotHeight - mPlotHeight*i/cLength
			l = svg.line(0,yCoord ,-5*cordZOOM, yCoord)
			g.addElement(l)
			t = svg.text(-40*cordZOOM, yCoord +5*cordZOOM, "%d"% i, 100, "verdana") # coordinate tag Y
			g.addElement(t)
			xCoord = mPlotWidth*i/cLength
			l = svg.line(xCoord, mPlotHeight, xCoord, mPlotHeight+5*cordZOOM)
			g.addElement(l)
			if i%200 == 0:
				t = svg.text(xCoord, mPlotHeight+10*cordZOOM, "%d"% i, 100, "verdana") # coordinate tag X
				g.addElement(t)
			i += 100
			
		drawSpaceMain.addElement(g)
		#draw Points
		finecolors = Plot.colorSpectrumSVG(12)
		finecolors.reverse()
		g = preColor = ""
		for item in data:
			_probeset, _chr, _Mb, _marker, _pvalue = item[2:]
			try:
				_idx = int((-math.log10(_pvalue))*12/6.0) # add module name
				_color = finecolors[_idx]
			except:
				_color = finecolors[-1]
			if _color != preColor:
				preColor = _color
				if g:
					drawSpaceMain.addElement(g)
				g = svg.group("points", style="stroke:%s;stroke-width:5" % _color, 
					transform="translate(%d,%d)" % (mainSquare*cordZOOM*0.1, mainSquare*cordZOOM*0.1),
					onmouseover="mvMsgBox(evt);", onmouseout="hdMsgBox();", onmousedown="openPage(evt);")
			else:
				pass
			px = mPlotWidth*item[0]/cLength
			py = mPlotHeight*(1.0-item[1]/cLength)
			l = svg.line("%2.1f" % (px-3*cordZOOM), "%2.1f" % py, "%2.1f" % (px+3*cordZOOM), "%2.1f" % py, ps=_probeset, mk=_marker)
			g.addElement(l)	

		drawSpaceMain.addElement(g)
		
		"""
		#draw spectrum
		i = 0
		j = 0
		middleoffsetX = 40
		labelFont=pid.Font(ttf="tahoma",size=12,bold=0)
		for dcolor in finecolors:
			drawSpace.drawLine(xLeftOffset+ plotWidth + middleoffsetX -15 , plotHeight + yTopOffset - i, \
				xLeftOffset+ plotWidth + middleoffsetX+15 , plotHeight + yTopOffset - i, color=dcolor)
			if i % 50 == 0:
				drawSpace.drawLine(xLeftOffset+ plotWidth +middleoffsetX+15 ,plotHeight + yTopOffset - i,  \
				xLeftOffset+ plotWidth +middleoffsetX+20,plotHeight + yTopOffset - i, color=pid.black)
				drawSpace.drawString("%1.1f" % -j , xLeftOffset+ plotWidth +middleoffsetX+25 ,plotHeight + yTopOffset - i+5, font = labelFont)
				j += 1
			i += 1
		drawSpace.drawLine(xLeftOffset+ plotWidth +middleoffsetX+15 ,plotHeight + yTopOffset - i+1,  \
			xLeftOffset+ plotWidth +middleoffsetX+20,plotHeight + yTopOffset - i+1, color=pid.black)	
		drawSpace.drawString("%1.1f" % -j , xLeftOffset+ plotWidth +middleoffsetX+25 ,plotHeight + yTopOffset - i+6, font = labelFont)
		labelFont=pid.Font(ttf="tahoma",size=14,bold=1)	
		drawSpace.drawString("Log(pValue)" , xLeftOffset+ plotWidth +middleoffsetX+60 ,plotHeight + yTopOffset - 100, font = labelFont, angle =90)
		
		labelFont=pid.Font(ttf="verdana",size=18,bold=0)
		drawSpace.drawString(XLabel, xLeftOffset + (plotWidth -drawSpace.stringWidth(XLabel,font=labelFont))/2.0, plotHeight + yTopOffset +40, color=pid.blue, font=labelFont)
		drawSpace.drawString(YLabel,xLeftOffset-60, plotHeight + yTopOffset-(plotHeight -drawSpace.stringWidth(YLabel,font=labelFont))/2.0, color=pid.blue, font=labelFont, angle =90)			
		"""
		drawSpace.addElement(drawSpaceMain)
		
		g= svg.group(id="dispBox", overflow="visible", 
			style="fill:white;stroke:orange;stroke-width:1;opacity:0.85;",
			transform="translate(%d,650)" % (cWidth-40-300), visibility="hidden")
		g.addElement(svg.rect(-80, -190, 300, 150, rx=10, ry=10))
		g.addElement(svg.line(21, -40, 58, -40, style="stroke:white;"))
		g.addElement(svg.polyline([[20, -40], [0, 0], [60, -40]]))
		g.addElement(svg.text(-60, -160, "ProbeSet ", style="&colorText; &allText; &subtitleText; &strokeText;", id="_probeset"))
		g.addElement(svg.text(-60, -125, "Marker ", style="&colorText; &allText; &subtitleText; &strokeText;", id="_marker"))

		drawSpace.addElement(g)

		canvasSVG.setSVG(drawSpace) #set the svg of the drawing to the svg
		return canvasSVG
			

	def drawGraph(self, canvas, data, cLength = 2500, offset= (80, 160, 60, 60), XLabel="QTL location (GMb)", YLabel="Gene location (GMb)"):
		xLeftOffset, xRightOffset, yTopOffset, yBottomOffset = offset
		plotWidth = canvas.size[0] - xLeftOffset - xRightOffset
		plotHeight = canvas.size[1] - yTopOffset - yBottomOffset
		
		#draw Frame
		canvas.drawRect(plotWidth+xLeftOffset, plotHeight + yTopOffset, xLeftOffset, yTopOffset)
		
		#draw Scale
		i = 100
		scaleFont=pid.Font(ttf="cour",size=11,bold=1)
		while i < cLength:
			yCoord = plotHeight + yTopOffset - plotHeight*i/cLength
			canvas.drawLine(xLeftOffset,yCoord ,xLeftOffset-5, yCoord)
			canvas.drawString("%d"% i,	xLeftOffset -40, yCoord +5,font=scaleFont)
			xCoord = xLeftOffset + plotWidth*i/cLength
			canvas.drawLine(xCoord, plotHeight + yTopOffset ,xCoord, plotHeight + yTopOffset+5)
			canvas.drawString("%d"% i,	xCoord -10, plotHeight + yTopOffset+15,font=scaleFont)
			i += 100

		#draw Points
		finecolors = Plot.colorSpectrum(300)
		finecolors.reverse()
		for item in data:
			_pvalue = item[-1]
			try:
				_idx = int((-math.log10(_pvalue))*300/6.0) # XZ, 09/11/2008: add module name
				_color = finecolors[_idx]
			except:
				_color = finecolors[-1]
				
			canvas.drawCross(xLeftOffset + plotWidth*item[0]/cLength, plotHeight + yTopOffset - plotHeight*item[1]/cLength, color=_color,size=3)
		
		#draw grid / always draw grid
		if 1: #self.grid == "on":
			for key in self.mouseChrLengthDict.keys():
				length = self.mouseChrLengthDict[key]
				if length != 0:
					yCoord = plotHeight + yTopOffset - plotHeight*length/cLength
					canvas.drawLine(xLeftOffset,yCoord ,xLeftOffset+plotWidth, yCoord, color=pid.lightgrey)
					xCoord = xLeftOffset + plotWidth*length/cLength
					canvas.drawLine(xCoord, plotHeight + yTopOffset ,xCoord, yTopOffset, color=pid.lightgrey)
		
		#draw spectrum
		i = 0
		j = 0
		middleoffsetX = 40
		labelFont=pid.Font(ttf="tahoma",size=12,bold=0)
		for dcolor in finecolors:
			canvas.drawLine(xLeftOffset+ plotWidth + middleoffsetX -15 , plotHeight + yTopOffset - i, \
				xLeftOffset+ plotWidth + middleoffsetX+15 , plotHeight + yTopOffset - i, color=dcolor)
			if i % 50 == 0:
				canvas.drawLine(xLeftOffset+ plotWidth +middleoffsetX+15 ,plotHeight + yTopOffset - i,  \
				xLeftOffset+ plotWidth +middleoffsetX+20,plotHeight + yTopOffset - i, color=pid.black)
				canvas.drawString("%1.1f" % -j , xLeftOffset+ plotWidth +middleoffsetX+25 ,plotHeight + yTopOffset - i+5, font = labelFont)
				j += 1
			i += 1
		canvas.drawLine(xLeftOffset+ plotWidth +middleoffsetX+15 ,plotHeight + yTopOffset - i+1,  \
			xLeftOffset+ plotWidth +middleoffsetX+20,plotHeight + yTopOffset - i+1, color=pid.black)	
		canvas.drawString("%1.1f" % -j , xLeftOffset+ plotWidth +middleoffsetX+25 ,plotHeight + yTopOffset - i+6, font = labelFont)
		labelFont=pid.Font(ttf="tahoma",size=14,bold=1)	
		canvas.drawString("Log(pValue)" , xLeftOffset+ plotWidth +middleoffsetX+60 ,plotHeight + yTopOffset - 100, font = labelFont, angle =90)
		
		labelFont=pid.Font(ttf="verdana",size=18,bold=0)
		canvas.drawString(XLabel, xLeftOffset + (plotWidth -canvas.stringWidth(XLabel,font=labelFont))/2.0, plotHeight + yTopOffset +40, color=pid.blue, font=labelFont)
		canvas.drawString(YLabel,xLeftOffset-60, plotHeight + yTopOffset-(plotHeight -canvas.stringWidth(YLabel,font=labelFont))/2.0, color=pid.blue, font=labelFont, angle =90)			
		return
	
	def readMouseGenome(self, RISet):
		ldict = {}
		lengths = []
		sum = 0
		#####################################
		# Retrieve Chr Length Information
		#####################################
		self.cursor.execute("""
			Select 
				Chr_Length.Name, Length from Chr_Length, InbredSet 
			where 
				Chr_Length.SpeciesId = InbredSet.SpeciesId AND
				InbredSet.Name = '%s'
			Order by 
				OrderId
			""" % RISet)
		lengths = self.cursor.fetchall()
		ldict[lengths[0][0]] = 0
		prev = lengths[0][1]/1000000.0
		sum += lengths[0][1]/1000000.0
		for item in lengths[1:]:
			ldict[item[0]] = prev
			prev += item[1]/1000000.0
			sum += item[1]/1000000.0
		return ldict, sum
	
	def cmppValue(self, A,B):
		if A[-1] < B[-1]:
			return -1
		elif A[-1] == B[-1]:
			return 0
		else:
			return 1
			
