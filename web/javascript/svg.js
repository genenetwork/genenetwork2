/*extracted and modified from http://www.carto.net/neumann/cartography/vienna/ */
var openURL="/webqtl/WebQTL.py?FormID=showDatabase&database=Eye_M2_0906_R&incparentsf1=1&ProbeSetID=";
var chrLength=[0.0, 491.91598118601547, 946.15708685124116, 1345.2216933525635, 1732.198920660242, 2111.6212086643609, 2484.8595921440615, 2847.1359103053924, 3176.8399906396698, 3486.3641319132003, 3810.7615243606533, 4114.7890532612491, 4415.4830426184499, 4716.5544971256113, 5026.024224847908, 5284.3571135528055, 5529.6098871486292, 5767.1869053349601, 5993.6795668729492, 6146.7463916706538];

var statusObj;
var zoomVal;
var svgdoc;
var zoomValueObj;
var dispBoxObj;
var probesetObj;
var markerObj;
var xObj;
var yObj;
var svgRect;
var svgMainViewport;
var overviewViewport;

var allWidth = 8200;
var allHeight = 8200;
var xOriginCorner = 0;
var yOriginCorner = 0;

var evtX;
var evtY;
var dataPanelEvtX;
var dataPanelEvtX;
var rectUlXCorner;
var rectUlYCorner
var pluginPixWidth;
var pluginPixHeight;
var mainPixWidth;
var mainPixHeight;
var mainX;
var mainY;
var scaleFactor = 1;
var width;
var height;
var pressed = 0;

var msgObj;

function initMap(evt) {
	//initializing values
	zoomVal = 100; //initial zoomFactor
	//svgdoc=evt.getTarget().getOwnerDocument();
	svgdoc = evt.target.ownerDocument;
   	statusObj = svgdoc.getElementById("statusText");
	statusObj = statusObj.firstChild;

	zoomValueObj = svgdoc.getElementById("zoomValueObj");
	zoomValueObj = zoomValueObj.firstChild;

	xObj = svgdoc.getElementById("XLabel");
	xObj = xObj.firstChild;
	yObj = svgdoc.getElementById("YLabel");
	yObj = yObj.firstChild;

	dispBoxObj = svgdoc.getElementById("dispBox");
	probesetObj = svgdoc.getElementById("_probeset");
	probesetObj = probesetObj.firstChild;
	markerObj = svgdoc.getElementById("_marker");
	markerObj = markerObj.firstChild;

	//dispBoxObj.parent.appendChild(dispBoxObj);
	svgRect = svgdoc.getElementById("overviewRect");
	allWidth = svgRect.getAttribute("width");
	allHeight = svgRect.getAttribute("height");
	svgMainViewport = svgdoc.getElementById("mainPlot");	
	mainPixWidth = svgMainViewport.getAttribute("width");
	mainPixHeight = svgMainViewport.getAttribute("height");
	mainX = svgMainViewport.getAttribute("x");
	mainY = svgMainViewport.getAttribute("y");
	//overviewObjects
	overviewViewport = svgdoc.getElementById("overviewPlot");		
	pluginPixWidth = overviewViewport.getAttribute("width");
	pluginPixHeight = overviewViewport.getAttribute("height");
	
	//msgObj = svgdoc.getElementById("msgText")
	//msgObj = msgObj.firstChild;
}

//simulating statusbar
function statusChange(text) {
	//statusObj.setData(text);
	statusObj.nodeValue=text;
}

//magnifier glass mouse-over effects
function magnify(evt,scaleFact,inOrOut) {
	if (inOrOut == "in") {
		if (zoomVal < 1000) {
			statusChange("click to zoom in");
			scaleObject(evt,scaleFact);
		}
		else {
			statusChange("maximum zoom factor reached! cannot zoom in any more!");			
		}
	}
	if (inOrOut == "out") {
		if (zoomVal >= 100) {
			statusChange("click to zoom out");
			scaleObject(evt,scaleFact);
		}
		else {
			statusChange("minimum zoom factor reached! cannot zoom out any more!");			
		}		
	}
	if (scaleFact == 1) {
			statusChange("plot ready");		
			scaleObject(evt,scaleFact);
	}	
}

// Lei Yan
// 2009/03/26

