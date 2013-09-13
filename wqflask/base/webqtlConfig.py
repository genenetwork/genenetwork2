#########################################'
#      Environment Variables - public
#########################################

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


GNROOT = "/home/zas1024/gene/" # Will remove this and dependent items later
SECUREDIR = GNROOT + 'secure/'
COMMON_LIB = GNROOT + 'support/admin'
HTMLPATH = GNROOT + 'web/'
PYLMM_PATH = '/home/zas1024/plink/'
SNP_PATH = '/home/zas1024/snps/' 
IMGDIR = HTMLPATH +'image/'
IMAGESPATH = HTMLPATH + 'images/'
UPLOADPATH = IMAGESPATH + 'upload/'
TMPDIR = '/tmp/'
GENODIR = HTMLPATH + 'genotypes/'
NEWGENODIR = HTMLPATH + 'new_genotypes/'
GENO_ARCHIVE_DIR = GENODIR + 'archive/'
TEXTDIR = HTMLPATH + 'ProbeSetFreeze_DataMatrix/'
CMDLINEDIR = HTMLPATH + 'webqtl/cmdLine/'
ChangableHtmlPath = GNROOT + 'web/'

SITENAME = 'GN'
PORTADDR = "http://50.16.251.170"
BASEHREF = '<base href="http://50.16.251.170/">'
INFOPAGEHREF = '/dbdoc/%s.html'
GLOSSARYFILE = "/glossary.html"
CGIDIR = '/webqtl/' #XZ: The variable name 'CGIDIR' should be changed to 'PYTHONDIR'
SCRIPTFILE = 'main.py'
REFRESHSTR = '<meta http-equiv="refresh" content="5;url=%s' + SCRIPTFILE +'?sid=%s">'
REFRESHDIR = '%s' + SCRIPTFILE +'?sid=%s'
