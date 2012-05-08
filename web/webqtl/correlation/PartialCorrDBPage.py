import string
import cPickle
import os
import pyXLWriter as xl

from htmlgen import HTMLgen2 as HT

from base import webqtlConfig
#import webqtlData
from utility.THCell import THCell
from utility.TDCell import TDCell
from base.webqtlTrait import webqtlTrait
from base.webqtlDataset import webqtlDataset
from base.templatePage import templatePage
from utility import webqtlUtil
from CorrelationPage import CorrelationPage
import correlationFunction
from dbFunction import webqtlDatabaseFunction


#########################################
#      Partial Correlation Dataset Page
#########################################


class PartialCorrDBPage(CorrelationPage):

    corrMinInformative = 4

    def __init__(self, fd):


        templatePage.__init__(self, fd)

        if not self.openMysql():
            return


        primaryTraitString = fd.formdata.getvalue('primaryTrait')
        primaryTrait = (webqtlTrait(fullname=primaryTraitString, cursor=self.cursor))

        controlTraitsString = fd.formdata.getvalue('controlTraits')
        controlTraitsList = list(string.split(controlTraitsString,','))
        controlTraits = []
        for item in controlTraitsList:
            controlTraits.append(webqtlTrait(fullname=item, cursor=self.cursor))

        #XZ, 3/16/2010: variable RISet must be pass by the form
        RISet = fd.RISet
        #XZ, 12/12/2008: get species infomation
        species = webqtlDatabaseFunction.retrieveSpecies(cursor=self.cursor, RISet=RISet)

        #XZ, 09/18/2008: get all information about the user selected database.
        self.target_db_name = fd.formdata.getvalue('database2')

	try:
            self.db = webqtlDataset(self.target_db_name, self.cursor)
        except:
            heading = "Partial Correlation Table"
            detail = ["The database you just requested has not been established yet."]
            self.error(heading=heading,detail=detail)
            return

        #XZ, 09/18/2008: check if user has the authority to get access to the database.
        if self.db.type == 'ProbeSet':
            self.cursor.execute('SELECT Id, Name, FullName, confidentiality, AuthorisedUsers FROM ProbeSetFreeze WHERE Name = "%s"' %  self.target_db_name)
            indId, indName, indFullName, confidential, AuthorisedUsers = self.cursor.fetchall()[0]

            if confidential == 1:
                access_to_confidential_dataset = 0

                #for the dataset that confidentiality is 1
                #1. 'admin' and 'root' can see all of the dataset
                #2. 'user' can see the dataset that AuthorisedUsers contains his id(stored in the Id field of User table)
                if webqtlConfig.USERDICT[self.privilege] > webqtlConfig.USERDICT['user']:
                    access_to_confidential_dataset = 1
                else:
                    AuthorisedUsersList=AuthorisedUsers.split(',')
                    if AuthorisedUsersList.__contains__(self.userName):
                        access_to_confidential_dataset = 1

                if not access_to_confidential_dataset:
                    #Error, Confidential Database
                    heading = "Partial Correlation Table"
                    detail = ["The %s database you selected is not open to the public at this time, please go back and select another database." % indFullName]
                    self.error(heading=heading,detail=detail,error="Confidential Database")
                    return


        primaryTrait.retrieveData()
        _primarystrains, _primaryvals, _primaryvars = primaryTrait.exportInformative()

	controlTraitNames = fd.formdata.getvalue('controlTraits')
        _controlstrains,_controlvals,_controlvars,_controlNs = correlationFunction.controlStrains(controlTraitNames,_primarystrains)

        ## If the strains for which each of the control traits and the primary trait have values are not identical,
        ## we must remove from the calculation all vlaues for strains that are not present in each. Without doing this,
        ## undesirable biases would be introduced.

        common_primary_control_strains = _primarystrains #keep _primarystrains
        fixed_primary_vals = _primaryvals #keep _primaryvals
        fixed_control_vals = _controlvals

	allsame = True	
	##allsame is boolean for whether or not primary and control trait have values for the same strains
	for i in _controlstrains:
		if _primarystrains != i:
			allsame=False
			break
	
	if not allsame:
                common_primary_control_strains, fixed_primary_vals, fixed_control_vals, _vars, _controlvars = correlationFunction.fixStrains(_primarystrains,_controlstrains,_primaryvals,_controlvals,_primaryvars,_controlvars)

        N = len(common_primary_control_strains)
        if N < self.corrMinInformative:
            heading = "Partial Correlation Table"
            detail = ['Fewer than %d strain data were entered for %s data set. No calculation of correlation has been attempted.' % (self.corrMinInformative, RISet)]
            self.error(heading=heading,detail=detail)
            return

        #XZ: We should check the value of control trait and primary trait here.
        nameOfIdenticalTraits = correlationFunction.findIdenticalTraits ( fixed_primary_vals, primaryTraitString, fixed_control_vals, controlTraitsList )
        if nameOfIdenticalTraits:
            heading = "Partial Correlation Table"
            detail = ['%s and %s have same values for the %s strains that will be used to calculate partial correlation (common for all primary and control traits). In such case, partial correlation can NOT be calculated. Please re-select your traits.' % (nameOfIdenticalTraits[0], nameOfIdenticalTraits[1], len(fixed_primary_vals))]
            self.error(heading=heading,detail=detail)
            return


        #XZ, 09/28/2008: if user select "1", then display 1, 3 and 4.
        #XZ, 09/28/2008: if user select "2", then display 2, 3 and 5.
        #XZ, 09/28/2008: if user select "3", then display 1, 3 and 4.
        #XZ, 09/28/2008: if user select "4", then display 1, 3 and 4.
        #XZ, 09/28/2008: if user select "5", then display 2, 3 and 5.		
        methodDict = {"1":"Genetic Correlation (Pearson's r)","2":"Genetic Correlation (Spearman's rho)","3":"SGO Literature Correlation","4":"Tissue Correlation (Pearson's r)", "5":"Tissue Correlation (Spearman's rho)"}
        self.method = fd.formdata.getvalue('method')
        if self.method not in ("1","2","3","4","5"):
            self.method = "1"

        self.returnNumber = int(fd.formdata.getvalue('criteria'))

        myTrait = primaryTrait
        myTrait.retrieveInfo()

        # We will not get Literature Correlations if there is no GeneId because there is nothing to look against
        try:
            input_trait_GeneId = myTrait.geneid
        except:
            input_trait_GeneId = None

        # We will not get Tissue Correlations if there is no gene symbol because there is nothing to look against
        try:
            input_trait_symbol = myTrait.symbol
        except:
            input_trait_symbol = None

        
        #XZ, 12/12/2008: if the species is rat or human, translate the geneid to mouse geneid
        input_trait_mouse_geneid = self.translateToMouseGeneID(species, input_trait_GeneId)

        #XZ: As of Nov/13/2010, this dataset is 'UTHSC Illumina V6.2 RankInv B6 D2 average CNS GI average (May 08)'
        TissueProbeSetFreezeId = 1


        #XZ, 09/22/2008: If we need search by GeneId, 
        #XZ, 09/22/2008: we have to check if this GeneId is in the literature or tissue correlation table.
        #XZ, 10/15/2008: We also to check if the selected database is probeset type.
        if self.method == "3" or self.method == "4" or self.method == "5":
            if self.db.type != "ProbeSet":
               self.error(heading="Wrong correlation type",detail="It is not possible to compute the %s between your trait and data in this %s database. Please try again after selecting another type of correlation." % (methodDict[self.method],self.db.name),error="Correlation Type Error")
               return

            """
            if not input_trait_GeneId:
                self.error(heading="No Associated GeneId",detail="This trait has no associated GeneId, so we are not able to show any literature or tissue related information.",error="No GeneId Error")
                return 
            """

            #XZ: We have checked geneid did exist 

            if self.method == "3":
                if not input_trait_GeneId or not self.checkForLitInfo(input_trait_mouse_geneid):
                    self.error(heading="No Literature Info",detail="This gene does not have any associated Literature Information.",error="Literature Correlation Error")
                    return  

            if self.method == "4" or self.method == "5":
                if not input_trait_symbol:
                    self.error(heading="No Tissue Correlation Information",detail="This gene does not have any associated Tissue Correlation Information.",error="Tissue Correlation Error")
                    return

                if not self.checkSymbolForTissueCorr(TissueProbeSetFreezeId, myTrait.symbol):
                    self.error(heading="No Tissue Correlation Information",detail="This gene does not have any associated Tissue Correlation Information.",error="Tissue Correlation Error")
                    return

#######################################################################################################################################

        nnCorr = len(fixed_primary_vals)

        #XZ: Use the fast method only for probeset dataset, and this dataset must have been created.
        #XZ: Otherwise, use original method

        useFastMethod = False

        if self.db.type == "ProbeSet":
            DatabaseFileName = self.getFileName( target_db_name=self.target_db_name )
            DirectoryList = os.listdir(webqtlConfig.TEXTDIR)  # List of existing text files. Used to check if a text file already exists
            if DatabaseFileName in DirectoryList:
                useFastMethod = True

        if useFastMethod:
            totalTraits, allcorrelations = self.getPartialCorrelationsFast(common_primary_control_strains , fixed_primary_vals, fixed_control_vals, nnCorr, DatabaseFileName, species, input_trait_GeneId, input_trait_symbol, TissueProbeSetFreezeId)

            if totalTraits == 0:
                useFastMethod = False

        #XZ, 01/08/2009: use the original method to retrieve from database and compute.            
        if not useFastMethod:
            totalTraits, allcorrelations = self.getPartialCorrelationsNormal(common_primary_control_strains, fixed_primary_vals, fixed_control_vals, nnCorr, species, input_trait_GeneId, input_trait_symbol,TissueProbeSetFreezeId)
	
