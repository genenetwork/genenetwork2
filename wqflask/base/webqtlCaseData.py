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
# This module is used by GeneNetwork project (www.genenetwork.org)
#
# Created by GeneNetwork Core Team 2010/08/10


from utility.logger import getLogger
logger = getLogger(__name__)

import utility.tools

utility.tools.show_settings()

class webqtlCaseData:
    """one case data in one trait"""

    def __init__(self, name, value=None, variance=None, num_cases=None, name2=None):
        self.name = name
        self.name2 = name2                  # Other name (for traits like BXD65a)
        self.value = value                  # Trait Value
        self.variance = variance            # Trait Variance
        self.num_cases = num_cases          # Number of individuals/cases
        self.extra_attributes = None
        self.this_id = None   # Set a sane default (can't be just "id" cause that's a reserved word)
        self.outlier = None   # Not set to True/False until later

    def __repr__(self):
        case_data_string = "<webqtlCaseData> "
        if self.value is not None:
            case_data_string += "value=%2.3f" % self.value
        if self.variance is not None:
            case_data_string += " variance=%2.3f" % self.variance
        if self.num_cases:
            case_data_string += " ndata=%s" % self.num_cases
        if self.name:
            case_data_string += " name=%s" % self.name
        if self.name2:
            case_data_string += " name2=%s" % self.name2
        return case_data_string

    @property
    def class_outlier(self):
        """Template helper"""
        if self.outlier:
            return "outlier"
        return ""

    @property
    def display_value(self):
        if self.value is not None:
            return "%2.3f" % self.value
        return "x"

    @property
    def display_variance(self):
        if self.variance is not None:
            return "%2.3f" % self.variance
        return "x"

    @property
    def display_num_cases(self):
        if self.num_cases is not None:
            return "%s" % self.num_cases
        return "x"