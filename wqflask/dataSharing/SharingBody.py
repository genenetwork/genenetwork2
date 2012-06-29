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

sharing_body_string = """
<TD vAlign=top width="100%" align="left" height=10 bgColor=#eeeeee>

							<p style="font-size:18px;font-family:verdana;color:black"><B> Data Set Download</B></p>
							<Form METHOD="get" ACTION="/webqtl/main.py" name="SEARCHFORM">

								<TABLE width="800" border="0">
					
					<!--  SPECIES  SELECTION -->				
									<TR>
										<TD align=right height="35" style="font-size:14px;font-family:verdana;color:black" width="16%">
											<B>Species:</B>
										</TD>
										<TD width="3%">
										</TD>
										<TD NOWRAP width="85%" align="left">
											<DIV Id="menu0">
												<Select NAME="species" size=1 id="species" onchange="fillOptions('species');">
												</Select>
											</DIV>
										</TD>
									</TR>
				
					<!--  GROUP  SELECTION -->	
									<TR>
										<TD align="right" height="35" style="font-size:14px;font-family:verdana;color:black">
											<B>Group:</B>
										</TD>
										<TD>
										</TD>
										<TD NOWRAP width="85%" align="left">
											<DIV Id="menu1">

												<Select NAME="cross" size=1 id="cross" onchange="fillOptions('cross');">
												</Select>
											<input type="button" class="button" value=" Info " onCLick="javascript:crossinfo();">
											</DIV>
										</TD>
									</TR>

					<!--  TYPE  SELECTION -->		
									<TR>
										<TD align=right height=35 style="font-size:14px;font-family:verdana;color:black">
											<B>Type:</B>
										</TD>
										<TD>
										</TD>
										<TD NOWRAP width="85%" align="left">
											<DIV Id="menu2">
												<Select NAME="tissue" size=1 id="tissue" onchange="fillOptions('tissue');">

												</Select>
											</DIV>
										</TD>
									</TR>

					<!--  DATABASE  SELECTION -->		
									<TR>
										<TD align=right height=35 style="font-size:14px;font-family:verdana;color:black">
											<B>Database:</B>
										</TD>
										<TD>
										</TD>
										<TD NOWRAP width="85%" align="left">
											<DIV Id="menu3">
												<Select NAME="database" size=1 id="database"> 
												</Select>
												<input type="button" class="button" value=" Info " onCLick="javascript:databaseinfo();">
											</DIV>
										</TD>
									</TR>

<!--  SEARCH, MAKE DEFAULT, ADVANCED SEARCH -->
									<TR>
										<td></td>
										<td></td>
										<TD ALIGN="left" HEIGHT="40">
											&nbsp;&nbsp;&nbsp;<INPUT TYPE="button" CLASS="button" STYLE="font-size:12px" VALUE="&nbsp;&nbsp;Download&nbsp;&nbsp;" onCLick="javascript:datasetinfo();">
										</TD>
									</TR>
								</TABLE>

								<SCRIPT SRC="/javascript/selectDatasetMenu.js"></SCRIPT>
							</FORM>
							
							<p style="font-size:18px;font-family:verdana;color:black"><B> GeneNetwork Accession Number</B></p>
							<form method="get" action="/webqtl/main.py" name="f2" target="_blank">
								<INPUT TYPE="hidden" NAME="FormID" VALUE="sharinginfo">
								<TABLE width="800" border="0">
									<tr>
										<td align=right height="35" style="font-size:14px;font-family:verdana;color:black" width="16%"><b>GN:</b></td>
										<td width=3%></td>
										<td><input type="text" name="GN_AccessionId" size="40" />&nbsp;&nbsp;E.g. 112</td>
									</tr>
									<tr>
										<td></td>
										<td></td>
										<td HEIGHT="40">
											&nbsp;&nbsp;&nbsp;<input type="Submit" class="button" STYLE="font-size:12px" VALUE="&nbsp;&nbsp;&nbsp;Submit&nbsp;&nbsp;&nbsp;">
										</td>
									</tr>
								</table>
							</form>
							
</td>
"""

