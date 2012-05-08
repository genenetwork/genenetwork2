"""
Maintainnce module. Update Genotype data, user can update the Marker 
one by one through web interface, or batch update one Population 
through submit genotype file
"""

import string
import os

from htmlgen import HTMLgen2 as HT

from base.templatePage import templatePage
from base import webqtlConfig
from utility import webqtlUtil
from dbFunction import webqtlDatabaseFunction



"""
The Fields of Geno, GenoXRef table that be shown to user for updating
"""
MarkerSpeciesInfoField = ['Name', 'Chr', 'Mb', 'Sequence', 'Source']
MarkerGroupInfoField = ['cM', 'Used_for_mapping']
MarkerInfoField = MarkerSpeciesInfoField + MarkerGroupInfoField
markerName_Feild_Separator = '_and_'

	
# retrieve all of the Inbred Set names and group them by Species
def retrieveSpeciesInbredSetGroup(cursor):
	"""
	@type cursor: MySQLdb.connect.cursor
	rtype: dictionary
	return: dictionary, the key are the name of Species, the value are 
	the InbredSet Names that related with the Species
	"""

	SpeciesInbredSet={}
	cursor.execute("""
		SELECT 
			Species.Id, Species.Name 
		FROM 
			Species, InbredSet
		WHERE 
			Species.Id=InbredSet.SpeciesId AND
			MappingMethodId = 1
		GROUP BY
			Species.Id
		""")
	species=cursor.fetchall()

	for item in species:
		SpeciesId, SpeciesName = item
		cursor.execute("SELECT distinct(InbredSet.Name) FROM InbredSet, GenoFreeze, GenoXRef WHERE SpeciesId=%d and GenoFreeze.InbredSetId = InbredSet.Id and GenoXRef.GenoFreezeId = GenoFreeze.Id and GenoXRef.Used_for_mapping='Y' " % SpeciesId)
		InbredSetNames=cursor.fetchall()

		InbredSetNameList=[]
		for InbredSetName in InbredSetNames:
			if InbredSetName[0]=='BXD300':
				continue
			InbredSetNameList.append(InbredSetName[0])
		SpeciesInbredSet[SpeciesName]=InbredSetNameList

	return SpeciesInbredSet


#XZ: This function will be called in many places.
# Each caller might organize the result in different way.
# So the raw database results are returned.
def retrieveGenoCode(cursor, InbredSetName):

	cursor.execute("""
		SELECT
			AlleleType, AlleleSymbol, DatabaseValue
		FROM
			GenoCode, InbredSet
		WHERE
			InbredSet.Name = '%s' AND
			InbredSetId = InbredSet.Id
                """ % InbredSetName )
	results = cursor.fetchall()

	GenoCode = []

	for one_result in results:
		GenoCode.append(one_result)

	return GenoCode


def retrieveGeneticTypeOfInbredSet(cursor, InbredSetName):

	GeneticType = ''

	cursor.execute("""
                SELECT
                        GeneticType
                FROM
                        InbredSet
                WHERE
                        InbredSet.Name=%s
                """, InbredSetName)
        result=cursor.fetchone()

        if result:
                GeneticType = result[0]

	return GeneticType




#XZ: For one group, retrieve the list of all strains that are in StrainXRef and used for mapping
def retrieveStrainUsedForMapping(cursor, GroupName):
	"""
	@type cursor: MySQLdb.connect.cursor
	@type GroupName: string
	@param GroupName: In MySQL table, it's called Inbred Set name, in GeneNetwork's Homepage, it's called group
	
	@rtype: list
	@return: The Strain's names that related with the Inbred Set
	"""

	cursor.execute("""
		SELECT 
			Strain.Name 
		FROM
			Strain, StrainXRef, InbredSet
		WHERE
			InbredSet.Name = '%s' AND
			StrainXRef.InbredSetId=InbredSet.Id AND
			StrainXRef.StrainId = Strain.Id AND
			StrainXRef.Used_for_mapping = 'Y'
		ORDER BY
			StrainXRef.OrderId
		""" % GroupName)
	results = cursor.fetchall()

	StrainList=[]
	for item in results:
		StrainList.append(item[0])

	return StrainList
	

#XZ: For one group, retrieve the dictionary of all strain id, name pairs that are in StrainXRef and used for mapping
def retrieveStrainNameIdUsedForMapping(cursor, GroupName):
        """
        @type cursor: MySQLdb.connect.cursor
        @type GroupName: string
        @param GroupName: In MySQL table, it's called Inbred Set name, in GeneNetwork's Homepage, it's called group

        @rtype: dictionary
        @return: dictionary, the key is Strain's name, the value is Strain's Id
        """

	StrainNameId = {}

        cursor.execute("""
                SELECT
                        Strain.Name, Strain.Id
                FROM
                        Strain, StrainXRef, InbredSet
                WHERE
                        InbredSet.Name = '%s' AND
                        StrainXRef.InbredSetId=InbredSet.Id AND
                        StrainXRef.StrainId = Strain.Id AND
                        StrainXRef.Used_for_mapping = 'Y'
                ORDER BY
                        StrainXRef.OrderId
                """ % GroupName)
        results = cursor.fetchall()

        for item in results:
                StrainNameId[item[0]] = item[1]

        return StrainNameId



# retrieve the strain's id by name, the Strain should bind with Inbred Set
#if the strain's name cann't be found, the id will be set to 'None' 
def retrieveStrainIds(cursor, StrainList, InbredSetName):
	"""
	@type cursor: MySQLdb.connect.cursor
	@type StrainList: list
	@param StrainList: the list of Strains' Name
	@type InbredSetName: string

	@rtype: dictionary
	@return: dictionary, the key is Strain's name, the value is Strain's Id
	"""

	StrainIds={}
	for Strain in StrainList:
		cursor.execute("""
			SELECT 
				Strain.Id 
			FROM 
				Strain,StrainXRef,InbredSet
			WHERE 
				Strain.Id=StrainXRef.StrainId AND
				StrainXRef.InbredSetId=InbredSet.Id AND
				Strain.Name=%s AND
				InbredSet.Name=%s
		""", (Strain, InbredSetName))
		result=cursor.fetchone()
		if result:
			StrainIds[Strain]=result[0]
		else:
			StrainIds[Strain]=None

	return StrainIds
	


