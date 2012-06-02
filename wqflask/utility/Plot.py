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

#import piddle as pid
from math import *
import random
import sys, os
from numarray import linear_algebra as la
from numarray import ones, array, dot, swapaxes

import reaper

import svg
import webqtlUtil
from base import webqtlConfig


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


def gammln(xx):
	cof=[76.18009173,-86.50532033,24.01409822,-1.231739516,0.120858003e-2,-0.536382e-5]
	x=xx-1.0
	tmp=x+5.5
	tmp -=(x+0.5)*log(tmp)
	ser=1.0
	for item in cof:
		x+=1.0
		ser+=item/x

	return -tmp+log(2.50662827465*ser)


def gser(a,x):
	gln=gammln(a)
	ITMAX=100
	EPS=3.0e-7

	if x<=0.0:
		gamser=0.0
		return [gamser,gln]
	else:
		ap=a
		sum=1.0/a
		dele=sum
		for i in range(1,ITMAX+1):
			ap+=1.0
			dele*=x/ap
			sum+=dele
			if abs(dele)<abs(sum)*EPS:
				gamser=sum*exp(-x+a*log(x)-gln)
				return [gamser,gln]
	return None

def gcf(a,x):
	ITMAX=100
	EPS=3.0e-7
	gold=0.0
	fac=1
	b1=1.0
	b0=0.0
	a0=1.0
	gln=gammln(a)

	a1=x
	for n in range(1,ITMAX+1):
		an=n+0.0
		ana=an-a
		a0=(a1+a0*ana)*fac
		b0=(b1+b0*ana)*fac
		anf=an*fac
		a1=x*a0+anf*a1
		b1=x*b0+anf*b1
		if (a1):
			fac=1.0/a1
			g=b1*fac
			if abs((g-gold)/g)<EPS:
				gammcf=exp(-x+a*log(x)-gln)*g
				return [gammcf,gln]
			gold=g
	return None

def gammp(a,x):
	if x<0.0 or a<=0.0:
		return None
	if x<(a+1.0):
		a=gser(a,x)[0]
		return a
	else:
		a=gcf(a,x)[0]
		return 1.0-a
def U(n):
	x=pow(0.5,1.0/n)
	m=[1-x]
	for i in range(2,n):
		a=(i-0.3175)/(n+0.365)
		m.append(a)
	m.append(x)
	return m

def erf(x):
	if x<0.0:
		return -gammp(0.5,x*x)
	else:
		return gammp(0.5,x*x)

def erfcc(x):
	z=abs(x)
	t=1.0/(1.0+0.5*z)
	ans=t*exp(-z*z-1.26551223+t*(1.00002368+t*(0.37409196+t*(0.09678418+t*(-0.18628806+t*(0.27886807+t*(-1.13520398+t*(1.48851587+t*(-0.82215223+t*0.17087277)))))))))
	if x>=0.0:
		return ans
	else:
		return 2.0-ans

def calMeanVar(data):
	n=len(data)
	if n<2:
		return None
	else:
		sum=reduce(lambda x,y:x+y,data,0.0)
		mean=sum/n
		z=data[:]
		for i in range(n):
			z[i]=z[i]-mean
		variance=reduce(lambda x,y:x+y*y,z,0.0)
		variance /= n-1
		variance =sqrt(variance)
		for i in range(n):
			z[i]=z[i]/variance
		return z

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

def gmean(lst):
	N = len(lst)
	if N == 0:
		return 0
	else:
		return (reduce(lambda x,y: x+y, lst, 0.0))/N

def gmedian(lst2):
	lst = lst2[:]
	N = len(lst)
	if N == 0:
		return 0
	else:
		lst.sort()
		if N % 2 == 0:
			return (lst[N/2]+lst[(N-2)/2])/2.0
		else:
			return lst[(N-1)/2]

def gpercentile(lst2, np):
	lst = lst2[:]
	N = len(lst)
	if N == 0 or np > 100 or np < 0:
		return None
	else:
		lst.sort()
		pNadd1 = (np/100.0)*N
		k = int(pNadd1)
		d = pNadd1 - k
		if k == 0:
			return lst[0]
		elif k >= N-1:
			return lst[N-1]
		else:
			return lst[k-1] + d*(lst[k] - lst[k-1])

def findOutliers(vals):

	valsOnly = []
	dataXZ = vals[:]
	for i in range(len(dataXZ)):
		valsOnly.append(dataXZ[i][1])

	data = [('', valsOnly[:])]

	for item in data:
		itemvalue = item[1]
		nValue = len(itemvalue)
		catValue = []

		for item2 in itemvalue:
			try:
				tstrain, tvalue = item2
			except:
				tvalue = item2
			if nValue <= 4:
				continue
			else:
				catValue.append(tvalue)

		if catValue != []:
			lowHinge = gpercentile(catValue, 25)
			upHinge = gpercentile(catValue, 75)
			Hstep = 1.5*(upHinge - lowHinge)

			outlier = []
			extreme = []

			upperBound = upHinge + Hstep
			lowerBound = lowHinge - Hstep

			for item in catValue:
				if item >= upHinge + 2*Hstep:
					extreme.append(item)
				elif item >= upHinge + Hstep:
					outlier.append(item)
				else:
					pass

			for item in catValue:
				if item <= lowHinge - 2*Hstep:
					extreme.append(item)
				elif item <= lowHinge - Hstep:
					outlier.append(item)
				else:
					pass
		else:
			upperBound = 1000
			lowerBound = -1000

	return upperBound, lowerBound


