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
from htmlgen import HTMLgen2 as HT

from utility import Plot
from base.templatePage import templatePage
from utility import webqtlUtil
from base import webqtlConfig

#########################################
#      Category Graph Page
#########################################
class CategoryGraphPage(templatePage):
	def __init__(self, fd):

		LRSFullThresh = 30
		LRSInteractThresh = 25
		maxPlotSize = 800
		mainfmName = webqtlUtil.genRandStr("fm_")

		templatePage.__init__(self, fd)

		if not fd.genotype:
			fd.readData()

		##Remove F1 and Parents
		fd.genotype = fd.genotype_1

		plotType = fd.formdata.getvalue('plotType')
		self.dict['title'] = '%s Plot' % plotType
		main_title = HT.Paragraph("%s Plot" % plotType)
		main_title.__setattr__("class","title")

		interval1 = fd.formdata.getvalue('interval1')
		interval2 = fd.formdata.getvalue('interval2')

		flanka1, flanka2, chram = string.split(interval1)
		flankb1, flankb2, chrbm = string.split(interval2)

		traitValues = string.split(fd.formdata.getvalue('traitValues'), ',')
		traitValues = map(webqtlUtil.StringAsFloat, traitValues)
		traitStrains = string.split(fd.formdata.getvalue('traitStrains'), ',')

		flankaGeno = []
		flankbGeno = []

		for chr in fd.genotype:
			for locus in chr:
				if locus.name in (flanka1, flankb1):
					if locus.name == flanka1:
						flankaGeno = locus.genotype[:]
					else:
						flankbGeno = locus.genotype[:]
			if flankaGeno and flankbGeno:
				break

		flankaDict = {}
		flankbDict = {}
		for i in range(len(fd.genotype.prgy)):
			flankaDict[fd.genotype.prgy[i]] = flankaGeno[i]
			flankbDict[fd.genotype.prgy[i]] = flankbGeno[i]

		BB = []
		BD = []
		DB = []
		DD = []

		iValues = []
		for i in range(len(traitValues)):
			if traitValues[i] != None:
				iValues.append(traitValues[i])
				thisstrain = traitStrains[i]
				try:
					a1 = flankaDict[thisstrain]
					b1 = flankbDict[thisstrain]
				except:
					continue
				if a1 == -1.0:
					if b1 == -1.0:
						BB.append((thisstrain, traitValues[i]))
					elif b1 == 1.0:
						BD.append((thisstrain, traitValues[i]))
				elif a1 == 1.0:
					if b1 == -1.0:
						DB.append((thisstrain, traitValues[i]))
					elif b1 == 1.0:
						DD.append((thisstrain, traitValues[i]))
				else:
					pass

		#print BB, BD, DB, DD, max(iValues), min(iValues)

		plotHeight = 400
		plotWidth = 600
		xLeftOffset = 60
		xRightOffset = 40
		yTopOffset = 40
		yBottomOffset = 60

		canvasHeight = plotHeight + yTopOffset + yBottomOffset
		canvasWidth = plotWidth + xLeftOffset + xRightOffset
		canvas = pid.PILCanvas(size=(canvasWidth,canvasHeight))
		XXX = [('Mat/Mat', BB), ('Mat/Pat', BD), ('Pat/Mat', DB), ('Pat/Pat', DD)]
		XLabel = "Interval 1 / Interval 2"

		if plotType == "Box":
			Plot.plotBoxPlot(canvas, XXX, offset=(xLeftOffset, xRightOffset, yTopOffset, yBottomOffset), XLabel = XLabel)
		else:
			#Could be a separate function, but seems no other uses
			max_Y = max(iValues)
			min_Y = min(iValues)
			scaleY = Plot.detScale(min_Y, max_Y)
			Yll = scaleY[0]
			Yur = scaleY[1]
			nStep = scaleY[2]
			stepY = (Yur - Yll)/nStep
			stepYPixel = plotHeight/(nStep)
			canvas.drawRect(plotWidth+xLeftOffset, plotHeight + yTopOffset, xLeftOffset, yTopOffset)

			##draw Y Scale
			YYY = Yll
			YCoord = plotHeight + yTopOffset
			scaleFont=pid.Font(ttf="cour",size=11,bold=1)
			for i in range(nStep+1):
				strY = Plot.cformat(d=YYY, rank=0)
				YCoord = max(YCoord, yTopOffset)
				canvas.drawLine(xLeftOffset,YCoord,xLeftOffset-5,YCoord)
				canvas.drawString(strY,	xLeftOffset -30,YCoord +5,font=scaleFont)
				YYY += stepY
				YCoord -= stepYPixel


			##draw X Scale
			stepX = plotWidth/len(XXX)
			XCoord = xLeftOffset + 0.5*stepX
			YCoord = plotHeight + yTopOffset
			scaleFont = pid.Font(ttf="tahoma",size=12,bold=0)
			labelFont = pid.Font(ttf="tahoma",size=13,bold=0)
			for item in XXX:
				itemname, itemvalue = item
				canvas.drawLine(XCoord, YCoord,XCoord, YCoord+5, color=pid.black)
				canvas.drawString(itemname, XCoord - canvas.stringWidth(itemname,font=labelFont)/2.0,YCoord +20,font=labelFont)
				itemvalue.sort(webqtlUtil.cmpOrder2)
				j = 0
				for item2 in itemvalue:
					tstrain, tvalue = item2
					canvas.drawCross(XCoord, plotHeight + yTopOffset - (tvalue-Yll)*plotHeight/(Yur - Yll), color=pid.red,size=5)
					if j % 2 == 0:
						canvas.drawString(tstrain, XCoord+5, plotHeight + yTopOffset - \
						(tvalue-Yll)*plotHeight/(Yur - Yll) +5, font=scaleFont, color=pid.blue)
					else:
						canvas.drawString(tstrain, XCoord-canvas.stringWidth(tstrain,font=scaleFont)-5, \
						plotHeight + yTopOffset - (tvalue-Yll)*plotHeight/(Yur - Yll) +5, font=scaleFont, color=pid.blue)
					j += 1
				XCoord += stepX


			labelFont=pid.Font(ttf="verdana",size=18,bold=0)
			canvas.drawString(XLabel, xLeftOffset + (plotWidth -canvas.stringWidth(XLabel,font=labelFont))/2.0, YCoord +40, font=labelFont)
			canvas.drawString("Value",xLeftOffset-40,  YCoord-(plotHeight -canvas.stringWidth("Value",font=labelFont))/2.0, font=labelFont, angle =90)


		filename= webqtlUtil.genRandStr("Cate_")
		canvas.save(webqtlConfig.IMGDIR+filename, format='gif')
		img=HT.Image('/image/'+filename+'.gif',border=0)

		TD_LR = HT.TD(height=200,width="100%",bgColor='#eeeeee',valign='top')
		TD_LR.append(main_title, HT.Center(img))#, traitValues , len(traitValues), traitStrains, len(traitStrains), len(fd.genotype.prgy))
		#TD_LR.append(main_title, HT.BR(), flanka1, flanka2, chram, HT.BR(), flankb1, flankb2, chrbm)
		self.dict['body'] = str(TD_LR)



