# Created by Luis Del Mar for GeneNetwork.org
# Email: ladelmar99@gmail.com
# LinkedIn: https://www.linkedin.com/in/luis-del-mar/
# GitHub: https://github.com/ladm99
# This script performs the following normalizations to a specific tab delimited dataset:
# 1. Average 2. Log2 normalize 3. ZScore Normaliza 4. Outlier detection 
#!/usr/bin/env python

from tkinter import Tk
from tkinter.filedialog import askopenfilename
import math
import traceback
import os

# method for file selection
def fileSelector():
	# Code from: https://stackoverflow.com/questions/3579568/choosing-a-file-in-python-with-simple-dialog
	Tk().withdraw() # we don't want a full GUI, so keep the root window from appearing
	filename = askopenfilename() # show an "Open" dialog box and return the path to the selected file
	return filename

# method for getting skipRow and skipCol
def skips():
	while True:
		skipRow = 0
		skipCol = 0
		r = input('Enter the number of rows that you wish skip (default is 0): ').strip()
		c = input('Enter the number of columns that you wish skip (default is 0): ').strip()
		try:
			if r != '':
				skipRow = int(r)
			if c != '':
				skipCol = int(c)
			return skipRow, skipCol
		except Exception as e:
			input('Enter a valid value')

# gets the mean of an array
def getMean(values):
	mean = 0.0
	for i in values:
		mean+=i
	mean /= len(values)
	return mean

# gets the standard deviation of an array
def getSTD(values):
	mean = getMean(values)
	phi = 0.0

	for i in values:
		phi += abs((i - mean)) ** 2
	phi = math.sqrt((phi/(len(values) - 1)))
	return phi


def log2Normalize(inputFile):
	try:
		skipRow, skipCol = skips()
		print(':Log2 normalize processing...looking for the minimal expression value')
		f = open('%s' % inputFile, 'r')
		# set min to max value
		min = float('inf')

		for i in range(skipRow + 1):
			f.readline()
		while True:
			data =f.readline()
			if not data:
				break
			else:
				s = data.split('\t')
				for j in range(skipCol + 1, len(s)):
					value = 0.0
					try:
						value = float(s[j])
						if min > value:
							min = value
					except Exception as e:
						pass
		f.close()
		print('Log2 normalize processing...calculating')
		f = open('%s' % inputFile, 'r')
		outputFile = os.path.split(inputFile)[1].replace('.txt', '_log2.txt')
		out = open(outputFile,'w')

		offset = 1.0
		if min < 0.0:
			offset = -min + 1.0
		for i in range(skipRow + 1):
			out.write(f.readline())
		linenum = 0
		while True:
			data = f.readline()
			if not data:
				break
			else:
				s = data.split('\t')
				for j in range(skipCol + 1):
					out.write(s[j] + '\t')
				for j in range(skipCol + 1, len(s)):
					try:
						value = math.log(float(s[j]) + offset) / math.log(2.0)
						out.write(str(round(value,3)) + '\t')
					except Exception as e:
						out.write('x')
						out.write('\t')
				out.write('\n')
				linenum +=1
				if linenum % 2500 == 0:
					print('Log2 normalize processing...finished' + str(linenum) + ' lines')
		f.close()
		out.close()
		print('Log2 normalize finished')
	except Exception as e:
		print(traceback.format_exc())

