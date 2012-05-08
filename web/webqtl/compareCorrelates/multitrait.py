# multitrait.py
# a tool to analyze the correlations between several different traits and the traits
# in a given dataset
#
# Parameters:
# correlation -- either "pearson" or "spearman" depending on which ones we want to use 
#
# filename -- an input file containing the traits to analyze
#
# progress -- if set, this parameter outputs a static progress page
# and uses a META redirect to trigger the real computation
#
# targetDatabaseType:
# one of "ProbeSet", "Publish", "Genotype" depending on the type of database
# we will use for the analysis
#
# targetDatabaseId:
# the id (*Freeze.Id in the database) of the particular database we will analyze
#
# threshold -- a float between 0 and 1 to determine which coefficents we wil l consider
#
# firstRun -- either 0 or 1
# whether to automatically pick reasonable defaults for the other three parameters
#
# outputType -- either "html" or "text"
# 
# Author: Stephen Pitts
# June 15, 2004

#Xiaodong changed the dependancy structure

import copy
import sys
import cgi
import os
import os.path
import math
import time
import numarray
import tempfile
import string
import cgitb #all tracebacks come out as HTMLified CGI,useful when we have a random crash in the middle

from base import templatePage
from base.webqtlTrait import webqtlTrait
from utility import webqtlUtil
from base import webqtlConfig
import trait
import correlation
import htmlModule

cgitb.enable()


# where this program's data files are
RootDir = webqtlConfig.IMGDIR # XZ, 09/10/2008: add module name 'webqtlConfig.'
RootDirURL = "/image/" # XZ, 09/10/2008: This parameter is not used in this module

tempfile.tempdir = RootDir
tempfile.template = "multitrait"

# MultitraitException: used if something goes wrong
# maybe in the future we should make exceptions more granular
class MultitraitException(Exception):
    def __init__(self, message):
        self.message = message

    def __repr__(self):
        return "MultitraitException: %s" % self.message

# buildParamDict: Cursor -> ParamDict
# to process and validate CGI arguments
# see the comment at the top of this file for valid cgi
# parameters
def buildParamDict(cursor, fd):
    params = {}
    fs = fd.formdata #cgi.FieldStorage()
    params["progress"] = fs.getfirst("progress", "0")
    params["filename"] = fs.getfirst("filename", "")
    if params["filename"] == "":
        raise MultitraitException("Required parameter filename missing.")

    params["targetDatabase"] = fs.getfirst("targetDatabase", "U74Av2RMA_Raw_ProbeSet_March04")
    params["firstRun"] = webqtlUtil.safeInt(fs.getfirst("firstRun", "0"),0)
    params["threshold"] = webqtlUtil.safeFloat(fs.getfirst("threshold", "0.5"), 0.5)
    params["subsetSize"] = webqtlUtil.safeInt(fs.getfirst("subsetSize", "10"), 10)
    
    if params["subsetSize"] < -1:
        params["subsetSize"] = -1
        
    params["correlation"] = fs.getfirst("correlation", "pearson")
    params["subsetCount"] = webqtlUtil.safeInt(fs.getfirst("subsetCount", 10), 10)
    
    if params["subsetCount"] < -1:
        params["subsetCount"] = -1
        
    #params["outputType"] = fs.getfirst("outputType", "html")
    
    #if params["outputType"] not in ("html", "text"):
    #    params["outputType"] = "html"
    
    if params["correlation"] not in ("pearson", "spearman"):
        params["correlation"] = "pearson"

    params["correlationName"] = params["correlation"].capitalize()

    # one of two cases:
    # 1) We have just come from a submit, so there are a bunch of display*
    #    but no displaySets. Thus, the code down there converts the display*
    #    to displaySets so the GET request doesn't get too long
    # 2) We have just been redirected from a progress page which already has
    #    a converted displaySets for us.

    displaySets = webqtlUtil.safeInt(fs.getfirst("displaySets","0"), 0)

    if displaySets == 0:
        for key in fs.keys():
            if key[:7] == "display":
                #print "Hit display key %s<br>" % key
                try:
                    whichSet = int(key[7:])
                    
                    # prevent malicious attacks
                    whichSet = min(whichSet, 512)
                    displaySets += pow(2, whichSet)
                
                except ValueError: pass

    params["displaySets"] = displaySets
    #print "In the beginning, display sets was %s: %s<br>" % (displaySets,
    #                                                     str(binaryDecompose(displaySets)))

    # if we are just gonna display a progress page, then there's no
    # reason to look up detailed database information
    #if params["progress"] == "1":
    #    return params
    
    a,b = trait.dbNameToTypeId(cursor, params["targetDatabase"]) # XZ, 09/10/2008: add module name
    params["targetDatabaseType"] = a
    params["targetDatabaseId"] = b
    params["targetDatabaseName"] = params["targetDatabase"]

    return params

# readInputFile: DB cursor -> string -> string, (arrayof Trait)
def readInputFile(cursor, filename):
    """
    To read an input file with n lines in the following format
    <databasetype>,<databaseid>,<traitname>
    and retrieve and populate traits with appropriate data
    from the database

    Also, for our purposes. we store the database type and
    database id in fields attached to the trait instances. We use
    this information to generate Javascript popups with trait
    information.

    In addition, we read the strain of mice that the traits are
    from so we can only show those databases to correlate against.
    """
    handle = open(filename)
    line = handle.readline()
    inbredSetName = line.strip()
    line = handle.readline()
    traits = []

