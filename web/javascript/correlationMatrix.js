
/*For Tissue Correlation Page; Default Export Tissue Text*/
function exportTissueText(items){
	var windowName = 'ExportTissueText';
	var newWindow = open("", windowName,"width=900,menubar=0,toolbar=1,resizable=1,status=1,scrollbars=1");
	var html = '<PRE>';
	
	for (i=0;i<items.length;i++){
		for (j=0;j<items[i].length;j++){
			if ((i>0) && (j>0)){
				html += items[i][j].slice(0,items[i][j].indexOf('/'));}
			else if (((i>0) && (j == 0)) || ((i == 0) && (j > 0))){
				html += items[i][j].slice(0, items[i][j].indexOf('/'));
				}
				
			else {
				html += "Correlation";}
			html += '\t';}
		html += '\n';}
	html += '</PRE>';
	
	html += '<BR><BR>';
	
	html += '<PRE>';
	for (i=0;i<items.length;i++){
		for (j=0;j<items[i].length;j++){
			if ((i>0) && (j>0)){
				html += items[i][j].slice(items[i][j].indexOf('/')+1, items[i][j].length);}
			else if (((i>0) && (j == 0)) || ((i == 0) && (j > 0))){
				html += items[i][j].slice(0, items[i][j].indexOf('/'));}
			else {
				html += 'P Value';}
			html += '\t';}
		html += '\n';}
	html += '</PRE>';
	
  	newWindow.document.write(html);
  	newWindow.document.close();
  	newWindow.focus();/**/
}

/*Export Tissue Text for long label*/
function exportTissueVerboseText(items){
	var windowName = 'ExportVerboseText';
	var newWindow = open("", windowName,"width=900,menubar=0,toolbar=1,resizable=1,status=1,scrollbars=1");
	var html = '<PRE>';
	
	for (i=0;i<items.length;i++){
		for (j=0;j<items[i].length;j++){
			if ((i>0) && (j>0)){
				html += items[i][j].slice(0,items[i][j].indexOf('/'));}
			else if ((i>0) && (j == 0)){
				position1 = items[i][j].indexOf('/') + 1;
				position2 = items[i][j].indexOf('/', position1);
				html += items[i][j].slice(position2 + 1, items[i][j].length);}
			else if ((i == 0) && (j>0)){
				html += items[i][j].slice(0, items[i][j].indexOf('/')) ;}
			else {
				html += "Correlation";}
			html += '\t';}
		html += '\n';}
	html += '</PRE>';
	
	html += '<BR><BR>';
	
	html += '<PRE>';
	for (i=0;i<items.length;i++){
		for (j=0;j<items[i].length;j++){
			if ((i>0) && (j>0)){
				html += items[i][j].slice(items[i][j].indexOf('/')+1, items[i][j].length);}
			else if ((i>0) && (j == 0)){
				position1 = items[i][j].indexOf('/') + 1;
				position2 = items[i][j].indexOf('/', position1) + 1;
				html += items[i][j].slice(position2, items[i][j].length);}
			else if ((i == 0) && (j>0)){
				html += items[i][j].slice(0, items[i][j].indexOf('/'));}
			else {
				html += 'P Value';}
			html += '\t';}
		html += '\n';}
	html += '</PRE>';
	
  	newWindow.document.write(html);
  	newWindow.document.close();
  	newWindow.focus();/**/
}

/*For Tissue Correlation Page; Default Save function for results of symbol count =1*/
function exportAllTissueText(items){
	var windowName = 'ExportTissueText';
	var newWindow = open("", windowName,"width=900,menubar=0,toolbar=1,resizable=1,status=1,scrollbars=1");
	var html = '<PRE>';
	
	for (i=0;i<items.length;i++){
		for (j=0;j<items[i].length;j++){
			if ((i>0) && (j>0)){
				html += items[i][j].slice(0,items[i][j].indexOf('/'));}
			else if (((i>0) && (j == 0)) || ((i == 0) && (j > 0))){
				html += items[i][j].slice(0, items[i][j].indexOf('/'));
				}
				
			else {
				html += "Correlation";}
			html += '\t';}
		html += '\n';}
	html += '</PRE>';
	
  	newWindow.document.write(html);
  	newWindow.document.close();
  	newWindow.focus();/**/
}

