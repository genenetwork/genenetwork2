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

# graphviz:
# a library for sending trait data to the graphviz utilities to get
# graphed

# ParamDict: a dictionary of strings that map to strings where the keys are
#     valid parameters and the values are validated versions of those parameters
#
# The list below also works for visualize.py; different parameters apply to different
# functions in the pipeline. See visualize.py for more details.
#
# parameters:
# filename: an input file with comma-delimited data to visualize
# kValue:
#    how to filter the edges; edges with correlation coefficents in
#    [-k, k] are not drawn
# whichValue: which of the two correlation coefficents are used;
#     0 means the top half (pearson) and
#     1 means the bottom half (spearman)
# width: the width of the graph in inches
# height: the height of the graph in inches
# --scale: an amount to multiply the length factors by to space out the nodes
# spline: whether to use splines instead of straight lines to draw graphs
# tune: whether to automatically pick intelligent default values for
#     kValue and spline based on the number of edges in the input data
# whichVersion: whether to display the graph zoomed or fullscreen
#     0 means zoom
#     1 means fullscreen
# printIslands: whether to display nodes with no visible edges
# 

# DataMatrix: a one-dimensional array of DataPoints in sorted order by i first



import copy
import os
#import os.path
import math
import string

from base import webqtlConfig
from utility import webqtlUtil
#import trait
from nGraphException import nGraphException
from ProcessedPoint import ProcessedPoint


# processDataMatrix: DataMatrix -> ParamDict -> void
# this is the second part after filterDataMatrix
# To process the set of points in a DataMatrix as follows
#    1) choose an appropriate color for the data point
#    2) filter those between k values
#    3) to use an r-to-Z transform to spread out the correlation
#       values from [-1,1] to (-inf, inf)
#    4) to invert the values so that higher correlations result in
#       shorter edges
#
# Note: this function modifies the matrix in-place. My functional
# programming instincts tell me that this is a bad idea.
def processDataMatrix(matrix, p):
    for pt2 in matrix:
        # filter using k
        if (-p["kValue"] <= pt2.value) and (pt2.value <= p["kValue"]):
            pt2.value = 0.00
            
        # Lei Yan
        # 05/28/2009
        # fix color
        
        # pick a color
        if pt2.value >= 0.7:
            pt2.color = p["cL6Name"]
            pt2.style = p["L6style"]
        elif pt2.value >= 0.5:
            pt2.color = p["cL5Name"]
            pt2.style = p["L5style"]
        elif pt2.value >= 0.0:
            pt2.color = p["cL4Name"]
            pt2.style = p["L4style"]
        elif pt2.value >= -0.5:
            pt2.color = p["cL3Name"]
            pt2.style = p["L3style"]
        elif pt2.value >= -0.7:
            pt2.color = p["cL2Name"]
            pt2.style = p["L2style"]
        else:
            pt2.color = p["cL1Name"]
            pt2.style = p["L1style"]
        
        # r to Z transform to generate the length
        # 0 gets transformed to infinity, which we can't
        # represent here, and 1 gets transformed to 0
        if p["lock"] == "no":
            if -0.01 < pt2.value and pt2.value < 0.01:
                pt2.length = 1000
            elif pt2.value > 0.99 or pt2.value < -0.99:
                pt2.length = 0
            else:
                pt2.length = pt2.value
                pt2.length = 0.5 * math.log((1 + pt2.length)/(1 - pt2.length))
        
                # invert so higher correlations mean closer edges
                #pt2.length = abs(p["scale"] * 1/pt2.length)
                pt2.length = abs(1/pt2.length)
        else:
            pt2.length = 2
            

# tuneParamDict: ParamDict -> Int -> Int -> ParamDict
# to adjust the parameter dictionary for a first-time run
# so that the graphing doesn't take so long, especially since
# small parameter changes can make a big performance difference
# note: you can pass this function an empty dictionary and
# get back a good set of default parameters for your
# particular graph
def tuneParamDict(p, nodes, edges):
    newp = copy.deepcopy(p)
    
    if nodes > 50:
        newp["splines"] = "no"
    else:
        newp["splines"] = "yes"
        
    if edges > 1000:
        newp["printIslands"] = 0
    else:
        newp["printIslands"] = 1
        
    if edges > 1000:
        newp["kValue"] = 0.8
    elif edges > 500:
        newp["kValue"] = 0.7
    elif edges > 250:
        newp["kValue"] = 0.6

    if nodes > 50:
        # there's no magic here; this formula
        # just seems to work
        dim = 3*math.sqrt(nodes)
        newp["width"] = round(dim,2)
        newp["height"] = round(dim,2)

        # the two values below shouldn't change 
        #        newp["scale"] = round(dim/10.0,2)
        #        newp["fontsize"] = round(14*newp["scale"],0)
        
    else:
        newp["width"] = 40.0
        newp["height"] = 40.0
        
    return newp