# XZ, 09/10/2008: In this while loop block, I changed the original variable name 'trait' to 'oneTrait'
    while line != "":
        line = line.strip()
        dbType, dbId, tName = line.split(",")

        if dbType == "ProbeSet":
            oneTrait = trait.queryProbeSetTraitByName(cursor, tName) # XZ, 09/10/2008: add module name
            oneTrait.populateDataId(cursor, dbId)
            oneTrait.dbName = trait.dbTypeIdToName(cursor, dbType, dbId) # XZ, 09/10/2008: add module name
        elif dbType == "Geno":
            speciesId = trait.getSpeciesIdByDbTypeId(cursor, dbType, dbId)
            oneTrait = trait.queryGenotypeTraitByName(cursor, speciesId, tName) # XZ, 09/10/2008: add module name
            oneTrait.populateDataId(cursor, dbId)
            oneTrait.dbName = trait.dbTypeIdToName(cursor, dbType, dbId) # XZ, 09/10/2008: add module name
        elif dbType == "Publish":
            oneTrait = trait.queryPublishTraitByName(cursor, dbId, tName) # XZ, 09/10/2008: add module name
            oneTrait.populateDataId(cursor, dbId)
            oneTrait.dbName = trait.dbTypeIdToName(cursor, dbType, dbId) # XZ, 09/10/2008: add module name
	elif dbType == "Temp":
	    oneTrait = trait.queryTempTraitByName(cursor, tName) # XZ, 09/10/2008: add module name
            oneTrait.populateDataId(cursor, dbId)
            oneTrait.dbName = "Temp"

        oneTrait.populateStrainData(cursor)
        traits.append(oneTrait)

        line = handle.readline()

    return inbredSetName, traits

# loadDatabase: Cursor -> ParamDict -> arrayof Trait
def loadDatabase(cursor, p):
    """
    To load a set of traits as specified by the
    targetDatabaseId
    and targetDatabaseType parameters

    Cursor should be a fastCursor from the webqtl library (i.e.
    a MySQLdb SSCursor). 
    
    Calling populateStrainData 20,000 or so times on a ProbeSet
    is really inefficent, so I wrote an optimized queryPopulatedProbeSetTraits
    in the trait module that uses a join to get all of the rows in
    bulk, store the resultset on the server, and do all sorts of nice buffering.
    It's about two or three times faster.
    """
    if p["targetDatabaseType"] == "ProbeSet": # XZ, 09/10/2008: add module name 
        dbTraits = trait.queryPopulatedProbeSetTraits(cursor,
                                       p["targetDatabaseId"])
    elif p["targetDatabaseType"] == "Publish": # XZ, 09/10/2008: add module name 
        dbTraits = trait.queryPublishTraits(cursor,
                                      p["targetDatabaseId"])
        psd = trait.PublishTrait.populateStrainData
    elif p["targetDatabaseType"] == "Geno": # XZ, 09/10/2008: add module name 
        dbTraits = trait.queryGenotypeTraits(cursor,
                                       p["targetDatabaseId"])
        psd = trait.GenotypeTrait.populateStrainData
    else:
        print "Unknown target database type %s" % p["targetDatabaseType"]

    if p["targetDatabaseType"] != "ProbeSet":
        map(psd, dbTraits, [cursor]*len(dbTraits))
        
    return dbTraits

def runProbeSetCorrelations(cursor, p, traits):
    """
    To run the correlations between the traits and the database.
    This function computes a correlation coefficent between each
    trait and every entry in the database, and partitions the database
    into a disjoint array of arrays which it returns.

    The length of the return array is 2^n, where n is the length of
    the trait array. Which constitutent element a of the return array
    a given trait ends up in is determined by the following formula
    i = i_02^0 + ... + i_(n-1)2^(n-1)
    where i_0 is 1 if corr(a,trait 0) >= threshold and 0 otherwise

    Since most of the several thousand database traits will end up
    with i=0, we don't return them, so the first element of the
    return array will be empty.

    A particular element of subarray j of the return array contains
    a 2-tuple (trait,kvalues). The variable trait is obviously the
    particular database trait that matches the user traits l_1, ..., l_m
    to which subarray j corresponds. kvalues is a list of the correlation
    values linking trait to l_1, ..., l_m, so the length of kvalues is
    the number of 1s in the binary representation of j (there must be
    a better way to describe this length).

    The return array is an array of 2-tuples. The first element of
    each tuple is the index of the particular subarray, and the second
    element is the subarray itself. The array is sorted in descending
    order by the number of 1's in the binary representation of the
    index so the first few subarrays are the ones that correspond to
    the largest sets. Each subarray is then sorted by the average of
    the magnitude of the individual correlation values.
    """

    kMin = p["threshold"]
    traitArrays = {}

    # TODO: Add Spearman support
    freezeId = p["targetDatabaseId"]
    if p["correlation"] == "pearson":
        correlations = correlation.calcProbeSetPearsonMatrix(cursor, freezeId, traits) #XZ, 09/10/2008: add module name
    else:
        correlations = correlation.calcProbeSetSpearmanMatrix(freezeId, traits) #XZ, 09/10/2008: add module name

    # now we test all of the correlations in bulk
    test = numarray.absolute(correlations)
    test = numarray.greater_equal(test, kMin)
    test = test.astype(numarray.Int8)
    #print test

    db = trait.queryProbeSetTraits(cursor, freezeId) #XZ, 09/10/2008: add module name
    for i in range(len(db)):
        cIndex = 0
        prods = []
        for j in range(len(traits)):
            if test[i,j] == 1:
                cIndex += pow(2, j)
                prods.append(correlations[i,j])
        if cIndex != 0:
            if not traitArrays.has_key(cIndex):
                traitArrays[cIndex] = []

            traitArrays[cIndex].append((db[i], prods))


    # sort each inner list of traitArrays
    # so the matched traits appear in descending order by the
    # average magnitude of the correlation
    def customCmp(traitPair, traitPair2):
        magAvg1 = numarray.average(map(abs, traitPair[1]))
        magAvg2 = numarray.average(map(abs, traitPair2[1]))

        # invert the sign to get descending order
        return -cmp(magAvg1, magAvg2)

    for traitArray in traitArrays.values():
        traitArray.sort(customCmp)

    # sort the outer list of traitArrays
    traitArrays2 = []
    i = 0
    for key in traitArrays.keys():
        a = traitArrays[key]
        if len(a) > 0:
            traitArrays2.append((key,a,len(binaryDecompose(key)),
                                 len(a)))

    # we sort by the number of 1's in the binary output
    # and then by the size of the list, both in descending order
    def customCmp2(aL,bL):
        a = -cmp(aL[2], bL[2])
        if a == 0:
            return -cmp(aL[3], bL[3])
        else:
            return a

    traitArrays2.sort(customCmp2)

    return traitArrays2

