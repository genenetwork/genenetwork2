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

#--Only imported by correlationPage.py.
#
#Functions:
#slink(lists) -- the only function called outside of this file.
#nearest(lists,i,j) -- some sort of recursive function.
#printarray(array,n) -- prints n elements of the given array
#this is a myseterious piece of code in GN that Kev Adler and Rob Williams do not understand.
#but is used in some way by the Traits Correlation function
#Kev and Rob suspect that the d2 matrix below is unused 
#We do not understand the signifance of "d" but Kev suspects it is unimportant
#These comments by Kev and Rob: May 23, 2008

d = [[0,9,3,6,11],[9,0,7,5,10],[3,7,0,9,2],[6,5,9,0,8],[11,10,2,8,0]]
d2 = [[0,9,5.5,6,11],[9,0,7,5,10],[5.5,7,0,9,2],[6,5,9,0,3],[11,10,2,3,0]]

def nearest(lists,i,j):
	if type(i) == type(1) and type(j) == type(1):
		return lists[i][j]
	elif type(i) == type(1):
		dist = 1e10
		for itemj in j[:-1]:
			d = nearest(lists,i,itemj)
			if dist > d:
				dist = d
	elif type(j) == type(1):
		dist = 1e10
		for itemi in i[:-1]:
			d = nearest(lists,itemi,j)
			if dist > d:
				dist = d
	else:
		dist = 1e10
		for itemi in i[:-1]:
			for itemj in j[:-1]:
				d = nearest(lists,itemi,itemj)
				if dist > d:
					dist = d
	return dist

def printarray(array,n):
	print "\n"
	for i in range(n):
		print array[i][:n]
	print "\n"

def slink(lists):
	try:
		if type(lists) != type([]) and type(lists) != type(()):
			raise 'FormatError'
		else:
			size = len(lists)
			for item in lists:
				if type(item) != type([]) and type(item) != type(()):
					raise 'FormatError'
				else:
					if len(item) != size:
						raise 'LengthError'
			for i in range(size):
				if lists[i][i] != 0:
					raise 'ValueError'
				for j in range(0,i):
					if lists[i][j] < 0:
						raise 'ValueError'
					if lists[i][j] != lists[j][i]:
						raise 'MirrorError'
	except 'FormatError':
		print "the format of the list is incorrect!"
		return []
	except 'LengthError':
		print "the list is not a square list!"
		return []
	except 'MirrorError':
		print "the list is not symmetric!"
		return []
	except 'ValueError':
		print "the distance is negative value!"
		return []
	except:
		print "Unknown Error"
		return [] 
	listindex = range(size)
	listindexcopy = range(size) 
	listscopy = []
	for i in range(size):
		listscopy.append(lists[i][:])
	initSize = size
	candidate = []
	while initSize >2:
		mindist = 1e10
		for i in range(initSize):
			for j in range(i+1,initSize):
				if listscopy[i][j] < mindist:
					mindist =  listscopy[i][j]
					candidate=[[i,j]]
				elif listscopy[i][j] == mindist:
					mindist =  listscopy[i][j]
					candidate.append([i,j])
				else:
					pass
		newmem = (listindexcopy[candidate[0][0]],listindexcopy[candidate[0][1]],mindist)
		listindexcopy.pop(candidate[0][1])
		listindexcopy[candidate[0][0]] = newmem
		
		initSize -= 1
		for i in range(initSize):
			for j in range(i+1,initSize):
				listscopy[i][j] = nearest(lists,listindexcopy[i],listindexcopy[j])
				listscopy[j][i] = listscopy[i][j]
		#print listindexcopy
		#printarray(listscopy,initSize)
	listindexcopy.append(nearest(lists,listindexcopy[0],listindexcopy[1]))
	return listindexcopy
	
	
	
