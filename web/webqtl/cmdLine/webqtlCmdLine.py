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



########################################################
#XZ, Aug 10, 2010
#This part is the temporary solution to make python be able to find other subpackages.
#We can't set global environment because there are many branches on the development machine.

import sys, os

current_file_name = __file__
pathname = os.path.dirname( current_file_name )
abs_path = os.path.abspath(pathname)
sys.path.insert(0, abs_path + '/..')

########################################################



import traceback
import string
import cPickle

from base import webqtlConfig
from base.templatePage import templatePage
from utility import webqtlUtil


if __name__ == "__main__":
	try:
		if len(sys.argv) > 2:
			getID = string.lower(sys.argv[1])
		else:
			raise ValueError
	
		cmdtype = sys.argv[1]
		sessionfile =  sys.argv[2]

		fd = None
		
		fp = open(os.path.join(webqtlConfig.TMPDIR, sessionfile + '.session'), 'rb')
		fd = cPickle.load(fp)
		fp.close()

		if cmdtype == "heatmap":
			from heatmap import heatmapPage
			reload(heatmapPage)
			page = heatmapPage.heatmapPage(fd)
			page.writeFile(sessionfile+'.html')
		elif cmdtype == "directplot":
			from pairScan import DirectPlotPage
			reload(DirectPlotPage)
			page = DirectPlotPage.DirectPlotPage(fd)
			page.writeFile(sessionfile+'.html')
		elif cmdtype == "networkGraph":
			from networkGraph import networkGraphPage
			reload(networkGraphPage)
			page = networkGraphPage.networkGraphPage(fd)
			page.writeFile(sessionfile+'.html')
		elif cmdtype == "interval":
			from intervalMapping import IntervalMappingPage
			reload(IntervalMappingPage)
			page = IntervalMappingPage.IntervalMappingPage(fd)
			page.writeFile(sessionfile+'.html')
		elif cmdtype == "correlation":
			from correlation import CorrelationPage
			reload (CorrelationPage)
			page = CorrelationPage.CorrelationPage(fd)
			page.writeFile(sessionfile+'.html')
                elif cmdtype == "partialCorrelation":
                        from correlation import PartialCorrDBPage
			reload(PartialCorrDBPage)
                        page = PartialCorrDBPage.PartialCorrDBPage(fd)
                        page.writeFile(sessionfile+'.html')
		elif cmdtype == "correlationComparison":
			from compareCorrelates import multitrait
			reload(multitrait)
			page = multitrait.compCorrPage(fd)
			page.writeFile(sessionfile+'.html')
		elif cmdtype == "genreport": # Generate Report Page
			spacer = '</TR></Table><Table width=900 cellSpacing=0 cellPadding=5><TR>'

			from basicStatistics import BasicStatisticsPage
			reload(BasicStatisticsPage)
			page1 = BasicStatisticsPage.BasicStatisticsPage(fd)

			if not fd.formdata.getvalue('bsCheck'):
				page1.dict['body'] = ""

			if fd.formdata.getvalue('tcCheck'):
				from correlation import CorrelationPage
				reload(CorrelationPage)
				page2 = CorrelationPage.CorrelationPage(fd)
				page1.dict['body'] += spacer + str(page2.dict['body'])
				page1.dict['js1'] +=  page2.dict['js1']

			if fd.formdata.getvalue('imCheck'):
				from intervalMapping import IntervalMappingPage
				reload(IntervalMappingPage)
				page3 = IntervalMappingPage.IntervalMappingPage(fd)
				page1.dict['body'] += spacer + str(page3.dict['body'])

			if fd.formdata.getvalue('mrCheck'):
				from markerRegression import MarkerRegressionPage
				reload(MarkerRegressionPage)
				page4 = MarkerRegressionPage.MarkerRegressionPage(fd)
				page1.dict['body'] += spacer + str(page4.dict['body'])

			if fd.formdata.getvalue('psCheck'):
				from pairScan import DirectPlotPage
				reload(DirectPlotPage)
				page5 = DirectPlotPage.DirectPlotPage(fd)
				page1.dict['body'] += spacer + str(page5.dict['body'])
									 
			page1.writeFile(sessionfile+'.html')
			
		elif cmdtype == "genreport2": # Generate Report Page v2
			spacer = '</TR></Table><Table width=900 cellSpacing=0 cellPadding=5><TR>'

			from basicStatistics import BasicStatisticsPage_alpha
			reload(BasicStatisticsPage_alpha)
			page1 = BasicStatisticsPage_alpha.BasicStatisticsPage_alpha(fd)
			page1.writeFile(sessionfile+'.html')
		elif cmdtype == "snpbrowser":
			from snpBrowser import snpBrowserPage
			reload(snpBrowserPage)
			page = snpBrowserPage.snpBrowserPage(fd)
			page.writeFile(sessionfile+'.html')
		elif cmdtype == "QTLminer":
			from qtlminer import QTLminer
			reload(QTLminer)
			page = QTLminer.QTLminer(fd)
			page.writeFile(sessionfile+'.html')
		elif cmdtype == "tissueCorrelation":
			from correlationMatrix import TissueCorrelationPage
			reload(TissueCorrelationPage)
			page = TissueCorrelationPage.TissueCorrelationPage(fd)
			page.writeFile(sessionfile+'.html')	
		elif cmdtype == "markerRegression":
			from markerRegression import MarkerRegressionPage
			reload(MarkerRegressionPage)
			page = MarkerRegressionPage.MarkerRegressionPage(fd)
			page.writeFile(sessionfile+'.html')				
		else:
			raise ValueError
	except:
		fp = open(os.path.join(webqtlConfig.TMPDIR, sessionfile +'.html'), 'wb')
		fp.write('\n\n<pre>')
		traceback.print_exc(file=fp)							
		fp.write('\n</pre>')
		fp.close()
