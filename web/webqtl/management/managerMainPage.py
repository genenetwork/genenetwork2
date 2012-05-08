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
from utility import webqtlUtil
from base import webqtlConfig

#XZ, 02/06/2009: Xiaodong created this class
class managerMainPage(templatePage):

    def __init__(self, fd):

        templatePage.__init__(self, fd)

        if not self.openMysql():
            return

        ifVerified = None

        ifVerified = fd.formdata.getvalue('ifVerified')

        if ifVerified != 'GN@UTHSC':
            user = fd.formdata.getvalue('user')
            password = fd.formdata.getvalue('password')
            privilege, user_id, userExist = webqtlUtil.authUser(user,password,self.cursor,encrypt = None)[:3]

            if userExist and webqtlConfig.USERDICT[privilege] >= webqtlConfig.USERDICT['admin']:
                ifVerified = True


        if not ifVerified:
            heading = "Error page"
            detail = ["You do not have privilege to change system configuration."]
            self.error(heading=heading,detail=detail)
            return
	else:
            TD_LR = HT.TD(height=200,width="100%", bgColor='#eeeeee')
            
            heading = "Please click button to make your selection"

            createUserAccountForm = HT.Form(cgi= os.path.join(webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE), enctype='multipart/form-data', name='createUserAccountForm', submit=HT.Input(type='hidden'))
            createUserAccountForm.append(
                HT.Input(type='button', name='', value='Manage User Accounts', Class="button", onClick="submitToNewWindow(this.form);"),
                HT.Input(type='hidden',name='FormID',value='createUserAccount'),
                HT.Input(type='hidden',name='ifVerified',value='GN@UTHSC')
            )

            assignUserToDatasetForm = HT.Form(cgi= os.path.join(webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE), enctype='multipart/form-data', name='assignUserToDatasetForm', submit=HT.Input(type='hidden'))
            assignUserToDatasetForm.append(
                HT.Input(type='button', name='', value='Manage Confidential Datasets', Class="button", onClick="submitToNewWindow(this.form);"),
                HT.Input(type='hidden',name='FormID',value='assignUserToDataset'),
                HT.Input(type='hidden',name='ifVerified',value='GN@UTHSC')
            )

            deletePhenotypeTraitForm = HT.Form(cgi= os.path.join(webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE), enctype='multipart/form-data', name='deletePhenotypeTraitForm', submit=HT.Input(type='hidden'))
            deletePhenotypeTraitForm.append(
                HT.Input(type='button', name='', value='Delete Phenotype Trait', Class="button", onClick="submitToNewWindow(this.form);"),
                HT.Input(type='hidden',name='FormID',value='deletePhenotypeTrait'),
                HT.Input(type='hidden',name='ifVerified',value='GN@UTHSC'),
                HT.Input(type='hidden',name='status',value='input')
            )

            exportPhenotypeDatasetForm = HT.Form(cgi= os.path.join(webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE), enctype='multipart/form-data', name='exportPhenotypeDatasetForm', submit=HT.Input(type='hidden'))
            exportPhenotypeDatasetForm.append(
                HT.Input(type='button', name='', value='Export Phenotype Dataset', Class="button", onClick="submitToNewWindow(this.form);"),
                HT.Input(type='hidden',name='FormID',value='exportPhenotypeDataset'),
                HT.Input(type='hidden',name='ifVerified',value='GN@UTHSC'),
                HT.Input(type='hidden',name='status',value='input')
            )

            updateGenotypeForm = HT.Form(cgi= os.path.join(webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE), enctype='multipart/form-data', name='updateGenotypeForm', submit=HT.Input(type='hidden'))
            updateGenotypeForm.append(
                HT.Input(type='button', name='', value='Update Genotype', Class="button", onClick="submitToNewWindow(this.form);"),
                HT.Input(type='hidden',name='FormID',value='updGeno'),
                HT.Input(type='hidden',name='ifVerified',value='GN@UTHSC')
            )

            editHeaderForm = HT.Form(cgi= os.path.join(webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE), enctype='multipart/form-data', name='editHeaderForm', submit=HT.Input(type='hidden'))
            editHeaderForm.append(
                HT.Input(type='button', name='', value='Edit Header', Class="button", onClick="submitToNewWindow(this.form);"),
		HT.Input(type='hidden', name='FormID', value='editHeaderFooter'),
		HT.Input(type='hidden', name='hf', value='h'),
            )

            editFooterForm = HT.Form(cgi= os.path.join(webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE), enctype='multipart/form-data', name='editFooterForm', submit=HT.Input(type='hidden'))
            editFooterForm.append(
                HT.Input(type='button', name='', value='Edit Footer', Class="button", onClick="submitToNewWindow(this.form);"),
                HT.Input(type='hidden', name='FormID', value='editHeaderFooter'),
		HT.Input(type='hidden', name='hf', value='f'),
            )

            TD_LR.append(heading, HT.P(),HT.P(), 
			createUserAccountForm, HT.P(),HT.P(), 
			assignUserToDatasetForm, HT.P(),HT.P(), 
			deletePhenotypeTraitForm, HT.P(),HT.P(), 
			exportPhenotypeDatasetForm, HT.P(),HT.P(),
                        updateGenotypeForm, HT.P(),HT.P(),
			editHeaderForm, HT.P(),HT.P(),
			editFooterForm)

            self.dict['body'] =  str(TD_LR)
            self.dict['title'] =  'Manager Main Page'