def ZScoreNormalize(inputFile):
	try:
		skipRow, skipCol = skips()
		print('ZScore normalize processing...calculating means')
		f = open('%s' % inputFile, 'r')
		for n in range(skipRow):
			f.readline()
		# skip first row which is just headers
		s = f.readline().split('\t')	
		col = len(s) - skipCol - 1
		# mean and phi lists are filled with 0.00
		mean = [0.00] * col
		phi = [0.00] * col

		row = 0

		# read to the end of the file
		while True:
			data = 	f.readline()
			if not data:
				break
			else:
				# put values into a list
				s = data.split('\t')
				for m in range(skipCol + 1, len(s)):
					try:
						mean[m - skipCol - 1] = mean[m - skipCol - 1] + float(s[m])
					except Exception as e:
						pass
				row+=1

		f.close()

		for m in range(col):
			mean[m] = mean[m] / row
		print('ZScore normalize processing...calculating standard divisions')
		f = open('%s' % inputFile, 'r')
		for k in range(skipRow + 1):
			# skip headers
			f.readline()
		while True:
			data = f.readline()
			if not data:
				break
			else:
				s = data.split('\t')
				for i1 in range(skipCol + 1, len(s)):
					value = 0.0
					try:
						value = float(s[i1])
						phi[i1 - skipCol - 1] = phi[i1 - skipCol - 1] + (value - mean[i1 - skipCol - 1]) ** 2
					except Exception as e:
						pass
					
		f.close()
		for j in range(col):
			phi[j] = math.sqrt(phi[j] / (row - 1))
			# print(str(mean[j]) + '\t' + str(phi[j]))

		outputFile = os.path.split(inputFile)[1].replace('.txt', '_Z.txt')
		f = open('%s' % inputFile, 'r')
		out = open(outputFile,'w')

		for i in range(skipRow + 1):
			out.write(f.readline())

		row = 0
		while True:
			data = f.readline()
			if not data:
				break
			else:
				s = data.split('\t')
				for i1 in range(skipRow + 1):
					out.write(s[i1] + '\t')
				for i1 in range(skipCol + 1, len(s)):
					try:
						value = float(s[i1])
						value = 2.0 * (value - mean[i1 - skipCol - 1]) / phi[i1 - skipCol - 1] + 8.0
						out.write(str(round(value, 3)) + '\t')
					except Exception as e:
						out.write('x' + '\t')
					

				out.write('\n')
				row+=1
				if row % 2500 == 0:
					print('ZScore normalize processing...finished ' + str(row) + ' lines')

		f.close()
		out.close()
		print('ZScore normalize finished')
	except Exception as e:
		print(e)

# find the average of values with column names that are the same
def average(inputFile, needSE):
	try:
		skipRow, skipCol = skips()
		f = open('%s' % inputFile, 'r')
		outputFile = os.path.split(inputFile)[1].replace('.txt', '_Avg.txt')
		out = open(outputFile,'w')

		titleList = [] # will hold all of the titles, used for getting indices for values
		itemList = [] # will hold all the unique titles

		# skips the appropriate amount of rows
		for i in range(skipRow):
			s = f.readline()
			out.write(s + '\n')

		s = f.readline().split('\t')
		for i in range(len(s)):
			s[i] = s[i].strip()
			titleList.append(s[i])
			if s[i] not in itemList and i > skipCol:
				itemList.append(s[i])

		for i in range(skipCol + 1):
			out.write(titleList[i])
			out.write('\t')

		for i in range(len(itemList)):
			out.write(itemList[i])
			if i < len(itemList) - 1:
				out.write('\t')
		out.write('\n')

		line = 0
		while True:
			data = f.readline()
			if not data:
				break
			else:
				s = data.split('\t')
				for j in range(skipCol + 1):
					out.write(str(s[j]) + '\t')

				for j in range(len(itemList)):
					avgItemValue = 0.0
					n = 0
					at = titleList.index(itemList[j])
					while(at >= 0):
						try:
							avgItemValue += float(s[at])
							n+=1
							at = titleList.index(itemList[j], at + 1)
						except Exception as e:
							at = -1
					if n == 0:
						out.write('x\t')
					else:
						avgItemValue /= n
						out.write(str(round(avgItemValue, 4)))
					if j < len(itemList) - 1:
						out.write('\t')

				out.write('\n')
				line +=1

				if line % 1000 == 0:
					print('Processing average...' + str(line) + ' lines\n')

		f.close()
		out.close()
	except Exception as e:
		print(traceback.format_exc())

	if needSE:
		getSE(inputFile, skipRow, skipCol)

