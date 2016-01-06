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
# Last updated by Zach 12/14/2010


import time
import string
from math import *
import piddle as pid
import sys,os
import cPickle
import httplib, urllib

from flask import Flask, g

from htmlgen import HTMLgen2 as HT


from utility import helper_functions
from utility import Plot
from base import webqtlConfig
#from intervalAnalyst import GeneUtil
#from base.webqtlTrait import webqtlTrait
#from base.templatePage import templatePage
from utility import webqtlUtil
#from utility.THCell import THCell
#from utility.TDCell import TDCell
#from dbFunction import webqtlDatabaseFunction
#from base.GeneralObject import GeneralObject

#import logging
#logging.basicConfig(filename="/tmp/gn_leiyan.log", level=logging.INFO)
#_log = logging.getLogger("gn\web\webqtl\intervalMapping\IntervalMappingPage.py")

#########################################
#      Inteval Mapping Plot Page
#########################################
class MarkerRegression(object):
    cMGraphInterval = 5
    maxBootStrap = 50
    GRAPH_MIN_WIDTH = 900
    GRAPH_MAX_WIDTH = 10000 # Don't set this too high
    GRAPH_DEFAULT_WIDTH = 1280
    MULT_GRAPH_DEFAULT_WIDTH = 2000
    MULT_GRAPH_MIN_WIDTH = 1400
    MULT_GRAPH_DEFAULT_WIDTH = 1600
    GRAPH_DEFAULT_HEIGHT = 600


    # Display order:
    # UCSC BAND =========
    # ENSEMBL BAND -=-=-=
    # ** GENES **********
    BAND_SPACING = 4

    #ENSEMBL_BAND_Y      = UCSC_BAND_Y + UCSC_BAND_HEIGHT + BAND_SPACING
    UCSC_BAND_HEIGHT = 10
    ENSEMBL_BAND_HEIGHT = 10
    WEBQTL_BAND_HEIGHT = 10

    #GENE_START_Y        = ENSEMBL_BAND_Y + ENSEMBL_BAND_HEIGHT + BAND_SPACING
    NUM_GENE_ROWS       = 10
    EACH_GENE_HEIGHT    = 6  # number of pixels tall, for each gene to display
    EACH_GENE_ARROW_WIDTH = 5
    EACH_GENE_ARROW_SPACING = 14
    DRAW_DETAIL_MB = 4
    DRAW_UTR_LABELS_MB = 4

    MIN_PIXELS_BETWEEN_LABELS = 50

    qmarkImg = HT.Image('/images/qmarkBoxBlue.gif', width=10, height=13, border=0, alt='Glossary')
    # Note that "qmark.gif" is a similar, smaller, rounded-edges question mark. It doesn't look
    # like the ones on the image, though, which is why we don't use it here.

    HELP_WINDOW_NAME = 'helpWind'

    ## BEGIN HaplotypeAnalyst
    NR_INDIVIDUALS = 0
    ## END HaplotypeAnalyst

    ALEX_DEBUG_BOOL_COLORIZE_GENES = 1 # 0=don't colorize, 1=colorize
    ALEX_DEBUG_BOOL_PRINT_GENE_LIST = 1

    kWIDTH_DEFAULT=1

    kONE_MILLION = 1000000

    LODFACTOR = 4.61

    SNP_COLOR           = pid.orange # Color for the SNP "seismograph"
    TRANSCRIPT_LOCATION_COLOR = pid.mediumpurple

    GENE_FILL_COLOR     = pid.HexColor(0x6666FF)
    GENE_OUTLINE_COLOR  = pid.HexColor(0x000077)
    BOOTSTRAP_BOX_COLOR = pid.yellow
    LRS_COLOR           = pid.HexColor(0x0000FF)
    LRS_LINE_WIDTH = 2
    SIGNIFICANT_COLOR   = pid.HexColor(0xEBC7C7)
    SUGGESTIVE_COLOR    = pid.gainsboro
    SIGNIFICANT_WIDTH = 5
    SUGGESTIVE_WIDTH = 5
    ADDITIVE_COLOR_POSITIVE = pid.green
    ADDITIVE_COLOR_NEGATIVE = pid.red
    ADDITIVE_COLOR = ADDITIVE_COLOR_POSITIVE
    DOMINANCE_COLOR_POSITIVE = pid.darkviolet
    DOMINANCE_COLOR_NEGATIVE = pid.orange

    ## BEGIN HaplotypeAnalyst
    HAPLOTYPE_POSITIVE = pid.green
    HAPLOTYPE_NEGATIVE = pid.red
    HAPLOTYPE_HETEROZYGOUS = pid.blue
    HAPLOTYPE_RECOMBINATION = pid.darkgray
    ## END HaplotypeAnalyst

    QMARK_EDGE_COLOR    = pid.HexColor(0x718118)
    QMARK_FILL_COLOR    = pid.HexColor(0xDEE3BB)

    TOP_RIGHT_INFO_COLOR = pid.black
    X_AXIS_LABEL_COLOR  = pid.black #HexColor(0x505050)

    MINI_VIEW_MAGNIFIED_REGION_COLOR = pid.HexColor(0xCC0000)
    MINI_VIEW_OUTSIDE_REGION_COLOR   = pid.HexColor(0xEEEEEE)
    MINI_VIEW_BORDER_COLOR           = pid.black

    CLICKABLE_WEBQTL_REGION_COLOR     = pid.HexColor(0xF5D3D3)
    CLICKABLE_WEBQTL_REGION_OUTLINE_COLOR = pid.HexColor(0xFCE9E9)
    CLICKABLE_WEBQTL_TEXT_COLOR       = pid.HexColor(0x912828)

    CLICKABLE_UCSC_REGION_COLOR     = pid.HexColor(0xDDDDEE)
    CLICKABLE_UCSC_REGION_OUTLINE_COLOR = pid.HexColor(0xEDEDFF)
    CLICKABLE_UCSC_TEXT_COLOR       = pid.HexColor(0x333366)

    CLICKABLE_ENSEMBL_REGION_COLOR  = pid.HexColor(0xEEEEDD)
    CLICKABLE_ENSEMBL_REGION_OUTLINE_COLOR = pid.HexColor(0xFEFEEE)
    CLICKABLE_ENSEMBL_TEXT_COLOR    = pid.HexColor(0x555500)

    GRAPH_BACK_LIGHT_COLOR = pid.HexColor(0xFBFBFF)
    GRAPH_BACK_DARK_COLOR  = pid.HexColor(0xF1F1F9)

    HELP_PAGE_REF = '/glossary.html'

    DRAW_UTR_LABELS=0

    def __init__(self, start_vars):

        #templatePage.__init__(self, fd)

        #if not self.openMysql():
        #    return

        #helper_functions.get_species_dataset_trait(self, start_vars)

        self.temp_uuid = start_vars['temp_uuid']

        self.dataset = start_vars['dataset']
        self.this_trait = start_vars['this_trait']
        self.species = start_vars['species']

        self.vals = start_vars['vals'] #Needed to put into form for when it is resubmitted for single chr views or remapping
 
        self.mapping_method = start_vars['mapping_method'] #Needing for form submission when doing single chr mapping or remapping after changing options

        self.js_data = start_vars['js_data']

        #ZS: Think I can just get all this from dataset object now
        #RISet and Species
        #if not fd.genotype:
        #    fd.readGenotype()
        #
        #fd.parentsf14regression = fd.formdata.getvalue('parentsf14regression')
        #
        #if ((fd.parentsf14regression == 'on') and fd.genotype_2):
        #    fd.genotype = fd.genotype_2
        #else:
        #    fd.genotype = fd.genotype_1
        #fd.strainlist = list(fd.genotype.prgy)
        #
        #self.species = webqtlDatabaseFunction.retrieveSpecies(cursor=self.cursor, RISet=fd.RISet)

        if self.dataset.species == "rat":
            self._ucscDb = "rn3"
        elif self.dataset.species == "mouse":
            self._ucscDb = "mm9"
        else:
            self._ucscDb = ""

        #####################################
        # Options
        #####################################
        #Mapping options
        self.plotScale = start_vars['mapping_scale']
        #self.plotScale = fd.formdata.getvalue('scale', 'physic')
        #if self.plotScale == 'physic' and not fd.genotype.Mbmap: #ZS: Not sure where "Mbmap" is stored, if at all; should be fine without this though
        #    self.plotScale = 'morgan'
        if start_vars['num_perm'] != "":
            self.nperm = int(start_vars['num_perm'])
        else:
            self.nperm = 0
        if (start_vars['num_perm'] == "") or (start_vars['num_perm'] < 1):
            self.permChecked = False
        else:
            self.permChecked = True
        #self.permChecked = fd.formdata.getvalue('permCheck', True)
        self.bootChecked = False #ZS: For now setting to False, I'll add this option later once rest of figure works
        #self.bootChecked = fd.formdata.getvalue('bootCheck', '')
        if 'control' in start_vars.keys():
            self.controlLocus = start_vars['control']
        else:
            self.controlLocus = ""
        #self.controlLocus = fd.formdata.getvalue('controlLocus', '')

        #try:
        self.selectedChr = int(start_vars['selected_chr'])
        #except:
        #    self.selectedChr = -1

        #whether include parents and F1 for InbredSet
        #fd.parentsf14regression = fd.formdata.getvalue('parentsf14regression')
        #if ((fd.parentsf14regression == 'on') and fd.genotype_2):
        #    fd.genotype = fd.genotype_2
        #else:
        #    fd.genotype = fd.genotype_1

        self.strainlist = self.dataset.group.samplelist
        self.genotype = self.dataset.group.read_genotype_file()

        #Darwing Options
        try:
            if self.selectedChr > -1:
                self.graphWidth  = min(self.GRAPH_MAX_WIDTH, self.GRAPH_MIN_WIDTH)
            else:
                self.graphWidth  = min(self.GRAPH_MAX_WIDTH, self.MULT_GRAPH_MIN_WIDTH)
        except:
            if self.selectedChr > -1:
                self.graphWidth  = self.GRAPH_DEFAULT_WIDTH
            else:
                self.graphWidth  = self.MULT_GRAPH_DEFAULT_WIDTH

        #try:
        #    if self.selectedChr > -1:
        #        self.graphWidth  = min(self.GRAPH_MAX_WIDTH, max(self.GRAPH_MIN_WIDTH, int(fd.formdata.getvalue('graphWidth'))))
        #    else:
        #        self.graphWidth  = min(self.GRAPH_MAX_WIDTH, max(self.MULT_GRAPH_MIN_WIDTH, int(fd.formdata.getvalue('graphWidth'))))
        #except:
        #    if self.selectedChr > -1:
        #        self.graphWidth  = self.GRAPH_DEFAULT_WIDTH
        #    else:
        #        self.graphWidth  = self.MULT_GRAPH_DEFAULT_WIDTH

## BEGIN HaplotypeAnalyst
        #self.haplotypeAnalystChecked = fd.formdata.getvalue('haplotypeAnalystCheck')
        self.haplotypeAnalystChecked = False
## END HaplotypeAnalyst


        self.graphHeight = self.GRAPH_DEFAULT_HEIGHT
        self.additiveChecked = False
        self.dominanceChecked = False
        self.LRS_LOD = start_vars['score_type']
        self.cutoff = start_vars['cutoff']
        self.intervalAnalystChecked = False
        self.legendChecked = False
        self.geneChecked = False
        self.SNPChecked  = False
        self.draw2X = False
        self.lrsMax = 0
        self.startMb = -1
        self.endMb = -1

        #self.additiveChecked = fd.formdata.getvalue('additiveCheck')
        #self.dominanceChecked = fd.formdata.getvalue('dominanceCheck')
        #self.LRS_LOD = fd.formdata.getvalue('LRSCheck', 'LRS')
        #self.intervalAnalystChecked = fd.formdata.getvalue('intervalAnalystCheck')
        #self.legendChecked = fd.formdata.getvalue('viewLegend')
        #self.geneChecked = fd.formdata.getvalue('showGenes')
        #self.SNPChecked  = fd.formdata.getvalue('showSNP')
        #self.draw2X = fd.formdata.getvalue('draw2X')
        #self.lrsMax = float(fd.formdata.getvalue('lrsMax', 0))
        #self.startMb = fd.formdata.getvalue('startMb', "-1")
        #self.endMb = fd.formdata.getvalue('endMb', "-1")

        #try:
        #    self.startMb = float(self.startMb)
        #    self.endMb = float(self.endMb)
        #    if self.startMb > self.endMb:
        #        temp = self.startMb
        #        self.startMb = self.endMb
        #        self.endMb = temp
        #    #minimal distance 10bp
        #    if self.endMb - self.startMb < 0.00001:
        #        self.endMb = self.startMb + 0.00001
        #except:
        #    self.startMb = self.endMb = -1

        #Trait Infos
        self.identification = ""
        #self.identification = fd.formdata.getvalue('identification', "")

        ################################################################
        # Generate Chr list and Retrieve Length Information
        ################################################################
        self.ChrList = [("All", -1)]
        for i, indChr in enumerate(self.genotype):
            self.ChrList.append((indChr.name, i))


        
        self.ChrLengthMbList = g.db.execute("""
                Select
                        Length from Chr_Length, InbredSet
                where
                        Chr_Length.SpeciesId = InbredSet.SpeciesId AND
                        InbredSet.Name = '%s' AND
                        Chr_Length.Name in (%s)
                Order by
                        Chr_Length.OrderId
                """ % (self.dataset.group.name, string.join(map(lambda X: "'%s'" % X[0], self.ChrList[1:]), ", ")))

        self.ChrLengthMbList = map(lambda x: x[0]/1000000.0, self.ChrLengthMbList)
        self.ChrLengthMbSum = reduce(lambda x, y:x+y, self.ChrLengthMbList, 0.0)
        if self.ChrLengthMbList:
            self.MbGraphInterval = self.ChrLengthMbSum/(len(self.ChrLengthMbList)*12) #Empirical Mb interval
        else:
            self.MbGraphInterval = 1

        self.ChrLengthCMList = []
        for i, _chr in enumerate(self.genotype):
            self.ChrLengthCMList.append(_chr[-1].cM - _chr[0].cM)
        self.ChrLengthCMSum = reduce(lambda x, y:x+y, self.ChrLengthCMList, 0.0)

        if self.plotScale == 'physic':
            self.GraphInterval = self.MbGraphInterval #Mb
        else:
            self.GraphInterval = self.cMGraphInterval #cM
			
        ################################################################
        # Get Trait Values and Infomation
        ################################################################
        ##input from search page or selection page
        #self.searchResult = fd.formdata.getvalue('searchResult')
        ##convert single selection into a list
        #if type("1") == type(self.searchResult):
        #    self.searchResult = string.split(self.searchResult,'\t')
        #
        #self.traitList = []
        #if self.searchResult and len(self.searchResult) > webqtlConfig.MULTIPLEMAPPINGLIMIT:
        #    heading = 'Multiple Interval Mapping'
        #    detail = ['In order to get clear result, do not select more than %d traits for \
        #            Multiple Interval Mapping analysis.' % webqtlConfig.MULTIPLEMAPPINGLIMIT]
        #    self.error(heading=heading,detail=detail)
        #    return
        #elif self.searchResult:
        #    self.dataSource = 'selectionPage'
        #    for item in self.searchResult:
        #        thisTrait = webqtlTrait(fullname=item, cursor=self.cursor)
        #        thisTrait.retrieveInfo()
        #        thisTrait.retrieveData(fd.strainlist)
        #        self.traitList.append(thisTrait)
        #else:

        #input from data editing page
        #fd.readData()
        #if not fd.allTraitData:
        #    heading = "Mapping"
        #    detail = ['No trait data was selected for %s data set. No mapping attempted.' % fd.RISet]
        #    self.error(heading=heading,detail=detail)
        #    return

        self.dataSource = 'editingPage'
        self.traitList = []
        thisTrait = start_vars['this_trait']
        #fullname = fd.formdata.getvalue('fullname', '')
        #if fullname:
        #    thisTrait = webqtlTrait(fullname=fullname, data=fd.allTraitData, cursor=self.cursor)
        #    thisTrait.retrieveInfo()
        #else:
        #    thisTrait = webqtlTrait(data=fd.allTraitData)
        self.traitList.append(thisTrait)


## BEGIN HaplotypeAnalyst
## count the amount of individuals to be plotted, and increase self.graphHeight
        #if self.haplotypeAnalystChecked and self.selectedChr > -1:
        #    thisTrait = self.traitList[0]
        #    _strains, _vals, _vars = thisTrait.exportInformative()
        #    smd=[]
        #    for ii, _val in enumerate(_vals):
        #        temp = GeneralObject(name=_strains[ii], value=_val)
        #        smd.append(temp)
        #    bxdlist=list(self.genotype.prgy)
        #    for j,_geno in enumerate (self.genotype[0][1].genotype):
        #        for item in smd:
        #            if item.name == bxdlist[j]:
        #                self.NR_INDIVIDUALS = self.NR_INDIVIDUALS + 1
## default:
        #    self.graphHeight = self.graphHeight + 2 * (self.NR_INDIVIDUALS+10) * self.EACH_GENE_HEIGHT
## for paper:
        #    #self.graphHeight = self.graphHeight + 1 * self.NR_INDIVIDUALS * self.EACH_GENE_HEIGHT - 180
