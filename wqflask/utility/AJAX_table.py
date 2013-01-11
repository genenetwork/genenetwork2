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

import cPickle
import os
import MySQLdb
import time
import pyXLWriter as xl

from htmlgen import HTMLgen2 as HT

from base import webqtlConfig
from THCell import THCell
from TDCell import TDCell
import webqtlUtil


class AJAX_table:
    def __init__(self, fd):
        file = fd.formdata.getfirst("file", "")
        sort = fd.formdata.getfirst("sort", "")
        order = fd.formdata.getfirst("order", "up")
        cmd = fd.formdata.getfirst("cmd", "")
        tableID = fd.formdata.getfirst("tableID", "")
        addIndex = fd.formdata.getfirst("addIndex", "1")
        hiddenColumnsString = fd.formdata.getfirst("hiddenColumns", "")
        hiddenColumns = hiddenColumnsString.split(',')

        try:
            fp = open(os.path.join(webqtlConfig.TMPDIR, file + '.obj'), 'rb')
            tblobj = cPickle.load(fp)
            fp.close()

            if cmd == 'addCorr':
                dbId = int(fd.formdata.getfirst("db"))
                dbFullName = fd.formdata.getfirst("dbname")
                trait = fd.formdata.getfirst("trait")
                form = fd.formdata.getfirst("form")
                ids = fd.formdata.getfirst("ids")
                vals = fd.formdata.getfirst("vals")
                ids = eval(ids)
                nnCorr = len(ids)
                vals = eval(vals)

                workbook = xl.Writer('%s.xls' % (webqtlConfig.TMPDIR+file))
                worksheet = workbook.add_worksheet()

                con = MySQLdb.Connect(db=webqtlConfig.DB_NAME,host=webqtlConfig.MYSQL_SERVER, user=webqtlConfig.DB_USER,passwd=webqtlConfig.DB_PASSWD)
                cursor = con.cursor()

                cursor.execute("Select name, ShortName from ProbeSetFreeze where Id = %s", dbId)
                dbName, dbShortName = cursor.fetchone()

                tblobj['header'][0].append(
                        THCell(HT.TD(dbShortName, Class="fs11 ffl b1 cw cbrb"),
                        text="%s" % dbShortName, idx=tblobj['header'][0][-1].idx + 1),
                )

                headingStyle = workbook.add_format(align = 'center', bold = 1, border = 1, size=13, fg_color = 0x1E, color="white")
                for i, item in enumerate(tblobj['header'][0]):
                    if (i > 0):
                        worksheet.write([8, i-1], item.text, headingStyle)
                        worksheet.set_column([i-1, i-1], 2*len(item.text))

                for i, row in enumerate(tblobj['body']):
                    ProbeSetId = row[1].text
                    #XZ, 03/02/2009: Xiaodong changed Data to ProbeSetData
                    cursor.execute("""
                            Select ProbeSetData.StrainId, ProbeSetData.Value
                            From ProbeSetData, ProbeSetXRef, ProbeSet
                            where ProbeSetXRef.ProbeSetFreezeId = %d AND
                                    ProbeSetXRef.DataId = ProbeSetData.Id AND
                                    ProbeSetXRef.ProbeSetId = ProbeSet.Id AND
                                    ProbeSet.Name = '%s'
                    """ % (dbId, ProbeSetId))
                    results = cursor.fetchall()
                    vdict = {}
                    for item in results:
                        vdict[item[0]] = item[1]
                    newvals = []
                    for id in ids:
                        if vdict.has_key(id):
                            newvals.append(vdict[id])
                        else:
                            newvals.append(None)
                    corr,nOverlap= webqtlUtil.calCorrelation(newvals,vals,nnCorr)
                    repr = '%0.4f' % corr
                    row.append(
                            TDCell(HT.TD(HT.Href(text=repr, url="javascript:showCorrPlotThird('%s', '%s', '%s')" % (form, dbName, ProbeSetId), Class="fs11 fwn ffl"), " / ", nOverlap, Class="fs11 fwn ffl b1 c222", align="middle"),repr,abs(corr))
                    )

                    last_row=0
                    for j, item in enumerate(tblobj['body'][i]):
                        if (j > 0):
                            worksheet.write([9+i, j-1], item.text)
                            last_row = 9+i
                    last_row += 1

                titleStyle = workbook.add_format(align = 'left', bold = 0, size=14, border = 1, border_color="gray")
                ##Write title Info
                # Modified by Hongqiang Li
                worksheet.write([0, 0], "Citations: Please see %s/reference.html" % webqtlConfig.PORTADDR, titleStyle)
                worksheet.write([1, 0], "Trait : %s" % trait, titleStyle)
                worksheet.write([2, 0], "Database : %s" % dbFullName, titleStyle)
                worksheet.write([3, 0], "Date : %s" % time.strftime("%B %d, %Y", time.gmtime()), titleStyle)
                worksheet.write([4, 0], "Time : %s GMT" % time.strftime("%H:%M ", time.gmtime()), titleStyle)
                worksheet.write([5, 0], "Status of data ownership: Possibly unpublished data; please see %s/statusandContact.html for details on sources, ownership, and usage of these data." % webqtlConfig.PORTADDR, titleStyle)
                #Write footer info
                worksheet.write([1 + last_row, 0], "Funding for The GeneNetwork: NIAAA (U01AA13499, U24AA13513), NIDA, NIMH, and NIAAA (P20-DA21131), NCI MMHCC (U01CA105417), and NCRR (U01NR 105417)", titleStyle)
                worksheet.write([2 + last_row, 0], "PLEASE RETAIN DATA SOURCE INFORMATION WHENEVER POSSIBLE", titleStyle)

                cursor.close()
                workbook.close()

                objfile = open(os.path.join(webqtlConfig.TMPDIR, file + '.obj'), 'wb')
                cPickle.dump(tblobj, objfile)
                objfile.close()
            else:
                pass

            self.value = str(webqtlUtil.genTableObj(tblobj=tblobj, file=file, sortby=(sort, order), tableID = tableID, addIndex = addIndex, hiddenColumns = hiddenColumns))

        except:
            self.value = "<span class='fs16 fwb cr ffl'>The table is no longer available on this server</span>"

    def __str__(self):
        return self.value

    def write(self):
        return str(self)
