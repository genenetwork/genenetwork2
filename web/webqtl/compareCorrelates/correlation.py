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

# correlation.py
# functions for computing correlations for traits
#
# Originally, this code was designed to compute Pearson product-moment
# coefficents. The basic function calcPearson scans the strain data
# for the two traits and drops data for a strain unless both traits have it.
# If there are less than six strains left, we conclude that there's
# insufficent data and drop the correlation.
#
# In addition, this code can compute Spearman rank-order coefficents using
# the calcSpearman function.

#Xiaodong changed the dependancy structure
import numarray
import numarray.ma as MA
import time

import trait

# strainDataUnion : StrainData -> StrainData -> array, array
def strainDataUnion(s1, s2):
    # build lists of values that both have
    # and make sure that both sets of values are in the same order
    s1p = []
    s2p = []
    sortedKeys = s1.keys()
    sortedKeys.sort()
    for s in sortedKeys:
        if s2.has_key(s):
            s1p.append(s1[s])
            s2p.append(s2[s])

    return (numarray.array(s1p, numarray.Float64),
            numarray.array(s2p, numarray.Float64))

# calcCorrelationHelper : array -> array -> float
def calcCorrelationHelper(s1p, s2p):
    # if the traits share less than six strains, then we don't
    # bother with the correlations
    if len(s1p) < 6:
        return 0.0
    
    # subtract by x-bar and y-bar elementwise
    #oldS1P = s1p.copy()
    #oldS2P = s2p.copy()
    
    s1p = (s1p - numarray.average(s1p)).astype(numarray.Float64)
    s2p = (s2p - numarray.average(s2p)).astype(numarray.Float64)

    # square for the variances 
    s1p_2 = numarray.sum(s1p**2)
    s2p_2 = numarray.sum(s2p**2)

    try: 
        corr = (numarray.sum(s1p*s2p)/
                numarray.sqrt(s1p_2 * s2p_2))
    except ZeroDivisionError:
        corr = 0.0

    return corr
    
# calcSpearman : Trait -> Trait -> float
def calcSpearman(trait1, trait2):
    s1p, s2p = strainDataUnion(trait1.strainData,
                               trait2.strainData)
    s1p = rankArray(s1p)
    s2p = rankArray(s2p)
    return calcCorrelationHelper(s1p, s2p)

# calcPearson : Trait -> Trait -> float
def calcPearson(trait1, trait2):
    # build lists of values that both have
    # and make sure that both sets of values are in the same order
    s1p, s2p = strainDataUnion(trait1.strainData,
                               trait2.strainData)

    return calcCorrelationHelper(s1p, s2p)

# buildPearsonCorrelationMatrix: (listof n traits) -> int s -> n x s matrix, n x s matrix
#def buildPearsonCorrelationMatrix(traits, sc):
#    dim = (len(traits), sc)
#    matrix = numarray.zeros(dim, MA.Float64)
#    testMatrix = numarray.zeros(dim, MA.Float64)

#    for i in range(len(traits)):
#        sd = traits[i].strainData
#        for key in sd.keys():
#            matrix[i,int(key) - 1] = sd[key]
#            testMatrix[i,int(key) - 1] = 1

def buildPearsonCorrelationMatrix(traits, commonStrains):
    dim = (len(traits), len(commonStrains))
    matrix = numarray.zeros(dim, MA.Float64)
    testMatrix = numarray.zeros(dim, MA.Float64)

    for i in range(len(traits)):
        sd = traits[i].strainData
        keys = sd.keys()
        for j in range(0, len(commonStrains)):
            if keys.__contains__(commonStrains[j]):
                matrix[i,j] = sd[commonStrains[j]]
                testMatrix[i,j] = 1

    return matrix, testMatrix

# buildSpearmanCorrelationMatrix: (listof n traits) -> int s -> n x s matrix, n x s matrix
def buildSpearmanCorrelationMatrix(traits, sc):
    dim = (len(traits), sc)
    matrix = numarray.zeros(dim, MA.Float64)
    testMatrix = numarray.zeros(dim, MA.Float64)

    def customCmp(a, b):
        return cmp(a[1], b[1])
    
    for i in range(len(traits)):
        # copy strain data to a temporary list and turn it into
        # (strain, expression) pairs
        sd = traits[i].strainData
        tempList = []
        for key in sd.keys():
            tempList.append((key, sd[key]))

        # sort the temporary list by expression
        tempList.sort(customCmp)
        
        for j in range(len(tempList)):
            # k is the strain id minus 1
            # 1-based strain id -> 0-based column index
            k = int(tempList[j][0]) - 1

            # j is the rank of the particular strain
            matrix[i,k] = j

            testMatrix[i,k] = 1

    return matrix, testMatrix
            
def findLargestStrain(traits, sc):
    strainMaxes = []
    for i in range(len(traits)):
        keys = traits[i].strainData.keys()
        strainMaxes.append(max(keys))

    return max(strainMaxes)

def findCommonStrains(traits1, traits2):
    commonStrains = []
    strains1 = []
    strains2 = []

    for trait in traits1:
        keys = trait.strainData.keys()
        for key in keys:
            if not strains1.__contains__(key):
                strains1.append(key)

    for trait in traits2:
        keys = trait.strainData.keys()
        for key in keys:
            if not strains2.__contains__(key):
                strains2.append(key)
 
    for strain in strains1:
        if strains2.__contains__(strain):
           commonStrains.append(strain)

    return commonStrains

