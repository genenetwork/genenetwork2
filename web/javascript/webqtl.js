// var NS4 = (document.layers) ? 1 : 0;
// var IE4 = (document.all) ? 1 : 0;

function openNewWin(myURL){
	windowName = 'formTarget' + (new Date().getTime());
	if (openNewWin.arguments.length == 2){
  		newWindow = open(myURL,windowName,openNewWin.arguments[1]);
	}
	else{
		newWindow = open(myURL,windowName,"menubar=1,toolbar=1,location=1,resizable=1,status=1,scrollbars=1,directories=1,width=900");
	}
}

/*XZ, 9/2/2009*/
/*submit form to new window*/
function submitToNewWindow(thisForm){
        var windowName = genNewWin();
        newWindow = open("",windowName,"menubar=1,toolbar=1,location=1,resizable=1,status=1,scrollbars=1,directories=1,width=900");
        newWindow.focus();
        thisForm.target = windowName;
        thisForm.submit();
}

/*Obsolete and To be mofdified*/
/*
function makeTree(thisForm, nnn){
  	var trait_list2 = new Array();
	var correlation2 = new Array();
	var symbol_list2 = new Array();
	var length = document.showDatabase.searchResult.length;
	var j = 0
	for(var i = 0; i < length; i++)
	{
		if (document.showDatabase.searchResult[i].checked == true){
			trait_list2 = trait_list2.concat(trait_list[i]);
			correlation2 = correlation2.concat(correlation[i]);
			symbol_list2 = symbol_list2.concat(symbol_list[i]);
			j += 1;
		}
	}
	
	var windowName = 'formTarget' + (new Date().getTime());
	var newWindow = open("", windowName,"width=900,menubar=0,toolbar=1,resizable=1,status=1,scrollbars=1");
	var html = "";
	if (j > 0)
	{	
		var waithtml1 ="<Blockquote class='title' id='red'>Your list of "+j+" transcripts is being exported to the Gene Ontology Tree Machine for analysis. This window will soon be replaced with the main GOTM results.</Blockquote>";
	}
	else
	{	
		var waithtml1 ="<Blockquote class='title' id='red'>Your should select at least one transcript to export to the Gene Ontology Tree Machine for analysis.</Blockquote>";
	}
  	html +=  waithtml1;
  	//newWindow.document.write(html);
  	//newWindow.document.close();
  	newWindow.focus();
  	if (j > 0)
  	{
		thisForm.trait_list.value = trait_list2.join(',');
		thisForm.correlation.value = correlation2.join(',');
		thisForm.symbol_list.value = symbol_list2.join(',');
		thisForm.target = windowName;
		thisForm.submit();
	}
}
*/

function showCorrelationPlot(ProbeSetID,CellID){
	windowName = 'formTarget' + (new Date().getTime());
	newWindow = open("",windowName,"menubar=1,toolbar=1,location=1,resizable=1,status=1,scrollbars=1,directories=1,width=900");
	document.showDatabase.target = windowName;
	document.showDatabase.FormID.value = "showCorrelationPlot";
	document.showDatabase.ProbeSetID.value = ProbeSetID;
	document.showDatabase.CellID.value = CellID;
	document.showDatabase.submit();
}


function showPairPlot(ChrA,ChrB){
	windowName = 'formTarget' + (new Date().getTime());
	newWindow = open("",windowName,"menubar=1,toolbar=1,location=1,resizable=1,status=1,scrollbars=1,directories=1,width=900");
	document.showPairPlot.target = windowName;
	document.showPairPlot.Chr_A.value = ChrA;
	document.showPairPlot.Chr_B.value = ChrB;
	document.showPairPlot.submit();
}

function showCorrelationPlot2(db, ProbeSetID, CellID, db2, ProbeSetID2, CellID2, rank){
	windowName = 'formTarget' + (new Date().getTime());
	newWindow = open("",windowName,"menubar=1,toolbar=1,location=1,resizable=1,status=1,scrollbars=1,directories=1,width=900");
	document.showDatabase.target = windowName;
	document.showDatabase.FormID.value = "showCorrelationPlot";
	document.showDatabase.database.value = db;
	document.showDatabase.ProbeSetID.value = ProbeSetID;
	document.showDatabase.CellID.value = CellID;
	document.showDatabase.database2.value = db2;
	document.showDatabase.ProbeSetID2.value = ProbeSetID2;
	document.showDatabase.CellID2.value = CellID2;
	document.showDatabase.rankOrder.value = rank;

	//This is to make sure the type of correlation is Sample Correlation
	if(typeof(document.showDatabase.X_geneSymbol) !== 'undefined'){
		document.showDatabase.X_geneSymbol.value = null;
		document.showDatabase.Y_geneSymbol.value = null;
	}

	document.showDatabase.submit();
}


function showProbeInfo(Database,ProbeSetID,CellID){
	windowName = 'formTarget' + (new Date().getTime());
	newWindow = open("",windowName,"menubar=1,toolbar=1,location=1,resizable=1,status=1,scrollbars=1,directories=1,width=900");
	document.showDatabase.target = windowName;
	document.showDatabase.FormID.value = "showProbeInfo";
	document.showDatabase.database.value = Database;
	document.showDatabase.ProbeSetID.value = ProbeSetID;
	document.showDatabase.CellID.value = CellID;
	document.showDatabase.submit();
}


function showDatabase(ProbeSetID,CellID){
	windowName = 'formTarget' + (new Date().getTime());
	newWindow = open("",windowName,"menubar=1,toolbar=1,location=1,resizable=1,status=1,scrollbars=1,directories=1,width=900");
	document.showDatabase.target = windowName;
	document.showDatabase.FormID.value = "showDatabase";
	document.showDatabase.ProbeSetID.value = ProbeSetID;
	document.showDatabase.CellID.value = CellID;
	document.showDatabase.submit();
}



