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
# Last updated by NL 2011/03/23


import math
import rpy2.robjects
import pp
import string

from utility import webqtlUtil
from base.webqtlTrait import webqtlTrait
from dbFunction import webqtlDatabaseFunction



#XZ: The input 'controls' is String. It contains the full name of control traits.
#XZ: The input variable 'strainlst' is List. It contains the strain names of primary trait.
#XZ: The returned tcstrains is the list of list [[],[]...]. So are tcvals and tcvars. The last returned parameter is list of numbers.
#XZ, 03/29/2010: For each returned control trait, there is no None value in it.
def controlStrains(controls, strainlst):

    controls = controls.split(',')

    cvals = {}
    for oneTraitName in controls:
        oneTrait = webqtlTrait(fullname=oneTraitName, cursor=webqtlDatabaseFunction.getCursor() )
        oneTrait.retrieveData()
        cvals[oneTraitName] = oneTrait.data

    tcstrains = []
    tcvals = []
    tcvars = []

    for oneTraitName in controls:
        strains = []
        vals = []
        vars = []

        for _strain in strainlst:
            if cvals[oneTraitName].has_key(_strain):
                _val = cvals[oneTraitName][_strain].val
                if _val != None:
                    strains.append(_strain)
                    vals.append(_val)
                    vars.append(None)

        tcstrains.append(strains)
        tcvals.append(vals)
        tcvars.append(vars)

    return tcstrains, tcvals, tcvars, [len(x) for x in tcstrains]



#XZ, 03/29/2010: After execution of functon "controlStrains" and "fixStrains", primary trait and control traits have the same strains and in the same order. There is no 'None' value in them.
def fixStrains(_strains,_controlstrains,_vals,_controlvals,_vars,_controlvars):
    """Corrects strains, vals, and vars so that all contrain only those strains common
    to the reference trait and all control traits."""

    def dictify(strains,vals,vars):
        subdict = {}
        for i in xrange(len(strains)):
            subdict[strains[i]] = (vals[i],vars[i])
        return subdict

    #XZ: The 'dicts' is a list of dictionary. The first element is the dictionary of reference trait. The rest elements are for control traits.
    dicts = []
    dicts.append(dictify(_strains,_vals,_vars))

    nCstrains = len(_controlstrains)
    for i in xrange(nCstrains):
        dicts.append(dictify(_controlstrains[i],_controlvals[i],_controlvars[i]))

    _newstrains = []
    _vals = []
    _vars = []
    _controlvals = [[] for x in xrange(nCstrains)]
    _controlvars = [[] for x in xrange(nCstrains)]

    for strain in _strains:
        inall = True
        for d in dicts:
            if strain not in d:
                inall = False
                break
        if inall:
            _newstrains.append(strain)
            _vals.append(dicts[0][strain][0])
            _vars.append(dicts[0][strain][1])
            for i in xrange(nCstrains):
                _controlvals[i].append(dicts[i+1][strain][0])
                _controlvars[i].append(dicts[i+1][strain][1])

    return _newstrains,  _vals, _controlvals, _vars, _controlvars


#XZ, 6/15/2010: If there is no identical control traits, the returned list is empty.
#else, the returned list has two elements of control trait name.
def findIdenticalControlTraits ( controlVals, controlNames ):
    nameOfIdenticalTraits = []

    controlTraitNumber = len(controlVals)

    if controlTraitNumber > 1:

        #XZ: reset the precision of values and convert to string type
        for oneTraitVal in controlVals:
            for oneStrainVal in oneTraitVal:
                oneStrainVal = '%.3f' % oneStrainVal

        for i, oneTraitVal in enumerate( controlVals ):
            for j in range(i+1, controlTraitNumber):
                if oneTraitVal == controlVals[j]:
                    nameOfIdenticalTraits.append(controlNames[i])
                    nameOfIdenticalTraits.append(controlNames[j])

    return nameOfIdenticalTraits