def plotBoxPlot(canvas, data, offset= (40, 40, 40, 40), XLabel="Category", YLabel="Value"):
	xLeftOffset, xRightOffset, yTopOffset, yBottomOffset = offset
	plotWidth = canvas.size[0] - xLeftOffset - xRightOffset
	plotHeight = canvas.size[1] - yTopOffset - yBottomOffset
	iValues = []
	for item in data:
		for item2 in item[1]:
			try:
				iValues.append(item2[1])
			except:
				iValues.append(item2)

	#draw frame
	max_Y = max(iValues)
	min_Y = min(iValues)
	scaleY = detScale(min_Y, max_Y)
	Yll = scaleY[0]
	Yur = scaleY[1]
	nStep = scaleY[2]
	stepY = (Yur - Yll)/nStep
	stepYPixel = plotHeight/(nStep)
	canvas.drawRect(plotWidth+xLeftOffset, plotHeight + yTopOffset, xLeftOffset, yTopOffset)

	##draw Y Scale
	YYY = Yll
	YCoord = plotHeight + yTopOffset
	scaleFont=pid.Font(ttf="cour",size=11,bold=1)
	for i in range(nStep+1):
		strY = cformat(d=YYY, rank=0)
		YCoord = max(YCoord, yTopOffset)
		canvas.drawLine(xLeftOffset,YCoord,xLeftOffset-5,YCoord)
		canvas.drawString(strY,	xLeftOffset -30,YCoord +5,font=scaleFont)
		YYY += stepY
		YCoord -= stepYPixel

	##draw X Scale
	stepX = plotWidth/len(data)
	XCoord = xLeftOffset + 0.5*stepX
	YCoord = plotHeight + yTopOffset
	scaleFont = pid.Font(ttf="tahoma",size=12,bold=0)
	labelFont = pid.Font(ttf="tahoma",size=13,bold=0)
	for item in data:
		itemname, itemvalue = item
		canvas.drawLine(XCoord, YCoord,XCoord, YCoord+5, color=pid.black)
		canvas.drawString(itemname, XCoord - canvas.stringWidth(itemname,font=labelFont)/2.0,\
		YCoord +20,font=labelFont)

		nValue = len(itemvalue)
		catValue = []
		for item2 in itemvalue:
			try:
				tstrain, tvalue = item2
			except:
				tvalue = item2
			if nValue <= 4:
				canvas.drawCross(XCoord, plotHeight + yTopOffset - (tvalue-Yll)*plotHeight/(Yur - Yll), color=pid.red,size=5)
			else:
				catValue.append(tvalue)
		if catValue != []:
			catMean = gmean(catValue)
			catMedian = gmedian(catValue)
			lowHinge = gpercentile(catValue, 25)
			upHinge = gpercentile(catValue, 75)
			Hstep = 1.5*(upHinge - lowHinge)

			outlier = []
			extrem = []

			upperAdj = None
			for item in catValue:
				if item >= upHinge + 2*Hstep:
					extrem.append(item)
				elif item >= upHinge + Hstep:
					outlier.append(item)
				elif item > upHinge and  item < upHinge + Hstep:
					if upperAdj == None or item > upperAdj:
						upperAdj = item
				else:
					pass
			lowerAdj = None
			for item in catValue:
				if item <= lowHinge - 2*Hstep:
					extrem.append(item)
				elif item <= lowHinge - Hstep:
					outlier.append(item)
				if item < lowHinge and  item > lowHinge - Hstep:
					if lowerAdj == None or item < lowerAdj:
						lowerAdj = item
					else:
						pass
			canvas.drawRect(XCoord-20, plotHeight + yTopOffset - (lowHinge-Yll)*plotHeight/(Yur - Yll), \
				XCoord+20, plotHeight + yTopOffset - (upHinge-Yll)*plotHeight/(Yur - Yll))
			canvas.drawLine(XCoord-20, plotHeight + yTopOffset - (catMedian-Yll)*plotHeight/(Yur - Yll), \
				XCoord+20, plotHeight + yTopOffset - (catMedian-Yll)*plotHeight/(Yur - Yll))
			if upperAdj != None:
				canvas.drawLine(XCoord, plotHeight + yTopOffset - (upHinge-Yll)*plotHeight/(Yur - Yll), \
				XCoord, plotHeight + yTopOffset - (upperAdj-Yll)*plotHeight/(Yur - Yll))
				canvas.drawLine(XCoord-20, plotHeight + yTopOffset - (upperAdj-Yll)*plotHeight/(Yur - Yll), \
				XCoord+20, plotHeight + yTopOffset - (upperAdj-Yll)*plotHeight/(Yur - Yll))
			if lowerAdj != None:
				canvas.drawLine(XCoord, plotHeight + yTopOffset - (lowHinge-Yll)*plotHeight/(Yur - Yll), \
				XCoord, plotHeight + yTopOffset - (lowerAdj-Yll)*plotHeight/(Yur - Yll))
				canvas.drawLine(XCoord-20, plotHeight + yTopOffset - (lowerAdj-Yll)*plotHeight/(Yur - Yll), \
				XCoord+20, plotHeight + yTopOffset - (lowerAdj-Yll)*plotHeight/(Yur - Yll))

			outlierFont = pid.Font(ttf="cour",size=12,bold=0)
			if outlier != []:
				for item in outlier:
					yc = plotHeight + yTopOffset - (item-Yll)*plotHeight/(Yur - Yll)
					#canvas.drawEllipse(XCoord-3, yc-3, XCoord+3, yc+3)
					canvas.drawString('o', XCoord-3, yc+5, font=outlierFont, color=pid.orange)
			if extrem != []:
				for item in extrem:
					yc = plotHeight + yTopOffset - (item-Yll)*plotHeight/(Yur - Yll)
					#canvas.drawEllipse(XCoord-3, yc-3, XCoord+3, yc+3)
					canvas.drawString('*', XCoord-3, yc+6, font=outlierFont, color=pid.red)

			canvas.drawCross(XCoord, plotHeight + yTopOffset - (catMean-Yll)*plotHeight/(Yur - Yll), \
				color=pid.blue,size=3)
			#print (catMean, catMedian, cat25per, cat75per)
			pass

		XCoord += stepX

	labelFont=pid.Font(ttf="verdana",size=18,bold=0)
	canvas.drawString(XLabel, xLeftOffset + (plotWidth -canvas.stringWidth(XLabel,font=labelFont))/2.0, \
	YCoord +40, font=labelFont)
	canvas.drawString(YLabel,xLeftOffset-40, YCoord-(plotHeight -canvas.stringWidth(YLabel,font=labelFont))/2.0,\
	 font=labelFont, angle =90)

