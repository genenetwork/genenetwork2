#Note that although this module gets imported a bit, the dict columnNames is never used outside this code.
#Also note that snpBrowser also defines a columnNames dict; it's different. -KA

from htmlgen import HTMLgen2 as HT
import os
import time
import pyXLWriter as xl

import GeneUtil
from base.templatePage import templatePage
from utility import webqtlUtil
from base import webqtlConfig


_scriptfile = "main.py?FormID=qtlminerresult"

#A dictionary that lets us map the html form names "txStart_mm6" -> "Mb Start (mm8)"
#the first item is the short name (column headers) and the second item is the long name (dropdown list)
#   [short name, long name, category]
columnNames = {"GeneSymbol" : ["Gene", "Gene Name", 'gene'], 
			"GeneDescription" : ["Description", "Gene Description", 'species'],
#			"probeset" : ["ProbeSet", "ProbeSet", 'gene'],
#		    "probesetsymbolA" : ["ProbeSet Symbol A", "ProbeSetsymbolA", 'gene'],
#			"probesetchrA" : ["probesetchrA", "probesetchrA", 'gene'],
			"hassnp" : ["Has nsSNP", "Has nsSNP", 'gene'],
			"hasindel" : ["Has indel", "Has indel", 'gene'],
			"hasexpr" : ["Has expr", "Has expression", 'gene'],
			"hascis" : ["Has cis", "Has cis regulation", 'gene'],
			"score" : ["Score", "Score", 'gene'],
			"meanA" : ["Expression A", "Expression in dataset 1", 'gene'],
			"meanB" : ["Expression B", "Expression in dataset 2", 'gene'],
			"meanC" : ["Expression C", "Expression in dataset 3", 'gene'],
			"probesetcisA" : ["Cis A", "Cis regulation in dataset 1", 'gene'],
			"probesetcisB" : ["Cis B", "Cis regulation in dataset 2", 'gene'],
			"probesetcisC" : ["Cis C", "Cis regulation in dataset 3", 'gene'],
			"probesetA" : ["ProbeSet A", "ProbeSet in dataset 1", 'gene'],
			"probesetB" : ["ProbeSet B", "ProbeSet in dataset 2", 'gene'],
			"probesetC" : ["ProbeSet C", "ProbeSet in dataset 3", 'gene'],
			"goterms" : ["GO biological process", "GO biological process", 'gene'],
			"pathways" : ["KEGG PathwayIDs", "KEGG PathwayIDs", 'gene'],
			"pathwaynames" : ["KEGG Pathways", "KEGG Pathways", 'gene'],
#			"newlrsA" : ["Lrs A", "lrs A", 'gene'],
#			"probesetchrB" : ["probesetchrB", "probesetchrB", 'gene'],
#			"newlrsB" : ["lrs B", "lrs B", 'gene'],
#			"probesetchrC" : ["probesetchrC", "probesetchrC", 'gene'],
#			"newlrsC" : ["lrs C", "lrs C", 'gene'],
			'GeneNeighborsCount' : ["Neighbors", "Gene Neighbors", 'gene'], 
			'GeneNeighborsRange' : ["Neighborhood", "Gene Neighborhood (Mb)", 'gene'], 
			'GeneNeighborsDensity' : ["Gene Density", "Gene Density (Neighbors/Mb)", 'gene'],  
			"ProteinID" : ["Prot ID", "Protein ID", 'protein'],
			"Chromosome" : ["Chr", "Chromosome", 'species'], 
			"TxStart" : ["Start", "Mb Start", 'species'], 
			"TxEnd" : ["End", "Mb End", 'species'], 
			"GeneLength" : ["Length", "Kb Length", 'species'], 
			"cdsStart" : ["CDS Start", "Mb CDS Start", 'species'], 
			"cdsEnd" : ["CDS End", "Mb CDS End", 'species'],
			"exonCount" : ["Num Exons", "Exon Count", 'species'], 
			"exonStarts" : ["Exon Starts", "Exon Starts", 'species'], 
			"exonEnds" : ["Exon Ends", "Exon Ends", 'species'], 
			"Strand" : ["Strand", "Strand", 'species'], 
			"GeneID" : ["Gene ID", "Gene ID", 'species'],
			"GenBankID" : ["GenBank", "GenBank ID", 'species'], 
			"UnigenID" : ["Unigen", "Unigen ID", 'species'],
			"NM_ID" : ["NM ID", "NM ID", 'species'], 
			"kgID" : ["kg ID", "kg ID", 'species'],
			"snpCountall" : ["SNPs", "SNP Count", 'species'], 
			"snpCountmis": ["nsSNPs all", "nsSNP Count all strains", 'species'], 
			"snpCountmissel": ["nsSNPs selected", "nsSNP Count selected strains", 'species'], 
			"snpDensity" : ["SNP Density", "SNP Density", 'species'], 
			"indelCountBXD" : ["Indels in BXD mice", "Indel Count in BXD mice", 'species'], 
			"lrs" : ["LRS", "Likelihood Ratio Statistic", 'misc'], 
			"lod" : ["LOD", "Likelihood Odds Ratio", 'misc'], 
			"pearson" : ["Pearson", "Pearson Product Moment", 'misc'], 
			"literature" : ["Lit Corr", "Literature Correlation", 'misc'], 
	}

###Species Freeze
speciesFreeze = {'mouse':'mm9', 'rat':'rn3', 'human':'hg19'}
for key in speciesFreeze.keys():
	speciesFreeze[speciesFreeze[key]] = key

class QTLminer (templatePage): ###
	filename = webqtlUtil.genRandStr("Itan_")

	javascript_content = """
<SCRIPT language="JAVASCRIPT">

function update4(self,form) {
   self.database='leeg';

}



	
</SCRIPT>
"""	
	def __init__(self, fd):
		templatePage.__init__(self, fd)
		if not self.openMysql():
			return

		self.species = fd.formdata.getvalue("species", "mouse")
		try:
			self.startMb = float(fd.formdata.getvalue("startMb"))
		except:
			self.startMb = 173
		try:
			self.endMb = float(fd.formdata.getvalue("endMb"))
		except:
			self.endMb = self.startMb + 1
			
		self.Chr = fd.formdata.getvalue("chromosome", "1")