#XZ, 6/15/2010: If there is no identical control traits, the returned list is empty.
#else, the returned list has two elements of control trait name.
#primaryVal is of list type. It contains value of primary trait.
#primaryName is of string type.
#controlVals is of list type. Each element is list too. Each element contain value of one control trait.
#controlNames is of list type.
def findIdenticalTraits (primaryVal, primaryName, controlVals, controlNames ):
    nameOfIdenticalTraits = []

    #XZ: reset the precision of values and convert to string type
    for oneStrainVal in primaryVal:
        oneStrainVal = '%.3f' % oneStrainVal

    for oneTraitVal in controlVals:
        for oneStrainVal in oneTraitVal:
            oneStrainVal = '%.3f' % oneStrainVal

    controlTraitNumber = len(controlVals)

    if controlTraitNumber > 1:
        for i, oneTraitVal in enumerate( controlVals ):
            for j in range(i+1, controlTraitNumber):
                if oneTraitVal == controlVals[j]:
                    nameOfIdenticalTraits.append(controlNames[i])
                    nameOfIdenticalTraits.append(controlNames[j])
                    break

    if len(nameOfIdenticalTraits) == 0:
        for i, oneTraitVal in enumerate( controlVals ):
            if primaryVal == oneTraitVal:
                nameOfIdenticalTraits.append(primaryName)
                nameOfIdenticalTraits.append(controlNames[i])
                break

    return nameOfIdenticalTraits



#XZ, 03/29/2010: The strains in primaryVal, controlVals, targetVals must be of the same number and in same order.
#XZ: No value in primaryVal and controlVals could be None.

