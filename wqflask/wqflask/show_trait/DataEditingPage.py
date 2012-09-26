from __future__ import absolute_import, print_function, division

import string
import os
import cPickle
from collections import OrderedDict
#import pyXLWriter as xl

import yaml

from htmlgen import HTMLgen2 as HT

from base import webqtlConfig
from base import webqtlCaseData
from utility import webqtlUtil, Plot, Bunch
from base.webqtlTrait import webqtlTrait
from dbFunction import webqtlDatabaseFunction
from base.templatePage import templatePage
from basicStatistics import BasicStatisticsFunctions

from pprint import pformat as pf

class DataEditingPage(templatePage):

    def __init__(self, fd, this_trait=None):

        templatePage.__init__(self, fd)
        assert self.openMysql(), "No datbase!"
        
        if not fd.genotype:
            fd.readData(incf1=1)

        # determine data editing page format
        variance_data_page = 0
        if fd.formID == 'varianceChoice':
            variance_data_page = 1

        if variance_data_page:
            fmID='dataEditing'
        else:
            if fd.enablevariance:
                fmID='pre_dataEditing'
            else:
                fmID='dataEditing'


        # Some fields, like method, are defaulted to None; otherwise in IE the field can't be changed using jquery
        hddn = OrderedDict(
                FormID = fmID,
                RISet = fd.RISet,
                submitID = '',
                scale = 'physic',
                additiveCheck = 'ON',
                showSNP = 'ON',
                showGenes = 'ON',
                method = None,
                parentsf14regression = 'OFF',
                stats_method = '1',
                chromosomes = '-1',
                topten = '',
                viewLegend = 'ON',
                intervalAnalystCheck = 'ON',
                valsHidden = 'OFF',
                database = '',
                criteria = None,
                MDPChoice = None,
                bootCheck = None,
                permCheck = None,
                applyVarianceSE = None,
                sampleNames = '_',
                sampleVals = '_',
                sampleVars = '_',
                otherStrainNames = '_',
                otherStrainVals = '_',
                otherStrainVars = '_',
                extra_attributes = '_',
                other_extra_attributes = '_'
                )

        if fd.enablevariance:
            hddn['enablevariance']='ON'
        if fd.incparentsf1:
            hddn['incparentsf1']='ON'

        if this_trait:
            hddn['fullname'] = str(this_trait)
            try:
                hddn['normalPlotTitle'] = this_trait.symbol
                hddn['normalPlotTitle'] += ": "
                hddn['normalPlotTitle'] += this_trait.name
            except:
                hddn['normalPlotTitle'] = str(this_trait.name)
            hddn['fromDataEditingPage'] = 1
            if this_trait.db and this_trait.db.type and this_trait.db.type == 'ProbeSet':
                hddn['trait_type'] = this_trait.db.type
                if this_trait.cellid:
                    hddn['cellid'] = this_trait.cellid
                else:
                    self.cursor.execute("SELECT h2 from ProbeSetXRef WHERE DataId = %d" %
                                        this_trait.mysqlid)
                    heritability = self.cursor.fetchone()
                    hddn['heritability'] = heritability

                hddn['attribute_names'] = ""

        hddn['mappingMethodId'] = webqtlDatabaseFunction.getMappingMethod (cursor=self.cursor,
                                                                           groupName=fd.RISet)

        if fd.identification:
            hddn['identification'] = fd.identification
        else:
            hddn['identification'] = "Un-named trait"  #If no identification, set identification to un-named

        self.dispTraitInformation(fd, "", hddn, this_trait) #Display trait information + function buttons

        if this_trait == None:
            this_trait = webqtlTrait(data=fd.allTraitData, db=None)

        ## Variance submit page only
        #if fd.enablevariance and not variance_data_page:
        #    pass
        #    #title2Body.append("Click the next button to go to the variance submission form.",
        #    #        HT.Center(next,reset))
        #else:
        #    pass
        #    # We'll get this part working later
        #    print("Calling dispBasicStatistics")
        #    self.dispBasicStatistics(fd, this_trait)

        self.build_correlation_tools(fd, this_trait)


        self.make_sample_lists(fd, variance_data_page, this_trait)
        
        if fd.allsamplelist:
            hddn['allsamplelist'] = string.join(fd.allsamplelist, ' ')

        if fd.varianceDispName != 'Variance':
            hddn['isSE'] = "yes"

        # We'll need access to this_trait and hddn in the Jinja2 Template, so we put it inside self
        self.this_trait = this_trait
        self.hddn = hddn

        self.sample_group_types = OrderedDict()
        self.sample_group_types['primary_only'] = fd.RISet + " Only"
        self.sample_group_types['other_only'] = "Non-" + fd.RISet
        self.sample_group_types['all_cases'] = "All Cases"
        self.js_data = dict(sample_groups = self.sample_group_types)


    def dispTraitInformation(self, fd, title1Body, hddn, this_trait):

        _Species = webqtlDatabaseFunction.retrieveSpecies(cursor=self.cursor, RISet=fd.RISet)

        #tbl = HT.TableLite(cellpadding=2, Class="collap", style="margin-left:20px;", width="840", valign="top", id="target1")

        #reset=HT.Input(type='Reset',name='',value=' Reset ',Class="button")

        #XZ, August 02, 2011: The display of icons is decided by the trait type (if trait exists), along with user log-in status. Note that the new submitted trait might not be trait object.
        addSelectionButton = ""
        verifyButton = ""
        rnaseqButton = ""
        geneWikiButton = ""
        probeButton = ""
        similarButton = ""
        snpBrowserButton = ""
        updateButton = ""

        addSelectionText = ""
        verifyText = ""
        rnaseqText = ""
        geneWikiText = ""
        probeText = ""
        similarText = ""
        snpBrowserText = ""
        updateText = ""

        if webqtlConfig.USERDICT[self.privilege] >= webqtlConfig.USERDICT['user']:

            if this_trait==None or this_trait.db.type=='Temp':
                updateButton = HT.Href(url="#redirect", onClick="dataEditingFunc(document.getElementsByName('dataInput')[0],'addPublish');")
                updateButton_img = HT.Image("/images/edit_icon.jpg", name="addnew", alt="Add To Publish", title="Add To Publish", style="border:none;")
                updateButton.append(updateButton_img)
                updateText = "Edit"
            elif this_trait.db.type != 'Temp':
                if this_trait.db.type == 'Publish' and this_trait.confidential: #XZ: confidential phenotype trait
                    if webqtlUtil.hasAccessToConfidentialPhenotypeTrait(privilege=self.privilege, userName=self.userName, authorized_users=this_trait.authorized_users):
                        updateButton = HT.Href(url="#redirect", onClick="dataEditingFunc(document.getElementsByName('dataInput')[0],'updateRecord');")
                        updateButton_img = HT.Image("/images/edit_icon.jpg", name="update", alt="Edit", title="Edit", style="border:none;")
                        updateButton.append(updateButton_img)
                        updateText = "Edit"
                else:
                    updateButton = HT.Href(url="#redirect", onClick="dataEditingFunc(document.getElementsByName('dataInput')[0],'updateRecord');")
                    updateButton_img = HT.Image("/images/edit_icon.jpg", name="update", alt="Edit", title="Edit", style="border:none;")
                    updateButton.append(updateButton_img)
                    updateText = "Edit"
            else:
                pass

        self.cursor.execute('SELECT Name FROM InbredSet WHERE Name="%s"' % fd.RISet)
        if this_trait:
            addSelectionButton = HT.Href(url="#redirect", onClick="addRmvSelection('%s', document.getElementsByName('%s')[0], 'addToSelection');" % (fd.RISet, 'dataInput'))
            addSelectionButton_img = HT.Image("/images/add_icon.jpg", name="addselect", alt="Add To Collection", title="Add To Collection", style="border:none;")
            #addSelectionButton.append(addSelectionButton_img)
            addSelectionText = "Add"
        elif self.cursor.fetchall():
            addSelectionButton = HT.Href(url="#redirect", onClick="dataEditingFunc(document.getElementsByName('%s')[0], 'addRecord');" % ('dataInput'))
            addSelectionButton_img = HT.Image("/images/add_icon.jpg", name="", alt="Add To Collection", title="Add To Collection", style="border:none;")
            #addSelectionButton.append(addSelectionButton_img)
            addSelectionText = "Add"
        else:
            pass


        # Microarray database information to display
        if this_trait and this_trait.db and this_trait.db.type == 'ProbeSet': #before, this line was only reached if this_trait != 0, but now we need to check
            try:
                hddn['GeneId'] = int(string.strip(this_trait.geneid))
            except:
                pass

            #Info2Disp = HT.Paragraph()

            #XZ: Gene Symbol
            if this_trait.symbol:
                #XZ: Show SNP Browser only for mouse
                if _Species == 'mouse':
                    self.cursor.execute("select geneSymbol from GeneList where geneSymbol = %s", this_trait.symbol)
                    geneName = self.cursor.fetchone()
                    if geneName:
                        snpurl = os.path.join(webqtlConfig.CGIDIR, "main.py?FormID=SnpBrowserResultPage&submitStatus=1&diffAlleles=True&customStrain=True") + "&geneName=%s" % geneName[0]
                    else:
                        if this_trait.chr and this_trait.mb:
                            snpurl = os.path.join(webqtlConfig.CGIDIR, "main.py?FormID=SnpBrowserResultPage&submitStatus=1&diffAlleles=True&customStrain=True") + \
                                    "&chr=%s&start=%2.6f&end=%2.6f" % (this_trait.chr, this_trait.mb-0.002, this_trait.mb+0.002)
                        else:
                            snpurl = ""

                    if snpurl:
                        snpBrowserButton = HT.Href(url="#redirect", onClick="openNewWin('%s')" % snpurl)
                        snpBrowserButton_img = HT.Image("/images/snp_icon.jpg", name="snpbrowser", alt=" View SNPs and Indels ", title=" View SNPs and Indels ", style="border:none;")
                        #snpBrowserButton.append(snpBrowserButton_img)
                        snpBrowserText = "SNPs"

                #XZ: Show GeneWiki for all species
                geneWikiButton = HT.Href(url="#redirect", onClick="openNewWin('%s')" % (os.path.join(webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE) + "?FormID=geneWiki&symbol=%s" % this_trait.symbol))
                geneWikiButton_img = HT.Image("/images/genewiki_icon.jpg", name="genewiki", alt=" Write or review comments about this gene ", title=" Write or review comments about this gene ", style="border:none;")
                #geneWikiButton.append(geneWikiButton_img)
                geneWikiText = 'GeneWiki'

                #XZ: display similar traits in other selected datasets
                if this_trait and this_trait.db and this_trait.db.type=="ProbeSet" and this_trait.symbol:
                    if _Species in ("mouse", "rat", "human"):
                        similarUrl = "%s?cmd=sch&gene=%s&alias=1&species=%s" % (os.path.join(webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE), this_trait.symbol, _Species)
                        similarButton = HT.Href(url="#redirect", onClick="openNewWin('%s')" % similarUrl)
                        similarButton_img = HT.Image("/images/find_icon.jpg", name="similar", alt=" Find similar expression data ", title=" Find similar expression data ", style="border:none;")
                        #similarButton.append(similarButton_img)
                        similarText = "Find"
                else:
                    pass
                #tbl.append(HT.TR(
                        #HT.TD('Gene Symbol: ', Class="fwb fs13", valign="top", nowrap="on", width=90),
                        #HT.TD(width=10, valign="top"),
                        #HT.TD(HT.Span('%s' % this_trait.symbol, valign="top", Class="fs13 fsI"), valign="top", width=740)
                        #))
            else:
                tbl.append(HT.TR(
                        HT.TD('Gene Symbol: ', Class="fwb fs13", valign="top", nowrap="on"),
                        HT.TD(width=10, valign="top"),
                        HT.TD(HT.Span('Not available', Class="fs13 fsI"), valign="top")
                        ))



            ##display Verify Location button
            try:
                blatsequence = this_trait.blatseq
                if not blatsequence:
                    #XZ, 06/03/2009: ProbeSet name is not unique among platforms. We should use ProbeSet Id instead.
                    self.cursor.execute("""SELECT Probe.Sequence, Probe.Name
                                           FROM Probe, ProbeSet, ProbeSetFreeze, ProbeSetXRef
                                           WHERE ProbeSetXRef.ProbeSetFreezeId = ProbeSetFreeze.Id AND
                                                 ProbeSetXRef.ProbeSetId = ProbeSet.Id AND
                                                 ProbeSetFreeze.Name = '%s' AND
                                                 ProbeSet.Name = '%s' AND
                                                 Probe.ProbeSetId = ProbeSet.Id order by Probe.SerialOrder""" % (this_trait.db.name, this_trait.name) )
                    seqs = self.cursor.fetchall()
                    if not seqs:
                        raise ValueError
                    else:
                        blatsequence = ''
                        for seqt in seqs:
                            if int(seqt[1][-1]) % 2 == 1:
                                blatsequence += string.strip(seqt[0])

                #--------Hongqiang add this part in order to not only blat ProbeSet, but also blat Probe
                blatsequence = '%3E'+this_trait.name+'%0A'+blatsequence+'%0A'
                #XZ, 06/03/2009: ProbeSet name is not unique among platforms. We should use ProbeSet Id instead.
                self.cursor.execute("""SELECT Probe.Sequence, Probe.Name
                                       FROM Probe, ProbeSet, ProbeSetFreeze, ProbeSetXRef
                                       WHERE ProbeSetXRef.ProbeSetFreezeId = ProbeSetFreeze.Id AND
                                             ProbeSetXRef.ProbeSetId = ProbeSet.Id AND
                                             ProbeSetFreeze.Name = '%s' AND
                                             ProbeSet.Name = '%s' AND
                                             Probe.ProbeSetId = ProbeSet.Id order by Probe.SerialOrder""" % (this_trait.db.name, this_trait.name) )

                seqs = self.cursor.fetchall()
                for seqt in seqs:
                    if int(seqt[1][-1]) %2 == 1:
                        blatsequence += '%3EProbe_'+string.strip(seqt[1])+'%0A'+string.strip(seqt[0])+'%0A'
                #--------
                #XZ, 07/16/2009: targetsequence is not used, so I comment out this block
                #targetsequence = this_trait.targetseq
                #if targetsequence==None:
                #       targetsequence = ""

                #XZ: Pay attention to the parameter of version (rn, mm, hg). They need to be changed if necessary.
                if _Species == "rat":
                    UCSC_BLAT_URL = webqtlConfig.UCSC_BLAT % ('rat', 'rn3', blatsequence)
                    UTHSC_BLAT_URL = ""
                elif _Species == "mouse":
                    UCSC_BLAT_URL = webqtlConfig.UCSC_BLAT % ('mouse', 'mm9', blatsequence)
                    UTHSC_BLAT_URL = webqtlConfig.UTHSC_BLAT % ('mouse', 'mm9', blatsequence)
                elif _Species == "human":
                    UCSC_BLAT_URL = webqtlConfig.UCSC_BLAT % ('human', 'hg19', blatsequence)
                    UTHSC_BLAT_URL = ""
                else:
                    UCSC_BLAT_URL = ""
                    UTHSC_BLAT_URL = ""

                if UCSC_BLAT_URL:
                    verifyButton = HT.Href(url="#", onClick="javascript:openNewWin('%s'); return false;" % UCSC_BLAT_URL)
                    verifyButtonImg = HT.Image("/images/verify_icon.jpg", name="verify", alt=" Check probe locations at UCSC ",
                            title=" Check probe locations at UCSC ", style="border:none;")
                    verifyButton.append(verifyButtonImg)
                    verifyText = 'Verify'
                if UTHSC_BLAT_URL:
                    rnaseqButton = HT.Href(url="#", onClick="javascript:openNewWin('%s'); return false;" % UTHSC_BLAT_URL)
                    rnaseqButtonImg = HT.Image("/images/rnaseq_icon.jpg", name="rnaseq", alt=" View probes, SNPs, and RNA-seq at UTHSC ",
                            title=" View probes, SNPs, and RNA-seq at UTHSC ", style="border:none;")
                    rnaseqButton.append(rnaseqButtonImg)
                    rnaseqText = 'RNA-seq'
                tSpan.append(HT.BR())
            except:
                pass

            #Display probe information (if any)
            if this_trait.db.name.find('Liver') >= 0 and this_trait.db.name.find('F2') < 0:
                pass
            else:
                #query database for number of probes associated with trait; if count > 0, set probe tool button and text
                self.cursor.execute("""SELECT count(*)
                                           FROM Probe, ProbeSet
                                           WHERE ProbeSet.Name = '%s' AND Probe.ProbeSetId = ProbeSet.Id""" % (this_trait.name))

                probeResult = self.cursor.fetchone()
                if probeResult[0] > 0:
                    probeurl = "%s?FormID=showProbeInfo&database=%s&ProbeSetID=%s&CellID=%s&RISet=%s&incparentsf1=ON" \
                            % (os.path.join(webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE), this_trait.db, this_trait.name, this_trait.cellid, fd.RISet)
                    probeButton = HT.Href(url="#", onClick="javascript:openNewWin('%s'); return false;" % probeurl)
                    probeButton_img = HT.Image("/images/probe_icon.jpg", name="probe", alt=" Check sequence of probes ", title=" Check sequence of probes ", style="border:none;")
                    #probeButton.append(probeButton_img)
                    probeText = "Probes"

            #tSpan = HT.Span(Class="fs13")

            #XZ: deal with blat score and blat specificity.
            #if this_trait.probe_set_specificity or this_trait.probe_set_blat_score:
            #    if this_trait.probe_set_specificity:
            #        pass
            #        #tSpan.append(HT.Href(url="/blatInfo.html", target="_blank", title="Values higher than 2 for the specificity are good", text="BLAT specificity", Class="non_bold"),": %.1f" % float(this_trait.probe_set_specificity), "&nbsp;"*3)
            #    if this_trait.probe_set_blat_score:
            #        pass
            #        #tSpan.append("Score: %s" % int(this_trait.probe_set_blat_score), "&nbsp;"*2)

            #onClick="openNewWin('/blatInfo.html')"

            #tbl.append(HT.TR(
            #        HT.TD('Target Score: ', Class="fwb fs13", valign="top", nowrap="on"),
            #        HT.TD(width=10, valign="top"),
            #        HT.TD(tSpan, valign="top")
            #        ))

            #tSpan = HT.Span(Class="fs13")
            #tSpan.append(str(_Species).capitalize(), ", ", fd.RISet)
            #
            #tbl.append(HT.TR(
            #        HT.TD('Species and Group: ', Class="fwb fs13", valign="top", nowrap="on"),
            #        HT.TD(width=10, valign="top"),
            #        HT.TD(tSpan, valign="top")
            #        ))

            #if this_trait.cellid:
            #    self.cursor.execute("""
            #                    select ProbeFreeze.Name from ProbeFreeze, ProbeSetFreeze
            #                            where
            #                    ProbeFreeze.Id = ProbeSetFreeze.ProbeFreezeId AND
            #                    ProbeSetFreeze.Id = %d""" % this_trait.db.id)
            #    probeDBName = self.cursor.fetchone()[0]
            #    tbl.append(HT.TR(
            #            HT.TD('Database: ', Class="fs13 fwb", valign="top", nowrap="on"),
            #            HT.TD(width=10, valign="top"),
            #            HT.TD(HT.Span('%s' % probeDBName, Class="non_bold"), valign="top")
            #            ))
            #else:
                #tbl.append(HT.TR(
                #        HT.TD('Database: ', Class="fs13 fwb", valign="top", nowrap="on"),
                #        HT.TD(width=10, valign="top"),
                #        HT.TD(HT.Href(text=this_trait.db.fullname, url = webqtlConfig.INFOPAGEHREF % this_trait.db.name,
                #        target='_blank', Class="fs13 fwn non_bold"), valign="top")
                #        ))
                #pass

            this_trait.species = _Species  # We need this in the template, so we tuck it into this_trait
            this_trait.database = this_trait.get_database()

            #XZ: ID links
            if this_trait.genbankid or this_trait.geneid or this_trait.unigeneid or this_trait.omim or this_trait.homologeneid:
                idStyle = "background:#dddddd;padding:2"
                tSpan = HT.Span(Class="fs13")
                if this_trait.geneid:
                    gurl = HT.Href(text= 'Gene', target='_blank',\
                            url=webqtlConfig.NCBI_LOCUSID % this_trait.geneid, Class="fs14 fwn", title="Info from NCBI Entrez Gene")
                    #tSpan.append(HT.Span(gurl, style=idStyle), "&nbsp;"*2)
                if this_trait.omim:
                    gurl = HT.Href(text= 'OMIM', target='_blank', \
                            url= webqtlConfig.OMIM_ID % this_trait.omim,Class="fs14 fwn", title="Summary from On Mendelian Inheritance in Man")
                    #tSpan.append(HT.Span(gurl, style=idStyle), "&nbsp;"*2)
                if this_trait.unigeneid:
                    try:
                        gurl = HT.Href(text= 'UniGene',target='_blank',\
                                url= webqtlConfig.UNIGEN_ID % tuple(string.split(this_trait.unigeneid,'.')[:2]),Class="fs14 fwn", title="UniGene ID")
                        #tSpan.append(HT.Span(gurl, style=idStyle), "&nbsp;"*2)
                    except:
                        pass
                if this_trait.genbankid:
                    this_trait.genbankid = '|'.join(this_trait.genbankid.split('|')[0:10])
                    if this_trait.genbankid[-1]=='|':
                        this_trait.genbankid=this_trait.genbankid[0:-1]
                    gurl = HT.Href(text= 'GenBank', target='_blank', \
                            url= webqtlConfig.GENBANK_ID % this_trait.genbankid,Class="fs14 fwn", title="Find the original GenBank sequence used to design the probes")
                    #tSpan.append(HT.Span(gurl, style=idStyle), "&nbsp;"*2)
                if this_trait.homologeneid:
                    hurl = HT.Href(text= 'HomoloGene', target='_blank',\
                            url=webqtlConfig.HOMOLOGENE_ID % this_trait.homologeneid, Class="fs14 fwn", title="Find similar genes in other species")
                    #tSpan.append(HT.Span(hurl, style=idStyle), "&nbsp;"*2)

                #tbl.append(
                #        HT.TR(HT.TD(colspan=3,height=6)),
                #        HT.TR(
                #        HT.TD('Resource Links: ', Class="fwb fs13", valign="top", nowrap="on"),
                #        HT.TD(width=10, valign="top"),
                #        HT.TD(tSpan, valign="top")
                #        ))

            #XZ: Resource Links:
            if this_trait.symbol:
                linkStyle = "background:#dddddd;padding:2"
                tSpan = HT.Span(style="font-family:verdana,serif;font-size:13px")

                #XZ,12/26/2008: Gene symbol may contain single quotation mark.
                #For example, Affymetrix, mouse430v2, 1440338_at, the symbol is 2'-Pde (geneid 211948)
                #I debug this by using double quotation marks.
                if _Species == "rat":

                    #XZ, 7/16/2009: The url for SymAtlas (renamed as BioGPS) has changed. We don't need this any more
                    #symatlas_species = "Rattus norvegicus"

                    #self.cursor.execute("SELECT kgID, chromosome,txStart,txEnd FROM GeneList_rn33 WHERE geneSymbol = '%s'" % this_trait.symbol)
                    self.cursor.execute('SELECT kgID, chromosome,txStart,txEnd FROM GeneList_rn33 WHERE geneSymbol = "%s"' % this_trait.symbol)
                    try:
                        kgId, chr, txst, txen = self.cursor.fetchall()[0]
                        if chr and txst and txen and kgId:
                            txst = int(txst*1000000)
                            txen = int(txen*1000000)
                            #tSpan.append(HT.Span(HT.Href(text= 'UCSC',target="mainFrame",\
                            #        title= 'Info from UCSC Genome Browser', url = webqtlConfig.UCSC_REFSEQ % ('rn3',kgId,chr,txst,txen),Class="fs14 fwn"), style=linkStyle)
                            #        , "&nbsp;"*2)
                    except:
                        pass
                if _Species == "mouse":

                    #XZ, 7/16/2009: The url for SymAtlas (renamed as BioGPS) has changed. We don't need this any more
                    #symatlas_species = "Mus musculus"

                    #self.cursor.execute("SELECT chromosome,txStart,txEnd FROM GeneList WHERE geneSymbol = '%s'" % this_trait.symbol)
                    self.cursor.execute('SELECT chromosome,txStart,txEnd FROM GeneList WHERE geneSymbol = "%s"' % this_trait.symbol)
                    try:
                        chr, txst, txen = self.cursor.fetchall()[0]
                        if chr and txst and txen and this_trait.refseq_transcriptid :
                            txst = int(txst*1000000)
                            txen = int(txen*1000000)
                            tSpan.append(HT.Span(HT.Href(text= 'UCSC',target="mainFrame",\
                                    title= 'Info from UCSC Genome Browser', url = webqtlConfig.UCSC_REFSEQ % ('mm9',this_trait.refseq_transcriptid,chr,txst,txen),
                                    Class="fs14 fwn"), style=linkStyle)
                                    , "&nbsp;"*2)
                    except:
                        pass

                #XZ, 7/16/2009: The url for SymAtlas (renamed as BioGPS) has changed. We don't need this any more
                #tSpan.append(HT.Span(HT.Href(text= 'SymAtlas',target="mainFrame",\
                #       url="http://symatlas.gnf.org/SymAtlas/bioentry?querytext=%s&query=14&species=%s&type=Expression" \
                #       % (this_trait.symbol,symatlas_species),Class="fs14 fwn", \
                #       title="Expression across many tissues and cell types"), style=linkStyle), "&nbsp;"*2)
                if this_trait.geneid and (_Species == "mouse" or _Species == "rat" or _Species == "human"):
                    #tSpan.append(HT.Span(HT.Href(text= 'BioGPS',target="mainFrame",\
                    #        url="http://biogps.gnf.org/?org=%s#goto=genereport&id=%s" \
                    #        % (_Species, this_trait.geneid),Class="fs14 fwn", \
                    #        title="Expression across many tissues and cell types"), style=linkStyle), "&nbsp;"*2)
                    pass
                #tSpan.append(HT.Span(HT.Href(text= 'STRING',target="mainFrame",\
                #        url="http://string.embl.de/newstring_cgi/show_link_summary.pl?identifier=%s" \
                #        % this_trait.symbol,Class="fs14 fwn", \
                #        title="Protein interactions: known and inferred"), style=linkStyle), "&nbsp;"*2)
                if this_trait.symbol:
                    #ZS: The "species scientific" converts the plain English species names we're using to their scientific names, which are needed for PANTHER's input
                    #We should probably use the scientific name along with the English name (if not instead of) elsewhere as well, given potential non-English speaking users
                    if _Species == "mouse":
                        species_scientific = "Mus%20musculus"
                    elif _Species == "rat":
                        species_scientific = "Rattus%20norvegicus"
                    elif _Species == "human":
                        species_scientific = "Homo%20sapiens"
                    elif _Species == "drosophila":
                        species_scientific = "Drosophila%20melanogaster"
                    else:
                        species_scientific = "all"

                    species_scientific
                    #tSpan.append(HT.Span(HT.Href(text= 'PANTHER',target="mainFrame", \
                    #        url="http://www.pantherdb.org/genes/geneList.do?searchType=basic&fieldName=all&organism=%s&listType=1&fieldValue=%s"  \
                    #        % (species_scientific, this_trait.symbol),Class="fs14 fwn", \
                    #        title="Gene and protein data resources from Celera-ABI"), style=linkStyle), "&nbsp;"*2)
                else:
                    pass
                #tSpan.append(HT.Span(HT.Href(text= 'BIND',target="mainFrame",\
                #       url="http://bind.ca/?textquery=%s" \
                #       % this_trait.symbol,Class="fs14 fwn", \
                #       title="Protein interactions"), style=linkStyle), "&nbsp;"*2)
                #if this_trait.geneid and (_Species == "mouse" or _Species == "rat" or _Species == "human"):
                #    tSpan.append(HT.Span(HT.Href(text= 'Gemma',target="mainFrame",\
                #            url="http://www.chibi.ubc.ca/Gemma/gene/showGene.html?ncbiid=%s" \
                #            % this_trait.geneid, Class="fs14 fwn", \
                #            title="Meta-analysis of gene expression data"), style=linkStyle), "&nbsp;"*2)
                #tSpan.append(HT.Span(HT.Href(text= 'SynDB',target="mainFrame",\
                #        url="http://lily.uthsc.edu:8080/20091027_GNInterfaces/20091027_redirectSynDB.jsp?query=%s" \
                #        % this_trait.symbol, Class="fs14 fwn", \
                #        title="Brain synapse database"), style=linkStyle), "&nbsp;"*2)
                #if _Species == "mouse":
                #    tSpan.append(HT.Span(HT.Href(text= 'ABA',target="mainFrame",\
                #            url="http://mouse.brain-map.org/brain/%s.html" \
                #            % this_trait.symbol, Class="fs14 fwn", \
                #            title="Allen Brain Atlas"), style=linkStyle), "&nbsp;"*2)

                if this_trait.geneid:
                    #if _Species == "mouse":
                    #       tSpan.append(HT.Span(HT.Href(text= 'ABA',target="mainFrame",\
                    #               url="http://www.brain-map.org/search.do?queryText=egeneid=%s" \
                    #               % this_trait.geneid, Class="fs14 fwn", \
                    #               title="Allen Brain Atlas"), style=linkStyle), "&nbsp;"*2)
                    if _Species == "human":
                        #tSpan.append(HT.Span(HT.Href(text= 'ABA',target="mainFrame",\
                        #        url="http://humancortex.alleninstitute.org/has/human/imageseries/search/1.html?searchSym=t&searchAlt=t&searchName=t&gene_term=&entrez_term=%s" \
                        #        % this_trait.geneid, Class="fs14 fwn", \
                        #        title="Allen Brain Atlas"), style=linkStyle), "&nbsp;"*2)
                        pass

                #tbl.append(
                #        HT.TR(HT.TD(colspan=3,height=6)),
                #        HT.TR(
                #        HT.TD(' '),
                #        HT.TD(width=10, valign="top"),
                #        HT.TD(tSpan, valign="top")))

            #menuTable = HT.TableLite(cellpadding=2, Class="collap", width="620", id="target1")
            #menuTable.append(HT.TR(HT.TD(addSelectionButton, align="center"),HT.TD(similarButton, align="center"),HT.TD(verifyButton, align="center"),HT.TD(geneWikiButton, align="center"),HT.TD(snpBrowserButton, align="center"),HT.TD(rnaseqButton, align="center"),HT.TD(probeButton, align="center"),HT.TD(updateButton, align="center"), colspan=3, height=50, style="vertical-align:bottom;"))
            #menuTable.append(HT.TR(HT.TD(addSelectionText, align="center"),HT.TD(similarText, align="center"),HT.TD(verifyText, align="center"),HT.TD(geneWikiText, align="center"),HT.TD(snpBrowserText, align="center"),HT.TD(rnaseqText, align="center"),HT.TD(probeText, align="center"),HT.TD(updateText, align="center"), colspan=3, height=50, style="vertical-align:bottom;"))


            #for zhou mi's cliques, need to be removed
            #if self.database[:6]  == 'BXDMic' and self.ProbeSetID in cliqueID:
            #       Info2Disp.append(HT.Strong('Clique Search: '),HT.Href(text='Search',\
            #               url ="http://compbio1.utmem.edu/clique_go/results.php?pid=%s&pval_1=0&pval_2=0.001" \
            #               % self.ProbeSetID,target='_blank',Class="normalsize"),HT.BR())

            #linkTable.append(HT.TR(linkTD))
            #Info2Disp.append(linkTable)
            #title1Body.append(tbl, HT.BR(), menuTable)

        elif this_trait and this_trait.db and this_trait.db.type =='Publish': #Check if trait is phenotype

            if this_trait.confidential:
                pass
                #tbl.append(HT.TR(
                #                HT.TD('Pre-publication Phenotype: ', Class="fs13 fwb", valign="top", nowrap="on", width=90),
                #                HT.TD(width=10, valign="top"),
                #                HT.TD(HT.Span(this_trait.pre_publication_description, Class="fs13"), valign="top", width=740)
                #                ))
                if webqtlUtil.hasAccessToConfidentialPhenotypeTrait(privilege=self.privilege, userName=self.userName, authorized_users=this_trait.authorized_users):
                    #tbl.append(HT.TR(
                    #                HT.TD('Post-publication Phenotype: ', Class="fs13 fwb", valign="top", nowrap="on", width=90),
                    #                HT.TD(width=10, valign="top"),
                    #                HT.TD(HT.Span(this_trait.post_publication_description, Class="fs13"), valign="top", width=740)
                    #                ))
                    #tbl.append(HT.TR(
                    #                HT.TD('Pre-publication Abbreviation: ', Class="fs13 fwb", valign="top", nowrap="on", width=90),
                    #                HT.TD(width=10, valign="top"),
                    #                HT.TD(HT.Span(this_trait.pre_publication_abbreviation, Class="fs13"), valign="top", width=740)
                    #                ))
                    #tbl.append(HT.TR(
                    #                HT.TD('Post-publication Abbreviation: ', Class="fs13 fwb", valign="top", nowrap="on", width=90),
                    #                HT.TD(width=10, valign="top"),
                    #                HT.TD(HT.Span(this_trait.post_publication_abbreviation, Class="fs13"), valign="top", width=740)
                    #                ))
                    #tbl.append(HT.TR(
                    #                HT.TD('Lab code: ', Class="fs13 fwb", valign="top", nowrap="on", width=90),
                    #                HT.TD(width=10, valign="top"),
                    #                HT.TD(HT.Span(this_trait.lab_code, Class="fs13"), valign="top", width=740)
                    #                ))
                    pass
                #tbl.append(HT.TR(
                #                HT.TD('Owner: ', Class="fs13 fwb", valign="top", nowrap="on", width=90),
                #                HT.TD(width=10, valign="top"),
                #                HT.TD(HT.Span(this_trait.owner, Class="fs13"), valign="top", width=740)
                #                ))
            else:
                pass
                #tbl.append(HT.TR(
                #                HT.TD('Phenotype: ', Class="fs13 fwb", valign="top", nowrap="on", width=90),
                #                HT.TD(width=10, valign="top"),
                #                HT.TD(HT.Span(this_trait.post_publication_description, Class="fs13"), valign="top", width=740)
                #                ))
            #tbl.append(HT.TR(
            #                HT.TD('Authors: ', Class="fs13 fwb",
            #                        valign="top", nowrap="on", width=90),
            #                HT.TD(width=10, valign="top"),
            #                HT.TD(HT.Span(this_trait.authors, Class="fs13"),
            #                        valign="top", width=740)
            #                ))
            #tbl.append(HT.TR(
            #                HT.TD('Title: ', Class="fs13 fwb",
            #                        valign="top", nowrap="on", width=90),
            #                HT.TD(width=10, valign="top"),
            #                HT.TD(HT.Span(this_trait.title, Class="fs13"),
            #                        valign="top", width=740)
            #                ))
            if this_trait.journal:
                journal = this_trait.journal
                if this_trait.year:
                    journal = this_trait.journal + " (%s)" % this_trait.year
                #
                #tbl.append(HT.TR(
                #        HT.TD('Journal: ', Class="fs13 fwb",
                #                valign="top", nowrap="on", width=90),
                #        HT.TD(width=10, valign="top"),
                #        HT.TD(HT.Span(journal, Class="fs13"),
                #                valign="top", width=740)
                #        ))
            PubMedLink = ""
            if this_trait.pubmed_id:
                PubMedLink = webqtlConfig.PUBMEDLINK_URL % this_trait.pubmed_id
            if PubMedLink:
                #tbl.append(HT.TR(
                #        HT.TD('Link: ', Class="fs13 fwb",
                #                valign="top", nowrap="on", width=90),
                #        HT.TD(width=10, valign="top"),
                #        HT.TD(HT.Span(HT.Href(url=PubMedLink, text="PubMed",target='_blank',Class="fs14 fwn"),
                #                style = "background:#cddcff;padding:2"), valign="top", width=740)
                #        ))
                pass

            menuTable = HT.TableLite(cellpadding=2, Class="collap", width="150", id="target1")
            #menuTable.append(HT.TR(HT.TD(addSelectionButton, align="center"),HT.TD(updateButton, align="center"), colspan=3, height=50, style="vertical-align:bottom;"))
            #menuTable.append(HT.TR(HT.TD(addSelectionText, align="center"),HT.TD(updateText, align="center"), colspan=3, height=50, style="vertical-align:bottom;"))

            #title1Body.append(tbl, HT.BR(), menuTable)

        elif this_trait and this_trait.db and this_trait.db.type == 'Geno': #Check if trait is genotype

            GenoInfo = HT.Paragraph()
            if this_trait.chr and this_trait.mb:
                location = ' Chr %s @ %s Mb' % (this_trait.chr,this_trait.mb)
            else:
                location = "not available"

            if this_trait.sequence and len(this_trait.sequence) > 100:
                if _Species == "rat":
                    UCSC_BLAT_URL = webqtlConfig.UCSC_BLAT % ('rat', 'rn3', this_trait.sequence)
                    UTHSC_BLAT_URL = webqtlConfig.UTHSC_BLAT % ('rat', 'rn3', this_trait.sequence)
                elif _Species == "mouse":
                    UCSC_BLAT_URL = webqtlConfig.UCSC_BLAT % ('mouse', 'mm9', this_trait.sequence)
                    UTHSC_BLAT_URL = webqtlConfig.UTHSC_BLAT % ('mouse', 'mm9', this_trait.sequence)
                elif _Species == "human":
                    UCSC_BLAT_URL = webqtlConfig.UCSC_BLAT % ('human', 'hg19', blatsequence)
                    UTHSC_BLAT_URL = webqtlConfig.UTHSC_BLAT % ('human', 'hg19', this_trait.sequence)
                else:
                    UCSC_BLAT_URL = ""
                    UTHSC_BLAT_URL = ""
                if UCSC_BLAT_URL:
                    #verifyButton = HT.Href(url="#", onClick="openNewWin('%s')" % UCSC_BLAT_URL)
                    verifyButton = HT.Href(url="#")
                    verifyButtonImg = HT.Image("/images/verify_icon.jpg", name="verify", alt=" Check probe locations at UCSC ", title=" Check probe locations at UCSC ", style="border:none;")
                    verifyButton.append(verifyButtonImg)
                    verifyText = "Verify"
                    rnaseqButton = HT.Href(url="#", onClick="openNewWin('%s')" % UTHSC_BLAT_URL)
                    rnaseqButtonImg = HT.Image("/images/rnaseq_icon.jpg", name="rnaseq", alt=" View probes, SNPs, and RNA-seq at UTHSC ", title=" View probes, SNPs, and RNA-seq at UTHSC ", style="border:none;")
                    rnaseqButton.append(rnaseqButtonImg)
                    rnaseqText = "RNA-seq"

            #tbl.append(HT.TR(
            #                HT.TD('Location: ', Class="fs13 fwb",
            #                        valign="top", nowrap="on", width=90),
            #                HT.TD(width=10, valign="top"),
            #                HT.TD(HT.Span(location, Class="fs13"), valign="top", width=740)
            #                ),
            #        HT.TR(
            #                HT.TD('SNP Search: ', Class="fs13 fwb",
            #                        valign="top", nowrap="on", width=90),
            #                HT.TD(width=10, valign="top"),
            #                HT.TD(HT.Href("http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?db=snp&cmd=search&term=%s" % this_trait.name, 'NCBI',Class="fs13"),
            #                        valign="top", width=740)
            #                ))

            menuTable = HT.TableLite(cellpadding=2, Class="collap", width="275", id="target1")
            #menuTable.append(HT.TR(HT.TD(addSelectionButton, align="center"),HT.TD(verifyButton, align="center"),HT.TD(rnaseqButton, align="center"), HT.TD(updateButton, align="center"), colspan=3, height=50, style="vertical-align:bottom;"))
            #menuTable.append(HT.TR(HT.TD(addSelectionText, align="center"),HT.TD(verifyText, align="center"),HT.TD(rnaseqText, align="center"), HT.TD(updateText, align="center"), colspan=3, height=50, style="vertical-align:bottom;"))

            #title1Body.append(tbl, HT.BR(), menuTable)

        elif (this_trait == None or this_trait.db.type == 'Temp'): #if temporary trait (user-submitted trait or PCA trait)

            #TempInfo = HT.Paragraph()
            if this_trait != None:
                if this_trait.description:
                    pass
                    #tbl.append(HT.TR(HT.TD(HT.Strong('Description: '),' %s ' % this_trait.description,HT.BR()), colspan=3, height=15))
            else:
                tbl.append(HT.TR(HT.TD(HT.Strong('Description: '),'not available',HT.BR(),HT.BR()), colspan=3, height=15))

            if (updateText == "Edit"):
                menuTable = HT.TableLite(cellpadding=2, Class="collap", width="150", id="target1")
            else:
                menuTable = HT.TableLite(cellpadding=2, Class="collap", width="80", id="target1")

            #menuTable.append(HT.TR(HT.TD(addSelectionButton, align="right"),HT.TD(updateButton, align="right"), colspan=3, height=50, style="vertical-align:bottom;")       )
            #menuTable.append(HT.TR(HT.TD(addSelectionText, align="center"),HT.TD(updateText, align="center"), colspan=3, height=50, style="vertical-align:bottom;"))
            #
            #title1Body.append(tbl, HT.BR(), menuTable)

        else:
            pass


    def dispBasicStatistics(self, fd, this_trait):

        #XZ, June 22, 2011: The definition and usage of primary_samples, other_samples, specialStrains, all_samples are not clear and hard to understand. But since they are only used in this function for draw graph purpose, they will not hurt the business logic outside. As of June 21, 2011, this function seems work fine, so no hurry to clean up. These parameters and code in this function should be cleaned along with fd.f1list, fd.parlist, fd.samplelist later.
        #stats_row = HT.TR()
        #stats_cell = HT.TD()

        if fd.genotype.type == "riset":
            samplelist = fd.f1list + fd.samplelist
        else:
            samplelist = fd.f1list + fd.parlist + fd.samplelist

        other_samples = [] #XZ: sample that is not of primary group
        specialStrains = [] #XZ: This might be replaced by other_samples / ZS: It is just other samples without parent/f1 samples.
        all_samples = []
        primary_samples = [] #XZ: sample of primary group, e.g., BXD, LXS

        #self.MDP_menu = HT.Select(name='stats_mdp', Class='stats_mdp')
        self.MDP_menu = [] # We're going to use the same named data structure as in the old version
                      # but repurpose it for Jinja2 as an array

        for sample in this_trait.data.keys():
            sampleName = sample.replace("_2nd_", "")
            if sample not in samplelist:
                if this_trait.data[sampleName].value != None:
                    if sample.find('F1') < 0:
                        specialStrains.append(sample)
                    if (this_trait.data[sampleName].value != None) and (sample not in (fd.f1list + fd.parlist)):
                        other_samples.append(sample) #XZ: at current stage, other_samples doesn't include parent samples and F1 samples of primary group
            else:
                if (this_trait.data[sampleName].value != None) and (sample not in (fd.f1list + fd.parlist)):
                    primary_samples.append(sample) #XZ: at current stage, the primary_samples is the same as fd.samplelist / ZS: I tried defining primary_samples as fd.samplelist instead, but in some cases it ended up including the parent samples (1436869_at BXD)

        if len(other_samples) > 3:
            other_samples.sort(key=webqtlUtil.natsort_key)
            primary_samples.sort(key=webqtlUtil.natsort_key)
            primary_samples = map(lambda X:"_2nd_"+X, fd.f1list + fd.parlist) + primary_samples #XZ: note that fd.f1list and fd.parlist are added.
            all_samples = primary_samples + other_samples
            other_samples = map(lambda X:"_2nd_"+X, fd.f1list + fd.parlist) + other_samples #XZ: note that fd.f1list and fd.parlist are added.
            print("ac1")   # This is the one used for first sall3
            self.MDP_menu.append(('All Cases','0'))
            self.MDP_menu.append(('%s Only' % fd.RISet, '1'))
            self.MDP_menu.append(('Non-%s Only' % fd.RISet, '2'))

        else:
            if (len(other_samples) > 0) and (len(primary_samples) + len(other_samples) > 3):
                print("ac2")
                self.MDP_menu.append(('All Cases','0'))
                self.MDP_menu.append(('%s Only' % fd.RISet,'1'))
                self.MDP_menu.append(('Non-%s Only' % fd.RISet,'2'))
                all_samples = primary_samples
                all_samples.sort(key=webqtlUtil.natsort_key)
                all_samples = map(lambda X:"_2nd_"+X, fd.f1list + fd.parlist) + all_samples
                primary_samples = map(lambda X:"_2nd_"+X, fd.f1list + fd.parlist) + primary_samples
            else:
                print("ac3")
                all_samples = samplelist

            other_samples.sort(key=webqtlUtil.natsort_key)
            all_samples = all_samples + other_samples

        if (len(other_samples)) > 0 and (len(primary_samples) + len(other_samples) > 4):
            #One set of vals for all, selected sample only, and non-selected only
            vals1 = []
            vals2 = []
            vals3 = []

            #Using all samples/cases for values
            #for sample_type in (all_samples, primary_samples, other_samples):
            for sampleNameOrig in all_samples:
                sampleName = sampleNameOrig.replace("_2nd_", "")

                #try:
                print("* type of this_trait:", type(this_trait))
                print("  name:", this_trait.__class__.__name__)
                print("  this_trait:", this_trait)
                print("  type of this_trait.data[sampleName]:", type(this_trait.data[sampleName]))
                print("  name:", this_trait.data[sampleName].__class__.__name__)
                print("  this_trait.data[sampleName]:", this_trait.data[sampleName])
                thisval = this_trait.data[sampleName].value
                print("  thisval:", thisval)
                thisvar = this_trait.data[sampleName].variance
                print("  thisvar:", thisvar)
                thisValFull = [sampleName, thisval, thisvar]
                print("  thisValFull:", thisValFull)
                #except:
                #    continue

                vals1.append(thisValFull)
                
                
            #vals1 = [[sampleNameOrig.replace("_2nd_", ""),
            #  this_trait.data[sampleName].val,
            #  this_trait.data[sampleName].var]
            #    for sampleNameOrig in all_samples]]
            #    

            #Using just the RISet sample
            for sampleNameOrig in primary_samples:
                sampleName = sampleNameOrig.replace("_2nd_", "")

                #try:
                thisval = this_trait.data[sampleName].value
                thisvar = this_trait.data[sampleName].variance
                thisValFull = [sampleName,thisval,thisvar]
                #except:
                #    continue

                vals2.append(thisValFull)

            #Using all non-RISet samples only
            for sampleNameOrig in other_samples:
                sampleName = sampleNameOrig.replace("_2nd_", "")

                #try:
                thisval = this_trait.data[sampleName].value
                thisvar = this_trait.data[sampleName].variance
                thisValFull = [sampleName,thisval,thisvar]
                #except:
                #    continue

                vals3.append(thisValFull)

            vals_set = [vals1,vals2,vals3]

        else:
            vals = []

            #Using all samples/cases for values
            for sampleNameOrig in all_samples:
                sampleName = sampleNameOrig.replace("_2nd_", "")

                #try:
                thisval = this_trait.data[sampleName].value
                thisvar = this_trait.data[sampleName].variance
                thisValFull = [sampleName,thisval,thisvar]
                #except:
                #    continue

                vals.append(thisValFull)

            vals_set = [vals]

        self.stats_data = []
        for i, vals in enumerate(vals_set):
            if i == 0 and len(vals) < 4:
                stats_container = HT.Div(id="stats_tabs", style="padding:10px;", Class="ui-tabs") #Needed for tabs; notice the "stats_script_text" below referring to this element
                stats_container.append(HT.Div(HT.Italic("Fewer than 4 case data were entered. No statistical analysis has been attempted.")))
                stats_script_text = """$(function() { $("#stats_tabs").tabs();});"""
                #stats_cell.append(stats_container)
                break
            elif (i == 1 and len(primary_samples) < 4):
                stats_container = HT.Div(id="stats_tabs%s" % i, Class="ui-tabs")
                stats_container.append(HT.Div(HT.Italic("Fewer than 4 " + fd.RISet + " case data were entered. No statistical analysis has been attempted.")))
            elif (i == 2 and len(other_samples) < 4):
                stats_container = HT.Div(id="stats_tabs%s" % i, Class="ui-tabs")
                stats_container.append(HT.Div(HT.Italic("Fewer than 4 non-" + fd.RISet + " case data were entered. No statistical analysis has been attempted.")))
                stats_script_text = """$(function() { $("#stats_tabs0").tabs(); $("#stats_tabs1").tabs(); $("#stats_tabs2").tabs();});"""
            else:
                #stats_container = HT.Div(id="stats_tabs%s" % i, Class="ui-tabs")
                stats_script_text = """$(function() { $("#stats_tabs0").tabs(); $("#stats_tabs1").tabs(); $("#stats_tabs2").tabs();});"""
            if len(vals) > 4:
                stats_tab_list = [HT.Href(text="Basic Table", url="#statstabs-1", Class="stats_tab"),HT.Href(text="Probability Plot", url="#statstabs-5", Class="stats_tab"),
                                                  HT.Href(text="Bar Graph (by name)", url="#statstabs-3", Class="stats_tab"), HT.Href(text="Bar Graph (by rank)", url="#statstabs-4", Class="stats_tab"),
                                                  HT.Href(text="Box Plot", url="#statstabs-2", Class="stats_tab")]
                #stats_tabs = HT.List(stats_tab_list)
                #stats_container.append(stats_tabs)
                #
                #table_div = HT.Div(id="statstabs-1")
                #table_container = HT.Paragraph()
                #
                #statsTable = HT.TableLite(cellspacing=0, cellpadding=0, width="100%")

                if this_trait.db:
                    if this_trait.cellid:
                        self.stats_data.append(BasicStatisticsFunctions.basicStatsTable(vals=vals, trait_type=this_trait.db.type, cellid=this_trait.cellid))
                    else:
                        self.stats_data.append(BasicStatisticsFunctions.basicStatsTable(vals=vals, trait_type=this_trait.db.type))
                else:
                    self.stats_data.append(BasicStatisticsFunctions.basicStatsTable(vals=vals))

                #statsTable.append(HT.TR(HT.TD(statsTableCell)))

                #table_container.append(statsTable)
                #table_div.append(table_container)
                #stats_container.append(table_div)
                #
                #normalplot_div = HT.Div(id="statstabs-5")
                #normalplot_container = HT.Paragraph()
                #normalplot = HT.TableLite(cellspacing=0, cellpadding=0, width="100%")

                try:
                    plotTitle = this_trait.symbol
                    plotTitle += ": "
                    plotTitle += this_trait.name
                except:
                    plotTitle = str(this_trait.name)

                #normalplot_img = BasicStatisticsFunctions.plotNormalProbability(vals=vals, RISet=fd.RISet, title=plotTitle, specialStrains=specialStrains)
                #normalplot.append(HT.TR(HT.TD(normalplot_img)))
                #normalplot.append(HT.TR(HT.TD(HT.BR(),HT.BR(),"This plot evaluates whether data are \
                #normally distributed. Different symbols represent different groups.",HT.BR(),HT.BR(),
                #"More about ", HT.Href(url="http://en.wikipedia.org/wiki/Normal_probability_plot",
                #                 target="_blank", text="Normal Probability Plots"), " and more about interpreting these plots from the ", HT.Href(url="/glossary.html#normal_probability", target="_blank", text="glossary"))))
                #normalplot_container.append(normalplot)
                #normalplot_div.append(normalplot_container)
                #stats_container.append(normalplot_div)

                #boxplot_div = HT.Div(id="statstabs-2")
                #boxplot_container = HT.Paragraph()
                #boxplot = HT.TableLite(cellspacing=0, cellpadding=0, width="100%")
                #boxplot_img, boxplot_link = BasicStatisticsFunctions.plotBoxPlot(vals)
                #boxplot.append(HT.TR(HT.TD(boxplot_img, HT.P(), boxplot_link, align="left")))
                #boxplot_container.append(boxplot)
                #boxplot_div.append(boxplot_container)
                #stats_container.append(boxplot_div)


                #barName_div = HT.Div(id="statstabs-3")
                #barName_container = HT.Paragraph()
                #barName = HT.TableLite(cellspacing=0, cellpadding=0, width="100%")
                #barName_img = BasicStatisticsFunctions.plotBarGraph(identification=fd.identification, RISet=fd.RISet, vals=vals, type="name")
                #barName.append(HT.TR(HT.TD(barName_img)))
                #barName_container.append(barName)
                #barName_div.append(barName_container)
                #stats_container.append(barName_div)
                #
                #barRank_div = HT.Div(id="statstabs-4")
                #barRank_container = HT.Paragraph()
                #barRank = HT.TableLite(cellspacing=0, cellpadding=0, width="100%")
                #barRank_img = BasicStatisticsFunctions.plotBarGraph(identification=fd.identification, RISet=fd.RISet, vals=vals, type="rank")
                #barRank.append(HT.TR(HT.TD(barRank_img)))
                #barRank_container.append(barRank)
                #barRank_div.append(barRank_container)
                #stats_container.append(barRank_div)

        #    stats_cell.append(stats_container)
        #
        #stats_script.append(stats_script_text)
        #
        #submitTable = HT.TableLite(cellspacing=0, cellpadding=0, width="100%", Class="target2")
        #stats_row.append(stats_cell)

        #submitTable.append(stats_row)
        #submitTable.append(stats_script)

        #title2Body.append(submitTable)


    def build_correlation_tools(self, fd, this_trait):

        #species = webqtlDatabaseFunction.retrieveSpecies(cursor=self.cursor, RISet=fd.RISet)

        RISetgp = fd.RISet
        
        # We're checking a string here!
        assert isinstance(RISetgp, basestring), "We need a string type thing here"
        if RISetgp[:3] == 'BXD':
            RISetgp = 'BXD'

        if RISetgp:
            #sample_correlation = HT.Input(type='button',name='sample_corr', value=' Compute ', Class="button sample_corr")
            #lit_correlation = HT.Input(type='button',name='lit_corr', value=' Compute ', Class="button lit_corr")
            #tissue_correlation = HT.Input(type='button',name='tiss_corr', value=' Compute ', Class="button tiss_corr")
            #methodText = HT.Span("Calculate:", Class="ffl fwb fs12")
            #
            #databaseText = HT.Span("Database:", Class="ffl fwb fs12")
            #databaseMenu1 = HT.Select(name='database1')
            #databaseMenu2 = HT.Select(name='database2')
            #databaseMenu3 = HT.Select(name='database3')

            dataset_menu = []
            print("[tape4] webqtlConfig.PUBLICTHRESH:", webqtlConfig.PUBLICTHRESH)
            print("[tape4] type webqtlConfig.PUBLICTHRESH:", type(webqtlConfig.PUBLICTHRESH))
            self.cursor.execute('''SELECT PublishFreeze.FullName,PublishFreeze.Name FROM 
                    PublishFreeze,InbredSet WHERE PublishFreeze.InbredSetId = InbredSet.Id 
                    and InbredSet.Name = %s and PublishFreeze.public > %s''', 
                    (RISetgp, webqtlConfig.PUBLICTHRESH))
            for item in self.cursor.fetchall():
                dataset_menu.append(dict(tissue=None,
                                         datasets=[item]))

            self.cursor.execute('''SELECT GenoFreeze.FullName,GenoFreeze.Name FROM GenoFreeze,
                    InbredSet WHERE GenoFreeze.InbredSetId = InbredSet.Id and InbredSet.Name = 
                    %s and GenoFreeze.public > %s''', 
                    (RISetgp, webqtlConfig.PUBLICTHRESH))
            for item in self.cursor.fetchall():
                dataset_menu.append(dict(tissue=None,
                                    datasets=[item]))

            #03/09/2009: Xiaodong changed the SQL query to order by Name as requested by Rob.
            self.cursor.execute('SELECT Id, Name FROM Tissue order by Name')
            for item in self.cursor.fetchall():
                tissue_id, tissue_name = item
                #databaseMenuSub = HT.Optgroup(label = '%s ------' % tissue_name)
                #dataset_sub_menu = []
                print("phun9")
                self.cursor.execute('''SELECT ProbeSetFreeze.FullName,ProbeSetFreeze.Name FROM ProbeSetFreeze, ProbeFreeze,
                InbredSet WHERE ProbeSetFreeze.ProbeFreezeId = ProbeFreeze.Id and ProbeFreeze.TissueId = %s and
                ProbeSetFreeze.public > %s and ProbeFreeze.InbredSetId = InbredSet.Id and InbredSet.Name like %s
                order by ProbeSetFreeze.CreateTime desc, ProbeSetFreeze.AvgId ''',
                (tissue_id, webqtlConfig.PUBLICTHRESH, "%" + RISetgp + "%"))
                print("phun8")
                dataset_sub_menu = [item for item in self.cursor.fetchall() if item]
                #for item2 in self.cursor.fetchall():
                #    dataset_sub_menu.append(item2)
                if dataset_sub_menu:
                    dataset_menu.append(dict(tissue=tissue_name,
                                        datasets=dataset_sub_menu))
                    #    ("**heading**", tissue_name))
                    #dataset_menu.append(dataset_sub_menu)
            
            dataset_menu_selected = None
            if len(dataset_menu):
                if this_trait and this_trait.db:
                    dataset_menu_selected = this_trait.db.name

                #criteriaText = HT.Span("Return:", Class="ffl fwb fs12")

                #criteriaMenu1 = HT.Select(name='criteria1', selected='500', onMouseOver="if (NS4 || IE4) activateEl('criterias', event);")
                
                return_results_menu = (100, 200, 500, 1000, 2000, 5000, 10000, 15000, 20000)
                return_results_menu_selected = 500
                
                #criteriaMenu1.append(('top 100','100'))
                #criteriaMenu1.append(('top 200','200'))
                #criteriaMenu1.append(('top 500','500'))
                #criteriaMenu1.append(('top 1000','1000'))
                #criteriaMenu1.append(('top 2000','2000'))
                #criteriaMenu1.append(('top 5000','5000'))
                #criteriaMenu1.append(('top 10000','10000'))
                #criteriaMenu1.append(('top 15000','15000'))
                #criteriaMenu1.append(('top 20000','20000'))

                #self.MDPRow1 = HT.TR(Class='mdp1')
                #self.MDPRow2 = HT.TR(Class='mdp2')
                #self.MDPRow3 = HT.TR(Class='mdp3')

            #    correlationMenus1 = HT.TableLite(
            #            HT.TR(HT.TD(databaseText), HT.TD(databaseMenu1, colspan="3")),
            #            HT.TR(HT.TD(criteriaText), HT.TD(criteriaMenu1)),
            #        self.MDPRow1, cellspacing=0, width="619px", cellpadding=2)
            #    correlationMenus1.append(HT.Input(name='orderBy', value='2', type='hidden'))    # to replace the orderBy menu
            #    correlationMenus2 = HT.TableLite(
            #            HT.TR(HT.TD(databaseText), HT.TD(databaseMenu2, colspan="3")),
            #            HT.TR(HT.TD(criteriaText), HT.TD(criteriaMenu2)),
            #        self.MDPRow2, cellspacing=0, width="619px", cellpadding=2)
            #    correlationMenus2.append(HT.Input(name='orderBy', value='2', type='hidden'))
            #    correlationMenus3 = HT.TableLite(
            #            HT.TR(HT.TD(databaseText), HT.TD(databaseMenu3, colspan="3")),
            #            HT.TR(HT.TD(criteriaText), HT.TD(criteriaMenu3)),
            #        self.MDPRow3, cellspacing=0, width="619px", cellpadding=2)
            #    correlationMenus3.append(HT.Input(name='orderBy', value='2', type='hidden'))
            #
            #else:
            #    correlationMenus = ""


        #corr_row = HT.TR()
        #corr_container = HT.Div(id="corr_tabs", Class="ui-tabs")
        #
        #if (this_trait.db != None and this_trait.db.type =='ProbeSet'):
        #    corr_tab_list = [HT.Href(text='Sample r', url="#corrtabs-1"),
        #                     HT.Href(text='Literature r',  url="#corrtabs-2"),
        #                     HT.Href(text='Tissue r', url="#corrtabs-3")]
        #else:
        #    corr_tab_list = [HT.Href(text='Sample r', url="#corrtabs-1")]
        #
        #corr_tabs = HT.List(corr_tab_list)
        #corr_container.append(corr_tabs)

        #if correlationMenus1 or correlationMenus2 or correlationMenus3:
            #sample_div = HT.Div(id="corrtabs-1")
            #sample_container = HT.Span()
            #
            #sample_type = HT.Input(type="radio", name="sample_method", value="1", checked="checked")
            #sample_type2 = HT.Input(type="radio", name="sample_method", value="2")
            #
            #sampleTable = HT.TableLite(cellspacing=0, cellpadding=0, width="100%")
            #sampleTD = HT.TD(correlationMenus1, HT.BR(),
            #                           "Pearson", sample_type, "&nbsp;"*3, "Spearman Rank", sample_type2, HT.BR(), HT.BR(),
            #                           sample_correlation, HT.BR(), HT.BR())
            #
            #sampleTD.append(HT.Span("The ",
            #                        HT.Href(url="/correlationAnnotation.html#sample_r", target="_blank",
            #                                text="Sample Correlation")," is computed between trait data and",
            #                            " any ",HT.BR()," other traits in the sample database selected above. Use ",
            #                            HT.Href(url="/glossary.html#Correlations", target="_blank", text="Spearman Rank"),
            #                            HT.BR(),"when the sample size is small (<20) or when there are influential \
            #                            outliers.", HT.BR(),Class="fs12"))

            #sampleTable.append(sampleTD)

            #sample_container.append(sampleTable)
            #sample_div.append(sample_container)
            #corr_container.append(sample_div)
            #
            #literature_div = HT.Div(id="corrtabs-2")
            #literature_container = HT.Span()

            #literatureTable = HT.TableLite(cellspacing=0, cellpadding=0, width="100%")
            #literatureTD = HT.TD(correlationMenus2,HT.BR(),lit_correlation, HT.BR(), HT.BR())
            #literatureTD.append(HT.Span("The ", HT.Href(url="/correlationAnnotation.html", target="_blank",text="Literature Correlation"), " (Lit r) between this gene and all other genes is computed",HT.BR(),
            #                            "using the ", HT.Href(url="https://grits.eecs.utk.edu/sgo/sgo.html", target="_blank", text="Semantic Gene Organizer"),
            #                            " and human, rat, and mouse data from PubMed. ", HT.BR(),"Values are ranked by Lit r, \
            #                            but Sample r and Tissue r are also displayed.", HT.BR(), HT.BR(),
            #                            HT.Href(url="/glossary.html#Literature", target="_blank", text="More on using Lit r"), Class="fs12"))
            #literatureTable.append(literatureTD)
            #
            #literature_container.append(literatureTable)
            #literature_div.append(literature_container)
            #
            #if this_trait.db != None:
            #    if (this_trait.db.type =='ProbeSet'):
            #        corr_container.append(literature_div)
            #
            #tissue_div = HT.Div(id="corrtabs-3")
            #tissue_container = HT.Span()
            #
            #tissue_type = HT.Input(type="radio", name="tissue_method", value="4", checked="checked")
            #tissue_type2 = HT.Input(type="radio", name="tissue_method", value="5")
            #
            #tissueTable = HT.TableLite(cellspacing=0, cellpadding=0, width="100%")
            #tissueTD = HT.TD(correlationMenus3,HT.BR(),
            #                           "Pearson", tissue_type, "&nbsp;"*3, "Spearman Rank", tissue_type2, HT.BR(), HT.BR(),
            #                           tissue_correlation, HT.BR(), HT.BR())
            #tissueTD.append(HT.Span("The ", HT.Href(url="/webqtl/main.py?FormID=tissueCorrelation", target="_blank", text="Tissue Correlation"),
            #" (Tissue r) estimates the similarity of expression of two genes",HT.BR()," or \
            #transcripts across different cells, tissues, or organs (",HT.Href(url="/correlationAnnotation.html#tissue_r", target="_blank", text="glossary"),"). \
            #Tissue correlations",HT.BR()," are generated by analyzing expression in multiple samples usually taken from \
            #single cases.",HT.BR(),HT.Bold("Pearson")," and ",HT.Bold("Spearman Rank")," correlations have been computed for all pairs \
            #of genes",HT.BR()," using data from mouse samples.",
            #HT.BR(), Class="fs12"))
            #tissueTable.append(tissueTD)
            #
            #tissue_container.append(tissueTable)
            #tissue_div.append(tissue_container)
            #if this_trait.db != None:
            #    if (this_trait.db.type =='ProbeSet'):
            #        corr_container.append(tissue_div)
            #
            #corr_row.append(HT.TD(corr_container))
            #
            #corr_script = HT.Script(language="Javascript")
            #corr_script_text = """$(function() { $("#corr_tabs").tabs(); });"""
            #corr_script.append(corr_script_text)
            #
            #submitTable = HT.TableLite(cellspacing=0, cellpadding=0, width="100%", Class="target4")
            #submitTable.append(corr_row)
            #submitTable.append(corr_script)
            #
            #title3Body.append(submitTable)
            self.corr_tools = dict(dataset_menu = dataset_menu,
                                          dataset_menu_selected = dataset_menu_selected,
                                          return_results_menu = return_results_menu,
                                          return_results_menu_selected = return_results_menu_selected,)


    def dispMappingTools(self, fd, title4Body, this_trait):

        _Species = webqtlDatabaseFunction.retrieveSpecies(cursor=self.cursor, RISet=fd.RISet)

        RISetgp = fd.RISet
        if RISetgp[:3] == 'BXD':
            RISetgp = 'BXD'

        #check boxes - one for regular interval mapping, the other for composite
        permCheck1= HT.Input(type='checkbox', Class='checkbox', name='permCheck1',checked="on")
        bootCheck1= HT.Input(type='checkbox', Class='checkbox', name='bootCheck1',checked=0)
        permCheck2= HT.Input(type='checkbox', Class='checkbox', name='permCheck2',checked="on")
        bootCheck2= HT.Input(type='checkbox', Class='checkbox', name='bootCheck2',checked=0)
        optionbox1 = HT.Input(type='checkbox', Class='checkbox', name='parentsf14regression1',checked=0)
        optionbox2 = HT.Input(type='checkbox', Class='checkbox', name='parentsf14regression2',checked=0)
        optionbox3 = HT.Input(type='checkbox', Class='checkbox', name='parentsf14regression3',checked=0)
        applyVariance1 = HT.Input(name='applyVarianceSE1',type='checkbox', Class='checkbox')
        applyVariance2 = HT.Input(name='applyVarianceSE2',type='checkbox', Class='checkbox')

        IntervalMappingButton=HT.Input(type='button' ,name='interval',value=' Compute ', Class="button")
        CompositeMappingButton=HT.Input(type='button' ,name='composite',value=' Compute ', Class="button")
        MarkerRegressionButton=HT.Input(type='button',name='marker', value=' Compute ', Class="button")

        chrText = HT.Span("Chromosome:", Class="ffl fwb fs12")

        # updated by NL 5-28-2010
        # Interval Mapping
        chrMenu = HT.Select(name='chromosomes1')
        chrMenu.append(("All",-1))
        for i in range(len(fd.genotype)):
            if len(fd.genotype[i]) > 1:
                chrMenu.append((fd.genotype[i].name, i))

        #Menu for Composite Interval Mapping
        chrMenu2 = HT.Select(name='chromosomes2')
        chrMenu2.append(("All",-1))
        for i in range(len(fd.genotype)):
            if len(fd.genotype[i]) > 1:
                chrMenu2.append((fd.genotype[i].name, i))

        if fd.genotype.Mbmap:
            scaleText = HT.Span("Mapping Scale:", Class="ffl fwb fs12")
            scaleMenu1 = HT.Select(name='scale1',
                                   onChange="checkUncheck(window.document.dataInput.scale1.value, window.document.dataInput.permCheck1, window.document.dataInput.bootCheck1)")
            scaleMenu1.append(("Megabase",'physic'))
            scaleMenu1.append(("Centimorgan",'morgan'))
            scaleMenu2 = HT.Select(name='scale2',
                                   onChange="checkUncheck(window.document.dataInput.scale2.value, window.document.dataInput.permCheck2, window.document.dataInput.bootCheck2)")
            scaleMenu2.append(("Megabase",'physic'))
            scaleMenu2.append(("Centimorgan",'morgan'))

        controlText = HT.Span("Control Locus:", Class="ffl fwb fs12")
        controlMenu = HT.Input(type="text", name="controlLocus", Class="controlLocus")

        if fd.genotype.Mbmap:
            intMappingMenu = HT.TableLite(
                    HT.TR(HT.TD(chrText), HT.TD(chrMenu, colspan="3")),
                    HT.TR(HT.TD(scaleText), HT.TD(scaleMenu1)),
                cellspacing=0, width="263px", cellpadding=2)
            compMappingMenu = HT.TableLite(
                    HT.TR(HT.TD(chrText), HT.TD(chrMenu2, colspan="3")),
                    HT.TR(HT.TD(scaleText), HT.TD(scaleMenu2)),
                    HT.TR(HT.TD(controlText), HT.TD(controlMenu)),
                cellspacing=0, width="325px", cellpadding=2)
        else:
            intMappingMenu = HT.TableLite(
                    HT.TR(HT.TD(chrText), HT.TD(chrMenu, colspan="3")),
                cellspacing=0, width="263px", cellpadding=2)
            compMappingMenu = HT.TableLite(
                    HT.TR(HT.TD(chrText), HT.TD(chrMenu2, colspan="3")),
                    HT.TR(HT.TD(controlText), HT.TD(controlMenu)),
                cellspacing=0, width="325px", cellpadding=2)

        directPlotButton = ""
        directPlotButton = HT.Input(type='button',name='', value=' Compute ',\
                onClick="dataEditingFunc(this.form,'directPlot');",Class="button")
        directPlotSortText = HT.Span(HT.Bold("Sort by: "), Class="ffl fwb fs12")
        directPlotSortMenu = HT.Select(name='graphSort')
        directPlotSortMenu.append(('LRS Full',0))
        directPlotSortMenu.append(('LRS Interact',1))
        directPlotPermuText = HT.Span("Permutation Test (n=500)", Class="ffl fs12")
        directPlotPermu = HT.Input(type='checkbox', Class='checkbox',name='directPermuCheckbox', checked="on")
        pairScanReturnText = HT.Span(HT.Bold("Return: "), Class="ffl fwb fs12")
        pairScanReturnMenu = HT.Select(name='pairScanReturn')
        pairScanReturnMenu.append(('top 50','50'))
        pairScanReturnMenu.append(('top 100','100'))
        pairScanReturnMenu.append(('top 200','200'))
        pairScanReturnMenu.append(('top 500','500'))

        pairScanMenus = HT.TableLite(
                HT.TR(HT.TD(directPlotSortText), HT.TD(directPlotSortMenu)),
                HT.TR(HT.TD(pairScanReturnText), HT.TD(pairScanReturnMenu)),
                cellspacing=0, width="232px", cellpadding=2)

        markerSuggestiveText = HT.Span(HT.Bold("Display LRS greater than:"), Class="ffl fwb fs12")
        markerSuggestive = HT.Input(name='suggestive', size=5, maxlength=8)
        displayAllText = HT.Span(" Display all LRS ", Class="ffl fs12")
        displayAll = HT.Input(name='displayAllLRS', type="checkbox", Class='checkbox')
        useParentsText = HT.Span(" Use Parents ", Class="ffl fs12")
        useParents = optionbox2
        applyVarianceText = HT.Span(" Use Weighted ", Class="ffl fs12")

        markerMenu = HT.TableLite(
                HT.TR(HT.TD(markerSuggestiveText), HT.TD(markerSuggestive)),
                HT.TR(HT.TD(displayAll,displayAllText)),
                HT.TR(HT.TD(useParents,useParentsText)),
                HT.TR(HT.TD(applyVariance2,applyVarianceText)),
                cellspacing=0, width="263px", cellpadding=2)


        mapping_row = HT.TR()
        mapping_container = HT.Div(id="mapping_tabs", Class="ui-tabs")

        mapping_tab_list = [HT.Href(text="Interval", url="#mappingtabs-1"), HT.Href(text="Marker Regression", url="#mappingtabs-2"), HT.Href(text="Composite", url="#mappingtabs-3"), HT.Href(text="Pair-Scan", url="#mappingtabs-4")]
        mapping_tabs = HT.List(mapping_tab_list)
        mapping_container.append(mapping_tabs)

        interval_div = HT.Div(id="mappingtabs-1")
        interval_container = HT.Span()

        intervalTable = HT.TableLite(cellspacing=0, cellpadding=0, width="100%")
        intTD = HT.TD(valign="top",NOWRAP='ON', Class="fs12 fwn")
        intTD.append(intMappingMenu,HT.BR())

        intTD.append(permCheck1,'Permutation Test (n=2000)',HT.BR(),
                     bootCheck1,'Bootstrap Test (n=2000)', HT.BR(), optionbox1, 'Use Parents', HT.BR(),
                     applyVariance1,'Use Weighted', HT.BR(), HT.BR(),IntervalMappingButton, HT.BR(), HT.BR())
        intervalTable.append(HT.TR(intTD), HT.TR(HT.TD(HT.Span(HT.Href(url='/glossary.html#intmap', target='_blank', text='Interval Mapping'),
                ' computes linkage maps for the entire genome or single',HT.BR(),' chromosomes.',
                ' The ',HT.Href(url='/glossary.html#permutation', target='_blank', text='Permutation Test'),' estimates suggestive and significant ',HT.BR(),' linkage scores. \
                The ',HT.Href(url='/glossary.html#bootstrap', target='_blank', text='Bootstrap Test'), ' estimates the precision of the QTL location.'
                ,Class="fs12"), HT.BR(), valign="top")))

        interval_container.append(intervalTable)
        interval_div.append(interval_container)
        mapping_container.append(interval_div)

        # Marker Regression

        marker_div = HT.Div(id="mappingtabs-2")
        marker_container = HT.Span()

        markerTable = HT.TableLite(cellspacing=0, cellpadding=0, width="100%")
        markerTD = HT.TD(valign="top",NOWRAP='ON', Class="fs12 fwn")
        markerTD.append(markerMenu,HT.BR())

        markerTD.append(MarkerRegressionButton,HT.BR(),HT.BR())

        markerTable.append(HT.TR(markerTD),HT.TR(HT.TD(HT.Span(HT.Href(url='/glossary.html#',target='_blank',text='Marker regression'),
                ' computes and displays LRS values for individual markers.',HT.BR(),
                'This function also lists additive effects (phenotype units per allele) and', HT.BR(),
                'dominance deviations for some datasets.', HT.BR(),Class="fs12"), HT.BR(), valign="top")))

        marker_container.append(markerTable)
        marker_div.append(marker_container)
        mapping_container.append(marker_div)

        # Composite interval mapping
        composite_div = HT.Div(id="mappingtabs-3")
        composite_container = HT.Span()

        compositeTable = HT.TableLite(cellspacing=0, cellpadding=3, width="100%")
        compTD = HT.TD(valign="top",NOWRAP='ON', Class="fs12 fwn")
        compTD.append(compMappingMenu,HT.BR())

        compTD.append(permCheck2, 'Permutation Test (n=2000)',HT.BR(),
                     bootCheck2,'Bootstrap Test (n=2000)', HT.BR(),
                     optionbox3, 'Use Parents', HT.BR(), HT.BR(), CompositeMappingButton, HT.BR(), HT.BR())
        compositeTable.append(HT.TR(compTD), HT.TR(HT.TD(HT.Span(HT.Href(url='/glossary.html#Composite',target='_blank',text='Composite Interval Mapping'),
                " allows you to control for a single marker as",HT.BR()," a cofactor. ",
                "To find a control marker, run the ",HT.Bold("Marker Regression")," function."),
                HT.BR(), valign="top")))

        composite_container.append(compositeTable)
        composite_div.append(composite_container)
        mapping_container.append(composite_div)

        # Pair Scan

        pairscan_div = HT.Div(id="mappingtabs-4")
        pairscan_container = HT.Span()

        pairScanTable = HT.TableLite(cellspacing=0, cellpadding=0, width="100%")
        pairScanTD = HT.TD(NOWRAP='ON', Class="fs12 fwn")
        pairScanTD.append(pairScanMenus,HT.BR())
        pairScanTD.append(directPlotPermu, directPlotPermuText, HT.BR(), HT.BR(),
                                          directPlotButton,HT.BR(),HT.BR())
        pairScanTable.append(HT.TR(pairScanTD), HT.TR(HT.TD(HT.Span(HT.Href(url='/glossary.html#Pair_Scan', target="_blank", text='Pair-Scan'),
                ' searches for pairs of chromosomal regions that are',HT.BR(),
                'involved in two-locus epistatic interactions.'), HT.BR(), valign="top")))

        pairscan_container.append(pairScanTable)
        pairscan_div.append(pairscan_container)
        mapping_container.append(pairscan_div)

        mapping_row.append(HT.TD(mapping_container))

        # Treat Interval Mapping and Marker Regression and Pair Scan as a group for displaying
        #disable Interval Mapping and Marker Regression and Pair Scan for human and the dataset doesn't have genotype file
        mappingMethodId = webqtlDatabaseFunction.getMappingMethod(cursor=self.cursor, groupName=RISetgp)

        mapping_script = HT.Script(language="Javascript")
        mapping_script_text = """$(function() { $("#mapping_tabs").tabs(); });"""
        mapping_script.append(mapping_script_text)

        submitTable = HT.TableLite(cellspacing=0, cellpadding=0, width="100%", Class="target2")

        if not mappingMethodId:
            if int(mappingMethodId) == 1:
                submitTable.append(mapping_row)
                submitTable.append(mapping_script)
            elif int(mappingMethodId) == 4:
                # NL; 09-26-2011 testing for Human Genome Association function
                mapping_row=HT.TR()
                mapping_container = HT.Div(id="mapping_tabs", Class="ui-tabs")

                mapping_tab_list = [HT.Href(text="Genome Association", url="#mappingtabs-1")]
                mapping_tabs = HT.List(mapping_tab_list)
                mapping_container.append(mapping_tabs)

                # Genome Association
                markerSuggestiveText = HT.Span(HT.Bold("P Value:"), Class="ffl fwb fs12")

                markerSuggestive = HT.Input(name='pValue', value='0.001', size=10, maxlength=20,onClick="this.value='';",onBlur="if(this.value==''){this.value='0.001'};")
                markerMenu = HT.TableLite(HT.TR(HT.TD(markerSuggestiveText), HT.TD(markerSuggestive),HT.TD(HT.Italic('&nbsp;&nbsp;&nbsp;(e.g. 0.001 or 1e-3 or 1E-3 or 3)'))),cellspacing=0, width="400px", cellpadding=2)
                MarkerRegressionButton=HT.Input(type='button',name='computePlink', value='&nbsp;&nbsp;Compute Using PLINK&nbsp;&nbsp;', onClick= "validatePvalue(this.form);", Class="button")

                marker_div = HT.Div(id="mappingtabs-1")
                marker_container = HT.Span()
                markerTable = HT.TableLite(cellspacing=0, cellpadding=0, width="100%")
                markerTD = HT.TD(valign="top",NOWRAP='ON', Class="fs12 fwn")
                markerTD.append(markerMenu,HT.BR())
                markerTD.append(MarkerRegressionButton,HT.BR(),HT.BR())
                markerTable.append(HT.TR(markerTD))

                marker_container.append(markerTable)
                marker_div.append(marker_container)

                mapping_container.append(marker_div)
                mapping_row.append(HT.TD(mapping_container))
                submitTable.append(mapping_row)
                submitTable.append(mapping_script)
            else:
                submitTable.append(HT.TR(HT.TD(HT.Div(HT.Italic("mappingMethodId %s has not been implemented for this dataset yet." % mappingMethodId), id="mapping_tabs", Class="ui-tabs"))))
                submitTable.append(mapping_script)

        else:
            submitTable.append(HT.TR(HT.TD(HT.Div(HT.Italic("Mapping options are disabled for data not matched with genotypes."), id="mapping_tabs", Class="ui-tabs"))))
            submitTable.append(mapping_script)

        title4Body.append(submitTable)


    def make_sample_lists(self, fd, variance_data_page, this_trait):
        if fd.genotype.type == "riset":
            all_samples_ordered = fd.f1list + fd.samplelist
        else:
            all_samples_ordered = fd.f1list + fd.parlist + fd.samplelist
        
        #ZS: Id values for this trait's extra attributes;
        #used to create "Exclude" dropdown and query for attribute values and create
        self.cursor.execute("""SELECT CaseAttribute.Id, CaseAttribute.Name
                                        FROM CaseAttribute, CaseAttributeXRef
                                WHERE CaseAttributeXRef.ProbeSetFreezeId = %s AND
                                        CaseAttribute.Id = CaseAttributeXRef.CaseAttributeId
                                        group by CaseAttributeXRef.CaseAttributeId""",
                                        (str(this_trait.db.id),))
        
        

        for this_attr_name in attribute_names:
            # Todo: Needs testing still!
            self.cursor.execute("""SELECT DISTINCT CaseAttributeXRef.Value
                                            FROM CaseAttribute, CaseAttributeXRef
                                            WHERE CaseAttribute.Name = %s AND
                                    CaseAttributeXRef.CaseAttributeId = CaseAttribute.Id""",
                                    (this_attr_name,))
            
            distinct_values = self.cursor.fetchall()

        this_trait_samples = set(this_trait.data.keys())

        primary_sample_names = all_samples_ordered

        print("primary_samplelist is:", pf(primary_sample_names))

        primary_samples = SampleList(self.cursor,
                                        fd=fd,
                                        variance_data_page=variance_data_page,
                                        sample_names=primary_sample_names,
                                        this_trait=this_trait,
                                        samples='primary',
                                        header="%s Only" % (fd.RISet))


        other_sample_names = []
        for sample in this_trait.data.keys():
            print("hjk - sample is:", sample)
            if sample not in all_samples_ordered:
                all_samples_ordered.append(sample)
                other_sample_names.append(sample)

        if other_sample_names:
            unappended_par_f1 = fd.f1list + fd.parlist
            par_f1_samples = ["_2nd_" + sample for sample in unappended_par_f1]
            
            other_samples.sort() #Sort other samples
            other_samples = par_f1_samples + other_samples

            other_samples = SampleList(self.cursor,
                                            fd=fd,
                                            variance_data_page=variance_data_page,
                                            sample_names=other_sample_names,
                                            this_trait=this_trait,
                                            samples='other',
                                            header="Non-%s" % (fd.RISet))
            
            self.sample_groups = (primary_samples, other_samples)
        else:
            self.sample_groups = (primary_samples,)

        #TODO: Figure out why this if statement is written this way - Zach
        if (other_sample_names or (fd.f1list and this_trait.data.has_key(fd.f1list[0])) 
                or (fd.f1list and this_trait.data.has_key(fd.f1list[1]))):
            print("hjs")
            fd.allsamplelist = all_samples_ordered
        
        