# fixLabel : string -> string
def fixLabel(lbl):
    """
    To split a label with newlines so it looks a bit better
    Note: we send the graphing program literal '\n' strings and
    it converts these into newlines
    """
    lblparts = lbl.split(" ")
    newlbl = ""
    i = 0
    for part in lblparts:
        if 10*(i+1) < len(newlbl):
            i += 1
            newlbl = newlbl + r"\n" + part
        else:
            newlbl = newlbl + " " + part
    return newlbl
    #return "\N"

def writeGraphFile(matrix, traits, filename, p):
    """
    Expresses the same information as the neato file, only in 
    eXtensible Graph Markup and Modeling Language (XGMML) so the user can develop his/her
    own graph in a program such as Cytoscape
    """
    inputFile1 = open(filename + "_xgmml_symbol.txt", "w")
    inputFile2 = open(filename + "_xgmml_name.txt", "w")
    inputFile3 = open(filename + "_plain_symbol.txt", "w")
    inputFile4 = open(filename + "_plain_name.txt", "w")
        
    inputFile1.write("<graph directed=\"1\" label=\"Network Graph\">\n")
    inputFile2.write("<graph directed=\"1\" label=\"Network Graph\">\n")
    
    #Write out nodes
    traitEdges = []
    for i in range(0, len(traits)):
        traitEdges.append(0)
    
    for i in range(0, len(traits)):
            
        labelName = traits[i].symbol
        inputFile1.write("\t<node id=\"%s\" label=\"%s\"></node>\n" % (i, labelName))
    
    for i in range(0, len(traits)):
        
        labelName = traits[i].name
        inputFile2.write("\t<node id=\"%s\" label=\"%s\"></node>\n" % (i, labelName))
            
    #Write out edges
    for point in matrix:

        traitEdges[point.i] = 1
        traitEdges[point.j] = 1
        if p["edges"] == "complex":
            _traitValue = "%.3f" % point.value
            inputFile1.write("\t<edge source=\"%s\" target=\"%s\" label=\"%s\"></edge>\n"
                             % (point.i,
                                point.j, 
                                _traitValue))
            inputFile2.write("\t<edge source=\"%s\" target=\"%s\" label=\"%s\"></edge>\n"
                             % (point.i,
                                point.j, 
                                _traitValue))
    
    inputFile1.write("</graph>")
    inputFile2.write("</graph>")
            
    for edge in matrix:
        inputFile3.write("%s\t%s\t%s\n" % (traits[edge.i].symbol, edge.value, traits[edge.j].symbol))    
    

    for edge in matrix:
        inputFile4.write("%s\t%s\t%s\n" % (traits[edge.i].name, edge.value, traits[edge.j].name))         
                
    inputFile1.close()
    inputFile2.close()
    inputFile3.close()
    inputFile4.close()
    
    return (os.path.split(filename))[1]

