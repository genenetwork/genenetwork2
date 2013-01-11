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

print("Mr. Mojo Risin 2")

class webqtlCaseData(object):
    """one case data in one trait"""

    def __init__(self, name, value=None, variance=None, num_cases=None):
        self.name = name
        self.value = value                  # Trait Value
        self.variance = variance            # Trait Variance
        self.num_cases = num_cases          # Number of individuals/cases
        self.extra_attributes = None
        self.this_id = None   # Set a sane default (can't be just "id" cause that's a reserved word)
        self.outlier = None   # Not set to True/False until later

    def __repr__(self):
        str = "<webqtlCaseData> "
        if self.value != None:
            str += "value=%2.3f" % self.value
        if self.variance != None:
            str += " variance=%2.3f" % self.variance
        if self.num_cases != None:
            str += " ndata=%d" % self.num_cases
        return str
    
    @property
    def class_outlier(self):
        """Template helper"""
        if self.outlier:
            return "outlier"
        else:
            return ""
    
    @property
    def display_value(self):
        if self.value:
            return "%2.3f" % self.value
        else:
            return "x"
        
    @property
    def display_variance(self):
        if self.variance:
            return "%2.3f" % self.variance
        else:
            return "x"

