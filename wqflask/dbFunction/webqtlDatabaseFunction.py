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


import MySQLdb
import string
from base import webqtlConfig

###########################################################################
#output: cursor instance
#function: connect to database and return cursor instance
###########################################################################
def getCursor():
    try:
        con = MySQLdb.Connect(db=webqtlConfig.DB_NAME, host=webqtlConfig.MYSQL_SERVER, user=webqtlConfig.DB_USER, passwd=webqtlConfig.DB_PASSWD)
        cursor = con.cursor()
        return cursor
    except:
        return None



###########################################################################
#input: cursor, groupName (string)
#output: mappingMethodId (int) info, value will be Null or else
#function: retrieve mappingMethodId info from InbredSet table
###########################################################################

def getMappingMethod(cursor=None, groupName=None):
    cursor.execute("select MappingMethodId from InbredSet where Name= '%s'" % groupName)
    mappingMethodId = cursor.fetchone()[0]
    return mappingMethodId

###########################################################################
#input: cursor, inbredSetId (int), strainId (int)
#output: isMappingId (bull) info, value will be 0,1,2 or else, 0 or Null means
# "can not do mapping", >0 means "can do mapping", >1 means "there exsists
# redundant data, user needs to choose one to do mapping function"
#function: retrieve isMappingId info from StrainXRef table
###########################################################################

def isMapping(cursor=None, inbredSetId=None, strainId=None):
    cursor.execute("select IsMapping from StrainXRef where InbredSetId='%d' and StrainId = '%d'" %(inbredSetId, strainId))
    isMappingId = cursor.fetchone()[0]
    return isMappingId

###########################################################################
#input: cursor, groupName (string)
#output: all species data info (array), value will be Null or else
#function: retrieve all species info from Species table
###########################################################################

def getAllSpecies(cursor=None):
    cursor.execute("select Id, Name, MenuName, FullName, TaxonomyId,OrderId from Species Order by OrderId")
    allSpecies = cursor.fetchall()
    return allSpecies

###########################################################################
#input: cursor, RISet (string)
#output: specie's name (string), value will be None or else
#function: retrieve specie's name info based on RISet
###########################################################################

def retrieveSpecies(cursor=None, group=None):
    try:
        cursor.execute("select Species.Name from Species, InbredSet where InbredSet.Name = '%s' and InbredSet.SpeciesId = Species.Id" % group)
        return cursor.fetchone()[0]
    except:
        return None

###########################################################################
#input: cursor, RISet (string)
#output: specie's Id (string), value will be None or else
#function: retrieve specie's Id info based on RISet
###########################################################################

def retrieveSpeciesId(cursor=None, RISet=None):
    try:
        cursor.execute("select SpeciesId from InbredSet where Name = '%s'" % RISet)
        return cursor.fetchone()[0]
    except:
        return None

###########################################################################
# input: cursor
# output: tissProbeSetFreezeIdList (list),
#         nameList (list),
#         fullNameList (list)
# function: retrieve all TissueProbeSetFreezeId,Name,FullName info
#           from TissueProbeSetFreeze table.
#           These data will listed in the dropdown menu in the first page of Tissue Correlation
###########################################################################

def getTissueDataSet(cursor=None):
    tissProbeSetFreezeIdList=[]
    nameList =[]
    fullNameList = []

    query = "select Id,Name,FullName from TissueProbeSetFreeze; "
    try:
        cursor.execute(query)
        result = cursor.fetchall()

        for row in result:
            tissProbeSetFreezeIdList.append(row[0])
            nameList.append(row[1])
            fullNameList.append(row[2])
    except:
        return None

    return tissProbeSetFreezeIdList,nameList,fullNameList

###########################################################################
# input: cursor,GeneSymbol (string), and TissueProbeSetFreezeId (string)
# output: geneId (string), dataId (string)
# function: retrieve geneId and DataId from TissueProbeSetXRef table
###########################################################################

def getGeneIdDataIdForTissueBySymbol(cursor=None, GeneSymbol=None, TissueProbeSetFreezeId= 0):
    query ="select GeneId, DataId from TissueProbeSetXRef where Symbol = '%s' and TissueProbeSetFreezeId=%s order by Mean desc" %(GeneSymbol,TissueProbeSetFreezeId)
    try:
        cursor.execute(query)
        result = cursor.fetchone()
        geneId = result[0]
        dataId = result[1]
    except:
        geneId = 0
        dataId = 0

    return geneId,dataId