function showDatabase2(Database,ProbeSetID,CellID){
	windowName = 'formTarget' + (new Date().getTime());
	newWindow = open("",windowName,"menubar=1,toolbar=1,location=1,resizable=1,status=1,scrollbars=1,directories=1,width=900");
	document.showDatabase.target = windowName;
	document.showDatabase.FormID.value = "showDatabase";
	document.showDatabase.database.value = Database;
	document.showDatabase.ProbeSetID.value = ProbeSetID;
	document.showDatabase.CellID.value = CellID;
	document.showDatabase.submit();
}


function showDatabase3(formName, Database,ProbeSetID,CellID){
	windowName = 'formTarget' + (new Date().getTime());
	newWindow = open("",windowName,"menubar=1,toolbar=1,location=1,resizable=1,status=1,scrollbars=1,directories=1,width=900");
	document[formName].target = windowName;
	document[formName].FormID.value = "showDatabase";
	document[formName].database.value = Database;
	document[formName].ProbeSetID.value = ProbeSetID;
	document[formName].CellID.value = CellID;
	document[formName].submit();
}


function showTextResult(){
	windowName = 'formTarget' + (new Date().getTime());
	newWindow = open("",windowName,"menubar=1,toolbar=1,location=1,resizable=1,status=1,scrollbars=1,directories=1,width=900");
	document.SEARCHFORM.target = windowName;
	document.SEARCHFORM.submit();
	newWindow.focus()
}

/*New form name independent function*/
function getForm(fmName){
	var match = 0;
	for (i=0; i< document.forms.length;i++){
		if (document.forms[i].name == fmName){
			thisForm = document.forms[i];
			match = 1;
			return thisForm;
		}
	}
	if (match == 0)
		return null;
}

function genNewWin(){
	windowName = 'formTarget' + (new Date().getTime());
	newWindow = open("",windowName, "menubar=1,toolbar=1,location=1,resizable=1,status=1,scrollbars=1,directories=1,width=900");
	return windowName;
}

function showTrait(fmName){
	var thisForm = getForm(fmName);
	if (thisForm == null || showTrait.arguments.length < 2)
		return;
	
	windowName = genNewWin();
	thisForm.target = windowName;
	
	thisForm.FormID.value = "showDatabase";
	thisForm.ProbeSetID.value = showTrait.arguments[1];
	if (showTrait.arguments.length > 2)
		thisForm.CellID.value = showTrait.arguments[2];
	else
		thisForm.CellID.value = "";
	thisForm.submit();
}

function showCateGraph(fmName){
	var thisForm = getForm(fmName);
	if (thisForm == null || showCateGraph.arguments.length < 2)
		return;
	
	windowName = genNewWin();
	thisForm.target = windowName;
	
	thisForm.FormID.value = "showCategoryGraph";
	thisForm.interval1.value = showCateGraph.arguments[1];
	thisForm.interval2.value = showCateGraph.arguments[2];
	thisForm.submit();
}

function showCorrPlot(fmName){
	var thisForm = getForm(fmName);
	if (thisForm == null || showCorrPlot.arguments.length < 2)
		return;
	
	windowName = genNewWin();
	thisForm.target = windowName;
	
	thisForm.FormID.value = "showCorrelationPlot";
	thisForm.ProbeSetID.value = showCorrPlot.arguments[1];
	if (showCorrPlot.arguments.length > 2)
		thisForm.CellID.value = showCorrPlot.arguments[2];
	else
		thisForm.CellID.value = "";
	
	thisForm.X_geneSymbol.value = null;
	thisForm.Y_geneSymbol.value = null;

	thisForm.submit();
	
}


function showCorrPlotThird(fmName){
	var thisForm = getForm(fmName);
	if (thisForm == null || showCorrPlotThird.arguments.length < 3)
		return;
	
	windowName = genNewWin();
	thisForm.target = windowName;
	
	var olddb = thisForm.database.value;
	
	thisForm.FormID.value = "showCorrelationPlot";
	thisForm.database.value = showCorrPlotThird.arguments[1];
	thisForm.ProbeSetID.value = showCorrPlotThird.arguments[2];
	if (showCorrPlotThird.arguments.length > 3)
		thisForm.CellID.value = showCorrPlotThird.arguments[3];
	else
		thisForm.CellID.value = "";
	thisForm.submit();
	thisForm.database.value = olddb;
}

/*
function ODE(thisForm, script){
	var trait_list_all = new Array();
	var correlation_all = new Array();
	var llid_list_all = new Array();
  	var trait_list2 = new Array();
	var correlation2 = new Array();
	var llid_list2 = new Array();
	var length = thisForm.searchResult.length;
	var j = 0;
	for(var i = 0; i < length; i++){
		var p = corrArray[thisForm.searchResult[i].value];
		if (thisForm.searchResult[i].checked == true){
			trait_list2 = trait_list2.concat(p.name);
			correlation2 = correlation2.concat(p.corr);
			llid_list2 = llid_list2.concat(p.geneid);
			j += 1;
		}
		trait_list_all = trait_list_all.concat(p.name);
		correlation_all = correlation_all.concat(p.corr);
		llid_list_all = llid_list_all.concat(p.geneid);
	}
	var windowName = 'formTarget' + (new Date().getTime());
	var newWindow = open("", windowName, "width=900,menubar=0,toolbar=1,resizable=1,status=1,scrollbars=1");
	var html = "";
	if (j == 0){	
		j = length;
		trait_list2 = trait_list_all;
		correlation2 = correlation_all;
		llid_list2 = llid_list_all;
	}
	
	var waithtml1 ="<Blockquote class='title' id='red'>Your list of "+j+" transcripts is being exported to the ODE for analysis. This window will soon be replaced with the results.</Blockquote>";
	
  	html +=  waithtml1;
  	newWindow.document.write(html);
  	newWindow.document.close();
  	newWindow.focus();
  	if (j > 0){
		thisForm.id_list.value = trait_list2.join(',');
		thisForm.correlation.value = correlation2.join(',');
		thisForm.id_value.value = thisForm.correlation.value;
		thisForm.llid_list.value = llid_list2.join(',');
		
		// ODE
		
		thisForm.idtype.value = thisForm.id_type.value;
		thisForm.species.value = thisForm.org.value;
		thisForm.list.value = thisForm.id_list.value;
		thisForm.client.value = "genenetwork";
		
		thisForm.target = windowName;
		var oldaction = thisForm.action;
		thisForm.action = script;
		thisForm.submit();
		thisForm.action = oldaction;
	}
}
*/
// 02/12/2009 
// Lei Yan