#############################################################

        if self.method == "3" and input_trait_GeneId:
            allcorrelations.sort(self.cmpLitCorr)
        elif self.method in ["4","5"] and input_trait_GeneId:
            allcorrelations.sort(self.cmpLitCorr)
        else:
            allcorrelations.sort(self.cmpPartialCorrPValue)

        #XZ, 09/20/2008: we only need the top ones.
        self.returnNumber = min(self.returnNumber,len(allcorrelations))
        allcorrelations = allcorrelations[:self.returnNumber]

        addLiteratureCorr = False
        addTissueCorr = False

        traitList = []
        for item in allcorrelations:
            thisTrait = webqtlTrait(db=self.db, name=item[0], cursor=self.cursor)
            thisTrait.retrieveInfo()

            thisTrait.Name = item[0]
            thisTrait.NOverlap = item[1]

            thisTrait.partial_corr = item[2]
            thisTrait.partial_corrPValue = item[3]

            thisTrait.corr = item[4]
            thisTrait.corrPValue = item[5] 
            # NL, 07/19/2010
            # js function changed, add a new parameter rankOrder for js function 'showTissueCorrPlot'		
            rankOrder = 0;
            if self.method in ["2","5"]:
                rankOrder = 1;
            thisTrait.rankOrder = rankOrder

            #XZ, 26/09/2008: Method is 4 or 5. Have fetched tissue corr, but no literature correlation yet.
            if len(item) == 8:
                thisTrait.tissueCorr = item[6]
                thisTrait.tissuePValue = item[7]
                addLiteratureCorr = True

            #XZ, 26/09/2008: Method is 3,  Have fetched literature corr, but no tissue corr yet.
            elif len(item) == 7:
                thisTrait.LCorr = item[6]
                thisTrait.mouse_geneid = self.translateToMouseGeneID(species, thisTrait.geneid)
                addTissueCorr = True

            #XZ, 26/09/2008: Method is 1 or 2. Have NOT fetched literature corr and tissue corr yet.
            # Phenotype data will not have geneid, and neither will some probes
            # we need to handle this because we will get an attribute error
            else:
                if input_trait_mouse_geneid and self.db.type=="ProbeSet":
                    addLiteratureCorr = True
                if input_trait_symbol and self.db.type=="ProbeSet":
                    addTissueCorr = True

            traitList.append(thisTrait)

        if addLiteratureCorr:
            traitList = self.getLiteratureCorrelationByList(input_trait_mouse_geneid, species, traitList)
        if addTissueCorr:
            traitList = self.getTissueCorrelationByList(primaryTraitSymbol=input_trait_symbol, traitList=traitList,TissueProbeSetFreezeId=TissueProbeSetFreezeId, method=self.method)

########################################################

        TD_LR = HT.TD(height=200,width="100%",bgColor='#eeeeee')

        mainfmName = webqtlUtil.genRandStr("fm_")
        form = HT.Form(cgi= os.path.join(webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE), enctype='multipart/form-data', name= mainfmName, submit=HT.Input(type='hidden'))
        hddn = {'FormID':'showDatabase', 'ProbeSetID':'_','database':self.target_db_name, 'CellID':'_', 'RISet':RISet, 'identification':fd.identification}

        if myTrait:
            hddn['fullname']=str(myTrait)


        for key in hddn.keys():
            form.append(HT.Input(name=key, value=hddn[key], type='hidden'))

        #XZ, 11/21/2008: add two parameters to form
        form.append(HT.Input(name="X_geneSymbol", value="", type='hidden'))
        form.append(HT.Input(name="Y_geneSymbol", value="", type='hidden'))

        #XZ, 3/11/2010: add one parameter to record if the method is rank order.

        form.append(HT.Input(name="rankOrder", value="%s" % rankOrder, type='hidden'))

        form.append(HT.Input(name="TissueProbeSetFreezeId", value="%s" % TissueProbeSetFreezeId, type='hidden'))


        ####################################
        # generate the info on top of page #
        ####################################

        info_form = self.getFormForPrimaryAndControlTraits (primaryTrait, controlTraits)
        info = self.getTopInfo(myTrait=myTrait, method=self.method, db=self.db, target_db_name=self.target_db_name, returnNumber=self.returnNumber, methodDict=methodDict, totalTraits=totalTraits, identification=fd.identification  )

        ##############
        # Excel file #
        ##############	
        filename= webqtlUtil.genRandStr("Corr_")
        xlsUrl = HT.Input(type='button', value = 'Download Table', onClick= "location.href='/tmp/%s.xls'" % filename, Class='button')
        # Create a new Excel workbook
        workbook = xl.Writer('%s.xls' % (webqtlConfig.TMPDIR+filename))
        headingStyle = workbook.add_format(align = 'center', bold = 1, border = 1, size=13, fg_color = 0x1E, color="white")

        #XZ, 3/18/2010: pay attention to the line number of header in this file. As of today, there are 7 lines.
        worksheet = self.createExcelFileWithTitleAndFooter(workbook=workbook, identification=fd.identification, db=self.db, returnNumber=self.returnNumber)

        newrow = 7



