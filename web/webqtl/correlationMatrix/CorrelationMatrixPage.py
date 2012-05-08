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
# Last updated by NL 2011/02/14

import os
import string
from htmlgen import HTMLgen2 as HT
import sys
import time
import numarray
import numarray.linear_algebra as la
import piddle as pid
import math

from base.templatePage import templatePage
from base import webqtlConfig
from base.webqtlTrait import webqtlTrait
from utility import webqtlUtil
from utility import Plot



# XZ, 09/09/2008: After adding several traits to collection, click "Correlation Matrix" button,
# XZ, 09/09/2008: This class will generate what you see.
#########################################
#      Correlation Matrix Page
#########################################

class CorrelationMatrixPage(templatePage):

    def __init__(self,fd,InputData=None):

        templatePage.__init__(self, fd)

        self.dict['title'] = 'Correlation Matrix'

        if not self.openMysql():
            return
            
        if not fd.genotype:
            fd.readGenotype()
            fd.strainlist = fd.f1list + fd.strainlist
            
        #self.searchResult = fd.formdata.getvalue('searchResult')
        self.oldSearchResult = fd.formdata.getvalue('oldSearchResult')
        
        if self.oldSearchResult:
            try:
                self.searchResult = fd.formdata.getvalue('oldSearchResult')
            except:
            	self.searchResult = fd.formdata.getvalue('searchResult')
        
        else:
        	self.searchResult = fd.formdata.getvalue('searchResult')
        
        if not self.searchResult:
            heading = 'Correlation Matrix'
            detail = ['You need to select at least two traits in order to generate correlation matrix.']
            self.error(heading=heading,detail=detail)
            return
        if type("1") == type(self.searchResult):
            self.searchResult = [self.searchResult]
        
        if self.searchResult:
            #testvals,names,dbInfos = self.getAllSearchResult(fd,self.searchResult)
            if len(self.searchResult) > webqtlConfig.MAXCORR:
                heading = 'Correlation Matrix'
                detail = ['In order to display Correlation Matrix properly, Do not select more than %d traits for Correlation Matrix.' % webqtlConfig.MAXCORR]
                self.error(heading=heading,detail=detail)
                return

            #XZ, 7/22/2009: this block is not necessary
            #elif len(self.searchResult) > 40:
            #    noPCA = 1
            #else:
            #    noPCA = 0
    
            traitList = []
            traitDataList = []
            for item in self.searchResult:
                thisTrait = webqtlTrait(fullname=item, cursor=self.cursor)
                thisTrait.retrieveInfo()
                thisTrait.retrieveData(fd.strainlist)
                traitList.append(thisTrait)
                traitDataList.append(thisTrait.exportData(fd.strainlist))
                
        else:
            heading = 'Correlation Matrix'
            detail = [HT.Font('Error : ',color='red'),HT.Font('Error occurs while retrieving data FROM database.',color='black')]
            self.error(heading=heading,detail=detail)
            return

        NNN = len(traitList)
        
        if NNN == 0:
            heading = "Correlation Matrix"
            detail = ['No trait was selected for %s data set. No matrix generated.' % self.data.RISet]
            self.error(heading=heading,detail=detail)
            return
        elif NNN < 2:
            heading = 'Correlation Matrix'
            detail = ['You need to select at least two traits in order to generate correlation matrix.']
            self.error(heading=heading,detail=detail)
            return
        else:
        	
        	
        	
            corArray = [([0] * (NNN+1))[:] for i in range(NNN+1)]
            pearsonArray = [([0] * (NNN))[:] for i in range(NNN)]
            spearmanArray = [([0] * (NNN))[:] for i in range(NNN)]
            corArray[0][0] = 'Correlation'
            TD_LR = HT.TD(colspan=2,width="100%",bgColor='#eeeeee')
            form = HT.Form( cgi= os.path.join(webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE), enctype='multipart/form-data', name='showDatabase', submit=HT.Input(type='hidden'))
            hddn = {'FormID':'showDatabase', 'ProbeSetID':'_','database':'_',
            'CellID':'_','ProbeSetID2':'_','database2':'_','CellID2':'_',
            'newNames':fd.formdata.getvalue("newNames", "_"), 
            'RISet':fd.RISet,'ShowStrains':'ON','ShowLine':'ON', 'rankOrder':'_', 
            "allstrainlist":string.join(fd.strainlist, " "), 'traitList':string.join(self.searchResult, "\t")}
            if fd.incparentsf1:
                hddn['incparentsf1']='ON'
            	    
            for key in hddn.keys():
                form.append(HT.Input(name=key, value=hddn[key], type='hidden'))
           
            for item in self.searchResult:
            	form.append(HT.Input(name='oldSearchResult', value=str(item), type='hidden'))
            
            traiturls = []
            traiturls2 = []
            shortNames = []
            verboseNames = []
            verboseNames2 = []
            verboseNames3 = []
            abbreviation = ''
            
            #dbInfo.ProbeSetID = ProbeSetID
            #dbInfo.CellID = CellID
            for i, thisTrait in enumerate(traitList):
                _url = "javascript:showDatabase2('%s','%s','%s');" % (thisTrait.db.name, thisTrait.name, thisTrait.cellid)
                #_text = 'Trait%d: ' % (i+1)+str(thisTrait)
                _text = 'Trait %d: ' % (i+1)+thisTrait.displayName()
                                
                if thisTrait.db.type == 'Geno':
                    _shortName = 'Genotype'
                    abbreviation = 'Genotype'
                    _verboseName = 'Locus %s' % (thisTrait.name)
                    _verboseName2 = 'Chr %s @ %s Mb' % (thisTrait.chr, '%2.3f' % thisTrait.mb)
                    _verboseName3 = ''
                elif thisTrait.db.type == 'Publish':
                    if thisTrait.post_publication_abbreviation:
                        AbbreviationString = thisTrait.post_publication_abbreviation
                    else:
                        AbbreviationString = ''
                    if thisTrait.confidential:
                        if not webqtlUtil.hasAccessToConfidentialPhenotypeTrait(privilege=self.privilege, userName=self.userName, authorized_users=thisTrait.authorized_users):
                            if thisTrait.pre_publication_abbreviation:
                                AbbreviationString = thisTrait.pre_publication_abbreviation
                            else:
                                AbbreviationString = ''
                    _shortName = 'Phenotype: %s' % (AbbreviationString)  
                    _verboseName2 = ''
                    _verboseName3 = ''
                    if thisTrait.pubmed_id:
                        _verboseName = 'PubMed %d: ' % thisTrait.pubmed_id
                    else: 
                        _verboseName = 'Unpublished '
                    _verboseName += 'RecordID/%s' % (thisTrait.name)
                    PhenotypeString = thisTrait.post_publication_description
                    if thisTrait.confidential:
                        if not webqtlUtil.hasAccessToConfidentialPhenotypeTrait(privilege=self.privilege, userName=self.userName, authorized_users=thisTrait.authorized_users):
                            PhenotypeString = thisTrait.pre_publication_description
                    _verboseName2 = 'Phenotype: %s' % (PhenotypeString)
                    if thisTrait.authors:
                        a1 = string.split(thisTrait.authors,',')[0]
                        while a1[0] == '"' or a1[0] == "'" :
                            a1 = a1[1:]
                            _verboseName += ' by '
                            _verboseName += HT.Italic('%s, and colleagues' % (a1))
                elif thisTrait.db.type == 'Temp':
                    abbreviation = ''
                    _shortName = thisTrait.name
                    if thisTrait.description:
                        _verboseName = thisTrait.description
                    else:
                        _verboseName = 'Temp'
                    _verboseName2 = ''
                    _verboseName3 = ''
                else:
                    abbreviation = thisTrait.symbol
                    _shortName = 'Symbol: %s ' % thisTrait.symbol
                    _verboseName = thisTrait.symbol
                    _verboseName2 = ''
                    _verboseName3 = ''
                    if thisTrait.chr and thisTrait.mb:
                        _verboseName += ' on Chr %s @ %s Mb' % (thisTrait.chr,thisTrait.mb)
                    if thisTrait.description:
                        _verboseName2 = '%s' % (thisTrait.description)
                    if thisTrait.probe_target_description:
                        _verboseName3 = '%s' % (thisTrait.probe_target_description)         
                                
                cururl = HT.Href(text=_text, url=_url,Class='fs12') 
                cururl2 = HT.Href(text='Trait%d' % (i+1),url=_url,Class='fs12')
                traiturls.append(cururl)
                traiturls2.append(cururl2)
                shortName = HT.Div(id="shortName_" + str(i), style="display:none")
                shortName.append(_shortName)
                shortNames.append(shortName)
                verboseName = HT.Div(id="verboseName_" + str(i), style="display:none")
                verboseName.append(_verboseName)
                verboseNames.append(verboseName)
                verboseName2 = HT.Div(id="verboseName2_" + str(i), style="display:none")
                verboseName2.append(_verboseName2)
                verboseNames2.append(verboseName2)
                verboseName3 = HT.Div(id="verboseName3_" + str(i), style="display:none")
                verboseName3.append(_verboseName3)
                verboseNames3.append(verboseName3)
                    

                                
                corArray[i+1][0] = 'Trait%d: ' % (i+1)+str(thisTrait) + '/' + str(thisTrait) + ': ' + abbreviation + '/' + str(thisTrait) + ': ' + str(_verboseName) + ' : ' + str(_verboseName2) + ' : ' + str(_verboseName3)
                corArray[0][i+1] = 'Trait%d: ' % (i+1)+str(thisTrait)
                
            corMatrixHeading = HT.Paragraph('Correlation Matrix', Class="title")
            
            tbl = HT.TableLite(Class="collap", border=0, cellspacing=1, 
                cellpadding=5, width='100%')
            row1 = HT.TR(HT.TD(Class="fs14 fwb ffl b1 cw cbrb"),
                HT.TD('Spearman Rank Correlation (rho)', Class="fs14 fwb ffl b1 cw cbrb", colspan= NNN+1,align="center")
                )
            row2 = HT.TR(
                HT.TD("P e a r s o n &nbsp;&nbsp;&nbsp; r", rowspan= NNN+1,Class="fs14 fwb ffl b1 cw cbrb", width=10,align="center"),
                HT.TD(Class="b1", width=300))
            for i in range(NNN):
                row2.append(HT.TD(traiturls2[i], Class="b1", align="center"))
            tbl.append(row1,row2)

            nOverlapTrait =9999            
            nnCorr = len(fd.strainlist)
            for i, thisTrait in enumerate(traitList):
                newrow = HT.TR()
                newrow.append(HT.TD(traiturls[i], shortNames[i], verboseNames[i], verboseNames2[i], 
                                    verboseNames3[i], Class="b1"))
                names1 = [thisTrait.db.name, thisTrait.name, thisTrait.cellid]
                for j, thisTrait2 in enumerate(traitList):
                    names2 = [thisTrait2.db.name, thisTrait2.name, thisTrait2.cellid]
                    if j < i:
                        corr,nOverlap = webqtlUtil.calCorrelation(traitDataList[i],traitDataList[j],nnCorr)
                        
                        rank = fd.formdata.getvalue("rankOrder", "0")
                        
                        if nOverlap < nOverlapTrait:
                            nOverlapTrait = nOverlap
                        if corr > 0.7:
                            fontcolor="red"
                        elif corr > 0.5:
                            fontcolor="#FF6600"
                        elif corr < -0.7:
                            fontcolor="blue"
                        elif corr < -0.5:
                            fontcolor="#009900"
                        else:
                            fontcolor ="#000000"

                        pearsonArray[i][j] = corr
                        pearsonArray[j][i] = corr
                        if corr!= 0.0:
                            corArray[i+1][j+1] = '%2.3f/%d' % (corr,nOverlap)
                            thisurl = HT.Href(text=HT.Font('%2.3f'% corr,HT.BR(),'%d' % nOverlap ,color=fontcolor, Class="fs11 fwn"),url = "javascript:showCorrelationPlot2(db='%s',ProbeSetID='%s',CellID='%s',db2='%s',ProbeSetID2='%s',CellID2='%s',rank='%s')" % (names1[0], names1[1], names1[2], names2[0], names2[1], names2[2], rank))
                        else:
                            corArray[i+1][j+1] = '---/%d' % nOverlap
                            thisurl = HT.Font('---',HT.BR(), '%d' % nOverlap)
                        
                        newrow.append(HT.TD(thisurl,Class="b1",NOWRAP="ON",align="middle"))
                    elif j == i:
                        corr,nOverlap = webqtlUtil.calCorrelation(traitDataList[i],traitDataList[j],nnCorr)
                        pearsonArray[i][j] = 1.0
                        spearmanArray[i][j] = 1.0
                        corArray[i+1][j+1] = '%2.3f/%d' % (corr,nOverlap)
                        nOverlap = webqtlUtil.calCorrelation(traitDataList[i],traitDataList[j],nnCorr)[1]
                        newrow.append(HT.TD(HT.Href(text=HT.Font(HT.Italic("n"),HT.BR(),str(nOverlap),Class="fs11 fwn b1",align="center", color="000000"), url="javascript:showDatabase2('%s','%s','%s')" % (thisTrait.db.name, thisTrait.name, thisTrait.cellid)), bgColor='#cccccc', align="center", Class="b1", NOWRAP="ON"))
                    else:       
                        corr,nOverlap = webqtlUtil.calCorrelationRank(traitDataList[i],traitDataList[j],nnCorr)
                        
                        rank = fd.formdata.getvalue("rankOrder", "1")
                        
                        if corr > 0.7:
                            fontcolor="red"
                        elif corr > 0.5:
                            fontcolor="#FF6600"
                        elif corr < -0.7:
                            fontcolor="blue"
                        elif corr < -0.5:
                            fontcolor="#009900"
                        else:
                            fontcolor ="#000000"
                        spearmanArray[i][j] = corr
                        spearmanArray[j][i] = corr
                        if corr!= 0.0:
                            corArray[i+1][j+1] = '%2.3f/%d' % (corr,nOverlap)
                            thisurl = HT.Href(text=HT.Font('%2.3f'% corr,HT.BR(),'%d' % nOverlap ,color=fontcolor, Class="fs11 fwn"),url = "javascript:showCorrelationPlot2(db='%s',ProbeSetID='%s',CellID='%s',db2='%s',ProbeSetID2='%s',CellID2='%s',rank='%s')" % (names1[0], names1[1], names1[2], names2[0], names2[1], names2[2], rank))
                        else:
                            corArray[i+1][j+1] = '---/%d' % nOverlap
                            thisurl = HT.Span('---',HT.BR(), '%d' % nOverlap, Class="fs11 fwn")
                        newrow.append(HT.TD(thisurl,Class="b1", NOWRAP="ON",align="middle"))
                tbl.append(newrow)
                
            info = HT.Blockquote('Lower left cells list Pearson product-moment correlations; upper right cells list Spearman rank order correlations. Each cell also contains the n of cases. Values higher than 0.7 are displayed in ',HT.Font('red', color='red'),'; those between 0.5 and 0.7 in  ',HT.Font('orange', color='#FF6600'),'; Values lower than -0.7 are in ',HT.Font('blue', color='blue'),'; between -0.5 and -0.7 in ',HT.Font('green', color='#009900'),'. Select any cell to generate a scatter plot. Select trait labels for more information.', Class="fs13 fwn")
            
            exportbutton = HT.Input(type='button',  name='export', value='Export', onClick="exportText(allCorrelations);",Class="button")
            shortButton = HT.Input(type='button' ,name='dispShort',value=' Short Labels ', onClick="displayShortName();",Class="button")
            verboseButton = HT.Input(type='button' ,name='dispVerbose',value=' Long Labels ', onClick="displayVerboseName();", Class="button")
            form.append(HT.Blockquote(tbl,HT.P(),shortButton,verboseButton,exportbutton))
            TD_LR.append(corMatrixHeading,info,form,HT.P())

            #if noPCA:
            #    TD_LR.append(HT.Blockquote('No PCA is computed if more than 32 traits are selected.'))

            #print corArray
            exportScript = """
                <SCRIPT language=JavaScript>
                var allCorrelations = %s;
                </SCRIPT>

            """
            exportScript = exportScript % str(corArray)
            self.dict['js1'] = exportScript+'<SCRIPT SRC="/javascript/correlationMatrix.js"></SCRIPT><BR>'
            self.dict['body'] = str(TD_LR)
            
            #don't calculate PCA while number exceed 32
            #if noPCA:
            #    return

            #XZ, 7/22/2009: deal with PCA stuff
            #Only for Array Data
            
            if NNN > 2:
    
                traitname = map(lambda X:str(X.name), traitList)
                
                #generate eigenvalues
                
                # import sys
                sys.argv=[" "]
                # import numarray
                # import numarray.linear_algebra as la
                #spearmanEigen = eigenvectors(array(spearmanArray))
                pearsonEigen = la.eigenvectors(numarray.array(pearsonArray))
                #spearmanEigenValue,spearmanEigenVectors = self.sortEigenVectors(spearmanEigen)
                pearsonEigenValue,pearsonEigenVectors = self.sortEigenVectors(pearsonEigen)
		
				
		"""
		for i in range(len(pearsonEigenValue)):
			if type(pearsonEigenValue[i]).__name__ == 'complex':
				pearsonEigenValue[i] = pearsonEigenValue[i].real
		for i in range(len(pearsonEigenVectors)):
			for j in range(len(pearsonEigenVectors[i])):
				if type(pearsonEigenVectors[i][j]).__name__ == 'complex':
					pearsonEigenVectors[i][j] = pearsonEigenVectors[i][j].real
				if type(pearsonEigenVectors[i][j]).__name__ == 'complex':
					pearsonEigenVectors[i][j] = pearsonEigenVectors[i][j].real		      
		"""
        
		if type(pearsonEigenValue[0]).__name__ == 'complex':
		   pass
		else:	
            	   traitHeading = HT.Paragraph('PCA Traits',align='left', Class="title")  
                   
        	   tbl2 = self.calcPCATraits(traitDataList=traitDataList, nnCorr=nnCorr, NNN=NNN, pearsonEigenValue=pearsonEigenValue, 
                                         pearsonEigenVectors=pearsonEigenVectors, form=form, fd=fd)
                   #Buttons on search page
                   #mintmap = HT.Input(type='button' ,name='mintmap',value='Multiple Mapping', onClick="databaseFunc(this.form,'showIntMap');",Class="button")
                   addselect = HT.Input(type='button' ,name='addselect',value='Add to Collection', onClick="addRmvSelection('%s', this.form, 'addToSelection');"  % fd.RISet,Class="button")
                   selectall = HT.Input(type='button' ,name='selectall',value='Select All', onClick="checkAll(this.form);",Class="button")
                   reset = HT.Input(type='reset',name='',value='Select None',Class="button")
                   updateNames = HT.Input(type='button', name='updateNames',value='Update Trait Names', onClick="editPCAName(this.form);", Class="button")
                   chrMenu = HT.Input(type='hidden',name='chromosomes',value='all')
                   
                   """
                   #need to be refined
                   if fd.genotype.Mbmap:
                       scaleMenu = HT.Select(name='scale')
                       scaleMenu.append(tuple(["Genetic Map",'morgan']))
                       scaleMenu.append(tuple(["Physical Map",'physic']))
                   else:
                       scaleMenu = ""
                   """    
                   
                   tbl2.append(HT.TR(HT.TD(HT.P(),chrMenu,updateNames,selectall,reset,addselect,colspan=3)))
        	   form.append(HT.P(),traitHeading,HT.Blockquote(tbl2))
                
                   plotHeading1 = HT.Paragraph('Scree Plot', Class="title") 
                   TD_LR.append(plotHeading1)
                   img1 = self.screePlot(NNN=NNN, pearsonEigenValue=pearsonEigenValue)
    
                   TD_LR.append(HT.Blockquote(img1))
                   
                   plotHeading2 = HT.Paragraph('Factor Loadings Plot', Class="title")
                   TD_LR.append(plotHeading2)
                   img2 = self.factorLoadingsPlot(pearsonEigenVectors=pearsonEigenVectors, traitList=traitList)
                   
                   TD_LR.append(HT.Blockquote(img2))                      

        self.dict['body'] = str(TD_LR)
    
    def screePlot(self, NNN=0, pearsonEigenValue=None):

        c1 = pid.PILCanvas(size=(700,500))
        Plot.plotXY(canvas=c1, dataX=range(1,NNN+1), dataY=pearsonEigenValue, rank=0, labelColor=pid.blue,plotColor=pid.red, symbolColor=pid.blue, XLabel='Factor Number', connectdot=1,YLabel='Percent of Total Variance %', title='Pearson\'s R Scree Plot')
        filename= webqtlUtil.genRandStr("Scree_")
        c1.save(webqtlConfig.IMGDIR+filename, format='gif')
        img=HT.Image('/image/'+filename+'.gif',border=0)
        
        return img
    
    def factorLoadingsPlot(self, pearsonEigenVectors=None, traitList=None):
        
        traitname = map(lambda X:str(X.name), traitList)
        c2 = pid.PILCanvas(size=(700,500))
        Plot.plotXY(c2, pearsonEigenVectors[0],pearsonEigenVectors[1], 0, dataLabel = traitname, labelColor=pid.blue, plotColor=pid.red, symbolColor=pid.blue,XLabel='Factor (1)', connectdot=1, YLabel='Factor (2)', title='Factor Loadings Plot (Pearson)', loadingPlot=1)
        filename= webqtlUtil.genRandStr("FacL_")
        c2.save(webqtlConfig.IMGDIR+filename, format='gif')
        img = HT.Image('/image/'+filename+'.gif',border=0)
     
        return img
    
    def calcPCATraits(self, traitDataList=None, nnCorr=0, NNN=0, pearsonEigenValue=None, pearsonEigenVectors=None, form=None, fd=None):  
       """
       This function currently returns the html to be displayed instead of the traits themselves. Need to fix later.
       """
    
       detailInfo = string.split(self.searchResult[0],':')
    
       self.sameProbeSet = 'yes'
       for item in self.searchResult[1:]:
           detailInfo2 = string.split(item,':')
           if detailInfo[0] != detailInfo2[0] or detailInfo[1] != detailInfo2[1]:
               self.sameProbeSet = None
               break
                
       for item in traitDataList:
           if len(item) != nnCorr:
               return
       infoStrains = []
       infoStrainsPos = []
       dataArray  = [[] for i in range(NNN)]
    
       for i in range(len(traitDataList[0])):
           currentStrain = 1
           for j in range(NNN):
               if not traitDataList[j][i]:
                   currentStrain = 0
                   break
           if currentStrain == 1:
               infoStrains.append(fd.strainlist[i])
               infoStrainsPos.append(i)
               for j in range(NNN): 
                   dataArray[j].append(traitDataList[j][i])

    
       self.cursor.execute('delete Temp, TempData FROM Temp, TempData WHERE Temp.DataId = TempData.Id and UNIX_TIMESTAMP()-UNIX_TIMESTAMP(CreateTime)>%d;' % webqtlConfig.MAXLIFE)

       StrainIds = []
       for item in infoStrains:
           self.cursor.execute('SELECT Strain.Id FROM Strain,StrainXRef, InbredSet WHERE Strain.Name="%s" and Strain.Id = StrainXRef.StrainId and StrainXRef.InbredSetId = InbredSet.Id and InbredSet.Name = "%s"' % (item, fd.RISet))
           StrainIds.append('%d' % self.cursor.fetchone()[0])
    
       """
       #minimal 12 overlapping strains      
       if len(dataArray[0]) < 12:
           form.append(HT.P(),traitHeading,HT.Blockquote(HT.Paragraph('The number of overlapping strains is less than 12, no PCA scores computed.',align='left')))
           self.dict['body'] = str(TD_LR)
           return
       """
       dataArray = self.zScore(dataArray)
       dataArray = numarray.array(dataArray)
       dataArray2 = numarray.dot(pearsonEigenVectors,dataArray)
    
       tbl2 = HT.TableLite(cellSpacing=2,cellPadding=0,border=0, width="100%")
    
       ct0 = time.localtime(time.time())
       ct = time.strftime("%B/%d %H:%M:%S",ct0)
       if self.sameProbeSet:
           newDescription = 'PCA Traits generated at %s from %s' % (ct,detailInfo[1])
       else:
           newDescription = 'PCA Traits generated at %s from traits selected' % ct
    

       j = 1
       self.cursor.execute('SELECT Id  FROM InbredSet WHERE Name = "%s"' % fd.RISet)
       InbredSetId = self.cursor.fetchall()[0][0]
       user_ip = fd.remote_ip
       if fd.formdata.getvalue("newNames"):
           newNames = fd.formdata.getvalue("newNames").split(",")
       else:
       	   newNames = 0
       
       for item in dataArray2:
           if pearsonEigenValue[j-1] < 100.0/NNN:
               break
           
           if (newNames == 0):
               description  = '%s : PC%02d' % (newDescription, j)              
           else:    
               description = '%s : %s' % (newDescription, newNames[j-1])           	   
                  
           self.cursor.execute('SELECT max(id) FROM TempData')
           try:
               DataId = self.cursor.fetchall()[0][0] + 1
           except:
               DataId = 1
           newProbeSetID = webqtlUtil.genRandStr("PCA_Tmp_")
           self.cursor.execute('insert into Temp(Name,description, createtime,DataId,InbredSetId,IP) values(%s,%s,Now(),%s,%s,%s)' ,(newProbeSetID, description, DataId,InbredSetId,user_ip))
        
           k = 0    
           for StrainId in StrainIds:
               self.cursor.execute('insert into TempData(Id, StrainId, value) values(%s,%s,%s)' % (DataId, StrainId, item[k]*(-1.0)))
               k += 1
           setDescription = HT.Div(id="pcaTrait%s" % j)
           descriptionLink = HT.Href(text=description, url="javascript:showDatabase2('Temp','%s','')" % newProbeSetID, Class="fwn")
           descriptionEdit = HT.Input(type='text', value='', name='editName%s' % j)
           
           #onBlur='editPDAName(this.form, %s);' % j
           
           setDescription.append(descriptionLink)
           setDescription.append(descriptionEdit)
           
           traitName = "%s:%s" % ('Temp',newProbeSetID)
           tbl2.append(HT.TR(HT.TD("%d."%j,align="right",valign="top"),HT.TD(HT.Input(type="checkbox", Class="checkbox", name="searchResult",value=traitName),valign="top",width=50),HT.TD(setDescription)))
           j += 1
    
       return tbl2
    
    def zScore(self,dataArray):
        NN = len(dataArray[0])
        if NN < 10:
            return dataArray
        else:
            i = 0
            for data in dataArray:
                N = len(data)
                S = reduce(lambda x,y: x+y, data, 0.)
                SS = reduce(lambda x,y: x+y*y, data, 0.)
                mean = S/N
                var = SS - S*S/N
                stdev = math.sqrt(var/(N-1))
                data2 = map(lambda x:(x-mean)/stdev,data)
                dataArray[i] = data2
                i += 1
            return dataArray
    
    def sortEigenVectors(self,vector):
        try:
            eigenValues = vector[0].tolist()
            eigenVectors = vector[1].tolist()
            combines = []
            i = 0
            for item in eigenValues:
                combines.append([eigenValues[i],eigenVectors[i]])
                i += 1
            combines.sort(webqtlUtil.cmpEigenValue)
            A = []
            B = []
            for item in combines:
                A.append(item[0])
                B.append(item[1])
            sum = reduce(lambda x,y: x+y, A, 0.0)
            A = map(lambda x:x*100.0/sum, A) 
            return [A,B]
        except:
            return []