def determinePartialsByR (primaryVal, controlVals, targetVals, targetNames, method='p'):

    def compute_partial ( primaryVal, controlVals, targetVals, targetNames, method ):

        rpy2.robjects.r("""
pcor.test <- function(x,y,z,use="mat",method="p",na.rm=T){
        # The partial correlation coefficient between x and y given z
        #
        # pcor.test is free and comes with ABSOLUTELY NO WARRANTY.
        #
        # x and y should be vectors
        #
        # z can be either a vector or a matrix
        #
        # use: There are two methods to calculate the partial correlation coefficient.
        #        One is by using variance-covariance matrix ("mat") and the other is by using recursive formula ("rec").
        #        Default is "mat".
        #
        # method: There are three ways to calculate the correlation coefficient,
        #           which are Pearson's ("p"), Spearman's ("s"), and Kendall's ("k") methods.
        #           The last two methods which are Spearman's and Kendall's coefficient are based on the non-parametric analysis.
        #           Default is "p".
        #
        # na.rm: If na.rm is T, then all the missing samples are deleted from the whole dataset, which is (x,y,z).
        #        If not, the missing samples will be removed just when the correlation coefficient is calculated.
        #          However, the number of samples for the p-value is the number of samples after removing
        #          all the missing samples from the whole dataset.
        #          Default is "T".

        x <- c(x)
        y <- c(y)
        z <- as.data.frame(z)

        if(use == "mat"){
                p.use <- "Var-Cov matrix"
                pcor = pcor.mat(x,y,z,method=method,na.rm=na.rm)
        }else if(use == "rec"){
                p.use <- "Recursive formula"
                pcor = pcor.rec(x,y,z,method=method,na.rm=na.rm)
        }else{
                stop("use should be either rec or mat!\n")
        }

        # print the method
        if(gregexpr("p",method)[[1]][1] == 1){
                p.method <- "Pearson"
        }else if(gregexpr("s",method)[[1]][1] == 1){
                p.method <- "Spearman"
        }else if(gregexpr("k",method)[[1]][1] == 1){
                p.method <- "Kendall"
        }else{
                stop("method should be pearson or spearman or kendall!\n")
        }

        # sample number
        n <- dim(na.omit(data.frame(x,y,z)))[1]

        # given variables' number
        gn <- dim(z)[2]

        # p-value
        if(p.method == "Kendall"){
                statistic <- pcor/sqrt(2*(2*(n-gn)+5)/(9*(n-gn)*(n-1-gn)))
                p.value <- 2*pnorm(-abs(statistic))

        }else{
                statistic <- pcor*sqrt((n-2-gn)/(1-pcor^2))
                p.value <- 2*pnorm(-abs(statistic))
        }

        data.frame(estimate=pcor,p.value=p.value,statistic=statistic,n=n,gn=gn,Method=p.method,Use=p.use)
}

# By using var-cov matrix
pcor.mat <- function(x,y,z,method="p",na.rm=T){

        x <- c(x)
        y <- c(y)
        z <- as.data.frame(z)

        if(dim(z)[2] == 0){
                stop("There should be given data\n")
        }

        data <- data.frame(x,y,z)

        if(na.rm == T){
                data = na.omit(data)
        }

        xdata <- na.omit(data.frame(data[,c(1,2)]))
        Sxx <- cov(xdata,xdata,m=method)

        xzdata <- na.omit(data)
        xdata <- data.frame(xzdata[,c(1,2)])
        zdata <- data.frame(xzdata[,-c(1,2)])
        Sxz <- cov(xdata,zdata,m=method)

        zdata <- na.omit(data.frame(data[,-c(1,2)]))
        Szz <- cov(zdata,zdata,m=method)

        # is Szz positive definite?
        zz.ev <- eigen(Szz)$values
        if(min(zz.ev)[1]<0){
                stop("\'Szz\' is not positive definite!\n")
        }

        # partial correlation
        Sxx.z <- Sxx - Sxz %*% solve(Szz) %*% t(Sxz)

        rxx.z <- cov2cor(Sxx.z)[1,2]

        rxx.z
}

# By using recursive formula
pcor.rec <- function(x,y,z,method="p",na.rm=T){
        #

        x <- c(x)
        y <- c(y)
        z <- as.data.frame(z)

        if(dim(z)[2] == 0){
                stop("There should be given data\n")
        }

        data <- data.frame(x,y,z)

        if(na.rm == T){
                data = na.omit(data)
        }

        # recursive formula
        if(dim(z)[2] == 1){
                tdata <- na.omit(data.frame(data[,1],data[,2]))
                rxy <- cor(tdata[,1],tdata[,2],m=method)

                tdata <- na.omit(data.frame(data[,1],data[,-c(1,2)]))
                rxz <- cor(tdata[,1],tdata[,2],m=method)

                tdata <- na.omit(data.frame(data[,2],data[,-c(1,2)]))
                ryz <- cor(tdata[,1],tdata[,2],m=method)

                rxy.z <- (rxy - rxz*ryz)/( sqrt(1-rxz^2)*sqrt(1-ryz^2) )

                return(rxy.z)
        }else{
                x <- c(data[,1])
                y <- c(data[,2])
                z0 <- c(data[,3])
                zc <- as.data.frame(data[,-c(1,2,3)])

                rxy.zc <- pcor.rec(x,y,zc,method=method,na.rm=na.rm)
                rxz0.zc <- pcor.rec(x,z0,zc,method=method,na.rm=na.rm)
                ryz0.zc <- pcor.rec(y,z0,zc,method=method,na.rm=na.rm)

                rxy.z <- (rxy.zc - rxz0.zc*ryz0.zc)/( sqrt(1-rxz0.zc^2)*sqrt(1-ryz0.zc^2) )
                return(rxy.z)
        }
}
""")

        R_pcorr_function = rpy2.robjects.r['pcor.test']
        R_corr_test = rpy2.robjects.r['cor.test']

        primary = rpy2.robjects.FloatVector(range(len(primaryVal)))
        for i in range(len(primaryVal)):
            primary[i] = primaryVal[i]

        control = rpy2.robjects.r.matrix(rpy2.robjects.FloatVector( range(len(controlVals)*len(controlVals[0])) ), ncol=len(controlVals))
        for i in range(len(controlVals)):
            for j in range(len(controlVals[0])):
                control[i*len(controlVals[0]) + j] = controlVals[i][j]

        allcorrelations = []

        for targetIndex, oneTargetVals in enumerate(targetVals):

            this_primary = None
            this_control = None
            this_target = None

            if None in oneTargetVals:

                goodIndex = []
                for i in range(len(oneTargetVals)):
                    if oneTargetVals[i] != None:
                        goodIndex.append(i)

                this_primary = rpy2.robjects.FloatVector(range(len(goodIndex)))
                for i in range(len(goodIndex)):
                    this_primary[i] = primaryVal[goodIndex[i]]

                this_control = rpy2.robjects.r.matrix(rpy2.robjects.FloatVector( range(len(controlVals)*len(goodIndex)) ), ncol=len(controlVals))
                for i in range(len(controlVals)):
                    for j in range(len(goodIndex)):
                        this_control[i*len(goodIndex) + j] = controlVals[i][goodIndex[j]]

                this_target = rpy2.robjects.FloatVector(range(len(goodIndex)))
                for i in range(len(goodIndex)):
                    this_target[i] = oneTargetVals[goodIndex[i]]

            else:
                this_primary = primary
                this_control = control
                this_target = rpy2.robjects.FloatVector(range(len(oneTargetVals)))
                for i in range(len(oneTargetVals)):
                    this_target[i] = oneTargetVals[i]

            one_name = targetNames[targetIndex]
            one_N = len(this_primary)

            #calculate partial correlation
            one_pc_coefficient = 'NA'
            one_pc_p = 1

            try:
                if method == 's':
                    result = R_pcorr_function(this_primary, this_target, this_control, method='s')
                else:
                    result = R_pcorr_function(this_primary, this_target, this_control)

                #XZ: In very few cases, the returned coefficient is nan.
                #XZ: One way to detect nan is to compare the number to itself. NaN is always != NaN
                if result[0][0] == result[0][0]:
                    one_pc_coefficient = result[0][0]
                    #XZ: when the coefficient value is 1 (primary trait and target trait are the same),
                    #XZ: occationally, the returned p value is nan instead of 0.
                    if result[1][0] == result[1][0]:
                        one_pc_p = result[1][0]
                    elif abs(one_pc_coefficient - 1) < 0.0000001:
                        one_pc_p = 0
            except:
                pass

            #calculate zero order correlation
            one_corr_coefficient = 0
            one_corr_p = 1

            try:
                if method == 's':
                    R_result = R_corr_test(this_primary, this_target, method='spearman')
                else:
                    R_result = R_corr_test(this_primary, this_target)

                one_corr_coefficient = R_result[3][0]
                one_corr_p = R_result[2][0]
            except:
                pass

            traitinfo = [ one_name, one_N, one_pc_coefficient, one_pc_p, one_corr_coefficient, one_corr_p ]

            allcorrelations.append(traitinfo)

        return allcorrelations
    #End of function compute_partial


    allcorrelations = []

    target_trait_number = len(targetVals)

    if target_trait_number < 1000:
        allcorrelations = compute_partial ( primaryVal, controlVals, targetVals, targetNames, method )
    else:
        step = 1000
        job_number = math.ceil( float(target_trait_number)/step )

        job_targetVals_lists = []
        job_targetNames_lists = []

        for job_index in range( int(job_number) ):
            starti = job_index*step
            endi = min((job_index+1)*step, target_trait_number)

            one_job_targetVals_list = []
            one_job_targetNames_list = []

            for i in range( starti, endi ):
                one_job_targetVals_list.append( targetVals[i] )
                one_job_targetNames_list.append( targetNames[i] )

            job_targetVals_lists.append( one_job_targetVals_list )
            job_targetNames_lists.append( one_job_targetNames_list )

        ppservers = ()
        # Creates jobserver with automatically detected number of workers
        job_server = pp.Server(ppservers=ppservers)

        jobs = []
        results = []

        for i, one_job_targetVals_list in enumerate( job_targetVals_lists ):
            one_job_targetNames_list = job_targetNames_lists[i]
            #pay attention to modules from outside
            jobs.append( job_server.submit(func=compute_partial, args=( primaryVal, controlVals, one_job_targetVals_list, one_job_targetNames_list, method), depfuncs=(), modules=("rpy2.robjects",)) )

        for one_job in jobs:
            one_result = one_job()
            results.append( one_result )

        for one_result in results:
            for one_traitinfo in one_result:
                allcorrelations.append( one_traitinfo )

    return allcorrelations



