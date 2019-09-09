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

import datetime
import string
from math import *
import piddle as pid
import sys,os
import cPickle
import httplib
import json

from flask import Flask, g

from htmlgen import HTMLgen2 as HT

from base import webqtlConfig
from base.GeneralObject import GeneralObject
from utility import webqtlUtil
from utility import helper_functions
from utility import Plot
from utility.benchmark import Bench
from wqflask.interval_analyst import GeneUtil
from base.webqtlConfig import TMPDIR, GENERATED_TEXT_DIR, GENERATED_IMAGE_DIR

import utility.logger
logger = utility.logger.getLogger(__name__ )

#########################################
#      Inteval Mapping Plot Page
#########################################
class DisplayMappingResults(object):
    cMGraphInterval = 5
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

    BAND_HEIGHT = 10
    BAND_HEIGHT = 10
    BAND_HEIGHT = 10

    NUM_GENE_ROWS       = 10
    EACH_GENE_HEIGHT    = 6  # number of pixels tall, for each gene to display
    EACH_GENE_ARROW_WIDTH = 5
    EACH_GENE_ARROW_SPACING = 14
    DRAW_DETAIL_MB = 4
    DRAW_UTR_LABELS_MB = 4

    qmarkImg = HT.Image('/images/qmarkBoxBlue.gif', width=10, height=13, border=0, alt='Glossary')
    # Note that "qmark.gif" is a similar, smaller, rounded-edges question mark. It doesn't look
    # like the ones on the image, though, which is why we don't use it here.

    HELP_WINDOW_NAME = 'helpWind'

    ## BEGIN HaplotypeAnalyst
    NR_INDIVIDUALS = 0
    ## END HaplotypeAnalyst

    ALEX_DEBUG_BOOL_PRINT_GENE_LIST = 1

    kONE_MILLION = 1000000

    LODFACTOR = 4.61

    SNP_COLOR           = pid.orange # Color for the SNP "seismograph"
    TRANSCRIPT_LOCATION_COLOR = pid.mediumpurple

    BOOTSTRAP_BOX_COLOR = pid.yellow
    LRS_COLOR           = pid.HexColor(0x0000FF)
    SIGNIFICANT_COLOR   = pid.HexColor(0xEBC7C7)
    SUGGESTIVE_COLOR    = pid.gainsboro
    SIGNIFICANT_WIDTH = 5
    SUGGESTIVE_WIDTH = 5
    ADDITIVE_COLOR_POSITIVE = pid.green
    ADDITIVE_COLOR_NEGATIVE = pid.orange
    DOMINANCE_COLOR_POSITIVE = pid.darkviolet
    DOMINANCE_COLOR_NEGATIVE = pid.red

    ## BEGIN HaplotypeAnalyst
    HAPLOTYPE_POSITIVE = pid.green
    HAPLOTYPE_NEGATIVE = pid.red
    HAPLOTYPE_HETEROZYGOUS = pid.blue
    HAPLOTYPE_RECOMBINATION = pid.darkgray
    ## END HaplotypeAnalyst

    TOP_RIGHT_INFO_COLOR = pid.black

    CLICKABLE_WEBQTL_REGION_COLOR     = pid.HexColor(0xF5D3D3)
    CLICKABLE_WEBQTL_REGION_OUTLINE_COLOR = pid.HexColor(0xFCE9E9)
    CLICKABLE_WEBQTL_TEXT_COLOR       = pid.HexColor(0x912828)

    CLICKABLE_PHENOGEN_REGION_COLOR   = pid.HexColor(0xA2FB94)
    CLICKABLE_PHENOGEN_REGION_OUTLINE_COLOR = pid.HexColor(0xCEFEC7)
    CLICKABLE_PHENOGEN_TEXT_COLOR     = pid.HexColor(0x1FD504)

    CLICKABLE_UCSC_REGION_COLOR     = pid.HexColor(0xDDDDEE)
    CLICKABLE_UCSC_REGION_OUTLINE_COLOR = pid.HexColor(0xEDEDFF)
    CLICKABLE_UCSC_TEXT_COLOR       = pid.HexColor(0x333366)

    CLICKABLE_ENSEMBL_REGION_COLOR  = pid.HexColor(0xEEEEDD)
    CLICKABLE_ENSEMBL_REGION_OUTLINE_COLOR = pid.HexColor(0xFEFEEE)
    CLICKABLE_ENSEMBL_TEXT_COLOR    = pid.HexColor(0x555500)

    GRAPH_BACK_LIGHT_COLOR = pid.HexColor(0xFBFBFF)
    GRAPH_BACK_DARK_COLOR  = pid.HexColor(0xF1F1F9)

    HELP_PAGE_REF = '/glossary.html'

    def __init__(self, start_vars):
        logger.info("Running qtlreaper")

        self.temp_uuid = start_vars['temp_uuid']

        self.dataset = start_vars['dataset']
        self.this_trait = start_vars['this_trait']
        self.n_samples = start_vars['num_vals']
        self.species = start_vars['species']
        self.genofile_string = ""
        if 'genofile_string' in start_vars:
            self.genofile_string = start_vars['genofile_string']

        self.geno_db_exists = start_vars['geno_db_exists']

        self.first_run = True
        if 'first_run' in start_vars:
            self.first_run = start_vars['first_run']

        #Needing for form submission when doing single chr mapping or remapping after changing options
        self.samples = start_vars['samples']
        self.vals = start_vars['vals']
        self.mapping_method = start_vars['mapping_method']
        self.mapping_results_path = start_vars['mapping_results_path']
        if self.mapping_method == "rqtl_geno":
            self.mapmethod_rqtl_geno = start_vars['method']
            self.mapmodel_rqtl_geno = start_vars['model']
            self.pair_scan = start_vars['pair_scan']

        #if self.mapping_method != "gemma" and self.mapping_method != "plink":
        self.js_data = start_vars['js_data']
        self.trimmed_markers = start_vars['trimmed_markers'] #Top markers to display in table

        if self.dataset.group.species == "rat":
            self._ucscDb = "rn3"
        elif self.dataset.group.species == "mouse":
            self._ucscDb = "mm9"
        else:
            self._ucscDb = ""

        #####################################
        # Options
        #####################################
        #Mapping options
        if start_vars['mapping_scale'] != "":
            self.plotScale = start_vars['mapping_scale']
        else:
            self.plotScale = "physic"

        self.manhattan_plot = start_vars['manhattan_plot']

        if 'permCheck' in start_vars.keys():
            self.permChecked = start_vars['permCheck']
        else:
            self.permChecked = False
        if start_vars['num_perm'] > 0:
            self.nperm = int(start_vars['num_perm'])
            if self.permChecked:
                self.perm_output = start_vars['perm_output']
                self.suggestive = start_vars['suggestive']
                self.significant = start_vars['significant']
        else:
            self.nperm = 0

        if 'bootCheck' in start_vars.keys():
            self.bootChecked = start_vars['bootCheck']
        else:
            self.bootChecked = False
        if 'num_bootstrap' in start_vars.keys():
            self.nboot = int(start_vars['num_bootstrap'])
        else:
            self.nboot = 0
        if 'bootstrap_results' in start_vars.keys():
            self.bootResult = start_vars['bootstrap_results']
        else:
            self.bootResult = []

        if 'do_control' in start_vars.keys():
            self.doControl = start_vars['do_control']
        else:
            self.doControl = "false"
        if 'control_marker' in start_vars.keys():
            self.controlLocus = start_vars['control_marker']
        else:
            self.controlLocus = ""
        if 'covariates' in start_vars.keys():
            self.covariates = start_vars['covariates']
        if 'maf' in start_vars.keys():
            self.maf = start_vars['maf']
        if 'output_files' in start_vars.keys():
            self.output_files = start_vars['output_files']
        if 'use_loco' in start_vars.keys() and self.mapping_method == "gemma":
            self.use_loco = start_vars['use_loco']

        if 'reaper_version' in start_vars.keys() and self.mapping_method == "reaper":
            self.reaper_version = start_vars['reaper_version']
            if 'output_files' in start_vars:
                self.output_files = ",".join(start_vars['output_files'])

        self.selectedChr = int(start_vars['selected_chr'])

        self.strainlist = start_vars['samples']

        if self.mapping_method == "reaper" and self.manhattan_plot != True:
            self.genotype = self.dataset.group.read_genotype_file(use_reaper=True)
        else:
            self.genotype = self.dataset.group.read_genotype_file()

        #Darwing Options
        try:
           if self.selectedChr > -1:
               self.graphWidth  = min(self.GRAPH_MAX_WIDTH, max(self.GRAPH_MIN_WIDTH, int(start_vars['graphWidth'])))
           else:
               self.graphWidth  = min(self.GRAPH_MAX_WIDTH, max(self.MULT_GRAPH_MIN_WIDTH, int(start_vars['graphWidth'])))
        except:
           if self.selectedChr > -1:
               self.graphWidth  = self.GRAPH_DEFAULT_WIDTH
           else:
               self.graphWidth  = self.MULT_GRAPH_DEFAULT_WIDTH