######################################################### FOR A 
		###### species
		
		self.cursor.execute("""
			Select
				Name, Id from Species
			Order by
				Id
			""" )
		res = self.cursor.fetchall()
		self.spA = res
		self.spAsel = fd.formdata.getvalue("myspeciesA", "mouse")

		if not hasattr(self,"spA"):
			self.spA = res2
			self.spAsel = 'mouse'

		###### group
		
		self.cursor.execute("""
			select 
				distinct InbredSet.Name, InbredSet.FullName
				from InbredSet, Species, ProbeFreeze, GenoFreeze, PublishFreeze
			where
			        InbredSet.SpeciesId= Species.Id and
				Species.Name='%s' and InbredSet.Name != 'BXD300' and
				(PublishFreeze.InbredSetId = InbredSet.Id or GenoFreeze.InbredSetId = InbredSet.Id or ProbeFreeze.InbredSetId = InbredSet.Id)
			order by
			        InbredSet.Name
			""" % self.spAsel)

		res = self.cursor.fetchall()

		if not hasattr(self,"grA"):
			self.grA = res
			self.grAsel = 'BXD'

		if fd.formdata.getvalue('submitter') == 'a1': 
			self.grA = res
			self.grAsel = self.grA[0][0]
		else:
			self.grAsel = fd.formdata.getvalue("groupA","BXD")

		###### type
		
		self.cursor.execute("""
			select
			   distinct Tissue.Name, concat(Tissue.Name, ' mRNA')
			from ProbeFreeze, ProbeSetFreeze, InbredSet, Tissue
			where
			   ProbeFreeze.TissueId = Tissue.Id and
			   ProbeFreeze.InbredSetId = InbredSet.Id and
			   InbredSet.Name in ('%s') and
			   ProbeSetFreeze.ProbeFreezeId = ProbeFreeze.Id and
			   ProbeSetFreeze.public > %d
			order by Tissue.Name
			""" % (self.grAsel,webqtlConfig.PUBLICTHRESH))

		res = self.cursor.fetchall()

		if not hasattr(self,"tyA"):
			self.tyA = res
			self.tyAsel = 'Hippocampus' 

		if fd.formdata.getvalue('submitter') in ['a1','a2'] : 
			self.tyA = res
			self.tyAsel = self.tyA[0][0]
		else:
			self.tyAsel = fd.formdata.getvalue("typeA","Hippocampus")

		###### database

		self.cursor.execute("""
		        select
			   ProbeSetFreeze.Name, ProbeSetFreeze.FullName
			   from ProbeSetFreeze, ProbeFreeze, InbredSet, Tissue
			where ProbeSetFreeze.ProbeFreezeId = ProbeFreeze.Id and
			   ProbeFreeze.TissueId = Tissue.Id and
			   ProbeFreeze.InbredSetId = InbredSet.Id and
			   InbredSet.Name in ('%s') and Tissue.name = '%s' and
			   ProbeSetFreeze.public > %d
			order by ProbeSetFreeze.CreateTime desc
			""" % (self.grAsel,self.tyAsel,webqtlConfig.PUBLICTHRESH))

		res = self.cursor.fetchall()

		if not hasattr(self,"daA"):
			self.daA = res
			self.daAsel = 'HC_M2_0606_P'

		if fd.formdata.getvalue('submitter') in ['a1','a2','a3'] : 
			self.daA = res
			self.daAsel = self.daA[0][0]
		else:
			self.daAsel = fd.formdata.getvalue("databaseA","HC_M2_0606_P")


######################################################### FOR B
		###### species
		
		self.cursor.execute("""
			Select
				Name, Id from Species
			Order by
				Id
			""" )
		res = self.cursor.fetchall()
		self.spB = res
		self.spBsel = fd.formdata.getvalue("myspeciesB", "mouse")

		if not hasattr(self,"spB"):
			self.spB = res
			self.spBsel = 'mouse'

		###### group
		
		self.cursor.execute("""
			select 
				distinct InbredSet.Name, InbredSet.FullName
				from InbredSet, Species, ProbeFreeze, GenoFreeze, PublishFreeze
			where
			        InbredSet.SpeciesId= Species.Id and
				Species.Name='%s' and InbredSet.Name != 'BXD300' and
				(PublishFreeze.InbredSetId = InbredSet.Id or GenoFreeze.InbredSetId = InbredSet.Id or ProbeFreeze.InbredSetId = InbredSet.Id)
			order by
			        InbredSet.Name
			""" % self.spBsel)

		res = self.cursor.fetchall()

		if not hasattr(self,"grB"):
			self.grB = res
			self.grBsel = 'CXB'

		if fd.formdata.getvalue('submitter') == 'b1': 
			self.grB = res
			self.grBsel = self.grB[0][0]
		else:
			self.grBsel = fd.formdata.getvalue("groupB","CXB")

		###### type
		
		self.cursor.execute("""
			select
			   distinct Tissue.Name, concat(Tissue.Name, ' mRNA')
			from ProbeFreeze, ProbeSetFreeze, InbredSet, Tissue
			where
			   ProbeFreeze.TissueId = Tissue.Id and
			   ProbeFreeze.InbredSetId = InbredSet.Id and
			   InbredSet.Name in ('%s') and
			   ProbeSetFreeze.ProbeFreezeId = ProbeFreeze.Id and
			   ProbeSetFreeze.public > %d
			order by Tissue.Name
			""" % (self.grBsel,webqtlConfig.PUBLICTHRESH))

		res = self.cursor.fetchall()

		if not hasattr(self,"tyB"):
			self.tyB = res
			self.tyBsel = 'Hippocampus' 

		if fd.formdata.getvalue('submitter') in ['b1','b2'] : 
			self.tyB = res
			self.tyBsel = self.tyB[0][0]
		else:
			self.tyBsel = fd.formdata.getvalue("typeB","Hippocampus")

		###### database

		self.cursor.execute("""
		        select
			   ProbeSetFreeze.Name, ProbeSetFreeze.FullName
			   from ProbeSetFreeze, ProbeFreeze, InbredSet, Tissue
			where ProbeSetFreeze.ProbeFreezeId = ProbeFreeze.Id and
			   ProbeFreeze.TissueId = Tissue.Id and
			   ProbeFreeze.InbredSetId = InbredSet.Id and
			   InbredSet.Name in ('%s') and Tissue.name = '%s' and
			   ProbeSetFreeze.public > %d
			order by ProbeSetFreeze.CreateTime desc
			""" % (self.grBsel,self.tyBsel,webqtlConfig.PUBLICTHRESH))

		res = self.cursor.fetchall()

		if not hasattr(self,"daB"):
			self.daB = res
			self.daBsel = 'HC_M2CB_1205_R'

		if fd.formdata.getvalue('submitter') in ['b1','b2','b3'] : 
			self.daB = res
			self.daBsel = self.daB[0][0]
		else:
			self.daBsel = fd.formdata.getvalue("databaseB","HC_M2CB_1205_R")



######################################################### FOR C
		###### species
	
		self.cursor.execute("""
			Select
				Name, Id from Species
			Order by
				Id
			""" )
		res = self.cursor.fetchall()
		self.spC = res
		self.spCsel = fd.formdata.getvalue("myspeciesC", "mouse")

		if not hasattr(self,"spC"):
			self.spC = res
			self.spCsel = 'mouse'

		###### group
		
		self.cursor.execute("""
			select 
				distinct InbredSet.Name, InbredSet.FullName
				from InbredSet, Species, ProbeFreeze, GenoFreeze, PublishFreeze
			where
			        InbredSet.SpeciesId= Species.Id and
				Species.Name='%s' and InbredSet.Name != 'BXD300' and
				(PublishFreeze.InbredSetId = InbredSet.Id or GenoFreeze.InbredSetId = InbredSet.Id or ProbeFreeze.InbredSetId = InbredSet.Id)
			order by
			        InbredSet.Name
			""" % self.spCsel)

		res = self.cursor.fetchall()

		if not hasattr(self,"grC"):
			self.grC = res
			self.grCsel = 'LXS'

		if fd.formdata.getvalue('submitter') == 'c1': 
			self.grC = res
			self.grCsel = self.grC[0][0]
		else:
			self.grCsel = fd.formdata.getvalue("groupC","LXS")

		###### type
		
		self.cursor.execute("""
			select
			   distinct Tissue.Name, concat(Tissue.Name, ' mRNA')
			from ProbeFreeze, ProbeSetFreeze, InbredSet, Tissue
			where
			   ProbeFreeze.TissueId = Tissue.Id and
			   ProbeFreeze.InbredSetId = InbredSet.Id and
			   InbredSet.Name in ('%s') and
			   ProbeSetFreeze.ProbeFreezeId = ProbeFreeze.Id and
			   ProbeSetFreeze.public > %d
			order by Tissue.Name
			""" % (self.grCsel,webqtlConfig.PUBLICTHRESH))

		res = self.cursor.fetchall()

		if not hasattr(self,"tyC"):
			self.tyC = res
			self.tyCsel = 'Hippocampus' 

		if fd.formdata.getvalue('submitter') in ['c1','c2'] : 
			self.tyC = res
			self.tyCsel = self.tyC[0][0]
		else:
			self.tyCsel = fd.formdata.getvalue("typeC","Hippocampus")

		###### database
		

		self.cursor.execute("""
		        select
			   ProbeSetFreeze.Name, ProbeSetFreeze.FullName
			   from ProbeSetFreeze, ProbeFreeze, InbredSet, Tissue
			where ProbeSetFreeze.ProbeFreezeId = ProbeFreeze.Id and
			   ProbeFreeze.TissueId = Tissue.Id and
			   ProbeFreeze.InbredSetId = InbredSet.Id and
			   InbredSet.Name in ('%s') and Tissue.name = '%s' and
			   ProbeSetFreeze.public > %d
			order by ProbeSetFreeze.CreateTime desc
			""" % (self.grCsel,self.tyCsel,webqtlConfig.PUBLICTHRESH))

		res = self.cursor.fetchall()

		if not hasattr(self,"daC"):
			self.daC = res
			self.daCsel = 'Illum_LXS_Hipp_loess0807'

		if fd.formdata.getvalue('submitter') in ['c1','c2','c3'] : 
			self.daC = res
			self.daCsel = self.daC[0][0]
		else:
			self.daCsel = fd.formdata.getvalue("databaseC","Illum_LXS_Hipp_loess0807")















