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
# Last updated by GeneNetwork Core Team 2010/10/20

import os
import string
import cPickle

from htmlgen import HTMLgen2 as HT

from base import webqtlConfig
from utility.THCell import THCell
from utility.TDCell import TDCell
from base.webqtlTrait import webqtlTrait
from base.templatePage import templatePage
from dbFunction import webqtlDatabaseFunction
from utility import webqtlUtil



class PartialCorrInputPage(templatePage):

    def __init__(self,fd):

        templatePage.__init__(self, fd)

        if not self.openMysql():
                return

        searchResult = fd.formdata.getvalue('searchResult')

        if not searchResult:
            heading = 'Partial Correlation'
            detail = ['You need to select at least three traits in order to calculate partial correlation.']
            self.error(heading=heading,detail=detail)
            return


        ## Adds the Trait instance for each trait name from the collection
        traits = []

        for item in searchResult:
            traits.append(webqtlTrait(fullname=item, cursor=self.cursor))

        RISet = fd.formdata.getvalue('RISet')
        species = webqtlDatabaseFunction.retrieveSpecies(cursor=self.cursor, RISet=RISet)

        #XZ: HTML part
        TD_LR = HT.TD(colspan=2,height=200,width="100%",bgColor='#eeeeee')
        TD_LR.append("Please select one primary trait, one to three control traits, and at least one target trait.", HT.P() )

        mainFormName = 'showDatabase'
        mainForm = HT.Form(cgi= os.path.join(webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE), name=mainFormName,submit=HT.Input(type='hidden'))

        #XZ: Add hidden form values
        hddn = {'FormID':'calPartialCorrTrait', 'database':'', 'ProbeSetID':'', 'CellID':'', #XZ: These four parameters are required by javascript function showDatabase2.
                'controlTraits':'',
                'primaryTrait':'',
                'targetTraits':'',
                'pcMethod':'',
                'RISet':RISet
               }


        for key in hddn.keys():
            mainForm.append(HT.Input(type='hidden', name=key, value=hddn[key]))

        radioNames = []

	for thisTrait in traits:
            oneRadioName = thisTrait.getName()
            radioNames.append(oneRadioName)
            
        radioNamesString = ','.join(radioNames)

        # Creates the image href that runs the javascript setting all traits as target or ignored
        setAllTarget = HT.Href(url="#redirect", onClick="setAllAsTarget(document.getElementsByName('showDatabase')[0], '%s');" % radioNamesString)
        setAllTargetImg = HT.Image("/images/select_all.gif", alt="Select All", title="Select All", style="border:none;")
        setAllTarget.append(setAllTargetImg)
        setAllIgnore = HT.Href(url="#redirect", onClick="setAllAsIgnore(document.getElementsByName('showDatabase')[0], '%s');" % radioNamesString)
        setAllIgnoreImg = HT.Image("/images/select_all.gif", alt="Select All", title="Select All", style="border:none;")
        setAllIgnore.append(setAllIgnoreImg)


        tblobj = {}
        tblobj['header'] = self.getCollectionTableHeader()

        sortby = self.getSortByValue()

        tblobj['body'] = self.getCollectionTableBody(traitList=traits, formName=mainFormName, species=species)

        filename= webqtlUtil.genRandStr("Search_")

        objfile = open('%s.obj' % (webqtlConfig.TMPDIR+filename), 'wb')
        cPickle.dump(tblobj, objfile)
        objfile.close()

        div = HT.Div(webqtlUtil.genTableObj(tblobj=tblobj, file=filename, sortby=sortby, tableID = "sortable", addIndex = "1"), Id="sortable")

        mainForm.append(div)

        #XZ: Add button
        radioNamesString = ','.join(radioNames)
        jsCommand_1 = "validateTrait(this.form, \'" + radioNamesString + "\', 0, 1);"
        jsCommand_2 = "validateTrait(this.form, \'" + radioNamesString + "\', 0, 2);"
        partialCorrTraitButton_1 = HT.Input(type='button', name='submitPartialCorrTrait_1', value='Pearson\'s r', onClick='%s' % jsCommand_1, Class="button")
        partialCorrTraitButton_2 = HT.Input(type='button', name='submitPartialCorrTrait_2', value='Spearman\'s rho', onClick='%s' % jsCommand_2, Class="button")
        mainForm.append(HT.BR(), "Compute partial correlation for target selected above:", HT.BR(),  partialCorrTraitButton_1, partialCorrTraitButton_2, HT.BR(), HT.BR(), HT.HR(color="gray",size=3) )

        jsCommand = "validateTrait(this.form, \'" + radioNamesString + "\', 1);"
        partialCorrDBButton = HT.Input(type='button', name='submitPartialCorrDB', value='Calculate', onClick='%s' % jsCommand,Class="button")

        methodText = HT.Span("Calculate:", Class="ffl fwb fs12")

        methodMenu = HT.Select(name='method')
        methodMenu.append(('Genetic Correlation, Pearson\'s r','1'))
        methodMenu.append(('Genetic Correlation, Spearman\'s rho','2'))
        methodMenu.append(('SGO Literature Correlation','3'))
        methodMenu.append(('Tissue Correlation, Pearson\'s r','4'))
        methodMenu.append(('Tissue Correlation, Spearman\'s rho','5'))

        databaseText = HT.Span("Choose Database:", Class="ffl fwb fs12")
        databaseMenu = HT.Select(name='database2')

        nmenu = 0

        self.cursor.execute('SELECT PublishFreeze.FullName,PublishFreeze.Name FROM \
                                PublishFreeze,InbredSet WHERE PublishFreeze.InbredSetId = InbredSet.Id \
                                and InbredSet.Name = "%s" and PublishFreeze.public > %d' % \
                                (RISet,webqtlConfig.PUBLICTHRESH))
        for item in self.cursor.fetchall():
                                databaseMenu.append(item)
                                nmenu += 1

        self.cursor.execute('SELECT GenoFreeze.FullName,GenoFreeze.Name FROM GenoFreeze,\
                                InbredSet WHERE GenoFreeze.InbredSetId = InbredSet.Id and InbredSet.Name = \
                                "%s" and GenoFreeze.public > %d' % (RISet,webqtlConfig.PUBLICTHRESH))
        for item in self.cursor.fetchall():
                                databaseMenu.append(item)
                                nmenu += 1

        #03/09/2009: Xiaodong changed the SQL query to order by Name as requested by Rob.
        self.cursor.execute('SELECT Id, Name FROM Tissue order by Name')
        for item in self.cursor.fetchall():
                                TId, TName = item
                                databaseMenuSub = HT.Optgroup(label = '%s ------' % TName)
                                self.cursor.execute('SELECT ProbeSetFreeze.FullName,ProbeSetFreeze.Name FROM ProbeSetFreeze, ProbeFreeze, \
                                InbredSet WHERE ProbeSetFreeze.ProbeFreezeId = ProbeFreeze.Id and ProbeFreeze.TissueId = %d and \
                                ProbeSetFreeze.public > %d and ProbeFreeze.InbredSetId = InbredSet.Id and InbredSet.Name like "%s%%" \
                                order by ProbeSetFreeze.CreateTime desc, ProbeSetFreeze.AvgId '  % (TId,webqtlConfig.PUBLICTHRESH, RISet))
                                for item2 in self.cursor.fetchall():
                                        databaseMenuSub.append(item2)
                                        nmenu += 1
                                databaseMenu.append(databaseMenuSub)

        if nmenu:
                                criteriaText = HT.Span("Return:", Class="ffl fwb fs12") 
                                criteriaMenu = HT.Select(name='criteria', selected='500')
                                criteriaMenu.append(('top 100','100'))
                                criteriaMenu.append(('top 200','200'))
                                criteriaMenu.append(('top 500','500'))
                                criteriaMenu.append(('top 1000','1000'))
                                criteriaMenu.append(('top 2000','2000'))
				criteriaMenu.append(('top 5000','5000'))
				criteriaMenu.append(('top 10000','10000'))
				criteriaMenu.append(('top 15000','15000'))
				criteriaMenu.append(('top 20000','20000'))

                                self.MPDCell = HT.TD()
                                correlationMenus = HT.TableLite( 
                                        HT.TR(
                                                HT.TD(databaseText,HT.BR(),databaseMenu, colspan=4)
                                        ), 
                                        HT.TR(
                                                HT.TD(methodText,HT.BR(),methodMenu),
                                                self.MPDCell, 
                                                HT.TD(criteriaText,HT.BR(),criteriaMenu)), 
                                        border=0, cellspacing=4, cellpadding=0)
        else:
            correlationMenus = ""

        mainForm.append(HT.Font('or',color='red', size=4), HT.BR(), HT.BR(), "Compute partial correlation for each trait in the database selected below:", HT.BR() )
        mainForm.append( partialCorrDBButton, HT.BR(), HT.BR(), correlationMenus)

        TD_LR.append(mainForm)

        self.dict['body'] = str(TD_LR)
        self.dict['js1'] =''
        self.dict['title'] = 'Partial Correlation Input'


    def getCollectionTableHeader(self):

                tblobj_header = []

                className = "fs13 fwb ffl b1 cw cbrb"

                tblobj_header = [[THCell(HT.TD('Index', Class=className, nowrap="on"), sort=0), 
                        THCell(HT.TD("Primary (X)",align="center", Class="fs13 fwb ffl b1 cw cbrb", nowrap="ON"), text="primary", sort=0),
                        THCell(HT.TD("Control (Z)",align="center", Class="fs13 fwb ffl b1 cw cbrb", nowrap="ON"), text="control", sort=0),
                        THCell(HT.TD("Target (Y)",align="center", Class="fs13 fwb ffl b1 cw cbrb", nowrap="ON"), text="target", sort=0),
                        THCell(HT.TD("Ignored",align="center", Class="fs13 fwb ffl b1 cw cbrb", nowrap="ON"), text="target", sort=0),
                        THCell(HT.TD('Dataset', HT.BR(), HT.BR(), valign="top", Class=className, nowrap="on"), text="dataset", idx=1),
                        THCell(HT.TD('Trait', HT.BR(), 'ID', HT.BR(), valign="top", Class=className, nowrap="on"), text="name", idx=2),
                        THCell(HT.TD('Description', HT.BR(), HT.BR(), valign="top", Class=className, nowrap="on"), text="desc", idx=3),
                        THCell(HT.TD('Location', HT.BR(), HT.BR(), valign="top", Class=className, nowrap="on"), text="location", idx=4),
                        THCell(HT.TD('Mean', HT.BR(), HT.BR(), valign="top", Class=className, nowrap="on"), text="mean", idx=5),
                        THCell(HT.TD('N', HT.BR(), 'Cases', HT.BR(), valign="top", Class=className, nowrap="on"), text="samples", idx=6),
                        THCell(HT.TD('Max LRS', HT.BR(), HT.BR(), valign="top", Class=className, nowrap="on"), text="lrs", idx=7),
                        THCell(HT.TD('Max LRS Location',HT.BR(),'Chr and Mb', HT.BR(), valign="top", Class=className, nowrap="on"), text="lrs_location", idx=8)]]

                return tblobj_header



    def getCollectionTableBody(self, traitList=None, formName=None, species=''):

                tblobj_body = []

                className = "fs12 fwn b1 c222"

                for thisTrait in traitList:
                        tr = []

                        if not thisTrait.haveinfo:
                                thisTrait.retrieveInfo(QTL=1)

                        trId = str(thisTrait)

                        oneRadioName = thisTrait.getName()

                        tr.append(TDCell( HT.TD(' ',align="center",valign="center",Class=className) ))
                        tr.append(TDCell( HT.TD(HT.Input(type="radio", name=oneRadioName, value="primary"),align="center",valign="center",Class=className) ))
                        tr.append(TDCell( HT.TD(HT.Input(type="radio", name=oneRadioName, value="control"),align="center",valign="center",Class=className) ))
                        tr.append(TDCell( HT.TD(HT.Input(type="radio", name=oneRadioName, value="target", checked="true"),align="center",valign="center",Class=className) ))
                        tr.append(TDCell( HT.TD(HT.Input(type="radio", name=oneRadioName, value="ignored"),align="center",valign="center",Class=className) ))

                        tr.append(TDCell(HT.TD(thisTrait.db.name, Class="fs12 fwn b1 c222"), thisTrait.db.name, thisTrait.db.name.upper()))

                        tr.append(TDCell(HT.TD(HT.Href(text=thisTrait.name,url="javascript:showDatabase3('%s','%s','%s','')" % (formName, thisTrait.db.name, thisTrait.name), Class="fs12 fwn"), nowrap="yes",align="left", Class=className
),str(thisTrait.name), thisTrait.name))

                        #description column
                        if (thisTrait.db.type == "Publish"):
				PhenotypeString = thisTrait.post_publication_description
				if thisTrait.confidential:
					if not webqtlUtil.hasAccessToConfidentialPhenotypeTrait(privilege=self.privilege, userName=self.userName, authorized_users=thisTrait.authorized_users):
						PhenotypeString = thisTrait.pre_publication_description
                                tr.append(TDCell(HT.TD(PhenotypeString, Class=className), PhenotypeString, PhenotypeString.upper()))
                        elif (thisTrait.db.type == "ProbeSet" or thisTrait.db.type == "Temp"):
                                description_string = str(thisTrait.description).strip()
                                if (thisTrait.db.type == "ProbeSet"):
                                        target_string = str(thisTrait.probe_target_description).strip()

                                        description_display = ''

                                        if len(description_string) > 1 and description_string != 'None':
                                                description_display = description_string
                                        else:
                                                description_display = thisTrait.symbol

                                        if len(description_display) > 1 and description_display != 'N/A' and len(target_string) > 1 and target_string != 'None':
                                                description_display = description_display + '; ' + target_string.strip()

                                        description_string = description_display

                                tr.append(TDCell(HT.TD(description_string, Class=className), description_string, description_string))
                        else:
                                tr.append(TDCell(HT.TD("--", align="left", Class=className), "--", "Zz"))

                        #location column
                        if (thisTrait.db.type == "Publish"):
                                tr.append(TDCell(HT.TD("--", align="left", Class=className), "--", "Zz"))
                        else:
                                #ZS: trait_location_value is used for sorting
                                trait_location_repr = "N/A"
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

                                tr.append( TDCell(HT.TD(trait_location_repr, nowrap="yes", Class=className), trait_location_repr, trait_location_value) )

                        if (thisTrait.db.type == "ProbeSet"):
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

