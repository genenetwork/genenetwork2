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

#########################################
#convert Field storage object to Dict object
#in order to be able to saved into a session file
#########################################

class cgiData(dict):
	'''convert Field storage object to Dict object
	   Filed storage object cannot be properly dumped	
	'''

	def __init__(self, field_storage=None):

		if not field_storage:
			field_storage={}
			
		for key in field_storage.keys():
			temp = field_storage.getlist(key)
			if len(temp) > 1:
				temp = map(self.toValue, temp)
			elif len(temp) == 1:
				temp = self.toValue(temp[0])
			else:
				temp = None
			self[key]= temp
	
	def toValue(self, obj):
		'''fieldstorge returns different type of objects, \
			need to convert to string or None'''	
		try:
			return obj.value
		except:
			return ""
	
	def getvalue(self, k, default= None):
		try:
			return self[k]
		except:
			return default

	getfirst = getvalue




