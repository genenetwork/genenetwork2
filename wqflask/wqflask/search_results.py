from __future__ import absolute_import, division, print_function

from wqflask import app

from flask import render_template

###################################################
#                                                 #
# This file uses only spaces for indentation      #
#                                                 #
###################################################

import string
import os
import cPickle
import re
from math import *
import time
#import pyXLWriter as xl
#import pp - Note from Sam: is this used?
import math
import datetime

from pprint import pformat as pf

# Instead of importing HT we're going to build a class below until we can eliminate it
from htmlgen import HTMLgen2 as HT

from base import webqtlConfig
from utility.THCell import THCell
from utility.TDCell import TDCell
from base.webqtlDataset import webqtlDataset
from base.webqtlTrait import webqtlTrait
from base.templatePage import templatePage
from wqflask import parser
from utility import webqtlUtil
from dbFunction import webqtlDatabaseFunction

from utility import formatting

import sys


#from base.JinjaPage import JinjaEnv, JinjaPage



class SearchResultPage(templatePage):

    maxReturn = 3000
    #NPerPage = 100
    nkeywords = 0

    def __init__(self, fd):
        print("initing SearchResultPage")
        import logging_tree
        logging_tree.printout()
        self.fd = fd
        templatePage.__init__(self, fd)
        assert self.openMysql(), "Couldn't open MySQL"

        print("fd is:", pf(fd))
        self.dataset = fd['dataset']

        # change back to self.dataset
        if not self.dataset or self.dataset == 'spacer':
            #Error, No dataset selected
            heading = "Search Result"
            detail = ['''No dataset was selected for this search, please
                go back and SELECT at least one dataset.''']
            self.error(heading=heading,detail=detail,error="No dataset Selected")
            return

        ###########################################
        #   Names and IDs of RISet / F2 set
        ###########################################
        if self.dataset == "All Phenotypes":
            self.cursor.execute("""
                select PublishFreeze.Name, InbredSet.Name, InbredSet.Id from PublishFreeze,
                InbredSet where PublishFreeze.Name not like 'BXD300%' and InbredSet.Id =
                PublishFreeze.InbredSetId""")
            results = self.cursor.fetchall()
            self.dataset = map(lambda x: webqtlDataset(x[0], self.cursor), results)
            self.dataset_groups = map(lambda x: x[1], results)
            self.dataset_group_ids = map(lambda x: x[2], results)
            self.single_group = False
        else:
            print("self.dataset is:", pf(self.dataset))
            self.dataset = webqtlDataset(self.dataset, self.cursor)
            print("self.dataset is now:", pf(self.dataset))
            #self.dataset = map(lambda x: webqtlDataset(x, self.cursor), self.dataset)
            #currently, webqtl won't allow multiple crosses
            #for other than multiple publish db search
            #so we can use the first dataset as example
            #if self.dataset.type=="Publish":
            #    pass
            if self.dataset.type in ("Geno", "ProbeSet"):

                #userExist = None
                # Can't use paramater substitution for table names apparently
                db_type = self.dataset.type + "Freeze"
                print("db_type [%s]: %s" % (type(db_type), db_type))

                query = '''SELECT Id, Name, FullName, confidentiality,
                                    AuthorisedUsers FROM %s WHERE Name = %%s''' % (db_type)

                self.cursor.execute(query, self.dataset.name)

                (indId,
                 indName,
                 indFullName,
                 confidential,
                 AuthorisedUsers) = self.cursor.fetchall()[0]

                if confidential:
                    # Allow confidential data later
                    NoConfindetialDataForYouTodaySorry
                    #access_to_confidential_dataset = 0
                    #
                    ##for the dataset that confidentiality is 1
                    ##1. 'admin' and 'root' can see all of the dataset
                    ##2. 'user' can see the dataset that AuthorisedUsers contains his id(stored in the Id field of User table)
                    #if webqtlConfig.USERDICT[self.privilege] > webqtlConfig.USERDICT['user']:
                    #    access_to_confidential_dataset = 1
                    #else:
                    #    AuthorisedUsersList=AuthorisedUsers.split(',')
                    #    if AuthorisedUsersList.__contains__(self.userName):
                    #        access_to_confidential_dataset = 1
                    #
                    #if not access_to_confidential_dataset:
                    #    #Error, No dataset selected
                    #    heading = "Search Result"
                    #    detail = ["The %s dataset you selected is not open to the public at this time, please go back and SELECT other dataset." % indFullName]
                    #    self.error(heading=heading,detail=detail,error="Confidential dataset")
                    #    return
            #else:
            #    heading = "Search Result"
            #    detail = ['''The dataset has not been established yet, please
            #        go back and SELECT at least one dataset.''']
            #    self.error(heading=heading,detail=detail,error="No dataset Selected")
            #    return

            self.dataset.get_group()
            self.single_group = True
            #XZ, August 24,2010: Since self.single_group = True, it's safe to assign one species Id.
            self.species_id = webqtlDatabaseFunction.retrieveSpeciesId(self.cursor,
                                                                       self.dataset.group)

        ###########################################
        #    make sure search from same type of datasets
        ###########################################
        #dbTypes = map(lambda X: X.type, self.dataset)
        #db_types = [table.type for table in self.dataset]
        #self.db_type = db_types[0]
        #for item in dbTypes:
        #    if item != self.dbType:
        #        heading = "Search Result"
        #        detail = ["Search can only be performed among the same type of datasets"]
        #        self.error(heading=heading,detail=detail,error="Error")
        #        return


        #self.db_type = self.dataset.type
        if self.dataset.type == "Publish":
            self.search_fields = ['Phenotype.Post_publication_description',
                                'Phenotype.Pre_publication_description',
                                'Phenotype.Pre_publication_abbreviation',
                                'Phenotype.Post_publication_abbreviation',
                                'Phenotype.Lab_code',
                                'Publication.PubMed_ID',
                                'Publication.Abstract',
                                'Publication.Title',
                                'Publication.Authors',
                                'PublishXRef.Id']

        elif self.dataset.type == "ProbeSet":
            self.search_fields = ['Name',
                                'Description',
                                'Probe_Target_Description',
                                'Symbol',
                                'Alias',
                                'GenbankId',
                                'UniGeneId',
                                'RefSeq_TranscriptId']
            self.header_fields = ['',
                                'ID',
                                'Symbol',
                                'Description',
                                'Location',
                                'Mean Expr',
                                'Max LRS',
                                'Max LRS Location']
        elif self.dataset.type == "Geno":
            self.search_fields = ['Name','Chr']


        self.do_search()
        self.gen_search_result()

        ###########################################
        #       Search Options
        ###########################################
        #self.matchwhole = fd['matchwhole']
        #split result into pages
        #self.pageNumber = fd.get('pageno', 0)
        #
        #try:
        #    self.pageNumber = int(self.pageNumber)
        #except Exception as why:
        #    print(why)
        #    self.pageNumber = 0


        ###########################################
        #       Generate Mysql Query
        ###########################################

        # Sam: We presume lines below aren't used...
        #geneIdListQuery = fd.get('geneId', '')
        #if geneIdListQuery:
        #    geneIdListQuery = string.replace(geneIdListQuery, ",", " ")
        #    geneIdListQuery = " geneId=%s" % string.join(string.split(geneIdListQuery), "-")

        #self.ANDkeyword = fd.get('ANDkeyword', "")
        #self.ORkeyword = fd.get('ORkeyword', "")

        #self.ORkeyword += geneIdListQuery

        #self.ANDkeyword = self.ANDkeyword.replace("\\", "").strip()
        #self.ORkeyword = self.ORkeyword.replace("\\", "").strip()
        #user defined sort option
        #self.orderByUserInput = fd.get('orderByUserInput', "").strip()
        #default sort option if user have not defined
        #self.orderByDefalut = ""

        #XZ, Dec/16/2010: I add examples to help understand this block of code. See details in function pattersearch.
        #
        ##XZ: self._1mPattern examples: WIKI=xxx, RIF=xxx, GO:0045202
        #self._1mPattern = re.compile('\s*(\S+)\s*[:=]\s*([a-zA-Z-\+\d\.]+)\s*')
        #
        ##XZ: self._2mPattern examples: Mean=(15.0 16.0), Range=(10 100), LRS=(Low_LRS_limit, High_LRS_limit), pvalue=(Low_limit, High_limit), Range=(10 100)
        #self._2mPattern = re.compile('\s*(\S+)\s*[=in]{1,2}\s*\(\s*([-\d\.]+)[, \t]+([-\d\.]+)[, \t]*([-\d\.]*)\s*\)')
        #
        ##XZ: self._3mPattern examples: Position=(Chr1 98 104), Pos=(Chr1 98 104), Mb=(Chr1 98 104), CisLRS=(Low_LRS_limit, High_LRS_limit, Mb_buffer), TransLRS=(Low_LRS_limit, High_LRS_limit, Mb_buffer)
        #self._3mPattern = re.compile('\s*(\S+)\s*[=in]{1,2}\s*\(\s*[Cc][Hh][Rr]([^, \t]+)[, \t]+([-\d\.]+)[, \t]+([-\d\.]+)\s*\)')
        #
        ##XZ: self._5mPattern examples: LRS=(Low_LRS_limit, High_LRS_limit, ChrNN, Mb_Low_Limit, Mb_High_Limit)
        #self._5mPattern = re.compile('\s*(\S+)\s*[=in]{1,2}\s*\(\s*([-\d\.]+)[, \t]+([-\d\.]+)[, \t]+[Cc][Hh][Rr]([^, \t]+)[, \t]+([-\d\.]+)[, \t]+([-\d\.]+)\s*\)')

        #Error, No keyword input
        #if not (self.ORkeyword or self.ANDkeyword):
        #    heading = "Search Result"
        #    detail = ["Please make sure to enter either your search terms (genes, traits, markers), or advanced search commands."]
        #    self.error(heading=heading,detail=detail,error="No search terms were entered")
        #    return

        #query clauses
        #self.ANDQuery = []
        #self.ORQuery = []
        ##descriptions, one for OR search, one for AND search
        #self.ANDDescriptionText = []
        #self.ORDescriptionText = []

        #if not self.normalSearch():
        #    return
        #if not self.patternSearch():
        #    return
        #if not self.assembleQuery():
        #    return
        #self.nresults = self.executeQuery()
        #
        #if len(self.dataset) > 1:
        #    dbUrl =  "Multiple phenotype datasets"
        #    dbUrlLink = " were"
        #else:
        #    dbUrl =  self.dataset[0].genHTML()
        #    dbUrlLink = " was"

        #SearchText = HT.Blockquote('GeneNetwork searched the ', dbUrl, ' for all records ')
        #if self.ORkeyword2:
        #    NNN = len(self.ORkeyword2)
        #    if NNN > 1:
        #        SearchText.append(' that match the terms ')
        #    else:
        #        SearchText.append(' that match the term ')
        #    for j, term in enumerate(self.ORkeyword2):
        #        SearchText.append(HT.U(term))
        #        if NNN > 1 and j < NNN-2:
        #            SearchText.append(", ")
        #        elif j == NNN-2:
        #            SearchText.append(", or ")
        #        else:
        #            pass
        #if self.ORDescriptionText:
        #    if self.ORkeyword2:
        #        SearchText.append("; ")
        #    else:
        #        SearchText.append(" ")
        #    for j, item in enumerate(self.ORDescriptionText):
        #        SearchText.append(item)
        #        if j < len(self.ORDescriptionText) -1:
        #            SearchText.append(";")
        #
        #if (self.ORkeyword2 or self.ORDescriptionText) and (self.ANDkeyword2 or self.ANDDescriptionText):
        #    SearchText.append("; ")
        #if self.ANDkeyword2:
        #    if (self.ORkeyword2 or self.ORDescriptionText):
        #        SearchText.append(' records')
        #    NNN = len(self.ANDkeyword2)
        #    if NNN > 1:
        #        SearchText.append(' that match the terms ')
        #    else:
        #        SearchText.append(' that match the term ')
        #    for j, term in enumerate(self.ANDkeyword2):
        #        SearchText.append(HT.U(term))
        #        if NNN > 1 and j < NNN-2:
        #            SearchText.append(", ")
        #        elif j == NNN-2:
        #            SearchText.append(", and ")
        #        else:
        #            pass
        #if self.ANDDescriptionText:
        #    if self.ANDkeyword2:
        #        SearchText.append(" and ")
        #    else:
        #        SearchText.append(" ")
        #    for j, item in enumerate(self.ANDDescriptionText):
        #        SearchText.append(item)
        #        if j < len(self.ANDDescriptionText) -1:
        #            SearchText.append(" and ")
        #
        #SearchText.append(". ")
        #if self.nresults == 0:
        #    heading = "Search Result"
        #    detail = ["Sorry, GeneNetwork did not find any records matching your request. Please check the syntax or try the ANY rather than the ALL field."]
        #    self.error(heading=heading,intro = SearchText.contents,detail=detail,error="Not Found")
        #    return
        #elif self.nresults == 1:
        #    SearchText.append(HT.P(), 'GeneNetwork found one record that matches your request. To study this record, click on its text below. To add this record to your Selection window, use the checkbox and then click the ', HT.Strong('Add to Collection'),' button. ')
        #elif self.nresults >= 1 and self.nresults <= self.maxReturn:
        #    SearchText.append(HT.P(), 'GeneNetwork found a total of ', HT.Span(self.nresults, Class='fwb cr'), ' records. To study any one of these records, click on its ID below. To add one or more records to your Selection window, use the checkbox and then click the ' , HT.Strong('Add to Collection'),' button. ')
        #else:
        #    SearchText.append(' A total of ',HT.Span(self.nresults, Class='fwb cr'), ' records were found.')
        #    heading = "Search Result"
        #    # Modified by Hongqiang Li
        #    # detail = ["The terms you entered match %d records. Please modify your search to generate %d or fewer matches, or review  " % (self.nresults, self.maxReturn), HT.Href(text='Search Help', target='_blank',  url='http://web2qtl.utmem.edu/searchHelp.html', Class='fs14'), " to learn more about syntax and the use of wildcard characters."]
        #    detail = ["The terms you entered match %d records. Please modify your search to generate %d or fewer matches, or review  " % (self.nresults, self.maxReturn), HT.Href(text='Search Help', target='_blank',  url='%s/searchHelp.html' % webqtlConfig.PORTADDR, Class='fs14'), " to learn more about syntax and the use of wildcard characters."]
        #    #
        #    self.error(heading=heading,intro = SearchText.contents,detail=detail,error="Over %d" % self.maxReturn)
        #    return


        #TD_LR.append(HT.Paragraph('Search Results', Class="title"), SearchText)

        #self.dict['body'] = str(TD_LR)
        #self.dict['js1'] = ''
        #self.dict['js2'] = 'onLoad="pageOffset()"'
        #self.dict['layer'] = self.generateWarningLayer()


    def gen_search_result(self):

        #pageTable = HT.TableLite(cellSpacing=2,cellPadding=0,width="100%",border=0)

        #last_result = False

        self.trait_list = []
        # result_set represents the results for each search term; a search of 
        # "shh grin2b" would have two sets of results, one for each term
        for result_set in self.results:
            for result in result_set:
                if not result:
                    continue
                #last_result = False

                seq = 1
                group = self.dataset.group
                self.form_name = form_name = 'show_dataset_'+group

                tblobj = {}
                species = webqtlDatabaseFunction.retrieveSpecies(cursor=self.cursor, RISet=group)

                #### Excel file 

                # Todo: Replace this with official Python temp file naming functions?
                filename= webqtlUtil.genRandStr("Search_")
                #xlsUrl = HT.Input(type='button', value = 'Download Table', onClick= "location.href='/tmp/%s.xls'" % filename, Class='button')
                # Create a new Excel workbook
                #workbook = xl.Writer('%s.xls' % (webqtlConfig.TMPDIR+filename))
                #headingStyle = workbook.add_format(align = 'center', bold = 1, border = 1, size=13, fg_color = 0x1E, color="white")

                #XZ, 3/18/2010: pay attention to the line number of header in this file. As of today, there are 7 lines.
                #worksheet = self.createExcelFileWithTitleAndFooter(workbook=workbook, db=this_trait.db, returnNumber=len(self.trait_list))
                newrow = 7

                #### Excel file stuff stops

                if self.dataset.type == "ProbeSet":
                    #for item in result:
                    print("foo locals are:", locals())
                    probe_set_id = result[1]
                    print("probe_set_id is:", pf(probe_set_id))
                    this_trait = webqtlTrait(db=self.dataset, name=probe_set_id, cursor=self.cursor)
                    this_trait.retrieveInfo(QTL=True)
                    print("this_trait is:", pf(this_trait))
                    self.trait_list.append(this_trait)
                    print("self.trait_list is:", pf(self.trait_list))

                    #tblobj['header'] = self.getTableHeaderForProbeSet(worksheet=worksheet, newrow=newrow, headingStyle=headingStyle)

                    #newrow += 1

                    sortby = self.getSortByValue(datasetType="ProbeSet")

                    tblobj['body'] = self.getTableBodyForProbeSet(trait_list=self.trait_list, formName=self.form_name, newrow=newrow, species=species)

                    #workbook.close()
                    #objfile = open('%s.obj' % (webqtlConfig.TMPDIR+filename), 'wb')
                    #cPickle.dump(tblobj, objfile)
                    #objfile.close()

                    #div = HT.Div(webqtlUtil.genTableObj(tblobj, filename, sortby), Id="sortable")

                    #pageTable.append(HT.TR(HT.TD(div)))
                elif self.dataset.type == "Publish":
                    #tblobj['header'] = self.getTableHeaderForPublish(worksheet=worksheet, newrow=newrow, headingStyle=headingStyle)

                    #newrow += 1

                    sortby = self.getSortByValue(datasetType="Publish")

                    #tblobj['body'] = self.getTableBodyForPublish(trait_list=self.trait_list, formName=mainfmName, worksheet=worksheet, newrow=newrow, species=species)

                    #workbook.close()
                    #objfile = open('%s.obj' % (webqtlConfig.TMPDIR+filename), 'wb')
                    #cPickle.dump(tblobj, objfile)
                    #objfile.close()

                    #div = HT.Div(webqtlUtil.genTableObj(tblobj, filename, sortby), Id="sortable")

                    #pageTable.append(HT.TR(HT.TD(div)))                    
                elif self.dataset.type == "Geno":
                    tblobj['header'] = self.getTableHeaderForGeno(worksheet=worksheet, newrow=newrow, headingStyle=headingStyle)

                    newrow += 1
                    sortby = self.getSortByValue(datasetType="Geno")

                    #tblobj['body'] = self.getTableBodyForGeno(trait_list=self.trait_list, form_name=form_name, worksheet=worksheet, newrow=newrow)

                    #workbook.close()
                    #objfile = open('%s.obj' % (webqtlConfig.TMPDIR+filename), 'wb')
                    #cPickle.dump(tblobj, objfile)
                    #objfile.close()

                    #div = HT.Div(webqtlUtil.genTableObj(tblobj, filename, sortby), Id="sortable")
                    #
                    #pageTable.append(HT.TR(HT.TD(div)))                    


                #traitForm = HT.Form(cgi= os.path.join(webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE), enctype='multipart/form-data', name=thisFormName, submit=HT.Input(type='hidden'))
                hddn = {'FormID':'showDatabase','ProbeSetID':'_','database':'_','CellID':'_','group':group}
                hddn['incparentsf1']='ON'
            #    for key in hddn.keys():
            #        traitForm.append(HT.Input(name=key, value=hddn[key], type='hidden'))
            #
            #    traitForm.append(HT.P(),pageTable)
            #
            #    TD_LR.append(traitForm)
            #    if len(self.results) > 1 and i < len(self.results) - 1:
            #        last_result = True
            #if last_result:
            #    TD_LR.contents.pop()

    def executeQuery(self):

        ##construct sorting
        if self.dbType == "Publish":
            sortQuery = " order by Publication_PubMed_ID desc, Phenotype_Name, thistable"
        elif self.dbType == "Geno":
            if not self.orderByUserInput:
                if self.orderByDefalut:
                    self.orderByUserInput = self.orderByDefalut
                else:
                    self.orderByUserInput = "POSITION"
                if self.orderByUserInput.upper() in ["POS", "POSITION", "MB"]:
                    self.orderByUserInput = "POSITION"
                else:
                    pass
            self.orderByUserInput = self.orderByUserInput.upper()
            self.orderByUserInputOrig = self.orderByUserInput[:]
            if self.orderByUserInput == "NAME":
                sortQuery = " order by Geno_Name, Geno_chr_num, Geno_Mb"
            elif self.orderByUserInput == "SOURCE":
                sortQuery = " order by Geno_Source2, Geno_chr_num, Geno_Mb"
            else:
                sortQuery = " order by Geno_chr_num, Geno_Mb"
        #ProbeSet
        else:
            if not self.orderByUserInput:
                if self.orderByDefalut:
                    self.orderByUserInput = self.orderByDefalut
                else:
                    self.orderByUserInput = "POSITION"

            self.orderByUserInput = self.orderByUserInput.upper()
            self.orderByUserInputOrig = self.orderByUserInput[:]
            #XZ: 8/18/2009: "POSITION-"
            if self.orderByUserInput[-1] == '-':
                self.orderByUserInput = self.orderByUserInput[:-1]
                sortDesc = 'desc'
            else:
                sortDesc = ''

            if self.orderByUserInput in  ["MEAN", "LRS", "PVALUE"]:
                #sortQuery = " order by T%s %s, TNAME, thistable desc" % (self.orderByUserInput, sortDesc)
                sortQuery = " order by T%s desc, TNAME, thistable desc" % self.orderByUserInput
            elif self.orderByUserInput in ["POS", "POSITION", "MB"]:
                sortQuery = " order by TCHR_NUM %s, TMB %s, TNAME, thistable desc" % (sortDesc, sortDesc)
            elif self.orderByUserInput == 'SYMBOL':
                sortQuery = " order by TSYMBOL, thistable desc"
            else:
                sortQuery = " order by TNAME_NUM, thistable desc"

        if self.singleCross:
            if len(self.query) > 1:
                searchQuery = map(lambda X:'(%s)' % X, self.query)
                searchQuery = string.join(searchQuery, '  UNION ALL ')
            else:
                searchQuery = self.query[0]
            searchQuery += sortQuery
            #searchCountQuery retrieve all the results
            searchCountQuery = [searchQuery]
            #searchQuery = searchQuery + " limit %d,%d" % (self.pageNumber*self.NPerPage, self.NPerPage) // We removed the page limit - Zach 2/22/11
            searchQuery = [searchQuery]
        else:
            searchCountQuery = searchQuery = map(lambda X: X+sortQuery, self.query)

        allResults = []
        self.results = []
        for item in searchCountQuery:
            start_time = datetime.datetime.now()
            _log.info("Executing query: %s"%(item))
            self.cursor.execute(item)
            allResults.append(self.cursor.fetchall())
            end_time = datetime.datetime.now()
            _log.info("Total time: %s"%(end_time-start_time))

        _log.info("Done executing queries")

        #searchCountQuery retrieve all the results, for counting use only
        if searchCountQuery != searchQuery:
            for item in searchQuery:
                self.cursor.execute(item)
                self.results.append(self.cursor.fetchall())
        else:
            self.results = allResults

        nresults = reduce(lambda Y,X:len(X)+Y, allResults, 0)
        return nresults


    def assembleQuery(self):
        self.query = []
        if self.ANDQuery or self.ORQuery:
            clause = self.ORQuery[:]

            for j, database in enumerate(self.dataset):
                if self.ANDQuery:
                    clause.append(" (%s) " % string.join(self.ANDQuery, " AND "))

                newclause = []

                for item in clause:
                    ##need to retrieve additional field which won't be used
                    ##in the future, for sorting purpose only
                    if self.dbType == "Publish":
                        if item.find("Geno.name") < 0:
                            incGenoTbl = ""
                        else:
                            incGenoTbl = " Geno, "
                        newclause.append("""SELECT %d, PublishXRef.Id,
                                         PublishFreeze.createtime as thistable,
                                         Publication.PubMed_ID as Publication_PubMed_ID,
                                         Phenotype.Post_publication_description as Phenotype_Name
                                         FROM %s PublishFreeze, Publication, PublishXRef,
                                         Phenotype WHERE PublishXRef.InbredSetId = %d and %s and
                                         PublishXRef.PhenotypeId = Phenotype.Id and
                                         PublishXRef.PublicationId = Publication.Id and
                                         PublishFreeze.Id = %d""" % (j, incGenoTbl,
                                         self.dataset_group_ids[j], item, database.id))
                    elif self.dbType == "ProbeSet":
                        if item.find("GOgene") < 0:
                            incGoTbl = ""
                        else:
                            incGoTbl = """ ,db_GeneOntology.term as GOterm,
                            db_GeneOntology.association as GOassociation,
                            db_GeneOntology.gene_product as GOgene_product """
                        if item.find("Geno.name") < 0:
                            incGenoTbl = ""
                        else:
                            incGenoTbl = " Geno, "
                        if item.find("GeneRIF_BASIC.") < 0:
                            incGeneRIFTbl = ""
                        else:
                            incGeneRIFTbl = " GeneRIF_BASIC, "
                        if item.find("GeneRIF.") < 0:
                            incGeneRIFTbl += ""
                        else:
                            incGeneRIFTbl += " GeneRIF, "
                        newclause.append("""SELECT distinct %d, ProbeSet.Name as TNAME, 0 as thistable,
                        ProbeSetXRef.Mean as TMEAN, ProbeSetXRef.LRS as TLRS, ProbeSetXRef.PVALUE as TPVALUE,
                        ProbeSet.Chr_num as TCHR_NUM, ProbeSet.Mb as TMB,  ProbeSet.Symbol as TSYMBOL,
                        ProbeSet.name_num as TNAME_NUM  FROM %s%s ProbeSetXRef, ProbeSet %s
                        WHERE %s and ProbeSet.Id = ProbeSetXRef.ProbeSetId and ProbeSetXRef.ProbeSetFreezeId = %d
                        """ % (j, incGeneRIFTbl, incGenoTbl, incGoTbl, item, database.id))
                    elif self.dbType == "Geno":
                        newclause.append("""SELECT %d, Geno.Name, GenoFreeze.createtime as thistable,
                                         Geno.Name as Geno_Name, Geno.Source2 as Geno_Source2,
                                         Geno.chr_num as Geno_chr_num, Geno.Mb as Geno_Mb FROM
                                         GenoXRef, GenoFreeze, Geno WHERE %s and Geno.Id
                                         = GenoXRef.GenoId and GenoXRef.GenoFreezeId =
                                         GenoFreeze.Id and GenoFreeze.Id = %d""" % (
                                            j, item, database.id))
                    else:
                        pass

                searchQuery = map(lambda X:'(%s)' % X, newclause)
                searchQuery = string.join(searchQuery, '  UNION ')
                self.query.append(searchQuery)
            return 1
        else:
            heading = "Search Result"
            detail = ["No keyword was entered for this search, please go back and enter your keyword."]
            self.error(heading=heading,detail=detail,error="No Keyword")
            return 0


    def do_search(self):
        print("fd.search_terms:", self.fd['search_terms'])
        self.search_terms = parser.parse(self.fd['search_terms'])
        print("After parsing:", self.search_terms)
        
        
        #print("ORkeyword is:", pf(self.ORkeyword))
        #self.ANDkeyword2 = parser.parse(self.ANDkeyword)
        #self.ORkeyword2 = parser.parse(self.ORkeyword)
        #print("ORkeyword2 is:", pf(parser.parse(self.ORkeyword)))

        #self.ANDkeyword2 = re.sub(self._1mPattern, '', self.ANDkeyword)
        #self.ANDkeyword2 = re.sub(self._2mPattern, '', self.ANDkeyword2)
        #self.ANDkeyword2 = re.sub(self._3mPattern, '', self.ANDkeyword2)
        #self.ANDkeyword2 = re.sub(self._5mPattern, '', self.ANDkeyword2)
        ###remove remain parethesis, could be input with  syntax error
        #self.ANDkeyword2 = re.sub(re.compile('\s*\([\s\S]*\)'), '', self.ANDkeyword2)
        #self.ANDkeyword2 = self.encregexp(self.ANDkeyword2)

        #self.ORkeyword2 = re.sub(self._1mPattern, '', self.ORkeyword)
        #self.ORkeyword2 = re.sub(self._2mPattern, '', self.ORkeyword2)
        #self.ORkeyword2 = re.sub(self._3mPattern, '', self.ORkeyword2)
        #self.ORkeyword2 = re.sub(self._5mPattern, '', self.ORkeyword2)
        ###remove remain parethesis, could be input with  syntax error
        #self.ORkeyword2 = re.sub(re.compile('\s*\([\s\S]*\)'), '', self.ORkeyword2)
        #self.ORkeyword2 = self.encregexp(self.ORkeyword2)
                
        self.results = []
        for item in self.search_terms:
            search_term = item['search_term']
        #    self.nkeywords += 1
        #    #ZS: If there are both AND and OR keywords, just use the OR keywords
        #    if k >=len(self.ORkeyword2):
        #        query = self.ANDQuery
        #        DescriptionText = self.ANDDescriptionText
        #        clausejoin = ' OR '
        #        fulltext = ANDFulltext
        #    else:
        #        query = self.ORQuery
        #        DescriptionText = self.ORDescriptionText
        #        clausejoin = ' OR '
        #        fulltext = ORFulltext

            print("item is:", pf(search_term))
            
            
            clause_item = (
""" MATCH (ProbeSet.Name,
        ProbeSet.description,
        ProbeSet.symbol,
        alias,
        GenbankId,
        UniGeneId,
        Probe_Target_Description)
        AGAINST ('%s' IN BOOLEAN MODE) """ % self.db_conn.escape_string(search_term))
            if self.dataset.type == "ProbeSet":
                
                query = (
"""SELECT distinct 0, ProbeSet.Name as TNAME, 0 as thistable,
    ProbeSetXRef.Mean as TMEAN,
    ProbeSetXRef.LRS as TLRS,
    ProbeSetXRef.PVALUE as TPVALUE,
    ProbeSet.Chr_num as TCHR_NUM,
    ProbeSet.Mb as TMB,
    ProbeSet.Symbol as TSYMBOL,
    ProbeSet.name_num as TNAME_NUM
    FROM ProbeSetXRef, ProbeSet
    WHERE %s
        and ProbeSet.Id = ProbeSetXRef.ProbeSetId
        and ProbeSetXRef.ProbeSetFreezeId = %s  
                """ % (self.db_conn.escape_string(search_term),
                       self.db_conn.escape_string(clause_item),
                self.db_conn.escape_string(str(self.dataset.id))))
                
            elif self.dataset.type == "Publish":
                include_geno = ""
                if search_term.find("Geno.name") >= 0:
                    include_geno = " Geno, "
                    
                query = (
"""SELECT 0, PublishXRef.Id, PublishFreeze.createtime as thistable,
    Publication.PubMed_ID as Publication_PubMed_ID,
    Phenotype.Post_publication_description as Phenotype_Name
    FROM %s PublishFreeze, Publication, PublishXRef, Phenotype
    WHERE PublishXRef.InbredSetId = %s and %s and
        PublishXRef.PhenotypeId = Phenotype.Id and
        PublishXRef.PublicationId = Publication.Id and
        PublishFreeze.Id = %s
                """ % (include_geno,
                       self.db_conn.escape_string(str(self.dataset.group_id)),
                       self.db_conn.escape_string(clause_item),
                       self.db_conn.escape_string(str(self.dataset.id))))

            elif self.dataset.type == "Geno":
                query = (
"""SELECT 0, Geno.Name, GenoFreeze.createtime as thistable,
    Geno.Name as Geno_Name,
    Geno.Source2 as Geno_Source2,
    Geno.chr_num as Geno_chr_num,
    Geno.Mb as Geno_Mb
    FROM GenoXRef, GenoFreeze, Geno
    WHERE %s and Geno.Id = GenoXRef.GenoId and
        GenoXRef.GenoFreezeId = GenoFreeze.Id and
        GenoFreeze.Id = %d
                """% (self.db_conn.escape_string(clause_item),
                      self.db_conn.escape_string(str(self.dataset.id))))


            self.cursor.execute(query)
            self.results.append(self.cursor.fetchall())

            print("self.results is:", pf(self.results))




            #if self.dataset.type == "ProbeSet" and search_term.find('.') < 0 and search_term.find('\'') < 0:
            #    full_text.append(search_term)
            #else:
            #    if self.matchwhole and search_term.find("'") < 0:
            #        search_term = "[[:<:]]"+ search_term+"[[:>:]]"
            #    clause2 = []
            #    for field in self.search_fields:
            #        if self.dataset.type == "Publish":
            #            clause2.append("%s REGEXP \"%s\"" % (field,search_term))
            #        else:
            #            clause2.append("%s REGEXP \"%s\"" % ("%s.%s" % (self.dataset.type,field),search_term))
            #    clause_item = "(%s)" % string.join(clause2, clausejoin)
            #    query.append(" (%s) " % clause_item)
        #if ANDFulltext:
        #    clauseItem = """ MATCH (ProbeSet.Name,ProbeSet.description,ProbeSet.symbol,
        #    alias,GenbankId, UniGeneId, Probe_Target_Description)
        #    AGAINST ('+%s' IN BOOLEAN MODE) """ % string.join(ANDFulltext, " +")
        #    self.ANDQuery.append(" (%s) " % clauseItem)
        #if ORFulltext:
        #clauseItem = """ MATCH (ProbeSet.Name,ProbeSet.description,ProbeSet.symbol,alias,
        #GenbankId, UniGeneId, Probe_Target_Description) AGAINST ('%s' IN BOOLEAN MODE)
        #""" % string.join(full_text, " ")
        #self.query.append(" (%s) " % clauseItem)


    def encregexp(self,str):
        if not str:
            return []
        else:
            wildcardkeyword = str.strip()
            wildcardkeyword = string.replace(wildcardkeyword,',',' ')
            wildcardkeyword = string.replace(wildcardkeyword,';',' ')
            wildcardkeyword = wildcardkeyword.split()
        NNN = len(wildcardkeyword)
        for i in range(NNN):
            keyword = wildcardkeyword[i]
            keyword = string.replace(keyword,"*",".*")
            keyword = string.replace(keyword,"?",".")
            wildcardkeyword[i] = keyword#'[[:<:]]'+ keyword+'[[:>:]]'
        return wildcardkeyword



    def patternSearch(self):
        # Lei Yan
        ##Process Inputs
        m1_AND = self._1mPattern.findall(self.ANDkeyword)
        m2_AND = self._2mPattern.findall(self.ANDkeyword)
        m3_AND = self._3mPattern.findall(self.ANDkeyword)
        m5_AND = self._5mPattern.findall(self.ANDkeyword)
        m1_OR = self._1mPattern.findall(self.ORkeyword)
        m2_OR = self._2mPattern.findall(self.ORkeyword)
        m3_OR = self._3mPattern.findall(self.ORkeyword)
        m5_OR = self._5mPattern.findall(self.ORkeyword)

        #pattern search
        if m1_AND or m1_OR or m2_AND or m2_OR or m3_AND or m3_OR or m5_AND or m5_OR:

            self.orderByDefalut = 'PROBESETID'

            _1Cmds = map(string.upper, map(lambda x:x[0], m1_AND + m1_OR))
            _2Cmds = map(string.upper, map(lambda x:x[0], m2_AND + m2_OR))
            _3Cmds = map(string.upper, map(lambda x:x[0], m3_AND + m3_OR))
            _5Cmds = map(string.upper, map(lambda x:x[0], m5_AND + m5_OR))

            self.nkeywords += len(_1Cmds) + len(_2Cmds) + len(_3Cmds)

            if self.dbType == "Publish" and \
                ( (_2Cmds and reduce(lambda x, y: (y not in ["LRS"]) or x, _2Cmds, False))\
                or (_5Cmds and reduce(lambda x, y: (y not in ["LRS"]) or x, _5Cmds, False)) ):
                heading = "Search Result"
                detail = ["Pattern search is not available for phenotype databases at this time."]
                self.error(heading=heading,detail=detail,error="Error")
                return 0
            elif (self.dbType == "ProbeSet" and
                ((_2Cmds and reduce(lambda x, y: (y not in [
                    "MEAN", "LRS", "PVALUE", "TRANSLRS", "CISLRS", "RANGE", "H2"
                    ]) or x, _2Cmds, False))\
                or (_3Cmds and reduce(lambda x, y: (y not in ["POS", "POSITION", "MB"]) or x, _3Cmds, False))\
                or (_5Cmds and reduce(lambda x, y: (y not in ["LRS"]) or x, _5Cmds, False))\
                or (_1Cmds and reduce(lambda x, y: (
                    y not in ["FLAG", "STRAND_PROBE", "STRAND_GENE", "GO", "WIKI", "RIF", "GENEID"]
                    ) or x, _1Cmds, False)))):
                heading = "Search Result"
                detail = ["You entered at least one incorrect search command."]
                self.error(heading=heading,detail=detail,error="Error")
                return 0
            elif self.dbType == "Geno" and (_1Cmds or _2Cmds or _5Cmds or (_3Cmds and reduce(
                lambda x, y: (y not in ["POS", "POSITION", "MB"]) or x, _3Cmds, False)) ):
                heading = "Search Result"
                detail = ["You entered at least one incorrect search command."]
                self.error(heading=heading,detail=detail,error="Error")
                return 0
            else:
                for k, item in enumerate(m1_OR+m1_AND):
                    if k >=len(m1_OR):
                        query = self.ANDQuery
                        DescriptionText = self.ANDDescriptionText
                    else:
                        query = self.ORQuery
                        DescriptionText = self.ORDescriptionText

                    if item[1] == '-':
                        strandName = 'minus'
                    elif item[1] == '+':
                        strandName = 'plus'
                    else:
                        strandName = item[1]

                    if item[0].upper() in ("FLAG"):
                        clauseItem = " %s.%s = %s " % (self.dbType, item[0], item[1])
                        DescriptionText.append(HT.Span(' with ', HT.U('FLAG'), ' equal to ', item[1]))
                    elif item[0].upper() in ("WIKI"):
                        clauseItem = " %s.symbol = GeneRIF.symbol and GeneRIF.versionId=0 and GeneRIF.display>0 and (GeneRIF.comment REGEXP \"%s\" or GeneRIF.initial = \"%s\") " % (self.dbType, "[[:<:]]"+ item[1]+"[[:>:]]", item[1])
                        DescriptionText.append(HT.Span(' with GeneWiki contains ', HT.U(item[1])))
                    elif item[0].upper() in ("RIF"):
                        clauseItem = " %s.symbol = GeneRIF_BASIC.symbol and MATCH (GeneRIF_BASIC.comment) AGAINST ('+%s' IN BOOLEAN MODE) " % (self.dbType, item[1])
                        DescriptionText.append(HT.Span(' with GeneRIF contains ', HT.U(item[1])))
                    elif item[0].upper() in ("GENEID"):
                        clauseItem = " %s.GeneId in ( %s ) " % (self.dbType, string.replace(item[1], '-', ', '))
                        DescriptionText.append(HT.Span(' with Entrez Gene ID in  ', HT.U(string.replace(item[1], '-', ', '))))
                    elif item[0].upper() in ("GO"):
                        Field = 'GOterm.acc'
                        Id = 'GO:'+('0000000'+item[1])[-7:]
                        Statements = '%s.symbol=GOgene_product.symbol and GOassociation.gene_product_id=GOgene_product.id and GOterm.id=GOassociation.term_id' % (self.dbType);
                        clauseItem = " %s = '%s' and %s " % (Field, Id, Statements)
                        #self.incGoTbl = " ,db_GeneOntology.term as GOterm, db_GeneOntology.association as GOassociation, db_GeneOntology.gene_product as GOgene_product "
                        DescriptionText.append(HT.Span(' with ', HT.U('GO'), ' ID equal to ', Id))
                    else:
                        clauseItem = " %s.%s = '%s' " % (self.dbType, item[0], item[1])
                        if item[0].upper() in ["STRAND_PROBE"]:
                            DescriptionText.append(' with probe on the %s strand' % strandName)
                        elif item[0].upper() in ["STRAND_GENE"]:
                            DescriptionText.append(' with gene on the %s strand' % strandName)
                        else:
                            pass
                    query.append(" (%s) " % clauseItem)

                for k, item in enumerate(m2_OR+m2_AND):
                    if k >=len(m2_OR):
                        query = self.ANDQuery
                        DescriptionText = self.ANDDescriptionText
                    else:
                        query = self.ORQuery
                        DescriptionText = self.ORDescriptionText

                    itemCmd = item[0]
                    lower_limit = float(item[1])
                    upper_limit = float(item[2])

                    if itemCmd.upper() in ("TRANSLRS", "CISLRS"):
                        if item[3]:
                            mthresh = float(item[3])
                            clauseItem = " %sXRef.LRS > %2.7f and %sXRef.LRS < %2.7f " % \
                                (self.dbType, min(lower_limit, upper_limit), self.dbType, max(lower_limit, upper_limit))
                            if itemCmd.upper() == "CISLRS":
                                clauseItem += """ and  %sXRef.Locus = Geno.name and Geno.SpeciesId = %s and %s.Chr = Geno.Chr and ABS(%s.Mb-Geno.Mb) < %2.7f """ % (self.dbType, self.speciesId, self.dbType, self.dbType, mthresh)
                                DescriptionText.append(HT.Span(' with a ', HT.U('cis-QTL'), ' having an LRS between %g and %g using a %g Mb exclusion buffer'  % (min(lower_limit, upper_limit), max(lower_limit, upper_limit),  mthresh)))
                            else:
                                clauseItem += """ and  %sXRef.Locus = Geno.name and Geno.SpeciesId = %s and (%s.Chr != Geno.Chr or (%s.Chr != Geno.Chr and ABS(%s.Mb-Geno.Mb) > %2.7f)) """ % (self.dbType, self.speciesId, self.dbType, self.dbType, self.dbType, mthresh)
                                DescriptionText.append(HT.Span(' with a ', HT.U('trans-QTL'), ' having an LRS between %g and %g using a %g Mb exclusion buffer'  % (min(lower_limit, upper_limit), max(lower_limit, upper_limit),  mthresh)))
                            query.append(" (%s) " % clauseItem)
                            self.orderByDefalut = "LRS"
                        else:
                            pass
                    elif itemCmd.upper() in ("RANGE"):
                        #XZ, 03/05/2009: Xiaodong changed Data to ProbeSetData
                        clauseItem = " (select Pow(2, max(value) -min(value)) from ProbeSetData where Id = ProbeSetXRef.dataId) > %2.7f and (select Pow(2, max(value) -min(value)) from ProbeSetData where Id = ProbeSetXRef.dataId) < %2.7f " % (min(lower_limit, upper_limit), max(lower_limit, upper_limit))
                        query.append(" (%s) " % clauseItem)
                        DescriptionText.append(HT.Span(' with a range of expression that varied between %g and %g' % (min(lower_limit, upper_limit),  max(lower_limit, upper_limit)), "  (fold difference)"))
                    else:
                        clauseItem = " %sXRef.%s > %2.7f and %sXRef.%s < %2.7f " % \
                            (self.dbType, itemCmd, min(lower_limit, upper_limit), self.dbType, itemCmd, max(lower_limit, upper_limit))
                        query.append(" (%s) " % clauseItem)
                        self.orderByDefalut = itemCmd
                        DescriptionText.append(HT.Span(' with ', HT.U(itemCmd), ' between %g and %g' % (min(lower_limit, upper_limit),  max(lower_limit, upper_limit))))

                for k, item in enumerate(m3_OR+m3_AND):
                    print("enumerating m3_OR+m3_AND with k: %s - item %s" % (k, item))
                    if self.dbType not in ("ProbeSet", "Geno"):
                        continue
                    if k >=len(m3_OR):
                        query = self.ANDQuery
                        DescriptionText = self.ANDDescriptionText
                    else:
                        query = self.ORQuery
                        DescriptionText = self.ORDescriptionText
                    itemCmd = item[0]


                    chr_number = item[1]     # chromosome number
                    lower_limit = float(item[2])
                    upper_limit = float(item[3])

                    if self.dbType == "ProbeSet":
                        fname = 'target genes'
                    elif self.dbType == "Geno":
                        fname = 'loci'

                    if lower_limit > upper_limit:
                        lower_limit, upper_limit = upper_limit, lower_limit


                    clauseItem = " %s.Chr = '%s' and %s.Mb > %2.7f and %s.Mb < %2.7f " % (
                            self.dbType, chr_number, self.dbType, lower_limit, self.dbType, upper_limit)


                    query.append(" (%s) " % clauseItem)
                    self.orderByDefalut = itemCmd

                    self.results_desc = dict()
                    #DescriptionText.append(HT.Span(' with ', HT.U('target genes'), ' on chromosome %s between %g and %g Mb' % \
                    #    (chr_number, min(lower_limit, upper_limit), max(lower_limit, upper_limit))))

                for k, item in enumerate(m5_OR+m5_AND):
                    if k >=len(m5_OR):
                        query = self.ANDQuery
                        DescriptionText = self.ANDDescriptionText
                    else:
                        query = self.ORQuery
                        DescriptionText = self.ORDescriptionText
                    itemCmd = item[0]
                    lower_limit = float(item[1])
                    upper_limit = float(item[2])
                    chr_number = item[3]
                    mb_lower_limit = float(item[4])
                    mb_upper_limit = float(item[5])
                    if self.dbType == "ProbeSet" or self.dbType == "Publish":
                        clauseItem = " %sXRef.LRS > %2.7f and %sXRef.LRS < %2.7f " % \
                            (self.dbType, min(lower_limit, upper_limit), self.dbType, max(lower_limit, upper_limit))
                        clauseItem += " and  %sXRef.Locus = Geno.name and Geno.SpeciesId = %s and Geno.Chr = '%s' and Geno.Mb > %2.7f and Geno.Mb < %2.7f" \
                            % (self.dbType, self.speciesId, chr_number, min(mb_lower_limit, mb_upper_limit),  max(mb_lower_limit, mb_upper_limit))
                        query.append(" (%s) " % clauseItem)
                        self.orderByDefalut = "MB"
                        DescriptionText.append(HT.Span(' with ', HT.U('LRS'), ' between %g and %g' % \
                            (min(lower_limit, upper_limit),  max(lower_limit, upper_limit)), \
                            ' on chromosome %s between %g and %g Mb' % \
                            (chr_number, min(mb_lower_limit, mb_upper_limit),  max(mb_lower_limit, mb_upper_limit))))
            pass

        return 1

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

    def getTableHeaderForGeno(self, worksheet=None, newrow=None, headingStyle=None):

        tblobj_header = []

        className = "fs13 fwb ffl b1 cw cbrb"

        tblobj_header = [[THCell(HT.TD(' ', Class=className), sort=0),
            THCell(HT.TD('Record', HT.BR(), 'ID', HT.BR(), Class=className), text='record_id', idx=1),
            THCell(HT.TD('Location', HT.BR(), 'Chr and Mb', HT.BR(), Class=className), text='location', idx=2)]]

        for ncol, item in enumerate(['Record ID', 'Location (Chr, Mb)']):
            worksheet.write([newrow, ncol], item, headingStyle)
            worksheet.set_column([ncol, ncol], 2*len(item))

        return tblobj_header


    def getTableBodyForGeno(self, trait_list, formName=None, worksheet=None, newrow=None):

        tblobj_body = []

        className = "fs12 fwn ffl b1 c222"

        for this_trait in trait_list:
            tr = []

            if not this_trait.haveinfo:
                this_trait.retrieveInfo()

            trId = str(this_trait)

            tr.append(TDCell(HT.TD(HT.Input(type="checkbox", Class="checkbox", name="searchResult",value=trId, onClick="highlight(this)"), nowrap="on", Class=className), text=trId))

            tr.append(TDCell(HT.TD(HT.Href(text=this_trait.name,url="javascript:showDatabase3('%s','%s','%s','')" % (formName, this_trait.db.name, this_trait.name), Class="fs12 fwn ffl"),align="left", Class=className), text=this_trait.name, val=this_trait.name.upper()))

            #XZ: trait_location_value is used for sorting
            trait_location_repr = 'N/A'
            trait_location_value = 1000000

            if this_trait.chr and this_trait.mb:
                try:
                    trait_location_value = int(this_trait.chr)*1000 + this_trait.mb
                except:
                    if this_trait.chr.upper() == 'X':
                        trait_location_value = 20*1000 + this_trait.mb
                    else:
                        trait_location_value = ord(str(this_trait.chr).upper()[0])*1000 + this_trait.mb

                trait_location_repr = 'Chr%s: %.6f' % (this_trait.chr, float(this_trait.mb) )

            tr.append(TDCell(HT.TD(trait_location_repr, Class="fs12 fwn b1 c222", nowrap="on"), trait_location_repr, trait_location_value))

            tblobj_body.append(tr)

            for ncol, item in enumerate([this_trait.name, trait_location_repr]):
                worksheet.write([newrow, ncol], item)

            newrow += 1

        return tblobj_body

    def getTableHeaderForPublish(self, worksheet=None, newrow=None, headingStyle=None):

        tblobj_header = []

        className = "fs13 fwb ffl b1 cw cbrb"

        tblobj_header = [[THCell(HT.TD(' ', Class=className, nowrap="on"), sort=0),
            THCell(HT.TD('Record',HT.BR(), 'ID',HT.BR(), Class=className, nowrap="on"), text="recond_id", idx=1),
            THCell(HT.TD('Phenotype',HT.BR(),HT.BR(), Class=className, nowrap="on"), text="pheno", idx=2),
            THCell(HT.TD('Authors',HT.BR(),HT.BR(), Class=className, nowrap="on"), text="auth", idx=3),
            THCell(HT.TD('Year',HT.BR(),HT.BR(), Class=className, nowrap="on"), text="year", idx=4),
            THCell(HT.TD('Max',HT.BR(), 'LRS', HT.BR(), Class="fs13 fwb ffl b1 cw cbrb", nowrap="on"), text="lrs", idx=5),
            THCell(HT.TD('Max LRS Location',HT.BR(),'Chr and Mb',HT.BR(), Class="fs13 fwb ffl b1 cw cbrb", nowrap="on"), text="lrs_location", idx=6)]]

        for ncol, item in enumerate(["Record", "Phenotype", "Authors", "Year", "Pubmed Id", "Max LRS", "Max LRS Location (Chr: Mb)"]):
            worksheet.write([newrow, ncol], item, headingStyle)
            worksheet.set_column([ncol, ncol], 2*len(item))

        return tblobj_header

    def getTableBodyForPublish(self, trait_list, formName=None, worksheet=None, newrow=None, species=''):

        tblobj_body = []

        className = "fs12 fwn b1 c222"

        for this_trait in trait_list:
            tr = []

            if not this_trait.haveinfo:
                this_trait.retrieveInfo(QTL=1)

            trId = str(this_trait)

            tr.append(TDCell(HT.TD(HT.Input(type="checkbox", Class="checkbox", name="searchResult",value=trId, onClick="highlight(this)"), nowrap="on", Class=className), text=trId))

            tr.append(TDCell(HT.TD(HT.Href(text=this_trait.name,url="javascript:showDatabase3('%s','%s','%s','')" % (formName, this_trait.db.name, this_trait.name), Class="fs12 fwn"), nowrap="yes",align="center", Class=className),str(this_trait.name), this_trait.name))

            PhenotypeString = this_trait.post_publication_description
            if this_trait.confidential:
                if not webqtlUtil.hasAccessToConfidentialPhenotypeTrait(privilege=self.privilege, userName=self.userName, authorized_users=this_trait.authorized_users):
                    PhenotypeString = this_trait.pre_publication_description
            tr.append(TDCell(HT.TD(PhenotypeString, Class=className), PhenotypeString, PhenotypeString.upper()))

            tr.append(TDCell(HT.TD(this_trait.authors, Class="fs12 fwn b1 c222 fsI"),this_trait.authors, this_trait.authors.strip().upper()))

            try:
                PubMedLinkText = myear = repr = int(this_trait.year)
            except:
                PubMedLinkText = repr = "N/A"
                myear = 0

            if this_trait.pubmed_id:
                PubMedLink = HT.Href(text= repr,url= webqtlConfig.PUBMEDLINK_URL % this_trait.pubmed_id,target='_blank', Class="fs12 fwn")
            else:
                PubMedLink = repr

            tr.append(TDCell(HT.TD(PubMedLink, Class=className, align='center'), repr, myear))

            #LRS and its location
            LRS_score_repr = 'N/A'
            LRS_score_value = 0
            LRS_location_repr = 'N/A'
            LRS_location_value = 1000000
            LRS_flag = 1


            if this_trait.lrs:
                LRS_score_repr = '%3.1f' % this_trait.lrs
                LRS_score_value = this_trait.lrs
                tr.append(TDCell(HT.TD(LRS_score_repr, Class=className), LRS_score_repr, LRS_score_value))

                self.cursor.execute("""
                    select Geno.Chr, Geno.Mb from Geno, Species
                    where Species.Name = '%s' and
                        Geno.Name = '%s' and
                        Geno.SpeciesId = Species.Id
                """ % (species, this_trait.locus))
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

                        LRS_location_repr = 'Chr%s: %.6f' % (LRS_Chr, float(LRS_Mb) )
                        LRS_flag = 0

                tr.append(TDCell(HT.TD(LRS_location_repr, Class=className, nowrap="on"), LRS_location_repr, LRS_location_value))

            else:
                tr.append(TDCell(HT.TD("N/A", Class=className), "N/A", "N/A"))
                tr.append(TDCell(HT.TD("N/A", Class=className), "N/A", "N/A"))

            tblobj_body.append(tr)

            for ncol, item in enumerate([this_trait.name, PhenotypeString, this_trait.authors, this_trait.year, this_trait.pubmed_id, LRS_score_repr, LRS_location_repr]):
                worksheet.write([newrow, ncol], item)

            newrow += 1

        return tblobj_body

    def getTableHeaderForProbeSet(self, worksheet=None, newrow=None, headingStyle=None):

        tblobj_header = []

        className = "fs13 fwb ffl b1 cw cbrb"

        #tblobj_header = [[THCell(HT.TD(' ', Class="fs13 fwb ffl b1 cw cbrb",nowrap='ON'), sort=0),
        #                 THCell(HT.TD('Record',HT.BR(), 'ID',HT.BR(), Class="fs13 fwb ffl b1 cw cbrb"), text="record_id", idx=1),
        #                 THCell(HT.TD('Symbol',HT.BR(),HT.BR(), Class="fs13 fwb ffl b1 cw cbrb"), text="symbol", idx=2),
        #                 THCell(HT.TD('Description',HT.BR(),HT.BR(), Class="fs13 fwb ffl b1 cw cbrb"), text="desc", idx=3),
        #                 THCell(HT.TD('Location',HT.BR(), 'Chr and Mb', HT.BR(), Class="fs13 fwb ffl b1 cw cbrb"), text="location", idx=4),
        #                 THCell(HT.TD('Mean',HT.BR(),'Expr',HT.BR(), Class="fs13 fwb ffl b1 cw cbrb"), text="mean", idx=5),
        #                 THCell(HT.TD('Max',HT.BR(),'LRS',HT.BR(), Class="fs13 fwb ffl b1 cw cbrb", nowrap='ON'), text="lrs", idx=6),
        #                THCell(HT.TD('Max LRS Location',HT.BR(),'Chr and Mb',HT.BR(), Class="fs13 fwb ffl b1 cw cbrb", nowrap='ON'), text="lrs_location", idx=7)]]
        #
        #for ncol, item in enumerate(['Record', 'Gene ID', 'Homologene ID', 'Symbol', 'Description', 'Location (Chr, Mb)', 'Mean Expr', 'Max LRS', 'Max LRS Location (Chr: Mb)']):
        #    worksheet.write([newrow, ncol], item, headingStyle)
        #    worksheet.set_column([ncol, ncol], 2*len(item))

        return tblobj_header

    def getTableBodyForProbeSet(self, trait_list=[], primaryTrait=None, formName=None, worksheet=None, newrow=None, species=''):
        #  Note: setting trait_list to [] is probably not a great idea.
        tblobj_body = []

        className = "fs12 fwn b1 c222"

        for this_trait in trait_list:

            if not this_trait.haveinfo:
                this_trait.retrieveInfo(QTL=1)

            if this_trait.symbol:
                pass
            else:
                this_trait.symbol = "N/A"

            tr = []

            trId = str(this_trait)

            #XZ, 12/08/2008: checkbox
            #tr.append(TDCell(HT.TD(HT.Input(type="checkbox", Class="checkbox", name="searchResult",value=trId, onClick="highlight(this)"), nowrap="on", Class="fs12 fwn ffl b1 c222"), text=trId))

            #XZ, 12/08/2008: probeset name
            #if this_trait.cellid:
            #    tr.append(TDCell(HT.TD(HT.Href(text=this_trait.name, url="javascript:showDatabase3('%s','%s','%s','%s')" % (formName, this_trait.db.name,this_trait.name,this_trait.cellid), Class="fs12 fwn"), Class=className), this_trait.name, this_trait.name.upper()))
            #else:
            #    tr.append(TDCell(HT.TD(HT.Href(text=this_trait.name, url="javascript:showDatabase3('%s','%s','%s','')" % (formName, this_trait.db.name,this_trait.name), Class="fs12 fwn"), Class=className), this_trait.name, this_trait.name.upper()))
            #
            #if this_trait.geneid:
            #    symbolurl = HT.Href(text=this_trait.symbol,target='_blank',url="http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?db=gene&cmd=Retrieve&dopt=Graphics&list_uids=%s" % this_trait.geneid, Class="font_black fs12 fwn")
            #else:
            #    symbolurl = HT.Href(text=this_trait.symbol,target='_blank',url="http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?CMD=search&DB=gene&term=%s" % this_trait.symbol, Class="font_black fs12 fwn")
            #
            ##XZ, 12/08/2008: gene symbol
            #tr.append(TDCell(HT.TD(symbolurl, Class="fs12 fwn b1 c222 fsI"),this_trait.symbol, this_trait.symbol.upper()))

            #XZ, 12/08/2008: description
            #XZ, 06/05/2009: Rob asked to add probe target description
            description_string = str(this_trait.description).strip()
            target_string = str(this_trait.probe_target_description).strip()

            description_display = ''

            if len(description_string) > 1 and description_string != 'None':
                description_display = description_string
            else:
                description_display = this_trait.symbol

            if len(description_display) > 1 and description_display != 'N/A' and len(target_string) > 1 and target_string != 'None':
                description_display = description_display + '; ' + target_string.strip()

            #tr.append(TDCell(HT.TD(description_display, Class=className), description_display, description_display))

            # Save it for the jinja2 tablet
            this_trait.description_display = description_display

            #XZ: trait_location_value is used for sorting
            trait_location_repr = 'N/A'
            trait_location_value = 1000000

            if this_trait.chr and this_trait.mb:
                try:
                    trait_location_value = int(this_trait.chr)*1000 + this_trait.mb
                except:
                    if this_trait.chr.upper() == 'X':
                        trait_location_value = 20*1000 + this_trait.mb
                    else:
                        trait_location_value = ord(str(this_trait.chr).upper()[0])*1000 + this_trait.mb

                trait_location_repr = 'Chr %s: %.4f Mb' % (this_trait.chr, float(this_trait.mb) )
                this_trait.trait_location_repr = trait_location_repr
                #this_trait.trait_location_value = trait_location_value
            tr.append(TDCell(HT.TD(trait_location_repr, Class=className, nowrap="on"), trait_location_repr, trait_location_value))

            #XZ, 01/12/08: This SQL query is much faster.
            query = (
"""select ProbeSetXRef.mean from ProbeSetXRef, ProbeSet
    where ProbeSetXRef.ProbeSetFreezeId = %s and
    ProbeSet.Id = ProbeSetXRef.ProbeSetId and
    ProbeSet.Name = '%s'
            """ % (self.db_conn.escape_string(str(this_trait.db.id)),
                   self.db_conn.escape_string(this_trait.name)))
            
            print("query is:", pf(query))
            
            self.cursor.execute(query)
            result = self.cursor.fetchone()

            if result:
                if result[0]:
                    mean = result[0]
                else:
                    mean=0
            else:
                mean = 0

            #XZ, 06/05/2009: It is neccessary to turn on nowrap
            this_trait.mean = repr = "%2.3f" % mean
            tr.append(TDCell(HT.TD(repr, Class=className, align='right', nowrap='ON'),repr, mean))

            #LRS and its location
            LRS_score_repr = 'N/A'
            LRS_score_value = 0
            LRS_location_repr = 'N/A'
            LRS_location_value = 1000000
            LRS_flag = 1

            #Max LRS and its Locus location
            if this_trait.lrs and this_trait.locus:
                self.cursor.execute("""
                    select Geno.Chr, Geno.Mb from Geno, Species
                    where Species.Name = '%s' and
                        Geno.Name = '%s' and
                        Geno.SpeciesId = Species.Id
                """ % (species, this_trait.locus))
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

                        this_trait.LRS_score_repr = LRS_score_repr = '%3.1f' % this_trait.lrs
                        this_trait.LRS_score_value = LRS_score_value = this_trait.lrs
                        this_trait.LRS_location_repr = LRS_location_repr = 'Chr %s: %.4f Mb' % (LRS_Chr, float(LRS_Mb) )
                        LRS_flag = 0

                        #tr.append(TDCell(HT.TD(HT.Href(text=LRS_score_repr,url="javascript:showIntervalMapping('%s', '%s : %s')" % (formName, this_trait.db.shortname, this_trait.name), Class="fs12 fwn"), Class=className, align='right', nowrap="on"),LRS_score_repr, LRS_score_value))
                        tr.append(TDCell(HT.TD(LRS_score_repr, Class=className, align='right', nowrap="on"), LRS_score_repr, LRS_score_value))
                        tr.append(TDCell(HT.TD(LRS_location_repr, Class=className, nowrap="on"), LRS_location_repr, LRS_location_value))

                if LRS_flag:
                    tr.append(TDCell(HT.TD(LRS_score_repr, Class=className), LRS_score_repr, LRS_score_value))
                    tr.append(TDCell(HT.TD(LRS_location_repr, Class=className), LRS_location_repr, LRS_location_value))

            else:
                tr.append(TDCell(HT.TD("N/A", Class=className), "N/A", "N/A"))
                tr.append(TDCell(HT.TD("N/A", Class=className), "N/A", "N/A"))

            tblobj_body.append(tr)

            #for ncol, item in enumerate([this_trait.name, this_trait.geneid, this_trait.homologeneid, this_trait.symbol, description_display, trait_location_repr, mean, LRS_score_repr, LRS_location_repr]):
            #    worksheet.write([newrow, ncol], item)


            newrow += 1

        return tblobj_body

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

    def getSortByValue(self, datasetType=''):

        if datasetType == 'Geno':
            sortby = ("location", "up")
        elif datasetType == 'ProbeSet':
            sortby = ("symbol", "up")
        else: #Phenotype
            sortby = ("record_id", "down")

        return sortby