#XZ, April 30, 2010: The input primaryTrait and targetTrait are instance of webqtlTrait
#XZ: The primaryTrait and targetTrait should have executed retrieveData function
def calZeroOrderCorr (primaryTrait, targetTrait, method='pearson'):

    #primaryTrait.retrieveData()

    #there is no None value in primary_val
    primary_strain, primary_val, primary_var = primaryTrait.exportInformative()

    #targetTrait.retrieveData()

    #there might be None value in target_val
    target_val = targetTrait.exportData(primary_strain, type="val")

    R_primary = rpy2.robjects.FloatVector(range(len(primary_val)))
    for i in range(len(primary_val)):
        R_primary[i] = primary_val[i]

    N = len(target_val)

    if None in target_val:
        goodIndex = []
        for i in range(len(target_val)):
            if target_val[i] != None:
                goodIndex.append(i)

        N = len(goodIndex)

        R_primary = rpy2.robjects.FloatVector(range(len(goodIndex)))
        for i in range(len(goodIndex)):
            R_primary[i] = primary_val[goodIndex[i]]

        R_target = rpy2.robjects.FloatVector(range(len(goodIndex)))
        for i in range(len(goodIndex)):
            R_target[i] = target_val[goodIndex[i]]

    else:
        R_target = rpy2.robjects.FloatVector(range(len(target_val)))
        for i in range(len(target_val)):
            R_target[i] = target_val[i]

    R_corr_test = rpy2.robjects.r['cor.test']

    if method == 'spearman':
        R_result = R_corr_test(R_primary, R_target, method='spearman')
    else:
        R_result = R_corr_test(R_primary, R_target)

    corr_result = []
    corr_result.append( R_result[3][0] )
    corr_result.append( N )
    corr_result.append( R_result[2][0] )

    return corr_result