def plotSecurity(canvas, text="12345"):
	if not text:
		return

	plotWidth = canvas.size[0]
	plotHeight = canvas.size[1]
	if plotHeight<=0 or plotWidth<=0:
		return

	bgColor = pid.Color(0.6+0.4*random.random(), 0.6+0.4*random.random(), 0.6+0.4*random.random())
	canvas.drawRect(0,0,plotWidth,plotHeight, edgeColor=bgColor, fillColor=bgColor)

	for i in range(30):
		randomColor = pid.Color(0.6+0.4*random.random(), 0.6+0.4*random.random(), 0.6+0.4*random.random())
		scaleFont=pid.Font(ttf="cour",size=random.choice(range(20, 50)))
		canvas.drawString(random.choice('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'),
			int(random.random()*plotWidth), int(random.random()*plotHeight), font=scaleFont,
			color=randomColor, angle=random.choice(range(-45, 50)))

	step = (plotWidth-20)/len(text)
	startX = 20
	for item in text:
		randomColor = pid.Color(0.6*random.random(),0.6*random.random(), 0.6*random.random())
		scaleFont=pid.Font(ttf="verdana",size=random.choice(range(50, 60)),bold=1)
		canvas.drawString(item, startX, plotHeight/2-10, font=scaleFont,
			color=randomColor, angle=random.choice(range(-45, 50)))
		startX += step

# parameter: data is either object returned by reaper permutation function (called by MarkerRegressionPage.py)
# or the first object returned by direct (pair-scan) permu function (called by DirectPlotPage.py)
def plotBar(canvas, data, barColor=pid.blue, axesColor=pid.black, labelColor=pid.black, XLabel=None, YLabel=None, title=None, offset= (60, 20, 40, 40), zoom = 1):

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
			canvas.drawRect(xc+2,yc,xc+barWidth-2,yTopOffset+plotHeight,edgeColor=barColor,fillColor=barColor)

	#draw drawing region
	canvas.drawRect(xLeftOffset, yTopOffset, xLeftOffset+plotWidth, yTopOffset+plotHeight)

	#draw scale
	scaleFont=pid.Font(ttf="cour",size=11,bold=1)
	x=xLow
	for i in range(stepX+1):
		xc=xLeftOffset+(x-xLow)*xScale
		canvas.drawLine(xc,yTopOffset+plotHeight,xc,yTopOffset+plotHeight+5, color=axesColor)
		strX = cformat(d=x, rank=0)
		canvas.drawString(strX,xc-canvas.stringWidth(strX,font=scaleFont)/2,yTopOffset+plotHeight+14,font=scaleFont)
		x+= (xTop - xLow)/stepX

	y=yLow
	for i in range(stepY+1):
		yc=yTopOffset+plotHeight-(y-yLow)*yScale
		canvas.drawLine(xLeftOffset,yc,xLeftOffset-5,yc, color=axesColor)
		strY = "%d" %y
		canvas.drawString(strY,xLeftOffset-canvas.stringWidth(strY,font=scaleFont)-6,yc+5,font=scaleFont)
		y+= (yTop - yLow)/stepY

	#draw label
	labelFont=pid.Font(ttf="tahoma",size=17,bold=0)
	if XLabel:
		canvas.drawString(XLabel,xLeftOffset+(plotWidth-canvas.stringWidth(XLabel,font=labelFont))/2.0,
			yTopOffset+plotHeight+yBottomOffset-10,font=labelFont,color=labelColor)

	if YLabel:
		canvas.drawString(YLabel, 19, yTopOffset+plotHeight-(plotHeight-canvas.stringWidth(YLabel,font=labelFont))/2.0,
			font=labelFont,color=labelColor,angle=90)

	labelFont=pid.Font(ttf="verdana",size=16,bold=0)
	if title:
		canvas.drawString(title,xLeftOffset+(plotWidth-canvas.stringWidth(title,font=labelFont))/2.0,
			20,font=labelFont,color=labelColor)

