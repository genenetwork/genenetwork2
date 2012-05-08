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

# ProcessedPoint: to store information about the relationship between
# two particular traits
# ProcessedPoint represents the calculations made by the program

class ProcessedPoint:

    def __init__(self, i, j):
        self.i = i
        self.j = j

    def __eq__(self, other):
        # print "ProcessedPoint: comparing %s and %s" % (self, other)
        return (self.i == other.i and
                self.j == other.j and
                self.value == other.value and
                self.color == other.color)

    def __str__(self):
        return "(%s,%s,%s,%s,%s)" % (self.i, 
                                     self.j, 
                                     self.value,
                                     self.length,
                                     self.color)