class SampleList(list):
    def __init__(self,
                 cursor,
                 fd,
                 variance_data_page,
                 sample_names,
                 this_trait,
                 samples,
                 header):
        
        self.header = header
        
        
        
        self.calc_attributes()

        for counter, sample_name in enumerate(sample_names, 1):
            sample_name = sample_name.replace("_2nd_", "")

            #ZS - If there's no value for the sample/strain, create the sample object (so samples with no value are still displayed in the table)
            try:
                sample = this_trait.data[sample_name]
            except KeyError:
                print("No sample %s, let's create it now" % sample_name)
                sample = webqtlCaseData.webqtlCaseData(sample_name)
            
            #sampleNameAdd = ''
            #if fd.RISet == 'AXBXA' and sampleName in ('AXB18/19/20','AXB13/14','BXA8/17'):
            #    sampleNameAdd = HT.Href(url='/mouseCross.html#AXB/BXA', text=HT.Sup('#'), Class='fs12', target="_blank")
            sample.extra_info = {}
            if fd.RISet == 'AXBXA' and sample_name in ('AXB18/19/20','AXB13/14','BXA8/17'):   
                sample.extra_info['url'] = "/mouseCross.html#AXB/BXA"
                sample.extra_info['css_class'] = "fs12" 
                
            print("zyt - sampleNameOrig:", sampleNameOrig)
            print("  type of sample:", type(sample))

            if samples == 'primary':
                sample.this_id = "Primary_" + str(counter)
            else:
                sample.this_id = "Other_" + str(counter)

            #### For extra attribute columns; currently only used by two human datasets - Zach
            if this_trait and this_trait.db and this_trait.db.type == 'ProbeSet':
                self.get_extra_attribute_values(attribute_ids, this_trait, sample_name)
                self.append(sample)
            #table_body.append(table_row)

        self.do_outliers()
        #do_outliers(the_samples)
        print("*the_samples are [%i]: %s" % (len(self), pf(self)))
        for sample in self:
            print("apple:", type(sample), sample)
        #return the_samples


    def do_outliers(self):
        values = [sample.value for sample in self if sample.value != None]
        upper_bound, lower_bound = Plot.find_outliers(values)
        
        for sample in self:
            if sample.value:
                if upper_bound and sample.value > upper_bound:
                    sample.outlier = True
                elif lower_bound and sample.value < lower_bound:
                    sample.outlier = True
                else:
                    sample.outlier = False
                    
    def calc_attributes(self):
        """Finds which extra attributes apply to this dataset"""
        
        
        #ZS: Id and name values for this trait's extra attributes  
        self.cursor.execute('''SELECT CaseAttribute.Id, CaseAttribute.Name
                                        FROM CaseAttribute, CaseAttributeXRef
                                        WHERE CaseAttributeXRef.ProbeSetFreezeId = %s AND
                                            CaseAttribute.Id = CaseAttributeXRef.CaseAttributeId
                                                group by CaseAttributeXRef.CaseAttributeId''',
                                                (str(this_trait.db.id),))

        #self.attributes = {key, value in self.cursor.fetchall()}
        #self.attributes = OrderedDict(self.attributes.iteritems())
        
        self.attributes = {}
        for key, value in self.cursor.fetchall():
            self.attributes[key] = Bunch()
            self.attributes[key].name = value

            self.cursor.execute('''SELECT DISTINCT CaseAttributeXRef.Value
                            FROM CaseAttribute, CaseAttributeXRef
                            WHERE CaseAttribute.Name = %s AND
                                CaseAttributeXRef.CaseAttributeId = CaseAttribute.Id''', (value,))            

            self.attributes[key].distinct_values = self.cursor.fetchall()


		try:

			exclude_menu = HT.Select(name="exclude_menu")
			dropdown_menus = [] #ZS: list of dropdown menus with the distinct values of each attribute (contained in DIVs so the style parameter can be edited and they can be hidden) 

			for attribute in self.cursor.fetchall():
				attribute_ids.append(attribute[0])
				attribute_names.append(attribute[1])
			for this_attr_name in attribute_names:
				exclude_menu.append((this_attr_name.capitalize(), this_attr_name))
				self.cursor.execute("""SELECT DISTINCT CaseAttributeXRef.Value
								FROM CaseAttribute, CaseAttributeXRef
								WHERE CaseAttribute.Name = '%s' AND
									CaseAttributeXRef.CaseAttributeId = CaseAttribute.Id""" % (this_attr_name))
				try:
					distinct_values = self.cursor.fetchall()
					attr_value_menu_div = HT.Div(style="display:none;", Class="attribute_values") #container used to show/hide dropdown menus
					attr_value_menu = HT.Select(name=this_attr_name)
                    			attr_value_menu.append(("None", "show_all"))
					for value in distinct_values:
						attr_value_menu.append((str(value[0]), value[0]))
					attr_value_menu_div.append(attr_value_menu)
					dropdown_menus.append(attr_value_menu_div)
				except:
					pass
		except:
			pass

                    
    def get_extra_attribute_values(self):
        
        if len(attribute_ids) > 0:

            #ZS: Get StrainId value for the next query
            cursor.execute("""SELECT Strain.Id
                                            FROM Strain, StrainXRef, InbredSetd
                                            WHERE Strain.Name = '%s' and
                                                    StrainXRef.StrainId = Strain.Id and
                                                    InbredSet.Id = StrainXRef.InbredSetId and
                                                    InbredSet.Name = '%s'""" % (sampleName, fd.RISet))

            sample_id = cursor.fetchone()[0]

            attr_counter = 1 # This is needed so the javascript can know which attribute type to associate this value with for the exported excel sheet (each attribute type being a column).
            for attribute_id in attribute_ids:

                #ZS: Add extra case attribute values (if any)
                cursor.execute("""SELECT Value
                                                FROM CaseAttributeXRef
                                        WHERE ProbeSetFreezeId = '%s' AND
                                                StrainId = '%s' AND
                                                CaseAttributeId = '%s'
                                                        group by CaseAttributeXRef.CaseAttributeId""" % (this_trait.db.id, sample_id, str(attribute_id)))

                attributeValue = cursor.fetchone()[0] #Trait-specific attributes, if any

                #ZS: If it's an int, turn it into one for sorting (for example, 101 would be lower than 80 if they're strings instead of ints)
                try:
                    attributeValue = int(attributeValue)
                except ValueError:
                    pass

                span_Id = samples+"_attribute"+str(attr_counter)+"_sample"+str(i+1)
                attr_container = HT.Span(attributeValue, Id=span_Id)
                attr_className = str(attributeValue) + "&nbsp;" + className
                table_row.append(HT.TD(attr_container, align='right', Class=attr_className))
                attr_counter += 1                    
