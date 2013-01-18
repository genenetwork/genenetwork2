from __future__ import absolute_import, print_function, division

from base.trait import GeneralTrait
from base import data_set  #import create_dataset

from pprint import pformat as pf

import time
import string
import math
#from math import *
#import piddle
import sys
import os
import httplib
import urllib

from htmlgen import HTMLgen2 as HT
from utility import Plot, Bunch
from wqflask.interval_analyst import GeneUtil
from base.trait import GeneralTrait
from base import data_set
from base.templatePage import templatePage
from utility import webqtlUtil, helper_functions
from base import webqtlConfig
from dbFunction import webqtlDatabaseFunction
from base.GeneralObject import GeneralObject

import reaper
import cPickle
from utility.THCell import THCell
from utility.TDCell import TDCell


class MarkerRegression(object):

    #def __init__(self, start_vars):
    #
    #    print("[mike] Now start_vars is:", pf(start_vars))
    #
    #    self.dataset = data_set.create_dataset(start_vars['dataset_name'])
    #    self.this_trait = GeneralTrait(dataset=self.dataset.name,
    #                                   name=start_vars['trait_id'],
    #                                   cellid=None)
    #    
    #    print("self.this_trait is: ", pf(self.this_trait))
    #    print("self.dataset is: ", pf(self.dataset))

    def __init__(self, start_vars):
        #templatePage.__init__(self, fd)

        #if not self.openMysql():
        #    return

        #print("start_vars are: ", pf(start_vars))

        helper_functions.get_dataset_and_trait(self, start_vars)

        self.num_perm = int(start_vars['num_perm'])

        # Passed in by the form (user might have edited)
        #samples = start_vars['allsamples'].split()
        
        self.samples = []   # Want only ones with values
        self.vals = []
        self.variances = []
        
        assert start_vars['display_all_lrs'] in ('True', 'False')
        self.display_all_lrs = True if start_vars['display_all_lrs'] == 'True' else False
        
        for sample in self.dataset.group.samplelist:
            value = start_vars['value:' + sample]
            variance = start_vars['variance:' + sample]
            if variance.strip().lower() == 'x':
                variance = 0
            else:
                variance = float(variance)
            if value.strip().lower() != 'x':
                self.samples.append(str(sample))
                self.vals.append(float(value))
                self.variances.append(variance)

        #self.initializeParameters(start_vars)

        #filename= webqtlUtil.genRandStr("Itvl_")
        #ChrList,ChrNameOrderIdDict,ChrOrderIdNameDict,ChrtLengthMbList= self.getChrNameOrderIdLength(RISet=fd.RISet)

        if False: # For PLINK

            traitInfoList = string.split(string.strip(fd.identification),':')
            probesetName = string.strip(traitInfoList[-1])
            plinkOutputFileName= webqtlUtil.genRandStr("%s_%s_"%(fd.RISet,probesetName))

            # get related values from fd.allTraitData; the format of 'allTraitValueDict'is {strainName1: value=-0.2...}
            fd.readData()
            allTraitValueDict = fd.allTraitData

            #automatically generate pheno txt file for PLINK
            self.genPhenoTxtFileForPlink(phenoFileName=plinkOutputFileName,RISetName=fd.RISet,probesetName=probesetName, valueDict=allTraitValueDict)
            # os.system full path is required for input and output files; specify missing value is -9999
            plink_command = '%splink/plink --noweb --ped %splink/%s.ped --no-fid --no-parents --no-sex --no-pheno --map %splink/%s.map --pheno %s/%s.txt --pheno-name %s --missing-phenotype -9999 --out %s%s --assoc ' % (webqtlConfig.HTMLPATH, webqtlConfig.HTMLPATH,  fd.RISet, webqtlConfig.HTMLPATH, fd.RISet, webqtlConfig.TMPDIR, plinkOutputFileName, probesetName, webqtlConfig.TMPDIR, plinkOutputFileName)

            os.system(plink_command)

            if fd.identification:
                heading2 = HT.Paragraph('Trait ID: %s' % fd.identification)
                heading2.__setattr__("class","subtitle")
                self.dict['title'] = '%s: Genome Association' % fd.identification
            else:
                heading2 = ""
                self.dict['title'] = 'Genome Association'

            if fd.traitInfo:
                symbol,chromosome,MB = string.split(fd.traitInfo,'\t')
                heading3 = HT.Paragraph('[ ',HT.Strong(HT.Italic('%s' % symbol,id="green")),' on Chr %s @ %s Mb ]' % (chromosome,MB))
            else:
                heading3 = ""

            heading = HT.Paragraph('Trait Data Entered for %s Set' % fd.RISet)
            heading.__setattr__("class","title")

            # header info part:Trait Data Entered for HLC Set & Trait ID:
            headerdiv = HT.TR(HT.TD(heading, heading2,heading3, width='45%',valign='top', align='left', bgColor='#eeeeee'))

            self.ChrList=ChrList  # get chr name from '1' to 'X'
            self.ChrLengthMbList = ChrLengthMbList

            # build plink result dict based on chr, key is chr name, value is in list type including Snpname, bp and pvalue info
            plinkResultDict={}
            count,minPvalue,plinkResultDict =self.getPlinkResultDict(outputFileName=plinkOutputFileName,thresholdPvalue=self.pValue,ChrOrderIdNameDict=ChrOrderIdNameDict)

            # if can not find results which are matched with assigned p-value, system info will show up
            if count >0:

                #for genome association report table
                reportTable=""
                # sortable table object
                resultstable,tblobj,bottomInfo = self.GenReportForPLINK(ChrNameOrderIdDict=ChrNameOrderIdDict, RISet=fd.RISet,plinkResultDict=plinkResultDict,thresholdPvalue=self.pValue,chrList=self.ChrList)

                # creat object for result table for sort function
                objfile = open('%s.obj' % (webqtlConfig.TMPDIR+filename), 'wb')
                cPickle.dump(tblobj, objfile)
                objfile.close()

                sortby = ("Index", "up")
                reportTable =HT.Div(webqtlUtil.genTableObj(tblobj=tblobj, file=filename, sortby=sortby, tableID = "sortable", addIndex = "0"), Id="sortable")

                descriptionTable =  HT.TableLite(border=0, cellpadding=0, cellspacing=0)
                descriptionTable.append(HT.TR(HT.TD(reportTable, colspan=3)))
                descriptionTable.append(HT.TR(HT.TD(HT.BR(),HT.BR())))
                descriptionTable.append(bottomInfo)

                # get each chr's length
                self.ChrLengthMbList = map(lambda x: x/1000000.0, self.ChrLengthMbList) # change unit from bp to mb
                self.ChrLengthMbSum = reduce(lambda x, y:x+y, self.ChrLengthMbList, 0.0)# get total length of all chrs
                if self.ChrLengthMbList:
                    self.GraphInterval = self.ChrLengthMbSum/(len(self.ChrLengthMbList)*12) #Empirical Mb interval
                else:
                    self.GraphInterval = 1

                # for human data, there's no CM value
                self.ChrLengthCMList = []
                self.ChrLengthCMSum = 0

                # begin: common part with human data
                intCanvas = pid.PILCanvas(size=(self.graphWidth,self.graphHeight))
                gifmap = self.plotIntMappingForPLINK(fd, intCanvas, startMb = self.startMb, endMb = self.endMb, plinkResultDict=plinkResultDict)

                intCanvas.save(os.path.join(webqtlConfig.IMGDIR, filename), format='png')
                intImg=HT.Image('/image/'+filename+'.png', border=0, usemap='#WebQTLImageMap')

                TD_LR = HT.TR(HT.TD(HT.Blockquote(gifmap,intImg, HT.P()), bgColor='#eeeeee', height = 200))
                self.dict['body'] = str(headerdiv)+str(TD_LR)+str(resultstable)+str(HT.TR(HT.TD(descriptionTable)))

            else:
                heading = "Genome Association"
                detail = ['There is no association with marker that meets this criteria. Please provide a less stringend threshold. The minimun p-value is %s.'%minPvalue]
                self.error(heading=heading,detail=detail)
                return

        else: # QTLreaper result
            #if not fd.genotype:
            #    fd.readData()
            #
            #fd.parentsf14regression = fd.formdata.getvalue('parentsf14regression')
            #weightedRegression = fd.formdata.getvalue('applyVarianceSE')

            #if fd.parentsf14regression and fd.genotype_2:
            #    _genotype = fd.genotype_2
            #else:
            #print("[black]:", self.genotype)

            #_strains, _vals, _vars, N = fd.informativeStrains(_genotype.prgy, weightedRegression)

            #if fd.identification:
            #    heading2 = HT.Paragraph('Trait ID: %s' % fd.identification)
            #    heading2.__setattr__("class","subtitle")
            #    self.dict['title'] = '%s: Genome Association' % fd.identification
            #else:
            #    heading2 = ""
            #    self.dict['title'] = 'Genome Association'

            #if fd.traitInfo:
            #    symbol, chromosome, MB = string.split(fd.traitInfo,'\t')
            #    heading3 = HT.Paragraph('[ ',HT.Strong(HT.Italic('%s' % symbol,id="green")),' on Chr %s @ %s Mb ]' % (chromosome,MB))
            #else:
            #    heading3 = ""

            ### Todo in 2013: Don't allow marker regression in show trait page when number of samples
            ### with values < 5

            #if N < webqtlConfig.KMININFORMATIVE:
            #    heading = "Genome Association"
            #    detail = ['Fewer than %d strain data were entered for %s data set. No mapping attempted.' % (webqtlConfig.KMININFORMATIVE, fd.RISet)]
            #    self.error(heading=heading,detail=detail)
            #    return
            #else:
            #    heading = HT.Paragraph('Trait Data Entered for %s Set' % fd.RISet)
            #    heading.__setattr__("class","title")

                #datadiv = HT.TD(heading, heading2,heading3, width='45%',valign='top', align='left', bgColor='#eeeeee')
            #resultstable,tblobj,bottomInfo  = self.GenReport(ChrNameOrderIdDict,fd, _genotype, _strains, _vals, _vars)
            
            self.gen_data()
            #resultstable = self.GenReport(fd, _genotype, _strains, _vals, _vars)

            # creat object for result table for sort function
            ##objfile = open('%s.obj' % (webqtlConfig.TMPDIR+filename), 'wb')
            ##cPickle.dump(tblobj, objfile)
            ##objfile.close()
            #
            #sortby = ("Index", "up")
            #reportTable =HT.Div(webqtlUtil.genTableObj(tblobj=tblobj, file=filename, sortby=sortby, tableID = "sortable", addIndex = "0"), Id="sortable")
            #
            #descriptionTable =  HT.TableLite(border=0, cellpadding=0, cellspacing=0)
            #descriptionTable.append(HT.TR(HT.TD(reportTable, colspan=3)))
            #descriptionTable.append(HT.TR(HT.TD(HT.BR(),HT.BR())))
            #descriptionTable.append(bottomInfo)

            #self.traitList=_vals

            ##########################plot#######################

            ################################################################
            # Generate Chr list and Retrieve Length Information
            ################################################################
            #self.genotype= _genotype
            #self.ChrList = [("All", -1)]

            #for i, indChr in enumerate(self.genotype):
            #    self.ChrList.append((indChr.name, i))

            #self.cursor.execute("""
            #        Select
            #                Length from Chr_Length, InbredSet
            #        where
            #                Chr_Length.SpeciesId = InbredSet.SpeciesId AND
            #                InbredSet.Name = '%s' AND
            #                Chr_Length.Name in (%s)
            #        Order by
            #                OrderId
            #        """ % (fd.RISet, string.join(map(lambda X: "'%s'" % X[0], self.ChrList[1:]), ", ")))
            #
            #self.ChrLengthMbList = self.cursor.fetchall()
            #self.ChrLengthMbList = map(lambda x: x[0]/1000000.0, self.ChrLengthMbList)
            #self.ChrLengthMbSum = reduce(lambda x, y:x+y, self.ChrLengthMbList, 0.0)
            #if self.ChrLengthMbList:
            #    self.MbGraphInterval = self.ChrLengthMbSum/(len(self.ChrLengthMbList)*12) #Empirical Mb interval
            #else:
            #    self.MbGraphInterval = 1
            #
            #self.ChrLengthCMList = []
            #for i, _chr in enumerate(self.genotype):
            #    self.ChrLengthCMList.append(_chr[-1].cM - _chr[0].cM)
            #self.ChrLengthCMSum = reduce(lambda x, y:x+y, self.ChrLengthCMList, 0.0)# used for calculate plot scale

            #self.GraphInterval = self.MbGraphInterval #Mb

            # begin: common part with human data
            #intCanvas = pid.PILCanvas(size=(self.graphWidth,self.graphHeight))
            #gifmap = self.plotIntMapping(fd, intCanvas, startMb = self.startMb, endMb = self.endMb, showLocusForm= "")
            #filename= webqtlUtil.genRandStr("Itvl_")
            #intCanvas.save(os.path.join(webqtlConfig.IMGDIR, filename), format='png')
            #intImg=HT.Image('/image/'+filename+'.png', border=0, usemap='#WebQTLImageMap')

            ################################################################
            # footnote goes here
            ################################################################
            #btminfo = HT.Paragraph(Id="smallsize") #Small('More information about this graph is available here.')

            #if (self.additiveChecked):
            #    btminfo.append(HT.BR(), 'A positive additive coefficient (', HT.Font('green', color='green'), ' line) indicates that %s alleles increase trait values. In contrast, a negative additive coefficient (' % fd.ppolar, HT.Font('red', color='red'), ' line) indicates that %s alleles increase trait values.' % fd.mpolar)


            #TD_LR = HT.TR(HT.TD(HT.Blockquote(gifmap,intImg, HT.P()), bgColor='#eeeeee', height = 200))
            #
            #self.dict['body'] = str(datadiv)+str(TD_LR)+str(resultstable)+str(HT.TR(HT.TD(descriptionTable)))

            # end: common part with human data
            
            self.js_data = dict(
                qtl_results = self.pure_qtl_results,
                lrs_array = self.lrs_array,
            )


    # add by NL 10-2-2011
    def initializeParameters(self, fd):
        """
        Initializes all of the MarkerRegressionPage class parameters,
        acquiring most values from the formdata (fd)
        
        """
        ###################################
        # manhattam plot parameters
        ###################################

        self.graphHeight = 600
        self.graphWidth  = 1280
        self.plotScale = 'physic'
        self.selectedChr = -1
        self.GRAPH_BACK_DARK_COLOR  = pid.HexColor(0xF1F1F9)
        self.GRAPH_BACK_LIGHT_COLOR = pid.HexColor(0xFBFBFF)
        self.LRS_COLOR  = pid.HexColor(0x0000FF)
        self.LRS_LOD ='LRS'
        self.lrsMax = float(fd.formdata.getvalue('lrsMax', 0))
        self.startMb  = fd.formdata.getvalue('startMb', "-1")
        self.endMb  = fd.formdata.getvalue('endMb', "-1")
        self.mappingMethodId  = fd.formdata.getvalue('mappingMethodId', "0")
        self.permChecked=True
        self.multipleInterval=False
        self.SIGNIFICANT_WIDTH = 5
        self.SUGGESTIVE_WIDTH = 5
        self.SIGNIFICANT_COLOR   = pid.HexColor(0xEBC7C7)
        self.SUGGESTIVE_COLOR    = pid.gainsboro
        self.colorCollection = [self.LRS_COLOR]
        self.additiveChecked= True
        self.ADDITIVE_COLOR_POSITIVE = pid.green
        self.legendChecked =False
        self.pValue=float(fd.formdata.getvalue('pValue',-1))

        # allow user to input p-value greater than 1,
        # in this case, the value will be treated as -lgP value. so the input value needs to be transferred to power of 10 format
        if self.pValue >1:
            self.pValue =10**-(self.pValue)

        try:
            self.startMb = float(self.startMb)
            self.endMb = float(self.endMb)
            if self.startMb > self.endMb:
                temp = self.startMb
                self.startMb = self.endMb
                self.endMb = temp
            #minimal distance 10bp
            if self.endMb - self.startMb < 0.00001:
                self.endMb = self.startMb + 0.00001
        except:
            self.startMb = self.endMb = -1

    def GenReportForPLINK(self, ChrNameOrderIdDict={},RISet='',plinkResultDict= {},thresholdPvalue=-1,chrList=[]):

        'Create an HTML division which reports any loci which are significantly associated with the submitted trait data.'
        #########################################
        #      Genome Association report
        #########################################
        locusFormName = webqtlUtil.genRandStr("fm_")
        locusForm = HT.Form(cgi = os.path.join(webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE), \
                enctype='multipart/form-data', name=locusFormName, submit=HT.Input(type='hidden'))
        hddn = {'FormID':'showDatabase','ProbeSetID':'_','database':RISet+"Geno",'CellID':'_', \
                'RISet':RISet, 'incparentsf1':'on'}
        for key in hddn.keys():
            locusForm.append(HT.Input(name=key, value=hddn[key], type='hidden'))

        regressionHeading = HT.Paragraph('Genome Association Report')
        regressionHeading.__setattr__("class","title")

        filename= webqtlUtil.genRandStr("GenomeAsscociation_")
        fpText = open('%s.txt' % (webqtlConfig.TMPDIR+filename), 'wb')
        fpText.write('The loci meet the criteria of P-Value <= %3.6f.\n'%thresholdPvalue)
        pValueInfo =HT.Paragraph('The loci meet the criteria of P-Value <= %3.6f.\n'%thresholdPvalue)

        textUrl = HT.Href(text = 'Download', url= '/tmp/'+filename+'.txt', target = "_blank", Class='fs12 fwn')
        bottomInfo = HT.TR(HT.TD(HT.Paragraph(textUrl, ' result in tab-delimited text format.', HT.BR(), HT.BR(),Class="fs12 fwn"), colspan=3))

        tblobj={}       # build dict for genTableObj function; keys include header and body
        tblobj_header = [] # value of key 'header'
        tblobj_body=[]          # value of key 'body'
        reportHeaderRow=[]      # header row list for tblobj_header (html part)
        headerList=['Index','SNP Name','Chr','Mb','-log(P)']
        headerStyle="fs14 fwb ffl b1 cw cbrb" # style of the header
        cellColorStyle = "fs13 b1 fwn c222" # style of the cells

        if headerList:
            for ncol, item in enumerate(headerList):
                reportHeaderRow.append(THCell(HT.TD(item, Class=headerStyle, valign='bottom',nowrap='ON'),text=item, idx=ncol))
            #download file for table headers' names
            fpText.write('SNP_Name\tChromosome\tMb\t-log(P)\n')

        tblobj_header.append(reportHeaderRow)
        tblobj['header']=tblobj_header

        index=1
        for chr in chrList:

            if plinkResultDict.has_key(chr):
                if chr in ChrNameOrderIdDict.keys():
                    chrOrderId =ChrNameOrderIdDict[chr]
                else:
                    chrOrderId=chr

                valueList=plinkResultDict[chr]

                for value in valueList:
                    reportBodyRow=[]        # row list for tblobj_body (html part)
                    snpName=value[0]
                    bp=value[1]
                    mb=int(bp)/1000000.0

                    try:
                        pValue =float(value[2])
                    except:
                        pValue =1
                    formattedPvalue = -math.log10(pValue)

                    formattedPvalue = webqtlUtil.SciFloat(formattedPvalue)
                    dbSnprs=snpName.replace('rs','')
                    SnpHref = HT.Href(text=snpName, url="http://www.ncbi.nlm.nih.gov/projects/SNP/snp_ref.cgi?rs=%s"%dbSnprs, target="_blank")

                    selectCheck=HT.Input(type="checkbox", Class="checkbox", name="index",value=index, onClick="highlight(this)")
                    reportBodyRow.append(TDCell(HT.TD(str(index),selectCheck, align='right',Class=cellColorStyle,nowrap='ON'),str(index),index))
                    reportBodyRow.append(TDCell(HT.TD(SnpHref, Class=cellColorStyle,nowrap='ON'),snpName, snpName))
                    reportBodyRow.append(TDCell(HT.TD(chr, Class=cellColorStyle, align="center",nowrap='ON'),chr, chrOrderId))
                    reportBodyRow.append(TDCell(HT.TD('%3.6f'%mb, Class=cellColorStyle, align="center",nowrap='ON'),mb, mb))
                    reportBodyRow.append(TDCell(HT.TD(formattedPvalue, Class=cellColorStyle, align="center",nowrap='ON'),formattedPvalue, float(formattedPvalue)))

                    fpText.write('%s\t%s\t%3.6f\t%s\n' % (snpName, str(chr), mb, formattedPvalue))
                    index+=1

                    tblobj_body.append(reportBodyRow)

        tblobj['body']=tblobj_body
        rv=HT.TR(HT.TD(regressionHeading,pValueInfo, locusForm, HT.P(), width='55%',valign='top', align='left',bgColor='#eeeeee'))

        return rv, tblobj,bottomInfo


    def gen_data(self):
        """Todo: Fill this in here"""

        #calculate QTL for each trait
        self.qtl_results = self.genotype.regression(strains = self.samples,
                                                trait = self.vals)
        self.lrs_array = self.genotype.permutation(strains = self.samples,
                                               trait = self.vals,
                                               nperm=self.num_perm)

        self.lrs_thresholds = Bunch(
                                suggestive = self.lrs_array[int(self.num_perm*0.37-1)],
                                significant = self.lrs_array[int(self.num_perm*0.95-1)],
                                highly_significant = self.lrs_array[int(self.num_perm*0.99-1)]
                                )

        if self.display_all_lrs:
            filtered_results = self.qtl_results
        else:
            suggestive_results = []
            self.pure_qtl_results = []
            for result in self.qtl_results:
                self.pure_qtl_results.append(dict(locus=dict(name=result.locus.name,
                                                             mb=result.locus.Mb,
                                                             chromosome=result.locus.chr),
                                                  lrs=result.lrs,
                                                  additive=result.additive))
                if result.lrs > self.lrs_thresholds.suggestive:
                    suggestive_results.append(result)
            filtered_results = suggestive_results 


        # Todo (2013): Use top_10 variable to generate page message about whether top 10 was used
        if not filtered_results:
            # We use the 10 results with the highest LRS values
            filtered_results = sorted(self.qtl_results)[-10:]
            self.top_10 = True
        else:
            self.top_10 = False



        #qtlresults2 = []
        #if self.disp_all_lrs:
        #    filtered = self.qtl_results[:]
        #else:
        #    filtered = filter(lambda x, y=fd.suggestive: x.lrs > y, qtlresults)
        #if len(filtered) == 0:
        #    qtlresults2 = qtlresults[:]
        #    qtlresults2.sort()
        #    filtered = qtlresults2[-10:]

        #########################################
        #      Permutation Graph
        #########################################
        #myCanvas = pid.PILCanvas(size=(400,300))
        ##plotBar(myCanvas,10,10,390,290,LRSArray,XLabel='LRS',YLabel='Frequency',title=' Histogram of Permutation Test',identification=fd.identification)
        #Plot.plotBar(myCanvas, LRSArray, XLabel='LRS',YLabel='Frequency',title=' Histogram of Permutation Test')
        #filename= webqtlUtil.genRandStr("Reg_")
        #myCanvas.save(webqtlConfig.IMGDIR+filename, format='gif')
        #img=HT.Image('/image/'+filename+'.gif',border=0,alt='Histogram of Permutation Test')
            
        #if fd.suggestive == None:
        #    fd.suggestive = LRSArray[int(fd.nperm*0.37-1)]
        #else:
        #    fd.suggestive = float(fd.suggestive)
        #if fd.significance == None:
        #    fd.significance = LRSArray[int(fd.nperm*0.95-1)]
        #else:
        #    fd.significance = float(fd.significance)

        #permutationHeading = HT.Paragraph('Histogram of Permutation Test')
        #permutationHeading.__setattr__("class","title")
        #
        #permutation = HT.TableLite()
        #permutation.append(HT.TR(HT.TD(img)))

        for marker in filtered_results:
            if marker.lrs > webqtlConfig.MAXLRS:
                marker.lrs = webqtlConfig.MAXLRS
        
        self.filtered_results = filtered_results

        #if fd.genotype.type == 'intercross':
        #    ncol =len(headerList)
        #    reportHeaderRow.append(THCell(HT.TD('Dominance Effect', Class=headerStyle, valign='bottom',nowrap='ON'),text='Dominance Effect', idx=ncol))
        #
        #    #download file for table headers' names
        #    fpText.write('LRS\tChromosome\tMb\tLocus\tAdditive Effect\tDominance Effect\n')
        #
        #    index=1
        #    for ii in filtered:
        #        #add by NL 06-20-2011: set LRS to 460 when LRS is infinite,
        #        if ii.lrs==float('inf') or ii.lrs>webqtlConfig.MAXLRS:
        #            LRS=webqtlConfig.MAXLRS #maximum LRS value
        #        else:
        #            LRS=ii.lrs
        #
        #        if LRS > fd.significance:
        #            lrs = HT.TD(HT.Font('%3.3f*' % LRS, color='#FF0000'),Class=cellColorStyle)
        #        else:
        #            lrs = HT.TD('%3.3f' % LRS,Class=cellColorStyle)
        #
        #        if ii.locus.chr in ChrNameOrderIdDict.keys():
        #            chrOrderId =ChrNameOrderIdDict[ii.locus.chr]
        #        else:
        #            chrOrderId=ii.locus.chr
        #
        #        reportBodyRow=[]        # row list for tblobj_body (html part)
        #        selectCheck=HT.Input(type="checkbox", Class="checkbox", name="index",value=index, onClick="highlight(this)")
        #        reportBodyRow.append(TDCell(HT.TD(str(index),selectCheck, align='right',Class=cellColorStyle,nowrap='ON'),str(index),index))
        #        reportBodyRow.append(TDCell(lrs,LRS, LRS))
        #        reportBodyRow.append(TDCell(HT.TD(ii.locus.chr, Class=cellColorStyle, align="center",nowrap='ON'),ii.locus.chr, chrOrderId))
        #        reportBodyRow.append(TDCell(HT.TD('%3.6f'%ii.locus.Mb, Class=cellColorStyle, align="center",nowrap='ON'),ii.locus.Mb, ii.locus.Mb))
        #        reportBodyRow.append(TDCell(HT.TD(HT.Href(text=ii.locus.name, url = "javascript:showTrait('%s','%s');" % (locusFormName, ii.locus.name), Class='normalsize'), Class=cellColorStyle, align="center",nowrap='ON'),ii.locus.name, ii.locus.name))
        #        reportBodyRow.append(TDCell(HT.TD('%3.3f' % ii.additive, Class=cellColorStyle, align="center",nowrap='ON'),ii.additive, ii.additive))
        #        reportBodyRow.append(TDCell(HT.TD('%3.3f' % ii.dominance, Class=cellColorStyle, align="center",nowrap='ON'),ii.dominance, ii.dominance))
        #
        #        fpText.write('%2.3f\t%s\t%3.6f\t%s\t%2.3f\t%2.3f\n' % (LRS, ii.locus.chr, ii.locus.Mb, ii.locus.name, ii.additive, ii.dominance))
        #        index+=1
        #        tblobj_body.append(reportBodyRow)
        #else:
        #    #download file for table headers' names
        #    fpText.write('LRS\tChromosome\tMb\tLocus\tAdditive Effect\n')
        #
        #    index=1
        #    for ii in filtered:
        #        #add by NL 06-20-2011: set LRS to 460 when LRS is infinite,
        #        if ii.lrs==float('inf') or ii.lrs>webqtlConfig.MAXLRS:
        #            LRS=webqtlConfig.MAXLRS #maximum LRS value
        #        else:
        #            LRS=ii.lrs
        #
        #        if LRS > fd.significance:
        #            lrs = HT.TD(HT.Font('%3.3f*' % LRS, color='#FF0000'),Class=cellColorStyle)
        #        else:
        #            lrs = HT.TD('%3.3f' % LRS,Class=cellColorStyle)
        #
        #        if ii.locus.chr in ChrNameOrderIdDict.keys():
        #            chrOrderId =ChrNameOrderIdDict[ii.locus.chr]
        #        else:
        #            chrOrderId=ii.locus.chr
        #
        #        reportBodyRow=[]        # row list for tblobj_body (html part)
        #        selectCheck=HT.Input(type="checkbox", Class="checkbox", name="index",value=index, onClick="highlight(this)")
        #        reportBodyRow.append(TDCell(HT.TD(str(index),selectCheck, align='right',Class=cellColorStyle,nowrap='ON'),str(index),index))
        #        reportBodyRow.append(TDCell(lrs,LRS, LRS))
        #        reportBodyRow.append(TDCell(HT.TD(ii.locus.chr, Class=cellColorStyle, align="center",nowrap='ON'),ii.locus.chr, chrOrderId))
        #        reportBodyRow.append(TDCell(HT.TD('%3.6f'%ii.locus.Mb, Class=cellColorStyle, align="center",nowrap='ON'),ii.locus.Mb, ii.locus.Mb))
        #        reportBodyRow.append(TDCell(HT.TD(HT.Href(text=ii.locus.name, url = "javascript:showTrait('%s','%s');" % (locusFormName, ii.locus.name), Class='normalsize'), Class=cellColorStyle, align="center",nowrap='ON'),ii.locus.name, ii.locus.name))
        #        reportBodyRow.append(TDCell(HT.TD('%3.3f' % ii.additive, Class=cellColorStyle, align="center",nowrap='ON'),ii.additive, ii.additive))
        #
        #        fpText.write('%2.3f\t%s\t%3.6f\t%s\t%2.3f\n' % (LRS, ii.locus.chr, ii.locus.Mb, ii.locus.name, ii.additive))
        #        index+=1
        #        tblobj_body.append(reportBodyRow)

        #tblobj_header.append(reportHeaderRow)
        #tblobj['header']=tblobj_header
        #tblobj['body']=tblobj_body

        #rv=HT.TD(regressionHeading,LRSInfo,report, locusForm, HT.P(),width='55%',valign='top', align='left', bgColor='#eeeeee')
        #if fd.genotype.type == 'intercross':
        #    bottomInfo.append(HT.BR(), HT.BR(), HT.Strong('Dominance Effect'),' is the difference between the mean trait value of cases heterozygous at a marker and the average mean for the two groups homozygous at this marker: e.g.,  BD - (BB+DD)/2]. A positive dominance effect indicates that the average phenotype of BD heterozygotes exceeds the mean of BB and DD homozygotes. No dominance deviation can be computed for a set of recombinant inbred strains or for a backcross.')
            #return rv,tblobj,bottomInfo

        #return rv,tblobj,bottomInfo

    def plotIntMappingForPLINK(self, fd, canvas, offset= (80, 120, 20, 80), zoom = 1, startMb = None, endMb = None, showLocusForm = "",plinkResultDict={}):
        #calculating margins
        xLeftOffset, xRightOffset, yTopOffset, yBottomOffset = offset

        fontZoom = zoom
        if zoom == 2:
            fontZoom = 1.5

        xLeftOffset = int(xLeftOffset*fontZoom)
        xRightOffset = int(xRightOffset*fontZoom)
        yBottomOffset = int(yBottomOffset*fontZoom)

        cWidth = canvas.size[0]
        cHeight = canvas.size[1]
        plotWidth = cWidth - xLeftOffset - xRightOffset
        plotHeight = cHeight - yTopOffset - yBottomOffset
        startPixelX = xLeftOffset
        endPixelX   = (xLeftOffset + plotWidth)

        #Drawing Area Height
        drawAreaHeight = plotHeight
        if self.plotScale == 'physic' and self.selectedChr > -1: # for single chr
            drawAreaHeight -= self.ENSEMBL_BAND_HEIGHT + self.UCSC_BAND_HEIGHT+ self.WEBQTL_BAND_HEIGHT + 3*self.BAND_SPACING+ 10*zoom
            if self.geneChecked:
                drawAreaHeight -= self.NUM_GENE_ROWS*self.EACH_GENE_HEIGHT + 3*self.BAND_SPACING + 10*zoom
        else:
            if self.selectedChr > -1:
                drawAreaHeight -= 20
            else:# for all chrs
                drawAreaHeight -= 30

        #Image map
        gifmap = HT.Map(name='WebQTLImageMap')

        newoffset = (xLeftOffset, xRightOffset, yTopOffset, yBottomOffset)
        # Draw the alternating-color background first and get plotXScale
        plotXScale = self.drawGraphBackgroundForPLINK(canvas, gifmap, offset=newoffset, zoom= zoom, startMb=startMb, endMb = endMb,plinkResultDict=plinkResultDict)

        # Draw X axis
        self.drawXAxisForPLINK(fd, canvas, drawAreaHeight, gifmap, plotXScale, showLocusForm, offset=newoffset, zoom= zoom, startMb=startMb, endMb = endMb)
        # Draw manhattam plot
        self.drawManhattanPlotForPLINK(canvas, drawAreaHeight, gifmap, plotXScale, offset=newoffset, zoom= zoom, startMb=startMb, endMb = endMb,plinkResultDict=plinkResultDict,thresholdPvalue=self.pValue)

        return gifmap


    def plotIntMapping(self, fd, canvas, offset= (80, 120, 20, 80), zoom = 1, startMb = None, endMb = None, showLocusForm = ""):
        #calculating margins
        xLeftOffset, xRightOffset, yTopOffset, yBottomOffset = offset

        fontZoom = zoom
        if zoom == 2:
            fontZoom = 1.5

        xLeftOffset = int(xLeftOffset*fontZoom)
        xRightOffset = int(xRightOffset*fontZoom)
        yBottomOffset = int(yBottomOffset*fontZoom)

        cWidth = canvas.size[0]
        cHeight = canvas.size[1]
        plotWidth = cWidth - xLeftOffset - xRightOffset
        plotHeight = cHeight - yTopOffset - yBottomOffset
        startPixelX = xLeftOffset
        endPixelX   = (xLeftOffset + plotWidth)

        #Drawing Area Height
        drawAreaHeight = plotHeight
        if self.plotScale == 'physic' and self.selectedChr > -1: # for single chr
            drawAreaHeight -= self.ENSEMBL_BAND_HEIGHT + self.UCSC_BAND_HEIGHT+ self.WEBQTL_BAND_HEIGHT + 3*self.BAND_SPACING+ 10*zoom
            if self.geneChecked:
                drawAreaHeight -= self.NUM_GENE_ROWS*self.EACH_GENE_HEIGHT + 3*self.BAND_SPACING + 10*zoom
        else:# for all chrs
            if self.selectedChr > -1:
                drawAreaHeight -= 20
            else:
                drawAreaHeight -= 30

        #Image map
        gifmap = HT.Map(name='WebQTLImageMap')

        newoffset = (xLeftOffset, xRightOffset, yTopOffset, yBottomOffset)
        # Draw the alternating-color background first and get plotXScale
        plotXScale = self.drawGraphBackground(canvas, gifmap, offset=newoffset, zoom= zoom, startMb=startMb, endMb = endMb)

        # Draw X axis
        self.drawXAxis(fd, canvas, drawAreaHeight, gifmap, plotXScale, showLocusForm, offset=newoffset, zoom= zoom, startMb=startMb, endMb = endMb)
        # Draw QTL curve
        self.drawQTL(canvas, drawAreaHeight, gifmap, plotXScale, offset=newoffset, zoom= zoom, startMb=startMb, endMb = endMb)

        #draw legend
        if self.multipleInterval:
            self.drawMultiTraitName(fd, canvas, gifmap, showLocusForm, offset=newoffset)
        elif self.legendChecked:
            self.drawLegendPanel(fd, canvas, offset=newoffset)
        else:
            pass

        #draw position, no need to use a separate function
        if fd.genotype.Mbmap:
            self.drawProbeSetPosition(canvas, plotXScale, offset=newoffset)

        return gifmap


    # functions for manhattam plot of markers
    def drawManhattanPlotForPLINK(self, canvas, drawAreaHeight, gifmap, plotXScale, offset= (40, 120, 80, 10), zoom = 1, startMb = None, endMb = None,plinkResultDict={},thresholdPvalue=-1):

        xLeftOffset, xRightOffset, yTopOffset, yBottomOffset = offset
        plotWidth = canvas.size[0] - xLeftOffset - xRightOffset
        plotHeight = canvas.size[1] - yTopOffset - yBottomOffset
        fontZoom = zoom
        if zoom == 2:
            fontZoom = 1.5

        # INTERCROSS = (self.genotype.type=="intercross")
        INTERCROSS ='' #??????

        ChrLengthDistList = self.ChrLengthMbList
        drawRegionDistance = self.ChrLengthMbSum
        GraphInterval=self.GraphInterval
        pvalueHeightThresh = drawAreaHeight - 80 #ZS: Otherwise the plot gets very close to the chromosome labels

        #draw the pvalue scale
        #We first determine whether or not we are using a sliding scale.
        #If so, we need to compute the maximum pvalue value to determine where the max y-value should be, and call this pvalueMax.
        #pvalueTop is then defined to be above the pvalueMax by enough to add one additional pvalueScale increment.
        #if we are using a set-scale, then we set pvalueTop to be the user's value, and pvalueMax doesn't matter.

        # for human data we use p value instead of lrs
        pValueList=[]
        for key in plinkResultDict:
            valueList = plinkResultDict[key]
            for item in valueList:
                pValue = item[-1]
                pValueList.append(pValue)

        formattedPValueList=[]
        for pValue in pValueList:
            try:
                pValue=float(pValue)
            except:
                pValue =1
            formattedpValue = -math.log10(pValue)
            formattedPValueList.append(formattedpValue)

        #sliding scale
        pvalueMax = max(formattedPValueList)
        #pvalueMax =pvalueMax +1
        # no permutation result for plink  func: GenReport()
        pvalueMin = int(-math.log10(thresholdPvalue))

        if pvalueMax> 100:
            pvalueScale = 20.0
        elif pvalueMax > 20:
            pvalueScale = 5.0
        elif pvalueMax > 7.5:
            pvalueScale = 2.5
        else:
            pvalueScale = 1.0

        # the base line for x-axis is -log(thresholdPvalue)
        pvalueAxisList = Plot.frange(pvalueMin, pvalueMax, pvalueScale)
        #make sure the user's value appears on the y-axis
        #ZS: There is no way to do this without making the position of the points not directly proportional to a given distance on the y-axis
        #tempPvalueMax=round(pvalueMax)
        tempPvalueMax = pvalueAxisList[len(pvalueAxisList)-1] + pvalueScale
        pvalueAxisList.append(tempPvalueMax)

        #ZS: I don't understand this; the if statement will be true for any number that isn't exactly X.5.
        #if abs(tempPvalueMax-pvalueMax) <0.5:
        #       tempPvalueMax=tempPvalueMax+1
        #       pvalueAxisList.append(tempPvalueMax)

        #draw the "pvalue" string to the left of the axis
        pvalueScaleFont=pid.Font(ttf="verdana", size=14*fontZoom, bold=0)
        pvalueLODFont=pid.Font(ttf="verdana", size=14*zoom*1.5, bold=0)
        yZero = yTopOffset + plotHeight

        #yAxis label display area
        yAxis_label ='-log(P)'
        canvas.drawString(yAxis_label, xLeftOffset - canvas.stringWidth("999.99", font=pvalueScaleFont) - 10*zoom, \
                                          yZero - 150, font=pvalueLODFont, color=pid.black, angle=90)

        for i,item in enumerate(pvalueAxisList):
            ypvalue = yZero - (float(i)/float(len(pvalueAxisList) - 1)) * pvalueHeightThresh
            canvas.drawLine(xLeftOffset, ypvalue, xLeftOffset - 4, ypvalue, color=self.LRS_COLOR, width=1*zoom)
            scaleStr = "%2.1f" % item
            #added by NL 6-24-2011:Y-axis scale display
            canvas.drawString(scaleStr, xLeftOffset-4-canvas.stringWidth(scaleStr, font=pvalueScaleFont)-5, ypvalue+3, font=pvalueScaleFont, color=self.LRS_COLOR)

        ChrList=self.ChrList
        startPosX = xLeftOffset

        for i, chr in enumerate(ChrList):

            if      plinkResultDict.has_key(chr):
                plinkresultList = plinkResultDict[chr]

                m = 0
                #add by NL 06-24-2011: for mahanttam plot
                symbolFont = pid.Font(ttf="fnt_bs", size=5,bold=0)
                # color for point in each chr
                chrCount=len(ChrList)
                chrColorDict =self.getColorForMarker(chrCount=chrCount,flag=1)
                for j, item in enumerate(plinkresultList):
                    try :
                        mb=float(item[1])/1000000.0
                    except:
                        mb=0

                    try :
                        pvalue =float(item[-1])
                    except:
                        pvalue =1

                    try:
                        snpName = item[0]
                    except:
                        snpName=''

                    formattedPvalue = -math.log10(pvalue)

                    Xc = startPosX + (mb-startMb)*plotXScale
                    Yc = yZero - (formattedPvalue-pvalueMin)*pvalueHeightThresh/(tempPvalueMax - pvalueMin)
                    canvas.drawString("5", Xc-canvas.stringWidth("5",font=symbolFont)/2+1,Yc+2,color=chrColorDict[i], font=symbolFont)
                    m += 1

            startPosX +=  (ChrLengthDistList[i]+GraphInterval)*plotXScale

        canvas.drawLine(xLeftOffset, yZero, xLeftOffset, yTopOffset, color=self.LRS_COLOR, width=1*zoom)  #the blue line running up the y axis

    def drawQTL(self, canvas, drawAreaHeight, gifmap, plotXScale, offset= (40, 120, 80, 10), zoom = 1, startMb = None, endMb = None):

        xLeftOffset, xRightOffset, yTopOffset, yBottomOffset = offset
        plotWidth = canvas.size[0] - xLeftOffset - xRightOffset
        plotHeight = canvas.size[1] - yTopOffset - yBottomOffset
        fontZoom = zoom
        if zoom == 2:
            fontZoom = 1.5

        INTERCROSS = (self.genotype.type=="intercross")

        ChrLengthDistList = self.ChrLengthMbList
        GraphInterval=self.GraphInterval
        LRSHeightThresh = drawAreaHeight
        AdditiveHeightThresh = drawAreaHeight/2
        DominanceHeightThresh = drawAreaHeight/2

        #draw the LRS scale
        #We first determine whether or not we are using a sliding scale.
        #If so, we need to compute the maximum LRS value to determine where the max y-value should be, and call this LRSMax.
        #LRSTop is then defined to be above the LRSMax by enough to add one additional LRSScale increment.
        #if we are using a set-scale, then we set LRSTop to be the user's value, and LRSMax doesn't matter.

        if self.LRS_LOD == 'LOD':
            lodm = self.LODFACTOR
        else:
            lodm = 1.0

        if self.lrsMax <= 0:  #sliding scale
            LRSMax = max(map(max, self.qtlresults)).lrs
            #genotype trait will give infinite LRS
            LRSMax = min(LRSMax, webqtlConfig.MAXLRS)
            LRSMax = max(self.significance, LRSMax)
        else:
            LRSMax = self.lrsMax*lodm

        if LRSMax/lodm > 100:
            LRSScale = 20.0
        elif LRSMax/lodm > 20:
            LRSScale = 5.0
        elif LRSMax/lodm > 7.5:
            LRSScale = 2.5
        else:
            LRSScale = 1.0

        LRSAxisList = Plot.frange(LRSScale, LRSMax/lodm, LRSScale)
        #make sure the user's value appears on the y-axis
        #update by NL 6-21-2011: round the LOD value to 100 when LRSMax is equal to 460
        LRSAxisList.append(round(LRSMax/lodm))

        #draw the "LRS" or "LOD" string to the left of the axis
        LRSScaleFont=pid.Font(ttf="verdana", size=14*fontZoom, bold=0)
        LRSLODFont=pid.Font(ttf="verdana", size=14*zoom*1.5, bold=0)
        yZero = yTopOffset + plotHeight

        #yAxis label display area
        canvas.drawString(self.LRS_LOD, xLeftOffset - canvas.stringWidth("999.99", font=LRSScaleFont) - 10*zoom, \
                                          yZero - 150, font=LRSLODFont, color=pid.black, angle=90)

        for item in LRSAxisList:
            yLRS = yZero - (item*lodm/LRSMax) * LRSHeightThresh
            canvas.drawLine(xLeftOffset, yLRS, xLeftOffset - 4, yLRS, color=self.LRS_COLOR, width=1*zoom)
            scaleStr = "%2.1f" % item
            #added by NL 6-24-2011:Y-axis scale display
            canvas.drawString(scaleStr, xLeftOffset-4-canvas.stringWidth(scaleStr, font=LRSScaleFont)-5, yLRS+3, font=LRSScaleFont, color=self.LRS_COLOR)


        #"Significant" and "Suggestive" Drawing Routine
        # ======= Draw the thick lines for "Significant" and "Suggestive" =====  (crowell: I tried to make the SNPs draw over these lines, but piddle wouldn't have it...)
        if self.permChecked and not self.multipleInterval:
            significantY = yZero - self.significance*LRSHeightThresh/LRSMax
            suggestiveY = yZero - self.suggestive*LRSHeightThresh/LRSMax


            startPosX = xLeftOffset
            for i, _chr in enumerate(self.genotype):
                rightEdge = int(startPosX + self.ChrLengthDistList[i]*plotXScale - self.SUGGESTIVE_WIDTH/1.5)
                #added by NL 6-24-2011:draw suggestive line (grey one)
                canvas.drawLine(startPosX+self.SUGGESTIVE_WIDTH/1.5, suggestiveY, rightEdge, suggestiveY, color=self.SUGGESTIVE_COLOR,
                        width=self.SUGGESTIVE_WIDTH*zoom, clipX=(xLeftOffset, xLeftOffset + plotWidth-2))
                #added by NL 6-24-2011:draw significant line (pink one)
                canvas.drawLine(startPosX+self.SUGGESTIVE_WIDTH/1.5, significantY, rightEdge, significantY, color=self.SIGNIFICANT_COLOR,
                        width=self.SIGNIFICANT_WIDTH*zoom, clipX=(xLeftOffset, xLeftOffset + plotWidth-2))
                sugg_coords = "%d, %d, %d, %d" % (startPosX, suggestiveY-2, rightEdge + 2*zoom, suggestiveY+2)
                sig_coords = "%d, %d, %d, %d" % (startPosX, significantY-2, rightEdge + 2*zoom, significantY+2)
                if self.LRS_LOD == 'LRS':
                    sugg_title = "Suggestive LRS = %0.2f" % self.suggestive
                    sig_title = "Significant LRS = %0.2f" % self.significance
                else:
                    sugg_title = "Suggestive LOD = %0.2f" % (self.suggestive/4.61)
                    sig_title = "Significant LOD = %0.2f" % (self.significance/4.61)
                Areas1 = HT.Area(shape='rect',coords=sugg_coords,title=sugg_title)
                Areas2 = HT.Area(shape='rect',coords=sig_coords,title=sig_title)
                gifmap.areas.append(Areas1)
                gifmap.areas.append(Areas2)

                startPosX +=  (self.ChrLengthDistList[i]+self.GraphInterval)*plotXScale


        if self.multipleInterval:
            lrsEdgeWidth = 1
        else:
            additiveMax = max(map(lambda X : abs(X.additive), self.qtlresults[0]))
            if INTERCROSS:
                dominanceMax = max(map(lambda X : abs(X.dominance), self.qtlresults[0]))
            else:
                dominanceMax = -1
            lrsEdgeWidth = 2
        for i, qtlresult in enumerate(self.qtlresults):
            m = 0
            startPosX = xLeftOffset
            thisLRSColor = self.colorCollection[i]

            #add by NL 06-24-2011: for mahanttam plot
            symbolFont = pid.Font(ttf="fnt_bs", size=5,bold=0)

            for j, _chr in enumerate(self.genotype):
                chrCount=len(self.genotype)
                chrColorDict =self.getColorForMarker(chrCount=chrCount,flag=1)
                LRSCoordXY = []
                AdditiveCoordXY = []
                DominanceCoordXY = []
                for k, _locus in enumerate(_chr):
                    if self.plotScale == 'physic':
                        Xc = startPosX + (_locus.Mb-startMb)*plotXScale
                    else:
                        Xc = startPosX + (_locus.cM-_chr[0].cM)*plotXScale
                    # updated by NL 06-18-2011:
                    # fix the over limit LRS graph issue since genotype trait may give infinite LRS;
                    # for any lrs is over than 460(LRS max in this system), it will be reset to 460
                    if      qtlresult[m].lrs> 460 or qtlresult[m].lrs=='inf':
                        Yc = yZero - webqtlConfig.MAXLRS*LRSHeightThresh/LRSMax
                    else:
                        Yc = yZero - qtlresult[m].lrs*LRSHeightThresh/LRSMax

                    LRSCoordXY.append((Xc, Yc))
                    #add by NL 06-24-2011: for mahanttam plot
                    #self.significance/4.61  consider chr and LOD
                    # significantY = yZero - self.significance*LRSHeightThresh/LRSMax
                    # if Yc >significantY:
                        # canvas.drawString(":", Xc-canvas.stringWidth(":",font=symbolFont)/2+1,Yc+2,color=pid.black, font=symbolFont)
                    # else:
                        # canvas.drawString(":", Xc-canvas.stringWidth(":",font=symbolFont)/2+1,Yc+2,color=pid.black, font=symbolFont)

                    # add by NL 06-27-2011: eliminate imputed value when locus name is equal to '-'
                    if (qtlresult[m].locus.name) and (qtlresult[m].locus.name!=' - '):
                        canvas.drawString("5", Xc-canvas.stringWidth("5",font=symbolFont)/2+1,Yc+2,color=chrColorDict[j], font=symbolFont)

                    if not self.multipleInterval and self.additiveChecked:
                        Yc = yZero - qtlresult[m].additive*AdditiveHeightThresh/additiveMax
                        AdditiveCoordXY.append((Xc, Yc))
                    if not self.multipleInterval and INTERCROSS and self.additiveChecked:
                        Yc = yZero - qtlresult[m].dominance*DominanceHeightThresh/dominanceMax
                        DominanceCoordXY.append((Xc, Yc))
                    m += 1

                startPosX +=  (ChrLengthDistList[j]+GraphInterval)*plotXScale


        ###draw additive scale
        if not self.multipleInterval and self.additiveChecked:
            additiveScaleFont=pid.Font(ttf="verdana",size=12*fontZoom,bold=0)
            additiveScale = Plot.detScaleOld(0,additiveMax)
            additiveStep = (additiveScale[1]-additiveScale[0])/additiveScale[2]
            additiveAxisList = Plot.frange(0, additiveScale[1], additiveStep)
            maxAdd =  additiveScale[1]
            addPlotScale = AdditiveHeightThresh/additiveMax

            additiveAxisList.append(additiveScale[1])
            for item in additiveAxisList:
                additiveY = yZero - item*addPlotScale
                canvas.drawLine(xLeftOffset + plotWidth,additiveY,xLeftOffset+4+ plotWidth,additiveY,color=self.ADDITIVE_COLOR_POSITIVE, width=1*zoom)
                scaleStr = "%2.3f" % item
                canvas.drawString(scaleStr,xLeftOffset + plotWidth +6,additiveY+5,font=additiveScaleFont,color=self.ADDITIVE_COLOR_POSITIVE)

            canvas.drawLine(xLeftOffset+plotWidth,additiveY,xLeftOffset+plotWidth,yZero,color=self.ADDITIVE_COLOR_POSITIVE, width=1*zoom)

        canvas.drawLine(xLeftOffset, yZero, xLeftOffset, yTopOffset, color=self.LRS_COLOR, width=1*zoom)  #the blue line running up the y axis

    def drawGraphBackgroundForPLINK(self, canvas, gifmap, offset= (80, 120, 80, 50), zoom = 1, startMb = None, endMb = None,plinkResultDict={} ):

        xLeftOffset, xRightOffset, yTopOffset, yBottomOffset = offset
        plotWidth = canvas.size[0] - xLeftOffset - xRightOffset
        plotHeight = canvas.size[1] - yTopOffset - yBottomOffset
        fontZoom = zoom
        if zoom == 2:
            fontZoom = 1.5

        #calculate plot scale
        #XZ: all of these global variables should be passed from function signiture
        ChrLengthDistList = self.ChrLengthMbList
        drawRegionDistance = self.ChrLengthMbSum
        GraphInterval=self.GraphInterval
        ChrList =self.ChrList

        #multiple chromosome view
        plotXScale = plotWidth / ((len(ChrList)-1)*GraphInterval + drawRegionDistance)

        startPosX = xLeftOffset
        chrLabelFont=pid.Font(ttf="verdana",size=24*fontZoom,bold=0)

        for i, _chr in enumerate(ChrList):

            if (i % 2 == 0):
                theBackColor = self.GRAPH_BACK_DARK_COLOR
            else:
                theBackColor = self.GRAPH_BACK_LIGHT_COLOR
            # NL:resize chr width for drawing
            if float(ChrLengthDistList[i])<90:
                ChrLengthDistList[i]=90
            #draw the shaded boxes and the sig/sug thick lines
            canvas.drawRect(startPosX, yTopOffset, startPosX + ChrLengthDistList[i]*plotXScale, \
                            yTopOffset+plotHeight, edgeColor=pid.gainsboro,fillColor=theBackColor)

            chrNameWidth = canvas.stringWidth(_chr, font=chrLabelFont)
            chrStartPix = startPosX + (ChrLengthDistList[i]*plotXScale -chrNameWidth)/2
            chrEndPix = startPosX + (ChrLengthDistList[i]*plotXScale +chrNameWidth)/2

            canvas.drawString(_chr, chrStartPix, yTopOffset +20,font = chrLabelFont,color=pid.dimgray)
            COORDS = "%d,%d,%d,%d" %(chrStartPix, yTopOffset, chrEndPix,yTopOffset +20)

            #add by NL 09-03-2010
            HREF = "javascript:changeView(%d,%s);" % (i,ChrLengthDistList)
            Areas = HT.Area(shape='rect',coords=COORDS,href=HREF)
            gifmap.areas.append(Areas)
            startPosX +=  (ChrLengthDistList[i]+GraphInterval)*plotXScale

        return plotXScale


    def drawGraphBackground(self, canvas, gifmap, offset= (80, 120, 80, 50), zoom = 1, startMb = None, endMb = None):
        ##conditions
        ##multiple Chromosome view
        ##single Chromosome Physical
        ##single Chromosome Genetic
        xLeftOffset, xRightOffset, yTopOffset, yBottomOffset = offset
        plotWidth = canvas.size[0] - xLeftOffset - xRightOffset
        plotHeight = canvas.size[1] - yTopOffset - yBottomOffset
        fontZoom = zoom
        if zoom == 2:
            fontZoom = 1.5

        #calculate plot scale
        if self.plotScale != 'physic':
            self.ChrLengthDistList = self.ChrLengthCMList
            drawRegionDistance = self.ChrLengthCMSum
        else:
            self.ChrLengthDistList = self.ChrLengthMbList
            drawRegionDistance = self.ChrLengthMbSum

        if self.selectedChr > -1: #single chromosome view
            spacingAmt = plotWidth/13.5
            i = 0
            for startPix in Plot.frange(xLeftOffset, xLeftOffset+plotWidth, spacingAmt):
                if (i % 2 == 0):
                    theBackColor = self.GRAPH_BACK_DARK_COLOR
                else:
                    theBackColor = self.GRAPH_BACK_LIGHT_COLOR
                i += 1
                canvas.drawRect(startPix, yTopOffset, min(startPix+spacingAmt, xLeftOffset+plotWidth), \
                        yTopOffset+plotHeight, edgeColor=theBackColor, fillColor=theBackColor)

            drawRegionDistance = self.ChrLengthDistList[self.selectedChr]
            self.ChrLengthDistList = [drawRegionDistance]
            if self.plotScale == 'physic':
                plotXScale = plotWidth / (endMb-startMb)
            else:
                plotXScale = plotWidth / drawRegionDistance

        else:   #multiple chromosome view
            plotXScale = plotWidth / ((len(self.genotype)-1)*self.GraphInterval + drawRegionDistance)

            startPosX = xLeftOffset
            chrLabelFont=pid.Font(ttf="verdana",size=24*fontZoom,bold=0)

            for i, _chr in enumerate(self.genotype):

                if (i % 2 == 0):
                    theBackColor = self.GRAPH_BACK_DARK_COLOR
                else:
                    theBackColor = self.GRAPH_BACK_LIGHT_COLOR

                #draw the shaded boxes and the sig/sug thick lines
                canvas.drawRect(startPosX, yTopOffset, startPosX + self.ChrLengthDistList[i]*plotXScale, \
                                yTopOffset+plotHeight, edgeColor=pid.gainsboro,fillColor=theBackColor)

                chrNameWidth = canvas.stringWidth(_chr.name, font=chrLabelFont)
                chrStartPix = startPosX + (self.ChrLengthDistList[i]*plotXScale -chrNameWidth)/2
                chrEndPix = startPosX + (self.ChrLengthDistList[i]*plotXScale +chrNameWidth)/2

                canvas.drawString(_chr.name, chrStartPix, yTopOffset +20,font = chrLabelFont,color=pid.dimgray)
                COORDS = "%d,%d,%d,%d" %(chrStartPix, yTopOffset, chrEndPix,yTopOffset +20)

                #add by NL 09-03-2010
                HREF = "javascript:changeView(%d,%s);" % (i,self.ChrLengthMbList)
                Areas = HT.Area(shape='rect',coords=COORDS,href=HREF)
                gifmap.areas.append(Areas)
                startPosX +=  (self.ChrLengthDistList[i]+self.GraphInterval)*plotXScale

        return plotXScale

    # XZ: The only difference of function drawXAxisForPLINK and function drawXAxis are the function name and the self.plotScale condition.
    def drawXAxisForPLINK(self, fd, canvas, drawAreaHeight, gifmap, plotXScale, showLocusForm, offset= (40, 120, 80, 10), zoom = 1, startMb = None, endMb = None):
        xLeftOffset, xRightOffset, yTopOffset, yBottomOffset = offset
        plotWidth = canvas.size[0] - xLeftOffset - xRightOffset
        plotHeight = canvas.size[1] - yTopOffset - yBottomOffset
        yZero = canvas.size[1] - yBottomOffset
        fontZoom = zoom
        if zoom == 2:
            fontZoom = 1.5

        #Parameters
        ChrLengthDistList = self.ChrLengthMbList
        GraphInterval=self.GraphInterval

        NUM_MINOR_TICKS = 5 # Number of minor ticks between major ticks
        X_MAJOR_TICK_THICKNESS = 2
        X_MINOR_TICK_THICKNESS = 1
        X_AXIS_THICKNESS = 1*zoom

        # ======= Alex: Draw the X-axis labels (megabase location)
        MBLabelFont = pid.Font(ttf="verdana", size=12*fontZoom, bold=0)
        xMajorTickHeight = 15 # How high the tick extends below the axis
        xMinorTickHeight = 5*zoom
        xAxisTickMarkColor = pid.black
        xAxisLabelColor = pid.black
        fontHeight = 12*fontZoom # How tall the font that we're using is
        spacingFromLabelToAxis = 20
        spacingFromLineToLabel = 3

        if self.plotScale == 'physic':
            strYLoc = yZero + spacingFromLabelToAxis + canvas.fontHeight(MBLabelFont)
            ###Physical single chromosome view
            if self.selectedChr > -1:
                graphMbWidth  = endMb - startMb
                XScale = Plot.detScale(startMb, endMb)
                XStart, XEnd, XStep = XScale
                if XStep < 8:
                    XStep *= 2
                spacingAmtX = spacingAmt = (XEnd-XStart)/XStep

                j = 0
                while  abs(spacingAmtX -int(spacingAmtX)) >= spacingAmtX/100.0 and j < 6:
                    j += 1
                    spacingAmtX *= 10

                formatStr = '%%2.%df' % j

                for counter, _Mb in enumerate(Plot.frange(XStart, XEnd, spacingAmt / NUM_MINOR_TICKS)):
                    if _Mb < startMb or _Mb > endMb:
                        continue
                    Xc = xLeftOffset + plotXScale*(_Mb - startMb)
                    if counter % NUM_MINOR_TICKS == 0: # Draw a MAJOR mark, not just a minor tick mark
                        canvas.drawLine(Xc, yZero, Xc, yZero+xMajorTickHeight, color=xAxisTickMarkColor, width=X_MAJOR_TICK_THICKNESS) # Draw the MAJOR tick mark
                        labelStr = str(formatStr % _Mb) # What Mbase location to put on the label
                        strWidth = canvas.stringWidth(labelStr, font=MBLabelFont)
                        drawStringXc = (Xc - (strWidth / 2.0))
                        canvas.drawString(labelStr, drawStringXc, strYLoc, font=MBLabelFont, color=xAxisLabelColor, angle=0)
                    else:
                        canvas.drawLine(Xc, yZero, Xc, yZero+xMinorTickHeight, color=xAxisTickMarkColor, width=X_MINOR_TICK_THICKNESS) # Draw the MINOR tick mark
                    # end else

            ###Physical genome wide view
            else:
                distScale = 0
                startPosX = xLeftOffset
                for i, distLen in enumerate(ChrLengthDistList):
                    if distScale == 0: #universal scale in whole genome mapping
                        if distLen > 75:
                            distScale = 25
                        elif distLen > 30:
                            distScale = 10
                        else:
                            distScale = 5
                    for tickdists in range(distScale, ceil(distLen), distScale):
                        canvas.drawLine(startPosX + tickdists*plotXScale, yZero, startPosX + tickdists*plotXScale, yZero + 7, color=pid.black, width=1*zoom)
                        canvas.drawString(str(tickdists), startPosX+tickdists*plotXScale, yZero + 10*zoom, color=pid.black, font=MBLabelFont, angle=270)
                    startPosX +=  (ChrLengthDistList[i]+GraphInterval)*plotXScale

            megabaseLabelFont = pid.Font(ttf="verdana", size=14*zoom*1.5, bold=0)
            canvas.drawString("Megabases", xLeftOffset + (plotWidth -canvas.stringWidth("Megabases", font=megabaseLabelFont))/2,
                    strYLoc + canvas.fontHeight(MBLabelFont) + 5*zoom, font=megabaseLabelFont, color=pid.black)
            pass

        canvas.drawLine(xLeftOffset, yZero, xLeftOffset+plotWidth, yZero, color=pid.black, width=X_AXIS_THICKNESS) # Draw the X axis itself

    def drawXAxis(self, fd, canvas, drawAreaHeight, gifmap, plotXScale, showLocusForm, offset= (40, 120, 80, 10), zoom = 1, startMb = None, endMb = None):
        xLeftOffset, xRightOffset, yTopOffset, yBottomOffset = offset
        plotWidth = canvas.size[0] - xLeftOffset - xRightOffset
        plotHeight = canvas.size[1] - yTopOffset - yBottomOffset
        yZero = canvas.size[1] - yBottomOffset
        fontZoom = zoom
        if zoom == 2:
            fontZoom = 1.5

        #Parameters
        NUM_MINOR_TICKS = 5 # Number of minor ticks between major ticks
        X_MAJOR_TICK_THICKNESS = 2
        X_MINOR_TICK_THICKNESS = 1
        X_AXIS_THICKNESS = 1*zoom

        # ======= Alex: Draw the X-axis labels (megabase location)
        MBLabelFont = pid.Font(ttf="verdana", size=12*fontZoom, bold=0)
        xMajorTickHeight = 15 # How high the tick extends below the axis
        xMinorTickHeight = 5*zoom
        xAxisTickMarkColor = pid.black
        xAxisLabelColor = pid.black
        fontHeight = 12*fontZoom # How tall the font that we're using is
        spacingFromLabelToAxis = 20
        spacingFromLineToLabel = 3

        if self.plotScale == 'physic':
            strYLoc = yZero + spacingFromLabelToAxis + canvas.fontHeight(MBLabelFont)
            ###Physical single chromosome view
            if self.selectedChr > -1:
                graphMbWidth  = endMb - startMb
                XScale = Plot.detScale(startMb, endMb)
                XStart, XEnd, XStep = XScale
                if XStep < 8:
                    XStep *= 2
                spacingAmtX = spacingAmt = (XEnd-XStart)/XStep

                j = 0
                while  abs(spacingAmtX -int(spacingAmtX)) >= spacingAmtX/100.0 and j < 6:
                    j += 1
                    spacingAmtX *= 10

                formatStr = '%%2.%df' % j

                for counter, _Mb in enumerate(Plot.frange(XStart, XEnd, spacingAmt / NUM_MINOR_TICKS)):
                    if _Mb < startMb or _Mb > endMb:
                        continue
                    Xc = xLeftOffset + plotXScale*(_Mb - startMb)
                    if counter % NUM_MINOR_TICKS == 0: # Draw a MAJOR mark, not just a minor tick mark
                        canvas.drawLine(Xc, yZero, Xc, yZero+xMajorTickHeight, color=xAxisTickMarkColor, width=X_MAJOR_TICK_THICKNESS) # Draw the MAJOR tick mark
                        labelStr = str(formatStr % _Mb) # What Mbase location to put on the label
                        strWidth = canvas.stringWidth(labelStr, font=MBLabelFont)
                        drawStringXc = (Xc - (strWidth / 2.0))
                        canvas.drawString(labelStr, drawStringXc, strYLoc, font=MBLabelFont, color=xAxisLabelColor, angle=0)
                    else:
                        canvas.drawLine(Xc, yZero, Xc, yZero+xMinorTickHeight, color=xAxisTickMarkColor, width=X_MINOR_TICK_THICKNESS) # Draw the MINOR tick mark
                    # end else

            ###Physical genome wide view
            else:
                distScale = 0
                startPosX = xLeftOffset
                for i, distLen in enumerate(self.ChrLengthDistList):
                    if distScale == 0: #universal scale in whole genome mapping
                        if distLen > 75:
                            distScale = 25
                        elif distLen > 30:
                            distScale = 10
                        else:
                            distScale = 5
                    for tickdists in range(distScale, ceil(distLen), distScale):
                        canvas.drawLine(startPosX + tickdists*plotXScale, yZero, startPosX + tickdists*plotXScale, yZero + 7, color=pid.black, width=1*zoom)
                        canvas.drawString(str(tickdists), startPosX+tickdists*plotXScale, yZero + 10*zoom, color=pid.black, font=MBLabelFont, angle=270)
                    startPosX +=  (self.ChrLengthDistList[i]+self.GraphInterval)*plotXScale

            megabaseLabelFont = pid.Font(ttf="verdana", size=14*zoom*1.5, bold=0)
            canvas.drawString("Megabases", xLeftOffset + (plotWidth -canvas.stringWidth("Megabases", font=megabaseLabelFont))/2,
                    strYLoc + canvas.fontHeight(MBLabelFont) + 5*zoom, font=megabaseLabelFont, color=pid.black)
            pass
        else:
            ChrAInfo = []
            preLpos = -1
            distinctCount = 0.0
            if len(self.genotype) > 1:
                for i, _chr in enumerate(self.genotype):
                    thisChr = []
                    Locus0CM = _chr[0].cM
                    nLoci = len(_chr)
                    if  nLoci <= 8:
                        for _locus in _chr:
                            if _locus.name != ' - ':
                                if _locus.cM != preLpos:
                                    distinctCount += 1
                                preLpos = _locus.cM
                                thisChr.append([_locus.name, _locus.cM-Locus0CM])
                    else:
                        for j in (0, nLoci/4, nLoci/2, nLoci*3/4, -1):
                            while _chr[j].name == ' - ':
                                j += 1
                            if _chr[j].cM != preLpos:
                                distinctCount += 1
                            preLpos = _chr[j].cM
                            thisChr.append([_chr[j].name, _chr[j].cM-Locus0CM])
                    ChrAInfo.append(thisChr)
            else:
                for i, _chr in enumerate(self.genotype):
                    thisChr = []
                    Locus0CM = _chr[0].cM
                    for _locus in _chr:
                        if _locus.name != ' - ':
                            if _locus.cM != preLpos:
                                distinctCount += 1
                            preLpos = _locus.cM
                            thisChr.append([_locus.name, _locus.cM-Locus0CM])
                    ChrAInfo.append(thisChr)

            stepA =  (plotWidth+0.0)/distinctCount

            LRectWidth = 10
            LRectHeight = 3
            offsetA = -stepA
            lineColor = pid.lightblue
            startPosX = xLeftOffset
            for j, ChrInfo in enumerate(ChrAInfo):
                preLpos = -1
                for i, item in enumerate(ChrInfo):
                    Lname,Lpos = item
                    if Lpos != preLpos:
                        offsetA += stepA
                        differ = 1
                    else:
                        differ = 0
                    preLpos = Lpos
                    Lpos *= plotXScale
                    if self.selectedChr > -1:
                        Zorder = i % 5
                    else:
                        Zorder = 0
                    if differ:
                        canvas.drawLine(startPosX+Lpos,yZero,xLeftOffset+offsetA,\
                        yZero+25, color=lineColor)
                        canvas.drawLine(xLeftOffset+offsetA,yZero+25,xLeftOffset+offsetA,\
                        yZero+40+Zorder*(LRectWidth+3),color=lineColor)
                        rectColor = pid.orange
                    else:
                        canvas.drawLine(xLeftOffset+offsetA, yZero+40+Zorder*(LRectWidth+3)-3,\
                        xLeftOffset+offsetA, yZero+40+Zorder*(LRectWidth+3),color=lineColor)
                        rectColor = pid.deeppink
                    canvas.drawRect(xLeftOffset+offsetA, yZero+40+Zorder*(LRectWidth+3),\
                            xLeftOffset+offsetA-LRectHeight,yZero+40+Zorder*(LRectWidth+3)+LRectWidth,\
                            edgeColor=rectColor,fillColor=rectColor,edgeWidth = 0)
                    COORDS="%d,%d,%d,%d"%(xLeftOffset+offsetA-LRectHeight, yZero+40+Zorder*(LRectWidth+3),\
                            xLeftOffset+offsetA,yZero+40+Zorder*(LRectWidth+3)+LRectWidth)
                    HREF="javascript:showDatabase3('%s','%s','%s','');" % (showLocusForm,fd.RISet+"Geno", Lname)
                    Areas=HT.Area(shape='rect',coords=COORDS,href=HREF, title="Locus : " + Lname)
                    gifmap.areas.append(Areas)
                ##piddle bug
                if j == 0:
                    canvas.drawLine(startPosX,yZero,startPosX,yZero+40, color=lineColor)
                startPosX += (self.ChrLengthDistList[j]+self.GraphInterval)*plotXScale

        canvas.drawLine(xLeftOffset, yZero, xLeftOffset+plotWidth, yZero, color=pid.black, width=X_AXIS_THICKNESS) # Draw the X axis itself

    def getColorForMarker(self, chrCount,flag):# no change is needed
        chrColorDict={}
        for i in range(chrCount):
            if flag==1: # display blue and lightblue intercross
                chrColorDict[i]=pid.black
            elif flag==0:
                if (i%2==0):
                    chrColorDict[i]=pid.blue
                else:
                    chrColorDict[i]=pid.lightblue
            else:#display different color for different chr
                if i in [0,8,16]:
                    chrColorDict[i]=pid.black
                elif i in [1,9,17]:
                    chrColorDict[i]=pid.red
                elif i in [2,10,18]:
                    chrColorDict[i]=pid.lightgreen
                elif i in [3,11,19]:
                    chrColorDict[i]=pid.blue
                elif i in [4,12]:
                    chrColorDict[i]=pid.lightblue
                elif i in [5,13]:
                    chrColorDict[i]=pid.hotpink
                elif i in [6,14]:
                    chrColorDict[i]=pid.gold
                elif i in [7,15]:
                    chrColorDict[i]=pid.grey

        return chrColorDict


    def drawProbeSetPosition(self, canvas, plotXScale, offset= (40, 120, 80, 10), zoom = 1, startMb = None, endMb = None):
        if len(self.traitList) != 1:
            return

        xLeftOffset, xRightOffset, yTopOffset, yBottomOffset = offset
        plotWidth = canvas.size[0] - xLeftOffset - xRightOffset
        plotHeight = canvas.size[1] - yTopOffset - yBottomOffset
        yZero = canvas.size[1] - yBottomOffset
        fontZoom = zoom
        if zoom == 2:
            fontZoom = 1.5

        try:
            Chr = self.traitList[0].chr # self.traitListChr =self.traitList[0].chr=_vals   need to change to chrList and mbList
            Mb = self.traitList[0].mb # self.traitListMb =self.traitList[0].mb=_vals
        except:
            return

        if self.plotScale == 'physic':
            if self.selectedChr > -1:
                if self.genotype[0].name != Chr or Mb < self.startMb or Mb > self.endMb:
                    return
                else:
                    locPixel = xLeftOffset + (Mb-self.startMb)*plotXScale
            else:
                locPixel = xLeftOffset
                for i, _chr in enumerate(self.genotype):
                    if _chr.name != Chr:
                        locPixel += (self.ChrLengthDistList[i] + self.GraphInterval)*plotXScale
                    else:
                        locPixel += Mb*plotXScale
                        break
        else:
            if self.selectedChr > -1:
                if self.genotype[0].name != Chr:
                    return
                else:
                    for i, _locus in enumerate(self.genotype[0]):
                        #the trait's position is on the left of the first genotype
                        if i==0 and _locus.Mb >= Mb:
                            locPixel=-1
                            break

                        #the trait's position is between two traits
                        if i > 0 and self.genotype[0][i-1].Mb < Mb and _locus.Mb >= Mb:
                            locPixel = xLeftOffset + plotXScale*(self.genotype[0][i-1].cM+(_locus.cM-self.genotype[0][i-1].cM)*(Mb -self.genotype[0][i-1].Mb)/(_locus.Mb-self.genotype[0][i-1].Mb))
                            break

                        #the trait's position is on the right of the last genotype
                        if i==len(self.genotype[0]) and Mb>=_locus.Mb:
                            locPixel = -1
            else:
                locPixel = xLeftOffset
                for i, _chr in enumerate(self.genotype):
                    if _chr.name != Chr:
                        locPixel += (self.ChrLengthDistList[i] + self.GraphInterval)*plotXScale
                    else:
                        locPixel += (Mb*(_chr[-1].cM-_chr[0].cM)/self.ChrLengthCMList[i])*plotXScale
                        break
        if locPixel >= 0:
            traitPixel = ((locPixel, yZero), (locPixel-6, yZero+12), (locPixel+6, yZero+12))
            canvas.drawPolygon(traitPixel, edgeColor=pid.black, fillColor=self.TRANSCRIPT_LOCATION_COLOR, closed=1)

        if self.legendChecked:
            startPosY = 15
            nCol = 2
            smallLabelFont = pid.Font(ttf="trebuc", size=12, bold=1)
            leftOffset = xLeftOffset+(nCol-1)*200
            canvas.drawPolygon(((leftOffset+6, startPosY-6), (leftOffset, startPosY+6), (leftOffset+12, startPosY+6)), edgeColor=pid.black, fillColor=self.TRANSCRIPT_LOCATION_COLOR, closed=1)
            canvas.drawString("Sequence Site", (leftOffset+15), (startPosY+5), smallLabelFont, self.TOP_RIGHT_INFO_COLOR)

    # build dict based on plink result, key is chr, value is list of [snp,BP,pValue]
    def getPlinkResultDict(self,outputFileName='',thresholdPvalue=-1,ChrOrderIdNameDict={}):

        ChrList =self.ChrList
        plinkResultDict={}

        plinkResultfp = open("%s%s.qassoc"% (webqtlConfig.TMPDIR, outputFileName), "rb")

        headerLine=plinkResultfp.readline()# read header line
        line = plinkResultfp.readline()

        valueList=[] # initialize value list, this list will include snp, bp and pvalue info
        pValueList=[]
        count=0

        while line:
            #convert line from str to list
            lineList=self.buildLineList(line=line)

            # only keep the records whose chromosome name is in db
            if ChrOrderIdNameDict.has_key(int(lineList[0])) and lineList[-1] and lineList[-1].strip()!='NA':

                chrName=ChrOrderIdNameDict[int(lineList[0])]
                snp = lineList[1]
                BP = lineList[2]
                pValue = float(lineList[-1])
                pValueList.append(pValue)

                if plinkResultDict.has_key(chrName):
                    valueList=plinkResultDict[chrName]

                    # pvalue range is [0,1]
                    if thresholdPvalue >=0 and thresholdPvalue<=1:
                        if pValue < thresholdPvalue:
                            valueList.append((snp,BP,pValue))
                            count+=1

                    plinkResultDict[chrName]=valueList
                    valueList=[]
                else:
                    if thresholdPvalue>=0 and thresholdPvalue<=1:
                        if pValue < thresholdPvalue:
                            valueList.append((snp,BP,pValue))
                            count+=1

                    if valueList:
                        plinkResultDict[chrName]=valueList

                    valueList=[]


                line =plinkResultfp.readline()
            else:
                line=plinkResultfp.readline()

        if pValueList:
            minPvalue= min(pValueList)
        else:
            minPvalue=0

        return count,minPvalue,plinkResultDict


    ######################################################
    # input: line: str,one line read from file
    # function: convert line from str to list;
    # output: lineList list
    #######################################################
    def buildLineList(self,line=None):

        lineList = string.split(string.strip(line),' ')# irregular number of whitespaces between columns
        lineList =[ item for item in lineList if item <>'']
        lineList = map(string.strip, lineList)

        return lineList

    #added by NL: automatically generate pheno txt file for PLINK based on strainList passed from dataEditing page
    def genPhenoTxtFileForPlink(self,phenoFileName='', RISetName='', probesetName='', valueDict={}):
        pedFileStrainList=self.getStrainNameFromPedFile(RISetName=RISetName)
        outputFile = open("%s%s.txt"%(webqtlConfig.TMPDIR,phenoFileName),"wb")
        headerLine = 'FID\tIID\t%s\n'%probesetName
        outputFile.write(headerLine)

        newValueList=[]

        #if valueDict does not include some strain, value will be set to -9999 as missing value
        for item in pedFileStrainList:
            try:
                value=valueDict[item]
                value=str(value).replace('value=','')
                value=value.strip()
            except:
                value=-9999

            newValueList.append(value)


        newLine=''
        for i, strain in enumerate(pedFileStrainList):
            j=i+1
            value=newValueList[i]
            newLine+='%s\t%s\t%s\n'%(strain, strain, value)

            if j%1000==0:
                outputFile.write(newLine)
                newLine=''

        if newLine:
            outputFile.write(newLine)

        outputFile.close()

    # get strain name from ped file in order
    def getStrainNameFromPedFile(self, RISetName=''):
        pedFileopen= open("%splink/%s.ped"%(webqtlConfig.HTMLPATH, RISetName),"r")
        line =pedFileopen.readline()
        strainNameList=[]

        while line:
            lineList=string.split(string.strip(line),'\t')
            lineList=map(string.strip,lineList)

            strainName=lineList[0]
            strainNameList.append(strainName)

            line =pedFileopen.readline()

        return strainNameList

    #################################################################
    ## Generate Chr list, Chr OrderId and Retrieve Length Information
    #################################################################
    #def getChrNameOrderIdLength(self,RISet=''):
    #
    #    try:
    #        query = """
    #                Select
    #                        Chr_Length.Name,Chr_Length.OrderId,Length from Chr_Length, InbredSet
    #                where
    #                        Chr_Length.SpeciesId = InbredSet.SpeciesId AND
    #                        InbredSet.Name = '%s'
    #                Order by OrderId
    #                """ % (RISet)
    #        self.cursor.execute(query)
    #
    #        results =self.cursor.fetchall()
    #        ChrList=[]
    #        ChrLengthMbList=[]
    #        ChrNameOrderIdDict={}
    #        ChrOrderIdNameDict={}
    #
    #        for item in results:
    #            ChrList.append(item[0])
    #            ChrNameOrderIdDict[item[0]]=item[1] # key is chr name, value is orderId
    #            ChrOrderIdNameDict[item[1]]=item[0] # key is orderId, value is chr name
    #            ChrLengthMbList.append(item[2])
    #
    #    except:
    #        ChrList=[]
    #        ChrNameOrderIdDict={}
    #        ChrLengthMbList=[]
    #
    #    return ChrList,ChrNameOrderIdDict,ChrOrderIdNameDict,ChrLengthMbList
  