## END HaplotypeAnalyst

        ################################################################
        # Calculations QTL goes here
        ################################################################
        self.multipleInterval = len(self.traitList) > 1
        self.qtlresults = start_vars['qtl_results']
        #errorMessage = self.calculateAllResult(fd)
        #if errorMessage:
        #    heading = "Mapping"
        #    detail = ['%s' % errorMessage]
        #    self.error(heading=heading,detail=detail)
        #    return

        if self.multipleInterval:
            self.colorCollection = Plot.colorSpectrum(len(self.qtlresults))
        else:
            self.colorCollection = [self.LRS_COLOR]


        #########################
        ## Get the sorting column
        #########################
        RISet = self.dataset.group.name
        if RISet in ('AXB', 'BXA', 'AXBXA'):
            self.diffCol = ['B6J', 'A/J']
        elif RISet in ('BXD', 'BXD300', 'B6D2F2', 'BDF2-2005', 'BDF2-1999', 'BHHBF2'):
            self.diffCol = ['B6J', 'D2J']
        elif RISet in ('CXB'):
            self.diffCol = ['CBY', 'B6J']
        elif RISet in ('BXH', 'BHF2'):
            self.diffCol = ['B6J', 'C3H']
        elif RISet in ('B6BTBRF2'):
            self.diffCol = ['B6J', 'BTB']
        elif RISet in ('LXS'):
            self.diffCol = ['ILS', 'ISS']
        else:
            self.diffCol= []

        for i, strain in enumerate(self.diffCol):
            self.diffCol[i] = g.db.execute("select Id from Strain where Symbol = %s", strain).fetchone()[0]
            #self.cursor.execute("select Id from Strain where Symbol = %s", strain)
            #self.diffCol[i] = self.cursor.fetchone()[0]
        #print self.diffCol

        ################################################################
        # GeneCollection goes here
        ################################################################
        if self.plotScale == 'physic':
            #StartMb or EndMb
            if self.startMb < 0 or self.endMb < 0:
                self.startMb = 0
                self.endMb = self.ChrLengthMbList[self.selectedChr]

        geneTable = ""

        #if self.plotScale == 'physic' and self.selectedChr > -1 and (self.intervalAnalystChecked  or self.geneChecked):
        #    chrName = self.genotype[0].name
        #    # Draw the genes for this chromosome / region of this chromosome
        #    if self.traitList and self.traitList[0] and len(self.traitList) == 1 and self.dataset.name:
        #        webqtldatabase = self.dataset.name
        #        #webqtldatabase = self.traitList[0].db.name
        #    else:
        #        webqtldatabase = None
        #
        #    self.geneCol = None
        #
        #    if self.species == "mouse":
        #        self.geneCol = GeneUtil.loadGenes(self.cursor, chrName, self.diffCol, self.startMb, self.endMb, webqtldatabase, "mouse")
        #    elif self.species == "rat":
        #        self.geneCol = GeneUtil.loadGenes(self.cursor, chrName, self.diffCol, self.startMb, self.endMb, webqtldatabase, "rat")
        #    else:
        #        self.geneCol = None
        #
        #    if self.geneCol and self.intervalAnalystChecked:
        #        #######################################################################
        #        #Nick use GENEID as RefGene to get Literature Correlation Informations#
        #        #For Interval Mapping, Literature Correlation isn't useful, so skip it#
        #        #through set GENEID is None                                           #
        #        #######################################################################
        #
        #        #GENEID = fd.formdata.getvalue('GeneId') or None
        #        GENEID = None
        # 
        #        geneTableContainer = HT.Div(Id="sortable") #Div to hold table
        #        geneTable = self.geneTable(self.geneCol,GENEID)
        #        geneTableContainer.append(geneTable)
        #        
        #        mainfmName = webqtlUtil.genRandStr("fm_")
        #        tableForm = HT.Form(cgi=os.path.join(webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE), enctype='multipart/form-data', name=mainfmName, submit=HT.Input(type='hidden'))
        #        tableForm.append(HT.Input(name='FormID', value='', type='hidden'))
        #        tableForm.append(geneTableContainer)
        #
        #else:
        self.geneCol = None

        ################################################################
        # Plots goes here
        ################################################################
        if self.plotScale != 'physic' or self.multipleInterval:
            showLocusForm =  webqtlUtil.genRandStr("fm_")
        else:
            showLocusForm = ""
        intCanvas = pid.PILCanvas(size=(self.graphWidth,self.graphHeight))
        gifmap = self.plotIntMapping(intCanvas, startMb = self.startMb, endMb = self.endMb, showLocusForm= showLocusForm)    

        self.gifmap = gifmap.__str__()
        #print("GIFMAP:", gifmap.__str__())

        self.filename= webqtlUtil.genRandStr("Itvl_")
        intCanvas.save(os.path.join(webqtlConfig.IMGDIR, self.filename), format='jpeg')
        intImg=HT.Image('/image/'+self.filename+'.png', border=0, usemap='#WebQTLImageMap')

        #Scales plot differently for high resolution
        if self.draw2X:
            intCanvasX2 = pid.PILCanvas(size=(self.graphWidth*2,self.graphHeight*2))
            gifmapX2 = self.plotIntMapping(intCanvasX2, startMb = self.startMb, endMb = self.endMb, showLocusForm= showLocusForm, zoom=2)
            intCanvasX2.save(os.path.join(webqtlConfig.IMGDIR, self.filename+"X2"), format='png')
            #DLintImgX2=HT.Href(text='Download',url = '/image/'+self.filename+'X2.png', Class='smallsize', target='_blank')
 
        #textUrl = self.writeQTL2Text(fd, self.filename)

        ################################################################
        # Info tables goes here
        ################################################################
        #traitInfoTD = self.traitInfoTD(fd)

        #if self.draw2X:
        #    traitInfoTD.append(HT.P(), DLintImgX2, ' a higher resolution 2X image. ')
        #else:
        #    traitInfoTD.append(HT.P())
        #if textUrl:
        #    traitInfoTD.append(HT.BR(), textUrl, ' results in tab-delimited text format.')
        #traitRemapTD = self.traitRemapTD(self.cursor, fd)
        #topTable = HT.TableLite(HT.TR(traitInfoTD, HT.TD("&nbsp;", width=25), traitRemapTD), border=0, cellspacing=0, cellpadding=0)

        ################################################################
        # Outputs goes here
        ################################################################
        #this form is used for opening Locus page or trait page, only available for genetic mapping
        if showLocusForm:
            showLocusForm = HT.Form(cgi= os.path.join(webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE), enctype='multipart/form-data',
                name=showLocusForm, submit=HT.Input(type='hidden'))
            hddn = {'FormID':'showDatabase', 'ProbeSetID':'_','database':fd.RISet+"Geno",'CellID':'_', 'RISet':fd.RISet, 'incparentsf1':'ON'}
            for key in hddn.keys():
                showLocusForm.append(HT.Input(name=key, value=hddn[key], type='hidden'))
            showLocusForm.append(intImg)
        else:
            showLocusForm = intImg
        
        if self.permChecked and not self.multipleInterval and 0<self.nperm:
            perm_histogram = self.drawPermutationHistogram()
            perm_text_file = self.permutationTextFile()

        ################################################################
        # footnote goes here
        ################################################################
        btminfo = HT.Paragraph(Id="smallsize") #Small('More information about this graph is available here.')

        if (self.additiveChecked):
            btminfo.append(HT.BR(), 'A positive additive coefficient (', HT.Font('green', color='green'), ' line) indicates that %s alleles increase trait values. In contrast, a negative additive coefficient (' % fd.ppolar, HT.Font('red', color='red'), ' line) indicates that %s alleles increase trait values.' % fd.mpolar)

        if self.traitList and self.traitList[0].dataset and self.traitList[0].dataset.type == 'Geno':
            btminfo.append(HT.BR(), 'Mapping using genotype data as a trait will result in infinity LRS at one locus. In order to display the result properly, all LRSs higher than 100 are capped at 100.')

        if self.permChecked and not self.multipleInterval and 0<self.nperm:
            TD_LR = HT.TD(HT.Blockquote(gifmap, showLocusForm, HT.P(), btminfo, HT.P(), perm_histogram, HT.P(), perm_text_file), bgColor='#eeeeee', height = 200)
            #TD_LR = HT.TD(HT.Blockquote(topTable), HT.Blockquote(gifmap, showLocusForm, HT.P(), btminfo, HT.P(), perm_histogram, HT.P(), perm_text_file), bgColor='#eeeeee', height = 200)
        else:
            TD_LR = HT.TD(HT.Blockquote(gifmap, showLocusForm, HT.P(), btminfo), bgColor='#eeeeee', height = 200)
            #TD_LR = HT.TD(HT.Blockquote(topTable), HT.Blockquote(gifmap, showLocusForm, HT.P(), btminfo, HT.P(), perm_histogram, HT.P(), perm_text_file), bgColor='#eeeeee', height = 200)


        if geneTable:
            iaForm = HT.Form(cgi= os.path.join(webqtlConfig.CGIDIR, "main.py?FormID=intervalAnalyst"), enctype='multipart/form-data',
                name="iaForm", submit=HT.Input(type='hidden'))
            hddn = {'chromosome':self.genotype[0].name, 'species':self.species,'startMb':self.startMb,'endMb':self.endMb}
            if self.diffCol:
                hddn['s1'] = self.diffCol[0]
                hddn['s2'] = self.diffCol[1]
            for key in hddn.keys():
                iaForm.append(HT.Input(name=key, value=hddn[key], type='hidden'))
            iaForm.append(HT.Paragraph("Interval Analyst : Chr %s from %2.6f to %2.6f Mb" % (self.genotype[0].name, self.startMb, self.endMb),
                HT.Input(name='customize', value='Customize', onClick= "formInNewWindow(this.form);", type='button', Class="button"), Class="subtitle"))
            TD_LR.append(HT.Blockquote(iaForm))
            # optionsTable
            selectall = HT.Href(url="#redirect", onClick="checkAll(document.getElementsByName('%s')[0]);" % mainfmName)
            selectall_img = HT.Image("/images/select_all2_final.jpg", name="selectall", alt="Select All", title="Select All", style="border:none;")
            selectall.append(selectall_img)
            reset = HT.Href(url="#redirect", onClick="checkNone(document.getElementsByName('%s')[0]); return false;" % mainfmName)
            reset_img = HT.Image("/images/select_none2_final.jpg", alt="Select None", title="Select None", style="border:none;")
            reset.append(reset_img)
            selectinvert = HT.Href(url="#redirect", onClick = "checkInvert(document.getElementsByName('%s')[0]);" % mainfmName)
            selectinvert_img = HT.Image("/images/invert_selection2_final.jpg", name="selectinvert", alt="Invert Selection", title="Invert Selection", style="border:none;")
            selectinvert.append(selectinvert_img)
            addselect = HT.Href(url="#redirect", onClick="addRmvSelection('%s', document.getElementsByName('%s')[0], 'addToSelection');" % (RISet, mainfmName))
            addselect_img = HT.Image("/images/add_collection1_final.jpg", name="addselect", alt="Add To Collection", title="Add To Collection", style="border:none;")
            addselect.append(addselect_img)
            geneweaver = HT.Href(url="#redirect", onClick="databaseFunc(document.getElementsByName('%s')[0], 'ODEIM');" % mainfmName)
            geneweaver_img = HT.Image("/images/ODE_logo_final.jpg", name="GeneWeaver", alt="Gene Weaver", title="Gene Weaver", style="border:none")
            geneweaver.append(geneweaver_img)
            optionsTable = HT.TableLite()
            optionsTable.append(HT.TR(
                HT.TD(selectall, width="77", style="text-align:center"),
                HT.TD(reset, width="77", style="text-align:center"),
                HT.TD(selectinvert, width="77", style="text-align:center"),
                HT.TD(geneweaver, width="77", style="text-align:center"),
                ))
            optionsTable.append(HT.TR(
                HT.TD("Select", style="text-align:center"),
                HT.TD("Deselect", style="text-align:center"),
                HT.TD("Invert", style="text-align:center"),
                HT.TD("Gene Weaver", style="text-align:center"),
                ))
            TD_LR.append(HT.Blockquote(optionsTable))
            # geneTableContainer
            TD_LR.append(HT.Blockquote(tableForm))

        self.body = TD_LR
       
        #self.dict['body'] = TD_LR
        #self.dict['title'] = "Mapping"


    def writeQTL2Text(self, filename):
        if self.multipleInterval:
            return ""
        #_dominance = (self.genotype.type == 'intercross')
        _Mb = self.genotype.Mbmap

        ###Write to text file
        fpText = open(os.path.join(webqtlConfig.TMPDIR, filename) + '.txt','wb')

        fpText.write("Source: WebQTL, The GeneNetwork (%s)\n" % webqtlConfig.PORTADDR)
        #
        fpText.write("Site: %s\n" % webqtlConfig.SITENAME)
        fpText.write("Page: Map Viewer\n")
        fpText.write(time.strftime("Date and Time (US Center): %b %d, %Y at %I.%M %p\n", time.localtime()))
        fpText.write("Trait ID: %s\n" % self.this_trait.name)
        fpText.write("Suggestive LRS = %0.2f\n" % self.suggestive)
        fpText.write("Significant LRS = %0.2f\n" % self.significance)
        """
        if self.this_trait.symbol and self.this_trait.chr and self.this_trait.mb:
                writeSymbol, writeChromosome, writeMb = self.this_trait.symbol, self.this_trait.chr, self.this_trait.mb
        else:
                writeSymbol, writeChromosome, writeMb = (" ", " ", " ")
        fpText.write("Gene Symbol: %s\n" % writeSymbol)
        fpText.write("Location: Chr %s @ %s Mb\n" % (writeChromosome, writeMb))
        #selectedChr = self.indexToChrName(int(fd.formdata.getvalue('chromosomes', -1)))
        #fpText.write("Chromosome: %s\n" % selectedChr)
        fpText.write("Region: %0.6f-%0.6f Mb\n\n" % (self.startMb, self.endMb))
        """

        if hasattr(self, 'LRSArray'):
            if _dominance:
                fpText.write('Chr\tLocus\tcM\tMb\tLRS\tP-value\tAdditive\tDominance\n')
            else:
                fpText.write('Chr\tLocus\tcM\tMb\tLRS\tP-value\tAdditive\n')
        else:
            if _dominance:
                fpText.write('Chr\tLocus\tcM\tMb\tLRS\tAdditive\tDominance\n')
            else:
                fpText.write('Chr\tLocus\tcM\tMb\tLRS\tAdditive\n')

        i = 0
        for marker in self.qtlresults:
            if _Mb:
                locusMb = '%2.3f' % marker['Mb']
            else:
                locusMb = 'N/A'

            if hasattr(self, 'LRSArray'):
                if start_vars['score_type'] == "LRS":
                    lrs_lod = marker['lrs_value']
                else:
                    lrs_lod = marker['lod_score']

                P_value = self.calculatePValue(lrs_lod, self.LRSArray)

                #if _dominance:
                #    fpText.write("%s\t%s\t%2.3f\t%s\t%2.3f\t%2.3f\t%2.3f\t%2.3f\n" %(qtlresult.locus.chr, \
                #            qtlresult.locus.name, qtlresult.locus.cM, locusMb , qtlresult.lrs, P_value,  qtlresult.additive, qtlresult.dominance))
                #else:
                if P_value:
                    fpText.write("%s\t%s\t%2.3f\t%s\t%2.3f\t%2.3f\n" %(marker['chr'], \
                        marker['name'], marker['cM'], locusMb, lrs_lod, P_value))
                else:
                    fpText.write("%s\t%s\t%2.3f\t%s\t%2.3f\t%s\n" %(marker['chr'], \
                        marker['name'], marker['cM'], locusMb , lrs_lod, '-'))
            else:
                #if _dominance:
                #    fpText.write("%s\t%s\t%2.3f\t%s\t%2.3f\t%2.3f\t%2.3f\n" %(qtlresult.locus.chr, \
                #            qtlresult.locus.name, qtlresult.locus.cM, locusMb , qtlresult.lrs, qtlresult.additive, qtlresult.dominance))
                #else:
                fpText.write("%s\t%s\t%2.3f\t%s\t%2.3f\n" %(marker['chr'], \
                        marker['name'], marker['cM'], locusMb , lrs_lod))

            i += 1

        fpText.close()
        textUrl = '/tmp/'+filename+'.txt'
        #textUrl = HT.Href(text = 'Download', url= '/tmp/'+filename+'.txt', target = "_blank", Class='smallsize')
        return textUrl

    def plotIntMapping(self, canvas, offset= (80, 120, 20, 100), zoom = 1, startMb = None, endMb = None, showLocusForm = ""):
        #calculating margins
        xLeftOffset, xRightOffset, yTopOffset, yBottomOffset = offset
        if self.multipleInterval:
            yTopOffset = max(80, yTopOffset)
        else:
            if self.legendChecked:
                yTopOffset = max(80, yTopOffset)
            else:
                pass

        if self.plotScale != 'physic':
            yBottomOffset = max(120, yBottomOffset)
        fontZoom = zoom
        if zoom == 2:
            xLeftOffset += 20
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
        if self.plotScale == 'physic' and self.selectedChr > -1:
            drawAreaHeight -= self.ENSEMBL_BAND_HEIGHT + self.UCSC_BAND_HEIGHT+ self.WEBQTL_BAND_HEIGHT + 3*self.BAND_SPACING+ 10*zoom
            if self.geneChecked:
                drawAreaHeight -= self.NUM_GENE_ROWS*self.EACH_GENE_HEIGHT + 3*self.BAND_SPACING + 10*zoom
        else:
            if self.selectedChr > -1:
                drawAreaHeight -= 20
            else:
                drawAreaHeight -= 30

