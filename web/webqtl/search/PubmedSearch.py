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

import re

from dbFunction import webqtlDatabaseFunction

import logging
logging.basicConfig(filename="/tmp/gn_log_leiyan", level=logging.INFO)
_log = logging.getLogger("PubmedSearch")

#########################################
# name=megan inst=washington
#########################################

class PubmedSearch:

		def __init__(self, s, ProbeSetFreezeId):
				cursor = webqtlDatabaseFunction.getCursor()
				if (not cursor):
						return
				self.olds = s
				self.news = s
				sql = "SELECT ProbeSet.Symbol FROM pubmedsearch,ProbeSet,ProbeSetXRef WHERE "
				#
				pattern_name = re.compile('\s*name\s*[:=]((\s*\(.+?\)\s*)|(\s*\S+\s*))', re.I)
				search_name = pattern_name.search(self.news)
				if search_name:
					self.news = self.news.replace(search_name.group(), ' ')
					keywords = search_name.group(1)
					keywords = keywords.strip()
					keywords = keywords.strip('(')
					keywords = keywords.strip(')')
					keywords = keywords.strip()
					keywords = keywords.split()
					for keyword in keywords:
						sql += "(MATCH (pubmedsearch.authorfullname,authorshortname) AGAINST ('%s' IN BOOLEAN MODE)) AND " % keyword
				_log.info("news_1: "+self.news)
				#
				pattern_inst = re.compile('\s*inst\s*[:=]((\s*\(.+?\)\s*)|(\s*\S+\s*))', re.I)
				search_inst = pattern_inst.search(self.news)
				if search_inst:
					self.news = self.news.replace(search_inst.group(), ' ')
					keywords = search_inst.group(1)
					keywords = keywords.strip()
					keywords = keywords.strip('(')
					keywords = keywords.strip(')')
					keywords = keywords.strip()
					keywords = keywords.split()
					for keyword in keywords:
						sql += "(MATCH (pubmedsearch.institute) AGAINST ('%s' IN BOOLEAN MODE)) AND " % keyword
				_log.info("news_2: "+self.news)
				#
				if search_name or search_inst:
					sql += "pubmedsearch.geneid=ProbeSet.GeneId AND "
					sql += "ProbeSet.Id=ProbeSetXRef.ProbeSetId AND "
					sql += "ProbeSetXRef.ProbeSetFreezeId=%d " % ProbeSetFreezeId
					sql += "GROUP BY ProbeSet.Symbol;"
					_log.info("sql: "+sql)
					cursor.execute(sql)
					symbols1 = cursor.fetchall()
					symbols2 = ''
					for symbol in symbols1:
						symbols2 += (symbol[0]+' ')
					self.news = symbols2 + self.news
					_log.info("symbols2: "+symbols2)
				else:
					self.news = self.olds

		def getNewS(self):
				return self.news