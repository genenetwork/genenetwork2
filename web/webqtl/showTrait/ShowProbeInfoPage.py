# Copyright (C) University of Tennessee Health Science Center, Memphis, TN.
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License
# as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Affero General Public License for more details.
#
# This program is available from Source Forge: at GeneNetwork Project
# (sourceforge.net/projects/genenetwork/).
#
# Contact Drs. Robert W. Williams and Xiaodong Zhou (2010)
# at rwilliams@uthsc.edu and xzhou15@uthsc.edu
#
#
#
# This module is used by GeneNetwork project (www.genenetwork.org)
#
# Created by GeneNetwork Core Team 2010/08/10
#
# Last updated by GeneNetwork Core Team 2010/10/20

import string
import sys,os

import cPickle

import reaper
from htmlgen import HTMLgen2 as HT

from base import webqtlConfig
from utility import webqtlUtil
from dbFunction import webqtlDatabaseFunction
from base.templatePage import templatePage
from base.webqtlDataset import webqtlDataset
from base.webqtlTrait import webqtlTrait
from utility.THCell import THCell
from utility.TDCell import TDCell

#########################################
#      Probe Infomation Page
#########################################

class ShowProbeInfoPage(templatePage):

	def __init__(self, fd):

		templatePage.__init__(self, fd)

		if not self.openMysql():
			return
		
		fd.readGenotype()
		TD_LR = HT.TD(height=200,width="100%",bgColor='#eeeeee')
		self.database = fd.formdata.getfirst('database')
		self.ProbeSetID = fd.formdata.getfirst('ProbeSetID')
		self.CellID = fd.formdata.getfirst('CellID')
		
		self.db = webqtlDataset(self.database, self.cursor)
		thisTrait = webqtlTrait(db= self.db, cursor=self.cursor, name=self.ProbeSetID) #, cellid=CellID)
		thisTrait.retrieveInfo()
		
		try:
			self.cursor.execute('SELECT ProbeFreeze.Name FROM ProbeFreeze,ProbeSetFreeze WHERE ProbeFreeze.Id = ProbeSetFreeze.ProbeFreezeId and ProbeSetFreeze.Name = "%s"' % self.db.name)
			self.probeDatabase = self.cursor.fetchall()[0][0]
			self.probeInfoDatabase = 'Probe'
		except:
			heading = 'Probe Information'
			intro = ['Trying to retrieve the probe information for ProbeSet ',HT.Span('%s' % self.ProbeSetID, Class="fwb cdg"),' in Database ',HT.Href(text='%s' % self.db.fullname,url=webqtlConfig.infopagehref % self.database)]
			detail = ['The information you just requested is not available at this time.']
			self.error(heading=heading,intro=intro,detail=detail)
			return


		form = HT.Form(cgi= os.path.join(webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE), enctype='multipart/form-data', name='showDatabase', submit=HT.Input(type='hidden'))
		hddn = {'FormID':'showDatabase','ProbeSetID':'_','database':'_','CellID':'_','RISet':fd.RISet, 'incparentsf1':'on'}
		if fd.RISet == 'BXD':
			hddn['parentsf1']='ON'
			
		for key in hddn.keys():
			form.append(HT.Input(name=key, value=hddn[key], type='hidden'))


		#Buttons on search page
		linkinfo ="%s/probeInfo.html" % webqtlConfig.PORTADDR
		mintmap = "" 
		probeinfo = HT.Input(type='button' ,name='mintmap',value='Info', onClick="openNewWin('%s');" % linkinfo, Class="button")
		cormatrix = HT.Href(url="#redirect", onClick="databaseFunc(document.getElementsByName('showDatabase')[0], 'corMatrix');")
		cormatrix_img = HT.Image("/images/correlation_matrix1_final.jpg", alt="Correlation Matrix and PCA", title="Correlation Matrix and PCA", style="border:none;")
		cormatrix.append(cormatrix_img)
		heatmap = HT.Href(url="#redirect", onClick="databaseFunc(document.getElementsByName('showDatabase')[0], 'heatmap');")
		heatmap_img = HT.Image("/images/heatmap2_final.jpg", name='mintmap', alt="QTL Heat Map and Clustering", title="QTL Heatmap and Clustering", style="border:none;")
		heatmap.append(heatmap_img)
		if self.ProbeSetID[-2:] in ('_A', '_B'):
			thisProbeSetID = self.ProbeSetID[:-2]
		else:
			thisProbeSetID = self.ProbeSetID
		thisurl = 'http://www.ensembl.org/Mus_musculus/featureview?type=AffyProbe&id=%s' % thisProbeSetID
		verifyButton = HT.Input(type="button",value="Verify Ensembl",onClick= "openNewWin('%s')" % thisurl, Class="button")
		
		addselect = HT.Input(type='button' ,name='addselect',value='Add to Collection', onClick="addRmvSelection('%s', this.form, 'addToSelection');"  % fd.RISet,Class="button")
		selectall = HT.Input(type='button' ,name='selectall',value='Select All', onClick="checkAll(this.form);",Class="button")
		selectpm = HT.Input(type='button' ,name='selectall',value='Select PM', onClick="checkPM(this.form);",Class="button")
		selectmm = HT.Input(type='button' ,name='selectall',value='Select MM', onClick="checkMM(this.form);",Class="button")
		selectinvert = HT.Input(type='button' ,name='selectinvert',value='Select Invert', onClick="checkInvert(this.form);",Class="button")
		reset = HT.Input(type='reset',name='',value='Select None',Class="button")
		chrMenu = HT.Input(type='hidden',name='chromosomes',value='all')
		probedata = HT.Input(type='hidden',name='probedata',value='all')
		
		url_rudi_track = self.getProbeTrackURL(self.probeDatabase, self.ProbeSetID)
		if url_rudi_track:		
		   rudi_track = HT.Input(type='button', name='ruditrack', value='Probe Track', onClick="openNewWin('%s')"%url_rudi_track, Class="button")
		else: rudi_track = None
		
		pinfopage = "/probeInfo.html"
		
		#updated by NL: 07-22-2011  get chosenStrains
		_f1, _f12, _mat, _pat = webqtlUtil.ParInfo[fd.RISet]
		chosenStrains="%s,%s"%(_mat,_pat)
		tblobj = {}
		tblobj['header']=[]

		tblobj['header'].append([
			THCell(HT.TD("", Class="cbrb cw fwb fs13 b1", rowspan=2,nowrap='ON'), sort=0),
			THCell(HT.TD(HT.Href(target="_PROBEINFO", url=pinfopage+"#probe", text=HT.Span('Probe', Class="cw fwb fs13")), HT.Sup(HT.Italic('1')), Class="cbrb cw fwb fs13 b1",align='center',rowspan=2,nowrap='ON'), text="probe", idx=1), 
			THCell(HT.TD(HT.Href(text=HT.Span('Sequence', Class="cw fwb fs13"), target="_PROBEINFO", url=pinfopage+"#Sequence"),HT.Sup(HT.Italic('2')), Class="cbrb cw fwb fs13 b1", align='center',rowspan=2,nowrap='ON'), text="seq", idx=2), 
			THCell(HT.TD(HT.Href(text=HT.Span('bl2seq', Class="cw fwb fs13"), target="_PROBEINFO", url=pinfopage+"#bl2seq"),HT.Sup(HT.Italic('3')), Class="cbrb cw fwb fs13 b1", align='center',rowspan=2,nowrap='ON'), sort=0), 
			THCell(HT.TD(HT.Href(text=HT.Span('Exons', Class="cw fwb fs13"), target="_PROBEINFO", url=pinfopage+"#Exon"),HT.Sup(HT.Italic('4')), Class="cbrb cw fwb fs13 b1",align='center',rowspan=2,nowrap='ON'), sort=0),
			THCell(HT.TD(HT.Href(text=HT.Span('Tm &deg;C', Class="cw fwb fs13"), target="_PROBEINFO", url=pinfopage+"#Tm"),HT.Sup(HT.Italic('5')), Class="cbrb cw fwb fs13 b1",align='center',rowspan=2,nowrap='ON'), text="tm", idx=5),
			THCell(HT.TD(HT.Href(text=HT.Span('Stacking Energy K', HT.Sub('B'),'T', Class="cw fwb fs13"), target="_PROBEINFO", url=pinfopage+"#KBT"),HT.Sup(HT.Italic('6')), Class="cbrb cw fwb fs13 b1",align='center',colspan=2,NOWRAP="yes",nowrap='ON'), sort=0),
			THCell(HT.TD(HT.Href(text=HT.Span('Mean', Class="cw fwb fs13"), target="_PROBEINFO", url=pinfopage+"#Mean"),HT.Sup(HT.Italic('7')), Class="cbrb cw fwb fs13 b1",align='center',rowspan=2,nowrap='ON'), text="mean", idx=8),
			THCell(HT.TD(HT.Href(text=HT.Span('Stdev', Class="cw fwb fs13"), target="_PROBEINFO", url=pinfopage+"#Stdev"),HT.Sup(HT.Italic('8')), Class="cbrb cw fwb fs13 b1",align='center',rowspan=2,nowrap='ON'), text="std", idx=9),
			THCell(HT.TD(HT.Href(text=HT.Span('Probe h2', Class="cw fwb fs13"), target="_PROBEINFO", url=pinfopage+"#h2"),HT.Sup(HT.Italic('9')), Class="cbrb cw fwb fs13 b1",align='center',rowspan=2,NOWRAP="yes"), text="h2", idx=10),
			THCell(HT.TD(HT.Href(text=HT.Span('Probe Location', Class="cw fwb fs13"), target="_PROBEINFO", url=pinfopage+"#location"), HT.Sup(HT.Italic('10')),Class="cbrb cw fwb fs13 b1",align='center',colspan=3)),
			THCell(HT.TD(HT.Href(text=HT.Span('SNPs', HT.BR(), '(Across all strains)', Class="cw fwb fs13"), target="_PROBEINFO", url=pinfopage+"#snps"), HT.Sup(HT.Italic('11')),Class="cbrb cw fwb fs13 b1",align='center',rowspan=2,NOWRAP="yes")),
			THCell(HT.TD(HT.Href(text=HT.Span('SNPs', HT.BR(),'(Different alleles only between %s and %s)'%(_mat,_pat), Class="cw fwb fs13"), target="_PROBEINFO", url=pinfopage+"#snps"), HT.Sup(HT.Italic('11')),Class="cbrb cw fwb fs13 b1",align='center',rowspan=2,NOWRAP="yes"))

		])
		
		tblobj['header'].append([
			THCell(HT.TD(HT.Span('GSB', Class="cw fwb fs13"),align='center', Class="cbrb ffl fwb fs13 b1",), text="gsb", idx=6),
			THCell(HT.TD(HT.Span('NSB', Class="cw fwb fs13"),align='center', Class="cbrb ffl fwb fs13 b1",), text="nsb", idx=7),
			THCell(HT.TD(HT.Span('Chr', Class="cw fwb fs13"), align='center', Class="cbrb ffl2 fwb fs13 b1",)),
			THCell(HT.TD(HT.Span('Start', Class="cw fwb fs13"),align='center', Class="cbrb ffl fwb fs13 b1",)),
			THCell(HT.TD(HT.Span('End', Class="cw fwb fs13"),align='center', Class="cbrb ffl fwb fs13 b1",)),
		])
		
		tblobj['body'] = []
		
		blatbutton = ''

		fetchField = ['Probe.Name','Probe.Sequence','Probe.ExonNo','Probe.Tm', 'Probe.E_GSB','Probe.E_NSB', 'ProbeH2.h2', 'ProbeH2.weight']

		query = "SELECT %s FROM (Probe, ProbeSet, ProbeFreeze) left join ProbeH2  on ProbeH2.ProbeId = Probe.Id and ProbeH2.ProbeFreezeId = ProbeFreeze.Id WHERE ProbeSet.Name = '%s' and Probe.ProbeSetId = ProbeSet.Id and ProbeFreeze.Name = '%s' order by Probe.SerialOrder" % (string.join(fetchField,','), self.ProbeSetID, self.probeDatabase)
		self.cursor.execute(query)
		results = self.cursor.fetchall()
		
		blatsequence = ""
		
		# add by NL: get strains' name in SnpPattern database table
		strainsInSnpPatternDBtable=self.getStrainNameIndexPair()  # after snpBrowserPage.py change to MVC, this function can be removed in this class and called from other class; 
		allStrainNameList=[v[0] for v in strainsInSnpPatternDBtable]
			
		speciesid = webqtlDatabaseFunction.retrieveSpeciesId(cursor=self.cursor,RISet=fd.RISet)
		for result in results:
			"""
			ProbeId, CellID,Sequence,ExonNo,Tm, E_GSB,E_NSB = map(self.nullRecord,result)
			h2 = ''
			query = "SELECT h2 FROM ProbeH2 WHERE ProbeFreezeId = '%s' and ProbeId=%s" % (self.probeDatabase, ProbeId)
			self.cursor.execute(query)
			results = self.cursor.fetchall()
			"""

			CellID,Sequence,ExonNo,Tm, E_GSB,E_NSB,h2, weight = map(self.nullRecord,result)
			
	
			Average = ''
			STDEV = ''
			mean = -10000.0
			stdev = -10000.0
			try:
				thisTrait.cellid = CellID
				thisTrait.retrieveData()
		
				mean, median, var, stdev, sem, N = reaper.anova(thisTrait.exportInformative()[1])
			
				if mean:
					Average = '%2.2f' % mean
				if stdev:
					STDEV = '%2.2f' % stdev
			except:
				pass

			if CellID == self.CellID:
				bkColor = "cbrdull fs11 b1"
			else:
				bkColor = "fs11 b1"
			seqcolor= ''
			
			if thisTrait.blatseq:
				blatsequence = thisTrait.blatseq
				if int(CellID[-1]) % 2 == 1:
					seqcolor= 'cdg'
			else:
				if int(CellID[-1]) % 2 == 1:
					seqcolor= 'cdg'
					blatsequence += string.strip(Sequence)
						
			if thisTrait.genbankid  and (int(CellID[-1]) % 2 == 1):
				probeurl = 'http://www.ncbi.nlm.nih.gov/blast/bl2seq/wblast2.cgi?one=%s&sseq=%s'  % (thisTrait.genbankid, Sequence)
				probefy1 = HT.Input(type="button",value="Blast",onClick= "openNewWin('%s')" % probeurl, Class="buttonsmaller")
			else:  
				probefy1 = ''
			
			traitName = str(thisTrait)

			#XZ, Aug 08, 2011: Note that probesets on some affy chips are not name as "xxx_at" (i.e., Affy Mouse Gene 1.0 ST (GPL6246)). 
			#EnsemblProbeSetID = self.ProbeSetID[0:self.ProbeSetID.index('_at')+3]
			EnsemblProbeSetID = self.ProbeSetID
			if '_at' in self.ProbeSetID:
				EnsemblProbeSetID = self.ProbeSetID[0:self.ProbeSetID.index('_at')+3]

			self.cursor.execute('''
					SELECT EnsemblProbeLocation.* 
					FROM EnsemblProbeLocation, EnsemblProbe, EnsemblChip, GeneChipEnsemblXRef, ProbeFreeze
					WHERE EnsemblProbeLocation.ProbeId=EnsemblProbe.Id and EnsemblProbe.ChipId=GeneChipEnsemblXRef.EnsemblChipId and
						GeneChipEnsemblXRef.GeneChipId=ProbeFreeze.ChipId and EnsemblProbe.Name=%s and EnsemblProbe.ProbeSet=%s and 
						ProbeFreeze.Name=%s group by Chr, Start, End'''
					,(CellID, EnsemblProbeSetID, self.probeDatabase))
			LocationFields = self.cursor.fetchall()

			Chr=''
			Start=''
			End=''
			if (len(LocationFields)>=1):
				Chr,Start,End,Strand,MisMatch,ProbeId = map(self.nullRecord,LocationFields[0])
				Start /= 1000000.0
				End /= 1000000.0
			if (len(LocationFields)>1):
				self.cursor.execute('''
						SELECT ProbeSet.Chr, ProbeSet.Mb FROM ProbeSet, ProbeFreeze 
						WHERE ProbeSet.ChipId=ProbeFreeze.ChipId and ProbeSet.Name=%s and ProbeFreeze.Name=%s'''
						,(self.ProbeSetID, self.probeDatabase))
				ProbeSetChr, ProbeSetMb = map(self.nullRecord,self.cursor.fetchall()[0])
					
				self.cursor.execute('''
						SELECT EnsemblProbeLocation.*, ABS(EnsemblProbeLocation.Start/1000000-%s) as Mb 
						FROM EnsemblProbeLocation, EnsemblProbe, EnsemblChip, GeneChipEnsemblXRef, ProbeFreeze
						WHERE EnsemblProbeLocation.ProbeId=EnsemblProbe.Id and EnsemblProbe.ChipId=GeneChipEnsemblXRef.EnsemblChipId and
							GeneChipEnsemblXRef.GeneChipId=ProbeFreeze.ChipId and EnsemblProbe.Name=%s and EnsemblProbe.ProbeSet=%s and
							EnsemblProbeLocation.Chr=%s and ProbeFreeze.Name=%s order by Mb limit 1'''
						,(ProbeSetMb, CellID, EnsemblProbeSetID, ProbeSetChr, self.probeDatabase))
				NewLocationFields = self.cursor.fetchall()
				if (len(NewLocationFields)>0):
					Chr,Start,End,Strand,MisMatch,ProbeId,Mb = map(self.nullRecord,NewLocationFields[0])
					Start /= 1000000.0
					End /= 1000000.0
					
			snp_collection = []	
			snpDiff_collection=[]
			
			startIndex=3
			if Chr != '' and Start != '' and End != '' and speciesid != None:
									
				self.cursor.execute('''
						   SELECT a.SnpName, a.Id, b.* FROM SnpAll a, SnpPattern b
						   WHERE a.Chromosome=%s and a.Position>=%s and a.Position<=%s 
						   and a.SpeciesId=%s and a.Id=b.SnpId'''
							,(Chr, Start, End, speciesid)) #chr,Start, End, 1))							
				snpresults = self.cursor.fetchall()
				
				index1=allStrainNameList.index(_mat) #_mat index in results
				index2=allStrainNameList.index(_pat) #_pat index in results
			
				for v in snpresults:
					#updated by NL: 07-22-2011  check 'limit to' to get snpBrowser snpresults
					snp_collection.append(HT.Href(text=v[0], url=os.path.join(webqtlConfig.CGIDIR, 
							"main.py?FormID=SnpBrowserResultPage&submitStatus=1&customStrain=1")+ "&geneName=%s" % v[0], Class="fs12 fwn", target="_blank"))
					snp_collection.append(HT.BR())
					#updated by NL: 07-27-2011  link snp info for different allele only	
					strain1_allele=v[startIndex+index1]
					strain2_allele=v[startIndex+index2]
					
					if strain1_allele!=strain2_allele:
						snpDiff_collection.append(HT.Href(text=v[0], url=os.path.join(webqtlConfig.CGIDIR, 
								"main.py?FormID=SnpBrowserResultPage&submitStatus=1&customStrain=1&diffAlleles=1&chosenStrains=%s"%chosenStrains)+ "&geneName=%s" % v[0], Class="fs12 fwn", target="_blank"))
						snpDiff_collection.append(HT.BR())
							

			tr = []	
			tr.append(TDCell(HT.TD(HT.Input(type="checkbox", Class='checkbox', name="searchResult",value=traitName, onClick="highlight(this)"), align="right", Class=bkColor, nowrap="on"), text=traitName))
			
			tr.append(TDCell(HT.TD(HT.Href(text=CellID, url = "javascript:showDatabase2('%s','%s','%s');" % (self.database,self.ProbeSetID,CellID),Class="fs12 fwn"),Class=bkColor), traitName, traitName.upper()))
			
			tr.append(TDCell(HT.TD(Sequence, Class=bkColor + " %s ffmono fs14" % seqcolor),Sequence,Sequence.upper()))
			tr.append(TDCell(HT.TD(probefy1,align='center',Class=bkColor))) 
			tr.append(TDCell(HT.TD(ExonNo,align='center',Class=bkColor)))
			
			try:
				TmValue = float(Tm)
			except:
				TmValue = 0.0
			tr.append(TDCell(HT.TD(Tm,align='center',Class=bkColor), Tm, TmValue))
			
			try:
				E_GSBValue = float(E_GSB)
			except:
				E_GSBValue = -10000.0
			tr.append(TDCell(HT.TD(E_GSB,align='center',Class=bkColor), E_GSB, E_GSBValue))

			try:
				E_NSBValue = float(E_NSB)
			except:
				E_NSBValue = -10000.0
			tr.append(TDCell(HT.TD(E_NSB,align='center',Class=bkColor), E_NSB, E_NSBValue))
			
			tr.append(TDCell(HT.TD(Average,align='center',Class=bkColor), Average, mean))
			tr.append(TDCell(HT.TD(STDEV,align='center',Class=bkColor), STDEV, stdev))

			try:
				h2Value = float(h2)
			except:
				h2Value = -10000.0
			tr.append(TDCell(HT.TD(h2,align='center',Class=bkColor), h2, h2Value))

			tr.append(TDCell(HT.TD(Chr,align='left',Class=bkColor)))
			tr.append(TDCell(HT.TD(Start,align='left',Class=bkColor)))
			tr.append(TDCell(HT.TD(End,align='left',Class=bkColor)))

			snp_td = HT.TD(align='left',Class=bkColor)
			for one_snp_href in snp_collection:
			    snp_td.append(one_snp_href)
	
			tr.append(TDCell(snp_td)) 
			
			#07-27-2011:add by NL: show SNP results for different allele only
			snpDiff_td= HT.TD(align='left', valign='top', Class=bkColor)
			for one_snpDiff_href in snpDiff_collection:
			    snpDiff_td.append(one_snpDiff_href)
			tr.append(TDCell(snpDiff_td))
			
			tblobj['body'].append(tr)
		
		# import cPickle
		filename = webqtlUtil.genRandStr("Probe_")
		objfile = open('%s.obj' % (webqtlConfig.TMPDIR+filename), 'wb')
		cPickle.dump(tblobj, objfile)
		objfile.close()
		# NL, 07/27/2010. genTableObj function has been moved from templatePage.py to webqtlUtil.py;		
		div = HT.Div(webqtlUtil.genTableObj(tblobj=tblobj, file=filename, sortby=("", ""), tableID = "sortable", addIndex = "1"), Id="sortable")

		#UCSC
		_Species = webqtlDatabaseFunction.retrieveSpecies(cursor=self.cursor, RISet=fd.RISet)
		if _Species == "rat":
			thisurl = webqtlConfig.UCSC_BLAT % ('rat', 'rn3', blatsequence)
		elif _Species == "mouse":
			thisurl = webqtlConfig.UCSC_BLAT % ('mouse', 'mm9', blatsequence)
		else:
			thisurl = ""
		if thisurl:	
			blatbutton = HT.Input(type='button' ,name='blatPM',value='Verify UCSC', onClick="window.open('%s','_blank')" % thisurl,Class="button")
		else:
			blatbutton = ""
		
		#GenBank
		genbankSeq = ""
		if thisTrait.genbankid:
			self.cursor.execute("SELECT Sequence FROM Genbank WHERE Id = '%s'" % thisTrait.genbankid )
			genbankSeq = self.cursor.fetchone()
			if genbankSeq:
				genbankSeq = genbankSeq[0]
		
		if genbankSeq: 
			if _Species == "rat":
				thisurl2 = webqtlConfig.UCSC_BLAT % ('rat', 'rn3', genbankSeq)
			if _Species == "mouse":
				thisurl2 = webqtlConfig.UCSC_BLAT % ('mouse', 'mm9', genbankSeq)
		else:
			thisurl2 = ''
		if thisurl2:	
			blatbutton2 = HT.Input(type='button' ,name='blatPM',value='Verify GenBank', onClick="window.open('%s','_blank')" % thisurl2,Class="button")
		else:
			blatbutton2 = ""
		
		#Snp
		snpBrowser = ""
		if thisTrait.symbol and _Species == 'mouse':
			self.cursor.execute("select geneSymbol from GeneList where geneSymbol = %s", thisTrait.symbol)
			geneName = self.cursor.fetchone()
			if geneName:
				snpurl = os.path.join(webqtlConfig.CGIDIR, "main.py?FormID=snpBrowser") + "&geneName=%s" % geneName[0]	
			else:
				if thisTrait.chr and thisTrait.mb:
					snpurl = os.path.join(webqtlConfig.CGIDIR, "main.py?FormID=snpBrowser") + \
							"&chr=%s&start=%2.6f&end=%2.6f" % (thisTrait.chr, thisTrait.mb-0.002, thisTrait.mb+0.002)
				else:
					snpurl = ""

			if snpurl:
				snpBrowser = HT.Input(type="button",value="SNP Browser",onClick= \
						"openNewWin('%s')" % snpurl, Class="button")

			else:
				snpBrowser = ""
		#end if
		
		heading = HT.Paragraph('Probe Information', Class="title")
		intro = HT.Paragraph('The table below lists information of all probes of probe set ',HT.Span(self.ProbeSetID, Class="fwb fs13"),' from database ', HT.Span(self.probeDatabase, Class="fwb fs13"), ".")
		buttons = HT.Paragraph(probedata,probeinfo,heatmap,cormatrix,blatbutton,blatbutton2,verifyButton,snpBrowser, HT.P(),selectall,selectpm,selectmm,selectinvert,reset,addselect)
		if rudi_track:
		   buttons.append(rudi_track)	
		form.append(buttons,div,HT.P())
	
		TD_LR.append(heading,intro,form, HT.P())
		self.dict['basehref'] = ''
		self.dict['body'] = str(TD_LR)
		self.dict['title'] = self.db.shortname + ' : ' + self.ProbeSetID +' / Probe Information'
        # updated by NL, javascript function xmlhttpPost(strURL, div, querystring) and function updatepage(Id, str)
		# have been moved to dhtml.js
	   	self.dict['js1'] = ''
		
	def nullRecord(self,x):
		if x or x == 0:
			return x
		else:
			return ""
			
