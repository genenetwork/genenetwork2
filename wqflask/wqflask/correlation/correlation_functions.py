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
# Last updated by NL 2011/03/23

from __future__ import absolute_import, print_function, division

import math
import rpy2.robjects
import string

from base.mrna_assay_tissue_data import MrnaAssayTissueData

from flask import Flask, g


#####################################################################################
#Input: primaryValue(list): one list of expression values of one probeSet,
#       targetValue(list): one list of expression values of one probeSet,
#               method(string): indicate correlation method ('pearson' or 'spearman')
#Output: corr_result(list): first item is Correlation Value, second item is tissue number,
#                           third item is PValue
#Function: get correlation value,Tissue quantity ,p value result by using R;
#Note : This function is special case since both primaryValue and targetValue are from
#the same dataset. So the length of these two parameters is the same. They are pairs.
#Also, in the datatable TissueProbeSetData, all Tissue values are loaded based on
#the same tissue order
#####################################################################################

def cal_zero_order_corr_for_tiss (primaryValue=[], targetValue=[], method='pearson'):

    R_primary = rpy2.robjects.FloatVector(list(range(len(primaryValue))))
    N = len(primaryValue)
    for i in range(len(primaryValue)):
        R_primary[i] = primaryValue[i]

    R_target = rpy2.robjects.FloatVector(list(range(len(targetValue))))
    for i in range(len(targetValue)):
        R_target[i]=targetValue[i]

    R_corr_test = rpy2.robjects.r['cor.test']
    if method =='spearman':
        R_result = R_corr_test(R_primary, R_target, method='spearman')
    else:
        R_result = R_corr_test(R_primary, R_target)

    corr_result =[]
    corr_result.append( R_result[3][0])
    corr_result.append( N )
    corr_result.append( R_result[2][0])

    return corr_result


###########################################################################
#Input: cursor, symbolList (list), dataIdDict(Dict)
#output: symbolValuepairDict (dictionary):one dictionary of Symbol and Value Pair,
#        key is symbol, value is one list of expression values of one probeSet;
#function: get one dictionary whose key is gene symbol and value is tissue expression data (list type).
#Attention! All keys are lower case!
###########################################################################
def get_symbol_value_pairs(tissue_data):
    id_list = [tissue_data[symbol.lower()].data_id for item in tissue_data]

    symbol_value_pairs = {}
    value_list=[]

    query = """SELECT value, id
               FROM TissueProbeSetData
               WHERE Id IN {}""".format(create_in_clause(id_list))

    try :
        results = g.db.execute(query).fetchall()
        for result in results:
            value_list.append(result.value)
        symbol_value_pairs[symbol] = value_list
    except:
        symbol_value_pairs[symbol] = None

    return symbol_value_pairs


########################################################################################################
#input: cursor, symbolList (list), dataIdDict(Dict): key is symbol
#output: SymbolValuePairDict(dictionary):one dictionary of Symbol and Value Pair.
#        key is symbol, value is one list of expression values of one probeSet.
#function: wrapper function for getSymbolValuePairDict function
#          build gene symbol list if necessary, cut it into small lists if necessary,
#          then call getSymbolValuePairDict function and merge the results.
########################################################################################################

def get_trait_symbol_and_tissue_values(symbol_list=None):
    tissue_data = MrnaAssayTissueData(gene_symbols=symbol_list)

    if len(tissue_data.gene_symbols):
        return tissue_data.get_symbol_values_pairs()