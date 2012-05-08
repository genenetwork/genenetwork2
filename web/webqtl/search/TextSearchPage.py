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
import os
import cPickle
from math import *

import reaper
from htmlgen import HTMLgen2 as HT

from base import admin
from base import webqtlConfig
from base.templatePage import templatePage
from utility import webqtlUtil
from base.webqtlDataset import webqtlDataset
from base.webqtlTrait import webqtlTrait
from utility.THCell import THCell
from utility.TDCell import TDCell
from utility import webqtlUtil



class TextSearchPage(templatePage):
	maxReturn = 200

	def __init__(self, fd):

		templatePage.__init__(self, fd)

                if not self.openMysql():
                        return

		# updated by NL, deleted jquery here, move it to dhtml.js
		self.dict['js1'] = ''

		species_list = [] #List of species (mouse, rat, human), with the selected species listed first

		input_species = string.strip(string.lower(fd.formdata.getfirst('species', "mouse"))) #XZ, Oct 28, 2009: I changed the default species to mouse.
		species_list.append(input_species)
		#Create list of species (mouse, rat, human) with the species the user selected first
		for species in ["mouse","rat","human"]:
			if species not in species_list:
				species_list.append(species)

		ADMIN_tissue_alias = admin.ADMIN_tissue_alias

		tissue = string.strip(string.lower(fd.formdata.getfirst('tissue', "")))
		if tissue:
			try:
				rev_ADMIN_tissue_alias = {}
				for key in ADMIN_tissue_alias.keys():
					rev_ADMIN_tissue_alias[key] = key
					for alias in ADMIN_tissue_alias[key]:
						rev_ADMIN_tissue_alias[alias.upper()] = key
				tissue = rev_ADMIN_tissue_alias[tissue.upper()]
			except:
				tissue = "UNKNOWN"

		#possibly text output
		txtOutput = [] #ZS: if format=text
		all_species_dataset_count = 0 #XZ: count of datasets across all species; used in the opening text of the page
		all_species_trait_count = 0  #XZ: count of records across all species; used in opening text of the page and text file (if format = text)

		#div containing the tabs (species_container), the tabs themselves (species_tab_list, which is inserted into species_tabs), and the table (species_table) containing both the tissue and results tables for each tab
		species_container = HT.Div(id="species_tabs", Class="tab_container") #Div that will contain tabs for mouse/rat/human species; each tab contains a table with the result count for each tissue group
		species_tab_list = [HT.Href(text="%s" % species_list[0].capitalize(), url="#species1"), HT.Href(text="%s" % species_list[1].capitalize(), url="#species2"), HT.Href(text="%s" % species_list[2].capitalize(), url="#species3")]
		species_tabs = HT.List(species_tab_list, Class="tabs")
		species_table = HT.TableLite(cellSpacing=0,cellPadding=0,width="100%",border=0, align="Left")

		for i in range(len(species_list)):
			species_container_table = HT.TableLite(cellSpacing=0,cellPadding=0,width="100%",border=0, align="Left") #ZS: Table containing both the tissue record count and trait record tables as cells; this fixes a display issue in some browsers that places the tables side by side instead of top/bottom

			species = species_list[i]
			ADMIN_search_dbs = admin.ADMIN_search_dbs[species]
			this_species_dataset_count = 0 #XZ: count of the datasets containing results for this species
			this_species_trait_count = 0  #XZ: count of the trait records for this species

			div = HT.Div(id="species%s" % (i+1), Class="tab_content")
			tab_container = HT.Span() #ZS: Contains species_container_table within the species' tab

			tissuePageTable = HT.TableLite(cellSpacing=0,cellPadding=0,width="100%",border=0, align="Left")				
			tissue_tblobj = {} # object used to create the table listing the results for each tissue
			tissue_tblobj['header'] = self.getTissueTableHeader() # creates header for table listing results for selected tissue

			traitPageTable = HT.TableLite(cellSpacing=0,cellPadding=0,width="100%",border=0, align="Left")
			trait_tblobj = {} # object used to create the table listing the trait results for each tissue
			trait_tblobj['header'] = self.getTraitTableHeader() # creates header for table listing trait results for selected tissue

			tissue_tblobj['body'], trait_tblobj['body'], this_species_dataset_count, this_species_trait_count, this_species_txtOutput = self.createTableBodies(fd, species, tissue, ADMIN_search_dbs)

			if species == input_species:
				txtOutput = this_species_txtOutput

			filename1 = webqtlUtil.genRandStr("Search_") #filename for tissue table object
			tissue_objfile = open('%s.obj' % (webqtlConfig.TMPDIR+filename1), 'wb')
			cPickle.dump(tissue_tblobj, tissue_objfile)
			tissue_objfile.close()

			tissue_sortby = self.getTissueSortByValue() # sets how the tissue table should be sorted by default
			tissue_div = HT.Div(webqtlUtil.genTableObj(tblobj=tissue_tblobj, file=filename1, sortby=tissue_sortby, tableID = "tissue_sort%s" % (i+1), addIndex = "1"), Id="tissue_sort%s" % (i+1))

			tissuePageTable.append(HT.TR(HT.TD("&nbsp;")))
			tissuePageTable.append(HT.TR(HT.TD(tissue_div)))
			tissuePageTable.append(HT.TR(HT.TD("&nbsp;")))
			species_container_table.append(HT.TR(HT.TD(tissuePageTable)), HT.TR(HT.TD("&nbsp;")))


			filename2 = webqtlUtil.genRandStr("Search_") #filename for trait table object
			trait_objfile = open('%s.obj' % (webqtlConfig.TMPDIR+filename2), 'wb')
			cPickle.dump(trait_tblobj, trait_objfile)
			trait_objfile.close()

			trait_sortby = self.getTraitSortByValue() # sets how the trait table should be sorted by default
			trait_div = HT.Div(webqtlUtil.genTableObj(tblobj=trait_tblobj, file=filename2, sortby=trait_sortby, tableID = "results_sort%s" % (i+1), addIndex = "0"), Id="results_sort%s" % (i+1))

			traitPageTable.append(HT.TR(HT.TD("&nbsp;")))
			traitPageTable.append(HT.TR(HT.TD(trait_div)))
			traitPageTable.append(HT.TR(HT.TD("&nbsp;")))
			species_container_table.append(HT.TR(HT.TD(traitPageTable)), HT.TR(HT.TD("&nbsp;")))

			if this_species_trait_count == 0:
				tab_container.append(HT.Div("No records retrieved for this species.", align="left", valign="top", style="font-size:42"))
			else:
				tab_container.append(species_container_table)

			all_species_dataset_count += this_species_dataset_count
			all_species_trait_count += this_species_trait_count

			div.append(tab_container)
			species_table.append(HT.TR(HT.TD(div)))

		species_container.append(species_table)
		



		if fd.returnFmt != 'text': #if the format is not 'text'
			self.dict['title'] = 'Search Results'
			TD_LR = HT.TD(height=100,width="100%",bgColor='#fafafa',valign="top")
			pageTable = HT.TableLite(cellSpacing=0,cellPadding=0,width="100%",border=0, align="Left") # Table containing all of the page's elements (opening text, form); in some browers the elements arrange themselves horizontally if you don't put them into a table, so this fixes that problem

			formTable = HT.TableLite(cellSpacing=2,cellPadding=0,width="100%",border=0) # Table containing all of the form's elements (tabs, option buttons); used to correct the same issue mentioned in pageTable's comment

			mainForm = HT.Form( cgi= os.path.join(webqtlConfig.CGIDIR, webqtlConfig.SCRIPTFILE), enctype='multipart/form-data', name='showDatabase', submit=HT.Input(type='hidden'))
			hddn = {'FormID':'showDatabase','ProbeSetID':'_','database':'_','CellID':'_','RISet':fd.RISet}
			hddn['incparentsf1']='ON'
			for key in hddn.keys():
				mainForm.append(HT.Input(name=key, value=hddn[key], type='hidden'))

			#Add to collection, select all, invert selection, and deselect all ("reset") buttons
			addselect = HT.Href(url="#redirect", Class="add_traits")
			addselect_img = HT.Image("/images/add_collection1_final.jpg", name="addselect", alt="Add To Collection", title="Add To Collection", style="border:none;")
			addselect.append(addselect_img)
			selectall = HT.Href(url="#redirect", onClick="checkAll(document.getElementsByName('showDatabase')[0]);")
			selectall_img = HT.Image("/images/select_all2_final.jpg", name="selectall", alt="Select All", title="Select All", style="border:none;")
			selectall.append(selectall_img)
			selectinvert = HT.Href(url="#redirect", onClick="checkInvert(document.getElementsByName('showDatabase')[0];")
			selectinvert_img = HT.Image("/images/invert_selection2_final.jpg", name="selectinvert", alt="Invert Selection", title="Invert Selection", style="border:none;")
			selectinvert.append(selectinvert_img)
			reset = HT.Href(url="#redirect", onClick="checkNone(document.getElementsByName('showDatabase')[0]); return false;")
			reset_img = HT.Image("/images/select_none2_final.jpg", alt="Select None", title="Select None", style="border:none;")
			reset.append(reset_img)

			#Table with select, deselect, invert, etc. It is used for the results table.
			optionsTable = HT.TableLite(cellSpacing=2,cellPadding=0,width="20%",border=0)
			optionsRow = HT.TR(HT.TD(selectall, width="25%"), HT.TD(reset, width="25%"), HT.TD(selectinvert, width="25%"), HT.TD(addselect, width="25%"))
			labelsRow = HT.TR(HT.TD("&nbsp;"*2,"Select", width="25%"), HT.TD("&nbsp;","Deselect", width="25%"), HT.TD("&nbsp;"*3,"Invert", width="25%"), HT.TD("&nbsp;"*4,"Add", width="25%"))
			optionsTable.append(HT.TR(HT.TD("&nbsp;")), optionsRow, labelsRow)
			
			if fd.geneName:
				searchType = "gene name " + fd.geneName
			elif fd.refseq:
				searchType = "RefSeq accession number " + fd.refseq
			elif fd.genbankid:
				searchType = "Genbank ID " + fd.genbankid
			elif fd.geneid:
				searchType = "Gene ID " + fd.geneid
			else:
				searchType = ""

			SearchText = HT.Span("You searched for the %s in GeneNetwork." % searchType, HT.BR(),
						"We queried %s expression datasets across %s species and listed the results" % (all_species_dataset_count, len(species_list)), HT.BR(),
						"below. A total of %s records that may be of interest to you were found. The" % all_species_trait_count, HT.BR(),
						"top table lists the number of results found for each relevant tissue, and the", HT.BR(),
						"bottom gives a basic summary of each result. To study one of the results, click", HT.BR(),
						"its Record ID. More detailed information is also available for each result's group", HT.BR() ,
						"and dataset. To switch between species, click the tab with the corresponding", HT.BR(),
						"label.", HT.BR(), HT.BR(),
						"Please visit the links to the right to learn more about the variety of features", HT.BR(),
						"available within GeneNetwork.")	
			
			LinkText = HT.Span()
			
			mainLink = HT.Href(url="/webqtl/main.py", text = "Main Search Page", target="_blank")
			homeLink = HT.Href(url="/home.html", text = "What is GeneNetwork?", target="_blank")
			tourLink = HT.Href(url="/tutorial/WebQTLTour/", text = "Tour of GeneNetwork (20-40 min)", target="_blank")
			faqLink = HT.Href(url="/faq.html", text = "Frequently Asked Questions", target="_blank")
			glossaryLink = HT.Href(url="/glossary.html", text = "Glossary of terms used throughout GeneNetwork", target="_blank")
			
			LinkText.append(mainLink, HT.BR(), homeLink, HT.BR(), tourLink, HT.BR(), faqLink, HT.BR(), glossaryLink)
			
			formTable.append(HT.TR(HT.TD(species_tabs, species_container)), HT.TR(HT.TD(optionsTable)))
			mainForm.append(formTable)
			

			if fd.geneName:
				SearchHeading = HT.Paragraph('Search Results for gene name ', fd.geneName)
			elif fd.refseq:
				SearchHeading = HT.Paragraph('Search Results for RefSeq accession number ', fd.refseq)
			elif fd.genbankid:
				SearchHeading = HT.Paragraph('Search Results for Genbank ID ', fd.genbankid)
			elif fd.geneid:
				SearchHeading = HT.Paragraph('Search Results for Gene ID ', fd.geneid)
			else:
				SearchHeading = HT.Paragraph('')

			SearchHeading.__setattr__("class","title")

			pageTable.append(HT.TR(HT.TD(SearchText, width=600), HT.TD(LinkText, align="left", valign="top")), HT.TR(HT.TD("&nbsp;", colspan=2)), HT.TR(HT.TD(mainForm, colspan=2)))
			TD_LR.append(SearchHeading, pageTable)
			self.dict['body'] = TD_LR
		else:
		    if len(txtOutput) == 0:
			self.output = "##No records were found for this species. \n"
		    else:
			self.output = "##A total of %d records were returned. \n" % all_species_trait_count
			newOutput = []
			strainLists = {}
			for item in txtOutput:
				tissueGrp, thisTrait = item
				RISet = thisTrait.riset
				if strainLists.has_key(RISet):
					thisStrainlist = strainLists[RISet]
				else:
					thisGenotype = reaper.Dataset()
					thisGenotype.read(os.path.join(webqtlConfig.GENODIR, RISet + '.geno'))
					if thisGenotype.type == "riset": 
						_f1, _f12, _mat, _pat = webqtlUtil.ParInfo[RISet]
						thisGenotype = thisGenotype.add(Mat=_mat, Pat=_pat, F1=_f1)
					thisStrainlist = list(thisGenotype.prgy)
					strainLists[RISet] = thisStrainlist
				thisTrait.retrieveData(strainlist=thisStrainlist)
				thisData = []
				for item in thisStrainlist:
					if thisTrait.data.has_key(item): thisData.append(thisTrait.data[item].val)
					else: thisData.append(None)
				newOutput.append(["Structure", "Database", "ProbeSetID", "Cross"] + thisStrainlist)
				newOutput.append([tissueGrp, '"%s"' % thisTrait.db.fullname, thisTrait.name, RISet]+map(str,thisData))
			newOutput = webqtlUtil.asymTranspose(newOutput)
			for item in newOutput:
				 self.output += string.join(item, "\t") + "\n"		


	def createTableBodies(self, fd, species, tissue, ADMIN_search_dbs):

		this_species_txtOutput = []

		#priority GeneName > refseq > genbankid
		this_species_trait_count = 0 #count of all traits in this species
		this_species_dataset_count = 0 #Number of datasets in this species
		row_count = 0 #Index number used in the first row of the trait table
		trait_tblobj_body = [] #body of table with the results themselves; 
		tissue_tblobj_body = [] #body of table with the number of results for each tissue group
		className = "fs12 fwn b1 c222"

		for i, tissueGrp in enumerate(ADMIN_search_dbs.keys()):
			if tissue and tissue.upper() != tissueGrp.upper():
				continue
			dbNames = ADMIN_search_dbs[tissueGrp]

			tissue_tr = [] #Table row for tissue group
			tissue_tr.append(TDCell(HT.TD('', Class=className)))
			tissue_tr.append(TDCell(HT.TD(tissueGrp.capitalize(), Class=className), tissueGrp, tissueGrp)) #Append cell with tissue name to row

			this_tissue_record_count = 0 #Count of the results for each tissue		
			for dbName in dbNames:
				this_species_dataset_count += 1
				thisDB = webqtlDataset(dbName, self.cursor)

				if fd.geneName:
					if fd.searchAlias:
						self.cursor.execute("""SELECT ProbeSet.Name
											FROM
										ProbeSet, ProbeSetFreeze, ProbeSetXRef
											WHERE
										ProbeSetFreeze.Name = "%s" AND
										ProbeSetFreeze.Id = ProbeSetXRef.ProbeSetFreezeId AND
										MATCH (ProbeSet.symbol, alias) AGAINST ("+%s" IN BOOLEAN MODE) AND
										ProbeSet.Id = ProbeSetXRef.ProbeSetId""" % (dbName, fd.geneName))
					else:
						self.cursor.execute("""SELECT ProbeSet.Name
											FROM
										ProbeSet, ProbeSetFreeze, ProbeSetXRef
											WHERE
										ProbeSetFreeze.Name = "%s" AND
										ProbeSetFreeze.Id = ProbeSetXRef.ProbeSetFreezeId AND
										ProbeSet.symbol = "%s" AND
										ProbeSet.Id = ProbeSetXRef.ProbeSetId""" % (dbName, fd.geneName))
				elif fd.refseq:

				# XZ, Oct/08/2009: Search for RefSeq ID is kind of tricky. One probeset can have multiple RefseqIDs that are delimited by ' /// ' (currently). 
				# So I have to use 'like' instead of '=' in SQL query. But user search with one short string, for example 'NM_1', it will return thousands of results. 
				# To prevent this, I set the restriction that the length of input Refseq ID must be at least 9 characters. Otherwise, do NOT start searching. 
				# Even with the restriction of input RefSeqID, I'm still worried about the 'like' in SQL query. My concern is in future, there might be RefSeqIDs with 
				# 10 characters whose first 9 characters are the same as the existing ones. So I decide to further check the result. We should also consider that the 
				# RefSeqID in database may have version number such as "NM_177938.2". If the input RefSeqID is 'NM_177938', it should be matched. I think we should get rid of the version number in database.

					if len(fd.refseq) < 9:
						if fd.returnFmt != 'text':
							heading = "Search Result"
							detail = ["The RefSeq ID that you inputed is less than 9 characters. GeneNetwork thinks it is not a legitimate RefSeq ID and did not do the search. Please try to use a RefSeq ID with at least 9 characters."]
							self.error(heading=heading,detail=detail,error="Not Found")
						else:
							self.output = "#The gene name or IDs you submitted did not match any record in the databases available. You may try different gene names or tissue type."
						return
					else:
						sqlString = """SELECT ProbeSet.Id, ProbeSet.RefSeq_TranscriptId
										FROM
									ProbeSet, ProbeSetFreeze, ProbeSetXRef
										WHERE
									ProbeSetFreeze.Name = "%s" AND
									ProbeSetFreeze.Id = ProbeSetXRef.ProbeSetFreezeId AND
									MATCH(ProbeSet.RefSeq_TranscriptId) AGAINST ("+%s" IN BOOLEAN MODE) AND
									ProbeSet.Id = ProbeSetXRef.ProbeSetId""" % (dbName, fd.refseq)

						self.cursor.execute(sqlString)

						results = self.cursor.fetchall()
						if results:
							Id_of_really_matched_probeset = []

							for one_result in results:
								ProbeSet_Id, ProbeSet_RefSeq_TranscriptId = one_result
								multiple_RefSeqId = string.split(string.strip(ProbeSet_RefSeq_TranscriptId), '///')
								for one_RefSeqId in multiple_RefSeqId:
									tokens = string.split( one_RefSeqId, '.' )
									one_RefSeqId_without_versionNum = string.strip(tokens[0])
									if one_RefSeqId_without_versionNum == fd.refseq:
										Id_of_really_matched_probeset.append( ProbeSet_Id )
										break

							if Id_of_really_matched_probeset:
								condition_string = " or ".join(["Id = %s" % one_ID for one_ID in Id_of_really_matched_probeset])
								sqlString = """SELECT ProbeSet.Name from ProbeSet where (%s)""" % condition_string

								self.cursor.execute(sqlString)
						else:
							pass

				elif fd.genbankid:
					self.cursor.execute("""SELECT ProbeSet.Name
										FROM
									ProbeSet, ProbeSetFreeze, ProbeSetXRef
										WHERE
									ProbeSetFreeze.Name = "%s" AND
									ProbeSetFreeze.Id = ProbeSetXRef.ProbeSetFreezeId AND
									ProbeSet.GenbankId = "%s" AND
									ProbeSet.Id = ProbeSetXRef.ProbeSetId""" % (dbName, fd.genbankid))
				elif fd.geneid:
					self.cursor.execute("""SELECT ProbeSet.Name
										FROM
									ProbeSet, ProbeSetFreeze, ProbeSetXRef
										WHERE
									ProbeSetFreeze.Name = "%s" AND
									ProbeSetFreeze.Id = ProbeSetXRef.ProbeSetFreezeId AND
									ProbeSet.GeneId = "%s" AND
									ProbeSet.Id = ProbeSetXRef.ProbeSetId""" % (dbName, fd.geneid))
				else:
					continue

				results = self.cursor.fetchall()			
				if len(results) > 0:
					this_tissue_record_count += len(results)
					this_species_trait_count += this_tissue_record_count

					for result in results:
				 		_ProbeSetID = result[0]
						thisTrait = webqtlTrait(db=thisDB, name=_ProbeSetID, cursor=self.cursor)
						results_tr = []
						trId = str(thisTrait)
						_traitUrl = thisTrait.genHTML(dispFromDatabase=1)
						_traitName = str(thisTrait)
						
						#ZS: check box column
						results_tr.append(TDCell(HT.TD(str(row_count+1), HT.Input(type="checkbox", Class="checkallbox", name="searchResult",value=trId, onClick="highlight(this)"), nowrap="on", align="right", Class=className), str(row_count+1), row_count+1))
						row_count += 1

						#ZS: Tissue column
						results_tr.append(TDCell(HT.TD(tissueGrp.capitalize(), Class=className), tissueGrp, tissueGrp))

						#ZS: Group column
						risetUrl = HT.Href(text=thisTrait.riset, url="http://www.genenetwork.org/%sCross.html#%s" % (species, thisTrait.riset), target="_blank", Class=className)
						results_tr.append(TDCell(HT.TD(risetUrl, Class=className), thisTrait.riset, thisTrait.riset))

						#ZS: Dataset column
						results_tr.append(TDCell(HT.TD(HT.Href(text=thisTrait.db.fullname, url = webqtlConfig.INFOPAGEHREF % thisTrait.db.name,
								target='_blank', Class="fs13 fwn non_bold"), Class=className), thisTrait.db.name.upper(), thisTrait.db.name.upper()))

						#ZS: Trait ID column
						results_tr.append(TDCell(HT.TD(HT.Href(text=thisTrait.getGivenName(),url="javascript:showDatabase3('%s','%s','%s','')" % ('showDatabase', thisTrait.db.name, thisTrait.name), Class="fs12 fwn"), nowrap="yes",align="left", Class=className),str(thisTrait.name), thisTrait.name))

						#ZS: Symbol column and Description column
						description_string = str(thisTrait.description).strip()
						if (thisTrait.db.type == "ProbeSet"):
							target_string = str(thisTrait.probe_target_description).strip()

            						description_display = ''

							if len(description_string) > 1 and description_string != 'None':
								description_display = description_string
							else:
           		    					description_display = thisTrait.symbol

            						if len(description_display) > 1 and description_display != 'N/A' and len(target_string) > 1 and target_string != 'None':
                						description_display = description_display + '; ' + target_string.strip()
					
							description_string = description_display
						else:
							results_tr.append(TDCell(HT.TD("--", align="left", Class=className), "--", "Zz"))
							
            					results_tr.append(TDCell(HT.TD(description_string, Class=className), description_string, description_string))

						#XZ: trait_location_value is used for sorting
						trait_location_repr = "--"
						trait_location_value = 1000000
	
						if hasattr(thisTrait, 'chr') and hasattr(thisTrait, 'mb') and thisTrait.chr and thisTrait.mb:
							try:
								trait_location_value = int(thisTrait.chr)*1000 + thisTrait.mb
							except:
								if thisTrait.chr.upper() == "X":
									trait_location_value = 20*1000 + thisTrait.mb
								else:
									trait_location_value = ord(str(thisTrait.chr).upper()[0])*1000 + thisTrait.mb
						
							trait_location_repr = "Chr%s: %.6f" % (thisTrait.chr, float(thisTrait.mb) )
				
						results_tr.append(TDCell(HT.TD(trait_location_repr, nowrap='ON', Class=className), trait_location_repr, trait_location_value))
	
						#ZS: Mean column
	           	 			self.cursor.execute("""
	                   	 			select ProbeSetXRef.mean from ProbeSetXRef, ProbeSet
	                   	 			where ProbeSetXRef.ProbeSetFreezeId = %d and
	                        	  			ProbeSet.Id = ProbeSetXRef.ProbeSetId and
	                        	  			ProbeSet.Name = '%s'
	            				""" % (thisTrait.db.id, thisTrait.name))
	            				result = self.cursor.fetchone()
	            				if result:
	                				if result[0]:
	                    					mean = result[0]
	                				else:
	                    					mean=0
	            				else:
	                				mean = 0
	
	            				repr = "%2.3f" % mean
	            				results_tr.append(TDCell(HT.TD(repr, Class=className, align='right', nowrap='ON'),repr, mean))
						trait_tblobj_body.append(results_tr)

						this_species_txtOutput.append([tissueGrp, thisTrait])


			tissue_tr.append(TDCell(HT.TD(str(this_tissue_record_count), Class=className), str(this_tissue_record_count), this_tissue_record_count))
			tissue_tblobj_body.append(tissue_tr)
	
		self.output = "self.output"

		return tissue_tblobj_body, trait_tblobj_body, this_species_dataset_count, this_species_trait_count, this_species_txtOutput


	def getTissueSortByValue(self):
	
		sortby = ("tissue_group", "up")

		return sortby


	def getTraitSortByValue(self):
	
		sortby = ("tissue", "up")

		return sortby


	def getTissueTableHeader(self):

		tblobj_header = []

		className = "fs13 fwb ffl b1 cw cbrb"

		tblobj_header = [[THCell(HT.TD(' ', Class=className, nowrap="on"), sort=0),
			THCell(HT.TD('Tissue',HT.BR(), HT.BR(), valign="top", Class=className, nowrap="on"), text="tissue_group", idx=1),	
			THCell(HT.TD('Results', HT.BR(), HT.BR(), valign="top", Class=className, nowrap="on"), text="results", idx=2)]]

		return tblobj_header

	def getTraitTableHeader(self):

		tblobj_header = []

		className = "fs13 fwb ffl b1 cw cbrb"

		tblobj_header = [[THCell(HT.TD('Index',HT.BR(), HT.BR(), valign="top", Class=className, nowrap="on"), text="index", idx=0),
			THCell(HT.TD('Tissue',HT.BR(), HT.BR(), valign="top", Class=className, nowrap="on"), text="tissue", idx=1),	
			THCell(HT.TD('Group',HT.BR(), HT.BR(), valign="top", Class=className, nowrap="on"), text="group", idx=2),	
			THCell(HT.TD('Dataset', HT.BR(), HT.BR(), valign="top", Class=className, nowrap="on"), text="dataset", idx=3),
			THCell(HT.TD('Record ID', HT.BR(), HT.BR(), valign="top", Class=className, nowrap="on"), text="name", idx=4),
			THCell(HT.TD('Description', HT.BR(), HT.BR(), valign="top", Class=className, nowrap="on"), text="desc", idx=5),
			THCell(HT.TD('Location', HT.BR(), 'Chr and Mb', HT.BR(), valign="top", Class=className, nowrap="on"), text="location", idx=6),
			THCell(HT.TD('Mean', HT.BR(), 'Expr', HT.BR(), valign="top", Class=className, nowrap="on"), text="mean", idx=7)]]

		return tblobj_header
