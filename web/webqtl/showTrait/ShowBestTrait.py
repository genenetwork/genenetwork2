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

#from base.templatePage import templatePage
#from basicStatistics.BasicStatisticsPage import BasicStatisticsPage
from htmlgen import HTMLgen2 as HT

from base import webqtlConfig
from utility import webqtlUtil
from base.webqtlTrait import webqtlTrait
from base.templatePage import templatePage
from DataEditingPage import DataEditingPage


#class ShowBestTrait(BasicStatisticsPage, templatePage):

class ShowBestTrait(DataEditingPage):
	def __init__(self,fd):

		########## geneName means symbol ##########
		geneName = fd.formdata.getvalue('gene')
		if geneName:
			geneName = string.strip(geneName)

		refseq = fd.formdata.getvalue('refseq')
		if refseq:
			refseq = string.strip(refseq)

		genbankid = fd.formdata.getvalue('genbankid')
		if genbankid:
			genbankid = string.strip(genbankid)

		geneid = fd.formdata.getvalue('geneid')
		if geneid:
			geneid = string.strip(geneid)

		species = fd.formdata.getvalue('species')
		tissue = fd.formdata.getvalue('tissue')
		database = fd.formdata.getvalue('database')

		########## searchAlias is just a singal, so it doesn't need be stripped ##########
		searchAlias = fd.formdata.getvalue('searchAlias')

		if not self.openMysql():
			return

		if database:
			if geneName:
				if searchAlias:
					self.cursor.execute(""" SELECT ProbeSetXRef.*
								FROM
									ProbeSet, ProbeSetXRef, DBList
								WHERE
									ProbeSetXRef.ProbeSetFreezeId = DBList.FreezeId AND
									ProbeSetXRef.ProbeSetId = ProbeSet.Id AND
									(DBList.Name=%s or DBList.Code=%s) AND
									MATCH (ProbeSet.symbol, alias) AGAINST ("+%s" IN BOOLEAN MODE)
								ORDER BY ProbeSetXRef.mean DESC
							    """ , (database, database, geneName))
				else:
					self.cursor.execute(""" SELECT ProbeSetXRef.*
								FROM    
									ProbeSet, ProbeSetXRef, DBList
								WHERE   
									ProbeSetXRef.ProbeSetFreezeId = DBList.FreezeId AND
									ProbeSetXRef.ProbeSetId = ProbeSet.Id AND
									(DBList.Name=%s or DBList.Code=%s) AND
									ProbeSet.symbol = %s
								ORDER BY ProbeSetXRef.mean DESC
							    """ , (database, database, geneName))
			elif refseq:
				self.cursor.execute(""" SELECT ProbeSetXRef.*
							FROM
								ProbeSet, ProbeSetXRef, DBList
							WHERE
								ProbeSetXRef.ProbeSetFreezeId = DBList.FreezeId AND
								ProbeSetXRef.ProbeSetId = ProbeSet.Id AND
								(DBList.Name=%s or DBList.Code=%s) AND
								ProbeSet.RefSeq_TranscriptId = %s
							ORDER BY ProbeSetXRef.mean DESC
						    """ , (database, database, refseq))
			elif genbankid:
				self.cursor.execute(""" SELECT ProbeSetXRef.*
							FROM
								ProbeSet, ProbeSetXRef, DBList
							WHERE
								ProbeSetXRef.ProbeSetFreezeId = DBList.FreezeId AND
								ProbeSetXRef.ProbeSetId = ProbeSet.Id AND
								(DBList.Name=%s or DBList.Code=%s) AND
								ProbeSet.GenbankId = %s
							ORDER BY ProbeSetXRef.mean DESC
						    """ , (database, database, genbankid))
			elif geneid:
				self.cursor.execute(""" SELECT ProbeSetXRef.*
							FROM
								ProbeSet, ProbeSetXRef, DBList
							WHERE
								ProbeSetXRef.ProbeSetFreezeId = DBList.FreezeId AND
								ProbeSetXRef.ProbeSetId = ProbeSet.Id AND
								(DBList.Name=%s or DBList.Code=%s) AND
								ProbeSet.GeneId = %s
							ORDER BY ProbeSetXRef.mean DESC
						    """ , (database, database, geneid))

			Results = self.cursor.fetchone()



			########## select the Data that match the selection(currently, only max mean available) ##########
			if Results:
				ProbeSetFreezeId = Results[0]
				ProbeSetId = Results[1]
				DataId = Results[2]

				self.cursor.execute("""
					select
						InbredSet.Name
					from
						InbredSet, ProbeFreeze, ProbeSetFreeze
					where
						InbredSet.Id=ProbeFreeze.InbredSetId and
						ProbeFreeze.Id=ProbeSetFreeze.ProbeFreezeId and
						ProbeSetFreeze.Id=%s
					""", ProbeSetFreezeId)
				fd.RISet = self.cursor.fetchone()[0]
				#fd.RISet = Results[0]

				self.cursor.execute("select Name, FullName from ProbeSetFreeze where Id=%s", ProbeSetFreezeId)
				fd.database, fd.identification = self.cursor.fetchone()

				self.cursor.execute("select Name, symbol, description from ProbeSet where Id=%s", ProbeSetId)
				fd.ProbeSetID, fd.symbol, fd.description = self.cursor.fetchone()

				fd.identification += ' : '+fd.ProbeSetID
				fd.formdata['fullname'] = fd.database+'::'+fd.ProbeSetID

				#XZ, 03/03/2009: Xiaodong changed Data to ProbeSetData	
				self.cursor.execute("select Strain.Name, ProbeSetData.Value from Strain, ProbeSetData where Strain.Id=ProbeSetData.StrainId and ProbeSetData.Id=%s", DataId)
				Results = self.cursor.fetchall()

				fd.allstrainlist = []
				for item in Results:
					fd.formdata[item[0]] = item[1]
					fd.allstrainlist.append(item[0])

				#XZ, 03/12/2009: Xiaodong changed SE to ProbeSetSE
				self.cursor.execute("select Strain.Name, ProbeSetSE.error from Strain, ProbeSetSE where Strain.Id = ProbeSetSE.StrainId and ProbeSetSE.DataId=%s", DataId)
				Results = self.cursor.fetchall()
				for item in Results:
					fd.formdata['V'+item[0]] = item[1]
			else:
				fd.RISet = 'BXD'
				fd.database = 'KI_2A_0405_Rz'
				fd.ProbeSetID = '1367452_at'
		else:
			fd.RISet = 'BXD'
			fd.database = 'KI_2A_0405_Rz'
			fd.ProbeSetID = '1367452_at'


		#BasicStatisticsPage.__init__(self, fd)


		thisTrait = webqtlTrait(db=fd.database, name=fd.ProbeSetID, cursor=self.cursor)
		thisTrait.retrieveInfo()
		thisTrait.retrieveData()
		DataEditingPage.__init__(self, fd, thisTrait)
		self.dict['title'] = '%s: Display Trait' % fd.identification


