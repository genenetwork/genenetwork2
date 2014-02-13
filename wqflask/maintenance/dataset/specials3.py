import utilities
import datastructure
import genotypes
import probesets
import calculate

def correlations(outputdir, genos, probesetfreeze):
    print probesetfreeze
    probesetfreezeid = probesetfreeze[0]
    probesetfreezename = probesetfreeze[1]
    probesetfreezefullname = probesetfreeze[2]
    #
    outputfile = open("%s/%d_%s.txt" % (outputdir, probesetfreezeid, probesetfreezename), "w+")
    outputfile.write("%s\t" % "ProbeSet Id")
    outputfile.write("%s\t" % "ProbeSet Name")
    outputfile.write("%s\t" % "Geno Name")
    outputfile.write("%s\t" % "Overlap Number")
    outputfile.write("%s\t" % "Pearson r")
    outputfile.write("%s\t" % "Pearson p")
    outputfile.write("%s\t" % "Spearman r")
    outputfile.write("%s\t" % "Spearman p")
    outputfile.write("\n")
    outputfile.flush()
    #
    probesetxrefs = probesets.get_probesetxref(probesetfreezeid)
    print "Get %d probesetxrefs" % (len(probesetxrefs))
    #
    for probesetxref in probesetxrefs:
        #
        probesetid = probesetxref[0]
        probesetdataid = probesetxref[1]
        probeset = probesets.get_probeset(probesetid)
        probesetname = probeset[1]
        probesetdata = probesets.get_probesetdata(probesetdataid)
        probesetdata = zip(*probesetdata)
        probesetdata = utilities.to_dic([strain.lower() for strain in probesetdata[1]], probesetdata[2])
        #
        for geno in genos:
            genoname = geno['locus']
            outputfile.write("%s\t" % probesetid)
            outputfile.write("%s\t" % probesetname)
            outputfile.write("%s\t" % genoname)
            #
            dic1 = geno['dicvalues']
            dic2 = probesetdata
            keys, values1, values2 = utilities.overlap(dic1, dic2)
            rs = calculate.correlation(values1, values2)
            #
            outputfile.write("%s\t" % len(keys))
            outputfile.write("%s\t" % rs[0][0])
            outputfile.write("%s\t" % rs[0][1])
            outputfile.write("%s\t" % rs[1][0])
            outputfile.write("%s\t" % rs[1][1])
            outputfile.write("\n")
            outputfile.flush()
    #
    outputfile.close()
    
"""
For:    Ash
Date:   2014-02-12
Function:
    Generate probeset data files.
    given probesetfreeze list.
"""
def generate_probesets(probesetfreezesfile, outputdir):
    file = open(probesetfreezesfile, 'r')
    for line in file:
        line = line.strip()
        cells = line.split()
        probesetfreezeid = cells[0]
        probesetfreeze = datastructure.get_probesetfreeze(probesetfreezeid)
        probesetfreezeid = probesetfreeze[0]
        probesetfreezename = probesetfreeze[1]
        inbredset = datastructure.get_inbredset(probesetfreezeid)
        inbredsetid = inbredset[0]
        strains = datastructure.get_strains(inbredsetid)
        #
        outputfile = open("%s/%d_%s.txt" % (outputdir, probesetfreezeid, probesetfreezename), "w+")
        outputfile.write("%s\t" % "ProbeSet Id")
        outputfile.write("%s\t" % "ProbeSet Name")
        outputfile.write("\n")
        outputfile.flush()
        #
        probesetxrefs = probesets.get_probesetxref(probesetfreezeid)
        print probesetfreeze
        print len(probesetxrefs)
        for probesetxref in probesetxrefs:
            pass
        #
        probesetid = probesetxref[0]
        probesetdataid = probesetxref[1]
        probeset = probesets.get_probeset(probesetid)
        probesetname = probeset[1]
        probesetdata = probesets.get_probesetdata(probesetdataid)
        probesetdata = zip(*probesetdata)
        probesetdata = utilities.to_dic([strain.lower() for strain in probesetdata[1]], probesetdata[2])
        #
        outputfile.close()
    file.close()

probesetfreezesfile = "/home/leiyan/gn2/wqflask/maintenance/dataset/datadir/20140205_Ash_correlations/output2/probesetfreezes_filter.txt"
outputdir           = "/home/leiyan/gn2/wqflask/maintenance/dataset/datadir/20140205_Ash_correlations/output2"
generate_probesets(probesetfreezesfile, outputdir)