def plotBarText(canvas, data, label, variance=None, barColor=pid.blue, axesColor=pid.black, labelColor=pid.black, XLabel=None, YLabel=None, title=None, sLabel = None, offset= (80, 20, 40, 100), barSpace = 2, zoom = 1):
	xLeftOffset, xRightOffset, yTopOffset, yBottomOffset = offset
	plotWidth = canvas.size[0] - xLeftOffset - xRightOffset
	plotHeight = canvas.size[1] - yTopOffset - yBottomOffset
	if plotHeight<=0 or plotWidth<=0:
		return

	NNN = len(data)
	if NNN < 2 or NNN != len(label):
		return
	if variance and len(variance)!=NNN:
		variance = []

	Y2 = data[:]
	if variance:
		for i in range(NNN):
			if variance[i]:
				Y2 += [data[i]-variance[i]]

	#Y axis
	YLow, YTop, stepY = detScale(min(Y2), max(Y2))
	YScale = plotHeight/(YTop - YLow)

	if YLow < 0  and  YTop > 0:
		drawZero = 1
	else:
		drawZero = 0

	#X axis
	X = range(NNN)
	Xll= 0
	Xur= NNN-1


	if drawZero:
		YZero = yTopOffset+plotHeight-YScale*(0-YLow)
		canvas.drawLine(xLeftOffset, YZero, xLeftOffset+plotWidth, YZero)
	else:
		YZero = yTopOffset+plotHeight
	#draw data
	spaceWidth = barSpace
	if spaceWidth < 1:
		spaceWidth = 1
	barWidth = int((plotWidth - (NNN-1.0)*spaceWidth)/NNN)

	xc= xLeftOffset
	scaleFont=pid.Font(ttf="verdana",size=11,bold=0)
	for i in range(NNN):
		yc = yTopOffset+plotHeight-(data[i]-YLow)*YScale
		canvas.drawRect(xc,YZero,xc+barWidth-1, yc, edgeColor=barColor,fillColor=barColor)
		if variance and variance[i]:
			varlen = variance[i]*YScale
			if yc-varlen < yTopOffset:
				topYd = yTopOffset
			else:
				topYd = yc-varlen
				canvas.drawLine(xc+barWidth/2-2,yc-varlen,xc+barWidth/2+2,yc-varlen,color=pid.red)
			canvas.drawLine(xc+barWidth/2,yc+varlen,xc+barWidth/2,topYd,color=pid.red)
			canvas.drawLine(xc+barWidth/2-2,yc+varlen,xc+barWidth/2+2,yc+varlen,color=pid.red)
		strX = label[i]
		canvas.drawString(strX,xc+barWidth/2.0+2,yTopOffset+plotHeight+2+canvas.stringWidth(strX,font=scaleFont),font=scaleFont,angle=90)
		xc += barWidth + spaceWidth

	#draw drawing region
	canvas.drawRect(xLeftOffset, yTopOffset, xLeftOffset+plotWidth, yTopOffset+plotHeight)

	#draw Y scale
	scaleFont=pid.Font(ttf="cour",size=16,bold=1)
	y=YLow
	for i in range(stepY+1):
		yc=yTopOffset+plotHeight-(y-YLow)*YScale
		canvas.drawLine(xLeftOffset,yc,xLeftOffset-5,yc, color=axesColor)
		strY = cformat(d=y, rank=0)
		canvas.drawString(strY,xLeftOffset-canvas.stringWidth(strY,font=scaleFont)-6,yc+5,font=scaleFont)
		y+= (YTop - YLow)/stepY

	#draw label
	labelFont=pid.Font(ttf="verdana",size=17,bold=0)
	if XLabel:
		canvas.drawString(XLabel,xLeftOffset+(plotWidth-canvas.stringWidth(XLabel,font=labelFont))/2.0,yTopOffset+plotHeight+65,font=labelFont,color=labelColor)

	if YLabel:
		canvas.drawString(YLabel,xLeftOffset-50, yTopOffset+plotHeight-(plotHeight-canvas.stringWidth(YLabel,font=labelFont))/2.0,font=labelFont,color=labelColor,angle=90)

	labelFont=pid.Font(ttf="verdana",size=18,bold=0)
	if title:
		canvas.drawString(title,xLeftOffset,yTopOffset-15,font=labelFont,color=labelColor)

	return