## BEGIN HaplotypeAnalyst
        if self.haplotypeAnalystChecked and self.selectedChr > -1:
            drawAreaHeight -= self.EACH_GENE_HEIGHT * (self.NR_INDIVIDUALS+10) * 2 * zoom
## END HaplotypeAnalyst

        if zoom == 2:
            drawAreaHeight -= 60

        #Image map
        gifmap = HT.Map(name = "WebQTLImageMap")
        #gifmap = None

        newoffset = (xLeftOffset, xRightOffset, yTopOffset, yBottomOffset)
        # Draw the alternating-color background first and get plotXScale
        plotXScale = self.drawGraphBackground(canvas, gifmap, offset=newoffset, zoom= zoom, startMb=startMb, endMb = endMb)

        #draw bootstap
        #if self.bootChecked and not self.multipleInterval:
        #    self.drawBootStrapResult(canvas, fd.nboot, drawAreaHeight, plotXScale, offset=newoffset)

        # Draw clickable region and gene band if selected
        if self.plotScale == 'physic' and self.selectedChr > -1:
            self.drawClickBand(canvas, gifmap, plotXScale, offset=newoffset, zoom = zoom, startMb=startMb, endMb = endMb)
            if self.geneChecked and self.geneCol:
                self.drawGeneBand(canvas, gifmap, plotXScale, offset=newoffset, zoom = zoom, startMb=startMb, endMb = endMb)
            if self.SNPChecked:
                self.drawSNPTrackNew(canvas, offset=newoffset, zoom = 2*zoom, startMb=startMb, endMb = endMb)
## BEGIN HaplotypeAnalyst
            if self.haplotypeAnalystChecked:
                self.drawHaplotypeBand(canvas, gifmap, plotXScale, offset=newoffset, zoom = zoom, startMb=startMb, endMb = endMb)
## END HaplotypeAnalyst
        # Draw X axis
        self.drawXAxis(canvas, drawAreaHeight, gifmap, plotXScale, showLocusForm, offset=newoffset, zoom = zoom, startMb=startMb, endMb = endMb)
        # Draw QTL curve
        self.drawQTL(canvas, drawAreaHeight, gifmap, plotXScale, offset=newoffset, zoom= zoom, startMb=startMb, endMb = endMb)

        #draw legend
        if self.multipleInterval:
            self.drawMultiTraitName(fd, canvas, gifmap, showLocusForm, offset=newoffset)
        elif self.legendChecked:
            self.drawLegendPanel(fd, canvas, offset=newoffset, zoom = zoom)
        else:
            pass

        #draw position, no need to use a separate function
        if self.genotype.Mbmap:
            self.drawProbeSetPosition(canvas, plotXScale, offset=newoffset, zoom = zoom)

        return gifmap

    def drawBootStrapResult(self, canvas, nboot, drawAreaHeight, plotXScale, offset= (40, 120, 80, 10), zoom = 1, startMb = None, endMb = None):
        xLeftOffset, xRightOffset, yTopOffset, yBottomOffset = offset
        plotWidth = canvas.size[0] - xLeftOffset - xRightOffset
        plotHeight = canvas.size[1] - yTopOffset - yBottomOffset
        yZero = canvas.size[1] - yBottomOffset
        fontZoom = zoom
        if zoom == 2:
            fontZoom = 1.5

        bootHeightThresh = drawAreaHeight*3/4

        #break bootstrap result into groups
        BootCoord = []
        i = 0
        startX = xLeftOffset
        for j, _chr in enumerate(self.genotype):
            BootCoord.append( [])
            for _locus in _chr:
                if self.plotScale == 'physic':
                    Xc = startX + (_locus.Mb-self.startMb)*plotXScale
                else:
                    Xc = startX + (_locus.cM-_chr[0].cM)*plotXScale
                BootCoord[-1].append([Xc, self.bootResult[i]])
                i += 1
            startX += (self.ChrLengthDistList[j] + self.GraphInterval)*plotXScale

        #reduce bootResult
        if self.selectedChr > -1:
            maxBootBar = 80.0
        else:
            maxBootBar = 200.0
        stepBootStrap = plotWidth/maxBootBar
        reducedBootCoord = []
        maxBootCount = 0

        for BootChrCoord in BootCoord:
            nBoot = len(BootChrCoord)
            bootStartPixX = BootChrCoord[0][0]
            bootCount = BootChrCoord[0][1]
            for i in range(1, nBoot):
                if BootChrCoord[i][0] - bootStartPixX < stepBootStrap:
                    bootCount += BootChrCoord[i][1]
                    continue
                else:
                    if maxBootCount < bootCount:
                        maxBootCount = bootCount
                    # end if
                    reducedBootCoord.append([bootStartPixX, BootChrCoord[i][0], bootCount])
                    bootStartPixX = BootChrCoord[i][0]
                    bootCount = BootChrCoord[i][1]
                # end else
            # end for
            #add last piece
            if BootChrCoord[-1][0] - bootStartPixX  > stepBootStrap/2.0:
                reducedBootCoord.append([bootStartPixX, BootChrCoord[-1][0], bootCount])
            else:
                reducedBootCoord[-1][2] += bootCount
                reducedBootCoord[-1][1] = BootChrCoord[-1][0]
            # end else
            if maxBootCount < reducedBootCoord[-1][2]:
                maxBootCount = reducedBootCoord[-1][2]
            # end if
        for item in reducedBootCoord:
            if item[2] > 0:
                if item[0] < xLeftOffset:
                    item[0] = xLeftOffset
                if item[0] > xLeftOffset+plotWidth:
                    item[0] = xLeftOffset+plotWidth
                if item[1] < xLeftOffset:
                    item[1] = xLeftOffset
                if item[1] > xLeftOffset+plotWidth:
                    item[1] = xLeftOffset+plotWidth
                if item[0] != item[1]:
                    canvas.drawRect(item[0], yZero, item[1], yZero - item[2]*bootHeightThresh/maxBootCount,
                    fillColor=self.BOOTSTRAP_BOX_COLOR)

        ###draw boot scale
        highestPercent = (maxBootCount*100.0)/nboot
        bootScale = Plot.detScale(0, highestPercent)
        bootScale = Plot.frange(bootScale[0], bootScale[1], bootScale[1]/bootScale[2])
        bootScale = bootScale[:-1] + [highestPercent]

        bootOffset = 50*fontZoom
        bootScaleFont=pid.Font(ttf="verdana",size=13*fontZoom,bold=0)
        canvas.drawRect(canvas.size[0]-bootOffset,yZero-bootHeightThresh,canvas.size[0]-bootOffset-15*zoom,yZero,fillColor = pid.yellow)
        canvas.drawLine(canvas.size[0]-bootOffset+4, yZero, canvas.size[0]-bootOffset, yZero, color=pid.black)
        canvas.drawString('0%' ,canvas.size[0]-bootOffset+10,yZero+5,font=bootScaleFont,color=pid.black)
        for item in bootScale:
            if item == 0:
                continue
            bootY = yZero-bootHeightThresh*item/highestPercent
            canvas.drawLine(canvas.size[0]-bootOffset+4,bootY,canvas.size[0]-bootOffset,bootY,color=pid.black)
            canvas.drawString('%2.1f'%item ,canvas.size[0]-bootOffset+10,bootY+5,font=bootScaleFont,color=pid.black)

        if self.legendChecked:
            startPosY = 30
            nCol = 2
            smallLabelFont = pid.Font(ttf="trebuc", size=12*fontZoom, bold=1)
            leftOffset = xLeftOffset+(nCol-1)*200
            canvas.drawRect(leftOffset,startPosY-6, leftOffset+12,startPosY+6, fillColor=pid.yellow)
            canvas.drawString('Frequency of the Peak LRS',leftOffset+ 20, startPosY+5,font=smallLabelFont,color=pid.black)

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
            Chr = self.traitList[0].chr
            Mb = self.traitList[0].mb
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
            smallLabelFont = pid.Font(ttf="trebuc", size=12*fontZoom, bold=1)
            leftOffset = xLeftOffset+(nCol-1)*200*fontZoom
            canvas.drawPolygon(((leftOffset+6, startPosY-6), (leftOffset, startPosY+6), (leftOffset+12, startPosY+6)), edgeColor=pid.black, fillColor=self.TRANSCRIPT_LOCATION_COLOR, closed=1)
            canvas.drawString("Sequence Site", (leftOffset+15), (startPosY+5), smallLabelFont, self.TOP_RIGHT_INFO_COLOR)


    def drawSNPTrackNew(self, canvas, offset= (40, 120, 80, 10), zoom = 1, startMb = None, endMb = None):
        if self.plotScale != 'physic' or self.selectedChr == -1 or not self.diffCol:
            return

        SNP_HEIGHT_MODIFIER = 18.0

        xLeftOffset, xRightOffset, yTopOffset, yBottomOffset = offset
        plotWidth = canvas.size[0] - xLeftOffset - xRightOffset
        plotHeight = canvas.size[1] - yTopOffset - yBottomOffset
        yZero = canvas.size[1] - yBottomOffset
        fontZoom = zoom
        if zoom == 2:
            fontZoom = 1.5

        drawSNPLocationY = yTopOffset + plotHeight
        chrName = self.genotype[0].name

        stepMb = (endMb-startMb)/plotWidth
        strainId1, strainId2 = self.diffCol
        SNPCounts = []

        while startMb<endMb:
            self.cursor.execute("""
                    select
                            count(*) from BXDSnpPosition
                    where
                            Chr = '%s' AND Mb >= %2.6f AND Mb < %2.6f AND
                            StrainId1 = %d AND StrainId2 = %d
                    """ % (chrName, startMb, startMb+stepMb, strainId1, strainId2))
            SNPCounts.append(self.cursor.fetchone()[0])
            startMb += stepMb

        if (len(SNPCounts) > 0):
            maxCount = max(SNPCounts)
            if maxCount>0:
                for i in range(xLeftOffset, xLeftOffset + plotWidth):
                    snpDensity = float(SNPCounts[i-xLeftOffset]*SNP_HEIGHT_MODIFIER/maxCount)
                    canvas.drawLine(i, drawSNPLocationY+(snpDensity)*zoom, i, drawSNPLocationY-(snpDensity)*zoom, color=self.SNP_COLOR, width=1)

    def drawMultiTraitName(self, fd, canvas, gifmap, showLocusForm, offset= (40, 120, 80, 10), zoom = 1, locLocation= None):
        nameWidths = []
        yPaddingTop = 10
        colorFont=pid.Font(ttf="trebuc",size=12,bold=1)
        if len(self.qtlresults) >20 and self.selectedChr > -1:
            rightShift = 20
            rightShiftStep = 60
            rectWidth = 10
        else:
            rightShift = 40
            rightShiftStep = 80
            rectWidth = 15

        for k, thisTrait in enumerate(self.traitList):
            thisLRSColor = self.colorCollection[k]
            kstep = k % 4
            if k!=0 and kstep==0:
                if nameWidths:
                    rightShiftStep = max(nameWidths[-4:]) + rectWidth + 20
                rightShift += rightShiftStep

            name = thisTrait.displayName()
            nameWidth = canvas.stringWidth(name,font=colorFont)
            nameWidths.append(nameWidth)

            canvas.drawRect(rightShift,yPaddingTop+kstep*15, rectWidth+rightShift,yPaddingTop+10+kstep*15, fillColor=thisLRSColor)
            canvas.drawString(name,rectWidth+2+rightShift,yPaddingTop+10+kstep*15,font=colorFont,color=pid.black)
            if thisTrait.db:

                COORDS = "%d,%d,%d,%d" %(rectWidth+2+rightShift,yPaddingTop+kstep*15,rectWidth+2+rightShift+nameWidth,yPaddingTop+10+kstep*15,)
                HREF= "javascript:showDatabase3('%s','%s','%s','');" % (showLocusForm, thisTrait.db.name, thisTrait.name)
                Areas = HT.Area(shape='rect',coords=COORDS,href=HREF)
                gifmap.areas.append(Areas)


    def drawLegendPanel(self, fd, canvas, offset= (40, 120, 80, 10), zoom = 1, locLocation= None):
        xLeftOffset, xRightOffset, yTopOffset, yBottomOffset = offset
        plotWidth = canvas.size[0] - xLeftOffset - xRightOffset
        plotHeight = canvas.size[1] - yTopOffset - yBottomOffset
        yZero = canvas.size[1] - yBottomOffset
        fontZoom = zoom
        if zoom == 2:
            fontZoom = 1.5


        labelFont=pid.Font(ttf="trebuc",size=12*fontZoom, bold=1)
        startPosY = 15
        stepPosY = 12*fontZoom
        canvas.drawLine(xLeftOffset,startPosY,xLeftOffset+32,startPosY,color=self.LRS_COLOR, width=2)
        canvas.drawString(self.LRS_LOD, xLeftOffset+40,startPosY+5,font=labelFont,color=pid.black)
        startPosY += stepPosY

        if self.additiveChecked:
            startPosX = xLeftOffset
            canvas.drawLine(startPosX,startPosY,startPosX+17,startPosY,color=self.ADDITIVE_COLOR_POSITIVE, width=2)
            canvas.drawLine(startPosX+18,startPosY,startPosX+32,startPosY,color=self.ADDITIVE_COLOR_NEGATIVE, width=2)
            canvas.drawString('Additive Effect',startPosX+40,startPosY+5,font=labelFont,color=pid.black)

        if self.genotype.type == 'intercross' and self.dominanceChecked:
            startPosX = xLeftOffset
            startPosY += stepPosY
            canvas.drawLine(startPosX,startPosY,startPosX+17,startPosY,color=self.DOMINANCE_COLOR_POSITIVE, width=4)
            canvas.drawLine(startPosX+18,startPosY,startPosX+35,startPosY,color=self.DOMINANCE_COLOR_NEGATIVE, width=4)
            canvas.drawString('Dominance Effect',startPosX+42,startPosY+5,font=labelFont,color=pid.black)

        if self.haplotypeAnalystChecked:
            startPosY += stepPosY
            startPosX = xLeftOffset
            canvas.drawLine(startPosX,startPosY,startPosX+17,startPosY,color=self.HAPLOTYPE_POSITIVE, width=4)
            canvas.drawLine(startPosX+18,startPosY,startPosX+35,startPosY,color=self.HAPLOTYPE_NEGATIVE, width=4)
            canvas.drawLine(startPosX+36,startPosY,startPosX+53,startPosY,color=self.HAPLOTYPE_HETEROZYGOUS, width=4)
            canvas.drawLine(startPosX+54,startPosY,startPosX+67,startPosY,color=self.HAPLOTYPE_RECOMBINATION, width=4)
            canvas.drawString('Haplotypes (Pat, Mat, Het, Unk)',startPosX+76,startPosY+5,font=labelFont,color=pid.black)

        if self.permChecked:
            startPosY += stepPosY
            startPosX = xLeftOffset
            canvas.drawLine(startPosX, startPosY, startPosX + 32, startPosY, color=self.SIGNIFICANT_COLOR, width=self.SIGNIFICANT_WIDTH)
            canvas.drawLine(startPosX, startPosY + stepPosY, startPosX + 32, startPosY + stepPosY, color=self.SUGGESTIVE_COLOR, width=self.SUGGESTIVE_WIDTH)
            lod = 1
            if self.LRS_LOD == 'LOD':
                lod = self.LODFACTOR
            canvas.drawString('Significant %s = %2.2f' % (self.LRS_LOD, self.significance/lod),xLeftOffset+42,startPosY +5,font=labelFont,color=pid.black)
            canvas.drawString('Suggestive %s = %2.2f' % (self.LRS_LOD, self.suggestive/lod),xLeftOffset+42,startPosY + 5 +stepPosY,font=labelFont,color=pid.black)



        labelFont=pid.Font(ttf="verdana",size=12*fontZoom)
        labelColor = pid.black
        if self.selectedChr == -1:
            string1 = 'Mapping for Dataset: %s, mapping on All Chromosomes' % fd.RISet
        else:
            string1 = 'Mapping for Dataset: %s, mapping on Chromosome %s' % (fd.RISet,self.genotype[0].name)
        if self.controlLocus:
            string2 = 'Using %s as control' % self.controlLocus
        else:
            string2 = 'Using Haldane mapping function with no control for other QTLs'
        d = 4+ max(canvas.stringWidth(string1,font=labelFont),canvas.stringWidth(string2,font=labelFont))
        if fd.identification:
            identification = "Trait ID: %s" % fd.identification
            canvas.drawString(identification,canvas.size[0] - xRightOffset-d,20*fontZoom,font=labelFont,color=labelColor)

        canvas.drawString(string1,canvas.size[0] - xRightOffset-d,35*fontZoom,font=labelFont,color=labelColor)
        canvas.drawString(string2,canvas.size[0] - xRightOffset-d,50*fontZoom,font=labelFont,color=labelColor)


    def drawGeneBand(self, canvas, gifmap, plotXScale, offset= (40, 120, 80, 10), zoom = 1, startMb = None, endMb = None):
        if self.plotScale != 'physic' or self.selectedChr == -1 or not self.geneCol:
            return

        xLeftOffset, xRightOffset, yTopOffset, yBottomOffset = offset
        plotWidth = canvas.size[0] - xLeftOffset - xRightOffset
        plotHeight = canvas.size[1] - yTopOffset - yBottomOffset
        yZero = canvas.size[1] - yBottomOffset
        fontZoom = zoom
        if zoom == 2:
            fontZoom = 1.5

        yPaddingTop = yTopOffset

        displayStartInBases = startMb*self.kONE_MILLION
        displayEndInBases = endMb*self.kONE_MILLION

        for gIndex, theGO in enumerate(self.geneCol):
            geneNCBILink = 'http://www.ncbi.nlm.nih.gov/gene?term=%s'
            if self.species == "mouse":
                txStart = theGO["TxStart"]
                txEnd = theGO["TxEnd"]
                geneLength = (txEnd - txStart)*1000.0
                tenPercentLength = geneLength*0.0001
                SNPdensity = theGO["snpCount"]/geneLength

                exonStarts = map(float, theGO['exonStarts'].split(",")[:-1])
                exonEnds = map(float, theGO['exonEnds'].split(",")[:-1])
                cdsStart = theGO['cdsStart']
                cdsEnd = theGO['cdsEnd']
                accession = theGO['NM_ID']
                geneId = theGO['GeneID']
                geneSymbol = theGO["GeneSymbol"]
                strand = theGO["Strand"]
                exonCount = theGO["exonCount"]

                geneStartPix = xLeftOffset + plotXScale*(float(txStart) - startMb)
                geneEndPix = xLeftOffset + plotXScale*(float(txEnd) - startMb) #at least one pixel

                if (geneEndPix < xLeftOffset):
                    return; # this gene is not on the screen
                elif (geneEndPix > xLeftOffset + plotWidth):
                    geneEndPix = xLeftOffset + plotWidth; # clip the last in-range gene
                if (geneStartPix > xLeftOffset + plotWidth):
                    return; # we are outside the valid on-screen range, so stop drawing genes
                elif (geneStartPix < xLeftOffset):
                    geneStartPix = xLeftOffset; # clip the first in-range gene

                #color the gene based on SNP density


                #found earlier, needs to be recomputed as snps are added

                #always apply colors now, even if SNP Track not checked - Zach 11/24/2010

                densities=[1.0000000000000001e-05, 0.094094033555233408, 0.3306166377816987, 0.88246026851027781, 2.6690084029581951, 4.1, 61.0]
                if SNPdensity < densities[0]:
                    myColor = pid.black
                elif SNPdensity < densities[1]:
                    myColor = pid.purple
                elif SNPdensity < densities[2]:
                    myColor = pid.darkblue
                elif SNPdensity < densities[3]:
                    myColor = pid.darkgreen
                elif SNPdensity < densities[4]:
                    myColor = pid.gold
                elif SNPdensity < densities[5]:
                    myColor = pid.darkorange
                else:
                    myColor = pid.darkred

                outlineColor = myColor
                fillColor    = myColor

                TITLE = "Gene: %s (%s)\nFrom %2.3f to %2.3f Mb (%s)\nNum. exons: %d." % (geneSymbol, accession, float(txStart), float(txEnd), strand, exonCount)
                # NL: 06-02-2011 Rob required to change this link for gene related
                HREF=geneNCBILink %geneSymbol

            elif self.species == "rat":
                exonStarts = []
                exonEnds = []
                txStart = theGO["TxStart"]
                txEnd = theGO["TxEnd"]
                cdsStart = theGO["TxStart"]
                cdsEnd = theGO["TxEnd"]
                geneId = theGO["GeneID"]
                geneSymbol = theGO["GeneSymbol"]
                strand = theGO["Strand"]
                exonCount = 0

                geneStartPix = xLeftOffset + plotXScale*(float(txStart) - startMb)
                geneEndPix = xLeftOffset + plotXScale*(float(txEnd) - startMb) #at least one pixel

                if (geneEndPix < xLeftOffset):
                    return; # this gene is not on the screen
                elif (geneEndPix > xLeftOffset + plotWidth):
                    geneEndPix = xLeftOffset + plotWidth; # clip the last in-range gene
                if (geneStartPix > xLeftOffset + plotWidth):
                    return; # we are outside the valid on-screen range, so stop drawing genes
                elif (geneStartPix < xLeftOffset):
                    geneStartPix = xLeftOffset; # clip the first in-range gene

                outlineColor = pid.darkblue
                fillColor = pid.darkblue
                TITLE = "Gene: %s\nFrom %2.3f to %2.3f Mb (%s)" % (geneSymbol, float(txStart), float(txEnd), strand)
                # NL: 06-02-2011 Rob required to change this link for gene related
                HREF=geneNCBILink %geneSymbol
            else:
                outlineColor = pid.orange
                fillColor = pid.orange
                TITLE = "Gene: %s" % geneSymbol

            #Draw Genes
            geneYLocation = yPaddingTop + (gIndex % self.NUM_GENE_ROWS) * self.EACH_GENE_HEIGHT*zoom

            if 1:#drawClickableRegions:
                geneYLocation += self.UCSC_BAND_HEIGHT + self.BAND_SPACING + self.ENSEMBL_BAND_HEIGHT + self.BAND_SPACING + self.WEBQTL_BAND_HEIGHT + self.BAND_SPACING
            else:
                geneYLocation += self.BAND_SPACING

            #draw the detail view
            if self.endMb - self.startMb <= self.DRAW_DETAIL_MB and geneEndPix - geneStartPix > self.EACH_GENE_ARROW_SPACING * 3:
                utrColor = pid.Color(0.66, 0.66, 0.66)
                arrowColor = pid.Color(0.7, 0.7, 0.7)

                #draw the line that runs the entire length of the gene
                #canvas.drawString(str(geneStartPix), 300, 400)
                canvas.drawLine(geneStartPix, geneYLocation + self.EACH_GENE_HEIGHT/2*zoom, geneEndPix, geneYLocation + self.EACH_GENE_HEIGHT/2*zoom, color=outlineColor, width=1)

                #draw the arrows
                for xCoord in range(0, geneEndPix-geneStartPix):

                    if (xCoord % self.EACH_GENE_ARROW_SPACING == 0 and xCoord + self.EACH_GENE_ARROW_SPACING < geneEndPix-geneStartPix) or xCoord == 0:
                        if strand == "+":
                            canvas.drawLine(geneStartPix + xCoord, geneYLocation, geneStartPix + xCoord + self.EACH_GENE_ARROW_WIDTH, geneYLocation +(self.EACH_GENE_HEIGHT / 2)*zoom, color=arrowColor, width=1)
                            canvas.drawLine(geneStartPix + xCoord, geneYLocation + self.EACH_GENE_HEIGHT*zoom, geneStartPix + xCoord+self.EACH_GENE_ARROW_WIDTH, geneYLocation + (self.EACH_GENE_HEIGHT / 2) * zoom, color=arrowColor, width=1)
                        else:
                            canvas.drawLine(geneStartPix + xCoord + self.EACH_GENE_ARROW_WIDTH, geneYLocation, geneStartPix + xCoord, geneYLocation +(self.EACH_GENE_HEIGHT / 2)*zoom, color=arrowColor, width=1)
                            canvas.drawLine(geneStartPix + xCoord + self.EACH_GENE_ARROW_WIDTH, geneYLocation + self.EACH_GENE_HEIGHT*zoom, geneStartPix + xCoord, geneYLocation + (self.EACH_GENE_HEIGHT / 2)*zoom, color=arrowColor, width=1)

                #draw the blocks for the exon regions
                for i in range(0, len(exonStarts)):
                    exonStartPix = (exonStarts[i]-startMb)*plotXScale + xLeftOffset
                    exonEndPix = (exonEnds[i]-startMb)*plotXScale + xLeftOffset
                    if (exonStartPix < xLeftOffset):
                        exonStartPix = xLeftOffset
                    if (exonEndPix < xLeftOffset):
                        exonEndPix = xLeftOffset
                    if (exonEndPix > xLeftOffset + plotWidth):
                        exonEndPix = xLeftOffset + plotWidth
                    if (exonStartPix > xLeftOffset + plotWidth):
                        exonStartPix = xLeftOffset + plotWidth
                    canvas.drawRect(exonStartPix, geneYLocation, exonEndPix, (geneYLocation + self.EACH_GENE_HEIGHT*zoom), edgeColor = outlineColor, fillColor = fillColor)

                #draw gray blocks for 3' and 5' UTR blocks
                if cdsStart and cdsEnd:

                    utrStartPix = (txStart-startMb)*plotXScale + xLeftOffset
                    utrEndPix = (cdsStart-startMb)*plotXScale + xLeftOffset
                    if (utrStartPix < xLeftOffset):
                        utrStartPix = xLeftOffset
                    if (utrEndPix < xLeftOffset):
                        utrEndPix = xLeftOffset
                    if (utrEndPix > xLeftOffset + plotWidth):
                        utrEndPix = xLeftOffset + plotWidth
                    if (utrStartPix > xLeftOffset + plotWidth):
                        utrStartPix = xLeftOffset + plotWidth
                    canvas.drawRect(utrStartPix, geneYLocation, utrEndPix, (geneYLocation+self.EACH_GENE_HEIGHT*zoom), edgeColor=utrColor, fillColor =utrColor)

                    if self.DRAW_UTR_LABELS and self.endMb - self.startMb <= self.DRAW_UTR_LABELS_MB:
                        if strand == "-":
                            labelText = "3'"
                        else:
                            labelText = "5'"
                        canvas.drawString(labelText, utrStartPix-9, geneYLocation+self.EACH_GENE_HEIGHT, pid.Font(face="helvetica", size=2))

                    #the second UTR region

                    utrStartPix = (cdsEnd-startMb)*plotXScale + xLeftOffset
                    utrEndPix = (txEnd-startMb)*plotXScale + xLeftOffset
                    if (utrStartPix < xLeftOffset):
                        utrStartPix = xLeftOffset
                    if (utrEndPix < xLeftOffset):
                        utrEndPix = xLeftOffset
                    if (utrEndPix > xLeftOffset + plotWidth):
                        utrEndPix = xLeftOffset + plotWidth
                    if (utrStartPix > xLeftOffset + plotWidth):
                        utrStartPix = xLeftOffset + plotWidth
                    canvas.drawRect(utrStartPix, geneYLocation, utrEndPix, (geneYLocation+self.EACH_GENE_HEIGHT*zoom), edgeColor=utrColor, fillColor =utrColor)

                    if self.DRAW_UTR_LABELS and self.endMb - self.startMb <= self.DRAW_UTR_LABELS_MB:
                        if tstrand == "-":
                            labelText = "5'"
                        else:
                            labelText = "3'"
                        canvas.drawString(labelText, utrEndPix+2, geneYLocation+self.EACH_GENE_HEIGHT, pid.Font(face="helvetica", size=2))

            #draw the genes as rectangles
            else:
                canvas.drawRect(geneStartPix, geneYLocation, geneEndPix, (geneYLocation + self.EACH_GENE_HEIGHT*zoom), edgeColor = outlineColor, fillColor = fillColor)

            COORDS = "%d, %d, %d, %d" %(geneStartPix, geneYLocation, geneEndPix, (geneYLocation + self.EACH_GENE_HEIGHT))
            # NL: 06-02-2011 Rob required to display NCBI info in a new window
            gifmap.areas.append(HT.Area(shape='rect',coords=COORDS,href=HREF, title=TITLE,target="_blank"))

