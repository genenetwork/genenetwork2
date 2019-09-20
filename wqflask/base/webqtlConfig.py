#########################################'
#      Environment Variables - public
#
# Note: much of this needs to handled by the settings/environment
# scripts. But rather than migrating everything in one go, we'll
# take it a step at a time. First the hard coded paths get replaced
# with those in utility/tools.py
#
#########################################

from utility.tools import valid_path, mk_dir, assert_dir, assert_writable_dir, flat_files, TEMPDIR

#Debug Level
#1 for debug, mod python will reload import each time
DEBUG = 1

#USER privilege
USERDICT = {'guest':1,'user':2, 'admin':3, 'root':4}

#minimum number of informative strains
KMININFORMATIVE = 5

#Daily download limit from one IP
DAILYMAXIMUM = 1000

#maximum LRS value
MAXLRS = 460.0

#MINIMUM Database public value
PUBLICTHRESH = 0

#EXTERNAL LINK ADDRESSES
PUBMEDLINK_URL = "http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?cmd=Retrieve&db=PubMed&list_uids=%s&dopt=Abstract"
UCSC_BLAT = 'http://genome.ucsc.edu/cgi-bin/hgBlat?org=%s&db=%s&type=0&sort=0&output=0&userSeq=%s'
UTHSC_BLAT = 'http://ucscbrowser.genenetwork.org/cgi-bin/hgBlat?org=%s&db=%s&type=0&sort=0&output=0&userSeq=%s'
UTHSC_BLAT2 = 'http://ucscbrowserbeta.genenetwork.org/cgi-bin/hgBlat?org=%s&db=%s&type=0&sort=0&output=0&userSeq=%s'
GENOMEBROWSER_URL="https://genome.ucsc.edu/cgi-bin/hgTracks?db=%s&position=%s"
NCBI_LOCUSID = "http://www.ncbi.nlm.nih.gov/gene?cmd=Retrieve&dopt=Graphics&list_uids=%s"
GENBANK_ID = "http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?db=Nucleotide&cmd=search&doptcmdl=DocSum&term=%s"
OMIM_ID = "http://www.ncbi.nlm.nih.gov/omim/%s"
UNIGEN_ID = "http://www.ncbi.nlm.nih.gov/UniGene/clust.cgi?ORG=%s&CID=%s"
HOMOLOGENE_ID = "http://www.ncbi.nlm.nih.gov/homologene/?term=%s"
GENOTATION_URL = "http://www.genotation.org/Getd2g.pl?gene_list=%s"
GTEX_URL = "https://www.gtexportal.org/home/gene/%s"
GENEBRIDGE_URL = "https://www.systems-genetics.org/modules_by_gene/%s?organism=%s"
GENEMANIA_URL = "https://genemania.org/search/%s/%s"
UCSC_REFSEQ = "http://genome.cse.ucsc.edu/cgi-bin/hgTracks?db=%s&hgg_gene=%s&hgg_chrom=chr%s&hgg_start=%s&hgg_end=%s"
BIOGPS_URL = "http://biogps.org/?org=%s#goto=genereport&id=%s"
STRING_URL = "http://string-db.org/newstring_cgi/show_network_section.pl?identifier=%s"
PANTHER_URL = "http://www.pantherdb.org/genes/geneList.do?searchType=basic&fieldName=all&organism=all&listType=1&fieldValue=%s"
GEMMA_URL = "http://www.chibi.ubc.ca/Gemma/gene/showGene.html?ncbiid=%s"
ABA_URL = "http://mouse.brain-map.org/search/show?search_type=gene&search_term=%s"
EBIGWAS_URL = "https://www.ebi.ac.uk/gwas/search?query=%s"
WIKI_PI_URL = "http://severus.dbmi.pitt.edu/wiki-pi/index.php/search?q=%s"
ENSEMBLETRANSCRIPT_URL="http://useast.ensembl.org/Mus_musculus/Transcript/Idhistory?t=%s"
DBSNP = 'http://ensembl.org/Mus_musculus/Variation/Population?v=%s'
PROTEIN_ATLAS_URL = "http://www.proteinatlas.org/search/%s"
OPEN_TARGETS_URL = "https://genetics.opentargets.org/gene/%s"

# Temporary storage (note that this TMPDIR can be set as an
# environment variable - use utility.tools.TEMPDIR when you
# want to reach this base dir
assert_writable_dir(TEMPDIR)

TMPDIR               = mk_dir(TEMPDIR+'/gn2/')
assert_writable_dir(TMPDIR)

CACHEDIR             = mk_dir(TMPDIR+'/cache/')
# We can no longer write into the git tree:
GENERATED_IMAGE_DIR  = mk_dir(TMPDIR+'generated/')
GENERATED_TEXT_DIR   = mk_dir(TMPDIR+'generated_text/')

# Make sure we have permissions to access these
assert_writable_dir(CACHEDIR)
assert_writable_dir(GENERATED_IMAGE_DIR)
assert_writable_dir(GENERATED_TEXT_DIR)

# Flat file directories
GENODIR              = flat_files('genotype')+'/'
assert_dir(GENODIR)
assert_dir(GENODIR+'bimbam') # for gemma

# JSON genotypes are OBSOLETE
JSON_GENODIR         = flat_files('genotype/json')+'/'
if not valid_path(JSON_GENODIR):
    # fall back on old location (move the dir, FIXME)
    JSON_GENODIR = flat_files('json')

# Are we using the following...?
PORTADDR = "http://50.16.251.170"
INFOPAGEHREF = '/dbdoc/%s.html'
CGIDIR = '/webqtl/' #XZ: The variable name 'CGIDIR' should be changed to 'PYTHONDIR'
