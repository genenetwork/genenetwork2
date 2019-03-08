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

from __future__ import print_function

from PIL import (Image, ImageColor, ImageDraw, ImageFont)
from pprint import pformat as pf

from math import *
import random
import sys, os
from numarray import linear_algebra as la
from numarray import ones, array, dot, swapaxes

import reaper

import webqtlUtil
import corestats
from base import webqtlConfig
from utility.pillow_utils import draw_rotated_text
import utility.logger
logger = utility.logger.getLogger(__name__ )

# ---- Define common colours ---- #
BLUE = ImageColor.getrgb("blue")
BLACK = ImageColor.getrgb("black")
# ---- END: Define common colours ---- #

# ---- FONT FILES ---- #
VERDANA_FILE = "./wqflask/static/fonts/verdana.ttf"
COUR_FILE = "./wqflask/static/fonts/courbd.ttf"
TAHOMA_FILE = "./wqflask/static/fonts/tahoma.ttf"
# ---- END: FONT FILES ---- #

def cformat(d, rank=0):
    'custom string format'
    strD = "%2.6f" % d

    if rank == 0:
        while strD[-1] in ('0','.'):
            if strD[-1] == '0' and strD[-2] == '.' and len(strD) <= 4:
                break
            elif strD[-1] == '.':
                strD = strD[:-1]
                break
            else:
                strD = strD[:-1]

    else:
        strD = strD.split(".")[0]

    if strD == '-0.0':
        strD = '0.0'
    return strD

def frange(start, end=None, inc=1.0):
    "A faster range-like function that does accept float increments..."
    if end == None:
        end = start + 0.0
        start = 0.0
    else:
        start += 0.0 # force it to be a float
    count = int((end - start) / inc)
    if start + count * inc != end:
    # Need to adjust the count. AFAICT, it always comes up one short.
        count += 1
    L = [start] * count
    for i in xrange(1, count):
        L[i] = start + i * inc
    return L

def find_outliers(vals):
    """Calculates the upper and lower bounds of a set of sample/case values


    >>> find_outliers([3.504, 5.234, 6.123, 7.234, 3.542, 5.341, 7.852, 4.555, 12.537])
    (11.252500000000001, 0.5364999999999993)

    >>> >>> find_outliers([9,12,15,17,31,50,7,5,6,8])
    (32.0, -8.0)

    If there are no vals, returns None for the upper and lower bounds,
    which code that calls it will have to deal with.
    >>> find_outliers([])
    (None, None)

    """

    logger.debug("xerxes vals is:", pf(vals))

    if vals:
        #logger.debug("vals is:", pf(vals))
        stats = corestats.Stats(vals)
        low_hinge = stats.percentile(25)
        up_hinge = stats.percentile(75)
        hstep = 1.5 * (up_hinge - low_hinge)

        upper_bound = up_hinge + hstep
        lower_bound = low_hinge - hstep

    else:
        upper_bound = None
        lower_bound = None

    logger.debug(pf(locals()))
    return upper_bound, lower_bound