## BEGIN HaplotypeAnalyst
    def drawHaplotypeBand(self, canvas, gifmap, plotXScale, offset= (40, 120, 80, 10), zoom = 1, startMb = None, endMb = None):
        if self.plotScale != 'physic' or self.selectedChr == -1 or not self.geneCol:
            return


        fpText = open(os.path.join(webqtlConfig.TMPDIR, "hallo") + '.txt','wb')

        clickableRegionLabelFont=pid.Font(ttf="verdana", size=9, bold=0)

        xLeftOffset, xRightOffset, yTopOffset, yBottomOffset = offset
        plotWidth = canvas.size[0] - xLeftOffset - xRightOffset
        plotHeight = canvas.size[1] - yTopOffset - yBottomOffset
        yZero = canvas.size[1] - yBottomOffset
        fontZoom = zoom
        widthMultiplier = 1

        yPaddingTop = yTopOffset

        exprdrawn = 0

        thisTrait = self.traitList[0]
        _strains, _vals, _vars = thisTrait.exportInformative()

        smd=[]
        for ii, _val in enumerate(_vals):
            temp = GeneralObject(name=_strains[ii], value=_val)
            smd.append(temp)

        smd.sort(lambda A, B: cmp(A.value, B.value))
        smd.reverse()

        bxdlist=list(self.genotype.prgy)

        oldgeneEndPix = -1
        #Initializing plotRight, error before
        plotRight = xRightOffset

#### find out PlotRight
        for i, _locus in enumerate(self.genotype[0]):
            txStart = self.genotype[0][i].Mb
            txEnd   = self.genotype[0][i].Mb

            geneStartPix = xLeftOffset + plotXScale*(float(txStart) - startMb)  - 0
            geneEndPix = xLeftOffset + plotXScale*(float(txEnd) - startMb) - 0

            drawit = 1
            if (geneStartPix < xLeftOffset):
                drawit = 0;
            if (geneStartPix > xLeftOffset + plotWidth):
                drawit = 0;

            if drawit == 1:

                if self.genotype[0][i].name != " - " :

                    plotRight = geneEndPix + 4



#### end find out PlotRight

        firstGene = 1
        lastGene = 0

        #Sets the length to the length of the strain list. Beforehand, "oldgeno = self.genotype[0][i].genotype"
        #was the only place it was initialized, which worked as long as the very start (startMb = None/0) wasn't being mapped.
        #Now there should always be some value set for "oldgeno" - Zach 12/14/2010
        oldgeno = [None]*len(self.strainlist)

        for i, _locus in enumerate(self.genotype[0]):
            txStart = self.genotype[0][i].Mb
            txEnd   = self.genotype[0][i].Mb

            geneStartPix = xLeftOffset + plotXScale*(float(txStart) - startMb)  - 0
            geneEndPix   = xLeftOffset + plotXScale*(float(txEnd)   - startMb)  + 0

            if oldgeneEndPix >= xLeftOffset:
                drawStart = oldgeneEndPix + 4
            else:
                drawStart = xLeftOffset + 3

            drawEnd = plotRight - 9

            drawit = 1

            if (geneStartPix < xLeftOffset):
                if firstGene == 1:
                    drawit = 1
                else:
                    drawit = 0

            elif (geneStartPix > (xLeftOffset + plotWidth - 3)):
                if lastGene == 0:
                    drawit = 1
                    drawEnd = xLeftOffset + plotWidth - 6
                    lastGene = 1
                else:
                    break

            else:
                firstGene = 0
                drawit = 1

            if drawit == 1:
                myColor = pid.darkblue
                outlineColor = myColor
                fillColor    = myColor

                maxind=0

                #Draw Genes

                geneYLocation = yPaddingTop + self.NUM_GENE_ROWS * (self.EACH_GENE_HEIGHT)*zoom

                if 1:#drawClickableRegions:
                    geneYLocation += self.UCSC_BAND_HEIGHT + self.BAND_SPACING + self.ENSEMBL_BAND_HEIGHT + self.BAND_SPACING + self.WEBQTL_BAND_HEIGHT + self.BAND_SPACING
                else:
                    geneYLocation += self.BAND_SPACING

                if self.genotype[0][i].name != " - " :

                    if (firstGene == 1) and (lastGene != 1):
                        oldgeneEndPix = drawStart = xLeftOffset
                        oldgeno = self.genotype[0][i].genotype
                        continue

                    for j,_geno in enumerate (self.genotype[0][i].genotype):

                        plotbxd=0
                        for item in smd:
                            if item.name == bxdlist[j]:
                                plotbxd=1

                        if (plotbxd == 1):
                            ind = 0
                            counter = 0
                            for item in smd:
                                counter = counter + 1
                                if item.name == bxdlist[j]:
                                    ind = counter
                            maxind=max(ind,maxind)

                            # lines
                            if (oldgeno[j] == -1 and _geno == -1):
                                mylineColor = self.HAPLOTYPE_NEGATIVE
                            elif (oldgeno[j] == 1 and _geno == 1):
                                mylineColor = self.HAPLOTYPE_POSITIVE
                            elif (oldgeno[j] == 0 and _geno == 0):
                                mylineColor = self.HAPLOTYPE_HETEROZYGOUS
                            else:
                                mylineColor = self.HAPLOTYPE_RECOMBINATION # XZ: Unknown

                            canvas.drawLine(drawStart, geneYLocation+7+2*ind*self.EACH_GENE_HEIGHT*zoom, drawEnd, geneYLocation+7+2*ind*self.EACH_GENE_HEIGHT*zoom, color = mylineColor, width=zoom*(self.EACH_GENE_HEIGHT+2))

                            fillColor=pid.black
                            outlineColor=pid.black
                            if lastGene == 0:
                                canvas.drawRect(geneStartPix, geneYLocation+2*ind*self.EACH_GENE_HEIGHT*zoom, geneEndPix, geneYLocation+2*ind*self.EACH_GENE_HEIGHT+ 2*self.EACH_GENE_HEIGHT*zoom, edgeColor = outlineColor, fillColor = fillColor)


                            COORDS = "%d, %d, %d, %d" %(geneStartPix, geneYLocation+ind*self.EACH_GENE_HEIGHT, geneEndPix+1, (geneYLocation + ind*self.EACH_GENE_HEIGHT))
                            TITLE = "Strain: %s, marker (%s) \n Position  %2.3f Mb." % (bxdlist[j], self.genotype[0][i].name, float(txStart))
                            HREF = ''
                            gifmap.areas.append(HT.Area(shape='rect',coords=COORDS,href=HREF, title=TITLE))

                            # if there are no more markers in a chromosome, the plotRight value calculated above will be before the plotWidth
                            # resulting in some empty space on the right side of the plot area. This draws an "unknown" bar from plotRight to the edge.
                            if (plotRight < (xLeftOffset + plotWidth - 3)) and (lastGene == 0):
                                drawEnd = xLeftOffset + plotWidth - 6
                                mylineColor = self.HAPLOTYPE_RECOMBINATION
                                canvas.drawLine(plotRight, geneYLocation+7+2*ind*self.EACH_GENE_HEIGHT*zoom, drawEnd, geneYLocation+7+2*ind*self.EACH_GENE_HEIGHT*zoom, color = mylineColor, width=zoom*(self.EACH_GENE_HEIGHT+2))


                    if lastGene == 0:
                        canvas.drawString("%s" % (self.genotype[0][i].name), geneStartPix , geneYLocation+17+2*maxind*self.EACH_GENE_HEIGHT*zoom, font=pid.Font(ttf="verdana", size=12, bold=0), color=pid.black, angle=-90)

                    oldgeneEndPix = geneEndPix;
                    oldgeno = self.genotype[0][i].genotype
                    firstGene = 0
                else:
                    lastGene = 0

        for j,_geno in enumerate (self.genotype[0][1].genotype):

            plotbxd=0
            for item in smd:
                if item.name == bxdlist[j]:
                    plotbxd=1

            if (plotbxd == 1):

                ind = 0
                counter = 0
                expr = 0
                for item in smd:
                    counter = counter + 1
                    if item.name == bxdlist[j]:
                        ind = counter
                        expr = item.value

                # Place where font is hardcoded
                canvas.drawString("%s" % (bxdlist[j]), (xLeftOffset + plotWidth + 10) , geneYLocation+8+2*ind*self.EACH_GENE_HEIGHT*zoom, font=pid.Font(ttf="verdana", size=12, bold=0), color=pid.black)
                canvas.drawString("%2.2f" % (expr), (xLeftOffset + plotWidth + 60) , geneYLocation+8+2*ind*self.EACH_GENE_HEIGHT*zoom, font=pid.Font(ttf="verdana", size=12, bold=0), color=pid.black)

        fpText.close()

