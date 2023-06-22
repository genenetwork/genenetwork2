# '
#      Environment Variables - public
#
# Note: much of this needs to handled by the settings/environment
# scripts. But rather than migrating everything in one go, we'll
# take it a step at a time. First the hard coded paths get replaced
# with those in utility/tools.py
#
#########################################
import os
from flask import Flask
from utility.tools import valid_path, mk_dir, assert_dir, get_setting, assert_writable_dir, flat_files

# Debug Level
# 1 for debug, mod python will reload import each time
DEBUG = 1

# USER privilege
USERDICT = {'guest': 1, 'user': 2, 'admin': 3, 'root': 4}

# Set privileges
SUPER_PRIVILEGES = {'data': 'edit', 'metadata': 'edit', 'admin': 'edit-admins'}
DEFAULT_PRIVILEGES = {'data': 'view', 'metadata': 'view', 'admin': 'not-admin'}

# minimum number of informative strains
KMININFORMATIVE = 5

# Daily download limit from one IP
DAILYMAXIMUM = 1000

# maximum LRS value
MAXLRS = 460.0

# MINIMUM Database public value
PUBLICTHRESH = 0

# Groups to treat as unique when drawing correlation dropdowns (not sure if this logic even makes sense or is necessary)
BXD_GROUP_EXCEPTIONS = ['BXD-Longevity', 'BXD-AE', 'BXD-Heart-Metals', 'BXD-NIA-AD']

# EXTERNAL LINK ADDRESSES
PUBMEDLINK_URL = "http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?cmd=Retrieve&db=PubMed&list_uids=%s&dopt=Abstract"
UCSC_BLAT = 'http://genome.ucsc.edu/cgi-bin/hgBlat?org=%s&db=%s&type=0&sort=0&output=0&userSeq=%s'
UTHSC_BLAT = 'http://ucscbrowser.genenetwork.org/cgi-bin/hgBlat?org=%s&db=%s&type=0&sort=0&output=0&userSeq=%s'
UTHSC_BLAT2 = 'http://ucscbrowserbeta.genenetwork.org/cgi-bin/hgBlat?org=%s&db=%s&type=0&sort=0&output=0&userSeq=%s'
GENOMEBROWSER_URL = "https://genome.ucsc.edu/cgi-bin/hgTracks?db=%s&position=%s"
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
ENSEMBLETRANSCRIPT_URL = "http://useast.ensembl.org/Mus_musculus/Transcript/Idhistory?t=%s"
DBSNP = 'http://ensembl.org/Mus_musculus/Variation/Population?v=%s'
PROTEIN_ATLAS_URL = "http://www.proteinatlas.org/search/%s"
OPEN_TARGETS_URL = "https://genetics.opentargets.org/gene/%s"
UNIPROT_URL = "https://www.uniprot.org/uniprot/%s"
RGD_URL = "https://rgd.mcw.edu/rgdweb/elasticResults.html?term=%s&category=Gene&species=%s"
PHENOGEN_URL = "https://phenogen.org/gene.jsp?speciesCB=Rn&auto=Y&geneTxt=%s&genomeVer=rn7&section=geneEQTL"
RRID_MOUSE_URL = "https://www.jax.org/strain/%s"
RRID_RAT_URL = "https://rgd.mcw.edu/rgdweb/report/strain/main.html?id=%s"

def update_settings(app: Flask) -> Flask:
    # Temporary storage (note that this TMPDIR can be set as an
    # environment variable - use utility.tools.TEMPDIR when you
    # want to reach this base dir
    TEMPDIR = assert_writable_dir(get_setting(app, "TEMPDIR"))

    TMPDIR = assert_writable_dir(mk_dir(TEMPDIR + '/gn2/'))
    app.config["TMPDIR"] = TMPDIR

    app.config["CACHEDIR"] = assert_writable_dir(mk_dir(TMPDIR + '/cache/'))
    # We can no longer write into the git tree:
    app.config["GENERATED_IMAGE_DIR"] = assert_writable_dir(mk_dir(TMPDIR + 'generated/'))
    app.config["GENERATED_TEXT_DIR"] = assert_writable_dir(mk_dir(TMPDIR + 'generated_text/'))

    # Flat file directories
    app.config["GENODIR"] = assert_dir(flat_files(app, 'genotype') + '/')
    # assert_dir(GENODIR+'bimbam') # for gemma

    # JSON genotypes are OBSOLETE
    JSON_GENODIR = flat_files(app, 'genotype/json') + '/'
    app.config["JSON_GENODIR"] = JSON_GENODIR
    if not valid_path(JSON_GENODIR):
        # fall back on old location (move the dir, FIXME)
        app.config["JSON_GENODIR"] = flat_files(app, 'json')


    app.config["TEXTDIR"] = os.path.join(os.environ.get(
        "GNSHARE", "/gnshare/gn/"), "web/ProbeSetFreeze_DataMatrix")
    # Are we using the following...?
    app.config["PORTADDR"] = "http://50.16.251.170"
    app.config["INFOPAGEHREF"] = '/dbdoc/%s.html'
    app.config["CGIDIR"] = '/webqtl/'  # XZ: The variable name 'CGIDIR' should be changed to 'PYTHONDIR'
    return app