# find the SE of the average of the values
def getSE(inputFile, skipRow, skipCol):
	try:
		f = open('%s' % inputFile, 'r')
		outputFile = os.path.split(inputFile)[1].replace('.txt', '_Avg_SE.txt')
		out = open(outputFile,'w')

		titleList = [] # will hold all of the titles, used for getting indices for values
		itemList = [] # will hold all the unique titles

		# skips the appropriate amount of rows
		for i in range(skipRow):
			s = f.readline()
			out.write(s + '\n')

		s = f.readline().split('\t')
		for i in range(len(s)):
			s[i] = s[i].strip()
			titleList.append(s[i])
			if s[i] not in itemList and i > skipCol:
				itemList.append(s[i])

		for i in range(skipCol + 1):
			out.write(titleList[i])
			out.write('\t')

		for i in range(len(itemList)):
			out.write(itemList[i])
			if i < len(itemList) - 1:
				out.write('\t')
		out.write('\n')

		line = 0
		while True:
			data = f.readline()
			if not data:
				break
			else:
				s = data.split('\t')
				for j in range(skipCol + 1):
					out.write(str(s[j]) + '\t')

				for j in range(len(itemList)):
					avgItemValue = 0.0
					n = 0
					at = titleList.index(itemList[j])
					while(at >= 0):
						try:
							avgItemValue += float(s[at])
							n+=1
							at = titleList.index(itemList[j], at + 1)
						except Exception as e:
							at = -1
					if n == 0:
						out.write('x\t')
					else:
						avgItemValue /= n
						SE = 0.0
						n = 0
						at = titleList.index(itemList[j])
						while at >= 0:
							try:
								SE += (avgItemValue - float(s[at])) * (avgItemValue - float(s[at]))
								n +=1
								at = titleList.index(itemList[j], at + 1)
							except Exception as e:
								at = -1

						if n > 1:
							SE = math.sqrt(SE / (n - 1))
							SE /= math.sqrt((n-1))
							out.write(str(round(SE, 8)))
							out.write('\t')
						else:
							out.write('\t')

				out.write('\n')
				line +=1

				if line % 1000 == 0:
					print('Processing average... Standard Error... ' + str(line) + ' lines\n')

		f.close()
		out.close()
	except Exception as e:
		print(traceback.format_exc())

# find outliers
def outlier(inputFile):
	try:
		skipRow, skipCol = skips()
		print('Outlier running')
		f = open('%s' % inputFile, 'r')
		outputFile = os.path.split(inputFile)[1].replace('.txt', '_Outlier.txt')
		out = open(outputFile,'w')

		for i in range(skipRow):
			f.readline()
		data = f.readline()
		for i in range(skipCol + 1):
			if data.index('\t') >= 0:
				data = data[data.index('\t'):]
			data = data.strip()

		sampleTitle = data.split('\t')
		sampleNum = len(sampleTitle)
		values = [0.0] * sampleNum
		marks = [0] * sampleNum
		geneNum = 0

		while True:
			data = f.readline()
			if not data:
				break
			else:
				s = data.split('\t')
				for k in range(sampleNum):
					try:
						values[k] = round(float(s[k + skipCol + 1]), 3)

					except Exception as e:
						pass

				mean = getMean(values)
				phi = getSTD(values)
				for k in range(sampleNum):
					if values[k] < (mean - 2.0 * phi) or values[k] > (mean + 2.0 * phi):
						marks[k] += 1
				
				geneNum += 1	
				if geneNum % 1000 == 0:
					print('Outlier running, finished...' + str(geneNum) + ' lines')

		for j in range(sampleNum):
			out.write(sampleTitle[j] + '\t')
			out.write(str(marks[j]) + '\t')
			out.write(str(round(marks[j] * 1.0 / geneNum, 3)))
			out.write('\n')
		out.close
		print('Outlier finished')

	except Exception as e:
		print(traceback.format_exc())

# adds dashes based on how long the filename is, just here to make the selection a little bit nicer
def dashes(string):
	dash = '-------------------------'
	for i in range(len(string)):
		dash+='-'
	return '\n' + dash

def main():
	input('Press Enter to select file')
	filename = fileSelector()

	while True:
		file = os.path.split(filename)[1]
		print('\nEnter Selection for file ' +  file + dashes(file))
		print('1. Average\n2. Log2 Normalize\n3. ZScore Normalize\n4. Outlier\n5. Select a new file\n6. Exit')
		select = input('Enter: ')

		if select == '1':
			needSE = False
			SE = input('Do you want to compute the standard error [Y/N] (default is no)').lower()
			if SE == 'y':
				needSE = True
			average(filename, needSE)
		elif select == '2':
			log2Normalize(filename)
		elif select == '3':
			ZScoreNormalize(filename)
		elif select == '4':
			outlier(filename)
		elif select == '5':
			filename = fileSelector()
		elif select == '6':
			exit()




main()