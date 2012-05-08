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

#ODEPage.py

import string
from htmlgen import HTMLgen2 as HT

from base import webqtlConfig
from base.webqtlTrait import webqtlTrait
from base.templatePage import templatePage
from dbFunction import webqtlDatabaseFunction
		
class ODEPage(templatePage):

    def __init__(self,fd):

        templatePage.__init__(self, fd)

        if not self.openMysql():
            return

        #XZ, self.theseTraits holds the "ProbeSet" traits.
        self.theseTraits = []

        self.searchResult = fd.formdata.getvalue('searchResult', [])
        if type("1") == type(self.searchResult):
            self.searchResult = [self.searchResult]

        for item in self.searchResult:
            try:
                thisTrait = webqtlTrait(fullname=item, cursor=self.cursor)
                thisTrait.retrieveInfo(QTL=1)
                if thisTrait.db.type == "ProbeSet":
                    self.theseTraits.append(thisTrait)
            except:
                pass

        if self.theseTraits:
            pass
        else:
            heading = 'ODE'
            detail = ['You need to select at least one microarray trait to submit.']
            self.error(heading=heading,detail=detail)
            return

        chipName = self.getChipName(fd)
        species = webqtlDatabaseFunction.retrieveSpecies(cursor=self.cursor, RISet=fd.RISet)

        if species == 'rat':
            species = 'Rattus norvegicus'
        elif species == 'human':
            species = 'Homo sapiens'
        elif species == 'mouse':
            species = 'Mus musculus'
        else:
            species = ''

        probesetNameList = self.getProbesetNameList(fd)

        TD_LR = HT.TD(height=200,width="100%",bgColor='#eeeeee',valign="middle")

        formODE = HT.Form(cgi="http://ontologicaldiscovery.org/index.php?action=manage&cmd=importGeneSet", enctype='multipart/form-data', name='formODE', submit = HT.Input(type='hidden'))

        hddnODE = {}

        hddnODE['client'] = 'genenetwork'
        hddnODE['species'] = species
        hddnODE['idtype'] = chipName
        hddnODE['list'] = string.join(probesetNameList, ",")

        for key in hddnODE.keys():
            formODE.append(HT.Input(name=key, value=hddnODE[key], type='hidden'))

        TD_LR.append(formODE)

        TD_LR.append(HT.Paragraph("Your selections of %d traits is being exported to the ODE" % len(self.theseTraits), Class="cr fs16 fwb", align="Center"))
        # updated by NL, moved mixedChipError() to webqtl.js and change it to mixedChipError(methodName)		
        if chipName == 'mixed':
            methodName = "ODE" 	
            self.dict['js1'] = """
                <SCRIPT LANGUAGE="JavaScript">
                    setTimeout("mixedChipError('%s')",1000);
                </SCRIPT>
                        """ % methodName 
        else:
            self.dict['js1'] = """
                <SCRIPT LANGUAGE="JavaScript">
                    setTimeout('document.formODE.submit()',1000);
                </SCRIPT>
                """

        self.dict['body'] = TD_LR



    def getProbesetNameList(self, fd):
        probesetNameList = []

        for item in self.theseTraits:
            probesetNameList.append(item.name)

        return probesetNameList



    def getChipName(self, fd):
        chipName0 = ""
        for item in self.theseTraits:
            self.cursor.execute('SELECT GeneChip.Name FROM GeneChip, ProbeFreeze, ProbeSetFreeze WHERE GeneChip.Id = ProbeFreeze.ChipId and ProbeSetFreeze.ProbeFreezeId = ProbeFreeze.Id and ProbeSetFreeze.Name = "%s"' % item.db.name)
            chipName = self.cursor.fetchone()[0]
            if chipName != chipName0:
                if chipName0:
                    return 'mixed'
                else:
                    chipName0 = chipName
            else:
                pass

        return chipName