def plotXY(canvas, dataX, dataY, rank=0, dataLabel=[], plotColor = pid.black, axesColor=pid.black, labelColor=pid.black, lineSize="thin", lineColor=pid.grey, idFont="arial", idColor=pid.blue, idSize="14", symbolColor=pid.black, symbolType="circle", filled="yes", symbolSize="tiny", XLabel=None, YLabel=None, title=None, fitcurve=None, connectdot=1, displayR=None, loadingPlot = 0, offset= (80, 20, 40, 60), zoom = 1, specialCases=[], showLabel = 1, bufferSpace = 15):
	'displayR : correlation scatter plot, loadings : loading plot'

	dataXRanked, dataYRanked = webqtlUtil.calRank(dataX, dataY, len(dataX))

	#get ID font size
	idFontSize = int(idSize)

	#If filled is yes, set fill color
	if filled == "yes":
		fillColor = symbolColor
	else:
		fillColor = None

	if symbolSize == "large":
		sizeModifier = 7
		fontModifier = 12
	elif symbolSize == "medium":
		sizeModifier = 5
		fontModifier = 8
	elif symbolSize == "small":
		sizeModifier = 3
		fontModifier = 3
	else:
		sizeModifier = 1
		fontModifier = -1

	if rank == 0:    # Pearson correlation
		bufferSpace = 0
		dataXPrimary = dataX
		dataYPrimary = dataY
		dataXAlt = dataXRanked    #Values used just for printing the other corr type to the graph image
		dataYAlt = dataYRanked    #Values used just for printing the other corr type to the graph image
	else:    # Spearman correlation: Switching Ranked and Unranked X and Y values
		dataXPrimary = dataXRanked
		dataYPrimary = dataYRanked
		dataXAlt = dataX    #Values used just for printing the other corr type to the graph image
		dataYAlt = dataY    #Values used just for printing the other corr type to the graph image

	xLeftOffset, xRightOffset, yTopOffset, yBottomOffset = offset
	plotWidth = canvas.size[0] - xLeftOffset - xRightOffset
	plotHeight = canvas.size[1] - yTopOffset - yBottomOffset
	if plotHeight<=0 or plotWidth<=0:
		return
	if len(dataXPrimary) < 1 or  len(dataXPrimary) != len(dataYPrimary) or (dataLabel and len(dataXPrimary) != len(dataLabel)):
		return

	max_X=max(dataXPrimary)
	min_X=min(dataXPrimary)
	max_Y=max(dataYPrimary)
	min_Y=min(dataYPrimary)

	#for some reason I forgot why I need to do this
	if loadingPlot:
		min_X = min(-0.1,min_X)
		max_X = max(0.1,max_X)
		min_Y = min(-0.1,min_Y)
		max_Y = max(0.1,max_Y)

	xLow, xTop, stepX=detScale(min_X,max_X)
	yLow, yTop, stepY=detScale(min_Y,max_Y)
	xScale = plotWidth/(xTop-xLow)
	yScale = plotHeight/(yTop-yLow)

	#draw drawing region
	canvas.drawRect(xLeftOffset-bufferSpace, yTopOffset, xLeftOffset+plotWidth, yTopOffset+plotHeight+bufferSpace)
	canvas.drawRect(xLeftOffset-bufferSpace+1, yTopOffset, xLeftOffset+plotWidth, yTopOffset+plotHeight+bufferSpace-1)

	#calculate data points
	data = map(lambda X, Y: (X, Y), dataXPrimary, dataYPrimary)
	xCoord = map(lambda X, Y: ((X-xLow)*xScale + xLeftOffset, yTopOffset+plotHeight-(Y-yLow)*yScale), dataXPrimary, dataYPrimary)

	labelFont=pid.Font(ttf=idFont,size=idFontSize,bold=0)

	if loadingPlot:
		xZero = -xLow*xScale+xLeftOffset
		yZero = yTopOffset+plotHeight+yLow*yScale
		for point in xCoord:
			canvas.drawLine(xZero,yZero,point[0],point[1],color=pid.red)
	else:
		if connectdot:
			canvas.drawPolygon(xCoord,edgeColor=plotColor,closed=0)
		else:
			pass

	symbolFont = pid.Font(ttf="fnt_bs", size=12+fontModifier,bold=0)

	for i, item in enumerate(xCoord):
		if dataLabel and dataLabel[i] in specialCases:
			canvas.drawRect(item[0]-3, item[1]-3, item[0]+3, item[1]+3, edgeColor=pid.green)
			#canvas.drawCross(item[0],item[1],color=pid.blue,size=5)
		else:
			if symbolType == "vertRect":
				canvas.drawRect(x1=item[0]-sizeModifier+2,y1=item[1]-sizeModifier-2, x2=item[0]+sizeModifier-1,y2=item[1]+sizeModifier+2, edgeColor=symbolColor, edgeWidth=1, fillColor=fillColor)
			elif (symbolType == "circle" and filled != "yes"):
				canvas.drawString(":", item[0]-canvas.stringWidth(":",font=symbolFont)/2+1,item[1]+2,color=symbolColor, font=symbolFont)
			elif (symbolType == "circle" and filled == "yes"):
				canvas.drawString("5", item[0]-canvas.stringWidth("5",font=symbolFont)/2+1,item[1]+2,color=symbolColor, font=symbolFont)
			elif symbolType == "horiRect":
				canvas.drawRect(x1=item[0]-sizeModifier-1,y1=item[1]-sizeModifier+3, x2=item[0]+sizeModifier+3,y2=item[1]+sizeModifier-2, edgeColor=symbolColor, edgeWidth=1, fillColor=fillColor)
			elif (symbolType == "square"):
				canvas.drawRect(x1=item[0]-sizeModifier+1,y1=item[1]-sizeModifier-4, x2=item[0]+sizeModifier+2,y2=item[1]+sizeModifier-3, edgeColor=symbolColor, edgeWidth=1, fillColor=fillColor)
			elif (symbolType == "diamond" and filled != "yes"):
				canvas.drawString(",", item[0]-canvas.stringWidth(",",font=symbolFont)/2+2, item[1]+6, font=symbolFont, color=symbolColor)
			elif (symbolType == "diamond" and filled == "yes"):
				canvas.drawString("D", item[0]-canvas.stringWidth("D",font=symbolFont)/2+2, item[1]+6, font=symbolFont, color=symbolColor)
			elif symbolType == "4-star":
				canvas.drawString("l", item[0]-canvas.stringWidth("l",font=symbolFont)/2+1, item[1]+3, font=symbolFont, color=symbolColor)
			elif symbolType == "3-star":
				canvas.drawString("k", item[0]-canvas.stringWidth("k",font=symbolFont)/2+1, item[1]+3, font=symbolFont, color=symbolColor)
			else:
				canvas.drawCross(item[0],item[1]-2,color=symbolColor, size=sizeModifier+2)

		if showLabel and dataLabel:
			if (symbolType == "vertRect" or symbolType == "diamond"):
				labelGap = 15
			elif (symbolType == "4-star" or symbolType == "3-star"):
				labelGap = 12
			else:
			    labelGap = 11
			canvas.drawString(dataLabel[i], item[0]- canvas.stringWidth(dataLabel[i],
				font=labelFont)/2 + 1, item[1]+(labelGap+sizeModifier+(idFontSize-12)), font=labelFont, color=idColor)

	#draw scale
	scaleFont=pid.Font(ttf="cour",size=16,bold=1)


	x=xLow
	for i in range(stepX+1):
		xc=xLeftOffset+(x-xLow)*xScale
		if ((x == 0) & (rank == 1)):
			pass
		else:
			canvas.drawLine(xc,yTopOffset+plotHeight + bufferSpace,xc,yTopOffset+plotHeight+5 + bufferSpace, color=axesColor)
		strX = cformat(d=x, rank=rank)
		if ((strX == "0") & (rank == 1)):
			pass
		else:
			canvas.drawString(strX,xc-canvas.stringWidth(strX,font=scaleFont)/2,yTopOffset+plotHeight+20 + bufferSpace,font=scaleFont)
		x+= (xTop - xLow)/stepX

	y=yLow
	for i in range(stepY+1):
		yc=yTopOffset+plotHeight-(y-yLow)*yScale
		if ((y == 0) & (rank == 1)):
			pass
		else:
			canvas.drawLine(xLeftOffset - bufferSpace,yc,xLeftOffset-5 - bufferSpace,yc, color=axesColor)
		strY = cformat(d=y, rank=rank)
		if ((strY == "0") & (rank == 1)):
			pass
		else:
			canvas.drawString(strY,xLeftOffset-canvas.stringWidth(strY,font=scaleFont)- 10 - bufferSpace,yc+4,font=scaleFont)
		y+= (yTop - yLow)/stepY

	#draw label

	labelFont=pid.Font(ttf="verdana",size=canvas.size[0]/45,bold=0)
	titleFont=pid.Font(ttf="verdana",size=canvas.size[0]/40,bold=0)

	if (rank == 1 and not title):
		canvas.drawString("Spearman Rank Correlation", xLeftOffset-canvas.size[0]*.025+(plotWidth-canvas.stringWidth("Spearman Rank Correlation",font=titleFont))/2.0,
						  25,font=titleFont,color=labelColor)
	elif (rank == 0 and not title):
		canvas.drawString("Pearson Correlation", xLeftOffset-canvas.size[0]*.025+(plotWidth-canvas.stringWidth("Pearson Correlation",font=titleFont))/2.0,
						  25,font=titleFont,color=labelColor)

	if XLabel:
		canvas.drawString(XLabel,xLeftOffset+(plotWidth-canvas.stringWidth(XLabel,font=labelFont))/2.0,
			yTopOffset+plotHeight+yBottomOffset-25,font=labelFont,color=labelColor)

	if YLabel:
		canvas.drawString(YLabel, xLeftOffset-65, yTopOffset+plotHeight- (plotHeight-canvas.stringWidth(YLabel,font=labelFont))/2.0,
			font=labelFont,color=labelColor,angle=90)

	labelFont=pid.Font(ttf="verdana",size=20,bold=0)
	if title:
		canvas.drawString(title,xLeftOffset+(plotWidth-canvas.stringWidth(title,font=labelFont))/2.0,
			20,font=labelFont,color=labelColor)

	if fitcurve:
		import sys
		sys.argv = [ "mod_python" ]
		#from numarray import linear_algebra as la
		#from numarray import ones, array, dot, swapaxes
		fitYY = array(dataYPrimary)
		fitXX = array([ones(len(dataXPrimary)),dataXPrimary])
		AA = dot(fitXX,swapaxes(fitXX,0,1))
		BB = dot(fitXX,fitYY)
		bb = la.linear_least_squares(AA,BB)[0]

		xc1 = xLeftOffset
		yc1 = yTopOffset+plotHeight-(bb[0]+bb[1]*xLow-yLow)*yScale
		if yc1 > yTopOffset+plotHeight:
			yc1 = yTopOffset+plotHeight
			xc1 = (yLow-bb[0])/bb[1]
			xc1=(xc1-xLow)*xScale+xLeftOffset
		elif yc1 < yTopOffset:
			yc1 = yTopOffset
			xc1 = (yTop-bb[0])/bb[1]
			xc1=(xc1-xLow)*xScale+xLeftOffset
		else:
			pass

		xc2 = xLeftOffset + plotWidth
		yc2 = yTopOffset+plotHeight-(bb[0]+bb[1]*xTop-yLow)*yScale
		if yc2 > yTopOffset+plotHeight:
			yc2 = yTopOffset+plotHeight
			xc2 = (yLow-bb[0])/bb[1]
			xc2=(xc2-xLow)*xScale+xLeftOffset
		elif yc2 < yTopOffset:
			yc2 = yTopOffset
			xc2 = (yTop-bb[0])/bb[1]
			xc2=(xc2-xLow)*xScale+xLeftOffset
		else:
			pass

		canvas.drawLine(xc1 - bufferSpace,yc1 + bufferSpace,xc2,yc2,color=lineColor)
		if lineSize == "medium":
			canvas.drawLine(xc1 - bufferSpace,yc1 + bufferSpace+1,xc2,yc2+1,color=lineColor)
		if lineSize == "thick":
			canvas.drawLine(xc1 - bufferSpace,yc1 + bufferSpace+1,xc2,yc2+1,color=lineColor)
			canvas.drawLine(xc1 - bufferSpace,yc1 + bufferSpace-1,xc2,yc2-1,color=lineColor)


	if displayR:
		labelFont=pid.Font(ttf="trebuc",size=canvas.size[0]/60,bold=0)
		NNN = len(dataX)
		corr = webqtlUtil.calCorrelation(dataXPrimary,dataYPrimary,NNN)[0]

		if NNN < 3:
			corrPValue = 1.0
		else:
			if abs(corr) >= 1.0:
				corrPValue = 0.0
			else:
				ZValue = 0.5*log((1.0+corr)/(1.0-corr))
				ZValue = ZValue*sqrt(NNN-3)
				corrPValue = 2.0*(1.0 - reaper.normp(abs(ZValue)))

		NStr = "N = %d" % NNN
		strLenN = canvas.stringWidth(NStr,font=labelFont)

		if rank == 1:
		    if corrPValue < 0.0000000000000001:
				corrStr = "Rho = %1.3f P < 1.00 E-16" % (corr)
		    else:
				corrStr = "Rho = %1.3f P = %3.2E" % (corr, corrPValue)
		else:
		    if corrPValue < 0.0000000000000001:
				corrStr = "r = %1.3f P < 1.00 E-16" % (corr)
		    else:
				corrStr = "r = %1.3f P = %3.2E" % (corr, corrPValue)
		strLen = canvas.stringWidth(corrStr,font=labelFont)

		canvas.drawString(NStr,xLeftOffset,yTopOffset-10,font=labelFont,color=labelColor)
		canvas.drawString(corrStr,xLeftOffset+plotWidth-strLen,yTopOffset-10,font=labelFont,color=labelColor)

	return xCoord