sharinginfo_body_string = """<td>
<a href="/webqtl/main.py?FormID=sharingListDataset">List of DataSets</a><br>
<H1 class="title" id="parent-fieldname-title">%s
<a href="/webqtl/main.py?FormID=sharinginfoedit&GN_AccessionId=%s"><img src="/images/modify.gif" alt="modify this page" border="0" valign="middle"></a>
<span style="color:red;">%s</span>
</H1>
<table border="0" width="100%%">
<tr>
<td valign="top" width="50%%">
<TABLE cellSpacing=0 cellPadding=5 width=100%% border=0>
                      <TR><td><b>GN Accession:</b> GN%s</TD></tr>
                      <TR><TD><b>GEO Series:</b> %s</TD></TR>
                      <TR><TD><b>Title:</b> %s</TD></TR> 
                      <TR><TD><b>Organism:</b> <a href=http://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?mode=Info&id=%s>%s</a></TD></tr>
                      <tr><TD><b>Group:</b> %s</TD></TR>
                      <TR><TD><b>Tissue:</b> %s</TD></tr>
                      <tr><TD><b>Dataset Status:</b> %s</TD></tr>
                      <TR><TD><b>Platforms:</b> %s</TD></TR>
                      <TR><TD><b>Normalization:</b> %s</TD></TR>
                      <TR><TD><!--Code below to Show hide Contact information -->
                       <a href="#" onclick="colapse('answer1')">See Contact Information</a><br>
                       <span id="answer1" style="display: none; return: false;">
					   %s<br>
                       %s<br>
                       %s<br>
                       %s<br>
                       %s, %s %s %s<br>
                       Tel. %s<br>
                       %s<br>
                       <a href="%s">%s</a>
                       </span><!--Code above to Show hide Contact information --></TD></TR>
</TABLE>
</td>
<td valign="top" width="50%%">
<table border="0" width="100%%">
<tr>
	<td bgcolor="#dce4e1"><b>Download datasets and supplementary data files</b></td>
</tr>
<tr>
	<td>%s</td>
</tr>
</table>
</td>
</tr>
</table>
<HR>
<p>
<table width="100%%" border="0" cellpadding="5" cellspacing="0">
<tr><td><span style="font-size:115%%;font-weight:bold;">Summary:</span></td></tr>
	<tr><td> %s<br><br></td></tr>
<tr><td><span style="font-size:115%%;font-weight:bold;">About the cases used to generate this set of data:</span></td></tr>
	<tr><td> %s<br><br></td></tr>
<tr><td><span style="font-size:115%%;font-weight:bold;">About the tissue used to generate this set of data:</span></td></tr>
	<tr><td> %s<br><br></td></tr>
<tr><td><span style="font-size:115%%;font-weight:bold;">About downloading this data set:</span></td></tr>
	<tr><td> %s<br><br></td></tr>
<tr><td><span style="font-size:115%%;font-weight:bold;">About the array platform:</span></td></tr>
	<tr><td> %s<br><br></td></tr>
<tr><td><span style="font-size:115%%;font-weight:bold;">About data values and data processing:</span></td></tr>
	<tr><td> %s<br><br></td></tr>
<tr><td><span style="font-size:115%%;font-weight:bold;">Data source acknowledgment:</span></td></tr>
	<tr><td> %s<br><br></td></tr>
<tr><td><span style="font-size:115%%;font-weight:bold;">Experiment Type:</span></td></tr>
	<tr><td> %s<br><br></td></tr>
<tr><td><span style="font-size:115%%;font-weight:bold;">Overall Design:</span></td></tr>
	<tr><td> %s<br><br></td></tr>
<tr><td><span style="font-size:115%%;font-weight:bold;">Contributor:</span></td></tr>
	<tr><td> %s<br><br></td></tr>
<tr><td><span style="font-size:115%%;font-weight:bold;">Citation:</span></td></tr>
	<tr><td> %s<br><br></td></tr>
<tr><td><span style="font-size:115%%;font-weight:bold;">Submission Date:</span></td></tr>
	<tr><td> %s<br><br></td></tr>
<tr><td><span style="font-size:115%%;font-weight:bold;">Laboratory:</span></td></tr>
	<tr><td> %s<br><br></td></tr>
<tr><td><span style="font-size:115%%;font-weight:bold;">Samples:</span></td></tr>
	<tr><td> %s<br><br></td></tr>
</table>
</p>
</td>
"""