#####################################################################

        mintmap = HT.Href(url="#redirect", onClick="databaseFunc(document.getElementsByName('%s')[0], 'showIntMap');" % mainfmName)
        mintmap_img = HT.Image("/images/multiple_interval_mapping1_final.jpg", name='mintmap', alt="Multiple Interval Mapping", title="Multiple Interval Mapping", style="border:none;")
        mintmap.append(mintmap_img)
        mcorr = HT.Href(url="#redirect", onClick="databaseFunc(document.getElementsByName('%s')[0], 'compCorr');" % mainfmName)
        mcorr_img = HT.Image("/images/compare_correlates2_final.jpg", alt="Compare Correlates", title="Compare Correlates", style="border:none;")
        mcorr.append(mcorr_img)
        cormatrix = HT.Href(url="#redirect", onClick="databaseFunc(document.getElementsByName('%s')[0], 'corMatrix');" % mainfmName)
        cormatrix_img = HT.Image("/images/correlation_matrix1_final.jpg", alt="Correlation Matrix and PCA", title="Correlation Matrix and PCA", style="border:none;")
        cormatrix.append(cormatrix_img)
        networkGraph = HT.Href(url="#redirect", onClick="databaseFunc(document.getElementsByName('%s')[0], 'networkGraph');" % mainfmName)
        networkGraph_img = HT.Image("/images/network_graph1_final.jpg", name='mintmap', alt="Network Graphs", title="Network Graphs", style="border:none;")
        networkGraph.append(networkGraph_img)
        heatmap = HT.Href(url="#redirect", onClick="databaseFunc(document.getElementsByName('%s')[0], 'heatmap');" % mainfmName)
        heatmap_img = HT.Image("/images/heatmap2_final.jpg", name='mintmap', alt="QTL Heat Map and Clustering", title="QTL Heatmap and Clustering", style="border:none;")
        heatmap.append(heatmap_img)
        partialCorr = HT.Href(url="#redirect", onClick="databaseFunc(document.getElementsByName('%s')[0], 'partialCorrInput');" % mainfmName) 
        partialCorr_img = HT.Image("/images/partial_correlation_final.jpg", name='partialCorr', alt="Partial Correlation", title="Partial Correlation", style="border:none;")
        partialCorr.append(partialCorr_img)
        addselect = HT.Href(url="#redirect", onClick="addRmvSelection('%s', document.getElementsByName('%s')[0], 'addToSelection');" % (RISet, mainfmName))
        addselect_img = HT.Image("/images/add_collection1_final.jpg", name="addselect", alt="Add To Collection", title="Add To Collection", style="border:none;")
        addselect.append(addselect_img)
	selectall = HT.Href(url="#redirect", onClick="checkAll(document.getElementsByName('%s')[0]);" % mainfmName)
        selectall_img = HT.Image("/images/select_all2_final.jpg", name="selectall", alt="Select All", title="Select All", style="border:none;")
        selectall.append(selectall_img)
        selectinvert = HT.Href(url="#redirect", onClick = "checkInvert(document.getElementsByName('%s')[0]);" % mainfmName)
        selectinvert_img = HT.Image("/images/invert_selection2_final.jpg", name="selectinvert", alt="Invert Selection", title="Invert Selection", style="border:none;")
        selectinvert.append(selectinvert_img)
        reset = HT.Href(url="#redirect", onClick="checkNone(document.getElementsByName('%s')[0]); return false;" % mainfmName)
        reset_img = HT.Image("/images/select_none2_final.jpg", alt="Select None", title="Select None", style="border:none;")
        reset.append(reset_img)
        selecttraits = HT.Input(type='button' ,name='selecttraits',value='Select Traits', onClick="checkTraits(this.form);",Class="button")
        selectgt = HT.Input(type='text' ,name='selectgt',value='-1.0', size=6,maxlength=10,onChange="checkNumeric(this,1.0,'-1.0','gthan','greater than filed')")
        selectlt = HT.Input(type='text' ,name='selectlt',value='1.0', size=6,maxlength=10,onChange="checkNumeric(this,-1.0,'1.0','lthan','less than field')")
        selectandor = HT.Select(name='selectandor')
        selectandor.append(('AND','and'))
        selectandor.append(('OR','or'))
        selectandor.selected.append('AND')

        chrMenu = HT.Input(type='hidden',name='chromosomes',value='all')

        corrHeading = HT.Paragraph('Partial Correlation Table', Class="title")

        	
        pageTable = HT.TableLite(cellSpacing=0,cellPadding=0,width="100%", border=0, align="Left")
        containerTable = HT.TableLite(cellSpacing=0,cellPadding=0,width="90%",border=0, align="Left")

        optionsTable = HT.TableLite(cellSpacing=2, cellPadding=0,width="320", height="80", border=0, align="Left")
        optionsTable.append(HT.TR(HT.TD(selectall), HT.TD(reset), HT.TD(selectinvert), HT.TD(addselect), align="left"))
        optionsTable.append(HT.TR(HT.TD("&nbsp;"*1,"Select"), HT.TD("Deselect"), HT.TD("&nbsp;"*1,"Invert"), HT.TD("&nbsp;"*3,"Add")))
        containerTable.append(HT.TR(HT.TD(optionsTable)))

        functionTable = HT.TableLite(cellSpacing=2,cellPadding=0,width="480",height="80", border=0, align="Left")
        functionRow = HT.TR(HT.TD(networkGraph, width="16.7%"), HT.TD(cormatrix, width="16.7%"), HT.TD(partialCorr, width="16.7%"), HT.TD(mcorr, width="16.7%"), HT.TD(mintmap, width="16.7%"), HT.TD(heatmap), align="left")
        labelRow = HT.TR(HT.TD("&nbsp;"*1,HT.Text("Graph")), HT.TD("&nbsp;"*1,HT.Text("Matrix")), HT.TD("&nbsp;"*1,HT.Text("Partial")), HT.TD(HT.Text("Compare")), HT.TD(HT.Text("QTL Map")), HT.TD(HT.Text(text="Heat Map")))
        functionTable.append(functionRow, labelRow)
        containerTable.append(HT.TR(HT.TD(functionTable), HT.BR()))

        moreOptions = HT.Input(type='button',name='options',value='More Options', onClick="",Class="toggle")
        fewerOptions = HT.Input(type='button',name='options',value='Fewer Options', onClick="",Class="toggle")

        if (fd.formdata.getvalue('showHideOptions') == 'less'):		
			containerTable.append(HT.TR(HT.TD("&nbsp;"), height="10"), HT.TR(HT.TD(HT.Div(fewerOptions, Class="toggleShowHide"))))
			containerTable.append(HT.TR(HT.TD("&nbsp;")))
        else:	
			containerTable.append(HT.TR(HT.TD("&nbsp;"), height="10"), HT.TR(HT.TD(HT.Div(moreOptions, Class="toggleShowHide"))))	
			containerTable.append(HT.TR(HT.TD("&nbsp;")))

        containerTable.append(HT.TR(HT.TD(HT.Span(selecttraits,' with partial r > ',selectgt, ' ',selectandor, ' r < ',selectlt,Class="bd1 cbddf fs11")), style="display:none;", Class="extra_options"))


        tblobj = {}


        if self.db.type=="Geno":
        	
            containerTable.append(HT.TR(HT.TD(xlsUrl, height=40)))
            pageTable.append(HT.TR(HT.TD(containerTable)))
        	
            tblobj['header'], worksheet = self.getTableHeaderForGeno( method=self.method, worksheet=worksheet, newrow=newrow, headingStyle=headingStyle)
            newrow += 1
            
            corrScript = HT.Script(language="Javascript")
            corrScript.append("var corrArray = new Array();")

            sortby = self.getSortByValue( calculationMethod = self.method )

            tblobj['body'], worksheet, corrScript = self.getTableBodyForGeno(traitList=traitList, formName=mainfmName, worksheet=worksheet, newrow=newrow, corrScript=corrScript)

            workbook.close()
            objfile = open('%s.obj' % (webqtlConfig.TMPDIR+filename), 'wb')
            cPickle.dump(tblobj, objfile)
            objfile.close()
			# NL, 07/27/2010. genTableObj function has been moved from templatePage.py to webqtlUtil.py;	
            div = HT.Div(webqtlUtil.genTableObj(tblobj=tblobj, file=filename, sortby=sortby, tableID = "sortable", addIndex = "1"), corrScript, Id="sortable")
            pageTable.append(HT.TR(HT.TD(div)))
            form.append(HT.Input(name='ShowStrains',type='hidden', value =1),
                        HT.Input(name='ShowLine',type='hidden', value =1),
                        HT.P(),pageTable)

            TD_LR.append(corrHeading, info_form, HT.P(), info, form, HT.P())

            self.dict['body'] =  str(TD_LR)
			# updated by NL. Delete function generateJavaScript, move js files to dhtml.js, webqtl.js and jqueryFunction.js
            self.dict['js1'] = ''
            self.dict['title'] = 'Partial Correlation Result'

        elif self.db.type=="Publish":
        	
            containerTable.append(HT.TR(HT.TD(xlsUrl, height=40)))
            pageTable.append(HT.TR(HT.TD(containerTable)))
        	
            tblobj['header'], worksheet = self.getTableHeaderForPublish(method=self.method, worksheet=worksheet, newrow=newrow, headingStyle=headingStyle)
            newrow += 1

            sortby = self.getSortByValue( calculationMethod = self.method )
            
            corrScript = HT.Script(language="Javascript")
            corrScript.append("var corrArray = new Array();")

            tblobj['body'], worksheet, corrScript = self.getTableBodyForPublish(traitList=traitList, formName=mainfmName, worksheet=worksheet, newrow=newrow, corrScript=corrScript)

            workbook.close()

            objfile = open('%s.obj' % (webqtlConfig.TMPDIR+filename), 'wb')
            cPickle.dump(tblobj, objfile)
            objfile.close()
			# NL, 07/27/2010. genTableObj function has been moved from templatePage.py to webqtlUtil.py;
            div = HT.Div(webqtlUtil.genTableObj(tblobj=tblobj, file=filename, sortby=sortby, tableID = "sortable", addIndex = "1"), corrScript, Id="sortable")
            pageTable.append(HT.TR(HT.TD(div)))

            form.append(
            HT.Input(name='ShowStrains',type='hidden', value =1),
            HT.Input(name='ShowLine',type='hidden', value =1),
            HT.P(),pageTable)

            TD_LR.append(corrHeading, info_form, HT.P(), info, form, HT.P())

            self.dict['body'] = str(TD_LR)
			#updated by NL. Delete function generateJavaScript, move js files to dhtml.js, webqtl.js and jqueryFunction.js
            self.dict['js1'] = ''
            self.dict['title'] = 'Partial Correlation Result'

        elif self.db.type=="ProbeSet":

            tblobj['header'], worksheet = self.getTableHeaderForProbeSet(method=self.method, worksheet=worksheet, newrow=newrow, headingStyle=headingStyle)
            newrow += 1

            sortby = self.getSortByValue( calculationMethod = self.method )

            corrScript = HT.Script(language="Javascript")
            corrScript.append("var corrArray = new Array();")

            tblobj['body'], worksheet, corrScript = self.getTableBodyForProbeSet(traitList=traitList, primaryTrait=myTrait, formName=mainfmName, worksheet=worksheet, newrow=newrow, corrScript=corrScript)

            workbook.close()
            objfile = open('%s.obj' % (webqtlConfig.TMPDIR+filename), 'wb')
            cPickle.dump(tblobj, objfile)
            objfile.close()	

            '''
            #XZ, 07/07/2010: I comment out this block of code.
            WebGestaltScript = HT.Script(language="Javascript")
            WebGestaltScript.append("""
setTimeout('openWebGestalt()', 2000);
function openWebGestalt(){
	var thisForm = document['WebGestalt'];
	makeWebGestaltTree(thisForm, '%s', %d, 'edag_only.php');
}	
            """ % (mainfmName, len(traitList)))	
            '''

            #XZ: here is the table of traits
			# NL, 07/27/2010. genTableObj function has been moved from templatePage.py to webqtlUtil.py;
            div = HT.Div(webqtlUtil.genTableObj(tblobj=tblobj, file=filename, sortby=sortby, tableID = "sortable", addIndex = "1"), corrScript, Id="sortable")

            self.cursor.execute('SELECT GeneChip.GO_tree_value FROM GeneChip, ProbeFreeze, ProbeSetFreeze WHERE GeneChip.Id = ProbeFreeze.ChipId and ProbeSetFreeze.ProbeFreezeId = ProbeFreeze.Id and ProbeSetFreeze.Name = "%s"' % self.db.name)
            result = self.cursor.fetchone()

            if result:
                GO_tree_value = result[0]

            if GO_tree_value:      

                hddnWebGestalt = {
                                  'id_list':'',
                                  'correlation':'',
                                  'id_value':'', 
                                  'llid_list':'',
                                  'id_type':GO_tree_value,
                                  'idtype':'',
                                  'species':'',
                                  'list':'',
                                  'client':''}
            
                hddnWebGestalt['ref_type'] = hddnWebGestalt['id_type']
                hddnWebGestalt['cat_type'] = 'GO'
                hddnWebGestalt['significancelevel'] = 'Top10'

                if species == 'rat':
                    hddnWebGestalt['org'] = 'Rattus norvegicus'
                elif species == 'human':
                    hddnWebGestalt['org'] = 'Homo sapiens'
                elif species == 'mouse':
                    hddnWebGestalt['org'] = 'Mus musculus'
                else:
                    hddnWebGestalt['org'] = ''
            
                for key in hddnWebGestalt.keys():
                    form.append(HT.Input(name=key, value=hddnWebGestalt[key], type='hidden'))

            #XZ, 01/12/2009: create database menu for 'Add Correlation'
            self.cursor.execute("""
                select 
                    ProbeSetFreeze.FullName, ProbeSetFreeze.Id, Tissue.name
                from 
                    ProbeSetFreeze, ProbeFreeze, ProbeSetFreeze as ps2, ProbeFreeze as p2, Tissue
                where
                    ps2.Id = %d
                    and ps2.ProbeFreezeId = p2.Id
                    and ProbeSetFreeze.ProbeFreezeId = ProbeFreeze.Id
                    and (ProbeFreeze.InbredSetId = p2.InbredSetId or (ProbeFreeze.InbredSetId in (1, 3) and p2.InbredSetId in (1, 3)))
                    and p2.ChipId = ProbeFreeze.ChipId
                    and ps2.Id != ProbeSetFreeze.Id
                    and ProbeFreeze.TissueId = Tissue.Id
                    and ProbeSetFreeze.public > %d
                order by
                    ProbeFreeze.TissueId, ProbeSetFreeze.CreateTime desc
                """ % (self.db.id, webqtlConfig.PUBLICTHRESH))

            results = self.cursor.fetchall()
            dbCustomizer = HT.Select(results, name = "customizer")
            databaseMenuSub = preTissue = ""
            for item in results:
                TName, TId, TTissue = item
                if TTissue != preTissue:
                    if databaseMenuSub:
                        dbCustomizer.append(databaseMenuSub)
                    databaseMenuSub = HT.Optgroup(label = '%s mRNA ------' % TTissue)
                    preTissue = TTissue

                databaseMenuSub.append(item[:2])
            if databaseMenuSub:
                dbCustomizer.append(databaseMenuSub)
			#updated by NL. Delete function generateJavaScript, move js files to dhtml.js, webqtl.js and jqueryFunction.js
			#variables: filename, strainIds and vals are required by getquerystring function
            strainIds=self.getStrainIds(species=species, strains=_primarystrains)
            var1 = HT.Input(name="filename", value=filename, type='hidden')
            var2 = HT.Input(name="strainIds", value=strainIds, type='hidden')
            var3 = HT.Input(name="vals", value=_primaryvals, type='hidden')
            customizerButton = HT.Input(type="button", Class="button", value="Add Correlation", onClick = "xmlhttpPost('%smain.py?FormID=AJAX_table', 'sortable', (getquerystring(this.form)))" % webqtlConfig.CGIDIR)

            containerTable.append(HT.TR(HT.TD(HT.Span(var1,var2,var3,customizerButton, "with", dbCustomizer, Class="bd1 cbddf fs11"), HT.BR(), HT.BR()), style="display:none;", Class="extra_options"))

            #outside analysis part
            GCATButton = HT.Href(url="#redirect", onClick="databaseFunc(document.getElementsByName('%s')[0], 'GCAT');" % mainfmName)
            GCATButton_img = HT.Image("/images/GCAT_logo_final.jpg", name="GCAT", alt="GCAT", title="GCAT", style="border:none")
            GCATButton.append(GCATButton_img)

            ODE = HT.Href(url="#redirect", onClick="databaseFunc(document.getElementsByName('%s')[0], 'ODE');" % mainfmName)
            ODE_img = HT.Image("/images/ODE_logo_final.jpg", name="ode", alt="ODE", title="ODE", style="border:none")
            ODE.append(ODE_img)
            	
            WebGestalt = HT.Href(url="#redirect", onClick="databaseFunc(document.getElementsByName('%s')[0], 'GOTree');" % mainfmName)
            WebGestalt_img = HT.Image("/images/webgestalt_icon_final.jpg", name="webgestalt", alt="Gene Set Analysis Toolkit", title="Gene Set Analysis Toolkit", style="border:none")        
            WebGestalt.append(WebGestalt_img)
                
            LinkOutTable = HT.TableLite(cellSpacing=2,cellPadding=0,width="320",height="80", border=0, align="Left")
            if not GO_tree_value:
                LinkOutRow = HT.TR(HT.TD(GCATButton, width="50%"), HT.TD(ODE, width="50%"), align="left")
                LinkOutLabels = HT.TR(HT.TD("&nbsp;", HT.Text("GCAT"), width="50%"), HT.TD("&nbsp;",HT.Text("ODE"), width="50%"), align="left")
            else:
                LinkOutRow = HT.TR(HT.TD(WebGestalt, width="25%"), HT.TD(GCATButton, width="25%"), HT.TD(ODE, width="25%"), align="left")
                LinkOutLabels = HT.TR(HT.TD(HT.Text("Gene Set")), HT.TD("&nbsp;"*2, HT.Text("GCAT")), HT.TD("&nbsp;"*3, HT.Text("ODE")), style="display:none;", Class="extra_options")
            LinkOutTable.append(LinkOutRow,LinkOutLabels)

            containerTable.append(HT.TR(HT.TD(LinkOutTable), Class="extra_options", style="display:none;"))                   
        	
            containerTable.append(HT.TR(HT.TD(xlsUrl, HT.BR(), HT.BR(), height=40)))

            pageTable.append(HT.TR(HT.TD(containerTable)))

            pageTable.append(HT.TR(HT.TD(div)))      
            
            if species == 'human':
                heatmap = ""     	
        	
            form.append(HT.Input(name='ShowStrains',type='hidden', value =1),
                        HT.Input(name='ShowLine',type='hidden', value =1),
                        info, HT.BR(), pageTable, HT.BR())
            		
            TD_LR.append(corrHeading, info_form, HT.P(), form, HT.P())


            self.dict['body'] = str(TD_LR)
            self.dict['title'] = 'Partial Correlation Result'
			# updated by NL. Delete function generateJavaScript, move js files to dhtml.js, webqtl.js and jqueryFunction.js
            self.dict['js1'] = ''
            self.dict['js2'] = 'onLoad="pageOffset()"'
            self.dict['layer'] = self.generateWarningLayer()
            
        else:
            self.dict['body'] = ""



