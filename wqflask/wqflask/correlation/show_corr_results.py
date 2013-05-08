## Copyright (C) University of Tennessee Health Science Center, Memphis, TN.
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
# Last updated by NL 2011/02/11
# Last updated by Christian Fernandez 2012/04/07
# Refactored correlation calculation into smaller functions in preparation of
# separating html from existing code

from __future__ import absolute_import, print_function, division

import string
from math import *
import cPickle
import os
import time
#import pyXLWriter as xl
import pp
import math

from pprint import pformat as pf

from htmlgen import HTMLgen2 as HT
import reaper

from base import webqtlConfig
from utility.THCell import THCell
from utility.TDCell import TDCell
from base.trait import GeneralTrait
from base import data_set
from base.templatePage import templatePage
from utility import webqtlUtil, helper_functions
from dbFunction import webqtlDatabaseFunction
import utility.webqtlUtil #this is for parallel computing only.
from wqflask.correlation import correlationFunction

from pprint import pformat as pf

METHOD_SAMPLE_PEARSON = "1"
METHOD_SAMPLE_RANK = "2"
METHOD_LIT = "3"
METHOD_TISSUE_PEARSON = "4"
METHOD_TISSUE_RANK = "5"

TISSUE_METHODS = [METHOD_TISSUE_PEARSON, METHOD_TISSUE_RANK]

TISSUE_MOUSE_DB = 1

class AuthException(Exception): pass


class Trait(object):


    def __init__(self, name, raw_values = None, lit_corr = None, tissue_corr = None, p_tissue = None):
        self.name = name
        self.raw_values = raw_values
        self.lit_corr = lit_corr
        self.tissue_corr = tissue_corr
        self.p_tissue = p_tissue
        self.correlation = 0
        self.p_value = 0

    @staticmethod
    def from_csv(line, data_start = 1):
        name = line[0]
        numbers = line[data_start:]
    #   _log.info(numbers)
        numbers = [ float(number) for number in numbers ]

        return Trait(name, raw_values = numbers)

    def calculate_correlation(self, values, method):
        """Calculate the correlation value and p value according to the method specified"""

        #ZS: This takes the list of values of the trait our selected trait is being correlated
        #against and removes the values of the samples our trait has no value for
        #There's probably a better way of dealing with this, but I'll have to ask Christian
        updated_raw_values = []
        updated_values = []
        for i in range(len(values)):
            if values[i] != "None":
                updated_raw_values.append(self.raw_values[i])
                updated_values.append(values[i])

        self.raw_values = updated_raw_values
        values = updated_values

        if method == METHOD_SAMPLE_PEARSON or method == METHOD_LIT or method == METHOD_TISSUE_PEARSON:
            corr,nOverlap = webqtlUtil.calCorrelation(self.raw_values, values, len(values))
        else:
            corr,nOverlap = webqtlUtil.calCorrelationRank(self.raw_values, values, len(values))

        self.correlation = corr
        self.overlap = nOverlap

        if self.overlap < 3:
            self.p_value = 1.0
        else:
            #ZS - This is probably the wrong way to deal with this. Correlation values of 1.0 definitely exist (the trait correlated against itself), so zero division needs to br prevented.
            if abs(self.correlation) >= 1.0:
                self.p_value = 0.0
            else:
                #Confirm that this division works after future import
                ZValue = 0.5*log((1.0+self.correlation)/(1.0-self.correlation))
                ZValue = ZValue*sqrt(self.overlap-3)
                self.p_value = 2.0*(1.0 - reaper.normp(abs(ZValue)))



#XZ, 01/14/2009: This method is for parallel computing only.
#XZ: It is supposed to be called when "Genetic Correlation, Pearson's r" (method 1)
#XZ: or "Genetic Correlation, Spearman's rho" (method 2) is selected
def compute_corr(input_nnCorr, input_trait, input_list, computing_method):

    allcorrelations = []
    for line in input_list:
        tokens = line.split('","')
        tokens[-1] = tokens[-1][:-2] #remove the last "
        tokens[0] = tokens[0][1:] #remove the first "

        traitdataName = tokens[0]
        database_trait = tokens[1:]

        if computing_method == "1": #XZ: Pearson's r
            corr,nOverlap = utility.webqtlUtil.calCorrelationText(input_trait, database_trait, input_nnCorr)
        else: #XZ: Spearman's rho
            corr,nOverlap = utility.webqtlUtil.calCorrelationRankText(input_trait, database_trait, input_nnCorr)
        traitinfo = [traitdataName,corr,nOverlap]
        allcorrelations.append(traitinfo)

    return allcorrelations

def get_correlation_method_key(form_data):
    #XZ, 09/28/2008: if user select "1", then display 1, 3 and 4.
    #XZ, 09/28/2008: if user select "2", then display 2, 3 and 5.
    #XZ, 09/28/2008: if user select "3", then display 1, 3 and 4.
    #XZ, 09/28/2008: if user select "4", then display 1, 3 and 4.
    #XZ, 09/28/2008: if user select "5", then display 2, 3 and 5.

    method = form_data.method
    if method not in ["1", "2", "3" ,"4", "5"]:
        return "1"

    return method


def get_custom_trait(form_data, cursor):
    """Pulls the custom trait, if it exists, out of the form data"""
    trait_name = form_data.fullname

    if trait_name:
        trait = webqtlTrait(fullname=trait_name, cursor=cursor)
        trait.retrieveInfo()
        return trait
    else:
        return None


#XZ, 09/18/2008: get the information such as value, variance of the input strain names from the form.
def get_sample_data(fd):
    #print("fd is:", pf(fd.__dict__))
    if fd.allstrainlist:
        mdpchoice = fd.MDPChoice
        #XZ, in HTML source code, it is "BXD Only", "BXH Only", and so on
        if mdpchoice == "1":
            strainlist = fd.f1list + fd.strainlist
        #XZ, in HTML source code, it is "Non-BXD Only", "Non-BXD Only", etc
        elif mdpchoice == "2":
            strainlist = []
            strainlist2 = fd.f1list + fd.strainlist
            for strain in fd.allstrainlist:
                if strain not in strainlist2:
                    strainlist.append(strain)
            #So called MDP Panel
            if strainlist:
                strainlist = fd.f1list + fd.parlist+strainlist
        #XZ, in HTML source code, it is "All Cases"
        else:
            strainlist = fd.allstrainlist
        #XZ, 09/18/2008: put the trait data into dictionary fd.allTraitData
        fd.readData(fd.allstrainlist)
    else:
        mdpchoice = None
        strainlist = fd.strainlist
        #XZ, 09/18/2008: put the trait data into dictionary fd.allTraitData
        fd.readData()

    return strainlist



def get_species(fd, cursor):
    #XZ, 3/16/2010: variable RISet must be pass by the form
    RISet = fd.RISet
    #XZ, 12/12/2008: get species infomation
    species = webqtlDatabaseFunction.retrieveSpecies(cursor=cursor, RISet=RISet)
    return species


def sortTraitCorrelations(traits, method="1"):
    if method in TISSUE_METHODS:
        traits.sort(key=lambda trait: trait.tissue_corr != None and abs(trait.tissue_corr), reverse=True)
    elif method == METHOD_LIT:
        traits.sort(key=lambda trait: trait.lit_corr != None and abs(trait.lit_corr), reverse=True)
    else:
        traits.sort(key=lambda trait: trait.correlation != None and abs(trait.correlation), reverse=True)

    return traits


def auth_user_for_db(db, cursor, target_db_name, privilege, username):
    """Authorize a user for access to a database if that database is
    confidential. A db (identified by a record in ProbeSetFreeze) contains a
    list of authorized users who may access it, as well as its confidentiality
    level.

    If the current user's privilege level is greater than 'user', ie: root or
    admin, then they are automatically authed, otherwise, check the
    AuthorizedUsers field for the presence of their name."""

    if db.type == 'ProbeSet':
        cursor.execute('SELECT Id, Name, FullName, confidentiality, AuthorisedUsers FROM ProbeSetFreeze WHERE Name = "%s"' %  target_db_name)
        indId, indName, indFullName, confidential, AuthorisedUsers = cursor.fetchall()[0]

        if confidential:
            authorized = 0

            #for the dataset that confidentiality is 1
            #1. 'admin' and 'root' can see all of the dataset
            #2. 'user' can see the dataset that AuthorisedUsers contains his id(stored in the Id field of User table)
            if webqtlConfig.USERDICT[privilege] > webqtlConfig.USERDICT['user']:
                authorized = 1
            else:
                if username in AuthorisedUsers.split(","):
                    authorized = 1

            if not authorized:
                raise AuthException("The %s database you selected is not open to the public at this time, please go back and select other database." % indFullName)


class CorrelationResults(object):

    corr_min_informative = 4

    #PAGE_HEADING = "Correlation Table"
    #CORRELATION_METHODS = {"1" : "Genetic Correlation (Pearson's r)",
    #                       "2" : "Genetic Correlation (Spearman's rho)",
    #                       "3" : "SGO Literature Correlation",
    #                       "4" : "Tissue Correlation (Pearson's r)",
    #                       "5" : "Tissue Correlation (Spearman's rho)"}
    #
    #RANK_ORDERS = {"1": 0, "2": 1, "3": 0, "4": 0, "5": 1}


    #def error(self, message, *args, **kw):
    #    heading = heading or self.PAGE_HEADING
    #    return templatePage.error(heading = heading, detail = [message], error=error)

    def __init__(self, start_vars):
        # get trait list from db (database name)
        # calculate correlation with Base vector and targets
        
        #self.this_trait = GeneralTrait(dataset=self.dataset.name,
        #                               name=start_vars['trait_id'],
        #                               cellid=None)                
        
        print("start_vars: ", pf(start_vars))
        
        helper_functions.get_species_dataset_trait(self, start_vars)
        self.dataset.group.read_genotype_file()
        
        self.samples = []   # Want only ones with values
        self.vals = []

        corr_samples_group = start_vars['corr_samples_group']

        #The two if statements below append samples to the sample list based upon whether the user
        #selected Primary Samples Only, Other Samples Only, or All Samples

        #If either BXD/whatever Only or All Samples, append all of that group's samplelist      
        if corr_samples_group != 'samples_other':
            self.process_samples(start_vars, self.dataset.group.samplelist, ())
        
        #If either Non-BXD/whatever or All Samples, get all samples from this_trait.data and
        #exclude the primary samples (because they would have been added in the previous
        #if statement if the user selected All Samples)
        if corr_samples_group != 'samples_primary':
            primary_samples = (self.dataset.group.parlist +
                                   self.dataset.group.f1list +
                                   self.dataset.group.samplelist)
            self.process_samples(start_vars, self.this_trait.data.keys(), primary_samples)

        #for i, sample in enumerate(self.samples):
        #    print("{} : {}".format(sample, self.vals[i]))
    
        self.target_dataset = data_set.create_dataset(start_vars['corr_dataset'])
        self.target_dataset.get_trait_data()
        print("trait_list: {}".format(pf(self.target_dataset.trait_data)))
        # Lei Yan todo
        for trait, values in self.target_dataset.trait_data.iteritems():
            correlation = calCorrelation(values, )

        #XZ, 09/18/2008: get all information about the user selected database.
        #target_db_name = fd.corr_dataset
        self.target_db_name = start_vars['corr_dataset']

        # Zach said this is ok
        # Auth if needed
        #try:
        #    auth_user_for_db(self.db, self.cursor, self.target_db_name, self.privilege, self.userName)
        #except AuthException as e:
        #    detail = [e.message]
        #    return self.error(detail)

        #XZ, 09/18/2008: filter out the strains that have no value.
        #self.sample_names, vals, vars, N = fd.informativeStrains(sample_list)

        #print("samplenames is:", pf(self.sample_names))
        #CF - If less than a minimum number of strains/cases in common, don't calculate anything
        #if len(self.sample_names) < self.corr_min_informative:
        #    detail = ['Fewer than %d strain data were entered for %s data set. No calculation of correlation has been attempted.' % (self.corr_min_informative, fd.RISet)]
        #    self.error(heading=None, detail=detail)

        #correlation_method = self.CORRELATION_METHODS[self.method]
        #rankOrder = self.RANK_ORDERS[self.method]

        # CF - Number of results returned
        # Todo: Get rid of self.returnNumber

        #self.record_count = 0

        #myTrait = get_custom_trait(fd, self.cursor)


        # We will not get Literature Correlations if there is no GeneId because there is nothing
        # to look against
        self.geneid = self.this_trait.geneid

        # We will not get Tissue Correlations if there is no gene symbol because there is nothing to look against
        #self.trait_symbol = myTrait.symbol


        #XZ, 12/12/2008: if the species is rat or human, translate the geneid to mouse geneid
        self.input_trait_mouse_gene_id = self.translateToMouseGeneID(self.dataset.group.species, self.geneid)

        #XZ: As of Nov/13/2010, this dataset is 'UTHSC Illumina V6.2 RankInv B6 D2 average CNS GI average (May 08)'
        self.tissue_probeset_freeze_id = 1

        traitList = self.correlate()

        _log.info("Done doing correlation calculation")