#		self.myspeciesA = fd.formdata.getvalue("myspeciesA", "mouse")
#		self.groupA = fd.formdata.getvalue("groupA", "BXD")
#		self.typeA = fd.formdata.getvalue("typeA", "Spleen")
#		self.databaseA = fd.formdata.getvalue("databaseA", "IoP_SPL_RMA_0509")#

#		self.myspeciesB = fd.formdata.getvalue("myspeciesB", "mouse")
#		self.groupB = fd.formdata.getvalue("groupB", "BXD")
#		self.typeB = fd.formdata.getvalue("typeB", "Spleen")
#		self.databaseB = fd.formdata.getvalue("databaseB", "IoP_SPL_RMA_0509")

		self.xls = fd.formdata.getvalue("xls", "1")
		try:
			s1 = int(fd.formdata.getvalue("s1"))
			s2 = int(fd.formdata.getvalue("s2"))
			self.diffColDefault = self.diffCol = [s1, s2]
		except:
			self.diffColDefault = self.diffCol = []
			if self.species !=  'mouse':
				self.diffColDefault = [2, 3]#default is B6 and D2 for other species



		self.str1 = fd.formdata.getvalue("str1", "C57BL/6J")
		self.str2 = fd.formdata.getvalue("str2", "DBA/2J")
		self.sorton = fd.formdata.getvalue("sorton", "Position")
			
		controlFrm, dispFields, dispFields2 = self.genControlForm(fd)
		##		if not fd.formdata.getvalue('submitter') in ['a1','a2','a3''a4'] :

		self.cursor.execute("""select Id from Strain where Name='%s'
			""" % self.str1 )
		strain1 = self.cursor.fetchone()[0]
		self.cursor.execute("""select Id from Strain where Name='%s'
			""" % self.str2 )
		strain2 = self.cursor.fetchone()[0]
		
		filename=''
		if fd.formdata.getvalue('submitter') in ['refresh'] or not hasattr(self,"daA"):
			geneTable, filename = self.genGeneTable(fd, dispFields, strain1, strain2)
		
		infoTD = HT.TD(width=400, valign= "top")
		infoTD.append(HT.Paragraph("QTLminer : Chr %s" % self.Chr, Class="title"), 
#			HT.Strong("Species : "), self.species.title(), HT.BR(),  

#			HT.Strong("myspeciesA : "), self.myspeciesA, HT.BR(),  
#			HT.Strong("groupA : "), self.groupA, HT.BR(),  
#			HT.Strong("typeA : "), self.typeA, HT.BR(),  
#			HT.Strong("databaseA : "), self.databaseA, HT.BR(),  

#			HT.Strong("myspeciesB : "), self.myspeciesB, HT.BR(),  
#			HT.Strong("groupB : "), self.groupB, HT.BR(),  
#			HT.Strong("typeB : "), self.typeB, HT.BR(),  
#			HT.Strong("databaseB : "), self.databaseB, HT.BR(),  

#			HT.Strong("spAsel : "), self.spAsel, HT.BR(),  
#			HT.Strong("grAsel : "), self.grAsel, HT.BR(),  
#			HT.Strong("tyAsel : "), self.tyAsel, HT.BR(),  
#			HT.Strong("daAsel : "), self.daAsel, HT.BR(),  

#			HT.Strong("spBsel : "), self.spBsel, HT.BR(),  
#			HT.Strong("grBsel : "), self.grBsel, HT.BR(),  
#			HT.Strong("tyBsel : "), self.tyBsel, HT.BR(),  
#			HT.Strong("daBsel : "), self.daBsel, HT.BR(),  

#			HT.Strong("chr : "), self.Chr, HT.BR(),  
#			HT.Strong("formdata.submitter :"), fd.formdata.getvalue("submitter"), HT.BR(),  
#			HT.Strong("formdata.myspeciesA : "), fd.formdata.getvalue("myspeciesA"), HT.BR(),  
#			HT.Strong("formdata.groupA: "), fd.formdata.getvalue("groupA") , HT.BR(),  
#			HT.Strong("formdata.myspeciesB : "), fd.formdata.getvalue("myspeciesB"), HT.BR(),  
#			HT.Strong("formdata.groupB: "), fd.formdata.getvalue("groupB") , HT.BR(),  
#			HT.Strong("formdata.type: "), fd.formdata.getvalue("type") , HT.BR(),  
#			HT.Strong("formdata.database: "), fd.formdata.getvalue("database") , HT.BR(),  
#			HT.Strong("Database : "), "UCSC %s" % speciesFreeze[self.species], HT.BR(),  
			HT.Strong("Range : "), "%2.6f Mb - %2.6f Mb" % (self.startMb, self.endMb), HT.BR(),  
			)

		if filename:
			infoTD.append(HT.BR(), HT.BR(), HT.Href(text="Download", url = "/tmp/" + filename, Class="normalsize")
					, " output in MS excel format.")

   		mainTable = HT.TableLite(HT.TR(infoTD, HT.TD(controlFrm, Class="doubleBorder", width=400), HT.TD("&nbsp;", width="")), cellpadding=10)

		if fd.formdata.getvalue('submitter') in ['refresh'] or not hasattr(self,"daA"):
			mainTable.append(HT.TR(HT.TD(geneTable, colspan=3)))

		self.dict['body'] = HT.TD(mainTable)
		self.dict['title'] = "QTLminer"
		
		self.cursor.close();
		
	def genGeneTable(self, fd, dispFields, strain1, strain2):
	
		filename = ""
		if self.xls:
			#import pyXLWriter as xl
			filename = "IntAn_Chr%s_%2.6f-%2.6f" % (self.Chr, self.startMb, self.endMb)
			filename += ".xls"
			
			# Create a new Excel workbook
			workbook = xl.Writer(os.path.join(webqtlConfig.TMPDIR, filename))
			worksheet = workbook.add_worksheet()
			titleStyle = workbook.add_format(align = 'left', bold = 0, size=18, border = 1, border_color="gray")
			headingStyle = workbook.add_format(align = 'center', bold = 1, size=13, fg_color = 0x1E, color="white", border = 1, border_color="gray")
			
			##Write title Info
			worksheet.write([0, 0], "GeneNetwork Interval Analyst Table", titleStyle)
			worksheet.write([1, 0], "%s%s" % (webqtlConfig.PORTADDR, os.path.join(webqtlConfig.CGIDIR, _scriptfile)))
			#
			worksheet.write([2, 0], "Date : %s" % time.strftime("%B %d, %Y", time.gmtime()))
			worksheet.write([3, 0], "Time : %s GMT" % time.strftime("%H:%M ", time.gmtime()))
			worksheet.write([4, 0], "Search by : %s" % fd.remote_ip)
			worksheet.write([5, 0], "view region : Chr %s %2.6f - %2.6f Mb" % (self.Chr, self.startMb, self.endMb))
			nTitleRow = 7
			
		geneTable = HT.TableLite(Class="collap", cellpadding=5)
		headerRow = HT.TR(HT.TD(" ", Class="fs13 fwb ffl b1 cw cbrb", width="1"))
		if self.xls:
			worksheet.write([nTitleRow, 0], "Index", headingStyle)
			
		for ncol, column in enumerate(dispFields):
			if column[0]=='meanA':
				headerRow.append(HT.TD("Expression in" , HT.BR(), self.grAsel, HT.BR(), self.tyAsel, Class="fs13 fwb ffl b1 cw cbrb", NOWRAP=1,align="Center"))
				if self.xls:
					colTitle = columnNames[column[0]][0]
					worksheet.write([nTitleRow, ncol+1], colTitle, headingStyle)
					worksheet.set_column([ncol+1, ncol+1], 2*len(colTitle))
			elif column[0]=='meanB':
				headerRow.append(HT.TD("Expression in" , HT.BR(), self.grBsel, HT.BR(), self.tyBsel, Class="fs13 fwb ffl b1 cw cbrb", NOWRAP=1,align="Center"))
				if self.xls:
					colTitle = columnNames[column[0]][0]
					worksheet.write([nTitleRow, ncol+1], colTitle, headingStyle)
					worksheet.set_column([ncol+1, ncol+1], 2*len(colTitle))
			elif column[0]=='meanC':
				headerRow.append(HT.TD("Expression in" , HT.BR(), self.grCsel, HT.BR(), self.tyCsel, Class="fs13 fwb ffl b1 cw cbrb", NOWRAP=1,align="Center"))
				if self.xls:
					colTitle = columnNames[column[0]][0]
					worksheet.write([nTitleRow, ncol+1], colTitle, headingStyle)
					worksheet.set_column([ncol+1, ncol+1], 2*len(colTitle))
			elif column[0]=='probesetcisA':
				headerRow.append(HT.TD("Cis regulated in" , HT.BR(), self.grAsel, HT.BR(), self.tyAsel, Class="fs13 fwb ffl b1 cw cbrb", NOWRAP=1,align="Center"))
				if self.xls:
					colTitle = columnNames[column[0]][0]
					worksheet.write([nTitleRow, ncol+1], colTitle, headingStyle)
					worksheet.set_column([ncol+1, ncol+1], 2*len(colTitle))
			elif column[0]=='probesetcisB':
				headerRow.append(HT.TD("Cis regulated in" , HT.BR(), self.grBsel, HT.BR(), self.tyBsel, Class="fs13 fwb ffl b1 cw cbrb", NOWRAP=1,align="Center"))
				if self.xls:
					colTitle = columnNames[column[0]][0]
					worksheet.write([nTitleRow, ncol+1], colTitle, headingStyle)
					worksheet.set_column([ncol+1, ncol+1], 2*len(colTitle))
			elif column[0]=='probesetcisC':
				headerRow.append(HT.TD("Cis regulated in" , HT.BR(), self.grCsel, HT.BR(), self.tyCsel, Class="fs13 fwb ffl b1 cw cbrb", NOWRAP=1,align="Center"))
				if self.xls:
					colTitle = columnNames[column[0]][0]
					worksheet.write([nTitleRow, ncol+1], colTitle, headingStyle)
					worksheet.set_column([ncol+1, ncol+1], 2*len(colTitle))
			elif column[0]=='probesetA':
				headerRow.append(HT.TD("Probeset in" , HT.BR(), self.grAsel, HT.BR(), self.tyAsel, Class="fs13 fwb ffl b1 cw cbrb", NOWRAP=1,align="Center"))
				if self.xls:
					colTitle = columnNames[column[0]][0]
					worksheet.write([nTitleRow, ncol+1], colTitle, headingStyle)
					worksheet.set_column([ncol+1, ncol+1], 2*len(colTitle))
			elif column[0]=='probesetB':
				headerRow.append(HT.TD("Probeset in" , HT.BR(), self.grBsel, HT.BR(), self.tyBsel, Class="fs13 fwb ffl b1 cw cbrb", NOWRAP=1,align="Center"))
				if self.xls:
					colTitle = columnNames[column[0]][0]
					worksheet.write([nTitleRow, ncol+1], colTitle, headingStyle)
					worksheet.set_column([ncol+1, ncol+1], 2*len(colTitle))
			elif column[0]=='probesetC':
				headerRow.append(HT.TD("Probeset in" , HT.BR(), self.grCsel, HT.BR(), self.tyCsel, Class="fs13 fwb ffl b1 cw cbrb", NOWRAP=1,align="Center"))
				if self.xls:
					colTitle = columnNames[column[0]][0]
					worksheet.write([nTitleRow, ncol+1], colTitle, headingStyle)
					worksheet.set_column([ncol+1, ncol+1], 2*len(colTitle))
			elif column[0]=='hasexpr':
				headerRow.append(HT.TD("Has expression in" , HT.BR(), self.grAsel, HT.BR(), self.tyAsel, Class="fs13 fwb ffl b1 cw cbrb", NOWRAP=1,align="Center"))
				if self.xls:
					colTitle = columnNames[column[0]][0]
					worksheet.write([nTitleRow, ncol+1], colTitle, headingStyle)
					worksheet.set_column([ncol+1, ncol+1], 2*len(colTitle))
			elif column[0]=='hascis':
				headerRow.append(HT.TD("Cis regulated in" , HT.BR(), self.grAsel, HT.BR(), self.tyAsel, Class="fs13 fwb ffl b1 cw cbrb", NOWRAP=1,align="Center"))
				if self.xls:
					colTitle = columnNames[column[0]][0]
					worksheet.write([nTitleRow, ncol+1], colTitle, headingStyle)
					worksheet.set_column([ncol+1, ncol+1], 2*len(colTitle))
			elif column[0]=='snpCountmis':
				headerRow.append(HT.TD("nsSNPs" , HT.BR(), "all strains", HT.BR(), "  ", Class="fs13 fwb ffl b1 cw cbrb", NOWRAP=1,align="Center"))
				if self.xls:
					colTitle = columnNames[column[0]][0]
					worksheet.write([nTitleRow, ncol+1], colTitle, headingStyle)
					worksheet.set_column([ncol+1, ncol+1], 2*len(colTitle))
			elif column[0]=='snpCountmissel':
				headerRow.append(HT.TD("nsSNPs" , HT.BR(), self.str1, " vs", HT.BR(), self.str2, Class="fs13 fwb ffl b1 cw cbrb", NOWRAP=1,align="Center"))
				if self.xls:
					colTitle = columnNames[column[0]][0]
					worksheet.write([nTitleRow, ncol+1], colTitle, headingStyle)
					worksheet.set_column([ncol+1, ncol+1], 2*len(colTitle))




			elif len(column) == 1:
				# header 
				headerRow.append(HT.TD(columnNames[column[0]][0], Class="fs13 fwb ffl b1 cw cbrb", NOWRAP=1,align="Center"))
				if self.xls:
					colTitle = columnNames[column[0]][0]
					worksheet.write([nTitleRow, ncol+1], colTitle, headingStyle)
					worksheet.set_column([ncol+1, ncol+1], 2*len(colTitle))
			else:
				# header 
				headerRow.append(HT.TD(columnNames[column[0]][0], HT.BR(), " (%s)" % speciesFreeze[column[1]], 
					Class="fs13 fwb ffl b1 cw cbrb", NOWRAP=1, align="Center"))
				if self.xls:
					colTitle = columnNames[column[0]][0] + " (%s)" % speciesFreeze[column[1]]
					worksheet.write([nTitleRow, ncol+1], colTitle, headingStyle)
					worksheet.set_column([ncol+1, ncol+1], 2*len(colTitle))
				#headerRow.append(HT.TD(columnNames[column[0]][0], HT.BR(), 
				#	"(%s %s)" % (column[1].title(), speciesFreeze[column[1]]), 
				#	Class="colorBlue", NOWRAP=1, align="Center"))
		geneTable.append(headerRow)

		geneColnul = GeneUtil.loadGenesForQTLminer(self.cursor, self.Chr, self.diffColDefault, self.startMb, self.endMb, species=self.species, databaseA=self.daAsel, databaseB=self.daBsel, databaseC=self.daCsel, str1=self.str1, str2=self.str2)
		
		# scores = []
		# for gIndex, theGO in enumerate(geneCol):
		# 	keyValue = ""
		#	fieldName = 'score'
		# 	if theGO.has_key(fieldName):
		# 		keyValue = theGO[fieldName]
		# 	scores.append(keyValue)

		sort_on = "TxStart"
		myrev = False
		if self.sorton == "Score":
			sort_on = "score"
			myrev = True
		geneColeen = [(dict_[sort_on], dict_) for dict_ in geneColnul]
		geneColeen.sort(reverse=myrev)
		geneCol = [dict_ for (key, dict_) in geneColeen]
					


		for gIndex, theGO in enumerate(geneCol):
			geneRow = HT.TR(HT.TD(gIndex+1, Class="fs12 fwn b1", align="right"))
			if self.xls:
				nTitleRow += 1
				worksheet.write([nTitleRow, 0], gIndex + 1)
				
			for ncol, column in enumerate(dispFields):
				if len(column) == 1 or column[1]== self.species:
					keyValue = ""
					fieldName = column[0]
					curSpecies = self.species
					curGO = theGO
					if theGO.has_key(fieldName):
						keyValue = theGO[fieldName]
				else:
					fieldName , othSpec = column
					curSpecies = othSpec
					subGO = '%sGene' % othSpec
					keyValue = ""
					curGO = theGO[subGO]
					if theGO[subGO].has_key(fieldName):
						keyValue = theGO[subGO][fieldName]
				
				if self.xls:
					worksheet.write([nTitleRow, ncol+1], keyValue)
				geneRow.append(self.formatTD(keyValue, fieldName, curSpecies, curGO, strain1, strain2))
					
			geneTable.append(geneRow)
			
		if self.xls:
			workbook.close()
		return geneTable, filename
	
	def formatTD(self, keyValue, fieldName, Species, theGO, strain1, strain2):
		if keyValue is None:
			keyValue = ""
		if keyValue != "":
			if fieldName in ("exonStarts", "exonEnds"):
				keyValue = string.replace(keyValue, ',', ' ')
				return HT.TD(HT.Span(keyValue, Class="code", Id="green"), width=350, Class="fs12 fwn b1")
			elif fieldName in ("GeneDescription"):
				if keyValue == "---":
					keyValue = ""
				return HT.TD(keyValue, Class="fs12 fwn b1", width=300)
			elif fieldName in ("GeneSymbol"):
				webqtlLink = HT.Href("./%s/%s?cmd=sch&gene=%s&alias=1&species=%s" % (webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE, keyValue, Species), 		
					HT.Image("/images/webqtl_search.gif", border=0, valign="top"), target="_blank")
				if theGO['GeneID']:
					geneSymbolLink = HT.Href(webqtlConfig.NCBI_LOCUSID % theGO['GeneID'], keyValue, Class="normalsize", target="_blank")
				else:
					geneSymbolLink = keyValue
				return HT.TD(webqtlLink, geneSymbolLink, Class="fs12 fwn b1",NOWRAP=1)
			elif fieldName == 'UnigenID':
				try:
					gurl = HT.Href(webqtlConfig.UNIGEN_ID % tuple(string.split(keyValue,'.')[:2]), keyValue, Class="normalsize", target="_blank")
				except:
					gurl = keyValue
				return HT.TD(gurl, Class="fs12 fwn b1",NOWRAP=1)
			elif fieldName in ("exonCount", "Chromosome"):
				return HT.TD(keyValue, Class="fs12 fwn b1",align="right")
			elif fieldName in ("snpCount"):
				return HT.TD(keyValue, Class="fs12 fwn b1",NOWRAP=1)
			elif fieldName in ("snpCountmis"):
				snpString = HT.Href(url="%s?FormID=SnpBrowserResultPage&submitStatus=1&chr=%s&start=%s&end=%s&domain=Exon&variant=SNP" % (os.path.join(webqtlConfig.CGIDIR, 'main.py'),theGO["Chromosome"], theGO["TxStart"], theGO["TxEnd"] ), text=theGO["snpCountmis"], target="_blank", Class="normalsize")
				return HT.TD(snpString, Class="fs12 fwn b1",NOWRAP=1)
			elif fieldName in ("snpCountmissel"):
				snpString = HT.Href(url="%s?FormID=SnpBrowserResultPage&submitStatus=1&chr=%s&start=%s&end=%s&domain=Exon&variant=SNP&customStrain=1&diffAlleles=1&chosenStrains=%s,%s" % (os.path.join(webqtlConfig.CGIDIR, 'main.py'),theGO["Chromosome"], theGO["TxStart"], theGO["TxEnd"], self.str1, self.str2 ), text=theGO["snpCountmissel"], target="_blank", Class="normalsize")
				return HT.TD(snpString, Class="fs12 fwn b1",NOWRAP=1)


