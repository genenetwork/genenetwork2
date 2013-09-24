from __future__ import absolute_import, print_function, division

from base.trait import GeneralTrait
from base import data_set  #import create_dataset

from pprint import pformat as pf

import string
import sys
import os
import collections

import numpy as np
from scipy import linalg

import simplejson as json

#from redis import Redis


from base.trait import GeneralTrait
from base import data_set
from base import species
from base import webqtlConfig
from wqflask.my_pylmm.data import prep_data
from wqflask.my_pylmm.pyLMM import lmm
from wqflask.my_pylmm.pyLMM import input
from utility import helper_functions
from utility import Plot, Bunch
from utility import temp_data

from utility.benchmark import Bench


class IntervalMapping(object):

    def __init__(self, start_vars, temp_uuid):

        #Currently only getting trait data for one trait, but will need
        #to change this to accept multiple traits once the collection page is implemented
        helper_functions.get_species_dataset_trait(self, start_vars)

        tempdata = temp_data.TempData(temp_uuid)
        
        self.samples = [] # Want only ones with values
        self.vals = []

        for sample in self.dataset.group.samplelist:
            value = start_vars['value:' + sample]
            self.samples.append(str(sample))
            self.vals.append(value)
 
        self.set_options(start_vars)
 
        self.gen_data(tempdata)

        #Get chromosome lengths for drawing the interval map plot
        chromosome_mb_lengths = {}
        for key in self.species.chromosomes.chromosomes.keys():
            chromosome_mb_lengths[key] = self.species.chromosomes.chromosomes[key].mb_length
        
        self.js_data = dict(
            chromosomes = chromosome_mb_lengths,
            qtl_results = self.qtl_results,
        )

    def get_qtl_results(self):
        """Gets the LOD (or LRS) score at each marker in order do the qtl mapping"""
        
        
        #INTERCROSS = (self.genotype.type=="intercross")

        #THESE ARE OLD COMMENTS
        #draw the LRS scale
        #We first determine whether or not we are using a sliding scale.
        #If so, we need to compute the maximum LRS value to determine where the max y-value should be, and call this LRSMax.
        #LRSTop is then defined to be above the LRSMax by enough to add one additional LRSScale increment.
        #if we are using a set-scale, then we set LRSTop to be the user's value, and LRSMax doesn't matter.
    
        #if self.lrs_lod == 'LOD':
        #    lodm = self.LODFACTOR
        #else:
        #    lodm = 1.0
                
        if self.lrsMax <= 0:  #sliding scale
            LRSMax = max(map(max, self.qtlresults)).lrs
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
        LRSScaleFont=pid.Font(ttf="verdana", size=14*fontZoom, bold=0)
        LRSLODFont=pid.Font(ttf="verdana", size=14*zoom*1.5, bold=0)
        yZero = yTopOffset + plotHeight
        
    
        canvas.drawString(self.LRS_LOD, xLeftOffset - canvas.stringWidth("999.99", font=LRSScaleFont) - 10*zoom, \
                          yZero - 150, font=LRSLODFont, color=pid.black, angle=90)
                        
        for item in LRSAxisList:
            yLRS = yZero - (item*lodm/LRSMax) * LRSHeightThresh
            canvas.drawLine(xLeftOffset, yLRS, xLeftOffset - 4, yLRS, color=self.LRS_COLOR, width=1*zoom)
            scaleStr = "%2.1f" % item
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
            for j, _chr in enumerate(self.genotype):
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
                    if 	qtlresult[m].lrs> 460 or qtlresult[m].lrs=='inf':
                        Yc = yZero - webqtlConfig.MAXLRS*LRSHeightThresh/LRSMax
                    else:	
                        Yc = yZero - qtlresult[m].lrs*LRSHeightThresh/LRSMax						
    
                    LRSCoordXY.append((Xc, Yc))
                    if not self.multipleInterval and self.additiveChecked:
                        Yc = yZero - qtlresult[m].additive*AdditiveHeightThresh/additiveMax
                        AdditiveCoordXY.append((Xc, Yc))
                    if not self.multipleInterval and INTERCROSS and self.additiveChecked:
                        Yc = yZero - qtlresult[m].dominance*DominanceHeightThresh/dominanceMax
                        DominanceCoordXY.append((Xc, Yc))
                    m += 1
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
                                    canvas.drawLine(Xc0, Yc0, Xcm, yZero, color=plusColor, width=1, clipX=(xLeftOffset, xLeftOffset + plotWidth))
                                    canvas.drawLine(Xcm, yZero, Xc, yZero-(Yc-yZero), color=minusColor, width=1, clipX=(xLeftOffset, xLeftOffset + plotWidth))
                                else:
                                    canvas.drawLine(Xc0, yZero - (Yc0-yZero), Xcm, yZero, color=minusColor, width=1, clipX=(xLeftOffset, xLeftOffset + plotWidth))
                                    canvas.drawLine(Xcm, yZero, Xc, Yc, color=plusColor, width=1, clipX=(xLeftOffset, xLeftOffset + plotWidth))
                            elif (Yc0-yZero)*(Yc-yZero) > 0:
                                if Yc < yZero:
                                    canvas.drawLine(Xc0, Yc0, Xc, Yc, color=plusColor, width=1, clipX=(xLeftOffset, xLeftOffset + plotWidth))
                                else:
                                    canvas.drawLine(Xc0, yZero - (Yc0-yZero), Xc, yZero - (Yc-yZero), color=minusColor, width=1, clipX=(xLeftOffset, xLeftOffset + plotWidth))
                            else:
                                minYc = min(Yc-yZero, Yc0-yZero)
                                if minYc < 0:
                                    canvas.drawLine(Xc0, Yc0, Xc, Yc, color=plusColor, width=1, clipX=(xLeftOffset, xLeftOffset + plotWidth))
                                else:
                                    canvas.drawLine(Xc0, yZero - (Yc0-yZero), Xc, yZero - (Yc-yZero), color=minusColor, width=1, clipX=(xLeftOffset, xLeftOffset + plotWidth))
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
                                    canvas.drawLine(Xc0, Yc0, Xcm, yZero, color=plusColor, width=1, clipX=(xLeftOffset, xLeftOffset + plotWidth))
                                    canvas.drawLine(Xcm, yZero, Xc, yZero-(Yc-yZero), color=minusColor, width=1, clipX=(xLeftOffset, xLeftOffset + plotWidth))
                                else:
                                    canvas.drawLine(Xc0, yZero - (Yc0-yZero), Xcm, yZero, color=minusColor, width=1, clipX=(xLeftOffset, xLeftOffset + plotWidth))
                                    canvas.drawLine(Xcm, yZero, Xc, Yc, color=plusColor, width=1, clipX=(xLeftOffset, xLeftOffset + plotWidth))
                            elif (Yc0-yZero)*(Yc-yZero) > 0:
                                if Yc < yZero:
                                    canvas.drawLine(Xc0, Yc0, Xc, Yc, color=plusColor, width=1, clipX=(xLeftOffset, xLeftOffset + plotWidth))
                                else:
                                    canvas.drawLine(Xc0, yZero - (Yc0-yZero), Xc, yZero - (Yc-yZero), color=minusColor, width=1, clipX=(xLeftOffset, xLeftOffset + plotWidth))
                            else:
                                minYc = min(Yc-yZero, Yc0-yZero)
                                if minYc < 0:
                                    canvas.drawLine(Xc0, Yc0, Xc, Yc, color=plusColor, width=1, clipX=(xLeftOffset, xLeftOffset + plotWidth))
                                else:
                                    canvas.drawLine(Xc0, yZero - (Yc0-yZero), Xc, yZero - (Yc-yZero), color=minusColor, width=1, clipX=(xLeftOffset, xLeftOffset + plotWidth))
                startPosX +=  (self.ChrLengthDistList[j]+self.GraphInterval)*plotXScale
        
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


    def set_options(self, start_vars):
        """Sets various options (physical/genetic mapping, # permutations, which chromosome"""
        
        self.plot_scale = start_vars['scale']
        #if self.plotScale == 'physic' and not fd.genotype.Mbmap:
        #    self.plotScale = 'morgan'
        self.num_permutations = start_vars['num_permutations']
        self.do_bootstrap = start_vars['do_bootstrap']
        self.control_locus = start_vars['control_locus']
        self.selected_chr = start_vars['selected_chr']


    def identify_empty_samples(self):
        no_val_samples = []
        for sample_count, val in enumerate(self.vals):
            if val == "x":
                no_val_samples.append(sample_count)
        return no_val_samples
        
    def trim_genotypes(self, genotype_data, no_value_samples):
        trimmed_genotype_data = []
        for marker in genotype_data:
            new_genotypes = []
            for item_count, genotype in enumerate(marker):
                if item_count in no_value_samples:
                    continue
                try:
                    genotype = float(genotype)
                except ValueError:
                    genotype = np.nan
                    pass
                new_genotypes.append(genotype)
            trimmed_genotype_data.append(new_genotypes)
        return trimmed_genotype_data