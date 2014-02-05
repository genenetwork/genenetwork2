import datastructure
import genotypes
import probesets

"""
For:    Rob, GeneNetwork
Date:   2014-02-04
Function:
    For BXD group, fetch probesets with given locus.

locus="rs3663871"
"""
def bxd_probesets_locus(locus):
    #
    inbredsetid=1
    #
    file = open('probesets_%s.txt' % (locus), 'w+')
    file.write("GN Dataset ID\t")
    file.write("Dataset Full Name\t")
    file.write("ProbeSet Name\t")
    file.write("Symbol\t")
    file.write("ProbeSet Description\t")
    file.write("Probe Target Description\t")
    file.write("ProbeSet Chr\t")
    file.write("ProbeSet Mb\t")
    file.write("Mean\t")
    file.write("LRS\t")
    file.write("Geno Chr\t")
    file.write("Geno Mb\t")
    file.write("\n")
    file.flush()
    #
    results = get_normalized_probeset(locus=locus, inbredsetid=inbredsetid)
    for row in results:
        file.write("%s\t" % (row[0]))
        file.write("%s\t" % (utilities.clearspaces(row[2], default='')))
        file.write("%s\t" % (utilities.clearspaces(row[3], default='')))
        file.write("%s\t" % (utilities.clearspaces(row[4], default='')))
        file.write("%s\t" % (utilities.clearspaces(row[5], default='')))
        file.write("%s\t" % (utilities.clearspaces(row[6], default='')))
        file.write("%s\t" % (utilities.clearspaces(row[7], default='')))
        file.write("%s\t" % (row[8]))
        file.write("%s\t" % (row[9]))
        file.write("%s\t" % (row[10]))
        file.write("%s\t" % (utilities.clearspaces(row[11], default='')))
        file.write("%s\t" % (row[12]))
        file.write('\n')
        file.flush()
    file.close()

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
    print "Get %d genos" % (len(genos))
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
            #
            probesetid = probesetxref[0]
            probesetdataid = probesetxref[1]
            probeset = probesets.get_probeset(probesetid)
            probesetname = probeset[1]
            probesetdata = probesets.get_probesetdata(probesetdataid)
            #
            for geno in genos:
                genoname = geno['locus']
                outputfile.write("%s\t" % probesetid)
                outputfile.write("%s\t" % probesetname)
                outputfile.write("%s\t" % genoname)
                outputfile.write("%s\t" % "Overlap Number")
                outputfile.write("%s\t" % "Pearson r")
                outputfile.write("%s\t" % "Pearson p")
                outputfile.write("%s\t" % "Spearman r")
                outputfile.write("%s\t" % "Spearman p")
                outputfile.write("\n")
                outputfile.flush()
        #
        outputfile.close()
        
bxd_correlations()