/*scripts in the Dataediting form*/

function dataEditingFunc(thisForm,submitIdValue){
	
	windowName = 'formTarget' + (new Date().getTime());

	if (thisForm.FormID.value!='secondRegression'){
		thisForm.FormID.value = 'dataEditing';
	}

	if ((submitIdValue == "markerRegression")||(submitIdValue == "compositeRegression")){
		thisForm.topten.value = "";
	}

	else if (submitIdValue == "addRecord"){
		windowName = thisForm.RISet.value;	
		var name = thisForm.identification.value;
		if (name != ""){
		}
		else{
			name = "Unnamed Trait";
    		}
		Namebox = prompt("Name of your trait",name);
		thisForm.identification.value = Namebox;
	}

	else{
	}

	newWindow = open("",windowName,"menubar=1,toolbar=1,location=1,resizable=1,status=1,scrollbars=1,directories=1,width=900");
	thisForm.target = windowName;
	newWindow.focus();		
	thisForm.submitID.value = submitIdValue;
	thisForm.submit();
}

/*searchForm etc.*/
function databaseFunc(thisForm,formIdValue){
	if(formIdValue=="GOTree" && typeof(corrArray)!='undefined' && corrArray!=null){
                makeListCorrelation(thisForm);
        }

	windowName = 'formTarget' + (new Date().getTime());
	newWindow = open("",windowName,"menubar=1,toolbar=1,location=1,resizable=1,status=1,scrollbars=1,directories=1,width=900");
	if (databaseFunc.arguments.length > 2){
  		newWindow.document.write("<center><H3><font color='black' face='verdana'>" + databaseFunc.arguments[2]+ "</font></h3></center>");
  		newWindow.document.close();
	}
	newWindow.focus();
	thisForm.target = windowName;
	thisForm.FormID.value = formIdValue;
	thisForm.submit();
}

/* make a list of correlation values for GOTree */
function makeListCorrelation(thisForm){
	var correlation = new Array();
	for(var i = 0; i < thisForm.searchResult.length; i++){
		if (thisForm.searchResult[i].checked == true){
			var p = corrArray[thisForm.searchResult[i].value];
			correlation = correlation.concat(p.corr);
		}
	}
	thisForm.correlation.value = correlation.join(',');
}

/*add/remove selection*/

function addRmvSelection(windowName, thisForm, addORrmv){
	var newWindow = window.open("",windowName,"menubar=1,toolbar=1,location=1,resizable=1,status=1,scrollbars=1,directories=1,width=900");
	thisForm.target = windowName;
	thisForm.FormID.value = addORrmv;
	thisForm.submit();
	newWindow.focus();	
}

function batchSelection(thisForm){
  	var select = thisForm.RISet;
  	var windowName = select.options[select.selectedIndex].value;
	var newWindow = open("",windowName,"menubar=1,toolbar=1,location=1,resizable=1,status=1,scrollbars=1,directories=1,width=900");
	newWindow.focus();
	thisForm.target = windowName;
	thisForm.submit();
}

/*opener involved*/

function showTop10(formName, submitIdValue){
	var match = 0;
	for (i=0; i< window.opener.document.forms.length;i++){
		if (window.opener.document.forms[i].name == formName){
			thisForm = window.opener.document.forms[i];
			match = 1;
			break;
		}
	}
	if (match == 0)
		return;

	thisForm.target = self.name;
	if ((submitIdValue == "markerRegression")||(submitIdValue == "compositeRegression")){
		thisForm.topten.value = "topten";
	}
		
	thisForm.submitID.value = submitIdValue;
	thisForm.submit();
}


function showIndividualChromosome(formName, submitIdValue, ii){
	var match = 0;
	for (i=0; i< window.opener.document.forms.length;i++){
		if (window.opener.document.forms[i].name == formName){
			thisForm = window.opener.document.forms[i];
			match = 1;
			break;
		}
	}
	if (match == 0)
		return;
		
	windowName = 'formTarget' + (new Date().getTime());
	newWindow = open("",windowName,"menubar=1,toolbar=1,location=1,resizable=1,status=1,scrollbars=1,directories=1,width=900");
	newWindow.focus();
	thisForm.target = windowName;
	
	if (submitIdValue == "showIntMap"){
		thisForm.chromosomes.value = ii;
	}
	else{
		thisForm.chromosomes.selectedIndex = ii;
	}

	thisForm.FormID.value = submitIdValue;
	thisForm.submit();

}

/*end of opener*/

function showSample(thisForm){
	thisForm.submitID.value = "sample";
	thisForm.submit();
}

function showNext(thisForm){
	thisForm.submitID.value = "next";
	thisForm.submit();
}


function changeStatusSubmit(thisForm, status) {
	thisForm.status.value = status;
        thisForm.submit();
}

