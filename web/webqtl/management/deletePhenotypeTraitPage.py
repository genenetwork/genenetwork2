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

from htmlgen import HTMLgen2 as HT

from base.templatePage import templatePage
from base import webqtlConfig
from base.webqtlDataset import webqtlDataset
from base.webqtlTrait import webqtlTrait


#XZ, 09/07/2009: Xiaodong created this class
class deletePhenotypeTraitPage(templatePage):

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
                self.dict['title'] =  'Delete Phenotype Trait Input Page'
            if status == 'check':
                PublishFreeze_Name = fd.formdata.getvalue('PublishFreeze_Name')
                traitID = fd.formdata.getvalue('traitID')
                self.dict['body'] =  self.checkInputPage(PublishFreeze_Name, traitID)
                self.dict['title'] =  'Delete Phenotype Trait Check Input Page'
            if status == 'delete':
                PublishFreeze_Name = fd.formdata.getvalue('PublishFreeze_Name')
                traitID = fd.formdata.getvalue('traitID')
                self.dict['body'] =  self.deleteResultPage(PublishFreeze_Name, traitID)
                self.dict['title'] =  'Delete Phenotype Trait Result Page'


    def genInputPage(self):

        crossMenu = HT.Select(name='PublishFreeze_Name', onChange='xchange()')

        self.cursor.execute('select PublishFreeze.Name from PublishFreeze, InbredSet where InbredSetId=InbredSet.Id')
        result = self.cursor.fetchall()

        for one_row in result:
            Name = one_row
            crossMenu.append(tuple([Name,Name]))

        TD_LR = HT.TD(height=200,width="100%",bgColor='#eeeeee')

        deletePhenotypeTraitForm = HT.Form(cgi= os.path.join(webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE), enctype='multipart/form-data', name='deletePhenotypeTraitForm', submit=HT.Input(type='hidden'))
        deletePhenotypeTraitForm.append(
                HT.Blockquote(
                              HT.Font('Publish Freeze Name '),
                              crossMenu,
                              HT.Font('   Phenotype Trait ID '),
                              HT.Input(type='text' ,name='traitID',value='', size=20,maxlength=20),
                              HT.Input(type='Submit', value='Submit', Class="button")),
                HT.Input(type='hidden',name='FormID',value='deletePhenotypeTrait'),
                HT.Input(type='hidden',name='ifVerified',value='GN@UTHSC'),
                HT.Input(type='hidden',name='status',value='check')
        )

        TD_LR.append(deletePhenotypeTraitForm)

        return str(TD_LR)


    def checkInputPage(self, PublishFreeze_Name, traitID):
        TD_LR = HT.TD(height=200,width="100%",bgColor='#eeeeee')

        try:
            db = webqtlDataset(PublishFreeze_Name, self.cursor)
            thisTrait = webqtlTrait(db=db, cursor=self.cursor, name=traitID)
            thisTrait.retrieveInfo()
            setDescription = thisTrait.genHTML(dispFromDatabase=1, privilege=self.privilege, userName=self.userName, authorized_users=thisTrait.authorized_users)
        except:
            TD_LR.append( HT.Font('This trait is not found. Please go back to check if you selected correct Group Name and inputed correct trait ID.', color='red') )
            return str(TD_LR)

        #TD_LR.append(HT.Font('Publish Freeze Name: %s' % PublishFreeze_Name, color='red'),HT.BR(), HT.Font('trait ID: %s' % traitID, color='red'), HT.BR())

        formMain = HT.Form(cgi=os.path.join(webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE), enctype='multipart/form-data', name='showDatabase', submit=HT.Input(type='hidden'))

        formMain.append(
                HT.Blockquote(
                              HT.Font('The trait '),
                              setDescription,
                              HT.Font(' will be deleted.'),
                              HT.BR(), HT.BR(),
                              HT.Font('Please open the trait and make sure you do want to delete it.', color = 'red')
                ),
                HT.Input(type='hidden',name='FormID',value=''),
                HT.Input(type='hidden',name='database',value=''),
                HT.Input(type='hidden',name='ProbeSetID',value=''),
                HT.Input(type='hidden',name='CellID',value='')
        )

        deletePhenotypeTraitForm = HT.Form(cgi= os.path.join(webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE), enctype='multipart/form-data', name='deletePhenotypeTraitForm', submit=HT.Input(type='hidden'))
        deletePhenotypeTraitForm.append(
            HT.Input(type='Submit', value='Delete Trait', Class="button"),
            HT.Input(type='hidden',name='FormID',value='deletePhenotypeTrait'),
            HT.Input(type='hidden',name='ifVerified',value='GN@UTHSC'),
            HT.Input(type='hidden',name='status',value='delete'),
            HT.Input(type='hidden',name='PublishFreeze_Name',value=db),
            HT.Input(type='hidden',name='traitID',value=traitID)
        )


        TD_LR.append(formMain, HT.BR(), HT.BR(), deletePhenotypeTraitForm)
        return str(TD_LR)

    def deleteResultPage(self, PublishFreeze_Name, traitID):
        TD_LR = HT.TD(height=200,width="100%",bgColor='#eeeeee')

        #TD_LR.append(HT.Font('Publish Freeze Name: %s' % PublishFreeze_Name, color='red'),HT.BR(), HT.Font('trait ID: %s' % traitID, color='red'), HT.BR(), HT.BR(), 'Being constructed...')

        self.cursor.execute( 'select InbredSetId from PublishFreeze where Name="%s"' % PublishFreeze_Name )
        InbredSetId = self.cursor.fetchone()[0]
        #TD_LR.append(HT.BR(), HT.BR(), 'InbredSetId: ', InbredSetId)

        self.cursor.execute( 'select PhenotypeId, PublicationId, DataId from PublishXRef where Id = %s and InbredSetId = %s' % (traitID, InbredSetId) )
        result = self.cursor.fetchone()
        PhenotypeId, PublicationId, DataId = result

        #TD_LR.append(HT.BR(), 'PhenotypeId: ', PhenotypeId)
        #TD_LR.append(HT.BR(), 'PublicationId: ', PublicationId)
        #TD_LR.append(HT.BR(), 'DataId: ', DataId)

        #PublishData
        self.cursor.execute('delete from PublishData where Id = %s' % DataId)

        #PublishSE
        self.cursor.execute('delete from PublishSE where DataId = %s' % DataId)

        #NStrain
        self.cursor.execute('delete from NStrain where DataId = %s' % DataId)

        #Phenotype
        self.cursor.execute( 'select count(*) from PublishXRef where PhenotypeId = %s' % PhenotypeId )
        PhenotypeId_count = self.cursor.fetchone()[0]
        #TD_LR.append(HT.BR(), HT.BR(), 'PhenotypeId_count: ', PhenotypeId_count)
        if PhenotypeId_count > 1:
            pass
        else:
            self.cursor.execute('delete from Phenotype where Id = %s' % PhenotypeId)

        #Publication
        self.cursor.execute( 'select count(*) from PublishXRef where PublicationId = %s' % PublicationId )
        PublicationId_count = self.cursor.fetchone()[0]
        #TD_LR.append(HT.BR(), 'PublicationId_count: ', PublicationId_count)
        if PublicationId_count > 1:
            pass
        else:
            self.cursor.execute('delete from Publication where Id = %s' % PublicationId)

        #PublishXRef
        self.cursor.execute( 'delete from PublishXRef where Id = %s and InbredSetId = %s' % (traitID, InbredSetId) )

        #TD_LR.append(HT.BR(), HT.BR() )
        TD_LR.append('The trait %s has been successfully deleted from %s' % (traitID, PublishFreeze_Name))

        return str(TD_LR)
