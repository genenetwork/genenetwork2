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
import pyXLWriter as xl
import time

import reaper
from htmlgen import HTMLgen2 as HT

from base.templatePage import templatePage
from utility import webqtlUtil
from base import webqtlConfig
from base.webqtlTrait import webqtlTrait



#XZ, 11/06/2009: Xiaodong created this class
class exportPhenotypeDatasetPage(templatePage):

    def __init__(self, fd):

        templatePage.__init__(self, fd)

        if not self.openMysql():
            return

        ifVerified = fd.formdata.getvalue('ifVerified')
        status = fd.formdata.getvalue('status')

        if ifVerified != 'GN@UTHSC':
            heading = "Error page"
            detail = ["You are NoT verified as administrator."]
            self.error(heading=heading,detail=detail)
            return
        else:
            if status == 'input':
                self.dict['body'] =  self.genInputPage()
                self.dict['title'] =  'Export Phenotype Dataset Input Page'
            if status == 'output':
                PublishFreeze_Name = fd.formdata.getvalue('PublishFreeze_Name')
                self.dict['body'] =  self.exportDatasetPage( fd, PublishFreeze_Name )
                self.dict['title'] =  'Export Phenotype Dataset Page'


    def genInputPage(self):

        crossMenu = HT.Select(name='PublishFreeze_Name', onChange='xchange()')

        self.cursor.execute('select PublishFreeze.Name from PublishFreeze, InbredSet where InbredSetId=InbredSet.Id')
        result = self.cursor.fetchall()

        for one_row in result:
            Name = one_row
            crossMenu.append(tuple([Name,Name]))

        TD_LR = HT.TD(height=200,width="100%",bgColor='#eeeeee')

        exportPhenotypeDatasetForm = HT.Form(cgi= os.path.join(webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE), enctype='multipart/form-data', name='exportPhenotypeDatasetForm', submit=HT.Input(type='hidden'))
        exportPhenotypeDatasetForm.append(
                HT.Blockquote(
                              HT.Font('Publish Freeze Name '),
                              crossMenu,
                              HT.Input(type='Submit', value='Submit', Class="button")),
                HT.Input(type='hidden',name='FormID',value='exportPhenotypeDataset'),
                HT.Input(type='hidden',name='status',value='output'),
                HT.Input(type='hidden',name='ifVerified',value='GN@UTHSC')
        )

        TD_LR.append( exportPhenotypeDatasetForm )

        return str(TD_LR)


    def exportDatasetPage(self, fd, PublishFreeze_Name):

        #return PublishFreeze_Name

                if not self.openMysql():
                        return

                self.cursor.execute( "select InbredSet.Name from PublishFreeze, InbredSet where PublishFreeze.InbredSetId=InbredSet.Id and PublishFreeze.Name='%s'" % PublishFreeze_Name )
                self.RISet = self.cursor.fetchone()[0]

                fd.RISet = self.RISet
                fd.incparentsf1 = 1
                fd.readGenotype()
                strainlist = fd.f1list + fd.strainlist

                #return str(strainlist)

                self.cursor.execute("Select Species.Name from Species, InbredSet where InbredSet.SpeciesId = Species.Id and InbredSet.Name = '%s'" % fd.RISet)
                self.Species = self.cursor.fetchone()[0]

                #return Species

                self.searchResult = []

                self.cursor.execute("Select PublishXRef.Id from PublishXRef, InbredSet where PublishXRef.InbredSetId = InbredSet.Id and InbredSet.Name = '%s'" % self.RISet)
                result = self.cursor.fetchall()

                for one_result in result:
                    self.searchResult.append( "%s::%s" % (PublishFreeze_Name, one_result[0]) )
                
                #return self.searchResult


                fields = ["ID", "Species", "Cross", "Database", "ProbeSetID / RecordID", "Symbol", "Description", "ProbeTarget", "PubMed_ID", "Phenotype", "Chr", "Mb", "Alias", "Gene_ID", "UniGene_ID", "Strand_Probe ", "Strand_Gene ", 
"Probe_set_specificity", "Probe_set_BLAT_score", "Probe_set_BLAT_Mb_start", "Probe_set_BLAT_Mb_end ", "QTL_Chr", "Locus_at_Peak", "Max_LRS", "P_value_of_MAX", "Mean_Expression"] + strainlist


                if self.searchResult:
                        traitList = []
                        for item in self.searchResult:
                                thisTrait = webqtlTrait(fullname=item, cursor=self.cursor)
                                thisTrait.retrieveInfo(QTL=1)
                                thisTrait.retrieveData(strainlist=strainlist)
                                traitList.append(thisTrait)

                        text = [fields]
                        for i, thisTrait in enumerate(traitList):
                                if thisTrait.db.type == 'ProbeSet':
                                        if not thisTrait.cellid: #ProbeSet
                                                text.append([str(i+1), self.Species, self.RISet, thisTrait.db.fullname, thisTrait.name, thisTrait.symbol, thisTrait.description, thisTrait.probe_target_description,"", "", thisTrait.chr, thisTrait.mb, thisTrait.alias, thisTrait.geneid, thisTrait.unigeneid, thisTrait.strand_probe, thisTrait.strand_gene, thisTrait.probe_set_specificity, thisTrait.probe_set_blat_score, thisTrait.probe_set_blat_mb_start, thisTrait.probe_set_blat_mb_end, locusChr[thisTrait.locus], thisTrait.locus, thisTrait.lrs, thisTrait.pvalue])
                                        else: #Probe
                                                text.append([str(i+1), self.Species, self.RISet, thisTrait.db.fullname, thisTrait.name + " : " + thisTrait.cellid, thisTrait.symbol, thisTrait.description, thisTrait.probe_target_description,"", "", thisTrait.chr, thisTrait.mb, thisTrait.alias, thisTrait.geneid, thisTrait.unigeneid, "", "", "", "", "", "", "", "", "", ""])
                                elif thisTrait.db.type == 'Publish':
                                    if thisTrait.pre_publication_description:
                                        if thisTrait.pubmed_id:
                                            text.append([str(i+1), self.Species, self.RISet, thisTrait.db.fullname, thisTrait.name, "", "", "", thisTrait.pubmed_id, thisTrait.post_publication_description, "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""])
                                        else:
                                            text.append([str(i+1), self.Species, self.RISet, thisTrait.db.fullname, thisTrait.name, "", "", "", "", thisTrait.pre_publication_description, "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""])
                                    else:
                                            text.append([str(i+1), self.Species, self.RISet, thisTrait.db.fullname, thisTrait.name, "", "", "", thisTrait.pubmed_id, thisTrait.post_publication_description, "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""])  

                                elif thisTrait.db.type == 'Temp':
                                        text.append([str(i+1), self.Species, self.RISet, thisTrait.db.fullname, thisTrait.name, "", thisTrait.description, "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""])
                                elif thisTrait.db.type == 'Geno':
                                        text.append([str(i+1), self.Species, self.RISet, thisTrait.db.fullname, thisTrait.name, "", thisTrait.name,"", "", "", thisTrait.chr, thisTrait.mb, "", "", "", "", "", "", "", "", "", "", "", "", ""])
                                else:
                                        continue

                                testval = thisTrait.exportData(strainlist)
                                try:
                                    mean = reaper.anova(testval)[0]
                                except:
                                    mean = 'N/A'
                                text[-1].append(mean)
                                text[-1] += testval
                        if len(text[0]) < 255 or len(text) < 255:
                                transpose = 0
                                if len(text[0]) >= 255:
                                        text = webqtlUtil.transpose(text)
                                        transpose = 1
                                filename = os.path.join(webqtlConfig.TMPDIR, webqtlUtil.generate_session() +'.xls')

                                # Create a new Excel workbook
                                workbook = xl.Writer(filename)
                                worksheet = workbook.add_worksheet()
                                headingStyle = workbook.add_format(align = 'center', bold = 1, size=13, color = 'green')
                                titleStyle = workbook.add_format(align = 'left', bold = 0, size=13, border = 1, border_color="gray")

                                ##Write title Info
                                worksheet.write([0, 0], "Data source: The GeneNetwork at %s" % webqtlConfig.PORTADDR, titleStyle)
                                worksheet.write([1, 0], "Citations: Please see %s/reference.html" % webqtlConfig.PORTADDR, titleStyle)
                                worksheet.write([2, 0], "Date : %s" % time.strftime("%B %d, %Y", time.gmtime()), titleStyle)
                                worksheet.write([3, 0], "Time : %s GMT" % time.strftime("%H:%M ", time.gmtime()), titleStyle)
                                worksheet.write([4, 0], "Status of data ownership: Possibly unpublished data; please see %s/statusandContact.html for details on sources, ownership, and usage of these data." % webqtlConfig.PORTADDR, titleStyle)
                                worksheet.write([6, 0], "This output file contains data from %d GeneNetwork databases listed below" % len(traitList), titleStyle)

                                # Row and column are zero indexed
                                nrow = startRow = 8
                                for row in text:
                                    for ncol, cell in enumerate(row):
                                        if nrow == startRow:
                                                worksheet.write([nrow, ncol], cell.strip(), headingStyle)
                                                worksheet.set_column([ncol, ncol], 2*len(cell))
                                        else:
                                                worksheet.write([nrow, ncol], cell)
                                    nrow += 1

                                worksheet.write([nrow+1, 0], "Funding for The GeneNetwork: NIAAA (U01AA13499, U24AA13513), NIDA, NIMH, and NIAAA (P20-DA 21131), NCI MMHCC (U01CA105417), and NCRR (U24 RR021760)", titleStyle)
                                worksheet.write([nrow+2, 0], "PLEASE RETAIN DATA SOURCE INFORMATION WHENEVER POSSIBLE", titleStyle)
                                workbook.close()

                                fp = open(filename, 'rb')
                                text = fp.read()
                                fp.close()

                                self.content_type = 'application/xls'
                                self.content_disposition = 'attachment; filename=%s' % ('export-%s.xls' % time.strftime("%y-%m-%d-%H-%M"))
                                self.attachment = text
                        else:
                                self.content_type = 'application/xls'
                                self.content_disposition = 'attachment; filename=%s' % ('export-%s.txt' % time.strftime("%y-%m-%d-%H-%M"))
                                for item in text:
                                        self.attachment += string.join(map(str, item), '\t')+ "\n"
                        self.cursor.close()
                else:
                        fd.req.content_type = 'text/html'
                        heading = 'Export Collection'
                        detail = [HT.Font('Error : ',color='red'),HT.Font('Error occurs while retrieving data from database.',color='black')]
                        self.error(heading=heading,detail=detail)