def plotXYSVG(drawSpace, dataX, dataY, rank=0, dataLabel=[], plotColor = "black", axesColor="black", labelColor="black", symbolColor="red", XLabel=None, YLabel=None, title=None, fitcurve=None, connectdot=1, displayR=None, loadingPlot = 0, offset= (80, 20, 40, 60), zoom = 1, specialCases=[], showLabel = 1):
	'displayR : correlation scatter plot, loadings : loading plot'

	dataXRanked, dataYRanked = webqtlUtil.calRank(dataX, dataY, len(dataX))

	# Switching Ranked and Unranked X and Y values if a Spearman Rank Correlation
	if rank == 0:
		dataXPrimary = dataX
		dataYPrimary = dataY
		dataXAlt = dataXRanked
		dataYAlt = dataYRanked

	else:
		dataXPrimary = dataXRanked
		dataYPrimary = dataYRanked
		dataXAlt = dataX
		dataYAlt = dataY



	xLeftOffset, xRightOffset, yTopOffset, yBottomOffset = offset
	plotWidth = drawSpace.attributes['width'] - xLeftOffset - xRightOffset
	plotHeight = drawSpace.attributes['height'] - yTopOffset - yBottomOffset
	if plotHeight<=0 or plotWidth<=0:
		return
	if len(dataXPrimary) < 1 or  len(dataXPrimary) != len(dataYPrimary) or (dataLabel and len(dataXPrimary) != len(dataLabel)):
		return

	max_X=max(dataXPrimary)
	min_X=min(dataXPrimary)
	max_Y=max(dataYPrimary)
	min_Y=min(dataYPrimary)

	#for some reason I forgot why I need to do this
	if loadingPlot:
		min_X = min(-0.1,min_X)
		max_X = max(0.1,max_X)
		min_Y = min(-0.1,min_Y)
		max_Y = max(0.1,max_Y)

	xLow, xTop, stepX=detScale(min_X,max_X)
	yLow, yTop, stepY=detScale(min_Y,max_Y)
	xScale = plotWidth/(xTop-xLow)
	yScale = plotHeight/(yTop-yLow)

	#draw drawing region
	r = svg.rect(xLeftOffset, yTopOffset, plotWidth,  plotHeight, 'none', axesColor, 1)
	drawSpace.addElement(r)

	#calculate data points
	data = map(lambda X, Y: (X, Y), dataXPrimary, dataYPrimary)
	xCoord = map(lambda X, Y: ((X-xLow)*xScale + xLeftOffset, yTopOffset+plotHeight-(Y-yLow)*yScale), dataXPrimary, dataYPrimary)
	labelFontF = "verdana"
	labelFontS = 11

	if loadingPlot:
		xZero = -xLow*xScale+xLeftOffset
		yZero = yTopOffset+plotHeight+yLow*yScale
		for point in xCoord:
			drawSpace.addElement(svg.line(xZero,yZero,point[0],point[1], "red", 1))
	else:
		if connectdot:
			pass
			#drawSpace.drawPolygon(xCoord,edgeColor=plotColor,closed=0)
		else:
			pass

	for i, item in enumerate(xCoord):
		if dataLabel and dataLabel[i] in specialCases:
			drawSpace.addElement(svg.rect(item[0]-3, item[1]-3, 6, 6, "none", "green", 0.5))
			#drawSpace.drawCross(item[0],item[1],color=pid.blue,size=5)
		else:
			drawSpace.addElement(svg.line(item[0],item[1]+5,item[0],item[1]-5,symbolColor,1))
			drawSpace.addElement(svg.line(item[0]+5,item[1],item[0]-5,item[1],symbolColor,1))
		if showLabel and dataLabel:
			pass
			drawSpace.addElement(svg.text(item[0], item[1]+14, dataLabel[i], labelFontS,
				labelFontF, text_anchor="middle", style="stroke:blue;stroke-width:0.5;"))
			#canvas.drawString(, item[0]- canvas.stringWidth(dataLabel[i],
			#	font=labelFont)/2, item[1]+14, font=labelFont, color=pid.blue)

	#draw scale
	#scaleFont=pid.Font(ttf="cour",size=14,bold=1)
	x=xLow
	for i in range(stepX+1):
		xc=xLeftOffset+(x-xLow)*xScale
		drawSpace.addElement(svg.line(xc,yTopOffset+plotHeight,xc,yTopOffset+plotHeight+5, axesColor, 1))
		strX = cformat(d=x, rank=rank)
		drawSpace.addElement(svg.text(xc,yTopOffset+plotHeight+20,strX,13, "courier", text_anchor="middle"))
		x+= (xTop - xLow)/stepX

	y=yLow
	for i in range(stepY+1):
		yc=yTopOffset+plotHeight-(y-yLow)*yScale
		drawSpace.addElement(svg.line(xLeftOffset,yc,xLeftOffset-5,yc, axesColor, 1))
		strY = cformat(d=y, rank=rank)
		drawSpace.addElement(svg.text(xLeftOffset-10,yc+5,strY,13, "courier", text_anchor="end"))
		y+= (yTop - yLow)/stepY

	#draw label
	labelFontF = "verdana"
	labelFontS = 17
	if XLabel:
		drawSpace.addElement(svg.text(xLeftOffset+plotWidth/2.0,
			yTopOffset+plotHeight+yBottomOffset-10,XLabel,
			labelFontS, labelFontF, text_anchor="middle"))

	if YLabel:
		drawSpace.addElement(svg.text(xLeftOffset-50,
			 yTopOffset+plotHeight/2,YLabel,
			labelFontS, labelFontF, text_anchor="middle", style="writing-mode:tb-rl", transform="rotate(270 %d %d)" % (xLeftOffset-50,  yTopOffset+plotHeight/2)))
		#drawSpace.drawString(YLabel, xLeftOffset-50, yTopOffset+plotHeight- (plotHeight-drawSpace.stringWidth(YLabel,font=labelFont))/2.0,
		#	font=labelFont,color=labelColor,angle=90)


	if fitcurve:
		sys.argv = [ "mod_python" ]
                #from numarray import linear_algebra as la
		#from numarray import ones, array, dot, swapaxes
		fitYY = array(dataYPrimary)
		fitXX = array([ones(len(dataXPrimary)),dataXPrimary])
		AA = dot(fitXX,swapaxes(fitXX,0,1))
		BB = dot(fitXX,fitYY)
		bb = la.linear_least_squares(AA,BB)[0]

		xc1 = xLeftOffset
		yc1 = yTopOffset+plotHeight-(bb[0]+bb[1]*xLow-yLow)*yScale
		if yc1 > yTopOffset+plotHeight:
			yc1 = yTopOffset+plotHeight
			xc1 = (yLow-bb[0])/bb[1]
			xc1=(xc1-xLow)*xScale+xLeftOffset
		elif yc1 < yTopOffset:
			yc1 = yTopOffset
			xc1 = (yTop-bb[0])/bb[1]
			xc1=(xc1-xLow)*xScale+xLeftOffset
		else:
			pass

		xc2 = xLeftOffset + plotWidth
		yc2 = yTopOffset+plotHeight-(bb[0]+bb[1]*xTop-yLow)*yScale
		if yc2 > yTopOffset+plotHeight:
			yc2 = yTopOffset+plotHeight
			xc2 = (yLow-bb[0])/bb[1]
			xc2=(xc2-xLow)*xScale+xLeftOffset
		elif yc2 < yTopOffset:
			yc2 = yTopOffset
			xc2 = (yTop-bb[0])/bb[1]
			xc2=(xc2-xLow)*xScale+xLeftOffset
		else:
			pass

		drawSpace.addElement(svg.line(xc1,yc1,xc2,yc2,"green", 1))

	if displayR:
		labelFontF = "trebuc"
		labelFontS = 14
		NNN = len(dataX)

		corr = webqtlUtil.calCorrelation(dataXPrimary,dataYPrimary,NNN)[0]

		if NNN < 3:
			corrPValue = 1.0
		else:
			if abs(corr) >= 1.0:
				corrPValue = 0.0
			else:
				ZValue = 0.5*log((1.0+corr)/(1.0-corr))
				ZValue = ZValue*sqrt(NNN-3)
				corrPValue = 2.0*(1.0 - reaper.normp(abs(ZValue)))

		NStr = "N of Cases=%d" % NNN

		if rank == 1:
			corrStr = "Spearman's r=%1.3f P=%3.2E" % (corr, corrPValue)
		else:
			corrStr = "Pearson's r=%1.3f P=%3.2E" % (corr, corrPValue)

		drawSpace.addElement(svg.text(xLeftOffset,yTopOffset-10,NStr,
			labelFontS, labelFontF, text_anchor="start"))
		drawSpace.addElement(svg.text(xLeftOffset+plotWidth,yTopOffset-25,corrStr,
			labelFontS, labelFontF, text_anchor="end"))
	"""
	"""
	return


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

