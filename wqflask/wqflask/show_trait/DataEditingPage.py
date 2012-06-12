import string
import os
import cPickle
from collections import OrderedDict
#import pyXLWriter as xl

from htmlgen import HTMLgen2 as HT

from base import webqtlConfig
from utility import webqtlUtil #, Plot
from base.webqtlTrait import webqtlTrait
from dbFunction import webqtlDatabaseFunction
from base.templatePage import templatePage
from basicStatistics import BasicStatisticsFunctions


#########################################
#      DataEditingPage
#########################################
class DataEditingPage(templatePage):

    def __init__(self, fd, thisTrait=None):

        templatePage.__init__(self, fd)

        #self.dict['title'] = 'Data Editing'
        #TD_LR = HT.TD(valign="top",width="100%",bgcolor="#fafafa")

        if not self.openMysql():
            return
        if not fd.genotype:
            fd.readData(incf1=1)

        #############################
        # determine data editing page format
        #############################
        varianceDataPage = 0
        if fd.formID == 'varianceChoice':
            varianceDataPage = 1

        if varianceDataPage:
            fmID='dataEditing'
            nCols = 6
        else:
            if fd.enablevariance:
                fmID='pre_dataEditing'
                nCols = 4
            else:
                fmID='dataEditing'
                nCols = 4

        #############################
        ##      titles, etc.
        #############################

        #titleTop = HT.Div()
        #
        #title1 = HT.Paragraph("&nbsp;&nbsp;Details and Links", style="border-radius: 5px;", Id="title1", Class="sectionheader")
        #title1Body = HT.Paragraph(Id="sectionbody1")
        #
        #if fd.enablevariance and not varianceDataPage:
        #       title2 = HT.Paragraph("&nbsp;&nbsp;Submit Variance", style="border-radius: 5px;", Id="title2", Class="sectionheader")
        #else:
        #       title2 = HT.Paragraph("&nbsp;&nbsp;Basic Statistics", style="border-radius: 5px;", Id="title2", Class="sectionheader")
        #title2Body = HT.Paragraph(Id="sectionbody2")
        #
        #title3 = HT.Paragraph("&nbsp;&nbsp;Calculate Correlations", style="border-radius: 5px;", Id="title3", Class="sectionheader")
        #title3Body = HT.Paragraph(Id="sectionbody3")
        #
        #title4 = HT.Paragraph("&nbsp;&nbsp;Mapping Tools", style="border-radius: 5px;", Id="title4", Class="sectionheader")
        #title4Body = HT.Paragraph(Id="sectionbody4")
        #
        #title5 = HT.Paragraph("&nbsp;&nbsp;Review and Edit Data", style="border-radius: 5px;", Id="title5", Class="sectionheader")
        #title5Body = HT.Paragraph(Id="sectionbody5")

        #############################
        ##     Hidden field
        #############################

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
                strainNames = '_',
                strainVals = '_',
                strainVars = '_',
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

        if thisTrait:
            hddn['fullname'] = str(thisTrait)
            try:
                hddn['normalPlotTitle'] = thisTrait.symbol
                hddn['normalPlotTitle'] += ": "
                hddn['normalPlotTitle'] += thisTrait.name
            except:
                hddn['normalPlotTitle'] = str(thisTrait.name)
            hddn['fromDataEditingPage'] = 1
            if thisTrait.db and thisTrait.db.type and thisTrait.db.type == 'ProbeSet':
                hddn['trait_type'] = thisTrait.db.type
                if thisTrait.cellid:
                    hddn['cellid'] = thisTrait.cellid
                else:
                    self.cursor.execute("SELECT h2 from ProbeSetXRef WHERE DataId = %d" % thisTrait.mysqlid)
                    heritability = self.cursor.fetchone()
                    hddn['heritability'] = heritability

                hddn['attribute_names'] = ""

        hddn['mappingMethodId'] = webqtlDatabaseFunction.getMappingMethod (cursor=self.cursor, groupName=fd.RISet)

        #############################
        ##  Display Trait Information
        #############################

        #headSpan = self.dispHeader(fd,thisTrait) #Draw header
        #
        #titleTop.append(headSpan)

        if fd.identification:
            hddn['identification'] = fd.identification

        else:
            hddn['identification'] = "Un-named trait"  #If no identification, set identification to un-named

        self.dispTraitInformation(fd, "", hddn, thisTrait) #Display trait information + function buttons

        #############################
        ##  Generate form and buttons
        #############################

        #mainForm = HT.Form(cgi= os.path.join(webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE),
        #    name='dataInput', submit=HT.Input(type='hidden'))

        #next=HT.Input(type='submit', name='submit',value='Next',Class="button")
        #reset=HT.Input(type='Reset',name='',value=' Reset ',Class="button")
        #correlationMenus = []

        if thisTrait == None:
            thisTrait = webqtlTrait(data=fd.allTraitData, db=None)

        # Variance submit page only
        if fd.enablevariance and not varianceDataPage:
            pass
            #title2Body.append("Click the next button to go to the variance submission form.",
            #        HT.Center(next,reset))
        else:
            pass
            # We'll get this part working later
            print("Calling dispBasicStatistics")
            self.dispBasicStatistics(fd, thisTrait)
            #self.dispMappingTools(fd, title4Body, thisTrait)

        #############################
        ##  Trait Value Table
        #############################
        #
        #self.dispTraitValues(fd, title5Body, varianceDataPage, nCols, mainForm, thisTrait)
        #
        if fd.allstrainlist:
            hddn['allstrainlist'] = string.join(fd.allstrainlist, ' ')

        # We put isSE into hddn
        if nCols == 6 and fd.varianceDispName != 'Variance':
            hddn['isSE'] = "yes"

        #for key in hddn.keys():
        #    mainForm.append(HT.Input(name=key, value=hddn[key], type='hidden'))
        #
        #if fd.enablevariance and not varianceDataPage:
        #    #pre dataediting page, need to submit variance
        #    mainForm.append(titleTop, title1,title1Body,title2,title2Body,title3,title3Body,title4,title4Body,title5,title5Body)
        #else:
        #    mainForm.append(titleTop, title1,title1Body,title2,title2Body,title3,title3Body,title4,title4Body,title5,title5Body)
        #TD_LR.append(HT.Paragraph(mainForm))
        #self.dict['body'] = str(TD_LR)

        # We'll need access to thisTrait and hddn uin the Jinja2 Template, so we put it inside self
        self.thisTrait = thisTrait
        self.hddn = hddn

    ##########################################
    ##  Function to display header
    ##########################################
    def dispHeader(self, fd, thisTrait):
        headSpan = HT.Div(style="font-size:14px;")

        #If trait, use trait name; otherwise, use identification value
        if thisTrait:
            if thisTrait.cellid:
                headSpan.append(HT.Strong('Trait Data and Analysis&nbsp;', style='font-size:16px;'),' for Probe ID ', thisTrait.cellid)
            else:
                headSpan.append(HT.Strong('Trait Data and Analysis&nbsp;', style='font-size:16px;'),' for Record ID ', thisTrait.name)
        else:
            if fd.identification:
                headSpan.append(HT.Strong('Trait ID ', style='font-size:16px;'),fd.identification)
            else:
                headSpan.append(HT.Strong('Un-named Trait', style='font-size:16px;'))

        return headSpan

    ##########################################
    ##  Function to display trait infos
    ##########################################
    def dispTraitInformation(self, fd, title1Body, hddn, thisTrait):

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

            if thisTrait==None or thisTrait.db.type=='Temp':
                updateButton = HT.Href(url="#redirect", onClick="dataEditingFunc(document.getElementsByName('dataInput')[0],'addPublish');")
                updateButton_img = HT.Image("/images/edit_icon.jpg", name="addnew", alt="Add To Publish", title="Add To Publish", style="border:none;")
                updateButton.append(updateButton_img)
                updateText = "Edit"
            elif thisTrait.db.type != 'Temp':
                if thisTrait.db.type == 'Publish' and thisTrait.confidential: #XZ: confidential phenotype trait
                    if webqtlUtil.hasAccessToConfidentialPhenotypeTrait(privilege=self.privilege, userName=self.userName, authorized_users=thisTrait.authorized_users):
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
        if thisTrait:
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
        if thisTrait and thisTrait.db and thisTrait.db.type == 'ProbeSet': #before, this line was only reached if thisTrait != 0, but now we need to check
            try:
                hddn['GeneId'] = int(string.strip(thisTrait.geneid))
            except:
                pass

            #Info2Disp = HT.Paragraph()

            #XZ: Gene Symbol
            if thisTrait.symbol:
                #XZ: Show SNP Browser only for mouse
                if _Species == 'mouse':
                    self.cursor.execute("select geneSymbol from GeneList where geneSymbol = %s", thisTrait.symbol)
                    geneName = self.cursor.fetchone()
                    if geneName:
                        snpurl = os.path.join(webqtlConfig.CGIDIR, "main.py?FormID=SnpBrowserResultPage&submitStatus=1&diffAlleles=True&customStrain=True") + "&geneName=%s" % geneName[0]
                    else:
                        if thisTrait.chr and thisTrait.mb:
                            snpurl = os.path.join(webqtlConfig.CGIDIR, "main.py?FormID=SnpBrowserResultPage&submitStatus=1&diffAlleles=True&customStrain=True") + \
                                    "&chr=%s&start=%2.6f&end=%2.6f" % (thisTrait.chr, thisTrait.mb-0.002, thisTrait.mb+0.002)
                        else:
                            snpurl = ""

                    if snpurl:
                        snpBrowserButton = HT.Href(url="#redirect", onClick="openNewWin('%s')" % snpurl)
                        snpBrowserButton_img = HT.Image("/images/snp_icon.jpg", name="snpbrowser", alt=" View SNPs and Indels ", title=" View SNPs and Indels ", style="border:none;")
                        #snpBrowserButton.append(snpBrowserButton_img)
                        snpBrowserText = "SNPs"

                #XZ: Show GeneWiki for all species
                geneWikiButton = HT.Href(url="#redirect", onClick="openNewWin('%s')" % (os.path.join(webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE) + "?FormID=geneWiki&symbol=%s" % thisTrait.symbol))
                geneWikiButton_img = HT.Image("/images/genewiki_icon.jpg", name="genewiki", alt=" Write or review comments about this gene ", title=" Write or review comments about this gene ", style="border:none;")
                #geneWikiButton.append(geneWikiButton_img)
                geneWikiText = 'GeneWiki'

                #XZ: display similar traits in other selected datasets
                if thisTrait and thisTrait.db and thisTrait.db.type=="ProbeSet" and thisTrait.symbol:
                    if _Species in ("mouse", "rat", "human"):
                        similarUrl = "%s?cmd=sch&gene=%s&alias=1&species=%s" % (os.path.join(webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE), thisTrait.symbol, _Species)
                        similarButton = HT.Href(url="#redirect", onClick="openNewWin('%s')" % similarUrl)
                        similarButton_img = HT.Image("/images/find_icon.jpg", name="similar", alt=" Find similar expression data ", title=" Find similar expression data ", style="border:none;")
                        #similarButton.append(similarButton_img)
                        similarText = "Find"
                else:
                    pass
                #tbl.append(HT.TR(
                        #HT.TD('Gene Symbol: ', Class="fwb fs13", valign="top", nowrap="on", width=90),
                        #HT.TD(width=10, valign="top"),
                        #HT.TD(HT.Span('%s' % thisTrait.symbol, valign="top", Class="fs13 fsI"), valign="top", width=740)
                        #))
            else:
                tbl.append(HT.TR(
                        HT.TD('Gene Symbol: ', Class="fwb fs13", valign="top", nowrap="on"),
                        HT.TD(width=10, valign="top"),
                        HT.TD(HT.Span('Not available', Class="fs13 fsI"), valign="top")
                        ))



            ##display Verify Location button
            try:
                blatsequence = thisTrait.blatseq
                if not blatsequence:
                    #XZ, 06/03/2009: ProbeSet name is not unique among platforms. We should use ProbeSet Id instead.
                    self.cursor.execute("""SELECT Probe.Sequence, Probe.Name
                                           FROM Probe, ProbeSet, ProbeSetFreeze, ProbeSetXRef
                                           WHERE ProbeSetXRef.ProbeSetFreezeId = ProbeSetFreeze.Id AND
                                                 ProbeSetXRef.ProbeSetId = ProbeSet.Id AND
                                                 ProbeSetFreeze.Name = '%s' AND
                                                 ProbeSet.Name = '%s' AND
                                                 Probe.ProbeSetId = ProbeSet.Id order by Probe.SerialOrder""" % (thisTrait.db.name, thisTrait.name) )
                    seqs = self.cursor.fetchall()
                    if not seqs:
                        raise ValueError
                    else:
                        blatsequence = ''
                        for seqt in seqs:
                            if int(seqt[1][-1]) % 2 == 1:
                                blatsequence += string.strip(seqt[0])

                #--------Hongqiang add this part in order to not only blat ProbeSet, but also blat Probe
                blatsequence = '%3E'+thisTrait.name+'%0A'+blatsequence+'%0A'
                #XZ, 06/03/2009: ProbeSet name is not unique among platforms. We should use ProbeSet Id instead.
                self.cursor.execute("""SELECT Probe.Sequence, Probe.Name
                                       FROM Probe, ProbeSet, ProbeSetFreeze, ProbeSetXRef
                                       WHERE ProbeSetXRef.ProbeSetFreezeId = ProbeSetFreeze.Id AND
                                             ProbeSetXRef.ProbeSetId = ProbeSet.Id AND
                                             ProbeSetFreeze.Name = '%s' AND
                                             ProbeSet.Name = '%s' AND
                                             Probe.ProbeSetId = ProbeSet.Id order by Probe.SerialOrder""" % (thisTrait.db.name, thisTrait.name) )

                seqs = self.cursor.fetchall()
                for seqt in seqs:
                    if int(seqt[1][-1]) %2 == 1:
                        blatsequence += '%3EProbe_'+string.strip(seqt[1])+'%0A'+string.strip(seqt[0])+'%0A'
                #--------
                #XZ, 07/16/2009: targetsequence is not used, so I comment out this block
                #targetsequence = thisTrait.targetseq
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
            if thisTrait.db.name.find('Liver') >= 0 and thisTrait.db.name.find('F2') < 0:
                pass
            else:
                #query database for number of probes associated with trait; if count > 0, set probe tool button and text
                self.cursor.execute("""SELECT count(*)
                                           FROM Probe, ProbeSet
                                           WHERE ProbeSet.Name = '%s' AND Probe.ProbeSetId = ProbeSet.Id""" % (thisTrait.name))

                probeResult = self.cursor.fetchone()
                if probeResult[0] > 0:
                    probeurl = "%s?FormID=showProbeInfo&database=%s&ProbeSetID=%s&CellID=%s&RISet=%s&incparentsf1=ON" \
                            % (os.path.join(webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE), thisTrait.db, thisTrait.name, thisTrait.cellid, fd.RISet)
                    probeButton = HT.Href(url="#", onClick="javascript:openNewWin('%s'); return false;" % probeurl)
                    probeButton_img = HT.Image("/images/probe_icon.jpg", name="probe", alt=" Check sequence of probes ", title=" Check sequence of probes ", style="border:none;")
                    #probeButton.append(probeButton_img)
                    probeText = "Probes"

            #tSpan = HT.Span(Class="fs13")

            #XZ: deal with blat score and blat specificity.
            #if thisTrait.probe_set_specificity or thisTrait.probe_set_blat_score:
            #    if thisTrait.probe_set_specificity:
            #        pass
            #        #tSpan.append(HT.Href(url="/blatInfo.html", target="_blank", title="Values higher than 2 for the specificity are good", text="BLAT specificity", Class="non_bold"),": %.1f" % float(thisTrait.probe_set_specificity), "&nbsp;"*3)
            #    if thisTrait.probe_set_blat_score:
            #        pass
            #        #tSpan.append("Score: %s" % int(thisTrait.probe_set_blat_score), "&nbsp;"*2)

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

            #if thisTrait.cellid:
            #    self.cursor.execute("""
            #                    select ProbeFreeze.Name from ProbeFreeze, ProbeSetFreeze
            #                            where
            #                    ProbeFreeze.Id = ProbeSetFreeze.ProbeFreezeId AND
            #                    ProbeSetFreeze.Id = %d""" % thisTrait.db.id)
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
                #        HT.TD(HT.Href(text=thisTrait.db.fullname, url = webqtlConfig.INFOPAGEHREF % thisTrait.db.name,
                #        target='_blank', Class="fs13 fwn non_bold"), valign="top")
                #        ))
                #pass

            thisTrait.species = _Species  # We need this in the template, so we tuck it into thisTrait
            thisTrait.database = thisTrait.get_database()

            #XZ: ID links
            if thisTrait.genbankid or thisTrait.geneid or thisTrait.unigeneid or thisTrait.omim or thisTrait.homologeneid:
                idStyle = "background:#dddddd;padding:2"
                tSpan = HT.Span(Class="fs13")
                if thisTrait.geneid:
                    gurl = HT.Href(text= 'Gene', target='_blank',\
                            url=webqtlConfig.NCBI_LOCUSID % thisTrait.geneid, Class="fs14 fwn", title="Info from NCBI Entrez Gene")
                    #tSpan.append(HT.Span(gurl, style=idStyle), "&nbsp;"*2)
                if thisTrait.omim:
                    gurl = HT.Href(text= 'OMIM', target='_blank', \
                            url= webqtlConfig.OMIM_ID % thisTrait.omim,Class="fs14 fwn", title="Summary from On Mendelian Inheritance in Man")
                    #tSpan.append(HT.Span(gurl, style=idStyle), "&nbsp;"*2)
                if thisTrait.unigeneid:
                    try:
                        gurl = HT.Href(text= 'UniGene',target='_blank',\
                                url= webqtlConfig.UNIGEN_ID % tuple(string.split(thisTrait.unigeneid,'.')[:2]),Class="fs14 fwn", title="UniGene ID")
                        #tSpan.append(HT.Span(gurl, style=idStyle), "&nbsp;"*2)
                    except:
                        pass
                if thisTrait.genbankid:
                    thisTrait.genbankid = '|'.join(thisTrait.genbankid.split('|')[0:10])
                    if thisTrait.genbankid[-1]=='|':
                        thisTrait.genbankid=thisTrait.genbankid[0:-1]
                    gurl = HT.Href(text= 'GenBank', target='_blank', \
                            url= webqtlConfig.GENBANK_ID % thisTrait.genbankid,Class="fs14 fwn", title="Find the original GenBank sequence used to design the probes")
                    #tSpan.append(HT.Span(gurl, style=idStyle), "&nbsp;"*2)
                if thisTrait.homologeneid:
                    hurl = HT.Href(text= 'HomoloGene', target='_blank',\
                            url=webqtlConfig.HOMOLOGENE_ID % thisTrait.homologeneid, Class="fs14 fwn", title="Find similar genes in other species")
                    #tSpan.append(HT.Span(hurl, style=idStyle), "&nbsp;"*2)

                #tbl.append(
                #        HT.TR(HT.TD(colspan=3,height=6)),
                #        HT.TR(
                #        HT.TD('Resource Links: ', Class="fwb fs13", valign="top", nowrap="on"),
                #        HT.TD(width=10, valign="top"),
                #        HT.TD(tSpan, valign="top")
                #        ))

            #XZ: Resource Links:
            if thisTrait.symbol:
                linkStyle = "background:#dddddd;padding:2"
                tSpan = HT.Span(style="font-family:verdana,serif;font-size:13px")

                #XZ,12/26/2008: Gene symbol may contain single quotation mark.
                #For example, Affymetrix, mouse430v2, 1440338_at, the symbol is 2'-Pde (geneid 211948)
                #I debug this by using double quotation marks.
                if _Species == "rat":

                    #XZ, 7/16/2009: The url for SymAtlas (renamed as BioGPS) has changed. We don't need this any more
                    #symatlas_species = "Rattus norvegicus"

                    #self.cursor.execute("SELECT kgID, chromosome,txStart,txEnd FROM GeneList_rn33 WHERE geneSymbol = '%s'" % thisTrait.symbol)
                    self.cursor.execute('SELECT kgID, chromosome,txStart,txEnd FROM GeneList_rn33 WHERE geneSymbol = "%s"' % thisTrait.symbol)
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

                    #self.cursor.execute("SELECT chromosome,txStart,txEnd FROM GeneList WHERE geneSymbol = '%s'" % thisTrait.symbol)
                    self.cursor.execute('SELECT chromosome,txStart,txEnd FROM GeneList WHERE geneSymbol = "%s"' % thisTrait.symbol)
                    try:
                        chr, txst, txen = self.cursor.fetchall()[0]
                        if chr and txst and txen and thisTrait.refseq_transcriptid :
                            txst = int(txst*1000000)
                            txen = int(txen*1000000)
                            tSpan.append(HT.Span(HT.Href(text= 'UCSC',target="mainFrame",\
                                    title= 'Info from UCSC Genome Browser', url = webqtlConfig.UCSC_REFSEQ % ('mm9',thisTrait.refseq_transcriptid,chr,txst,txen),
                                    Class="fs14 fwn"), style=linkStyle)
                                    , "&nbsp;"*2)
                    except:
                        pass

                #XZ, 7/16/2009: The url for SymAtlas (renamed as BioGPS) has changed. We don't need this any more
                #tSpan.append(HT.Span(HT.Href(text= 'SymAtlas',target="mainFrame",\
                #       url="http://symatlas.gnf.org/SymAtlas/bioentry?querytext=%s&query=14&species=%s&type=Expression" \
                #       % (thisTrait.symbol,symatlas_species),Class="fs14 fwn", \
                #       title="Expression across many tissues and cell types"), style=linkStyle), "&nbsp;"*2)
                if thisTrait.geneid and (_Species == "mouse" or _Species == "rat" or _Species == "human"):
                    #tSpan.append(HT.Span(HT.Href(text= 'BioGPS',target="mainFrame",\
                    #        url="http://biogps.gnf.org/?org=%s#goto=genereport&id=%s" \
                    #        % (_Species, thisTrait.geneid),Class="fs14 fwn", \
                    #        title="Expression across many tissues and cell types"), style=linkStyle), "&nbsp;"*2)
                    pass
                #tSpan.append(HT.Span(HT.Href(text= 'STRING',target="mainFrame",\
                #        url="http://string.embl.de/newstring_cgi/show_link_summary.pl?identifier=%s" \
                #        % thisTrait.symbol,Class="fs14 fwn", \
                #        title="Protein interactions: known and inferred"), style=linkStyle), "&nbsp;"*2)
                if thisTrait.symbol:
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
                    #        % (species_scientific, thisTrait.symbol),Class="fs14 fwn", \
                    #        title="Gene and protein data resources from Celera-ABI"), style=linkStyle), "&nbsp;"*2)
                else:
                    pass
                #tSpan.append(HT.Span(HT.Href(text= 'BIND',target="mainFrame",\
                #       url="http://bind.ca/?textquery=%s" \
                #       % thisTrait.symbol,Class="fs14 fwn", \
                #       title="Protein interactions"), style=linkStyle), "&nbsp;"*2)
                #if thisTrait.geneid and (_Species == "mouse" or _Species == "rat" or _Species == "human"):
                #    tSpan.append(HT.Span(HT.Href(text= 'Gemma',target="mainFrame",\
                #            url="http://www.chibi.ubc.ca/Gemma/gene/showGene.html?ncbiid=%s" \
                #            % thisTrait.geneid, Class="fs14 fwn", \
                #            title="Meta-analysis of gene expression data"), style=linkStyle), "&nbsp;"*2)
                #tSpan.append(HT.Span(HT.Href(text= 'SynDB',target="mainFrame",\
                #        url="http://lily.uthsc.edu:8080/20091027_GNInterfaces/20091027_redirectSynDB.jsp?query=%s" \
                #        % thisTrait.symbol, Class="fs14 fwn", \
                #        title="Brain synapse database"), style=linkStyle), "&nbsp;"*2)
                #if _Species == "mouse":
                #    tSpan.append(HT.Span(HT.Href(text= 'ABA',target="mainFrame",\
                #            url="http://mouse.brain-map.org/brain/%s.html" \
                #            % thisTrait.symbol, Class="fs14 fwn", \
                #            title="Allen Brain Atlas"), style=linkStyle), "&nbsp;"*2)

                if thisTrait.geneid:
                    #if _Species == "mouse":
                    #       tSpan.append(HT.Span(HT.Href(text= 'ABA',target="mainFrame",\
                    #               url="http://www.brain-map.org/search.do?queryText=egeneid=%s" \
                    #               % thisTrait.geneid, Class="fs14 fwn", \
                    #               title="Allen Brain Atlas"), style=linkStyle), "&nbsp;"*2)
                    if _Species == "human":
                        #tSpan.append(HT.Span(HT.Href(text= 'ABA',target="mainFrame",\
                        #        url="http://humancortex.alleninstitute.org/has/human/imageseries/search/1.html?searchSym=t&searchAlt=t&searchName=t&gene_term=&entrez_term=%s" \
                        #        % thisTrait.geneid, Class="fs14 fwn", \
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

        elif thisTrait and thisTrait.db and thisTrait.db.type =='Publish': #Check if trait is phenotype

            if thisTrait.confidential:
                pass
                #tbl.append(HT.TR(
                #                HT.TD('Pre-publication Phenotype: ', Class="fs13 fwb", valign="top", nowrap="on", width=90),
                #                HT.TD(width=10, valign="top"),
                #                HT.TD(HT.Span(thisTrait.pre_publication_description, Class="fs13"), valign="top", width=740)
                #                ))
                if webqtlUtil.hasAccessToConfidentialPhenotypeTrait(privilege=self.privilege, userName=self.userName, authorized_users=thisTrait.authorized_users):
                    #tbl.append(HT.TR(
                    #                HT.TD('Post-publication Phenotype: ', Class="fs13 fwb", valign="top", nowrap="on", width=90),
                    #                HT.TD(width=10, valign="top"),
                    #                HT.TD(HT.Span(thisTrait.post_publication_description, Class="fs13"), valign="top", width=740)
                    #                ))
                    #tbl.append(HT.TR(
                    #                HT.TD('Pre-publication Abbreviation: ', Class="fs13 fwb", valign="top", nowrap="on", width=90),
                    #                HT.TD(width=10, valign="top"),
                    #                HT.TD(HT.Span(thisTrait.pre_publication_abbreviation, Class="fs13"), valign="top", width=740)
                    #                ))
                    #tbl.append(HT.TR(
                    #                HT.TD('Post-publication Abbreviation: ', Class="fs13 fwb", valign="top", nowrap="on", width=90),
                    #                HT.TD(width=10, valign="top"),
                    #                HT.TD(HT.Span(thisTrait.post_publication_abbreviation, Class="fs13"), valign="top", width=740)
                    #                ))
                    #tbl.append(HT.TR(
                    #                HT.TD('Lab code: ', Class="fs13 fwb", valign="top", nowrap="on", width=90),
                    #                HT.TD(width=10, valign="top"),
                    #                HT.TD(HT.Span(thisTrait.lab_code, Class="fs13"), valign="top", width=740)
                    #                ))
                    pass
                #tbl.append(HT.TR(
                #                HT.TD('Owner: ', Class="fs13 fwb", valign="top", nowrap="on", width=90),
                #                HT.TD(width=10, valign="top"),
                #                HT.TD(HT.Span(thisTrait.owner, Class="fs13"), valign="top", width=740)
                #                ))
            else:
                pass
                #tbl.append(HT.TR(
                #                HT.TD('Phenotype: ', Class="fs13 fwb", valign="top", nowrap="on", width=90),
                #                HT.TD(width=10, valign="top"),
                #                HT.TD(HT.Span(thisTrait.post_publication_description, Class="fs13"), valign="top", width=740)
                #                ))
            #tbl.append(HT.TR(
            #                HT.TD('Authors: ', Class="fs13 fwb",
            #                        valign="top", nowrap="on", width=90),
            #                HT.TD(width=10, valign="top"),
            #                HT.TD(HT.Span(thisTrait.authors, Class="fs13"),
            #                        valign="top", width=740)
            #                ))
            #tbl.append(HT.TR(
            #                HT.TD('Title: ', Class="fs13 fwb",
            #                        valign="top", nowrap="on", width=90),
            #                HT.TD(width=10, valign="top"),
            #                HT.TD(HT.Span(thisTrait.title, Class="fs13"),
            #                        valign="top", width=740)
            #                ))
            if thisTrait.journal:
                journal = thisTrait.journal
                if thisTrait.year:
                    journal = thisTrait.journal + " (%s)" % thisTrait.year
                #
                #tbl.append(HT.TR(
                #        HT.TD('Journal: ', Class="fs13 fwb",
                #                valign="top", nowrap="on", width=90),
                #        HT.TD(width=10, valign="top"),
                #        HT.TD(HT.Span(journal, Class="fs13"),
                #                valign="top", width=740)
                #        ))
            PubMedLink = ""
            if thisTrait.pubmed_id:
                PubMedLink = webqtlConfig.PUBMEDLINK_URL % thisTrait.pubmed_id
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

        elif thisTrait and thisTrait.db and thisTrait.db.type == 'Geno': #Check if trait is genotype

            GenoInfo = HT.Paragraph()
            if thisTrait.chr and thisTrait.mb:
                location = ' Chr %s @ %s Mb' % (thisTrait.chr,thisTrait.mb)
            else:
                location = "not available"

            if thisTrait.sequence and len(thisTrait.sequence) > 100:
                if _Species == "rat":
                    UCSC_BLAT_URL = webqtlConfig.UCSC_BLAT % ('rat', 'rn3', thisTrait.sequence)
                    UTHSC_BLAT_URL = webqtlConfig.UTHSC_BLAT % ('rat', 'rn3', thisTrait.sequence)
                elif _Species == "mouse":
                    UCSC_BLAT_URL = webqtlConfig.UCSC_BLAT % ('mouse', 'mm9', thisTrait.sequence)
                    UTHSC_BLAT_URL = webqtlConfig.UTHSC_BLAT % ('mouse', 'mm9', thisTrait.sequence)
                elif _Species == "human":
                    UCSC_BLAT_URL = webqtlConfig.UCSC_BLAT % ('human', 'hg19', blatsequence)
                    UTHSC_BLAT_URL = webqtlConfig.UTHSC_BLAT % ('human', 'hg19', thisTrait.sequence)
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
            #                HT.TD(HT.Href("http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?db=snp&cmd=search&term=%s" % thisTrait.name, 'NCBI',Class="fs13"),
            #                        valign="top", width=740)
            #                ))

            menuTable = HT.TableLite(cellpadding=2, Class="collap", width="275", id="target1")
            #menuTable.append(HT.TR(HT.TD(addSelectionButton, align="center"),HT.TD(verifyButton, align="center"),HT.TD(rnaseqButton, align="center"), HT.TD(updateButton, align="center"), colspan=3, height=50, style="vertical-align:bottom;"))
            #menuTable.append(HT.TR(HT.TD(addSelectionText, align="center"),HT.TD(verifyText, align="center"),HT.TD(rnaseqText, align="center"), HT.TD(updateText, align="center"), colspan=3, height=50, style="vertical-align:bottom;"))

            #title1Body.append(tbl, HT.BR(), menuTable)

        elif (thisTrait == None or thisTrait.db.type == 'Temp'): #if temporary trait (user-submitted trait or PCA trait)

            #TempInfo = HT.Paragraph()
            if thisTrait != None:
                if thisTrait.description:
                    pass
                    #tbl.append(HT.TR(HT.TD(HT.Strong('Description: '),' %s ' % thisTrait.description,HT.BR()), colspan=3, height=15))
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


    ##########################################
    ##  Function to display analysis tools
    ##########################################
    def dispBasicStatistics(self, fd, thisTrait):

        #XZ, June 22, 2011: The definition and usage of primary_strains, other_strains, specialStrains, all_strains are not clear and hard to understand. But since they are only used in this function for draw graph purpose, they will not hurt the business logic outside. As of June 21, 2011, this function seems work fine, so no hurry to clean up. These parameters and code in this function should be cleaned along with fd.f1list, fd.parlist, fd.strainlist later.
        #stats_row = HT.TR()
        #stats_cell = HT.TD()

        if fd.genotype.type == "riset":
            strainlist = fd.f1list + fd.strainlist
        else:
            strainlist = fd.f1list + fd.parlist + fd.strainlist

        other_strains = [] #XZ: strain that is not of primary group
        specialStrains = [] #XZ: This might be replaced by other_strains / ZS: It is just other strains without parent/f1 strains.
        all_strains = []
        primary_strains = [] #XZ: strain of primary group, e.g., BXD, LXS

        #MDP_menu = HT.Select(name='stats_mdp', Class='stats_mdp')
        MDP_menu = [] # We're going to use the same named data structure as in the old version
                      # but repurpose it for Jinja2 as an array

        for strain in thisTrait.data.keys():
            strainName = strain.replace("_2nd_", "")
            if strain not in strainlist:
                if (thisTrait.data[strainName].val != None):
                    if strain.find('F1') < 0:
                        specialStrains.append(strain)
                    if (thisTrait.data[strainName].val != None) and (strain not in (fd.f1list + fd.parlist)):
                        other_strains.append(strain) #XZ: at current stage, other_strains doesn't include parent strains and F1 strains of primary group
            else:
                if (thisTrait.data[strainName].val != None) and (strain not in (fd.f1list + fd.parlist)):
                    primary_strains.append(strain) #XZ: at current stage, the primary_strains is the same as fd.strainlist / ZS: I tried defining primary_strains as fd.strainlist instead, but in some cases it ended up including the parent strains (1436869_at BXD)

        if len(other_strains) > 3:
            other_strains.sort(key=webqtlUtil.natsort_key)
            primary_strains.sort(key=webqtlUtil.natsort_key)
            primary_strains = map(lambda X:"_2nd_"+X, fd.f1list + fd.parlist) + primary_strains #XZ: note that fd.f1list and fd.parlist are added.
            all_strains = primary_strains + other_strains
            other_strains = map(lambda X:"_2nd_"+X, fd.f1list + fd.parlist) + other_strains #XZ: note that fd.f1list and fd.parlist are added.
            print("ac1")   # This is the one used for first sall3
            MDP_menu.append(('All Cases','0'))
            MDP_menu.append(('%s Only' % fd.RISet, '1'))
            MDP_menu.append(('Non-%s Only' % fd.RISet, '2'))
            #stats_row.append("Include: ", MDP_menu, HT.BR(), HT.BR())
        else:
            if (len(other_strains) > 0) and (len(primary_strains) + len(other_strains) > 3):
                print("ac2")
                MDP_menu.append(('All Cases','0'))
                MDP_menu.append(('%s Only' % fd.RISet,'1'))
                MDP_menu.append(('Non-%s Only' % fd.RISet,'2'))
                #stats_row.append("Include: ", MDP_menu, "&nbsp;"*3)
                all_strains = primary_strains
                all_strains.sort(key=webqtlUtil.natsort_key)
                all_strains = map(lambda X:"_2nd_"+X, fd.f1list + fd.parlist) + all_strains
                primary_strains = map(lambda X:"_2nd_"+X, fd.f1list + fd.parlist) + primary_strains
            else:
                print("ac3")
                all_strains = strainlist

            other_strains.sort(key=webqtlUtil.natsort_key)
            all_strains = all_strains + other_strains
            pass

        #update_button = HT.Input(type='button',value=' Update Figures ', Class="button update") #This is used to reload the page and update the Basic Statistics figures with user-edited data
        #stats_row.append(update_button, HT.BR(), HT.BR())

        if (len(other_strains)) > 0 and (len(primary_strains) + len(other_strains) > 4):
            #One set of vals for all, selected strain only, and non-selected only
            vals1 = []
            vals2 = []
            vals3 = []

            #Using all strains/cases for values
            for i, strainNameOrig in enumerate(all_strains):
                strainName = strainNameOrig.replace("_2nd_", "")

                try:
                    thisval = thisTrait.data[strainName].val
                    thisvar = thisTrait.data[strainName].var
                    thisValFull = [strainName, thisval, thisvar]
                except:
                    continue

                vals1.append(thisValFull)

            #Using just the RISet strain
            for i, strainNameOrig in enumerate(primary_strains):
                strainName = strainNameOrig.replace("_2nd_", "")

                try:
                    thisval = thisTrait.data[strainName].val
                    thisvar = thisTrait.data[strainName].var
                    thisValFull = [strainName,thisval,thisvar]
                except:
                    continue

                vals2.append(thisValFull)

            #Using all non-RISet strains only
            for i, strainNameOrig in enumerate(other_strains):
                strainName = strainNameOrig.replace("_2nd_", "")

                try:
                    thisval = thisTrait.data[strainName].val
                    thisvar = thisTrait.data[strainName].var
                    thisValFull = [strainName,thisval,thisvar]
                except:
                    continue

                vals3.append(thisValFull)

            vals_set = [vals1,vals2,vals3]

        else:
            vals = []

            #Using all strains/cases for values
            for i, strainNameOrig in enumerate(all_strains):
                strainName = strainNameOrig.replace("_2nd_", "")

                try:
                    thisval = thisTrait.data[strainName].val
                    thisvar = thisTrait.data[strainName].var
                    thisValFull = [strainName,thisval,thisvar]
                except:
                    continue

                vals.append(thisValFull)

            vals_set = [vals]

        #stats_script = HT.Script(language="Javascript") #script needed for tabs
        self.stats_data = []
        for i, vals in enumerate(vals_set):
            if i == 0 and len(vals) < 4:
                stats_container = HT.Div(id="stats_tabs", style="padding:10px;", Class="ui-tabs") #Needed for tabs; notice the "stats_script_text" below referring to this element
                stats_container.append(HT.Div(HT.Italic("Fewer than 4 case data were entered. No statistical analysis has been attempted.")))
                stats_script_text = """$(function() { $("#stats_tabs").tabs();});"""
                #stats_cell.append(stats_container)
                break
            elif (i == 1 and len(primary_strains) < 4):
                stats_container = HT.Div(id="stats_tabs%s" % i, Class="ui-tabs")
                stats_container.append(HT.Div(HT.Italic("Fewer than 4 " + fd.RISet + " case data were entered. No statistical analysis has been attempted.")))
            elif (i == 2 and len(other_strains) < 4):
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

                if thisTrait.db:
                    if thisTrait.cellid:
                        self.stats_data.append(BasicStatisticsFunctions.basicStatsTable(vals=vals, trait_type=thisTrait.db.type, cellid=thisTrait.cellid))
                    else:
                        self.stats_data.append(BasicStatisticsFunctions.basicStatsTable(vals=vals, trait_type=thisTrait.db.type))
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
                    plotTitle = thisTrait.symbol
                    plotTitle += ": "
                    plotTitle += thisTrait.name
                except:
                    plotTitle = str(thisTrait.name)

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


    def dispCorrelationTools(self, fd, title3Body, thisTrait):

        _Species = webqtlDatabaseFunction.retrieveSpecies(cursor=self.cursor, RISet=fd.RISet)

        RISetgp = fd.RISet
        if RISetgp[:3] == 'BXD':
            RISetgp = 'BXD'

        if RISetgp:
            sample_correlation = HT.Input(type='button',name='sample_corr', value=' Compute ', Class="button sample_corr")
            lit_correlation = HT.Input(type='button',name='lit_corr', value=' Compute ', Class="button lit_corr")
            tissue_correlation = HT.Input(type='button',name='tiss_corr', value=' Compute ', Class="button tiss_corr")
            methodText = HT.Span("Calculate:", Class="ffl fwb fs12")

            databaseText = HT.Span("Database:", Class="ffl fwb fs12")
            databaseMenu1 = HT.Select(name='database1')
            databaseMenu2 = HT.Select(name='database2')
            databaseMenu3 = HT.Select(name='database3')

            nmenu = 0
            self.cursor.execute('SELECT PublishFreeze.FullName,PublishFreeze.Name FROM \
                    PublishFreeze,InbredSet WHERE PublishFreeze.InbredSetId = InbredSet.Id \
                    and InbredSet.Name = "%s" and PublishFreeze.public > %d' % \
                    (RISetgp,webqtlConfig.PUBLICTHRESH))
            for item in self.cursor.fetchall():
                databaseMenu1.append(item)
                databaseMenu2.append(item)
                databaseMenu3.append(item)
                nmenu += 1
            self.cursor.execute('SELECT GenoFreeze.FullName,GenoFreeze.Name FROM GenoFreeze,\
                    InbredSet WHERE GenoFreeze.InbredSetId = InbredSet.Id and InbredSet.Name = \
                    "%s" and GenoFreeze.public > %d' % (RISetgp,webqtlConfig.PUBLICTHRESH))
            for item in self.cursor.fetchall():
                databaseMenu1.append(item)
                databaseMenu2.append(item)
                databaseMenu3.append(item)
                nmenu += 1
            #03/09/2009: Xiaodong changed the SQL query to order by Name as requested by Rob.
            self.cursor.execute('SELECT Id, Name FROM Tissue order by Name')
            for item in self.cursor.fetchall():
                TId, TName = item
                databaseMenuSub = HT.Optgroup(label = '%s ------' % TName)
                self.cursor.execute('SELECT ProbeSetFreeze.FullName,ProbeSetFreeze.Name FROM ProbeSetFreeze, ProbeFreeze, \
                InbredSet WHERE ProbeSetFreeze.ProbeFreezeId = ProbeFreeze.Id and ProbeFreeze.TissueId = %d and \
                ProbeSetFreeze.public > %d and ProbeFreeze.InbredSetId = InbredSet.Id and InbredSet.Name like "%s%%" \
                order by ProbeSetFreeze.CreateTime desc, ProbeSetFreeze.AvgId '  % (TId,webqtlConfig.PUBLICTHRESH, RISetgp))
                for item2 in self.cursor.fetchall():
                    databaseMenuSub.append(item2)
                    nmenu += 1
                databaseMenu1.append(databaseMenuSub)
                databaseMenu2.append(databaseMenuSub)
                databaseMenu3.append(databaseMenuSub)
            if nmenu:
                if thisTrait and thisTrait.db != None:
                    databaseMenu1.selected.append(thisTrait.db.fullname)
                    databaseMenu2.selected.append(thisTrait.db.fullname)
                    databaseMenu3.selected.append(thisTrait.db.fullname)

                criteriaText = HT.Span("Return:", Class="ffl fwb fs12")

                criteriaMenu1 = HT.Select(name='criteria1', selected='500', onMouseOver="if (NS4 || IE4) activateEl('criterias', event);")
                criteriaMenu1.append(('top 100','100'))
                criteriaMenu1.append(('top 200','200'))
                criteriaMenu1.append(('top 500','500'))
                criteriaMenu1.append(('top 1000','1000'))
                criteriaMenu1.append(('top 2000','2000'))
                criteriaMenu1.append(('top 5000','5000'))
                criteriaMenu1.append(('top 10000','10000'))
                criteriaMenu1.append(('top 15000','15000'))
                criteriaMenu1.append(('top 20000','20000'))

                criteriaMenu2 = HT.Select(name='criteria2', selected='500', onMouseOver="if (NS4 || IE4) activateEl('criterias', event);")
                criteriaMenu2.append(('top 100','100'))
                criteriaMenu2.append(('top 200','200'))
                criteriaMenu2.append(('top 500','500'))
                criteriaMenu2.append(('top 1000','1000'))
                criteriaMenu2.append(('top 2000','2000'))
                criteriaMenu2.append(('top 5000','5000'))
                criteriaMenu2.append(('top 10000','10000'))
                criteriaMenu2.append(('top 15000','15000'))
                criteriaMenu2.append(('top 20000','20000'))

                criteriaMenu3 = HT.Select(name='criteria3', selected='500', onMouseOver="if (NS4 || IE4) activateEl('criterias', event);")
                criteriaMenu3.append(('top 100','100'))
                criteriaMenu3.append(('top 200','200'))
                criteriaMenu3.append(('top 500','500'))
                criteriaMenu3.append(('top 1000','1000'))
                criteriaMenu3.append(('top 2000','2000'))
                criteriaMenu3.append(('top 5000','5000'))
                criteriaMenu3.append(('top 10000','10000'))
                criteriaMenu3.append(('top 15000','15000'))
                criteriaMenu3.append(('top 20000','20000'))


                self.MDPRow1 = HT.TR(Class='mdp1')
                self.MDPRow2 = HT.TR(Class='mdp2')
                self.MDPRow3 = HT.TR(Class='mdp3')

                correlationMenus1 = HT.TableLite(
                        HT.TR(HT.TD(databaseText), HT.TD(databaseMenu1, colspan="3")),
                        HT.TR(HT.TD(criteriaText), HT.TD(criteriaMenu1)),
                    self.MDPRow1, cellspacing=0, width="619px", cellpadding=2)
                correlationMenus1.append(HT.Input(name='orderBy', value='2', type='hidden'))    # to replace the orderBy menu
                correlationMenus2 = HT.TableLite(
                        HT.TR(HT.TD(databaseText), HT.TD(databaseMenu2, colspan="3")),
                        HT.TR(HT.TD(criteriaText), HT.TD(criteriaMenu2)),
                    self.MDPRow2, cellspacing=0, width="619px", cellpadding=2)
                correlationMenus2.append(HT.Input(name='orderBy', value='2', type='hidden'))
                correlationMenus3 = HT.TableLite(
                        HT.TR(HT.TD(databaseText), HT.TD(databaseMenu3, colspan="3")),
                        HT.TR(HT.TD(criteriaText), HT.TD(criteriaMenu3)),
                    self.MDPRow3, cellspacing=0, width="619px", cellpadding=2)
                correlationMenus3.append(HT.Input(name='orderBy', value='2', type='hidden'))

            else:
                correlationMenus = ""


        corr_row = HT.TR()
        corr_container = HT.Div(id="corr_tabs", Class="ui-tabs")

        if (thisTrait.db != None and thisTrait.db.type =='ProbeSet'):
            corr_tab_list = [HT.Href(text='Sample r', url="#corrtabs-1"), HT.Href(text='Literature r',  url="#corrtabs-2"), HT.Href(text='Tissue r', url="#corrtabs-3")]
        else:
            corr_tab_list = [HT.Href(text='Sample r', url="#corrtabs-1")]

        corr_tabs = HT.List(corr_tab_list)
        corr_container.append(corr_tabs)

        if correlationMenus1 or correlationMenus2 or correlationMenus3:
            sample_div = HT.Div(id="corrtabs-1")
            sample_container = HT.Span()

            sample_type = HT.Input(type="radio", name="sample_method", value="1", checked="checked")
            sample_type2 = HT.Input(type="radio", name="sample_method", value="2")

            sampleTable = HT.TableLite(cellspacing=0, cellpadding=0, width="100%")
            sampleTD = HT.TD(correlationMenus1, HT.BR(),
                                       "Pearson", sample_type, "&nbsp;"*3, "Spearman Rank", sample_type2, HT.BR(), HT.BR(),
                                       sample_correlation, HT.BR(), HT.BR())

            sampleTD.append(HT.Span("The ",HT.Href(url="/correlationAnnotation.html#sample_r", target="_blank", text="Sample Correlation")," is computed between trait data and",
                                                                            " any ",HT.BR()," other traits in the sample database selected above. Use ",
                                                                            HT.Href(url="/glossary.html#Correlations", target="_blank", text="Spearman Rank"),
                                                                            HT.BR(),"when the sample size is small (<20) or when there are influential \
                                                                            outliers.", HT.BR(),Class="fs12"))

            sampleTable.append(sampleTD)

            sample_container.append(sampleTable)
            sample_div.append(sample_container)
            corr_container.append(sample_div)

            literature_div = HT.Div(id="corrtabs-2")
            literature_container = HT.Span()

            literatureTable = HT.TableLite(cellspacing=0, cellpadding=0, width="100%")
            literatureTD = HT.TD(correlationMenus2,HT.BR(),lit_correlation, HT.BR(), HT.BR())
            literatureTD.append(HT.Span("The ", HT.Href(url="/correlationAnnotation.html", target="_blank",text="Literature Correlation"), " (Lit r) between this gene and all other genes is computed",HT.BR(),
                                        "using the ", HT.Href(url="https://grits.eecs.utk.edu/sgo/sgo.html", target="_blank", text="Semantic Gene Organizer"),
                                        " and human, rat, and mouse data from PubMed. ", HT.BR(),"Values are ranked by Lit r, \
                                        but Sample r and Tissue r are also displayed.", HT.BR(), HT.BR(),
                                        HT.Href(url="/glossary.html#Literature", target="_blank", text="More on using Lit r"), Class="fs12"))
            literatureTable.append(literatureTD)

            literature_container.append(literatureTable)
            literature_div.append(literature_container)

            if thisTrait.db != None:
                if (thisTrait.db.type =='ProbeSet'):
                    corr_container.append(literature_div)

            tissue_div = HT.Div(id="corrtabs-3")
            tissue_container = HT.Span()

            tissue_type = HT.Input(type="radio", name="tissue_method", value="4", checked="checked")
            tissue_type2 = HT.Input(type="radio", name="tissue_method", value="5")

            tissueTable = HT.TableLite(cellspacing=0, cellpadding=0, width="100%")
            tissueTD = HT.TD(correlationMenus3,HT.BR(),
                                       "Pearson", tissue_type, "&nbsp;"*3, "Spearman Rank", tissue_type2, HT.BR(), HT.BR(),
                                       tissue_correlation, HT.BR(), HT.BR())
            tissueTD.append(HT.Span("The ", HT.Href(url="/webqtl/main.py?FormID=tissueCorrelation", target="_blank", text="Tissue Correlation"),
            " (Tissue r) estimates the similarity of expression of two genes",HT.BR()," or \
            transcripts across different cells, tissues, or organs (",HT.Href(url="/correlationAnnotation.html#tissue_r", target="_blank", text="glossary"),"). \
            Tissue correlations",HT.BR()," are generated by analyzing expression in multiple samples usually taken from \
            single cases.",HT.BR(),HT.Bold("Pearson")," and ",HT.Bold("Spearman Rank")," correlations have been computed for all pairs \
            of genes",HT.BR()," using data from mouse samples.",
            HT.BR(), Class="fs12"))
            tissueTable.append(tissueTD)

            tissue_container.append(tissueTable)
            tissue_div.append(tissue_container)
            if thisTrait.db != None:
                if (thisTrait.db.type =='ProbeSet'):
                    corr_container.append(tissue_div)

            corr_row.append(HT.TD(corr_container))

            corr_script = HT.Script(language="Javascript")
            corr_script_text = """$(function() { $("#corr_tabs").tabs(); });"""
            corr_script.append(corr_script_text)

            submitTable = HT.TableLite(cellspacing=0, cellpadding=0, width="100%", Class="target4")
            submitTable.append(corr_row)
            submitTable.append(corr_script)

            title3Body.append(submitTable)


    def dispMappingTools(self, fd, title4Body, thisTrait):

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
        chrMenu.append(tuple(["All",-1]))
        for i in range(len(fd.genotype)):
            if  len(fd.genotype[i]) > 1:
                chrMenu.append(tuple([fd.genotype[i].name,i]))

        #Menu for Composite Interval Mapping
        chrMenu2 = HT.Select(name='chromosomes2')
        chrMenu2.append(tuple(["All",-1]))
        for i in range(len(fd.genotype)):
            if  len(fd.genotype[i]) > 1:
                chrMenu2.append(tuple([fd.genotype[i].name,i]))

        if fd.genotype.Mbmap:
            scaleText = HT.Span("Mapping Scale:", Class="ffl fwb fs12")
            scaleMenu1 = HT.Select(name='scale1', onChange="checkUncheck(window.document.dataInput.scale1.value, window.document.dataInput.permCheck1, window.document.dataInput.bootCheck1)")
            scaleMenu1.append(("Megabase",'physic'))
            scaleMenu1.append(("Centimorgan",'morgan'))
            scaleMenu2 = HT.Select(name='scale2', onChange="checkUncheck(window.document.dataInput.scale2.value, window.document.dataInput.permCheck2, window.document.dataInput.bootCheck2)")
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

        if mappingMethodId != None:
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


    def natural_sort(strain_list):

        sorted = []
        for strain in strain_list:
            try:
                strain = int(strain)
                try: sorted[-1] = sorted[-1] * 10 + strain
                except: sorted.append(strain)
            except:
                sorted.append(strain)
        return sorted

    ##########################################
    ##  Function to display trait tables
    ##########################################
    def dispTraitValues(self, fd , title5Body, varianceDataPage, nCols, mainForm, thisTrait):
        traitTableOptions = HT.Div(style="border: 3px solid #EEEEEE; -moz-border-radius: 10px; -webkit-border-radius: 10px; width: 625px; padding: 5px 5px 10px 8px; font-size: 12px; background: #DDDDDD;")
        resetButton = HT.Input(type='button',name='resetButton',value=' Reset ',Class="button")
        blockSamplesField = HT.Input(type="text",style="background-color:white;border: 1px solid black;font-size: 14px;", name="removeField")
        blockSamplesButton = HT.Input(type='button',value=' Block ', name='blockSamples', Class="button")
        showHideNoValue = HT.Input(type='button', name='showHideNoValue', value=' Hide No Value ',Class='button')
        blockMenuSpan = HT.Span(Id="blockMenuSpan")
        blockMenu = HT.Select(name='block_method')

        if fd.genotype.type == "riset":
            allstrainlist_neworder = fd.f1list + fd.strainlist
        else:
            allstrainlist_neworder = fd.f1list + fd.parlist + fd.strainlist

        attribute_ids = []
        attribute_names = []
        try:
            #ZS: Id values for this trait's extra attributes; used to create "Exclude" dropdown and query for attribute values and create
            self.cursor.execute("""SELECT CaseAttribute.Id, CaseAttribute.Name
                                            FROM CaseAttribute, CaseAttributeXRef
                                    WHERE CaseAttributeXRef.ProbeSetFreezeId = '%s' AND
                                            CaseAttribute.Id = CaseAttributeXRef.CaseAttributeId
                                            group by CaseAttributeXRef.CaseAttributeId""" % (str(thisTrait.db.id)))

            exclude_menu = HT.Select(name="exclude_menu")
            dropdown_menus = [] #ZS: list of dropdown menus with the distinct values of each attribute (contained in DIVs so the style parameter can be edited and they can be hidden)

            for attribute in self.cursor.fetchall():
                #attribute_ids.append(attribute[0])
                #attribute_names.append(attribute[1])
                pass
            for this_attr_name in attribute_names:
                #exclude_menu.append((this_attr_name.capitalize(), this_attr_name))
                self.cursor.execute("""SELECT DISTINCT CaseAttributeXRef.Value
                                                FROM CaseAttribute, CaseAttributeXRef
                                                WHERE CaseAttribute.Name = '%s' AND
                                                        CaseAttributeXRef.CaseAttributeId = CaseAttribute.Id""" % (this_attr_name))
                try:
                    distinct_values = self.cursor.fetchall()
                    attr_value_menu_div = HT.Div(style="display:none;", Class="attribute_values") #container used to show/hide dropdown menus
                    attr_value_menu = HT.Select(name=this_attr_name)
                    #attr_value_menu.append(("None", "show_all"))
                    for value in distinct_values:
                        #attr_value_menu.append((str(value[0]), value[0]))
                        pass
                    #attr_value_menu_div.append(attr_value_menu)
                    #dropdown_menus.append(attr_value_menu_div)
                except:
                    pass
        except:
            pass

        other_strains = []
        for strain in thisTrait.data.keys():
            if strain not in allstrainlist_neworder:
                pass
                #other_strains.append(strain)

        if other_strains:
            #blockMenu.append(('%s Only' % fd.RISet,'1'))
            #blockMenu.append(('Non-%s Only' % fd.RISet,'0'))
            #blockMenuSpan.append(blockMenu)
            pass
        else:
            pass

        showHideOutliers = HT.Input(type='button', name='showHideOutliers', value=' Hide Outliers ', Class='button')
        showHideMenuOptions = HT.Span(Id="showHideOptions", style="line-height:225%;")
        if other_strains:
            pass
            #showHideMenuOptions.append(HT.Bold("&nbsp;&nbsp;Block samples by index:&nbsp;&nbsp;&nbsp;&nbsp;"), blockSamplesField, "&nbsp;&nbsp;&nbsp;", blockMenuSpan, "&nbsp;&nbsp;&nbsp;", blockSamplesButton, HT.BR())
        else:
            pass
            #showHideMenuOptions.append(HT.Bold("&nbsp;&nbsp;Block samples by index:&nbsp;&nbsp;&nbsp;&nbsp;"), blockSamplesField, "&nbsp;&nbsp;&nbsp;", blockSamplesButton, HT.BR())

        exportButton = HT.Input(type='button', name='export', value=' Export ', Class='button')
        if len(attribute_names) > 0:
            excludeButton = HT.Input(type='button', name='excludeGroup', value=' Block ', Class='button')
            #showHideMenuOptions.append(HT.Bold("&nbsp;&nbsp;Block samples by group:"), "&nbsp;"*5, exclude_menu, "&nbsp;"*5)
            for menu in dropdown_menus:
                pass
                #showHideMenuOptions.append(menu)
            #showHideMenuOptions.append("&nbsp;"*5, excludeButton, HT.BR())
        #showHideMenuOptions.append(HT.Bold("&nbsp;&nbsp;Options:"), "&nbsp;"*5, showHideNoValue, "&nbsp;"*5, showHideOutliers, "&nbsp;"*5, resetButton, "&nbsp;"*5, exportButton)

        #traitTableOptions.append(showHideMenuOptions,HT.BR(),HT.BR())
        #traitTableOptions.append(HT.Span("&nbsp;&nbsp;Outliers highlighted in ", HT.Bold("&nbsp;yellow&nbsp;", style="background-color:yellow;"), " can be hidden using the ",
        #                                                    HT.Strong(" Hide Outliers "), " button,",HT.BR(),"&nbsp;&nbsp;and samples with no value (x) can be hidden by clicking ",
        #                                                    HT.Strong(" Hide No Value "), "."), HT.BR())


        #dispintro = HT.Paragraph("Edit or delete values in the Trait Data boxes, and use the ", HT.Strong("Reset"), " option as needed.",Class="fs12", style="margin-left:20px;")
        #
        #table = HT.TableLite(cellspacing=0, cellpadding=0, width="100%", Class="target5") #Everything needs to be inside this table object in order for the toggle to work
        #container = HT.Div() #This will contain everything and be put into a cell of the table defined above
        #
        #container.append(dispintro, traitTableOptions, HT.BR())

        #primary_table = HT.TableLite(cellspacing=0, cellpadding=0, Id="sortable1", Class="tablesorter")
        #primary_header = self.getTableHeader(fd=fd, thisTrait=thisTrait, nCols=nCols, attribute_names=attribute_names) #Generate header for primary table object

        other_strainsExist = False
        for strain in thisTrait.data.keys():
            if strain not in allstrainlist_neworder:
                other_strainsExist = True
                break

        primary_body = self.addTrait2Table(fd=fd, varianceDataPage=varianceDataPage, strainlist=allstrainlist_neworder, mainForm=mainForm, thisTrait=thisTrait, other_strainsExist=other_strainsExist, attribute_ids=attribute_ids, attribute_names=attribute_names, strains='primary')

        #primary_table.append(primary_header)
        for i in range(len(primary_body)):
            pass
            #primary_table.append(primary_body[i])

        other_strains = []
        for strain in thisTrait.data.keys():
            if strain not in allstrainlist_neworder:
                pass
                #allstrainlist_neworder.append(strain)
                #other_strains.append(strain)

        if other_strains:
            other_table = HT.TableLite(cellspacing=0, cellpadding=0, Id="sortable2", Class="tablesorter") #Table object with other (for example, non-BXD / MDP) traits
            other_header = self.getTableHeader(fd=fd, thisTrait=thisTrait, nCols=nCols, attribute_names=attribute_names) #Generate header for other table object; same function is used as the one used for the primary table, since the header is the same
            other_strains.sort() #Sort other strains
            other_strains = map(lambda X:"_2nd_"+X, fd.f1list + fd.parlist) + other_strains #Append F1 and parent strains to the beginning of the sorted list of other strains

            MDPText = HT.Span("Samples:", Class="ffl fwb fs12")
            MDPMenu1 = HT.Select(name='MDPChoice1')
            MDPMenu2 = HT.Select(name='MDPChoice2')
            MDPMenu3 = HT.Select(name='MDPChoice3')
            #MDPMenu1.append(('%s Only' % fd.RISet,'1'))
            #MDPMenu2.append(('%s Only' % fd.RISet,'1'))
            #MDPMenu3.append(('%s Only' % fd.RISet,'1'))
            #MDPMenu1.append(('Non-%s Only' % fd.RISet,'2'))
            #MDPMenu2.append(('Non-%s Only' % fd.RISet,'2'))
            #MDPMenu3.append(('Non-%s Only' % fd.RISet,'2'))
            #MDPMenu1.append(('All Cases','0'))
            #MDPMenu2.append(('All Cases','0'))
            #MDPMenu3.append(('All Cases','0'))
            #self.MDPRow1.append(HT.TD(MDPText),HT.TD(MDPMenu1))
            #self.MDPRow2.append(HT.TD(MDPText),HT.TD(MDPMenu2))
            #self.MDPRow3.append(HT.TD(MDPText),HT.TD(MDPMenu3))

            other_body = self.addTrait2Table(fd=fd, varianceDataPage=varianceDataPage, strainlist=other_strains, mainForm=mainForm, thisTrait=thisTrait, attribute_ids=attribute_ids, attribute_names=attribute_names, strains='other')

            #other_table.append(other_header)
            for i in range(len(other_body)):
                pass
                #other_table.append(other_body[i])
        else:
            pass

        if other_strains or (fd.f1list and thisTrait.data.has_key(fd.f1list[0])) \
                or (fd.f1list and thisTrait.data.has_key(fd.f1list[1])):
            fd.allstrainlist = allstrainlist_neworder

        ## We put isSE into hddn
        #if nCols == 6 and fd.varianceDispName != 'Variance':
        #    #mainForm.append(HT.Input(name='isSE', value="yes", type='hidden'))
        #    hddn['isSE'] = "yes"

        primary_div = HT.Div(primary_table, Id="primary") #Container for table with primary (for example, BXD) strain values
        #container.append(primary_div)

        if other_strains:
            other_div = HT.Div(other_table, Id="other") #Container for table with other (for example, Non-BXD/MDP) strain values
            #container.append(HT.Div('&nbsp;', height=30))
            #container.append(other_div)

        table.append(HT.TR(HT.TD(container)))
        #title5Body.append(table)

    def addTrait2Table(self, fd, varianceDataPage, strainlist, mainForm, thisTrait, other_strainsExist=None, attribute_ids=[], attribute_names=[], strains='primary'):
        #XZ, Aug 23, 2010: I commented the code related to the display of animal case
        #strainInfo = thisTrait.has_key('strainInfo') and thisTrait.strainInfo

        table_body = []
        vals = []

        for i, strainNameOrig in enumerate(strainlist):
            strainName = strainNameOrig.replace("_2nd_", "")

            try:
                thisval = thisTrait.data[strainName].val
                thisvar = thisTrait.data[strainName].var
                thisValFull = [strainName,thisval,thisvar]
            except:
                continue

            vals.append(thisValFull)

        upperBound, lowerBound = Plot.findOutliers(vals) # ZS: Values greater than upperBound or less than lowerBound are considered outliers.

        for i, strainNameOrig in enumerate(strainlist):

            trId = strainNameOrig
            selectCheck = HT.Input(type="checkbox", name="selectCheck", value=trId, Class="checkbox", onClick="highlight(this)")

            strainName = strainNameOrig.replace("_2nd_", "")
            strainNameAdd = ''
            if fd.RISet == 'AXBXA' and strainName in ('AXB18/19/20','AXB13/14','BXA8/17'):
                strainNameAdd = HT.Href(url='/mouseCross.html#AXB/BXA', text=HT.Sup('#'), Class='fs12', target="_blank")

            try:
                thisval, thisvar, thisNP = thisTrait.data[strainName].val, thisTrait.data[strainName].var, thisTrait.data[strainName].N
                if thisNP:
                    mainForm.append(HT.Input(name='N'+strainName, value=thisNP, type='hidden'))
                else:
                    pass
            except:
                thisval = thisvar = 'x'

            try:
                traitVal = thisval
                dispVal = "%2.3f" % thisval
            except:
                traitVal = ''
                dispVal = 'x'

            strainNameDisp = HT.Span(strainName, Class='fs14 fwn ffl')

            if varianceDataPage:
                try:
                    traitVar = thisvar
                    dispVar = "%2.3f" % thisvar
                except:
                    traitVar = ''
                    dispVar = 'x'

            if thisval == 'x':
                traitVar = '' #ZS: Used to be 0, but it doesn't seem like a good idea for values of 0 to *always* be at the bottom when you sort; it makes more sense to put "nothing"

                className = 'fs13 b1 c222 '
                valueClassName = 'fs13 b1 c222 valueField '
                rowClassName = 'novalue '
            else:
                if (thisval >= upperBound) or (thisval <= lowerBound):
                    className = 'fs13 b1 c222 outlier '
                    valueClassName = 'fs13 b1 c222 valueField '
                    rowClassName = 'outlier'
                else:
                    className = 'fs13 b1 c222 '
                    valueClassName = 'fs13 b1 c222 valueField '
                    rowClassName = ' '

            if varianceDataPage:
                varClassName = valueClassName + str(traitVar)
            valueClassName += str(traitVal)

            if strainNameOrig == strainName:
                if other_strainsExist and strainNameOrig in (fd.parlist + fd.f1list):
                    ########################################################################################################################################################
                      # ZS: Append value and variance to the value and variance input fields' list of classes; this is so the javascript can update the value when the user
                      # changes it. The updated value is then used when the table is sorted (tablesorter.js). This needs to be done because the "value" attribute is immutable.
                    #########################################################################################################################################################

                    valueField = HT.Input(name=strainNameOrig, size=8, maxlength=8, style="text-align:right; background-color:#FFFFFF;", value=dispVal,
                            onChange= "javascript:this.form['_2nd_%s'].value=this.form['%s'].value;" % (strainNameOrig.replace("/", ""), strainNameOrig.replace("/", "")), Class=valueClassName)
                    if varianceDataPage:
                        seField = HT.Input(name='V'+strainNameOrig, size=8, maxlength=8, style="text-align:right", value=dispVar,
                                onChange= "javascript:this.form['V_2nd_%s'].value=this.form['V%s'].value;" % (strainNameOrig.replace("/", ""), strainNameOrig.replace("/", "")), Class=varClassName)
                else:
                    valueField = HT.Input(name=strainNameOrig, size=8, maxlength=8, style="text-align:right; background-color:#FFFFFF;", value=dispVal, Class=valueClassName)
                    if varianceDataPage:
                        seField = HT.Input(name='V'+strainNameOrig, size=8, maxlength=8, style="text-align:right", value=dispVar, Class=varClassName)
            else:
                valueField = HT.Input(name=strainNameOrig, size=8, maxlength=8, style="text-align:right", value=dispVal,
                                      onChange= "javascript:this.form['%s'].value=this.form['%s'].value;" % (strainNameOrig.replace("/", ""), strainNameOrig.replace("/", "")), Class=valueClassName)
                if varianceDataPage:
                    seField = HT.Input(name='V'+strainNameOrig, size=8, maxlength=8, style="text-align:right", value=dispVar,
                            onChange= "javascript:this.form['V%s'].value=this.form['V%s'].value;" % (strainNameOrig.replace("/", ""), strainNameOrig.replace("/", "")), Class=varClassName)

            if (strains == 'primary'):
                table_row = HT.TR(Id="Primary_"+str(i+1), Class=rowClassName)
            else:
                table_row = HT.TR(Id="Other_"+str(i+1), Class=rowClassName)

            if varianceDataPage:
                table_row.append(HT.TD(str(i+1), selectCheck, width=45, align='right', Class=className))
                table_row.append(HT.TD(strainNameDisp, strainNameAdd, align='right', width=100, Class=className))
                table_row.append(HT.TD(valueField, width=70, align='right', Id="value_"+str(i)+"_"+strains, Class=className))
                table_row.append(HT.TD("&plusmn;", width=20, align='center', Class=className))
                table_row.append(HT.TD(seField, width=80, align='right', Id="SE_"+str(i)+"_"+strains, Class=className))
            else:
                table_row.append(HT.TD(str(i+1), selectCheck, width=45, align='right', Class=className))
                table_row.append(HT.TD(strainNameDisp, strainNameAdd, align='right', width=100, Class=className))
                table_row.append(HT.TD(valueField, width=70, align='right', Id="value_"+str(i)+"_"+strains, Class=className))

            if thisTrait and thisTrait.db and thisTrait.db.type =='ProbeSet':
                if len(attribute_ids) > 0:

                    #ZS: Get StrainId value for the next query
                    self.cursor.execute("""SELECT Strain.Id
                                                    FROM Strain, StrainXRef, InbredSet
                                                    WHERE Strain.Name = '%s' and
                                                            StrainXRef.StrainId = Strain.Id and
                                                            InbredSet.Id = StrainXRef.InbredSetId and
                                                            InbredSet.Name = '%s'""" % (strainName, fd.RISet))

                    strain_id = self.cursor.fetchone()[0]

                    attr_counter = 1 # This is needed so the javascript can know which attribute type to associate this value with for the exported excel sheet (each attribute type being a column).
                    for attribute_id in attribute_ids:

                        #ZS: Add extra case attribute values (if any)
                        self.cursor.execute("""SELECT Value
                                                        FROM CaseAttributeXRef
                                                WHERE ProbeSetFreezeId = '%s' AND
                                                        StrainId = '%s' AND
                                                        CaseAttributeId = '%s'
                                                                group by CaseAttributeXRef.CaseAttributeId""" % (thisTrait.db.id, strain_id, str(attribute_id)))

                        attributeValue = self.cursor.fetchone()[0] #Trait-specific attributes, if any

                        #ZS: If it's an int, turn it into one for sorting (for example, 101 would be lower than 80 if they're strings instead of ints)
                        try:
                            attributeValue = int(attributeValue)
                        except:
                            pass

                        span_Id = strains+"_attribute"+str(attr_counter)+"_sample"+str(i+1)
                        attr_container = HT.Span(attributeValue, Id=span_Id)
                        attr_className = str(attributeValue) + "&nbsp;" + className
                        table_row.append(HT.TD(attr_container, align='right', Class=attr_className))
                        attr_counter += 1

            table_body.append(table_row)
        return table_body

    def getTableHeader(self, fd, thisTrait, nCols, attribute_names):

        table_header = HT.TR()

        col_class = "fs13 fwb ff1 b1 cw cbrb"

        if nCols == 6:
            try:
                if fd.varianceDispName:
                    pass
            except:
                fd.varianceDispName = 'Variance'

            table_header.append(HT.TH('Index', align='right', width=60, Class=col_class),
                    HT.TH('Sample', align='right', width=100, Class=col_class),
                    HT.TH('Value', align='right', width=70, Class=col_class),
                    HT.TH('&nbsp;', width=20, Class=col_class),
                    HT.TH(fd.varianceDispName, align='right', width=80, Class=col_class))

        elif nCols == 4:
            table_header.append(HT.TH('Index', align='right', width=60, Class=col_class),
                    HT.TH('Sample', align='right', width=100, Class=col_class),
                    HT.TH('Value', align='right', width=70, Class=col_class))

        else:
            pass

        if len(attribute_names) > 0:
            i=0
            for attribute in attribute_names:
                char_count = len(attribute)
                cell_width = char_count * 14
                table_header.append(HT.TH(attribute, align='right', width=cell_width, Class="attribute_name " + col_class))
                i+=1

        return table_header


    def getSortByValue(self):

        sortby = ("", "")

        return sortby