## END HaplotypeAnalyst

    def drawClickBand(self, canvas, gifmap, plotXScale, offset= (40, 120, 80, 10), zoom = 1, startMb = None, endMb = None):
        if self.plotScale != 'physic' or self.selectedChr == -1:
            return

        xLeftOffset, xRightOffset, yTopOffset, yBottomOffset = offset
        plotWidth = canvas.size[0] - xLeftOffset - xRightOffset
        plotHeight = canvas.size[1] - yTopOffset - yBottomOffset
        yZero = canvas.size[1] - yBottomOffset
        fontZoom = zoom
        if zoom == 2:
            fontZoom = 1.5

        # only draw this many clickable regions (if you set it higher, you get more precision in clicking,
        # but it makes the HTML huge, and takes forever to render the page in the first place)
        # Draw the bands that you can click on to go to UCSC / Ensembl
        MAX_CLICKABLE_REGION_DIVISIONS = 100
        clickableRegionLabelFont=pid.Font(ttf="verdana", size=9, bold=0)
        pixelStep = max(5, int(float(plotWidth)/MAX_CLICKABLE_REGION_DIVISIONS))
        # pixelStep: every N pixels, we make a new clickable area for the user to go to that area of the genome.

        numBasesCurrentlyOnScreen = self.kONE_MILLION*abs(startMb - endMb) # Number of bases on screen now
        flankingWidthInBases = int ( min( (float(numBasesCurrentlyOnScreen) / 2.0), (5*self.kONE_MILLION) ) )
        webqtlZoomWidth = numBasesCurrentlyOnScreen / 16.0
        # Flanking width should be such that we either zoom in to a 10 million base region, or we show the clicked region at the same scale as we are currently seeing.

        currentChromosome = self.genotype[0].name
        i = 0
        
        paddingTop = yTopOffset
        ucscPaddingTop = paddingTop + self.WEBQTL_BAND_HEIGHT + self.BAND_SPACING
        ensemblPaddingTop = ucscPaddingTop + self.UCSC_BAND_HEIGHT + self.BAND_SPACING
        
        if zoom == 1:
            for pixel in range(xLeftOffset, xLeftOffset + plotWidth, pixelStep):
    
                calBase = self.kONE_MILLION*(startMb + (endMb-startMb)*(pixel-xLeftOffset-0.0)/plotWidth)
    
                xBrowse1 = pixel
                xBrowse2 = min(xLeftOffset + plotWidth, (pixel + pixelStep - 1))
    
                WEBQTL_COORDS = "%d, %d, %d, %d" % (xBrowse1, paddingTop, xBrowse2, (paddingTop+self.WEBQTL_BAND_HEIGHT))
                bandWidth = xBrowse2 - xBrowse1
                WEBQTL_HREF = "javascript:centerIntervalMapOnRange2('%s', %f, %f, document.changeViewForm)" % (currentChromosome, max(0, (calBase-webqtlZoomWidth))/1000000.0, (calBase+webqtlZoomWidth)/1000000.0)
    
                WEBQTL_TITLE = "Click to view this section of the genome in WebQTL"
                gifmap.areas.append(HT.Area(shape='rect',coords=WEBQTL_COORDS,href=WEBQTL_HREF, title=WEBQTL_TITLE))
                canvas.drawRect(xBrowse1, paddingTop, xBrowse2, (paddingTop + self.WEBQTL_BAND_HEIGHT), edgeColor=self.CLICKABLE_WEBQTL_REGION_COLOR, fillColor=self.CLICKABLE_WEBQTL_REGION_COLOR)
                canvas.drawLine(xBrowse1, paddingTop, xBrowse1, (paddingTop + self.WEBQTL_BAND_HEIGHT), color=self.CLICKABLE_WEBQTL_REGION_OUTLINE_COLOR)
    
                UCSC_COORDS = "%d, %d, %d, %d" %(xBrowse1, ucscPaddingTop, xBrowse2, (ucscPaddingTop+self.UCSC_BAND_HEIGHT))
                if self.species == "mouse":
                    UCSC_HREF = "http://genome.ucsc.edu/cgi-bin/hgTracks?db=%s&position=chr%s:%d-%d&hgt.customText=%s/snp/chr%s" % (self._ucscDb, currentChromosome, max(0, calBase-flankingWidthInBases), calBase+flankingWidthInBases, webqtlConfig.PORTADDR, currentChromosome)
                else:
                    UCSC_HREF = "http://genome.ucsc.edu/cgi-bin/hgTracks?db=%s&position=chr%s:%d-%d" % (self._ucscDb, currentChromosome, max(0, calBase-flankingWidthInBases), calBase+flankingWidthInBases)
                UCSC_TITLE = "Click to view this section of the genome in the UCSC Genome Browser"
                gifmap.areas.append(HT.Area(shape='rect',coords=UCSC_COORDS,href=UCSC_HREF, title=UCSC_TITLE))
                canvas.drawRect(xBrowse1, ucscPaddingTop, xBrowse2, (ucscPaddingTop+self.UCSC_BAND_HEIGHT), edgeColor=self.CLICKABLE_UCSC_REGION_COLOR, fillColor=self.CLICKABLE_UCSC_REGION_COLOR)
                canvas.drawLine(xBrowse1, ucscPaddingTop, xBrowse1, (ucscPaddingTop+self.UCSC_BAND_HEIGHT), color=self.CLICKABLE_UCSC_REGION_OUTLINE_COLOR)
    
                ENSEMBL_COORDS = "%d, %d, %d, %d" %(xBrowse1, ensemblPaddingTop, xBrowse2, (ensemblPaddingTop+self.ENSEMBL_BAND_HEIGHT))
                if self.species == "mouse":
                    ENSEMBL_HREF = "http://www.ensembl.org/Mus_musculus/contigview?highlight=&chr=%s&vc_start=%d&vc_end=%d&x=35&y=12" % (currentChromosome, max(0, calBase-flankingWidthInBases), calBase+flankingWidthInBases)
                else:
                    ENSEMBL_HREF = "http://www.ensembl.org/Rattus_norvegicus/contigview?chr=%s&start=%d&end=%d" % (currentChromosome, max(0, calBase-flankingWidthInBases), calBase+flankingWidthInBases)
                ENSEMBL_TITLE = "Click to view this section of the genome in the Ensembl Genome Browser"
                gifmap.areas.append(HT.Area(shape='rect',coords=ENSEMBL_COORDS,href=ENSEMBL_HREF, title=ENSEMBL_TITLE))
                canvas.drawRect(xBrowse1, ensemblPaddingTop, xBrowse2, (ensemblPaddingTop+self.ENSEMBL_BAND_HEIGHT), edgeColor=self.CLICKABLE_ENSEMBL_REGION_COLOR, fillColor=self.CLICKABLE_ENSEMBL_REGION_COLOR)
                canvas.drawLine(xBrowse1, ensemblPaddingTop, xBrowse1, (ensemblPaddingTop+self.ENSEMBL_BAND_HEIGHT), color=self.CLICKABLE_ENSEMBL_REGION_OUTLINE_COLOR)
            # end for

            canvas.drawString("Click to view the corresponding section of the genome in an 8x expanded WebQTL map", (xLeftOffset + 10), paddingTop + self.WEBQTL_BAND_HEIGHT/2, font=clickableRegionLabelFont, color=self.CLICKABLE_WEBQTL_TEXT_COLOR)
            canvas.drawString("Click to view the corresponding section of the genome in the UCSC Genome Browser", (xLeftOffset + 10), ucscPaddingTop + self.UCSC_BAND_HEIGHT/2, font=clickableRegionLabelFont, color=self.CLICKABLE_UCSC_TEXT_COLOR)
            canvas.drawString("Click to view the corresponding section of the genome in the Ensembl Genome Browser", (xLeftOffset+10), ensemblPaddingTop + self.ENSEMBL_BAND_HEIGHT/2, font=clickableRegionLabelFont, color=self.CLICKABLE_ENSEMBL_TEXT_COLOR)

            #draw the gray text
            chrFont = pid.Font(ttf="verdana", size=26*zoom, bold=1)
            traitFont = pid.Font(ttf="verdana", size=14, bold=0)
            chrX = xLeftOffset + plotWidth - 2 - canvas.stringWidth("Chr %s" % currentChromosome, font=chrFont)
            canvas.drawString("Chr %s" % currentChromosome, chrX, ensemblPaddingTop-5, font=chrFont, color=pid.gray)
            traitX = chrX - 28 - canvas.stringWidth("database", font=traitFont)
            # end of drawBrowserClickableRegions
        else:
            #draw the gray text
            chrFont = pid.Font(ttf="verdana", size=26*zoom, bold=1)
            traitFont = pid.Font(ttf="verdana", size=14, bold=0)
            chrX = xLeftOffset + (plotWidth - canvas.stringWidth("Chr %s" % currentChromosome, font=chrFont))/2
            canvas.drawString("Chr %s" % currentChromosome, chrX, 32, font=chrFont, color=pid.gray)
            traitX = chrX - 28 - canvas.stringWidth("database", font=traitFont)
            # end of drawBrowserClickableRegions
        pass

    def drawXAxis(self, canvas, drawAreaHeight, gifmap, plotXScale, showLocusForm, offset= (40, 120, 80, 10), zoom = 1, startMb = None, endMb = None):
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
        MBLabelFont = pid.Font(ttf="verdana", size=15*zoom, bold=0)
        xMajorTickHeight = 10 * zoom # How high the tick extends below the axis
        xMinorTickHeight = 5*zoom
        xAxisTickMarkColor = pid.black
        xAxisLabelColor = pid.black
        fontHeight = 12*fontZoom # How tall the font that we're using is
        spacingFromLabelToAxis = 5
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
                    for tickdists in range(distScale, int(ceil(distLen)), distScale):
                        canvas.drawLine(startPosX + tickdists*plotXScale, yZero, startPosX + tickdists*plotXScale, yZero + 7, color=pid.black, width=1*zoom)
                        canvas.drawString(str(tickdists), startPosX+tickdists*plotXScale, yZero + 10*zoom, color=pid.black, font=MBLabelFont, angle=270)
                    startPosX +=  (self.ChrLengthDistList[i]+self.GraphInterval)*plotXScale

            megabaseLabelFont = pid.Font(ttf="verdana", size=18*zoom*1.5, bold=0)
            canvas.drawString("Megabases", xLeftOffset + (plotWidth - canvas.stringWidth("Megabases", font=megabaseLabelFont))/2,
                    strYLoc + canvas.fontHeight(MBLabelFont)+ 10*(zoom%2) + 10, font=megabaseLabelFont, color=pid.black)
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


    def drawQTL(self, canvas, drawAreaHeight, gifmap, plotXScale, offset= (40, 120, 80, 10), zoom = 1, startMb = None, endMb = None):
        xLeftOffset, xRightOffset, yTopOffset, yBottomOffset = offset
        plotWidth = canvas.size[0] - xLeftOffset - xRightOffset
        plotHeight = canvas.size[1] - yTopOffset - yBottomOffset
        fontZoom = zoom
        if zoom == 2:
            fontZoom = 1.5

        INTERCROSS = (self.genotype.type=="intercross")

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
            if "lrs_value" in self.qtlresults[0]:
                LRSMax = max([result['lrs_value'] for result in self.qtlresults])
                #LRSMax = max(map(max, self.qtlresults)).lrs_value
            else: 
                LRSMax = max([result['lod_score'] for result in self.qtlresults])
                #LRSMax = max(map(max, self.qtlresults)).lod_score
            #genotype trait will give infinite LRS
            LRSMax = min(LRSMax, webqtlConfig.MAXLRS)
            if self.permChecked and not self.multipleInterval:
                self.significance = min(self.significance, webqtlConfig.MAXLRS)
                self.suggestive = min(self.suggestive, webqtlConfig.MAXLRS)
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
        LRSScaleFont=pid.Font(ttf="verdana", size=16*zoom, bold=0)
        LRSLODFont=pid.Font(ttf="verdana", size=18*zoom*1.5, bold=0)
        yZero = yTopOffset + plotHeight

        canvas.drawString(self.LRS_LOD, xLeftOffset - canvas.stringWidth("999.99", font=LRSScaleFont) - 15*(zoom-1), \
                                          yZero - 150 - 300*(zoom - 1), font=LRSLODFont, color=pid.black, angle=90)

        for item in LRSAxisList:
            if LRSMax == 0.0:
                LRSMax = 0.000001
            yLRS = yZero - (item*lodm/LRSMax) * LRSHeightThresh
            canvas.drawLine(xLeftOffset, yLRS, xLeftOffset - 4, yLRS, color=self.LRS_COLOR, width=1*zoom)
            scaleStr = "%2.1f" % item
            #Draw the LRS/LOD Y axis label
            canvas.drawString(scaleStr, xLeftOffset-4-canvas.stringWidth(scaleStr, font=LRSScaleFont)-5, yLRS+3, font=LRSScaleFont, color=self.LRS_COLOR)


        #"Significant" and "Suggestive" Drawing Routine
        # ======= Draw the thick lines for "Significant" and "Suggestive" =====  (crowell: I tried to make the SNPs draw over these lines, but piddle wouldn't have it...)
        if self.permChecked and not self.multipleInterval:
            significantY = yZero - self.significance*LRSHeightThresh/LRSMax
            suggestiveY = yZero - self.suggestive*LRSHeightThresh/LRSMax
            startPosX = xLeftOffset
            for i, _chr in enumerate(self.genotype):
                rightEdge = int(startPosX + self.ChrLengthDistList[i]*plotXScale - self.SUGGESTIVE_WIDTH/1.5)
                canvas.drawLine(startPosX+self.SUGGESTIVE_WIDTH/1.5, suggestiveY, rightEdge, suggestiveY, color=self.SUGGESTIVE_COLOR,
                        width=self.SUGGESTIVE_WIDTH*zoom, clipX=(xLeftOffset, xLeftOffset + plotWidth-2))
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
            #additiveMax = max(map(lambda X : abs(X.additive), self.qtlresults[0]))
            #if INTERCROSS:
            #    dominanceMax = max(map(lambda X : abs(X.dominance), self.qtlresults[0]))
            #else:
            #    dominanceMax = -1
            lrsEdgeWidth = 2
            
        if zoom == 2:
            lrsEdgeWidth = 2 * lrsEdgeWidth

        LRSCoordXY = []
        AdditiveCoordXY = []
        DominanceCoordXY = []

        previous_chr = 1
        previous_chr_as_int = 0
        oldStartPosX = 0
        startPosX = xLeftOffset
        for i, qtlresult in enumerate(self.qtlresults):
            m = 0
            #startPosX = xLeftOffset
            thisLRSColor = self.colorCollection[0]

            if qtlresult['chr'] != previous_chr and self.selectedChr == -1:
                previous_chr = qtlresult['chr']
                previous_chr_as_int += 1

                print("ChrLengthDistList:", self.ChrLengthDistList)

                newStartPosX = (self.ChrLengthDistList[previous_chr_as_int - 1]+self.GraphInterval)*plotXScale
                if newStartPosX != oldStartPosX:
                    startPosX += newStartPosX
                    oldStartPosX = newStartPosX

            #startPosX += (self.ChrLengthDistList[j]+self.GraphInterval)*plotXScale

            #for j, _chr in enumerate(self.genotype):
            if self.selectedChr == -1 or qtlresult['chr'] == self.selectedChr:
                #LRSCoordXY = []
                #AdditiveCoordXY = []
                #DominanceCoordXY = []
                #for k, _locus in enumerate(_chr):
                if 1 == 1:
                    if self.plotScale == 'physic':
                        #Xc = startPosX + (_locus.Mb-startMb)*plotXScale
                        Xc = startPosX + (qtlresult['Mb']-startMb)*plotXScale
                    else:
                        #Xc = startPosX + (_locus.cM-_chr[0].cM)*plotXScale
                        Xc = startPosX + (qtlresult['cM']-qtlresult[0]['cM'])*plotXScale

                    # updated by NL 06-18-2011:
                    # fix the over limit LRS graph issue since genotype trait may give infinite LRS;
                    # for any lrs is over than 460(LRS max in this system), it will be reset to 460
                    if qtlresult['lrs_value'] > 460 or qtlresult['lrs_value']=='inf':
                    #if self.qtlresults[j]['lrs_value'] > 460 or self.qtlresults[j]['lrs_value']=='inf':
                        Yc = yZero - webqtlConfig.MAXLRS*LRSHeightThresh/LRSMax
                    else:
                        Yc = yZero - qtlresult['lrs_value']*LRSHeightThresh/LRSMax

                    LRSCoordXY.append((Xc, Yc))
                    #if not self.multipleInterval and self.additiveChecked:
                    #    if additiveMax == 0.0:
                    #        additiveMax = 0.000001
                    #    Yc = yZero - qtlresult[m].additive*AdditiveHeightThresh/additiveMax
                    #    AdditiveCoordXY.append((Xc, Yc))
                    #if not self.multipleInterval and INTERCROSS and self.additiveChecked:
                    #    Yc = yZero - qtlresult[m].dominance*DominanceHeightThresh/dominanceMax
                    #    DominanceCoordXY.append((Xc, Yc))
                    m += 1
                #canvas.drawPolygon(LRSCoordXY,edgeColor=thisLRSColor,closed=0, edgeWidth=lrsEdgeWidth, clipX=(xLeftOffset, xLeftOffset + plotWidth))

                lineWidth = 1
                if not self.multipleInterval and self.additiveChecked:
                    plusColor = self.ADDITIVE_COLOR_POSITIVE
                    minusColor = self.ADDITIVE_COLOR_NEGATIVE
                    for k, aPoint in enumerate(AdditiveCoordXY):
                        if k > 0:
                            Xc0, Yc0 = AdditiveCoordXY[k-1]
                            Xc, Yc = aPoint
                            if (Yc0-yZero)*(Yc-yZero) < 0:
                                if Xc == Xc0: #genotype , locus distance is 0
                                    Xcm = Xc
                                else:
                                    Xcm = (yZero-Yc0)/((Yc-Yc0)/(Xc-Xc0)) +Xc0
                                if Yc0 < yZero:
                                    canvas.drawLine(Xc0, Yc0, Xcm, yZero, color=plusColor, width=lineWidth, clipX=(xLeftOffset, xLeftOffset + plotWidth))
                                    canvas.drawLine(Xcm, yZero, Xc, yZero-(Yc-yZero), color=minusColor, width=lineWidth, clipX=(xLeftOffset, xLeftOffset + plotWidth))
                                else:
                                    canvas.drawLine(Xc0, yZero - (Yc0-yZero), Xcm, yZero, color=minusColor, width=lineWidth, clipX=(xLeftOffset, xLeftOffset + plotWidth))
                                    canvas.drawLine(Xcm, yZero, Xc, Yc, color=plusColor, width=lineWidth, clipX=(xLeftOffset, xLeftOffset + plotWidth))
                            elif (Yc0-yZero)*(Yc-yZero) > 0:
                                if Yc < yZero:
                                    canvas.drawLine(Xc0, Yc0, Xc, Yc, color=plusColor, width=lineWidth, clipX=(xLeftOffset, xLeftOffset + plotWidth))
                                else:
                                    canvas.drawLine(Xc0, yZero - (Yc0-yZero), Xc, yZero - (Yc-yZero), color=minusColor, width=lineWidth, clipX=(xLeftOffset, xLeftOffset + plotWidth))
                            else:
                                minYc = min(Yc-yZero, Yc0-yZero)
                                if minYc < 0:
                                    canvas.drawLine(Xc0, Yc0, Xc, Yc, color=plusColor, width=lineWidth, clipX=(xLeftOffset, xLeftOffset + plotWidth))
                                else:
                                    canvas.drawLine(Xc0, yZero - (Yc0-yZero), Xc, yZero - (Yc-yZero), color=minusColor, width=lineWidth, clipX=(xLeftOffset, xLeftOffset + plotWidth))
                if not self.multipleInterval and INTERCROSS and self.dominanceChecked:
                    plusColor = self.DOMINANCE_COLOR_POSITIVE
                    minusColor = self.DOMINANCE_COLOR_NEGATIVE
                    for k, aPoint in enumerate(DominanceCoordXY):
                        if k > 0:
                            Xc0, Yc0 = DominanceCoordXY[k-1]
                            Xc, Yc = aPoint
                            if (Yc0-yZero)*(Yc-yZero) < 0:
                                if Xc == Xc0: #genotype , locus distance is 0
                                    Xcm = Xc
                                else:
                                    Xcm = (yZero-Yc0)/((Yc-Yc0)/(Xc-Xc0)) +Xc0
                                if Yc0 < yZero:
                                    canvas.drawLine(Xc0, Yc0, Xcm, yZero, color=plusColor, width=lineWidth, clipX=(xLeftOffset, xLeftOffset + plotWidth))
                                    canvas.drawLine(Xcm, yZero, Xc, yZero-(Yc-yZero), color=minusColor, width=lineWidth, clipX=(xLeftOffset, xLeftOffset + plotWidth))
                                else:
                                    canvas.drawLine(Xc0, yZero - (Yc0-yZero), Xcm, yZero, color=minusColor, width=lineWidth, clipX=(xLeftOffset, xLeftOffset + plotWidth))
                                    canvas.drawLine(Xcm, yZero, Xc, Yc, color=plusColor, width=lineWidth, clipX=(xLeftOffset, xLeftOffset + plotWidth))
                            elif (Yc0-yZero)*(Yc-yZero) > 0:
                                if Yc < yZero:
                                    canvas.drawLine(Xc0, Yc0, Xc, Yc, color=plusColor, width=lineWidth, clipX=(xLeftOffset, xLeftOffset + plotWidth))
                                else:
                                    canvas.drawLine(Xc0, yZero - (Yc0-yZero), Xc, yZero - (Yc-yZero), color=minusColor, width=lineWidth, clipX=(xLeftOffset, xLeftOffset + plotWidth))
                            else:
                                minYc = min(Yc-yZero, Yc0-yZero)
                                if minYc < 0:
                                    canvas.drawLine(Xc0, Yc0, Xc, Yc, color=plusColor, width=lineWidth, clipX=(xLeftOffset, xLeftOffset + plotWidth))
                                else:
                                    canvas.drawLine(Xc0, yZero - (Yc0-yZero), Xc, yZero - (Yc-yZero), color=minusColor, width=lineWidth, clipX=(xLeftOffset, xLeftOffset + plotWidth))
                

        canvas.drawPolygon(LRSCoordXY,edgeColor=thisLRSColor,closed=0, edgeWidth=lrsEdgeWidth, clipX=(xLeftOffset, xLeftOffset + plotWidth))

        ###draw additive scale
        if not self.multipleInterval and self.additiveChecked:
            additiveScaleFont=pid.Font(ttf="verdana",size=16*zoom,bold=0)
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

        canvas.drawLine(xLeftOffset, yZero, xLeftOffset, yTopOffset + 30*(zoom - 1), color=self.LRS_COLOR, width=1*zoom)  #the blue line running up the y axis


    def drawGraphBackground(self, canvas, gifmap, offset= (80, 120, 80, 50), zoom = 1, startMb = None, endMb = None):
        ##conditions
        ##multiple Chromosome view
        ##single Chromosome Physical
        ##single Chromosome Genetic
        xLeftOffset, xRightOffset, yTopOffset, yBottomOffset = offset
        plotWidth = canvas.size[0] - xLeftOffset - xRightOffset
        plotHeight = canvas.size[1] - yTopOffset - yBottomOffset
        yBottom = yTopOffset+plotHeight
        fontZoom = zoom
        if zoom == 2:
            fontZoom = 1.5
            yTopOffset += 30
        
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
                        yBottom, edgeColor=theBackColor, fillColor=theBackColor)

            drawRegionDistance = self.ChrLengthDistList[self.selectedChr]
            self.ChrLengthDistList = [drawRegionDistance]
            if self.plotScale == 'physic':
                plotXScale = plotWidth / (endMb-startMb)
            else:
                plotXScale = plotWidth / drawRegionDistance

        else:   #multiple chromosome view
            plotXScale = plotWidth / ((len(self.genotype)-1)*self.GraphInterval + drawRegionDistance)

            startPosX = xLeftOffset
            if fontZoom == 1.5:
                chrFontZoom = 2
            else:
                chrFontZoom = 1
            chrLabelFont=pid.Font(ttf="verdana",size=24*chrFontZoom,bold=0)

            for i, _chr in enumerate(self.genotype):
                if (i % 2 == 0):
                    theBackColor = self.GRAPH_BACK_DARK_COLOR
                else:
                    theBackColor = self.GRAPH_BACK_LIGHT_COLOR

                #draw the shaded boxes and the sig/sug thick lines
                canvas.drawRect(startPosX, yTopOffset, startPosX + self.ChrLengthDistList[i]*plotXScale, \
                                yBottom, edgeColor=pid.gainsboro,fillColor=theBackColor)

                chrNameWidth = canvas.stringWidth(_chr.name, font=chrLabelFont)
                chrStartPix = startPosX + (self.ChrLengthDistList[i]*plotXScale -chrNameWidth)/2
                chrEndPix = startPosX + (self.ChrLengthDistList[i]*plotXScale +chrNameWidth)/2

                canvas.drawString(_chr.name, chrStartPix, yTopOffset + 20 ,font = chrLabelFont,color=pid.black)
                COORDS = "%d,%d,%d,%d" %(chrStartPix, yTopOffset, chrEndPix,yTopOffset +20)

                #add by NL 09-03-2010
                HREF = "javascript:chrView(%d,%s);" % (i,self.ChrLengthMbList)
                #HREF = "javascript:changeView(%d,%s);" % (i,self.ChrLengthMbList)
                Areas = HT.Area(shape='rect',coords=COORDS,href=HREF)
                gifmap.areas.append(Areas)
                startPosX +=  (self.ChrLengthDistList[i]+self.GraphInterval)*plotXScale

        return plotXScale

    def calculateAllResult(self, fd):

        weightedRegression = fd.formdata.getvalue('applyVarianceSE')

        self.genotype = self.genotype.addinterval()
        resultSlice = []
        controlGeno = []

        if self.multipleInterval:
            self.suggestive = 0
            self.significance = 0
            if self.selectedChr > -1:
                self.genotype.chromosome = [self.genotype[self.selectedChr]]
        else:
            #single interval mapping
            try:
                self.suggestive = float(fd.formdata.getvalue('permSuggestive'))
                self.significance = float(fd.formdata.getvalue('permSignificance'))
            except:
                self.suggestive = None
                self.significance = None

            _strains, _vals, _vars = self.traitList[0].exportInformative(weightedRegression)

            if webqtlUtil.ListNotNull(_vars):
                pass
            else:
                weightedRegression = 0
                _strains, _vals, _vars = self.traitList[0].exportInformative()

            ##locate genotype of control Locus
            if self.controlLocus:
                controlGeno2 = []
                _FIND = 0
                for _chr in self.genotype:
                    for _locus in _chr:
                        if _locus.name == self.controlLocus:
                            controlGeno2 = _locus.genotype
                            _FIND = 1
                            break
                    if _FIND:
                        break
                if controlGeno2:
                    _prgy = list(self.genotype.prgy)
                    for _strain in _strains:
                        _idx = _prgy.index(_strain)
                        controlGeno.append(controlGeno2[_idx])
                else:
                    return "The control marker you selected is not in the genofile."

            if weightedRegression:
                self.LRSArray = self.genotype.permutation(strains = _strains, trait = _vals,
                        variance = _vars, nperm=self.nperm)
            else:
                self.LRSArray = self.genotype.permutation(strains = _strains, trait = _vals,
                        nperm=self.nperm)

            if self.significance and self.suggestive:
                pass
            else:
                if self.nperm < 100:
                    self.suggestive = 0
                    self.significance = 0
                else:
                    self.suggestive = self.LRSArray[int(self.nperm*0.37-1)]
                    self.significance = self.LRSArray[int(self.nperm*0.95-1)]

            #calculating bootstrap
            #from now on, genotype could only contain a single chromosome
            #permutation need to be performed genome wide, this is not the case for bootstrap

            #due to the design of qtlreaper, composite regression need to be performed genome wide
            if not self.controlLocus and self.selectedChr > -1:
                self.genotype.chromosome = [self.genotype[self.selectedChr]]
            elif self.selectedChr > -1: #self.controlLocus and self.selectedChr > -1
                lociPerChr = map(len, self.genotype)
                resultSlice = reduce(lambda X, Y: X+Y, lociPerChr[:self.selectedChr], 0)
                resultSlice = [resultSlice,resultSlice+lociPerChr[self.selectedChr]]
            else:
                pass

        #calculate QTL for each trait
        self.qtlresults = []

        for thisTrait in self.traitList:
            _strains, _vals, _vars = thisTrait.exportInformative(weightedRegression)
            if self.controlLocus:
                if weightedRegression:
                    qtlresult = self.genotype.regression(strains = _strains, trait = _vals,
                                    variance = _vars, control = self.controlLocus)
                else:
                    qtlresult = self.genotype.regression(strains = _strains, trait = _vals,
                            control = self.controlLocus)
                if resultSlice:
                    qtlresult = qtlresult[resultSlice[0]:resultSlice[1]]
            else:
                if weightedRegression:
                    qtlresult = self.genotype.regression(strains = _strains, trait = _vals,
                                    variance = _vars)
                else:
                    qtlresult = self.genotype.regression(strains = _strains, trait = _vals)

            self.qtlresults.append(qtlresult)

        if not self.multipleInterval:
            if self.controlLocus and self.selectedChr > -1:
                self.genotype.chromosome = [self.genotype[self.selectedChr]]

            if self.bootChecked:
                if controlGeno:
                    self.bootResult = self.genotype.bootstrap(strains = _strains, trait = _vals,
                            control = controlGeno, nboot=fd.nboot)
                elif weightedRegression:
                    self.bootResult = self.genotype.bootstrap(strains = _strains, trait = _vals,
                            variance = _vars, nboot=fd.nboot)
                else:
                    self.bootResult = self.genotype.bootstrap(strains = _strains, trait = _vals,
                            nboot=fd.nboot)
            else:
                self.bootResult = []

    def calculatePValue (self, query_LRS, permutation_LRS_array):
        query_index = len(permutation_LRS_array)
        for i, one_permutation_LRS in enumerate(permutation_LRS_array):
            if one_permutation_LRS >= query_LRS:
                query_index = i
                break
        try:
            P_value = float(len(permutation_LRS_array) - query_index) / len(permutation_LRS_array)
        except:
            P_value = ''
        return P_value

    def helpButton(self, anchor):
        return HT.Href(self.HELP_PAGE_REF + '#%s' % anchor, self.qmarkImg, target=self.HELP_WINDOW_NAME)


    def traitRemapTD(self, cursor, fd):
        chrList = HT.Select(name="chromosomes", data=self.ChrList, selected=[self.selectedChr],
                onChange="chrLength(this.form.chromosomes.value, this.form.scale.value, this.form, self.ChrLengthMbList);")

        physicOnly = HT.Span(' *', Class="cr")

        showSNPCheck   = HT.Input(type='checkbox', Class='checkbox', name='showSNP', value='ON', checked=self.SNPChecked)
        showSNPText    = HT.Span('SNP Track ', self.helpButton("snpSeismograph"), Class="fs12 fwn")

        showGenesCheck = HT.Input(type='checkbox', Class='checkbox', name='showGenes', value='ON', checked=self.geneChecked)
        showGenesText  = HT.Span('Gene Track', Class="fs12 fwn")

        showIntervalAnalystCheck = HT.Input(type='checkbox', Class='checkbox', name='intervalAnalystCheck', value='ON', checked=self.intervalAnalystChecked)
        showIntervalAnalystText = HT.Span('Interval Analyst', Class="fs12 fwn")
