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
# This module is used by GeneNetwork project (www.genenetwork.org)
#
# Created by GeneNetwork Core Team 2010/11/10
#
# Last updated by Ning Liu, 2011/01/26


#tissueCorrelationMatrix: funciton part for TissueCorrelationPage.py
from htmlgen import HTMLgen2 as HT
from correlation import correlationFunction
from dbFunction import webqtlDatabaseFunction
import sys

#########################################
#      Tissue Correlation Page
#########################################

class  tissueCorrelationMatrix:
	def __init__(self,tissueProbeSetFreezeId=None):
		
		#initialize parameters
		self.tProbeSetFreezeId = tissueProbeSetFreezeId
		self.cursor = webqtlDatabaseFunction.getCursor()



	#retreive dataSet info from database table TissueProbeSetFreeze to get all TissueProbeSetFreezeId(List), Name(List) and FullName(List)
	def getTissueDataSet(self):	
		tissProbeSetFreezeIds,Names,fullNames = webqtlDatabaseFunction.getTissueDataSet(cursor=self.cursor)
		return tissProbeSetFreezeIds,Names,fullNames


	#retrieve DatasetName, DatasetFullName based on TissueProbeSetFreezeId, return DatasetName(string), DatasetFullName(string)
	def getFullnameofCurrentDataset(self):
	
		DatasetName, DatasetFullName =webqtlDatabaseFunction.getDatasetNamesByTissueProbeSetFreezeId(cursor=self.cursor, TissueProbeSetFreezeId=self.tProbeSetFreezeId)		
		return DatasetName, DatasetFullName

				
	#retrieve how many tissue used in the specific dataset based on TissueProbeSetFreezeId, return TissueCount(int)
	def getTissueCountofCurrentDataset(self):
	
		TissueCount =webqtlDatabaseFunction.getTissueCountByTissueProbeSetFreezeId(cursor=self.cursor,TissueProbeSetFreezeId=self.tProbeSetFreezeId)
		return TissueCount


		
	#retrieve corrArray(array), pvArray(array) for display by calling  calculation function:calZeroOrderCorrForTiss
	def getTissueCorrPvArray(self,geneNameLst=None,dataIdDict=None):	
		#retrieve SymbolValuePairDict(Dict), dictionary of Symbol and Value Pair.key is symbol, value is one list of expression values of one probeSet
		symbolValuepairDict =correlationFunction.getGeneSymbolTissueValueDict(cursor=self.cursor,symbolList=geneNameLst,dataIdDict=dataIdDict)
		corrArray,pvArray = correlationFunction.getCorrPvArray(cursor=self.cursor,priGeneSymbolList=geneNameLst,symbolValuepairDict=symbolValuepairDict)
		return corrArray,pvArray


		
	#retrieve symbolList,geneIdList,dataIdList,ChrList,MbList,descList,pTargetDescList (all are list type) to 
	#get multi lists for short and long label functions, and for getSymbolValuePairDict and 
	#getGeneSymbolTissueValueDict to build dict to get CorrPvArray
	def getTissueProbeSetXRefInfo(self,GeneNameLst=[]):
		symbolList,geneIdDict,dataIdDict,ChrDict,MbDict,descDict,pTargetDescDict =correlationFunction.getTissueProbeSetXRefInfo(cursor=self.cursor,GeneNameLst=GeneNameLst,TissueProbeSetFreezeId=self.tProbeSetFreezeId)
		return symbolList,geneIdDict,dataIdDict,ChrDict,MbDict,descDict,pTargetDescDict		



	#retrieve corrArray(array), pvArray(array) for gene symbol pair
	def getCorrPvArrayForGeneSymbolPair(self,geneNameLst=None):
		corrArray = None
		pvArray = None

		if len(geneNameLst) == 2:
			#retrieve SymbolValuePairDict(Dict), dictionary of Symbol and Value Pair.key is symbol, value is one list of expression values of one probeSet
			symbolList,geneIdDict,dataIdDict,ChrDict,MbDict,descDict,pTargetDescDict =correlationFunction.getTissueProbeSetXRefInfo(cursor=self.cursor,GeneNameLst=geneNameLst,TissueProbeSetFreezeId=self.tProbeSetFreezeId)	
			symbolValuepairDict =correlationFunction.getGeneSymbolTissueValueDict(cursor=self.cursor,symbolList=geneNameLst,dataIdDict=dataIdDict)
			corrArray,pvArray = correlationFunction.getCorrPvArray(cursor=self.cursor,priGeneSymbolList=geneNameLst,symbolValuepairDict=symbolValuepairDict)

		return corrArray,pvArray


	#retrieve symbolCorrDict(dict), symbolPvalueDict(dict) to get all tissues' correlation value and P value; key is symbol	
	def calculateCorrOfAllTissueTrait(self, primaryTraitSymbol=None, method='0'):
		symbolCorrDict, symbolPvalueDict = correlationFunction.calculateCorrOfAllTissueTrait(cursor=self.cursor, primaryTraitSymbol=primaryTraitSymbol, TissueProbeSetFreezeId=self.tProbeSetFreezeId,method=method)
		
		return symbolCorrDict, symbolPvalueDict

	#Translate GeneId to gene symbol and keep the original order.
	def getGeneSymbolLst(self, geneSymbols=None):
		geneSymbolLst=[]
		geneIdLst=[]
		#split the input string at every occurrence of the delimiter '\r', and return the substrings in an array. 
		tokens=geneSymbols.strip().split('\r')

		#Ning: To keep the original order of input symbols and GeneIds
		for i in tokens:
			i=i.strip()
			if (len(i) >0) and (i not in geneSymbolLst):
				geneSymbolLst.append(i)
				# if input includes geneId(s), then put it/them into geneIdLst
				if i.isdigit():
					geneIdLst.append(i)

		#Ning: Replace GeneId with symbol if applicable
		if len(geneIdLst)>0:
			# if input includes geneId(s), replace geneId by geneSymbol; 
			geneIdSymbolPair =webqtlDatabaseFunction.getGeneIdSymbolPairByGeneId(cursor=self.cursor, geneIdLst =geneIdLst)
			for geneId in geneIdLst:
				if geneIdSymbolPair[geneId]:
					index = geneSymbolLst.index(geneId)
					geneSymbolLst[index] =geneIdSymbolPair[geneId]

		return geneSymbolLst
			
		

