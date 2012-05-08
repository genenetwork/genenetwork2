#GoTreePage.py

import string
from htmlgen import HTMLgen2 as HT

from base import webqtlConfig
from base.webqtlTrait import webqtlTrait
from base.templatePage import templatePage
from dbFunction import webqtlDatabaseFunction
	
			
#########################################
#     GoTree Page
#########################################
class GoTreePage(templatePage):

	def __init__(self,fd):

		self.theseTraits = []
		TD_LR = HT.TD(height=200,width="100%",bgColor='#eeeeee',valign="middle")
		
		templatePage.__init__(self, fd)

		if not self.openMysql():
			return

		self.searchResult = fd.formdata.getvalue('searchResult', [])
		if type("1") == type(self.searchResult):
			self.searchResult = [self.searchResult]

		#XZ, self.theseTraits holds the "ProbeSet" traits.

		for item in self.searchResult:
			try:
				thisTrait = webqtlTrait(fullname=item, cursor=self.cursor)
				thisTrait.retrieveInfo(QTL=1)
				if thisTrait.db.type == "ProbeSet":
					self.theseTraits.append(thisTrait)
			except:
				pass
				
		if self.theseTraits:
			pass
		else:
			templatePage.__init__(self, fd)
			heading = 'WebGestalt'
			detail = ['You need to select at least one microarray trait to submit.']
			self.error(heading=heading,detail=detail)
			return
			
		chipName = self.testChip(fd)

		#XZ, 8/24/2009: the name of arraylist is misleading. It holds the name of traits.
		arraylist, geneIdList = self.genGeneIdList(fd)
		
		target_url = "http://bioinfo.vanderbilt.edu/webgestalt/webgestalt.php"
		
		formWebGestalt = HT.Form(cgi=target_url, enctype='multipart/form-data', name='WebGestalt', submit = HT.Input(type='hidden'))

		id_type = chipName

		hddnWebGestalt = {'id_list':string.join(arraylist, ","),
				  'id_type':id_type}
		
		hddnWebGestalt['ref_type'] = hddnWebGestalt['id_type']
		hddnWebGestalt['analysis_type'] = 'GO'
		hddnWebGestalt['significancelevel'] = 'Top10'
		hddnWebGestalt['stat'] = 'Hypergeometric'
		hddnWebGestalt['mtc'] = 'BH'
		hddnWebGestalt['min'] = '2'
		hddnWebGestalt['id_value'] = fd.formdata.getvalue('correlation') 
			
                species = webqtlDatabaseFunction.retrieveSpecies(cursor=self.cursor, RISet=fd.RISet)

                if species == 'rat':
                    hddnWebGestalt['org'] = 'Rattus norvegicus'
                elif species == 'human':
                    hddnWebGestalt['org'] = 'Homo sapiens'
                elif species == 'mouse':
                    hddnWebGestalt['org'] = 'Mus musculus'
                else:
                    hddnWebGestalt['org'] = ''

		hddnWebGestalt['org'] = hddnWebGestalt['org'].replace(' ','_')
		
		for key in hddnWebGestalt.keys():
				formWebGestalt.append(HT.Input(name=key, value=hddnWebGestalt[key], type='hidden'))
	
		TD_LR.append(formWebGestalt)

		TD_LR.append(HT.Paragraph("Your selection of %d traits is being submitted to GO Tree" % len(self.theseTraits), Class="cr fs16 fwb", align="Center"))
		
		# updated by NL, moved mixedChipError() to webqtl.js and change it to mixedChipError(methodName)
		#                moved unknownChipError() to webqtl.js and change it to unknownChipError(chipName)
		if chipName == 'mixed':
			methodName = "WebGestalt"
			self.dict['js1'] = """
				<SCRIPT LANGUAGE="JavaScript">		
					setTimeout("mixedChipError('%s')" ,1000);
				</SCRIPT>
			""" % methodName 
		elif chipName.find('_NA') > 0:
			chipName = chipName[0:-3]
			self.dict['js1'] = """
                <SCRIPT LANGUAGE="JavaScript">
                setTimeout("unknownChipError('%s')",1000);
                </SCRIPT>
            """ % chipName
		else:
			self.dict['js1'] = """
				<SCRIPT LANGUAGE="JavaScript">
					setTimeout('document.WebGestalt.submit()',1000);
				</SCRIPT>
			"""
			
		self.dict['body'] = TD_LR
	
	def testChip(self, fd):
		chipName0 = ""

		for item in self.theseTraits:
			self.cursor.execute('SELECT GeneChip.GO_tree_value FROM GeneChip, ProbeFreeze, ProbeSetFreeze WHERE GeneChip.Id = ProbeFreeze.ChipId and ProbeSetFreeze.ProbeFreezeId = ProbeFreeze.Id and ProbeSetFreeze.Name = "%s"' % item.db.name)
			result = self.cursor.fetchone()
			if result:
				chipName = result[0]
				if chipName:
					if chipName != chipName0:
						if chipName0:
							return 'mixed'
						else:
							chipName0 = chipName
					else:
						pass
				else:
					self.cursor.execute('SELECT GeneChip.Name FROM GeneChip, ProbeFreeze, ProbeSetFreeze WHERE GeneChip.Id = ProbeFreeze.ChipId and ProbeSetFreeze.ProbeFreezeId = ProbeFreeze.Id and ProbeSetFreeze.Name = "%s"' % item.db.name)
					result = self.cursor.fetchone()
					chipName = '%s_NA' % result[0]
					return chipName
			else:
				self.cursor.execute('SELECT GeneChip.Name FROM GeneChip, ProbeFreeze, ProbeSetFreeze WHERE GeneChip.Id = ProbeFreeze.ChipId and ProbeSetFreeze.ProbeFreezeId = ProbeFreeze.Id and ProbeSetFreeze.Name = "%s"' % item.db.name)
				result = self.cursor.fetchone()
				chipName = '%s_NA' % result[0]
				return chipName
		return chipName

	def genGeneIdList(self, fd):
		arrayList = []
		geneList = []
		for item in self.theseTraits:
			arrayList.append(item.name)
			item.retrieveInfo()
			geneList.append(str(item.geneid))
		return arrayList, geneList
	
