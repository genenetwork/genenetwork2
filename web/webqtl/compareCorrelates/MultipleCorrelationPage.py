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

from base.templatePage import templatePage
from utility import webqtlUtil
from base.webqtlTrait import webqtlTrait
from base import webqtlConfig
import multitrait

# XZ, 09/09/2008: After adding several traits to collection, click "Compare Correlates" button,
# XZ, 09/09/2008: This class will generate what you see.
# XZ, 09/09/2008: This class just collect the input, then pass them to multitrait.py
#########################################
#     Multiple Correlation Page
#########################################
class MultipleCorrelationPage(templatePage):

        def __init__(self,fd):

                templatePage.__init__(self, fd)

                if not self.openMysql():
                        return
                if not fd.genotype:
                        fd.readData()

                self.searchResult = fd.formdata.getvalue('searchResult')
                if not self.searchResult:
                        heading = 'Compare Correlates'
                        detail = ['You need to select at least two traits in order to generate correlation matrix.']
                        self.error(heading=heading,detail=detail)
                        print 'Content-type: text/html\n'
                        self.write()
                        return
                if type("1") == type(self.searchResult):
                        self.searchResult = [self.searchResult]

                if self.searchResult:
                        if len(self.searchResult) > 100:
                                heading = 'Compare Correlates'
                                detail = ['In order to display Compare Correlates properly, Do not select more than %d traits for Compare Correlates.' % 100]
                                self.error(heading=heading,detail=detail)
                                print 'Content-type: text/html\n'
                                self.write()
                                return
                        else:
                                pass

                        traitList = []
                        for item in self.searchResult:
                                thisTrait = webqtlTrait(fullname=item, cursor=self.cursor)
                                thisTrait.retrieveInfo()
                                traitList.append(thisTrait)
                else:
                        heading = 'Compare Correlates'
                        detail = [HT.Font('Error : ',color='red'),HT.Font('Error occurs while retrieving data from database.',color='black')]
                        self.error(heading=heading,detail=detail)
                        print 'Content-type: text/html\n'
                        self.write()
                        return


                ##########
                filename= webqtlUtil.genRandStr("mult_")
                fp = open(webqtlConfig.IMGDIR+filename, 'wb')
                fp.write('%s\n' % fd.RISet)
                for thisTrait in traitList:
                        fp.write("%s,%s,%s\n" % (thisTrait.db.type,thisTrait.db.id,thisTrait.name))
                fp.close()
                fd.formdata["filename"] = filename

                params = {"filename":filename, "targetDatabase":"",
                        "threshold":0.5, "subsetSize":10,
                        "correlation":"pearson", "subsetCount":10,
                        "firstRun":"1"}
                results = []
                txtOutputFileName = ""

                self.dict['body'] = multitrait.TraitCorrelationPage(fd, params, self.cursor, traitList, results, 
                                                        fd.RISet,txtOutputFileName).dict['body']
                self.dict['title'] = 'Compare Correlates'
            