# retrieve the GenoFreezeId
def retrieveGenoFreezeId(cursor, InbredSetName):
	"""
	@type cursor: MySQLdb.connect.cursor
	@type InbredSetName: string

	@rtype: int
	@return: the GenoFreezeId related with the Inbred Set's name
	"""

	cursor.execute("""
		SELECT 
			GenoFreeze.Id
		FROM
			InbredSet, GenoFreeze
		WHERE
			GenoFreeze.InbredSetId=InbredSet.Id AND
			InbredSet.Name=%s
		""", InbredSetName)
	result=cursor.fetchone()
	
	if result:
		return result[0]
	else:
		return None
		

# retrieve the DataId 
def retrieveDataId(cursor, GenoId, InbredSetName):
	"""
	@type cursor: MySQLdb.connect.cursor
	@type GenoId: int
	@type InbredSetName: int
	
	@rtype: int
	@return: the DataId relate with the Geno(Marker) and the Inbred Set
	"""

	cursor.execute("""
		SELECT 
			GenoXRef.DataId
		FROM
			GenoXRef, GenoFreeze, InbredSet
		WHERE
			GenoXRef.GenoFreezeId=GenoFreeze.Id AND
			GenoFreeze.InbredSetId=InbredSet.Id AND
			GenoXRef.GenoId=%s AND
			InbredSet.Name=%s
		""", (GenoId, InbredSetName))
	result=cursor.fetchone()

	if result:
		return result[0]
	else:
		return None


# retrieve the max Id from GenoData table
def retrieveMaxGenoDataId(cursor):
	"""
	@type cursor: MySQLdb.connect.cursor
	
	@rtype: int
	@return: the maximal Id of the Data table
	"""
	
	cursor.execute('SELECT max(Id) FROM GenoData')
	results = cursor.fetchone()

	return results[0]


# retrieve the max Id from Geno table	
def retrieveMaxGenoId(cursor):
	"""
	@type cursor: MySQLdb.connect.cursor
	
	@rtype: int	
	@return: the maximal Id of the Geno table
	"""
	
	cursor.execute('SELECT max(Id) FROM Geno')
	results = cursor.fetchone()
	
	return results[0]
	

# retrieve the strain names related with a data.Id
# Note that for one group, even if one strain is labelled as Used_for_mapping in StrainXRef table,
# if the allele value for this strain is unknown, there is no record for this strain along with this group in GenoData table.
# So the list of strains returned by this function <= list of strains returned by function retrieveStrainUsedForMapping.
def retrieveDataStrains(cursor, DataId):
	"""
	@type cursor: MySQLdb.connect.cursor
	@type DataId: int
	
	@rtype: list
	@return: the names list of the Strains that related with the DataId
	"""
	
	cursor.execute("SELECT Strain.Name FROM Strain, GenoData WHERE GenoData.StrainId=Strain.Id AND GenoData.Id=%s", DataId)
	results=cursor.fetchall()
	
	Strains=[]
	for item in results:
		Strains.append(item[0])
		
	return Strains
				


def retrieveMarkerNameForGroupByRange(cursor, InbredSetName, Chr, MbStart, MbEnd):

	MarkerName = []

	SpeciesId = webqtlDatabaseFunction.retrieveSpeciesId(cursor, InbredSetName)

	GenoFreezeId = retrieveGenoFreezeId(cursor, InbredSetName)

	MbStartClause = ''
	MbEndClause = ''

	try:
		MbStartClause = 'and  Mb >= %s ' % float(MbStart)
	except:
		pass

	try:
		MbEndClause = 'and  Mb <= %s' % float(MbEnd)
	except:
		pass


	cmd = "SELECT Geno.Name FROM Geno, GenoXRef WHERE Geno.SpeciesId=%s and Chr='%s' " % (SpeciesId, Chr) + MbStartClause + MbEndClause +  " and GenoXRef.GenoFreezeId=%s and GenoXRef.GenoId=Geno.Id and GenoXRef.Used_for_mapping='Y' order by Mb" % (GenoFreezeId)

	cursor.execute(cmd)

	results = cursor.fetchall()
	for one_result in results:
		MarkerName.append( one_result[0] )

	return MarkerName


	
# retrive the Marker's infomation from Geno and GenoXRef table, 
# the information includes the Id of the marker matchs and all of the MarkerInfoField that defined upper
def retrieveMarkerInfoForGroup(cursor, MarkerName, InbredSetName):
	"""
	@type cursor: MySQLdb.connect.cursor
	@type MarkerName: string
	
	@rtype: list
	@return: the Marker's Id, Name, Chr, cM, Mb, Sequence, Source
	"""


	SpeciesId = webqtlDatabaseFunction.retrieveSpeciesId(cursor, InbredSetName)

	GenoFreezeId = retrieveGenoFreezeId(cursor, InbredSetName)
	
	cmd = ','.join( MarkerInfoField )
	cmd = "SELECT Geno.Id," + cmd + " FROM Geno, GenoXRef WHERE Geno.SpeciesId=%s and Geno.Name='%s' and GenoXRef.GenoFreezeId=%s and GenoXRef.GenoId=Geno.Id" % (SpeciesId, MarkerName, GenoFreezeId)
	cursor.execute(cmd)
	result = cursor.fetchone()
	
	if result:
		return result
	else:
		return None


def retrieveMarkerPositionForSpecies(cursor, GenoId):

	Chr = ''
	Mb = ''

	cursor.execute( "select Chr, Mb from Geno where Id=%s" % GenoId )
	result = cursor.fetchone()

	Chr = result[0]
	Mb = result[1]

	return Chr, Mb


def checkIfMarkerInSpecies (cursor, MarkerName, InbredSetName):

	cmd = "SELECT Geno.Id FROM Geno, InbredSet, Species WHERE Geno.SpeciesId=Species.Id AND Geno.Name='%s' and InbredSet.Name = '%s' and InbredSet.SpeciesId = Species.Id" % (MarkerName, InbredSetName)
	cursor.execute(cmd)
	result = cursor.fetchone()

	if result:
		return result
	else:
		return None

	
	
		
