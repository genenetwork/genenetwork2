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
import time
import re
import math
from math import *

from base import webqtlConfig

# NL, 07/27/2010. moved from webqtlForm.py
#Dict of Parents and F1 information, In the order of [F1, Mat, Pat]
ParInfo ={
'BXH':['BHF1', 'HBF1',  'C57BL/6J', 'C3H/HeJ'],
'AKXD':['AKF1', 'KAF1', 'AKR/J', 'DBA/2J'],
'BXD':['B6D2F1', 'D2B6F1', 'C57BL/6J', 'DBA/2J'],
'C57BL-6JxC57BL-6NJF2':['', '', 'C57BL/6J', 'C57BL/6NJ'],
'BXD300':['B6D2F1', 'D2B6F1', 'C57BL/6J', 'DBA/2J'],
'B6BTBRF2':['B6BTBRF1', 'BTBRB6F1', 'C57BL/6J', 'BTBRT<+>tf/J'],
'BHHBF2':['B6HF2','HB6F2','C57BL/6J','C3H/HeJ'],
'BHF2':['B6HF2','HB6F2','C57BL/6J','C3H/HeJ'],
'B6D2F2':['B6D2F1', 'D2B6F1', 'C57BL/6J', 'DBA/2J'],
'BDF2-1999':['B6D2F2', 'D2B6F2', 'C57BL/6J', 'DBA/2J'],
'BDF2-2005':['B6D2F1', 'D2B6F1', 'C57BL/6J', 'DBA/2J'],
'CTB6F2':['CTB6F2','B6CTF2','C57BL/6J','Castaneous'],
'CXB':['CBF1', 'BCF1', 'C57BL/6ByJ', 'BALB/cByJ'],
'AXBXA':['ABF1', 'BAF1', 'C57BL/6J', 'A/J'],
'AXB':['ABF1', 'BAF1', 'C57BL/6J', 'A/J'],
'BXA':['BAF1', 'ABF1', 'C57BL/6J', 'A/J'],
'LXS':['LSF1', 'SLF1', 'ISS', 'ILS'],
'HXBBXH':['SHR_BNF1', 'BN_SHRF1', 'BN-Lx/Cub', 'SHR/OlaIpcv'],
'BayXSha':['BayXShaF1', 'ShaXBayF1', 'Bay-0','Shahdara'],
'ColXBur':['ColXBurF1', 'BurXColF1', 'Col-0','Bur-0'],
'ColXCvi':['ColXCviF1', 'CviXColF1', 'Col-0','Cvi'],
'SXM':['SMF1', 'MSF1', 'Steptoe','Morex'],
'HRDP':['SHR_BNF1', 'BN_SHRF1', 'BN-Lx/Cub', 'SHR/OlaIpcv']
}

#########################################
#      Accessory Functions
#########################################

def genRandStr(prefix = "", length=8, chars=string.letters+string.digits):
    from random import choice
    _str = prefix[:]
    for i in range(length):
        _str += choice(chars)
    return _str

def ListNotNull(lst):
    '''Obsolete - Use built in function any (or all or whatever)


    Determine if the elements in a list are all null

    '''
    for item in lst:
        if item is not None:
            return 1
    return None

def readLineCSV(line): ### dcrowell July 2008
    """Parses a CSV string of text and returns a list containing each element as a string.
    Used by correlationPage"""
    returnList = line.split('","')
    returnList[-1]=returnList[-1][:-2]
    returnList[0]=returnList[0][1:]
    return returnList

def cmpEigenValue(A,B):
    try:
        if A[0] > B[0]:
            return -1
        elif A[0] == B[0]:
            return 0
        else:
            return 1
    except:
        return 0

def hasAccessToConfidentialPhenotypeTrait(privilege, userName, authorized_users):
    access_to_confidential_phenotype_trait = 0
    if webqtlConfig.USERDICT[privilege] > webqtlConfig.USERDICT['user']:
        access_to_confidential_phenotype_trait = 1
    else:
        AuthorizedUsersList=map(string.strip, string.split(authorized_users, ','))
        if AuthorizedUsersList.__contains__(userName):
            access_to_confidential_phenotype_trait = 1
    return access_to_confidential_phenotype_trait