# writeNeatoFile : DataMatrix -> arrayof Traits -> String -> ParamDict -> String
def writeNeatoFile(matrix, traits, filename, GeneIdArray, p):
    """
    Given input data, to write a valid input file for neato, optionally
    writing entries for nodes that have no edges.
    
    NOTE: There is a big difference between removing an edge and zeroing
    its value. Because writeNeatoFile is edge-driven, zeroing an edge's value
    will still result in its node being written.
    """
    inputFile = open(filename, "w")
    
    """
    This file (inputFile_pdf) is rotated 90 degrees. This is because of a bug in graphviz 
    that causes pdf output onto a non-landscape layout to often be cut off at the edge
    of the page. This second filename (which is just the first + "_pdf" is then read
    in the "visualizePage" class in networkGraph.py and used to generate the postscript
    file that is converted to pdf.
    """
    inputFile_pdf = open(filename + "_pdf", "w")
    
    
    if p["splines"] == "yes":
        splines = "true"
    else:
        splines = "false"
    
    # header        
    inputFile.write('''graph webqtlGraph {
    overlap="false";
    start="regular";
    splines="%s";
    ratio="auto";
    fontpath = "%s";
    node [fontname="%s", fontsize=%s, shape="%s"];
    edge [fontname="%s", fontsize=%s];
    ''' % (splines, webqtlConfig.PIDDLE_FONT_PATH,
           p["nfont"], p["nfontsize"], p["nodeshapeType"],
           p["cfont"], p["cfontsize"]))
    
    inputFile_pdf.write('''graph webqtlGraph {
    overlap="false";
    start="regular";
    splines="%s";
    rotate="90";
    center="true";
    size="11,8.5";
    margin="0";
    ratio="fill";
    fontpath = "%s";
    node [fontname="%s", fontsize=%s, shape="%s"];
    edge [fontname="%s", fontsize=%s];
    ''' % (splines, webqtlConfig.PIDDLE_FONT_PATH,
           p["nfont"], p["nfontsize"], p["nodeshapeType"],
           p["cfont"], p["cfontsize"]))

    # traitEdges stores whether a particular trait has edges
    traitEdges = []
    for i in range(0, len(traits)):
        traitEdges.append(0)
       
    if p["dispcorr"] == "yes":
        _dispCorr = 1
    else:
        _dispCorr = 0
    # print edges first while keeping track of nodes
    for point in matrix:
        if point.value != 0:
            traitEdges[point.i] = 1
            traitEdges[point.j] = 1
            if p["edges"] == "complex":
                if _dispCorr:
                    _traitValue = "%.3f" % point.value
                else:
                    _traitValue = ""
                if p["correlationName"] == "Pearson":
                    inputFile.write('%s -- %s [len=%s, weight=%s, label=\"%s\", color=\"%s\", style=\"%s\", edgeURL=\"javascript:showCorrelationPlot2(db=\'%s\',ProbeSetID=\'%s\',CellID=\'\',db2=\'%s\',ProbeSetID2=\'%s\',CellID2=\'\',rank=\'%s\');\", edgetooltip="%s"];\n'
                                    % (point.i,
                                       point.j, 
                                       point.length,
                                       point.length, 
                                       _traitValue,
                                       point.color,
                                       point.style,
                                       str(traits[point.i].datasetName()),
                                       str(traits[point.i].nameNoDB()),
                                       str(traits[point.j].datasetName()),
                                       str(traits[point.j].nameNoDB()),
                                       "0",
    				                   "Pearson Correlation Plot between " + str(traits[point.i].symbol) + " and " + str(traits[point.j].symbol)))
                elif p["correlationName"] == "Spearman":
                    inputFile.write('%s -- %s [len=%s, weight=%s, label=\"%s\", color=\"%s\", style=\"%s\", edgeURL=\"javascript:showCorrelationPlot2(db=\'%s\',ProbeSetID=\'%s\',CellID=\'\',db2=\'%s\',ProbeSetID2=\'%s\',CellID2=\'\',rank=\'%s\');\", edgetooltip="%s"];\n'
                                    % (point.i,
                                       point.j, 
                                       point.length,
                                       point.length, 
                                       _traitValue,
                                       point.color,
                                       point.style,
                                       str(traits[point.j].datasetName()),
                                       str(traits[point.j].nameNoDB()),
                                       str(traits[point.i].datasetName()),
                                       str(traits[point.i].nameNoDB()),
                                       "1",
                                       "Spearman Correlation Plot between " + str(traits[point.i].symbol) + " and " + str(traits[point.j].symbol)))    
                elif p["correlationName"] == "Tissue":
                    inputFile.write('%s -- %s [len=%s, weight=%s, label=\"%s\", color=\"%s\", style=\"%s\", edgeURL=\"javascript:showTissueCorrPlot(fmName=\'showDatabase\', X_geneSymbol=\'%s\', Y_geneSymbol=\'%s\', rank=\'0\');\", edgetooltip="%s"];\n'
                                    % (point.i,
                                       point.j, 
                                       point.length,
                                       point.length, 
                                       _traitValue,
                                       point.color,
                                       point.style,
                                       str(traits[point.i].symbol),
                                       str(traits[point.j].symbol),
                                       "Tissue Correlation Plot between " + str(traits[point.i].symbol) + " and " + str(traits[point.j].symbol)))      
                else:
                    inputFile.write('%s -- %s [len=%s, weight=%s, label=\"%s\", color=\"%s\", style=\"%s\", edgeURL=\"javascript:showCorrelationPlot2(db=\'%s\',ProbeSetID=\'%s\',CellID=\'\',db2=\'%s\',ProbeSetID2=\'%s\',CellID2=\'\',rank=\'%s\');\", edgetooltip="%s"];\n'
                                    % (point.i,
                                       point.j, 
                                       point.length,
                                       point.length, 
                                       _traitValue,
                                       point.color,
                                       point.style,
                                       str(traits[point.i].datasetName()),
                                       str(traits[point.i].nameNoDB()),
                                       str(traits[point.j].datasetName()),
                                       str(traits[point.j].nameNoDB()),
                                       "0",
                                       "Correlation Plot between " + str(traits[point.i].symbol) + " and " + str(traits[point.j].symbol)))         
                inputFile_pdf.write('%s -- %s [len=%s, weight=%s, label=\"%s\", color=\"%s\", style=\"%s\", edgetooltip="%s"];\n'
                                % (point.i,
                                   point.j, 
                                   point.length,
                                   point.length, 
                                   _traitValue,
                                   point.color,
                                   point.style,
                                   "Correlation Plot between " + str(traits[point.i].symbol) + " and " + str(traits[point.j].symbol)))
					
            else:
                inputFile.write('%s -- %s [color="%s", style="%s"];\n'
                                % (point.i, 
                                   point.j, 
                                   point.color,
                                   point.style))
                inputFile_pdf.write('%s -- %s [color="%s", style="%s"];\n'
                                % (point.i, 
                                   point.j, 
                                   point.color,
                                   point.style))

    # now print nodes
    # the target attribute below is undocumented; I found it by looking
    # in the neato code
    for i in range(0, len(traits)):
        if traitEdges[i] == 1 or p["printIslands"] == 1:
            _tname = str(traits[i])
            if _tname.find("Publish") > 0:
            	plotColor = p["cPubName"]
            elif _tname.find("Geno") > 0:
            	plotColor = p["cGenName"]
            else:
            	plotColor = p["cMicName"]
            if p['nodelabel'] == 'yes':
            	labelName = _tname
            else:
            	labelName = traits[i].symbol

            inputFile.write('%s [label="%s", href="javascript:showDatabase2(\'%s\',\'%s\',\'\');", color="%s", style = "filled"];\n'
                            % (i, labelName, traits[i].datasetName(), traits[i].nameNoDB(), plotColor))# traits[i].color
            inputFile_pdf.write('%s [label="%s", href="javascript:showDatabase2(\'%s\',\'%s\',\'\');", color="%s", style = "filled"];\n'
                            % (i, labelName, traits[i].datasetName(), traits[i].nameNoDB(), plotColor))# traits[i].color
            
    # footer
    inputFile.write("}\n")
    inputFile_pdf.write("]\n")
    inputFile.close()
    inputFile_pdf.close()

    # return only the filename portion, omitting the directory
    return (os.path.split(filename))[1]

