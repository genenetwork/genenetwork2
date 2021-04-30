import string

from flask import Flask, g

# Just return a list of dictionaries
# each dictionary contains sub-dictionary


def loadGenes(chrName, diffCol, startMb, endMb, species='mouse'):
    fetchFields = ['SpeciesId', 'Id', 'GeneSymbol', 'GeneDescription', 'Chromosome', 'TxStart', 'TxEnd',
                   'Strand', 'GeneID', 'NM_ID', 'kgID', 'GenBankID', 'UnigenID', 'ProteinID', 'AlignID',
                   'exonCount', 'exonStarts', 'exonEnds', 'cdsStart', 'cdsEnd']

    # List All Species in the Gene Table
    speciesDict = {}
    results = g.db.execute("""
                SELECT Species.Name, GeneList.SpeciesId
                FROM Species, GeneList
                WHERE GeneList.SpeciesId = Species.Id
                GROUP BY GeneList.SpeciesId""").fetchall()

    for item in results:
        speciesDict[item[0]] = item[1]

    # List current Species and other Species
    speciesId = speciesDict[species]
    otherSpecies = [[X, speciesDict[X]] for X in list(speciesDict.keys())]
    otherSpecies.remove([species, speciesId])

    results = g.db.execute("""
                SELECT %s FROM GeneList
				WHERE SpeciesId = %d AND
                      Chromosome = '%s' AND
					  ((TxStart > %f and TxStart <= %f) OR (TxEnd > %f and TxEnd <= %f))
				ORDER BY txStart
                """ % (", ".join(fetchFields),
                       speciesId, chrName,
                       startMb, endMb,
                       startMb, endMb)).fetchall()

    GeneList = []

    if results:
        for result in results:
            newdict = {}
            for j, item in enumerate(fetchFields):
                newdict[item] = result[j]
            # count SNPs if possible
            if diffCol and species == 'mouse':
                newdict["snpCount"] = g.db.execute("""
                                        SELECT count(*)
                                        FROM BXDSnpPosition
                                        WHERE Chr = '%s' AND
                                              Mb >= %2.6f AND Mb < %2.6f AND
                                              StrainId1 = %d AND StrainId2 = %d
                                        """ % (chrName, newdict["TxStart"], newdict["TxEnd"], diffCol[0], diffCol[1])).fetchone()[0]
                newdict["snpDensity"] = newdict["snpCount"] / \
                    (newdict["TxEnd"] - newdict["TxStart"]) / 1000.0
            else:
                newdict["snpDensity"] = newdict["snpCount"] = 0

            try:
                newdict['GeneLength'] = 1000.0 * (newdict['TxEnd'] - newdict['TxStart'])
            except:
                pass

            # load gene from other Species by the same name
            for item in otherSpecies:
                othSpec, othSpecId = item
                newdict2 = {}

                resultsOther = g.db.execute("SELECT %s FROM GeneList WHERE SpeciesId = %d AND geneSymbol= '%s' LIMIT 1" % (", ".join(fetchFields),
                                                                                                                           othSpecId,
                                                                                                                           newdict["GeneSymbol"])).fetchone()

                if resultsOther:
                    for j, item in enumerate(fetchFields):
                        newdict2[item] = resultsOther[j]

                    # count SNPs if possible, could be a separate function
                    if diffCol and othSpec == 'mouse':
                        newdict2["snpCount"] = g.db.execute("""
                                                    SELECT count(*)
                                                    FROM BXDSnpPosition
                                                    WHERE Chr = '%s' AND
                                                          Mb >= %2.6f AND Mb < %2.6f AND
                                                          StrainId1 = %d AND StrainId2 = %d
                                                    """ % (chrName, newdict["TxStart"], newdict["TxEnd"], diffCol[0], diffCol[1])).fetchone()[0]

                        newdict2["snpDensity"] = newdict2["snpCount"] / \
                            (newdict2["TxEnd"] - newdict2["TxStart"]) / 1000.0
                    else:
                        newdict2["snpDensity"] = newdict2["snpCount"] = 0

                    try:
                        newdict2['GeneLength'] = 1000.0 * \
                            (newdict2['TxEnd'] - newdict2['TxStart'])
                    except:
                        pass

                newdict['%sGene' % othSpec] = newdict2

            GeneList.append(newdict)

    return GeneList
