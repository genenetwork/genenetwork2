import utilities
import datastructure
import genotypes
import probesets
import calculate

"""
For:    Rob, GeneNetwork
Date:   2014-02-04
Function:
    For BXD group, fetch probesets with given locus (mapping info).

locus="rs3663871"
"""
def bxd_probesets_locus(locus, inbredsetid):
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
    results = probesets.get_normalized_probeset(locus=locus, inbredsetid=inbredsetid)
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

locus='rs3663871'
inbredsetid=1
bxd_probesets_locus(locus=locus, inbredsetid=inbredsetid)
