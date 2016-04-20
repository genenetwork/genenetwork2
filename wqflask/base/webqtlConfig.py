#########################################'
#      Environment Variables - public
#
# Note: much of this needs to handled by the settings/environment
# scripts. But rather than migrating everything in one go, we'll
# take it a step at a time. First the hard coded paths get replaced
# with those in utility/tools.py
# 
#########################################

from utility.tools import mk_dir, assert_dir, flat_files, TEMPDIR

#Debug Level
#1 for debug, mod python will reload import each time
DEBUG = 1

#USER privilege
USERDICT = {'guest':1,'user':2, 'admin':3, 'root':4}

#minimum number of informative strains
KMININFORMATIVE = 5

#maximum number of traits for interval mapping
MULTIPLEMAPPINGLIMIT = 11

#maximum number of traits for correlation
MAXCORR = 100

#Daily download limit from one IP
DAILYMAXIMUM = 1000

#maximum LRS value
MAXLRS = 460.0

#temporary data life span
MAXLIFE = 86400

#MINIMUM Database public value
PUBLICTHRESH = 0

#NBCI address
NCBI_LOCUSID = "http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?db=gene&cmd=Retrieve&dopt=Graphics&list_uids=%s"
UCSC_REFSEQ = "http://genome.cse.ucsc.edu/cgi-bin/hgGene?db=%s&hgg_gene=%s&hgg_chrom=chr%s&hgg_start=%s&hgg_end=%s"
GENBANK_ID = "http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?db=Nucleotide&cmd=search&doptcmdl=DocSum&term=%s"
OMIM_ID = "http://www.ncbi.nlm.nih.gov/omim/%s"
UNIGEN_ID = "http://www.ncbi.nlm.nih.gov/UniGene/clust.cgi?ORG=%s&CID=%s";
HOMOLOGENE_ID = "http://www.ncbi.nlm.nih.gov/sites/entrez?Db=homologene&Cmd=DetailsSearch&Term=%s"
PUBMEDLINK_URL = "http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?cmd=Retrieve&db=PubMed&list_uids=%s&dopt=Abstract"
UCSC_POS = "http://genome.ucsc.edu/cgi-bin/hgTracks?clade=mammal&org=%s&db=%s&position=chr%s:%s-%s&pix=800&Submit=submit"
UCSC_BLAT = 'http://genome.ucsc.edu/cgi-bin/hgBlat?org=%s&db=%s&type=0&sort=0&output=0&userSeq=%s'
UTHSC_BLAT = 'http://ucscbrowser.genenetwork.org/cgi-bin/hgBlat?org=%s&db=%s&type=0&sort=0&output=0&userSeq=%s'
UCSC_GENOME = "http://genome.ucsc.edu/cgi-bin/hgTracks?db=%s&position=chr%s:%d-%d&hgt.customText=http://web2qtl.utmem.edu:88/snp/chr%s"
ENSEMBLE_BLAT = 'http://www.ensembl.org/Mus_musculus/featureview?type=AffyProbe&id=%s'
DBSNP = 'http://www.ncbi.nlm.nih.gov/SNP/snp_ref.cgi?type=rs&rs=%s'
UCSC_RUDI_TRACK_URL = " http://genome.cse.ucsc.edu/cgi-bin/hgTracks?org=%s&db=%s&hgt.customText=http://gbic.biol.rug.nl/~ralberts/tracks/%s/%s"
GENOMEBROWSER_URL="http://ucscbrowser.genenetwork.org/cgi-bin/hgTracks?clade=mammal&org=Mouse&db=mm9&position=%s&hgt.suggest=&pix=800&Submit=submit"
ENSEMBLETRANSCRIPT_URL="http://useast.ensembl.org/Mus_musculus/Lucene/Details?species=Mus_musculus;idx=Transcript;end=1;q=%s"

# HTMLPATH = GNROOT + 'genotype_files/'
# PYLMM_PATH
# IMGDIR = GNROOT + '/wqflask/wqflask/static/output/'

# Temporary storage:
TMPDIR               = mk_dir(TEMPDIR+'/gn2/')
CACHEDIR             = mk_dir(TEMPDIR+'/cache/')
# We can no longer write into the git tree:
GENERATED_IMAGE_DIR  = mk_dir(TMPDIR+'/generate/')
GENERATED_TEXT_DIR   = mk_dir(TMPDIR+'/generate_text/')

# Flat file directories
GENODIR              = flat_files('genotype')+'/'
JSON_GENODIR         = assert_dir(GENODIR+'json/')

# SITENAME = 'GN'
# PORTADDR = "http://50.16.251.170"
# BASEHREF = '<base href="http://50.16.251.170/">'

INFOPAGEHREF = '/dbdoc/%s.html'
CGIDIR = '/webqtl/' #XZ: The variable name 'CGIDIR' should be changed to 'PYTHONDIR'
SCRIPTFILE = 'main.py'

# GLOSSARYFILE = "/glossary.html"
# REFRESHSTR = '<meta http-equiv="refresh" content="5;url=%s' + SCRIPTFILE +'?sid=%s">'
# REFRESHDIR = '%s' + SCRIPTFILE +'?sid=%s'
