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
import reaper

from utility import Plot
from base.templatePage import templatePage
from base import webqtlConfig
from utility import webqtlUtil



class CompositeMarkerRegressionPage(templatePage):

	def __init__(self, fd):

		templatePage.__init__(self, fd)

		if not fd.genotype:
			fd.readData()
		
		fd.parentsf14regression = fd.formdata.getvalue('parentsf14regression')
		
		weightedRegression = fd.formdata.getvalue('applyVarianceSE')
		
		if fd.parentsf14regression and fd.genotype_2:
			_genotype = fd.genotype_2
		else:
			_genotype = fd.genotype_1
		
		_strains, _vals, _vars, N = fd.informativeStrains(_genotype.prgy, weightedRegression)
		
		self.data = fd
		if self.data.identification:
			heading2 = HT.Paragraph('Trait ID: %s' % self.data.identification)
			heading2.__setattr__("class","subtitle")
			self.dict['title'] = '%s: Composite Regression' % self.data.identification
		else:
			heading2 = ""
			self.dict['title'] = 'Composite Regression'
		
		if self.data.traitInfo:
			symbol,chromosome,MB = string.split(fd.traitInfo,'\t')
			heading3 = HT.Paragraph('[ ',HT.Strong(HT.Italic('%s' % symbol,id="green")),' on Chr %s @ %s Mb ]' % (chromosome,MB))
		else:
			heading3 = ""
		if N < webqtlConfig.KMININFORMATIVE:
			heading = "Composite Regression"
			detail = ['Fewer than %d strain data were entered for %s data set. No mapping attempted.' % (webqtlConfig.KMININFORMATIVE, self.data.RISet)]
			self.error(heading=heading,detail=detail)
			return
		else:
			heading = HT.Paragraph('Trait Data Entered for %s Set' % self.data.RISet)
			heading.__setattr__("class","title")
			tt = HT.TableLite()
			for ii in range(N/2):
				tt.append(HT.TR(HT.TD(_strains[2*ii],nowrap="yes"),HT.TD(width=10),  HT.TD(_vals[2*ii], nowrap="yes"), \
				HT.TD(width=20), HT.TD(_strains[2*ii+1],nowrap="yes"),HT.TD(width=10),  HT.TD(_vals[2*ii+1],nowrap="yes")))
			if N % 2:
				tt.append(HT.TR(HT.TD(_strains[N-1],nowrap="yes"),HT.TD(width=10),  HT.TD(_vals[N-1],nowrap="yes"), \
				HT.TD(width=20), HT.TD("",nowrap="yes"),HT.TD(width=10), HT.TD("",nowrap="yes")))
			indata = tt 
			
			mean, median, var, stdev, sem, N = reaper.anova(_vals)
			 
			stats = HT.Paragraph('Number of entered values = %d ' % N,HT.BR(),\
				'Mean value = %8.3f ' % mean, HT.BR(), \
				'Median value = %8.3f ' % median, HT.BR(), \
				'Variance = %8.3f ' % var, HT.BR(), \
				'Standard Deviation = %8.3f ' % stdev, HT.BR(), \
				'Standard Error = %8.3f ' % sem)
				
			self.controlLocus = fd.formdata.getvalue('controlLocus')
			heading4 = HT.Blockquote('Control Background Selected for %s Data Set:' % self.data.RISet)
			heading4.__setattr__("class","subtitle")
			
			datadiv = HT.TD(heading, HT.Center(heading2,heading3,indata, stats, heading4,HT.Center(self.controlLocus)), width='45%',valign='top', bgColor='#eeeeee')
			
			resultstable = self.GenReport(fd, _genotype, _strains, _vals, _vars)
			self.dict['body'] = str(datadiv)+str(resultstable)
	
	def GenReport(self, fd, _genotype, _strains, _vals, _vars= []):
		'Create an HTML division which reports any loci which are significantly associated with the submitted trait data.'	
		if webqtlUtil.ListNotNull(_vars):
			qtlresults = _genotype.regression(strains = _strains, trait = _vals, variance = _vars, control = self.controlLocus)
			LRSArray = _genotype.permutation(strains = _strains, trait = _vals, variance = _vars, nperm=fd.nperm)
		else:
			qtlresults = _genotype.regression(strains = _strains, trait = _vals, control = self.controlLocus)
			LRSArray = _genotype.permutation(strains = _strains, trait = _vals,nperm=fd.nperm)
		
		myCanvas = pid.PILCanvas(size=(400,300))
		#plotBar(myCanvas,10,10,390,290,LRSArray,XLabel='LRS',YLabel='Frequency',title=' Histogram of Permutation Test',identification=fd.identification)
		Plot.plotBar(myCanvas, LRSArray,XLabel='LRS',YLabel='Frequency',title=' Histogram of Permutation Test')
		filename= webqtlUtil.genRandStr("Reg_")
		myCanvas.save(webqtlConfig.IMGDIR+filename, format='gif')
		img=HT.Image('/image/'+filename+'.gif',border=0,alt='Histogram of Permutation Test')
			
		if fd.suggestive == None:
			fd.suggestive = LRSArray[int(fd.nperm*0.37-1)]
		else:
			fd.suggestive = float(fd.suggestive)
		if fd.significance == None:
			fd.significance = LRSArray[int(fd.nperm*0.95-1)]
		else:
			fd.significance = float(fd.significance)
		
		#########################################
		#      Permutation Graph
		#########################################
		permutationHeading = HT.Paragraph('Histogram of Permutation Test')
		permutationHeading.__setattr__("class","title")
		lrs = HT.Blockquote('Total of %d permutations' % fd.nperm,HT.P(),'Suggestive LRS = %2.2f' % LRSArray[int(fd.nperm*0.37-1)],\
			HT.BR(),'Significant LRS = %2.2f' % LRSArray[int(fd.nperm*0.95-1)],HT.BR(),'Highly Significant LRS =%2.2f' % LRSArray[int(fd.nperm*0.99-1)])  
		
		permutation = HT.TableLite()
		permutation.append(HT.TR(HT.TD(img)),HT.TR(HT.TD(lrs)))

		_dispAllLRS = 0
		if fd.formdata.getvalue('displayAllLRS'):
			_dispAllLRS = 1
		qtlresults2 = []
		if _dispAllLRS:
			filtered = qtlresults[:]
		else:
			filtered = filter(lambda x, y=fd.suggestive: x.lrs > y, qtlresults)
		if len(filtered) == 0:
			qtlresults2 = qtlresults[:]
			qtlresults2.sort()
			filtered = qtlresults2[-10:]
		
		#########################################
		#      Marker regression report
		#########################################
		locusFormName = webqtlUtil.genRandStr("fm_")
		locusForm = HT.Form(cgi = os.path.join(webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE), \
			enctype='multipart/form-data', name=locusFormName, submit=HT.Input(type='hidden'))
		hddn = {'FormID':'showDatabase','ProbeSetID':'_','database':fd.RISet+"Geno",'CellID':'_', \
			'RISet':fd.RISet, 'incparentsf1':'on'}
		for key in hddn.keys():
			locusForm.append(HT.Input(name=key, value=hddn[key], type='hidden'))
		
		regressionHeading = HT.Paragraph('Marker Regression Report')
		regressionHeading.__setattr__("class","title")
		if qtlresults2 != []:
			report = HT.Blockquote(HT.Font('No association ',color="#FF0000"),HT.Font('with a likelihood ratio statistic greater than %3.1f was found. Here are the top 10 LRSs.' % fd.suggestive,color="#000000"))
		else:
			report = HT.Blockquote('The following loci in the %s data set have associations with the above trait data.\n' % fd.RISet, HT.P())
		report.__setattr__("class","normalsize")
		
		fpText = open('%s.txt' % (webqtlConfig.TMPDIR+filename), 'wb')
		textUrl = HT.Href(text = 'Download', url= '/tmp/'+filename+'.txt', target = "_blank", Class='fs12 fwn')
		
		bottomInfo = HT.Paragraph(textUrl, ' result in tab-delimited text format.', HT.BR(), HT.BR(),'LRS values marked with',HT.Font(' * ',color="red"), 'are greater than the significance threshold (specified by you or by permutation test). ' , HT.BR(), HT.BR(), HT.Strong('Additive Effect'), ' is half the difference in the mean phenotype of all cases that are homozygous for one parental allel at this marker minus the mean of all cases that are homozygous for the other parental allele at this marker. ','In the case of %s strains, for example,' % fd.RISet,' A positive additive effect indicates that %s alleles increase trait values. Negative additive effect indicates that %s alleles increase trait values.'% (fd.ppolar,fd.mpolar),Class="fs12 fwn")

		c1 = HT.TD('LRS',Class="fs14 fwb ffl b1 cw cbrb")
		c2 = HT.TD('Chr',Class="fs14 fwb ffl b1 cw cbrb")
		c3 = HT.TD('Mb',Class="fs14 fwb ffl b1 cw cbrb")
		c4 = HT.TD('Locus',Class="fs14 fwb ffl b1 cw cbrb")
		c5 = HT.TD('Additive Effect',Class="fs14 fwb ffl b1 cw cbrb")
		
		fpText.write('LRS\tChr\tMb\tLocus\tAdditive Effect\n')
		hr = HT.TR(c1, c2, c3, c4, c5)
		tbl = HT.TableLite(border=0, width="90%", cellpadding=0, cellspacing=0, Class="collap")
		tbl.append(hr)
		for ii in filtered:
			#add by NL 06-22-2011: set LRS to 460 when LRS is infinite, 
			if ii.lrs==float('inf') or ii.lrs>webqtlConfig.MAXLRS:
				LRS=webqtlConfig.MAXLRS #maximum LRS value
			else:
				LRS=ii.lrs		
			fpText.write('%2.3f\t%s\t%s\t%s\t%2.3f\n' % (LRS, ii.locus.chr, ii.locus.Mb, ii.locus.name, ii.additive))
			if LRS > fd.significance:
				c1 = HT.TD('%3.3f*' % LRS, Class="fs13 b1 cbw cr")
			else:
				c1 = HT.TD('%3.3f' % LRS,Class="fs13 b1 cbw c222")
			tbl.append(HT.TR(c1, HT.TD(ii.locus.chr,Class="fs13 b1 cbw c222"), HT.TD(ii.locus.Mb,Class="fs13 b1 cbw c222"), HT.TD(HT.Href(text=ii.locus.name, url = "javascript:showTrait('%s','%s');" % (locusFormName, ii.locus.name), Class='normalsize'), Class="fs13 b1 cbw c222"), HT.TD('%3.3f' % ii.additive,Class="fs13 b1 cbw c222"),bgColor='#eeeeee'))
		
		locusForm.append(tbl)
		tbl2 = HT.TableLite(border=0, cellspacing=0, cellpadding=0,width="90%")
		tbl2.append(HT.TR(HT.TD(bottomInfo)))
		rv=HT.TD(permutationHeading,HT.Center(permutation),regressionHeading,report, HT.Center(locusForm,HT.P(),tbl2,HT.P()),width='55%',valign='top', bgColor='#eeeeee')
		return rv
		
