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

from htmlgen import HTMLgen2 as HT
import direct

from utility import Plot
from base.templatePage import templatePage
from utility import webqtlUtil
from base import webqtlConfig

#########################################
#      PairPlotPage
#########################################
class PairPlotPage(templatePage):
	def __init__(self, fd):

		LRSFullThresh = 30
		LRSInteractThresh = 25
		maxPlotSize = 1000
		mainfmName = webqtlUtil.genRandStr("fm_")

		templatePage.__init__(self, fd)

		self.dict['title'] = 'Pair-Scan Plot'

		if not self.openMysql():
			return

		TD_LR = HT.TD(height=200,width="100%",bgColor='#eeeeee')
		vals = fd.formdata.getvalue('idata')
		vals = map(float,string.split(vals,','))
		strains = fd.formdata.getvalue('istrain')
		strains = string.split(strains,',')
		Chr_A = int(fd.formdata.getvalue('Chr_A'))
		Chr_B = int(fd.formdata.getvalue('Chr_B'))
		if len(vals) > webqtlConfig.KMININFORMATIVE:
			d = direct.exhaust(webqtlConfig.GENODIR, vals, strains, fd.RISet, Chr_A, Chr_B)#XZ, 08/14/2008: add module name webqtlConfig
			chrsInfo = d[2]
			longerChrLen = max(chrsInfo[Chr_A][0], chrsInfo[Chr_B][0])
			shorterChrlen = min(chrsInfo[Chr_A][0], chrsInfo[Chr_B][0])

			plotHeight = int(chrsInfo[Chr_B][0]*maxPlotSize/longerChrLen)
			plotWidth = int(chrsInfo[Chr_A][0]*maxPlotSize/longerChrLen)


			xLeftOffset = 200
			xRightOffset = 40
			yTopOffset = 40
			yBottomOffset = 200
			colorAreaWidth = 120

			canvasHeight = plotHeight + yTopOffset + yBottomOffset
			canvasWidth = plotWidth + xLeftOffset + xRightOffset + colorAreaWidth


			canvas = pid.PILCanvas(size=(canvasWidth,canvasHeight))
			plotScale = plotHeight/chrsInfo[Chr_B][0]

			rectInfo = d[1]
			finecolors = Plot.colorSpectrum(250)
			finecolors.reverse()
			#draw LRS Full
			for item in rectInfo:
				LRSFull,LRSInteract,LRSa,LRSb,chras,chram,chrae,chrbs,chrbm,chrbe,chra,chrb,flanka,flankb = item
				if Chr_A > Chr_B:
					colorIndex = int(LRSFull *250 /LRSFullThresh)
				else:
					colorIndex = int(LRSInteract *250 /LRSInteractThresh)
				if colorIndex >= 250:
					colorIndex = 249
				elif colorIndex < 0:
					colorIndex = 0
				dcolor = finecolors[colorIndex]
				if chra != chrb or (abs(chrbe - chrae) > 10 and abs(chrbs - chras) > 10):
					canvas.drawRect(xLeftOffset+chras*plotScale,yTopOffset+plotHeight- \
					chrbs*plotScale,xLeftOffset+chrae*plotScale,yTopOffset+plotHeight- \
					chrbe*plotScale,edgeColor=dcolor,fillColor=dcolor,edgeWidth = 0)
				elif chrbs >= chras:
					canvas.drawPolygon([(xLeftOffset+chras*plotScale,yTopOffset+plotHeight-chrbs*plotScale),\
					(xLeftOffset+chras*plotScale,yTopOffset+plotHeight-chrbe*plotScale),\
					(xLeftOffset+chrae*plotScale,yTopOffset+plotHeight-chrbe*plotScale)],\
					edgeColor=dcolor,fillColor=dcolor,edgeWidth = 0,closed =1)
				else:
					canvas.drawPolygon([(xLeftOffset+chras*plotScale,yTopOffset+plotHeight-chrbs*plotScale),\
					(xLeftOffset+chrae*plotScale,yTopOffset+plotHeight-chrbs*plotScale), \
					(xLeftOffset+chrae*plotScale,yTopOffset+plotHeight-chrbe*plotScale)], \
					edgeColor=dcolor,fillColor=dcolor,edgeWidth = 0,closed =1)

			labelFont=pid.Font(ttf="verdana",size=24,bold=0)
			chrName = "chromosome %s" % chrsInfo[Chr_A][1]
			canvas.drawString(chrName,xLeftOffset + (plotWidth - canvas.stringWidth(chrName,font=labelFont))/2,\
			yTopOffset+plotHeight+ 170,font=labelFont)
			chrName = "chromosome %s" % chrsInfo[Chr_B][1]
			canvas.drawString(chrName, 30, yTopOffset +(canvas.stringWidth(chrName,font=labelFont) + plotHeight)/2,\
			font=labelFont, angle = 90)
			if Chr_A == Chr_B:
				infoStr = "minimum distance = 10 cM"
				infoStrWidth = canvas.stringWidth(infoStr,font=labelFont)
				canvas.drawString(infoStr, xLeftOffset + (plotWidth-infoStrWidth*0.707)/2, yTopOffset + \
				(plotHeight+infoStrWidth*0.707)/2,font=labelFont, angle = 45, color=pid.red)

			labelFont=pid.Font(ttf="verdana",size=12,bold=0)
			gifmap = HT.Map(name='markerMap')

			lineColor = pid.lightblue
			#draw ChrA Loci
			ChrAInfo = d[3]
			preLpos = -1
			i = 0
			for item in ChrAInfo:
				Lname,Lpos = item
				if Lpos != preLpos:
					i += 1
				preLpos = Lpos
			stepA = float(plotWidth)/i

			offsetA = -stepA
			LRectWidth = 10
			LRectHeight = 3
			i = 0
			preLpos = -1
			for item in ChrAInfo:
				Lname,Lpos = item
				if Lpos != preLpos:
					offsetA += stepA
					differ = 1
				else:
					differ = 0
				preLpos = Lpos
				Lpos *= plotScale
				Zorder = i % 5
				"""
				LStrWidth = canvas.stringWidth(Lname,font=labelFont)
				canvas.drawString(Lname,xLeftOffset+offsetA+4,yTopOffset+plotHeight+140,\
				font=labelFont,color=pid.blue,angle=90)
				canvas.drawLine(xLeftOffset+Lpos,yTopOffset+plotHeight,xLeftOffset+offsetA,\
				yTopOffset+plotHeight+25,color=lineColor)
				canvas.drawLine(xLeftOffset+offsetA,yTopOffset+plotHeight+25,xLeftOffset+offsetA,\
				yTopOffset+plotHeight+140-LStrWidth,color=lineColor)
				COORDS="%d,%d,%d,%d"%(xLeftOffset+offsetA+4,yTopOffset+plotHeight+140,\
				xLeftOffset+offsetA-6,yTopOffset+plotHeight+140-LStrWidth)
				"""
				if differ:
					canvas.drawLine(xLeftOffset+Lpos,yTopOffset+plotHeight,xLeftOffset+offsetA,\
					yTopOffset+plotHeight+25,color=lineColor)
					canvas.drawLine(xLeftOffset+offsetA,yTopOffset+plotHeight+25,xLeftOffset+offsetA,\
					yTopOffset+plotHeight+80+Zorder*(LRectWidth+3),color=lineColor)
					rectColor = pid.orange
				else:
					canvas.drawLine(xLeftOffset+offsetA, yTopOffset+plotHeight+80+Zorder*(LRectWidth+3)-3,\
					xLeftOffset+offsetA, yTopOffset+plotHeight+80+Zorder*(LRectWidth+3),color=lineColor)
					rectColor = pid.deeppink
				canvas.drawRect(xLeftOffset+offsetA, yTopOffset+plotHeight+80+Zorder*(LRectWidth+3),\
					xLeftOffset+offsetA-LRectHeight,yTopOffset+plotHeight+80+Zorder*(LRectWidth+3)+LRectWidth,\
					edgeColor=rectColor,fillColor=rectColor,edgeWidth = 0)
				COORDS="%d,%d,%d,%d"%(xLeftOffset+offsetA, yTopOffset+plotHeight+80+Zorder*(LRectWidth+3),\
					xLeftOffset+offsetA-LRectHeight,yTopOffset+plotHeight+80+Zorder*(LRectWidth+3)+LRectWidth)
				HREF="javascript:showTrait('%s','%s');" % (mainfmName, Lname)
				Areas=HT.Area(shape='rect',coords=COORDS,href=HREF, title="Locus : " + Lname)
				gifmap.areas.append(Areas)
				i += 1
				#print (i , offsetA, Lname, Lpos, preLpos)
				#print "<BR>"

			#draw ChrB Loci
			ChrBInfo = d[4]
			preLpos = -1
			i = 0
			for item in ChrBInfo:
				Lname,Lpos = item
				if Lpos != preLpos:
					i += 1
				preLpos = Lpos
			stepB = float(plotHeight)/i

			offsetB = -stepB
			LRectWidth = 10
			LRectHeight = 3
			i = 0
			preLpos = -1
			for item in ChrBInfo:
				Lname,Lpos = item
				if Lpos != preLpos:
					offsetB += stepB
					differ = 1
				else:
					differ = 0
				preLpos = Lpos
				Lpos *= plotScale
				Zorder = i % 5
				Lname,Lpos = item
				Lpos *= plotScale
				"""
				LStrWidth = canvas.stringWidth(Lname,font=labelFont)
				canvas.drawString(Lname, 45,yTopOffset+plotHeight-offsetB+4,font=labelFont,color=pid.blue)
				canvas.drawLine(45+LStrWidth,yTopOffset+plotHeight-offsetB,xLeftOffset-25,\
				yTopOffset+plotHeight-offsetB,color=lineColor)
				canvas.drawLine(xLeftOffset-25,yTopOffset+plotHeight-offsetB,xLeftOffset,\
				yTopOffset+plotHeight-Lpos,color=lineColor)
				COORDS = "%d,%d,%d,%d" %(45,yTopOffset+plotHeight-offsetB+4,45+LStrWidth,\
				yTopOffset+plotHeight-offsetB-6)
				"""
				if differ:
					canvas.drawLine(xLeftOffset,yTopOffset+plotHeight-Lpos, xLeftOffset-25,\
					yTopOffset+plotHeight-offsetB,color=lineColor)
					canvas.drawLine(xLeftOffset -25, yTopOffset+plotHeight-offsetB, \
					xLeftOffset-80 -Zorder*(LRectWidth+3),yTopOffset+plotHeight-offsetB, color=lineColor)
					rectColor = pid.orange
				else:
					canvas.drawLine(xLeftOffset -80 -Zorder*(LRectWidth+3)+3, yTopOffset+plotHeight-offsetB, \
					xLeftOffset-80 -Zorder*(LRectWidth+3),yTopOffset+plotHeight-offsetB, color=lineColor)
					rectColor = pid.deeppink
				HREF = "javascript:showTrait('%s','%s');" % (mainfmName, Lname)
				canvas.drawRect(xLeftOffset-80 -Zorder*(LRectWidth+3),yTopOffset+plotHeight-offsetB,\
					xLeftOffset-80 -Zorder*(LRectWidth+3)-LRectWidth,yTopOffset+plotHeight-offsetB +LRectHeight,\
					edgeColor=rectColor,fillColor=rectColor,edgeWidth = 0)
				COORDS="%d,%d,%d,%d"%(xLeftOffset-80 -Zorder*(LRectWidth+3),yTopOffset+plotHeight-offsetB,\
					xLeftOffset-80 -Zorder*(LRectWidth+3)-LRectWidth,yTopOffset+plotHeight-offsetB +LRectHeight)
				Areas=HT.Area(shape='rect',coords=COORDS,href=HREF, title="Locus : " + Lname)
				gifmap.areas.append(Areas)
				i += 1

			canvas.drawRect(xLeftOffset, yTopOffset, xLeftOffset+plotWidth, yTopOffset+plotHeight,edgeColor=pid.black)

			#draw spectrum
			i = 0
			labelFont=pid.Font(ttf="tahoma",size=14,bold=0)
			middleoffsetX = 80
			for dcolor in finecolors:
				canvas.drawLine(xLeftOffset+ plotWidth +middleoffsetX-15 , plotHeight + yTopOffset - i, \
				xLeftOffset+ plotWidth +middleoffsetX+15 , plotHeight + yTopOffset - i, color=dcolor)
				if i % 50 == 0:
					if Chr_A >= Chr_B:
						canvas.drawLine(xLeftOffset+ plotWidth +middleoffsetX+15 ,plotHeight + yTopOffset - i, \
						xLeftOffset+ plotWidth +middleoffsetX+20,plotHeight + yTopOffset - i, color=pid.black)
						canvas.drawString('%d' % int(LRSFullThresh*i/250.0),xLeftOffset+ plotWidth +middleoffsetX+22,\
						plotHeight + yTopOffset - i +5, font = labelFont,color=pid.black)
					if Chr_A <= Chr_B:
						canvas.drawLine(xLeftOffset+ plotWidth +middleoffsetX-15 ,plotHeight + yTopOffset - i, \
						xLeftOffset+ plotWidth +middleoffsetX-20,plotHeight + yTopOffset - i, color=pid.black)
						canvas.drawString('%d' % int(LRSInteractThresh*i/250.0),xLeftOffset+plotWidth+middleoffsetX-40,\
						plotHeight + yTopOffset - i +5, font = labelFont,color=pid.black)
				i += 1
			#draw spectrum label
			labelFont2=pid.Font(ttf="verdana",size=20,bold=0)
			if i % 50 == 0:
				i -= 1
				if Chr_A >= Chr_B:
					canvas.drawLine(xLeftOffset+ plotWidth +middleoffsetX+15 ,plotHeight + yTopOffset - i, \
					xLeftOffset+ plotWidth +middleoffsetX+20,plotHeight + yTopOffset - i, color=pid.black)
					canvas.drawString('%d' % int(LRSFullThresh*(i+1)/250.0),xLeftOffset+ plotWidth +middleoffsetX+22,\
					plotHeight + yTopOffset - i +5, font = labelFont,color=pid.black)
					canvas.drawString('LRS Full',xLeftOffset+ plotWidth +middleoffsetX+50,plotHeight + yTopOffset, \
					font = labelFont2,color=pid.dimgray,angle=90)
				if Chr_A <= Chr_B:
					canvas.drawLine(xLeftOffset+ plotWidth +middleoffsetX-15 ,plotHeight + yTopOffset - i, \
					xLeftOffset+ plotWidth +middleoffsetX-20,plotHeight + yTopOffset - i, color=pid.black)
					canvas.drawString('%d' % int(LRSInteractThresh*(i+1)/250.0),xLeftOffset+ plotWidth+middleoffsetX-40,\
					plotHeight + yTopOffset - i +5, font = labelFont,color=pid.black)
					canvas.drawString('LRS Interaction',xLeftOffset+ plotWidth +middleoffsetX-50,\
					plotHeight + yTopOffset, font = labelFont2,color=pid.dimgray,angle=90)

			filename= webqtlUtil.genRandStr("Pair_")
			canvas.save(webqtlConfig.IMGDIR+filename, format='png')
			img2=HT.Image('/image/'+filename+'.png',border=0,usemap='#markerMap')

			main_title = HT.Paragraph("Pair-Scan Results: Chromosome Pair")
			main_title.__setattr__("class","title")
			form = HT.Form(cgi = os.path.join(webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE), enctype='multipart/form-data', \
			name=mainfmName, submit=HT.Input(type='hidden'))
			hddn = {'FormID':'showDatabase','ProbeSetID':'_','database':fd.RISet+"Geno",'CellID':'_','RISet':fd.RISet, 'incparentsf1':'on'}
			if fd.incparentsf1:
				hddn['incparentsf1']='ON'
			for key in hddn.keys():
				form.append(HT.Input(name=key, value=hddn[key], type='hidden'))
			form.append(img2,gifmap)
			TD_LR.append(main_title, HT.Center(form), HT.P())
		else:
			heading = "Direct Plot"
			detail = ['Fewer than %d strain data were entered for %s data set. No statitical analysis has been attempted.'\
			 % (webqtlConfig.KMININFORMATIVE, fd.RISet)]
			self.error(heading=heading,detail=detail)
			return
		self.dict['body'] = str(TD_LR)


