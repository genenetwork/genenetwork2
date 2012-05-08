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


from mod_python import apache, util, Session, Cookie
import time
import string

from base.webqtlFormData import webqtlFormData

import logging
logging.basicConfig(filename="/tmp/gn_log", level=logging.INFO)
_log = logging.getLogger("main")



def handler(req):
	_log.info("Handling a request")
	req.content_type = 'text/html'

	formdata = util.FieldStorage(req)

	formID = formdata.getfirst('FormID')
	sid = formdata.getfirst('sid')
	cmdID = formdata.getfirst('cmd')
	page = None

	#XZ: this statement must be put into handler function
	_log.info("Loading session")
	mod_python_session = Session.Session(req, timeout=864000, lock=0)
	mod_python_session.load()			
	_log.info("Done loading session")

	if sid:
		from cmdLine import procPage
		reload(procPage)
		req.content_type = 'text/html'
		procPage.procPage(sid, req)
	else:	
		fd = webqtlFormData(req=req, mod_python_session=mod_python_session, FieldStorage_formdata=formdata)

		if formID:
		        _log.info("Dispatching on %s, %s"%(formID, fd.formID))
			#XZ: Special case. Pay attention to parameters! We can NOT pass 'fd'!
                        if fd.formID == 'uploadFile':
				from base import cookieData
				from misc import uploadFilePage
				reload(uploadFilePage)
				reload(cookieData)
				cookies = cookieData.cookieData(Cookie.get_cookies(req)) #new module
				req.content_type = 'text/html'
				page = uploadFilePage.uploadFilePage(fd, formdata, cookies)

                        #search
                        elif fd.formID in ('searchResult','asearchResult'):
                                from search import SearchResultPage
                                reload(SearchResultPage)
                                req.content_type = 'text/html'
                                page = SearchResultPage.SearchResultPage(fd)

                        #showTrait
                        elif fd.formID == 'showDatabase':
                                from showTrait import ShowTraitPage
                                reload(ShowTraitPage)
                                req.content_type = 'text/html'
                                page = ShowTraitPage.ShowTraitPage(fd)
                        elif fd.formID == 'showBest':
                                from showTrait import ShowBestTrait
                                reload(ShowBestTrait)
                                req.content_type = 'text/html'
                                page = ShowBestTrait.ShowBestTrait(fd)
                        elif fd.formID == 'showProbeInfo':
                                from showTrait import ShowProbeInfoPage
                                reload(ShowProbeInfoPage)
                                page = ShowProbeInfoPage.ShowProbeInfoPage(fd)
                                req.content_type = 'text/html'
			elif fd.formID in ('crossChoice', 'varianceChoice'):
				if not fd.submitID:
					req.content_type = 'text/html'
					req.write('check your page')
				elif fd.submitID == 'sample':
					from showTrait import testTraitPage  # new module
					reload(testTraitPage)
					page = testTraitPage.testTraitPage()
					req.content_type = 'text/html'
				else:
					from showTrait import DataEditingPage
					reload(DataEditingPage)
					req.content_type = 'text/html'
					page = DataEditingPage.DataEditingPage(fd)

			#from Trait Data and Analysis form page
			elif fd.formID == 'dataEditing':
				if not fd.submitID:
					req.content_type = 'text/html'
					req.write('check your page')
				elif fd.submitID == 'basicStatistics': #Updated Basic Statistics page (pop-up when user hits "update" button in DataEditingPage.py
					from basicStatistics import updatedBasicStatisticsPage
                                        reload(updatedBasicStatisticsPage)
                                        req.content_type = 'text/html'
                                        page = updatedBasicStatisticsPage.updatedBasicStatisticsPage(fd)
                                elif fd.submitID == 'updateRecord':
                                        from updateTrait import DataUpdatePage
                                        reload(DataUpdatePage)
                                        req.content_type = 'text/html'
                                        page=DataUpdatePage.DataUpdatePage(fd)
                                elif fd.submitID == 'addRecord':
                                        from collection import AddUserInputToSelectionPage
                                        reload(AddUserInputToSelectionPage)
                                        page = AddUserInputToSelectionPage.AddUserInputToSelectionPage(fd)
                                        req.content_type = 'text/html'
                                elif fd.submitID == 'addPublish':
                                        from submitTrait import AddUserInputToPublishPage
                                        reload(AddUserInputToPublishPage)
                                        req.content_type = 'text/html'
                                        page = AddUserInputToPublishPage.AddUserInputToPublishPage(fd)
                                elif fd.submitID == 'correlation':
                                        from cmdLine import cmdCorrelationPage
                                        reload(cmdCorrelationPage)
                                        page = cmdCorrelationPage.cmdCorrelationPage(fd)
                                elif fd.submitID == 'intervalMap':
                                        from cmdLine import cmdIntervalMappingPage
                                        reload(cmdIntervalMappingPage)
                                        page = cmdIntervalMappingPage.cmdIntervalMappingPage(fd)
				elif fd.submitID == 'markerRegression':
					from cmdLine import cmdMarkerRegressionPage
					reload(cmdMarkerRegressionPage)
					req.content_type = 'text/html'
					page = cmdMarkerRegressionPage.cmdMarkerRegressionPage(fd)

				elif fd.submitID == 'directPlot':
					from cmdLine import cmdDirectPlotPage
					reload(cmdDirectPlotPage)
					req.content_type = 'text/html'
					page = cmdDirectPlotPage.cmdDirectPlotPage(fd)
				elif fd.submitID == 'exportData':
					from showTrait import exportPage
					reload(exportPage)
					req.content_type = 'text/html'
					page = exportPage.ExportPage(fd)
				elif fd.submitID == 'showAll':
					from cmdLine import cmdShowAllPage
					reload(cmdShowAllPage)
					page = cmdShowAllPage.cmdShowAllPage(fd)
				elif fd.submitID == 'showAll2':
					from cmdLine import cmdShowAllPage2
					reload(cmdShowAllPage2)
					page=cmdShowAllPage2.cmdShowAllPage2(fd)
				else:
					pass

			#from marker regression result page
                        elif fd.formID == 'secondRegression':
                                if not fd.submitID:
                                        req.content_type = 'text/html'
                                        req.write('check your page')
                                elif fd.submitID == 'compositeRegression':
                                        req.content_type = 'text/html'
                                        from markerRegression import CompositeMarkerRegressionPage
                                        reload(CompositeMarkerRegressionPage)
                                        page = CompositeMarkerRegressionPage.CompositeMarkerRegressionPage(fd)
                                elif fd.submitID == 'intervalMap':
                                        from intervalMapping import IntervalMappingPage
                                        reload(IntervalMappingPage)
                                        page = IntervalMappingPage.IntervalMappingPage(fd)
                                else:
                                        pass

			#cmdLine	
			elif fd.formID == 'showIntMap':
				from cmdLine import cmdIntervalMappingPage
				reload(cmdIntervalMappingPage)
				page = cmdIntervalMappingPage.cmdIntervalMappingPage(fd)
                        elif fd.formID == 'heatmap':
                                from cmdLine import cmdHeatmapPage
                                reload(cmdHeatmapPage)
                                page = cmdHeatmapPage.cmdHeatmapPage(fd)
                        elif fd.formID == 'networkGraph':
                                from cmdLine import cmdNetworkGraphPage
                                reload(cmdNetworkGraphPage)
                                page = cmdNetworkGraphPage.cmdNetworkGraphPage(fd)
                        elif fd.formID == 'compCorr2':
                                from cmdLine import cmdCompCorrPage
                                reload(cmdCompCorrPage)
                                page = cmdCompCorrPage.cmdCompCorrPage(fd)
                        elif fd.formID == 'calPartialCorrDB':
                                from cmdLine import cmdPartialCorrelationPage
                                reload(cmdPartialCorrelationPage)
                                page = cmdPartialCorrelationPage.cmdPartialCorrelationPage(fd)
				
			#pairScan
			elif fd.formID == 'showCategoryGraph':
				from pairScan import CategoryGraphPage
				reload(CategoryGraphPage)
				req.content_type = 'text/html'
				page = CategoryGraphPage.CategoryGraphPage(fd)
			elif fd.formID == 'pairPlot':
				from pairScan import PairPlotPage
				reload(PairPlotPage)
				req.content_type = 'text/html'
				page = PairPlotPage.PairPlotPage(fd)

			#compareCorrelates
			elif fd.formID == 'compCorr':
				from compareCorrelates import MultipleCorrelationPage
				reload(MultipleCorrelationPage)
				page = MultipleCorrelationPage.MultipleCorrelationPage(fd)

			#correlationMatrix
			elif fd.formID == 'corMatrix':
				from correlationMatrix import CorrelationMatrixPage
				reload(CorrelationMatrixPage)
				req.content_type = 'text/html'
				page = CorrelationMatrixPage.CorrelationMatrixPage(fd)
                        elif fd.formID=='tissueCorrelation' or fd.formID=='dispMultiSymbolsResult':
                                from correlationMatrix import TissueCorrelationPage
                                reload(TissueCorrelationPage)
                                page = TissueCorrelationPage.TissueCorrelationPage(fd)
			elif fd.formID =='dispTissueCorrelationResult':
				from cmdLine import cmdTissueCorrelationResultPage
				reload (cmdTissueCorrelationResultPage)
				page = cmdTissueCorrelationResultPage.cmdTissueCorrelationResultPage(fd)
			elif fd.formID=='tissueAbbreviation':
				from correlationMatrix import TissueAbbreviationPage
				reload(TissueAbbreviationPage)
				page = TissueAbbreviationPage.TissueAbbreviationPage(fd)
			
			#collection
			elif fd.formID == 'dispSelection':
				from collection import DisplaySelectionPage
				reload(DisplaySelectionPage)
				page = DisplaySelectionPage.DisplaySelectionPage(fd)
				req.content_type = 'text/html'
			elif fd.formID == 'addToSelection':
				from collection import AddToSelectionPage
				reload(AddToSelectionPage)
				page = AddToSelectionPage.AddToSelectionPage(fd)
				req.content_type = 'text/html'
			elif fd.formID == 'removeSelection':
				from collection import RemoveSelectionPage
				reload(RemoveSelectionPage)
				page = RemoveSelectionPage.RemoveSelectionPage(fd)
				req.content_type = 'text/html'
			elif fd.formID == 'exportSelect':
				from collection import ExportSelectionPage
				reload(ExportSelectionPage)
				page = ExportSelectionPage.ExportSelectionPage(fd)
			elif fd.formID == 'importSelect':
				from collection import ImportSelectionPage
				reload(ImportSelectionPage)
				page = ImportSelectionPage.ImportSelectionPage(fd)
				req.content_type = 'text/html'
			elif fd.formID == 'exportSelectionDetailInfo':
				from collection import ExportSelectionDetailInfoPage
				reload(ExportSelectionDetailInfoPage)
				page = ExportSelectionDetailInfoPage.ExportSelectionDetailInfoPage(fd)
                        elif fd.formID == 'batSubmitResult':
                                from collection import BatchSubmitSelectionPage
                                reload(BatchSubmitSelectionPage)
                                page = BatchSubmitSelectionPage.BatchSubmitSelectionPage(fd)
                                req.content_type = 'text/html'

			#user
			elif fd.formID == 'userLogin':
				from user import userLogin
				reload(userLogin)
				page = userLogin.userLogin(fd)
				req.content_type = 'text/html'
			elif fd.formID == 'userLogoff':
				from user import userLogoff
				reload(userLogoff)
				page = userLogoff.userLogoff(fd)
				req.content_type = 'text/html'
			elif fd.formID == 'userPasswd':
				from user import userPasswd
				reload(userPasswd)
				page = userPasswd.userPasswd(fd)
				req.content_type = 'text/html'

			#submitTrait
                        elif fd.formID == 'pre_dataEditing':
                                from submitTrait import VarianceChoicePage
                                reload(VarianceChoicePage)
                                page = VarianceChoicePage.VarianceChoicePage(fd)
                                req.content_type = 'text/html'
			elif fd.formID == 'batSubmit':
				from submitTrait import BatchSubmitPage
				reload(BatchSubmitPage)
				req.content_type = 'text/html'
				page = BatchSubmitPage.BatchSubmitPage(fd)


			#misc
                        elif fd.formID == 'editHtml':
                                from misc import editHtmlPage
                                reload(editHtmlPage)
                                req.content_type = 'text/html'
                                page = editHtmlPage.editHtmlPage(fd)

			#genomeGraph
			elif fd.formID == 'transciptMapping':
				from genomeGraph import cmdGenomeScanPage
				reload(cmdGenomeScanPage)
				req.content_type = 'text/html'
				page = cmdGenomeScanPage.cmdGenomeScanPage(fd)
			elif fd.formID == 'genAllDbResult':
				from genomeGraph import genAllDbResultPage
				reload(genAllDbResultPage)
				page = genAllDbResultPage.genAllDbResultPage(fd)	

			#geneWiki
			elif fd.formID == 'geneWiki':
				from geneWiki import AddGeneRIFPage
				reload(AddGeneRIFPage)
				page = AddGeneRIFPage.AddGeneRIFPage(fd)

			#externalResource
			elif fd.formID == 'GOTree':
				from externalResource import GoTreePage
				reload(GoTreePage)
				req.content_type = 'text/html'
				page = GoTreePage.GoTreePage(fd)
			elif fd.formID == 'ODE':
                                from externalResource import ODEPage
                                reload(ODEPage)
                                req.content_type = 'text/html'
                                page = ODEPage.ODEPage(fd)
                        elif fd.formID == 'GCAT':
                                from externalResource import GCATPage
                                reload(GCATPage)
                                req.content_type = 'text/html'
                                page = GCATPage.GCATPage(fd)

			#management
                        elif fd.formID == 'managerMain':
                                from management import managerMainPage
                                reload(managerMainPage)
                                req.content_type = 'text/html'
                                page = managerMainPage.managerMainPage(fd)
                        elif fd.formID == 'createUserAccount':
                                from management import createUserAccountPage
                                reload(createUserAccountPage)
                                req.content_type = 'text/html'
                                page = createUserAccountPage.createUserAccountPage(fd)
                        elif fd.formID == 'assignUserToDataset':
                                from management import assignUserToDatasetPage
                                reload(assignUserToDatasetPage)
                                req.content_type = 'text/html'
                                page = assignUserToDatasetPage.assignUserToDatasetPage(fd)
                        elif fd.formID == 'deletePhenotypeTrait':
                                from management import deletePhenotypeTraitPage
                                reload(deletePhenotypeTraitPage)
                                req.content_type = 'text/html'
                                page = deletePhenotypeTraitPage.deletePhenotypeTraitPage(fd)	
                        elif fd.formID == 'exportPhenotypeDataset':
                                from management import exportPhenotypeDatasetPage
                                reload(exportPhenotypeDatasetPage)
                                req.content_type = 'text/html'
                                page = exportPhenotypeDatasetPage.exportPhenotypeDatasetPage(fd)
                        elif fd.formID == 'editHeaderFooter':
                                from management import editHeaderFooter
                                reload(editHeaderFooter)
                                req.content_type = 'text/html'
                                page = editHeaderFooter.editHeaderFooter(fd)
			elif fd.formID == 'updGeno':
                                from management import GenoUpdate
                                reload(GenoUpdate)
                                req.content_type = 'text/html'
                                page = GenoUpdate.GenoUpdate(fd)

			#correlation
                        elif fd.formID == 'showCorrelationPlot':
                                from correlation import PlotCorrelationPage
                                reload(PlotCorrelationPage)
                                req.content_type = 'text/html'
                                page = PlotCorrelationPage.PlotCorrelationPage(fd)
                        elif fd.formID == 'partialCorrInput':
                                from correlation import PartialCorrInputPage
                                reload(PartialCorrInputPage)
                                req.content_type = 'text/html'
                                page = PartialCorrInputPage.PartialCorrInputPage(fd)
                        elif fd.formID == 'calPartialCorrTrait':
                                from correlation import PartialCorrTraitPage
                                reload(PartialCorrTraitPage)
                                req.content_type = 'text/html'
                                page = PartialCorrTraitPage.PartialCorrTraitPage(fd)

			#elif fd.formID == 'BNInput':
			#	from BN import BNInputPage
			#	reload(BNInputPage)
			#	req.content_type = 'text/html'
			#	page = BNInputPage.BNInputPage(fd)

                        elif fd.formID == 'updateRecord':
				from updateTrait import DataUpdatePage
				reload(DataUpdatePage)
				req.content_type = 'text/html'
				page=DataUpdatePage.DataUpdatePage(fd)

			#schema
			elif fd.formID == 'schemaShowPage':
				from schema import ShowSchemaPage
				reload(ShowSchemaPage)
				req.content_type = 'text/html'
				page = ShowSchemaPage.ShowSchemaPage(fd)
			elif fd.formID == 'schemaShowComment':
				from schema import ShowCommentPage
				reload(ShowCommentPage)
				req.content_type = 'text/html'
				page = ShowCommentPage.ShowCommentPage(fd)
			elif fd.formID == 'schemaUpdateComment':
				from schema import UpdateCommentPage
				reload(UpdateCommentPage)
				req.content_type = 'text/html'
				page = UpdateCommentPage.UpdateCommentPage(fd)

			#snpBrowser
			elif fd.formID == 'snpBrowser':
				req.content_type = 'text/html'
				snpId = fd.formdata.getfirst('snpId')
				if snpId:
					from snpBrowser import snpDetails
					reload(snpDetails)
					page = snpDetails.snpDetails(fd, snpId)
				else:
					from snpBrowser import snpBrowserPage
					reload(snpBrowserPage)
					page = snpBrowserPage.snpBrowserPage(fd)
			elif fd.formID =='SnpBrowserResultPage':
				from cmdLine import cmdSnpBrowserResultPage
				reload (cmdSnpBrowserResultPage)
				page = cmdSnpBrowserResultPage.cmdSnpBrowserResultPage(fd)

			#intervalAnalyst
			elif fd.formID == 'intervalAnalyst':
				from intervalAnalyst import IntervalAnalystPage
				reload(IntervalAnalystPage)
				req.content_type = 'text/html'
				page = IntervalAnalystPage.IntervalAnalystPage(fd)			

			#AJAX_table
			elif fd.formID == 'AJAX_table':
				from utility import AJAX_table
				reload(AJAX_table)
				req.content_type = 'text/html'
				req.write(AJAX_table.AJAX_table(fd).write())

                      	elif fd.formID == 'submitSingleTrait':
				from submitTrait import CrossChoicePage
				reload(CrossChoicePage)
				page = CrossChoicePage.CrossChoicePage(fd)
				req.content_type = 'text/html'

			elif fd.formID == 'sharing':
				from dataSharing import SharingPage
				reload(SharingPage)
				page = SharingPage.SharingPage(fd)
				req.content_type = 'text/html'

			elif fd.formID == 'sharinginfo':
				from dataSharing import SharingInfoPage
				reload(SharingInfoPage)
				page = SharingInfoPage.SharingInfoPage(fd)
				req.content_type = 'text/html'
			
			elif fd.formID == 'sharinginfoedit':
				from dataSharing import SharingInfoEditPage
				reload(SharingInfoEditPage)
				page = SharingInfoEditPage.SharingInfoEditPage(fd)
				req.content_type = 'text/html'
				
			elif fd.formID == 'sharinginfodelete':
				from dataSharing import SharingInfoDeletePage
				reload(SharingInfoDeletePage)
				page = SharingInfoDeletePage.SharingInfoDeletePage(fd)
				req.content_type = 'text/html'

			elif fd.formID == 'sharinginfoupdate':
				from dataSharing import SharingInfoUpdatePage
				reload(SharingInfoUpdatePage)
				page = SharingInfoUpdatePage.SharingInfoUpdatePage(fd)
				req.content_type = 'text/html'

			elif fd.formID == 'sharingListDataset':
				from dataSharing import SharingListDataSetPage
				reload(SharingListDataSetPage)
				page = SharingListDataSetPage.SharingListDataSetPage(fd)
				req.content_type = 'text/html'

			elif fd.formID == 'sharinginfoadd':
				from dataSharing import SharingInfoAddPage
				reload(SharingInfoAddPage)
				page = SharingInfoAddPage.SharingInfoAddPage(fd)
				req.content_type = 'text/html'

			elif fd.formID == 'annotation':
				from annotation import AnnotationPage
				reload(AnnotationPage)
				page = AnnotationPage.AnnotationPage(fd)
				req.content_type = 'text/html'

			elif fd.formID == 'qtlminer':
				from qtlminer import QTLminer
                                reload(QTLminer)
                                req.content_type = 'text/html'
                                page = QTLminer.QTLminer(fd)
			elif fd.formID == 'qtlminerresult':
				from cmdLine import cmdQTLminerPage
                                reload (cmdQTLminerPage)
                                page = cmdQTLminerPage.cmdQTLminerPage(fd)

			else:
				from search import IndexPage
				reload(IndexPage)
				page = IndexPage.IndexPage(fd)
				req.content_type = 'text/html'

                        #elif fd.formID == 'updGeno':
                        #       import GenoUpdate
                        #       reload(GenoUpdate)
                        #       req.content_type = 'text/html'
                        #       page=GenoUpdate.GenoUpdate(fd)
                        #elif fd.formID == 'updStrain':
                        #       import StrainUpdate
                        #       reload(StrainUpdate)
                        #       req.content_type = 'text/html'
                        #       page=StrainUpdate.StrainUpdate(fd)
                        #elif fd.formID == 'showTextResult':
                        #       import resultPage
                        #       reload(resultPage)
                        #       page = resultPage.ShowTextResult(fd)
                        #elif fd.formID == 'showStrainInfo':
                        #       import dataPage
                        #       reload(dataPage)
                        #       req.content_type = 'text/html'
                        #       page = dataPage.ShowStrainInfoPage(fd)
                        #elif fd.formID == 'showImage':
                        #       import dataPage
                        #       reload(dataPage)
                        #       req.content_type = 'text/html'
                        #       page = dataPage.ShowImagePage(fd)
                        #XZ, 04/29/2009: There is one webpage gn/web/webqtl/blat.html and I have moved it to junk folder. This function is very old and I don't think it is being used.
                        #elif fd.formID == 'BlatSearch':
                        #       import miscPage
                        #       reload(miscPage)
                        #       page = miscPage.ShowBlatResult(fd)
                        #elif fd.formID == 'admin':
                        #       import adminPage
                        #       reload(adminPage)
                        #       req.content_type = 'text/html'
                        #       page = adminPage.adminModifyPage(fd)

		elif cmdID: 
			#need to rewrite
			cmdID = string.lower(cmdID)
			if cmdID in ('get','trait','tra'):
	                        from textUI import cmdGet
				reload(cmdGet)
				req.content_type = 'text/plain'
				req.write(cmdGet.cmdGet(fd).write())
			elif cmdID in ('help', 'hlp'):
				from textUI import cmdHelp
				reload(cmdHelp)
				req.content_type = 'text/plain'
				req.write(cmdHelp.cmdHelp(fd).write())
			elif cmdID in ('correlation','cor','pea','pearson'):
				from textUI import cmdCorrelation
				reload(cmdCorrelation)	   
				req.content_type = 'text/plain'
				req.write(cmdCorrelation.cmdCorrelation(fd).write())
			elif cmdID in ('map','marker'):
				from textUI import cmdMap
				reload(cmdMap)
				req.content_type = 'text/plain'
				req.write(cmdMap.cmdMap(fd).write())
			elif cmdID in ('geno','gen','genotype'):
				from textUI import cmdGeno
				reload(cmdGeno)
				req.content_type = 'text/plain'
				req.write(cmdGeno.cmdGeno(fd).write())
			elif cmdID in ('interval','int'):
				from textUI import cmdInterval
				reload(cmdInterval)
				req.content_type = 'text/plain'
				req.write(cmdInterval.cmdInterval(fd).write())
			elif cmdID in ('show','shw'):
				from textUI import cmdShowEditing
				reload(cmdShowEditing)
				req.content_type = 'text/html'
				result = cmdShowEditing.cmdShowEditing(fd)
				page = result.page
			elif cmdID in ('search','sch'):
				req.content_type = 'text/plain'
				from textUI import cmdSearchGene
				reload(cmdSearchGene)
				result = cmdSearchGene.cmdSearchGene(fd)
				page = result.page
				req.write(result.text)

			#elif cmdID in ('tst','Test'):
			#	req.write('Content-type: application/x-download')
			#	req.write('Content-disposition: attachment; filename=my.txt\n')
			#	genotype_file = GENODIR + 'AKXD.geno'
			#	fp = open(genotype_file)
			#	line = fp.read()
			#	fp.close()
			#	req.write(line)
			#XZ, 03/03/2009: This fuction must be initiated from URL
			#XZ: http://www.genenetwork.org/webqtl/WebQTL.py?cmd=birn&species=mouse&tissue=Hippocampus&ProbeId=1436869_at&Strain=BXD1
			#elif cmdID[0:4]=="birn":
			#	req.content_type = 'text/plain'
			#	import BIRN
			#	reload(BIRN)
			#	result = BIRN.birnSwitch(fd)
			#	req.write(result.text)
                        #elif cmdID in ('spear','spearman','spe'):
                        #       import cmdSpearman  # new modules
                        #       reload(cmdSpearman)
                        #       req.content_type = 'text/plain'
                        #       req.write(cmdSpearman.cmdSpearman(fd).write())
                        #elif cmdID in ('snp','track'):
                        #       import cmdSnpTrack  # new modules
                        #       reload(cmdSnpTrack)
                        #       req.content_type = 'text/plain'
                        #       req.write(cmdSnpTrack.cmdSnpTrack(fd).write())

			else:
				req.content_type = 'text/html'
				req.write("###Wrong Command")

                ######## Create first page when called with no formID ########

		else:
			_log.info("Going to the search page")
			from search import IndexPage
                        reload(IndexPage)
                        page = IndexPage.IndexPage(fd)
                        req.content_type = 'text/html'
	
	if page:
		#send Cookie first
		if page.cookie:
			for item in page.cookie:
				if (item):
					modcookie = Cookie.Cookie(item.name, item.value)
					modcookie.path = item.path
					if item.expire != None:
						modcookie.expires = time.time() + item.expire
					Cookie.add_cookie(req, modcookie)

		#save session
		if page.session_data_changed:
			for one_key in page.session_data_changed.keys():
				mod_python_session[one_key] = page.session_data_changed[one_key]
			mod_python_session.save()


		req.content_type= page.content_type

		#send attachment
		if page.redirection:
			util.redirect(req, page.redirection)
		elif page.content_disposition:
			req.headers_out["Content-Disposition"] = page.content_disposition
			req.write(page.attachment)
		elif page.debug: # for debug
			req.write(page.debug)
		#send regular content
		else:
			req.write(page.write())
	else:
		pass
		
	return apache.OK
	