def calcPearsonMatrix(traits1, traits2, sc, strainThreshold=6,
                      verbose = 0):
    return calcMatrixHelper(buildPearsonCorrelationMatrix,
                            traits1, traits2, sc, strainThreshold,
                            verbose)

def calcProbeSetPearsonMatrix(cursor, freezeId, traits2, strainThreshold=6,
                      verbose = 0):

    cursor.execute('select ProbeSetId from ProbeSetXRef where ProbeSetFreezeId = %s order by ProbeSetId' % freezeId)
    ProbeSetIds = cursor.fetchall()

    results = []
    i=0
    while i<len(ProbeSetIds):
        ProbeSetId1 = ProbeSetIds[i][0]
        if (i+4999) < len(ProbeSetIds):
            ProbeSetId2 = ProbeSetIds[i+4999][0]
        else:
            ProbeSetId2 = ProbeSetIds[len(ProbeSetIds)-1][0]

        traits1 = trait.queryPopulatedProbeSetTraits2(cursor, freezeId, ProbeSetId1, ProbeSetId2) # XZ,09/10/2008: add module name 'trait.'
        SubMatrix = calcMatrixHelper(buildPearsonCorrelationMatrix,
                                     traits1, traits2, 1000, strainThreshold,
                                     verbose)
        results.append(SubMatrix)
        i += 5000

    returnValue = numarray.zeros((len(ProbeSetIds), len(traits2)), MA.Float64)
    row = 0
    col = 0
    for SubMatrix in results:
        for i in range(0, len(SubMatrix)):
            for j in range(0, len(traits2)):
                returnValue[row,col] = SubMatrix[i,j]
                col += 1
            col = 0
            row +=1

    return returnValue

    

# note: this code DOES NOT WORK, especially in cases where
# there are missing observations (e.g. when comparing traits
# from different probesetfreezes)
def calcSpearmanMatrix(traits1, traits2, sc, strainThreshold=6,
                       verbose=0):
    return calcMatrixHelper(buildSpearmanCorrelationMatrix,
                            traits1, traits2, sc, strainThreshold,
                            verbose)
    
def calcMatrixHelper(builder, traits1, traits2, sc, strainThreshold,
                     verbose):

    # intelligently figure out strain count
    step0 = time.time()
    #localSC = max(findLargestStrain(traits1, sc),
    #              findLargestStrain(traits2, sc))

    commonStrains = findCommonStrains(traits1, traits2)

    buildStart = time.time()
    matrix1, test1 = builder(traits1, commonStrains)
    matrix2, test2 = builder(traits2, commonStrains)
    buildTime = time.time() - buildStart

    step1 = time.time()

    ns = numarray.innerproduct(test1, test2)

    # mask all ns less than strainThreshold so the correlation values
    # end up masked
    # ns is now a MaskedArray and so all ops involving ns will be
    # MaskedArrays
    ns = MA.masked_less(ns, strainThreshold, copy=0)
        
    # divide-by-zero errors are automatically masked
    #ns = -1.0/ns

    step2 = time.time()
    
    # see comment above to find out where this ridiculously cool
    # matrix algebra comes from
    xs = numarray.innerproduct(matrix1, test2)
    ys = numarray.innerproduct(test1, matrix2)
    xys = numarray.innerproduct(matrix1, matrix2)

    # use in-place operations to try to speed things up
    numarray.power(matrix1, 2, matrix1)
    numarray.power(matrix2, 2, matrix2)

    x2s = numarray.innerproduct(matrix1, test2)
    y2s = numarray.innerproduct(test1, matrix2)

    step3 = time.time()

    # parens below are very important
    # the instant we touch ns, arrays become masked and
    # computation is much, much slower
    top = ns*xys - (xs*ys)
    bottom1 = ns*x2s - (xs*xs)
    bottom2 = ns*y2s - (ys*ys)
    bottom = MA.sqrt(bottom1*bottom2)

    # mask catches floating point divide-by-zero problems here
    corrs = top / bottom

    step4 = time.time()

    # we define undefined correlations as zero even though there
    # is a mathematical distinction
    returnValue = MA.filled(corrs, 0.0)

    step5 = time.time()
    
    #print ("calcMatrixHelper: %.2f s, %.2f s, %.2f s, %.2f s, %.2f s, %.2f s, total: %.2f s"
    #       %(buildTime,
    #         buildStart - step0,
    #         step2 - step1,
    #         step3 - step2,
    #         step4 - step3,
    #         step5 - step4,
    #         step5 - step0))

    if verbose:
        print "Matrix 1:", matrix1
        print "Matrix 2:", matrix2
        print "Ns:", ns
        print "Xs", xs
        print "Ys", ys
        print "XYs:", xys
        print "Top:", top
        print "Bottom 1:", bottom1
        print "Bottom 2:", bottom2
        print "Bottom:", bottom
        print "Corrs:", corrsa

        
    return returnValue
    
    

# rankArray: listof float -> listof float
# to generate a companion list to alof with
# the actual value of each element replaced by the
# value's rank
def rankArray(floatArray):
    # first we save the original index of each element
    tmpAlof = []
    returnArray = numarray.zeros(len(floatArray), numarray.Float64)
    i = 0
    for i in range(len(floatArray)):
        tmpAlof.append((i,floatArray[i]))

    # now we sort by the data value
    def customCmp(a,b): return cmp(a[1],b[1])
    tmpAlof.sort(customCmp)

    # finally we use the new rank data to populate the
    # return array
    for i in range(len(floatArray)):
        returnArray[tmpAlof[i][0]] = i+1

    return returnArray