#####################################################################################
#Input: primaryValue(list): one list of expression values of one probeSet,
#       targetValue(list): one list of expression values of one probeSet,
#               method(string): indicate correlation method ('pearson' or 'spearman')
#Output: corr_result(list): first item is Correlation Value, second item is tissue number,
#                           third item is PValue
#Function: get correlation value,Tissue quantity ,p value result by using R;
#Note : This function is special case since both primaryValue and targetValue are from
#the same dataset. So the length of these two parameters is the same. They are pairs.
#Also, in the datatable TissueProbeSetData, all Tissue values are loaded based on
#the same tissue order
#####################################################################################

def calZeroOrderCorrForTiss (primaryValue=[], targetValue=[], method='pearson'):

    R_primary = rpy2.robjects.FloatVector(range(len(primaryValue)))
    N = len(primaryValue)
    for i in range(len(primaryValue)):
        R_primary[i] = primaryValue[i]

    R_target = rpy2.robjects.FloatVector(range(len(targetValue)))
    for i in range(len(targetValue)):
        R_target[i]=targetValue[i]

    R_corr_test = rpy2.robjects.r['cor.test']
    if method =='spearman':
        R_result = R_corr_test(R_primary, R_target, method='spearman')
    else:
        R_result = R_corr_test(R_primary, R_target)

    corr_result =[]
    corr_result.append( R_result[3][0])
    corr_result.append( N )
    corr_result.append( R_result[2][0])

    return corr_result




