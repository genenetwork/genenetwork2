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

import string
import cPickle
import os

from htmlgen import HTMLgen2 as HT

from base import webqtlConfig
from utility.THCell import THCell
from utility.TDCell import TDCell
from base.webqtlTrait import webqtlTrait
from base.templatePage import templatePage
from utility import webqtlUtil
from CorrelationPage import CorrelationPage
import correlationFunction



class PartialCorrTraitPage(CorrelationPage):

    corrMinInformative = 4


    def __init__(self,fd):

        templatePage.__init__(self, fd)

        if not self.openMysql():
            return

        TD_LR = HT.TD(colspan=2,height=200,width="100%",bgColor='#eeeeee')

        TD_LR.append(HT.Paragraph("Partial Correlation Table", Class="title"), '\n')

        pc_method = fd.formdata.getvalue('pcMethod')

        primaryTraitString = fd.formdata.getvalue('primaryTrait')
        primaryTrait = (webqtlTrait(fullname=primaryTraitString, cursor=self.cursor))

        controlTraitsString = fd.formdata.getvalue('controlTraits')
        controlTraitsList = list(string.split(controlTraitsString,','))
        controlTraits = []
        for item in controlTraitsList:
            controlTraits.append(webqtlTrait(fullname=item, cursor=self.cursor))

        targetTraitsString = fd.formdata.getvalue('targetTraits')
        targetTraitsList = list(string.split(targetTraitsString,','))
        targetTraits = []
        _targetnames = []
        for item in targetTraitsList:
            oneTargetTrait = webqtlTrait(fullname=item, cursor=self.cursor)
            oneTargetTrait.retrieveInfo()
            targetTraits.append( oneTargetTrait )
            _targetnames.append( oneTargetTrait.name )

        #XZ: filter out the strains that have no value.
        primaryTrait.retrieveData()
        _strains, _vals, _vars = primaryTrait.exportInformative()

        #XZ: _controlstrains, _controlvals and _controlvars are list of list [ [], [], ...]. _controlNs is number
        _controlstrains,_controlvals,_controlvars,_controlNs = correlationFunction.controlStrains(controlTraitsString,_strains)

        N = len(_strains)

        allsame = True
        ##allsame is boolean for whether or not primary and control trait have values for the same strains
        for i in _controlstrains:
                if _strains != i:
                        allsame=False
                        break

        ##   If the strains for which each of the control traits and the primary trait have values are not identical, 
        ## we must remove from the calculation all vlaues for strains that are not present in each. Without doing this,
        ## undesirable biases would be introduced.
        # XZ, 01/11/2010: After execution of function fixStrains, variables _vals,_controlvals,_vars,_controlvars have the same number and same order of strains as strains in variable _strains. The _controlstrains remains intact.
        if not allsame:
                _strains,_vals,_controlvals,_vars,_controlvars = correlationFunction.fixStrains(_strains,_controlstrains,_vals,_controlvals,_vars,_controlvars)
                N = len(_strains)

        #XZ: We should check the value of control trait and primary trait here.
        nameOfIdenticalTraits = correlationFunction.findIdenticalTraits ( _vals, primaryTraitString, _controlvals, controlTraitsList )
        if nameOfIdenticalTraits:
            heading = "Partial Correlation Table"
            detail = ['%s and %s have same values for the %s strains that will be used to calculate partial correlation (common for all primary and control traits). In such case, partial correlation can NOT be calculated. Please re-select your traits.' % (nameOfIdenticalTraits[0], nameOfIdenticalTraits[1], len(_vals))]
            self.error(heading=heading,detail=detail)
            return


        if N < self.corrMinInformative:
            heading = "Partial Correlation Table"
            detail = ['Fewer than %d strain data were entered for %s data set. No calculation of correlation has been attempted.' % (self.corrMinInformative, fd.RISet)]
            self.error(heading=heading,detail=detail)
            return

        #XZ, 01/11/2010: Pay attention to the target trait strain number and order!
        #XZ 03/29/2010: need to input target trait values to this function.

        _targetvals = []
        for oneTargetTrait in targetTraits:
            oneTargetTrait.retrieveData()
            oneTraitVals = oneTargetTrait.exportData( _strains )
            _targetvals.append(oneTraitVals)


        if pc_method == 'spearman':
            allcorrelations = correlationFunction.determinePartialsByR(primaryVal = _vals, controlVals = _controlvals, targetVals = _targetvals, targetNames = _targetnames, method='s')
        else:
            allcorrelations = correlationFunction.determinePartialsByR(primaryVal = _vals, controlVals = _controlvals, targetVals = _targetvals, targetNames = _targetnames)

        totalTraits = len(allcorrelations)


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
            controlTraitsTable.append(HT.TR(HT.TD("%d."%seq,align="left", width=10),
                                            HT.TD(HT.Href(text='%s' % descriptionString,url="javascript:showDatabase2('%s','%s','%s')" % (thisTrait.db.name,thisTrait.name,thisTrait.cellid), Class="fs12 fwn") )))
            seq += 1

        info_form.append(controlTraitsTable)


        TD_LR.append(info_form)        


        mainfmName = webqtlUtil.genRandStr("fm_")
        form = HT.Form(cgi= os.path.join(webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE), enctype='multipart/form-data', name= mainfmName, submit=HT.Input(type='hidden'))

        hddn = {'FormID':'showDatabase', 'database':'_', 'ProbeSetID':'_', 'CellID':'_' }#XZ: These four parameters are required by javascript function showDatabase2.

        for key in hddn.keys():
            form.append(HT.Input(name=key, value=hddn[key], type='hidden'))


        filename= webqtlUtil.genRandStr("Corr_")

        tblobj = {}

        if pc_method == 'spearman':
            tblobj['header'] = \
            [[THCell(HT.TD('', Class="fs13 fwb ffl b1 cw cbrb"), sort=0),
              THCell(HT.TD('Database', Class="fs13 fwb ffl b1 cw cbrb",align='center'), text='db', idx=1),
              THCell(HT.TD('Record', Class="fs13 fwb ffl b1 cw cbrb",align='center'), text='id', idx=2),
              THCell(HT.TD('Symbol', Class="fs13 fwb ffl b1 cw cbrb"), text='symbol', idx=3),
              THCell(HT.TD('Description', Class="fs13 fwb ffl b1 cw cbrb", align='center'), text='desc', idx=4),
              THCell(HT.TD('N ', nowrap="on", Class="fs13 fwb ffl b1 cw cbrb"), text='nstr', idx=5),
              THCell(HT.TD('Partial rho ', nowrap="on", Class="fs13 fwb ffl b1 cw cbrb"), text='partial_corr', idx=6),
              THCell(HT.TD('p(partial rho)', Class="fs13 fwb ffl b1 cw cbrb",nowrap='ON'), text='partial_pv', idx=7),
              THCell(HT.TD('rho ', nowrap="on", Class="fs13 fwb ffl b1 cw cbrb"), text='corr', idx=8),
              THCell(HT.TD('p(rho)', Class="fs13 fwb ffl b1 cw cbrb",nowrap='ON'), text='pv', idx=9),
              THCell(HT.TD('delta rho', Class="fs13 fwb ffl b1 cw cbrb",nowrap='ON'), text='delta_rho', idx=10)]]
        else:
            tblobj['header'] = \
            [[THCell(HT.TD('', Class="fs13 fwb ffl b1 cw cbrb"), sort=0),
              THCell(HT.TD('Database', Class="fs13 fwb ffl b1 cw cbrb",align='center'), text='db', idx=1),
              THCell(HT.TD('Record', Class="fs13 fwb ffl b1 cw cbrb",align='center'), text='id', idx=2),
              THCell(HT.TD('Symbol', Class="fs13 fwb ffl b1 cw cbrb"), text='symbol', idx=3),
              THCell(HT.TD('Description', Class="fs13 fwb ffl b1 cw cbrb", align='center'), text='desc', idx=4),
              THCell(HT.TD('N ', nowrap="on", Class="fs13 fwb ffl b1 cw cbrb"), text='nstr', idx=5),
              THCell(HT.TD('Partial r ', nowrap="on", Class="fs13 fwb ffl b1 cw cbrb"), text='partial_corr', idx=6),
              THCell(HT.TD('p(partial r)', Class="fs13 fwb ffl b1 cw cbrb",nowrap='ON'), text='partial_pv', idx=7),
              THCell(HT.TD('r ', nowrap="on", Class="fs13 fwb ffl b1 cw cbrb"), text='corr', idx=8),
              THCell(HT.TD('p(r)', Class="fs13 fwb ffl b1 cw cbrb",nowrap='ON'), text='pv', idx=9),
              THCell(HT.TD('delta r', Class="fs13 fwb ffl b1 cw cbrb",nowrap='ON'), text='delta_r', idx=10)]]

        sortby = ("partial_pv", "up")

        tblobj['body'] = []
        for i, thisTrait in enumerate(targetTraits):
            tr = []

            trId = str(thisTrait)
            tr.append(TDCell(HT.TD(HT.Input(type="checkbox", Class="checkbox", name="searchResult",value=trId, onClick="highlight(this)"), nowrap="on", Class="fs12 fwn ffl b1 c222"), text=trId))
            tr.append(TDCell(HT.TD(HT.Href(text=thisTrait.db.fullname,url=webqtlConfig.INFOPAGEHREF % thisTrait.db.name,target="_blank", Class="fs12 fwn"), Class="fs12 fwn ffl b1 c222"), text=thisTrait.db.name, val=thisTrait
.db.name.upper()))
            tr.append(TDCell(HT.TD(HT.Href(text=thisTrait.name,url="javascript:showDatabase3('%s', '%s', '%s', '%s')" % (mainfmName,thisTrait.db.name,thisTrait.name,thisTrait.cellid), Class="fs12 fwn"), Class="fs12 fwn b1 c222"), text=thisTrait.name, val=thisTrait.name))

            #XZ: Symbol column
            if thisTrait.db.type =="ProbeSet":
                if thisTrait.symbol:
                    tr.append(TDCell(HT.TD(thisTrait.symbol, Class="fs12 fwn ffl b1 c222"), text=thisTrait.symbol, val=thisTrait.symbol.upper()))
                else:
                    tr.append(TDCell(HT.TD('NA', Class="fs12 fwn ffl b1 c222"), text='NA', val='NA'))
            elif thisTrait.db.type =="Publish":
                AbbreviationString = "--"
                if (thisTrait.post_publication_abbreviation != None):
                    AbbreviationString = thisTrait.post_publication_abbreviation

                if thisTrait.confidential:
                    if not webqtlUtil.hasAccessToConfidentialPhenotypeTrait(privilege=self.privilege, userName=self.userName, authorized_users=thisTrait.authorized_users):
                        if thisTrait.pre_publication_abbreviation:
                            AbbreviationString = thisTrait.pre_publication_abbreviation
                        else:
                            AbbreviationString = "--"

                if AbbreviationString == "--":
                    tr.append(TDCell(HT.TD('NA', Class="fs12 fwn ffl b1 c222"), text='NA', val='NA'))
                else:
                    tr.append(TDCell(HT.TD(AbbreviationString, Class="fs12 fwn ffl b1 c222"), text=AbbreviationString, val=AbbreviationString.upper()))
            else:
                tr.append(TDCell(HT.TD(thisTrait.name, Class="fs12 fwn ffl b1 c222"), text=thisTrait.name, val=thisTrait.name))

            #XZ: Description column
            if thisTrait.db.type =="ProbeSet" or thisTrait.db.type == "Temp":
                tr.append(TDCell(HT.TD(thisTrait.description, Class="fs12 fwn ffl b1 c222"), text=thisTrait.description, val=thisTrait.description.upper()))
            elif thisTrait.db.type =="Publish":
		PhenotypeString = thisTrait.post_publication_description
		if thisTrait.confidential:
			if not webqtlUtil.hasAccessToConfidentialPhenotypeTrait(privilege=self.privilege, userName=self.userName, authorized_users=thisTrait.authorized_users):
				PhenotypeString = thisTrait.pre_publication_description
                tr.append(TDCell(HT.TD(PhenotypeString, Class="fs12 fwn ffl b1 c222"), text=PhenotypeString, val=PhenotypeString.upper()))
            else:
                tr.append(TDCell(HT.TD(thisTrait.name, Class="fs12 fwn ffl b1 c222"), text=thisTrait.name, val=thisTrait.name))

            tr.append(TDCell(HT.TD(allcorrelations[i][1], Class="fs12 fwn ffl b1 c222", align='right'), text=allcorrelations[i][1], val=allcorrelations[i][1]))

            #partial correlation result
            try:
                repr = '%3.3f' % float(allcorrelations[i][2])
                tr.append(TDCell(HT.TD(repr, Class="fs12 fwn ffl b1 c222", align='right'), text=repr, val=abs(allcorrelations[i][2])))
            except:
                repr = 'NA'
                tr.append(TDCell(HT.TD(repr, Class="fs12 fwn ffl b1 c222", align='left'), text=repr, val=0 ))

            repr = webqtlUtil.SciFloat(allcorrelations[i][3])
            tr.append(TDCell(HT.TD(repr, Class="fs12 fwn ffl b1 c222", nowrap='ON', align='right'), text=repr, val=allcorrelations[i][3]))

            #zero order correlation result
            repr = '%3.3f' % float(allcorrelations[i][4])
            tr.append(TDCell(HT.TD(repr, Class="fs12 fwn ffl b1 c222", align='right'), text=repr, val=abs(allcorrelations[i][4])))

            repr = webqtlUtil.SciFloat(allcorrelations[i][5])
            tr.append(TDCell(HT.TD(repr, Class="fs12 fwn ffl b1 c222", nowrap='ON', align='right'), text=repr, val=allcorrelations[i][5]))

            #delta
            try:
                repr = '%3.3f' % ( float(allcorrelations[i][2]) - float(allcorrelations[i][4]) )
                tr.append(TDCell(HT.TD(repr, Class="fs12 fwn ffl b1 c222", align='right'), text=repr, val=repr ))
            except:
                repr = 'NA'
                tr.append(TDCell(HT.TD(repr, Class="fs12 fwn ffl b1 c222", align='left'), text=repr, val=0 ))

            tblobj['body'].append(tr)

        objfile = open('%s.obj' % (webqtlConfig.TMPDIR+filename), 'wb')
        cPickle.dump(tblobj, objfile)
        objfile.close()
		# NL, 07/27/2010. genTableObj function has been moved from templatePage.py to webqtlUtil.py;
        div = HT.Div(webqtlUtil.genTableObj(tblobj=tblobj, file=filename, sortby=sortby, tableID = "sortable", addIndex = "1"), Id="sortable")
        form.append(div)


        TD_LR.append(HT.Center(form),HT.P())

        self.dict['body'] =  str(TD_LR)
		# updated by NL, moved js function xmlhttpPost() and updatepage() to dhtml.js
        self.dict['js1'] = ''
        self.dict['title'] = 'Partial Correlation Result'

