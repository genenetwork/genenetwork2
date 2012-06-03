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
from math import *
import piddle as pid
import os

from htmlgen import HTMLgen2 as HT
import reaper

from utility import Plot
from base.webqtlTrait import webqtlTrait
from base.templatePage import templatePage
from utility import webqtlUtil
from base import webqtlConfig
from dbFunction import webqtlDatabaseFunction



class BasicStatisticsPage_alpha(templatePage):

	plotMinInformative = 4

	def __init__(self, fd):

		templatePage.__init__(self, fd)

		if not fd.genotype:
			fd.readGenotype()
			strainlist2 = fd.strainlist

		if fd.allstrainlist:
			strainlist2 = fd.allstrainlist

		fd.readData(strainlist2)

		specialStrains = []
		setStrains = []
		for item in strainlist2:
			if item not in fd.strainlist and item.find('F1') < 0:
				specialStrains.append(item)
			else:
				setStrains.append(item)
		specialStrains.sort()
		#So called MDP Panel
		if specialStrains:
			specialStrains = fd.f1list+fd.parlist+specialStrains

		self.plotType = fd.formdata.getvalue('ptype', '0')
		plotStrains = strainlist2
		if specialStrains:
			if self.plotType == '1':
				plotStrains = setStrains
			if self.plotType == '2':
				plotStrains = specialStrains

		self.dict['title'] = 'Basic Statistics'
		if not self.openMysql():
			return

		self.showstrains = 1
		self.identification = "unnamed trait"

		self.fullname = fd.formdata.getvalue('fullname', '')
		if self.fullname:
			self.Trait = webqtlTrait(fullname=self.fullname, cursor=self.cursor)
			self.Trait.retrieveInfo()
		else:
			self.Trait = None

		if fd.identification:
			self.identification = fd.identification
			self.dict['title'] = self.identification + ' / '+self.dict['title']
		TD_LR = HT.TD(height=200,width="100%",bgColor='#eeeeee')

		##should not display Variance, but cannot convert Variance to SE
		#print plotStrains, fd.allTraitData.keys()
		if len(fd.allTraitData) > 0:
			vals=[]
			InformData = []
			for _strain in plotStrains:
				if fd.allTraitData.has_key(_strain):
					_val, _var = fd.allTraitData[_strain].val, fd.allTraitData[_strain].var
					if _val != None:
						vals.append([_strain, _val, _var])
						InformData.append(_val)

			if len(vals) >= self.plotMinInformative:
				supertable2 = HT.TableLite(border=0, cellspacing=0, cellpadding=5,width="800")

				staIntro1 = HT.Paragraph("The table and plots below list the basic statistical analysis result of trait",HT.Strong(" %s" % self.identification))

				#####
				#anova
				#####
				traitmean, traitmedian, traitvar, traitstdev, traitsem, N = reaper.anova(InformData)
				TDStatis = HT.TD(width="360", valign="top")
				tbl2 = HT.TableLite(cellpadding=5, cellspacing=0, Class="collap")
				dataXZ = vals[:]
				dataXZ.sort(self.cmpValue)
				tbl2.append(HT.TR(HT.TD("Statistic",align="center", Class="fs14 fwb ffl b1 cw cbrb", width = 200),
						HT.TD("Value", align="center", Class="fs14 fwb ffl b1 cw cbrb", width = 140)))
				tbl2.append(HT.TR(HT.TD("N of Cases",align="center", Class="fs13 b1 cbw c222"),
						HT.TD(N,nowrap="yes",align="center", Class="fs13 b1 cbw c222")))
				tbl2.append(HT.TR(HT.TD("Mean",align="center", Class="fs13 b1 cbw c222",nowrap="yes"),
						HT.TD("%2.3f" % traitmean,nowrap="yes",align="center", Class="fs13 b1 cbw c222")))
				tbl2.append(HT.TR(HT.TD("Median",align="center", Class="fs13 b1 cbw c222",nowrap="yes"),
						HT.TD("%2.3f" % traitmedian,nowrap="yes",align="center", Class="fs13 b1 cbw c222")))
				#tbl2.append(HT.TR(HT.TD("Variance",align="center", Class="fs13 b1 cbw c222",nowrap="yes"),
				#		HT.TD("%2.3f" % traitvar,nowrap="yes",align="center", Class="fs13 b1 cbw c222")))
				tbl2.append(HT.TR(HT.TD("SEM",align="center", Class="fs13 b1 cbw c222",nowrap="yes"),
						HT.TD("%2.3f" % traitsem,nowrap="yes",align="center", Class="fs13 b1 cbw c222")))
				tbl2.append(HT.TR(HT.TD("SD",align="center", Class="fs13 b1 cbw c222",nowrap="yes"),
						HT.TD("%2.3f" % traitstdev,nowrap="yes",align="center", Class="fs13 b1 cbw c222")))
				tbl2.append(HT.TR(HT.TD("Minimum",align="center", Class="fs13 b1 cbw c222",nowrap="yes"),
						HT.TD("%s" % dataXZ[0][1],nowrap="yes",align="center", Class="fs13 b1 cbw c222")))
				tbl2.append(HT.TR(HT.TD("Maximum",align="center", Class="fs13 b1 cbw c222",nowrap="yes"),
						HT.TD("%s" % dataXZ[-1][1],nowrap="yes",align="center", Class="fs13 b1 cbw c222")))
				if self.Trait and self.Trait.db.type == 'ProbeSet':
					#IRQuest = HT.Href(text="Interquartile Range", url=webqtlConfig.glossaryfile +"#Interquartile",target="_blank", Class="fs14")
					#IRQuest.append(HT.BR())
					#IRQuest.append(" (fold difference)")
					tbl2.append(HT.TR(HT.TD("Range (log2)",align="center", Class="fs13 b1 cbw c222",nowrap="yes"),
						HT.TD("%2.3f" % (dataXZ[-1][1]-dataXZ[0][1]),nowrap="yes",align="center", Class="fs13 b1 cbw c222")))
					tbl2.append(HT.TR(HT.TD(HT.Span("Range (fold)"),align="center", Class="fs13 b1 cbw c222",nowrap="yes"),
						HT.TD("%2.2f" % pow(2.0,(dataXZ[-1][1]-dataXZ[0][1])), nowrap="yes",align="center", Class="fs13 b1 cbw c222")))
					tbl2.append(HT.TR(HT.TD(HT.Span("Quartile Range",HT.BR()," (fold difference)"),align="center", Class="fs13 b1 cbw c222",nowrap="yes"),
						HT.TD("%2.2f" % pow(2.0,(dataXZ[int((N-1)*3.0/4.0)][1]-dataXZ[int((N-1)/4.0)][1])), nowrap="yes",align="center", Class="fs13 b1 cbw c222")))

					# (Lei Yan)
					# 2008/12/19
					self.Trait.retrieveData()
					#XZ, 04/01/2009: don't try to get H2 value for probe.
					if self.Trait.cellid:
						pass
					else:
						self.cursor.execute("SELECT DataId, h2 from ProbeSetXRef WHERE DataId = %d" % self.Trait.mysqlid)
						dataid, heritability = self.cursor.fetchone()
						if heritability:
							tbl2.append(HT.TR(HT.TD(HT.Span("Heritability"),align="center", Class="fs13 b1 cbw c222",nowrap="yes"),HT.TD("%s" % heritability, nowrap="yes",align="center", Class="fs13 b1 cbw c222")))
						else:
							tbl2.append(HT.TR(HT.TD(HT.Span("Heritability"),align="center", Class="fs13 b1 cbw c222",nowrap="yes"),HT.TD("NaN", nowrap="yes",align="center", Class="fs13 b1 cbw c222")))

					# Lei Yan
					# 2008/12/19

				TDStatis.append(tbl2)

				plotHeight = 220
				plotWidth = 120
				xLeftOffset = 60
				xRightOffset = 25
				yTopOffset = 20
				yBottomOffset = 53

				canvasHeight = plotHeight + yTopOffset + yBottomOffset
				canvasWidth = plotWidth + xLeftOffset + xRightOffset
				canvas = pid.PILCanvas(size=(canvasWidth,canvasHeight))
				XXX = [('', InformData[:])]

				Plot.plotBoxPlot(canvas, XXX, offset=(xLeftOffset, xRightOffset, yTopOffset, yBottomOffset), XLabel= "Trait")
				filename= webqtlUtil.genRandStr("Box_")
				canvas.save(webqtlConfig.IMGDIR+filename, format='gif')
				img=HT.Image('/image/'+filename+'.gif',border=0)

				#supertable2.append(HT.TR(HT.TD(staIntro1, colspan=3 )))
				tb = HT.TableLite(border=0, cellspacing=0, cellpadding=0)
				tb.append(HT.TR(HT.TD(img, align="left", style="border: 1px solid #999999; padding:0px;")))
				supertable2.append(HT.TR(TDStatis, HT.TD(tb)))

				dataXZ = vals[:]
				tvals = []
				tnames = []
				tvars = []
				for i in range(len(dataXZ)):
					tvals.append(dataXZ[i][1])
					tnames.append(webqtlUtil.genShortStrainName(fd, dataXZ[i][0]))
					tvars.append(dataXZ[i][2])
				nnStrain = len(tnames)

				sLabel = 1

				###determine bar width and space width
				if nnStrain < 20:
					sw = 4
				elif nnStrain < 40:
					sw = 3
				else:
					sw = 2

				### 700 is the default plot width minus Xoffsets for 40 strains
				defaultWidth = 650
				if nnStrain > 40:
					defaultWidth += (nnStrain-40)*10
				defaultOffset = 100
				bw = int(0.5+(defaultWidth - (nnStrain-1.0)*sw)/nnStrain)
				if bw < 10:
					bw = 10

				plotWidth = (nnStrain-1)*sw + nnStrain*bw + defaultOffset
				plotHeight = 500
				#print [plotWidth, plotHeight, bw, sw, nnStrain]
				c = pid.PILCanvas(size=(plotWidth,plotHeight))
				Plot.plotBarText(c, tvals, tnames, variance=tvars, YLabel='Value', title='%s by Case (sorted by name)' % self.identification, sLabel = sLabel, barSpace = sw)

				filename= webqtlUtil.genRandStr("Bar_")
				c.save(webqtlConfig.IMGDIR+filename, format='gif')
				img0=HT.Image('/image/'+filename+'.gif',border=0)

				dataXZ = vals[:]
				dataXZ.sort(self.cmpValue)
				tvals = []
				tnames = []
				tvars = []
				for i in range(len(dataXZ)):
					tvals.append(dataXZ[i][1])
					tnames.append(webqtlUtil.genShortStrainName(fd, dataXZ[i][0]))
					tvars.append(dataXZ[i][2])

				c = pid.PILCanvas(size=(plotWidth,plotHeight))
				Plot.plotBarText(c, tvals, tnames, variance=tvars, YLabel='Value', title='%s by Case (ranked)' % self.identification, sLabel = sLabel, barSpace = sw)

				filename= webqtlUtil.genRandStr("Bar_")
				c.save(webqtlConfig.IMGDIR+filename, format='gif')
				img1=HT.Image('/image/'+filename+'.gif',border=0)
				
				# Lei Yan
				# 05/18/2009
				# report
				
				title = HT.Paragraph('REPORT on the variation of Shh (or PCA Composite Trait XXXX) (sonic hedgehog) in the (insert Data set name) of (insert Species informal name, e.g., Mouse, Rat, Human, Barley, Arabidopsis)', Class="title")
				header = HT.Paragraph('''This report was generated by GeneNetwork on May 11, 2009, at 11.20 AM using the Basic Statistics module (v 1.0) and data from the Hippocampus Consortium M430v2 (Jun06) PDNN data set. For more details and updates on this data set please link to URL:get Basic Statistics''')
				hr = HT.HR()
				p1 = HT.Paragraph('''Trait values for Shh were taken from the (insert Database name, Hippocampus Consortium M430v2 (Jun06) PDNN). GeneNetwork contains data for NN (e.g., 99) cases. In general, data are averages for each case. A summary of mean, median, and the range of these data are provided in Table 1 and in the box plot (Figure 1). Data for individual cases are provided in Figure 2A and 2B, often with error bars (SEM). ''')
				p2 = HT.Paragraph('''Trait values for Shh range 5.1-fold: from a low of 8.2 (please round value) in 129S1/SvImJ to a high of 10.6 (please round value) in BXD9.  The interquartile range (the difference between values closest to the 25% and 75% levels) is a more modest 1.8-fold. The mean value is XX. ''')
				t1 = HT.Paragraph('''Table 1.  Summary of Shh data from the Hippocampus Consortium M430v2 (june06) PDNN data set''')
				f1 = HT.Paragraph('''Figure 1. ''')
				f1.append(HT.Href(text="Box plot", url="http://davidmlane.com/hyperstat/A37797.html", target="_blank", Class="fs14"))
				f1.append(HT.Text(''' of Shh data from the Hippocampus Consortium M430v2 (june06) PDNN data set'''))
				f2A = HT.Paragraph('''Figure 2A: Bar chart of Shh data ordered by case from the Hippocampus Consortium M430v2 (june06) PDNN data set''')
				f2B = HT.Paragraph('''Figure 2B: Bar chart of Shh values ordered by from the Hippocampus Consortium M430v2 (june06) PDNN data set''')
				TD_LR.append(HT.Blockquote(title, HT.P(), header, hr, p1, HT.P(), p2, HT.P(), supertable2, t1, f1, HT.P(), img0, f2A, HT.P(), img1, f2B))
				self.dict['body'] = str(TD_LR)
			else:
				heading = "Basic Statistics"
				detail = ['Fewer than %d case data were entered for %s data set. No statitical analysis has been attempted.' % (self.plotMinInformative, fd.RISet)]
				self.error(heading=heading,detail=detail)
				return
		else:
			heading = "Basic Statistics"
			detail = ['Empty data set, please check your data.']
			self.error(heading=heading,detail=detail)
			return

	def traitInfo(self, fd, specialStrains = None):
		species = webqtlDatabaseFunction.retrieveSpecies(cursor=self.cursor, RISet=fd.RISet)
		heading2 = HT.Paragraph(HT.Strong('Population: '), "%s %s" % (species.title(), fd.RISet) , HT.BR())
		if self.Trait:
			trait_url = HT.Href(text=self.Trait.name, url = os.path.join(webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE) + \
					"?FormID=showDatabase&incparentsf1=1&database=%s&ProbeSetID=%s" % (self.Trait.db.name, self.Trait.name), \
					target='_blank', Class="fs13 fwn")
			heading2.append(HT.Strong("Database: "),
				HT.Href(text=self.Trait.db.fullname, url = webqtlConfig.INFOPAGEHREF % self.Trait.db.name ,
					target='_blank',Class="fs13 fwn"),HT.BR())
			if self.Trait.db.type == 'ProbeSet':
				heading2.append(HT.Strong('Trait ID: '), trait_url, HT.BR(),
					HT.Strong("Gene Symbol: "), HT.Italic('%s' % self.Trait.symbol,id="green"),HT.BR())
				if self.Trait.chr and self.Trait.mb:
					heading2.append(HT.Strong("Location: "), 'Chr %s @ %s Mb' % (self.Trait.chr, self.Trait.mb))
			elif self.Trait.db.type == 'Geno':
				heading2.append(HT.Strong('Locus : '), trait_url, HT.BR())
				#heading2.append(HT.Strong("Gene Symbol: "), HT.Italic('%s' % self.Trait.Symbol,id="green"),HT.BR())
				if self.Trait.chr and self.Trait.mb:
					heading2.append(HT.Strong("Location: "), 'Chr %s @ %s Mb' % (self.Trait.chr, self.Trait.mb))
			elif self.Trait.db.type == 'Publish':
				heading2.append(HT.Strong('Record ID: '), trait_url, HT.BR())
				heading2.append(HT.Strong('Phenotype: '), self.Trait.phenotype, HT.BR())
				heading2.append(HT.Strong('Author: '), self.Trait.authors, HT.BR())
			elif self.Trait.db.type == 'Temp':
				heading2.append(HT.Strong('Description: '), self.Trait.description, HT.BR())
				#heading2.append(HT.Strong('Author: '), self.Trait.authors, HT.BR())
			else:
				pass
		else:
			heading2.append(HT.Strong("Trait Name: "), fd.identification)

		if specialStrains:
			mdpform = HT.Form(cgi= os.path.join(webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE), name='MDP_Form',submit=HT.Input(type='hidden'))
			mdphddn = {'FormID':'dataEditing', 'submitID':'basicStatistics','RISet':fd.RISet, "allstrainlist":string.join(fd.allstrainlist, " "), "ptype":self.plotType, 'identification':fd.identification, "incparentsf1":1}
			if self.fullname:  mdphddn['fullname'] = self.fullname
			webqtlUtil.exportData(mdphddn, fd.allTraitData)
			for key in mdphddn.keys():
				mdpform.append(HT.Input(name=key, value=mdphddn[key], type='hidden'))
			btn0 = HT.Input(type='button' ,name='',value='All Cases',onClick="this.form.ptype.value=0;submit();", Class="button")
			btn1 = HT.Input(type='button' ,name='',value='%s Only' % fd.RISet,onClick="this.form.ptype.value=1;submit();", Class="button")
			btn2 = HT.Input(type='button' ,name='',value='MDP Only', onClick="this.form.ptype.value=2;submit();", Class="button")
			mdpform.append(btn0)
			mdpform.append(btn1)
			mdpform.append(btn2)
			heading2.append(HT.P(), mdpform)

		return HT.Span(heading2)

	def calSD(self,var):
		try:
			return sqrt(abs(var))
		except:
			return None


	def cmpValue(self,A,B):
		try:
			if A[1] < B[1]:
				return -1
			elif A[1] == B[1]:
				return 0
			else:
				return 1
		except:
			return 0