####################################
#                                  #
#Partial CorrelationPage Functions #
#                                  #
####################################


    def getSortByValue(self, calculationMethod):

        sortby = ("partial_pv", "up")

        if calculationMethod == "3": #XZ: literature correlation
                sortby = ("lcorr","down")
        elif calculationMethod == "4" or calculationMethod == "5": #XZ: tissue correlation
                sortby = ("tissuecorr", "down")

        return sortby


    #XZ, 3/31/2010: 
    #A[0] holds trait name.
    #A[1] holds partial correlation coefficient number.
    #A[2] holds N.
    #A[3] holds p value of partial correlation.
    def cmpPartialCorrPValue (self, A, B):
        try:
            if A[3] < B[3]:
                return -1
            elif A[3] == B[3]:
                return 0
            else:
                return 1
        except:
                return 0


    #XZ, 4/1/2010:
    #A[0] holds trait name.
    #A[1] holds N.
    #A[2] holds partial correlation coefficient number.
    #A[3] holds p value of partial correlation.
    #A[6] holds literature corr or tissue corr value.
    #Sort by literature corr or tissue corr first, then by partial corr p value.
    def cmpLitCorr(self, A, B):
        try:
            if abs(A[6]) < abs(B[6]):
                return 1
            elif abs(A[6]) == abs(B[6]):
                if A[3] < B[3]:
                    return -1
                elif A[3] == B[3]:
                    return 0
                else:
                    return 1
            else:
                return -1
        except:
            return 0


    def getPartialCorrelationsFast(self, _strains, _vals, _controlvals, nnCorr, DatabaseFileName, species, input_trait_GeneId,gene_symbol,TissueProbeSetFreezeId ):
	"""Calculates and returns correlation coefficients using data from a csv text file."""

	try:
		allcorrelations = []

		useLit = False
                if self.method == "3":
                    litCorrs = self.fetchLitCorrelations(species=species, GeneId=input_trait_GeneId, db=self.db, returnNumber=self.returnNumber)
                    useLit = True

                useTissueCorr = False
                if self.method == "4" or self.method == "5":
                    tissueCorrs = self.fetchTissueCorrelations(db=self.db,primaryTraitSymbol=gene_symbol, TissueProbeSetFreezeId=TissueProbeSetFreezeId, method=self.method, returnNumber=self.returnNumber)
                    useTissueCorr = True

                datasetFile = open(webqtlConfig.TEXTDIR+DatabaseFileName,'r')

                #XZ, 01/08/2009: read the first line
                line = datasetFile.readline()
                dataset_strains = webqtlUtil.readLineCSV(line)[1:]

                #XZ, 3/30/2010: This step is critical.
                good_dataset_strains_index = []

                for i in range(len(_strains)):
                    found_in_dataset_strains = 0
                    for j, one_dataset_strain in enumerate(dataset_strains):
                        if one_dataset_strain == _strains[i]:
                            found_in_dataset_strains = 1
                            good_dataset_strains_index.append(j)
                            break

                    if not found_in_dataset_strains:
                        good_dataset_strains_index.append(-99999)

                allTargetTraitNames = []
                allTargetTraitValues = []

                #XZ, 04/01/2009: If literature corr or tissue corr is selected,
                #XZ: there is no need to compute partial correlation for all traits.
                #XZ: If genetic corr is selected, compute partial correlation for all traits.
                for line in datasetFile:
                        trait_line = webqtlUtil.readLineCSV(line)
                        trait_name = trait_line[0]
                        trait_data = trait_line[1:]

                        if useLit:
                           if not litCorrs.has_key( trait_name ):
                                continue

                        if useTissueCorr:
                            if not tissueCorrs.has_key( trait_name ):
                                continue

                        #XZ, 04/01/2010: If useLit or useTissueCorr, and this trait should not be added,
                        #it will not go to the next step.

                        good_dataset_vals = []
                        for i in good_dataset_strains_index:
                            if i == -99999:
                                good_dataset_vals.append(None)
                            else:
                                good_dataset_vals.append( float(trait_data[i]) )

                        allTargetTraitNames.append(trait_name)
                        allTargetTraitValues.append(good_dataset_vals)

                datasetFile.close()

                if self.method in ["2", "5"]: #Spearman
                    allcorrelations = correlationFunction.determinePartialsByR(primaryVal=_vals, controlVals=_controlvals, targetVals=allTargetTraitValues, targetNames=allTargetTraitNames, method='s')
                else:
                    allcorrelations = correlationFunction.determinePartialsByR(primaryVal=_vals, controlVals=_controlvals, targetVals=allTargetTraitValues, targetNames=allTargetTraitNames)

                totalTraits = len(allcorrelations)

                if useLit or useTissueCorr:
                    for i, item in enumerate(allcorrelations):
                        if useLit:
                            allcorrelations[i].append(litCorrs[ item[0] ])
                        if useTissueCorr:
                            tempCorr, tempPValue = tissueCorrs[ item[0] ]
                            allcorrelations[i].append(tempCorr)
                            allcorrelations[i].append(tempPValue)

		return totalTraits, allcorrelations
	except:
                return 0, 0


    def getPartialCorrelationsNormal(self,  _strains, _vals, _controlvals, nnCorr, species, input_trait_GeneId, input_trait_symbol,TissueProbeSetFreezeId):
	    """Calculates and returns correlation coefficients"""

            traitdatabase, dataStartPos = self.fetchAllDatabaseData(species=species, GeneId=input_trait_GeneId, GeneSymbol=input_trait_symbol, strains=_strains, db=self.db, method=self.method, returnNumber=self.returnNumber, tissueProbeSetFreezeId=TissueProbeSetFreezeId)
            totalTraits = len(traitdatabase) #XZ, 09/18/2008: total trait number

	    allcorrelations = []

            allTargetTraitNames = []
            allTargetTraitValues = []

	    for traitdata in traitdatabase:
                traitdataName = traitdata[0]
                traitvals = traitdata[dataStartPos:]
                allTargetTraitNames.append (traitdataName)
                allTargetTraitValues.append (traitvals)

            if self.method in ["2", "5"]: #Spearman
                allcorrelations = correlationFunction.determinePartialsByR(primaryVal=_vals, controlVals=_controlvals, targetVals=allTargetTraitValues, targetNames=allTargetTraitNames, method='s')
            else:
                allcorrelations = correlationFunction.determinePartialsByR(primaryVal=_vals, controlVals=_controlvals, targetVals=allTargetTraitValues, targetNames=allTargetTraitNames)

            #XZ, 09/28/2008: if user select '3', then fetchAllDatabaseData would give us LitCorr in the [1] position
            #XZ, 09/28/2008: if user select '4' or '5', then fetchAllDatabaseData would give us Tissue Corr in the [1] position
            #XZ, 09/28/2008: and Tissue Corr P Value in the [2] position
            if input_trait_GeneId and self.db.type == "ProbeSet" and self.method in ["3", "4", "5"]:
                for i, item in enumerate(allcorrelations):
                    if self.method == "3":
                        item.append( traitdatabase[1] )
                    if self.method == "4" or self.method == "5":
                        item.append( traitdatabase[1] )
                        item.append( traitdatabase[2] )	


	    return totalTraits, allcorrelations


    def getTableHeaderForPublish(self, method=None, worksheet=None, newrow=None, headingStyle=None):

        tblobj_header = []

        if method in ["1", "3", "4"]:
            tblobj_header = [[THCell(HT.TD('', Class="fs13 fwb ffl b1 cw cbrb", nowrap="on"), sort=0), 
                              THCell(HT.TD('Record', Class="fs13 fwb ffl b1 cw cbrb", nowrap="on"), text="id", idx=1),
                              THCell(HT.TD('Phenotype', Class="fs13 fwb ffl b1 cw cbrb", nowrap="on"), text="pheno", idx=2),
                              THCell(HT.TD('Authors', Class="fs13 fwb ffl b1 cw cbrb", nowrap="on"), text="auth", idx=3),
                              THCell(HT.TD('Year', Class="fs13 fwb ffl b1 cw cbrb", nowrap="on"), text="year", idx=4),
                              THCell(HT.TD('N', Class="fs13 fwb ffl b1 cw cbrb", nowrap="on"), text="nstr", idx=5),
                              THCell(HT.TD('Partial r ', Class="fs13 fwb ffl b1 cw cbrb", nowrap="on"), text="partial_corr", idx=6),
                              THCell(HT.TD('p(partial r)', Class="fs13 fwb ffl b1 cw cbrb",nowrap='ON'), text="partial_pv", idx=7),
                              THCell(HT.TD('r ', Class="fs13 fwb ffl b1 cw cbrb", nowrap="on"), text="corr", idx=8),
                              THCell(HT.TD('p(r)', Class="fs13 fwb ffl b1 cw cbrb",nowrap='ON'), text="pv", idx=9),
                              THCell(HT.TD('delta r', Class="fs13 fwb ffl b1 cw cbrb", nowrap="on"), text="delta_corr", idx=10)]]

            for ncol, item in enumerate(["Record", "Phenotype", "Authors", "Year", "PubMedID", "N", "Partial r", "p(partial r)", "r   ", "p(r)", "delta r"]):
                worksheet.write([newrow, ncol], item, headingStyle)
                worksheet.set_column([ncol, ncol], 2*len(item))
        else:
            tblobj_header = [[THCell(HT.TD('', Class="fs13 fwb ffl b1 cw cbrb", nowrap="on"), sort=0),
                              THCell(HT.TD('Record', Class="fs13 fwb ffl b1 cw cbrb", nowrap="on"), text="id", idx=1),
                              THCell(HT.TD('Phenotype', Class="fs13 fwb ffl b1 cw cbrb", nowrap="on"), text="pheno", idx=2),
                              THCell(HT.TD('Authors', Class="fs13 fwb ffl b1 cw cbrb", nowrap="on"), text="auth", idx=3),
                              THCell(HT.TD('Year', Class="fs13 fwb ffl b1 cw cbrb", nowrap="on"), text="year", idx=4),
                              THCell(HT.TD('N', Class="fs13 fwb ffl b1 cw cbrb", nowrap="on"), text="nstr", idx=5),
                              THCell(HT.TD('Partial rho ', Class="fs13 fwb ffl b1 cw cbrb", nowrap="on"), text="partial_corr", idx=6),
                              THCell(HT.TD('p(partial rho)', Class="fs13 fwb ffl b1 cw cbrb",nowrap='ON'), text="partial_pv", idx=7),
                              THCell(HT.TD('rho ', Class="fs13 fwb ffl b1 cw cbrb", nowrap="on"), text="corr", idx=8),
                              THCell(HT.TD('p(rho)', Class="fs13 fwb ffl b1 cw cbrb",nowrap='ON'), text="pv", idx=9),
                              THCell(HT.TD('delta rho', Class="fs13 fwb ffl b1 cw cbrb", nowrap="on"), text="delta_corr", idx=10)]]

            for ncol, item in enumerate(["Record", "Phenotype", "Authors", "Year", "PubMedID", "N", "Partial rho", "p(partial rho)", "rho ", "p(rho)", "delta rho"]):
                worksheet.write([newrow, ncol], item, headingStyle)
                worksheet.set_column([ncol, ncol], 2*len(item))

        return tblobj_header, worksheet


    def getTableBodyForPublish(self, traitList, formName=None, worksheet=None, newrow=None, corrScript=None):

        tblobj_body = []

        for thisTrait in traitList:
            tr = []

            trId = str(thisTrait)

            #partial corr value could be string 'NA'
            try:
                corrScript.append('corrArray["%s"] = {corr:%1.4f};' % (trId, thisTrait.partial_corr))
            except:
                corrScript.append('corrArray["%s"] = {corr:"NA"};' % (trId))

            tr.append(TDCell(HT.TD(HT.Input(type="checkbox", Class="checkbox", name="searchResult",value=trId, onClick="highlight(this)"), nowrap="on", Class="fs12 fwn ffl b1 c222"), text=trId))

            tr.append(TDCell(HT.TD(HT.Href(text=thisTrait.name,url="javascript:showTrait('%s', '%s')" % (formName, thisTrait.name), Class="fs12 fwn"), nowrap="yes",align="center", Class="fs12 fwn b1 c222"),str(thisTrait.name), thisTrait.name))

            PhenotypeString = thisTrait.post_publication_description
            if thisTrait.confidential:
                if not webqtlUtil.hasAccessToConfidentialPhenotypeTrait(privilege=self.privilege, userName=self.userName, authorized_users=thisTrait.authorized_users):
                    PhenotypeString = thisTrait.pre_publication_description
            tr.append(TDCell(HT.TD(PhenotypeString, Class="fs12 fwn b1 c222"), PhenotypeString, PhenotypeString.upper()))

            tr.append(TDCell(HT.TD(thisTrait.authors, Class="fs12 fwn b1 c222 fsI"),thisTrait.authors, thisTrait.authors.strip().upper()))

            try:
                PubMedLinkText = myear = repr = int(thisTrait.year)
            except:
                PubMedLinkText = repr = "N/A"
                myear = 0
            if thisTrait.pubmed_id:
                PubMedLink = HT.Href(text= repr,url= webqtlConfig.PUBMEDLINK_URL % thisTrait.pubmed_id,target='_blank', Class="fs12 fwn")
            else:
                PubMedLink = repr

            tr.append(TDCell(HT.TD(PubMedLink, Class="fs12 fwn b1 c222", align='center'), repr, myear))

            repr = '%d' % thisTrait.NOverlap
            tr.append(TDCell(HT.TD(repr, Class="fs12 fwn ffl b1 c222", align='right'),repr,thisTrait.NOverlap))

            try:
                repr = '%3.3f' % thisTrait.partial_corr
                tr.append(TDCell(HT.TD(repr, Class="fs12 fwn b1 c222", align='right', nowrap="on"), repr, abs(thisTrait.partial_corr)))
            except:
                repr = 'NA'
                tr.append(TDCell(HT.TD(repr, Class="fs12 fwn ffl b1 c222", align='left'), text=repr, val=0 ))

            repr = webqtlUtil.SciFloat(thisTrait.partial_corrPValue)
            tr.append(TDCell(HT.TD(repr,nowrap='ON', Class="fs12 fwn ffl b1 c222", align='right'),repr,thisTrait.partial_corrPValue))

            repr = '%3.3f' % thisTrait.corr
            tr.append(TDCell(HT.TD(repr, Class="fs12 fwn b1 c222", align='right', nowrap="on"), repr, abs(thisTrait.corr)))

            repr = webqtlUtil.SciFloat(thisTrait.corrPValue)
            tr.append(TDCell(HT.TD(repr,nowrap='ON', Class="fs12 fwn ffl b1 c222", align='right'),repr,thisTrait.corrPValue))

            #delta
            try:
                delta = '%3.3f' % ( float(thisTrait.partial_corr) - float(thisTrait.corr) )
                tr.append(TDCell(HT.TD(delta, Class="fs12 fwn ffl b1 c222", align='right', nowrap="on"), text=delta, val=abs(float(delta)) ))            
            except:
                delta = 'NA'
                tr.append(TDCell(HT.TD(delta, Class="fs12 fwn ffl b1 c222", align='left'), text=delta, val=0 ))

            tblobj_body.append(tr)
            
            for ncol, item in enumerate([thisTrait.name, PhenotypeString, thisTrait.authors, thisTrait.year, thisTrait.pubmed_id, thisTrait.NOverlap, thisTrait.partial_corr, thisTrait.partial_corrPValue, thisTrait.corr, thisTrait.corrPValue, delta]):
                worksheet.write([newrow, ncol], str(item) )
            newrow += 1

        return tblobj_body, worksheet, corrScript


    def getTableHeaderForGeno(self, method=None, worksheet=None, newrow=None, headingStyle=None):
        tblobj_header = []

        if method in ["1", "3", "4"]:
            tblobj_header = [[THCell(HT.TD('', Class="fs13 fwb ffl b1 cw cbrb"), sort=0),
                              THCell(HT.TD('Locus', Class="fs13 fwb ffl b1 cw cbrb",align='center'), text='locus', idx=1),
                              THCell(HT.TD('Chr', Class="fs13 fwb ffl b1 cw cbrb"), text='chr', idx=2),
                              THCell(HT.TD('Megabase', Class="fs13 fwb ffl b1 cw cbrb"), text='Mb', idx=3),
                              THCell(HT.TD('N', Class="fs13 fwb ffl b1 cw cbrb",nowrap='ON'), text='nstr', idx=4),
                              THCell(HT.TD('Partial r ', Class="fs13 fwb ffl b1 cw cbrb",nowrap='ON'), text='partial_corr', idx=5),
                              THCell(HT.TD('p(partial r)', Class="fs13 fwb ffl b1 cw cbrb",nowrap='ON'), text='partial_pv', idx=6),
                              THCell(HT.TD('r ', Class="fs13 fwb ffl b1 cw cbrb",nowrap='ON'), text='corr', idx=7),
                              THCell(HT.TD('p(r)', Class="fs13 fwb ffl b1 cw cbrb",nowrap='ON'), text='pv', idx=8),
                              THCell(HT.TD('delta r', Class="fs13 fwb ffl b1 cw cbrb",nowrap='ON'), text='delta_corr', idx=9)]]

            for ncol, item in enumerate(['Locus', 'Chr', '  Mb  ', ' N ', 'Partial r', 'p(partial r)', 'r    ', 'p(r)', 'delta r' ]):
                worksheet.write([newrow, ncol], item, headingStyle)
                worksheet.set_column([ncol, ncol], 2*len(item))
        else:
            tblobj_header = [[THCell(HT.TD('', Class="fs13 fwb ffl b1 cw cbrb"), sort=0),
                              THCell(HT.TD('Locus', Class="fs13 fwb ffl b1 cw cbrb",align='center'), text='locus', idx=1),
                              THCell(HT.TD('Chr', Class="fs13 fwb ffl b1 cw cbrb"), text='chr', idx=2),
                              THCell(HT.TD('Megabase', Class="fs13 fwb ffl b1 cw cbrb"), text='Mb', idx=3),
                              THCell(HT.TD('N', Class="fs13 fwb ffl b1 cw cbrb",nowrap='ON'), text='nstr', idx=4),
                              THCell(HT.TD('Partial rho', Class="fs13 fwb ffl b1 cw cbrb",nowrap='ON'), text='partial_corr', idx=5),
                              THCell(HT.TD('p(partial rho)', Class="fs13 fwb ffl b1 cw cbrb",nowrap='ON'), text='partial_pv', idx=6),
                              THCell(HT.TD('rho ', Class="fs13 fwb ffl b1 cw cbrb", nowrap='ON'), text='corr', idx=7),
                              THCell(HT.TD('p(rho)', Class="fs13 fwb ffl b1 cw cbrb",nowrap='ON'), text='pv', idx=8),
                              THCell(HT.TD('delta rho', Class="fs13 fwb ffl b1 cw cbrb",nowrap='ON'), text='delta_corr', idx=9)]]

            for ncol, item in enumerate(['Locus', 'Chr', '  Mb  ', ' N ', 'Partial rho', 'p(partial rho)', 'rho  ', 'p(rho)', 'delta rho' ]):
                worksheet.write([newrow, ncol], item, headingStyle)
                worksheet.set_column([ncol, ncol], 2*len(item))

        return tblobj_header, worksheet



    def getTableBodyForGeno(self, traitList, formName=None, worksheet=None, newrow=None, corrScript=None):

        tblobj_body = []

        for thisTrait in traitList:
            tr = []

            trId = str(thisTrait)

            #partial corr value could be string 'NA'
            try:
                corrScript.append('corrArray["%s"] = {corr:%1.4f};' % (trId, thisTrait.partial_corr))
            except:
                corrScript.append('corrArray["%s"] = {corr:"NA"};' % (trId))

            tr.append(TDCell(HT.TD(HT.Input(type="checkbox", Class="checkbox", name="searchResult",value=trId, onClick="highlight(this)"), nowrap="on", Class="fs12 fwn ffl b1 c222"), text=trId))

            tr.append(TDCell(HT.TD(HT.Href(text=thisTrait.name,url="javascript:showTrait('%s', '%s')" % (formName, thisTrait.name), Class="fs12 fwn ffl"),align="center", Class="fs12 fwn ffl b1 c222"), text=thisTrait.name, val=thisTrait.name.upper()))

            #tr.append(TDCell(HT.TD(thisTrait.chr, Class="fs12 fwn ffl b1 c222", align='right'), text=str(thisTrait.chr)))

            try:
                Mbvalue = int(thisTrait.chr)*1000 + thisTrait.mb
            except:
                if not thisTrait.chr or not thisTrait.mb:
                    Mbvalue = 1000000
                elif thisTrait.chr.upper() == 'X':
                    Mbvalue = 20*1000 + thisTrait.mb
                else:
                    Mbvalue = ord(str(thisTrait.chr).upper()[0])*1000 + thisTrait.mb

            tr.append(TDCell( HT.TD(thisTrait.chr, Class="fs12 fwn b1 c222", align='right'), thisTrait.chr, Mbvalue) )
            tr.append(TDCell(HT.TD(thisTrait.mb, Class="fs12 fwn ffl b1 c222", align='right'), text=str(thisTrait.mb), val=Mbvalue))

            repr = '%d' % thisTrait.NOverlap
            tr.append(TDCell(HT.TD(repr, Class="fs12 fwn ffl b1 c222", align='right'),repr,thisTrait.NOverlap))

            try:
                repr='%3.3f' % thisTrait.partial_corr
                tr.append(TDCell(HT.TD(repr, Class="fs12 fwn ffl b1 c222", align='right',nowrap='ON'),repr,abs(thisTrait.partial_corr)))
            except:
                repr = 'NA'
                tr.append(TDCell(HT.TD(repr, Class="fs12 fwn ffl b1 c222", align='left'), text=repr, val=0 ))

            repr = webqtlUtil.SciFloat(thisTrait.partial_corrPValue)
            tr.append(TDCell(HT.TD(repr,nowrap='ON', Class="fs12 fwn ffl b1 c222", align='right'),repr,thisTrait.partial_corrPValue))

            repr = '%3.3f' % thisTrait.corr
            tr.append(TDCell(HT.TD(repr, Class="fs12 fwn b1 c222", align='right',nowrap='ON'), repr, abs(thisTrait.corr)))

            repr = webqtlUtil.SciFloat(thisTrait.corrPValue)
            tr.append(TDCell(HT.TD(repr,nowrap='ON', Class="fs12 fwn ffl b1 c222", align='right'),repr,thisTrait.corrPValue))

            #delta
            try:
                delta = '%3.3f' % ( float(thisTrait.partial_corr) - float(thisTrait.corr) )
                tr.append(TDCell(HT.TD(delta, Class="fs12 fwn ffl b1 c222", align='right', nowrap='ON'), text=delta, val=abs(float(delta)) ))
            except:
                delta = 'NA'
                tr.append(TDCell(HT.TD(delta, Class="fs12 fwn ffl b1 c222", align='left'), text=delta, val=0 ))

            tblobj_body.append(tr)

            for ncol, item in enumerate([thisTrait.name, thisTrait.chr, thisTrait.mb, thisTrait.NOverlap, thisTrait.partial_corr, thisTrait.partial_corrPValue, thisTrait.corr, thisTrait.corrPValue, delta]):
                worksheet.write([newrow, ncol], item)
            newrow += 1

        return tblobj_body, worksheet, corrScript


    def getTableHeaderForProbeSet(self, method=None, worksheet=None, newrow=None, headingStyle=None):

        tblobj_header = []

        if method in ["1","3","4"]:
            tblobj_header = [[THCell(HT.TD(' ', Class="fs13 fwb ffl b1 cw cbrb",nowrap='ON'), sort=0),
                              THCell(HT.TD('Record',HT.BR(),HT.BR(), Class="fs13 fwb ffl b1 cw cbrb"), text="id", idx=1),
                              THCell(HT.TD('','Symbol',HT.BR(),HT.BR(), Class="fs13 fwb ffl b1 cw cbrb"), text="symbol", idx=2),
                              THCell(HT.TD('','Description',HT.BR(),HT.BR(), Class="fs13 fwb ffl b1 cw cbrb"), text="desc", idx=3),
                              #XZ, 12/09/2008: sort chr
                              THCell(HT.TD('','Chr',HT.BR(),HT.BR(), Class="fs13 fwb ffl b1 cw cbrb"), text="chr", idx=4),
                              THCell(HT.TD('','Mb',HT.BR(),HT.BR(), Class="fs13 fwb ffl b1 cw cbrb"), text="Mb", idx=5),
                              THCell(HT.TD('Mean',HT.BR(),'Expr',HT.BR(), Class="fs13 fwb ffl b1 cw cbrb"), text="mean", idx=6),
                              THCell(HT.TD('N',HT.BR(),HT.BR(), Class="fs13 fwb ffl b1 cw cbrb",nowrap='ON'), text="nstr", idx=7),
                              THCell(HT.TD(HT.Href(
                                                   text = HT.Span('Sample',HT.BR(), 'Partial r', HT.Sup('  ?', style="color:#f00"),HT.BR(), Class="fs13 fwb ffl cw"),
                                                   target = '_blank',
                                                   url = "/correlationAnnotation.html#genetic_r"), 
                                           Class="fs13 fwb ffl b1 cw cbrb", nowrap='ON'), text="partial_corr", idx=8),
                              THCell(HT.TD(HT.Href(
                                                   text = HT.Span('Sample',HT.BR(), 'p(partial r)', HT.Sup('  ?', style="color:#f00"),HT.BR(), Class="fs13 fwb ffl cw"),
                                                   target = '_blank',
                                                   url = "/correlationAnnotation.html#genetic_p_r"),
                                           Class="fs13 fwb ffl b1 cw cbrb", nowrap='ON'), text="partial_pv", idx=9),
                              THCell(HT.TD(HT.Href(
                                                   text = HT.Span('Sample',HT.BR(), 'r', HT.Sup('  ?', style="color:#f00"),HT.BR(), Class="fs13 fwb ffl cw"),
                                                   target = '_blank',
                                                   url = "/correlationAnnotation.html#genetic_r"),
                                           Class="fs13 fwb ffl b1 cw cbrb", nowrap='ON'), text="corr", idx=10),
                              THCell(HT.TD(HT.Href(
                                                   text = HT.Span('Sample',HT.BR(), 'p(r)', HT.Sup('  ?', style="color:#f00"),HT.BR(), Class="fs13 fwb ffl cw"),
                                                   target = '_blank',
                                                   url = "/correlationAnnotation.html#genetic_p_r"),
                                           Class="fs13 fwb ffl b1 cw cbrb", nowrap='ON'), text="pv", idx=11),
                              THCell(HT.TD('delta',HT.BR(), 'r', HT.BR(), Class="fs13 fwb ffl b1 cw cbrb",nowrap='ON'), text="delta_corr", idx=12),
                              THCell(HT.TD(HT.Href(
                                                   text = HT.Span('Pubmed',HT.BR(), 'r', HT.Sup('  ?', style="color:#f00"),HT.BR(), Class="fs13 fwb ffl cw"),
                                                   target = '_blank',
                                                   url = "/correlationAnnotation.html#literatureCorr"),
                                           Class="fs13 fwb ffl b1 cw cbrb", nowrap='ON'), text="lcorr", idx=13),
                              #XZ, 09/22/2008: tissue correlation
                              THCell(HT.TD(HT.Href(
                                                   text = HT.Span('Tissue',HT.BR(), 'r', HT.Sup('  ?', style="color:#f00"),HT.BR(), Class="fs13 fwb ffl cw"),
                                                   target = '_blank',
                                                   url = "/correlationAnnotation.html#tissue_r"),
                                           Class="fs13 fwb ffl b1 cw cbrb", nowrap='ON'), text="tissuecorr", idx=14),
                              THCell(HT.TD(HT.Href(
                                                   text = HT.Span('Tissue',HT.BR(), 'p(r)', HT.Sup('  ?', style="color:#f00"),HT.BR(), Class="fs13 fwb ffl cw"),
                                                   target = '_blank',
                                                   url = "/correlationAnnotation.html#tissue_p_r"),
                                           Class="fs13 fwb ffl b1 cw cbrb", nowrap='ON'), text="tissuepvalue", idx=15)]]

            for ncol, item in enumerate(['Record', 'Gene ID', 'Symbol', 'Description', 'Chr', 'Megabase', 'Mean Expr', 'N ', 'Sample Partial r', 'Sample p(partial r)', 'Sample r', 'Sample p(r)', 'delta r', 'Lit Corr', 'Tissue r', 'Tissue p(r)']):
                worksheet.write([newrow, ncol], item, headingStyle)
                worksheet.set_column([ncol, ncol], 2*len(item))
        else:
            tblobj_header = [[THCell(HT.TD(' ', Class="fs13 fwb ffl b1 cw cbrb",nowrap='ON'), sort=0),
                              THCell(HT.TD('Record',HT.BR(),HT.BR(), Class="fs13 fwb ffl b1 cw cbrb"), text="id", idx=1),
                              THCell(HT.TD('','Symbol',HT.BR(),HT.BR(), Class="fs13 fwb ffl b1 cw cbrb"), text="symbol", idx=2),
                              THCell(HT.TD('','Description',HT.BR(),HT.BR(), Class="fs13 fwb ffl b1 cw cbrb"), text="desc", idx=3),
                              THCell(HT.TD('','Chr',HT.BR(),HT.BR(), Class="fs13 fwb ffl b1 cw cbrb"), text="chr", idx=4),
                              THCell(HT.TD('','Mb',HT.BR(),HT.BR(), Class="fs13 fwb ffl b1 cw cbrb"), text="Mb", idx=5),
                              THCell(HT.TD('Mean',HT.BR(),'Expr',HT.BR(), Class="fs13 fwb ffl b1 cw cbrb"), text="mean", idx=6),
                              THCell(HT.TD('N',HT.BR(),HT.BR(), Class="fs13 fwb ffl b1 cw cbrb",nowrap='ON'), text="nstr", idx=7),
                              THCell(HT.TD(HT.Href(
                                                   text = HT.Span('Sample',HT.BR(), 'Partial rho', HT.Sup('  ?', style="color:#f00"),HT.BR(), Class="fs13 fwb ffl cw"),
                                                   target = '_blank',
                                                   url = "/correlationAnnotation.html#genetic_rho"), 
                                           Class="fs13 fwb ffl b1 cw cbrb", nowrap='ON'), text="partial_corr", idx=8),
                              THCell(HT.TD(HT.Href(
                                                   text = HT.Span('Sample',HT.BR(), 'p(partial rho)', HT.Sup('  ?', style="color:#f00"),HT.BR(), Class="fs13 fwb ffl cw"),
                                                   target = '_blank',
                                                   url = "/correlationAnnotation.html#genetic_p_rho"),
                                           Class="fs13 fwb ffl b1 cw cbrb", nowrap='ON'), text="partial_pv", idx=9),
                              THCell(HT.TD(HT.Href(
                                                   text = HT.Span('Sample',HT.BR(), 'rho', HT.Sup('  ?', style="color:#f00"),HT.BR(), Class="fs13 fwb ffl cw"),
                                                   target = '_blank',
                                                   url = "/correlationAnnotation.html#genetic_r"),
                                           Class="fs13 fwb ffl b1 cw cbrb", nowrap='ON'), text="corr", idx=10),
                              THCell(HT.TD(HT.Href(
                                                   text = HT.Span('Sample',HT.BR(), 'p(rho)', HT.Sup('  ?', style="color:#f00"),HT.BR(), Class="fs13 fwb ffl cw"),
                                                   target = '_blank',
                                                   url = "/correlationAnnotation.html#genetic_p_r"),
                                           Class="fs13 fwb ffl b1 cw cbrb", nowrap='ON'), text="pv", idx=11),
                              THCell(HT.TD('delta',HT.BR(),'rho', HT.BR(), Class="fs13 fwb ffl b1 cw cbrb",nowrap='ON'), text="delta_corr", idx=12),
                              THCell(HT.TD(HT.Href(
                                                   text = HT.Span('Pubmed',HT.BR(), 'r', HT.Sup('  ?', style="color:#f00"),HT.BR(), Class="fs13 fwb ffl cw"),
                                                   target = '_blank',
                                                   url = "/correlationAnnotation.html#literatureCorr"),
                                           Class="fs13 fwb ffl b1 cw cbrb", nowrap='ON'), text="lcorr", idx=13),
                              #XZ, 09/22/2008: tissue correlation
                              THCell(HT.TD(HT.Href(
                                                   text = HT.Span('Tissue',HT.BR(), 'rho', HT.Sup('  ?', style="color:#f00"),HT.BR(), Class="fs13 fwb ffl cw"),
                                                   target = '_blank',
                                                   url = "/correlationAnnotation.html#tissue_rho"),
                                           Class="fs13 fwb ffl b1 cw cbrb", nowrap='ON'), text="tissuecorr", idx=14),
                              THCell(HT.TD(HT.Href(
                                                   text = HT.Span('Tissue',HT.BR(), 'p(rho)', HT.Sup('  ?', style="color:#f00"),HT.BR(), Class="fs13 fwb ffl cw"),
                                                   target = '_blank',
                                                   url = "/correlationAnnotation.html#tissue_p_rho"),
                                           Class="fs13 fwb ffl b1 cw cbrb", nowrap='ON'), text="tissuepvalue", idx=15)]]

            for ncol, item in enumerate(['Record', 'Gene ID', 'Symbol', 'Description', 'Chr', 'Megabase', 'Mean Expr', 'N ', 'Sample Partial rho', 'Sample p(partial rho)', 'Sample rho', 'Sample p(rho)', 'delta rho', 'Pubmed r', 'Tissue rho', 'Tissue p(rho)']):
                worksheet.write([newrow, ncol], item, headingStyle)
                worksheet.set_column([ncol, ncol], 2*len(item))

        return tblobj_header, worksheet


    def getTableBodyForProbeSet(self, traitList=[], primaryTrait=None, formName=None, worksheet=None, newrow=None, corrScript=None):

        tblobj_body = []

        for thisTrait in traitList:

            if thisTrait.symbol:
                pass
            else:
                thisTrait.symbol = "N/A"

            if thisTrait.geneid:
                symbolurl = HT.Href(text=thisTrait.symbol,target='_blank',url="http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?db=gene&cmd=Retrieve&dopt=Graphics&list_uids=%s" % thisTrait.geneid, Class="fs12 fwn")
            else:
                symbolurl = HT.Href(text=thisTrait.symbol,target='_blank',url="http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?CMD=search&DB=gene&term=%s" % thisTrait.symbol, Class="fs12 fwn")

            tr = []

            trId = str(thisTrait)

            #partial corr value could be string 'NA'
            try:
                corrScript.append('corrArray["%s"] = {corr:%1.4f};' % (trId, thisTrait.partial_corr))
            except:
                corrScript.append('corrArray["%s"] = {corr:"NA"};' % (trId))

            #XZ, 12/08/2008: checkbox
            tr.append(TDCell(HT.TD(HT.Input(type="checkbox", Class="checkbox", name="searchResult",value=trId, onClick="highlight(this)"), nowrap="on", Class="fs12 fwn ffl b1 c222"), text=trId))

            #XZ, 12/08/2008: probeset name
            tr.append(TDCell(HT.TD(HT.Href(text=thisTrait.name,url="javascript:showTrait('%s', '%s')" % (formName,thisTrait.name), Class="fs12 fwn"), Class="fs12 fwn b1 c222"), thisTrait.name, thisTrait.name.upper()))

            #XZ, 12/08/2008: gene symbol
            tr.append(TDCell(HT.TD(symbolurl, Class="fs12 fwn b1 c222 fsI"),thisTrait.symbol, thisTrait.symbol.upper()))

            #XZ, 12/08/2008: description
            #XZ, 06/05/2009: Rob asked to add probe target description
            description_string = str(thisTrait.description).strip()
            target_string = str(thisTrait.probe_target_description).strip()

            description_display = ''

            if len(description_string) > 1 and description_string != 'None':
                description_display = description_string
            else:
                description_display = thisTrait.symbol

            if len(description_display) > 1 and description_display != 'N/A' and len(target_string) > 1 and target_string != 'None':
                description_display = description_display + '; ' + target_string.strip()

            tr.append(TDCell(HT.TD(description_display, Class="fs12 fwn b1 c222"), description_display, description_display))

            #XZ, 12/08/2008: Mbvalue is used for sorting
            try:
                Mbvalue = int(thisTrait.chr)*1000 + thisTrait.mb
            except:
                if not thisTrait.chr or not thisTrait.mb:
                    Mbvalue = 1000000
                elif thisTrait.chr.upper() == 'X':
                    Mbvalue = 20*1000 + thisTrait.mb
                else:
                    Mbvalue = ord(str(thisTrait.chr).upper()[0])*1000 + thisTrait.mb

            #XZ, 12/08/2008: chromosome number
            #XZ, 12/10/2008: use Mbvalue to sort chromosome
            tr.append(TDCell( HT.TD(thisTrait.chr, Class="fs12 fwn b1 c222", align='right'), thisTrait.chr, Mbvalue) )

            #XZ, 12/08/2008: Rob wants 6 digit precision, and we have to deal with that the mb could be None
            if not thisTrait.mb:
                tr.append(TDCell(HT.TD(thisTrait.mb, Class="fs12 fwn b1 c222",align='right'), thisTrait.mb, Mbvalue))
            else:
                tr.append(TDCell(HT.TD('%.6f' % thisTrait.mb, Class="fs12 fwn b1 c222", align='right'), thisTrait.mb, Mbvalue))

            #XZ, 01/12/08: This SQL query is much faster.
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
            tr.append(TDCell(HT.TD(repr, Class="fs12 fwn ffl b1 c222", align='right', nowrap='ON'),repr, mean))

            #XZ: number of overlaped cases for partial corr
            repr = '%d' % thisTrait.NOverlap
            tr.append(TDCell(HT.TD(repr, Class="fs12 fwn ffl b1 c222", align='right'),repr,thisTrait.NOverlap))

            #XZ: sample partial correlation
            try:
                repr='%3.3f' % thisTrait.partial_corr
                tr.append(TDCell(HT.TD(repr, Class="fs12 fwn ffl b1 c222", align='right', nowrap='ON'),repr,abs(thisTrait.partial_corr)))
            except:
                repr = 'NA'
                tr.append(TDCell(HT.TD(repr, Class="fs12 fwn ffl b1 c222", align='left'), text=repr, val=0 ))

            #XZ: p value of genetic partial correlation
            repr = webqtlUtil.SciFloat(thisTrait.partial_corrPValue)
            tr.append(TDCell(HT.TD(repr,nowrap='ON', Class="fs12 fwn ffl b1 c222", align='right'),repr,thisTrait.partial_corrPValue))

            repr = '%3.3f' % thisTrait.corr
            tr.append(TDCell(HT.TD(repr, Class="fs12 fwn b1 c222", align='right',nowrap='ON'), repr, abs(thisTrait.corr)))

            repr = webqtlUtil.SciFloat(thisTrait.corrPValue)
            tr.append(TDCell(HT.TD(repr,nowrap='ON', Class="fs12 fwn ffl b1 c222", align='right'),repr,thisTrait.corrPValue))

            #delta
            try:
                delta = '%3.3f' % ( float(thisTrait.partial_corr) - float(thisTrait.corr) )
                tr.append(TDCell(HT.TD(delta, Class="fs12 fwn ffl b1 c222", align='right', nowrap='ON'), text=delta, val=abs(float(delta)) ))
            except:
                delta = 'NA'
                tr.append(TDCell(HT.TD(delta, Class="fs12 fwn ffl b1 c222", align='left'), text=delta, val=0 ))

            #XZ, 12/08/2008: literature correlation
            LCorr = 0.0
            LCorrStr = "N/A"
            if hasattr(thisTrait, 'LCorr') and thisTrait.LCorr:
                LCorr = thisTrait.LCorr
                LCorrStr = "%2.3f" % thisTrait.LCorr
            tr.append(TDCell(HT.TD(LCorrStr, Class="fs12 fwn b1 c222", align='right'), LCorrStr, abs(LCorr)))

            #XZ, 09/22/2008: tissue correlation.
            TCorr = 0.0
            TCorrStr = "N/A"
            #XZ, 11/18/2010: need to pass two gene symbols
            if hasattr(thisTrait, 'tissueCorr') and thisTrait.tissueCorr:
                TCorr = thisTrait.tissueCorr
                TCorrStr = "%2.3f" % thisTrait.tissueCorr
		#NL, 07/19/2010: add a new parameter rankOrder for js function 'showTissueCorrPlot'
                rankOrder =thisTrait.rankOrder
                TCorrPlotURL = "javascript:showTissueCorrPlot('%s','%s','%s',%d)" %(formName, primaryTrait.symbol, thisTrait.symbol,rankOrder)
                tr.append(TDCell(HT.TD(HT.Href(text=TCorrStr, url=TCorrPlotURL, Class="fs12 fwn ff1"), Class="fs12 fwn ff1 b1 c222", align='right'), TCorrStr, abs(TCorr) ))
            else:
                tr.append(TDCell(HT.TD(TCorrStr, Class="fs12 fwn b1 c222", align='right'), TCorrStr, abs(TCorr)))

            #XZ, 12/08/2008: p value of tissue correlation
            TPValue = 1.0
            TPValueStr = "N/A"
            if hasattr(thisTrait, 'tissueCorr') and thisTrait.tissueCorr: #XZ, 09/22/2008: thisTrait.tissuePValue can't be used here because it could be 0
                TPValue = thisTrait.tissuePValue
                TPValueStr = "%2.3f" % thisTrait.tissuePValue
            tr.append(TDCell(HT.TD(TPValueStr, Class="fs12 fwn b1 c222", align='right'), TPValueStr, abs(TPValue) ))

            tblobj_body.append(tr)

            for ncol, item in enumerate([thisTrait.name, thisTrait.geneid, thisTrait.symbol, thisTrait.description, thisTrait.chr, thisTrait.mb, mean, thisTrait.NOverlap, thisTrait.partial_corr, thisTrait.partial_corrPValue, thisTrait.corr, thisTrait.corrPValue, delta, LCorrStr, TCorrStr, TPValueStr]):
                worksheet.write([newrow, ncol], item)

            newrow += 1

        return tblobj_body, worksheet, corrScript


    def getFormForPrimaryAndControlTraits (self, primaryTrait, controlTraits):

        info_form = HT.Form(cgi= os.path.join(webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE), enctype='multipart/form-data', name='showDatabase', submit=HT.Input(type='hidden'))

        hddn = {'FormID':'showDatabase', 'database':'_', 'ProbeSetID':'_', 'CellID':'_' }#XZ: These four parameters are required by javascript function showDatabase2.
        
        for key in hddn.keys():
            info_form.append(HT.Input(name=key, value=hddn[key], type='hidden'))

        info_form.append(HT.Paragraph("Primary Trait", Class="subtitle"), '\n')

        primaryTraitTable = HT.TableLite(cellSpacing=4,cellPadding=0,width="90%",border=0)
        descriptionString = primaryTrait.genHTML(dispFromDatabase=1)
        if primaryTrait.db.type == 'Publish' and primaryTrait.confidential:
            descriptionString = primaryTrait.genHTML(dispFromDatabase=1, privilege=self.privilege, userName=self.userName, authorized_users=primaryTrait.authorized_users)
        primaryTraitTable.append(HT.TR(HT.TD(HT.Href(text='%s' % descriptionString, url="javascript:showDatabase2('%s','%s','%s')" % (primaryTrait.db.name,primaryTrait.name,primaryTrait.cellid), Class="fs12 fwn") )))

        info_form.append(primaryTraitTable)

        info_form.append(HT.Paragraph("Control Traits", Class="subtitle"), '\n')

        controlTraitsTable = HT.TableLite(cellSpacing=4,cellPadding=0,width="90%",border=0)

        seq = 1

        ## Generate the listing table for control traits
        for thisTrait in controlTraits:
            descriptionString = thisTrait.genHTML(dispFromDatabase=1)
            if thisTrait.db.type == 'Publish' and thisTrait.confidential:
                descriptionString = thisTrait.genHTML(dispFromDatabase=1, privilege=self.privilege, userName=self.userName, authorized_users=thisTrait.authorized_users)
            controlTraitsTable.append(HT.TR(HT.TD("%d."%seq,align="right",width=10),
                                            HT.TD(HT.Href(text='%s' % descriptionString,url="javascript:showDatabase2('%s','%s','%s')" % (thisTrait.db.name,thisTrait.name,thisTrait.cellid), Class="fs12 fwn") )))
            seq += 1

        info_form.append(controlTraitsTable)

        return info_form
