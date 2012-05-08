import string
import os
import re
import cPickle
import pyXLWriter as xl

from base import webqtlConfig
from utility import webqtlUtil
from base.templatePage import templatePage

class ExportPage(templatePage):

	def __init__(self, fd):

		templatePage.__init__(self, fd)

		filename = webqtlUtil.genRandStr("Export_")
		workbook = xl.Writer('%s.xls' % (webqtlConfig.TMPDIR+filename))
		style_formats = [] #Array with Excel style formats - Zach 9/2/2011
		heading = workbook.add_format(align = 'center', bold = 1, border = 1, size=13, fg_color = 0x1E, color="white") #Style for the header cells
		right  = workbook.add_format(align = 'right') #Style to align cell contents to the right
		style_formats.append(heading)
		style_formats.append(right)
		worksheet = workbook.add_worksheet()

		primaryStrainNames = fd.formdata.getvalue('strainNames', '').split(',')
		primaryVals = fd.formdata.getvalue('strainVals', '').split(',')
		primaryVars = fd.formdata.getvalue('strainVars', '').split(',')
		otherStrainNames = fd.formdata.getvalue('otherStrainNames', '').split(',')
		otherVals = fd.formdata.getvalue('otherStrainVals', '').split(',')
		otherVars = fd.formdata.getvalue('otherStrainVars', '').split(',')
		attributeData = fd.formdata.getvalue('extra_attributes', '')
		otherAttributeData = fd.formdata.getvalue('other_extra_attributes', '')

		#ZS: This section is to parse the attribute formdata string
		attributeTypes = attributeData.split('/')
		otherAttributeTypes = otherAttributeData.split('/')
		
		attributeNames = []
		attributeVals = []
		for i in range(len(attributeTypes)):
			if i < len(attributeTypes) - 1:
				attributeNames.append(attributeTypes[i].split(':')[0])
				attributeVals.append(attributeTypes[i].split(':')[1].split(','))
			else:
				break

		otherAttributeNames = []
		otherAttributeVals = []
		for i in range(len(otherAttributeTypes)):
			if i < len(otherAttributeTypes) - 1:
				otherAttributeNames.append(otherAttributeTypes[i].split(':')[0])
				otherAttributeVals.append(otherAttributeTypes[i].split(':')[1].split(','))
			else:
				break

		varsExist = 0 #ZS: Even if there are no variances "primaryVars" would still be populated with empty values, so we need to check if there really are any
		for i in range(len(primaryVars)):
			if primaryVars[i] != '':
				varsExist = 1
				break

		otherStrainsExist = 0 #ZS: Same as above; checking to see if there's a set of "other" (non-primary) strains
		for i in range(len(otherStrainNames)):
			if otherStrainNames[i] != '':
				otherStrainsExist = 1
				break

		if varsExist == 1:
			column_headers = ["Sample", "Value", " SE "] #ZS: Names of the header for each column in the excel worksheet
		else:
			column_headers = ["Sample", "Value"]


		for attr_name in attributeNames:
			column_headers.append(attr_name)

		start_line = 0 #Gets last line of "primary" strain values to define a start-point for "other" strain values
		for ncol, item in enumerate(column_headers):
			worksheet.write([start_line, ncol], item, style_formats[0])
			worksheet.set_column([ncol, ncol], 2*len(item))

		start_line += 1
		last_line = start_line

		for i in range(len(primaryStrainNames)):
			ncol = 0
			if varsExist == 1:
				for ncol, item in enumerate([primaryStrainNames[i], primaryVals[i], primaryVars[i]]):
					worksheet.write([start_line + i, ncol], item, style_formats[1])
					ncol += 1
			else:
				for ncol, item in enumerate([primaryStrainNames[i], primaryVals[i]]):
					worksheet.write([start_line + i, ncol], item, style_formats[1])
					ncol += 1

			for attribute_type in attributeVals:
				worksheet.write([start_line + i, ncol], attribute_type[i], style_formats[1])
				ncol += 1

			last_line += 1

		if otherStrainsExist == 1:
				start_line = last_line + 2

				for ncol, item in enumerate(column_headers):
					worksheet.write([start_line, ncol], item, style_formats[0])
					worksheet.set_column([ncol, ncol], 2*len(item))
				start_line += 1

				for i in range(len(otherStrainNames)):
					ncol = 0
					if varsExist == 1:
						for ncol, item in enumerate([otherStrainNames[i], otherVals[i], otherVars[i]]):
							worksheet.write([start_line + i, ncol], item, style_formats[1])
							ncol += 1
					else:
						for ncol, item in enumerate([otherStrainNames[i], otherVals[i]]):
							worksheet.write([start_line + i, ncol], item, style_formats[1])

					for attribute_type in otherAttributeVals:
						worksheet.write([start_line + i, ncol], attribute_type[i], style_formats[1])
						ncol += 1

		workbook.close()

		full_filename = os.path.join(webqtlConfig.TMPDIR, '%s.xls' % filename)
		fp = open(full_filename, 'rb')
		text = fp.read()
		fp.close()
		
		self.content_type = 'application/xls'
		self.content_disposition = 'attachment; filename=%s' % ('%s.xls' % filename)
		self.attachment = text
		

		