def runCorrelations(p, strainCount, traits, db):
    """
    To run the correlations between the traits and the database.
    This function computes a correlation coefficent between each
    trait and every entry in the database, and partitions the database
    into a disjoint array of arrays which it returns.

    The length of the return array is 2^n, where n is the length of
    the trait array. Which constitutent element a of the return array
    a given trait ends up in is determined by the following formula
    i = i_02^0 + ... + i_(n-1)2^(n-1)
    where i_0 is 1 if corr(a,trait 0) >= threshold and 0 otherwise

    Since most of the several thousand database traits will end up
    with i=0, we don't return them, so the first element of the
    return array will be empty.

    A particular element of subarray j of the return array contains
    a 2-tuple (trait,kvalues). The variable trait is obviously the
    particular database trait that matches the user traits l_1, ..., l_m
    to which subarray j corresponds. kvalues is a list of the correlation
    values linking trait to l_1, ..., l_m, so the length of kvalues is
    the number of 1s in the binary representation of j (there must be
    a better way to describe this length).

    The return array is an array of 2-tuples. The first element of
    each tuple is the index of the particular subarray, and the second
    element is the subarray itself. The array is sorted in descending
    order by the number of 1's in the binary representation of the
    index so the first few subarrays are the ones that correspond to
    the largest sets. Each subarray is then sorted by the average of
    the magnitude of the individual correlation values.
    """
    kMin = p["threshold"]
    traitArrays = {}

    # TODO: Add Spearman support
    if p["correlation"] == "pearson":
        correlations = correlation.calcPearsonMatrix(db, traits, strainCount) #XZ, 09/10/2008: add module name
    else:
        correlations = correlation.calcSpearmanMatrix(db, traits, strainCount) #XZ, 09/10/2008: add module name

    # now we test all of the correlations in bulk
    test = numarray.absolute(correlations) 
    test = numarray.greater_equal(test, kMin)
    test = test.astype(numarray.Int8)
    #print test
    

    for i in range(len(db)):
        cIndex = 0
        prods = []
        for j in range(len(traits)):
            if test[i,j] == 1:
                cIndex += pow(2, j)
                prods.append(correlations[i,j])
        if cIndex != 0:
            if not traitArrays.has_key(cIndex):
                traitArrays[cIndex] = []

            traitArrays[cIndex].append((db[i], prods))
                
    # sort each inner list of traitArrays
    # so the matched traits appear in descending order by the
    # average magnitude of the correlation
    def customCmp(traitPair, traitPair2):
        magAvg1 = numarray.average(map(abs, traitPair[1]))
        magAvg2 = numarray.average(map(abs, traitPair2[1]))

        # invert the sign to get descending order
        return -cmp(magAvg1, magAvg2)
    
    for traitArray in traitArrays.values():
        traitArray.sort(customCmp)

    # sort the outer list of traitArrays
    traitArrays2 = []
    i = 0
    for key in traitArrays.keys():
        a = traitArrays[key]
        if len(a) > 0:
            traitArrays2.append((key,a,len(binaryDecompose(key)),
                                 len(a)))

    # we sort by the number of 1's in the binary output
    # and then by the size of the list, both in descending order
    def customCmp2(aL,bL):
        a = -cmp(aL[2], bL[2])
        if a == 0:
            return -cmp(aL[3], bL[3])
        else:
            return a

    traitArrays2.sort(customCmp2)

    return traitArrays2


# XZ, 09/09/2008: In multiple trait correlation result page,
# XZ, 09/09/2008: click "Download a text version of the above results in CSV format"