# parameter: data is either object returned by reaper permutation function (called by MarkerRegressionPage.py)
# or the first object returned by direct (pair-scan) permu function (called by DirectPlotPage.py)
def plotBar(canvas, data, barColor=BLUE, axesColor=BLACK, labelColor=BLACK, XLabel=None, YLabel=None, title=None, offset= (60, 20, 40, 40), zoom = 1):
    im_drawer = ImageDraw.Draw(canvas)
    xLeftOffset, xRightOffset, yTopOffset, yBottomOffset = offset

    plotWidth = canvas.size[0] - xLeftOffset - xRightOffset
    plotHeight = canvas.size[1] - yTopOffset - yBottomOffset
    if plotHeight<=0 or plotWidth<=0:
       return

    if len(data) < 2:
       return

    max_D = max(data)
    min_D = min(data)
    #add by NL 06-20-2011: fix the error: when max_D is infinite, log function in detScale will go wrong
    if max_D == float('inf') or max_D>webqtlConfig.MAXLRS:
       max_D=webqtlConfig.MAXLRS #maximum LRS value

    xLow, xTop, stepX = detScale(min_D, max_D)

    #reduce data
    #ZS: Used to determine number of bins for permutation output
    step = ceil((xTop-xLow)/50.0)
    j = xLow
    dataXY = []
    Count = []
    while j <= xTop:
       dataXY.append(j)
       Count.append(0)
       j += step

    for i, item in enumerate(data):
       if item == float('inf') or item>webqtlConfig.MAXLRS:
           item = webqtlConfig.MAXLRS #maximum LRS value
       j = int((item-xLow)/step)
       Count[j] += 1

    yLow, yTop, stepY=detScale(0,max(Count))

    #draw data
    xScale = plotWidth/(xTop-xLow)
    yScale = plotHeight/(yTop-yLow)
    barWidth = xScale*step

    for i, count in enumerate(Count):
       if count:
           xc = (dataXY[i]-xLow)*xScale+xLeftOffset
           yc =-(count-yLow)*yScale+yTopOffset+plotHeight
           im_drawer.rectangle(
               xy=((xc+2,yc),(xc+barWidth-2,yTopOffset+plotHeight)),
               outline=barColor, fill=barColor)

    #draw drawing region
    im_drawer.rectangle(
        xy=((xLeftOffset, yTopOffset), (xLeftOffset+plotWidth, yTopOffset+plotHeight))
    )

    #draw scale
    scaleFont=ImageFont.truetype(font=COUR_FILE,size=11)
    x=xLow
    for i in range(int(stepX)+1):
       xc=xLeftOffset+(x-xLow)*xScale
       im_drawer.line(
           xy=((xc,yTopOffset+plotHeight),(xc,yTopOffset+plotHeight+5)),
           fill=axesColor)
       strX = cformat(d=x, rank=0)
       im_drawer.text(
           text=strX,
           xy=(xc-im_drawer.textsize(strX,font=scaleFont)[0]/2,
               yTopOffset+plotHeight+14),font=scaleFont)
       x+= (xTop - xLow)/stepX

    y=yLow
    for i in range(int(stepY)+1):
       yc=yTopOffset+plotHeight-(y-yLow)*yScale
       im_drawer.line(xy=((xLeftOffset,yc),(xLeftOffset-5,yc)), fill=axesColor)
       strY = "%d" %y
       im_drawer.text(
           text=strY,
           xy=(xLeftOffset-im_drawer.textsize(strY,font=scaleFont)[0]-6,yc+5),
           font=scaleFont)
       y+= (yTop - yLow)/stepY

    #draw label
    labelFont=ImageFont.truetype(font=TAHOMA_FILE,size=17)
    if XLabel:
       im_drawer.text(
           text=XLabel,
           xy=(xLeftOffset+(
               plotWidth-im_drawer.textsize(XLabel,font=labelFont)[0])/2.0,
               yTopOffset+plotHeight+yBottomOffset-10),
           font=labelFont,fill=labelColor)

    if YLabel:
        draw_rotated_text(canvas, text=YLabel,
                          xy=(19,
                              yTopOffset+plotHeight-(
                                  plotHeight-im_drawer.textsize(
                                      YLabel,font=labelFont)[0])/2.0),
                          font=labelFont, fill=labelColor, angle=90)

    labelFont=ImageFont.truetype(font=VERDANA_FILE,size=16)
    if title:
       im_drawer.text(
           text=title,
           xy=(xLeftOffset+(plotWidth-im_drawer.textsize(
               title,font=labelFont)[0])/2.0,
               20),
           font=labelFont,fill=labelColor)

# This function determines the scale of the plot
def detScaleOld(min,max):
    if min>=max:
        return None
    elif min == -1.0 and max == 1.0:
        return [-1.2,1.2,12]
    else:
        a=max-min
        b=floor(log10(a))
        c=pow(10.0,b)
        if a < c*5.0:
            c/=2.0
        #print a,b,c
        low=c*floor(min/c)
        high=c*ceil(max/c)
        return [low,high,round((high-low)/c)]

def detScale(min=0,max=0):

    if min>=max:
        return None
    elif min == -1.0 and max == 1.0:
        return [-1.2,1.2,12]
    else:
        a=max-min
        if max != 0:
            max += 0.1*a
        if min != 0:
            if min > 0 and min < 0.1*a:
                min = 0.0
            else:
                min -= 0.1*a
        a=max-min
        b=floor(log10(a))
        c=pow(10.0,b)
        low=c*floor(min/c)
        high=c*ceil(max/c)
        n = round((high-low)/c)
        div = 2.0
        while n < 5 or n > 15:
            if n < 5:
                c /= div
            else:
                c *= div
            if div == 2.0:
                div =5.0
            else:
                div =2.0
            low=c*floor(min/c)
            high=c*ceil(max/c)
            n = round((high-low)/c)

        return [low,high,n]

def bluefunc(x):
    return 1.0 / (1.0 + exp(-10*(x-0.6)))

def redfunc(x):
    return 1.0 / (1.0 + exp(10*(x-0.5)))

def greenfunc(x):
    return 1 - pow(redfunc(x+0.2),2) - bluefunc(x-0.3)

def colorSpectrum(n=100):
    multiple = 10
    if n == 1:
        return [ImageColor.getrgb("rgb(100%,0%,0%)")]
    elif n == 2:
        return [ImageColor.getrgb("100%,0%,0%)"),
                ImageColor.getrgb("rgb(0%,0%,100%)")]
    elif n == 3:
        return [ImageColor.getrgb("rgb(100%,0%,0%)"),
                ImageColor.getrgb("rgb(0%,100%,0%)"),
                ImageColor.getrgb("rgb(0%,0%,100%)")]
    N = n*multiple
    out = [None]*N;
    for i in range(N):
        x = float(i)/N
        out[i] = ImageColor.getrgb("rgb({}%,{}%,{}%".format(
            *[int(i*100) for i in (
                redfunc(x), greenfunc(x), bluefunc(x))]))
    out2 = [out[0]]
    step = N/float(n-1)
    j = 0
    for i in range(n-2):
        j += step
        out2.append(out[int(j)])
    out2.append(out[-1])
    return out2

def _test():
    import doctest
    doctest.testmod()


if __name__=="__main__":
    _test()