//scale any object that has a transform-value
function scaleObject(evt,factor) {
        //reference to the currently selected object
        var element = evt.target;

        //query old transform value (we need the translation value)
        var curTransform = element.getAttribute("transform");
        curTransform = new String(curTransform); //Wert in ein String umwandeln
        //no fear from Regular expressions ... just copy it, I copied it either ...
        var translateRegExp=/translate\(([-+]?\d+)(\s*[\s,]\s*)([-+]?\d+)\)\s*/;

        //This part extracts the translation-value from the whole transform-string
        if (curTransform.length != 0)
        {
          var result = curTransform.match(translateRegExp);
          if (result == null || result.index == -1)
          {
             oldTranslateX = 0;
             oldTranslateY = 0;
          }
          else
          {
             oldTranslateX = result[1];
             oldTranslateY = result[3];
          }
          //concatenate the string again, add scale-factor
          var newtransform = "translate(" + oldTranslateX + " " + oldTranslateY + ") " + "scale(" + factor + ")";
        }
        //set transform-factor
        element.setAttribute('transform', newtransform);
}

function zoomIt(inOrOut) {
	if (zoomVal>=300) step=100.0;
	else step=50.0;
	if (inOrOut == "in") {
		if (zoomVal < 1000) {
			statusChange("click to zoom in");
			zoomVal = zoomVal + step;
			zoomItReally();
		}
		else {
			statusChange("maximum zoom factor reached! cannot zoom in any more!");
		}
	}
	if (inOrOut == "out") {
		if (zoomVal > 100) {
			statusChange("click to zoom out");
			zoomVal = zoomVal - step;
			zoomItReally();
		}
		else {
			statusChange("minimum zoom factor reached! cannot zoom out any more!");			
		}		
	}
}

function zoomItReally() {
	statusChange("panning plot - please be patient ...");
	
	//get values from draggable rectangle
	xulcorner = parseFloat(svgRect.getAttribute("x"));
	yulcorner = parseFloat(svgRect.getAttribute("y"));
	width = parseFloat(svgRect.getAttribute("width"));
	height = parseFloat(svgRect.getAttribute("height"));
	
	//calcs
	xcenter = xulcorner + width / 2;
	ycenter = yulcorner + height / 2;
	xnulcorner = xcenter - allWidth / 2 * (100/zoomVal);
	ynulcorner = ycenter - allHeight / 2 * (100/zoomVal);
	nWidth = allWidth * (100/zoomVal);
	nHeight = allHeight * (100/zoomVal);

	if (zoomVal == 100) {
		xnulcorner = 0;
		ynulcorner = 0;
	}		
	//set values of draggable rectangle
	svgRect.setAttribute("x",xnulcorner);
	svgRect.setAttribute("y",ynulcorner);
	svgRect.setAttribute("width",nWidth);
	svgRect.setAttribute("height",nHeight);
	
	//set viewport of main map
	newViewport = xnulcorner + " " + ynulcorner + " " + nWidth + " " + nHeight;
	svgMainViewport.setAttribute("viewBox",newViewport);/**/
	//zoomValueObj.setData("ZOOM: " + zoomVal+"%");
	zoomValueObj.nodeValue="ZOOM: " + zoomVal+"%";
	statusChange("plot ready ...");
}

function beginPan(evt) {
	pressed = 1;
	width = parseFloat(svgRect.getAttribute("width"));
	height = parseFloat(svgRect.getAttribute("height"));
	evtX = parseFloat(evt.clientX) * scaleFactor;
	evtY = parseFloat(evt.clientY) * scaleFactor;
	rectUlXCorner = parseFloat(svgRect.getAttribute("x"));
	rectUlYCorner = parseFloat(svgRect.getAttribute("y"));	
}

