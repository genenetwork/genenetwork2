import datastructure
import genotypes
import probesets

"""
For:    Ash
Date:   2014-02-05
Function:
    For BXD group, calculate correlations with genotypes and probesets.
Running History:
    2014-02-05  /home/leiyan/gn2/wqflask/maintenance/dataset/datadir/20140205_Ash_correlations/output
"""
def bxd_correlations():
    #
    inbredsetid = 1
    genofile = "/home/leiyan/gn/web/genotypes/BXD.geno"
    outputdir = "/home/leiyan/gn2/wqflask/maintenance/dataset/datadir/20140205_Ash_correlations/output"
    #
    t = genotypes.load_genos(genofile)
    genostrains = t[0]
    genos = t[1]
    #
    probesetfreezes = datastructure.get_probesetfreezes(inbredsetid)
    print "Get %d probesetfreezes" % (len(probesetfreezes))
    #
    for probesetfreeze in probesetfreezes:
        #
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
            probesetid = probesetxref[0]
            probesetdataid = probesetxref[1]
            probeset = probesets.get_probeset(probesetid)
            probesetdata = probesets.get_probesetdata(probesetdataid)
        #
        outputfile.close()
        
bxd_correlations()