def batchCalTissueCorr(primaryTraitValue=[], SymbolValueDict={}, method='pearson'):

    def cal_tissue_corr(primaryTraitValue, oneSymbolValueDict, method ):

        oneSymbolCorrDict = {}
        oneSymbolPvalueDict = {}

        R_corr_test = rpy2.robjects.r['cor.test']

        R_primary = rpy2.robjects.FloatVector(range(len(primaryTraitValue)))

        for i in range(len(primaryTraitValue)):
            R_primary[i] = primaryTraitValue[i]

        for (oneTraitSymbol, oneTraitValue) in oneSymbolValueDict.iteritems():
            R_target = rpy2.robjects.FloatVector(range(len(oneTraitValue)))
            for i in range(len(oneTraitValue)):
                R_target[i] = oneTraitValue[i]

            if method =='spearman':
                R_result = R_corr_test(R_primary, R_target, method='spearman')
            else:
                R_result = R_corr_test(R_primary, R_target)

            oneSymbolCorrDict[oneTraitSymbol] = R_result[3][0]
            oneSymbolPvalueDict[oneTraitSymbol] = R_result[2][0]

        return(oneSymbolCorrDict, oneSymbolPvalueDict)



    symbolCorrDict = {}
    symbolPvalueDict = {}

    items_number = len(SymbolValueDict)

    if items_number <= 1000:
        symbolCorrDict, symbolPvalueDict = cal_tissue_corr(primaryTraitValue, SymbolValueDict, method)
    else:
        items_list = SymbolValueDict.items()

        step = 1000
        job_number = math.ceil( float(items_number)/step )

        job_oneSymbolValueDict_list = []

        for job_index in range( int(job_number) ):
            starti = job_index*step
            endi = min((job_index+1)*step, items_number)

            oneSymbolValueDict = {}

            for i in range( starti, endi ):
                one_item = items_list[i]
                one_symbol = one_item[0]
                one_value = one_item[1]
                oneSymbolValueDict[one_symbol] = one_value

            job_oneSymbolValueDict_list.append( oneSymbolValueDict )


        ppservers = ()
        # Creates jobserver with automatically detected number of workers
        job_server = pp.Server(ppservers=ppservers)

        jobs = []
        results = []

        for i, oneSymbolValueDict in enumerate( job_oneSymbolValueDict_list ):

            #pay attention to modules from outside
            jobs.append( job_server.submit(func=cal_tissue_corr, args=(primaryTraitValue, oneSymbolValueDict, method), depfuncs=(), modules=("rpy2.robjects",)) )

        for one_job in jobs:
            one_result = one_job()
            results.append( one_result )

        for one_result in results:
            oneSymbolCorrDict, oneSymbolPvalueDict = one_result
            symbolCorrDict.update( oneSymbolCorrDict )
            symbolPvalueDict.update( oneSymbolPvalueDict )

    return (symbolCorrDict, symbolPvalueDict)

###########################################################################
#Input: cursor, GeneNameLst (list), TissueProbeSetFreezeId
#output: geneIdDict,dataIdDict,ChrDict,MbDict,descDict,pTargetDescDict (Dict)
#function: get multi dicts for short and long label functions, and for getSymbolValuePairDict and
# getGeneSymbolTissueValueDict to build dict to get CorrPvArray
#Note: If there are multiple probesets for one gene, select the one with highest mean.
###########################################################################
def getTissueProbeSetXRefInfo(cursor=None,GeneNameLst=[],TissueProbeSetFreezeId=0):
    Symbols =""
    symbolList =[]
    geneIdDict ={}
    dataIdDict = {}
    ChrDict = {}
    MbDict = {}
    descDict = {}
    pTargetDescDict = {}

    count = len(GeneNameLst)

    # Added by NL 01/06/2011
    # Note that:inner join is necessary in this query to get distinct record in one symbol group with highest mean value
    # Duo to the limit size of TissueProbeSetFreezeId table in DB, performance of inner join is acceptable.
    if count==0:
        query='''
                        select t.Symbol,t.GeneId, t.DataId,t.Chr, t.Mb,t.description,t.Probe_Target_Description
                        from (
                                select Symbol, max(Mean) as maxmean
                                from TissueProbeSetXRef
                                where TissueProbeSetFreezeId=%s and Symbol!='' and Symbol Is Not Null group by Symbol)
                        as x inner join TissueProbeSetXRef as t on t.Symbol = x.Symbol and t.Mean = x.maxmean;
                '''%TissueProbeSetFreezeId

    else:
        for i, item in enumerate(GeneNameLst):

            if i == count-1:
                Symbols += "'%s'" %item
            else:
                Symbols += "'%s'," %item

        Symbols = "("+ Symbols+")"
        query='''
                        select t.Symbol,t.GeneId, t.DataId,t.Chr, t.Mb,t.description,t.Probe_Target_Description
                        from (
                                select Symbol, max(Mean) as maxmean
                                from TissueProbeSetXRef
                                where TissueProbeSetFreezeId=%s and Symbol in %s group by Symbol)
                        as x inner join TissueProbeSetXRef as t on t.Symbol = x.Symbol and t.Mean = x.maxmean;
                '''% (TissueProbeSetFreezeId,Symbols)

    try:

        cursor.execute(query)
        results =cursor.fetchall()
        resultCount = len(results)
        # Key in all dicts is the lower-cased symbol
        for i, item in enumerate(results):
            symbol = item[0]
            symbolList.append(symbol)

            key =symbol.lower()
            geneIdDict[key]=item[1]
            dataIdDict[key]=item[2]
            ChrDict[key]=item[3]
            MbDict[key]=item[4]
            descDict[key]=item[5]
            pTargetDescDict[key]=item[6]

    except:
        symbolList = None
        geneIdDict=None
        dataIdDict=None
        ChrDict=None
        MbDict=None
        descDict=None
        pTargetDescDict=None

    return symbolList,geneIdDict,dataIdDict,ChrDict,MbDict,descDict,pTargetDescDict