## BEGIN HaplotypeAnalyst
        if 'haplotypeAnalystCheck' in start_vars.keys():
            self.haplotypeAnalystChecked = start_vars['haplotypeAnalystCheck']
        else:
            self.haplotypeAnalystChecked = False
## END HaplotypeAnalyst

        self.graphHeight = self.GRAPH_DEFAULT_HEIGHT
        self.dominanceChecked = False
        if 'LRSCheck' in start_vars.keys():
            self.LRS_LOD = start_vars['LRSCheck']
        else:
            self.LRS_LOD = start_vars['score_type']
        self.intervalAnalystChecked = True
        self.draw2X = False
        if 'additiveCheck' in start_vars.keys():
            self.additiveChecked = start_vars['additiveCheck']
        else:
            self.additiveChecked = False
        if 'viewLegend' in start_vars.keys():
            self.legendChecked = start_vars['viewLegend']
        else:
            self.legendChecked = False
        if 'showSNP' in start_vars.keys():
            self.SNPChecked = start_vars['showSNP']
        else:
            self.SNPChecked = False
        if 'showGenes' in start_vars.keys():
            self.geneChecked = start_vars['showGenes']
        else:
            self.geneChecked = False
        try:
            self.startMb = float(start_vars['startMb'])
        except:
            self.startMb = -1
        try:
            self.endMb = float(start_vars['endMb'])
        except:
            self.endMb = -1
        try:
            self.lrsMax = float(start_vars['lrsMax'])
        except:
            self.lrsMax = 0

        #Trait Infos
        self.identification = ""

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

        self.traitList = []
        thisTrait = start_vars['this_trait']
        self.traitList.append(thisTrait)

## BEGIN HaplotypeAnalyst
## count the amount of individuals to be plotted, and increase self.graphHeight
        if self.haplotypeAnalystChecked and self.selectedChr > -1:
            thisTrait = self.this_trait
            _strains, _vals, _vars, _aliases = thisTrait.export_informative()
            smd=[]
            for ii, _val in enumerate(self.vals):
                if _val != "x":
                    temp = GeneralObject(name=self.samples[ii], value=float(_val))
                    smd.append(temp)
                else:
                    continue
            samplelist = list(self.genotype.prgy)
            for j,_geno in enumerate (self.genotype[0][1].genotype):
                for item in smd:
                    if item.name == samplelist[j]:
                        self.NR_INDIVIDUALS = self.NR_INDIVIDUALS + 1
# default:
            self.graphHeight = self.graphHeight + 2 * (self.NR_INDIVIDUALS+10) * self.EACH_GENE_HEIGHT