## BEGIN HaplotypeAnalyst

        showHaplotypeAnalystCheck = HT.Input(type='checkbox', Class='checkbox', name='haplotypeAnalystCheck', value='ON', checked=self.haplotypeAnalystChecked)
        showHaplotypeAnalystText = HT.Span('Haplotype Analyst', Class="fs12 fwn")
## END HaplotypeAnalyst

        leftBox = HT.Input(type="text", name="startMb", size=10)
        rightBox = HT.Input(type="text", name="endMb", size=10)
        if self.selectedChr > -1 and self.plotScale=='physic':
            leftBox.value = self.startMb
            rightBox.value = self.endMb

        scaleBox = HT.Select(name="scale", onChange="chrLength(this.form.chromosomes.value, this.form.scale.value, this.form, self.ChrLengthMbList);")
        scaleBox.append(("Genetic", "morgan"))
        if fd.genotype.Mbmap:
            scaleBox.append(("Physical", "physic"))
        scaleBox.selected.append(self.plotScale)

        permBox = HT.Input(type="checkbox", name="permCheck", value='ON', checked=self.permChecked, Class="checkbox")
        permText = HT.Span("Permutation Test ", self.helpButton("Permutation"), Class="fs12 fwn")
        bootBox = HT.Input(type="checkbox", name="bootCheck", value='ON', checked=self.bootChecked, Class="checkbox")
        bootText = HT.Span("Bootstrap Test ", self.helpButton("bootstrap"), Class="fs12 fwn")
        additiveBox = HT.Input(type="checkbox", name="additiveCheck", value='ON', checked=self.additiveChecked, Class="checkbox")
        additiveText = HT.Span("Allele Effects ", self.helpButton("additive"), Class="fs12 fwn")
        dominanceBox = HT.Input(type="checkbox", name="dominanceCheck", value='ON', checked=self.dominanceChecked, Class="checkbox")
        dominanceText = HT.Span("Dominance Effects ", self.helpButton("Dominance"), Class="fs12 fwn")

        lrsRadio = HT.Input(type="radio", name="LRSCheck", value='LRS', checked = (self.LRS_LOD == "LRS"))
        lodRadio = HT.Input(type="radio", name="LRSCheck", value='LOD', checked = (self.LRS_LOD != "LRS"))
        lrsMaxBox = HT.Input(type="text", name="lrsMax", value=self.lrsMax, size=3)
        widthBox = HT.Input(type="text", name="graphWidth", size=5, value=str(self.graphWidth))
        legendBox = HT.Input(type="checkbox", name="viewLegend", value='ON', checked=self.legendChecked, Class="checkbox")
        legendText = HT.Span("Legend", Class="fs12 fwn")

        draw2XBox = HT.Input(type="checkbox", name="draw2X", value='ON', Class="checkbox")
        draw2XText = HT.Span("2X Plot", Class="fs12 fwn")

        regraphButton = HT.Input(type="button", Class="button", onClick="javascript:databaseFunc(this.form,'showIntMap');", value="Remap")
        controlsForm = HT.Form(cgi= os.path.join(webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE), enctype="multipart/form-data", name="changeViewForm", submit=HT.Input(type='hidden'))
        controlsTable = HT.TableLite(border=0)
        innerControlsTable = HT.TableLite(border=0)
        if self.selectedChr == -1:
            minimumGraphWidth = self.MULT_GRAPH_MIN_WIDTH
        else:
            minimumGraphWidth = self.GRAPH_MIN_WIDTH
        innerControlsTable.append(
                HT.TR(HT.TD("Chr: ", Class="fs12 fwb ffl"),HT.TD(chrList, scaleBox, regraphButton)),
                HT.TR(HT.TD("View: ", Class="fs12 fwb ffl"),HT.TD(leftBox, " to ", rightBox, "Mb", physicOnly, NOWRAP="on")),
                HT.TR(HT.TD("Units: ", Class="fs12 fwb ffl"), HT.TD(lrsRadio, "LRS ", lodRadio, "LOD ", self.helpButton("LOD"))),
                HT.TR(HT.TD(" ", Class="fs12 fwb ffl"), HT.TD(lrsMaxBox, "units on Y-axis (0 for default)", Class="fs11 fwn")),
                HT.TR(HT.TD("Width: ", Class="fs12 fwb ffl"), HT.TD(widthBox, "pixels (minimum=%d)" % minimumGraphWidth, Class="fs11 fwn "))
        )
        #whether SNP
        # comment this, because this will make caculation very slow.
        #cursor.execute("Select Species.Id from SnpAll, Species where SnpAll.SpeciesId = Species.Id and Species.Name = %s limit 1", self.species)
        #SNPorNot = cursor.fetchall()
        SNPorNot = True
        #Whether Gene
        cursor.execute("Select Species.Id from GeneList, Species where GeneList.SpeciesId = Species.Id and Species.Name = %s limit 1", self.species)
        GeneorNot = cursor.fetchall()

        if self.multipleInterval:
            optionPanel = HT.TD(valign="top", NOWRAP="on")
        else:
            optionPanel = HT.TD(permBox, permText, HT.BR(), bootBox, bootText, HT.BR(), additiveBox, additiveText, HT.BR(), valign="top", NOWRAP="on")
		#whether dominance
        if self.genotype.type == 'intercross':
            optionPanel.append(dominanceBox, dominanceText, HT.BR())
        if SNPorNot:
            optionPanel.append(showSNPCheck, showSNPText, physicOnly, HT.BR())
        if GeneorNot:
            optionPanel.append(showGenesCheck, showGenesText, physicOnly, HT.BR(),
                    showIntervalAnalystCheck, showIntervalAnalystText, physicOnly, HT.BR())