# retrive the Marker's Used_for_mapping status from MySQL
# for one marker, if we want it be contains in the special genotype file, we can set its value in Used_for_mapping column to 'Y' in the GenoXRef table.
# In GenoXRef table, the default value of column Used_for_mapping is 'N'.
# GenoXRef table is the relationship of the Marker and the allele value that this marker in special genotype
def mappingForThisGroup(cursor, GenoFreezeId, GenoId):
	"""
	@type cursor: MySQLdb.connect.cursor
	@type MarkerName: string
	@type InbredSetName: string
	
	@rtype: boolean
	@return: the status that if the marker's exprssion value in special Inbred Set will be hide(not shown in genotype file)
	"""
	
	cursor.execute("""
		SELECT 
			Used_for_mapping
		FROM
			GenoXRef
		WHERE
			GenoFreezeId = %s AND
			GenoId = %s
		""", (GenoFreezeId, GenoId))
	result = cursor.fetchone()

	Used_for_mapping = False
	if result:
		if result[0] == 'Y':
			Used_for_mapping = True

	return Used_for_mapping
	
			
# Retrieve the allele values of a Marker in specific genotype
#
# 1. Retrieve strain name and allele value from GenoData table
# 2. Put the result into dictionary, the key is strain name. The value is allele (-1, 0, 1).
# 
# Note even one strain is used for mapping for one group in GenoXRef table. When its genotype is unknown,
# it has no record in GenoData table (e.g., BXD102 strain for marker rs6376963).
# In this case, the dictionary key doesn't include this strain.
def retrieveAllele (cursor, GenoFreezeId, GenoId):
	"""
	@type cursor: MySQLdb.connect.cursor
	@type MarkerName: string
	@type InbredSetName: string
	
	@rtype: dictionary
	@return: dictionary, the keys are strain names, the values are alleles 
	that the Marker in specials Inbred Set
	"""

	Alleles = {}

	#retrieve the strains' name and their allele values 
	cursor.execute("""
		SELECT 
			Strain.Name, GenoData.Value 
		FROM
			Strain, GenoData, GenoXRef
		WHERE
			GenoXRef.GenoFreezeId=%s AND
			GenoXRef.GenoId=%s AND
			GenoXRef.DataId=GenoData.Id AND
			GenoData.StrainId=Strain.Id
		""", (GenoFreezeId, GenoId))
	results = cursor.fetchall()
	
	# set the allele value of the strain that appears in Data to the value from Data 
	for item in results:
		Alleles[item[0]]=item[1]
		
	return Alleles



def retrieveGroupNeedExported (cursor, GenoId):

	Groups = []

	cursor.execute("""
		SELECT
			InbredSet.Name
		FROM
			InbredSet, GenoFreeze, GenoXRef
		WHERE
			Used_for_mapping = 'Y' AND
			GenoXRef.GenoId = %s AND
			GenoXRef.GenoFreezeId = GenoFreeze.Id AND
			GenoFreeze.InbredSetId = InbredSet.Id
		""", (GenoId) )
	results = cursor.fetchall()

        if results:
		for one_result in results:
			Groups.append( one_result[0] )

        return Groups


def get_chr_num (cursor, Chr='', SpeciesId=0):

	chr_num = 99

	cmd = "SELECT OrderId FROM Chr_Length WHERE Name='%s' and SpeciesId=%s " % (Chr, SpeciesId)

	cursor.execute(cmd)
	result = cursor.fetchone()

	if result:
		chr_num = result[0]

	return chr_num



def addGeno(cursor, GenoId, InbredSetName, MarkerWebID, fd):

	SpeciesId = webqtlDatabaseFunction.retrieveSpeciesId(cursor, InbredSetName)

	Name = fd.formdata.getvalue( MarkerWebID + markerName_Feild_Separator + 'Name' )
	Chr = fd.formdata.getvalue( MarkerWebID + markerName_Feild_Separator + 'Chr' )
	Mb = fd.formdata.getvalue( MarkerWebID + markerName_Feild_Separator + 'Mb' )
	Sequence = fd.formdata.getvalue( MarkerWebID + markerName_Feild_Separator + 'Sequence' )
	Source = fd.formdata.getvalue( MarkerWebID + markerName_Feild_Separator + 'Source' )

	chr_num = get_chr_num (cursor, Chr, SpeciesId)

	cmd = "INSERT INTO Geno (Id, SpeciesId, Name, Marker_Name, Chr, Mb, Sequence, Source, chr_num) VALUES (%s, %s, '%s', '%s', '%s', %s, '%s', '%s', %s )" % (GenoId, SpeciesId, Name, Name, Chr, Mb, Sequence, Source, chr_num)
	cursor.execute(cmd)



def updateGeno(cursor, GenoId, InbredSetName, MarkerWebID, fd):

	SpeciesId = webqtlDatabaseFunction.retrieveSpeciesId(cursor, InbredSetName)

	Chr = fd.formdata.getvalue( MarkerWebID + markerName_Feild_Separator + 'Chr' )
	cmd = "UPDATE Geno SET Chr='%s' WHERE Id=%s" % (Chr, GenoId)
	cursor.execute(cmd)

	chr_num = get_chr_num (cursor, Chr, SpeciesId)
	cmd = "UPDATE Geno SET chr_num=%s WHERE Id=%s" % (chr_num, GenoId)
	cursor.execute(cmd)

	Mb = fd.formdata.getvalue( MarkerWebID + markerName_Feild_Separator + 'Mb' )
	cmd = "UPDATE Geno SET Mb=%s WHERE Id=%s" % (Mb, GenoId)
	cursor.execute(cmd)

	Sequence = fd.formdata.getvalue( MarkerWebID + markerName_Feild_Separator + 'Sequence' )
	cmd = "UPDATE Geno SET Sequence='%s' WHERE Id=%s" % (Sequence, GenoId)
	cursor.execute(cmd)

	Source = fd.formdata.getvalue( MarkerWebID + markerName_Feild_Separator + 'Source' )
	cmd = "UPDATE Geno SET Source='%s' WHERE Id=%s" % (Source, GenoId)
	cursor.execute(cmd)