function doPan(evt) {
	if (pressed == 1) {
		newEvtX = parseFloat(evt.clientX) * scaleFactor; //scaleFactor is because of resizable interface
		newEvtY = parseFloat(evt.clientY) * scaleFactor;
		toMoveX = rectUlXCorner + (newEvtX - evtX) * allWidth / pluginPixWidth;
		toMoveY = rectUlYCorner + (newEvtY - evtY) * allHeight / pluginPixHeight;
		
		//restrict to borders of overviewmap
		if (toMoveX < xOriginCorner) {
			svgRect.setAttribute("x",xOriginCorner);
		}
		else if ((toMoveX + width) > (xOriginCorner + allWidth)) {
			svgRect.setAttribute("x",xOriginCorner + allWidth - width);				
		}
		else {
			svgRect.setAttribute("x",toMoveX);			
		}
		if (toMoveY < yOriginCorner) {
			svgRect.setAttribute("y",yOriginCorner);
		}
		else if ((toMoveY + height) > (yOriginCorner + allHeight)) {
			svgRect.setAttribute("y",yOriginCorner + allHeight - height);
		}				
		else {
			svgRect.setAttribute("y",toMoveY);
		}
		
		evtX = newEvtX;
		evtY = newEvtY;
		rectUlXCorner = parseFloat(svgRect.getAttribute("x"));
		rectUlYCorner = parseFloat(svgRect.getAttribute("y"));	
	}	
}

function endPan() {
	statusChange("panning plot - please be patient ...");
	pressed = 0;
	//set viewport of main plot
	xulcorner = parseFloat(svgRect.getAttribute("x"));
	yulcorner = parseFloat(svgRect.getAttribute("y"));
	width = parseFloat(svgRect.getAttribute("width"));
	height = parseFloat(svgRect.getAttribute("height"));
	newViewport = xulcorner + " " + yulcorner + " " + width + " " + height;
	svgMainViewport.setAttribute("viewBox",newViewport);
	statusChange("plot ready ...");
}

function showChr(evt) {
	xulcorner = parseFloat(svgRect.getAttribute("x"));
	yulcorner = parseFloat(svgRect.getAttribute("y"));
	width = parseFloat(svgRect.getAttribute("width"));
	height = parseFloat(svgRect.getAttribute("height"));
	myX = parseFloat(evt.clientX-mainX) * scaleFactor;
	myY = parseFloat(evt.clientY-mainY) * scaleFactor;
	myX = xulcorner + (myX*100/zoomVal -0.1*mainPixWidth)* allWidth/ mainPixWidth;
	myY = allHeight*0.8-(yulcorner + (myY*100/zoomVal -0.1*mainPixWidth)* allHeight/ mainPixHeight);

	for (i=0; i<chrLength.length; i++){
		if (chrLength[i] > myX) break;
	}
	i = (i==chrLength.length)? "X":i;
	//xObj.setData("Marker GMb (Chr "+ i+")");
	xObj.nodeValue="Marker GMb (Chr "+ i+")";

	for (i=0; i<chrLength.length; i++){
		if (chrLength[i] > myY) break;
	}
	i = (i==chrLength.length)? "X":i;
	//yObj.setData("Transcript GMb (Chr "+ i+")");
	yObj.nodeValue="Transcript GMb (Chr "+ i+")";
}

function showNoChr(evt) {
	//xObj.setData("Marker GMb");
	xObj.nodeValue="Marker GMb.";
	//yObj.setData("Transcript GMb");
	yObj.nodeValue="Transcript GMb.";
}

function mvMsgBox(evt) {
	var element = evt.target;
	var myX = parseFloat(evt.clientX)+2;
	var myY = parseFloat(evt.clientY)-2;
	var newtransform = "translate(" + myX + " " + myY + ") " + "scale(0.8)";
	dispBoxObj.setAttribute('transform', newtransform);
	dispBoxObj.setAttribute('visibility', 'visible');
	//probesetObj.setData("ProbeSet : " + element.getAttribute("ps"));
	probesetObj.nodeValue="ProbeSet : " + element.getAttribute("ps");
	//markerObj.setData("Marker : " + element.getAttribute("mk"));
	markerObj.nodeValue="Marker : " + element.getAttribute("mk");
}

function hdMsgBox() {
	dispBoxObj.setAttribute('visibility', 'hidden');
}

function openPage(evt) {
	var element = evt.target;
	var windowName = 'formTarget' + (new Date().getTime());
	//var openWinString = "openNewWin('"+openURL+element.getAttribute("ps")+"')";
	//var aURL = "http://www.genenetwork.org"+openURL+element.getAttribute("ps");
	var aURL = openURL+element.getAttribute("ps");
	var newWin = window.open(aURL);
	newWin.focus();
	return false;
	
	//browserEval(openWinString);
}
