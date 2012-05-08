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
# Last updated by NL 2010/02/11

#!/usr/bin/python
# networkGraph.py
# Author: Stephen Pitts
# 6/2/2004
#
# a script to take a matrix of data from a WebQTL job and generate a
# graph using the neato package from GraphViz
#
# See graphviz for documentation of the parameters
#


#from mod_python import apache, util, Cookie
#import cgi
import tempfile
import os
import time
import sys
import cgitb
import string

from htmlgen import HTMLgen2 as HT

from base.templatePage import templatePage
import networkGraphUtils
from base import webqtlConfig
from utility import webqtlUtil
from base.webqtlTrait import webqtlTrait
import compareCorrelates.trait as smpTrait
from GraphPage import GraphPage
from networkGraphPageBody import networkGraphPageBody
from correlationMatrix.tissueCorrelationMatrix import tissueCorrelationMatrix

cgitb.enable()


class networkGraphPage(templatePage):

    def __init__(self,fd,InputData=None):

        templatePage.__init__(self, fd)

        if not self.openMysql():
            return
            
        if not fd.genotype:
            fd.readGenotype()
                
        self.searchResult = fd.formdata.getvalue('searchResult')

        self.tissueProbeSetFeezeId = "1" #XZ, Jan 03, 2010: currently, this dataset is "UTHSC Illumina V6.2 RankInv B6 D2 average CNS GI average (May 08)"
        TissueCorrMatrixObject = tissueCorrelationMatrix(tissueProbeSetFreezeId=self.tissueProbeSetFeezeId)

        if type("1") == type(self.searchResult):
            self.searchResult = string.split(self.searchResult, '\t')
        
        if (not self.searchResult or (len(self.searchResult) < 2)):
            heading = 'Network Graph'
            detail = ['You need to select at least two traits in order to generate Network Graph.']
            self.error(heading=heading,detail=detail)
            print 'Content-type: text/html\n'
            self.write()
            return
        
        if self.searchResult:
            if len(self.searchResult) > webqtlConfig.MAXCORR:
                heading = 'Network Graph'
                detail = ['In order to display Network Graph properly, Do not select more than %d traits for Network Graph.' % webqtlConfig.MAXCORR]
                self.error(heading=heading,detail=detail)
                print 'Content-type: text/html\n'
                self.write()
                return
            else:    
                pass
                
            traitList = []
            traitDataList = []
            
            for item in self.searchResult:
                thisTrait = webqtlTrait(fullname=item, cursor=self.cursor)
                thisTrait.retrieveInfo()
                thisTrait.retrieveData(fd.strainlist)
                traitList.append(thisTrait)
                traitDataList.append(thisTrait.exportData(fd.strainlist))
                   
        else:
            heading = 'Network Graph'
            detail = [HT.Font('Error : ',color='red'),HT.Font('Error occurs while retrieving data from database.',color='black')]
            self.error(heading=heading,detail=detail)
            print 'Content-type: text/html\n'
            self.write()
            return

        NNN = len(traitList)
        
        if NNN < 2:
            templatePage.__init__(self, fd)
            heading = 'Network Graph'
            detail = ['You need to select at least two traits in order to generate a Network Graph']
            print 'Content-type: text/html\n'
            self.write()
            return
        else:
            pearsonArray = [([0] * (NNN))[:] for i in range(NNN)]
            spearmanArray = [([0] * (NNN))[:] for i in range(NNN)]
            GeneIdArray = []
            GeneSymbolList = [] #XZ, Jan 03, 2011: holds gene symbols for calculating tissue correlation
            traitInfoArray = []

            i = 0
            nnCorr = len(fd.strainlist)
            for i, thisTrait in enumerate(traitList):
                names1 = [thisTrait.db.name, thisTrait.name, thisTrait.cellid]
                for j, thisTrait2 in enumerate(traitList):
                    names2 = [thisTrait2.db.name, thisTrait2.name, thisTrait2.cellid]
                    if j < i:
                        corr,nOverlap = webqtlUtil.calCorrelation(traitDataList[i],traitDataList[j],nnCorr)
                        pearsonArray[i][j] = corr
                        pearsonArray[j][i] = corr
                    elif j == i:
                        pearsonArray[i][j] = 1.0
                        spearmanArray[i][j] = 1.0
                    else:
                        corr,nOverlap = webqtlUtil.calCorrelationRank(traitDataList[i],traitDataList[j],nnCorr)
                        spearmanArray[i][j] = corr
                        spearmanArray[j][i] = corr
                    
                GeneId1 = None
                tmpSymbol = None
                if thisTrait.db.type == 'ProbeSet':
                    try:
                        GeneId1 = int(thisTrait.geneid)
                    except:
                        GeneId1 = 0
                    if thisTrait.symbol:
                        tmpSymbol = thisTrait.symbol.lower()
                GeneIdArray.append(GeneId1)
                GeneSymbolList.append(tmpSymbol)

            _traits = []
            _matrix = []

            for i in range(NNN):
                turl = webqtlConfig.CGIDIR + webqtlConfig.SCRIPTFILE + '?FormID=showDatabase&database=%s&ProbeSetID=%s' % (traitList[i].db.name, traitList[i].name)
                if traitList[i].cellid:
                    turl += "&CellID=%s" % traitList[i].cellid
                    
                if traitList[i].db.type == 'ProbeSet':
                    if traitList[i].symbol:
                        _symbol = traitList[i].symbol
                    else:
                        _symbol = 'unknown'
                elif traitList[i].db.type == 'Publish':
                    _symbol = traitList[i].name
                    if traitList[i].confidential:
                        if webqtlUtil.hasAccessToConfidentialPhenotypeTrait(privilege=self.privilege, userName=self.userName, authorized_users=traitList[i].authorized_users):
                            if traitList[i].post_publication_abbreviation:
                                _symbol = traitList[i].post_publication_abbreviation
                        else:
                            if traitList[i].pre_publication_abbreviation:
                                _symbol = traitList[i].pre_publication_abbreviation
                    else:
                        if traitList[i].post_publication_abbreviation:
                            _symbol = traitList[i].post_publication_abbreviation

                #XZ, 05/26/2009: Xiaodong add code for Geno data
                elif traitList[i].db.type == 'Geno':
                    _symbol = traitList[i].name
                else:
                    _symbol = traitList[i].description
                    #####if this trait entered by user
                    if _symbol.__contains__('entered'):
                        _symbol = _symbol[:_symbol.index('entered')]
                    #####if this trait generaged by genenetwork
                    elif _symbol.__contains__('generated'):
                        _symbol = _symbol[_symbol.rindex(':')+1:]
                
                newTrait = smpTrait.Trait(name=str(traitList[i]), href=turl, symbol=_symbol)
                newTrait.color = "black"
                _traits.append(newTrait)
                
                for j in range(i+1, NNN):
                    dataPoint = smpTrait.RawPoint(i, j)
                    dataPoint.spearman = spearmanArray[i][j]
                    dataPoint.pearson = pearsonArray[i][j]

                    #XZ: get literature correlation info.
                    if GeneIdArray[i] and GeneIdArray[j]:
                        if GeneIdArray[i] == GeneIdArray[j]:
                            dataPoint.literature = 1
                        else:
                            self.cursor.execute("SELECT Value from LCorrRamin3 WHERE (GeneId1 = %d and GeneId2 = %d) or (GeneId1 = %d and GeneId2 = %d)" % (GeneIdArray[i], GeneIdArray[j], GeneIdArray[j], GeneIdArray[i]))
                            try:    
                                dataPoint.literature = self.cursor.fetchone()[0]
                            except:
                                dataPoint.literature = 0
                    else:
                        dataPoint.literature = 0

                    #XZ: get tissue correlation info
                    if GeneSymbolList[i] and GeneSymbolList[j]:
                        dataPoint.tissue = 0
                        geneSymbolPair = []
                        geneSymbolPair.append(GeneSymbolList[i])
                        geneSymbolPair.append(GeneSymbolList[j])
                        corrArray,pvArray = TissueCorrMatrixObject.getCorrPvArrayForGeneSymbolPair(geneNameLst=geneSymbolPair)
                        if corrArray[1][0]:
                            dataPoint.tissue = corrArray[1][0]
                    else:
                        dataPoint.tissue = 0

                    _matrix.append(dataPoint)
        
            OrigDir = os.getcwd()

            sessionfile = fd.formdata.getvalue('session')
            
            inputFilename = fd.formdata.getvalue('inputFile')

            #If there is no sessionfile generate one and dump all matrix/trait values
            if not sessionfile:
                filename = webqtlUtil.generate_session()    
                webqtlUtil.dump_session([_matrix, _traits], os.path.join(webqtlConfig.TMPDIR, filename + '.session'))
                sessionfile = filename
            
            startTime = time.time()
            
            #Build parameter dictionary used by networkGraphPage class using buildParamDict function
            params = networkGraphUtils.buildParamDict(fd, sessionfile)
    
            nodes = len(_traits)
            rawEdges = len(_matrix)
            
            if params["tune"] == "yes":
                params = networkGraphUtils.tuneParamDict(params, nodes, rawEdges)
              
            matrix = networkGraphUtils.filterDataMatrix(_matrix, params)
            
            optimalNode = networkGraphUtils.optimalRadialNode(matrix)
            
            if not inputFilename:
                inputFilename = tempfile.mktemp()
            
            inputFilename = webqtlConfig.IMGDIR + inputFilename.split("/")[2]
                                           
            #writes out 4 graph files for exporting
            graphFile = "/image/" + networkGraphUtils.writeGraphFile(matrix, _traits, inputFilename, params)
            
            networkGraphUtils.processDataMatrix(matrix, params)

            edges = 0

            for edge in matrix:
                if edge.value != 0:
                    edges +=1

            for trait in _traits:
                trait.name = networkGraphUtils.fixLabel(trait.name)
            
            RootDir = webqtlConfig.IMGDIR
            RootDirURL = "/image/"                  


                  
                        #This code writes the datafile that the graphviz function runNeato uses to generate the 
                        #"digraph" file that defines the graphs parameters
            datafile = networkGraphUtils.writeNeatoFile(matrix=matrix, traits=_traits, filename=inputFilename, GeneIdArray=GeneIdArray, p=params)
            
            #Generate graph in various file types                      
            layoutfile = networkGraphUtils.runNeato(datafile, "dot", "dot", params["gType"]) # XZ, 09/11/2008: add module name
            # ZS 03/04/2010 This second output file (layoutfile_pdf) is rotated by 90 degrees to prevent an issue with pdf output being cut off at the edges
            layoutfile_pdf = networkGraphUtils.runNeato(datafile + "_pdf", "dot", "dot", params["gType"]) # ZS 03/04/2010
            pngfile = networkGraphUtils.runNeato(layoutfile, "png", "png", params["gType"]) 
            mapfile = networkGraphUtils.runNeato(layoutfile, "cmapx", "cmapx", params["gType"])# XZ, 09/11/2008: add module name    
            giffile = networkGraphUtils.runNeato(layoutfile, "gif", "gif", params["gType"])# XZ, 09/11/2008:add module name
            psfile = networkGraphUtils.runNeato(layoutfile_pdf, "ps", "ps", params["gType"])# XZ, 09/11/2008: add module name
            pdffile = networkGraphUtils.runPsToPdf(psfile, params["width"], params["height"])# XZ, 09/11/2008: add module name
            
                        #This generates text files in XGGML (standardized graphing language) and plain text
                        #so the user can create his/her own graphs in a program like Cytoscape
                    
            htmlfile1 = datafile + ".html"
            htmlfile2 = datafile + ".graph.html"

            os.chdir(OrigDir)

            #This generates the graph in various image formats
            giffile = RootDirURL + giffile
            pngfile = RootDirURL + pngfile
            pdffile = RootDirURL + pdffile
            endTime = time.time()
            totalTime = endTime - startTime

            os.chdir(RootDir)

            page2 = GraphPage(giffile, mapfile)
            page2.writeToFile(htmlfile2)
            
            #This generates the HTML for the body of the Network Graph page
            page1 = networkGraphPageBody(fd, matrix, _traits, htmlfile2, giffile, pdffile, nodes, edges, rawEdges, totalTime, params, page2.content, graphFile, optimalNode)
            
            #Adds the javascript colorSel to the body to allow line color selection
            self.dict["js1"] = '<SCRIPT SRC="/javascript/colorSel.js"></SCRIPT><BR>'   
            #self.dict["js1"] += '<SCRIPT SRC="/javascript/networkGraph.js"></SCRIPT>' 
                        
            #Set body of current templatePage to body of the templatePage networkGraphPage                        
            self.dict['body'] = page1.dict['body']                


