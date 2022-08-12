import string

from wqflask.database import database_connection

def load_homology(chr_name, start_mb, end_mb, source_file):
    homology_list = []
    with open(source_file) as h_file:
        current_chr = 0
        for line in h_file:
            line_items = line.split()
            this_dict = {
                "ref_chr": line_items[2][3:],
                "ref_strand": line_items[4],
                "ref_start": float(line_items[5])/1000000,
                "ref_end": float(line_items[6])/1000000,
                "query_chr": line_items[7][3:],
                "query_strand": line_items[9],
                "query_start": float(line_items[10])/1000000,
                "query_end": float(line_items[11])/1000000
            }

            if str(this_dict["ref_chr"]) == str(chr_name) and
                ((this_dict["ref_start"]>= start_mb and this_dict["ref_end"] <= end_mb) or
                    (this_dict["ref_start"] < start_mb and this_dict["ref_end"] <= end_mb) or
                    (this_dict["ref_start"] >= start_mb and this_dict["ref_end"] > end_mb) or
                    (this_dict["ref_start"] < start_mb and this_dict["ref_end"] > end_mb)):
                homology_list.append(this_dict)

    return homology_list

def loadGenes(chrName, diffCol, startMb, endMb, species='mouse'):
    assembly_map = {
        "mouse": "mm10",
        "rat": "rn7"
    }

    def append_assembly(fetch_fields, species):
        query_fields = []
        for field in fetch_fields:
            if field in ['Chr', 'TxStart', 'TxEnd', 'Strand']:
                query_fields.append(field + "_" + assembly_map[species])
            else:
                query_fields.append(field)

        return query_fields


    fetchFields = ['SpeciesId', 'Id', 'GeneSymbol', 'GeneDescription', 'Chr', 'TxStart', 'TxEnd',
                   'Strand', 'GeneID', 'NM_ID', 'kgID', 'GenBankID', 'UnigenID', 'ProteinID', 'AlignID',
                   'exonCount', 'exonStarts', 'exonEnds', 'cdsStart', 'cdsEnd']

    # List All Species in the Gene Table
    speciesDict = {}
    results = []
    with database_connection() as conn, conn.cursor() as cursor:
        cursor.execute("SELECT Species.Name, GeneList081722.SpeciesId "
                       "FROM Species, GeneList081722 WHERE "
                       "GeneList081722.SpeciesId = Species.Id "
                       "GROUP BY GeneList081722.SpeciesId")
        results = cursor.fetchall()
        for item in results:
            if item[0] == "rat":
                speciesDict[item[0]] = (item[1], "rn7")
            else:
                speciesDict[item[0]] = (item[1], "mm10")

        # List current Species and other Species
        speciesId, assembly = speciesDict[species]
        otherSpecies = [[X, speciesDict[X][0], speciesDict[X][1]] for X in list(speciesDict.keys())]
        otherSpecies.remove([species, speciesId, assembly])
        query_fields = append_assembly(fetchFields, species)

        cursor.execute(f"SELECT {', '.join(query_fields)} FROM GeneList081722 "
                       "WHERE SpeciesId = %s AND "
                       f"Chr_{assembly}" + " = %s AND "
                       f"((TxStart_{assembly}" + " > %s and " + f"TxStart_{assembly}" + " <= %s) "
                       f"OR (TxEnd_{assembly}" + " > %s and " + f"TxEnd_{assembly}" + " <= %s)) "
                       f"ORDER BY TxStart_{assembly}",
                       (speciesId, chrName,
                        startMb, endMb,
                        startMb, endMb))
        results = cursor.fetchall()

        GeneList = []
        if results:
            for result in results:
                newdict = {}
                for j, item in enumerate(fetchFields):
                    newdict[item] = result[j]
                # count SNPs if possible
                if diffCol and species == 'mouse':
                    cursor.execute(
                        "SELECT count(*) FROM BXDSnpPosition "
                        "WHERE Chr = %s AND "
                        "Mb >= %s AND Mb < %s "
                        "AND StrainId1 = %s AND StrainId2 = %s",
                    (chrName, f"{newdict['TxStart']:2.6f}",
                     f"{newdict['TxEnd']:2.6f}",
                     diffCol[0], diffCol[1],))
                    newdict["snpCount"] = cursor.fetchone()[0]
                    newdict["snpDensity"] = (
                        newdict["snpCount"] /
                        (newdict["TxEnd"] - newdict["TxStart"]) / 1000.0)
                else:
                    newdict["snpDensity"] = newdict["snpCount"] = 0
                try:
                    newdict['GeneLength'] = 1000.0 * \
                        (newdict['TxEnd'] - newdict['TxStart'])
                except:
                    pass
                # load gene from other Species by the same name
                for item in otherSpecies:
                    othSpec, othSpecId, othSpecAssembly = item
                    newdict2 = {}
                    query_fields = append_assembly(fetchFields, othSpec)
                    cursor.execute(
                        f"SELECT {', '.join(query_fields)} FROM GeneList081722 WHERE "
                        "SpeciesId = %s AND "
                        "geneSymbol= %s LIMIT 1",
                        (othSpecId,
                         newdict["GeneSymbol"]))
                    resultsOther = cursor.fetchone()
                    if resultsOther:
                        for j, item in enumerate(fetchFields):
                            newdict2[item] = resultsOther[j]

                        # count SNPs if possible, could be a separate function
                        if diffCol and othSpec == 'mouse':
                            cursor.execute(
                                "SELECT count(*) FROM BXDSnpPosition "
                                "WHERE Chr = %s AND Mb >= %s AND "
                                "Mb < %s AND StrainId1 = %s "
                                "AND StrainId2 = %s",
                                (chrName, f"{newdict['TxStart']:2.6f}",
                                 f"{newdict['TxEnd']:2.6f}",
                                 diffCol[0], diffCol[1]))
                            if snp_count := cursor.fetchone():
                                newdict2["snpCount"] = snp_count[0]

                            newdict2["snpDensity"] = (
                                newdict2["snpCount"]
                                / (newdict2["TxEnd"] - newdict2["TxStart"])
                                / 1000.0)
                        else:
                            newdict2["snpDensity"] = newdict2["snpCount"] = 0
                        try:
                            newdict2['GeneLength'] = (
                                1000.0 * (newdict2['TxEnd'] - newdict2['TxStart']))
                        except:
                            pass

                    newdict['%sGene' % othSpec] = newdict2

                GeneList.append(newdict)
        return GeneList
