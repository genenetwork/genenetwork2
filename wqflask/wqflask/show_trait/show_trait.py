from __future__ import absolute_import, print_function, division

import string
import os
import cPickle
import uuid
#import pyXLWriter as xl

from collections import OrderedDict

from flask import Flask, g

from htmlgen import HTMLgen2 as HT

from base import webqtlConfig
from base import webqtlCaseData
from wqflask.show_trait.SampleList import SampleList
from utility import webqtlUtil, Plot, Bunch, helper_functions
from base.trait import GeneralTrait
from base import data_set
from dbFunction import webqtlDatabaseFunction
from basicStatistics import BasicStatisticsFunctions

from pprint import pformat as pf

###############################################
#
# Todo: Put in security to ensure that user has permission to access confidential data sets
# And add i.p.limiting as necessary
#
##############################################



class ShowTrait(object):

    def __init__(self, kw):
        print("in ShowTrait, kw are:", kw)
        
        if kw['trait_id'] != None:
            self.temp_trait = False
            self.trait_id = kw['trait_id']
            helper_functions.get_species_dataset_trait(self, kw)
        else:
            self.temp_trait = True
            self.create_temp_trait()

        #self.dataset.group.read_genotype_file()

        # Todo: Add back in the ones we actually need from below, as we discover we need them
        hddn = OrderedDict()

        ## Some fields, like method, are defaulted to None; otherwise in IE the field can't be changed using jquery
        #hddn = OrderedDict(
        #        FormID = fmID,
        #        group = fd.group,
        #        submitID = '',
        #        scale = 'physic',
        #        additiveCheck = 'ON',
        #        showSNP = 'ON',
        #        showGenes = 'ON',
        #        method = None,
        #        parentsf14regression = 'OFF',
        #        stats_method = '1',
        #        chromosomes = '-1',
        #        topten = '',
        #        viewLegend = 'ON',
        #        intervalAnalystCheck = 'ON',
        #        valsHidden = 'OFF',
        #        database = '',
        #        criteria = None,
        #        MDPChoice = None,
        #        bootCheck = None,
        #        permCheck = None,
        #        applyVarianceSE = None,
        #        sampleNames = '_',
        #        sampleVals = '_',
        #        sampleVars = '_',
        #        otherStrainNames = '_',
        #        otherStrainVals = '_',
        #        otherStrainVars = '_',
        #        extra_attributes = '_',
        #        other_extra_attributes = '_',
        #        export_data = None
        #        )

        #if this_trait:
        #    if this_trait.dataset and this_trait.dataset.type and this_trait.dataset.type == 'ProbeSet':
        #            self.cursor.execute("SELECT h2 from ProbeSetXRef WHERE DataId = %d" %
        #                                this_trait.mysqlid)
        #            heritability = self.cursor.fetchone()

        self.dispTraitInformation(kw, "", hddn, self.this_trait) #Display trait information + function buttons

        self.build_correlation_tools(self.this_trait)

        #Get nearest marker for composite mapping

        print("self.dataset.type:", self.dataset.type)
        if hasattr(self.this_trait, 'locus_chr') and self.this_trait.locus_chr != "" and self.dataset.type != "Geno" and self.dataset.type != "Publish":
            self.nearest_marker1 = get_nearest_marker(self.this_trait, self.dataset)[0]
            self.nearest_marker2 = get_nearest_marker(self.this_trait, self.dataset)[1]
        else:
            self.nearest_marker1 = ""
            self.nearest_marker2 = ""

        self.make_sample_lists(self.this_trait)

        if self.dataset.group.allsamples:
            hddn['allsamples'] = string.join(self.dataset.group.allsamples, ' ')

        hddn['trait_id'] = self.trait_id
        hddn['dataset'] = self.dataset.name
        hddn['use_outliers'] = False
        hddn['method'] = "pylmm"
        hddn['mapping_display_all'] = True
        hddn['suggestive'] = 0
        hddn['num_perm'] = 0
        hddn['manhattan_plot'] = False
        if hasattr(self.this_trait, 'locus_chr') and self.this_trait.locus_chr != "" and self.dataset.type != "Geno" and self.dataset.type != "Publish":
            hddn['control_marker'] = self.nearest_marker1+","+self.nearest_marker2
        else:
            hddn['control_marker'] = ""
        hddn['maf'] = 0.01
        hddn['compare_traits'] = []
    
        # We'll need access to this_trait and hddn in the Jinja2 Template, so we put it inside self
        self.hddn = hddn
        
        self.temp_uuid = uuid.uuid4()

        self.sample_group_types = OrderedDict()
        self.sample_group_types['samples_primary'] = self.dataset.group.name + " Only"
        self.sample_group_types['samples_other'] = "Non-" + self.dataset.group.name
        self.sample_group_types['samples_all'] = "All Cases"
        sample_lists = [group.sample_list for group in self.sample_groups]
        print("sample_lists is:", pf(sample_lists))
        
        probability_plot_data = []
        sample_vals = []
        sample_z_scores = []
        for sample_list in sample_lists:
            for sample in sample_list:
                sample_vals.append(sample.prob_plot_value)
                sample_z_scores.append(sample.z_score)
        probability_plot_data.append(sample_z_scores)        
        probability_plot_data.append(sample_vals)

        
        js_data = dict(sample_group_types = self.sample_group_types,
                        sample_lists = sample_lists,
                        probability_plot_data = probability_plot_data,
                        attribute_names = self.sample_groups[0].attributes,
                        temp_uuid = self.temp_uuid)
        self.js_data = js_data

    def read_data(self, include_f1=False):
        '''read user input data or from trait data and analysis form'''

        #if incf1 == None:
        #    incf1 = []

        #if not self.genotype:
        #    self.dataset.read_genotype_file()
        if not samplelist:
            if include_f1:
                samplelist = self.f1list + self.samplelist
            else:
                samplelist = self.samplelist

        traitfiledata = getattr(self, "traitfile", None)
        traitpastedata = getattr(self, "traitpaste", None)
        variancefiledata = getattr(self, "variancefile", None)
        variancepastedata = getattr(self, "variancepaste", None)
        Nfiledata = getattr(self, "Nfile", None)

        #### Todo: Rewrite below when we get to someone submitting their own trait #####

        def to_float(item):
            try:
                return float(item)
            except ValueError:
                return None

        print("bottle samplelist is:", samplelist)
        if traitfiledata:
            tt = traitfiledata.split()
            values = map(webqtlUtil.StringAsFloat, tt)
        elif traitpastedata:
            tt = traitpastedata.split()
            values = map(webqtlUtil.StringAsFloat, tt)
        else:
            print("mapping formdataasfloat")
            #values = map(self.FormDataAsFloat, samplelist)
            values = [to_float(getattr(self, key)) for key in samplelist]
        print("rocket values is:", values)


        if len(values) < len(samplelist):
            values += [None] * (len(samplelist) - len(values))
        elif len(values) > len(samplelist):
            values = values[:len(samplelist)]
        print("now values is:", values)


        if variancefiledata:
            tt = variancefiledata.split()
            variances = map(webqtlUtil.StringAsFloat, tt)
        elif variancepastedata:
            tt = variancepastedata.split()
            variances = map(webqtlUtil.StringAsFloat, tt)
        else:
            variances = map(self.FormVarianceAsFloat, samplelist)

        if len(variances) < len(samplelist):
            variances += [None]*(len(samplelist) - len(variances))
        elif len(variances) > len(samplelist):
            variances = variances[:len(samplelist)]

        if Nfiledata:
            tt = string.split(Nfiledata)
            nsamples = map(webqtlUtil.IntAsFloat, tt)
            if len(nsamples) < len(samplelist):
                nsamples += [None]*(len(samplelist) - len(nsamples))
        else:
            nsamples = map(self.FormNAsFloat, samplelist)

        ##values, variances, nsamples is obsolete
        self.allTraitData = {}
        for i, _sample in enumerate(samplelist):
            if values[i] != None:
                self.allTraitData[_sample] = webqtlCaseData(
                    _sample, values[i], variances[i], nsamples[i])
        print("allTraitData is:", pf(self.allTraitData))
        

    def dispTraitInformation(self, args, title1Body, hddn, this_trait):

        _Species = webqtlDatabaseFunction.retrieve_species(group=self.dataset.group.name)

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

        #if webqtlConfig.USERDICT[self.privilege] >= webqtlConfig.USERDICT['user']:
        #
        #    if this_trait==None or this_trait.dataset.type=='Temp':
        #        updateButton = HT.Href(url="#redirect", onClick="dataEditingFunc(document.getElementsByName('dataInput')[0],'addPublish');")
        #        updateButton_img = HT.Image("/images/edit_icon.jpg", name="addnew", alt="Add To Publish", title="Add To Publish", style="border:none;")
        #        updateButton.append(updateButton_img)
        #        updateText = "Edit"
        #    elif this_trait.dataset.type != 'Temp':
        #        if this_trait.dataset.type == 'Publish' and this_trait.confidential: #XZ: confidential phenotype trait
        #            if webqtlUtil.hasAccessToConfidentialPhenotypeTrait(privilege=self.privilege, userName=self.userName, authorized_users=this_trait.authorized_users):
        #                updateButton = HT.Href(url="#redirect", onClick="dataEditingFunc(document.getElementsByName('dataInput')[0],'updateRecord');")
        #                updateButton_img = HT.Image("/images/edit_icon.jpg", name="update", alt="Edit", title="Edit", style="border:none;")
        #                updateButton.append(updateButton_img)
        #                updateText = "Edit"
        #        else:
        #            updateButton = HT.Href(url="#redirect", onClick="dataEditingFunc(document.getElementsByName('dataInput')[0],'updateRecord');")
        #            updateButton_img = HT.Image("/images/edit_icon.jpg", name="update", alt="Edit", title="Edit", style="border:none;")
        #            updateButton.append(updateButton_img)
        #            updateText = "Edit"
        #    else:
        #        pass

        g.db.execute("SELECT Name FROM InbredSet WHERE Name=%s", self.dataset.group.name)
        if this_trait:
            addSelectionButton = HT.Href(url="#redirect", onClick="addRmvSelection('%s', document.getElementsByName('%s')[0], 'addToSelection');" % (self.dataset.group.name, 'dataInput'))
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
        if this_trait and this_trait.dataset and this_trait.dataset.type == 'ProbeSet': #before, this line was only reached if this_trait != 0, but now we need to check
            try:
                hddn['GeneId'] = int(string.strip(this_trait.geneid))
            except:
                pass

            #Info2Disp = HT.Paragraph()

            #XZ: Gene Symbol
            if this_trait.symbol:
                #XZ: Show SNP Browser only for mouse
                if _Species == 'mouse':
                    geneName = g.db.execute("SELECT geneSymbol FROM GeneList WHERE geneSymbol = %s", this_trait.symbol).fetchone()
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
                        snpBrowserText = "SNPs"

                #XZ: Show GeneWiki for all species
                geneWikiButton = HT.Href(url="#redirect", onClick="openNewWin('%s')" % (os.path.join(webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE) + "?FormID=geneWiki&symbol=%s" % this_trait.symbol))
                geneWikiButton_img = HT.Image("/images/genewiki_icon.jpg", name="genewiki", alt=" Write or review comments about this gene ", title=" Write or review comments about this gene ", style="border:none;")
                geneWikiText = 'GeneWiki'

                #XZ: display similar traits in other selected datasets
                if this_trait and this_trait.dataset and this_trait.dataset.type=="ProbeSet" and this_trait.symbol:
                    if _Species in ("mouse", "rat", "human"):
                        similarUrl = "%s?cmd=sch&gene=%s&alias=1&species=%s" % (os.path.join(webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE), this_trait.symbol, _Species)
                        similarButton = HT.Href(url="#redirect", onClick="openNewWin('%s')" % similarUrl)
                        similarButton_img = HT.Image("/images/find_icon.jpg", name="similar", alt=" Find similar expression data ", title=" Find similar expression data ", style="border:none;")
                        similarText = "Find"
                else:
                    pass
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
                                                 Probe.ProbeSetId = ProbeSet.Id order by Probe.SerialOrder""" % (this_trait.dataset.name, this_trait.name) )
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
                                             Probe.ProbeSetId = ProbeSet.Id order by Probe.SerialOrder""" % (this_trait.dataset.name, this_trait.name) )

                seqs = self.cursor.fetchall()
                for seqt in seqs:
                    if int(seqt[1][-1]) %2 == 1:
                        blatsequence += '%3EProbe_'+string.strip(seqt[1])+'%0A'+string.strip(seqt[0])+'%0A'

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
            if this_trait.dataset.name.find('Liver') >= 0 and this_trait.dataset.name.find('F2') < 0:
                pass
            else:
                query = """SELECT count(*)
                           FROM Probe, ProbeSet
                           WHERE ProbeSet.Name = '%s' AND Probe.ProbeSetId = ProbeSet.Id""" % (this_trait.name)
                #query database for number of probes associated with trait; if count > 0, set probe tool button and text
                probeResult = g.db.execute(query).fetchone()
                if probeResult[0] > 0:
                    probeurl = "%s?FormID=showProbeInfo&database=%s&ProbeSetID=%s&CellID=%s&group=%s&incparentsf1=ON" \
                            % (os.path.join(webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE), this_trait.dataset, this_trait.name, this_trait.cellid, self.dataset.group.name)
                    probeButton = HT.Href(url="#", onClick="javascript:openNewWin('%s'); return false;" % probeurl)
                    probeButton_img = HT.Image("/images/probe_icon.jpg", name="probe", alt=" Check sequence of probes ", title=" Check sequence of probes ", style="border:none;")
                    #probeButton.append(probeButton_img)
                    probeText = "Probes"

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
                    #try:
                    print("this_trait.symbol:", this_trait.symbol)
                    result = g.db.execute("SELECT chromosome,txStart,txEnd FROM GeneList WHERE geneSymbol = %s", (this_trait.symbol)).fetchone()
                    if result != None:
                        this_chr, txst, txen = result[0], result[1], result[2]
                    #this_chr, txst, txen = g.db.execute("SELECT chromosome,txStart,txEnd FROM GeneList WHERE geneSymbol = %s", (this_trait.symbol)).fetchone()
                        if this_chr and txst and txen and this_trait.refseq_transcriptid :
                            txst = int(txst*1000000)
                            txen = int(txen*1000000)
                        #tSpan.append(HT.Span(HT.Href(text= 'UCSC',target="mainFrame",\
                        #        title= 'Info from UCSC Genome Browser', url = webqtlConfig.UCSC_REFSEQ % ('mm9',
                        #                                                                                  this_trait.refseq_transcriptid,
                        #                                                                                  this_chr,
                        #                                                                                  txst,
                        #                                                                                  txen),
                        #        Class="fs14 fwn"), style=linkStyle)
                        #        , "&nbsp;"*2)
                        
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

            #for zhou mi's cliques, need to be removed
            #if self.database[:6]  == 'BXDMic' and self.ProbeSetID in cliqueID:
            #       Info2Disp.append(HT.Strong('Clique Search: '),HT.Href(text='Search',\
            #               url ="http://compbio1.utmem.edu/clique_go/results.php?pid=%s&pval_1=0&pval_2=0.001" \
            #               % self.ProbeSetID,target='_blank',Class="normalsize"),HT.BR())

        elif this_trait and this_trait.dataset and this_trait.dataset.type =='Publish': #Check if trait is phenotype

            #if this_trait.confidential:
            #    pass
            #    #tbl.append(HT.TR(
            #    #                HT.TD('Pre-publication Phenotype: ', Class="fs13 fwb", valign="top", nowrap="on", width=90),
            #    #                HT.TD(width=10, valign="top"),
            #    #                HT.TD(HT.Span(this_trait.pre_publication_description, Class="fs13"), valign="top", width=740)
            #    #                ))
            #    if webqtlUtil.hasAccessToConfidentialPhenotypeTrait(privilege=self.privilege, userName=self.userName, authorized_users=this_trait.authorized_users):
            #        #tbl.append(HT.TR(
            #        #                HT.TD('Post-publication Phenotype: ', Class="fs13 fwb", valign="top", nowrap="on", width=90),
            #        #                HT.TD(width=10, valign="top"),
            #        #                HT.TD(HT.Span(this_trait.post_publication_description, Class="fs13"), valign="top", width=740)
            #        #                ))
            #        #tbl.append(HT.TR(
            #        #                HT.TD('Pre-publication Abbreviation: ', Class="fs13 fwb", valign="top", nowrap="on", width=90),
            #        #                HT.TD(width=10, valign="top"),
            #        #                HT.TD(HT.Span(this_trait.pre_publication_abbreviation, Class="fs13"), valign="top", width=740)
            #        #                ))
            #        #tbl.append(HT.TR(
            #        #                HT.TD('Post-publication Abbreviation: ', Class="fs13 fwb", valign="top", nowrap="on", width=90),
            #        #                HT.TD(width=10, valign="top"),
            #        #                HT.TD(HT.Span(this_trait.post_publication_abbreviation, Class="fs13"), valign="top", width=740)
            #        #                ))
            #        #tbl.append(HT.TR(
            #        #                HT.TD('Lab code: ', Class="fs13 fwb", valign="top", nowrap="on", width=90),
            #        #                HT.TD(width=10, valign="top"),
            #        #                HT.TD(HT.Span(this_trait.lab_code, Class="fs13"), valign="top", width=740)
            #        #                ))
            #        pass
            #    #tbl.append(HT.TR(
            #    #                HT.TD('Owner: ', Class="fs13 fwb", valign="top", nowrap="on", width=90),
            #    #                HT.TD(width=10, valign="top"),
            #    #                HT.TD(HT.Span(this_trait.owner, Class="fs13"), valign="top", width=740)
            #    #                ))
            #else:
            #    pass
            #    #tbl.append(HT.TR(
            #    #                HT.TD('Phenotype: ', Class="fs13 fwb", valign="top", nowrap="on", width=90),
            #    #                HT.TD(width=10, valign="top"),
            #    #                HT.TD(HT.Span(this_trait.post_publication_description, Class="fs13"), valign="top", width=740)
            #    #                ))
            ##tbl.append(HT.TR(
            ##                HT.TD('Authors: ', Class="fs13 fwb",
            ##                        valign="top", nowrap="on", width=90),
            ##                HT.TD(width=10, valign="top"),
            ##                HT.TD(HT.Span(this_trait.authors, Class="fs13"),
            ##                        valign="top", width=740)
            ##                ))
            ##tbl.append(HT.TR(
            ##                HT.TD('Title: ', Class="fs13 fwb",
            ##                        valign="top", nowrap="on", width=90),
            ##                HT.TD(width=10, valign="top"),
            ##                HT.TD(HT.Span(this_trait.title, Class="fs13"),
            ##                        valign="top", width=740)
            ##                ))
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

        elif this_trait and this_trait.dataset and this_trait.dataset.type == 'Geno': #Check if trait is genotype

            if this_trait.chr and this_trait.mb:
                location = ' Chr %s @ %s Mb' % (this_trait.chr,this_trait.mb)
            else:
                location = "not available"

            #if this_trait.sequence and len(this_trait.sequence) > 100:
            #    if _Species == "rat":
            #        UCSC_BLAT_URL = webqtlConfig.UCSC_BLAT % ('rat', 'rn3', this_trait.sequence)
            #        UTHSC_BLAT_URL = webqtlConfig.UTHSC_BLAT % ('rat', 'rn3', this_trait.sequence)
            #    elif _Species == "mouse":
            #        UCSC_BLAT_URL = webqtlConfig.UCSC_BLAT % ('mouse', 'mm9', this_trait.sequence)
            #        UTHSC_BLAT_URL = webqtlConfig.UTHSC_BLAT % ('mouse', 'mm9', this_trait.sequence)
            #    elif _Species == "human":
            #        UCSC_BLAT_URL = webqtlConfig.UCSC_BLAT % ('human', 'hg19', blatsequence)
            #        UTHSC_BLAT_URL = webqtlConfig.UTHSC_BLAT % ('human', 'hg19', this_trait.sequence)
            #    else:
            #        UCSC_BLAT_URL = ""
            #        UTHSC_BLAT_URL = ""
            #    if UCSC_BLAT_URL:
            #        #verifyButton = HT.Href(url="#", onClick="openNewWin('%s')" % UCSC_BLAT_URL)
            #        verifyButton = HT.Href(url="#")
            #        verifyButtonImg = HT.Image("/images/verify_icon.jpg", name="verify", alt=" Check probe locations at UCSC ", title=" Check probe locations at UCSC ", style="border:none;")
            #        verifyButton.append(verifyButtonImg)
            #        verifyText = "Verify"
            #        rnaseqButton = HT.Href(url="#", onClick="openNewWin('%s')" % UTHSC_BLAT_URL)
            #        rnaseqButtonImg = HT.Image("/images/rnaseq_icon.jpg", name="rnaseq", alt=" View probes, SNPs, and RNA-seq at UTHSC ", title=" View probes, SNPs, and RNA-seq at UTHSC ", style="border:none;")
            #        rnaseqButton.append(rnaseqButtonImg)
            #        rnaseqText = "RNA-seq"

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


    def dispBasicStatistics(self, fd, this_trait):

        #XZ, June 22, 2011: The definition and usage of primary_samples, other_samples, specialStrains, all_samples are not clear and hard to understand. But since they are only used in this function for draw graph purpose, they will not hurt the business logic outside. As of June 21, 2011, this function seems work fine, so no hurry to clean up. These parameters and code in this function should be cleaned along with fd.f1list, fd.parlist, fd.samplelist later.

        # This should still be riset here - Sam - Nov. 2012
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
            self.MDP_menu.append(('%s Only' % fd.group, '1'))
            self.MDP_menu.append(('Non-%s Only' % fd.group, '2'))

        else:
            if (len(other_samples) > 0) and (len(primary_samples) + len(other_samples) > 3):
                print("ac2")
                self.MDP_menu.append(('All Cases','0'))
                self.MDP_menu.append(('%s Only' % fd.group,'1'))
                self.MDP_menu.append(('Non-%s Only' % fd.group,'2'))
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

                vals1.append(thisValFull)

            #Using just the group sample
            for sampleNameOrig in primary_samples:
                sampleName = sampleNameOrig.replace("_2nd_", "")

                thisval = this_trait.data[sampleName].value
                thisvar = this_trait.data[sampleName].variance
                thisValFull = [sampleName,thisval,thisvar]

                vals2.append(thisValFull)

            #Using all non-group samples only
            for sampleNameOrig in other_samples:
                sampleName = sampleNameOrig.replace("_2nd_", "")

                thisval = this_trait.data[sampleName].value
                thisvar = this_trait.data[sampleName].variance
                thisValFull = [sampleName,thisval,thisvar]

                vals3.append(thisValFull)

            vals_set = [vals1,vals2,vals3]

        else:
            vals = []

            #Using all samples/cases for values
            for sampleNameOrig in all_samples:
                sampleName = sampleNameOrig.replace("_2nd_", "")

                thisval = this_trait.data[sampleName].value
                thisvar = this_trait.data[sampleName].variance
                thisValFull = [sampleName,thisval,thisvar]

                vals.append(thisValFull)

            vals_set = [vals]

        self.stats_data = []
        for i, vals in enumerate(vals_set):
            if i == 0 and len(vals) < 4:
                stats_container = HT.Div(id="stats_tabs", style="padding:10px;", Class="ui-tabs") #Needed for tabs; notice the "stats_script_text" below referring to this element
                stats_container.append(HT.Div(HT.Italic("Fewer than 4 case data were entered. No statistical analysis has been attempted.")))
                break
            elif (i == 1 and len(primary_samples) < 4):
                stats_container = HT.Div(id="stats_tabs%s" % i, Class="ui-tabs")
                #stats_container.append(HT.Div(HT.Italic("Fewer than 4 " + fd.group + " case data were entered. No statistical analysis has been attempted.")))
            elif (i == 2 and len(other_samples) < 4):
                stats_container = HT.Div(id="stats_tabs%s" % i, Class="ui-tabs")
                stats_container.append(HT.Div(HT.Italic("Fewer than 4 non-" + fd.group + " case data were entered. No statistical analysis has been attempted.")))
            else:
                continue
            if len(vals) > 4:
                stats_tab_list = [HT.Href(text="Basic Table", url="#statstabs-1", Class="stats_tab"),HT.Href(text="Probability Plot", url="#statstabs-5", Class="stats_tab"),
                                                  HT.Href(text="Bar Graph (by name)", url="#statstabs-3", Class="stats_tab"), HT.Href(text="Bar Graph (by rank)", url="#statstabs-4", Class="stats_tab"),
                                                  HT.Href(text="Box Plot", url="#statstabs-2", Class="stats_tab")]

                if this_trait.dataset:
                    if this_trait.cellid:
                        self.stats_data.append(BasicStatisticsFunctions.basicStatsTable(vals=vals, trait_type=this_trait.dataset.type, cellid=this_trait.cellid))
                    else:
                        self.stats_data.append(BasicStatisticsFunctions.basicStatsTable(vals=vals, trait_type=this_trait.dataset.type))
                else:
                    self.stats_data.append(BasicStatisticsFunctions.basicStatsTable(vals=vals))

                #normalplot_div = HT.Div(id="statstabs-5")
                #normalplot_container = HT.Paragraph()
                #normalplot = HT.TableLite(cellspacing=0, cellpadding=0, width="100%")

                try:
                    plotTitle = this_trait.symbol
                    plotTitle += ": "
                    plotTitle += this_trait.name
                except:
                    plotTitle = str(this_trait.name)

                    #normalplot_img = BasicStatisticsFunctions.plotNormalProbability(vals=vals, group=fd.group, title=plotTitle, specialStrains=specialStrains)
                    #normalplot.append(HT.TR(HT.TD(normalplot_img)))
                    #normalplot.append(HT.TR(HT.TD(HT.BR(),HT.BR(),"This plot evaluates whether data are \
                    #normally distributed. Different symbols represent different groups.",HT.BR(),HT.BR(),
                    #"More about ", HT.Href(url="http://en.wikipedia.org/wiki/Normal_probability_plot",
                    #                 target="_blank", text="Normal Probability Plots"), " and more about interpreting these plots from the ", HT.Href(url="/glossary.html#normal_probability", target="_blank", text="glossary"))))

                    #boxplot_div = HT.Div(id="statstabs-2")
                    #boxplot_container = HT.Paragraph()
                    #boxplot = HT.TableLite(cellspacing=0, cellpadding=0, width="100%")
                    #boxplot_img, boxplot_link = BasicStatisticsFunctions.plotBoxPlot(vals)
                    #boxplot.append(HT.TR(HT.TD(boxplot_img, HT.P(), boxplot_link, align="left")))

                    #barName_div = HT.Div(id="statstabs-3")
                    #barName_container = HT.Paragraph()
                    #barName = HT.TableLite(cellspacing=0, cellpadding=0, width="100%")
                    #barName_img = BasicStatisticsFunctions.plotBarGraph(identification=fd.identification, group=fd.group, vals=vals, type="name")

                    #barRank_div = HT.Div(id="statstabs-4")
                    #barRank_container = HT.Paragraph()
                    #barRank = HT.TableLite(cellspacing=0, cellpadding=0, width="100%")
                    #barRank_img = BasicStatisticsFunctions.plotBarGraph(identification=fd.identification, group=fd.group, vals=vals, type="rank")


    def build_correlation_tools(self, this_trait):

        #species = webqtlDatabaseFunction.retrieveSpecies(cursor=self.cursor, group=fd.group)

        this_group = self.dataset.group.name

        # We're checking a string here!
        assert isinstance(this_group, basestring), "We need a string type thing here"
        if this_group[:3] == 'BXD':
            this_group = 'BXD'

        if this_group:

            dataset_menu = []
            print("[tape4] webqtlConfig.PUBLICTHRESH:", webqtlConfig.PUBLICTHRESH)
            print("[tape4] type webqtlConfig.PUBLICTHRESH:", type(webqtlConfig.PUBLICTHRESH))
            results = g.db.execute("""SELECT PublishFreeze.FullName,PublishFreeze.Name FROM
                    PublishFreeze,InbredSet WHERE PublishFreeze.InbredSetId = InbredSet.Id
                    and InbredSet.Name = %s and PublishFreeze.public > %s""",
                    (this_group, webqtlConfig.PUBLICTHRESH))
            for item in results.fetchall():
                dataset_menu.append(dict(tissue=None,
                                         datasets=[item]))

            results = g.db.execute("""SELECT GenoFreeze.FullName,GenoFreeze.Name FROM GenoFreeze,
                    InbredSet WHERE GenoFreeze.InbredSetId = InbredSet.Id and InbredSet.Name =
                    %s and GenoFreeze.public > %s""",
                    (this_group, webqtlConfig.PUBLICTHRESH))
            for item in results.fetchall():
                dataset_menu.append(dict(tissue=None,
                                    datasets=[item]))

            #03/09/2009: Xiaodong changed the SQL query to order by Name as requested by Rob.
            tissues = g.db.execute("SELECT Id, Name FROM Tissue order by Name")
            for item in tissues.fetchall():
                tissue_id, tissue_name = item
                data_sets = g.db.execute('''SELECT ProbeSetFreeze.FullName,ProbeSetFreeze.Name FROM ProbeSetFreeze, ProbeFreeze,
                InbredSet WHERE ProbeSetFreeze.ProbeFreezeId = ProbeFreeze.Id and ProbeFreeze.TissueId = %s and
                ProbeSetFreeze.public > %s and ProbeFreeze.InbredSetId = InbredSet.Id and InbredSet.Name like %s
                order by ProbeSetFreeze.CreateTime desc, ProbeSetFreeze.AvgId ''',
                (tissue_id, webqtlConfig.PUBLICTHRESH, "%" + this_group + "%"))
                dataset_sub_menu = [item for item in data_sets.fetchall() if item]
                if dataset_sub_menu:
                    dataset_menu.append(dict(tissue=tissue_name,
                                        datasets=dataset_sub_menu))

            dataset_menu_selected = None
            if len(dataset_menu):
                if this_trait and this_trait.dataset:
                    dataset_menu_selected = this_trait.dataset.name

                return_results_menu = (100, 200, 500, 1000, 2000, 5000, 10000, 15000, 20000)
                return_results_menu_selected = 500

            self.corr_tools = dict(dataset_menu = dataset_menu,
                                          dataset_menu_selected = dataset_menu_selected,
                                          return_results_menu = return_results_menu,
                                          return_results_menu_selected = return_results_menu_selected,)


    def build_mapping_tools(self, this_trait):


        _Species = webqtlDatabaseFunction.retrieveSpecies(cursor=self.cursor, group=fd.group)

        this_group = fd.group
        if this_group[:3] == 'BXD':
            this_group = 'BXD'

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
        mappingMethodId = webqtlDatabaseFunction.getMappingMethod(cursor=self.cursor, groupName=this_group)

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


    def make_sample_lists(self, this_trait):
        if self.dataset.group.parlist:
            all_samples_ordered = (self.dataset.group.parlist +
                                   self.dataset.group.f1list +
                                   self.dataset.group.samplelist)
        elif self.dataset.group.f1list:
            all_samples_ordered = self.dataset.group.f1list + self.dataset.group.samplelist
        else:
            all_samples_ordered = self.dataset.group.samplelist

        this_trait_samples = set(this_trait.data.keys())

        primary_sample_names = all_samples_ordered

        print("self.dataset.group", pf(self.dataset.group.__dict__))
        print("-*- primary_samplelist is:", pf(primary_sample_names))

        other_sample_names = []
        for sample in this_trait.data.keys():
            if sample not in all_samples_ordered:
                all_samples_ordered.append(sample)
                other_sample_names.append(sample)

        other_sample_names, all_samples_ordered = get_samplelist_from_trait_data(this_trait,
                                                                                 all_samples_ordered)
        
        
        print("species:", self.dataset.group.species)
        if self.dataset.group.species == "human":
            primary_sample_names += other_sample_names
            
        primary_samples = SampleList(dataset = self.dataset,
                                        sample_names=primary_sample_names,
                                        this_trait=this_trait,
                                        sample_group_type='primary',
                                        header="%s Only" % (self.dataset.group.name))
        print("primary_samples is: ", pf(primary_samples))

        print("other_sample_names2:", other_sample_names)
        if other_sample_names and self.dataset.group.species != "human":
            parent_f1_samples = None
            if self.dataset.group.parlist and self.dataset.group.f1list:
                parent_f1_samples = self.dataset.group.parlist + self.dataset.group.f1list

            other_sample_names.sort() #Sort other samples
            if parent_f1_samples:
                other_sample_names = parent_f1_samples + other_sample_names

            print("other_sample_names:", other_sample_names)

            other_samples = SampleList(dataset=self.dataset,
                                        sample_names=other_sample_names,
                                        this_trait=this_trait,
                                        sample_group_type='other',
                                        header="Non-%s" % (self.dataset.group.name))

            self.sample_groups = (primary_samples, other_samples)
        else:
            self.sample_groups = (primary_samples,)

        #TODO: Figure out why this if statement is written this way - Zach
        #if (other_sample_names or (fd.f1list and this_trait.data.has_key(fd.f1list[0]))
        #        or (fd.f1list and this_trait.data.has_key(fd.f1list[1]))):
        #    print("hjs")
        self.dataset.group.allsamples = all_samples_ordered


def get_samplelist_from_trait_data(this_trait, all_samples_ordered):
    other_sample_names = []
    for sample in this_trait.data.keys():
        if sample not in all_samples_ordered:
            all_samples_ordered.append(sample)
            other_sample_names.append(sample)
            
    return other_sample_names, all_samples_ordered

def get_nearest_marker(this_trait, this_db):
    this_chr = this_trait.locus_chr
    print("this_chr:", this_chr)
    this_mb = this_trait.locus_mb
    print("this_mb:", this_mb)
    query = """SELECT Geno.Name
               FROM Geno, GenoXRef, GenoFreeze
               WHERE Geno.Chr = '{}' AND
                     GenoXRef.GenoId = Geno.Id AND
                     GenoFreeze.Id = GenoXRef.GenoFreezeId AND
                     GenoFreeze.Name = '{}'
               ORDER BY ABS( Geno.Mb - {}) LIMIT 2""".format(this_chr, this_db.group.name+"Geno", this_mb)
    print("query:", query)

    result = g.db.execute(query).fetchall()
    print("result:", result)

    if result == []:
        return "", ""
    else:
        return result[0][0], result[1][0]
    
    