/* Display Short Label for Tissue */
function displayTissueShortName(){
	var geneSymbols = document.getElementsByName("Symbol");
	
	var exportButton = document.getElementsByName("export")[0];
	var shortNameCheck = document.getElementById("shortName_1"); // to check if currently short
	
	if (shortNameCheck.style.display == 'none'){
		exportButton.value="Export";
		exportButton.onclick = function(){exportTissueText(allCorrelations);};
	}
	else {
		exportButton.value="Export";
		exportButton.onclick = function(){exportTissueText(allCorrelations);};
	}
	
	for (i=0; i < geneSymbols.length; i++){
		var shortName = document.getElementById("shortName_" + String(i));
		var verboseName = document.getElementById("verboseName_" + String(i));
		var verboseName2 = document.getElementById("verboseName2_" + String(i));
		var verboseName3 = document.getElementById("verboseName3_" + String(i));
		
		
		if (shortName.style.display == 'block') {
			shortName.style.display = 'none';
		}		
	
		else if (shortName.style.display == 'none') {
			if (verboseName.style.display == 'block'){
				verboseName.style.display = 'none';
				verboseName2.style.display = 'none';
				verboseName3.style.display = 'none';
			}	
			shortName.style.display = 'block';
		}
	}
}

/* Display Long Label for Tissue */
function displayTissueVerboseName(){
	var geneSymbols = document.getElementsByName("Symbol");
	
	var exportButton = document.getElementsByName("export")[0];
	var verboseNameCheck = document.getElementById("verboseName_0"); // to check if currently verbose
	
	if (verboseNameCheck.style.display == 'none'){
		exportButton.value="Export";
		exportButton.onclick = function(){exportTissueVerboseText(allCorrelations);};
	}
	else {
		exportButton.value="Export";
		exportButton.onclick = function(){exportTissueText(allCorrelations);};
	}
	
	for (i=0; i < geneSymbols.length; i++){
		var verboseName = document.getElementById("verboseName_" + String(i));
		var verboseName2 = document.getElementById("verboseName2_" + String(i));
		var verboseName3 = document.getElementById("verboseName3_" + String(i));
		var shortName = document.getElementById("shortName_" + String(i));
		
		
		if (verboseName.style.display == 'block') {
			verboseName.style.display = 'none';
			verboseName2.style.display = 'none';
			verboseName3.style.display = 'none';
		}
		
		else if (verboseName.style.display == 'none'){
			if (shortName.style.display == 'block'){
				shortName.style.display = 'none';
			}
			verboseName.style.display = 'block';
			verboseName2.style.display = 'block';
			verboseName3.style.display = 'block';
		}	
	}
	
}

/* Info page for dataset of tissue correlation */
function tissueDatasetInfo(thisForm,dataSetNames){
    var windowName = 'dataset_info';
    var Index = thisForm.selectedIndex;
	var datasetName =dataSetNames[Index]
    var page = '/dbdoc/' + datasetName + '.html';
    newWindow = open(page,windowName,"menubar=1,toolbar=1,location=1,resizable=1,status=1,scrollbars=1,directories=1,width=900");
    newWindow.focus()
}


/*for correlation matrix page*/
/* Display Short Label in Correlation Matrix */
function displayShortName(){
	var traitList = document.getElementsByName("traitList")[0].value.split("\t");
	var exportButton = document.getElementsByName("export")[0];
	var shortNameCheck = document.getElementById("shortName_1"); // to check if currently short
	
	if (shortNameCheck.style.display == 'none'){
		exportButton.value="Export";
		exportButton.onclick = function(){exportAbbreviationText(allCorrelations);};
	}
	else {
		exportButton.value="Export";
		exportButton.onclick = function(){exportText(allCorrelations);};
	}
	
	for (i=0; i < traitList.length; i++){
		var shortName = document.getElementById("shortName_" + String(i));
		var verboseName = document.getElementById("verboseName_" + String(i));
		var verboseName2 = document.getElementById("verboseName2_" + String(i));
		var verboseName3 = document.getElementById("verboseName3_" + String(i));
		
		
		if (shortName.style.display == 'block') {
			shortName.style.display = 'none';
		}		
	
		else if (shortName.style.display == 'none') {
			if (verboseName.style.display == 'block'){
				verboseName.style.display = 'none';
				verboseName2.style.display = 'none';
				verboseName3.style.display = 'none';
			}	
			shortName.style.display = 'block';
		}
	}
}