# TraitCorrelationText: a class to display trait correlations
# as textual output
class TraitCorrelationText:
    # build a text shell to describe the given trait correlations
    # this method sets self.output; use str(self) to actually
    # get the text page
    #
    # traits is a list of traits and traitArray is a
    # list of 3-tuples: index, traits', garbage
    # where index is a binary-encoded description of which subset of
    # traits the list traits' matches
    #
    # traits' is a list of 3-tuples as well: trait, correlations, garbage
    # where trait is a particular trait and correlations is a list of float
    # correlations (matching traits above)
    def __init__(self, p, traits, traitArray):
        output = "Correlation Comparison\n"
        output += "from WebQTL and the University of Tennessee Health Science Center\n"
        output += "initiated at " + time.asctime(time.gmtime()) + " UTC\n\n"
        
        output += self.showOptionPanel(p)
        output += self.showSelectedTraits(traits)
        output += self.showSummaryCorrelationResults(p, traits, traitArray)
        output += self.showDetailedCorrelationResults(p, traits, traitArray)

        self.output = output

    # showOptionPanel: ParamDict -> string
    # to display the options used to run this correlation
    def showOptionPanel(self, params):
        output = "Correlation Comparison Options:\n"
        output += "Target database,%s\n" % params["targetDatabase"]
        output += "Correlation type,%s\n" % params["correlationName"]
        output += "Threshold,%f\n" % params["threshold"]
        #output += "Subsets to Show,%d\n" % params["subsetCount"]
        #output += "Traits to Show Per Subset,%d\n\n" % params["subsetSize"]
        return output

    # showSelectedTraits: (listof Trait) -> string
    # to display the traits compared with the database
    # note: we can't use tabular output because the traits could be of
    # different types and produce different fields
    def showSelectedTraits(self, traits):
        output = "Selected Traits:\n"
        for trait in traits:
            output += '"' + trait.longName() + '"' + "\n"
        output += "\n"
        return output

    # showSummaryCorrelationResults: ParamDict -> (listof Trait) ->
    #    TraitArray -> string
    # see comment for __init__ for a description of TraitArray
    #
    # to show a summary (sets and sizes) of the correlation results
    # as well as an X to indicate whether they will be included
    # in the detailed output
    def showSummaryCorrelationResults(self, p, traits, traitArray):
        output = "Correlation Comparison Summary:\n"

        #if p["subsetCount"] != -1:
        #    ourSubsetCount = min(p["subsetCount"], len(traitArray))
        #else:

        ourSubsetCount = len(traitArray)
            
        displayDecomposition = binaryDecompose(p["displaySets"])
        for j in range(ourSubsetCount):
            i = traitArray[j][0]
            traitSubarray = traitArray[j][1]
            if len(traitSubarray) == 0:
                continue
            
            targetTraits = decomposeIndex(traits, i)
            traitDesc = string.join(map(trait.Trait.shortName, targetTraits), # XZ, 09/10/2008: add module name
                                    ", ")
            if j in displayDecomposition:
                checked = "X"
            else:
                checked = ""

            output += '"%s","%s","%d"\n' % (checked, traitDesc, len(traitSubarray))

        output += "\n"
        return output

    # showDetailedCorrelationResults: ParamDict -> (listof Trait) ->
    #   TraitArray -> string
    #
    # to show a detailed list of the correlation results; that is,
    # to completely enumerate each subset of traitArray using the
    # filtering parameters in p
    def showDetailedCorrelationResults(self, p, traits, traitArray):
        output = "Correlation Comparison Details:\n"
        displayDecomposition = binaryDecompose(p["displaySets"])
        displayDecomposition.sort()

        def formatCorr(c):
            return "%.4f" % c
        
        for j in displayDecomposition:
            i = traitArray[j][0]
            traitSubarray = traitArray[j][1]

            if len(traitSubarray) == 0:
                continue

            targetTraits = decomposeIndex(traits, i)
            extraColumnHeaders = map(trait.Trait.shortName, targetTraits) # XZ, 09/10/2008: add module name
            traitDesc = string.join(extraColumnHeaders, ", ")

            #if(p["subsetSize"] != -1 and len(traitSubarray) > p["subsetSize"]):
            #    traitDesc += ",(showing top %s of %s)" % (p["subsetSize"],
            #                                             len(traitSubarray))
            #    traitSubarray = traitSubarray[0:p["subsetSize"]]

            output += "%s\n" % traitDesc
            output += traitSubarray[0][0].csvHeader([], extraColumnHeaders)
            output += "\n"
            for oneTrait, corr in traitSubarray:#XZ, 09/10/2008: change original variable name 'trait' to 'oneTrait'
                corr = map(formatCorr, corr)
                output += oneTrait.csvRow([], corr) + "\n"

            output += "\n"
        
        return output

    # __str__ : string
    # to return self.output as the string representation of this page
    # self.output is built in __init__
    def __str__(self):
        return self.output