function editHTML(thisForm, execCommand){
	if (execCommand == "preview"){
		windowName = 'formTarget' + (new Date().getTime());
		newWindow = open("",windowName,"menubar=1,toolbar=1,location=1,resizable=1,status=1,scrollbars=1,directories=1,width=900");
		newWindow.focus();
		thisForm.target = windowName;
		thisForm.preview.value = "newWindow";
		thisForm.submit();
	}
	else if (execCommand == "submit"){
		//thisForm.target = window;
		thisForm.preview.value = "";
		thisForm.submit();
	}
	else{
	}
}

function dataWindow(form){
  var SaveAs = (document.execCommand) ? 1 : 0;
  newWindow = open("", "thankYouWin","width=600,menubar=1,toolbar=1,height=300,resizable=0,status=1,scrollbars=1");
  var html = "";
  for (var i=0; i < form.length; i++)
   {
        if (form.elements[i].type == "text")
        {
                if (form.elements[i].value=="")
                   html +="x ";
                else
                   html += form.elements[i].value+" ";
        }
   }
  newWindow.document.open();
  newWindow.document.write(html);
  newWindow.document.close();
  newWindow.focus();

  if (!SaveAs)
	{alert("Feature is not avaiable in current type of browser,You \nneed to manually save the content into a text format \nfile, The window will be automatically closed in 20 \nseconds!");
	setTimeout("newWindow.close()", 20000);}
  else
    {
	  if (newWindow.document.execCommand('SaveAs',false,'.txt'))
		{newWindow.close();}
	  else{
	    alert("Either you cancelled the SaveAs Dialog, or this feature \nis not avaiable in current type of browser, You \ncan manually save the content into a text format file.");
	    setTimeout("newWindow.close()", 20000);
	  }
	}
}


function xchange() {  
  var select = document.crossChoice.RISet;
  var value = select.options[select.selectedIndex].value;
  
  if (value !="BDAI") return;
  document.crossChoice.variance.checked = false;
}

/*display Info Page and Data Set buttom Added by A. Centeno*/

function datasetinfo(){
    var windowName = 'dataset_info' + (new Date().getTime());
    var select = document.SEARCHFORM.database;
    var database = select.options[select.selectedIndex].value;
	var page = '/webqtl/main.py?FormID=sharinginfo&InfoPageName=' + database;
    newWindow = open(page,windowName,"menubar=1,toolbar=1,location=1,resizable=1,status=1,scrollbars=1,directories=1,width=900");
    newWindow.focus();
}

function databaseinfo(){
    var windowName = 'database_info' + (new Date().getTime());
    var select = document.SEARCHFORM.database;
    var database = select.options[select.selectedIndex].value;
    var page = '/webqtl/main.py?FormID=sharinginfo&InfoPageName=' + database;
    newWindow = open(page,windowName,"menubar=1,toolbar=1,location=1,resizable=1,status=1,scrollbars=1,directories=1,width=900");
    newWindow.focus();
}

function crossinfo(){
    var windowName = 'cross_info';
    var select0 = document.SEARCHFORM.species;
    var select1 = document.SEARCHFORM.cross;
    var specie = select0.options[select0.selectedIndex].value;
    var database = select1.options[select1.selectedIndex].value;
    var page = '/' + specie + 'Cross.html#' + database;
    newWindow = open(page,windowName,"menubar=1,toolbar=1,location=1,resizable=1,status=1,scrollbars=1,directories=1,width=900");
    newWindow.focus();
}

function crossinfo2(){
    var windowName = 'cross_info';
    var select = document.crossChoice.RISet;
    var database = select.options[select.selectedIndex].value;
    var page = '/cross.html#' + database;
    newWindow = open(page,windowName,"menubar=1,toolbar=1,location=1,resizable=1,status=1,scrollbars=1,directories=1,width=900");
    newWindow.focus()
}


function checkWidth(){
	var width = document.getElementsByName('plotSize')[0].value
	
	if (width < 600) {
		alert("Plot size is too small - setting size to 600")
		document.getElementsByName('plotSize')[0].value = 600
	}	
}

function changeLineColor(){
	var lineColor = document.getElementsByName('lineColorSel')[0].value
	
	document.getElementsByName('lineColor')[0].value = lineColor
}

function changeLineSize(){
	var lineSize = document.getElementsByName('lineSizeSel')[0].value
	
	document.getElementsByName('lineSize')[0].value = lineSize
}

function changeIdColor(){
	var idColor = document.getElementsByName('idColorSel')[0].value
	
	document.getElementsByName('idColor')[0].value = idColor
}

function changeIdFont(){
	var idFont = document.getElementsByName('idFontSel')[0].value
	
	document.getElementsByName('idFont')[0].value = idFont
}

function changeIdSize(){
	var idSize = document.getElementsByName('idSizeSel')[0].value
	
	document.getElementsByName('idSize')[0].value = idSize
}

function changeSymbolColor(){
	var symbolColor = document.getElementsByName('colorSel')[0].value
	
	document.getElementsByName('symbolColor')[0].value = symbolColor
}

function changeSymbol(){
	var symbol = document.getElementsByName('symbolSel')[0].value
	
	document.getElementsByName('symbol')[0].value = symbol
}

function changeFilled(){
	var filled = document.getElementsByName('fillSel')[0].value
	
	document.getElementsByName('filled')[0].value = filled
}

function changeSize(){
	var symbolSize = document.getElementsByName('sizeSel')[0].value
	
	document.getElementsByName('symbolSize')[0].value = symbolSize
}


function checkAll(thisForm){ 
	var length = thisForm.searchResult.length;
	for(var i = 0; i < length; i++)
	{
		thisForm.searchResult[i].checked = true;
		highlight(thisForm.searchResult[i]);
	}
} 