###########################################################################
#Input: cursor, symbolList (list), dataIdDict(Dict)
#output: symbolValuepairDict (dictionary):one dictionary of Symbol and Value Pair,
#        key is symbol, value is one list of expression values of one probeSet;
#function: get one dictionary whose key is gene symbol and value is tissue expression data (list type).
#Attention! All keys are lower case!
###########################################################################
def getSymbolValuePairDict(cursor=None,symbolList=None,dataIdDict={}):
    symbolList = map(string.lower, symbolList)
    symbolValuepairDict={}
    valueList=[]

    for key in symbolList:
        if dataIdDict.has_key(key):
            DataId = dataIdDict[key]

            valueQuery = "select value from TissueProbeSetData where Id=%s" % DataId
            try :
                cursor.execute(valueQuery)
                valueResults = cursor.fetchall()
                for item in valueResults:
                    item =item[0]
                    valueList.append(item)
                symbolValuepairDict[key] = valueList
                valueList=[]
            except:
                symbolValuepairDict[key] = None

    return symbolValuepairDict


########################################################################################################
#input: cursor, symbolList (list), dataIdDict(Dict): key is symbol
#output: SymbolValuePairDict(dictionary):one dictionary of Symbol and Value Pair.
#        key is symbol, value is one list of expression values of one probeSet.
#function: wrapper function for getSymbolValuePairDict function
#          build gene symbol list if necessary, cut it into small lists if necessary,
#          then call getSymbolValuePairDict function and merge the results.
########################################################################################################

def getGeneSymbolTissueValueDict(cursor=None,symbolList=None,dataIdDict={}):
    limitNum=1000
    count = len(symbolList)

    SymbolValuePairDict = {}

    if count !=0 and count <=limitNum:
        SymbolValuePairDict = getSymbolValuePairDict(cursor=cursor,symbolList=symbolList,dataIdDict=dataIdDict)

    elif count >limitNum:
        SymbolValuePairDict={}
        n = count/limitNum
        start =0
        stop =0

        for i in range(n):
            stop =limitNum*(i+1)
            gList1 = symbolList[start:stop]
            PairDict1 = getSymbolValuePairDict(cursor=cursor,symbolList=gList1,dataIdDict=dataIdDict)
            start =limitNum*(i+1)

            SymbolValuePairDict.update(PairDict1)

        if stop < count:
            stop = count
            gList2 = symbolList[start:stop]
            PairDict2 = getSymbolValuePairDict(cursor=cursor,symbolList=gList2,dataIdDict=dataIdDict)
            SymbolValuePairDict.update(PairDict2)

    return SymbolValuePairDict

########################################################################################################
#input: cursor, GeneNameLst (list), TissueProbeSetFreezeId(int)
#output: SymbolValuePairDict(dictionary):one dictionary of Symbol and Value Pair.
#        key is symbol, value is one list of expression values of one probeSet.
#function: wrapper function of getGeneSymbolTissueValueDict function
#          for CorrelationPage.py
########################################################################################################

def getGeneSymbolTissueValueDictForTrait(cursor=None,GeneNameLst=[],TissueProbeSetFreezeId=0):
    SymbolValuePairDict={}
    symbolList,geneIdDict,dataIdDict,ChrDict,MbDict,descDict,pTargetDescDict = getTissueProbeSetXRefInfo(cursor=cursor,GeneNameLst=GeneNameLst,TissueProbeSetFreezeId=TissueProbeSetFreezeId)
    if symbolList:
        SymbolValuePairDict = getGeneSymbolTissueValueDict(cursor=cursor,symbolList=symbolList,dataIdDict=dataIdDict)
    return SymbolValuePairDict