#				if keyValue:
#					snpString = HT.Href(url="%s?chr=%s&start=%s&end=%s&geneName=%s&s1=%d&s2=%d" % (os.path.join(webqtlConfig.CGIDIR, 'snpBrowser.py'), theGO["Chromosome"], theGO["TxStart"], theGO["TxEnd"], theGO["GeneSymbol"], self.diffColDefault[0], self.diffColDefault[1]), text=theGO["snpCount"], target="_blank", Class="normalsize")
#				else:
#					snpString = keyValue
#				return HT.TD(snpString, Class="fs12 fwn b1",align="right")
			elif fieldName in ("snpDensity", "GeneLength"):
				if keyValue: keyValue = "%2.3f" % keyValue
				else: keyValue = ""
				return HT.TD(keyValue, Class="fs12 fwn b1",align="right")
			elif fieldName in ("TxStart", "TxEnd"):
				return HT.TD("%2.6f" % keyValue, Class="fs12 fwn b1",align="right")
			elif fieldName in ("score"):
				return HT.TD("%1d" % keyValue, Class="fs12 fwn b1",align="right")
			elif fieldName in ("pathways", "pathwaynames", "goterms"):
				html = HT.Paragraph(Class="fs12 fwn b1")
				for kk in keyValue:
					html.append(kk,HT.BR())
				return HT.TD(html, Class="fs12 fwn b1",align="right",NOWRAP=1)
			elif fieldName in ("probesetA", "probesetB", "probesetC"):
				html = HT.Paragraph(Class="fs12 fwn b1")
				for kk in keyValue:
					html.append(kk,HT.BR())
				return HT.TD(html, Class="fs12 fwn b1",align="right")
			elif fieldName in ("probesetsymbolA"):
				html = HT.Paragraph(Class="fs12 fwn b1")
				for kk in keyValue:
					html.append(kk,HT.BR())
				return HT.TD(html, Class="fs12 fwn b1",align="right")
			elif fieldName in ("meanA", "meanB", "meanC"):
				html = HT.Paragraph(Class="fs12 fwn b1")
				for kk in keyValue:
					html.append(str(round(kk,1)),HT.BR())
				return HT.TD(html, Class="fs12 fwn b1",align="right")
			elif fieldName in ("hassnp", "hasindel", "hasexpr","hascis"):
				html = HT.Paragraph(Class="fs12 fwn b1")
				for kk in keyValue:
					html.append(kk,HT.BR())
				return HT.TD(html, Class="fs12 fwn b1",align="right")
			elif fieldName in ("newlrsA", "newlrsB", "newlrsC"):
				html = HT.Paragraph(Class="fs12 fwn b1")
				for kk in keyValue:
					html.append(str(round(kk,1)),HT.BR())
				return HT.TD(html, Class="fs12 fwn b1",align="right")
			elif fieldName in ("probesetcisA", "probesetcisB", "probesetcisC"):
				html = HT.Paragraph(Class="fs12 fwn b1")
				for kk in keyValue:
					html.append(kk,HT.BR())