# TraitCorrelationPage: a class to display trait correlations
# for now this is just one HTML file, so we don't even write it
# to a temporary file somewhere
class TraitCorrelationPage(templatePage.templatePage):
    """
    Using the templatePage class, we build an HTML shell for
    the core data here: the trait correlation lists.

    The way templatePage works, we build the page in pieces in
    the __init__ method and later on use the inherited write
    method to render the page.
    """
    def __init__(self, fd, p, cursor, traits, traitArray, inbredSetName, txtFilename):

        templatePage.templatePage.__init__(self, fd)
         
        self.dict["title"] = "Correlation Comparison"
        self.dict["basehref"] = ""
		# NL: deleted js1 content part, since it has not been used in this project
        self.dict["js1"] = ""
        self.dict["js2"] = ""

        body = "<td><h1>Correlation Comparison</h1>"
        body += "<p>Run at %s UTC</p>" % time.asctime(time.gmtime())
        body += """
        <p>The correlation comparison tool identifies intersecting sets of traits that are
correlated with your selections at a specified threshold. A correlation comparison 
involves the following steps:</p>
<ol>
<li><p>
<b>Correlate:</b> 
Choose a <i>Target Database</i>, a <i>Correlation Type</i>, and a <i>Correlation
Threshold</i>. For your initial correlation, leave <i>Number of Subsets to Show</i> and 
<i>Traits to Show per Subset</i> at their default values of 10. Using the Correlation 
Options panel, you can adjust the <i>Correlation Threshold</i>, <i>Number of Subsets to
Show</i>, and <i>Traits to Show per Subset</i>.
</p></li>

<li><p>
<b>Add to Collection:</b>
You can use the check boxes in the <i>Correlation 
Comparison Details</i> panel and the buttons at the bottom of the page to add these
results to your selections page for further analysis in WebQTL.
</p></li>

<li><p> 
<b>Filter:</b>
Using the <i>Correlation Comparison Summary</i> panel, choose which
subsets you would like to display for export. Note that if you change the
parameters in the <i>Correlation Options</i> panel, you will need to re-apply your filter.
</p></li>

<li><p>
<b>Export:</b>
Once you are satisfied with your report, use the export link at
the bottom of the page to save the report as a comma-separated (CSV) text file
which you can then import into Excel or another tool. Note: the exported report
will list all subsets in the summary view and only those traits in the subsets
you have selected in the Filter step.
</p></li>
</ol>
"""
        
#        body += """
#        <p>The correlation
#        comparison tool identifies the intersecting sets of traits that are
#        correlated with your selections. A correlation comparison involves
#        the following steps:</p>
#        <ol>
#        <li><p><b>Correlate:</b> Choose a <i>Target Database</i>, a <i>Correlation Type</i>, and a <i>Correlation Threshold</i>.
#        For the initial correlation, leave <i>Subsets to Show</i> and <i>Traits to Show per Subset</i>
#        at their default values of 10.</p></li>
#        <li><p><b>Refine Correlation:</b> Using the <i>Correlation Options</i> panel,
#        adjust the <i>Correlation Threshold</i>, <i>Subsets to Show</i>, and <i>Traits to
#        Show per Subset</i> until you have a reasonable number of traits.</p></li>
#        <li><p><b>Filter:</b> Using the <i>Correlation Comparison Summary</i> panel, choose which subsets you would
#        like to see. Note that if you change the parameters in the <i>Correlation Options</i> panel, you will
#        loose the filter you have selected.</p></li>
#        <li><p><b>Export:</b> Once you are satisfied with your report, use the export
#        link at the bottom of the page to save the report as a comma-separated (CSV) text file which
#        you can then import into Excel or another tool. Note: the exported report
#        will show all subsets in the summary view and all traits in each subset you have
#        selected in the Filter step.
#        <li><p><b>Shopping Cart:</b> In addition, you can use the
#        check boxes in the <i>Correlation Comparison Details</i> panel and the
#        buttons at the bottom of the page to add the traits you have found to the shopping cart.</p>
#        </li>
#        </ol>
#        """

        body += self.showOptionPanel(p, cursor, inbredSetName)        
        body += self.showSelectedTraits(traits, p, inbredSetName)

        if p["firstRun"] == 0:
            body += self.showCorrelationResults(p, inbredSetName, traits, traitArray)

            exportParams = copy.copy(p)
            exportParams["outputType"] = "text"
            
            body += ('''
            <h2>Export these results</h2>
            <p>
            <a href="/image/%s">Download a text version of the above results in CSV format</a>. This text version differs from
            the version you see on this page in two ways. First, the summary view shows all subsets. Second, the details
            view shows all traits in the subsets that you have selected.
            </p>
            '''
                     % txtFilename)


        
        body += "</td>"
        self.dict["body"] = body


    # showOptionPanel: ParamDict -> Cursor -> String ->  String
    # to build an option panel for the multitrait correlation
    # we expect the database list to be a list of 2-tuples
    # the first element of each tuple is the short name
    # and the second element of the tuple is the long name
    def showOptionPanel(self, params, cursor, inbredSetName):
        output = '''
        <h2>Correlation Options</h2>
	<FORM METHOD="POST" ACTION="%s%s" ENCTYPE="multipart/form-data">
	<INPUT TYPE="hidden" NAME="FormID" VALUE="compCorr2">
        <input type="hidden" name="filename" value="%s">
        <input type="hidden" name="firstRun" value="0">
        <input type="hidden" name="progress" value="1">
        <table>
        <tr>
        <td>Target Database:</td><td>
        ''' % (webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE, params["filename"])

        output += htmlModule.genDatabaseMenu(db = cursor,
                                  public=0,
                                  RISetgp = inbredSetName,
                                  selectname="targetDatabase",
                                  selected=params["targetDatabase"])
        output += "</td></tr>"

        corrSelected = ["",""]

        if params["correlation"] == "pearson":
            corrSelected[0] = "SELECTED"
        else:
            corrSelected[1] = "SELECTED"
        
        output += ('''
                   <tr>
                   <td>Correlation Method:</td>
                   <td><select name="correlation">
                       <option value="pearson" %s>Pearson</option>
                       <!--<option value="spearman" %s>Spearman</option>-->
                       </select></td></tr>
                       ''' % (corrSelected[0], corrSelected[1]))
        output += ('<tr><td>Correlation Threshold:</td><td><input name="threshold" value="%s" /></td></tr>'
                   % params["threshold"])
        output += ('<tr><td>Subsets to Show (-1 to show all subsets):</td><td><input name="subsetCount" value="%s" /></td></tr>'
                   % params["subsetCount"])
        output += ('<tr><td>Traits to Show per Subset (-1 to show all traits):</td><td><input name="subsetSize" value="%s" /></td></tr>'
                   % params["subsetSize"])

        # a cosmetic change to hopefully make this form a bit easier to use