function checkNone(thisForm){ 
	var length = thisForm.searchResult.length;
	for(var i = 0; i < length; i++)
	{
		thisForm.searchResult[i].checked = false;
		highlight(thisForm.searchResult[i]);
	}
} 

function checkInvert(thisForm){ 
	var length = thisForm.searchResult.length;
	for(var i = 0; i < length; i++)
	{
		thisForm.searchResult[i].checked = !(thisForm.searchResult[i].checked);
		highlight(thisForm.searchResult[i]);
	}
} 

/*Not used anymore*/
function checkTraits2(thisForm){ 
	var length = thisForm.searchResult.length;
	var category = thisForm.selectmenu.value;
	for(var i = 0; i < length; i++)
	{
		if (category == 'gt0.8')
		{
			if (correlation[i] > 0.8)
				{thisForm.searchResult[i].checked = true;}
			else
				{thisForm.searchResult[i].checked = false;}
		}
		else if (category == 'gt0.4')
		{
			if (correlation[i] > 0.4)
				{thisForm.searchResult[i].checked = true;}
			else
				{thisForm.searchResult[i].checked = false;}
		}
		else if (category == 'gt0.0')
		{
			if (correlation[i] > 0.0)
				{thisForm.searchResult[i].checked = true;}
			else
				{thisForm.searchResult[i].checked = false;}
		}
		else if (category == 'lt0.0')
		{
			if (correlation[i] < 0.0)
				{thisForm.searchResult[i].checked = true;}
			else
				{thisForm.searchResult[i].checked = false;}
		}
		else if (category == 'lt-0.4')
		{
			if (correlation[i] < -0.4)
				{thisForm.searchResult[i].checked = true;}
			else
				{thisForm.searchResult[i].checked = false;}
		}
		else if (category == 'lt-0.8')
		{
			if (correlation[i] < -0.8)
				{thisForm.searchResult[i].checked = true;}
			else
				{thisForm.searchResult[i].checked = false;}
		}
		else
			{}
	}
} 


function checkNumeric(field,limit,resetvalue,compares,fdname)
	{
		pattern = /^-?[0-9]*\.?[0-9]*$/; 
		if(pattern.test(field.value)==false)
		{
			alert("Not numeric in " + fdname);
			field.value = resetvalue;
		}
		else 
		{
			if (compares == 'gthan') {
			if(field.value > limit)
			{
				alert("Out of range in " + fdname);
				field.value = resetvalue;
			}}
			else {
			if(field.value < limit)
			{
				alert("Out of range in " + fdname);
				field.value = resetvalue;
			}}
		}
	}

function checkTraits(thisForm){ 
	var length = thisForm.searchResult.length;
	var andor = thisForm.selectandor.value;
	var gthan = parseFloat(thisForm.selectgt.value);
	var lthan = parseFloat(thisForm.selectlt.value);
	//alert(length + ' / ' + andor  + ' / ' + gthan + ' / ' + lthan);
	for(var i = 0; i < length; i++)
	{
		var p = corrArray[thisForm.searchResult[i].value];
		if (andor == 'and')
		{
			if ((p.corr > gthan) && ( p.corr < lthan))
				{thisForm.searchResult[i].checked = true;}
			else
				{thisForm.searchResult[i].checked = false;}
		}
		else if (andor == 'or')
		{
			if ((p.corr > gthan) || ( p.corr < lthan))
				{thisForm.searchResult[i].checked = true;}
			else
				{thisForm.searchResult[i].checked = false;}
		}
		else
			{}
		highlight(thisForm.searchResult[i]);
	}


}


function checkPM(thisForm){ 
	var length = thisForm.searchResult.length;
	for(var i = 0; i < length; i++)
	{
		curStr = thisForm.searchResult[i].value;
		//alert(curStr.charAt(curStr.length - 1));
		if ((curStr.charAt(curStr.length - 1) % 2) == 1)
			{thisForm.searchResult[i].checked = true;}
		else
			{thisForm.searchResult[i].checked = false;}
		highlight(thisForm.searchResult[i]);
	}
} 
function checkMM(thisForm){ 
	var length = thisForm.searchResult.length;
	for(var i = 0; i < length; i++)
	{
		curStr = thisForm.searchResult[i].value;
		if ((curStr.charAt(curStr.length - 1) % 2) == 0)
			{thisForm.searchResult[i].checked = true;}
		else
			{thisForm.searchResult[i].checked = false;}
		highlight(thisForm.searchResult[i]);
	}
} 


function directPermuAlert(thisForm){ 
	if (thisForm.directPermuCheckbox.checked){ 
		alert("Interaction permutation will take long time to compute.\n Check this box only when necessary."); 
	}
} 

function cliqueDatabase(pid){
	var windowName = 'clique';
	var newWindow = open("", windowName,"width=900,menubar=0,toolbar=1,resizable=1,status=1,scrollbars=1");
	var html = '<form name=info action=http://compbio1.uthsc.edu/clique_go/results.php method=post><center><table cellspacing=0 cellpadding=0 border=0 width=50%><tr><td><font size=+1> ProbsetId </font><input type=text name=pid value=';
	html += pid;
  	html += ' size=20 maxlength=30 ></td><tr><td><font size=+1> p-value range: between </font><input type=text name=pval_1 value=0 size=8 maxlength=20 > and <input type=text name=pval_2 value=0.01 size=8 maxlength=20></td><td><input type=submit value=Search Clique onclick=return check();></td></tr></table></center></form>';
	newWindow.document.write(html);
  	newWindow.document.close();
  	newWindow.focus();
}

function getCookie(NameOfCookie){
	if (document.cookie.length > 0){
		begin = document.cookie.indexOf(NameOfCookie+"=");
		if (begin != -1){
			begin += NameOfCookie.length+1;
			end = document.cookie.indexOf(";", begin);
			if (end == -1) end = document.cookie.length;
			return unescape(document.cookie.substring(begin, end));
			}
	}
	return null;
}