#					if kk==0:
#						html.append('no',HT.BR())
#					if kk==1:
#						html.append('yes',HT.BR())
				return HT.TD(html, Class="fs12 fwn b1",align="right")
			else:
				return HT.TD(keyValue, Class="fs12 fwn b1",NOWRAP=1)
		else:
			return HT.TD(keyValue, Class="fs12 fwn b1",NOWRAP=1,align="right")

#	def getStrainNameList(self, strain_data):
#	      return strain_data[1:]
	def getStrainNamePair(self):
		strainNamePair=[]
		query ='SELECT * FROM SnpPattern limit 1'
		self.cursor.execute(query)
		num_fields = len(self.cursor.description)
		field_names = [i[0] for i in self.cursor.description]
		strainsNameList=field_names[1:]
		for index, name in enumerate(strainsNameList):
			strainNamePair.append((name,name))
		return strainNamePair
				
	def genControlForm(self, fd):
		##desc GeneList
		self.cursor.execute("Desc GeneList")
		GeneListFields = self.cursor.fetchall()
		GeneListFields = map(lambda X: X[0], GeneListFields)
		
		#group columns by category--used for creating the dropdown list of possible columns
		categories = {}
		for item in columnNames.keys():
			category = columnNames[item]
			if category[-1] not in categories.keys():
				categories[category[-1]] = [item ]
			else:
				categories[category[-1]] = categories[category[-1]]+[item]
	
		##List All Species in the Gene Table
		speciesDict = {}
		self.cursor.execute("select Species.Name, GeneList.SpeciesId from Species, GeneList where \
			GeneList.SpeciesId = Species.Id group by GeneList.SpeciesId order by Species.Id")
		results = self.cursor.fetchall()
		speciesField = categories.pop('species', [])
		categoriesOrder = ['gene', 'protein']
		for item in results:
			specName, specId = item
			categoriesOrder.append(specName)
			speciesDict[specName] = specId
			AppliedField = []
			for item2 in speciesField:
				if item2 in GeneListFields:
					self.cursor.execute("select %s from GeneList where SpeciesId = %d and %s is not NULL limit 1 " % (item2, specId, item2))
					columnApply = self.cursor.fetchone()
					if not columnApply:
						continue
				elif specName != 'mouse' and item2 in ('snpCount', 'snpDensity'):
					continue
				else:
					pass
				AppliedField.append(item2)
			categories[specName] = AppliedField
			
		categoriesOrder += ['misc']

		s1_data = self.getStrainNamePair()
		self.allStrainNames = s1_data[1:]


		
		############################################################
		## Create the list of possible columns for the dropdown list
		############################################################
		allColumnsList = HT.Select(name="allColumns", Class="snpBrowserDropBox")#onChange="addToList(this.form.allColumns.options[this.form.allColumns.selectedIndex].text, this.form.allColumns.options[this.form.allColumns.selectedIndex].value, this.form.columns)")
		
		for category in categoriesOrder:
			allFields = categories[category]
			if allFields:
				geneOpt = HT.Optgroup(label=category.title())
				for item in allFields:
					if category in speciesFreeze.keys():
						geneOpt.append(("%s (%s %s)" % (columnNames[item][1], category.title(), speciesFreeze[category]), 
							"%s__%s" % (item, speciesFreeze[category])))
					else:
						geneOpt.append((columnNames[item][1], item))
				geneOpt.sort()
				allColumnsList.append(geneOpt)

		allColumnsList2 = HT.Select(name="allColumns2", Class="snpBrowserDropBox")
		for item in self.allStrainNames:
			allColumnsList2.append(item)
		
		######################################
		## Create the list of selected columns
		######################################
		
		#cols contains the value of all the selected columns
		submitCols = cols = fd.formdata.getvalue("columns", "default")
		
		if cols == "default":
			if self.species=="mouse":  #these are the same columns that are shown on intervalPage.py
				cols = ['GeneSymbol', 'GeneDescription', 'goterms', 'pathwaynames', 'Chromosome', 'TxStart', 'snpCountmis', 'snpCountmissel', 'meanA', 'meanB', 'meanC', 'probesetcisA','probesetcisB','probesetcisC', 'probesetA','probesetB','probesetC', 'indelCountBXD','hassnp','hasindel','hasexpr','hascis','score']
			elif self.species=="rat":
				cols = ['GeneSymbol', 'GeneDescription', 'Chromosome', 'TxStart', 'GeneLength', 'Strand', 'GeneID', 'UnigenID']
			else:
				#should not happen
				cols = []
		else:
			if type(cols)==type(""):
				cols = [cols]
			
		colsLst = []
		dispFields = []
		for column in cols:
			if submitCols == "default" and column not in ('GeneSymbol') and (column in GeneListFields or column in speciesField):
				colsLst.append(("%s (%s %s)" % (columnNames[column][1], self.species.title(), speciesFreeze[self.species]), 
							"%s__%s" % (column, speciesFreeze[self.species])))
				dispFields.append([column, self.species])
			else:
				column2 = column.split("__")
				if len(column2) == 1:
					colsLst.append((columnNames[column2[0]][1], column))
					dispFields.append([column])
				else:
					thisSpecies = speciesFreeze[column2[1]]
					colsLst.append(("%s (%s %s)" % (columnNames[column2[0]][1], thisSpecies.title(), column2[1]), 
							column))
					dispFields.append((column2[0], thisSpecies))
		selectedColumnsList = HT.Select(name="columns", Class="snpBrowserSelectBox", multiple="true", data=colsLst, size=6)



		######### now for the strains!!!!!!

		#cols contains the value of all the selected columns
		submitCols2 = cols2 = fd.formdata.getvalue("columns2", "default")
		
		if cols2 == "default":
			if self.species=="mouse":  #these are the same columns that are shown on intervalPage.py
				cols2 = ['C57BL/6J', 'DBA/2J',]
			else:
				#should not happen
				cols2 = []
		else:
			if type(cols2)==type(""):
				cols2 = [cols2]
			
		colsLst2 = []
		dispFields2 = []
		for column2 in cols2:
#			if submitCols2 == "default" and (column in GeneListFields or column in speciesField):
#				colsLst2.append(("%s (%s %s)" % (columnNames[column][1], self.species.title(), speciesFreeze[self.species]), 
#							"%s__%s" % (column, speciesFreeze[self.species])))
#				dispFields.append([column, self.species])
#			else:
#				column2 = column.split("__")
#				if len(column2) == 1:
			colsLst2.append((column2, column2))
			dispFields2.append([column2])
		selectedColumnsList2 = HT.Select(name="columns2", Class="snpBrowserSelectBox", multiple="true", data=colsLst2, size=6)

		######### now for the sorton

		#cols contains the value of all the selected columns
		submitCols3 = cols3 = fd.formdata.getvalue("columns3", "default")
		
		if cols3 == "default":
			if self.species=="mouse":  #these are the same columns that are shown on intervalPage.py
				cols3 = ['Position', 'Score',]
			else:
				#should not happen
				cols3 = []
		else:
			if type(cols3)==type(""):
				cols3 = [cols3]
			
		colsLst3 = []
		dispFields3 = []
		for column3 in cols3:
			colsLst3.append((column3, column3))
			dispFields3.append([column3])
		selectedColumnsList3 = HT.Select(name="columns3", Class="snpBrowserSelectBox", multiple="true", data=colsLst3, size=6)




		
		##########################
        ## Create the columns form
		##########################		
		columnsForm = HT.Form(name="columnsForm", submit=HT.Input(type='hidden'), cgi=os.path.join(webqtlConfig.CGIDIR, _scriptfile), enctype="multipart/form-data")
		columnsForm.append(HT.Input(type="hidden", name="fromdatabase", value= fd.formdata.getvalue("fromdatabase", "unknown")))
		columnsForm.append(HT.Input(type="hidden", name="species", value=self.species))	
		columnsForm.append(HT.Input(type="hidden", name="submitter", value="empty"))	
		if self.diffCol:
			columnsForm.append(HT.Input(type="hidden", name="s1", value=self.diffCol[0]))
			columnsForm.append(HT.Input(type="hidden", name="s2", value=self.diffCol[1]))
		startBox = HT.Input(type="text", name="startMb", value=self.startMb, size=10)
		endBox = HT.Input(type="text", name="endMb", value=self.endMb, size=10)
		addButton = HT.Input(type="button", name="add", value="Add", Class="button", onClick="addToList(this.form.allColumns.options[this.form.allColumns.selectedIndex].text, this.form.allColumns.options[this.form.allColumns.selectedIndex].value, this.form.columns)")