############################################################################################################################################

        TD_LR = HT.TD(height=200,width="100%",bgColor='#eeeeee')

        mainfmName = webqtlUtil.genRandStr("fm_")
        form = HT.Form(cgi = os.path.join(webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE),
                       enctype='multipart/form-data', name= mainfmName, submit=HT.Input(type='hidden'))
        hddn = {'FormID': 'showDatabase',
                'ProbeSetID': '_',
                'database': self.target_db_name,
                'databaseFull': self.db.fullname,
                'CellID': '_',
                'RISet': fd.RISet,
                'identification': fd.identification}

        if myTrait:
            hddn['fullname'] = fd.fullname
        if mdp_choice:
            hddn['MDPChoice']= mdp_choice


        #XZ, 09/18/2008: pass the trait data to next page by hidden parameters.
        webqtlUtil.exportData(hddn, fd.allTraitData)

        if fd.incparentsf1:
            hddn['incparentsf1']='ON'

        if fd.allstrainlist:
            hddn['allstrainlist'] = string.join(fd.allstrainlist, ' ')


        for key in hddn.keys():
            form.append(HT.Input(name=key, value=hddn[key], type='hidden'))

        #XZ, 11/21/2008: add two parameters to form
        form.append(HT.Input(name="X_geneSymbol", value="", type='hidden'))
        form.append(HT.Input(name="Y_geneSymbol", value="", type='hidden'))

        #XZ, 3/11/2010: add one parameter to record if the method is rank order.
        form.append(HT.Input(name="rankOrder", value="%s" % rankOrder, type='hidden'))

        form.append(HT.Input(name="TissueProbeSetFreezeId", value="%s" % self.tissue_probeset_freeze_id, type='hidden'))

        ####################################
        # generate the info on top of page #
        ####################################

        info = self.getTopInfo(myTrait=myTrait, method=self.method, db=self.db, target_db_name=self.target_db_name, returnNumber=self.returnNumber, methodDict=self.CORRELATION_METHODS, totalTraits=traitList, identification=fd.identification  )

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


        #Select All, Deselect All, Invert Selection, Add to Collection
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
        addselect = HT.Href(url="#redirect", onClick="addRmvSelection('%s', document.getElementsByName('%s')[0], 'addToSelection');" % (fd.RISet, mainfmName))
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


        #External analysis tools
        GCATButton = HT.Href(url="#redirect", onClick="databaseFunc(document.getElementsByName('%s')[0], 'GCAT');" % mainfmName)
        GCATButton_img = HT.Image("/images/GCAT_logo_final.jpg", name="GCAT", alt="GCAT", title="GCAT", style="border:none")
        GCATButton.append(GCATButton_img)

        ODE = HT.Href(url="#redirect", onClick="databaseFunc(document.getElementsByName('%s')[0], 'ODE');" % mainfmName)
        ODE_img = HT.Image("/images/ODE_logo_final.jpg", name="ode", alt="ODE", title="ODE", style="border:none")
        ODE.append(ODE_img)

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

        self.cursor.execute('SELECT GeneChip.GO_tree_value FROM GeneChip, ProbeFreeze, ProbeSetFreeze WHERE GeneChip.Id = ProbeFreeze.ChipId and ProbeSetFreeze.ProbeFreezeId = ProbeFreeze.Id and ProbeSetFreeze.Name = "%s"' % self.db.name)
        result = self.cursor.fetchone()

        if result:
            GO_tree_value = result[0]

        if GO_tree_value:

            WebGestalt = HT.Href(url="#redirect", onClick="databaseFunc(document.getElementsByName('%s')[0], 'GOTree');" % mainfmName)
            WebGestalt_img = HT.Image("/images/webgestalt_icon_final.jpg", name="webgestalt", alt="Gene Set Analysis Toolkit", title="Gene Set Analysis Toolkit", style="border:none")
            WebGestalt.append(WebGestalt_img)

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

            if self.species == 'rat':
                hddnWebGestalt['org'] = 'Rattus norvegicus'
            elif self.species == 'human':
                hddnWebGestalt['org'] = 'Homo sapiens'
            elif self.species == 'mouse':
                hddnWebGestalt['org'] = 'Mus musculus'
            else:
                hddnWebGestalt['org'] = ''

            for key in hddnWebGestalt.keys():
                form.append(HT.Input(name=key, value=hddnWebGestalt[key], type='hidden'))


        #Create tables with options, etc

        pageTable = HT.TableLite(cellSpacing=0,cellPadding=0,width="100%", border=0, align="Left")

        containerTable = HT.TableLite(cellSpacing=0,cellPadding=0,width="90%",border=0, align="Left")


        if not GO_tree_value:
            optionsTable = HT.TableLite(cellSpacing=2, cellPadding=0,width="480", height="80", border=0, align="Left")
            optionsTable.append(HT.TR(HT.TD(selectall), HT.TD(reset), HT.TD(selectinvert), HT.TD(addselect), HT.TD(GCATButton), HT.TD(ODE), align="left"))
            optionsTable.append(HT.TR(HT.TD("&nbsp;"*1,"Select"), HT.TD("Deselect"), HT.TD("&nbsp;"*1,"Invert"), HT.TD("&nbsp;"*3,"Add"), HT.TD("Gene Set"), HT.TD("&nbsp;"*2,"GCAT")))
        else:
            optionsTable = HT.TableLite(cellSpacing=2, cellPadding=0,width="560", height="80", border=0, align="Left")
            optionsTable.append(HT.TR(HT.TD(selectall), HT.TD(reset), HT.TD(selectinvert), HT.TD(addselect), HT.TD(GCATButton), HT.TD(ODE), HT.TD(WebGestalt), align="left"))
            optionsTable.append(HT.TR(HT.TD("&nbsp;"*1,"Select"), HT.TD("Deselect"), HT.TD("&nbsp;"*1,"Invert"), HT.TD("&nbsp;"*3,"Add"), HT.TD("Gene Set"), HT.TD("&nbsp;"*2,"GCAT"), HT.TD("&nbsp;"*3, "ODE")))
        containerTable.append(HT.TR(HT.TD(optionsTable)))

        functionTable = HT.TableLite(cellSpacing=2,cellPadding=0,width="480",height="80", border=0, align="Left")
        functionRow = HT.TR(HT.TD(networkGraph, width="16.7%"), HT.TD(cormatrix, width="16.7%"), HT.TD(partialCorr, width="16.7%"), HT.TD(mcorr, width="16.7%"), HT.TD(mintmap, width="16.7%"), HT.TD(heatmap), align="left")
        labelRow = HT.TR(HT.TD("&nbsp;"*1,HT.Text("Graph")), HT.TD("&nbsp;"*1,HT.Text("Matrix")), HT.TD("&nbsp;"*1,HT.Text("Partial")), HT.TD(HT.Text("Compare")), HT.TD(HT.Text("QTL Map")), HT.TD(HT.Text(text="Heat Map")))
        functionTable.append(functionRow, labelRow)
        containerTable.append(HT.TR(HT.TD(functionTable), HT.BR()))

        #more_options = HT.Image("/images/more_options1_final.jpg", name='more_options', alt="Expand Options", title="Expand Options", style="border:none;", Class="toggleShowHide")

        #containerTable.append(HT.TR(HT.TD(more_options, HT.BR(), HT.BR())))

        moreOptions = HT.Input(type='button',name='options',value='More Options', onClick="",Class="toggle")
        fewerOptions = HT.Input(type='button',name='options',value='Fewer Options', onClick="",Class="toggle")

        """
        if (fd.formdata.getvalue('showHideOptions') == 'less'):
            containerTable.append(HT.TR(HT.TD("&nbsp;"), height="10"), HT.TR(HT.TD(HT.Div(fewerOptions, Class="toggleShowHide"))))
            containerTable.append(HT.TR(HT.TD("&nbsp;")))
        else:
            containerTable.append(HT.TR(HT.TD("&nbsp;"), height="10"), HT.TR(HT.TD(HT.Div(moreOptions, Class="toggleShowHide"))))
            containerTable.append(HT.TR(HT.TD("&nbsp;")))
        """

        containerTable.append(HT.TR(HT.TD(HT.Span(selecttraits,' with r > ',selectgt, ' ',selectandor, ' r < ',selectlt,Class="bd1 cbddf fs11")), style="display:none;", Class="extra_options"))

        chrMenu = HT.Input(type='hidden',name='chromosomes',value='all')

        corrHeading = HT.Paragraph('Correlation Table', Class="title")


        tblobj = {}

        if self.db.type=="Geno":
            containerTable.append(HT.TR(HT.TD(xlsUrl, height=60)))

            pageTable.append(HT.TR(HT.TD(containerTable)))

            tblobj['header'], worksheet = self.getTableHeaderForGeno( method=self.method, worksheet=worksheet, newrow=newrow, headingStyle=headingStyle)
            newrow += 1

            sortby = self.getSortByValue( calculationMethod = self.method )

            corrScript = HT.Script(language="Javascript")
            corrScript.append("var corrArray = new Array();")

            tblobj['body'], worksheet, corrScript = self.getTableBodyForGeno(traitList=traitList, formName=mainfmName, worksheet=worksheet, newrow=newrow, corrScript=corrScript)

            workbook.close()
            objfile = open('%s.obj' % (webqtlConfig.TMPDIR+filename), 'wb')
            cPickle.dump(tblobj, objfile)
            objfile.close()

            div = HT.Div(webqtlUtil.genTableObj(tblobj=tblobj, file=filename, sortby=sortby, tableID = "sortable", addIndex = "1"), corrScript, Id="sortable")

            pageTable.append(HT.TR(HT.TD(div)))

            form.append(HT.Input(name='ShowStrains',type='hidden', value =1),
                        HT.Input(name='ShowLine',type='hidden', value =1),
                        HT.P(), HT.P(), pageTable)
            TD_LR.append(corrHeading, info, form, HT.P())

            self.dict['body'] =  str(TD_LR)
            self.dict['js1'] = ''
            self.dict['title'] = 'Correlation'

        elif self.db.type=="Publish":

            containerTable.append(HT.TR(HT.TD(xlsUrl, height=40)))

            pageTable.append(HT.TR(HT.TD(containerTable)))

            tblobj['header'], worksheet = self.getTableHeaderForPublish(method=self.method, worksheet=worksheet, newrow=newrow, headingStyle=headingStyle)
            newrow += 1

            sortby = self.getSortByValue( calculationMethod = self.method )

            corrScript = HT.Script(language="Javascript")
            corrScript.append("var corrArray = new Array();")

            tblobj['body'], worksheet, corrScript = self.getTableBodyForPublish(traitList=traitList, formName=mainfmName, worksheet=worksheet, newrow=newrow, corrScript=corrScript, species=self.species)

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
            HT.P(), pageTable)
            TD_LR.append(corrHeading, info, form, HT.P())

            self.dict['body'] = str(TD_LR)
            self.dict['js1'] = ''
            self.dict['title'] = 'Correlation'


        elif self.db.type=="ProbeSet":
            tblobj['header'], worksheet = self.getTableHeaderForProbeSet(method=self.method, worksheet=worksheet, newrow=newrow, headingStyle=headingStyle)
            newrow += 1

            sortby = self.getSortByValue( calculationMethod = self.method )

            corrScript = HT.Script(language="Javascript")
            corrScript.append("var corrArray = new Array();")

            tblobj['body'], worksheet, corrScript = self.getTableBodyForProbeSet(traitList=traitList, primaryTrait=myTrait, formName=mainfmName, worksheet=worksheet, newrow=newrow, corrScript=corrScript, species=self.species)

            workbook.close()
            objfile = open('%s.obj' % (webqtlConfig.TMPDIR+filename), 'wb')
            cPickle.dump(tblobj, objfile)
            objfile.close()

            #XZ: here is the table of traits
            div = HT.Div(webqtlUtil.genTableObj(tblobj=tblobj, file=filename, sortby=sortby, tableID = "sortable", addIndex = "1", hiddenColumns=["Gene ID","Homologene ID"]), corrScript, Id="sortable")


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
            strainIds=self.getStrainIds(species=self.species, strains=self.sample_names)
            var1 = HT.Input(name="filename", value=filename, type='hidden')
            var2 = HT.Input(name="strainIds", value=strainIds, type='hidden')
            var3 = HT.Input(name="vals", value=vals, type='hidden')
            customizerButton = HT.Input(type="button", Class="button", value="Add Correlation", onClick = "xmlhttpPost('%smain.py?FormID=AJAX_table', 'sortable', (getquerystring(this.form)))" % webqtlConfig.CGIDIR)

            containerTable.append(HT.TR(HT.TD(HT.Span(var1,var2,var3,customizerButton, "with", dbCustomizer, Class="bd1 cbddf fs11"), HT.BR(), HT.BR()), style="display:none;", Class="extra_options"))

            containerTable.append(HT.TR(HT.TD(xlsUrl, HT.BR(), HT.BR())))

            pageTable.append(HT.TR(HT.TD(containerTable)))

            pageTable.append(HT.TR(HT.TD(div)))

            if self.species == 'human':
                heatmap = ""

            form.append(HT.Input(name='ShowStrains',type='hidden', value =1),
                            HT.Input(name='ShowLine',type='hidden', value =1),
                            info, HT.BR(), pageTable, HT.BR())

            TD_LR.append(corrHeading, form, HT.P())


            self.dict['body'] = str(TD_LR)
            self.dict['title'] = 'Correlation'
                        # updated by NL. Delete function generateJavaScript, move js files to dhtml.js, webqtl.js and jqueryFunction.js
            self.dict['js1'] = ''
            self.dict['js2'] = 'onLoad="pageOffset()"'
            self.dict['layer'] = self.generateWarningLayer()
        else:
            self.dict['body'] = ""

    def get_all_dataset_data(self):
        
        """
        SELECT ProbeSet.Name, T128.value, T129.value, T130.value, T131.value, T132.value, T134.value, T135.value, T138.value, T139.value, T140.value, T141.value, T142.value, T144
        .value, T145.value, T147.value, T148.value, T149.value, T487.value, T919.value, T920.value, T922.value
        FROM (ProbeSet, ProbeSetXRef, ProbeSetFreeze)
        left join ProbeSetData as T128 on T128.Id = ProbeSetXRef.DataId and T128.StrainId=128
        left join ProbeSetData as T129 on T129.Id = ProbeSetXRef.DataId and T129.StrainId=129
        left join ProbeSetData as T130 on T130.Id = ProbeSetXRef.DataId and T130.StrainId=130
        left join ProbeSetData as T131 on T131.Id = ProbeSetXRef.DataId and T131.StrainId=131
        left join ProbeSetData as T132 on T132.Id = ProbeSetXRef.DataId and T132.StrainId=132
        left join ProbeSetData as T134 on T134.Id = ProbeSetXRef.DataId and T134.StrainId=134
        left join ProbeSetData as T135 on T135.Id = ProbeSetXRef.DataId and T135.StrainId=135
        left join ProbeSetData as T138 on T138.Id = ProbeSetXRef.DataId and T138.StrainId=138
        left join ProbeSetData as T139 on T139.Id = ProbeSetXRef.DataId and T139.StrainId=139
        left join ProbeSetData as T140 on T140.Id = ProbeSetXRef.DataId and T140.StrainId=140
        left join ProbeSetData as T141 on T141.Id = ProbeSetXRef.DataId and T141.StrainId=141
        left join ProbeSetData as T142 on T142.Id = ProbeSetXRef.DataId and T142.StrainId=142
        left join ProbeSetData as T144 on T144.Id = ProbeSetXRef.DataId and T144.StrainId=144
        left join ProbeSetData as T145 on T145.Id = ProbeSetXRef.DataId and T145.StrainId=145
        left join ProbeSetData as T147 on T147.Id = ProbeSetXRef.DataId and T147.StrainId=147
        left join ProbeSetData as T148 on T148.Id = ProbeSetXRef.DataId and T148.StrainId=148
        left join ProbeSetData as T149 on T149.Id = ProbeSetXRef.DataId and T149.StrainId=149
        left join ProbeSetData as T487 on T487.Id = ProbeSetXRef.DataId and T487.StrainId=487
        left join ProbeSetData as T919 on T919.Id = ProbeSetXRef.DataId and T919.StrainId=919
        left join ProbeSetData as T920 on T920.Id = ProbeSetXRef.DataId and T920.StrainId=920
        left join ProbeSetData as T922 on T922.Id = ProbeSetXRef.DataId and T922.StrainId=922
        WHERE ProbeSetXRef.ProbeSetFreezeId = ProbeSetFreeze.Id and
        ProbeSetFreeze.Name = 'HC_M2_0606_P' and
        ProbeSet.Id = ProbeSetXRef.ProbeSetId order by ProbeSet.Id
        """


    def process_samples(self, start_vars, sample_names, excluded_samples):
        for sample in sample_names:
            if sample not in excluded_samples:
                value = start_vars['value:' + sample]
                variance = start_vars['variance:' + sample]
                if variance.strip().lower() == 'x':
                    variance = 0
                else:
                    variance = float(variance)
                if value.strip().lower() != 'x':
                    self.samples.append(str(sample))
                    self.vals.append(float(value))
                    #self.variances.append(variance)    

    def getSortByValue(self, calculationMethod):

        if calculationMethod == "1":
            sortby = ("Sample p(r)", "up")
        elif calculationMethod == "2":
            sortby = ("Sample p(rho)", "up")
        elif calculationMethod == "3": #XZ: literature correlation
            sortby = ("Lit Corr","down")
        elif calculationMethod == "4": #XZ: tissue correlation
            sortby = ("Tissue r", "down")
        elif calculationMethod == "5":
            sortby = ("Tissue rho", "down")

        return sortby



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


    #XZ, 01/07/2009: In HTML code, the variable 'database' corresponds to the column 'Name' in database table.
    def getFileName(self, target_db_name):  ### dcrowell  August 2008
        """Returns the name of the reference database file with which correlations are calculated.
        Takes argument cursor which is a cursor object of any instance of a subclass of templatePage
        Used by correlationPage"""

        trait_id, full_name = g.db.execute("""SELECT Id, FullName
                                              FROM ProbeSetFreeze
                                              WHERE Name = '%s'""" % target_db_name).fetchone()
        for char in [' ', '/']:
            full_name = full_name.replace(char, '_')
            
        file_name = 'ProbeSetFreezeId_' + str(trait_id) + '_FullName_' + full_name + '.txt'

        return file_name



    #XZ, 01/29/2009: I modified this function.
    #XZ: Note that the type of StrainIds must be number, not string.
    def getStrainIds(self, species=None, strains=[]):
        StrainIds = []
        for item in strains:
            self.cursor.execute('''SELECT Strain.Id FROM Strain, Species WHERE
                Strain.Name="%s" and Strain.SpeciesId=Species.Id and Species.name = "%s" ''' % (item, species))
            Id = self.cursor.fetchone()[0]
            StrainIds.append(Id)

        return StrainIds


    #XZ, 12/12/2008: if the species is rat or human, translate the geneid to mouse geneid
    #XZ, 12/12/2008: if the input geneid is 'None', return 0
    #XZ, 12/12/2008: if the input geneid has no corresponding mouse geneid, return 0
    def translateToMouseGeneID(self, species, geneid):
        #mouse_geneid = 0

        if not geneid:
            return 0

        #self.id, self.name, self.fullname, self.shortname = g.db.execute("""
        #        SELECT Id, Name, FullName, ShortName
        #        FROM %s
        #        WHERE public > %s AND
        #             (Name = '%s' OR FullName = '%s' OR ShortName = '%s')
        #  """ % (query_args)).fetchone()

        if species == 'mouse':
            mouse_geneid = geneid
        elif species == 'rat':
            mouse_geneid = g.db.execute(
                """SELECT mouse FROM GeneIDXRef WHERE rat='%d'""", int(geneid)).fetchone().mouse
            #if record:
            #    mouse_geneid = record[0]
        elif species == 'human':
            mouse_geneid = g.db.execute(
                """SELECT mouse FROM GeneIDXRef WHERE human='%d'""", int(geneid)).fetchone().mouse
            #if record:
            #    mouse_geneid = record[0]
        print("mouse_geneid:", mouse_geneid)
        return mouse_geneid


    #XZ, 12/16/2008: the input geneid is of mouse type
    def checkForLitInfo(self,geneId):
        q = 'SELECT 1 FROM LCorrRamin3 WHERE GeneId1=%s LIMIT 1' % geneId
        self.cursor.execute(q)
        try:
            x = self.cursor.fetchone()
            if x: return True
            else: raise
        except: return False


    #XZ, 12/16/2008: the input geneid is of mouse type
    def checkSymbolForTissueCorr(self, tissueProbeSetFreezeId=0, symbol=""):
        q = "SELECT 1 FROM  TissueProbeSetXRef WHERE TissueProbeSetFreezeId=%s and Symbol='%s' LIMIT 1" % (tissueProbeSetFreezeId,symbol)
        self.cursor.execute(q)
        try:
            x = self.cursor.fetchone()
            if x: return True
            else: raise
        except: return False


    def fetchAllDatabaseData(self, species, GeneId, GeneSymbol, strains, db, method, returnNumber, tissueProbeSetFreezeId):

        StrainIds = []
        for item in strains:
            self.cursor.execute('''SELECT Strain.Id FROM Strain, Species WHERE Strain.Name="%s" and Strain.SpeciesId=Species.Id and Species.name = "%s" ''' % (item, species))
            Id = self.cursor.fetchone()[0]
            StrainIds.append('%d' % Id)

        # break it into smaller chunks so we don't overload the MySql server
        nnn = len(StrainIds) / 25
        if len(StrainIds) % 25:
            nnn += 1
        oridata = []

        #XZ, 09/24/2008: build one temporary table that only contains the records associated with the input GeneId
        tempTable = None
        if GeneId and db.type == "ProbeSet":
            if method == "3":
                tempTable = self.getTempLiteratureTable(species=species, input_species_geneid=GeneId, returnNumber=returnNumber)

            if method == "4" or method == "5":
                tempTable = self.getTempTissueCorrTable(primaryTraitSymbol=GeneSymbol, TissueProbeSetFreezeId=TISSUE_MOUSE_DB, method=method, returnNumber=returnNumber)

        for step in range(nnn):
            temp = []
            StrainIdstep = StrainIds[step*25:min(len(StrainIds), (step+1)*25)]
            for item in StrainIdstep: temp.append('T%s.value' % item)

            if db.type == "Publish":
                query = "SELECT PublishXRef.Id, "
                dataStartPos = 1
                query += string.join(temp,', ')
                query += ' FROM (PublishXRef, PublishFreeze)'
                #XZ, 03/04/2009: Xiaodong changed Data to PublishData
                for item in StrainIdstep:
                    query += 'left join PublishData as T%s on T%s.Id = PublishXRef.DataId and T%s.StrainId=%s\n' %(item,item,item,item)
                query += "WHERE PublishXRef.InbredSetId = PublishFreeze.InbredSetId and PublishFreeze.Name = '%s'" % (db.name, )
            #XZ, 09/20/2008: extract literature correlation value together with gene expression values.
            #XZ, 09/20/2008: notice the difference between the code in next block.
            #elif tempTable:
            #    # we can get a little performance out of selecting our LitCorr here
            #    # but also we need to do this because we are unconcerned with probes that have no geneId associated with them
            #    # as we would not have litCorr data.
            #
            #    if method == "3":
            #        query = "SELECT %s.Name, %s.value," %  (db.type,tempTable)
            #        dataStartPos = 2
            #    if method == "4" or method == "5":
            #        query = "SELECT %s.Name, %s.Correlation, %s.PValue," %  (db.type,tempTable, tempTable)
            #        dataStartPos = 3
            #
            #    query += string.join(temp,', ')
            #    query += ' FROM (%s, %sXRef, %sFreeze)' % (db.type, db.type, db.type)
            #    if method == "3":
            #        query += ' LEFT JOIN %s ON %s.GeneId2=ProbeSet.GeneId ' % (tempTable,tempTable)
            #    if method == "4" or method == "5":
            #        query += ' LEFT JOIN %s ON %s.Symbol=ProbeSet.Symbol ' % (tempTable,tempTable)
            #    #XZ, 03/04/2009: Xiaodong changed Data to %sData and changed parameters from %(item,item, db.type,item,item) to %(db.type, item,item, db.type,item,item)
            #    for item in StrainIdstep:
            #        query += 'left join %sData as T%s on T%s.Id = %sXRef.DataId and T%s.StrainId=%s\n' %(db.type, item,item, db.type,item,item)
            #
            #    if method == "3":
            #        query += "WHERE ProbeSet.GeneId IS NOT NULL AND %s.value IS NOT NULL AND %sXRef.%sFreezeId = %sFreeze.Id and %sFreeze.Name = '%s'  and %s.Id = %sXRef.%sId order by %s.Id" % (tempTable,db.type, db.type, db.type, db.type, db.name, db.type, db.type, db.type, db.type)
            #    if method == "4" or method == "5":
            #        query += "WHERE ProbeSet.Symbol IS NOT NULL AND %s.Correlation IS NOT NULL AND %sXRef.%sFreezeId = %sFreeze.Id and %sFreeze.Name = '%s'  and %s.Id = %sXRef.%sId order by %s.Id" % (tempTable,db.type, db.type, db.type, db.type, db.name, db.type, db.type, db.type, db.type)
            else:
                query = "SELECT %s.Name," %  db.type
                dataStartPos = 1
                query += string.join(temp,', ')
                query += ' FROM (%s, %sXRef, %sFreeze)' % (db.type, db.type, db.type)
                #XZ, 03/04/2009: Xiaodong changed Data to %sData and changed parameters from %(item,item, db.type,item,item) to %(db.type, item,item, db.type,item,item)
                for item in StrainIdstep:
                    query += 'left join %sData as T%s on T%s.Id = %sXRef.DataId and T%s.StrainId=%s\n' %(db.type, item,item, db.type,item,item)
                query += "WHERE %sXRef.%sFreezeId = %sFreeze.Id and %sFreeze.Name = '%s'  and %s.Id = %sXRef.%sId order by %s.Id" % (db.type, db.type, db.type, db.type, db.name, db.type, db.type, db.type, db.type)

            self.cursor.execute(query)
            results = self.cursor.fetchall()
            oridata.append(results)

        datasize = len(oridata[0])
        traits = []
        # put all of the separate data together into a huge list of lists
        for j in range(datasize):
            traitdata = list(oridata[0][j])
            for i in range(1,nnn):
                traitdata += list(oridata[i][j][dataStartPos:])

            trait = Trait(traitdata[0], traitdata[dataStartPos:])

            if method == METHOD_LIT:
                trait.lit_corr = traitdata[1]

            if method in TISSUE_METHODS:
                trait.tissue_corr = traitdata[1]
                trait.p_tissue = traitdata[2]

            traits.append(trait)

        if tempTable:
            self.cursor.execute( 'DROP TEMPORARY TABLE %s' % tempTable )

        return traits




    # XZ, 09/20/2008: This function creates TEMPORARY TABLE tmpTableName_2 and return its name.
    # XZ, 09/20/2008: It stores top literature correlation values associated with the input geneId.
    # XZ, 09/20/2008: Attention: In each row, the input geneId is always in column GeneId1.
    #XZ, 12/16/2008: the input geneid can be of mouse, rat or human type
    def getTempLiteratureTable(self, species, input_species_geneid, returnNumber):
        # according to mysql the TEMPORARY TABLE name should not have to be unique because
        # it is only available to the current connection. This program will be invoked via command line, but if it
        # were to be invoked over mod_python this could cuase problems.  mod_python will keep the connection alive
        # in its executing threads ( i think) so there is a potential for the table not being dropped between users.
        #XZ, 01/29/2009: To prevent the potential risk, I generate random table names and drop the tables after use them.


        # the 'input_species_geneid' could be rat or human geneid, need to translate it to mouse geneid
        translated_mouse_geneid = self.translateToMouseGeneID (species, input_species_geneid)

        tmpTableName_1 = webqtlUtil.genRandStr(prefix="LITERATURE")

        q1 = 'CREATE TEMPORARY TABLE %s (GeneId1 int(12) unsigned, GeneId2 int(12) unsigned PRIMARY KEY, value double)' % tmpTableName_1
        q2 = 'INSERT INTO %s (GeneId1, GeneId2, value) SELECT GeneId1,GeneId2,value FROM LCorrRamin3 WHERE GeneId1=%s' % (tmpTableName_1, translated_mouse_geneid)
        q3 = 'INSERT INTO %s (GeneId1, GeneId2, value) SELECT GeneId2,GeneId1,value FROM LCorrRamin3 WHERE GeneId2=%s AND GeneId1!=%s' % (tmpTableName_1, translated_mouse_geneid,translated_mouse_geneid)
        for x in [q1,q2,q3]: self.cursor.execute(x)

        #XZ, 09/23/2008: Just use the top records insteard of using all records
        tmpTableName_2 = webqtlUtil.genRandStr(prefix="TOPLITERATURE")

        q1 = 'CREATE TEMPORARY TABLE %s (GeneId1 int(12) unsigned, GeneId2 int(12) unsigned PRIMARY KEY, value double)' % tmpTableName_2
        self.cursor.execute(q1)
        q2 = 'SELECT GeneId1, GeneId2, value FROM %s ORDER BY value DESC' % tmpTableName_1
        self.cursor.execute(q2)
        result = self.cursor.fetchall()

        counter = 0 #this is to count how many records being inserted into table
        for one_row in result:
            mouse_geneid1, mouse_geneid2, lit_corr_alue = one_row

            #mouse_geneid1 has been tested before, now should test if mouse_geneid2 has corresponding geneid in other species
            translated_species_geneid = 0
            if species == 'mouse':
                translated_species_geneid = mouse_geneid2
            elif species == 'rat':
                self.cursor.execute( "SELECT rat FROM GeneIDXRef WHERE mouse=%d" % int(mouse_geneid2) )
                record = self.cursor.fetchone()
                if record:
                    translated_species_geneid = record[0]
            elif species == 'human':
                self.cursor.execute( "SELECT human FROM GeneIDXRef WHERE mouse=%d" % int(mouse_geneid2) )
                record = self.cursor.fetchone()
                if record:
                    translated_species_geneid = record[0]

            if translated_species_geneid:
                self.cursor.execute( 'INSERT INTO %s (GeneId1, GeneId2, value) VALUES (%d,%d,%f)' % (tmpTableName_2, int(input_species_geneid),int(translated_species_geneid), float(lit_corr_alue)) )
                counter = counter + 1

            #pay attention to the number
            if (counter > 2*returnNumber):
                break

        self.cursor.execute('DROP TEMPORARY TABLE %s' % tmpTableName_1)

        return tmpTableName_2



    #XZ, 09/23/2008: In tissue correlation tables, there is no record of GeneId1 == GeneId2
    #XZ, 09/24/2008: Note that the correlation value can be negative.
    def getTempTissueCorrTable(self, primaryTraitSymbol="", TissueProbeSetFreezeId=0, method="", returnNumber=0):

        def cmpTissCorrAbsoluteValue(A, B):
            try:
                if abs(A[1]) < abs(B[1]): return 1
                elif abs(A[1]) == abs(B[1]):
                    return 0
                else: return -1
            except:
                return 0

        symbolCorrDict, symbolPvalueDict = self.calculateCorrOfAllTissueTrait(primaryTraitSymbol=primaryTraitSymbol, TissueProbeSetFreezeId=TISSUE_MOUSE_DB, method=method)

        symbolCorrList = symbolCorrDict.items()

        symbolCorrList.sort(cmpTissCorrAbsoluteValue)
        symbolCorrList = symbolCorrList[0 : 2*returnNumber]

        tmpTableName = webqtlUtil.genRandStr(prefix="TOPTISSUE")

        q1 = 'CREATE TEMPORARY TABLE %s (Symbol varchar(100) PRIMARY KEY, Correlation float, PValue float)' % tmpTableName
        self.cursor.execute(q1)

        for one_pair in symbolCorrList:
            one_symbol = one_pair[0]
            one_corr = one_pair[1]
            one_p_value = symbolPvalueDict[one_symbol]

            self.cursor.execute( "INSERT INTO %s (Symbol, Correlation, PValue) VALUES ('%s',%f,%f)" % (tmpTableName, one_symbol, float(one_corr), float(one_p_value)) )

        return tmpTableName


    #XZ, 01/09/2009: This function was created by David Crowell. Xiaodong cleaned up and modified it.
    def fetchLitCorrelations(self, species, GeneId, db, returnNumber): ### Used to generate Lit Correlations when calculations are done from text file.  dcrowell August 2008
        """Uses getTempLiteratureTable to generate table of literatire correlations.  This function then gathers that data and
        pairs it with the TraitID string.  Takes as its arguments a formdata instance, and a database instance.
        Returns a dictionary of 'TraitID':'LitCorr' for the requested correlation"""

        tempTable = self.getTempLiteratureTable(species=species, input_species_geneid=GeneId, returnNumber=returnNumber)

        query = "SELECT %s.Name, %s.value" %  (db.type,tempTable)
        query += ' FROM (%s, %sXRef, %sFreeze)' % (db.type, db.type, db.type)
        query += ' LEFT JOIN %s ON %s.GeneId2=ProbeSet.GeneId ' % (tempTable,tempTable)
        query += "WHERE ProbeSet.GeneId IS NOT NULL AND %s.value IS NOT NULL AND %sXRef.%sFreezeId = %sFreeze.Id and %sFreeze.Name = '%s'  and %s.Id = %sXRef.%sId order by %s.Id" % (tempTable, db.type, db.type, db.type, db.type, db.name, db.type, db.type, db.type, db.type)

        self.cursor.execute(query)
        results = self.cursor.fetchall()

        litCorrDict = {}

        for entry in results:
            traitName,litcorr = entry
            litCorrDict[traitName] = litcorr

        self.cursor.execute('DROP TEMPORARY TABLE %s' % tempTable)

        return litCorrDict



    #XZ, 01/09/2009: Xiaodong created this function.
    def fetchTissueCorrelations(self, db, primaryTraitSymbol="", TissueProbeSetFreezeId=0, method="", returnNumber = 0):
        """Uses getTempTissueCorrTable to generate table of tissue correlations.  This function then gathers that data and
        pairs it with the TraitID string.  Takes as its arguments a formdata instance, and a database instance.
        Returns a dictionary of 'TraitID':(tissueCorr, tissuePValue) for the requested correlation"""


        tempTable = self.getTempTissueCorrTable(primaryTraitSymbol=primaryTraitSymbol, TissueProbeSetFreezeId=TISSUE_MOUSE_DB, method=method, returnNumber=returnNumber)

        query = "SELECT ProbeSet.Name, %s.Correlation, %s.PValue" %  (tempTable, tempTable)
        query += ' FROM (ProbeSet, ProbeSetXRef, ProbeSetFreeze)'
        query += ' LEFT JOIN %s ON %s.Symbol=ProbeSet.Symbol ' % (tempTable,tempTable)
        query += "WHERE ProbeSetFreeze.Name = '%s' and ProbeSetFreeze.Id=ProbeSetXRef.ProbeSetFreezeId and ProbeSet.Id = ProbeSetXRef.ProbeSetId and ProbeSet.Symbol IS NOT NULL AND %s.Correlation IS NOT NULL" % (db.name, tempTable)

        self.cursor.execute(query)
        results = self.cursor.fetchall()

        tissueCorrDict = {}

        for entry in results:
            traitName, tissueCorr, tissuePValue = entry
            tissueCorrDict[traitName] = (tissueCorr, tissuePValue)

        self.cursor.execute('DROP TEMPORARY TABLE %s' % tempTable)

        return tissueCorrDict



    #XZ, 01/13/2008
    def getLiteratureCorrelationByList(self, input_trait_mouse_geneid=None, species=None, traitList=None):

        tmpTableName = webqtlUtil.genRandStr(prefix="LITERATURE")

        q1 = 'CREATE TEMPORARY TABLE %s (GeneId1 int(12) unsigned, GeneId2 int(12) unsigned PRIMARY KEY, value double)' % tmpTableName
        q2 = 'INSERT INTO %s (GeneId1, GeneId2, value) SELECT GeneId1,GeneId2,value FROM LCorrRamin3 WHERE GeneId1=%s' % (tmpTableName, input_trait_mouse_geneid)
        q3 = 'INSERT INTO %s (GeneId1, GeneId2, value) SELECT GeneId2,GeneId1,value FROM LCorrRamin3 WHERE GeneId2=%s AND GeneId1!=%s' % (tmpTableName, input_trait_mouse_geneid, input_trait_mouse_geneid)

        for x in [q1,q2,q3]:
            self.cursor.execute(x)

        for thisTrait in traitList:
            try:
                if thisTrait.geneid:
                    thisTrait.mouse_geneid = self.translateToMouseGeneID(species, thisTrait.geneid)
                else:
                    thisTrait.mouse_geneid = 0
            except:
                thisTrait.mouse_geneid = 0

            if thisTrait.mouse_geneid and str(thisTrait.mouse_geneid).find(";") == -1:
                try:
                    self.cursor.execute("SELECT value FROM %s WHERE GeneId2 = %s" % (tmpTableName, thisTrait.mouse_geneid))
                    result =  self.cursor.fetchone()
                    if result:
                        thisTrait.LCorr = result[0]
                    else:
                        thisTrait.LCorr = None
                except:
                    thisTrait.LCorr = None
            else:
                thisTrait.LCorr = None

        self.cursor.execute("DROP TEMPORARY TABLE %s" % tmpTableName)

        return traitList

    def get_traits(self, vals):

        #Todo: Redo cached stuff using memcached
        if False:
            _log.info("Using the fast method because the file exists")
            lit_corrs = {}
            tissue_corrs = {}
            use_lit = False
            if self.method == METHOD_LIT:
                lit_corrs = self.fetchLitCorrelations(species=self.species, GeneId=self.gene_id, db=self.db, returnNumber=self.returnNumber)
                use_lit = True

            use_tissue_corr = False
            if self.method in TISSUE_METHODS:
                tissue_corrs = self.fetchTissueCorrelations(db=self.db, primaryTraitSymbol=self.trait_symbol, TissueProbeSetFreezeId=TISSUE_MOUSE_DB, method=self.method, returnNumber = self.returnNumber)
                use_tissue_corr = True

            DatabaseFileName = self.getFileName( target_db_name=self.target_db_name )
            datasetFile = open(webqtlConfig.TEXTDIR+DatabaseFileName,'r')

            #XZ, 01/08/2009: read the first line
            line = datasetFile.readline()
            cached_sample_names = webqtlUtil.readLineCSV(line)[1:]

            #XZ, 01/08/2009: This step is critical. It is necessary for this new method.
            #XZ: The original function fetchAllDatabaseData uses all strains stored in variable _strains to
            #XZ: retrieve the values of each strain from database in real time.
            #XZ: The new method uses all strains stored in variable dataset_strains to create a new variable
            #XZ: _newvals. _newvals has the same length as dataset_strains. The items in _newvals is in
            #XZ: the same order of items in dataset_strains. The value of each item in _newvals is either
            #XZ: the value of correspinding strain in _vals or 'None'.
            new_vals = []
            for name in cached_sample_names:
                if name in self.sample_names:
                    new_vals.append(float(vals[self.sample_names.index(name)]))
                else:
                    new_vals.append('None')

            nnCorr = len(new_vals)

            #XZ, 01/14/2009: If literature corr or tissue corr is selected,
            #XZ: there is no need to use parallel computing.

            traits = []
            data_start = 1
            for line in datasetFile:
                raw_trait = webqtlUtil.readLineCSV(line)
                trait = Trait.from_csv(raw_trait, data_start)
                trait.lit_corr = lit_corrs.get(trait.name)
                trait.tissue_corr, trait.p_tissue = tissue_corrs.get(trait.name, (None, None))
                traits.append(trait)

            return traits, new_vals

        else:
            traits = self.fetchAllDatabaseData(species=self.dataset.species,
                                               GeneId=self.gene_id,
                                               GeneSymbol=self.trait.symbol,
                                               strains=self.sample_names,
                                               db=self.db,
                                               method=self.method,
                                               returnNumber=self.returnNumber,
                                               tissueProbeSetFreezeId= self.tissue_probeset_freeze_id)
            totalTraits = len(traits) #XZ, 09/18/2008: total trait number

        return traits


        def do_parallel_correlation(self):
            _log.info("Invoking parallel computing")
            input_line_list = datasetFile.readlines()
            _log.info("Read lines from the file")
            all_line_number = len(input_line_list)

            step = 1000
            job_number = math.ceil( float(all_line_number)/step )

            job_input_lists = []

            _log.info("Configuring jobs")

            for job_index in range( int(job_number) ):
                starti = job_index*step
                endi = min((job_index+1)*step, all_line_number)

                one_job_input_list = []

                for i in range( starti, endi ):
                    one_job_input_list.append( input_line_list[i] )

                job_input_lists.append( one_job_input_list )

            _log.info("Creating pp servers")

            ppservers = ()
            # Creates jobserver with automatically detected number of workers
            job_server = pp.Server(ppservers=ppservers)

            _log.info("Done creating servers")

            jobs = []
            results = []

            _log.info("Starting parallel computation, submitting jobs")
            for one_job_input_list in job_input_lists: #pay attention to modules from outside
                jobs.append( job_server.submit(func=compute_corr, args=(nnCorr, _newvals, one_job_input_list, self.method), depfuncs=(), modules=("utility.webqtlUtil",)) )
            _log.info("Done submitting jobs")

            for one_job in jobs:
                one_result = one_job()
                results.append( one_result )

            _log.info("Acquiring results")

            for one_result in results:
                for one_traitinfo in one_result:
                    allcorrelations.append( one_traitinfo )

            _log.info("Appending the results")

        datasetFile.close()
        totalTraits = len(allcorrelations)
        _log.info("Done correlating using the fast method")


    def correlate(self):

        correlations = []

        #XZ: Use the fast method only for probeset dataset, and this dataset must have been created.
        #XZ: Otherwise, use original method
        #_log.info("Entering correlation")

        #db_filename = self.getFileName(target_db_name=self.target_db_name)
        #
        #cache_available = db_filename in os.listdir(webqtlConfig.TEXTDIR)

         # If the cache file exists, do a cached correlation for probeset data
        if self.dataset.type == "ProbeSet":