# runNeato : string -> string -> string
def runNeato(filename, extension, format, gType):
    """
    to run neato on the dataset in the given filename and produce an image file
    in the given format whose name we will return. Right now we assume
    that format is a valid neato output (see graphviz docs) and a valid extension
    for the source datafile. For example,
    runNeato('input1', 'png') will produce a file called 'input1.png'
    by invoking 'neato input1 -Tpng -o input1.png'
    """
    # trim extension off of filename before adding output extension
    if filename.find(".") > 0:
        filenameBase = filename[:filename.find(".")]
    else:
        filenameBase = filename
        
    imageFilename = filenameBase + "." + extension

    #choose which algorithm to run depended upon parameter gType
    #neato: energy based algorithm
    #circular: nodes given circular structure determined by which nodes are most closely correlated
    #radial: first node listed (when you search) is center of the graph, all other nodes are in a circular structure around it
    #fdp: force based algorithm

    if gType == "none":
    # to keep the output of neato from going to stdout, we open a pipe
    # and then wait for it to terminate
    
        if format in ('gif', 'cmapx', 'ps'):
            neatoExit = os.spawnlp(os.P_WAIT, "/usr/local/bin/neato", "/usr/local/bin/neato", "-s", "-T", format, webqtlConfig.IMGDIR + filename, "-o", webqtlConfig.IMGDIR + imageFilename)
    
        else:
            neatoExit = os.spawnlp(os.P_WAIT, "/usr/local/bin/neato", "/usr/local/bin/neato", webqtlConfig.IMGDIR + filename, "-T", format, "-o", webqtlConfig.IMGDIR + imageFilename)

        if neatoExit == 0:
            return imageFilename
        
        return imageFilename


    elif gType == "neato":
    # to keep the output of neato from going to stdout, we open a pipe
    # and then wait for it to terminate
        if format in ('gif', 'cmapx', 'ps'):
            neatoExit = os.spawnlp(os.P_WAIT, "/usr/local/bin/neato", "/usr/local/bin/neato", "-s", "-T", format, webqtlConfig.IMGDIR + filename, "-o", webqtlConfig.IMGDIR + imageFilename)
    
        else:
            neatoExit = os.spawnlp(os.P_WAIT, "/usr/local/bin/neato", "/usr/local/bin/neato", webqtlConfig.IMGDIR + filename, "-T", format, "-o", webqtlConfig.IMGDIR + imageFilename)

        if neatoExit == 0:
            return imageFilename
        
        return imageFilename

    elif gType == "circular":
	
        if format in ('gif', 'cmapx', 'ps'):
            neatoExit = os.spawnlp(os.P_WAIT, "/usr/local/bin/circo", "/usr/local/bin/circo", "-s", "-T", format, webqtlConfig.IMGDIR + filename, "-o", webqtlConfig.IMGDIR + imageFilename)
        
        else:
            neatoExit = os.spawnlp(os.P_WAIT, "/usr/local/bin/circo", "/usr/local/bin/circo", webqtlConfig.IMGDIR + filename, "-T", format, "-o", webqtlConfig.IMGDIR + imageFilename)

        if neatoExit == 0:
            return imageFilename
        
        return imageFilename

    elif gType == "radial":
	
        if format in ('gif', 'cmapx', 'ps'):
            neatoExit = os.spawnlp(os.P_WAIT, "/usr/local/bin/twopi", "/usr/local/bin/twopi", "-s", "-T", format, webqtlConfig.IMGDIR + filename, "-o", webqtlConfig.IMGDIR + imageFilename)
        
        else:
            neatoExit = os.spawnlp(os.P_WAIT, "/usr/local/bin/twopi", "/usr/local/bin/twopi", webqtlConfig.IMGDIR + filename, "-T", format, "-o", webqtlConfig.IMGDIR + imageFilename)

        if neatoExit == 0:
            return imageFilename
        
        return imageFilename

    elif gType == "fdp":

        if format in ('gif', 'cmapx', 'ps'):
            neatoExit = os.spawnlp(os.P_WAIT, "/usr/local/bin/fdp", "/usr/local/bin/fdp", "-s", "-T", format, webqtlConfig.IMGDIR + filename, "-o", webqtlConfig.IMGDIR + imageFilename)
        
        else:
            neatoExit = os.spawnlp(os.P_WAIT, "/usr/local/bin/fdp", "/usr/local/bin/fdp", webqtlConfig.IMGDIR + filename, "-T", format, "-o", webqtlConfig.IMGDIR + imageFilename)

        if neatoExit == 0:
            return imageFilename
        
        return imageFilename
    

    return imageFilename