## END HaplotypeAnalyst

        ################################################################
        # Calculations QTL goes here
        ################################################################
        self.multipleInterval = len(self.traitList) > 1
        self.qtlresults = start_vars['qtl_results']

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

        ################################################################
        # GeneCollection goes here
        ################################################################
        if self.plotScale == 'physic' and self.selectedChr != -1:
            #StartMb or EndMb
            if self.startMb < 0 or self.endMb < 0:
                self.startMb = 0
                self.endMb = self.ChrLengthMbList[self.selectedChr - 1]

        geneTable = ""

        self.geneCol = None
        if self.plotScale == 'physic' and self.selectedChr > -1 and (self.intervalAnalystChecked  or self.geneChecked):
            # Draw the genes for this chromosome / region of this chromosome
            webqtldatabase = self.dataset.name

            if self.dataset.group.species == "mouse":
                if self.selectedChr == 20:
                    chrName = "X"
                else:
                    chrName = self.selectedChr
                self.geneCol = GeneUtil.loadGenes(chrName, self.diffCol, self.startMb, self.endMb, "mouse")
            elif self.dataset.group.species == "rat":
                if self.selectedChr == 21:
                    chrName = "X"
                else:
                    chrName = self.selectedChr
                self.geneCol = GeneUtil.loadGenes(chrName, self.diffCol, self.startMb, self.endMb, "rat")

            if self.geneCol and self.intervalAnalystChecked:
               #######################################################################
               #Nick use GENEID as RefGene to get Literature Correlation Informations#
               #For Interval Mapping, Literature Correlation isn't useful, so skip it#
               #through set GENEID is None                                           #
               #######################################################################

               GENEID = None

               self.geneTable(self.geneCol, GENEID)

        ################################################################
        # Plots goes here
        ################################################################
        showLocusForm = ""
        intCanvas = pid.PILCanvas(size=(self.graphWidth, self.graphHeight))
        with Bench("Drawing Plot"):
            gifmap = self.plotIntMapping(intCanvas, startMb = self.startMb, endMb = self.endMb, showLocusForm= showLocusForm)

        self.gifmap = gifmap.__str__()

        self.filename= webqtlUtil.genRandStr("Itvl_")
        intCanvas.save(os.path.join(webqtlConfig.GENERATED_IMAGE_DIR, self.filename), format='png')
        intImg=HT.Image('/image/'+self.filename+'.png', border=0, usemap='#WebQTLImageMap')

        #Scales plot differently for high resolution
        if self.draw2X:
            intCanvasX2 = pid.PILCanvas(size=(self.graphWidth*2,self.graphHeight*2))
            gifmapX2 = self.plotIntMapping(intCanvasX2, startMb = self.startMb, endMb = self.endMb, showLocusForm= showLocusForm, zoom=2)
            intCanvasX2.save(os.path.join(webqtlConfig.GENERATED_IMAGE_DIR, self.filename+"X2"), format='png')

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

        if (self.permChecked and self.nperm > 0) and not (self.multipleInterval and 0 < self.nperm):
            self.perm_filename = self.drawPermutationHistogram()

        ################################################################
        # footnote goes here
        ################################################################
        btminfo = HT.Paragraph(Id="smallsize") #Small('More information about this graph is available here.')

        if self.traitList and self.traitList[0].dataset and self.traitList[0].dataset.type == 'Geno':
            btminfo.append(HT.BR(), 'Mapping using genotype data as a trait will result in infinity LRS at one locus. In order to display the result properly, all LRSs higher than 100 are capped at 100.')

    def plotIntMapping(self, canvas, offset= (80, 120, 20, 100), zoom = 1, startMb = None, endMb = None, showLocusForm = ""):
        #calculating margins
        xLeftOffset, xRightOffset, yTopOffset, yBottomOffset = offset
        if self.multipleInterval:
            yTopOffset = max(90, yTopOffset)
        else:
            if self.legendChecked:
                yTopOffset = max(90, yTopOffset)
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

        #Drawing Area Height
        drawAreaHeight = plotHeight
        if self.plotScale == 'physic' and self.selectedChr > -1:
            if self.dataset.group.species == "mouse" or self.dataset.group.species == "rat":
                drawAreaHeight -= 4*self.BAND_HEIGHT + 4*self.BAND_SPACING+ 10*zoom
            else:
                drawAreaHeight -= 3*self.BAND_HEIGHT + 3*self.BAND_SPACING+ 10*zoom
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

        newoffset = (xLeftOffset, xRightOffset, yTopOffset, yBottomOffset)
        # Draw the alternating-color background first and get plotXScale
        plotXScale = self.drawGraphBackground(canvas, gifmap, offset=newoffset, zoom= zoom, startMb=startMb, endMb = endMb)

        #draw bootstap
        if self.bootChecked and not self.multipleInterval and not self.manhattan_plot:
            self.drawBootStrapResult(canvas, self.nboot, drawAreaHeight, plotXScale, offset=newoffset, zoom= zoom, startMb=startMb, endMb = endMb)

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
            self.drawLegendPanel(canvas, offset=newoffset, zoom = zoom)
        else:
            pass

        #draw position, no need to use a separate function
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

        if self.selectedChr == -1: #ZS: If viewing full genome/all chromosomes
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
        else:
            for j, _chr in enumerate(self.genotype):
                if _chr.name == self.ChrList[self.selectedChr][0]:
                    BootCoord.append( [])
                for _locus in _chr:
                    if _chr.name == self.ChrList[self.selectedChr][0]:
                        if self.plotScale == 'physic':
                            Xc = startX + (_locus.Mb-startMb)*plotXScale
                        else:
                            Xc = startX + (_locus.cM-_chr[0].cM)*plotXScale
                        BootCoord[-1].append([Xc, self.bootResult[i]])
                    i += 1

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

        previous_chr = 1
        previous_chr_as_int = 0
        if self.plotScale == "physic":
            this_chr = str(self.ChrList[self.selectedChr][0])
        else:
            this_chr = str(self.ChrList[self.selectedChr][1]+1)

        if self.plotScale == 'physic':
            if self.selectedChr > -1:
                if this_chr != Chr or Mb < self.startMb or Mb > self.endMb:
                    return
                else:
                    locPixel = xLeftOffset + (Mb-self.startMb)*plotXScale
            else:
                locPixel = xLeftOffset
                for i, _chr in enumerate(self.ChrList[1:]):
                    if _chr[0] != Chr:
                        locPixel += (self.ChrLengthDistList[i] + self.GraphInterval)*plotXScale
                    else:
                        locPixel += Mb*plotXScale
                        break
        else:
            if self.selectedChr > -1:
                for i, qtlresult in enumerate(self.qtlresults):
                    if qtlresult['chr'] != self.selectedChr:
                        continue

                    if i==0 and qtlresult['Mb'] >= Mb:
                        locPixel=-1
                        break

                    #the trait's position is between two traits
                    if i > 0 and self.qtlresults[i-1]['Mb'] < Mb and qtlresult['Mb'] >= Mb:
                        locPixel = xLeftOffset + plotXScale*(self.qtlresults[i-1]['Mb']+(qtlresult['Mb']-self.qtlresults[i-1]['Mb'])*(Mb - self.qtlresults[i-1]['Mb'])/(qtlresult['Mb']-self.qtlresults[i-1]['Mb']))
                        break

                    #the trait's position is on the right of the last genotype
                    if i==len(self.qtlresults) and Mb>=qtlresult['Mb']:
                        locPixel = -1
            else:
                locPixel = xLeftOffset
                for i, _chr in enumerate(self.ChrList):
                    if i < (len(self.ChrList)-1):
                        if _chr != Chr:
                            locPixel += (self.ChrLengthDistList[i] + self.GraphInterval)*plotXScale
                        else:
                            locPixel += (Mb*(_chr[-1].cM-_chr[0].cM)/self.ChrLengthCMList[i])*plotXScale
                            break
        if locPixel >= 0 and self.plotScale == 'physic':
            traitPixel = ((locPixel, yZero), (locPixel-7, yZero+14), (locPixel+7, yZero+14))
            canvas.drawPolygon(traitPixel, edgeColor=pid.black, fillColor=self.TRANSCRIPT_LOCATION_COLOR, closed=1)

        if self.legendChecked:
            startPosY = 15
            nCol = 2
            smallLabelFont = pid.Font(ttf="trebuc", size=12*fontZoom, bold=1)
            if self.manhattan_plot:
                leftOffset = xLeftOffset
            else:
                leftOffset = xLeftOffset+(nCol-1)*200*fontZoom
            canvas.drawPolygon(((leftOffset+7, startPosY-7), (leftOffset, startPosY+7), (leftOffset+14, startPosY+7)), edgeColor=pid.black, fillColor=self.TRANSCRIPT_LOCATION_COLOR, closed=1)
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
        #chrName = self.genotype[0].name
        chrName = self.ChrList[self.selectedChr][0]

        stepMb = (endMb-startMb)/plotWidth
        strainId1, strainId2 = self.diffCol
        SNPCounts = []

        while startMb<endMb:
            snp_count = g.db.execute("""
                    select
                            count(*) from BXDSnpPosition
                    where
                            Chr = '%s' AND Mb >= %2.6f AND Mb < %2.6f AND
                            StrainId1 = %d AND StrainId2 = %d
                    """ % (chrName, startMb, startMb+stepMb, strainId1, strainId2)).fetchone()[0]
            SNPCounts.append(snp_count)
            startMb += stepMb

        if (len(SNPCounts) > 0):
            maxCount = max(SNPCounts)
            if maxCount>0:
                for i in range(xLeftOffset, xLeftOffset + plotWidth):
                    snpDensity = float(SNPCounts[i-xLeftOffset]*SNP_HEIGHT_MODIFIER/maxCount)
                    canvas.drawLine(i, drawSNPLocationY+(snpDensity)*zoom, i, drawSNPLocationY-(snpDensity)*zoom, color=self.SNP_COLOR, width=1)

    def drawMultiTraitName(self, fd, canvas, gifmap, showLocusForm, offset= (40, 120, 80, 10), zoom = 1):
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

    def drawLegendPanel(self, canvas, offset= (40, 120, 80, 10), zoom = 1):
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
        if self.manhattan_plot != True:
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

        if self.permChecked and self.nperm > 0:
            startPosY += stepPosY
            startPosX = xLeftOffset
            canvas.drawLine(startPosX, startPosY, startPosX + 32, startPosY, color=self.SIGNIFICANT_COLOR, width=self.SIGNIFICANT_WIDTH)
            canvas.drawLine(startPosX, startPosY + stepPosY, startPosX + 32, startPosY + stepPosY, color=self.SUGGESTIVE_COLOR, width=self.SUGGESTIVE_WIDTH)
            canvas.drawString('Significant %s = %2.2f' % (self.LRS_LOD, self.significant),xLeftOffset+42,startPosY +5,font=labelFont,color=pid.black)
            canvas.drawString('Suggestive %s = %2.2f' % (self.LRS_LOD, self.suggestive),xLeftOffset+42,startPosY + 5 +stepPosY,font=labelFont,color=pid.black)

        labelFont = pid.Font(ttf="verdana",size=12*fontZoom)
        labelColor = pid.black
        if self.dataset.type == "Publish" or self.dataset.type == "Geno":
            dataset_label = self.dataset.fullname
        else:
            dataset_label = "%s - %s" % (self.dataset.group.name, self.dataset.fullname)

        string1 = 'Dataset: %s' % (dataset_label)

        if self.genofile_string == "":
            string2 = 'Genotype File: %s.geno' % self.dataset.group.name
        else:
            string2 = 'Genotype File: %s' % self.genofile_string

        string4 = ''
        if self.mapping_method == "gemma" or self.mapping_method == "gemma_bimbam":
            if self.use_loco == "True":
                string3 = 'Using GEMMA mapping method with LOCO and '
            else:
                string3 = 'Using GEMMA mapping method with '
            if self.covariates != "":
                string3 += 'the cofactors below:'
                cofactor_names = ", ".join([covar.split(":")[0] for covar in self.covariates.split(",")])
                string4 = cofactor_names
            else:
                string3 += 'no cofactors'
        elif self.mapping_method == "rqtl_plink" or self.mapping_method == "rqtl_geno":
            string3 = 'Using R/qtl mapping method with '
            if self.controlLocus and self.doControl != "false":
                string3 += '%s as control' % self.controlLocus
            else:
                string3 += 'no control for other QTLs'
        else:
            string3 = 'Using Haldane mapping function with '
            if self.controlLocus and self.doControl != "false":
                string3 += '%s as control' % self.controlLocus
            else:
                string3 += 'no control for other QTLs'

        if self.this_trait.name:
            if self.selectedChr == -1:
                identification = "Mapping on All Chromosomes for "
            else:
                identification = "Mapping on Chromosome %s for " % (self.ChrList[self.selectedChr][0])

            if self.this_trait.symbol:
                identification += "Trait: %s - %s" % (self.this_trait.name, self.this_trait.symbol)
            elif self.dataset.type == "Publish":
                if self.this_trait.post_publication_abbreviation:
                    identification += "Trait: %s - %s" % (self.this_trait.name, self.this_trait.post_publication_abbreviation)
                elif self.this_trait.pre_publication_abbreviation:
                    identification += "Trait: %s - %s" % (self.this_trait.name, self.this_trait.pre_publication_abbreviation)
                else:
                    identification += "Trait: %s" % (self.this_trait.name)
            else:
                identification += "Trait: %s" % (self.this_trait.name)
            identification += " with %s samples" % (self.n_samples)

            d = 4+ max(canvas.stringWidth(identification, font=labelFont), canvas.stringWidth(string1, font=labelFont), canvas.stringWidth(string2, font=labelFont))
            canvas.drawString(identification,canvas.size[0] - xRightOffset-d,20*fontZoom,font=labelFont,color=labelColor)
        else:
            d = 4+ max(canvas.stringWidth(string1, font=labelFont), canvas.stringWidth(string2, font=labelFont))
        canvas.drawString(string1,canvas.size[0] - xRightOffset-d,35*fontZoom,font=labelFont,color=labelColor)
        canvas.drawString(string2,canvas.size[0] - xRightOffset-d,50*fontZoom,font=labelFont,color=labelColor)
        canvas.drawString(string3,canvas.size[0] - xRightOffset-d,65*fontZoom,font=labelFont,color=labelColor)
        if string4 != '':
            canvas.drawString(string4,canvas.size[0] - xRightOffset-d,80*fontZoom,font=labelFont,color=labelColor)
            canvas.drawString("Created at: " + str(datetime.datetime.now()).split('.')[0], canvas.size[0] - xRightOffset-d,95*fontZoom,font=labelFont,color=labelColor)
        else:
            canvas.drawString("Created at: " + str(datetime.datetime.now()).split('.')[0], canvas.size[0] - xRightOffset-d,80*fontZoom,font=labelFont,color=labelColor)

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

        for gIndex, theGO in enumerate(self.geneCol):
            geneNCBILink = 'http://www.ncbi.nlm.nih.gov/gene?term=%s'
            if self.dataset.group.species == "mouse":
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

            elif self.dataset.group.species == "rat":
                exonStarts = []
                exonEnds = []
                txStart = theGO["TxStart"]
                txEnd = theGO["TxEnd"]
                cdsStart = theGO["TxStart"]
                cdsEnd = theGO["TxEnd"]
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
            if self.dataset.group.species == "mouse" or self.dataset.group.species == "rat":
                geneYLocation += 4*self.BAND_HEIGHT + 4*self.BAND_SPACING
            else:
                geneYLocation += 3*self.BAND_HEIGHT + 3*self.BAND_SPACING

            #draw the detail view
            if self.endMb - self.startMb <= self.DRAW_DETAIL_MB and geneEndPix - geneStartPix > self.EACH_GENE_ARROW_SPACING * 3:
                utrColor = pid.Color(0.66, 0.66, 0.66)
                arrowColor = pid.Color(0.7, 0.7, 0.7)

                #draw the line that runs the entire length of the gene
                canvas.drawLine(geneStartPix, geneYLocation + self.EACH_GENE_HEIGHT/2*zoom, geneEndPix, geneYLocation + self.EACH_GENE_HEIGHT/2*zoom, color=outlineColor, width=1)

                #draw the arrows
                if geneEndPix - geneStartPix < 1:
                    genePixRange = 1
                else:
                    genePixRange = int(geneEndPix - geneStartPix)
                for xCoord in range(0, genePixRange):

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
                    #canvas.drawRect(utrStartPix, geneYLocation, utrEndPix, (geneYLocation+self.EACH_GENE_HEIGHT*zoom), edgeColor=utrColor, fillColor =utrColor)

                    if self.endMb - self.startMb <= self.DRAW_UTR_LABELS_MB:
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
                    #canvas.drawRect(utrStartPix, geneYLocation, utrEndPix, (geneYLocation+self.EACH_GENE_HEIGHT*zoom), edgeColor=utrColor, fillColor =utrColor)

                    if self.endMb - self.startMb <= self.DRAW_UTR_LABELS_MB:
                        if strand == "-":
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

        xLeftOffset, xRightOffset, yTopOffset, yBottomOffset = offset
        plotWidth = canvas.size[0] - xLeftOffset - xRightOffset

        yPaddingTop = yTopOffset

        thisTrait = self.this_trait
        _strains, _vals, _vars, _aliases = thisTrait.export_informative()

        smd=[]
        for ii, _val in enumerate(self.vals):
            if _val != "x":
                temp = GeneralObject(name=self.samples[ii], value=float(_val))
                smd.append(temp)
            else:
                continue

        smd.sort(lambda A, B: cmp(A.value, B.value))
        smd.reverse()

        samplelist = list(self.genotype.prgy)

        oldgeneEndPix = -1
        #Initializing plotRight, error before
        plotRight = xRightOffset