def updateGenoXRef(cursor, GenoFreezeId, GenoId, MarkerWebID, fd):

	cM = fd.formdata.getvalue( MarkerWebID + markerName_Feild_Separator + 'cM' )
	cmd = "UPDATE GenoXRef SET cM=%s WHERE GenoFreezeId=%s AND GenoId=%s" % (cM, GenoFreezeId, GenoId)
	cursor.execute(cmd)

	Used_for_mapping = fd.formdata.getvalue( MarkerWebID + markerName_Feild_Separator + 'Used_for_mapping')

	if Used_for_mapping == 'on':
		cmd = "UPDATE GenoXRef SET Used_for_mapping='Y' WHERE GenoFreezeId=%s AND GenoId=%s" % (GenoFreezeId, GenoId)
	else:
		cmd = "UPDATE GenoXRef SET Used_for_mapping='N' WHERE GenoFreezeId=%s AND GenoId=%s" % (GenoFreezeId, GenoId)
	cursor.execute(cmd)



def addGenoXRef(cursor, GenoFreezeId, GenoId, DataId, MarkerWebID, fd):

	cM = fd.formdata.getvalue( MarkerWebID + markerName_Feild_Separator + 'cM')

	Used_for_mapping = fd.formdata.getvalue( MarkerWebID + markerName_Feild_Separator + 'Used_for_mapping')

	Used_for_mapping_db_value = 'N'
	if Used_for_mapping == 'on':
		Used_for_mapping_db_value = 'Y'

	cmd = "INSERT INTO GenoXRef (GenoFreezeId, GenoId, DataId, cM, Used_for_mapping) VALUES (%s, %s, %s, %s, '%s')" % (GenoFreezeId, GenoId, DataId, cM, Used_for_mapping_db_value)

	cursor.execute(cmd)



def insertGenoData(cursor, InbredSetName, DataId, MarkerWebID, fd):

	StrainList = retrieveStrainUsedForMapping (cursor, InbredSetName)
	StrainIds = retrieveStrainIds(cursor, StrainList, InbredSetName)

	for Strain in StrainList:
		if fd.formdata.has_key( MarkerWebID + markerName_Feild_Separator + Strain ):
			value = fd.formdata.getvalue( MarkerWebID + markerName_Feild_Separator + Strain )

			# XZ: The legitimate values are hard coded. Should be dynamical (from database).
			try:
				int_value = int(float(value))

				if int_value in (0, 1, -1):
					cmd = "INSERT INTO GenoData VALUES(%d,%d,%s)"%(DataId, StrainIds[Strain], int_value)
					cursor.execute(cmd)
			except:
				pass


#XZ: This function is to compare the input position (Chr, Mb) with position in database.
# It should be executed before update database record.
def getAllGroupsNeedExported(cursor, GroupNeedExport=[], GenoId=0, Chr='', Mb=''):

	db_Chr, db_Mb = retrieveMarkerPositionForSpecies(cursor, GenoId)

	if str(Chr) == str(db_Chr) and str(Mb) == str(db_Mb):
		pass
	else:
		temp = retrieveGroupNeedExported (cursor, GenoId)
		for one_group in temp:
			try:
				GroupNeedExport.index(one_group)
			except:
				GroupNeedExport.append(one_group)

	return GroupNeedExport