function setCookie(NameOfCookie, value, expiredays){
	var ExpireDate = new Date ();
	ExpireDate.setTime(ExpireDate.getTime() + (expiredays * 24 * 3600 * 1000));
	document.cookie = NameOfCookie + "=" + escape(value) + ((expiredays == null) ? "" : "; expires=" + ExpireDate.toGMTString()) + "; path=/";
}


function delCookie (NameOfCookie){
	if (getCookie(NameOfCookie)){
		document.cookie = NameOfCookie + "=" + "; expires=Thu, 01-Jan-70 00:00:01 GMT";
	}
}


function highlight(chkbox){
	var tr = document.getElementById(chkbox.value);
	if (tr){
		if (chkbox.checked == true)
			tr.bgColor='#FFEE99';
		else
			tr.bgColor='#eeeeee';
	}
}

/* refresh function option when domain options change */
function snpbrowser_function_refresh() {
   var idx = document.newSNPPadding.domain.selectedIndex;
   if (idx != 1) {
      document.newSNPPadding.exonfunction.options[0].selected=true;
      for (var i=1; i<document.newSNPPadding.exonfunction.length; i++) {
          document.newSNPPadding.exonfunction.options[i].selected=false;
      }
   } 
}

function snpbrowser_domain_refresh() {
   /* to refresh domain option when function option change */
   var form = document.newSNPPadding;
   var idx = form.exonfunction.selectedIndex;
   if (idx != 0) {
        form.domain.options[0].selected = false;
        form.domain.options[1].selected = true;
        for (var i=2; i<form.domain.length; i++) {
             form.domain.options[i].selected = false;
        }
   }
}

function showHideOptions() {
	var options = document.getElementById("options");
	var showOptions = document.getElementsByName("showOptions")[0];
	var optionsButton = document.getElementsByName("optionsButton")[0];
	
	if (showOptions.value == '0') {
		showOptions.value = '1';
		optionsButton.value = "Hide Options";
	}
	else {
		showOptions.value = '0';
		optionsButton.value = "Show Options";
	}
	
	options.style.display = (options.style.display != 'none' ? 'none' : '' );	
}

function editPCAName(thisForm) {
	var pcaTraits = document.getElementsByName("searchResult");
	
	var nameArray = new Array();
	
	for (j=1; j<=pcaTraits.length; j++){
		var traitName = "pcaTrait" + String(j);
		var pcaTrait = document.getElementById(traitName).childNodes[0].innerHTML;
		var editID = "editName" + String(j);
		var editName = document.getElementsByName(editID)[0].value;
		var originalName = pcaTrait.split(":")[3];
		
		if (editName.length < 1) {
			nameArray.push(originalName);
		}
		else {
			nameArray.push(editName);
		}
	}
	
	var newNames = nameArray.join(",");
	
	thisForm.newNames.value = newNames;
	thisForm.searchResult = thisForm.oldSearchResult;
	thisForm.FormID.value = "corMatrix";
	
	thisForm.submit();
}


/*
Used by GoTreePage.py,ODEPage.py ,add the parameter 'methodName'
*/
function mixedChipError(methodName){
	str ='Sorry, the analysis was interrupted because your selections from GeneNetwork apparently include data from more than one array platform (ie., Affymetrix U74A and M430 2.0). Most ' + methodName + ' analyses assume that you are using a single array type and compute statistical values on the basis of that particular array. Please reselect traits from a single platform and submit again.';
	alert(str);
	window.close();
}

/*
Used by GoTreePage.py, add the parameter 'chipName'
*/
function unknownChipError(chipName){
	alert("Sorry, the analysis was interrupted because your selections from GeneNetwork apparently include data from platform "+ chipName +" which is unknown by WebGestalt. Please reselect traits and submit again.");
	window.close();
}

/*
Used by PartialCorrInputPage.py, 
*/
function validateTrait(thisForm, inputRadioNames, type, method)
{
    var radioArray = new Array();
    radioArray = inputRadioNames.split(',');

    var value = null;
    var primaryCount = 0;
    var controlCount = 0;
    var targetCount = 0;
    var primaryString = '';
    var controlString = '';
    var targetString = '';

    for (var i = 0; i < radioArray.length; i++)
    {
        radioElement = thisForm[radioArray[i]]

        for (var j = 0; j < radioElement.length; j++)
        {
            if (radioElement[j].checked) {
                value = radioElement[j].value;
            }
        }

        if (value == "primary") {
            primaryCount += 1;
            primaryString += radioElement[0].name + ',';
        }
        else if (value == "control") {
            controlCount += 1;
            controlString += radioElement[0].name + ',';
        }
        else if (value == "target") {
            targetCount += 1;
            targetString += radioElement[0].name + ',';
        }
    }

    primaryString = primaryString.slice(0,primaryString.length-1);
    controlString = controlString.slice(0,controlString.length-1);
    targetString = targetString.slice(0,targetString.length-1);

    if (primaryCount < 1) {
        alert("You must select one primary trait!");
    }
    else if (primaryCount > 1) {
        alert("You selected multiple primary traits. Please just select one primary trait!");
    }
    else if (controlCount < 1) {
        alert("You must select at least one control trait!");
    }
    else if (controlCount > 3) {
        alert("You selected more than three control traits. Please select no more than three control trait!");
    }
    else if (targetCount < 1 && type == 0) {
        alert("You must select at least one target trait!");
    }
    else {
        thisForm.primaryTrait.value = primaryString;
        thisForm.controlTraits.value = controlString;
        thisForm.targetTraits.value = targetString;

        if (type == 0){
            if (method == 1) {
                thisForm.pcMethod.value = "pearson";
            }
            else {
                thisForm.pcMethod.value = "spearman";
            }

            databaseFunc(thisForm,'calPartialCorrTrait');
        }
        if (type == 1){
            databaseFunc(thisForm,'calPartialCorrDB');
        }

    }
    
}

