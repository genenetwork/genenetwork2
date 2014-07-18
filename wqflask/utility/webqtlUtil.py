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
import time
import re
import math
from math import *

from htmlgen import HTMLgen2 as HT

from base import webqtlConfig




# NL, 07/27/2010. moved from webqtlForm.py
#Dict of Parents and F1 information, In the order of [F1, Mat, Pat]
ParInfo ={
'BXH':['BHF1', 'HBF1',  'C57BL/6J', 'C3H/HeJ'],
'AKXD':['AKF1', 'KAF1', 'AKR/J', 'DBA/2J'],
'BXD':['B6D2F1', 'D2B6F1', 'C57BL/6J', 'DBA/2J'],
'BXD300':['B6D2F1', 'D2B6F1', 'C57BL/6J', 'DBA/2J'],
'B6BTBRF2':['B6BTBRF1', 'BTBRB6F1', 'C57BL/6J', 'BTBRT<+>tf/J'],
'BHHBF2':['B6HF2','HB6F2','C57BL/6J','C3H/HeJ'],
'BHF2':['B6HF2','HB6F2','C57BL/6J','C3H/HeJ'],
'B6D2F2':['B6D2F1', 'D2B6F1', 'C57BL/6J', 'DBA/2J'],
'BDF2-1999':['B6D2F2', 'D2B6F2', 'C57BL/6J', 'DBA/2J'],
'BDF2-2005':['B6D2F1', 'D2B6F1', 'C57BL/6J', 'DBA/2J'],
'CTB6F2':['CTB6F2','B6CTF2','C57BL/6J','Castaneous'],
'CXB':['CBF1', 'BCF1', 'C57BL/6ByJ', 'BALB/cByJ'],
'AXBXA':['ABF1', 'BAF1', 'C57BL/6J', 'A/J'],
'AXB':['ABF1', 'BAF1', 'C57BL/6J', 'A/J'],
'BXA':['BAF1', 'ABF1', 'C57BL/6J', 'A/J'],
'LXS':['LSF1', 'SLF1', 'ISS', 'ILS'],
'HXBBXH':['HSRBNF1', 'BNHSRF1', 'BN', 'HSR'],
'BayXSha':['BayXShaF1', 'ShaXBayF1', 'Bay-0','Shahdara'],
'ColXBur':['ColXBurF1', 'BurXColF1', 'Col-0','Bur-0'],
'ColXCvi':['ColXCviF1', 'CviXColF1', 'Col-0','Cvi'],
'SXM':['SMF1', 'MSF1', 'Steptoe','Morex']
}


# NL, 07/27/2010. moved from template.py
IMGSTEP1 = HT.Image('/images/step1.gif', alt='STEP 1',border=0) #XZ, Only be used in inputPage.py
IMGSTEP2 = HT.Image('/images/step2.gif', alt='STEP 2',border=0) #XZ, Only be used in inputPage.py
IMGSTEP3 = HT.Image('/images/step3.gif', alt='STEP 3',border=0) #XZ, Only be used in inputPage.py
IMGNEXT = HT.Image('/images/arrowdown.gif', alt='NEXT',border=0) #XZ, Only be used in inputPage.py

IMGASC = HT.Image("/images/sortup.gif", border=0)
IMGASCON = HT.Image("/images/sortupon.gif", border=0)
IMGDESC = HT.Image("/images/sortdown.gif", border=0)
IMGDESCON = HT.Image("/images/sortdownon.gif", border=0)

"""
IMGASC = HT.Image("/images/sortup_icon.gif", border=0)
IMGASCON = HT.Image("/images/sortupon.gif", border=0)
IMGDESC = HT.Image("/images/sortdown_icon.gif", border=0)
IMGDESCON = HT.Image("/images/sortdownon.gif", border=0)
IMG_UNSORTED = HT.Image("/images/unsorted_icon.gif", border=0)
"""

PROGRESSBAR = HT.Image('/images/waitAnima2.gif', alt='checkblue',align="middle",border=0)

#########################################
#      Accessory Functions
#########################################

