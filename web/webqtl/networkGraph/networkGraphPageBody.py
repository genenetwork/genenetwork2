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

from base.templatePage import templatePage
import networkGraphUtils
from base import webqtlConfig
         

# our output representation is fairly complicated
# because we use an iframe to represent the image and the image has
# an associated image map, our output is actually three files
# 1) a networkGraphPage instance -- the URL we pass to the user
# 2) a GraphPage with the image map and the graph -- this page has to be
#    there to pass the imagemap data to the browser
# 3) a PNG graph file itself

class networkGraphPageBody(templatePage):
    """
    Using the templatePage class, we build an HTML shell for the graph
    that displays the parameters used to generate it and allows the
    user to redraw the graph with different parameters.

    The way templatePage works, we build the page in pieces in the __init__
    method and later on use the inherited write method to render the page.
    """

    def __init__(self, fd, matrix, traits, imageHtmlName, imageName, pdfName, nodes,
                 edges, rawEdges, totalTime, p, graphcode, graphName, optimalNode):

        templatePage.__init__(self, fd)

        if p["printIslands"] == 0:
            island = "Only nodes with edges"
        else:
            island = "All nodes"

        body = """ <td><P class='title'>Network Graph</P>
        <Blockquote><p>The %s nodes in the
        graph below show the selected traits. %s are displayed. The
        %s edges between the nodes, filtered from the %s total edges and
        drawn as %s, show <b>%s</b> correlation
        coefficients greater than %s or less than -%s. The graph\'s
        canvas is %s by %s cm, and the node
        labels are drawn with a %s point font, and the edge 
        labels are drawn with a %s point font. Right-click or control-click
        on the graph to save it to disk for further manipulation. See
        below for the trait key, and graph options.</p>
        """ % (nodes, island, edges, rawEdges,
               p["splineName"], p["correlationName"], 
               p["kValue"],
               p["kValue"], 
               p["width"], 
               p["height"], 
               p["nfontsize"], 
               p["cfontsize"])
        
        #Generate a list of symbols for the central node selection drop-down menu
        
        symbolList = networkGraphUtils.generateSymbolList(traits)
        
        #Some of these hidden variables (CellID, CellID2, ProbesetID2, etc) exist 
        #to be used by the javascript functions called when a user clicks on an edge or node
        
        formParams = '''
        
        <form name="showDatabase" action="%s%s" METHOD="POST"  enctype="multipart/form-data">
        
        <input type="hidden" name="filename" value="%s" />
        <input type="hidden" name="exportFilename" value="%s" />
        <input type="hidden" name="progress" value="1" />
        <input type="hidden" name="database" value="_" />
        <input type="hidden" name="database2" value="_" />
        <input type="hidden" name="ProbeSetID" value="_" />
        <input type="hidden" name="ProbeSetID2" value="_" />
        <input type="hidden" name="CellID" value="_" />
        <input type="hidden" name="CellID2" value="_" />
        <input type="hidden" name="tune" value="no" />
        <input type="hidden" name="ShowLine" value="ON">
        <input type="hidden" name="ShowStrains" value="ON">
        <input type="hidden" name="FormID" value="showDatabase" />
        <input type="hidden" name="RISet" value="%s" />
        <input type="hidden" name="incparentsf1" value="ON" />
        <input type="hidden" name="session" value="%s" />
        <input type="hidden" name="searchResult" id="searchResult" value="%s" />
        <input type="hidden" name="symbolList" id="symbolList" value="%s" />
        <input type="hidden" name="optimalNode" id="optimalNode" value="%s" />
        <input type="hidden" name="rankOrder" id="rankOrder" value="_" />
        <input type="hidden" name="X_geneID" id="X_geneID" value="_" />
        <input type="hidden" name="Y_geneID" id="Y_geneID" value="_" />
        <input type="hidden" name="X_geneSymbol" id="X_geneSymbol" value="_" />
        <input type="hidden" name="Y_geneSymbol" id="Y_geneSymbol" value="_" />
        <input type="hidden" name="TissueProbeSetFreezeId" id="TissueProbeSetFreezeId" value="1" />
        ''' % (webqtlConfig.CGIDIR,
               webqtlConfig.SCRIPTFILE,
               p["filename"],
               graphName,
               p["riset"],
               p["session"],
               p["searchResult"],
               symbolList,
               optimalNode)
        
        body += formParams
        
        #Adds the html generated by graphviz that displays the graph itself
        body += graphcode

        #Initializes all form values

        selected = ["","","",""]
        selected[p["whichValue"]] = "CHECKED"

        selected3 = ["",""]
        if p["splines"] == "yes":
            selected3[0] = "CHECKED"
        else:
            selected3[1] = "CHECKED"

        selected5 = ["",""]
        if p["nodeshape"] == "yes":
            selected5[0] = "CHECKED"
        else:
            selected5[1] = "CHECKED"
            
        selected7 = ["",""]
        if p["nodelabel"] == "yes":
            selected7[0] = "CHECKED"
        else:
            selected7[1] = "CHECKED"
            
        selected6 = ["",""]
        if p["dispcorr"] == "yes":
            selected6[0] = "CHECKED"
        else:
            selected6[1] = "CHECKED"

        selected4 = ["", ""]
        selected4[p["printIslands"]] = "CHECKED"
       
        selectedExportFormat = ["",""]
        if p["exportFormat"] == "xgmml":
            selectedExportFormat[0] = "selected='selected'"
        elif p["exportFormat"] == "plain":
            selectedExportFormat[1] = "selected='selected'"
        
        selectedTraitType = ["",""]
        if p["traitType"] == "symbol":
            selectedTraitType[0] = "selected='selected'"
        elif p["traitType"] == "name":
            selectedTraitType[1] = "selected='selected'"

	selectedgType = ["","","","",""]
	if p["gType"] == "none":
	    selectedgType[0] = "selected='selected'"
        elif p["gType"] == "neato":
            selectedgType[1] = "selected='selected'"
	elif p["gType"] == "fdp":
	    selectedgType[2] = "selected='selected'"
	elif p["gType"] == "circular":
	    selectedgType[3] = "selected='selected'"
	elif p["gType"] == "radial":
	    selectedgType[4] = "selected='selected'"	
 
 
        selectedLock = ["",""]
        if p["lock"] == "no":
            selectedLock[0] = "selected='selected'"
        elif p["lock"] == "yes":
            selectedLock[1] = "selected='selected'"
 
        # line 1~6
        
        selectedL1style = ["","","","",""]
        if p["L1style"] == "":
            selectedL1style[0] = "selected='selected'"
        elif p["L1style"] == "bold":
            selectedL1style[1] = "selected='selected'"
        elif p["L1style"] == "dotted":
            selectedL1style[2] = "selected='selected'"
        elif p["L1style"] == "dashed":
            selectedL1style[3] = "selected='selected'"
        else:
            selectedL1style[4] = "selected='selected'"
        
        selectedL2style = ["","","","",""]
        if p["L2style"] == "":
            selectedL2style[0] = "selected='selected'"
        elif p["L2style"] == "bold":
            selectedL2style[1] = "selected='selected'"
        elif p["L2style"] == "dotted":
            selectedL2style[2] = "selected='selected'"
        elif p["L2style"] == "dashed":
            selectedL2style[3] = "selected='selected'"
        else:
            selectedL2style[4] = "selected='selected'"
        
        selectedL3style = ["","","","",""]
        if p["L3style"] == "":
            selectedL3style[0] = "selected='selected'"
        elif p["L3style"] == "bold":
            selectedL3style[1] = "selected='selected'"
        elif p["L3style"] == "dotted":
            selectedL3style[2] = "selected='selected'"
        elif p["L3style"] == "dashed":
            selectedL3style[3] = "selected='selected'"
        else:
            selectedL3style[4] = "selected='selected'"
        
        selectedL4style = ["","","","",""]
        if p["L4style"] == "":
            selectedL4style[0] = "selected='selected'"
        elif p["L4style"] == "bold":
            selectedL4style[1] = "selected='selected'"
        elif p["L4style"] == "dotted":
            selectedL4style[2] = "selected='selected'"
        elif p["L4style"] == "dashed":
            selectedL4style[3] = "selected='selected'"
        else:
            selectedL4style[4] = "selected='selected'"
        
        selectedL5style = ["","","","",""]
        if p["L5style"] == "":
            selectedL5style[0] = "selected='selected'"
        elif p["L5style"] == "bold":
            selectedL5style[1] = "selected='selected'"
        elif p["L5style"] == "dotted":
            selectedL5style[2] = "selected='selected'"
        elif p["L5style"] == "dashed":
            selectedL5style[3] = "selected='selected'"
        else:
            selectedL5style[4] = "selected='selected'"
        
        selectedL6style = ["","","","",""]
        if p["L6style"] == "":
            selectedL6style[0] = "selected='selected'"
        elif p["L6style"] == "bold":
            selectedL6style[1] = "selected='selected'"
        elif p["L6style"] == "dotted":
            selectedL6style[2] = "selected='selected'"
        elif p["L6style"] == "dashed":
            selectedL6style[3] = "selected='selected'"
        else:
            selectedL6style[4] = "selected='selected'"
            
        nfontSelected = ["", "", ""]
        if p["nfont"] == "arial":
            nfontSelected[0] = "selected='selected'"
        elif p["nfont"] == "verdana":
            nfontSelected[1] = "selected='selected'"
        elif p["nfont"] == "times":
            nfontSelected[2] = "selected='selected'"
            
        cfontSelected = ["", "", ""]
        if p["cfont"] == "arial":
            cfontSelected[0] = "selected='selected'"
        elif p["cfont"] == "verdana":
            cfontSelected[1] = "selected='selected'"
        elif p["cfont"] == "times":
            cfontSelected[2] = "selected='selected'"
 
        #Writes the form part of the body
 
        body += ''' <br><br>
        <TABLE cellspacing=0 Cellpadding=0>
        <TR>
        <TD class="doubleBorder">
       
        <Table Cellpadding=3>
        
        <tr><td align="left">
        <dd>
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
        <input type="submit" name="mintmap" value="    Redraw    " class="button" onClick="return sortSearchResults(this.form);" />
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
        <input TYPE="Button" class="button" value="    Info    " onclick="javascript:window.open('/networkGraphInfo.html', '_blank');">
        </dd>
        </td></tr>
        
        <tr><td align='center' colspan='2'><hr size='1'></td></tr>
    <tr>
		<tr align='left' valign='top'>
		    <td align='left'>
		    &nbsp;<select align='left' name='gType' id='gType' onchange='addTraitSelection();'>
		    <option value='none' %s>Select Graph Method</option>
			<option value='neato' %s>Spring Model Layout (energy reduction)</option>
			<option value='fdp' %s>Spring Model Layout (force reduction)</option>
			<option value='circular' %s>Circular Layout</option>
			<option value='radial' %s>Radial Layout</option>
		    </select>
		    <div align="left" id='nodeSelect'> </div>
		    </td>
		</tr>
	</tr>
	
	    <tr><td align='center' colspan='2'><hr size='1'></td></tr>
	    
    <tr><td align='center' colspan='2'>

        <table width='100%%'>

        <tr align='left'>
            <td>Lock Graph Structure</td>
            <td align='left'><select name='lock' id='lock' onChange="changeThreshold();">
            <option value='no' %s>No</option>
            <option value='yes' %s>Yes</option>
            </select></td>
        </tr>
        <tr><td align='left' colspan='2' nowrap='nowrap'>
        Locking the graph structure allows the user to hold the position of<br>
        all nodes and the length of all edges constant, letting him/her easily<br>
        compare between different correlation types. Changing the value to "yes"<br> 
        requires the line threshold to be set to 0 in order to lock the structure.<br>
        </td></tr>
        </td>
    </tr>
	
	
	<tr><td align='center' colspan='2'><hr size='1'></td></tr>        

        <tr><td align='center' colspan='2'>
            
                <table width='100%%'>
                
                <tr align='center'>
                    <td>Line Type 1:</td>
                    <td>-1</td>
                    <td>to</td>
                    <td>-0.7</td>
                    <td><Input type=radio name=colorS value="cL1" checked></TD>
                    <td bgcolor="%s" ID="cL1" width=20></td>
                    <td><select name='L1style'>
                        <option value='' %s>normal</option>
                        <option value='bold' %s>bold</option>
                        <option value='dotted' %s>dotted</option>
                        <option value='dashed' %s>dashed</option>
                        <option value='invis' %s>invisible</option>
                    </select></td>
                </tr>
                
                <tr align='center'>
                    <td>Line Type 2:</td>
                    <td>-0.7</td>
                    <td>to</td>
                    <td>-0.5</td>
                    <td><Input type=radio name=colorS value="cL2"></TD>
                    <Td bgcolor="%s" ID="cL2" width=20></td>
                    <td><select name='L2style'>
                        <option value='' %s>normal</option>
                        <option value='bold' %s>bold</option>
                        <option value='dotted' %s>dotted</option>
                        <option value='dashed' %s>dashed</option>
                        <option value='invis' %s>invisible</option>
                    </select></td>
                </tr>
                
                <tr align='center'>
                    <td>Line Type 3:</td>
                    <td>-0.5</td>
                    <td>to</td>
                    <td>0</td>
                    <td><Input type=radio name=colorS value="cL3"></TD>
                    <Td bgcolor="%s" ID="cL3" width=20></td>
                    <td><select name='L3style'>
                        <option value='' %s>normal</option>
                        <option value='bold' %s>bold</option>
                        <option value='dotted' %s>dotted</option>
                        <option value='dashed' %s>dashed</option>
                        <option value='invis' %s>invisible</option>
                    </select></td>
                </tr>
                
                <tr align='center'>
                    <td>Line Type 4:</td>
                    <td>0</td>
                    <td>to</td>
                    <td>0.5</td>
                    <td><Input type=radio name=colorS value="cL4"></TD>
                    <Td bgcolor="%s" ID="cL4" width=20></td>
                    <td><select name='L4style'>
                        <option value='' %s>normal</option>
                        <option value='bold' %s>bold</option>
                        <option value='dotted' %s>dotted</option>
                        <option value='dashed' %s>dashed</option>
                        <option value='invis' %s>invisible</option>
                    </select></td>
                </tr>
                
                <tr align='center'>
                    <td>Line Type 5:</td>
                    <td>0.5</td>
                    <td>to</td>
                    <td>0.7</td>
                    <td><Input type=radio name=colorS value="cL5"></TD>
                    <Td bgcolor="%s" ID="cL5" width=20></td>
                    <td><select name='L5style'>
                        <option value='' %s>normal</option>
                        <option value='bold' %s>bold</option>
                        <option value='dotted' %s>dotted</option>
                        <option value='dashed' %s>dashed</option>
                        <option value='invis' %s>invisible</option>
                    </select></td>
                </tr>
                
                <tr align='center'>
                    <td>Line Type 6:</td>
                    <td>0.7</td>
                    <td>to</td>
                    <td>1</td>
                    <td><Input type=radio name=colorS value="cL6"></TD>
                    <Td bgcolor="%s" ID="cL6" width=20></td>
                    <td><select name='L6style'>
                        <option value='' %s>normal</option>
                        <option value='bold' %s>bold</option>
                        <option value='dotted' %s>dotted</option>
                        <option value='dashed' %s>dashed</option>
                        <option value='invis' %s>invisible</option>
                    </select></td>
                </tr>
                
                </table>
            </td>
        </tr>
        
        <tr><td align='center' colspan='2' nowrap='nowrap'>To change colors, select Line Type then select Color below.</td></tr>
        
        <tr><td align='center' colspan='2'><hr size='1'></td></tr>
        
        <tr>
            <TD align="right">Correlation Type:</TD>
            <TD>
                <table border='0' cellspacing='0' cellpadding='0' width='100%%'>
                    <tr>
                        <td><Input type="radio" name="whichValue" value="0" %s>Pearson</td>
                        <td><Input type="radio" name="whichValue" value="1" %s>Spearman</td>
                        <td rowspan=2 align="center"><input TYPE="Button" class="button" value="Info" onclick="javascript:window.open('/correlationAnnotation.html', '_blank');"></td>
                    </tr>
                    <tr>
                        <td><Input type="radio" name="whichValue" value="2" %s>Literature</td>
                        <td><Input type="radio" name="whichValue" value="3" %s>Tissue</td>
                    </tr>
                </table>
            </TD>
        </TR>
        
        <TR>
            <TD align="right" NOWRAP>Line Threshold:</TD>
            <TD NOWRAP>Absolute values greater than <input size="5" name="kValue" id="kValue" value="%s"></TD>
        </TR>
        
        <tr><td align='center' colspan='2'><hr size='1'></td></tr>
        
        <TR>
            <TD align="right">Draw Nodes :</TD>
            <TD NOWRAP>
                <Input type="radio" name="printIslands" value="1" %s>all
                <Input type="radio" name="printIslands" value="0" %s>connected only
            </TD>
        </TR>
        
        <TR>
            <TD align="right">Node Shape:</TD>
            <TD>
                <Input type="radio" name="nodeshape" value="yes" %s>rectangle
                <Input type="radio" name="nodeshape" value="no" %s>ellipse
            </TD>
        </TR>
        
        <TR>
            <TD align="right">Node Label:</TD>
            <TD>
                <Input type="radio" name="nodelabel" value="yes" %s>trait name<br>
                <Input type="radio" name="nodelabel" value="no" %s>gene symbol / marker name
            </TD>
        </TR>
        
        <tr>
            <td align="right">Node Font:</td>
            <TD>
                <select name='nfont'>
                    <option value='Arial' %s>Arial</option>
                    <option value='Verdana' %s>Verdana</option>
                    <option value='Times' %s>Times</option>
                </select>
            </TD>
        </TR>
        
        <tr>
            <td align="right">Node Font Size:</td>
            <TD><input size="5" name="nfontsize" value="%s"> point</TD>
        </TR>
        
        <tr><td align='center' colspan='2'><hr size='1'></td></tr>
        
        <TR>
            <TD align="right">Draw Lines:</TD>
            <TD>
                <Input type="radio" name="splines" value="yes" %s>curved
                <Input type="radio" name="splines" value="no" %s>straight
            </TD>
        </TR>
        
        <TR>
            <TD align="right">Display Correlations:</TD>
            <TD>
                <Input type="radio" name="dispcorr" value="no" %s>no
                <Input type="radio" name="dispcorr" value="yes" %s>yes
            </TD>
        </tr>
        
        <tr>
            <td align="right">Line Font:</td>
            <TD>
                <select name='cfont'>
                    <option value='Arial' %s>Arial</option>
                    <option value='Verdana' %s>Verdana</option>
                    <option value='Times' %s>Times</option>
                </select>
            </TD>
        </TR>
        
        <TR>
            <TD align="right" nowrap="nowrap">Line Font Size:</TD>
            <TD><input size="5" name="cfontsize" value="%s"> point</TD>
        </TR>
        
        <tr><td align='center' colspan='2'><hr size='1'></td></tr>
        
        <TR><TD colspan = 2>
        
        <Input type=hidden name=cPubName value="%s">
        <Input type=hidden name=cMicName value="%s">
        <Input type=hidden name=cGenName value="%s">
        
        <Input type=hidden name=cPubColor value="%s">
        <Input type=hidden name=cMicColor value="%s">
        <Input type=hidden name=cGenColor value="%s">
        
        <Input type=hidden name=cL1Name value="%s">
        <Input type=hidden name=cL2Name value="%s">
        <Input type=hidden name=cL3Name value="%s">
        <Input type=hidden name=cL4Name value="%s">
        <Input type=hidden name=cL5Name value="%s">
        <Input type=hidden name=cL6Name value="%s">
        
        <Input type=hidden name=cL1Color value="%s">
        <Input type=hidden name=cL2Color value="%s">
        <Input type=hidden name=cL3Color value="%s">
        <Input type=hidden name=cL4Color value="%s">
        <Input type=hidden name=cL5Color value="%s">
        <Input type=hidden name=cL6Color value="%s">
        
        <Input type=hidden id=initThreshold value="0.5">
        
		<Table CellSpacing = 3>
			<tr>
			    <TD><Input type=radio name=colorS value="cPub"> Publish </TD>
			    <Td bgcolor="%s" ID="cPub" width=20 height=10></td>
			    <TD><Input type=radio name=colorS value="cMic"> Microarray </TD>
			    <Td bgcolor="%s" ID="cMic" width=20 height=10></td>
			    <TD><Input type=radio name=colorS value="cGen"> Genotype </TD>
			    <Td bgcolor="%s" ID="cGen" width=20 height=10></td>
			</tr>
		</table>
		
		</td></tr>
		
		<tr><td align='center' colspan='2'><hr size='1'></td></tr>
		
		<tr>
		    <td colspan='2' align='center'>
		        <img NAME="colorPanel" src="/images/colorPanel.png" alt="colorPanel" onClick="clickHandler(event, this);">
		    </TD>
		</TR>
		
		<tr><td align='center' colspan='2'><hr size='1'></td></tr>
		
		<tr><td align='center' colspan='2'><input type="submit" name="mintmap" value="    Redraw Graph    " class="button" onClick="return sortSearchResults(this.form);"/></td></tr>
        
        </TABLE>
        </form></TD>
        <SCRIPT type="text/javascript" SRC="/javascript/networkGraph.js"></SCRIPT>
        ''' % (selectedgType[0], selectedgType[1], selectedgType[2], selectedgType[3], selectedgType[4],
                           selectedLock[0], selectedLock[1],
                           p["cL1Color"],
                           selectedL1style[0], selectedL1style[1], selectedL1style[2], selectedL1style[3], selectedL1style[4],
                           p["cL2Color"],
                           selectedL2style[0], selectedL2style[1], selectedL2style[2], selectedL2style[3], selectedL2style[4],
                           p["cL3Color"],
                           selectedL3style[0], selectedL3style[1], selectedL3style[2], selectedL3style[3], selectedL3style[4],
                           p["cL4Color"],
                           selectedL4style[0], selectedL4style[1], selectedL4style[2], selectedL4style[3], selectedL4style[4],
                           p["cL5Color"],
                           selectedL5style[0], selectedL5style[1], selectedL5style[2], selectedL5style[3], selectedL5style[4],
                           p["cL6Color"],
                           selectedL6style[0], selectedL6style[1], selectedL6style[2], selectedL6style[3], selectedL6style[4],
                           selected[0], selected[1], selected[2], selected[3],
                           p["kValue"], 
                           selected4[1], selected4[0], 
                           selected5[0], selected5[1], 
                           selected7[0], selected7[1],
                           nfontSelected[0], nfontSelected[1], nfontSelected[2],
                           p["nfontsize"],
                           selected3[0], selected3[1], 
                           selected6[1], selected6[0],
                           cfontSelected[0], cfontSelected[1], cfontSelected[2],
                           p["cfontsize"],
                           p["cPubName"], p["cMicName"], p["cGenName"],
                           p["cPubColor"], p["cMicColor"], p["cGenColor"],
                           p["cL1Name"], p["cL2Name"], p["cL3Name"], p["cL4Name"], p["cL5Name"], p["cL6Name"],
                           p["cL1Color"], p["cL2Color"], p["cL3Color"], p["cL4Color"], p["cL5Color"], p["cL6Color"],
                           p["cPubColor"], p["cMicColor"], p["cGenColor"])
        
		#updated by NL 09-03-2010 function changeFormat() has been moved to webqtl.js and be changed to changeFormat(graphName)
        #Javascript that selects the correct graph export file given what the user selects 
        #from the two drop-down menus

        body += ''' <td width='10'>&nbsp;</td> 
        <TD valign="top"><p>Right-click or control-click on the following
        links to download this graph as a <a href="%s" class="normalsize" target="_blank">GIF file</a> or
        a <a href="%s" class="normalsize" target="_blank">PDF file</a>.</p> ''' % (imageName, pdfName)
        
        body += ''' <p>Initial edge lengths were computed by applying an r-to-Z transform to the correlation coefficents
        and then inverting the results. The graph drawing algorithm
        found a configuration that minimizes the total stretching of the edges.</p> ''' 
        
        body += ''' <p>This graph took %s seconds to generate with the <a href="http://www.research.att.com/sw/tools/graphviz/" class="normalsize" target="_blank">
        GraphViz</a> visualization toolkit from <a href="http://www.research.att.com" class="normalsize" target="_blank">AT&amp;T Research</a>.</p>''' % (round(totalTime, 2))
        
        #Form to export graph file as either XGMML (standardized graphing format) or a
        #plain text file with trait names/symbols and correlations
        
        body += '''
        <form name="graphExport">
        <p>Export Graph File:</p>
        <p><select name='exportFormat' id='exportFormat' onchange='changeFormat("%s")'>
            <option value='plain' %s>Plain Text Format</option>
            <option value='xgmml' %s>XGMML Format</option>
        </select>
        &nbsp&nbsp&nbsp&nbsp&nbsp
        <select name='traitType' id='traitType' onchange='changeFormat("%s")'>
            <option value='symbol' %s>Trait Symbol</option>
            <option value='name' %s>Full Trait Name</option>
        </select></p>
        
        <p>
        <input type="button" class="button" name="exportGraphFile" value="   Export Graph File   "/>
        </p>
        </form> 
        ''' % (graphName, selectedExportFormat[0], selectedExportFormat[1],
               graphName, selectedTraitType[0], selectedTraitType[1])

        body += '''</Blockquote></td>
        </TR></TABLE> 
        <form method="get" action="http://www.google.com/search">
        <input type="text"   name="q" size="31" maxlength="255" value="" />
        <input type="submit" value="Google Search" />
        <input type="radio"  name="sitesearch" value="" /> The Web
        <input type="radio"  name="sitesearch" value="genenetwork.org" checked /> GeneNetwork <br />
        </form>
        ''' 

        
        self.dict["body"] = body

    def writeToFile(self, filename):
        """
        Output the contents of this HTML page to a file.
        """
        handle = open(filename, "w")
        handle.write(str(self))
        handle.close()