sharinginfoedit_body_string = """<td>
<H1 class="title">%s</H1>
<script language="javascript">
function CheckGNAccesionId(){
	if (document.sharinginfoupdate.GN_AccesionId.value.length  ==  0){
		alert("Please input GN Accesion Id");
		document.sharinginfoupdate.GN_AccesionId.focus();
		return false;
	} else {
		return true;
	}
}
</script>
<table border="0" CELLSPACING="0" CELLPADDING="8">
<form name="sharinginfoupdate" method="post" action="/webqtl/main.py?FormID=sharinginfoupdate" onsubmit="return CheckGNAccesionId();">
<input type="hidden" name="Id" value="%s">

  <tr><TH COLSPAN=2><h2 class="title">Principal Investigator</h2></TH></tr>
   <tr><td align="right" width="100"><b>Contact Name:</b></td><td width="200"><input type='text' name='Contact_Name' size='90' value='%s'></td></tr>
   <tr><td align="right"><b>Emails:</b></td><td><input type='text' name='Emails' size='90' value='%s'></td></tr>
   <tr><td align="right"><b>Phone:</b></td><td><input type='text' name='Phone' size='90' value='%s'></td></tr>
   <tr><td align="right"><b>URL:</b></td><td><input type='text' name='URL' size='90' value='%s'></td></tr>
   <tr><td align="right"><b>Organization Name:</b></td><td><input type='text' name='Organization_Name' size='90' value='%s'></td></tr>
   <tr><td align="right"><b>Department:</b></td><td><input type='text' name='Department' size='90' value='%s'></td></tr>
   <tr><td align="right"><b>Laboratory:</b></td><td><input type='text' name='Laboratory' size='90' value='%s'></td></tr>
   <tr><td align="right"><b>Address:</b></td><td><input type='text' name='Street' size='90' value='%s'></td></tr>
   <tr><td align="right"><b>City:</b></td><td><input type='text' name='City' size='90' value='%s'></td></tr>
   <tr><td align="right"><b>State:</b></td><td><input type='text' name='State' size='90' value='%s'></td></tr>
   <tr><td align="right"><b>ZIP:</b></td><td><input type='text' name='ZIP' size='90' value='%s'></td></tr>
   <tr><td align="right"><b>Country:</b></td><td><input type='text' name='Country' size='90' value='%s'></td></tr>
   
  <tr><TH COLSPAN=2><h2 class="title">Summary</h2></TH></tr>
  <tr><td align="right"><b>Summary: </b></td><td><TEXTAREA NAME="Summary" cols="77" rows="15">%s</textarea></td></tr>
   
  <tr><TH COLSPAN=2><h2 class="title">Biology</h2></TH></tr>
  <tr><td align="right"><b>Experiment Design:</b></td><td><TEXTAREA NAME="Experiment_Type" cols="77" rows="15">%s</textarea></td></tr>
  <tr><td align="right"><b>About the cases used to<br>generate this set of data:</b></td><td><TEXTAREA NAME="About_Cases" cols="77" rows="15">%s</textarea></td></tr>
  <tr><td align="right"><b>About the tissue used to<br>generate this set of data:</b></td><td><TEXTAREA NAME="About_Tissue" cols="77" rows="15">%s</textarea></td></tr>
  
  <tr><TH COLSPAN=2><h2 class="title">Technique</h2></TH></tr>
  <tr><td align="right"><b>About downloading this data set:</b></td><td><TEXTAREA NAME="About_Download" cols="77" rows="15">%s</textarea></td></tr>
  <tr><td align="right"><b>About the array platform:</b></td><td><TEXTAREA NAME="About_Array_Platform" cols="77" rows="15">%s</textarea></td></tr>
  
  <tr><TH COLSPAN=2><h2 class="title">Bioinformatics</h2></TH></tr>
  <tr><td align="right"><b>About data values and<br>data processing:</b></td><td><TEXTAREA NAME="About_Data_Values_Processing" cols="77" rows="15">%s</textarea></td></tr>
  <tr><td align="right"><b>Overall Design:</b></td><td><TEXTAREA NAME="Overall_Design" cols="77" rows="15">%s</textarea></td></tr>
  
  <tr><TH COLSPAN=2><h2 class="title">Misc</h2></TH></tr>
  <tr><td align="right"><b>Contributor:</b></td><td><TEXTAREA NAME="Contributor" cols="77" rows="15">%s</textarea></td></tr>
  <tr><td align="right"><b>Citation:</b></td><td><TEXTAREA NAME="Citation" cols="77" rows="5">%s</textarea></td></tr>
  <tr><td align="right"><b>Data source acknowledgment:</b></td><td><TEXTAREA NAME="Data_Source_Acknowledge" cols="77" rows="15">%s</textarea></td></tr>

  <tr><TH COLSPAN=2><h2 class="title">Administrator ONLY</h2></TH></tr>
  <tr><td align="right"><b>GN Accesion Id:</b></td><td><input type='text' name='GN_AccesionId' size='90' value='%s'></td></tr>
   <tr><td align="right"><b>DB Title in GN:</b></td><td><input type='text' name='InfoPageTitle' size='90' value='%s'></td></tr>
   <tr><td align="right"><b>GEO Series:</b></td><td><input type='text' name='GEO_Series' size='90' value='%s'></td></tr>
   <tr><td align="right"><b>Status:</b></td><td><input type='text' name='Status' size='90' value='%s'></td></tr>
   <tr><td align="right"><b>Title:</b></td><td><input type='text' name='Title' size='90' value='%s'></td></tr>
   <tr><td align="right"><b>Organism_Id (Taxonomy ID):</b></td><td><input type='text' name='Organism_Id' size='90' value='%s'></td></tr>
   <tr><td align="right"><b>Organism:</b></td><td><input type='text' name='Organism' size='90' value='%s'></td></tr>
   <tr><td align="right"><b>Submission Date:</b></td><td><input type='text' name='Submission_Date' size='90' value='%s'></td></tr>
   <tr><td align="right"><b>Platforms:</b></td><td><input type='text' name='Platforms' size='90' value='%s'></td></tr>
   <tr><td align="right"><b>Species:</b></td><td><input type='text' name='Species' size='90' value='%s'></td></tr>
   <tr><td align="right"><b>Tissue:</b></td><td><input type='text' name='Tissue' size='90' value='%s'></td></tr>
   <tr><td align="right"><b>Normalization:</b></td><td><input type='text' name='Normalization' size='90' value='%s'></td></tr>
   <tr><td align="right"><b>Inbred Set:</b></td><td><input type='text' name='InbredSet' size='90' value='%s'></td></tr>
   <tr><td align="right"><b>Info Page Name:</b></td><td><input type='text' name='InfoPageName' size='90' value='%s'></td></tr>
   <tr><td align="right"><b>Samples:</b></td><td><input type='text' name='Samples' size='90' value='%s'></td></tr>
   <tr><td align="right"><b>Authorized Users:</b></td><td><input type='text' name='AuthorizedUsers' size='90' value='%s'></td></tr>  
   <tr><td align="right"><b>Progress:</b></td><td><input type='text' name='Progress' size='90' value='%s'></td></tr>

  <tr><td> <colspan='2' align="center"><input type="Submit" class="button" style="font-size:12px" value="  Submit  "></td></tr>

</form>
</table>
</td>"""