#		addButton2 = HT.Input(type="button", name="add", value="Add", Class="button", onClick="addToList(this.form.allColumns2.options[this.form.allColumns2.selectedIndex].text, this.form.allColumns2.options[this.form.allColumns2.selectedIndex].value, this.form.columns2)")
		removeButton = HT.Input(type="button", name="remove", value="Remove", Class="button", onClick="removeFromList(this.form.columns.selectedIndex, this.form.columns)")
#		removeButton2 = HT.Input(type="button", name="remove", value="Remove", Class="button", onClick="removeFromList(this.form.columns2.selectedIndex, this.form.columns2)")
		upButton = HT.Input(type="button", name="up", value="Up", Class="button", onClick="swapOptions(this.form.columns.selectedIndex, this.form.columns.selectedIndex-1, this.form.columns)")
		downButton = HT.Input(type="button", name="down", value="Down", Class="button", onClick="swapOptions(this.form.columns.selectedIndex, this.form.columns.selectedIndex+1, this.form.columns)")
		clearButton = HT.Input(type="button", name="clear", value="Clear", Class="button", onClick="deleteAllElements(this.form.columns)")		
		submitButton = HT.Input(type="submit", value="Analyze QTL interval", Class="button", onClick="Javascript:this.form.submitter.value='refresh';selectAllElements(this.form.columns)")		


		selectChrBox = HT.Select(name="chromosome")
		self.cursor.execute("""
			Select
				Chr_Length.Name, Length from Chr_Length, Species
			where
				Chr_Length.SpeciesId = Species.Id AND
				Species.Name = '%s' 
			Order by
				Chr_Length.OrderId
			""" % self.species)
		
		results = self.cursor.fetchall()
		for chrInfo in results:
			selectChrBox.append((chrInfo[0], chrInfo[0]))
		selectChrBox.selected.append(self.Chr)

############################################ 2 strain boxes

		selectstr1 = HT.Select(name="str1")
		for item in self.allStrainNames:
			selectstr1.append(item[0])
		selectstr1.selected.append(self.str1)

		selectstr2 = HT.Select(name="str2")
		for item in self.allStrainNames:
			selectstr2.append(item[0])
		selectstr2.selected.append(self.str2)

############################################ select sort on

		selectsorton = HT.Select(name="sorton")
		selectsorton.append('Position')
		selectsorton.append('Score')
		selectsorton.selected.append('Position')


############################################
		selectSpeciesBoxA = HT.Select(name="myspeciesA",onChange="Javascript:this.form.submitter.value='s2';submit();")
		for speciesInfo in self.spA:
			name = ''
			if speciesInfo[0]=='mouse':
				name='Mouse'
			elif speciesInfo[0]=='rat':
				name='Rat'
			elif speciesInfo[0]=='arabidopsis':
				name='Arabidopsis thaliana'
			elif speciesInfo[0]=='human':
				name='Human'
			elif speciesInfo[0]=='barley':
				name='Barley'
			elif speciesInfo[0]=='drosophila':
				name='Drosophila'
			elif speciesInfo[0]=='macaque monkey':
				name='Macaque Monkey'

			selectSpeciesBoxA.append((name, speciesInfo[0]))
		selectSpeciesBoxA.selected.append(self.spAsel)

		selectGroupBoxA = HT.Select(name="groupA",onChange="Javascript:this.form.submitter.value='a2';submit();")
		for groupInfo in self.grA:
			selectGroupBoxA.append((groupInfo[1], groupInfo[0]))
		selectGroupBoxA.selected.append(self.grAsel)

		selectTypeBoxA = HT.Select(name="typeA",onChange="Javascript:this.form.submitter.value='a3';submit();")
		for typeInfo in self.tyA:
			selectTypeBoxA.append((typeInfo[0] + ' mRNA', typeInfo[0]))
		selectTypeBoxA.selected.append(self.tyAsel)

		selectDatabaseBoxA = HT.Select(name="databaseA",onChange="Javascript:this.form.submitter.value='a4';submit();")
		for databaseInfo in self.daA:
			selectDatabaseBoxA.append((databaseInfo[1], databaseInfo[0]))
		selectDatabaseBoxA.selected.append(self.daAsel)

#############################
############################################
		selectSpeciesBoxB = HT.Select(name="myspeciesB",onChange="Javascript:this.form.submitter.value='b1';submit();")
		for speciesInfo in self.spB:
			name = ''
			if speciesInfo[0]=='mouse':
				name='Mouse'
			elif speciesInfo[0]=='rat':
				name='Rat'
			elif speciesInfo[0]=='arabidopsis':
				name='Arabidopsis thaliana'
			elif speciesInfo[0]=='human':
				name='Human'
			elif speciesInfo[0]=='barley':
				name='Barley'
			elif speciesInfo[0]=='drosophila':
				name='Drosophila'
			elif speciesInfo[0]=='macaque monkey':
				name='Macaque Monkey'

			selectSpeciesBoxB.append((name, speciesInfo[0]))			
		selectSpeciesBoxB.selected.append(self.spBsel)

		selectGroupBoxB = HT.Select(name="groupB",onChange="Javascript:this.form.submitter.value='b2';submit();")
		for groupInfo in self.grB:
			selectGroupBoxB.append((groupInfo[1], groupInfo[0]))
		selectGroupBoxB.selected.append(self.grBsel)

		selectTypeBoxB = HT.Select(name="typeB",onChange="Javascript:this.form.submitter.value='b3';submit();")
		for typeInfo in self.tyB:
			selectTypeBoxB.append((typeInfo[0] + ' mRNA', typeInfo[0]))
		selectTypeBoxB.selected.append(self.tyBsel)

		selectDatabaseBoxB = HT.Select(name="databaseB",onChange="Javascript:this.form.submitter.value='b4';submit();")
		for databaseInfo in self.daB:
			selectDatabaseBoxB.append((databaseInfo[1], databaseInfo[0]))
		selectDatabaseBoxB.selected.append(self.daBsel)

