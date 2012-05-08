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

class webqtlCaseData:
	"""
	one case data in one trait
	"""

	val = None		#Trait Value
	var = None		#Trait Variance
	N   = None		#Number of individuals

	def __init__(self, val=val, var=var, N=N):
		self.val = val
		self.var = var
		self.N = N
	
	def __str__(self):
		str = ""
		if self.val != None:
			str += "value=%2.3f" % self.val
		if self.var != None:
			str += " variance=%2.3f" % self.var
		if self.N != None:
			str += " ndata=%d" % self.N
		return str
	
	__repr__ = __str__