# runPsToPdf: string -> int -> intstring
# to run Ps2Pdf to convert the given input postscript file to an 8.5 by 11
# pdf file The width and height should be specified in inches. We assume
# that the PS files output by GraphViz are 72 dpi.
def runPsToPdf(psfile, width, height):
    # we add 1 for padding b/c sometimes a small part of the graph gets
    # cut off
    newwidth = int((width + 1) * 720)
    newheight = int((height + 1) * 720)

    # replace the ps extension with a pdf one
    pdffile = psfile[:-2] + "pdf"

    os.spawnlp(os.P_WAIT, "ps2pdf", 
               "-g%sx%s" % (newwidth, newheight),
               webqtlConfig.IMGDIR + psfile, webqtlConfig.IMGDIR + pdffile)

    return pdffile

# buildParamDict: void -> ParamDict
# to process and validate CGI arguments,
# looking up human-readable names where necessary
# see the comment at the top of the file for valid cgi parameters
def buildParamDict(fs, sessionfile):
    params = {}
       
    params["inputFile"] = fs.formdata.getvalue("inputFile", "")
    params["progress"] = fs.formdata.getvalue("progress", "1")
    params["filename"] = fs.formdata.getvalue("filename", "")
    params["session"] = sessionfile
    
    if type("1") != type(fs.formdata.getvalue("searchResult")):
        params["searchResult"] = string.join(fs.formdata.getvalue("searchResult"),'\t')
    else:
        params["searchResult"] = fs.formdata.getvalue("searchResult")
        
    params["riset"] = fs.formdata.getvalue("RISet", "")
    #if params["filename"] == "":
    #    raise nGraphException("Required parameter filename missing")
   
    #parameter determining whether export button returns an xgmml graph file or plain text file
    params["exportFormat"] = fs.formdata.getvalue("exportFormat", "xgmml")
    
    #parameter determining whether or not traits in the graph file are listed by their symbol or name
    params["traitType"] = fs.formdata.getvalue("traitType", "symbol")
   
    #parameter saying whether or not graph structure should be locked when you redraw the graph
    params["lock"] = fs.formdata.getvalue("lock", "no")
    
    #parameter saying what algorithm should be used to draw the graph
    params["gType"] = fs.formdata.getvalue("gType", "none")

    params["kValue"] = webqtlUtil.safeFloat(fs.formdata.getvalue("kValue", "0.5"), 0.5)
    params["whichValue"] = webqtlUtil.safeInt(fs.formdata.getvalue("whichValue","0"),0)
    
    # 1 inch = 2.54 cm
    # 1 cm = 0.3937 inch
    
    params["width"] = webqtlUtil.safeFloat(fs.formdata.getvalue("width", "40.0"), 40.0)
    params["height"] = webqtlUtil.safeFloat(fs.formdata.getvalue("height", "40.0"), 40.0)
    
    yesno = ["yes", "no"]
    
    params["tune"] = webqtlUtil.safeString(fs.formdata.getvalue("tune", "yes"), yesno, "yes")
    
    params["printIslands"] = webqtlUtil.safeInt(fs.formdata.getvalue("printIslands", "1"),1)
    params["nodeshape"] = webqtlUtil.safeString(fs.formdata.getvalue("nodeshape","yes"), yesno, "yes")
    params["nodelabel"] = webqtlUtil.safeString(fs.formdata.getvalue("nodelabel","no"), yesno, "no")
    params["nfont"] = fs.formdata.getvalue("nfont","Arial")
    params["nfontsize"] = webqtlUtil.safeFloat(fs.formdata.getvalue("nfontsize", "10.0"), 10.0)

    params["splines"] = webqtlUtil.safeString(fs.formdata.getvalue("splines","yes"), yesno, "yes")    
    params["dispcorr"] = webqtlUtil.safeString(fs.formdata.getvalue("dispcorr","no"), yesno, "no")
    params["cfont"] = fs.formdata.getvalue("cfont","Arial")
    params["cfontsize"] = webqtlUtil.safeFloat(fs.formdata.getvalue("cfontsize", "10.0"), 10.0)
    
    params["cPubName"] = fs.formdata.getvalue("cPubName","palegreen")
    params["cMicName"] = fs.formdata.getvalue("cMicName","lightblue")
    params["cGenName"] = fs.formdata.getvalue("cGenName","lightcoral")
    
    params["cPubColor"] = fs.formdata.getvalue("cPubColor","98fb98")
    params["cMicColor"] = fs.formdata.getvalue("cMicColor","add8e6")
    params["cGenColor"] = fs.formdata.getvalue("cGenColor","f08080")
    
    params["cL1Name"] = fs.formdata.getvalue("cL1Name","blue")
    params["cL2Name"] = fs.formdata.getvalue("cL2Name","green")
    params["cL3Name"] = fs.formdata.getvalue("cL3Name","black")
    params["cL4Name"] = fs.formdata.getvalue("cL4Name","pink")
    params["cL5Name"] = fs.formdata.getvalue("cL5Name","orange")
    params["cL6Name"] = fs.formdata.getvalue("cL6Name","red")
    
    params["cL1Color"] = fs.formdata.getvalue("cL1Color","0000ff")
    params["cL2Color"] = fs.formdata.getvalue("cL2Color","00ff00")
    params["cL3Color"] = fs.formdata.getvalue("cL3Color","000000")
    params["cL4Color"] = fs.formdata.getvalue("cL4Color","ffc0cb")
    params["cL5Color"] = fs.formdata.getvalue("cL5Color","ffa500")
    params["cL6Color"] = fs.formdata.getvalue("cL6Color","ff0000")
    
    params["L1style"] = fs.formdata.getvalue("L1style","bold")
    params["L2style"] = fs.formdata.getvalue("L2style","")
    params["L3style"] = fs.formdata.getvalue("L3style","dashed")
    params["L4style"] = fs.formdata.getvalue("L4style","dashed")
    params["L5style"] = fs.formdata.getvalue("L5style","")
    params["L6style"] = fs.formdata.getvalue("L6style","bold")
    
    if params["splines"] == "yes":
        params["splineName"] = "curves"
    else:
        params["splineName"] = "lines"
        
    if params["nodeshape"] == "yes":
        params["nodeshapeType"] = "box"
    else:
        params["nodeshapeType"] = "ellipse"
        
    if params["whichValue"] == 0:
        params["correlationName"] = "Pearson"
    elif params["whichValue"] == 1:
        params["correlationName"] = "Spearman"
    elif params["whichValue"] == 2:
        params["correlationName"] = "Literature"
    else:
        params["correlationName"] = "Tissue"

    # see graphviz::writeNeatoFile to find out what this done
    params["edges"] = "complex"
    
    return params        