def detScale(min=0,max=0,bufferSpace=3):

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



def colorSpectrumOld(n):
	if n == 1:
		return [pid.Color(1,0,0)]
	elif n == 2:
		return [pid.Color(1,0,0),pid.Color(0,0,1)]
	elif n == 3:
		return [pid.Color(1,0,0),pid.Color(0,1,0),pid.Color(0,0,1)]
	else:
		step = 2.0/(n-1)
		red = 1.0
		green = 0.0
		blue = 0.0
		colors = [pid.Color(red,green,blue)]
		i = 1
		greenpeak = 0
		while i < n:
			if red >= step:
				red -= step
				green += step
				if green >= 1.0:
					greenpeak = 1
					blue += green -1.0
					green = 1.0
			else:
				red = 0.0
				if greenpeak:
					green -= step
					blue += step
				else:
					green += step
				if green >= 1.0:
					greenpeak = 1
					blue += green -1.0
					green = 2.0 -green
				elif green < 0.0:
					green = 0.0
				else:
					pass
			colors.append(pid.Color(red,green,blue))
			i += 1
		return colors




def bluefunc(x):
	return 1.0 / (1.0 + exp(-10*(x-0.6)))


def redfunc(x):
	return 1.0 / (1.0 + exp(10*(x-0.5)))

