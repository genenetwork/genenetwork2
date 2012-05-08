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

import MySQLdb

from base.templatePage import templatePage
from base import webqtlConfig
from dbFunction import webqtlDatabaseFunction
import SharingBody
import SharingInfo

#########################################
#      Sharing Info Update Page
#########################################
class SharingInfoUpdatePage(templatePage):

		def __init__(self, fd=None):
				templatePage.__init__(self, fd)
				if webqtlConfig.USERDICT[self.privilege] >= webqtlConfig.USERDICT['admin']:
						pass
				else:
						heading = "Editing Info"
						detail = ["You don't have the permission to modify this file"]
						self.error(heading=heading,detail=detail,error="Error")
						return
				cursor = webqtlDatabaseFunction.getCursor()
				if (not cursor):
						return
				Id=fd.formdata.getvalue('Id')
				GN_AccesionId=fd.formdata.getvalue('GN_AccesionId')
				GEO_Series=fd.formdata.getvalue('GEO_Series')
				Status=fd.formdata.getvalue('Status')
				Title=fd.formdata.getvalue('Title')
				Organism_Id=fd.formdata.getvalue('Organism_Id')
				Organism=fd.formdata.getvalue('Organism')
				Experiment_Type =fd.formdata.getvalue('Experiment_Type') 
				Summary=fd.formdata.getvalue('Summary')
				Overall_Design=fd.formdata.getvalue('Overall_Design')
				Contributor=fd.formdata.getvalue('Contributor')
				Citation=fd.formdata.getvalue('Citation')
				Submission_Date=fd.formdata.getvalue('Submission_Date')
				Contact_Name=fd.formdata.getvalue('Contact_Name')
				Emails=fd.formdata.getvalue('Emails')
				Phone=fd.formdata.getvalue('Phone')
				URL=fd.formdata.getvalue('URL')
				Organization_Name=fd.formdata.getvalue('Organization_Name')
				Department=fd.formdata.getvalue('Department')
				Laboratory=fd.formdata.getvalue('Laboratory')
				Street=fd.formdata.getvalue('Street')
				City=fd.formdata.getvalue('City')
				State=fd.formdata.getvalue('State')
				ZIP=fd.formdata.getvalue('ZIP')
				Country=fd.formdata.getvalue('Country')
				Platforms=fd.formdata.getvalue('Platforms')
				Samples=fd.formdata.getvalue('Samples')
				Species=fd.formdata.getvalue('Species')
				Tissue=fd.formdata.getvalue('Tissue')
				Normalization=fd.formdata.getvalue('Normalization')
				InbredSet=fd.formdata.getvalue('InbredSet')
				InfoPageName=fd.formdata.getvalue('InfoPageName')
				InfoPageTitle=fd.formdata.getvalue('InfoPageTitle')
				About_Cases=fd.formdata.getvalue('About_Cases')
				About_Tissue=fd.formdata.getvalue('About_Tissue')
				About_Download=fd.formdata.getvalue('About_Download')
				About_Array_Platform=fd.formdata.getvalue('About_Array_Platform')
				About_Data_Values_Processing=fd.formdata.getvalue('About_Data_Values_Processing')
				Data_Source_Acknowledge=fd.formdata.getvalue('Data_Source_Acknowledge')
				AuthorizedUsers=fd.formdata.getvalue('AuthorizedUsers')
				Progress=fd.formdata.getvalue('Progress')
				if Id=='-1':
						sharingInfoObject = SharingInfo.SharingInfo(GN_AccesionId, InfoPageName)
						info, filelist = sharingInfoObject.getInfo()
						if info:
								heading = "Editing Info"
								detail = ["The new dataset info record is duplicate."]
								self.error(heading=heading, detail=detail, error="Error")
								return
						sql = """INSERT INTO InfoFiles SET GN_AccesionId=%s, GEO_Series=%s, Status=%s, Title=%s, Organism_Id=%s, Organism=%s, Experiment_Type=%s, Summary=%s, Overall_Design=%s, Contributor=%s, Citation=%s, Submission_Date=%s, Contact_Name=%s, Emails=%s, Phone=%s, URL=%s, Organization_Name=%s, Department=%s, Laboratory=%s, Street=%s, City=%s, State=%s, ZIP=%s, Country=%s, Platforms=%s, Samples=%s, Species=%s, Tissue=%s, Normalization=%s, InbredSet=%s, InfoPageName=%s, InfoPageTitle=%s, About_Cases=%s, About_Tissue=%s, About_Download=%s, About_Array_Platform=%s, About_Data_Values_Processing=%s, Data_Source_Acknowledge=%s, AuthorizedUsers=%s, Progreso=%s"""
						cursor.execute(sql, tuple([GN_AccesionId, GEO_Series, Status, Title, Organism_Id, Organism, Experiment_Type, Summary, Overall_Design, Contributor, Citation, Submission_Date, Contact_Name, Emails, Phone, URL, Organization_Name, Department, Laboratory, Street, City, State, ZIP, Country, Platforms, Samples, Species, Tissue, Normalization, InbredSet, InfoPageName, InfoPageTitle, About_Cases, About_Tissue, About_Download, About_Array_Platform, About_Data_Values_Processing, Data_Source_Acknowledge, AuthorizedUsers, Progress]))
						infoupdate="This record has been succesfully added."
				else:
						sql = """UPDATE InfoFiles SET GN_AccesionId=%s, GEO_Series=%s, Status=%s, Title=%s, Organism_Id=%s, Organism=%s, Experiment_Type=%s, Summary=%s, Overall_Design=%s, Contributor=%s, Citation=%s, Submission_Date=%s, Contact_Name=%s, Emails=%s, Phone=%s, URL=%s, Organization_Name=%s, Department=%s, Laboratory=%s, Street=%s, City=%s, State=%s, ZIP=%s, Country=%s, Platforms=%s, Samples=%s, Species=%s, Tissue=%s, Normalization=%s, InbredSet=%s, InfoPageName=%s, InfoPageTitle=%s, About_Cases=%s, About_Tissue=%s, About_Download=%s, About_Array_Platform=%s, About_Data_Values_Processing=%s, Data_Source_Acknowledge=%s, AuthorizedUsers=%s, Progreso=%s WHERE Id=%s"""
						cursor.execute(sql, tuple([GN_AccesionId, GEO_Series, Status, Title, Organism_Id, Organism, Experiment_Type, Summary, Overall_Design, Contributor, Citation, Submission_Date, Contact_Name, Emails, Phone, URL, Organization_Name, Department, Laboratory, Street, City, State, ZIP, Country, Platforms, Samples, Species, Tissue, Normalization, InbredSet, InfoPageName, InfoPageTitle, About_Cases, About_Tissue, About_Download, About_Array_Platform, About_Data_Values_Processing, Data_Source_Acknowledge, AuthorizedUsers, Progress, Id]))
						infoupdate="This record has been succesfully updated."
				sharingInfoObject = SharingInfo.SharingInfo(GN_AccesionId, InfoPageName)
				self.dict['body'] = sharingInfoObject.getBody(infoupdate=infoupdate)