/*
used by IntervalMappingPage.py
*/
function changeView(i, Chr_Mb_list){
	var oldwidth= document.changeViewForm.graphWidth.value;
	var oldselect= document.changeViewForm.chromosomes.selectedIndex;
	var oldstart= document.changeViewForm.startMb.value;
	var oldend= document.changeViewForm.startMb.value;
	windowName = 'formTarget' + (new Date().getTime());
	newWindow = open('',windowName,'menubar=1,toolbar=1,location=1,resizable=1,status=1,scrollbars=1,directories=1,width=900');
	document.changeViewForm.target = windowName;
	document.changeViewForm.chromosomes.selectedIndex = i+1;
	document.changeViewForm.startMb.value = '0.000000'; 
	document.changeViewForm.endMb.value = Chr_Mb_list[i];
	document.changeViewForm.graphWidth.value = 1280;
	document.changeViewForm.submit();
	document.changeViewForm.graphWidth.value = oldwidth;
	document.changeViewForm.chromosomes.selectedIndex = oldselect;
	document.changeViewForm.startMb.value = oldstart;
	document.changeViewForm.endMb.value = oldend;
	newWindow.focus();
}

/*
used by IntervalMappingPage.py
*/
function chrLength(a, b, c, Chr_Mb_list) {
 if (b=='physic' && a>-1) {
  c.startMb.value = '0.000000';
  c.endMb.value = Chr_Mb_list[a];
 } else {
  c.startMb.value = '';
  c.endMb.value = '';
 }
 if (a>-1) c.graphWidth.value = 1280;
 else c.graphWidth.value = 1600;
}

/*
used by networkGraphPageBody.py
*/
function changeFormat(graphName){
	var graphFormat = document.getElementById('exportFormat').value;
	var traitType = document.getElementById('traitType').value;
	
	if (graphFormat=="xgmml"){
		if (traitType=="symbol"){
			var graphname = graphName+ "_xgmml_symbol.txt";
			document.getElementById('exportGraphFile').onclick = function() { window.open(graphname) };
		}
		else if (traitType=="name"){
			var graphname = graphName+ "_xgmml_name.txt";
			document.getElementById('exportGraphFile').onclick = function() { window.open(graphname) };
		}
	}
	
	else if (graphFormat=="plain")
	{
		if (traitType=="symbol")
		{
			var graphname = graphName+ "_plain_symbol.txt";
			document.getElementById('exportGraphFile').onclick = function() { window.open(graphname) };
		}
		else if (traitType=="name")
		{
			var graphname = graphName+ "_plain_name.txt";
			document.getElementById('exportGraphFile').onclick = function() { window.open(graphname) };
		}
	}

} 


/*
used by snpBrowserPage.py
*/
function set_customStrains_cookie() {
    var options = document.newSNPPadding.chosenStrains.options;
    var size = options.length;
    strains = "";
    if (size > 0) {
       strains = strains + options[0].text+":"+options[0].value;
    }
    for (var i=1; i<size; i++) {
       strains = strains + "," + options[i].text + ":" +
                      options[i].value;
    }
    var exdate = new Date();
    exdate.setDate(exdate.getDate()+100);
    document.cookie = "customStrains1="+strains+
           ";expires="+exdate.toGMTString()
}

/*
* moved from beta2.js 
*/	
function centerIntervalMapOnRange2(chr, start, stop, form) {
	var oldindex = form.chromosomes.selectedIndex;
	var oldstart = form.startMb.value;
	var oldend = form.endMb.value;
	
	for (var i = 1; i < form.chromosomes.length; i++){
		if(form.chromosomes.options[i].text == chr){
			form.chromosomes.selectedIndex = i;
			break;
		}
	}
	form.startMb.value = start;
	form.endMb.value = stop;
	databaseFunc(form,'showIntMap');
	form.chromosomes.selectedIndex = oldindex;
	form.startMb.value = oldstart;
	form.endMb.value = oldend;
	
}

/*
* moved from index3.html 
*/	

String.prototype.trim = function(){
	return this.replace(/(^\s*)|(\s*$)/g, "");
}

