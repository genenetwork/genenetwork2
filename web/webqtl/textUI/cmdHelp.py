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

from base import webqtlConfig
from base.admin import ADMIN_tissue_alias
from cmdClass import cmdClass

#########################################
#      Help Class
#########################################

#XZ, 03/23/2009: There are several issues need attention.
#1. Some probeset datasets are not added into DBList.
#2. Do NOT show confidential datasets. 
#3. Get rid of ADMIN_tissue_alias. We should use info from database instead.

class cmdHelp(cmdClass):
	def __init__(self,fd=None):

		cmdClass.__init__(self,fd)

		if not webqtlConfig.TEXTUI:
			self.contents.append("Please send your request to http://robot.genenetwork.org")
			return


		machineParse = self.data.getvalue('parse')
		topic = self.data.getvalue('topic')
		if topic:
			topic = topic.lower()
			if topic == 'tissue':
				self.contents.append("%s%s|          %s" %("Tissue", ' '*(50-len("Tissue")), "Tissue Abbreviations"))
				self.contents.append("%s%s| %s" %("", ' '*50, "(Separated by space, case insensitive)"))
				self.contents.append("%s|%s" %('_'*50, '_'*40))
			
				keys = ADMIN_tissue_alias.keys()
				keys.sort()
				for key in keys:
					self.contents.append("%s%s|   %s" % (key , ' '*(50-len(key)),  string.join(ADMIN_tissue_alias[key], "  ")))
					self.contents.append("%s|%s" %('_'*50, '_'*40))
			else:	
				pass
		else:
			self.contents = ["#Use database code table below to access data", "#For machine parse friendly output please use",
					     "#http://www.genenetwork.org%s%s?cmd=help&parse=machine" % (webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE)]
			self.cursor.execute("""(SELECT DBType.Name, DBList.FreezeId, DBList.Code, ProbeSetFreeze.CreateTime as Time
						from ProbeSetFreeze, DBType, DBList WHERE DBType.Id = DBList.DBTypeId and 
						DBType.Name = 'ProbeSet' and DBList.FreezeId = ProbeSetFreeze.Id  and 
						ProbeSetFreeze.public > %d order by ProbeSetFreeze.CreateTime ,DBList.Name, DBList.Id) 
						UNION 
						(SELECT DBType.Name, DBList.FreezeId, DBList.Code, PublishFreeze.CreateTime as Time
						from PublishFreeze, DBType, DBList WHERE DBType.Id = DBList.DBTypeId and 
						DBType.Name = 'Publish' and DBList.FreezeId = PublishFreeze.Id order by 
						PublishFreeze.CreateTime ,DBList.Name, DBList.Id) 
						UNION
						(SELECT DBType.Name, DBList.FreezeId, DBList.Code, GenoFreeze.CreateTime 
						from GenoFreeze, DBType, DBList WHERE DBType.Id = DBList.DBTypeId and 
						DBType.Name = 'Geno' and DBList.FreezeId = GenoFreeze.Id order by 
						GenoFreeze.CreateTime ,DBList.Name, DBList.Id)""" % webqtlConfig.PUBLICTHRESH)
			dbs = self.cursor.fetchall()
			if machineParse =="machine":
				pass
			else:
				self.contents.append("\n")
				self.contents.append("%s%s|          %s" %("Database_Name", ' '*(50-len("Database_Name")), "Database_Access_Code_Name"))
				self.contents.append("%s|%s" %('_'*50, '_'*40))
			for dbInfo in dbs:
				self.cursor.execute('SELECT FullName from %sFreeze WHERE Id = %d and public > %d' % (dbInfo[0], dbInfo[1],webqtlConfig.PUBLICTHRESH))
				results = self.cursor.fetchall()
				if not results:
					pass
				else:
					if machineParse =="machine":
						self.contents.append(results[0][0]+ ',' +dbInfo[2])
					else:
						self.contents.append("%s%s|          %s" %(results[0][0], ' '*(50-len(results[0][0])), dbInfo[2]))
						self.contents.append("%s|%s" %('_'*50, '_'*40))
	

			