## BEGIN HaplotypeAnalyst
        optionPanel.append(showHaplotypeAnalystCheck, showHaplotypeAnalystText, physicOnly, HT.BR())
## END HaplotypeAnalyst
        optionPanel.append(legendBox, legendText, HT.BR(),draw2XBox, draw2XText)
        controlsTable.append(
                HT.TR(HT.TD(innerControlsTable, valign="top"),
                        HT.TD("&nbsp;", width=15), optionPanel),
                HT.TR(HT.TD(physicOnly, " only apply to single chromosome physical mapping", align="Center", colspan=3, Class="fs11 fwn"))
                        )
        controlsForm.append(controlsTable)

        controlsForm.append(HT.Input(name="permSuggestive", value=self.suggestive, type="hidden"))
        controlsForm.append(HT.Input(name="permSignificance", value=self.significance, type="hidden"))

## BEGIN HaplotypeAnalyst #### haplotypeAnalystCheck added below
## END HaplotypeAnalyst

        for key in fd.formdata.keys():
            if key == "searchResult" and type([]) == type(fd.formdata.getvalue(key)):
                controlsForm.append(HT.Input(name=key, value=string.join(fd.formdata.getvalue(key), "\t"), type="hidden"))
            elif key not in ("endMb",  "startMb",  "chromosomes", "scale", "permCheck", "bootCheck",  "additiveCheck", "dominanceCheck",
                    "LRSCheck", "intervalAnalystCheck", "haplotypeAnalystCheck", "lrsMax", "graphWidth", "viewLegend", 'showGenes', 'showSNP', 'draw2X',
                    'permSuggestive', "permSignificance"):
                controlsForm.append(HT.Input(name=key, value=fd.formdata.getvalue(key), type="hidden"))
            else:
                pass

        # updated by NL, move function changeView(i) to webqtl.js and change it to function changeView(i, Chr_Mb_list)
        #                move function chrLength(a, b, c) to webqtl.js and change it to function chrLength(a, b, c, Chr_Mb_list)
        self.dict['js1'] = '<script src="/javascript/sorttable.js"></script>'
        return HT.TD(controlsForm, Class="doubleBorder", width=400)

    def traitInfoTD(self, fd):
        if self.selectedChr == -1:
            intMapHeading = HT.Paragraph('Map Viewer: Whole Genome', Class="title")
        else:
            intMapHeading = HT.Paragraph('Map Viewer: Chr %s' % self.genotype[0].name, Class="title")

        heading2 = HT.Paragraph(HT.Strong('Population: '), "%s %s" % (self.species.title(), fd.RISet) , HT.BR())
        #Trait is from an database
        if self.traitList and self.traitList[0] and self.traitList[0].db:
            #single trait
            if len(self.traitList) == 1:
                thisTrait = self.traitList[0]
                trait_url = HT.Href(text=thisTrait.name, url = os.path.join(webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE) + \
                        "?FormID=showDatabase&incparentsf1=1&database=%s&ProbeSetID=%s" % (thisTrait.db.name, thisTrait.name), \
                        target='_blank', Class="normalsize")
                heading2.append(HT.Strong("Database: "), HT.Href(text=thisTrait.db.fullname, url = webqtlConfig.INFOPAGEHREF % thisTrait.db.name ,\
                        target='_blank',Class="normalsize"),HT.BR())
                if thisTrait.db.type == 'ProbeSet':
                    heading2.append(HT.Strong('Trait ID: '), trait_url, HT.BR(),
                            HT.Strong("Gene Symbol: "), HT.Italic('%s' % thisTrait.symbol,id="green"),HT.BR())
                    if thisTrait.chr and thisTrait.mb:
                        heading2.append(HT.Strong("Location: "), 'Chr %s @ %s Mb' % (thisTrait.chr, thisTrait.mb))
                elif thisTrait.db.type == 'Geno':
                    heading2.append(HT.Strong('Locus : '), trait_url, HT.BR())
                    if thisTrait.chr and thisTrait.mb:
                        heading2.append(HT.Strong("Location: "), 'Chr %s @ %s Mb' % (thisTrait.chr, thisTrait.mb))
                elif thisTrait.db.type == 'Publish':
                    heading2.append(HT.Strong('Record ID: '), trait_url, HT.BR())
                else:
                    pass
            else:
                heading2.append(HT.Strong("Traits: "), "Multiple Traits")
        else:
            heading2.append(HT.Strong("Trait Name: "), fd.identification)
        return HT.TD(intMapHeading, heading2, valign="top")

    def drawPermutationHistogram(self):
        #########################################
        #      Permutation Graph
        #########################################
        myCanvas = pid.PILCanvas(size=(400,300))
        #plotBar(myCanvas,10,10,390,290,LRSArray,XLabel='LRS',YLabel='Frequency',title=' Histogram of Permutation Test',identification=fd.identification)
        Plot.plotBar(myCanvas, self.LRSArray,XLabel='LRS',YLabel='Frequency',title=' Histogram of Permutation Test')
        filename= webqtlUtil.genRandStr("Reg_")
        myCanvas.save(webqtlConfig.IMGDIR+filename, format='gif')
        img=HT.Image('/image/'+filename+'.gif',border=0,alt='Histogram of Permutation Test')


        self.suggestive = self.LRSArray[int(self.nperm*0.37-1)]
        self.significant = self.LRSArray[int(self.nperm*0.95-1)]
        self.highlysignificant = self.LRSArray[int(self.nperm*0.99-1)]

        permutationHeading = HT.Paragraph('Histogram of Permutation Test')
        permutationHeading.__setattr__("class","title")

        permutation = HT.TableLite()
        permutation.append(HT.TR(HT.TD(img)),
                           HT.TR(HT.TD('')),
                           HT.TR(HT.TD('Total of %d permutations'%self.nperm)))
        
        return permutation
    
    def permutationTextFile(self):
        filename= webqtlUtil.genRandStr("Reg_")
        fpText = open('%s.txt' % (webqtlConfig.TMPDIR+filename), 'wb')
        fpText.write('Suggestive LRS (p = 0.63) = %3.2f\n'%self.suggestive)
        fpText.write('Significant LRS (p = 0.05) = %3.2f\n'%self.significant)
        fpText.write('Highly Significant LRS (p = 0.01) = %3.2f\n\n'%self.highlysignificant)
        fpText.write('%s Permutations\n\n' % str(len(self.LRSArray)))
        LRSInfo =HT.Paragraph('&nbsp;&nbsp;&nbsp;&nbsp;Suggestive LRS = %3.2f\n'%self.suggestive,
                              HT.BR(),
                              '&nbsp;&nbsp;&nbsp;&nbsp;Significant LRS =%3.2f\n'%self.significant,
                              HT.BR(),
                              '&nbsp;&nbsp;&nbsp;&nbsp;Highly Significant LRS =%3.2f\n' % self.highlysignificant)
        
        for lrs_value in self.LRSArray:
            fpText.write(str(lrs_value) + "\n")
        
        textUrl = HT.Href(text = 'Download Permutation Results', url= '/tmp/'+filename+'.txt', target = "_blank", Class='fs12 fwn')
        
        return textUrl

    def geneTable(self, geneCol, refGene=None):
        #SNPLink = 0 #Not sure what this is used for

        if self.species == 'mouse' or self.species == 'rat':

            gene_tblobj = {}
            gene_tblobj["header"] = self.getGeneTableHeader(refGene=None)
            gene_tblobj["body"] = self.getGeneTableBody(geneCol, refGene=None)

            sortby = self.getSortByValue()

            filename= webqtlUtil.genRandStr("Mapping_")

            objfile = open('%s.obj' % (webqtlConfig.TMPDIR+filename), 'wb')
            cPickle.dump(gene_tblobj, objfile)
            objfile.close()

            gene_table = webqtlUtil.genTableObj(tblobj=gene_tblobj, file=filename, sortby=sortby, tableID="sortable", addIndex="0")

        else:
            gene_table = ""

        return gene_table    

    def getLiteratureCorrelation(cursor,geneId1=None,geneId2=None):
        if not geneId1 or not geneId2:
            return None
        if geneId1 == geneId2:
            return 1.0
        geneId1 = str(geneId1)
        geneId2 = str(geneId2)
        lCorr = None
        try:
            query = 'SELECT Value FROM LCorrRamin3 WHERE GeneId1 = %s and GeneId2 = %s'
            for x,y in [(geneId1,geneId2),(geneId2,geneId1)]:
                cursor.execute(query,(x,y))
                lCorr =  cursor.fetchone()
                if lCorr:
                    lCorr = lCorr[0]
                    break
        except: raise #lCorr = None
        return lCorr

    def getGeneTableHeader(self, refGene=None):

        gene_tblobj_header = []

        col_class = "fs14 fwb ffl b1 cw cbrb"

        if self.species == "mouse":

            if refGene:
                gene_tblobj_header = [[THCell(HT.TD('Index', HT.BR(), HT.BR(), align='left', width=50, Class=col_class), text="index", idx=0),
                        THCell(HT.TD('Symbol', HT.BR(), HT.BR(), align='left', width=100, Class=col_class), text="symbol", idx=1),
                        THCell(HT.TD('Mb Start',HT.BR(),'(mm9)', align='left', width=100, Class=col_class), text="mb_start_mm9", idx=2),
                        THCell(HT.TD('Length (Kb)', HT.BR(), HT.BR(), align='left', width=100, Class=col_class), text="length", idx=3),
                        THCell(HT.TD('SNP',HT.BR(),'Count', align='left', width=47, Class=col_class), text="snp_count", idx=4),
                        THCell(HT.TD('SNP',HT.BR(),'Density', align='left', width=78, Class=col_class), text="snp_density", idx=5),
                        THCell(HT.TD('Avg',HT.BR(),'Expr', HT.BR(), HT.BR(), align='left', width=44, Class=col_class), sort=0, idx=6),
                        THCell(HT.TD('Human',HT.BR(),'Chr', align='left', width=60, Class=col_class), text="human_chr", idx=7),
                        THCell(HT.TD('Mb Start',HT.BR(),'(hg19)', align='left', width=100, Class=col_class), text="mb_start_hg19", idx=8),
                        THCell(HT.TD('Literature',HT.BR(),'Correlation', align='left', width=100, Class=col_class), text="lit_corr", idx=9),
                        THCell(HT.TD('Gene Description', HT.BR(), HT.BR(), align='left', width=290, Class=col_class), text="description", idx=10),
                        THCell(HT.TD('PolymiRTS',HT.BR(),'Database', HT.BR(), HT.Href(url='http://compbio.uthsc.edu/miRSNP/', text='>>', target="_blank", Class="normalsize"),
                                        align='left', width=100, Class=col_class), sort=0, idx=11),
                        THCell(HT.TD('Gene Weaver', HT.BR(), 'Info Content', HT.BR(), HT.Href(url='http://geneweaver.org/', text='>>', target="_blank", Class="normalsize"),
                                        align='left', width=110, Class=col_class), sort=0, idx=12),
                                        ]]
            else:
                gene_tblobj_header = [[THCell(HT.TD('Index', HT.BR(), HT.BR(), align='left', width=50, Class=col_class), text="index", idx=0),
                        THCell(HT.TD('Symbol', HT.BR(), HT.BR(), align='left', width=100, Class=col_class), text="symbol", idx=1),
                        THCell(HT.TD('Mb Start',HT.BR(),'(mm9)', align='left', width=100, Class=col_class), text="mb_start_mm9", idx=2),
                        THCell(HT.TD('Length (Kb)', HT.BR(), HT.BR(), align='left', width=100, Class=col_class), text="length", idx=3),
                        THCell(HT.TD('SNP',HT.BR(),'Count', align='left', width=47, Class=col_class), text="snp_count", idx=4),
                        THCell(HT.TD('SNP',HT.BR(),'Density', align='left', width=78, Class=col_class), text="snp_density", idx=5),
                        THCell(HT.TD('Avg',HT.BR(),'Expr', HT.BR(), HT.BR(), align='left', width=44, Class=col_class), sort=0, idx=6),
                        THCell(HT.TD('Human',HT.BR(),'Chr', align='left', width=60, Class=col_class), text="human_chr", idx=7),
                        THCell(HT.TD('Mb Start',HT.BR(),'(hg19)', align='left', width=100, Class=col_class), text="mb_start_hg19", idx=8),
                        THCell(HT.TD('Gene Description', HT.BR(), HT.BR(), align='left', width=290, Class=col_class), text="description", idx=9),
                        THCell(HT.TD('PolymiRTS',HT.BR(),'Database', HT.BR(), HT.Href(url='http://compbio.uthsc.edu/miRSNP/', text='>>', target="_blank", Class="normalsize"),
                                        align='left', width=100, Class=col_class), sort=0, idx=10),
                        THCell(HT.TD('Gene Weaver', HT.BR(), 'Info Content', HT.BR(), HT.Href(url='http://geneweaver.org/', text='>>', target="_blank", Class="normalsize"),
                                        align='left', width=110, Class=col_class), sort=0, idx=11),
                                        ]]

        elif self.species == "rat":

            gene_tblobj_header = [[THCell(HT.TD('Index', HT.BR(), HT.BR(), align='left', width=50, Class=col_class), text="index", idx=0),
                    THCell(HT.TD('Symbol', HT.BR(), HT.BR(), align='left', width=100, Class=col_class), text="symbol", idx=1),
                    THCell(HT.TD('Mb Start',HT.BR(),'(rn3)', align='left', width=100, Class=col_class), text="mb_start_rn3", idx=2),
                    THCell(HT.TD('Length (Kb)', HT.BR(), HT.BR(), align='left', width=100, Class=col_class), text="length", idx=3),
                    THCell(HT.TD('Avg',HT.BR(),'Expr', HT.BR(), HT.BR(), align='left', width=44, Class=col_class), sort=0, idx=4),
                    THCell(HT.TD('Mouse',HT.BR(),'Chr', align='left', width=60, Class=col_class), text="mouse_chr", idx=5),
                    THCell(HT.TD('Mb Start',HT.BR(),'(mm9)', align='left', width=100, Class=col_class), text="mb_start_mm9", idx=6),
                    THCell(HT.TD('Human',HT.BR(),'Chr', align='left', width=60, Class=col_class), text="human_chr", idx=7),
                    THCell(HT.TD('Mb Start',HT.BR(),'(hg19)', align='left', width=100, Class=col_class), text="mb_start_hg19", idx=8),
                    THCell(HT.TD('Gene Description', HT.BR(), HT.BR(), align='left', Class=col_class), text="description", idx=9)]]

        else:
            pass

        return gene_tblobj_header

    def getGeneTableBody(self, geneCol, refGene=None):

        tblobj_body = [] #contains table rows
        className = "fs13 b1 c222"

        tableIterationsCnt = 0
        if self.species == "mouse":

            # polymiRTS
            # http://lily.uthsc.edu:8080/20090422_UTHSC_cuiyan/PolymiRTS_CLS?chrom=2&chrom_from=115&chrom_to=125
            #XZ: We can NOT assume their web service is always on. We must put this block of code in try except.
            try:
                conn = httplib.HTTPConnection("lily.uthsc.edu:8080")
                conn.request("GET", "/20090422_UTHSC_cuiyan/PolymiRTS_CLS?chrom=%s&chrom_from=%s&chrom_to=%s" % (self.genotype[0].name, self.startMb, self.endMb))
                response = conn.getresponse()
                data = response.read()
                data = data.split()
                conn.close()
                dic = {}
                index = 0
                for i in data:
                    if index%3==0:
                        dic[data[index]] = HT.Href(url=data[index+2], text=data[index+1], target="_blank", Class="normalsize")
                    index = index+1
            except Exception:
                dic={}

            for gIndex, theGO in enumerate(geneCol):

                tableIterationsCnt = tableIterationsCnt + 1

                this_row = [] #container for the cells of each row
                selectCheck = HT.Input(type="checkbox", name="searchResult", value=theGO["GeneSymbol"], Class="checkbox", onClick="highlight(this)") #checkbox for each row

                geneLength = (theGO["TxEnd"] - theGO["TxStart"])*1000.0
                tenPercentLength = geneLength*0.0001
                txStart = theGO["TxStart"]
                txEnd = theGO["TxEnd"]
                theGO["snpDensity"] = theGO["snpCount"]/geneLength
                if self.ALEX_DEBUG_BOOL_PRINT_GENE_LIST:
                    #accessionString = 'http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?CMD=Display&DB=gene&term=%s'  % theGO["NM_ID"]
                    geneIdString = 'http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?db=gene&cmd=Retrieve&dopt=Graphics&list_uids=%s' % theGO["GeneID"]

                    allProbeString = '%s?cmd=sch&gene=%s&alias=1' % (os.path.join(webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE), theGO["GeneSymbol"])
                    if theGO["snpCount"]:
                        snpString = HT.Href(url="%s&chr=%s&start=%s&end=%s&geneName=%s&s1=%d&s2=%d" % (os.path.join(webqtlConfig.CGIDIR, 'main.py?FormID=snpBrowser'),
                                theGO["Chromosome"], theGO["TxStart"], theGO["TxEnd"], theGO["GeneSymbol"], self.diffCol[0], self.diffCol[1]),
                                text=theGO["snpCount"], target="_blank", Class="normalsize")
                    else:
                        snpString = 0

                    mouseStartString = "http://genome.ucsc.edu/cgi-bin/hgTracks?clade=vertebrate&org=Mouse&db=mm9&position=chr" + theGO["Chromosome"] + "%3A" + str(int(theGO["TxStart"] * 1000000.0))  + "-" + str(int(theGO["TxEnd"]*1000000.0)) +"&pix=620&Submit=submit"

                    #Used for sorting
                    mouseStartValue = int(theGO["TxStart"])


                    #the chromosomes for human 1 are 1qXX.XX
                    if theGO['humanGene']:
                        if theGO['humanGene']["TxStart"] == '':
                            humanStartDisplay = ""
                        else:
                            humanStartDisplay = "%0.6f" % theGO['humanGene']["TxStart"]

                        humanChr = theGO['humanGene']["Chromosome"]
                        if humanChr.find('q'):
                            humanChrSort = humanChr[:humanChr.find("q")].join(humanChr[(humanChr.find("q")+1):]) #value used when sorting table
                        elif humanChr.find('p'):
                            humanChrSort = humanChr[:humanChr.find("p")].join(humanChr[(humanChr.find("p")+1):]) #value used when sorting table
                        else:
                            humanChrSort = humanChr
                        humanTxStart = theGO['humanGene']["TxStart"]

                        #Used for sorting
                        humanStartValue = float(theGO['humanGene']["TxStart"])

                        humanStartString = "http://genome.ucsc.edu/cgi-bin/hgTracks?clade=vertebrate&org=Human&db=hg17&position=chr%s:%d-%d" %  (humanChr, int(1000000*theGO['humanGene']["TxStart"]), int(1000000*theGO['humanGene']["TxEnd"]))
                    else:
                        humanStartString = humanChr = humanChrSort = humanStartDisplay = humanStartValue = "--"

                    geneDescription = theGO["GeneDescription"]
                    if len(geneDescription) > 26:
                        geneDescription = geneDescription[:26]+"..."
                    probeSetSearch = HT.Href(allProbeString, HT.Image("/images/webqtl_search.gif", border=0), target="_blank")

                    if theGO["snpDensity"] < 0.000001:
                        snpDensityStr = "0"
                    else:
                        snpDensityStr = "%0.6f" % theGO["snpDensity"]

                    avgExpr = [] #theGO["avgExprVal"]
                    if avgExpr in ([], None):
                        avgExpr = "--"
                    else:
                        avgExpr = "%0.6f" % avgExpr

                    # polymiRTS
                    polymiRTS = ' '
                    if dic.has_key(theGO["GeneID"]):
                        polymiRTS = dic[theGO["GeneID"]]

                    # If we have a referenceGene then we will show the Literature Correlation
                    if refGene:
                        try:
                            literatureCorrelation = self.getLiteratureCorrelation(self.cursor,refGene,theGO['GeneID'])
                        except:
                            literatureCorrelation = "N/A"

                        literatureCorrelationString = str(self.getLiteratureCorrelation(self.cursor,refGene,theGO['GeneID']) or "N/A")

                        this_row.append(TDCell(HT.TD(tableIterationsCnt, selectCheck, width=30, align='right', Class=className), tableIterationsCnt, tableIterationsCnt))
                        this_row.append(TDCell(HT.TD(HT.Href(geneIdString, theGO["GeneSymbol"], target="_blank"), "&nbsp;", probeSetSearch, align='right', Class=className), theGO["GeneSymbol"], theGO["GeneSymbol"]))
                        this_row.append(TDCell(HT.TD(HT.Href(mouseStartString, "%0.6f" % txStart, target="_blank"), align='right', Class=className), str(mouseStartValue), mouseStartValue))
                        this_row.append(TDCell(HT.TD(HT.Href("javascript:centerIntervalMapOnRange2('%s', " % theGO["Chromosome"]+str(txStart-tenPercentLength) + ", " + str(txEnd+tenPercentLength) + ", document.changeViewForm)", "%0.3f" % geneLength), align='right', Class=className), "%0.3f" % geneLength, geneLength))
                        this_row.append(TDCell(HT.TD(snpString, align='right', Class=className), str(theGO["snpCount"]), theGO["snpCount"]))
                        this_row.append(TDCell(HT.TD(snpDensityStr, align='right', Class=className), snpDensityStr, theGO["snpDensity"]))
                        this_row.append(TDCell(HT.TD(avgExpr, align='right', Class=className), "--", "--"))
                        this_row.append(TDCell(HT.TD(humanChr, align='right', Class=className), humanChr, humanChrSort))
                        this_row.append(TDCell(HT.TD(HT.Href(humanStartString, humanStartDisplay, target="_blank"), align='right', Class=className), humanStartDisplay, humanStartValue))
                        this_row.append(TDCell(HT.TD(literatureCorrelationString, align='right', Class=className), literatureCorrelationString, literatureCorrelation))
                        this_row.append(TDCell(HT.TD(geneDescription, align='right', Class=className), geneDescription, geneDescription))
                        this_row.append(TDCell(HT.TD(polymiRTS, align='right', Class=className), "", ""))
                        this_row.append(TDCell(HT.TD("", align='right', Class=className), "", ""))

                    else:
                        this_row.append(TDCell(HT.TD(tableIterationsCnt, selectCheck, width=30, align='right', Class=className), tableIterationsCnt, tableIterationsCnt))
                        this_row.append(TDCell(HT.TD(HT.Href(geneIdString, theGO["GeneSymbol"], target="_blank"), "&nbsp;", probeSetSearch, align='right', Class=className), theGO["GeneSymbol"], theGO["GeneSymbol"]))
                        this_row.append(TDCell(HT.TD(HT.Href(mouseStartString, "%0.6f" % txStart, target="_blank"), align='right', Class=className), str(mouseStartValue), mouseStartValue))
                        this_row.append(TDCell(HT.TD(HT.Href("javascript:centerIntervalMapOnRange2('%s', " % theGO["Chromosome"]+str(txStart-tenPercentLength) + ", " + str(txEnd+tenPercentLength) + ", document.changeViewForm)", "%0.3f" % geneLength), align='right', Class=className), "%0.3f" % geneLength, geneLength))
                        this_row.append(TDCell(HT.TD(snpString, align='right', Class=className), str(theGO["snpCount"]), theGO["snpCount"]))
                        this_row.append(TDCell(HT.TD(snpDensityStr, align='right', Class=className), snpDensityStr, theGO["snpDensity"]))
                        this_row.append(TDCell(HT.TD(avgExpr, align='right', Class=className), "--", "--"))
                        this_row.append(TDCell(HT.TD(humanChr, align='right', Class=className), humanChr, humanChrSort))
                        this_row.append(TDCell(HT.TD(HT.Href(humanStartString, humanStartDisplay, target="_blank"), align='right', Class=className), humanStartDisplay, humanStartValue))
                        this_row.append(TDCell(HT.TD(geneDescription, align='right', Class=className), geneDescription, geneDescription))
                        this_row.append(TDCell(HT.TD(polymiRTS, align='right', Class=className), "", ""))
                        this_row.append(TDCell(HT.TD("", align='right', Class=className), "", ""))

                tblobj_body.append(this_row)

        elif self.species == 'rat':

            for gIndex, theGO in enumerate(geneCol):

                this_row = [] #container for the cells of each row
                selectCheck = HT.Input(type="checkbox", name="searchResult", Class="checkbox", onClick="highlight(this)") #checkbox for each row

                webqtlSearch = HT.Href(os.path.join(webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE)+"?cmd=sch&gene=%s&alias=1&species=rat" % theGO["GeneSymbol"], HT.Image("/images/webqtl_search.gif", border=0), target="_blank")

                if theGO["GeneID"] != "":
                    geneSymbolNCBI = HT.Href("http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?db=gene&cmd=Retrieve&dopt=Graphics&list_uids=%s" % theGO["GeneID"], theGO["GeneSymbol"], Class="normalsize", target="_blanK")
                else:
                    geneSymbolNCBI = theGO["GeneSymbol"]

                geneLength = (float(theGO["TxEnd"]) - float(theGO["TxStart"]))
                geneLengthURL = "javascript:centerIntervalMapOnRange2('%s', %f, %f, document.changeViewForm)" % (theGO["Chromosome"], float(theGO["TxStart"])-(geneLength*0.1), float(theGO["TxEnd"])+(geneLength*0.1))

                avgExprVal = []
                if avgExprVal != "" and avgExprVal:
                    avgExprVal = "%0.5f" % float(avgExprVal)
                else:
                    avgExprVal = ""

                #Mouse Gene
                if theGO['mouseGene']:
                    mouseChr = theGO['mouseGene']["Chromosome"]
                    mouseTxStart = theGO['mouseGene']["TxStart"]
                else:
                    mouseChr = mouseTxStart = ""

                #the chromosomes for human 1 are 1qXX.XX
                if theGO['humanGene']:
                    humanChr = theGO['humanGene']["Chromosome"]
                    if 'q' in humanChr:
                        humanChrSort = humanChr[:humanChr.find("q")].join(humanChr[(humanChr.find("q")+1):]) #value used when sorting table
                    elif 'p' in humanChr:
                        humanChrSort = humanChr[:humanChr.find("p")].join(humanChr[(humanChr.find("p")+1):]) #value used when sorting table
                    else:
                        humanChrSort = humanChr
                    humanTxStart = theGO['humanGene']["TxStart"]
                else:
                    humanChr = humanTxStart = humanChrSort = ""

                geneDesc = theGO["GeneDescription"]
                if geneDesc == "---":
                    geneDesc = ""

                """
                if len(geneDesc) > 40:
                        geneDesc = gene0So apparently Angola prison (which used to be a slave plantation) has a rodeo that they invite the general public to.
The prisoners are not trained before hand
But its cool because its completely voluntary.
And by voluntary, according to HFG when I talked to him, they have a choice between doing it or door number two and "door number 2 is... rather worse than volunteering"Desc[:37] + "..."
                """

                this_row.append(TDCell(HT.TD(gIndex + 1, selectCheck, align='left', Class=className), str(gIndex+1), gIndex+1))
                this_row.append(TDCell(HT.TD(webqtlSearch, geneSymbolNCBI, align='left', Class=className), theGO["GeneSymbol"], theGO["GeneSymbol"]))
                this_row.append(TDCell(HT.TD(theGO["TxStart"], align='left', Class=className), theGO["TxStart"], theGO["TxStart"]))
                this_row.append(TDCell(HT.TD(HT.Href(geneLengthURL, "%0.3f" % (geneLength*1000.0)), align='left', Class=className), "%0.3f" % (geneLength*1000.0), (geneLength*1000.0)))
                this_row.append(TDCell(HT.TD(avgExprVal, align='left', Class=className), "", ""))
                this_row.append(TDCell(HT.TD(mouseChr, align='left', Class=className), mouseChr, mouseChr))
                this_row.append(TDCell(HT.TD(mouseTxStart, align='left', Class=className), mouseTxStart, mouseTxStart))
                this_row.append(TDCell(HT.TD(humanChr, align='left', Class=className), humanChr, humanChrSort))
                this_row.append(TDCell(HT.TD(humanTxStart, align='left', Class=className), humanTxStart, humanTxStart))
                this_row.append(TDCell(HT.TD(geneDesc, align='left', Class=className), geneDesc, geneDesc))

                tblobj_body.append(this_row)

        else:
            pass

        return tblobj_body


    def getSortByValue(self):

        sortby = ("", "")

        return sortby