########################################################################################################
#Input: cursor(cursor): MySQL connnection cursor;
#       priGeneSymbolList(list): one list of gene symbol;
#       symbolValuepairDict(dictionary): one dictionary of Symbol and Value Pair,
#               key is symbol, value is one list of expression values of one probeSet;
#Output: corrArray(array): array of Correlation Value,
#        pvArray(array): array of PValue;
#Function: build corrArray, pvArray for display by calling  calculation function:calZeroOrderCorrForTiss
########################################################################################################

def getCorrPvArray(cursor=None,priGeneSymbolList=[],symbolValuepairDict={}):
    # setting initial value for corrArray, pvArray equal to 0
    Num = len(priGeneSymbolList)

    corrArray = [([0] * (Num))[:] for i in range(Num)]
    pvArray = [([0] * (Num))[:] for i in range(Num)]
    i = 0
    for pkey in priGeneSymbolList:
        j = 0
        pkey = pkey.strip().lower()# key in symbolValuepairDict is low case
        if symbolValuepairDict.has_key(pkey):
            priValue = symbolValuepairDict[pkey]
            for tkey in priGeneSymbolList:
                tkey = tkey.strip().lower()# key in symbolValuepairDict is low case
                if priValue and symbolValuepairDict.has_key(tkey):
                    tarValue = symbolValuepairDict[tkey]

                    if tarValue:
                        if i>j:
                            # corrArray stores Pearson Correlation values
                            # pvArray stores Pearson P-Values
                            pcorr_result =calZeroOrderCorrForTiss(primaryValue=priValue,targetValue=tarValue)
                            corrArray[i][j] =pcorr_result[0]
                            pvArray[i][j] =pcorr_result[2]
                        elif i<j:
                            # corrArray stores Spearman Correlation values
                            # pvArray stores Spearman P-Values
                            scorr_result =calZeroOrderCorrForTiss(primaryValue=priValue,targetValue=tarValue,method='spearman')
                            corrArray[i][j] =scorr_result[0]
                            pvArray[i][j] =scorr_result[2]
                        else:
                            # on the diagonal line, correlation value is 1, P-Values is 0
                            corrArray[i][j] =1
                            pvArray[i][j] =0
                        j+=1
                    else:
                        corrArray[i][j] = None
                        pvArray[i][j] = None
                        j+=1
                else:
                    corrArray[i][j] = None
                    pvArray[i][j] = None
                    j+=1
        else:
            corrArray[i][j] = None
            pvArray[i][j] = None

        i+=1

    return corrArray, pvArray

########################################################################################################
#Input: cursor(cursor): MySQL connnection cursor;
#       primaryTraitSymbol(string): one gene symbol;
#               TissueProbeSetFreezeId (int): Id of related TissueProbeSetFreeze
#       method: '0' default value, Pearson Correlation; '1', Spearman Correlation
#Output: symbolCorrDict(Dict): Dict of Correlation Value, key is symbol
#        symbolPvalueDict(Dict): Dict of PValue,key is symbol ;
#Function: build symbolCorrDict, symbolPvalueDict for display by calling  calculation function:calZeroOrderCorrForTiss
########################################################################################################
def calculateCorrOfAllTissueTrait(cursor=None, primaryTraitSymbol=None, TissueProbeSetFreezeId=None,method='0'):

    symbolCorrDict = {}
    symbolPvalueDict = {}

    primaryTraitSymbolValueDict = getGeneSymbolTissueValueDictForTrait(cursor=cursor, GeneNameLst=[primaryTraitSymbol], TissueProbeSetFreezeId=TissueProbeSetFreezeId)
    primaryTraitValue = primaryTraitSymbolValueDict.values()[0]

    SymbolValueDict = getGeneSymbolTissueValueDictForTrait(cursor=cursor, GeneNameLst=[], TissueProbeSetFreezeId=TissueProbeSetFreezeId)

    if method =='1':
        symbolCorrDict, symbolPvalueDict = batchCalTissueCorr(primaryTraitValue,SymbolValueDict,method='spearman')
    else:
        symbolCorrDict, symbolPvalueDict = batchCalTissueCorr(primaryTraitValue,SymbolValueDict)


    return (symbolCorrDict, symbolPvalueDict)
