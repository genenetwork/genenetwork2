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
from htmlgen import HTMLgen2 as HT

from base.templatePage import templatePage
from base import webqtlConfig
from heatmap.Heatmap import Heatmap


# XZ, 09/09/2008: After adding several traits to collection, click "QTL Heatmap" button,
# XZ, 09/09/2008: This class will generate what you see.
#########################################
#      QTL heatmap Page
#########################################
class heatmapPage(templatePage):

        def __init__(self,fd):

                templatePage.__init__(self, fd)

                if not self.openMysql():
                        return
                if not fd.genotype:
                        fd.readGenotype()

                searchResult = fd.formdata.getvalue('searchResult')
                if not searchResult:
                        heading = 'QTL Heatmap'
                        detail = ['You need to select at least two traits in order to generate QTL heatmap.']
                        self.error(heading=heading,detail=detail)
                        return
                if type("1") == type(searchResult):
                        searchResult = string.split(searchResult,'\t')
                if searchResult:
                        if len(searchResult) > webqtlConfig.MAXCORR:
                                heading = 'QTL Heatmap'
                                detail = ['In order to display the QTL heat map properly, do not select more than %d traits for analysis.' % webqtlConfig.MAXCORR]
                                self.error(heading=heading,detail=detail)
                                return
                else:
                        heading = 'QTL Heatmap'
                        detail = [HT.Font('Error : ',color='red'),HT.Font('Error occurs while retrieving data from database.',color='black')]
                        self.error(heading=heading,detail=detail)
                        return
                self.dict['title'] = 'QTL heatmap'
                NNN = len(searchResult)
                if NNN == 0:
                        heading = "QTL Heatmap"
                        detail = ['No trait was selected for %s data set. No QTL heatmap was generated.' % fd.RISet]
                        self.error(heading=heading,detail=detail)
                        return
                elif NNN < 2:
                        heading = 'QTL Heatmap'
                        detail = ['You need to select at least two traits in order to generate QTL heatmap.']
                        self.error(heading=heading,detail=detail)
                        return
                else:
                        colorScheme = fd.formdata.getvalue('colorScheme')
                        if not colorScheme:
                                colorScheme = '1'
                        heatmapObject = Heatmap(fd=fd, searchResult=searchResult, colorScheme=colorScheme, userPrivilege=self.privilege, userName=self.userName)
                        filename, areas, sessionfile = heatmapObject.getResult()
                        gifmap = HT.Map(name='traitMap')
                        for area in areas:
                                Areas = HT.Area(shape='rect', coords=area[0], href=area[1], title=area[2])
                                gifmap.areas.append(Areas)
                        img2=HT.Image('/image/'+filename+'.png',border=0,usemap='#traitMap')
                        imgUrl = 'Right-click or control-click on the link to download this graph as a <a href="/image/%s.png" class="normalsize" target="_blank">PNG file</a>' % filename
                        form = HT.Form(cgi= os.path.join(webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE), enctype='multipart/form-data', name='showDatabase', submit=HT.Input(type='hidden'))
                        hddn = {'FormID':'showDatabase','ProbeSetID':'_','database':fd.RISet+"Geno",'CellID':'_','RISet':fd.RISet,'searchResult':string.join(searchResult,'\t')}
                        if fd.incparentsf1:
                                hddn['incparentsf1']='ON'
                        for key in hddn.keys():
                                form.append(HT.Input(name=key, value=hddn[key], type='hidden'))
                        heatmapButton = HT.Input(type='button' ,name='mintmap',value='Redraw QTL Heatmap', onClick="databaseFunc(this.form,'heatmap');",Class="button")
                        spects = {'0':'Single Spectrum','1':'Grey + Blue + Red','2':'Blue + Red'}
                        schemeMenu = HT.Select(name='colorScheme')
                        schemeMenu.append(('Single Spectrum',0))
                        schemeMenu.append(('Grey + Blue + Red',1))
                        schemeMenu.append(('Blue + Red',2))
                        schemeMenu.selected.append(spects[colorScheme])
                        clusterCheck= HT.Input(type='checkbox', Class='checkbox', name='clusterCheck',checked=0)
                        targetDescriptionCheck = HT.Input(type='checkbox', Class='checkbox', name='targetDescriptionCheck',checked=0)
                        form.append(gifmap,schemeMenu, heatmapButton, HT.P(), clusterCheck, '  Cluster traits  ', targetDescriptionCheck, '  Add description', HT.P(),img2, HT.P(), imgUrl)
                        form.append(HT.Input(name='session', value=sessionfile, type='hidden'))
                        heatmapHelp = HT.Input(type='button' ,name='heatmapHelpButton',value='Info', onClick="openNewWin('/heatmap.html');",Class="button")
                        heatmapHeading = HT.Paragraph('QTL Heatmap ', heatmapHelp, Class="title")
                        TD_LR = HT.TD(colspan=2,height=200,width="100%",bgColor='#eeeeee')
                        TD_LR.append(heatmapHeading, HT.P(),HT.P(),HT.P(),HT.P(),HT.P(),form)
                        self.dict['body'] = str(TD_LR)