#           if self.method in [METHOD_SAMPLE_PEARSON, METHOD_SAMPLE_RANK] and cache_available:
#               traits = do_parallel_correlation()
#
#           else:

            traits = self.get_traits(self.vals)

            for trait in traits:
                trait.calculate_correlation(vals, self.method)

        self.record_count = len(traits) #ZS: This isn't a good way to get this value, so I need to change it later

        #XZ, 3/31/2010: Theoretically, we should create one function 'comTissueCorr'
        #to compare each trait by their tissue corr p values.
        #But because the tissue corr p values are generated by permutation test,
        #the top ones always have p value 0. So comparing p values actually does nothing.
        #In addition, for the tissue data in our database, the N is always the same.
        #So it's safe to compare with tissue corr statistic value.
        #That's the same as literature corr.
        #if self.method in [METHOD_LIT, METHOD_TISSUE_PEARSON, METHOD_TISSUE_RANK] and self.gene_id:
        #    traits.sort(webqtlUtil.cmpLitCorr)
        #else:
        #if self.method in TISSUE_METHODS:
        #    sort(traits, key=lambda A: math.fabs(A.tissue_corr))
        #elif self.method == METHOD_LIT:
        #    traits.sort(traits, key=lambda A: math.fabs(A.lit_corr))
        #else:
        traits = sortTraitCorrelations(traits, self.method)

        # Strip to the top N correlations
        traits = traits[:min(self.returnNumber, len(traits))]

        addLiteratureCorr = False
        addTissueCorr = False

        trait_list = []
        for trait in traits:
            db_trait = webqtlTrait(db=self.db, name=trait.name, cursor=self.cursor)
            db_trait.retrieveInfo( QTL='Yes' )

            db_trait.Name = trait.name
            db_trait.corr = trait.correlation
            db_trait.nOverlap = trait.overlap
            db_trait.corrPValue = trait.p_value

            # NL, 07/19/2010
            # js function changed, add a new parameter rankOrder for js function 'showTissueCorrPlot'
            db_trait.RANK_ORDER = self.RANK_ORDERS[self.method]

            #XZ, 26/09/2008: Method is 4 or 5. Have fetched tissue corr, but no literature correlation yet.
            if self.method in TISSUE_METHODS:
                db_trait.tissueCorr = trait.tissue_corr
                db_trait.tissuePValue = trait.p_tissue
                addTissueCorr = True


            #XZ, 26/09/2008: Method is 3,  Have fetched literature corr, but no tissue corr yet.
            elif self.method == METHOD_LIT:
                db_trait.LCorr = trait.lit_corr
                db_trait.mouse_geneid = self.translateToMouseGeneID(self.species, db_trait.geneid)
                addLiteratureCorr = True

            #XZ, 26/09/2008: Method is 1 or 2. Have NOT fetched literature corr and tissue corr yet.
            # Phenotype data will not have geneid, and neither will some probes
            # we need to handle this because we will get an attribute error
            else:
                if self.input_trait_mouse_gene_id and self.db.type=="ProbeSet":
                    addLiteratureCorr = True
                if self.trait_symbol and self.db.type=="ProbeSet":
                    addTissueCorr = True

            trait_list.append(db_trait)

        if addLiteratureCorr:
            trait_list = self.getLiteratureCorrelationByList(self.input_trait_mouse_gene_id,
                                                    self.species, trait_list)
        if addTissueCorr:
            trait_list = self.getTissueCorrelationByList(
                        primaryTraitSymbol = self.trait_symbol,
                        traitList = trait_list,
                        TissueProbeSetFreezeId = TISSUE_MOUSE_DB,
                        method=self.method)

        return trait_list

    def calculateCorrOfAllTissueTrait(self, primaryTraitSymbol=None, TissueProbeSetFreezeId=None, method=None):

        symbolCorrDict = {}
        symbolPvalueDict = {}

        primaryTraitSymbolValueDict = correlationFunction.getGeneSymbolTissueValueDictForTrait(cursor=self.cursor, GeneNameLst=[primaryTraitSymbol], TissueProbeSetFreezeId=TISSUE_MOUSE_DB)
        primaryTraitValue = primaryTraitSymbolValueDict.values()[0]

        SymbolValueDict = correlationFunction.getGeneSymbolTissueValueDictForTrait(cursor=self.cursor, GeneNameLst=[], TissueProbeSetFreezeId=TISSUE_MOUSE_DB)

        if method in ["2","5"]:
            symbolCorrDict, symbolPvalueDict = correlationFunction.batchCalTissueCorr(primaryTraitValue,SymbolValueDict,method='spearman')
        else:
            symbolCorrDict, symbolPvalueDict = correlationFunction.batchCalTissueCorr(primaryTraitValue,SymbolValueDict)


        return (symbolCorrDict, symbolPvalueDict)



    #XZ, 10/13/2010
    def getTissueCorrelationByList(self, primaryTraitSymbol=None, traitList=None, TissueProbeSetFreezeId=None, method=None):

        primaryTraitSymbolValueDict = correlationFunction.getGeneSymbolTissueValueDictForTrait(cursor=self.cursor, GeneNameLst=[primaryTraitSymbol], TissueProbeSetFreezeId=TISSUE_MOUSE_DB)

        if primaryTraitSymbol.lower() in primaryTraitSymbolValueDict:
            primaryTraitValue = primaryTraitSymbolValueDict[primaryTraitSymbol.lower()]

            geneSymbolList = []

            for thisTrait in traitList:
                if hasattr(thisTrait, 'symbol'):
                    geneSymbolList.append(thisTrait.symbol)

            SymbolValueDict = correlationFunction.getGeneSymbolTissueValueDictForTrait(cursor=self.cursor, GeneNameLst=geneSymbolList, TissueProbeSetFreezeId=TISSUE_MOUSE_DB)

            for thisTrait in traitList:
                if hasattr(thisTrait, 'symbol') and thisTrait.symbol and thisTrait.symbol.lower() in SymbolValueDict:
                    oneTraitValue = SymbolValueDict[thisTrait.symbol.lower()]
                    if method in ["2","5"]:
                        result = correlationFunction.calZeroOrderCorrForTiss( primaryTraitValue, oneTraitValue, method='spearman' )
                    else:
                        result = correlationFunction.calZeroOrderCorrForTiss( primaryTraitValue, oneTraitValue)
                    thisTrait.tissueCorr = result[0]
                    thisTrait.tissuePValue = result[2]
                else:
                    thisTrait.tissueCorr = None
                    thisTrait.tissuePValue = None
        else:
            for thisTrait in traitList:
                thisTrait.tissueCorr = None
                thisTrait.tissuePValue = None

        return traitList


    def getTopInfo(self, myTrait=None, method=None, db=None, target_db_name=None, returnNumber=None, methodDict=None, totalTraits=None, identification=None  ):

        if myTrait:
            if method in ["1","2"]: #genetic correlation
                info = HT.Paragraph("Values of Record %s in the " % myTrait.getGivenName(), HT.Href(text=myTrait.db.fullname,url=webqtlConfig.INFOPAGEHREF % myTrait.db.name,target="_blank", Class="fwn"),
                                     " database were compared to all %d records in the " % self.record_count, HT.Href(text=db.fullname,url=webqtlConfig.INFOPAGEHREF % target_db_name,target="_blank", Class="fwn"),
                                     ' database. The top %d correlations ranked by the %s are displayed.' % (returnNumber,methodDict[method]),
                                     ' You can resort this list using the small arrowheads in the top row.')
            else:
                #myTrait.retrieveInfo()#need to know geneid and symbol
                if method == "3":#literature correlation
                    searchDBName = "Literature Correlation"
                    searchDBLink = "/correlationAnnotation.html#literatureCorr"
                else: #tissue correlation
                    searchDBName = "Tissue Correlation"
                    searchDBLink = "/correlationAnnotation.html#tissueCorr"
                info = HT.Paragraph("Your input record %s in the " % myTrait.getGivenName(), HT.Href(text=myTrait.db.fullname,url=webqtlConfig.INFOPAGEHREF % myTrait.db.name,target="_blank", Class="fwn"),
                                     " database corresponds to ",
                                     HT.Href(text='gene Id %s, and gene symbol %s' % (myTrait.geneid, myTrait.symbol), target='_blank',url="http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?db=gene&cmd=Retrieve&dopt=Graphics&list_uids=%s" % myTrait.geneid, Class="fs12 fwn"),
                                     '. GN ranked all genes in the ', HT.Href(text=searchDBName,url=searchDBLink,target="_blank", Class="fwn"),' database by the %s.' % methodDict[method],
                                     ' The top %d probes or probesets in the ' % returnNumber, HT.Href(text=db.fullname,url=webqtlConfig.INFOPAGEHREF % target_db_name,target="_blank", Class="fwn"),
                                     ' database corresponding to the top genes ranked by the %s are displayed.' %( methodDict[method]),
                                     ' You can resort this list using the small arrowheads in the top row.' )

        elif identification:
            info = HT.Paragraph('Values of %s were compared to all %d traits in '  % (identification, self.record_count),
                                 HT.Href(text=db.fullname,url=webqtlConfig.INFOPAGEHREF % target_db_name,target="_blank",Class="fwn"),
                                 ' database. The TOP %d correlations ranked by the %s are displayed.' % (returnNumber,methodDict[method]),
                                 ' You can resort this list using the small arrowheads in the top row.')

        else:
            info = HT.Paragraph('Trait values were compared to all values in ',
                                 HT.Href(text=db.fullname,url=webqtlConfig.INFOPAGEHREF % target_db_name,target="_blank",Class="fwn"),
                                 ' database. The TOP %d correlations ranked by the %s are displayed.' % (returnNumber,methodDict[method]),
                                 ' You can resort this list using the small arrowheads in the top row.')

        if db.type=="Geno":
            info.append(HT.BR(),HT.BR(),'Clicking on the Locus will open the  genotypes data for that locus. Click on the correlation to see a scatter plot of the trait data.')
        elif db.type=="Publish":
            info.append(HT.BR(),HT.BR(),'Clicking on the record ID will open the  published phenotype data for that publication. Click on the correlation to see a scatter plot of the trait data. ')
        elif db.type=="ProbeSet":
            info.append(HT.BR(),'Click the correlation values to generate scatter plots. Select the Record ID to open the Trait Data and Analysis form. Select the symbol to open NCBI Entrez.')
        else:
            pass


        return info


    def createExcelFileWithTitleAndFooter(self, workbook=None, identification=None, db=None, returnNumber=None):

        worksheet = workbook.add_worksheet()

        titleStyle = workbook.add_format(align = 'left', bold = 0, size=14, border = 1, border_color="gray")

        ##Write title Info
        # Modified by Hongqiang Li
        worksheet.write([1, 0], "Citations: Please see %s/reference.html" % webqtlConfig.PORTADDR, titleStyle)
        worksheet.write([1, 0], "Citations: Please see %s/reference.html" % webqtlConfig.PORTADDR, titleStyle)
        worksheet.write([2, 0], "Trait : %s" % identification, titleStyle)
        worksheet.write([3, 0], "Database : %s" % db.fullname, titleStyle)
        worksheet.write([4, 0], "Date : %s" % time.strftime("%B %d, %Y", time.gmtime()), titleStyle)
        worksheet.write([5, 0], "Time : %s GMT" % time.strftime("%H:%M ", time.gmtime()), titleStyle)
        worksheet.write([6, 0], "Status of data ownership: Possibly unpublished data; please see %s/statusandContact.html for details on sources, ownership, and usage of these data." % webqtlConfig.PORTADDR, titleStyle)
        #Write footer info
        worksheet.write([9 + returnNumber, 0], "Funding for The GeneNetwork: NIAAA (U01AA13499, U24AA13513), NIDA, NIMH, and NIAAA (P20-DA21131), NCI MMHCC (U01CA105417), and NCRR (U01NR 105417)", titleStyle)
        worksheet.write([10 + returnNumber, 0], "PLEASE RETAIN DATA SOURCE INFORMATION WHENEVER POSSIBLE", titleStyle)

        return worksheet


    def getTableHeaderForGeno(self, method=None, worksheet=None, newrow=None, headingStyle=None):

        tblobj_header = []

        if method in ["1","3","4"]:
            tblobj_header = [[THCell(HT.TD(' ', Class="fs13 fwb ffl b1 cw cbrb"), sort=0),
                              THCell(HT.TD('Record', HT.BR(), 'ID', HT.BR(), Class="fs13 fwb ffl b1 cw cbrb"), text='Record ID', idx=1),
                              THCell(HT.TD('Location', HT.BR(), 'Chr and Mb', HT.BR(), Class="fs13 fwb ffl b1 cw cbrb"), text='Location (Chr and Mb)', idx=2),
                              THCell(HT.TD(HT.Href(
                                                   text = HT.Span('Sample',HT.BR(), 'r', HT.Sup('  ?', style="color:#f00"),HT.BR(), Class="fs13 fwb ffl cw"),
                                                   target = '_blank',
                                                   url = "/correlationAnnotation.html#genetic_r"),
                                           Class="fs13 fwb ffl b1 cw cbrb", nowrap='ON'), text="Sample r", idx=3),
                              THCell(HT.TD('N',HT.BR(),'Cases',HT.BR(), Class="fs13 fwb ffl b1 cw cbrb"), text="N Cases", idx=4),
                              THCell(HT.TD(HT.Href(
                                                   text = HT.Span('Sample',HT.BR(), 'p(r)', HT.Sup('  ?', style="color:#f00"),HT.BR(), Class="fs13 fwb ffl cw"),
                                                   target = '_blank',
                                                   url = "/correlationAnnotation.html#genetic_p_r"),
                                           Class="fs13 fwb ffl b1 cw cbrb", nowrap='ON'), text="Sample p(r)", idx=5)]]

            for ncol, item in enumerate(['Record ID', 'Location (Chr, Mb)', 'Sample r', 'N Cases', 'Sample p(r)']):
                worksheet.write([newrow, ncol], item, headingStyle)
                worksheet.set_column([ncol, ncol], 2*len(item))
        else:
            tblobj_header = [[THCell(HT.TD(' ', Class="fs13 fwb ffl b1 cw cbrb"), sort=0),
                              THCell(HT.TD('Record', HT.BR(), 'ID', HT.BR(), Class="fs13 fwb ffl b1 cw cbrb"), text='Record ID', idx=1),
                              THCell(HT.TD('Location', HT.BR(), 'Chr and Mb', HT.BR(), Class="fs13 fwb ffl b1 cw cbrb"), text='Location (Chr and Mb)', idx=2),
                              THCell(HT.TD(HT.Href(
                                                   text = HT.Span('Sample',HT.BR(), 'rho', HT.Sup('  ?', style="color:#f00"),HT.BR(), Class="fs13 fwb ffl cw"),
                                                   target = '_blank',
                                                   url = "/correlationAnnotation.html#genetic_rho"),
                                           Class="fs13 fwb ffl b1 cw cbrb", nowrap='ON'), text="Sample rho", idx=3),
                              THCell(HT.TD('N',HT.BR(),'Cases',HT.BR(), Class="fs13 fwb ffl b1 cw cbrb"), text="N Cases", idx=4),
                              THCell(HT.TD(HT.Href(
                                                   text = HT.Span('Sample',HT.BR(), 'p(rho)', HT.Sup('  ?', style="color:#f00"),HT.BR(), Class="fs13 fwb ffl cw"),
                                                   target = '_blank',
                                                   url = "/correlationAnnotation.html#genetic_p_rho"),
                                           Class="fs13 fwb ffl b1 cw cbrb", nowrap='ON'), text="Sample p(rho)", idx=5)]]

            for ncol, item in enumerate(['Record ID', 'Location (Chr, Mb)', 'Sample rho', 'N Cases', 'Sample p(rho)']):
                worksheet.write([newrow, ncol], item, headingStyle)
                worksheet.set_column([ncol, ncol], 2*len(item))


        return tblobj_header, worksheet


    def getTableBodyForGeno(self, traitList, formName=None, worksheet=None, newrow=None, corrScript=None):

        tblobj_body = []

        for thisTrait in traitList:
            tr = []

            trId = str(thisTrait)

            corrScript.append('corrArray["%s"] = {corr:%1.4f};' % (trId, thisTrait.corr))

            tr.append(TDCell(HT.TD(HT.Input(type="checkbox", Class="checkbox", name="searchResult",value=trId, onClick="highlight(this)"), nowrap="on", Class="fs12 fwn ffl b1 c222"), text=trId))

            tr.append(TDCell(HT.TD(HT.Href(text=thisTrait.name,url="javascript:showTrait('%s', '%s')" % (formName, thisTrait.name), Class="fs12 fwn ffl"),align="left", Class="fs12 fwn ffl b1 c222"), text=thisTrait.name, val=thisTrait.name.upper()))

            #XZ: trait_location_value is used for sorting
            trait_location_repr = '--'
            trait_location_value = 1000000

            if thisTrait.chr and thisTrait.mb:
                try:
                    trait_location_value = int(thisTrait.chr)*1000 + thisTrait.mb
                except:
                    if thisTrait.chr.upper() == 'X':
                        trait_location_value = 20*1000 + thisTrait.mb
                    else:
                        trait_location_value = ord(str(thisTrait.chr).upper()[0])*1000 + thisTrait.mb

                trait_location_repr = 'Chr%s: %.6f' % (thisTrait.chr, float(thisTrait.mb) )

            tr.append(TDCell(HT.TD(trait_location_repr, Class="fs12 fwn b1 c222", nowrap="on"), trait_location_repr, trait_location_value))


            repr='%3.3f' % thisTrait.corr
            tr.append(TDCell(HT.TD(HT.Href(text=repr, url="javascript:showCorrPlot('%s', '%s')" % (formName, thisTrait.name), Class="fs12 fwn ffl"), Class="fs12 fwn ffl b1 c222", nowrap='ON', align='right'),repr,abs(thisTrait.corr)))

            repr = '%d' % thisTrait.nOverlap
            tr.append(TDCell(HT.TD(repr, Class="fs12 fwn ffl b1 c222",align='right'),repr,thisTrait.nOverlap))

            repr = webqtlUtil.SciFloat(thisTrait.corrPValue)
            tr.append(TDCell(HT.TD(repr,nowrap='ON', Class="fs12 fwn ffl b1 c222", align='right'),repr,thisTrait.corrPValue))

            tblobj_body.append(tr)

            for ncol, item in enumerate([thisTrait.name, trait_location_repr, thisTrait.corr, thisTrait.nOverlap, thisTrait.corrPValue]):
                worksheet.write([newrow, ncol], item)
            newrow += 1

        return tblobj_body, worksheet, corrScript


    def getTableHeaderForPublish(self, method=None, worksheet=None, newrow=None, headingStyle=None):

        tblobj_header = []

        if method in ["1","3","4"]:
            tblobj_header = [[THCell(HT.TD(' ', Class="fs13 fwb ffl b1 cw cbrb", nowrap="on"), sort=0),
                              THCell(HT.TD('Record',HT.BR(), 'ID',HT.BR(), Class="fs13 fwb ffl b1 cw cbrb", nowrap="on"), text="Record ID", idx=1),
                              THCell(HT.TD('Phenotype', HT.BR(),HT.BR(), Class="fs13 fwb ffl b1 cw cbrb", nowrap="on"), text="Phenotype", idx=2),
                              THCell(HT.TD('Authors', HT.BR(),HT.BR(), Class="fs13 fwb ffl b1 cw cbrb", nowrap="on"), text="Authors", idx=3),
                              THCell(HT.TD('Year', HT.BR(),HT.BR(), Class="fs13 fwb ffl b1 cw cbrb", nowrap="on"), text="Year", idx=4),
                              THCell(HT.TD('Max',HT.BR(), 'LRS', HT.BR(), Class="fs13 fwb ffl b1 cw cbrb", nowrap="on"), text="Max LRS", idx=5),
                              THCell(HT.TD('Max LRS Location',HT.BR(),'Chr and Mb',HT.BR(), Class="fs13 fwb ffl b1 cw cbrb", nowrap="on"), text="Max LRS Location", idx=6),
                              THCell(HT.TD(HT.Href(
                                                   text = HT.Span('Sample',HT.BR(), 'r', HT.Sup('  ?', style="color:#f00"),HT.BR(), Class="fs13 fwb ffl cw"),
                                                   target = '_blank',
                                                   url = "/correlationAnnotation.html#genetic_r"),
                                           Class="fs13 fwb ffl b1 cw cbrb", nowrap='ON'), text="Sample r", idx=7),
                              THCell(HT.TD('N',HT.BR(),'Cases',HT.BR(), Class="fs13 fwb ffl b1 cw cbrb"), text="N Cases", idx=8),
                              THCell(HT.TD(HT.Href(
                                                   text = HT.Span('Sample',HT.BR(), 'p(r)', HT.Sup('  ?', style="color:#f00"),HT.BR(), Class="fs13 fwb ffl cw"),
                                                   target = '_blank',
                                                   url = "/correlationAnnotation.html#genetic_p_r"),
                                           Class="fs13 fwb ffl b1 cw cbrb", nowrap='ON'), text="Sample p(r)", idx=9)]]

            for ncol, item in enumerate(["Record", "Phenotype", "Authors", "Year", "Pubmed Id", "Max LRS", "Max LRS Location (Chr: Mb)", "Sample r", "N Cases", "Sample p(r)"]):
                worksheet.write([newrow, ncol], item, headingStyle)
                worksheet.set_column([ncol, ncol], 2*len(item))
        else:
            tblobj_header = [[THCell(HT.TD(' ', Class="fs13 fwb ffl b1 cw cbrb", nowrap="on"), sort=0),
                              THCell(HT.TD('Record',HT.BR(), 'ID',HT.BR(), Class="fs13 fwb ffl b1 cw cbrb", nowrap="on"), text="Record ID", idx=1),
                              THCell(HT.TD('Phenotype', HT.BR(),HT.BR(), Class="fs13 fwb ffl b1 cw cbrb", nowrap="on"), text="Phenotype", idx=2),
                              THCell(HT.TD('Authors', HT.BR(),HT.BR(), Class="fs13 fwb ffl b1 cw cbrb", nowrap="on"), text="Authors", idx=3),
                              THCell(HT.TD('Year', HT.BR(),HT.BR(), Class="fs13 fwb ffl b1 cw cbrb", nowrap="on"), text="Year", idx=4),
                              THCell(HT.TD('Max',HT.BR(), 'LRS', HT.BR(), Class="fs13 fwb ffl b1 cw cbrb", nowrap="on"), text="Max LRS", idx=5),
                              THCell(HT.TD('Max LRS Location',HT.BR(),'Chr and Mb',HT.BR(), Class="fs13 fwb ffl b1 cw cbrb", nowrap="on"), text="Max LRS Location", idx=6),
                              THCell(HT.TD(HT.Href(
                                                   text = HT.Span('Sample',HT.BR(), 'rho', HT.Sup('  ?', style="color:#f00"),HT.BR(), Class="fs13 fwb ffl cw"),
                                                   target = '_blank',
                                                   url = "/correlationAnnotation.html#genetic_rho"),
                                           Class="fs13 fwb ffl b1 cw cbrb", nowrap='ON'), text="Sample rho", idx=7),
                              THCell(HT.TD('N',HT.BR(),'Cases',HT.BR(), Class="fs13 fwb ffl b1 cw cbrb"), text="N Cases", idx=8),
                              THCell(HT.TD(HT.Href(
                                                   text = HT.Span('Sample',HT.BR(), 'p(rho)', HT.Sup('  ?', style="color:#f00"),HT.BR(), Class="fs13 fwb ffl cw"),
                                                   target = '_blank',
                                                   url = "/correlationAnnotation.html#genetic_p_rho"),
                                           Class="fs13 fwb ffl b1 cw cbrb", nowrap='ON'), text="Sample p(rho)", idx=9)]]

            for ncol, item in enumerate(["Record", "Phenotype", "Authors", "Year", "Pubmed Id", "Max LRS", "Max LRS Location (Chr: Mb)", "Sample rho", "N Cases", "Sample p(rho)"]):
                worksheet.write([newrow, ncol], item, headingStyle)
                worksheet.set_column([ncol, ncol], 2*len(item))


        return tblobj_header, worksheet


    def getTableBodyForPublish(self, traitList, formName=None, worksheet=None, newrow=None, corrScript=None, species=''):

        tblobj_body = []

        for thisTrait in traitList:
            tr = []

            trId = str(thisTrait)

            corrScript.append('corrArray["%s"] = {corr:%1.4f};' % (trId, thisTrait.corr))

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
                PubMedLinkText = repr = "--"
                myear = 0
            if thisTrait.pubmed_id:
                PubMedLink = HT.Href(text= repr,url= webqtlConfig.PUBMEDLINK_URL % thisTrait.pubmed_id,target='_blank', Class="fs12 fwn")
            else:
                PubMedLink = repr

            tr.append(TDCell(HT.TD(PubMedLink, Class="fs12 fwn b1 c222", align='center'), repr, myear))

            #LRS and its location
            LRS_score_repr = '--'
            LRS_score_value = 0
            LRS_location_repr = '--'
            LRS_location_value = 1000000
            LRS_flag = 1

            #Max LRS and its Locus location
            if thisTrait.lrs and thisTrait.locus:
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

                        #tr.append(TDCell(HT.TD(HT.Href(text=LRS_score_repr,url="javascript:showIntervalMapping('%s', '%s : %s')" % (formName, thisTrait.db.shortname, thisTrait.name), Class="fs12 fwn"), Class="fs12 fwn ffl b1 c222", align='right', nowrap="on"),LRS_score_repr, LRS_score_value))
                        tr.append(TDCell(HT.TD(LRS_score_repr, Class="fs12 fwn b1 c222", align='right', nowrap="on"), LRS_score_repr, LRS_score_value))
                        tr.append(TDCell(HT.TD(LRS_location_repr, Class="fs12 fwn b1 c222"), LRS_location_repr, LRS_location_value))

            if LRS_flag:
                tr.append(TDCell(HT.TD(LRS_score_repr, Class="fs12 fwn b1 c222"), LRS_score_repr, LRS_score_value))
                tr.append(TDCell(HT.TD(LRS_location_repr, Class="fs12 fwn b1 c222"), LRS_location_repr, LRS_location_value))

            repr = '%3.4f' % thisTrait.corr
            tr.append(TDCell(HT.TD(HT.Href(text=repr,url="javascript:showCorrPlot('%s', '%s')" % (formName,thisTrait.name), Class="fs12 fwn"), Class="fs12 fwn b1 c222", align='right',nowrap="on"), repr, abs(thisTrait.corr)))

            repr = '%d' % thisTrait.nOverlap
            tr.append(TDCell(HT.TD(repr, Class="fs12 fwn ffl b1 c222", align='right'),repr,thisTrait.nOverlap))

            repr = webqtlUtil.SciFloat(thisTrait.corrPValue)
            tr.append(TDCell(HT.TD(repr,nowrap='ON', Class="fs12 fwn ffl b1 c222", align='right'),repr,thisTrait.corrPValue))

            tblobj_body.append(tr)

            for ncol, item in enumerate([thisTrait.name, PhenotypeString, thisTrait.authors, thisTrait.year, thisTrait.pubmed_id, LRS_score_repr, LRS_location_repr, thisTrait.corr, thisTrait.nOverlap, thisTrait.corrPValue]):
                worksheet.write([newrow, ncol], item)
            newrow += 1

        return tblobj_body, worksheet, corrScript


    def getTableHeaderForProbeSet(self, method=None, worksheet=None, newrow=None, headingStyle=None):

        tblobj_header = []

        if method in ["1","3","4"]:
            tblobj_header = [[THCell(HT.TD(' ', Class="fs13 fwb ffl b1 cw cbrb",nowrap='ON'), sort=0),
                              THCell(HT.TD('Record',HT.BR(), 'ID',HT.BR(), Class="fs13 fwb ffl b1 cw cbrb"), text="Record ID", idx=1),
                              THCell(HT.TD('Gene',HT.BR(), 'ID',HT.BR(), Class="fs13 fwb ffl b1 cw cbrb"), text="Gene ID", idx=2),
                              THCell(HT.TD('Homologene',HT.BR(), 'ID',HT.BR(), Class="fs13 fwb ffl b1 cw cbrb"), text="Homologene ID", idx=3),
                              THCell(HT.TD('Symbol',HT.BR(),HT.BR(), Class="fs13 fwb ffl b1 cw cbrb"), text="Symbol", idx=4),
                              THCell(HT.TD('Description',HT.BR(),HT.BR(), Class="fs13 fwb ffl b1 cw cbrb"), text="Description", idx=5),
                              THCell(HT.TD('Location',HT.BR(), 'Chr and Mb', HT.BR(), Class="fs13 fwb ffl b1 cw cbrb"), text="Location (Chr: Mb)", idx=6),
                              THCell(HT.TD('Mean',HT.BR(),'Expr',HT.BR(), Class="fs13 fwb ffl b1 cw cbrb"), text="Mean Expr", idx=7),
                              THCell(HT.TD('Max',HT.BR(),'LRS',HT.BR(), Class="fs13 fwb ffl b1 cw cbrb", nowrap='ON'), text="Max LRS", idx=8),
                              THCell(HT.TD('Max LRS Location',HT.BR(),'Chr and Mb',HT.BR(), Class="fs13 fwb ffl b1 cw cbrb", nowrap='ON'), text="Max LRS Location (Chr: Mb)", idx=9),
                              THCell(HT.TD(HT.Href(
                                                   text = HT.Span('Sample',HT.BR(), 'r', HT.Sup('  ?', style="color:#f00"),HT.BR(), Class="fs13 fwb ffl cw"),
                                                   target = '_blank',
                                                   url = "/correlationAnnotation.html#genetic_r"),
                                           Class="fs13 fwb ffl b1 cw cbrb", nowrap='ON'), text="Sample r", idx=10),
                              THCell(HT.TD('N',HT.BR(),'Cases',HT.BR(), Class="fs13 fwb ffl b1 cw cbrb"), text="N Cases", idx=11),
                              THCell(HT.TD(HT.Href(
                                                   text = HT.Span('Sample',HT.BR(), 'p(r)', HT.Sup('  ?', style="color:#f00"),HT.BR(), Class="fs13 fwb ffl cw"),
                                                   target = '_blank',
                                                   url = "/correlationAnnotation.html#genetic_p_r"),
                                           Class="fs13 fwb ffl b1 cw cbrb", nowrap='ON'), text="Sample p(r)", idx=12),
                              THCell(HT.TD(HT.Href(
                                                   text = HT.Span('Lit',HT.BR(), 'Corr', HT.Sup('  ?', style="color:#f00"),HT.BR(), Class="fs13 fwb ffl cw"),
                                                   target = '_blank',
                                                   url = "/correlationAnnotation.html#literatureCorr"),
                                           Class="fs13 fwb ffl b1 cw cbrb", nowrap='ON'), text="Lit Corr", idx=13),
                              #XZ, 09/22/2008: tissue correlation
                              THCell(HT.TD(HT.Href(
                                                   text = HT.Span('Tissue',HT.BR(), 'r', HT.Sup('  ?', style="color:#f00"),HT.BR(), Class="fs13 fwb ffl cw"),
                                                   target = '_blank',
                                                   url = "/correlationAnnotation.html#tissue_r"),
                                           Class="fs13 fwb ffl b1 cw cbrb", nowrap='ON'), text="Tissue r", idx=14),
                              THCell(HT.TD(HT.Href(
                                                   text = HT.Span('Tissue',HT.BR(), 'p(r)', HT.Sup('  ?', style="color:#f00"),HT.BR(), Class="fs13 fwb ffl cw"),
                                                   target = '_blank',
                                                   url = "/correlationAnnotation.html#tissue_p_r"),
                                           Class="fs13 fwb ffl b1 cw cbrb", nowrap='ON'), text="Tissue p(r)", idx=15)]]

            for ncol, item in enumerate(['Record', 'Gene ID', 'Homologene ID', 'Symbol', 'Description', 'Location (Chr: Mb)', 'Mean Expr', 'Max LRS', 'Max LRS Location (Chr: Mb)', 'Sample r', 'N Cases', 'Sample p(r)', 'Lit Corr', 'Tissue r', 'Tissue p(r)']):
                worksheet.write([newrow, ncol], item, headingStyle)
                worksheet.set_column([ncol, ncol], 2*len(item))
        else:
            tblobj_header = [[THCell(HT.TD(' ', Class="fs13 fwb ffl b1 cw cbrb",nowrap='ON'), sort=0),
                              THCell(HT.TD('Record',HT.BR(), 'ID',HT.BR(), Class="fs13 fwb ffl b1 cw cbrb"), text="Record ID", idx=1),
                              THCell(HT.TD('Gene',HT.BR(), 'ID',HT.BR(), Class="fs13 fwb ffl b1 cw cbrb"), text="Gene ID", idx=2),
                              THCell(HT.TD('Homologene',HT.BR(), 'ID',HT.BR(), Class="fs13 fwb ffl b1 cw cbrb"), text="Homologene ID", idx=3),
                              THCell(HT.TD('Symbol',HT.BR(),HT.BR(), Class="fs13 fwb ffl b1 cw cbrb"), text="Symbol", idx=4),
                              THCell(HT.TD('Description',HT.BR(),HT.BR(), Class="fs13 fwb ffl b1 cw cbrb"), text="Description", idx=5),
                              THCell(HT.TD('Location',HT.BR(), 'Chr and Mb', HT.BR(), Class="fs13 fwb ffl b1 cw cbrb"), text="Location (Chr: Mb)", idx=6),
                              THCell(HT.TD('Mean',HT.BR(),'Expr',HT.BR(), Class="fs13 fwb ffl b1 cw cbrb"), text="Mean Expr", idx=7),
                              THCell(HT.TD('Max',HT.BR(),'LRS',HT.BR(), Class="fs13 fwb ffl b1 cw cbrb", nowrap='ON'), text="Max LRS", idx=8),
                              THCell(HT.TD('Max LRS Location',HT.BR(),'Chr and Mb',HT.BR(), Class="fs13 fwb ffl b1 cw cbrb", nowrap='ON'), text="Max LRS Location (Chr: Mb)", idx=9),
                              THCell(HT.TD(HT.Href(
                                                   text = HT.Span('Sample',HT.BR(), 'rho', HT.Sup('  ?', style="color:#f00"),HT.BR(), Class="fs13 fwb ffl cw"),
                                                   target = '_blank',
                                                   url = "/correlationAnnotation.html#genetic_rho"),
                                           Class="fs13 fwb ffl b1 cw cbrb", nowrap='ON'), text="Sample rho", idx=10),
                              THCell(HT.TD('N',HT.BR(),'Cases',HT.BR(), Class="fs13 fwb ffl b1 cw cbrb"), text="N Cases", idx=11),
                              THCell(HT.TD(HT.Href(
                                                   text = HT.Span('Sample',HT.BR(), 'p(rho)', HT.Sup('  ?', style="color:#f00"),HT.BR(), Class="fs13 fwb ffl cw"),
                                                   target = '_blank',
                                                   url = "/correlationAnnotation.html#genetic_p_rho"),
                                           Class="fs13 fwb ffl b1 cw cbrb", nowrap='ON'), text="Sample p(rho)", idx=12),
                              THCell(HT.TD(HT.Href(
                                                   text = HT.Span('Lit',HT.BR(), 'Corr', HT.Sup('  ?', style="color:#f00"),HT.BR(), Class="fs13 fwb ffl cw"),
                                                   target = '_blank',
                                                   url = "/correlationAnnotation.html#literatureCorr"),
                                           Class="fs13 fwb ffl b1 cw cbrb", nowrap='ON'), text="Lit Corr", idx=13),
                              #XZ, 09/22/2008: tissue correlation
                              THCell(HT.TD(HT.Href(
                                                   text = HT.Span('Tissue',HT.BR(), 'rho', HT.Sup('  ?', style="color:#f00"),HT.BR(), Class="fs13 fwb ffl cw"),
                                                   target = '_blank',
                                                   url = "/correlationAnnotation.html#tissue_r"),
                                           Class="fs13 fwb ffl b1 cw cbrb", nowrap='ON'), text="Tissue rho", idx=14),
                              THCell(HT.TD(HT.Href(
                                                   text = HT.Span('Tissue',HT.BR(), 'p(rho)', HT.Sup('  ?', style="color:#f00"),HT.BR(), Class="fs13 fwb ffl cw"),
                                                   target = '_blank',
                                                   url = "/correlationAnnotation.html#tissue_p_r"),
                                           Class="fs13 fwb ffl b1 cw cbrb", nowrap='ON'), text="Tissue p(rho)", idx=15)]]

            for ncol, item in enumerate(['Record ID', 'Gene ID', 'Homologene ID', 'Symbol', 'Description', 'Location (Chr: Mb)', 'Mean Expr', 'Max LRS', 'Max LRS Location (Chr: Mb)', 'Sample rho', 'N Cases', 'Sample p(rho)', 'Lit Corr', 'Tissue rho', 'Tissue p(rho)']):
                worksheet.write([newrow, ncol], item, headingStyle)
                worksheet.set_column([ncol, ncol], 2*len(item))

        return tblobj_header, worksheet


    def getTableBodyForProbeSet(self, traitList=[], primaryTrait=None, formName=None, worksheet=None, newrow=None, corrScript=None, species=''):

        tblobj_body = []

        for thisTrait in traitList:

            if thisTrait.symbol:
                pass
            else:
                thisTrait.symbol = "--"

            if thisTrait.geneid:
                symbolurl = HT.Href(text=thisTrait.symbol,target='_blank',url="http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?db=gene&cmd=Retrieve&dopt=Graphics&list_uids=%s" % thisTrait.geneid, Class="fs12 fwn")
            else:
                symbolurl = HT.Href(text=thisTrait.symbol,target='_blank',url="http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?CMD=search&DB=gene&term=%s" % thisTrait.symbol, Class="fs12 fwn")

            tr = []

            trId = str(thisTrait)

            corrScript.append('corrArray["%s"] = {corr:%1.4f};' % (trId, thisTrait.corr))

            #XZ, 12/08/2008: checkbox
            tr.append(TDCell(HT.TD(HT.Input(type="checkbox", Class="checkbox", name="searchResult",value=trId, onClick="highlight(this)"), nowrap="on", Class="fs12 fwn ffl b1 c222"), text=trId))

            #XZ, 12/08/2008: probeset name
            tr.append(TDCell(HT.TD(HT.Href(text=thisTrait.name,url="javascript:showTrait('%s', '%s')" % (formName,thisTrait.name), Class="fs12 fwn"), Class="fs12 fwn b1 c222"), thisTrait.name, thisTrait.name.upper()))

            #XZ, 12/08/2008: gene id
            if thisTrait.geneid:
                tr.append(TDCell(None, thisTrait.geneid, val=999))
            else:
                tr.append(TDCell(None, thisTrait.geneid, val=999))

            #XZ, 12/08/2008: homologene id
            if thisTrait.homologeneid:
                tr.append(TDCell("", thisTrait.homologeneid, val=999))
            else:
                tr.append(TDCell("", thisTrait.homologeneid, val=999))

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

            #XZ: trait_location_value is used for sorting
            trait_location_repr = '--'
            trait_location_value = 1000000

            if thisTrait.chr and thisTrait.mb:
                try:
                    trait_location_value = int(thisTrait.chr)*1000 + thisTrait.mb
                except:
                    if thisTrait.chr.upper() == 'X':
                        trait_location_value = 20*1000 + thisTrait.mb
                    else:
                        trait_location_value = ord(str(thisTrait.chr).upper()[0])*1000 + thisTrait.mb

                trait_location_repr = 'Chr%s: %.6f' % (thisTrait.chr, float(thisTrait.mb) )

            tr.append(TDCell(HT.TD(trait_location_repr, Class="fs12 fwn b1 c222", nowrap="on"), trait_location_repr, trait_location_value))

            """
            #XZ, 12/08/2008: chromosome number
            #XZ, 12/10/2008: use Mbvalue to sort chromosome
            tr.append(TDCell( HT.TD(thisTrait.chr, Class="fs12 fwn b1 c222", align='right'), thisTrait.chr, Mbvalue) )

            #XZ, 12/08/2008: Rob wants 6 digit precision, and we have to deal with that the mb could be None
            if not thisTrait.mb:
                tr.append(TDCell(HT.TD(thisTrait.mb, Class="fs12 fwn b1 c222",align='right'), thisTrait.mb, Mbvalue))
            else:
                tr.append(TDCell(HT.TD('%.6f' % thisTrait.mb, Class="fs12 fwn b1 c222", align='right'), thisTrait.mb, Mbvalue))
            """



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

            #LRS and its location
            LRS_score_repr = '--'
            LRS_score_value = 0
            LRS_location_repr = '--'
            LRS_location_value = 1000000
            LRS_flag = 1

            #Max LRS and its Locus location
            if thisTrait.lrs and thisTrait.locus:
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

                        #tr.append(TDCell(HT.TD(HT.Href(text=LRS_score_repr,url="javascript:showIntervalMapping('%s', '%s : %s')" % (formName, thisTrait.db.shortname, thisTrait.name), Class="fs12 fwn"), Class="fs12 fwn ffl b1 c222", align='right', nowrap="on"),LRS_score_repr, LRS_score_value))
                        tr.append(TDCell(HT.TD(LRS_score_repr, Class="fs12 fwn b1 c222", align='right', nowrap="on"), LRS_score_repr, LRS_score_value))
                        tr.append(TDCell(HT.TD(LRS_location_repr, Class="fs12 fwn b1 c222", nowrap="on"), LRS_location_repr, LRS_location_value))

            if LRS_flag:
                tr.append(TDCell(HT.TD(LRS_score_repr, Class="fs12 fwn b1 c222"), LRS_score_repr, LRS_score_value))
                tr.append(TDCell(HT.TD(LRS_location_repr, Class="fs12 fwn b1 c222"), LRS_location_repr, LRS_location_value))


            #XZ, 12/08/2008: generic correlation
            repr='%3.3f' % thisTrait.corr
            tr.append(TDCell(HT.TD(HT.Href(text=repr, url="javascript:showCorrPlot('%s', '%s')" % (formName, thisTrait.name), Class="fs12 fwn ffl"), Class="fs12 fwn ffl b1 c222", align='right'),repr,abs(thisTrait.corr)))

            #XZ, 12/08/2008: number of overlaped cases
            repr = '%d' % thisTrait.nOverlap
            tr.append(TDCell(HT.TD(repr, Class="fs12 fwn ffl b1 c222", align='right'),repr,thisTrait.nOverlap))

            #XZ, 12/08/2008: p value of genetic correlation
            repr = webqtlUtil.SciFloat(thisTrait.corrPValue)
            tr.append(TDCell(HT.TD(repr,nowrap='ON', Class="fs12 fwn ffl b1 c222", align='right'),repr,thisTrait.corrPValue))

            #XZ, 12/08/2008: literature correlation
            LCorr = 0.0
            LCorrStr = "--"
            if hasattr(thisTrait, 'LCorr') and thisTrait.LCorr:
                LCorr = thisTrait.LCorr
                LCorrStr = "%2.3f" % thisTrait.LCorr
            tr.append(TDCell(HT.TD(LCorrStr, Class="fs12 fwn b1 c222", align='right'), LCorrStr, abs(LCorr)))

            #XZ, 09/22/2008: tissue correlation.
            TCorr = 0.0
            TCorrStr = "--"
            #XZ, 11/20/2008: need to pass two geneids: input_trait_mouse_geneid and thisTrait.mouse_geneid
            if hasattr(thisTrait, 'tissueCorr') and thisTrait.tissueCorr:
                TCorr = thisTrait.tissueCorr
                TCorrStr = "%2.3f" % thisTrait.tissueCorr
                # NL, 07/19/2010: add a new parameter rankOrder for js function 'showTissueCorrPlot'
                rankOrder = self.RANK_ORDERS[self.method]
                TCorrPlotURL = "javascript:showTissueCorrPlot('%s','%s','%s',%d)" %(formName, primaryTrait.symbol, thisTrait.symbol,rankOrder)
                tr.append(TDCell(HT.TD(HT.Href(text=TCorrStr, url=TCorrPlotURL, Class="fs12 fwn ff1"), Class="fs12 fwn ff1 b1 c222", align='right'), TCorrStr, abs(TCorr)))
            else:
                tr.append(TDCell(HT.TD(TCorrStr, Class="fs12 fwn b1 c222", align='right'), TCorrStr, abs(TCorr)))

            #XZ, 12/08/2008: p value of tissue correlation
            TPValue = 1.0
            TPValueStr = "--"
            if hasattr(thisTrait, 'tissueCorr') and thisTrait.tissuePValue: #XZ, 09/22/2008: thisTrait.tissuePValue can't be used here because it could be 0
                TPValue = thisTrait.tissuePValue
                TPValueStr = "%2.3f" % thisTrait.tissuePValue
            tr.append(TDCell(HT.TD(TPValueStr, Class="fs12 fwn b1 c222", align='right'), TPValueStr, TPValue))

            tblobj_body.append(tr)

            for ncol, item in enumerate([thisTrait.name, thisTrait.geneid, thisTrait.homologeneid, thisTrait.symbol, thisTrait.description, trait_location_repr, mean, LRS_score_repr, LRS_location_repr, thisTrait.corr, thisTrait.nOverlap, thisTrait.corrPValue, LCorr, TCorr, TPValue]):
                worksheet.write([newrow, ncol], item)

            newrow += 1

        return tblobj_body, worksheet, corrScript


def calCorrelation(values_1, values_2):
    N = Math.min(len(values_1), len(values_2))
    X = []
    Y = []
    for i in range(N):
        if values_1[i]!= None and values_2[i]!= None:
            X.append(values_1[i])
            Y.append(values_2[i])
    NN = len(X)
    if NN <6:
        return (0.0,NN)
    sx = reduce(lambda x,y:x+y,X,0.0)
    sy = reduce(lambda x,y:x+y,Y,0.0)
    x_mean = sx/NN
    y_mean = sy/NN
    xyd = 0.0
    sxd = 0.0
    syd = 0.0
    for i in range(NN):
        xyd += (X[i] - x_mean)*(Y[i] - y_mean)
        sxd += (X[i] - x_mean)*(X[i] - x_mean)
        syd += (Y[i] - y_mean)*(Y[i] - y_mean)
    try:
        corr = xyd/(sqrt(sxd)*sqrt(syd))
    except:
        corr = 0
    return (corr, NN)
