import collections

from gn2.utility import Bunch


class MrnaAssayTissueData:

    def __init__(self, conn, gene_symbols=None):
        self.gene_symbols = gene_symbols
        self.conn = conn
        if self.gene_symbols is None:
            self.gene_symbols = []

        self.data = collections.defaultdict(Bunch)
        results = ()
        # Note that inner join is necessary in this query to get
        # distinct record in one symbol group with highest mean value
        # Due to the limit size of TissueProbeSetFreezeId table in DB,
        # performance of inner join is
        # acceptable.MrnaAssayTissueData(gene_symbols=symbol_list)
        with conn.cursor() as cursor:
            if len(self.gene_symbols) == 0:
                cursor.execute(
                    "SELECT t.Symbol, t.GeneId, t.DataId, "
                    "t.Chr, t.Mb, t.description, "
                    "t.Probe_Target_Description FROM (SELECT Symbol, "
                    "max(Mean) AS maxmean "
                    "FROM TissueProbeSetXRef WHERE "
                    "TissueProbeSetFreezeId=1 AND "
                    "Symbol != '' AND Symbol IS NOT "
                    "Null GROUP BY Symbol) "
                    "AS x INNER JOIN "
                    "TissueProbeSetXRef AS t ON "
                    "t.Symbol = x.Symbol "
                    "AND t.Mean = x.maxmean")
            else:
                cursor.execute(
                    "SELECT t.Symbol, t.GeneId, t.DataId, "
                    "t.Chr, t.Mb, t.description, "
                    "t.Probe_Target_Description FROM (SELECT Symbol, "
                    "max(Mean) AS maxmean "
                    "FROM TissueProbeSetXRef WHERE "
                    "TissueProbeSetFreezeId=1 AND "
                    "Symbol IN "
                    f"({', '.join(['%s'] * len(self.gene_symbols))}) "
                    "GROUP BY Symbol) AS x INNER JOIN "
                    "TissueProbeSetXRef AS t ON t.Symbol = x.Symbol "
                    "AND t.Mean = x.maxmean",
                    tuple(self.gene_symbols))
            results = list(cursor.fetchall())
        lower_symbols = {}
        for gene_symbol in self.gene_symbols:
            if gene_symbol is not None:
                lower_symbols[gene_symbol.lower()] = True

        for result in results:
            (symbol, gene_id, data_id, _chr, _mb,
             descr, probeset_target_descr) = result
            if symbol is not None and lower_symbols.get(symbol.lower()):
                symbol = symbol.lower()
                self.data[symbol].gene_id = gene_id
                self.data[symbol].data_id = data_id
                self.data[symbol].chr = _chr
                self.data[symbol].mb = _mb
                self.data[symbol].description = descr
                (self.data[symbol]
                 .probe_target_description) = probeset_target_descr


    def get_symbol_values_pairs(self):
        """Get one dictionary whose key is gene symbol and value is
        tissue expression data (list type).  All keys are lower case.

        The output is a symbolValuepairDict (dictionary): one
        dictionary of Symbol and Value Pair; key is symbol, value is
        one list of expression values of one probeSet;

        """
        id_list = [self.data[symbol].data_id for symbol in self.data]

        symbol_values_dict = {}

        if len(id_list) > 0:
            results = []
            with self.conn.cursor() as cursor:

                cursor.execute(
                    "SELECT TissueProbeSetXRef.Symbol, TissueProbeSetData.value "
                    "FROM TissueProbeSetXRef, TissueProbeSetData"
                    f" WHERE TissueProbeSetData.Id IN ({', '.join(['%s'] * len(id_list))})"
                    " AND TissueProbeSetXRef.DataId = TissueProbeSetData.Id"
                    ,tuple(id_list))

                results = cursor.fetchall()
                for result in results:
                    (symbol, value) = result
                    if symbol.lower() not in symbol_values_dict:
                        symbol_values_dict[symbol.lower()] = [value]
                    else:
                        symbol_values_dict[symbol.lower()].append(
                            value)
        return symbol_values_dict
