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

from htmlgen import HTMLgen2 as HT
from base import webqtlConfig

from base.templatePage import templatePage


#########################################
#      Sharing List DataSet Page
#########################################
class SharingListDataSetPage(templatePage):

    def __init__(self, fd=None):
        templatePage.__init__(self, fd)

        if not self.openMysql():
            return

        if webqtlConfig.USERDICT[self.privilege] >= webqtlConfig.USERDICT['admin']:
            pass
        else:
            heading = "Editing Info"
            detail = ["You don't have the permission to list the datasets"]
            self.error(heading=heading,detail=detail,error="Error")
            return


        TD_LR = HT.TD(height=200,width="100%",bgColor='#eeeeee')

        query = """select GN_AccesionId, InfoPageTitle, Progreso from InfoFiles order by GN_AccesionId"""
        self.cursor.execute(query)
        result = self.cursor.fetchall()

        heading = HT.Paragraph('Dataset Table', Class="title")

        newrecord = HT.Href(text="New Record", url="/webqtl/main.py?FormID=sharinginfoadd")

        info = "Click the accession id to view the dataset info. Click the dataset name to edit the dataset info."

        datasetTable = HT.TableLite(border=0, cellpadding=0, cellspacing=0, Class="collap", width="100%")

        tableHeaderRow = HT.TR()
        tableHeaderRow.append(HT.TD("Accession Id", Class='fs14 fwb ffl b1 cw cbrb', align="center"))
        tableHeaderRow.append(HT.TD("Dataset name", Class='fs14 fwb ffl b1 cw cbrb', align="center"))
        tableHeaderRow.append(HT.TD("Progress", Class='fs14 fwb ffl b1 cw cbrb', align="center"))
        tableHeaderRow.append(HT.TD("Operation", Class='fs14 fwb ffl b1 cw cbrb', align="center"))
        datasetTable.append(tableHeaderRow)

        for one_row in result:
            Accession_Id, InfoPage_title, Progress = one_row
            datasetRow = HT.TR()
            datasetRow.append(HT.TD(HT.Href(text="GN%s" % Accession_Id, url="/webqtl/main.py?FormID=sharinginfo&GN_AccessionId=%s" % Accession_Id, Class='fs12 fwn'), Class="fs12 fwn b1 c222"))
            datasetRow.append(HT.TD(HT.Href(text="%s" % InfoPage_title, url="/webqtl/main.py?FormID=sharinginfo&GN_AccessionId=%s" % Accession_Id, Class='fs12 fwn'), Class="fs12 fwn b1 c222"))
            datasetRow.append(HT.TD("%s" % Progress, Class='fs12 fwn ffl b1 c222'))
            operation_edit = HT.Href(text="Edit", url="/webqtl/main.py?FormID=sharinginfoedit&GN_AccessionId=%s" % Accession_Id)
            operation_delete = HT.Href(text="Delete", onClick="deleteRecord(%s); return false;" % Accession_Id)
            operation = HT.TD(Class="fs12 fwn b1 c222", align="center")
            operation.append(operation_edit)
            operation.append("&nbsp;&nbsp;&nbsp;&nbsp;")
            operation.append(operation_delete)
            datasetRow.append(operation)
            datasetTable.append(datasetRow)

        TD_LR.append(heading, HT.P(), newrecord, HT.P(), info, HT.P(), datasetTable)

        js1 = """       <script language="javascript" type="text/javascript">
                                        function deleteRecord(id){
                                                question = confirm("Are you sure you want to delete the dataset info record (Accession Id="+id+")?")
                                                if (question != "0"){
                                                        window.open("/webqtl/main.py?FormID=sharinginfodelete&GN_AccessionId="+id, "_self");
                                                }
                                        }
                                        </script>"""
        self.dict['js1'] = js1
        self.dict['body'] =  str(TD_LR)