/* Display Long Label in Correlation Matrix*/
function displayVerboseName(){
	var traitList = document.getElementsByName("traitList")[0].value.split("\t");
	var exportButton = document.getElementsByName("export")[0];
	var verboseNameCheck = document.getElementById("verboseName_0"); // to check if currently verbose
	
	if (verboseNameCheck.style.display == 'none'){
		exportButton.value="Export";
		exportButton.onclick = function(){exportVerboseText(allCorrelations);};
	}
	else {
		exportButton.value="Export";
		exportButton.onclick = function(){exportText(allCorrelations);};
	}
	
	for (i=0; i < traitList.length; i++){
		var verboseName = document.getElementById("verboseName_" + String(i));
		var verboseName2 = document.getElementById("verboseName2_" + String(i));
		var verboseName3 = document.getElementById("verboseName3_" + String(i));
		var shortName = document.getElementById("shortName_" + String(i));
		
		if (verboseName.style.display == 'block') {
			verboseName.style.display = 'none';
			verboseName2.style.display = 'none';
			verboseName3.style.display = 'none';
		}
		
		else if (verboseName.style.display == 'none'){
			if (shortName.style.display == 'block'){
				shortName.style.display = 'none';
			}
			verboseName.style.display = 'block';
			verboseName2.style.display = 'block';
			verboseName3.style.display = 'block';
		}	
	}
	
}

/*Export for long label in Correlation Matrix*/
function exportVerboseText(items){
	var windowName = 'ExportVerboseText';
	var newWindow = open("", windowName,"width=900,menubar=0,toolbar=1,resizable=1,status=1,scrollbars=1");
	var html = '<PRE>';
	
	for (i=0;i<items.length;i++){
		for (j=0;j<items[i].length;j++){
			if ((i>0) && (j>0)){
				html += items[i][j].slice(0,items[i][j].indexOf('/'));}
			else if ((i>0) && (j == 0)){
				position1 = items[i][j].indexOf('/') + 1;
				position2 = items[i][j].indexOf('/', position1);
				html += "Trait " + String(i) + ": " + items[i][j].slice(position2 + 1, items[i][j].length);}
			else if ((i == 0) && (j>0)){
				html += items[i][j];}
			else {
				html += "Correlation";}
			html += '\t';}
		html += '\n';}
	html += '</PRE>';
	
	html += '<BR><BR>';
	
	html += '<PRE>';
	for (i=0;i<items.length;i++){
		for (j=0;j<items[i].length;j++){
			if ((i>0) && (j>0)){
				html += items[i][j].slice(items[i][j].indexOf('/')+1, items[i][j].length);}
			else if ((i>0) && (j == 0)){
				position1 = items[i][j].indexOf('/') + 1;
				position2 = items[i][j].indexOf('/', position1) + 1;
				html += "Trait " + String(i) + ": " + items[i][j].slice(position2, items[i][j].length);}
			else if ((i == 0) && (j>0)){
				html += items[i][j];}
			else {
				html += 'N';}
			html += '\t';}
		html += '\n';}
	html += '</PRE>';
	
  	newWindow.document.write(html);
  	newWindow.document.close();
  	newWindow.focus();/**/
}