###########################################################################
# input: cursor, TissueProbeSetFreezeId (int)
# output: chipId (int)
# function: retrieve chipId from TissueProbeFreeze table
###########################################################################

def getChipIdByTissueProbeSetFreezeId(cursor=None, TissueProbeSetFreezeId=None):
    query = "select TissueProbeFreezeId from TissueProbeSetFreeze where Id =%s" % TissueProbeSetFreezeId
    try:
        cursor.execute(query)
        result = cursor.fetchone()
        TissueProbeFreezeId = result[0]
    except:
        TissueProbeFreezeId =0

    query1 = "select ChipId from TissueProbeFreeze where Id =%s" % TissueProbeFreezeId
    try:
        cursor.execute(query1)
        result1 = cursor.fetchone()
        chipId = result1[0]
    except:
        chipId =0

    return chipId

###########################################################################
# input: cursor, TissueProbeSetFreezeId (int)
# output: TissueCount (int)
# function: retrieve how many tissue used in the specific dataset based on TissueProbeSetFreezeId
###########################################################################
def getTissueCountByTissueProbeSetFreezeId(cursor=None, TissueProbeSetFreezeId=None):
    query1 ="select DataId from TissueProbeSetXRef where TissueProbeSetFreezeId =%s limit 1" % TissueProbeSetFreezeId
    try:
        cursor.execute(query1)
        result1 = cursor.fetchone()
        DataId = result1[0]

        query2 =" select count(*) from TissueProbeSetData where Id=%s" % DataId
        try:
            cursor.execute(query2)
            result2 = cursor.fetchone()
            TissueCount = result2[0]
        except:
            TissueCount =0
    except:
        TissueCount =0

    return TissueCount

###########################################################################
# input: cursor, TissueProbeSetFreezeId (int)
# output: DataSetName(string),DataSetFullName(string)
# function: retrieve DataSetName, DataSetFullName based on TissueProbeSetFreezeId
###########################################################################
def getDataSetNamesByTissueProbeSetFreezeId(cursor=None, TissueProbeSetFreezeId=None):
    query ="select Name, FullName from TissueProbeSetFreeze where Id=%s" % TissueProbeSetFreezeId
    try:
        cursor.execute(query)
        result = cursor.fetchone()
        DataSetName = result[0]
        DataSetFullName =result[1]
    except:
        DataSetName =None
        DataSetFullName =None

    return DataSetName, DataSetFullName

###########################################################################
# input: cursor, geneIdLst (list)
# output: geneIdSymbolPair(dict),key is geneId, value is geneSymbol
# function: retrieve GeneId, GeneSymbol based on geneId List
###########################################################################
def getGeneIdSymbolPairByGeneId(cursor=None, geneIdLst =None):
    geneIdSymbolPair={}
    for geneId in geneIdLst:
        geneIdSymbolPair[geneId]=None

    query ="select GeneId,GeneSymbol from GeneList where GeneId in (%s)" % string.join(geneIdLst, ", ")
    try:
        cursor.execute(query)
        results = cursor.fetchall()
        for item in results:
            geneId =item[0]
            geneSymbol =item[1]
            geneIdSymbolPair[geneId]=geneSymbol
    except:
        geneIdSymbolPair=None

    return geneIdSymbolPair


def updateTissueProbesetXRefByProbesetId(cursor=None, probesetId=None):
    query ="select Symbol,GeneId,Chr,Mb,description, Probe_Target_Description from ProbeSet where Id =%s"%probesetId
    try:
        cursor.execute(query)
        result =cursor.fetchone()

        updateQuery ='''
                        Update TissueProbeSetXRef
                        Set Symbol='%s',GeneId='%s', Chr='%s', Mb='%s', description ='%s',Probe_Target_Description='%s'
                        where ProbesetId=%s
                        '''%(result[0],result[1],result[2],result[3],result[4],result[5],probesetId)

        cursor.execute(updateQuery)

    except:
        return None