#### find out PlotRight
        for _chr in self.genotype:
            if _chr.name == self.ChrList[self.selectedChr][0]:
                for i, _locus in enumerate(_chr):
                    txStart = _chr[i].Mb
                    txEnd   = _chr[i].Mb

                    geneStartPix = xLeftOffset + plotXScale*(float(txStart) - startMb)  - 0
                    geneEndPix = xLeftOffset + plotXScale*(float(txEnd) - startMb) - 0

                    drawit = 1
                    if (geneStartPix < xLeftOffset):
                        drawit = 0;
                    if (geneStartPix > xLeftOffset + plotWidth):
                        drawit = 0;

                    if drawit == 1:
                        if _chr[i].name != " - " :
                            plotRight = geneEndPix + 4

#### end find out PlotRight

        firstGene = 1
        lastGene = 0

        #Sets the length to the length of the strain list. Beforehand, "oldgeno = self.genotype[0][i].genotype"
        #was the only place it was initialized, which worked as long as the very start (startMb = None/0) wasn't being mapped.
        #Now there should always be some value set for "oldgeno" - Zach 12/14/2010
        oldgeno = [None]*len(self.strainlist)

        for i, _chr in enumerate(self.genotype):
            if _chr.name == self.ChrList[self.selectedChr][0]:
                for j, _locus in enumerate(_chr):
                    txStart = _chr[j].Mb
                    txEnd   = _chr[j].Mb

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
                        if self.dataset.group.species == "mouse" or self.dataset.group.species == "rat":
                            geneYLocation += 4*self.BAND_HEIGHT + 4*self.BAND_SPACING
                        else:
                            geneYLocation += 3*self.BAND_HEIGHT + 3*self.BAND_SPACING

                        if _chr[j].name != " - " :

                            if (firstGene == 1) and (lastGene != 1):
                                oldgeneEndPix = drawStart = xLeftOffset
                                oldgeno = _chr[j].genotype
                                continue

                            for k, _geno in enumerate (_chr[j].genotype):
                                plotbxd=0
                                for item in smd:
                                    if item.name == samplelist[k]:
                                        plotbxd=1

                                if (plotbxd == 1):
                                    ind = 0
                                    counter = 0
                                    for item in smd:
                                        counter = counter + 1
                                        if item.name == samplelist[k]:
                                            ind = counter
                                    maxind=max(ind,maxind)

                                    # lines
                                    if (oldgeno[k] == -1 and _geno == -1):
                                        mylineColor = self.HAPLOTYPE_NEGATIVE
                                    elif (oldgeno[k] == 1 and _geno == 1):
                                        mylineColor = self.HAPLOTYPE_POSITIVE
                                    elif (oldgeno[k] == 0 and _geno == 0):
                                        mylineColor = self.HAPLOTYPE_HETEROZYGOUS
                                    else:
                                        mylineColor = self.HAPLOTYPE_RECOMBINATION # XZ: Unknown

                                    canvas.drawLine(drawStart, geneYLocation+7+2*ind*self.EACH_GENE_HEIGHT*zoom, drawEnd, geneYLocation+7+2*ind*self.EACH_GENE_HEIGHT*zoom, color = mylineColor, width=zoom*(self.EACH_GENE_HEIGHT+2))

                                    fillColor=pid.black
                                    outlineColor=pid.black
                                    if lastGene == 0:
                                        canvas.drawRect(geneStartPix, geneYLocation+2*ind*self.EACH_GENE_HEIGHT*zoom, geneEndPix, geneYLocation+2*ind*self.EACH_GENE_HEIGHT+ 2*self.EACH_GENE_HEIGHT*zoom, edgeColor = outlineColor, fillColor = fillColor)


                                    COORDS = "%d, %d, %d, %d" %(geneStartPix, geneYLocation+ind*self.EACH_GENE_HEIGHT, geneEndPix+1, (geneYLocation + ind*self.EACH_GENE_HEIGHT))
                                    TITLE = "Strain: %s, marker (%s) \n Position  %2.3f Mb." % (samplelist[k], _chr[j].name, float(txStart))
                                    HREF = ''
                                    gifmap.areas.append(HT.Area(shape='rect',coords=COORDS,href=HREF, title=TITLE))

                                    # if there are no more markers in a chromosome, the plotRight value calculated above will be before the plotWidth
                                    # resulting in some empty space on the right side of the plot area. This draws an "unknown" bar from plotRight to the edge.
                                    if (plotRight < (xLeftOffset + plotWidth - 3)) and (lastGene == 0):
                                        drawEnd = xLeftOffset + plotWidth - 6
                                        mylineColor = self.HAPLOTYPE_RECOMBINATION
                                        canvas.drawLine(plotRight, geneYLocation+7+2*ind*self.EACH_GENE_HEIGHT*zoom, drawEnd, geneYLocation+7+2*ind*self.EACH_GENE_HEIGHT*zoom, color = mylineColor, width=zoom*(self.EACH_GENE_HEIGHT+2))


                            if lastGene == 0:
                                canvas.drawString("%s" % (_chr[j].name), geneStartPix , geneYLocation+17+2*maxind*self.EACH_GENE_HEIGHT*zoom, font=pid.Font(ttf="verdana", size=12, bold=0), color=pid.black, angle=-90)

                            oldgeneEndPix = geneEndPix;
                            oldgeno = _chr[j].genotype
                            firstGene = 0
                        else:
                            lastGene = 0

        for i, _chr in enumerate(self.genotype):
            if _chr.name == self.ChrList[self.selectedChr][0]:
                for j, _geno in enumerate(_chr[1]):

                    plotbxd=0
                    for item in smd:
                        if item.name == samplelist[j]:
                            plotbxd=1

                    if (plotbxd == 1):

                        ind = 0
                        counter = 0
                        expr = 0
                        for item in smd:
                            counter = counter + 1
                            if item.name == samplelist[j]:
                                ind = counter
                                expr = item.value

                        # Place where font is hardcoded
                        canvas.drawString("%s" % (samplelist[j]), (xLeftOffset + plotWidth + 10) , geneYLocation+8+2*ind*self.EACH_GENE_HEIGHT*zoom, font=pid.Font(ttf="verdana", size=12, bold=0), color=pid.black)
                        canvas.drawString("%2.2f" % (expr), (xLeftOffset + plotWidth + 60) , geneYLocation+8+2*ind*self.EACH_GENE_HEIGHT*zoom, font=pid.Font(ttf="verdana", size=12, bold=0), color=pid.black)

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
        if self.dataset.group.species == "mouse" or self.dataset.group.species == "rat":
            phenogenPaddingTop = paddingTop + (self.BAND_HEIGHT + self.BAND_SPACING)
            ucscPaddingTop = paddingTop + 2*(self.BAND_HEIGHT + self.BAND_SPACING)
            ensemblPaddingTop = paddingTop + 3*(self.BAND_HEIGHT + self.BAND_SPACING)
        else:
            ucscPaddingTop = paddingTop + (self.BAND_HEIGHT + self.BAND_SPACING)
            ensemblPaddingTop = paddingTop + 2*(self.BAND_HEIGHT + self.BAND_SPACING)

        if zoom == 1:
            for pixel in range(xLeftOffset, xLeftOffset + plotWidth, pixelStep):

                calBase = self.kONE_MILLION*(startMb + (endMb-startMb)*(pixel-xLeftOffset-0.0)/plotWidth)
                if pixel == (xLeftOffset + pixelStep*2):
                  logger.debug("CALBASE:", calBase)
                  logger.debug("FLANKING:", flankingWidthInBases)

                xBrowse1 = pixel
                xBrowse2 = min(xLeftOffset + plotWidth, (pixel + pixelStep - 1))

                WEBQTL_COORDS = "%d, %d, %d, %d" % (xBrowse1, paddingTop, xBrowse2, (paddingTop+self.BAND_HEIGHT))
                WEBQTL_HREF = "javascript:rangeView('%s', %f, %f)" % (self.selectedChr - 1, max(0, (calBase-webqtlZoomWidth))/1000000.0, (calBase+webqtlZoomWidth)/1000000.0)

                WEBQTL_TITLE = "Click to view this section of the genome in WebQTL"
                gifmap.areas.append(HT.Area(shape='rect',coords=WEBQTL_COORDS,href=WEBQTL_HREF, title=WEBQTL_TITLE))
                canvas.drawRect(xBrowse1, paddingTop, xBrowse2, (paddingTop + self.BAND_HEIGHT), edgeColor=self.CLICKABLE_WEBQTL_REGION_COLOR, fillColor=self.CLICKABLE_WEBQTL_REGION_COLOR)
                canvas.drawLine(xBrowse1, paddingTop, xBrowse1, (paddingTop + self.BAND_HEIGHT), color=self.CLICKABLE_WEBQTL_REGION_OUTLINE_COLOR)

                if self.dataset.group.species == "mouse" or self.dataset.group.species == "rat":
                    PHENOGEN_COORDS = "%d, %d, %d, %d" % (xBrowse1, phenogenPaddingTop, xBrowse2, (phenogenPaddingTop+self.BAND_HEIGHT))
                    if self.dataset.group.species == "mouse":
                        PHENOGEN_HREF = "https://phenogen.org/PhenoGen/gene.jsp?speciesCB=Mm&auto=Y&geneTxt=chr%s:%d-%d&genomeVer=mm10" % (self.selectedChr, max(0, calBase-flankingWidthInBases), calBase+flankingWidthInBases)
                    else:
                        PHENOGEN_HREF = "https://phenogen.org/PhenoGen/gene.jsp?speciesCB=Mm&auto=Y&geneTxt=chr%s:%d-%d&genomeVer=mm10" % (self.selectedChr, max(0, calBase-flankingWidthInBases), calBase+flankingWidthInBases)
                    PHENOGEN_TITLE = "Click to view this section of the genome in PhenoGen"
                    gifmap.areas.append(HT.Area(shape='rect',coords=PHENOGEN_COORDS,href=PHENOGEN_HREF, title=PHENOGEN_TITLE))
                    canvas.drawRect(xBrowse1, phenogenPaddingTop, xBrowse2, (phenogenPaddingTop+self.BAND_HEIGHT), edgeColor=self.CLICKABLE_PHENOGEN_REGION_COLOR, fillColor=self.CLICKABLE_PHENOGEN_REGION_COLOR)
                    canvas.drawLine(xBrowse1, phenogenPaddingTop, xBrowse1, (phenogenPaddingTop+self.BAND_HEIGHT), color=self.CLICKABLE_PHENOGEN_REGION_OUTLINE_COLOR)

                UCSC_COORDS = "%d, %d, %d, %d" %(xBrowse1, ucscPaddingTop, xBrowse2, (ucscPaddingTop+self.BAND_HEIGHT))
                if self.dataset.group.species == "mouse":
                    UCSC_HREF = "http://genome.ucsc.edu/cgi-bin/hgTracks?db=%s&position=chr%s:%d-%d&hgt.customText=%s/snp/chr%s" % (self._ucscDb, self.selectedChr, max(0, calBase-flankingWidthInBases), calBase+flankingWidthInBases, webqtlConfig.PORTADDR, self.selectedChr)
                else:
                    UCSC_HREF = "http://genome.ucsc.edu/cgi-bin/hgTracks?db=%s&position=chr%s:%d-%d" % (self._ucscDb, self.selectedChr, max(0, calBase-flankingWidthInBases), calBase+flankingWidthInBases)
                UCSC_TITLE = "Click to view this section of the genome in the UCSC Genome Browser"
                gifmap.areas.append(HT.Area(shape='rect',coords=UCSC_COORDS,href=UCSC_HREF, title=UCSC_TITLE))
                canvas.drawRect(xBrowse1, ucscPaddingTop, xBrowse2, (ucscPaddingTop+self.BAND_HEIGHT), edgeColor=self.CLICKABLE_UCSC_REGION_COLOR, fillColor=self.CLICKABLE_UCSC_REGION_COLOR)
                canvas.drawLine(xBrowse1, ucscPaddingTop, xBrowse1, (ucscPaddingTop+self.BAND_HEIGHT), color=self.CLICKABLE_UCSC_REGION_OUTLINE_COLOR)

                ENSEMBL_COORDS = "%d, %d, %d, %d" %(xBrowse1, ensemblPaddingTop, xBrowse2, (ensemblPaddingTop+self.BAND_HEIGHT))
                if self.dataset.group.species == "mouse":
                    ENSEMBL_HREF = "http://www.ensembl.org/Mus_musculus/contigview?highlight=&chr=%s&vc_start=%d&vc_end=%d&x=35&y=12" % (self.selectedChr, max(0, calBase-flankingWidthInBases), calBase+flankingWidthInBases)
                else:
                    ENSEMBL_HREF = "http://www.ensembl.org/Rattus_norvegicus/contigview?chr=%s&start=%d&end=%d" % (self.selectedChr, max(0, calBase-flankingWidthInBases), calBase+flankingWidthInBases)
                ENSEMBL_TITLE = "Click to view this section of the genome in the Ensembl Genome Browser"
                gifmap.areas.append(HT.Area(shape='rect',coords=ENSEMBL_COORDS,href=ENSEMBL_HREF, title=ENSEMBL_TITLE))
                canvas.drawRect(xBrowse1, ensemblPaddingTop, xBrowse2, (ensemblPaddingTop+self.BAND_HEIGHT), edgeColor=self.CLICKABLE_ENSEMBL_REGION_COLOR, fillColor=self.CLICKABLE_ENSEMBL_REGION_COLOR)
                canvas.drawLine(xBrowse1, ensemblPaddingTop, xBrowse1, (ensemblPaddingTop+self.BAND_HEIGHT), color=self.CLICKABLE_ENSEMBL_REGION_OUTLINE_COLOR)
            # end for

            canvas.drawString("Click to view the corresponding section of the genome in an 8x expanded WebQTL map", (xLeftOffset + 10), paddingTop + self.BAND_HEIGHT/2, font=clickableRegionLabelFont, color=self.CLICKABLE_WEBQTL_TEXT_COLOR)
            if self.dataset.group.species == "mouse" or self.dataset.group.species == "rat":
                canvas.drawString("Click to view the corresponding section of the genome in PhenoGen", (xLeftOffset + 10), phenogenPaddingTop + self.BAND_HEIGHT/2, font=clickableRegionLabelFont, color=self.CLICKABLE_PHENOGEN_TEXT_COLOR)
            canvas.drawString("Click to view the corresponding section of the genome in the UCSC Genome Browser", (xLeftOffset + 10), ucscPaddingTop + self.BAND_HEIGHT/2, font=clickableRegionLabelFont, color=self.CLICKABLE_UCSC_TEXT_COLOR)
            canvas.drawString("Click to view the corresponding section of the genome in the Ensembl Genome Browser", (xLeftOffset+10), ensemblPaddingTop + self.BAND_HEIGHT/2, font=clickableRegionLabelFont, color=self.CLICKABLE_ENSEMBL_TEXT_COLOR)

            #draw the gray text
            chrFont = pid.Font(ttf="verdana", size=26*zoom, bold=1)
            traitFont = pid.Font(ttf="verdana", size=14, bold=0)
            chrX = xLeftOffset + plotWidth - 2 - canvas.stringWidth("Chr %s" % self.ChrList[self.selectedChr][0], font=chrFont)
            canvas.drawString("Chr %s" % self.ChrList[self.selectedChr][0], chrX, ensemblPaddingTop-5, font=chrFont, color=pid.gray)
            # end of drawBrowserClickableRegions
        else:
            #draw the gray text
            chrFont = pid.Font(ttf="verdana", size=26*zoom, bold=1)
            traitFont = pid.Font(ttf="verdana", size=14, bold=0)
            chrX = xLeftOffset + (plotWidth - canvas.stringWidth("Chr %s" % currentChromosome, font=chrFont))/2
            canvas.drawString("Chr %s" % currentChromosome, chrX, 32, font=chrFont, color=pid.gray)
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

        if self.plotScale == 'physic':
            strYLoc = yZero + spacingFromLabelToAxis + canvas.fontHeight(MBLabelFont)
            ###Physical single chromosome view
            if self.selectedChr > -1:
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
                    for j, tickdists in enumerate(range(distScale, int(ceil(distLen)), distScale)):
                        canvas.drawLine(startPosX + tickdists*plotXScale, yZero, startPosX + tickdists*plotXScale, yZero + 7, color=pid.black, width=1*zoom)
                        if j % 2 == 0:
                            canvas.drawString(str(tickdists), startPosX+tickdists*plotXScale, yZero + 10*zoom, color=pid.black, font=MBLabelFont, angle=270)
                    startPosX +=  (self.ChrLengthDistList[i]+self.GraphInterval)*plotXScale

            megabaseLabelFont = pid.Font(ttf="verdana", size=18*zoom*1.5, bold=0)
            canvas.drawString("Megabases", xLeftOffset + (plotWidth - canvas.stringWidth("Megabases", font=megabaseLabelFont))/2,
                    strYLoc + canvas.fontHeight(MBLabelFont)+ 10*(zoom%2) + 10, font=megabaseLabelFont, color=pid.black)
            pass
        else:
            strYLoc = yZero + spacingFromLabelToAxis + canvas.fontHeight(MBLabelFont) + 8
            ChrAInfo = []
            preLpos = -1
            distinctCount = 0.0

            if self.selectedChr == -1: #ZS: If viewing full genome/all chromosomes
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
                    if _chr.name == self.ChrList[self.selectedChr][0]:
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
                    HREF="/show_trait?trait_id=%s&dataset=%s" % (Lname, self.dataset.group.name+"Geno")
                    #HREF="javascript:showDatabase3('%s','%s','%s','');" % (showLocusForm,fd.RISet+"Geno", Lname)
                    Areas=HT.Area(shape='rect', coords=COORDS, href=HREF, target="_blank", title="Locus : " + Lname)
                    gifmap.areas.append(Areas)
                ##piddle bug
                if j == 0:
                    canvas.drawLine(startPosX,yZero,startPosX,yZero+40, color=lineColor)
                startPosX += (self.ChrLengthDistList[j]+self.GraphInterval)*plotXScale

            centimorganLabelFont = pid.Font(ttf="verdana", size=18*zoom*1.5, bold=0)
            canvas.drawString("Centimorgans", xLeftOffset + (plotWidth - canvas.stringWidth("Megabases", font=centimorganLabelFont))/2,
                    strYLoc + canvas.fontHeight(MBLabelFont)+ 10*(zoom%2) + 10, font=centimorganLabelFont, color=pid.black)

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
        #If so, we need to compute the maximum LRS value to determine where the max y-value should be, and call this LRS_LOD_Max.
        #LRSTop is then defined to be above the LRS_LOD_Max by enough to add one additional LRSScale increment.
        #if we are using a set-scale, then we set LRSTop to be the user's value, and LRS_LOD_Max doesn't matter.

        #ZS: This is a mess, but I don't know a better way to account for different mapping methods returning results in different formats + the option to change between LRS and LOD
        if self.lrsMax <= 0:  #sliding scale
            if "lrs_value" in self.qtlresults[0]:
                LRS_LOD_Max = max([result['lrs_value'] for result in self.qtlresults])
                if self.LRS_LOD == "LOD" or self.LRS_LOD == "-log(p)":
                    LRS_LOD_Max = LRS_LOD_Max / self.LODFACTOR
                    if self.permChecked and self.nperm > 0 and not self.multipleInterval:
                        self.significant = min(self.significant / self.LODFACTOR, webqtlConfig.MAXLRS)
                        self.suggestive = min(self.suggestive / self.LODFACTOR, webqtlConfig.MAXLRS)
                else:
                    if self.permChecked and self.nperm > 0 and not self.multipleInterval:
                        self.significant = min(self.significant, webqtlConfig.MAXLRS)
                        self.suggestive = min(self.suggestive, webqtlConfig.MAXLRS)
                    else:
                        pass
            else:
                LRS_LOD_Max = max([result['lod_score'] for result in self.qtlresults])
                if self.LRS_LOD == "LRS":
                    LRS_LOD_Max = LRS_LOD_Max * self.LODFACTOR
                    if self.permChecked and self.nperm > 0 and not self.multipleInterval:
                        self.significant = min(self.significant * self.LODFACTOR, webqtlConfig.MAXLRS)
                        self.suggestive = min(self.suggestive * self.LODFACTOR, webqtlConfig.MAXLRS)
                else:
                    if self.permChecked and self.nperm > 0 and not self.multipleInterval:
                        self.significant = min(self.significant, webqtlConfig.MAXLRS)
                        self.suggestive = min(self.suggestive, webqtlConfig.MAXLRS)
                    else:
                        pass

            if self.permChecked and self.nperm > 0 and not self.multipleInterval:
                LRS_LOD_Max = max(self.significant, LRS_LOD_Max)
            else:
                LRS_LOD_Max = 1.15*LRS_LOD_Max

            #genotype trait will give infinite LRS
            LRS_LOD_Max = min(LRS_LOD_Max, webqtlConfig.MAXLRS)
        else:
            LRS_LOD_Max = self.lrsMax

        #ZS: Needed to pass to genome browser
        js_data = json.loads(self.js_data)
        if self.LRS_LOD == "LRS":
            js_data['max_score'] = LRS_LOD_Max/4.61
        else:
            js_data['max_score'] = LRS_LOD_Max
        self.js_data = json.dumps(js_data)

        if LRS_LOD_Max > 100:
            LRSScale = 20.0
        elif LRS_LOD_Max > 20:
            LRSScale = 5.0
        elif LRS_LOD_Max > 7.5:
            LRSScale = 2.5
        else:
            LRSScale = 1.0

        LRSAxisList = Plot.frange(LRSScale, LRS_LOD_Max, LRSScale)
        #make sure the user's value appears on the y-axis
        #update by NL 6-21-2011: round the LOD value to 100 when LRS_LOD_Max is equal to 460
        LRSAxisList.append(round(LRS_LOD_Max))

        #draw the "LRS" or "LOD" string to the left of the axis
        LRSScaleFont=pid.Font(ttf="verdana", size=16*zoom, bold=0)
        LRSLODFont=pid.Font(ttf="verdana", size=18*zoom*1.5, bold=0)
        yZero = yTopOffset + plotHeight

        canvas.drawString(self.LRS_LOD, xLeftOffset - canvas.stringWidth("999.99", font=LRSScaleFont) - 15*(zoom-1), \
                                          yZero - 150 - 300*(zoom - 1), font=LRSLODFont, color=pid.black, angle=90)

        for item in LRSAxisList:
            if LRS_LOD_Max == 0.0:
                LRS_LOD_Max = 0.000001
            yLRS = yZero - (item/LRS_LOD_Max) * LRSHeightThresh
            canvas.drawLine(xLeftOffset, yLRS, xLeftOffset - 4, yLRS, color=self.LRS_COLOR, width=1*zoom)
            scaleStr = "%2.1f" % item
            #Draw the LRS/LOD Y axis label
            canvas.drawString(scaleStr, xLeftOffset-4-canvas.stringWidth(scaleStr, font=LRSScaleFont)-5, yLRS+3, font=LRSScaleFont, color=self.LRS_COLOR)

        if self.permChecked and self.nperm > 0 and not self.multipleInterval:
            significantY = yZero - self.significant*LRSHeightThresh/LRS_LOD_Max
            suggestiveY = yZero - self.suggestive*LRSHeightThresh/LRS_LOD_Max
            startPosX = xLeftOffset

            #"Significant" and "Suggestive" Drawing Routine
            # ======= Draw the thick lines for "Significant" and "Suggestive" =====  (crowell: I tried to make the SNPs draw over these lines, but piddle wouldn't have it...)

            #ZS: I don't know if what I did here with this inner function is clever or overly complicated, but it's the only way I could think of to avoid duplicating the code inside this function
            def add_suggestive_significant_lines_and_legend(start_pos_x, chr_length_dist):
                rightEdge = int(start_pos_x + chr_length_dist*plotXScale - self.SUGGESTIVE_WIDTH/1.5)
                canvas.drawLine(start_pos_x+self.SUGGESTIVE_WIDTH/1.5, suggestiveY, rightEdge, suggestiveY, color=self.SUGGESTIVE_COLOR,
                        width=self.SUGGESTIVE_WIDTH*zoom, clipX=(xLeftOffset, xLeftOffset + plotWidth-2))
                canvas.drawLine(start_pos_x+self.SUGGESTIVE_WIDTH/1.5, significantY, rightEdge, significantY, color=self.SIGNIFICANT_COLOR,
                        width=self.SIGNIFICANT_WIDTH*zoom, clipX=(xLeftOffset, xLeftOffset + plotWidth-2))
                sugg_coords = "%d, %d, %d, %d" % (start_pos_x, suggestiveY-2, rightEdge + 2*zoom, suggestiveY+2)
                sig_coords = "%d, %d, %d, %d" % (start_pos_x, significantY-2, rightEdge + 2*zoom, significantY+2)
                if self.LRS_LOD == 'LRS':
                    sugg_title = "Suggestive LRS = %0.2f" % self.suggestive
                    sig_title = "Significant LRS = %0.2f" % self.significant
                else:
                    sugg_title = "Suggestive LOD = %0.2f" % (self.suggestive/4.61)
                    sig_title = "Significant LOD = %0.2f" % (self.significant/4.61)
                Areas1 = HT.Area(shape='rect',coords=sugg_coords,title=sugg_title)
                Areas2 = HT.Area(shape='rect',coords=sig_coords,title=sig_title)
                gifmap.areas.append(Areas1)
                gifmap.areas.append(Areas2)

                start_pos_x +=  (chr_length_dist+self.GraphInterval)*plotXScale
                return start_pos_x

            for i, _chr in enumerate(self.genotype):
                if self.selectedChr != -1:
                    if _chr.name == self.ChrList[self.selectedChr][0]:
                        startPosX = add_suggestive_significant_lines_and_legend(startPosX, self.ChrLengthDistList[0])
                        break
                    else:
                        continue
                else:
                    startPosX = add_suggestive_significant_lines_and_legend(startPosX, self.ChrLengthDistList[i])

        if self.multipleInterval:
            lrsEdgeWidth = 1
        else:
            if self.additiveChecked:
                additiveMax = max(map(lambda X : abs(X['additive']), self.qtlresults))
            lrsEdgeWidth = 2

        if zoom == 2:
            lrsEdgeWidth = 2 * lrsEdgeWidth

        LRSCoordXY = []
        AdditiveCoordXY = []
        DominanceCoordXY = []

        symbolFont = pid.Font(ttf="fnt_bs", size=5,bold=0) #ZS: For Manhattan Plot

        previous_chr = 1
        previous_chr_as_int = 0
        lineWidth = 1
        oldStartPosX = 0
        startPosX = xLeftOffset
        for i, qtlresult in enumerate(self.qtlresults):
            m = 0
            thisLRSColor = self.colorCollection[0]
            if qtlresult['chr'] != previous_chr and self.selectedChr == -1:
                if self.manhattan_plot != True:
                    canvas.drawPolygon(LRSCoordXY,edgeColor=thisLRSColor,closed=0, edgeWidth=lrsEdgeWidth, clipX=(xLeftOffset, xLeftOffset + plotWidth))

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

                LRSCoordXY = []
                AdditiveCoordXY = []
                previous_chr = qtlresult['chr']
                previous_chr_as_int += 1
                newStartPosX = (self.ChrLengthDistList[previous_chr_as_int - 1]+self.GraphInterval)*plotXScale
                if newStartPosX != oldStartPosX:
                    startPosX += newStartPosX
                    oldStartPosX = newStartPosX

            #ZS: This is beause the chromosome value stored in qtlresult['chr'] can be (for example) either X or 20 depending upon the mapping method/scale used
            if self.plotScale == "physic":
                this_chr = str(self.ChrList[self.selectedChr][0])
            else:
                this_chr = str(self.ChrList[self.selectedChr][1]+1)
            if self.selectedChr == -1 or str(qtlresult['chr']) == this_chr:
                Xc = startPosX + (qtlresult['Mb']-startMb)*plotXScale
                # updated by NL 06-18-2011:
                # fix the over limit LRS graph issue since genotype trait may give infinite LRS;
                # for any lrs is over than 460(LRS max in this system), it will be reset to 460
                if 'lrs_value' in qtlresult:
                    if self.LRS_LOD == "LOD" or self.LRS_LOD == "-log(p)":
                        if qtlresult['lrs_value'] > 460 or qtlresult['lrs_value']=='inf':
                            Yc = yZero - webqtlConfig.MAXLRS*LRSHeightThresh/(LRS_LOD_Max*self.LODFACTOR)
                        else:
                            Yc = yZero - qtlresult['lrs_value']*LRSHeightThresh/(LRS_LOD_Max*self.LODFACTOR)
                    else:
                        if qtlresult['lrs_value'] > 460 or qtlresult['lrs_value']=='inf':
                            Yc = yZero - webqtlConfig.MAXLRS*LRSHeightThresh/LRS_LOD_Max
                        else:
                            Yc = yZero - qtlresult['lrs_value']*LRSHeightThresh/LRS_LOD_Max
                else:
                    if qtlresult['lod_score'] > 100 or qtlresult['lod_score']=='inf':
                        Yc = yZero - webqtlConfig.MAXLRS*LRSHeightThresh/LRS_LOD_Max
                    else:
                        if self.LRS_LOD == "LRS":
                            Yc = yZero - qtlresult['lod_score']*self.LODFACTOR*LRSHeightThresh/LRS_LOD_Max
                        else:
                            Yc = yZero - qtlresult['lod_score']*LRSHeightThresh/LRS_LOD_Max

                if self.manhattan_plot == True:
                    if self.selectedChr == -1 and (previous_chr_as_int % 2 == 1):
                        point_color = pid.red
                    else:
                        point_color = pid.blue

                    final_x_pos = Xc-canvas.stringWidth("5",font=symbolFont)/2+1
                    if final_x_pos > (xLeftOffset + plotWidth):
                        continue
                        #break ZS: This is temporary until issue with sorting for GEMMA is fixed
                    elif final_x_pos < xLeftOffset:
                        continue
                    else:
                        canvas.drawString("5", final_x_pos,Yc+2,color=point_color, font=symbolFont)
                else:
                    LRSCoordXY.append((Xc, Yc))

                if not self.multipleInterval and self.additiveChecked:
                   if additiveMax == 0.0:
                       additiveMax = 0.000001
                   Yc = yZero - qtlresult['additive']*AdditiveHeightThresh/additiveMax
                   AdditiveCoordXY.append((Xc, Yc))

                m += 1

        if self.manhattan_plot != True:
            canvas.drawPolygon(LRSCoordXY,edgeColor=thisLRSColor,closed=0, edgeWidth=lrsEdgeWidth, clipX=(xLeftOffset, xLeftOffset + plotWidth))

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


        ###draw additive scale
        if not self.multipleInterval and self.additiveChecked:
            additiveScaleFont=pid.Font(ttf="verdana",size=16*zoom,bold=0)
            additiveScale = Plot.detScaleOld(0,additiveMax)
            additiveStep = (additiveScale[1]-additiveScale[0])/additiveScale[2]
            additiveAxisList = Plot.frange(0, additiveScale[1], additiveStep)
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

            drawRegionDistance = self.ChrLengthDistList[self.ChrList[self.selectedChr][1]]
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

    def drawPermutationHistogram(self):
        #########################################
        #      Permutation Graph
        #########################################
        myCanvas = pid.PILCanvas(size=(400,300))
        if 'lod_score' in self.qtlresults[0] and self.LRS_LOD == "LRS":
            perm_output = [value*4.61 for value in self.perm_output]
        elif 'lod_score' not in self.qtlresults[0] and self.LRS_LOD == "LOD":
            perm_output = [value/4.61 for value in self.perm_output]
        else:
            perm_output = self.perm_output

        Plot.plotBar(myCanvas, perm_output, XLabel=self.LRS_LOD, YLabel='Frequency', title=' Histogram of Permutation Test')
        filename= webqtlUtil.genRandStr("Reg_")
        myCanvas.save(GENERATED_IMAGE_DIR+filename, format='gif')

        return filename

    def geneTable(self, geneCol, refGene=None):
        if self.dataset.group.species == 'mouse' or self.dataset.group.species == 'rat':
            self.gene_table_header = self.getGeneTableHeaderList(refGene=None)
            self.gene_table_body = self.getGeneTableBody(geneCol, refGene=None)
        else:
            self.gene_table_header = None
            self.gene_table_body = None

    def getGeneTableHeaderList(self, refGene=None):

        gene_table_header_list = []
        if self.dataset.group.species == "mouse":
            if refGene:
                gene_table_header_list = ["Index",
                                               "Symbol",
                                               "Mb Start",
                                               "Length (Kb)",
                                               "SNP Count",
                                               "SNP Density",
                                               "Avg Expr",
                                               "Human Chr",
                                               "Mb Start (hg19)",
                                               "Literature Correlation",
                                               "Gene Description"]
            else:
                gene_table_header_list = ["",
                                          "Index",
                                          "Symbol",
                                          "Mb Start",
                                          "Length (Kb)",
                                          "SNP Count",
                                          "SNP Density",
                                          "Avg Expr",
                                          "Human Chr",
                                          "Mb Start (hg19)",
                                          "Gene Description"]
        elif self.dataset.group.species == "rat":
            gene_table_header_list = ["",
                                      "Index",
                                      "Symbol",
                                      "Mb Start",
                                      "Length (Kb)",
                                      "Avg Expr",
                                      "Mouse Chr",
                                      "Mb Start (mm9)",
                                      "Human Chr",
                                      "Mb Start (hg19)",
                                      "Gene Description"]

        return gene_table_header_list

    def getGeneTableBody(self, geneCol, refGene=None):
        gene_table_body = []

        tableIterationsCnt = 0
        if self.dataset.group.species == "mouse":
            for gIndex, theGO in enumerate(geneCol):

                tableIterationsCnt = tableIterationsCnt + 1

                this_row = [] #container for the cells of each row
                selectCheck = HT.Input(type="checkbox", name="selectCheck", value=theGO["GeneSymbol"], Class="checkbox trait_checkbox") #checkbox for each row

                geneLength = (theGO["TxEnd"] - theGO["TxStart"])*1000.0
                tenPercentLength = geneLength*0.0001
                txStart = theGO["TxStart"]
                txEnd = theGO["TxEnd"]
                theGO["snpDensity"] = theGO["snpCount"]/geneLength
                if self.ALEX_DEBUG_BOOL_PRINT_GENE_LIST:
                    geneIdString = 'http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?db=gene&cmd=Retrieve&dopt=Graphics&list_uids=%s' % theGO["GeneID"]

                    if theGO["snpCount"]:
                        snpString = HT.Href(url="http://genenetwork.org/webqtl/main.py?FormID=snpBrowser&chr=%s&start=%s&end=%s&geneName=%s&s1=%d&s2=%d" % (theGO["Chromosome"],
                                theGO["TxStart"], theGO["TxEnd"], theGO["GeneSymbol"], self.diffCol[0], self.diffCol[1]),
                                text=theGO["snpCount"], target="_blank", Class="normalsize")
                    else:
                        snpString = 0

                    mouseStartString = "http://genome.ucsc.edu/cgi-bin/hgTracks?clade=vertebrate&org=Mouse&db=mm9&position=chr" + theGO["Chromosome"] + "%3A" + str(int(theGO["TxStart"] * 1000000.0))  + "-" + str(int(theGO["TxEnd"]*1000000.0)) +"&pix=620&Submit=submit"

                    #the chromosomes for human 1 are 1qXX.XX
                    if theGO['humanGene']:
                        if theGO['humanGene']["TxStart"] == '':
                            humanStartDisplay = ""
                        else:
                            humanStartDisplay = "%0.6f" % theGO['humanGene']["TxStart"]

                        humanChr = theGO['humanGene']["Chromosome"]
                        humanTxStart = theGO['humanGene']["TxStart"]

                        humanStartString = "http://genome.ucsc.edu/cgi-bin/hgTracks?clade=vertebrate&org=Human&db=hg17&position=chr%s:%d-%d" %  (humanChr, int(1000000*theGO['humanGene']["TxStart"]), int(1000000*theGO['humanGene']["TxEnd"]))
                    else:
                        humanStartString = humanChr = humanStartDisplay = "--"

                    geneDescription = theGO["GeneDescription"]
                    if len(geneDescription) > 70:
                        geneDescription = geneDescription[:70]+"..."

                    if theGO["snpDensity"] < 0.000001:
                        snpDensityStr = "0"
                    else:
                        snpDensityStr = "%0.6f" % theGO["snpDensity"]

                    avgExpr = [] #theGO["avgExprVal"]
                    if avgExpr in ([], None):
                        avgExpr = "--"
                    else:
                        avgExpr = "%0.6f" % avgExpr

                    # If we have a referenceGene then we will show the Literature Correlation
                    if theGO["Chromosome"] == "X":
                        chr_as_int = 19
                    else:
                        chr_as_int = int(theGO["Chromosome"]) - 1
                    if refGene:
                        literatureCorrelationString = str(self.getLiteratureCorrelation(self.cursor,refGene,theGO['GeneID']) or "N/A")

                        this_row = [selectCheck.__str__(),
                                    str(tableIterationsCnt),
                                    HT.Href(geneIdString, theGO["GeneSymbol"], target="_blank").__str__(),
                                    HT.Href(mouseStartString, "%0.6f" % txStart, target="_blank").__str__(),
                                    HT.Href("javascript:rangeView('%s', %f, %f)" % (str(chr_as_int), txStart-tenPercentLength, txEnd+tenPercentLength), "%0.3f" % geneLength).__str__(),
                                    snpString,
                                    snpDensityStr,
                                    avgExpr,
                                    humanChr,
                                    HT.Href(humanStartString, humanStartDisplay, target="_blank").__str__(),
                                    literatureCorrelationString,
                                    geneDescription]
                    else:
                        this_row = [selectCheck.__str__(),
                                    str(tableIterationsCnt),
                                    HT.Href(geneIdString, theGO["GeneSymbol"], target="_blank").__str__(),
                                    HT.Href(mouseStartString, "%0.6f" % txStart, target="_blank").__str__(),
                                    HT.Href("javascript:rangeView('%s', %f, %f)" % (str(chr_as_int), txStart-tenPercentLength, txEnd+tenPercentLength), "%0.3f" % geneLength).__str__(),
                                    snpString,
                                    snpDensityStr,
                                    avgExpr,
                                    humanChr,
                                    HT.Href(humanStartString, humanStartDisplay, target="_blank").__str__(),
                                    geneDescription]

                gene_table_body.append(this_row)

        elif self.dataset.group.species == 'rat':
            for gIndex, theGO in enumerate(geneCol):
                this_row = [] #container for the cells of each row
                selectCheck = HT.Input(type="checkbox", name="selectCheck", Class="checkbox trait_checkbox").__str__() #checkbox for each row

                #ZS: May want to get this working again later
                #webqtlSearch = HT.Href(os.path.join(webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE)+"?cmd=sch&gene=%s&alias=1&species=rat" % theGO["GeneSymbol"], ">>", target="_blank").__str__()

                if theGO["GeneID"] != "":
                    geneSymbolNCBI = HT.Href("http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?db=gene&cmd=Retrieve&dopt=Graphics&list_uids=%s" % theGO["GeneID"], theGO["GeneSymbol"], Class="normalsize", target="_blank").__str__()
                else:
                    geneSymbolNCBI = theGO["GeneSymbol"]

                if theGO["Chromosome"] == "X":
                    chr_as_int = 20
                else:
                    chr_as_int = int(theGO["Chromosome"]) - 1

                geneLength = (float(theGO["TxEnd"]) - float(theGO["TxStart"]))
                geneLengthURL = "javascript:rangeView('%s', %f, %f)" % (theGO["Chromosome"], float(theGO["TxStart"])-(geneLength*0.1), float(theGO["TxEnd"])+(geneLength*0.1))

                avgExprVal = []
                if avgExprVal != "" and avgExprVal:
                    avgExprVal = "%0.5f" % float(avgExprVal)
                else:
                    avgExprVal = ""

                #Mouse Gene
                if theGO['mouseGene']:
                    mouseChr = theGO['mouseGene']["Chromosome"]
                    mouseTxStart = "%0.6f" % theGO['mouseGene']["TxStart"]
                else:
                    mouseChr = mouseTxStart = ""

                #the chromosomes for human 1 are 1qXX.XX
                if theGO['humanGene']:
                    humanChr = theGO['humanGene']["Chromosome"]
                    humanTxStart = "%0.6f" % theGO['humanGene']["TxStart"]
                else:
                    humanChr = humanTxStart = ""

                geneDesc = theGO["GeneDescription"]
                if geneDesc == "---":
                    geneDesc = ""

                this_row = [selectCheck.__str__(),
                            str(gIndex+1),
                            geneSymbolNCBI,
                            "%0.6f" % theGO["TxStart"],
                            HT.Href(geneLengthURL, "%0.3f" % (geneLength*1000.0)).__str__(),
                            avgExprVal,
                            mouseChr,
                            mouseTxStart,
                            humanChr,
                            humanTxStart,
                            geneDesc]

                gene_table_body.append(this_row)

        return gene_table_body

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