##########################
#   UCSC Probe track by Ridi Albert
##########################	
	def convertChipName2Rudi(self, officialName):
	 rudiName = None
	 if officialName == 'Hu6800':
	    rudiName = "ANHuGeneFL"
	 else:
	    rudiName = officialName.replace('_','')
	    rudiName = rudiName.replace('-','')
	    rudiName = "AN%s"%rudiName
	 return rudiName
       
	def getProbeTrackURL(self, probesetfreeze_id, probeset_id):
		  try:
		     self.cursor.execute('SELECT GeneChip.Name, GeneChip.SpeciesId FROM ProbeFreeze,GeneChip WHERE ProbeFreeze.ChipId = GeneChip.Id and ProbeFreeze.Name = "%s"' % probesetfreeze_id)
		     chipname, species = self.cursor.fetchall()[0]
		  except:
		     return  None  
		  
		  if not species:
		     return None
		       
		  chipname_in_url = self.convertChipName2Rudi(chipname)
		  orgs = {1:"mouse", 2:"rat"}
		  dbs = {1:"mm8", 2:"mm6"}	 	  
	  
		  try:
		  	url = webqtlConfig.UCSC_RUDI_TRACK_URL%(orgs[species], dbs[species],chipname_in_url, probeset_id)
		  except:
			url = ''
	  
		  return url
		  
		  
	#NL 05-13-2011: get field_names in query			  
	def getStrainNameIndexPair(self):

		strainNameIndexPair=[]
		query ='SELECT * FROM SnpPattern limit 1'
		self.cursor.execute(query)

		num_fields = len(self.cursor.description)
		field_names = [i[0] for i in self.cursor.description]
		strainsNameList=field_names[1:]
		
		# index for strain name starts from 1
		for index, name in enumerate(strainsNameList):
			index=index+1
			strainNameIndexPair.append((name,index))

		return strainNameIndexPair

		
		