#        if params["firstRun"] == 1:
#            applyName = "Correlate"
#        else:
#            applyName = "Refine Correlation"
            
        output += '''
        <tr>
        <td colspan="2"><input class="button" type="submit" value="Correlate" /></td>
        </tr>
        </table>
        </form>
        ''' 

        return output

    # showSelectedTraits: listof Trait -> string
    # to show a list of the selected traits
    def showSelectedTraits(self, traits, p, inbredSetName):
        output = '''
		<form action="%s%s" method="post" name="showDatabase">
		<INPUT TYPE="hidden" NAME="FormID" VALUE="showDatabase">

		<input type="hidden" name="incparentsf1" value="ON">
		<input type="hidden" name="ShowStrains" value="ON">
		<input type="hidden" name="ShowLine" value="ON">
		<input type="hidden" name="database" value="">
		<input type="hidden" name="ProbeSetID" value="">
		<input type="hidden" name="RISet" value="%s">
		<input type="hidden" name="CellID" value="">
		<input type="hidden" name="database2" value="">
		<input type="hidden" name="rankOrder" value="">
		<input type="hidden" name="ProbeSetID2" value="">
		<input type="hidden" name="CellID2" value="">
		''' % (webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE, inbredSetName)

        output += "<h2>Selected Traits</h2>"        
        output += '<table cellpadding="2" cellspacing="0"><tr bgcolor="FFFFFF"><th>Database</th><th>Trait</th></tr>'
        flip = 1
        colors = ["FFFFFF", "cccccc"]
        
        for trait in traits:
            # we take advantage of the secret dbName attribute that
            # loadDatabase fills in
            descriptionString = trait.genHTML()
            if trait.db.type == 'Publish' and trait.confidential:
                descriptionString = trait.genHTML(privilege=self.privilege, userName=self.userName, authorized_users=trait.authorized_users)
            output += '''
            <tr bgcolor="%s"><td><a href="/dbdoc/%s.html">%s</a></td>
                <td><a href="javascript:showDatabase2('%s', '%s', '')">%s</a></td>
                </tr>
            ''' % (colors[flip], trait.db.name, trait.db.name, trait.db.name, trait.name, descriptionString)
            flip = not flip

        output += "</table></form>"
        return output


    # showSummaryCorrelationResults
    # show just the number of traits in each subarray
    def showSummaryCorrelationResults(self, p, traits, traitArray):
        output = '''
        <form action="%s%s" method="post">
	<INPUT TYPE="hidden" NAME="FormID" VALUE="compCorr2">
        <input type="hidden" name="filename" value="%s">
        <input type="hidden" name="firstRun" value="0">
        <input type="hidden" name="progress" value="1">
        <input type="hidden" name="correlation" value="%s">
        <input type="hidden" name="threshold" value="%s">
        <input type="hidden" name="rankOrder" value="">
        <input type="hidden" name="subsetCount" value="%s">
        <input type="hidden" name="subsetSize" value="%s">
        <input type="hidden" name="targetDatabase" value="%s">
        ''' % (webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE, p["filename"], p["correlation"], p["threshold"],
               p["subsetCount"], p["subsetSize"], p["targetDatabase"])
        
        output += '''
        <table cellpadding="2" cellspacing="0">
        <tr>
        <th>Trait Subsets</th>
        <th colspan="2">Intersecting Set Size</th>
        </tr>
        '''
        # figure out a scale for the summary graph
        # for now we set max = 300 pixels wide
        if p["subsetCount"] != -1:
            ourSubsetCount = min(p["subsetCount"], len(traitArray))
        else:
            ourSubsetCount = len(traitArray)
            
        screenWidth = 600
        lengths = []
        for j in range(ourSubsetCount):
            lengths.append(len(traitArray[j][1]))
        maxLength = max(lengths)
        
        displayDecomposition = binaryDecompose(p["displaySets"])
        flip = 0
        colors = ["FFFFFF", "cccccc"]
        
        for j in range(ourSubsetCount):
            i = traitArray[j][0]
            traitSubarray = traitArray[j][1]
            
            if len(traitSubarray) == 0:
                continue

            targetTraits = decomposeIndex(traits, i)
            traitDesc = string.join(map(webqtlTrait.displayName, targetTraits),
                                    ", ")
            
            if j in displayDecomposition:
                checked = "CHECKED"
            else:
                checked = ""

            barWidth = (len(traitSubarray) * screenWidth) / maxLength
            output += ('''<tr bgcolor="%s">
                              <td><input type="checkbox" name="display%d" value="1" %s>%s</input></td>
                              <td>%s</td>
                              <td><img src="/images/blue.png" width="%d" height="25"></td></tr>'''
                       % (colors[flip], j, checked, traitDesc, len(traitSubarray), barWidth))
            flip = not flip
            
        output += '''
        <tr>
        <td colspan="3">
        <input class="button" type="submit" value="Filter" /></td>
        </tr>
        </table></form>
        '''
        return output
    
    # showDetailedCorrelationResults
    # actually show the traits in each subarray
    def showDetailedCorrelationResults(self, p, inbredSetName, traits,
                                       traitArray):
        output = "<h2>Correlation Comparison Details</h2>"

        # the hidden form below powers all of the JavaScript links,
        # the shopping cart links, and the correlation plot links

        output += '''
        <form action="%s%s" method="post">
        <input type="hidden" name="database" value="%s">
        <input type="hidden" name="FormID" value="showDatabase">
        <input type="hidden" name="traitfile" value="">
	<input type="hidden" name="incparentsf1" value="ON">
	<input type="hidden" name="ShowStrains" value="ON">
        <input type="hidden" name="ProbeSetID" value="">
	<input type="hidden" name="ShowLine" value="ON">
        <input type="hidden" name="RISet" value="%s">
        <input type="hidden" name="CellID" value="">
        <input type="hidden" name="database2" value="">
        <input type="hidden" name="rankOrder" value="">
        <input type="hidden" name="ProbeSetID2" value="">
        <input type="hidden" name="CellID2" value="">
        ''' % (webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE, p["targetDatabase"], inbredSetName)


        displayDecomposition = binaryDecompose(p["displaySets"])

        # necessary to ensure that subset order is the same in the
        # summary and the detailed view
        displayDecomposition.sort()

        # here's a trick: the first trait we show must have the widest row because it correlates
        # with the largest set of input traits
        firstSubset = traitArray[displayDecomposition[0]]
        firstTrait = firstSubset[1][0][0]
        extraColumnCount = firstSubset[2]
        totalColumnCount = 1 + len(firstTrait.row()) + extraColumnCount

        output += "<table cellpadding=2 cellspacing=0>\n"
        for j in displayDecomposition:
            i = traitArray[j][0]
            traitSubarray = traitArray[j][1]

            # we don't display trait combinations for which there are
            # no correlations
            if len(traitSubarray) == 0:
                continue
            
            # generate a description of the traits that this particular array
            # matches highly
            targetTraits = decomposeIndex(traits, i)
            extraColumnHeaders = map(webqtlTrait.displayName, targetTraits)
            traitDesc = string.join(extraColumnHeaders, ", ")

            # massage extraColumnHeaders so that they can be wrapped
            for i in range(len(extraColumnHeaders)):
                ech = extraColumnHeaders[i]
                ech = ech.replace("-", " ")
                ech = ech.replace("_", " ")
                extraColumnHeaders[i] = ech

            # pad extraColumnHeaders if we have less columns than the max
            paddingNeeded = extraColumnCount - len(extraColumnHeaders)
            if paddingNeeded > 0:
                extraColumnHeaders.extend(paddingNeeded * ["&nbsp;"])
                    
            # we limit the output to the top ones
            if(p["subsetSize"] != -1 and len(traitSubarray) > p["subsetSize"]):
                traitDesc += " (showing top %s of %s)" % (p["subsetSize"], len(traitSubarray))
                traitSubarray = traitSubarray[0:p["subsetSize"]]
                
            # combine that description with actual database traits themselves
            # and the correlation values
            output += '<tr><td colspan="%d"><h3>%s</h3></td></tr>' % (totalColumnCount, traitDesc)
            #output += '<h3>%s</h3>\n<table cellpadding=2 cellspacing=0>\n'% traitDesc

            # we assume that every trait in traitSubarray is the same type
            # of trait
            flip = 0
            colors = ["FFFFFF", "cccccc"]
            
            output += traitSubarray[0][0].tableRowHeader(["&nbsp;"], extraColumnHeaders, colors[0])

            for traitPair in traitSubarray:
                corr = []
		traitPair[0].dbName = p['targetDatabase']
                trait = traitPair[0]

                for i in range(len(traitPair[1])):
                    corrValue = traitPair[1][i]
                    corrPlotLink = ('''
                    <a href="javascript:showCorrelationPlot2(db='%s',ProbeSetID='%s',CellID='',db2='%s',ProbeSetID2='%s',CellID2='',rank='%s')">%.2f</a>
                    ''' % (p["targetDatabaseName"], trait.name,  targetTraits[i].db.name, targetTraits[i].name, "0", corrValue))
                    corr.append(corrPlotLink)
    
                corr.extend(paddingNeeded * ["&nbsp;"])
                    
                checkbox = ('<INPUT TYPE="checkbox" NAME="searchResult" VALUE="%s:%s" />'
                            % (p["targetDatabaseName"], trait.name))
                flip = not flip
                output += traitPair[0].tableRow([checkbox], corr, colors[flip])
            
            #output += "</table>"
            i += 1
            output += '<tr><td colspan="%d">&nbsp;</td></tr>' % totalColumnCount

        output += "</table>"

        # print form buttons if there were checkboxes above
        output += '''
        <div align="left">
        <INPUT TYPE="button" NAME="addselect" CLASS="button" VALUE="Add to Collection"
        onClick="addRmvSelection('%s',this.form, 'addToSelection');">
        <INPUT TYPE="button" NAME="selectall" CLASS="button" VALUE="Select All" onClick="checkAll(this.form);">
        <INPUT TYPE="reset" CLASS="button" VALUE="Select None">
        </div>
        </form>
        ''' % inbredSetName

        return output
    
    # showCorrelationResults: ParamDict -> listof Trait -> tupleof (int,arrayof trait) -> String
    # to build an output display for the multitrait correlation results
    def showCorrelationResults(self, p, inbredSetName, traits, traitArray):
        output = '''
        <h2>Correlation Comparison Summary</h2>
        <p>
        %s correlations were computed for each of the selected traits with each trait in
        the <a href="/dbdoc/%s.html">%s</a> database.
        Subsets of database traits for which correlations were higher than %s
        or lower than -%s are shown below based on which traits
        they correlated highly with. The top %s subsets, ranked by the number of input traits that
        they correspond with, are shown, and at most %s traits in each subset are shown. </p>
        ''' % (p["correlationName"],
               p["targetDatabase"], p["targetDatabaseName"],
               p["threshold"], p["threshold"], p["subsetCount"],
               p["subsetSize"])


        totalTraits = 0
        for j in range(len(traitArray)):
            totalTraits += len(traitArray[j][1])
                        
        if totalTraits == 0:
            output += """
            <p>
            No shared corrrelates were found with your given traits at this
            threshold. You may wish to lower the correlation threshold or choose different traits.
            </p>
            """
        else:
            output += self.showSummaryCorrelationResults(p, traits, traitArray)
            output += self.showDetailedCorrelationResults(p, inbredSetName,
                                                          traits, traitArray)

        return output