class GenoUpdate(templatePage):

	def __init__(self, fd):	

		templatePage.__init__(self, fd)
		
		# get mysql connection, if not, show error
		if not self.openMysql():
			heading = "Geno Updating"
			detail = ["Can't connect to MySQL server"]
			self.error(heading=heading,detail=detail)
			return
			

		self.dict['title'] = 'Geno Updating'

		# status is the switch, direct what's the next step
		try:
			status = fd.formdata.getvalue('status')
		except:
			status = ''

		if fd.formdata.getvalue('submit')=='Clear':
			status=''

		if not status: # show 
			self.dict['body']=self.showSelectionPage()
		elif status=='search' or status == 'addNewMarker':
			InbredSetName = fd.formdata.getvalue('InbredSetName')
			Chr = fd.formdata.getvalue('Chr')

			if not InbredSetName:
				self.dict['body']= "Please select the population."
				return
			elif not Chr:
                                self.dict['body']= "Please input Chr."
                                return
			else:
				self.dict['body']=self.showAllMarkers (InbredSetName, Chr, fd)

		elif status == 'editMarkerTable':
			self.dict['body'] = self.editMarkerTable(fd)

		elif status == 'checkMarkerHasBeenInGroup': # check if there is anything changed.
			InbredSetName = fd.formdata.getvalue('InbredSetName')
			Marker = fd.formdata.getvalue('Name')
			self.dict['body'] = self.checkMarkerHasBeenInGroup (InbredSetName, Marker, fd)

		elif status=='changeMarker': #insert new marker
                        InbredSetName = fd.formdata.getvalue('InbredSetName')
                        self.dict['body']=self.changeMarker(InbredSetName, fd)

		else: #this part is used to test, the proceduce won't come here in normal cycle
			HTTable = HT.TableLite(border=0, cellspacing=1, cellpadding=1,align="center")
			for key in fd.formdata.keys():
				HTTable.append(HT.TR(HT.TD(key), HT.TD(':'), HT.TD(fd.formdata.getvalue(key))))
			self.dict['body'] = HTTable
			
			


	# this is the first page, user upload their genotype file here, or input
	# which marker they want to update
	def showSelectionPage(self):
		"""
		The first page, in this page, user can upload a genotype file for batch updating, 
		or enter a Marker for one by one updating

		@rtype: string
		@return: HTML
		"""

		# get the InbredSet Name list
		SpeciesInbredSet = retrieveSpeciesInbredSetGroup(self.cursor)
		
		# generate homepage

		HTTableLite_Population = HT.TableLite(border=0, width="100%")

		HTTD_InbredSet = HT.TD(width="30%")

		HTSelect_InbredSetNames = HT.Select(name='InbredSetName')
		HTSelect_InbredSetNames.append("")
		for SpeciesName in SpeciesInbredSet.keys():
			HT_OptGroup_Species=HT.Optgroup()
			HT_OptGroup_Species.label=SpeciesName
			for InbredSetName in SpeciesInbredSet[SpeciesName]:
				HT_OptGroup_Species.append(InbredSetName)
			HTSelect_InbredSetNames.append(HT_OptGroup_Species)

		HTTD_InbredSet.append( HT.Font(HT.Strong('Group (required) '), color="red") )
		HTTD_InbredSet.append(HTSelect_InbredSetNames)

                HTTableLite_Population.append(HT.TR(HTTD_InbredSet))

		HTTableLite_Marker = HT.TableLite(border=0, width="100%")
		HTTD_Chr = HT.TD()
		HTTD_Chr.append( HT.Font(HT.Strong('Chr (required) '), color="red") )
		HTTD_Chr.append(HT.Input(name='Chr', size=3))
		HTTD_Mb = HT.TD()
		HTTD_Mb.append(HT.Font(HT.Strong('Mb')), ' from ')
		HTTD_Mb.append(HT.Input(name='MbStart', size=10))
		HTTD_Mb.append(' to ')
		HTTD_Mb.append(HT.Input(name='MbEnd', size=10))
		HTTableLite_Marker.append(HT.TR(HTTD_Chr), HT.TR(), HT.TR(HTTD_Mb) )



		HTTableLite_Search = HT.TableLite(border=1, width="100%")
		HTTableLite_Search.append(
		    HT.TR(HT.TD(HTTableLite_Population, height="100")),
		    HT.TR(HT.TD("Enter Chr and Mb range", HT.BR(), HT.BR(),
				HTTableLite_Marker,
				height="100")) 
		)	


		HTInput_Submit = HT.Input(type='submit', name='submit', value='Submit',Class="button")
		HTInput_Clear = HT.Input(type='submit', name='submit', value='Clear', Class="button")
		HTInput_FormId = HT.Input(type='hidden', name='FormID', value='updGeno')
		HTInput_Status = HT.Input(type='hidden', name='status', value='search')
						
		HTForm_Search = HT.Form(cgi=os.path.join(webqtlConfig.CGIDIR, 'main.py'), \
			enctype= 'multipart/form-data', submit='')
		HTForm_Search.append(HTTableLite_Search)
		HTForm_Search.append(HTInput_Submit)
		HTForm_Search.append(HTInput_Clear)

		HTForm_Search.append(HTInput_FormId)
		HTForm_Search.append(HTInput_Status)

		HTTableLite_Content = HT.TableLite(border=1, width="100%")
		HTTableLite_Content.append(HT.TR(HT.TD(HTForm_Search, width="50%"), \
						HT.TD(HT.Font(HT.Strong("Instructions:"), HT.BR(),HT.BR(), "The \"from\" and \"to\" inputs for Mb range are optional.", HT.BR(),HT.BR(), "If only the \"from\" input is provided, the result will be all markers from the input position to the end of chromosome.", HT.BR(),HT.BR(), "If only the \"to\" input is provided, the result will be all markers from the beginning of the chromosome to the input position.", HT.BR(),HT.BR(), "If no input is provided for Mb range, the result will be all markers on the chromosome."), valign='top', width="50%") \
						))
		
		return HTTableLite_Content


	

	def searchMappingMarkerInDB (self, InbredSetName="", Chr='', MbStart='', MbEnd=''):
		"""
		Show Marker's information for updating or inserting

		@type InbredSetName: string
		@type MarkerName: string

		@rtype: string
		@return: The HTML form that contains the Marker's information
		"""


		MarkerInfoDic = {}		

		MarkerNamesByRange = retrieveMarkerNameForGroupByRange(self.cursor, InbredSetName, Chr, MbStart, MbEnd)

		for one_MarkerName in MarkerNamesByRange:
			one_MarkerGroupInfo = retrieveMarkerInfoForGroup (self.cursor, one_MarkerName, InbredSetName)
			MarkerInfoDic[ one_MarkerName ] = one_MarkerGroupInfo

		return MarkerNamesByRange, MarkerInfoDic



	def showAllMarkers( self, InbredSetName, Chr, fd ):

		MbStart = fd.formdata.getvalue('MbStart')
		MbEnd = fd.formdata.getvalue('MbEnd')

		inputStatus = fd.formdata.getvalue('status')

		newMarkerNameQuantityDic = {}
		MarkerNameAdded = []

		MarkerNames, MarkerInfoDic = self.searchMappingMarkerInDB (InbredSetName=InbredSetName, Chr=Chr, MbStart=MbStart, MbEnd=MbEnd)

		MainTable = HT.TableLite(border=1, cellspacing=1, cellpadding=1,align="left")

		if inputStatus == 'search':


			InputTable = HT.TableLite(border=1, cellspacing=1, cellpadding=1,align="left")

			InputTable.append( HT.TR( HT.TD( HT.Textarea(name="InputNewMarker", rows=10, cols=20)),
						HT.TD(HT.Font( "Add one input per line.", HT.BR(), HT.BR(), \
								"Each input must be in the format of: existing marker name,quantity", HT.BR(), HT.BR(), \
								"For instance, the input rs6376963, 2 will add two markers after rs6376963", HT.BR(), HT.BR(), \
								"The input existing marker name must have been shown in the table below.", HT.BR(), HT.BR(), color="red"), \
								HT.Input(type='submit', name='inputmarker_submit', value='Add new markers', Class="button", onClick= "changeStatusSubmit(this.form, 'addNewMarker');" ) ) ) )

			MainTable.append( HT.TR(HT.TD(InputTable)) )
		else:
			InputNewMarkerString = fd.formdata.getvalue('InputNewMarker')

			InputNewMarkerLines = InputNewMarkerString.split('\n')
			for one_line in InputNewMarkerLines:
				one_line = one_line.strip()
				if len(one_line) > 0:
					one_line_tokens = one_line.split(',')
					try:
						first_token = one_line_tokens[0].strip()
						second_token = one_line_tokens[1].strip()
						second_token = int( second_token )
						if first_token in MarkerNames:
							newMarkerNameQuantityDic[ first_token ] = second_token
					except:
						pass


		MarkerTable = HT.TableLite(border=1, cellspacing=1, cellpadding=1,align="left")

		HeaderRow = HT.TR()


		for one_field in MarkerSpeciesInfoField:
			HeaderRow.append( HT.TD(one_field) )

		for one_field in MarkerGroupInfoField:
			HeaderRow.append( HT.TD(one_field) )

		GenoFreezeId = retrieveGenoFreezeId(self.cursor, InbredSetName)
		StrainList = retrieveStrainUsedForMapping (self.cursor, InbredSetName)

		for one_strain in StrainList:
                        HeaderRow.append( HT.TD(one_strain) )

		MarkerTable.append( HeaderRow )


		for one_MarkerName in MarkerNames:
			one_MarkerGroupInfo = MarkerInfoDic[ one_MarkerName ]
			oneMarkerRow = self.showOneMarker (InbredSetName=InbredSetName, MarkerName=one_MarkerName, suffix="", MarkerGroupInfo=one_MarkerGroupInfo, StrainList=StrainList, marker_type='existed')
			MarkerTable.append( oneMarkerRow )

			if newMarkerNameQuantityDic.has_key(one_MarkerName):
				for i in range(0, newMarkerNameQuantityDic[one_MarkerName]):
					MarkerNameAdded.append( one_MarkerName + '_add_' + str(i) )
					oneMarkerRow = self.showOneMarker (InbredSetName=InbredSetName, MarkerName=one_MarkerName, suffix='_add_' + str(i), MarkerGroupInfo=one_MarkerGroupInfo, StrainList=StrainList, marker_type='add')
					MarkerTable.append( oneMarkerRow )



		MarkerTable.append( HT.TR(HT.TD( HT.Input(type='submit', name='markertable_submit', value='Edit marker table',Class="button", onClick= "changeStatusSubmit(this.form, 'editMarkerTable');") )) )

		MainTable.append( HT.TR(HT.TD(MarkerTable)) )


		HTInput_Submit = HT.Input(type='hidden', name='submit', value='Submit',Class="button")
		HTInput_FormId = HT.Input(type='hidden', name='FormID', value='updGeno')
		HTInput_Status = HT.Input(type='hidden', name='status', value='')
                HTInput_InbredSetName = HT.Input(type='hidden', name='InbredSetName', value=InbredSetName)
		HTInput_Chr = HT.Input(type='hidden', name='Chr', value=Chr)
		HTInput_MbStart = HT.Input(type='hidden', name='MbStart', value=MbStart)
		HTInput_MbEnd = HT.Input(type='hidden', name='MbEnd', value=MbEnd)
		HTInput_MarkerNamesExisted = HT.Input(type='hidden', name='MarkerNamesExisted', value=','.join(MarkerNames) )
		HTInput_MarkerNamesAdded = HT.Input(type='hidden', name='MarkerNamesAdded', value=','.join(MarkerNameAdded) )


                HTForm_showAllMarkers = HT.Form(cgi=os.path.join(webqtlConfig.CGIDIR, 'main.py'), enctype= 'multipart/form-data', submit=HTInput_Submit)

		HTForm_showAllMarkers.append( MainTable )
                HTForm_showAllMarkers.append(HTInput_FormId)
		HTForm_showAllMarkers.append(HTInput_Status)
                HTForm_showAllMarkers.append(HTInput_InbredSetName)
		HTForm_showAllMarkers.append(HTInput_Chr)
		HTForm_showAllMarkers.append(HTInput_MbStart)
		HTForm_showAllMarkers.append(HTInput_MbEnd)
		HTForm_showAllMarkers.append(HTInput_MarkerNamesExisted)
		HTForm_showAllMarkers.append(HTInput_MarkerNamesAdded)

		return HTForm_showAllMarkers



	def showOneMarker (self, InbredSetName="", MarkerName="", suffix="", MarkerGroupInfo=[], StrainList=[], marker_type=''):

		GenoInfo={}

		#XZ: The first item of MarkerInfo is Geno.Id
		GenoId = MarkerGroupInfo[0]

		for i in range(1, len(MarkerGroupInfo)):
			if MarkerGroupInfo[i] != None:
				GenoInfo[ MarkerInfoField[i-1] ] = str(MarkerGroupInfo[i])
			else:
				GenoInfo[ MarkerInfoField[i-1] ] = ''
		
		if GenoInfo['Used_for_mapping'] == 'Y':
			GenoInfo['Used_for_mapping'] = True
		else:
			GenoInfo['Used_for_mapping'] = False


		MarkerRow = HT.TR()

		# Species level info
		for i in range(0, len(MarkerSpeciesInfoField)):
			if MarkerSpeciesInfoField[i] == 'Name':
				if marker_type == 'existed':
					MarkerRow.append( HT.TD(GenoInfo['Name']) )
				else:
					MarkerRow.append(HT.TD(HT.Input(name = MarkerName + suffix + markerName_Feild_Separator + MarkerSpeciesInfoField[i], size=20, maxlength=500, value=MarkerName + suffix  )))
			else:
				MarkerRow.append(HT.TD(HT.Input(name = MarkerName + suffix + markerName_Feild_Separator + MarkerSpeciesInfoField[i], size=10, maxlength=500, value=GenoInfo[MarkerSpeciesInfoField[i]])))

		# Group level info
		for i in range(0, len(MarkerGroupInfoField)):
                        if MarkerGroupInfoField[i] != 'Used_for_mapping':
                                MarkerRow.append( HT.TD(HT.Input(name = MarkerName + suffix + markerName_Feild_Separator + MarkerGroupInfoField[i], size=10, value=GenoInfo[MarkerGroupInfoField[i]])))
                        else:
				MarkerRow.append( HT.TD(HT.Input(type='checkbox', name= MarkerName + suffix + markerName_Feild_Separator + 'Used_for_mapping', checked=GenoInfo['Used_for_mapping']  )))

                # retrive Marker allele values
                GenoFreezeId = retrieveGenoFreezeId(self.cursor, InbredSetName)
                Alleles = retrieveAllele (self.cursor, GenoFreezeId, GenoId)

		for i in range(0, len(StrainList)):
			try:
				Value = Alleles[StrainList[i]]
			except:
				Value = 'X' # 'X' is the symbol for unknown allele
			MarkerRow.append( HT.TD(HT.Input(name = MarkerName + suffix + markerName_Feild_Separator + StrainList[i], size=3, maxlength=5, value=Value)))


		return MarkerRow


	def editMarkerTable (self, fd):

		InbredSetName = fd.formdata.getvalue('InbredSetName')
                Chr = fd.formdata.getvalue('Chr')

		MbStart = fd.formdata.getvalue('MbStart')
		MbEnd = fd.formdata.getvalue('MbEnd')

		MarkerNamesExistedString = fd.formdata.getvalue('MarkerNamesExisted')
		MarkerNamesAddedString = fd.formdata.getvalue('MarkerNamesAdded')

		MarkerNamesExisted = []
		MarkerNamesAdded = []

		MarkerNamesExistedString = MarkerNamesExistedString.strip()
		MarkerNamesExisted = MarkerNamesExistedString.split(',')

		MarkerNamesAddedString = MarkerNamesAddedString.strip()
		if MarkerNamesAddedString:
			MarkerNamesAdded = MarkerNamesAddedString.split(',')

		GroupNeedExport = []
		# To simplify the business logic, just add this group to the list anyway
		GroupNeedExport.append(InbredSetName)


		for one_marker in MarkerNamesExisted:
			if self.checkMarkerHasBeenInGroup(InbredSetName=InbredSetName, MarkerName=one_marker, fd=fd):
				GroupNeedExport = self.changeMarker( InbredSetName=InbredSetName, MarkerWebID=one_marker, MarkerName=one_marker, GroupNeedExport=GroupNeedExport, fd=fd)

		if MarkerNamesAdded:
			for one_marker in MarkerNamesAdded:
				input_name = fd.formdata.getvalue( one_marker + markerName_Feild_Separator + 'Name' )
				GroupNeedExport = self.changeMarker( InbredSetName=InbredSetName, MarkerWebID=one_marker, MarkerName=input_name, GroupNeedExport=GroupNeedExport, fd=fd)

		export_info = self.exportAllGenoFiles( GroupNeedExport )

		contents = []

		contents.append(export_info)

		HTInput_FormId = HT.Input(type='hidden', name='FormID', value='updGeno')
		HTInput_Back = HT.Input(type="submit", name="backButton", value="Back to main page", Class="button")
		HTForm_Back = HT.Form(name='StrainForm', cgi=os.path.join(webqtlConfig.CGIDIR, 'main.py'), \
					enctype= 'multipart/form-data', submit=HTInput_Back)
		HTForm_Back.append(HTInput_FormId)

		contents.append(str(HTForm_Back))

		return '<BR>'.join(contents)

		# return "%s" % export_info



	def checkMarkerHasBeenInGroup(self, InbredSetName="", MarkerName="", fd=None):

		isChanged = False

		# retrive Marker information from database
		MarkerGroupInfo = retrieveMarkerInfoForGroup (self.cursor, MarkerName, InbredSetName)

		GenoId = MarkerGroupInfo[0]

		GenoInfo={}

		for i in range(1, len(MarkerGroupInfo)):
				if MarkerGroupInfo[i] != None:
					GenoInfo[MarkerInfoField[i-1]] = str( MarkerGroupInfo[i] )
				else:
					GenoInfo[MarkerInfoField[i-1]] = ''

		if GenoInfo['Used_for_mapping'] == 'Y':
			GenoInfo['Used_for_mapping'] = True
		else:
			GenoInfo['Used_for_mapping'] = False

		
		# check the changing of Geno information

		for i in range(0, len(MarkerInfoField)):

			if MarkerInfoField[i] == 'Name':
				continue

			webInputValue = fd.formdata.getvalue( MarkerName + markerName_Feild_Separator + MarkerInfoField[i] )


			if MarkerInfoField[i] == 'Used_for_mapping':
				if webInputValue == 'on':
					webInputValue = True
				else:
					webInputValue = False


			if GenoInfo[MarkerInfoField[i]] != webInputValue:
				isChanged = True

		# retrive Marker alleles
		GenoFreezeId = retrieveGenoFreezeId(self.cursor, InbredSetName)
		db_alleles = retrieveAllele (self.cursor, GenoFreezeId, GenoId)
		StrainList = retrieveStrainUsedForMapping (self.cursor, InbredSetName)


		# check the changing of allele values

		for i in range(0, len(StrainList)):
			webInputValue = fd.formdata.getvalue(MarkerName + markerName_Feild_Separator + StrainList[i])

			if not db_alleles.has_key(StrainList[i]):
				#XZ: This is hard coded.
				#XZ: The best way is to check if the input value is in ('B', 'D', 'H').
				if webInputValue.upper() != 'X': # 'X' is the symbol for unknown allele.
					isChanged = True
			else:
				if str( db_alleles[StrainList[i]]) != webInputValue:
					isChanged = True


		return isChanged


	def changeMarker(self,InbredSetName="", MarkerWebID="", MarkerName="", GroupNeedExport=[], fd=None):

		GenoFreezeId = retrieveGenoFreezeId( self.cursor, InbredSetName )

		MarkerGroupInfo = retrieveMarkerInfoForGroup(self.cursor, MarkerName, InbredSetName)

		# This marker has record for this group.
		# Need to keep the original GeneId and marker name.
		if MarkerGroupInfo:

			#XZ: The first item of MarkerInfo is Geno.Id
			GenoId = MarkerGroupInfo[0]

			#This function should be excuted before update Chr and Mb in database.
			GroupNeedExport = getAllGroupsNeedExported(self.cursor, GroupNeedExport=GroupNeedExport, GenoId=GenoId, \
									Chr=fd.formdata.getvalue(MarkerWebID + markerName_Feild_Separator + 'Chr'), \
									Mb=fd.formdata.getvalue(MarkerWebID + markerName_Feild_Separator + 'Mb') )

			# Update the info in Geno (Chr, Mb, Sequence, Source).
			updateGeno(self.cursor, GenoId, InbredSetName, MarkerWebID, fd)

			# Update GenoXRef (cM, Used_for_mapping)
			updateGenoXRef(self.cursor, GenoFreezeId, GenoId, MarkerWebID, fd)

			# Keep the original GenoXRef.DataId value.
			DataId = retrieveDataId(self.cursor, GenoId, InbredSetName)

			# Delete the original alleles
			cmd = "delete from GenoData where Id=%s" % DataId
			self.cursor.execute(cmd)

			# Insert new alleles.
			insertGenoData(cursor=self.cursor, InbredSetName=InbredSetName, DataId=DataId, MarkerWebID=MarkerWebID, fd=fd)

		else: # No record for this group.

			hasInfoForSpecies = checkIfMarkerInSpecies(self.cursor, MarkerName, InbredSetName)

			if hasInfoForSpecies:

				# Keep the original GenoId.
				GenoId = hasInfoForSpecies[0]

				#This function should be excuted before update Chr and Mb in database.
				GroupNeedExport = getAllGroupsNeedExported(self.cursor, GroupNeedExport=GroupNeedExport, GenoId=GenoId, \
										Chr=fd.formdata.getvalue( MarkerWebID + markerName_Feild_Separator + 'Chr' ), \
										Mb=fd.formdata.getvalue( MarkerWebID + markerName_Feild_Separator + 'Mb') )


				# Update the info in Geno (Chr, Mb, Sequence, Source).
                                updateGeno(self.cursor, GenoId, InbredSetName, MarkerWebID, fd)


				# Get new GenoData.Id
				DataId = retrieveMaxGenoDataId(self.cursor) + 1

				# Add record in GenoXRef table for this group.
				addGenoXRef(self.cursor, GenoFreezeId, GenoId, DataId, MarkerWebID, fd)

				# Add record in GenoData table.
				insertGenoData(cursor=self.cursor, InbredSetName=InbredSetName, DataId=DataId, MarkerWebID=MarkerWebID, fd=fd)

			else:
				# Get new Geno.Id
				GenoId = retrieveMaxGenoId(cursor=self.cursor) + 1

				# Add record in Geno
				addGeno(self.cursor, GenoId, InbredSetName, MarkerWebID, fd)

				# Get new GenoData.Id
				DataId = retrieveMaxGenoDataId(self.cursor) + 1

				# Add record into GenoXRef table.
				addGenoXRef(self.cursor, GenoFreezeId, GenoId, DataId, MarkerWebID, fd)

				#Add record into GenoData table.
				insertGenoData(cursor=self.cursor, InbredSetName=InbredSetName, DataId=DataId, MarkerWebID=MarkerWebID, fd=fd)

		return GroupNeedExport



	def exportAllGenoFiles (self, InbredSetNameList = []):

		warning = "As to the change made, the following groups need to be exported to generate new geno files: %s\n<br><br> " % str(InbredSetNameList)

		whiteList = ['BXD']

		warning = warning + "At current development stage, the following groups can be exported to generate geno files: %s\n<br><br>" % str(whiteList)
		warning = warning + "Here are the geno files that are ACTUALLY exported according to the change you made:\n<br>"

		blackList = []
		for one_group in InbredSetNameList:
			if one_group in whiteList:
				self.exportOneGenoFile( one_group )
				warning = warning + "<a href='/genotypes/%s.geno" % one_group + "'>" + one_group + " geno file</a>\n<br>"
			else:
				blackList.append(one_group)

		return warning



	def exportOneGenoFile (self, InbredSetName=''):

		geno_file = open(webqtlConfig.GENODIR + InbredSetName + '.geno', 'w')

		query = "select SpeciesId from InbredSet where Name='%s' " % InbredSetName
		self.cursor.execute( query )
		SpeciesId = self.cursor.fetchone()[0]

		GenoFreezeId = retrieveGenoFreezeId( self.cursor, InbredSetName )

		StrainUsedForMapping = retrieveStrainUsedForMapping(self.cursor, InbredSetName )

		StrainNameIdUsedForMapping = retrieveStrainNameIdUsedForMapping( self.cursor, InbredSetName )

		GenoCode_record = retrieveGenoCode(self.cursor, InbredSetName )

		Allle_value_symbol = {}
		symbol_for_unknown = ''

		for one_result in GenoCode_record:
			if str(one_result[2]) != 'None':
				Allle_value_symbol[one_result[2]] = one_result[1]
			else:
				symbol_for_unknown = one_result[1]


		geno_file.write('@name:%s\n' % InbredSetName )

		GeneticType = retrieveGeneticTypeOfInbredSet(self.cursor, InbredSetName )

                geno_file.write('@type:%s\n' % str(GeneticType) )

		for one_result in GenoCode_record:
			geno_file.write('@%s:%s\n' % (one_result[0], one_result[1]) )

		geno_file.write('Chr\tLocus\tcM\tMb')	

		for one_strain in StrainUsedForMapping:
			geno_file.write('\t%s' % one_strain )

		
		query = "select Geno.Chr, Geno.Name, GenoXRef.cM, Geno.Mb, GenoXRef.DataId from Geno, GenoXRef where SpeciesId=%s and GenoFreezeId=%s and Used_for_mapping='Y' and Geno.Id=GenoId order by chr_num, Mb" % (SpeciesId, GenoFreezeId)
		self.cursor.execute( query )
		results = self.cursor.fetchall()

		StrainId_Allele = {}

		for one_result in results:
			Chr, Name, cM, Mb, DataId = one_result
			geno_file.write('\n%s\t%s\t%s\t%s' % (Chr, Name, cM, Mb) )

			StrainId_Allele = {}

			query = "select StrainId, value from GenoData where Id=%s " % DataId
			self.cursor.execute( query )
			GenoData_results = self.cursor.fetchall()

			for one_GenoData_result in GenoData_results:
				StrainId_Allele[ one_GenoData_result[0] ] = one_GenoData_result[1]

			for one_strain_name in StrainUsedForMapping:
				one_strain_id = StrainNameIdUsedForMapping[ one_strain_name ]

				if StrainId_Allele.has_key( one_strain_id ):
					one_allele_value = StrainId_Allele[one_strain_id]
					one_allele_symbol = Allle_value_symbol[ one_allele_value ]
					geno_file.write( '\t%s' % one_allele_symbol )
				else:
					geno_file.write( '\t%s' % symbol_for_unknown  )




	






