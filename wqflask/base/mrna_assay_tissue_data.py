import collections

from flask import g

from utility import db_tools
from utility import Bunch

from utility.db_tools import escape
from gn3.db_utils import database_connector


from utility.logger import getLogger
logger = getLogger(__name__)


class MrnaAssayTissueData:

    def __init__(self, gene_symbols=None):
        self.gene_symbols = gene_symbols
        if self.gene_symbols == None:
            self.gene_symbols = []

        self.data = collections.defaultdict(Bunch)

        query = '''select t.Symbol, t.GeneId, t.DataId, t.Chr, t.Mb, t.description, t.Probe_Target_Description
                        from (
                        select Symbol, max(Mean) as maxmean
                        from TissueProbeSetXRef
                        where TissueProbeSetFreezeId=1 and '''

        # Note that inner join is necessary in this query to get distinct record in one symbol group
        # with highest mean value
        # Due to the limit size of TissueProbeSetFreezeId table in DB,
        # performance of inner join is acceptable.MrnaAssayTissueData(gene_symbols=symbol_list)
        if len(gene_symbols) == 0:
            query += '''Symbol!='' and Symbol Is Not Null group by Symbol)
                as x inner join TissueProbeSetXRef as t on t.Symbol = x.Symbol
                and t.Mean = x.maxmean;
                    '''
        else:
            in_clause = db_tools.create_in_clause(gene_symbols)

            # ZS: This was in the query, not sure why: http://docs.python.org/2/library/string.html?highlight=lower#string.lower
            query += ''' Symbol in {} group by Symbol)
                as x inner join TissueProbeSetXRef as t on t.Symbol = x.Symbol
                and t.Mean = x.maxmean;
                    '''.format(in_clause)


        # lower_symbols = []
        lower_symbols = {}
        for gene_symbol in gene_symbols:
            # lower_symbols[gene_symbol.lower()] = True
            if gene_symbol != None:
                lower_symbols[gene_symbol.lower()] = True
        results = list(g.db.execute(query).fetchall())
        for result in results:
            symbol = result[0]
            if symbol  is not None and lower_symbols.get(symbol.lower()):

                symbol = symbol.lower()

                self.data[symbol].gene_id = result.GeneId
                self.data[symbol].data_id = result.DataId
                self.data[symbol].chr = result.Chr
                self.data[symbol].mb = result.Mb
                self.data[symbol].description = result.description
                self.data[symbol].probe_target_description = result.Probe_Target_Description

    ###########################################################################
    # Input: cursor, symbolList (list), dataIdDict(Dict)
    # output: symbolValuepairDict (dictionary):one dictionary of Symbol and Value Pair,
    #        key is symbol, value is one list of expression values of one probeSet;
    # function: get one dictionary whose key is gene symbol and value is tissue expression data (list type).
    # Attention! All keys are lower case!
    ###########################################################################

    def get_symbol_values_pairs(self):
        id_list = [self.data[symbol].data_id for symbol in self.data]

        symbol_values_dict = {}

        if len(id_list) > 0:
            query = """SELECT TissueProbeSetXRef.Symbol, TissueProbeSetData.value
                       FROM TissueProbeSetXRef, TissueProbeSetData
                       WHERE TissueProbeSetData.Id IN {} and
                             TissueProbeSetXRef.DataId = TissueProbeSetData.Id""".format(db_tools.create_in_clause(id_list))


            results = g.db.execute(query).fetchall()
            for result in results:
                if result.Symbol.lower() not in symbol_values_dict:
                    symbol_values_dict[result.Symbol.lower()] = [result.value]
                else:
                    symbol_values_dict[result.Symbol.lower()].append(
                        result.value)

        return symbol_values_dict