# decomposeIndex: (listof Trait) -> Int ->
#   (listof Trait)
# to use i to partition T into a sublist
# each bit in i controls the inclusion or exclusion of a trait
def decomposeIndex(traits, i):
    targetTraits = []
    
    for j in range(len(traits)):
        # look, mom, a bitwise and!
        # expression below tests whether the jth bit is
        # set in i
        # see runCorrelation for how we decompose the
        # array index
        if (i & pow(2,j)) == pow(2,j):
            targetTraits.append(traits[j])

    return targetTraits
    
# binaryDecompose: int -> (listof int)
# to decompose a number into its constituent powers of 2
# returns a list of the exponents a_1...a_n such that the input m
# is m = 2^a_1 + ... + 2^a_n
def binaryDecompose(n):
    if n == 0:
        return []

    # we start with the highest power of 2 <= this number
    # and work our way down, subtracting powers of 2
    start = long(math.floor(math.log(n)/math.log(2)))
    
    exponents = []
    while start >= 0:
        if n >= long(math.pow(2, start)):
            n -= math.pow(2,start)
            exponents.append(start)
        start -= 1
    return exponents

# powerOf : int -> int -> boolean
# to determine whether m is a power of n;
# more precisely, whether there exists z in Z s.t.
# n^z = m
def powerOf(m, n):
    trialZ = math.floor(math.log(m)/math.log(n))
    return pow(n,trialZ) == m


