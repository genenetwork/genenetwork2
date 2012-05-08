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

class GeneralObject:
	"""
	Base class to define an Object.
	a = [Spam(1, 4), Spam(9, 3), Spam(4,6)]
	a.sort(lambda x, y: cmp(x.eggs, y.eggs))
	"""

	def __init__(self, *args, **kw):
		self.contents = list(args)
		for name, value in kw.items():
			setattr(self, name, value)
			
	def __setitem__(self, key, value):
		setattr(self, key, value)
		
	def __getitem__(self, key):
		return getattr(self, key)
		
	def __getattr__(self, key):
		if key in self.__dict__.keys():
			return self.__dict__[key]
		else:
			return eval("self.__dict__.%s" % key)
			
	def __len__(self):
		return len(self.__dict__) - 1
				
	def __str__(self):
		s = ''
		for key in self.__dict__.keys():
			if key != 'contents':
				s += '%s = %s\n' % (key,self.__dict__[key])
		return s
	
	def __repr__(self):
		s = ''
		for key in self.__dict__.keys():
			s += '%s = %s\n' % (key,self.__dict__[key])
		return s
	
	def __cmp__(self,other):
		return len(self.__dict__.keys()).__cmp__(len(other.__dict__.keys()))