############################################
#############################
############################################
		selectSpeciesBoxC = HT.Select(name="myspeciesC",onChange="Javascript:this.form.submitter.value='c1';submit();")
		for speciesInfo in self.spC:
			name = ''
			if speciesInfo[0]=='mouse':
				name='Mouse'
			elif speciesInfo[0]=='rat':
				name='Rat'
			elif speciesInfo[0]=='arabidopsis':
				name='Arabidopsis thaliana'
			elif speciesInfo[0]=='human':
				name='Human'
			elif speciesInfo[0]=='barley':
				name='Barley'
			elif speciesInfo[0]=='drosophila':
				name='Drosophila'
			elif speciesInfo[0]=='macaque monkey':
				name='Macaque Monkey'

			selectSpeciesBoxC.append((name, speciesInfo[0]))			
		selectSpeciesBoxC.selected.append(self.spCsel)

		selectGroupBoxC = HT.Select(name="groupC",onChange="Javascript:this.form.submitter.value='c2';submit();")
		for groupInfo in self.grC:
			selectGroupBoxC.append((groupInfo[1], groupInfo[0]))
		selectGroupBoxC.selected.append(self.grCsel)

		selectTypeBoxC = HT.Select(name="typeC",onChange="Javascript:this.form.submitter.value='c3';submit();")
		for typeInfo in self.tyC:
			selectTypeBoxC.append((typeInfo[0] + ' mRNA', typeInfo[0]))
		selectTypeBoxC.selected.append(self.tyCsel)

		selectDatabaseBoxC = HT.Select(name="databaseC",onChange="Javascript:this.form.submitter.value='c4';submit();")
		for databaseInfo in self.daC:
			selectDatabaseBoxC.append((databaseInfo[1], databaseInfo[0]))
		selectDatabaseBoxC.selected.append(self.daCsel)

############################################




#############################


		

		innerColumnsTable = HT.TableLite(border=0, Class="collap", cellpadding = 2)
		innerColumnsTable.append(HT.TR(HT.TD(selectedColumnsList)),
					 HT.TR(HT.TD(clearButton, removeButton, upButton, downButton)))
#		innerColumnsTable2 = HT.TableLite(border=0, Class="collap", cellpadding = 2)
#		innerColumnsTable2.append(HT.TR(HT.TD(selectedColumnsList2)),
#					 HT.TR(HT.TD(removeButton2)))
		columnsTable = HT.TableLite(border=0, cellpadding=2, cellspacing=0)
		columnsTable.append(
				    HT.TR(HT.TD(HT.Font("&nbsp;")),
					  HT.TD(HT.Strong("Select the QTL interval"))),
					HT.TR(HT.TD(HT.Font("Chr: ", size=-1)),
					  HT.TD(selectChrBox)),
				    HT.TR(HT.TD(HT.Font("View: ", size=-1)),
					  HT.TD(startBox, HT.Font("Mb to ", size=-1), endBox, HT.Font("Mb", size=-1))),
				    HT.TR(HT.TD(HT.Font("&nbsp;", size=-1)),
					  HT.TD("&nbsp;")),
				    HT.TR(HT.TD(HT.Font("&nbsp;")),
					  HT.TD(HT.Strong("Select two mouse strains for inclusion of nsSNP count"))),
				    HT.TR(HT.TD(HT.Font("Strains: ", size=-1)),
					  HT.TD(selectstr1,selectstr2)),
				    HT.TR(HT.TD(HT.Font("&nbsp;", size=-1)),
					  HT.TD("&nbsp;")),
				    HT.TR(HT.TD(HT.Font("&nbsp;")),
					  HT.TD(HT.Strong("Select 3 datasets for inclusion of expression and cis-activity data"))),
				    HT.TR(HT.TD(HT.Font("&nbsp;", size=-1)),
					  HT.TD("&nbsp;")),
				    HT.TR(HT.TD("&nbsp;"),
					  HT.TD(HT.Font("Dataset 1", size=-1))),
				    HT.TR(HT.TD(HT.Font("Species: ", size=-1)),
					  HT.TD(selectSpeciesBoxA)),
				    HT.TR(HT.TD(HT.Font("Group: ", size=-1)),
					  HT.TD(selectGroupBoxA)),
				    HT.TR(HT.TD(HT.Font("Type: ", size=-1)),
					  HT.TD(selectTypeBoxA)),
				    HT.TR(HT.TD(HT.Font("Database: ", size=-1)),
					  HT.TD(selectDatabaseBoxA)),
				    HT.TR(HT.TD(HT.Font("&nbsp;", size=-1)),
					  HT.TD("&nbsp;")),
				    HT.TR(HT.TD("&nbsp;"),
					  HT.TD(HT.Font("Dataset 2", size=-1))),
				    HT.TR(HT.TD(HT.Font("Species: ", size=-1)),
					  HT.TD(selectSpeciesBoxB)),
				    HT.TR(HT.TD(HT.Font("Group: ", size=-1)),
					  HT.TD(selectGroupBoxB)),
				    HT.TR(HT.TD(HT.Font("Type: ", size=-1)),
					  HT.TD(selectTypeBoxB)),
				    HT.TR(HT.TD(HT.Font("Database: ", size=-1)),
					  HT.TD(selectDatabaseBoxB)),
				    HT.TR(HT.TD(HT.Font("&nbsp;", size=-1)),
					  HT.TD("&nbsp;")),
				    HT.TR(HT.TD("&nbsp;"),
					  HT.TD(HT.Font("Dataset 3", size=-1))),
				    HT.TR(HT.TD(HT.Font("Species: ", size=-1)),
					  HT.TD(selectSpeciesBoxC)),	
				    HT.TR(HT.TD(HT.Font("Group: ", size=-1)),
					  HT.TD(selectGroupBoxC)),
					HT.TR(HT.TD(HT.Font("Type: ", size=-1)),
					  HT.TD(selectTypeBoxC)),
				    HT.TR(HT.TD(HT.Font("Database: ", size=-1)),
					  HT.TD(selectDatabaseBoxC)),
#				    HT.TR(HT.TD(""),
#					  HT.TD(innerColumnsTable2)),
				    HT.TR(HT.TD(HT.Font("&nbsp;", size=-1)),
					  HT.TD("&nbsp;")),
				    HT.TR(HT.TD(HT.Font("&nbsp;")),
					  HT.TD(HT.Strong("Optionally, choose additional data to display"))),
				    HT.TR(HT.TD(HT.Font("Show: ", size=-1)),
					  HT.TD(allColumnsList, addButton)),
				    HT.TR(HT.TD(HT.Font("Selected:",size=-1)),
					  HT.TD(innerColumnsTable)),
				    HT.TR(HT.TD(HT.Font("&nbsp;", size=-1)),
					  HT.TD("&nbsp;")),
				    HT.TR(HT.TD(HT.Font("Sort by: ", size=-1)),
					  HT.TD(selectsorton)),
				    HT.TR(HT.TD(HT.Font("&nbsp;", size=-1)),
					  HT.TD("&nbsp;")),
				    HT.TR(HT.TD(HT.Font("&nbsp;", size=-1)),
					  HT.TD(submitButton)),
				    
				    )
		columnsForm.append(columnsTable)
		#columnsForm.append(HT.Input(type="hidden", name="sort", value=diffCol),
		#		   HT.Input(type="hidden", name="identification", value=identification),
		#		   HT.Input(type="hidden", name="traitInfo", value=traitInfo))
		
		return columnsForm, dispFields, dispFields2
