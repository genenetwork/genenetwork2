import string
import os
import MySQLdb

from base import webqtlConfig

######################################### 
#      Basic Class
#########################################
class cmdClass:
	def __init__(self,fd):
		self.contents = []
		self.accessError = 0
		self.error = 0
		self.accessCode = '###Database Code : <a href="%s%s?cmd=help">%s%s?cmd=help</a>' % (webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE, webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE)
		self.data = fd.formdata
		self.cmdID = self.data.getvalue('cmd')
		self.showurl = self.data.getvalue('url')
		self.cursor = None
		self.user_ip = fd.remote_ip
		
		try:
			if not self.openMysql():
				self.accessError = 1
				self.contents = ['###Error: Database is not ready']
				return
			
			if not self.accessCount():
				self.accessError = 1
				self.contents = ['###Error: You have reached maximum access today ']
				return
			self.accessRecord()
		except:
			self.accessError = 1
			self.contents = ['###Error: Database is not ready']
			return

		
		self.probeset = self.data.getvalue('probeset')
		self.database = self.data.getvalue('db')
		self.probe = self.data.getvalue('probe')
		
		self.sourcedata = []
		
		
		try:
			self.format = self.data.getvalue('format')[:3]
		except:
			self.format = 'row'
		if not self.probeset or not self.database:
			self.error = 1
			return

	def openMysql(self):
		try:
			# con = MySQLdb.Connect(db='db_webqtl', host = webqtlConfig.MYSQL_SERVER)
			# Modified by Fan Zhang
			con = MySQLdb.Connect(db=webqtlConfig.DB_NAME,host=webqtlConfig.MYSQL_SERVER, user=webqtlConfig.DB_USER,passwd=webqtlConfig.DB_PASSWD)
			self.cursor = con.cursor()
			return 1
		except:
			return 0

	#XZ, 03/23/2009: The function name is confusing. This function is to get the database type(ProbeSet, Publish, Geno) id.	
	def getDBId(self,code):
		self.cursor.execute('SELECT DBType.Name, DBList.FreezeId from DBType, DBList WHERE DBType.Id = DBList.DBTypeId and DBList.code= "%s"' % code)
		result = self.cursor.fetchall()
		if not result:
			return (None, None)
		else:
			return result[0]

	#XZ, 03/23/2009: This is to get the inbredset name.
	def getRISet(self,prefix, DbId):
		if prefix == 'ProbeSet':
			self.cursor.execute('SELECT InbredSet.Name from InbredSet, ProbeSetFreeze, ProbeFreeze WHERE ProbeFreeze.InbredSetId = InbredSet.Id and ProbeFreeze.Id = ProbeSetFreeze.ProbeFreezeId and ProbeSetFreeze.Id = %d' % DbId)
		else:
			self.cursor.execute('SELECT InbredSet.Name from %sFreeze, InbredSet WHERE %sFreeze.InbredSetId = InbredSet.Id and %sFreeze.Id = %d' % (prefix, prefix, prefix, DbId))
		result = self.cursor.fetchall()
		if result:
			if result[0][0] == "BXD300":
				return "BXD"
			else:
				return result[0][0]
		else:
			return None
		
	def accessCount(self):
		try:
			user_ip = self.user_ip
			query = """SELECT count(id) FROM AccessLog WHERE ip_address = %s AND UNIX_TIMESTAMP()-UNIX_TIMESTAMP(accesstime)<86400"""
			self.cursor.execute(query,user_ip)
			daycount = self.cursor.fetchall()
			if daycount:
				daycount = daycount[0][0]
				if daycount > webqtlConfig.DAILYMAXIMUM:
					return 0
				else:
					return 1
			else:
				return 1
		except:
			return 0
		
	def accessRecord(self):
		try:
			user_ip = self.user_ip
			self.updMysql()
			query = """INSERT INTO AccessLog(accesstime,ip_address) values(Now(),%s)""" 
			self.cursor.execute(query,user_ip)
			self.openMysql()
		except:
			pass

	def __str__(self):
		text = map(str,self.contents)
		if self.showurl:
			text.append('http://%s%s?%s' % (os.environ['HTTP_HOST'],os.environ['SCRIPT_NAME'],os.environ['QUERY_STRING'][:-8]))
			text += self.sourcedata
		return string.join(text,'\n')

	def write(self):
		if self.cursor:
			self.cursor.close()
		try:
			browser = os.environ['HTTP_USER_AGENT']
			return '<pre>%s</pre>' % str(self)
		except:
			return str(self)
	
	def write2(self):
		print str(self)
	
	def getTraitData(self, prefix, dbId, probeset, probe = None): 
		headerDict = {'ProbeSet':'ProbeSetID', 'Publish':'RecordID', 'Geno':'Locus'}
		if prefix == None or dbId == None:
			return None, None
		if probe and prefix=='ProbeSet':
			#XZ, 03/05/2009: test http://www.genenetwork.org/webqtl/WebQTL.py?cmd=get&probeset=98332_at&db=bra08-03MAS5&probe=pm&format=col
			if string.lower(probe) in ("all","mm","pm"):
				query = "SELECT Probe.Name from Probe, ProbeSet WHERE Probe.ProbeSetId = ProbeSet.Id and ProbeSet.Name = '%s' order by Probe.Name" % probeset
				self.cursor.execute(query)
				allprobes = self.cursor.fetchall()
				if not allprobes:
					return None, None
					
				fetchprobes = []
				for item in allprobes:
					if probe == 'all':
						fetchprobes.append(item[0])
					else:		
						try:
							taildigit =  int(item[0][-1]) % 2
							if probe == "pm" and taildigit == 1:
								fetchprobes.append(item[0])
							if probe == "mm" and taildigit == 0:
								fetchprobes.append(item[0])
						except:
							pass
				if not fetchprobes:
					return None, None
				#XZ, 03/05/2009: Xiaodong changed Data to ProbeData	
				query = "SELECT Strain.Name, ProbeData.value, Probe.Name from ProbeData, ProbeFreeze, ProbeSetFreeze, ProbeXRef, Strain, Probe, ProbeSet WHERE ProbeSet.Name = '%s' and Probe.ProbeSetId = ProbeSet.Id and ProbeXRef.ProbeId = Probe.Id and ProbeXRef.ProbeFreezeId = ProbeFreeze.Id and ProbeSetFreeze.ProbeFreezeId = ProbeFreeze.Id and ProbeSetFreeze.Id = %d and ProbeXRef.DataId = ProbeData.Id and ProbeData.StrainId = Strain.Id and Probe.Name in (%s) order by Strain.Id, Probe.Name " % (probeset,dbId, "'" + string.join(fetchprobes, "', '") +"'")
				self.cursor.execute(query)
				traitdata = self.cursor.fetchall()
				if not traitdata:
					pass
				else:
					nfield = len(fetchprobes)
					heads = [['ProbeSet'] + [probeset]*nfield]
					heads.append(['probe'] + fetchprobes)
					posdict = {}
					i = 0
					for item in fetchprobes:
						posdict[item] = i
						i += 1
					prevStrain = ''
					traitdata2 = []
					i = -1 
					for item in traitdata:
						if item[0] != prevStrain:
							prevStrain = item[0]
							i += 1
							traitdata2.append([item[0]] +  [None] * nfield)
						else:
							pass
						traitdata2[i][posdict[item[-1]]+1] = item[1]
					
					traitdata = traitdata2
			#XZ, 03/05/2009: test http://www.genenetwork.org/webqtl/WebQTL.py?cmd=get&probeset=98332_at&db=bra08-03MAS5&probe=119637&format=col
			else:
				heads = [('ProbeSetId', probeset), ('ProbeId',probe)]
				#XZ, 03/05/2009: Xiaodong changed Data to ProbeData
				query = "SELECT Strain.Name, ProbeData.value from ProbeData, ProbeFreeze, ProbeSetFreeze, ProbeXRef, Strain, Probe, ProbeSet WHERE Probe.Name = '%s' and ProbeSet.Name = '%s' and Probe.ProbeSetId = ProbeSet.Id and ProbeXRef.ProbeId = Probe.Id and ProbeXRef.ProbeFreezeId = ProbeFreeze.Id and ProbeSetFreeze.ProbeFreezeId = ProbeFreeze.Id and ProbeSetFreeze.Id = %d and ProbeXRef.DataId = ProbeData.Id and ProbeData.StrainId = Strain.Id" % (probe,probeset,dbId)
				#print 'Content-type: text/html\n'
				self.cursor.execute(query)
				traitdata = self.cursor.fetchall()
		#XZ, 03/05/2009: test http://www.genenetwork.org/webqtl/WebQTL.py?cmd=get&probeset=98332_at&db=bra08-03MAS5&format=col
		elif prefix=='ProbeSet': #XZ: probeset data
			heads = [(headerDict[prefix], probeset)]
			query = "SELECT Strain.Name, %sData.value from %sData, Strain, %s, %sXRef WHERE %s.Name = '%s' and %sXRef.%sId = %s.Id and %sXRef.%sFreezeId = %d and  %sXRef.DataId = %sData.Id and %sData.StrainId = Strain.Id order by Strain.Id" % (prefix, prefix, prefix, prefix, prefix, probeset,prefix, prefix, prefix, prefix, prefix, dbId, prefix, prefix, prefix)
			self.cursor.execute(query)
			traitdata = self.cursor.fetchall()
		#XZ, 03/05/2009: test http://www.genenetwork.org/webqtl/WebQTL.py?cmd=get&probeset=10834&db=BXDPublish&format=col
		elif prefix=='Publish':
			heads = [(headerDict[prefix], probeset)]
			#XZ, 03/05/2009: Xiaodong changed Data to PublishData
			query = "SELECT Strain.Name, PublishData.value from PublishData, Strain, PublishXRef, PublishFreeze WHERE PublishXRef.InbredSetId = PublishFreeze.InbredSetId and PublishData.Id = PublishXRef.DataId and PublishXRef.Id = %s and PublishFreeze.Id = %d and PublishData.StrainId = Strain.Id" % (probeset, dbId)
			self.cursor.execute(query)
			traitdata = self.cursor.fetchall()
		#XZ, 03/05/2009: test http://www.genenetwork.org/webqtl/WebQTL.py?cmd=get&probeset=rs13475701&db=BXDGeno&format=col
		else: #XZ: genotype data
			heads = [(headerDict[prefix], probeset)]
			RISet = self.getRISet(prefix, dbId)
			self.cursor.execute("select SpeciesId from InbredSet where Name = '%s'" % RISet)
			speciesId = self.cursor.fetchone()[0]			
			#XZ, 03/05/2009: Xiaodong changed Data to %sData
			query = "SELECT Strain.Name, %sData.value from %sData, Strain, %s, %sXRef WHERE %s.SpeciesId=%s and %s.Name = '%s' and %sXRef.%sId = %s.Id and %sXRef.%sFreezeId = %d and  %sXRef.DataId = %sData.Id and %sData.StrainId = Strain.Id order by Strain.Id" % (prefix, prefix, prefix, prefix, prefix, speciesId, prefix, probeset,prefix, prefix, prefix, prefix, prefix, dbId, prefix, prefix, prefix)
			self.cursor.execute(query)
			traitdata = self.cursor.fetchall()
		if traitdata:
			return traitdata, heads
		else:
			return None, None
