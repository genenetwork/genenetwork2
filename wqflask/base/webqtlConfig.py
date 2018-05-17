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
SCRIPTFILE = 'main.py'