def greenfunc(x):
	return 1 - pow(redfunc(x+0.2),2) - bluefunc(x-0.3)

def colorSpectrum(n=100):
	multiple = 10
	if n == 1:
		return [pid.Color(1,0,0)]
	elif n == 2:
		return [pid.Color(1,0,0),pid.Color(0,0,1)]
	elif n == 3:
		return [pid.Color(1,0,0),pid.Color(0,1,0),pid.Color(0,0,1)]
	N = n*multiple
	out = [None]*N;
	for i in range(N):
		x = float(i)/N
		out[i] = pid.Color(redfunc(x), greenfunc(x), bluefunc(x));
	out2 = [out[0]]
	step = N/float(n-1)
	j = 0
	for i in range(n-2):
		j += step
		out2.append(out[int(j)])
	out2.append(out[-1])
	return out2


def colorSpectrumSVG(n=100):
	multiple = 10
	if n == 1:
		return ["rgb(255,0,0)"]
	elif n == 2:
		return ["rgb(255,0,0)","rgb(0,0,255)"]
	elif n == 3:
		return ["rgb(255,0,0)","rgb(0,255,0)","rgb(0,0,255)"]
	N = n*multiple
	out = [None]*N;
	for i in range(N):
		x = float(i)/N
		out[i] = "rgb(%d, %d, %d)" % (redfunc(x)*255, greenfunc(x)*255, bluefunc(x)*255);
	out2 = [out[0]]
	step = N/float(n-1)
	j = 0
	for i in range(n-2):
		j += step
		out2.append(out[int(j)])
	out2.append(out[-1])
	return out2


def BWSpectrum(n=100):
	multiple = 10
	if n == 1:
		return [pid.Color(0,0,0)]
	elif n == 2:
		return [pid.Color(0,0,0),pid.Color(1,1,1)]
	elif n == 3:
		return [pid.Color(0,0,0),pid.Color(0.5,0.5,0.5),pid.Color(1,1,1)]

	step = 1.0/n
	x = 0.0
	out = []
	for i in range(n):
		out.append(pid.Color(x,x,x));
		x += step
	return out
