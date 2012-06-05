#import string
from math import *
#import piddle as pid
#import os

#import reaper
from htmlgen import HTMLgen2 as HT

#from utility import Plot
from utility import webqtlUtil
from base import webqtlConfig
from dbFunction import webqtlDatabaseFunction

def basicStatsTable(vals, trait_type=None, cellid=None, heritability=None):

    valsOnly = []
    dataXZ = vals[:]
    for i in range(len(dataXZ)):
        valsOnly.append(dataXZ[i][1])

    traitmean, traitmedian, traitvar, traitstdev, traitsem, N = reaper.anova(valsOnly) #ZS: Should convert this from reaper to R in the future

    tbl = HT.TableLite(cellpadding=20, cellspacing=0)
    dataXZ = vals[:]
    dataXZ.sort(webqtlUtil.cmpOrder)
    tbl.append(HT.TR(HT.TD("Statistic",align="left", Class="fs14 fwb ffl b1 cw cbrb", width = 180),
                    HT.TD("Value", align="right", Class="fs14 fwb ffl b1 cw cbrb", width = 60)))
    tbl.append(HT.TR(HT.TD("N of Samples",align="left", Class="fs13 b1 cbw c222"),
                    HT.TD(N,nowrap="yes", Class="fs13 b1 cbw c222"), align="right"))
    tbl.append(HT.TR(HT.TD("Mean",align="left", Class="fs13 b1 cbw c222",nowrap="yes"),
                    HT.TD("%2.3f" % traitmean,nowrap="yes", Class="fs13 b1 cbw c222"), align="right"))
    tbl.append(HT.TR(HT.TD("Median",align="left", Class="fs13 b1 cbw c222",nowrap="yes"),
                    HT.TD("%2.3f" % traitmedian,nowrap="yes", Class="fs13 b1 cbw c222"), align="right"))
    #tbl.append(HT.TR(HT.TD("Variance",align="left", Class="fs13 b1 cbw c222",nowrap="yes"),
    #               HT.TD("%2.3f" % traitvar,nowrap="yes",align="left", Class="fs13 b1 cbw c222")))
    tbl.append(HT.TR(HT.TD("Standard Error (SE)",align="left", Class="fs13 b1 cbw c222",nowrap="yes"),
                    HT.TD("%2.3f" % traitsem,nowrap="yes", Class="fs13 b1 cbw c222"), align="right"))
    tbl.append(HT.TR(HT.TD("Standard Deviation (SD)", align="left", Class="fs13 b1 cbw c222",nowrap="yes"),
                    HT.TD("%2.3f" % traitstdev,nowrap="yes", Class="fs13 b1 cbw c222"), align="right"))
    tbl.append(HT.TR(HT.TD("Minimum", align="left", Class="fs13 b1 cbw c222",nowrap="yes"),
                    HT.TD("%s" % dataXZ[0][1],nowrap="yes", Class="fs13 b1 cbw c222"), align="right"))
    tbl.append(HT.TR(HT.TD("Maximum", align="left", Class="fs13 b1 cbw c222",nowrap="yes"),
                    HT.TD("%s" % dataXZ[-1][1],nowrap="yes", Class="fs13 b1 cbw c222"), align="right"))
    if (trait_type != None and trait_type == 'ProbeSet'):
        #IRQuest = HT.Href(text="Interquartile Range", url=webqtlConfig.glossaryfile +"#Interquartile",target="_blank", Class="fs14")
        #IRQuest.append(HT.BR())
        #IRQuest.append(" (fold difference)")
        tbl.append(HT.TR(HT.TD("Range (log2)",align="left", Class="fs13 b1 cbw c222",nowrap="yes"),
                HT.TD("%2.3f" % (dataXZ[-1][1]-dataXZ[0][1]),nowrap="yes", Class="fs13 b1 cbw c222"), align="right"))
        tbl.append(HT.TR(HT.TD(HT.Span("Range (fold)"),align="left", Class="fs13 b1 cbw c222",nowrap="yes"),
                HT.TD("%2.2f" % pow(2.0,(dataXZ[-1][1]-dataXZ[0][1])), nowrap="yes", Class="fs13 b1 cbw c222"), align="right"))
        tbl.append(HT.TR(HT.TD(HT.Span(HT.Href(url="/glossary.html#Interquartile", target="_blank", text="Interquartile Range", Class="non_bold")), align="left", Class="fs13 b1 cbw c222",nowrap="yes"),
                HT.TD("%2.2f" % pow(2.0,(dataXZ[int((N-1)*3.0/4.0)][1]-dataXZ[int((N-1)/4.0)][1])), nowrap="yes", Class="fs13 b1 cbw c222"), align="right"))

        #XZ, 04/01/2009: don't try to get H2 value for probe.
        if cellid:
            pass
        else:
            if heritability:
                tbl.append(HT.TR(HT.TD(HT.Span("Heritability"),align="center", Class="fs13 b1 cbw c222",nowrap="yes"),HT.TD("%s" % heritability, nowrap="yes",align="center", Class="fs13 b1 cbw c222")))
            else:
                pass
        # Lei Yan
        # 2008/12/19

    return tbl

