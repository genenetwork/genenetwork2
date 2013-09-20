from __future__ import absolute_import, print_function, division

import collections

from flask import g

from utility import db_tools
from utility import Bunch

from MySQLdb import escape_string as escape

from pprint import pformat as pf

class MrnaAssayTissueData(object):
    
    def __init__(self, gene_symbols=None):
        self.gene_symbols = gene_symbols
        self.have_data = False
        if self.gene_symbols == None:
            self.gene_symbols = []
        
        self.data = collections.defaultdict(Bunch)
            
        #self.gene_id_dict ={}
        #self.data_id_dict = {}
        #self.chr_dict = {}
        #self.mb_dict = {}
        #self.desc_dict = {}
        #self.probe_target_desc_dict = {}
        
        query =  '''select t.Symbol, t.GeneId, t.DataId,t.Chr, t.Mb, t.description, t.Probe_Target_Description
                        from (
                        select Symbol, max(Mean) as maxmean
                        from TissueProbeSetXRef
                        where TissueProbeSetFreezeId=1 and '''
        
        # Note that inner join is necessary in this query to get distinct record in one symbol group
        # with highest mean value
        # Due to the limit size of TissueProbeSetFreezeId table in DB,
        # performance of inner join is acceptable.MrnaAssayTissueData(gene_symbols=symbol_list)
        print("len(gene_symbols): ", len(gene_symbols))
        if len(gene_symbols) == 0:
            query +=  '''Symbol!='' and Symbol Is Not Null group by Symbol)
                as x inner join TissueProbeSetXRef as t on t.Symbol = x.Symbol
                and t.Mean = x.maxmean;  
                    '''
        else:
            in_clause = db_tools.create_in_clause(gene_symbols)
            
            query += ''' Symbol in {} group by Symbol)
                as x inner join TissueProbeSetXRef as t on t.Symbol = x.Symbol
                and t.Mean = x.maxmean;
                    '''.format(in_clause)

        results = g.db.execute(query).fetchall()
        for result in results:
            symbol = result[0]
            if symbol in gene_symbols:
            #gene_symbols.append(symbol)
                symbol = symbol.lower()
                
                self.data[symbol].gene_id = result.GeneId
                self.data[symbol].data_id = result.DataId
                self.data[symbol].chr = result.Chr
                self.data[symbol].mb = result.Mb
                self.data[symbol].description = result.description
                self.data[symbol].probe_target_description = result.Probe_Target_Description

        #print("self.data: ", pf(self.data))

    ###########################################################################
    #Input: cursor, symbolList (list), dataIdDict(Dict)
    #output: symbolValuepairDict (dictionary):one dictionary of Symbol and Value Pair,
    #        key is symbol, value is one list of expression values of one probeSet;
    #function: get one dictionary whose key is gene symbol and value is tissue expression data (list type).
    #Attention! All keys are lower case!
    ###########################################################################
    
    def get_symbol_values_pairs(self):
        id_list = [self.data[symbol].data_id for symbol in self.data]

        symbol_values_dict = {}
        
        query = """SELECT TissueProbeSetXRef.Symbol, TissueProbeSetData.value
                   FROM TissueProbeSetXRef, TissueProbeSetData
                   WHERE TissueProbeSetData.Id IN {} and
                         TissueProbeSetXRef.DataId = TissueProbeSetData.Id""".format(db_tools.create_in_clause(id_list))
        
        results = g.db.execute(query).fetchall()
        for result in results:
            if result.Symbol.lower() not in symbol_values_dict:
                symbol_values_dict[result.Symbol.lower()] = [result.value]
            else:
                symbol_values_dict[result.Symbol.lower()].append(result.value)

        #for symbol in self.data:
        #    data_id = self.data[symbol].data_id
        #    symbol_values_dict[symbol] = self.get_tissue_values(data_id)
        
    
        return symbol_values_dict
    
    
    #def get_tissue_values(self, data_id):
    #    """Gets the tissue values for a particular gene"""
    #
    #    tissue_values=[]
    #
    #    query = """SELECT value, id
    #               FROM TissueProbeSetData
    #               WHERE Id IN {}""".format(db_tools.create_in_clause(data_id))
    #
    #    #try :
    #    results = g.db.execute(query).fetchall()
    #    for result in results:
    #        tissue_values.append(result.value)
    #    #symbol_values_dict[symbol] = value_list
    #    #except:
    #    #    symbol_values_pairs[symbol] = None
    #
    #    return tissue_values
    
########################################################################################################
#input: cursor, symbolList (list), dataIdDict(Dict): key is symbol
#output: SymbolValuePairDict(dictionary):one dictionary of Symbol and Value Pair.
#        key is symbol, value is one list of expression values of one probeSet.
#function: wrapper function for getSymbolValuePairDict function
#          build gene symbol list if necessary, cut it into small lists if necessary,
#          then call getSymbolValuePairDict function and merge the results.
########################################################################################################

#def get_trait_symbol_and_tissue_values(symbol_list=None):
#    tissue_data = MrnaAssayTissueData(gene_symbols=symbol_list)
#
#    #symbolList,
#    #geneIdDict,
#    #dataIdDict,
#    #ChrDict,
#    #MbDict,
#    #descDict,
#    #pTargetDescDict = getTissueProbeSetXRefInfo(
#    #                    GeneNameLst=GeneNameLst,TissueProbeSetFreezeId=TissueProbeSetFreezeId)
#    
#    if len(tissue_data.gene_symbols):
#        return get_symbol_values_pairs(tissue_data)
            
