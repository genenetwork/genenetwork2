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
from math import *
import os

import direct
from htmlgen import HTMLgen2 as HT

from utility import Plot
from base.webqtlTrait import webqtlTrait
from base.templatePage import templatePage
from utility import webqtlUtil
from base import webqtlConfig



class DirectPlotPage(templatePage):
	def __init__(self, fd):

		LRSFullThresh = 30
		LRSInteractThresh = 25

		templatePage.__init__(self, fd)

		if not fd.genotype:
			fd.readData()

		incVars = 0
		_genotype = fd.genotype_1
		_strains, _vals, _vars, N = fd.informativeStrains(_genotype.prgy, incVars)

		self.dict['title'] = 'Pair-Scan Plot'
		if not self.openMysql():
			return

		iPermuCheck = fd.formdata.getvalue('directPermuCheckbox')

		try:
			graphtype = int(fd.formdata.getvalue('graphtype'))
		except:
			graphtype = 1
		try:
			graphsort = int(fd.formdata.getvalue('graphSort'))
		except:
			graphsort = 1
		try:
			returnIntervalPairNum = int(fd.formdata.getvalue('pairScanReturn'))
		except:
			returnIntervalPairNum = 50

		pairIntro = HT.Blockquote("The graph below displays pair-scan results for the trait ",HT.Strong(" %s" % fd.identification))
		if not graphsort:
			tblIntro = HT.Blockquote('This table lists LRS scores for the top %d pairs of intervals (Interval 1 on the left and Interval 2 on the right). Pairs are sorted by the "LRS Full" column. Both intervals are defined by proximal and distal markers that flank the single best position.' % returnIntervalPairNum)
		else:
			tblIntro = HT.Blockquote('This table lists LRS scores for the top %d pairs of intervals (Interval 1 on the left and Interval 2 on the right). Pairs are sorted by the "LRS Interaction" column. Both intervals are defined by proximal and distal markers that flank the single best position.' % returnIntervalPairNum)

		try:
			thisTrait = webqtlTrait(fullname=fd.formdata.getvalue("fullname"), cursor=self.cursor)
			pairIntro.append(' from the database ' , thisTrait.db.genHTML())
		except:
			pass

		pairIntro.append('. The upper left half of the plot highlights any epistatic interactions (corresponding to the column labeled "LRS Interact"). In contrast, the lower right half provides a summary of LRS of the full model, representing cumulative effects of linear and non-linear terms (column labeled "LRS Full"). The WebQTL implementation of the scan for 2-locus epistatic interactions is based on the DIRECT global optimization algorithm developed by ',HT.Href(text ="Ljungberg",url='http://user.it.uu.se/~kl/qtl_software.html',target="_blank", Class = "fs14 fwn"),', Holmgren, and Carlborg (',HT.Href(text = "2004",url='http://bioinformatics.oupjournals.org/cgi/content/abstract/bth175?ijkey=21Pp0pgOuBL6Q&keytype=ref', Class = "fs14 fwn"),').')

		main_title = HT.Paragraph("Pair-Scan Results: An Analysis of Epistatic Interactions")
		main_title.__setattr__("class","title")

		subtitle1 = HT.Paragraph("Pair-Scan Graph")
		subtitle3 = HT.Paragraph("Pair-Scan Top LRS")
		subtitle1.__setattr__("class","subtitle")
		subtitle3.__setattr__("class","subtitle")

		self.identification = "unnamed trait"
		if fd.identification:
			self.identification = fd.identification
			self.dict['title'] = self.identification + ' / '+self.dict['title']

		#####################################
		#
		# Remove the Parents & F1 data
		#
		#####################################

		if _vals:
			if len(_vals) > webqtlConfig.KMININFORMATIVE:
				ResultFull = []
				ResultInteract = []
				ResultAdd = []

				#permutation test
				subtitle2 = ''
				permuTbl = ''
				permuIntro = ''
				if iPermuCheck:
					subtitle2 = HT.Paragraph("Pair-Scan Permutation Results")
					subtitle2.__setattr__("class","subtitle")
					permuIntro = HT.Blockquote("Phenotypes were randomly permuted 500 times among strains or individuals and reanalyzed using the pair-scan algorithm. We extracted the single highest LRS for the full model for each of these permuted data sets. The histograms of these highest LRS values provide an empirical way to estimate the probability of obtaining an LRS above suggestive or significant thresholds.")

					prtmuTblIntro1 = HT.Paragraph("The following table gives threshold values for Suggestive (P=0.63) and Significant associations (P=0.05) defined by Lander & Kruglyak and for the slightly more stringent P=0.01 level. (The Highly Significant level of Lander & Kruglyak corresponds to P=0.001 and cannot be estimated with 500 permutations.)")
					prtmuTblIntro2 = HT.Paragraph("If the full model exceeds the permutation-based Significant threshold, then different models for those locations can be tested by conventional chi-square tests at P<0.01. Interaction is significant if LRS Interact exceeds 6.64 for RI strains or 13.28 for an F2. If interaction is not significant, the two-QTL model is better than a one-QTL model if LRS Additive exceeds LRS 1 or LRS 2 by 6.64 for RI strains or 9.21 for an F2.")
					ResultFull, ResultInteract, ResultAdd = direct.permu(webqtlConfig.GENODIR, _vals, _strains, fd.RISet, 500) #XZ, 08/14/2008: add module name webqtlConfig
					ResultFull.sort()
					ResultInteract.sort()
					ResultAdd.sort()
					nPermuResult = len(ResultFull)
					# draw Histogram
					cFull = pid.PILCanvas(size=(400,300))
					Plot.plotBar(cFull, ResultFull,XLabel='LRS',YLabel='Frequency',title=' Histogram of LRS Full')
					#plotBar(cFull,10,10,390,290,ResultFull,XLabel='LRS',YLabel='Frequency',title=' Histogram of LRS Full')
					filename= webqtlUtil.genRandStr("Pair_")
					cFull.save(webqtlConfig.IMGDIR+filename, format='gif')
					imgFull=HT.Image('/image/'+filename+'.gif',border=0,alt='Histogram of LRS Full')


					superPermuTbl = HT.TableLite(border=0, cellspacing=0, cellpadding=0,bgcolor ='#999999')
					permuTbl2 = HT.TableLite(border=0, cellspacing= 1, cellpadding=5)
					permuTbl2.append(HT.TR(HT.TD(HT.Font('LRS', color = '#FFFFFF')), HT.TD(HT.Font('p = 0.63', color = '#FFFFFF'), width = 150, align='Center'), HT.TD(HT.Font('p = 0.05', color = '#FFFFFF'), width = 150, align='Center'), HT.TD(HT.Font('p = 0.01', color = '#FFFFFF'), width = 150, align='Center'),bgColor='royalblue'))
					permuTbl2.append(HT.TR(HT.TD('Full'), HT.TD('%2.1f' % ResultFull[int(nPermuResult*0.37 -1)], align="Center"), HT.TD('%2.1f' % ResultFull[int(nPermuResult*0.95 -1)], align="Center"), HT.TD('%2.1f' % ResultFull[int(nPermuResult*0.99 -1)], align="Center"),bgColor="#eeeeee"))
					superPermuTbl.append(HT.TD(HT.TD(permuTbl2)))

					permuTbl1 = HT.TableLite(border=0, cellspacing= 0, cellpadding=5,width='100%')
					permuTbl1.append(HT.TR(HT.TD(imgFull, align="Center", width = 410), HT.TD(prtmuTblIntro1, superPermuTbl, prtmuTblIntro2, width = 490)))

					permuTbl = HT.Center(permuTbl1, HT.P())

					#permuTbl.append(HT.TR(HT.TD(HT.BR(), 'LRS Full  = %2.1f, ' % ResultFull[int(nPermuResult*0.37 -1)], 'LRS Full  = %2.1f, ' % ResultFull[int(nPermuResult*0.95 -1)], 'LRS Full highly significant (p=0.001) = %2.1f, ' % ResultFull[int(nPermuResult*0.999 -1)] , HT.BR(), 'LRS Interact suggestive (p=0.63) = %2.1f, ' % ResultInteract[int(nPermuResult*0.37 -1)], 'LRS Interact significant (p=0.05) = %2.1f, ' % ResultInteract[int(nPermuResult*0.95 -1)], 'LRS Interact  = %2.1f, ' % ResultInteract[int(nPermuResult*0.999 -1)] , HT.BR(),'LRS Additive suggestive (p=0.63) = %2.1f, ' % ResultAdd[int(nPermuResult*0.37 -1)], 'LRS Additive significant (p=0.05) = %2.1f, ' % ResultAdd[int(nPermuResult*0.95 -1)], 'LRS Additive highly significant (p=0.001) = %2.1f, ' % ResultAdd[int(nPermuResult*0.999 -1)], HT.BR(), 'Total number of permutation is %d' % nPermuResult, HT.BR(), HT.BR(),colspan=2)))
					#tblIntro.append(HT.P(), HT.Center(permuTbl))

				#print vals, strains, fd.RISet
				d = direct.direct(webqtlConfig.GENODIR, _vals, _strains, fd.RISet, 8000)#XZ, 08/14/2008: add module name webqtlConfig
				chrsInfo = d[2]
				sum = 0
				offsets = [0]
				i = 0
				for item in chrsInfo:
					if i > 0:
						offsets.append(sum)
					sum += item[0]
					i += 1
				offsets.append(sum)
				#print sum,offset,d[2]
				canvasWidth = 880
				canvasHeight = 880
				if graphtype:
					colorAreaWidth = 230
				else:
					colorAreaWidth = 0
				c = pid.PILCanvas(size=(canvasWidth + colorAreaWidth ,canvasHeight))
				xoffset = 40
				yoffset = 40
				width = canvasWidth - xoffset*2
				height = canvasHeight - yoffset*2

				xscale = width/sum
				yscale = height/sum

				rectInfo = d[1]
				rectInfo.sort(webqtlUtil.cmpLRSFull)

				finecolors = Plot.colorSpectrum(250)
				finecolors.reverse()
				regLRS = [0]*height
				#draw LRS Full

				for item in rectInfo:
					LRSFull,LRSInteract,LRSa,LRSb,chras,chram,chrae,chrbs,chrbm,chrbe,chra,chrb,flanka,flankb = item
					if LRSFull > 30:
						dcolor = pid.red
					elif LRSFull > 20:
						dcolor = pid.orange
					elif LRSFull > 10:
						dcolor = pid.olivedrab
					elif LRSFull > 0:
						dcolor = pid.grey
					else:
						LRSFull = 0
						dcolor = pid.grey

					chras += offsets[chra]
					chram += offsets[chra]
					chrae += offsets[chra]
					chrbs += offsets[chrb]
					chrbm += offsets[chrb]
					chrbe += offsets[chrb]

					regLRSD = int(chram*yscale)
					if regLRS[regLRSD] < LRSa:
						regLRS[regLRSD] = LRSa
					regLRSD = int(chrbm*yscale)
					if regLRS[regLRSD] < LRSb:
						regLRS[regLRSD] = LRSb

					if graphtype:
						colorIndex = int(LRSFull *250 /LRSFullThresh)
						if colorIndex >= 250:
							colorIndex = 249
						dcolor = finecolors[colorIndex]
						if chra != chrb or ((chrbe - chrae) > 10 and (chrbs - chras) > 10):
							c.drawRect(xoffset+chrbs*xscale,yoffset+height-chras*yscale,xoffset+chrbe*xscale,yoffset+height-chrae*yscale,edgeColor=dcolor,fillColor=dcolor,edgeWidth = 0)
						else:
							c.drawPolygon([(xoffset+chrbs*xscale,yoffset+height-chras*yscale),(xoffset+chrbe*xscale,yoffset+height-chras*yscale),(xoffset+chrbe*xscale,yoffset+height-chrae*yscale)],edgeColor=dcolor,fillColor=dcolor,edgeWidth = 0,closed =1)
					else:
						c.drawCross(xoffset+chrbm*xscale,yoffset+height-chram*yscale,color=dcolor,size=2)
				#draw Marker Regression LRS
				if graphtype:
					"""
					maxLRS = max(regLRS)
					pts = []
					i = 0
					for item in regLRS:
						pts.append((xoffset+width+35+item*50/maxLRS, yoffset+height-i))
						i += 1
					c.drawPolygon(pts,edgeColor=pid.blue,edgeWidth=1,closed=0)
					"""
					LRS1Thresh = 16.2
					i = 0
					for item in regLRS:
						colorIndex = int(item *250 /LRS1Thresh)
						if colorIndex >= 250:
							colorIndex = 249
						dcolor = finecolors[colorIndex]
						c.drawLine(xoffset+width+35,yoffset+height-i,xoffset+width+55,yoffset+height-i,color=dcolor)
						i += 1
					labelFont=pid.Font(ttf="arial",size=20,bold=0)
					c.drawString('Single Locus Regression',xoffset+width+90,yoffset+height, font = labelFont,color=pid.dimgray,angle=90)
				#draw LRS Interact
				rectInfo.sort(webqtlUtil.cmpLRSInteract)
				for item in rectInfo:
					LRSFull,LRSInteract,LRSa,LRSb,chras,chram,chrae,chrbs,chrbm,chrbe,chra,chrb,flanka,flankb = item
					if LRSInteract > 30:
						dcolor = pid.red
					elif LRSInteract > 20:
						dcolor = pid.orange
					elif LRSInteract > 10:
						dcolor = pid.olivedrab
					elif LRSInteract > 0:
						dcolor = pid.grey
					else:
						LRSInteract = 0
						dcolor = pid.grey
					chras += offsets[chra]
					chram += offsets[chra]
					chrae += offsets[chra]
					chrbs += offsets[chrb]
					chrbm += offsets[chrb]
					chrbe += offsets[chrb]
					if graphtype:
						colorIndex = int(LRSInteract *250 / LRSInteractThresh )
						if colorIndex >= 250:
							colorIndex = 249
						dcolor = finecolors[colorIndex]
						if chra != chrb or ((chrbe - chrae) > 10 and (chrbs - chras) > 10):
							c.drawRect(xoffset+chras*xscale,yoffset+height-chrbs*yscale,xoffset+chrae*xscale,yoffset+height-chrbe*yscale,edgeColor=dcolor,fillColor=dcolor,edgeWidth = 0)
						else:
							c.drawPolygon([(xoffset+chras*xscale,yoffset+height-chrbs*yscale),(xoffset+chras*xscale,yoffset+height-chrbe*yscale),(xoffset+chrae*xscale,yoffset+height-chrbe*yscale)],edgeColor=dcolor,fillColor=dcolor,edgeWidth = 0,closed =1)
					else:
						c.drawCross(xoffset+chram*xscale,yoffset+height-chrbm*yscale,color=dcolor,size=2)
				#draw chromosomes label
				labelFont=pid.Font(ttf="tahoma",size=24,bold=0)
				i = 0
				for item in chrsInfo:
					strWidth = c.stringWidth(item[1],font=labelFont)
					c.drawString(item[1],xoffset+offsets[i]*xscale +(item[0]*xscale-strWidth)/2,canvasHeight -15,font = labelFont,color=pid.dimgray)
					c.drawString(item[1],xoffset+offsets[i]*xscale +(item[0]*xscale-strWidth)/2,yoffset-10,font = labelFont,color=pid.dimgray)
					c.drawString(item[1],xoffset-strWidth-5,yoffset+height - offsets[i]*yscale -(item[0]*yscale-22)/2,font = labelFont,color=pid.dimgray)
					c.drawString(item[1],canvasWidth-xoffset+5,yoffset+height - offsets[i]*yscale -(item[0]*yscale-22)/2,font = labelFont,color=pid.dimgray)
					i += 1


				c.drawRect(xoffset,yoffset,xoffset+width,yoffset+height)
				for item in offsets:
					c.drawLine(xoffset,yoffset+height-item*yscale,xoffset+width,yoffset+height-item*yscale)
					c.drawLine(xoffset+item*xscale,yoffset,xoffset+item*xscale,yoffset+height)

				#draw pngMap
				pngMap = HT.Map(name='pairPlotMap')
				#print offsets, len(offsets)
				for i in range(len(offsets)-1):
					for j in range(len(offsets)-1):
						COORDS = "%d,%d,%d,%d" %(xoffset+offsets[i]*xscale, yoffset+height-offsets[j+1]*yscale, xoffset+offsets[i+1]*xscale, yoffset+height-offsets[j]*yscale)
						HREF = "javascript:showPairPlot(%d,%d);" % (i,j)
						Areas = HT.Area(shape='rect',coords=COORDS,href=HREF)
						pngMap.areas.append(Areas)

				#draw spectrum
				if graphtype:
					i = 0
					labelFont=pid.Font(ttf="tahoma",size=14,bold=0)
					middleoffsetX = 180
					for dcolor in finecolors:
						if i % 50 == 0:
							c.drawLine(xoffset+ width +middleoffsetX-15 , height + yoffset -i, xoffset+ width +middleoffsetX-20,height + yoffset -i, color=pid.black)
							c.drawString('%d' % int(LRSInteractThresh*i/250.0),xoffset+ width+ middleoffsetX-40,height + yoffset -i +5, font = labelFont,color=pid.black)
							c.drawLine(xoffset+ width +middleoffsetX+15 , height + yoffset -i, xoffset+ width +middleoffsetX+20 ,height + yoffset -i, color=pid.black)
							c.drawString('%d' % int(LRSFullThresh*i/250.0),xoffset+ width + middleoffsetX+25,height + yoffset -i +5, font = labelFont,color=pid.black)
						c.drawLine(xoffset+ width +middleoffsetX-15 , height + yoffset -i, xoffset+ width +middleoffsetX+15 ,height + yoffset -i, color=dcolor)
						i += 1

					if i % 50 == 0:
						i -= 1
						c.drawLine(xoffset+ width +middleoffsetX-15 , height + yoffset -i, xoffset+ width +middleoffsetX-20,height + yoffset -i, color=pid.black)
						c.drawString('%d' % ceil(LRSInteractThresh*i/250.0),xoffset+ width + middleoffsetX-40,height + yoffset -i +5, font = labelFont,color=pid.black)
						c.drawLine(xoffset+ width +middleoffsetX+15 , height + yoffset -i, xoffset+ width +middleoffsetX+20 ,height + yoffset -i, color=pid.black)
						c.drawString('%d' % ceil(LRSFullThresh*i/250.0),xoffset+ width + middleoffsetX+25,height + yoffset -i +5, font = labelFont,color=pid.black)

					labelFont=pid.Font(ttf="verdana",size=20,bold=0)
					c.drawString('LRS Interaction',xoffset+ width + middleoffsetX-50,height + yoffset, font = labelFont,color=pid.dimgray,angle=90)
					c.drawString('LRS Full',xoffset+ width + middleoffsetX+50,height + yoffset, font = labelFont,color=pid.dimgray,angle=90)

				filename= webqtlUtil.genRandStr("Pair_")
				c.save(webqtlConfig.IMGDIR+filename, format='png')
				img2=HT.Image('/image/'+filename+'.png',border=0,usemap='#pairPlotMap')


				form0 = HT.Form( cgi= os.path.join(webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE), enctype='multipart/form-data', name='showPairPlot', submit=HT.Input(type='hidden'))
				hddn0 = {'FormID':'pairPlot','Chr_A':'_','Chr_B':'','idata':string.join(map(str, _vals), ','),'istrain':string.join(_strains, ','),'RISet':fd.RISet}
				for key in hddn0.keys():
					form0.append(HT.Input(name=key, value=hddn0[key], type='hidden'))

				form0.append(img2, pngMap)

				mainfmName = webqtlUtil.genRandStr("fm_")
				txtform = HT.Form( cgi= os.path.join(webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE), enctype='multipart/form-data', name=mainfmName, submit=HT.Input(type='hidden'))
				hddn = {'FormID':'showDatabase','ProbeSetID':'_','database':fd.RISet+"Geno",'CellID':'_','RISet':fd.RISet}
				#XZ, Aug 11, 2010: The variable traitStrains is not assigned right values before (should not be assigned fd.strainlist).
				#hddn['traitStrains'] = string.join(fd.strainlist, ',')
				hddn['traitStrains'] = string.join(_strains, ',')
				hddn['traitValues'] = string.join(map(str, _vals), ',')
				hddn['interval1'] = ''
				hddn['interval2'] = ''
				if fd.incparentsf1:
					hddn['incparentsf1']='ON'
				for key in hddn.keys():
					txtform.append(HT.Input(name=key, value=hddn[key], type='hidden'))

				tbl = HT.TableLite(Class="collap", cellspacing=1, cellpadding=5,width=canvasWidth + colorAreaWidth)

				c1 = HT.TD('Interval 1',colspan=3,align="Center", Class="fs13 fwb ffl b1 cw cbrb")
				c2 = HT.TD('Interval 2',colspan=3,align="Center", Class="fs13 fwb ffl b1 cw cbrb")
				c11 = HT.TD('Position',rowspan=2,align="Center", Class="fs13 fwb ffl b1 cw cbrb")
				c12 = HT.TD('Flanking Markers',colspan=2,align="Center", Class="fs13 fwb ffl b1 cw cbrb")
				c111 = HT.TD('Proximal',align="Center", Class="fs13 fwb ffl b1 cw cbrb")
				c112 = HT.TD('Distal',align="Center", Class="fs13 fwb ffl b1 cw cbrb")


				c3 = HT.TD('LRS Full',rowspan=3,align="Center", Class="fs13 fwb ffl b1 cw cbrb")
				c4 = HT.TD('LRS Additive',rowspan=3,align="Center", Class="fs13 fwb ffl b1 cw cbrb")
				c5 = HT.TD('LRS Interact',rowspan=3,align="Center", Class="fs13 fwb ffl b1 cw cbrb")
				c6 = HT.TD('LRS 1',rowspan=3,align="Center", Class="fs13 fwb ffl b1 cw cbrb")
				c7 = HT.TD('LRS 2',rowspan=3,align="Center", Class="fs13 fwb ffl b1 cw cbrb")


				tbl.append(HT.TR(c1,c3,c4,c5,c6,c7,c2))

				tbl.append(HT.TR(c11,c12,c11,c12))
				tbl.append(HT.TR(c111,c112,c111,c112))
				if not graphsort: #Sort by LRS Full
					rectInfo.sort(webqtlUtil.cmpLRSFull)
				rectInfoReturned = rectInfo[len(rectInfo) - returnIntervalPairNum:]
				rectInfoReturned.reverse()

				for item in rectInfoReturned:
					LRSFull,LRSInteract,LRSa,LRSb,chras,chram,chrae,chrbs,chrbm,chrbe,chra,chrb,flanka,flankb = item
					LRSAdditive = LRSFull - LRSInteract
					flanka1,flanka2 = string.split(flanka)
					flankb1,flankb2 = string.split(flankb)
					urla1 = HT.Href(text = flanka1, url = "javascript:showTrait('%s','%s');" % (mainfmName, flanka1),Class= "fs12 fwn")
					urla2 = HT.Href(text = flanka2, url = "javascript:showTrait('%s','%s');" % (mainfmName, flanka2),Class= "fs12 fwn")
					urlb1 = HT.Href(text = flankb1, url = "javascript:showTrait('%s','%s');" % (mainfmName, flankb1),Class= "fs12 fwn")
					urlb2 = HT.Href(text = flankb2, url = "javascript:showTrait('%s','%s');" % (mainfmName, flankb2),Class= "fs12 fwn")
					urlGenGraph = HT.Href(text = "Plot", url = "javascript:showCateGraph('%s',  '%s %s %2.3f', '%s %s %2.3f');" % (mainfmName, flanka1, flanka2, chram, flankb1, flankb2, chrbm),Class= "fs12 fwn")
					tr1 = HT.TR(
						HT.TD('Chr %s @ %2.1f cM ' % (chrsInfo[chra][1],chram),Class= "fs12 b1 fwn"),
						HT.TD(urla1,Class= "fs12 b1 fwn"),
						HT.TD(urla2,Class= "fs12 b1 fwn"),
						HT.TD('%2.3f ' % LRSFull, urlGenGraph,Class= "fs12 b1 fwn"),
						HT.TD('%2.3f' % LRSAdditive,Class= "fs12 b1 fwn"),
						HT.TD('%2.3f' % LRSInteract,Class= "fs12 b1 fwn"),
						HT.TD('%2.3f' % LRSa,Class= "fs12 b1 fwn"),
						HT.TD('%2.3f' % LRSb,Class= "fs12 b1 fwn"),
						HT.TD('Chr %s @ %2.1f cM' % (chrsInfo[chrb][1],chrbm),Class= "fs12 b1 fwn"),
						HT.TD(urlb1,Class= "fs12 b1 fwn"),
						HT.TD(urlb2,Class= "fs12 b1 fwn"))
					tbl.append(tr1)

				plotType1 = HT.Input(type="radio", name="plotType", value ="Dot", checked=1)
				plotType2 = HT.Input(type="radio", name="plotType", value ="Box")
				plotText = HT.Paragraph("Plot Type : ", plotType1, " Dot ", plotType2, " Box",  )

				txtform.append(plotText, tbl)
				TD_LR = HT.TD(colspan=2,height=200,width="100%",bgColor='#eeeeee')
				TD_LR.append(main_title,HT.Blockquote(subtitle1, pairIntro, HT.P(), HT.Center(form0,HT.P())),HT.Blockquote(subtitle2, permuIntro,HT.P(), HT.Center(permuTbl)), HT.Blockquote(subtitle3, tblIntro, HT.P(),HT.Center(txtform), HT.P()))
				self.dict['body'] = str(TD_LR)
			else:
				heading = "Direct Plot"
				detail = ['Fewer than %d strain data were entered for %s data set. No statitical analysis has been attempted.' % (webqtlConfig.KMININFORMATIVE, fd.RISet)]
				self.error(heading=heading,detail=detail)
				return
		else:
			heading = "Direct Plot"
			detail = ['Empty data set, please check your data.']
			self.error(heading=heading,detail=detail)
			return