def inverseCumul(p):
    #Coefficients in rational approximations.
    a = [-3.969683028665376e+01,2.209460984245205e+02,-2.759285104469687e+02,1.383577518672690e+02,-3.066479806614716e+01,2.506628277459239e+00]

    b = [-5.447609879822406e+01,1.615858368580409e+02,-1.556989798598866e+02,6.680131188771972e+01,-1.328068155288572e+01]

    c = [-7.784894002430293e-03,-3.223964580411365e-01,-2.400758277161838e+00,-2.549732539343734e+00,4.374664141464968e+00,2.938163982698783e+00]

    d =  [7.784695709041462e-03,3.224671290700398e-01,2.445134137142996e+00,3.754408661907416e+00]

    #Define break-points.

    p_low  = 0.02425
    p_high = 1 - p_low

    #Rational approximation for lower region.

    if p > 0 and p < p_low:
        q = sqrt(-2*log(p))
        x = (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)


    #Rational approximation for central region.

    elif p>= p_low and p <= p_high:
        q = p - 0.5
        r = q*q
        x = (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q /(((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)

    #Rational approximation for upper region.

    elif p>p_high and  p < 1:
        q = sqrt(-2*log(1-p))
        x = -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) /((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)

    else:
        return None

    if p>0 and p < 1:
        e = 0.5 * erfcc(-x/sqrt(2)) - p 
        u = e * sqrt(2*pi) * exp(x*x/2)
        x = x - u/(1 + x*u/2)
        return x
    else:
        return None

def erfcc(x):
	z=abs(x)
	t=1.0/(1.0+0.5*z)
	ans=t*exp(-z*z-1.26551223+t*(1.00002368+t*(0.37409196+t*(0.09678418+t*(-0.18628806+t*(0.27886807+t*(-1.13520398+t*(1.48851587+t*(-0.82215223+t*0.17087277)))))))))
	if x>=0.0:
		return ans
	else:
		return 2.0-ans

def U(n):
	x=pow(0.5,1.0/n)
	m=[1-x]
	for i in range(2,n):
		a=(i-0.3175)/(n+0.365)
		m.append(a)
	m.append(x)
	return m

def decodeEscape(str):
    a = str
    pattern = re.compile('(%[0-9A-Fa-f][0-9A-Fa-f])')
    match = pattern.findall(a)
    matched = []
    for item in match:
        if item not in matched:
            a = a.replace(item, '%c' % eval("0x"+item[-2:]))
        matched.append(item)
    return a

def exportData(hddn, tdata, NP = None):
    for key in tdata.keys():
        _val, _var, _N = tdata[key].val, tdata[key].var, tdata[key].N
        if _val != None:
            hddn[key] = _val
            if _var != None:
                hddn['V'+key] = _var
            if NP and _N != None:
                hddn['N'+key] = _N

def genShortStrainName(RISet='', input_strainName=''):
    #aliasStrainDict = {'C57BL/6J':'B6','DBA/2J':'D2'}
    strainName = input_strainName
    if RISet != 'AXBXA':
        if RISet == 'BXD300':
            this_RISet = 'BXD'
        elif RISet == 'BDF2-2005':
            this_RISet = 'CASE05_'
        else:
            this_RISet = RISet
        strainName = string.replace(strainName,this_RISet,'')
        strainName = string.replace(strainName,'CASE','')
        try:
            strainName = "%02d" % int(strainName)
        except:
            pass
    else:
        strainName = string.replace(strainName,'AXB','A')
        strainName = string.replace(strainName,'BXA','B')
        try:
            strainName = strainName[0] + "%02d" % int(strainName[1:])
        except:
            pass
    return strainName

def toInt(in_str):
    "Converts an arbitrary string to an unsigned integer"
    start = -1
    end = -1
    for i, char in enumerate(in_str):
        if char >= '0' and char <= '9':
            if start < 0:
                start = i
            end = i+1
        else:
            if start >= 0:
                break
    if start < end:
        return int(in_str[start:end])
    else:
        return  -1

def transpose(m):
    'transpose a matrix'
    n = len(m)
    return [[m[j][i] for i in range(len(m[0])) for j in range(n)][k*n:k*n+n] for k in range(len(m[0]))]

def asymTranspose(m):
    'transpose a matrix'
    t = max(map(len, m))
    n = len(m)
    m2 = [["-"]]*n
    for i in range(n):
        m2[i] = m[i] + [""]*(t- len(m[i]))
    return [[m2[j][i] for i in range(len(m2[0])) for j in range(n)][k*n:k*n+n] for k in range(len(m2[0]))]

def genRandStr(prefix = "", length=8, chars=string.letters+string.digits):
    from random import choice
    _str = prefix[:]
    for i in range(length):
        _str += choice(chars)
    return _str

def generate_session():
    import sha
    return sha.new(str(time.time())).hexdigest()

def cvt2Dict(x):
    tmp = {}
    for key in x.keys():
        tmp[key] = x[key]
    return tmp

def dump_session(session_obj, filename):
    "It seems mod python can only cPickle most basic data type"
    import cPickle
    session_file = open(filename, 'wb')
    #try:
    #       pass
    #except:
    #       pass
    cPickle.dump(session_obj, session_file)
    session_file.close()

def StringAsFloat(str):
    'Converts string to float but catches any exception and returns None'
    try:
        return float(str)
    except:
        return None

def IntAsFloat(str):
    'Converts string to Int but catches any exception and returns None'
    try:
        return int(str)
    except:
        return None

def FloatAsFloat(flt):
    'Converts float to string but catches any exception and returns None'
    try:
        return float("%2.3f" % flt)
    except:
        return None

def RemoveZero(flt):
    'Converts string to float but catches any exception and returns None'
    try:
        if abs(flt) < 1e-6:
            return None
        else:
            return flt
    except:
        return None


def SciFloat(d):
    'Converts string to float but catches any exception and returns None'

    try:
        if abs(d) <= 1.0e-4:
            return "%1.2e" % d
        else:
            return "%1.5f" % d
    except:
        return None

###To be removed
def FloatList2String(lst):
    'Converts float list to string but catches any exception and returns None'
    tt=''
    try:
        for item in lst:
            if item == None:
                tt += 'X '
            else:
                tt += '%f ' % item
        return tt
    except:
        return ""

def ListNotNull(lst):
    '''Obsolete - Use built in function any (or all or whatever)
    
    
    Determine if the elements in a list are all null
    
    '''
    for item in lst:
        if item is not None:
            return 1
    return None

###To be removed
def FileDataProcess(str):
    'Remove the description text from the input file if theres any'
    i=0
    while i<len(str):
        if str[i]<'\x7f' and str[i]>'\x20':
            break
        else:
            i+=1
    str=str[i:]
    str=string.join(string.split(str,'\000'),'')
    i=string.find(str,"*****")
    if i>-1:
        return str[i+5:]
    else:
        return str

def rank(a,lst,offset=0):
    """Calculate the integer rank of a number in an array, can be used to calculate p-value"""
    n = len(lst)
    if n == 2:
        if a <lst[0]:
            return offset
        elif a > lst[1]:
            return offset + 2
        else:
            return offset +1
    elif n == 1:
        if a <lst[0]:
            return offset
        else:
            return offset +1
    elif n== 0:
        return offset
    else:
        mid = n/2
        if a < lst[mid]:
            return rank(a,lst[:mid-1],offset)
        else:
            return rank(a,lst[mid:],offset+mid)

def cmpScanResult(A,B):
    try:
        if A.LRS > B.LRS:
            return 1
        elif A.LRS == B.LRS:
            return 0
        else:
            return -1
    except:
        return 0


def cmpScanResult2(A,B):
    try:
        if A.LRS < B.LRS:
            return 1
        elif A.LRS == B.LRS:
            return 0
        else:
            return -1
    except:
        return 0

def cmpOrder(A,B):
    try:
        if A[1] < B[1]:
            return -1
        elif A[1] == B[1]:
            return 0
        else:
            return 1
    except:
        return 0

def cmpOrder2(A,B):
    try:
        if A[-1] < B[-1]:
            return -1
        elif A[-1] == B[-1]:
            return 0
        else:
            return 1
    except:
        return 0




def calRank(xVals, yVals, N): ###  Zach Sloan, February 4 2010
    """
    Returns a ranked set of X and Y values. These are used when generating
    a Spearman scatterplot. Bear in mind that this sets values equal to each
    other as the same rank.
    """
    XX = []
    YY = []
    X = [0]*len(xVals)
    Y = [0]*len(yVals)
    j = 0

    for i in range(len(xVals)):

        if xVals[i] != None and yVals[i] != None:
            XX.append((j, xVals[i]))
            YY.append((j, yVals[i]))
            j = j + 1

    NN = len(XX)

    XX.sort(cmpOrder2)
    YY.sort(cmpOrder2)

    j = 1
    rank = 0.0

    while j < NN:

        if XX[j][1] != XX[j-1][1]:
            X[XX[j-1][0]] = j
            j = j+1

        else:
            jt = j+1
            ji = j
            for jt in range(j+1, NN):
                if (XX[jt][1] != XX[j-1][1]):
                    break
            rank = 0.5*(j+jt)
            for ji in range(j-1, jt):
                X[XX[ji][0]] = rank
            if (jt == NN-1):
                if (XX[jt][1] == XX[j-1][1]):
                    X[XX[NN-1][0]] = rank
            j = jt+1

    if j == NN:
        if X[XX[NN-1][0]] == 0:
            X[XX[NN-1][0]] = NN

    j = 1
    rank = 0.0

    while j < NN:

        if YY[j][1] != YY[j-1][1]:
            Y[YY[j-1][0]] = j
            j = j+1
        else:
            jt = j+1
            ji = j
            for jt in range(j+1, NN):
                if (YY[jt][1] != YY[j-1][1]):
                    break
            rank = 0.5*(j+jt)
            for ji in range(j-1, jt):
                Y[YY[ji][0]] = rank
            if (jt == NN-1):
                if (YY[jt][1] == YY[j-1][1]):
                    Y[YY[NN-1][0]] = rank
            j = jt+1

    if j == NN:
        if Y[YY[NN-1][0]] == 0:
            Y[YY[NN-1][0]] = NN

    return (X,Y)

def calCorrelationRank(xVals,yVals,N):
    """
    Calculated Spearman Ranked Correlation. The algorithm works
    by setting all tied ranks to the average of those ranks (for
    example, if ranks 5-10 all have the same value, each will be set
    to rank 7.5).
    """

    XX = []
    YY = []
    j = 0

    for i in range(len(xVals)):
        if xVals[i]!= None and yVals[i]!= None:
            XX.append((j,xVals[i]))
            YY.append((j,yVals[i]))
            j = j+1

    NN = len(XX)
    if NN <6:
        return (0.0,NN)
    XX.sort(cmpOrder2)
    YY.sort(cmpOrder2)
    X = [0]*NN
    Y = [0]*NN

    j = 1
    rank = 0.0
    t = 0.0
    sx = 0.0

    while j < NN:

        if XX[j][1] != XX[j-1][1]:
            X[XX[j-1][0]] = j
            j = j+1

        else:
            jt = j+1
            ji = j
            for jt in range(j+1, NN):
                if (XX[jt][1] != XX[j-1][1]):
                    break
            rank = 0.5*(j+jt)
            for ji in range(j-1, jt):
                X[XX[ji][0]] = rank
            t = jt-j
            sx = sx + (t*t*t-t)
            if (jt == NN-1):
                if (XX[jt][1] == XX[j-1][1]):
                    X[XX[NN-1][0]] = rank
            j = jt+1

    if j == NN:
        if X[XX[NN-1][0]] == 0:
            X[XX[NN-1][0]] = NN

    j = 1
    rank = 0.0
    t = 0.0
    sy = 0.0

    while j < NN:

        if YY[j][1] != YY[j-1][1]:
            Y[YY[j-1][0]] = j
            j = j+1
        else:
            jt = j+1
            ji = j
            for jt in range(j+1, NN):
                if (YY[jt][1] != YY[j-1][1]):
                    break
            rank = 0.5*(j+jt)
            for ji in range(j-1, jt):
                Y[YY[ji][0]] = rank
            t = jt - j
            sy = sy + (t*t*t-t)
            if (jt == NN-1):
                if (YY[jt][1] == YY[j-1][1]):
                    Y[YY[NN-1][0]] = rank
            j = jt+1

    if j == NN:
        if Y[YY[NN-1][0]] == 0:
            Y[YY[NN-1][0]] = NN

    D = 0.0

    for i in range(NN):
        D += (X[i]-Y[i])*(X[i]-Y[i])

    fac = (1.0 -sx/(NN*NN*NN-NN))*(1.0-sy/(NN*NN*NN-NN))

    return ((1-(6.0/(NN*NN*NN-NN))*(D+(sx+sy)/12.0))/math.sqrt(fac),NN)


def calCorrelationRankText(dbdata,userdata,N): ### dcrowell = David Crowell, July 2008
    """Calculates correlation ranks with data formatted from the text file.
    dbdata, userdata are lists of strings.  N is an int.  Returns a float.
    Used by correlationPage"""
    XX = []
    YY = []
    j = 0
    for i in range(N):
        if (dbdata[i]!= None and userdata[i]!=None) and (dbdata[i]!= 'None' and userdata[i]!='None'):
            XX.append((j,float(dbdata[i])))
            YY.append((j,float(userdata[i])))
            j += 1
    NN = len(XX)
    if NN <6:
        return (0.0,NN)
    XX.sort(cmpOrder2)
    YY.sort(cmpOrder2)
    X = [0]*NN
    Y = [0]*NN

    j = 1
    rank = 0.0
    t = 0.0
    sx = 0.0

    while j < NN:

        if XX[j][1] != XX[j-1][1]:
            X[XX[j-1][0]] = j
            j = j+1

        else:
            jt = j+1
            ji = j
            for jt in range(j+1, NN):
                if (XX[jt][1] != XX[j-1][1]):
                    break
            rank = 0.5*(j+jt)
            for ji in range(j-1, jt):
                X[XX[ji][0]] = rank
            t = jt-j
            sx = sx + (t*t*t-t)
            if (jt == NN-1):
                if (XX[jt][1] == XX[j-1][1]):
                    X[XX[NN-1][0]] = rank
            j = jt+1

    if j == NN:
        if X[XX[NN-1][0]] == 0:
            X[XX[NN-1][0]] = NN

    j = 1
    rank = 0.0
    t = 0.0
    sy = 0.0

    while j < NN:

        if YY[j][1] != YY[j-1][1]:
            Y[YY[j-1][0]] = j
            j = j+1
        else:
            jt = j+1
            ji = j
            for jt in range(j+1, NN):
                if (YY[jt][1] != YY[j-1][1]):
                    break
            rank = 0.5*(j+jt)
            for ji in range(j-1, jt):
                Y[YY[ji][0]] = rank
            t = jt - j
            sy = sy + (t*t*t-t)
            if (jt == NN-1):
                if (YY[jt][1] == YY[j-1][1]):
                    Y[YY[NN-1][0]] = rank
            j = jt+1

    if j == NN:
        if Y[YY[NN-1][0]] == 0:
            Y[YY[NN-1][0]] = NN

    D = 0.0

    for i in range(NN):
        D += (X[i]-Y[i])*(X[i]-Y[i])

    fac = (1.0 -sx/(NN*NN*NN-NN))*(1.0-sy/(NN*NN*NN-NN))

    return ((1-(6.0/(NN*NN*NN-NN))*(D+(sx+sy)/12.0))/math.sqrt(fac),NN)



def calCorrelation(dbdata,userdata,N):
    X = []
    Y = []
    for i in range(N):
        if dbdata[i]!= None and userdata[i]!= None:
            X.append(dbdata[i])
            Y.append(userdata[i])
    NN = len(X)
    if NN <6:
        return (0.0,NN)
    sx = reduce(lambda x,y:x+y,X,0.0)
    sy = reduce(lambda x,y:x+y,Y,0.0)
    meanx = sx/NN
    meany = sy/NN
    xyd = 0.0
    sxd = 0.0
    syd = 0.0
    for i in range(NN):
        xyd += (X[i] - meanx)*(Y[i]-meany)
        sxd += (X[i] - meanx)*(X[i] - meanx)
        syd += (Y[i] - meany)*(Y[i] - meany)
    try:
        corr = xyd/(sqrt(sxd)*sqrt(syd))
    except:
        corr = 0
    return (corr,NN)

def calCorrelationText(dbdata,userdata,N): ### dcrowell July 2008
    """Calculates correlation coefficients with values formatted from text files. dbdata, userdata are lists of strings.  N is an int.  Returns a float
    Used by correlationPage"""
    X = []
    Y = []
    for i in range(N):
        #if (dbdata[i]!= None and userdata[i]!= None) and (dbdata[i]!= 'None' and userdata[i]!= 'None'):
        #               X.append(float(dbdata[i]))
        #               Y.append(float(userdata[i]))
        if dbdata[i] == None or dbdata[i] == 'None' or userdata[i] == None or userdata[i] == 'None':
            continue
        else:
            X.append(float(dbdata[i]))
            Y.append(float(userdata[i]))
    NN = len(X)
    if NN <6:
        return (0.0,NN)
    sx = sum(X)
    sy = sum(Y)
    meanx = sx/float(NN)
    meany = sy/float(NN)
    xyd = 0.0
    sxd = 0.0
    syd = 0.0
    for i in range(NN):
        x1 = X[i]-meanx
        y1 = Y[i]-meany
        xyd += x1*y1
        sxd += x1**2
        syd += y1**2
    try:
        corr = xyd/(sqrt(sxd)*sqrt(syd))
    except:
        corr = 0
    return (corr,NN)


def readLineCSV(line): ### dcrowell July 2008
    """Parses a CSV string of text and returns a list containing each element as a string.
    Used by correlationPage"""
    returnList = line.split('","')
    returnList[-1]=returnList[-1][:-2]
    returnList[0]=returnList[0][1:]
    return returnList


def cmpCorr(A,B):
    try:
        if abs(A[1]) < abs(B[1]):
            return 1
        elif abs(A[1]) == abs(B[1]):
            return 0
        else:
            return -1
    except:
        return 0

def cmpLitCorr(A,B):
    try:
        if abs(A[3]) < abs(B[3]): return 1
        elif abs(A[3]) == abs(B[3]):
            if abs(A[1]) < abs(B[1]): return 1
            elif abs(A[1]) == abs(B[1]): return 0
            else: return -1
        else: return -1
    except:
        return 0

def cmpPValue(A,B):
    try:
        if A.corrPValue < B.corrPValue:
            return -1
        elif A.corrPValue == B.corrPValue:
            if abs(A.corr) > abs(B.corr):
                return -1
            elif abs(A.corr) < abs(B.corr):
                return 1
            else:
                return 0
        else:
            return 1
    except:
        return 0

def cmpEigenValue(A,B):
    try:
        if A[0] > B[0]:
            return -1
        elif A[0] == B[0]:
            return 0
        else:
            return 1
    except:
        return 0


def cmpLRSFull(A,B):
    try:
        if A[0] < B[0]:
            return -1
        elif A[0] == B[0]:
            return 0
        else:
            return 1
    except:
        return 0

def cmpLRSInteract(A,B):
    try:
        if A[1] < B[1]:
            return -1
        elif A[1] == B[1]:
            return 0
        else:
            return 1
    except:
        return 0


def cmpPos(A,B):
    try:
        try:
            AChr = int(A.chr)
        except:
            AChr = 20
        try:
            BChr = int(B.chr)
        except:
            BChr = 20
        if AChr > BChr:
            return 1
        elif AChr == BChr:
            if A.mb > B.mb:
                return 1
            if A.mb == B.mb:
                return 0
            else:
                return -1
        else:
            return -1
    except:
        return 0

def cmpGenoPos(A,B):
    try:
        A1 = A.chr
        B1 = B.chr
        try:
            A1 = int(A1)
        except:
            A1 = 25
        try:
            B1 = int(B1)
        except:
            B1 = 25
        if A1 > B1:
            return 1
        elif A1 == B1:
            if A.mb > B.mb:
                return 1
            if A.mb == B.mb:
                return 0
            else:
                return -1
        else:
            return -1
    except:
        return 0

#XZhou: Must use "BINARY" to enable case sensitive comparison.
def authUser(name,password,db, encrypt=None):
    try:
        if encrypt:
            query = 'SELECT privilege, id,name,password, grpName FROM User WHERE name= BINARY \'%s\' and password= BINARY \'%s\'' % (name,password)
        else:
            query = 'SELECT privilege, id,name,password, grpName FROM User WHERE name= BINARY \'%s\' and password= BINARY SHA(\'%s\')' % (name,password)
        db.execute(query)
        records = db.fetchone()
        if not records:
            raise ValueError
        return records#(privilege,id,name,password,grpName)
    except:
        return (None, None, None, None, None)


def hasAccessToConfidentialPhenotypeTrait(privilege, userName, authorized_users):
    access_to_confidential_phenotype_trait = 0
    if webqtlConfig.USERDICT[privilege] > webqtlConfig.USERDICT['user']:
        access_to_confidential_phenotype_trait = 1
    else:
        AuthorizedUsersList=map(string.strip, string.split(authorized_users, ','))
        if AuthorizedUsersList.__contains__(userName):
            access_to_confidential_phenotype_trait = 1
    return access_to_confidential_phenotype_trait


class VisualizeException(Exception):
    def __init__(self, message):
        self.message = message
    def __str__(self):
        return self.message

# safeConvert : (string -> A) -> A -> A
# to convert a string to type A, using the supplied default value
# if the given conversion function doesn't work
def safeConvert(f, value, default):
    try:
        return f(value)
    except:
        return default

# safeFloat : string -> float -> float
# to convert a string to a float safely
def safeFloat(value, default):
    return safeConvert(float, value, default)

# safeInt: string -> int -> int
# to convert a string to an int safely
def safeInt(value, default):
    return safeConvert(int, value, default)

# safeString : string -> (arrayof string) -> string -> string
# if a string is not in a list of strings to pick a default value
# for that string
def safeString(value, validChoices, default):
    if value in validChoices:
        return value
    else:
        return default

# yesNoToInt: string -> int
# map "yes" -> 1 and "no" -> 0
def yesNoToInt(value):
    if value == "yes":
        return 1
    elif value == "no":
        return 0
    else:
        return None

# IntToYesNo: int -> string
# map 1 -> "yes" and 0 -> "no"
def intToYesNo(value):
    if value == 1:
        return "yes"
    elif value == 0:
        return "no"
    else:
        return None

def formatField(name):
    name = name.replace("_", " ")
    name = name.title()
    #name = name.replace("Mb Mm6", "Mb");
    return name.replace("Id", "ID")

#XZ, 03/27/2009: This function is very specific.
#It is used by AJAX_table.py, correlationPage.py and dataPage.py


def genTableObj(tblobj=None, file="", sortby = ("", ""), tableID = "sortable", addIndex = "1", hiddenColumns=[]):
    header = tblobj['header']
    body = tblobj['body']
    field, order = sortby

    #ZAS 9/12/2011 - The hiddenColumns array needs to be converted into a string so they can be placed into the javascript of each up/down button
    hiddenColumnsString = ",".join(hiddenColumns)

    tbl = HT.TableLite(Class="collap b2", cellspacing=1, cellpadding=5)

    hiddenColumnIdx = [] #indices of columns to hide
    idx = -1
    last_idx = 0 #ZS: This is the index of the last item in the regular table header (without any extra parameters). It is used to determine the index of each extra parameter.
    for row in header:
        hr = HT.TR()
        for i, item in enumerate(row):
            if (item.text == '') or (item.text not in hiddenColumns):
                if item.sort and item.text:
                    down = HT.Href("javascript:xmlhttpPost('%smain.py?FormID=AJAX_table', '%s', 'sort=%s&order=down&file=%s&tableID=%s&addIndex=%s&hiddenColumns=%s')" % (webqtlConfig.CGIDIR, tableID, item.text, file, tableID, addIndex, hiddenColumnsString),IMGDESC)
                    up = HT.Href("javascript:xmlhttpPost('%smain.py?FormID=AJAX_table', '%s', 'sort=%s&order=up&file=%s&tableID=%s&addIndex=%s&hiddenColumns=%s')" % (webqtlConfig.CGIDIR, tableID, item.text, file, tableID, addIndex, hiddenColumnsString),IMGASC)
                    if item.text == field:
                        idx = item.idx
                        last_idx = idx
                        if order == 'up':
                            up = IMGASCON
                        elif order == 'down':
                            down = IMGDESCON
                    item.html.append(HT.Div(up, down, style="float: bottom;"))
                hr.append(item.html)
            else:
                hiddenColumnIdx.append(i)
        tbl.append(hr)

    for i, row in enumerate(body):
        for j, item in enumerate(row):
            if order == 'down':
                if (item.val == '' or item.val == 'x' or item.val == 'None'):
                    item.val = 0
            if order == 'up':
                if (item.val == '' or item.val == 'x' or item.val == 'None'):
                    item.val = 'zzzzz'

    if idx >= 0:
        if order == 'down':
            body.sort(lambda A, B: cmp(B[idx].val, A[idx].val), key=natsort_key)
        elif order == 'up':
            body.sort(lambda A, B: cmp(A[idx].val, B[idx].val), key=natsort_key)
        else:
            pass

    for i, row in enumerate(body):
        hr = HT.TR(Id = row[0].text)
        for j, item in enumerate(row):
            if (j not in hiddenColumnIdx):
                if j == 0:
                    if addIndex == "1":
                        item.html.contents = [i+1] + item.html.contents
                hr.append(item.html)
        tbl.append(hr)

    return tbl

def natsort_key(string):
    r = []
    for c in string:
        try:
            c = int(c)
            try: r[-1] = r[-1] * 10 + c
            except: r.append(c)
        except:
            r.append(c)
    return r