def optimalRadialNode(matrix):
    """
    Automatically determines the node with the most/strongest correlations with 
    other nodes. If the user selects "radial" for Graph Type and then "Auto" for the
    central node then this node is used as the central node. The algorithm is simply a sum of 
    each node's correlations that fall above the threshold set by the user.
    """
    
    optMatrix = [0]*(len(matrix)+1)
    
    for pt in matrix:
	 if abs(pt.value) > 0.5:
            optMatrix[pt.i] += abs(pt.value)
            optMatrix[pt.j] += abs(pt.value)
    
    optPoint = 0
    optCorrTotal = 0
    
    j = 0
    
    for point in optMatrix:
        if (float(point) > float(optCorrTotal)):
            optPoint = j
            optCorrTotal = point
        j += 1
    
    
    return optPoint    
    
# filterDataMatrix : DataMatrix -> ParamDict -> DataMatrix
def filterDataMatrix(matrix, p):
    """
    To convert a set of input RawPoints to a set of
    ProcessedPoints and to choose the appropriate
    correlation coefficent.
    """
    newmatrix = []
    for pt in matrix:
        pt2 = ProcessedPoint(pt.i, pt.j) # XZ, 09/11/2008: add module name
        
        # pick right value
        if p["whichValue"] == 0:
            pt2.value = pt.pearson
        elif p["whichValue"] == 1:
            pt2.value = pt.spearman
        elif p["whichValue"] == 2:
            pt2.value = pt.literature
        elif p["whichValue"] == 3:
            pt2.value = pt.tissue
        else:
            raise nGraphException("whichValue should be either 0, 1, 2 or 3")

        try:
            pt2.value = float(pt2.value)
        except:
            pt2.value = 0.00

        newmatrix.append(pt2)
        
        

    return newmatrix
   
def generateSymbolList(traits):
    """ 
    Generates a list of trait symbols to be displayed in the central node 
    selection drop-down menu when plotting a radial graph
    """
        
    traitList = traits
    
    symbolList = [None]*len(traitList)
    
    i=0
    for trait in traitList:
        symbolList[i] = str(trait.symbol)
        i = i+1
        
    symbolListString = "\t".join(symbolList)
    
    return symbolListString       
    