function asearch(thisform){
	//
	var orkeyword = thisform.ORkeyword.value.trim();
	//
	var any_position_chr = thisform.any_position_chr.value.trim();
	var any_position_from = thisform.any_position_from.value.trim();
	var any_position_to = thisform.any_position_to.value.trim();
	if(0<any_position_chr.length && 0<any_position_from.length && 0<any_position_to.length){
		orkeyword += ' position=('+any_position_chr+' '+any_position_from+' '+any_position_to+')';
	}
	//
	var any_mean_from = thisform.any_mean_from.value.trim();
	var any_mean_to = thisform.any_mean_to.value.trim();
	if(0<any_mean_from.length && 0<any_mean_to.length){
		orkeyword += ' mean=('+any_mean_from+' '+any_mean_to+')';
	}
	//
	var any_range_from = thisform.any_range_from.value.trim();
	var any_range_to = thisform.any_range_to.value.trim();
	if(0<any_range_from.length && 0<any_range_to.length){
		orkeyword += ' range=('+any_range_from+' '+any_range_to+')';
	}
	//
	var any_wiki = thisform.any_wiki.value.trim();
	if(0<any_wiki.length){
		orkeyword += ' wiki='+any_wiki;
	}
	//
	var any_rif = thisform.any_rif.value.trim();
	if(0<any_rif.length){
		orkeyword += ' rif='+any_rif;
	}
	//
	var any_lrs_from = thisform.any_lrs_from.value.trim();
	var any_lrs_to = thisform.any_lrs_to.value.trim();
	if(0<any_lrs_from.length && 0<any_lrs_to.length){
		orkeyword += ' lrs=('+any_lrs_from+' '+any_lrs_to+')';
	}
	//
	var any_pvalue_from = thisform.any_pvalue_from.value.trim();
	var any_pvalue_to = thisform.any_pvalue_to.value.trim();
	if(0<any_pvalue_from.length && 0<any_pvalue_to.length){
		orkeyword += ' pvalue=('+any_pvalue_from+' '+any_pvalue_to+')';
	}
	//
	var any_h2_from = thisform.any_h2_from.value.trim();
	var any_h2_to = thisform.any_h2_to.value.trim();
	if(0<any_h2_from.length && 0<any_h2_to.length){
		orkeyword += ' h2=('+any_h2_from+' '+any_h2_to+')';
	}
	//
	var andkeyword = thisform.ANDkeyword.value;
	//
	var all_position_chr = thisform.all_position_chr.value.trim();
	var all_position_from = thisform.all_position_from.value.trim();
	var all_position_to = thisform.all_position_to.value.trim();
	if(0<all_position_chr.length && 0<all_position_from.length && 0<all_position_to.length){
		andkeyword += ' position=('+all_position_chr+' '+all_position_from+' '+all_position_to+')';
	}
	//
	var all_mean_from = thisform.all_mean_from.value.trim();
	var all_mean_to = thisform.all_mean_to.value.trim();
	if(0<all_mean_from.length && 0<all_mean_to.length){
		andkeyword += ' mean=('+all_mean_from+' '+all_mean_to+')';
	}
	//
	var all_range_from = thisform.all_range_from.value.trim();
	var all_range_to = thisform.all_range_to.value.trim();
	if(0<all_range_from.length && 0<all_range_to.length){
		andkeyword += ' range=('+all_range_from+' '+all_range_to+')';
	}
	//
	var all_wiki = thisform.all_wiki.value.trim();
	if(0<all_wiki.length){
		andkeyword += ' wiki='+all_wiki;
	}
	//
	var all_rif = thisform.all_rif.value.trim();
	if(0<all_rif.length){
		andkeyword += ' rif='+all_rif;
	}
	//
	var all_lrs_from = thisform.all_lrs_from.value.trim();
	var all_lrs_to = thisform.all_lrs_to.value.trim();
	if(0<all_lrs_from.length && 0<all_lrs_to.length){
		andkeyword += ' lrs=('+all_lrs_from+' '+all_lrs_to+')';
	}
	//
	var all_pvalue_from = thisform.all_pvalue_from.value.trim();
	var all_pvalue_to = thisform.all_pvalue_to.value.trim();
	if(0<all_pvalue_from.length && 0<all_pvalue_to.length){
		andkeyword += ' pvalue=('+all_pvalue_from+' '+all_pvalue_to+')';
	}
	//
	var all_h2_from = thisform.all_h2_from.value.trim();
	var all_h2_to = thisform.all_h2_to.value.trim();
	if(0<all_h2_from.length && 0<all_h2_to.length){
		andkeyword += ' h2=('+all_h2_from+' '+all_h2_to+')';
	}

	thisform.ORkeyword.value = orkeyword.trim();
	thisform.ANDkeyword.value = andkeyword.trim();

	thisform.submit();
        thisform.ORkeyword.value = "";
        thisform.ANDkeyword.value = "";
        document.getElementById('tfor').focus();
}

function searchInitial(){
        document.getElementById('tfor').value = "";
    	document.getElementById('tfor').focus();
}


/* set focus function for designated Id in html page */
function setFocus(Id)
{
        document.getElementById(Id).focus();
}
/*Tissue correlation plot*/
function showTissueCorrPlot(fmName,geneSymbol1, geneSymbol2,rank){

    var thisForm = getForm(fmName);
    if (thisForm == null || showTissueCorrPlot.arguments.length < 3)
    	return;
	
	if (rank){
		thisForm.rankOrder.value = rank;
	}else{
		thisForm.rankOrder.value = 0;
	}
    
    windowName = genNewWin();
    thisForm.target = windowName;

    thisForm.FormID.value = "showCorrelationPlot";

    thisForm.X_geneSymbol.value = geneSymbol1;
    thisForm.Y_geneSymbol.value = geneSymbol2;

    // This is to make sure the type of correlation is Tissue Correlation. Note that the string value 'none' is used to make judgement in PlotCorrelationPage.py.
    thisForm.ProbeSetID.value = 'none';
    if(typeof(thisForm.ProbeSetID2) !== 'undefined'){
    	thisForm.ProbeSetID2.value = 'none';
    }
    thisForm.submit();	
}

/* Used by MarkerRegressionPage.py */
function validatePvalue(thisForm){
	var pValue=thisForm.pValue.value;

    if (pValue ==""){
		alert("Please enter the P-Value.");
		thisForm.pValue.focus();
	}
	else if(isNaN(pValue))
	{
		alert("Please enter numeric value.");
		thisForm.pValue.focus();
	}	
	else if (pValue <0){
		alert("Please enter the valid P-Value.");
		thisForm.pValue.focus();
	}else {

		dataEditingFunc(thisForm,'markerRegression');

	}

	

}

function showTissueAbbr(fmName,shortname, fullname){
    var thisForm = getForm(fmName);
    windowName = genNewWin();
    thisForm.target = windowName;
    thisForm.FormID.value = 'tissueAbbreviation';
    thisForm.shortTissueName.value=shortname;
    thisForm.fullTissueName.value=fullname;
	
    thisForm.submit();
    thisForm.FormID.value = 'showCorrelationPlot';
    thisForm.target =''
	
}
