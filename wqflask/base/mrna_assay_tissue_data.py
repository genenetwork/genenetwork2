from __future__ import absolute_import, print_function, division

import collections

from flask import g

from utility import db_tools
from utility import Bunch

from MySQLdb import escape_string as escape

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
        # performance of inner join is acceptable.
        if len(gene_symbols) == 0:
            query +=  '''Symbol!='' and Symbol Is Not Null group by Symbol)
                as x inner join TissueProbeSetXRef as t on t.Symbol = x.Symbol
                and t.Mean = x.maxmean;  
                    '''
        else:
            in_clause = dbtools.create_in_clause(gene_symbols)
            
            query += ''' Symbol in {} group by Symbol)
                as x inner join TissueProbeSetXRef as t on t.Symbol = x.Symbol
                and t.Mean = x.maxmean;
                    '''.format(in_clause)

        results = g.db.execute(query).fetchall()
        for result in results:
            symbol = item[0]
            gene_symbols.append(symbol)
            symbol = symbol.lower()
            
            self.data[symbol].gene_id = result.GeneId
            self.data[symbol].data_id = result.DataId
            self.data[symbol].chr = result.Chr
            self.data[symbol].mb = result.Mb
            self.data[symbol].description = result.description
            self.data[symbol].probe_target_description = result.Probe_Target_Description


    ###########################################################################
    #Input: cursor, symbolList (list), dataIdDict(Dict)
    #output: symbolValuepairDict (dictionary):one dictionary of Symbol and Value Pair,
    #        key is symbol, value is one list of expression values of one probeSet;
    #function: get one dictionary whose key is gene symbol and value is tissue expression data (list type).
    #Attention! All keys are lower case!
    ###########################################################################
    def get_symbol_value_pairs(self):
        
        id_list = [self.tissue_data[symbol.lower()].data_id for item in self.tissue_data]
    
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
    
        #for symbol in symbol_list:
        #    if tissue_data.has_key(symbol):
        #        data_id = tissue_data[symbol].data_id
        #
        #        query = """select value, id
        #                   from TissueProbeSetData
        #                   where Id={}""".format(escape(data_id))
        #        try :
        #            results = g.db.execute(query).fetchall()
        #            for item in results:
        #                item = item[0]
        #                value_list.append(item)
        #            symbol_value_pairs[symbol] = value_list
        #            value_list=[]
        #        except:
        #            symbol_value_pairs[symbol] = None
    
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
    
        #symbolList,
        #geneIdDict,
        #dataIdDict,
        #ChrDict,
        #MbDict,
        #descDict,
        #pTargetDescDict = getTissueProbeSetXRefInfo(
        #                    GeneNameLst=GeneNameLst,TissueProbeSetFreezeId=TissueProbeSetFreezeId)
        
        if len(tissue_data.gene_symbols):
            return get_symbol_value_pairs(tissue_data)
            