class compCorrPage(templatePage.templatePage):
	def __init__(self,fd):
		templatePage.templatePage.__init__(self, fd)

                if not self.openMysql():
                        return

		cursor = self.cursor
		params = buildParamDict(cursor, fd)

		# get the input data
		inbredSetName, traits = readInputFile(cursor, RootDir + params["filename"])
        
		# and what we are comparing the data to
		dbTraits = []
		if params["targetDatabaseType"] != "ProbeSet":
			dbTraits = loadDatabase(cursor, params)

        
		# run the comparison itself
		strainCount = trait.queryStrainCount(cursor) # XZ, 09/10/2008: add module name 
		if params["targetDatabaseType"] == "ProbeSet":
			results = runProbeSetCorrelations(cursor, params, traits)
		else:
			results = runCorrelations(params, strainCount, traits, dbTraits)

		# try to be smart about what to output:
		# we want to limit the number of traits shown, at least initially
		# and since traitArray is already sorted with most interesting
		# subsets first, we simply pick up the first 500 or so traits
		# that we find
		if params["displaySets"] == 0:
			selectedTraits = 0
			for j in range(len(results)):
				#print "Scanning subarray %d" % j
				if selectedTraits <= 200:
					params["displaySets"] += pow(2, j)
					selectedTraits += len(results[j][1])

		traitList = []
		for oneTrait in traits:  # XZ, 09/10/2008: change the original variable name 'trait' to 'oneTrait'
			traitName = oneTrait.dbName+'::'+oneTrait.name  # XZ, 09/10/2008: change the original variable name 'trait' to 'oneTrait'
			aTrait =  webqtlTrait(cursor=self.cursor, fullname=traitName)
			traitList.append(aTrait)

		# and generate some output
		txtOutputFilename = tempfile.mktemp() 
		txtOutputHandle = open(txtOutputFilename, "w")
		txtOutput = TraitCorrelationText(params, traits, results)
		txtOutputHandle.write(str(txtOutput))
		txtOutputHandle.close()
		txtOutputFilename = os.path.split(txtOutputFilename)[1]

		self.dict['body'] = TraitCorrelationPage(fd, params, cursor, traitList,
					results, inbredSetName,
					txtOutputFilename).dict['body']
