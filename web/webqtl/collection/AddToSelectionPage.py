#AddToSelectionPage.py

import string
from htmlgen import HTMLgen2 as HT
import os
import cPickle
import reaper

from base import webqtlConfig
from base.templatePage import templatePage
from utility.THCell import THCell
from utility.TDCell import TDCell
from utility import webqtlUtil
from showTrait import ShowProbeInfoPage
# NL, 07/27/2010: add 'import webqtlDatabaseFunction' for retrieveSpecies function
from dbFunction import webqtlDatabaseFunction
from base.webqtlTrait import webqtlTrait

	
#########################################
#      Add to Selection Page
#########################################
class AddToSelectionPage(templatePage):

	def __init__(self,fd):

		templatePage.__init__(self, fd)

		if not self.openMysql():
			return

		if not fd.genotype:
			fd.readGenotype()
		
		self.searchResult = fd.formdata.getvalue('searchResult', [])
		if type("1") == type(self.searchResult):
			self.searchResult = [self.searchResult]
		if fd.formdata.getvalue('fromDataEditingPage'):
			searchResult2 = fd.formdata.getvalue('fullname')
			if searchResult2:
				self.searchResult.append(searchResult2)
		
		if self.searchResult:
			pass
		else:
			templatePage.__init__(self, fd)
			heading = 'Add Collections'
			detail = ['You need to select at least one trait to add to your selection.']
			self.error(heading=heading,detail=detail)
			return

		if self.genSelection(fd=fd):
			self.writeHTML(fd)


		
	def genSelection(self, fd=None, checkPreSelection = 1):
		collectionName = '%s_Select' % fd.RISet

		if checkPreSelection:
			try:
				preSelection = fd.input_session_data[collectionName]
				preSelection = list(string.split(preSelection,','))
			except:
				preSelection = []
		else:
			preSelection = []

		if preSelection:
			for item in preSelection:
				if item not in self.searchResult:
					self.searchResult.append(item)

		self.searchResult = map(self.transfer2NewName, self.searchResult)

		for item in self.searchResult:
			if not item:
				self.searchResult.remove(item)

		if len(self.searchResult) > 3000:
                        heading = 'Add Collections'
                        detail = ['You are adding over 3000 traits to selections, please reduce your number of traits.']
                        self.error(heading=heading,detail=detail)
                        return 0
	
		searchResult2 = []
		self.theseTraits = []
		for item in self.searchResult:
			try:
				thisTrait = webqtlTrait(fullname=item, cursor=self.cursor)
				thisTrait.retrieveInfo(QTL=1)
				self.theseTraits.append(thisTrait)
				searchResult2.append(item)
			except:
				pass

		allTraitStr = string.join(searchResult2,',')

		self.session_data_changed[collectionName] = allTraitStr

		return 1


	
	def writeHTML(self,fd):
		TD_LR = HT.TD(height=100,width="100%",bgColor='#eeeeee',valign="top")
		pageTable = HT.TableLite(cellSpacing=0,cellPadding=0,width="100%",border=0, align="Left")
		tbl = HT.TableLite(cellSpacing=2,cellPadding=0,width="90%",border=0, align="Left")
		seq = 1
		SelectionHeading = HT.Paragraph('%s Trait Collection' % fd.RISet, Class="title")
		
		mintmap = HT.Href(url="#redirect", onClick="if(validateTraitNumber()){databaseFunc(document.getElementsByName('showDatabase')[0], 'showIntMap');}")
		mintmap_img = HT.Image("/images/multiple_interval_mapping1_final.jpg", name='mintmap', alt="Multiple Interval Mapping", title="Multiple Interval Mapping", style="border:none;")
		mintmap.append(mintmap_img)
		mcorr = HT.Href(url="#redirect", onClick="if(validateTraitNumber()){databaseFunc(document.getElementsByName('showDatabase')[0], 'compCorr');}")
		mcorr_img = HT.Image("/images/compare_correlates2_final.jpg", name='comparecorr', alt="Compare Correlates", title="Compare Correlates", style="border:none;")
		mcorr.append(mcorr_img)
		cormatrix = HT.Href(url="#redirect", onClick="if(validateTraitNumber()){databaseFunc(document.getElementsByName('showDatabase')[0], 'corMatrix');}")
		cormatrix_img = HT.Image("/images/correlation_matrix1_final.jpg", name='corrmatrix', alt="Correlation Matrix and PCA", title="Correlation Matrix and PCA", style="border:none;")
		cormatrix.append(cormatrix_img)
		networkGraph = HT.Href(url="#redirect", onClick="if(validateTraitNumber()){databaseFunc(document.getElementsByName('showDatabase')[0], 'networkGraph');}")
		networkGraph_img = HT.Image("/images/network_graph1_final.jpg", name='networkgraph', alt="Network Graphs", title="Network Graphs", style="border:none;")
		networkGraph.append(networkGraph_img)
		heatmap = HT.Href(url="#redirect", onClick="if(validateTraitNumber()){databaseFunc(document.getElementsByName('showDatabase')[0], 'heatmap');}")
		heatmap_img = HT.Image("/images/heatmap2_final.jpg", name='heatmap', alt="QTL Heat Map and Clustering", title="QTL Heatmap and Clustering", style="border:none;")
		heatmap.append(heatmap_img)
		partialCorr = HT.Href(url="#redirect", onClick="if(validateTraitNumber()){databaseFunc(document.getElementsByName('showDatabase')[0], 'partialCorrInput');}")
		partialCorr_img = HT.Image("/images/partial_correlation_final.jpg", name='partialCorr', alt="Partial Correlation", title="Partial Correlation", style="border:none;")
		partialCorr.append(partialCorr_img)

		BN = HT.Href(url="#redirect", onClick="if(validateTraitNumber()){databaseFunc(document.getElementsByName('showDatabase')[0], 'BNInput');}")
		networkGraph_img = HT.Image("/images/network_graph1_final.jpg", name='BayesianNetwork', alt="Bayesian Network", title="Bayesian Network", style="border:none;")
		BN.append(networkGraph_img)

		removeselect = HT.Href(url="#redirect", onClick="addRmvSelection('%s', document.getElementsByName('showDatabase')[0], 'removeSelection');" % fd.RISet)
		removeselect_img = HT.Image("/images/remove_selection1_final.jpg", name="removeselect", alt="Remove Selection", title="Remove Selection", style="border:none;")
		removeselect.append(removeselect_img)	
		selectall = HT.Href(url="#redirect", onClick="$('.checkallbox').attr('checked', true);")
		selectall_img = HT.Image("/images/select_all2_final.jpg", name="selectall", alt="Select All", title="Select All", style="border:none;")
		selectall.append(selectall_img)
		reset = HT.Href(url="#redirect", onClick="$('.checkallbox').attr('checked', false);")
		reset_img = HT.Image("/images/select_none2_final.jpg", alt="Select None", title="Select None", style="border:none;")
		reset.append(reset_img)
		exportSelect = HT.Href(url="#redirect", onClick="databaseFunc(document.getElementsByName('showDatabase')[0], 'exportSelectionDetailInfo');")
		exportSelect_img = HT.Image("/images/export2_final.jpg", name="exportSelection", alt="Export Selection", title="Export Selection", style="border:none;")
		exportSelect.append(exportSelect_img)
		selectinvert = HT.Href(url="#redirect", onClick = "checkInvert(document.getElementsByName('showDatabase')[0]);")
		selectinvert_img = HT.Image("/images/invert_selection2_final.jpg", name="selectinvert", alt="Invert Selection", title="Invert Selection", style="border:none;")
		selectinvert.append(selectinvert_img)

		chrMenu = HT.Input(type='hidden',name='chromosomes',value='all')
		
		importFile = HT.Input(type='file', name='importfile', size=15)
		importButton = HT.Input(type='button',name='importSelection',value='Load Collection', onClick="addRmvSelection('%s', this.form, 'importSelect');" % fd.RISet,Class="button")
		exportButton = HT.Input(type='button' ,name='exportSelection',value='Save Collection', onClick="databaseFunc(this.form,'exportSelect');", Class="button")
		importMenu = HT.Select(name='importmethod')
		importMenu.append(('append','append'))
		importMenu.append(('replace','replace'))            
	
		ODE = HT.Href(url="#redirect", onClick="databaseFunc(document.getElementsByName('showDatabase')[0], 'ODE');")
		ODE_img = HT.Image("/images/ODE_logo_final.jpg", name="ode", alt="ODE", title="ODE", style="border:none")
		ODE.append(ODE_img)
	        
		GCATButton = HT.Href(url="#redirect", onClick="databaseFunc(document.getElementsByName('showDatabase')[0], 'GCAT');")
		GCATButton_img = HT.Image("/images/GCAT_logo_final.jpg", name="GCAT", alt="GCAT", title="GCAT", style="border:none")
		GCATButton.append(GCATButton_img)
		
        	GeneSet = HT.Href(url="#redirect", onClick="databaseFunc(document.getElementsByName('showDatabase')[0],'GOTree');")
        	GeneSet_img = HT.Image("/images/webgestalt_icon_final.jpg", name="webgestalt", alt="Gene Set Analysis Toolkit", title="Gene Set Analysis Toolkit", style="border:none")        
        	GeneSet.append(GeneSet_img)      

		#need to be refined
        	if fd.genotype.Mbmap:
            	    scale = HT.Input(name="scale", value="physic", type="hidden")
        	else:
            	    scale = ""
 
        	formMain = HT.Form(cgi=os.path.join(webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE), enctype='multipart/form-data', name='showDatabase', submit=HT.Input(type='hidden'))

		#XZ, July 22, 2011: I add parameters for interval mapping
        	hddn = {'FormID':'showDatabase','ProbeSetID':'_','database':'_','CellID':'_','RISet':fd.RISet,'incparentsf1':'ON','showHideOptions':'more','scale':'physic','additiveCheck':'ON', 'showSNP':'ON', 'showGenes':'ON', 'intervalAnalystCheck':'ON','bootCheck':None, 'permCheck':None, 'applyVarianceSE':None}
        	for key in hddn.keys():
            	    formMain.append(HT.Input(name=key, value=hddn[key], type='hidden'))

        	if not self.searchResult:
            	    SelectionHeading = HT.Paragraph('%s Trait Collection' % fd.RISet, Class="title")
            	    formMain.append(HT.HR(width="70%", color = "blue"),importFile, ' ', importMenu, ' ', importButton)
            	    TD_LR.append(SelectionHeading,HT.Blockquote('No trait has been added to this selection.'), HT.Center(HT.BR(), HT.BR(), HT.BR(), HT.BR(), formMain))
            	    self.dict['body'] = str(TD_LR)
            	    self.dict['title'] = "%s Trait Collection" % fd.RISet
            	    return

		#########################################
		# Creating table object for AJAX table  #
		#########################################
		tblobj = {}
		mainfmName = 'showDatabase'
		# NL, 07/27/2010. retrieveSpecies function has been moved from webqtlTrait.py to webqtlDatabaseFunction.py;
		species = webqtlDatabaseFunction.retrieveSpecies(cursor=self.cursor, RISet=fd.RISet)
		if species == 'human':
			chrMenu = scale = mintmap = heatmap = ""

		tblobj['header'] = self.getCollectionTableHeader()

		sortby = self.getSortByValue()

		thisRISet = fd.RISet
		tblobj['body'] = self.getCollectionTableBody(RISet=thisRISet, traitList=self.theseTraits, formName=mainfmName, species=species)

		filename= webqtlUtil.genRandStr("Search_")

		objfile = open('%s.obj' % (webqtlConfig.TMPDIR+filename), 'wb')
		cPickle.dump(tblobj, objfile)
		objfile.close()


		div = HT.Div(webqtlUtil.genTableObj(tblobj=tblobj, file=filename, sortby=sortby, tableID = "sortable", addIndex = "1"), Id="sortable")		


        	containerTable = HT.TableLite(cellSpacing=2,cellPadding=0,width="90%",border=0,align="Left")
        	postContainerTable = HT.TableLite(cellSpacing=2,cellPadding=0,width="90%",border=0,align="Left")

        	optionsTable = HT.TableLite(cellSpacing=2, cellPadding=0,width="400", border=0, align="Left")
        	optionsTable.append(HT.TR(HT.TD(selectall), HT.TD(reset), HT.TD(selectinvert), HT.TD(removeselect), HT.TD(exportSelect)))
        	optionsTable.append(HT.TR(HT.TD("&nbsp;"*1,"Select"), HT.TD("Deselect"), HT.TD("&nbsp;"*1,"Invert"), HT.TD("&nbsp;"*1,"Remove"), HT.TD("&nbsp;"*1,"Export")))
        	postContainerTable.append(HT.TR(HT.TD(optionsTable)))
        	containerTable.append(HT.TR(HT.TD(optionsTable)))

        	functionTable = HT.TableLite(cellSpacing=2,cellPadding=0,width="480",border=0, align="Left")
        	functionRow = HT.TR(HT.TD(networkGraph, width="16.7%"), HT.TD(cormatrix, width="16.7%"), HT.TD(partialCorr, width="16.7%"), HT.TD(mcorr, width="16.7%"), HT.TD(mintmap, width="16.7%"), HT.TD(heatmap))
        	if species == "human":
        	    labelRow = HT.TR(HT.TD("&nbsp;"*2,HT.Text("Graph")), HT.TD("&nbsp;"*2,HT.Text("Matrix")), HT.TD("&nbsp;"*2, HT.Text("Partial")), HT.TD(HT.Text("Compare")))
        	else:
        		labelRow = HT.TR(HT.TD("&nbsp;"*2,HT.Text("Graph")), HT.TD("&nbsp;"*2,HT.Text("Matrix")), HT.TD("&nbsp;"*2, HT.Text("Partial")), HT.TD(HT.Text("Compare")), HT.TD(HT.Text("QTL Map")), HT.TD(HT.Text(text="Heat Map")))
        	functionTable.append(functionRow, labelRow)
        	postContainerTable.append(HT.TR(HT.TD(functionTable)))
        	containerTable.append(HT.TR(HT.TD(functionTable)))

        	moreOptions = HT.Input(type='button',name='options',value='More Options', onClick="",Class="toggle")
        	fewerOptions = HT.Input(type='button',name='options',value='Fewer Options', onClick="",Class="toggle")
        	
        	

        	if (fd.formdata.getvalue('showHideOptions') == 'less'):		
            	    postContainerTable.append(HT.TR(HT.TD("&nbsp;"), height="10"), HT.TR(HT.TD(HT.Div(fewerOptions, Class="toggleShowHide"))))
            	    containerTable.append(HT.TR(HT.TD("&nbsp;"), height="10"), HT.TR(HT.TD(HT.Div(fewerOptions, Class="toggleShowHide"))))
        	else:	
            	    postContainerTable.append(HT.TR(HT.TD("&nbsp;"), height="10"), HT.TR(HT.TD(HT.Div(moreOptions, Class="toggleShowHide"))))
            	    containerTable.append(HT.TR(HT.TD("&nbsp;"), height="10"), HT.TR(HT.TD(HT.Div(moreOptions, Class="toggleShowHide"))))	


        	LinkOutTable = HT.TableLite(cellSpacing=2,cellPadding=0,width="320",border=0, align="Left")
        	LinkOutRow = HT.TR(HT.TD(GeneSet, width="33%"), HT.TD(GCATButton, width="33%"), HT.TD(ODE, width="33%"), style="display:none;", Class="extra_options")
        	LinkOutLabels = HT.TR(HT.TD(HT.Text("Gene Set")), HT.TD("&nbsp;"*2, HT.Text("GCAT")), HT.TD("&nbsp;"*3, HT.Text("ODE")), style="display:none;", Class="extra_options")
        	LinkOutTable.append(LinkOutRow,LinkOutLabels)
        	postContainerTable.append(HT.TR(HT.TD("&nbsp;"), height=10), HT.TR(HT.TD(LinkOutTable)))
        	containerTable.append(HT.TR(HT.TD("&nbsp;"), height=10), HT.TR(HT.TD(LinkOutTable)))      
                
        	pageTable.append(HT.TR(HT.TD(containerTable)))
        	chrMenu = scale = ""

        	pageTable.append(HT.TR(HT.TD(div)))
        	pageTable.append(HT.TR(HT.TD("&nbsp;")))
        	if len(self.theseTraits) > 20:
            	    pageTable.append(HT.TR(HT.TD(postContainerTable)))
        	pageTable.append(HT.TR(HT.TD(importFile, ' ', importMenu, ' ', importButton, '&nbsp;'*10, exportButton)))
		    #Took out scaleMenu since it will be replaced with a jquery popup in the future - Zach 5/10/2010
        	formMain.append(chrMenu,scale,pageTable)
		    
		#Updated by NL, deleted showHideJS, moved jquery to jqueryFunction.js 
		self.dict['js1'] = ''
            	TD_LR.append(SelectionHeading,formMain)

        	self.dict['body'] = str(TD_LR)
        	self.dict['js2'] = 'onLoad="pageOffset()"'
        	self.dict['layer'] = self.generateWarningLayer()       	
        	self.dict['title'] = "%s Trait Collection" % thisRISet

	def transfer2NewName(self, str):
		"this is temporary"
		if str.find("::") < 0:
			return str.replace(":", "::")
		else:
			return str
		
	def generateWarningLayer(self):

		layerString = """
			<!-- BEGIN FLOATING LAYER CODE //-->
			<div id="warningLayer" style="padding:3px; border: 1px solid #222;
  			background-color: #fff; position:absolute;width:250px;left:100;top:100;visibility:hidden">			
				<table border="0" width="250" class="cbrb" cellspacing="0" cellpadding="5">
					<tr>
						<td width="100%">
  							<table border="0" width="100%" cellspacing="0" cellpadding="0" height="36">
  								<tr>
  									<td class="cbrb cw ff15 fwb" align="Center" width="100%" style="padding:4px">
        									Sort Table
  									</td>
  								</tr>
  								<tr>
  									<td width="100%" bgcolor="#eeeeee" align="Center" style="padding:4px">
										<!-- PLACE YOUR CONTENT HERE //-->
										Resorting this table <br>
										<!-- END OF CONTENT AREA //-->
  									</td>
  								</tr>
  							</table>
						</td>
					</tr>
				</table>
			</div>
			<!-- END FLOATING LAYER CODE //-->

            		"""

		return layerString		
		
	def getCollectionTableHeader(self):

		tblobj_header = []

		className = "fs13 fwb ffl b1 cw cbrb"

		tblobj_header = [[THCell(HT.TD(' ', Class=className, nowrap="on"), sort=0), 
			THCell(HT.TD('Dataset', HT.BR(), HT.BR(), valign="top", Class=className, nowrap="on"), text="dataset", idx=1),
			THCell(HT.TD('Trait', HT.BR(), 'ID', HT.BR(), valign="top", Class=className, nowrap="on"), text="name", idx=2),
			THCell(HT.TD('Symbol', HT.BR(), HT.BR(), valign="top", Class=className, nowrap="on"), text="symbol", idx=3),
			THCell(HT.TD('Description', HT.BR(), HT.BR(), valign="top", Class=className, nowrap="on"), text="desc", idx=4),
			THCell(HT.TD('Location', HT.BR(), HT.BR(), valign="top", Class=className, nowrap="on"), text="location", idx=5),
			THCell(HT.TD('Mean', HT.BR(), HT.BR(), valign="top", Class=className, nowrap="on"), text="mean", idx=6),
			THCell(HT.TD('N', HT.BR(), 'Cases', HT.BR(), valign="top", Class=className, nowrap="on"), text="samples", idx=7),
			THCell(HT.TD('Max LRS', HT.BR(), HT.BR(), valign="top", Class=className, nowrap="on"), text="lrs", idx=8),
			THCell(HT.TD('Max LRS Location',HT.BR(),'Chr and Mb', HT.BR(), valign="top", Class=className, nowrap="on"), text="lrs_location", idx=9)]]

		return tblobj_header

	def getCollectionTableBody(self, RISet=None, traitList=None, formName=None, species=''):

		tblobj_body = []

		className = "fs12 fwn b1 c222"

		for thisTrait in traitList:
			tr = []

			if not thisTrait.haveinfo:
				thisTrait.retrieveInfo(QTL=1)

			if thisTrait.riset != RISet:
				continue	

			trId = str(thisTrait)

			#XZ: check box column
			tr.append(TDCell(HT.TD(HT.Input(type="checkbox", Class="checkallbox", name="searchResult",value=trId, onClick="highlight(this)"), nowrap="on", Class=className)))

			#XZ: Dataset column
			tr.append(TDCell(HT.TD(thisTrait.db.name, Class="fs12 fwn b1 c222"), thisTrait.db.name, thisTrait.db.name.upper()))

			#XZ: Trait ID column
			if thisTrait.cellid:
				tr.append(TDCell(HT.TD(HT.Href(text=thisTrait.cellid,url="javascript:showDatabase3('%s','%s','%s','%s')" % (formName, thisTrait.db.name, thisTrait.name, thisTrait.cellid), Class="fs12 fwn"), nowrap="yes",align="left", Class=className),str(thisTrait.cellid), thisTrait.cellid))
			else:
				tr.append(TDCell(HT.TD(HT.Href(text=thisTrait.getGivenName(),url="javascript:showDatabase3('%s','%s','%s','')" % (formName, thisTrait.db.name, thisTrait.name), Class="fs12 fwn"), nowrap="yes",align="left", Class=className),str(thisTrait.name), thisTrait.name))

			#XZ: Symbol column and Description column
			if (thisTrait.db.type == "Publish"):
				AbbreviationString = "--"
				if (thisTrait.post_publication_abbreviation != None):
					AbbreviationString = thisTrait.post_publication_abbreviation
				PhenotypeString = thisTrait.post_publication_description
				if thisTrait.confidential:
					if not webqtlUtil.hasAccessToConfidentialPhenotypeTrait(privilege=self.privilege, userName=self.userName, authorized_users=thisTrait.authorized_users):
						if thisTrait.pre_publication_abbreviation:
							AbbreviationString = thisTrait.pre_publication_abbreviation
						else:
							AbbreviationString = "--"
						PhenotypeString = thisTrait.pre_publication_description

				if AbbreviationString == "--":
					tr.append(TDCell(HT.TD("--", align="left", Class=className), "--", "Zz"))
				else:
					tr.append(TDCell(HT.TD(AbbreviationString, Class=className), AbbreviationString, AbbreviationString.upper()))

				tr.append(TDCell(HT.TD(PhenotypeString, Class=className), PhenotypeString, PhenotypeString.upper()))


			elif (thisTrait.db.type == "ProbeSet" or thisTrait.db.type == "Temp"):
				description_string = str(thisTrait.description).strip()
				if (thisTrait.db.type == "ProbeSet"):
					if (thisTrait.symbol != None):
           					if thisTrait.geneid:
                        				symbolurl = HT.Href(text=thisTrait.symbol,target='_blank',url="http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?db=gene&cmd=Retrieve&dopt=Graphics&list_uids=%s" % thisTrait.geneid, Class="font_black fs12 fwn")
            					else:
                        				symbolurl = HT.Href(text=thisTrait.symbol,target='_blank',url="http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?CMD=search&DB=gene&term=%s" % thisTrait.symbol, Class="font_black fs12 fwn")
						tr.append(TDCell(HT.TD(symbolurl, align="left", Class="fs12 fwn b1 c222 fsI"), thisTrait.symbol, thisTrait.symbol))
            				else:
						tr.append(TDCell(HT.TD("--", align="left", Class=className), "--", "Zz"))
					target_string = str(thisTrait.probe_target_description).strip()

            				description_display = ''

					if len(description_string) > 1 and description_string != 'None':
						description_display = description_string
					else:
           		    			description_display = thisTrait.symbol

            				if len(description_display) > 1 and description_display != 'N/A' and len(target_string) > 1 and target_string != 'None':
                				description_display = description_display + '; ' + target_string.strip()
					
					description_string = description_display
				else:
					tr.append(TDCell(HT.TD("--", align="left", Class=className), "--", "Zz"))
            			tr.append(TDCell(HT.TD(description_string, Class=className), description_string, description_string))
			else:
				if (thisTrait.name != None):
					tr.append(TDCell(HT.TD(thisTrait.name, Class="fs12 fwn b1 c222"), thisTrait.name, thisTrait.name))
				else:
					tr.append(TDCell(HT.TD("--", align="left", Class=className), "--", "Zz"))
				tr.append(TDCell(HT.TD("--", align="left", Class=className), "--", "Zz"))

			#XZ: Location column
			if (thisTrait.db.type == "Publish"):
				tr.append(TDCell(HT.TD("--", align="left", Class=className), "--", "Zz"))
			else:
				if thisTrait.db.type == "ProbeSet" and thisTrait.cellid:
					EnsemblProbeSetID = thisTrait.name
					if '_at' in thisTrait.name:
						EnsemblProbeSetID = thisTrait.name[0:thisTrait.name.index('_at')+3]	

					#These tables (Ensembl) were created by Xusheng Wang in 2010 and are mm9 (so they'll need to be changed at some point to be mm10.
					self.cursor.execute('''
							SELECT EnsemblProbeLocation.* 
							FROM EnsemblProbeLocation, EnsemblProbe, EnsemblChip, GeneChipEnsemblXRef, ProbeFreeze, ProbeSetFreeze
							WHERE EnsemblProbeLocation.ProbeId=EnsemblProbe.Id and EnsemblProbe.ChipId=GeneChipEnsemblXRef.EnsemblChipId and
								GeneChipEnsemblXRef.GeneChipId=ProbeFreeze.ChipId and EnsemblProbe.Name=%s and EnsemblProbe.ProbeSet=%s and
								ProbeSetFreeze.Id=%s and ProbeSetFreeze.ProbeFreezeId = ProbeFreeze.Id group by Chr, Start, End'''
							,(thisTrait.cellid, EnsemblProbeSetID, thisTrait.db.id))
					LocationFields = self.cursor.fetchall()

					Chr=''
					Mb=''
					Start=''
					End=''
					if (len(LocationFields)>=1):
						Chr,Start,End,Strand,MisMatch,ProbeId = map(self.nullRecord,LocationFields[0])
						Start /= 1000000.0
						End /= 1000000.0
						Mb = Start
					if (len(LocationFields)>1):
						self.cursor.execute('''
								SELECT ProbeSet.Chr, ProbeSet.Mb FROM ProbeSet, ProbeFreeze, ProbeSetFreeze 
								WHERE ProbeSet.ChipId=ProbeFreeze.ChipId and ProbeSet.Name=%s and ProbeSetFreeze.Id=%s and
									ProbeSetFreeze.ProbeFreezeId = ProbeFreeze.Id'''
								,(thisTrait.name, thisTrait.db.id))
						ProbeSetChr, ProbeSetMb = map(self.nullRecord,self.cursor.fetchall()[0])
					
						self.cursor.execute('''
								SELECT EnsemblProbeLocation.*, ABS(EnsemblProbeLocation.Start/1000000-%s) as Mb 
								FROM EnsemblProbeLocation, EnsemblProbe, EnsemblChip, GeneChipEnsemblXRef, ProbeFreeze
								WHERE EnsemblProbeLocation.ProbeId=EnsemblProbe.Id and EnsemblProbe.ChipId=GeneChipEnsemblXRef.EnsemblChipId and
									GeneChipEnsemblXRef.GeneChipId=ProbeFreeze.ChipId and EnsemblProbe.Name=%s and EnsemblProbe.ProbeSet=%s and
									EnsemblProbeLocation.Chr=%s and ProbeSetFreezeId=%s and ProbeSetFreeze.ProbeFreezeId = ProbeFreeze.Id order by Mb limit 1'''
								,(ProbeSetMb, thisTrait.cellid, EnsemblProbeSetID, ProbeSetChr, thisTrait.db.id))
						NewLocationFields = self.cursor.fetchall()
						if (len(NewLocationFields)>0):
							Chr,Start,End,Strand,MisMatch,ProbeId,Mb = map(self.nullRecord,NewLocationFields[0])
							Start /= 1000000.0
							End /= 1000000.0
							Mb = Start

					#ZS: trait_location_value is used for sorting
					trait_location_repr = "--"
					trait_location_value = 1000000

					if Chr and Mb:
						try:
							trait_location_value = int(Chr)*1000 + Mb
						except:
							if Chr.upper() == "X":
								trait_location_value = 20*1000 + Mb
							else:
								trait_location_value = ord(str(Chr).upper()[0])*1000 + Mb
					
						trait_location_repr = "Chr%s: %.6f" % (Chr, float(Mb) )
			
					tr.append(TDCell(HT.TD(trait_location_repr, nowrap='ON', Class=className), trait_location_repr, trait_location_value))
				
				else:

					#ZS: trait_location_value is used for sorting
					trait_location_repr = "--"
					trait_location_value = 1000000

					if hasattr(thisTrait, 'chr') and hasattr(thisTrait, 'mb') and thisTrait.chr and thisTrait.mb:
						try:
							trait_location_value = int(thisTrait.chr)*1000 + thisTrait.mb
						except:
							if thisTrait.chr.upper() == "X":
								trait_location_value = 20*1000 + thisTrait.mb
							else:
								trait_location_value = ord(str(thisTrait.chr).upper()[0])*1000 + thisTrait.mb
					
						trait_location_repr = "Chr%s: %.6f" % (thisTrait.chr, float(thisTrait.mb) )
			
					tr.append(TDCell(HT.TD(trait_location_repr, nowrap='ON', Class=className), trait_location_repr, trait_location_value))

			#XZ: Mean column
			if (thisTrait.db.type == "ProbeSet"):
				if thisTrait.cellid:
					mean = -10000.0
					try:
						thisTrait.retrieveData()
						mean, median, var, stdev, sem, N = reaper.anova(thisTrait.exportInformative()[1])
					except:
						pass
					repr = '%2.3f' % mean
					mean = '%2.2f' % mean
            				tr.append(TDCell(HT.TD(repr, Class=className, align='right', nowrap='ON'),repr, mean))	
				else:
           	 			self.cursor.execute("""
                   	 			select ProbeSetXRef.mean from ProbeSetXRef, ProbeSet
                   	 			where ProbeSetXRef.ProbeSetFreezeId = %d and
                        	  			ProbeSet.Id = ProbeSetXRef.ProbeSetId and
                        	  			ProbeSet.Name = '%s'
            				""" % (thisTrait.db.id, thisTrait.name))
            				result = self.cursor.fetchone()
            				if result:
                				if result[0]:
                    					mean = result[0]
                				else:
                    					mean=0
            				else:
                				mean = 0

					#XZ, 06/05/2009: It is neccessary to turn on nowrap
            				repr = "%2.3f" % mean
            				tr.append(TDCell(HT.TD(repr, Class=className, align='right', nowrap='ON'),repr, mean))	

			elif (thisTrait.db.type == "Publish"):
				self.cursor.execute("""
				select count(PublishData.value), sum(PublishData.value) from PublishData, PublishXRef, PublishFreeze
				where PublishData.Id = PublishXRef.DataId and 
					PublishXRef.Id = %s and
					PublishXRef.InbredSetId = PublishFreeze.InbredSetId and
					PublishFreeze.Id = %d
				""" % (thisTrait.name, thisTrait.db.id))
				result = self.cursor.fetchone()

				if result:
					if result[0] and result[1]:
						mean = result[1]/result[0]
					else:	
						mean = 0
				else:
					mean = 0

				repr = "%2.3f" % mean
				tr.append(TDCell(HT.TD(repr, Class=className, align='right', nowrap='ON'),repr, mean))		
			else:
				tr.append(TDCell(HT.TD("--", Class=className, align='left', nowrap='ON'),"--", 0))			
			
			#Number of cases
			n_cases_value = 0
			n_cases_repr = "--"
			if (thisTrait.db.type == "Publish"):
				self.cursor.execute("""
				select count(PublishData.value) from PublishData, PublishXRef, PublishFreeze
				where PublishData.Id = PublishXRef.DataId and 
					PublishXRef.Id = %s and
					PublishXRef.InbredSetId = PublishFreeze.InbredSetId and
					PublishFreeze.Id = %d
				""" % (thisTrait.name, thisTrait.db.id))
				result = self.cursor.fetchone()

				if result:
					if result[0]:
						n_cases_value = result[0]
						n_cases_repr = result[0]

				if (n_cases_value == "--"):
					tr.append(TDCell(HT.TD(n_cases_repr, Class=className, align='left', nowrap="on"), n_cases_repr, n_cases_value))
				else:
					tr.append(TDCell(HT.TD(n_cases_repr, Class=className, align='right', nowrap="on"), n_cases_repr, n_cases_value))	
			
			elif (thisTrait.db.type == "ProbeSet"):
				self.cursor.execute("""
				select count(ProbeSetData.value) from ProbeSet, ProbeSetXRef, ProbeSetData, ProbeSetFreeze
				where ProbeSet.Name='%s' and
					ProbeSetXRef.ProbeSetId = ProbeSet.Id and
					ProbeSetXRef.DataId = ProbeSetData.Id and
					ProbeSetXRef.ProbeSetFreezeId = ProbeSetFreeze.Id and
					ProbeSetFreeze.Name = '%s'
				""" % (thisTrait.name, thisTrait.db.name))
				result = self.cursor.fetchone()

				if result:
					if result[0]:
						n_cases_value = result[0]
						n_cases_repr = result[0]
				if (n_cases_value == "--"):
					tr.append(TDCell(HT.TD(n_cases_repr, Class=className, align='left', nowrap="on"), n_cases_repr, n_cases_value))
				else:
					tr.append(TDCell(HT.TD(n_cases_repr, Class=className, align='right', nowrap="on"), n_cases_repr, n_cases_value))
			
			elif (thisTrait.db.type == "Geno"):
				self.cursor.execute("""
				select count(GenoData.value) from GenoData, GenoXRef, GenoFreeze, Geno, Strain
				where Geno.SpeciesId = %s and Geno.Name='%s' and
					GenoXRef.GenoId = Geno.Id and
					GenoXRef.DataId = GenoData.Id and
					GenoXRef.GenoFreezeId = GenoFreeze.Id and
					GenoData.StrainId = Strain.Id and
					GenoFreeze.Name = '%s'
				""" % (webqtlDatabaseFunction.retrieveSpeciesId(self.cursor, thisTrait.db.riset), thisTrait.name, thisTrait.db.name))
				result = self.cursor.fetchone()

				if result:
					if result[0]:
						n_cases_value = result[0]
						n_cases_repr = result[0]
				if (n_cases_value == "--"):
					tr.append(TDCell(HT.TD(n_cases_repr, Class=className, align='left', nowrap="on"), n_cases_repr, n_cases_value))
				else:
					tr.append(TDCell(HT.TD(n_cases_repr, Class=className, align='right', nowrap="on"), n_cases_repr, n_cases_value))

			else:
				tr.append(TDCell(HT.TD(n_cases_repr, Class=className, align='left', nowrap="on"), n_cases_repr, n_cases_value))

			#XZ: Max LRS column and Max LRS Location column
			if (thisTrait.db.type != "Geno"):
            			#LRS and its location
            			LRS_score_repr = '--'
            			LRS_score_value = 0
            			LRS_location_repr = '--'
            			LRS_location_value = 1000000
            			LRS_flag = 1

            			#Max LRS and its Locus location
            			if hasattr(thisTrait, 'lrs') and hasattr(thisTrait, 'locus') and thisTrait.lrs and thisTrait.locus:
                			self.cursor.execute("""
                    			select Geno.Chr, Geno.Mb from Geno, Species
                    			where Species.Name = '%s' and
                          			Geno.Name = '%s' and
                          			Geno.SpeciesId = Species.Id
                			""" % (species, thisTrait.locus))
                			result = self.cursor.fetchone()

                			if result:
                    				if result[0] and result[1]:
                        				LRS_Chr = result[0]
                        				LRS_Mb = result[1]

                        				#XZ: LRS_location_value is used for sorting
                        				try:
								LRS_location_value = int(LRS_Chr)*1000 + float(LRS_Mb)
							except:
								if LRS_Chr.upper() == 'X':
									LRS_location_value = 20*1000 + float(LRS_Mb)
								else:
									LRS_location_value = ord(str(LRS_chr).upper()[0])*1000 + float(LRS_Mb)


                        				LRS_score_repr = '%3.1f' % thisTrait.lrs
                        				LRS_score_value = thisTrait.lrs
                        				LRS_location_repr = 'Chr%s: %.6f' % (LRS_Chr, float(LRS_Mb) )
                        				LRS_flag = 0

                        				tr.append(TDCell(HT.TD(LRS_score_repr, Class=className, align='right', nowrap="on"), LRS_score_repr, LRS_score_value))
                        				tr.append(TDCell(HT.TD(LRS_location_repr, Class=className), LRS_location_repr, LRS_location_value))

            			if LRS_flag:
                			tr.append(TDCell(HT.TD(LRS_score_repr, Class=className), LRS_score_repr, LRS_score_value))
                			tr.append(TDCell(HT.TD(LRS_location_repr, Class=className), LRS_location_repr, LRS_location_value))
			else:
                		tr.append(TDCell(HT.TD("--", align="left", Class=className), "--", 0))
                		tr.append(TDCell(HT.TD("--", align="left", Class=className), "--", 1000000))							

			tblobj_body.append(tr)

		return tblobj_body		
		
	def getSortByValue(self):

		sortby = ("pv", "up")

		return sortby

	def nullRecord(self,x):
		if x or x == 0:
			return x
		else:
			return ""
		