/*Default Export for labels in Correlation Matrix*/
function exportText(items){
	var windowName = 'ExportText';
	var newWindow = open("", windowName,"width=900,menubar=0,toolbar=1,resizable=1,status=1,scrollbars=1");
	var html = '<PRE>';
	for (i=0;i<items.length;i++){
		for (j=0;j<items[i].length;j++){
			//alert(" i="+i+"---j="+j+"----item[i][j]=="+items[i][j]);
			if ((i>0) && (j>0)){
				html += items[i][j].slice(0,items[i][j].indexOf('/'));}
			else if (((i>0) && (j == 0)) || ((i == 0) && (j > 0))){
				html += items[i][j].slice(0, items[i][j].indexOf('/'));}
			else {
				html += "Correlation";}
			html += '\t';}
		html += '\n';}
	html += '</PRE>';
	
	html += '<BR><BR>';
	
	html += '<PRE>';
	for (i=0;i<items.length;i++){
		for (j=0;j<items[i].length;j++){
			if ((i>0) && (j>0)){
				html += items[i][j].slice(items[i][j].indexOf('/')+1, items[i][j].length);}
			else if (((i>0) && (j == 0)) || ((i == 0) && (j > 0))){
				html += items[i][j].slice(0, items[i][j].indexOf('/'));}
			else {
				html += 'N';}
			html += '\t';}
		html += '\n';}
	html += '</PRE>';
	
  	newWindow.document.write(html);
  	newWindow.document.close();
  	newWindow.focus();/**/
}

/*Export for short label in Correlation Matrix*/
function exportAbbreviationText(items){
	var windowName = 'ExportAbbreviationText';
	var newWindow = open("", windowName,"width=900,menubar=0,toolbar=1,resizable=1,status=1,scrollbars=1");
	var html = '<PRE>';
	
	for (i=0;i<items.length;i++){
		for (j=0;j<items[i].length;j++){
			if ((i>0) && (j>0)){
				html += items[i][j].slice(0,items[i][j].indexOf('/'));}
			else if ((i>0) && (j == 0)){
				position1 = items[i][j].indexOf('/') + 1;
				position2 = items[i][j].indexOf('/', position1);
				html += "Trait " + String(i) + ": " + items[i][j].slice(position1, position2);}
			else if ((i == 0) && (j>0)){
				html += items[i][j];}
			else {
				html += "Correlation";}
			html += '\t';}
		html += '\n';}
	html += '</PRE>';
	
	html += '<BR><BR>';
	
	html += '<PRE>';
	for (i=0;i<items.length;i++){
		for (j=0;j<items[i].length;j++){
			if ((i>0) && (j>0)){
				html += items[i][j].slice(items[i][j].indexOf('/')+1, items[i][j].length);}
			else if ((i>0) && (j == 0)){
				position1 = items[i][j].indexOf('/') + 1;
				position2 = items[i][j].indexOf('/', position1);
				html += "Trait " + String(i) + ": " + items[i][j].slice(position1, position2);}
			else if ((i == 0) && (j>0)){
				html += items[i][j];}
			else {
				html += 'N';}
			html += '\t';}
		html += '\n';}
	html += '</PRE>';
	
  	newWindow.document.write(html);
  	newWindow.document.close();
  	newWindow.focus();/**/
}

/*dynamic change formID for process bar display issue. Only Single symbol result page needs process bar*/
function selectFormIdForTissueCorr(fmName){

	var thisForm = getForm(fmName);
	var geneSymbolStr =thisForm.geneSymbols.value;	
	var geneSymbolStrSplit =geneSymbolStr.split(/\n/);//delimiter is very important here

	len=geneSymbolStrSplit.length;
	if (len==1){
		thisForm.FormID.value="dispTissueCorrelationResult";
	}
	else{
		thisForm.FormID.value="dispMultiSymbolsResult";
	}
	thisForm.submit()
}

/*make default for dropdown menu in tissue correlation page*/
function makeTissueCorrDefault(thisform){
	setCookie('cookieTest', 'cookieTest', 1);
	var cookieTest = getCookie('cookieTest');
	delCookie('cookieTest');
	if (cookieTest){
		var defaultTissueDataset = thisform.tissueProbeSetFeezeId.value;
		setCookie('defaultTissueDataset', defaultTissueDataset, 10);
		alert("The current dataset is set to default.");
	}
	else{
		alert("You need to enable Cookies in your browser.");
	}

}

/*set default selected value for tissue correlation dataset Id*/
function getTissueCorrDefault(fmName){
	var thisForm = getForm(fmName);
	if (getCookie('defaultTissueDataset')){
		thisForm.tissueProbeSetFeezeId.selectedIndex =(getCookie('defaultTissueDataset'))-1;
	}
	else{
		thisForm.tissueProbeSetFeezeId.selectedIndex =0;
	}

}
