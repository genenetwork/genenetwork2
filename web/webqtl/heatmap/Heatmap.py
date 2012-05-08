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

import os
import string
import piddle as pid
import cPickle

from base import webqtlConfig
from base.webqtlTrait import webqtlTrait
from dbFunction import webqtlDatabaseFunction
from utility import webqtlUtil 
from utility import Plot
import slink


# XZ, 09/09/2008: After adding several traits to collection, click "QTL Heatmap" button,
# XZ, 09/09/2008: This class will generate what you see.
#########################################
#      QTL heatmap Page
#########################################
class Heatmap:

        def __init__(self, fd=None, searchResult=None, colorScheme=None, userPrivilege=None, userName=None):
                cursor = webqtlDatabaseFunction.getCursor()
                if (not cursor):
                        return
                targetDescriptionChecked = fd.formdata.getvalue('targetDescriptionCheck', '')
                clusterChecked = fd.formdata.getvalue('clusterCheck', '')
                sessionfile = fd.formdata.getvalue("session")
                genotype = fd.genotype
                strainlist = fd.strainlist
                ppolar = fd.ppolar
                mpolar = fd.mpolar
                traitList = []
                traitDataList = []
                for item in searchResult:
                        thisTrait = webqtlTrait(fullname=item, cursor=cursor)
                        thisTrait.retrieveInfo()
                        thisTrait.retrieveData(fd.strainlist)
                        traitList.append(thisTrait)
                        traitDataList.append(thisTrait.exportData(fd.strainlist))
                self.buildCanvas(colorScheme=colorScheme, targetDescriptionChecked=targetDescriptionChecked, clusterChecked=clusterChecked, sessionfile=sessionfile, genotype=genotype, strainlist=strainlist, ppolar=ppolar, mpolar=mpolar, traitList=traitList, traitDataList=traitDataList, userPrivilege=userPrivilege, userName=userName)

       	def buildCanvas(self, colorScheme='', targetDescriptionChecked='', clusterChecked='', sessionfile='', genotype=None, strainlist=None, ppolar=None, mpolar=None, traitList=None, traitDataList=None, userPrivilege=None, userName=None):
                labelFont = pid.Font(ttf="tahoma",size=14,bold=0)
                topHeight = 0
       	       	NNN = len(traitList)
       	       	#XZ: It's necessory to define canvas here
                canvas = pid.PILCanvas(size=(80+NNN*20,880))
                names = map(webqtlTrait.displayName, traitList)
                #XZ, 7/29/2009: create trait display and find max strWidth
                strWidth = 0
                for j in range(len(names)):
                        thisTrait = traitList[j]
                        if targetDescriptionChecked:
                            if thisTrait.db.type == 'ProbeSet':
                                if thisTrait.probe_target_description:
                                        names[j] += ' [%s at Chr %s @ %2.3fMB, %s]' % (thisTrait.symbol, thisTrait.chr, thisTrait.mb, thisTrait.probe_target_description)
                                else:
                                        names[j] += ' [%s at Chr %s @ %2.3fMB]' % (thisTrait.symbol, thisTrait.chr, thisTrait.mb)
                            elif thisTrait.db.type == 'Geno':
                                names[j] += ' [Chr %s @ %2.3fMB]' % (thisTrait.chr, thisTrait.mb)
                            elif thisTrait.db.type == 'Publish':
                                if thisTrait.confidential:
                                    if webqtlUtil.hasAccessToConfidentialPhenotypeTrait(privilege=userPrivilege, userName=userName, authorized_users=thisTrait.authorized_users):
                                        if thisTrait.post_publication_abbreviation:
                                            names[j] += ' [%s]' % (thisTrait.post_publication_abbreviation)
                                    else:
                                        if thisTrait.pre_publication_abbreviation:
                                            names[j] += ' [%s]' % (thisTrait.pre_publication_abbreviation)
                                else:
                                    if thisTrait.post_publication_abbreviation:
                                        names[j] += ' [%s]' % (thisTrait.post_publication_abbreviation)
                            else:
                                pass

                        i = canvas.stringWidth(names[j], font=labelFont)
                        if i > strWidth:
                                strWidth = i

                width = NNN*20
                xoffset = 40
                yoffset = 40
                cellHeight = 3
                nLoci = reduce(lambda x,y: x+y, map(lambda x: len(x),genotype),0)

                if nLoci > 2000:
                        cellHeight = 1
                elif nLoci > 1000:
                        cellHeight = 2
                elif nLoci < 200:
                        cellHeight = 10
                else:
                        pass

                pos = range(NNN)
                neworder = []
                BWs = Plot.BWSpectrum()
                colors100 = Plot.colorSpectrum()
                colors = Plot.colorSpectrum(130)
                finecolors = Plot.colorSpectrum(250)
                colors100.reverse()
                colors.reverse()
                finecolors.reverse()

                scaleFont=pid.Font(ttf="tahoma",size=10,bold=0)
				
                if not clusterChecked: #XZ: this part is for original order
                        for i in range(len(names)):
                                neworder.append((xoffset+20*(i+1), i))

                        canvas = pid.PILCanvas(size=(80+NNN*20+240,80+ topHeight +5+5+strWidth+nLoci*cellHeight+80+20*cellHeight))

                        self.drawTraitNameBottom(canvas,names,yoffset,neworder,strWidth,topHeight,labelFont)
                else: #XZ: this part is to cluster traits
                        topHeight = 400
                        canvas = pid.PILCanvas(size=(80+NNN*20+240,80+ topHeight +5+5+strWidth+nLoci*cellHeight+80+20*cellHeight))

                        corArray = [([0] * (NNN))[:] for i in range(NNN)]

                        nnCorr = len(strainlist)

                        #XZ, 08/04/2009: I commented out pearsonArray, spearmanArray
                        for i, thisTrait in enumerate(traitList):
                            names1 = [thisTrait.db.name, thisTrait.name, thisTrait.cellid]
                            for j, thisTrait2 in enumerate(traitList):
                                    names2 = [thisTrait2.db.name, thisTrait2.name, thisTrait2.cellid]
                                    if j < i:
                                            corr,nOverlap = webqtlUtil.calCorrelation(traitDataList[i], traitDataList[j],nnCorr)
                                            if (1-corr) < 0:
                                                    distance = 0.0
                                            else:
                                                    distance = 1-corr
                                            corArray[i][j] = distance
                                            corArray[j][i] = distance
                                    elif j == i:
                                            corArray[i][j] = 0.0
                                    else:
                                            pass

                        #XZ, 7/29/2009: The parameter d has info of cluster (group member and distance). The format of d is tricky. Print it out to see it's format.
                        d = slink.slink(corArray)

                        #XZ, 7/29/2009: Attention: The 'neworder' is changed by the 'draw' function
                        #XZ, 7/30/2009: Only toppos[1][0] and top[1][1] are used later. Then what toppos[0] is used for? 
                        toppos = self.draw(canvas,names,d,xoffset,yoffset,neworder,topHeight)
                        self.drawTraitNameTop(canvas,names,yoffset,neworder,strWidth,topHeight,labelFont)

                        #XZ, 7/29/2009: draw the top vertical line
                        canvas.drawLine(toppos[1][0],toppos[1][1],toppos[1][0],yoffset)

                        #XZ: draw string 'distance = 1-r'
                        canvas.drawString('distance = 1-r',neworder[-1][0] + 50, topHeight*3/4,font=labelFont,angle=90)

                        #draw Scale
                        scaleFont=pid.Font(ttf="tahoma",size=10,bold=0)
                        x = neworder[-1][0]
                        canvas.drawLine(x+5, topHeight+yoffset, x+5, yoffset, color=pid.black)
                        y = 0
                        while y <=2:
                                canvas.drawLine(x+5, topHeight*y/2.0+yoffset, x+10, topHeight*y/2.0+yoffset)
                                canvas.drawString('%2.1f' % (2-y), x+12, topHeight*y/2.0+yoffset, font=scaleFont)
                                y += 0.5


                chrname = 0
                chrnameFont=pid.Font(ttf="tahoma",size=24,bold=0)
                Ncol = 0

                nearestMarkers = self.getNearestMarker(traitList, genotype)

                # import cPickle
                if sessionfile:
                        fp = open(os.path.join(webqtlConfig.TMPDIR, sessionfile + '.session'), 'rb')
                        permData = cPickle.load(fp)
                        fp.close()
                else:
                        permData = {}

                areas = []
				#XZ, 7/31/2009: This for loop is to generate the heatmap
                #XZ: draw trait by trait instead of marker by marker
                for order in neworder:
                        #startHeight = 40+400+5+5+strWidth
                        startHeight = topHeight + 40+5+5+strWidth
                        startWidth = order[0]-5
                        if Ncol and Ncol % 5 == 0:
                                drawStartPixel = 8
                        else:
                                drawStartPixel = 9

                        tempVal = traitDataList[order[1]]
                        _vals = []
                        _strains = [] 
                        for i in range(len(strainlist)):
                                if tempVal[i] != None:
                                        _strains.append(strainlist[i])
                                        _vals.append(tempVal[i])

                        qtlresult = genotype.regression(strains = _strains, trait = _vals)

                        if sessionfile:
                                LRSArray = permData[str(traitList[order[1]])]
                        else:
                                LRSArray = genotype.permutation(strains = _strains, trait = _vals, nperm = 1000)
                                permData[str(traitList[order[1]])] = LRSArray

                        sugLRS = LRSArray[369]
                        sigLRS = LRSArray[949]
                        prechr = 0
                        chrstart = 0
                        nearest = nearestMarkers[order[1]]
                        midpoint = []

                        for item in qtlresult:
                                if item.lrs > webqtlConfig.MAXLRS:
                                        adjustlrs = webqtlConfig.MAXLRS
                                else:
                                        adjustlrs = item.lrs

                                if item.locus.chr != prechr:
                                        if prechr:
                                                canvas.drawRect(startWidth-drawStartPixel, startHeight, startWidth+10, startHeight+3,edgeColor=pid.white, edgeWidth=0, fillColor=pid.white)
                                                startHeight+= 3
                                                if not chrname:
                                                        canvas.drawString(prechr,xoffset-20,(chrstart+startHeight)/2,font = chrnameFont,color=pid.dimgray)
                                        prechr = item.locus.chr
                                        chrstart = startHeight
                                if colorScheme == '0':
                                        if adjustlrs <= sugLRS:
                                                colorIndex = int(65*adjustlrs/sugLRS)
                                        else:
                                                colorIndex = int(65 + 35*(adjustlrs-sugLRS)/(sigLRS-sugLRS))
                                        if colorIndex > 99:
                                                colorIndex = 99
                                        colorIndex = colors100[colorIndex]
                                elif colorScheme == '1':
                                        sugLRS = LRSArray[369]/2.0
                                        if adjustlrs <= sugLRS:
                                                colorIndex = BWs[20+int(50*adjustlrs/sugLRS)]
                                        else:
                                                if item.additive > 0:
                                                        colorIndex = int(80 + 50*(adjustlrs-sugLRS)/(sigLRS-sugLRS))
                                                else:
                                                        colorIndex = int(50 - 50*(adjustlrs-sugLRS)/(sigLRS-sugLRS))
                                                if colorIndex > 129:
                                                        colorIndex = 129
                                                if colorIndex < 0:
                                                        colorIndex = 0
                                                colorIndex = colors[colorIndex]
                                elif colorScheme == '2':
                                        if item.additive > 0:
                                                colorIndex = int(150 + 100*(adjustlrs/sigLRS))
                                        else:
                                                colorIndex = int(100 - 100*(adjustlrs/sigLRS))
                                        if colorIndex > 249:
                                                colorIndex = 249
                                        if colorIndex < 0:
                                                        colorIndex = 0
                                        colorIndex = finecolors[colorIndex]
                                else:
                                        colorIndex = pid.white

                                if startHeight > 1:
                                        canvas.drawRect(startWidth-drawStartPixel, startHeight, startWidth+10, startHeight+cellHeight,edgeColor=colorIndex, edgeWidth=0, fillColor=colorIndex)
                                else:
                                        canvas.drawLine(startWidth-drawStartPixel, startHeight, startWidth+10, startHeight, Color=colorIndex)

                                if item.locus.name == nearest:
                                        midpoint = [startWidth,startHeight-5]
                                startHeight+=cellHeight

                        #XZ, map link to trait name and band
                        COORDS = "%d,%d,%d,%d" %(startWidth-drawStartPixel,topHeight+40,startWidth+10,startHeight)
                        HREF = "javascript:showDatabase2('%s','%s','%s');" % (traitList[order[1]].db.name, traitList[order[1]].name, traitList[order[1]].cellid)
                        area = (COORDS, HREF, '%s' % names[order[1]])
                        areas.append(area)

                        if midpoint:
                                traitPixel = ((midpoint[0],midpoint[1]),(midpoint[0]-6,midpoint[1]+12),(midpoint[0]+6,midpoint[1]+12))
                                canvas.drawPolygon(traitPixel,edgeColor=pid.black,fillColor=pid.orange,closed=1)

                        if not chrname:
                                canvas.drawString(prechr,xoffset-20,(chrstart+startHeight)/2,font = chrnameFont,color=pid.dimgray)
                        chrname = 1
                        Ncol += 1


                #draw Spectrum
                startSpect = neworder[-1][0] + 30
                startHeight = topHeight + 40+5+5+strWidth

                if colorScheme == '0':
                        for i in range(100):
                                canvas.drawLine(startSpect+i,startHeight+20,startSpect+i,startHeight+40,color=colors100[i])
                        scaleFont=pid.Font(ttf="tahoma",size=10,bold=0)
                        canvas.drawLine(startSpect,startHeight+45,startSpect,startHeight+39,color=pid.black)
                        canvas.drawString('LRS = 0',startSpect,startHeight+55,font=scaleFont)
                        canvas.drawLine(startSpect+64,startHeight+45,startSpect+64,startHeight+39,color=pid.black)
                        canvas.drawString('Suggestive LRS',startSpect+64,startHeight+55,font=scaleFont)
                        canvas.drawLine(startSpect+99,startHeight+45,startSpect+99,startHeight+39,color=pid.black)
                        canvas.drawString('Significant LRS',startSpect+105,startHeight+40,font=scaleFont)
                elif colorScheme == '1':
                        for i in range(50):
                                canvas.drawLine(startSpect+i,startHeight,startSpect+i,startHeight+40,color=BWs[20+i])
                        for i in range(50,100):
                                canvas.drawLine(startSpect+i,startHeight,startSpect+i,startHeight+20,color=colors[100-i])
                                canvas.drawLine(startSpect+i,startHeight+20,startSpect+i,startHeight+40,color=colors[30+i])

                        canvas.drawLine(startSpect,startHeight+45,startSpect,startHeight+39,color=pid.black)
                        canvas.drawString('LRS = 0',startSpect,startHeight+60,font=scaleFont)
                        canvas.drawLine(startSpect+50,startHeight+45,startSpect+50,startHeight+39,color=pid.black)
                        canvas.drawString('0.5*Suggestive LRS',startSpect+50,startHeight+ 60,font=scaleFont)
                        canvas.drawLine(startSpect+99,startHeight+45,startSpect+99,startHeight+39,color=pid.black)
                        canvas.drawString('Significant LRS',startSpect+105,startHeight+50,font=scaleFont)
                        textFont=pid.Font(ttf="verdana",size=18,bold=0)
                        canvas.drawString('%s +' % ppolar,startSpect+120,startHeight+ 35,font=textFont,color=pid.red)
                        canvas.drawString('%s +' % mpolar,startSpect+120,startHeight+ 15,font=textFont,color=pid.blue)
                elif colorScheme == '2':
                        for i in range(100):
                                canvas.drawLine(startSpect+i,startHeight,startSpect+i,startHeight+20,color=finecolors[100-i])
                                canvas.drawLine(startSpect+i,startHeight+20,startSpect+i,startHeight+40,color=finecolors[150+i])

                        canvas.drawLine(startSpect,startHeight+45,startSpect,startHeight+39,color=pid.black)
                        canvas.drawString('LRS = 0',startSpect,startHeight+60,font=scaleFont)
                        canvas.drawLine(startSpect+99,startHeight+45,startSpect+99,startHeight+39,color=pid.black)
                        canvas.drawString('Significant LRS',startSpect+105,startHeight+50,font=scaleFont)
                        textFont=pid.Font(ttf="verdana",size=18,bold=0)
                        canvas.drawString('%s +' % ppolar,startSpect+120,startHeight+ 35,font=textFont,color=pid.red)
                        canvas.drawString('%s +' % mpolar,startSpect+120,startHeight+ 15,font=textFont,color=pid.blue)
						
                filename= webqtlUtil.genRandStr("Heatmap_")
                canvas.save(webqtlConfig.IMGDIR+filename, format='png')
                if not sessionfile:
                        sessionfile = webqtlUtil.generate_session()
                        webqtlUtil.dump_session(permData, os.path.join(webqtlConfig.TMPDIR, sessionfile +'.session'))
                self.filename=filename
                self.areas=areas
                self.sessionfile=sessionfile
        
        def getResult(self):
                return self.filename, self.areas, self.sessionfile

        #XZ, 7/31/2009: This function put the order of traits into parameter neworder,
        #XZ: return the position of the top vertical line of the hierarchical tree, draw the hierarchical tree.
        def draw(self,canvas,names,d,xoffset,yoffset,neworder,topHeight):
                maxDistance = topHeight
                fontoffset = 4    #XZ, 7/31/2009: used only for drawing tree
                if type(d[0]) == type(1) and type(d[1]) == type(1):
                        neworder.append((xoffset+20,d[0]))
                        neworder.append((xoffset+40,d[1]))
                        height = d[2]*maxDistance/2
                        canvas.drawLine(xoffset+20-fontoffset,maxDistance+yoffset,xoffset+20-fontoffset,maxDistance-height+yoffset)
                        canvas.drawLine(xoffset+40-fontoffset,maxDistance+yoffset,xoffset+40-fontoffset,maxDistance-height+yoffset)
                        canvas.drawLine(xoffset+40-fontoffset,maxDistance+yoffset-height,xoffset+20-fontoffset,maxDistance-height+yoffset)
                        return (40,(xoffset+30-fontoffset,maxDistance-height+yoffset))
                elif type(d[0]) == type(1):
                        neworder.append((xoffset+20,d[0]))
                        d2 = self.draw(canvas,names,d[1],xoffset+20,yoffset,neworder,topHeight)
                        height = d[2]*maxDistance/2
                        canvas.drawLine(xoffset+20-fontoffset,maxDistance+yoffset,xoffset+20-fontoffset,maxDistance-height+yoffset)
                        canvas.drawLine(d2[1][0],d2[1][1],d2[1][0],maxDistance-height+yoffset)
                        canvas.drawLine(d2[1][0],maxDistance-height+yoffset,xoffset+20-fontoffset,maxDistance-height+yoffset)
                        return (20+d2[0],((d2[1][0]+xoffset+20-fontoffset)/2,maxDistance-height+yoffset))
                elif type(d[1]) == type(1):
                        d1 = self.draw(canvas,names,d[0],xoffset,yoffset,neworder,topHeight)
                        neworder.append((xoffset+d1[0]+20,d[1]))
                        height = d[2]*maxDistance/2
                        canvas.drawLine(xoffset+d1[0]+20-fontoffset,maxDistance+yoffset,xoffset+d1[0]+20-fontoffset,maxDistance-height+yoffset)
                        canvas.drawLine(d1[1][0],d1[1][1],d1[1][0],maxDistance-height+yoffset)
                        canvas.drawLine(d1[1][0],maxDistance-height+yoffset,xoffset+d1[0]+20-fontoffset,maxDistance-height+yoffset)
                        return (d1[0]+20,((d1[1][0]+xoffset+d1[0]+20-fontoffset)/2,maxDistance-height+yoffset))
                else:
                        d1 = self.draw(canvas,names,d[0],xoffset,yoffset,neworder,topHeight)
                        d2 = self.draw(canvas,names,d[1],xoffset+d1[0],yoffset,neworder,topHeight)
                        height = d[2]*maxDistance/2
                        canvas.drawLine(d2[1][0],d2[1][1],d2[1][0],maxDistance-height+yoffset)
                        canvas.drawLine(d1[1][0],d1[1][1],d1[1][0],maxDistance-height+yoffset)
                        canvas.drawLine(d1[1][0],maxDistance-height+yoffset,d2[1][0],maxDistance-height+yoffset)
                        return (d1[0]+d2[0],((d1[1][0]+d2[1][0])/2,maxDistance-height+yoffset))

        #XZ, 7/31/2009: dras trait names
        def drawTraitNameBottom (self,canvas,names,yoffset,neworder,strWidth,topHeight,labelFont):
                maxDistance = topHeight
                for oneOrder in neworder:
                        canvas.drawString(names[oneOrder[1]],oneOrder[0]-5,maxDistance+yoffset+5+strWidth-canvas.stringWidth(names[oneOrder[1]],font=labelFont),font=labelFont,color=pid.black,angle=270)

        def drawTraitNameTop (self,canvas,names,yoffset,neworder,strWidth,topHeight,labelFont):
                maxDistance = topHeight
                for oneOrder in neworder:
                        canvas.drawString(names[oneOrder[1]],oneOrder[0]-5,maxDistance+yoffset+5,font=labelFont,color=pid.black,angle=270)


        def getNearestMarker(self, traitList, genotype):
                out = []
                if not genotype.Mbmap:
                        return [None]* len(traitList)
                for item in traitList:
                        try:
                                nearest = None
                                for _chr in genotype:
                                        if _chr.name != item.chr:
                                                continue
                                        distance = 1e30
                                        for _locus in _chr:
                                                if abs(_locus.Mb-item.mb) < distance:
                                                        distance = abs(_locus.Mb-item.mb)
                                                        nearest = _locus.name
                                out.append(nearest)
                        except:
                                out.append(None)

                return out