def plotNormalProbability(vals=None, RISet='', title=None, showstrains=0, specialStrains=[None], size=(750,500)):

    dataXZ = vals[:]
    dataXZ.sort(webqtlUtil.cmpOrder)
    dataLabel = []
    dataX = map(lambda X: X[1], dataXZ)

    showLabel = showstrains
    if len(dataXZ) > 50:
        showLabel = 0
    for item in dataXZ:
        strainName = webqtlUtil.genShortStrainName(RISet=RISet, input_strainName=item[0])
        dataLabel.append(strainName)

    dataY=Plot.U(len(dataX))
    dataZ=map(Plot.inverseCumul,dataY)
    c = pid.PILCanvas(size=(750,500))
    Plot.plotXY(c, dataZ, dataX, dataLabel = dataLabel, XLabel='Expected Z score', connectdot=0, YLabel='Trait value', title=title, specialCases=specialStrains, showLabel = showLabel)

    filename= webqtlUtil.genRandStr("nP_")
    c.save(webqtlConfig.IMGDIR+filename, format='gif')

    img=HT.Image('/image/'+filename+'.gif',border=0)

    return img

def plotBoxPlot(vals):

    valsOnly = []
    dataXZ = vals[:]
    for i in range(len(dataXZ)):
        valsOnly.append(dataXZ[i][1])

    plotHeight = 320
    plotWidth = 220
    xLeftOffset = 60
    xRightOffset = 40
    yTopOffset = 40
    yBottomOffset = 60

    canvasHeight = plotHeight + yTopOffset + yBottomOffset
    canvasWidth = plotWidth + xLeftOffset + xRightOffset
    canvas = pid.PILCanvas(size=(canvasWidth,canvasHeight))
    XXX = [('', valsOnly[:])]

    Plot.plotBoxPlot(canvas, XXX, offset=(xLeftOffset, xRightOffset, yTopOffset, yBottomOffset), XLabel= "Trait")
    filename= webqtlUtil.genRandStr("Box_")
    canvas.save(webqtlConfig.IMGDIR+filename, format='gif')
    img=HT.Image('/image/'+filename+'.gif',border=0)

    plotLink = HT.Span("More about ", HT.Href(text="Box Plots", url="http://davidmlane.com/hyperstat/A37797.html", target="_blank", Class="fs13"))

    return img, plotLink

def plotBarGraph(identification='', RISet='', vals=None, type="name"):

    this_identification = "unnamed trait"
    if identification:
        this_identification = identification

    if type=="rank":
        dataXZ = vals[:]
        dataXZ.sort(webqtlUtil.cmpOrder)
        title='%s' % this_identification
    else:
        dataXZ = vals[:]
        title='%s' % this_identification

    tvals = []
    tnames = []
    tvars = []
    for i in range(len(dataXZ)):
        tvals.append(dataXZ[i][1])
        tnames.append(webqtlUtil.genShortStrainName(RISet=RISet, input_strainName=dataXZ[i][0]))
        tvars.append(dataXZ[i][2])
    nnStrain = len(tnames)

    sLabel = 1

    ###determine bar width and space width
    if nnStrain < 20:
        sw = 4
    elif nnStrain < 40:
        sw = 3
    else:
        sw = 2

    ### 700 is the default plot width minus Xoffsets for 40 strains
    defaultWidth = 650
    if nnStrain > 40:
        defaultWidth += (nnStrain-40)*10
    defaultOffset = 100
    bw = int(0.5+(defaultWidth - (nnStrain-1.0)*sw)/nnStrain)
    if bw < 10:
        bw = 10

    plotWidth = (nnStrain-1)*sw + nnStrain*bw + defaultOffset
    plotHeight = 500
    #print [plotWidth, plotHeight, bw, sw, nnStrain]
    c = pid.PILCanvas(size=(plotWidth,plotHeight))
    Plot.plotBarText(c, tvals, tnames, variance=tvars, YLabel='Value', title=title, sLabel = sLabel, barSpace = sw)

    filename= webqtlUtil.genRandStr("Bar_")
    c.save(webqtlConfig.IMGDIR+filename, format='gif')
    img=HT.Image('/image/'+filename+'.gif',border=0)

    return img
