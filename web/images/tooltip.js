 /**********************************************************
 *             Popup Window Definition Part                *
 *                                                         *
 * To add a popup window, add a string definition below.   *
 * To include the item in the printing friendly page,      *
 * modify the longStr by adding the item to it.            *
 * Don't change anything else.                             *
 **********************************************************/

var htmlOpener = "<html><head><title>Tooltip and Popup Window Demo</title>"+
		 "</head><body bgcolor='navyblue'><p>"
var htmlCloser = "</body></html>"

 demo1 = "<center><b>Title Here.</b></center><p>It is fun. Don't forget to put a line break here.<p>"

 demo2 = "No title in this window. Just plain text.<p>"
 
 demo3 = "How much is a picture worth? <p><center><img src='corr.gif'>"+
         "</center><p>"

/****END OF STRING DEFINITION*****/

 var popupWin
 var wholeWin
  function popup(term)  // write corresponding content to the popup window
  {
    popupWin = window.open("", "puWin",  "width=480,height=200,scrollbars,dependent,resizable");
   popupWin.document.open("text/html", "replace"); 
   popupWin.document.write(htmlOpener);
   popupWin.document.write(term);
   popupWin.document.write(htmlCloser);
   popupWin.document.close();  // close layout stream
   popupWin.focus();  // bring the popup window to the front
  }
 
  function closeDep() {
  if (popupWin && popupWin.open && !popupWin.closed) popupWin.close();
  if (wholeWin && wholeWin.open && !wholeWin.closed) wholeWin.close();

  }

   
/***********************END OF FUNCTION POPUP******************************/

  function printwhole()
  {
	longStr ="<center><h2>Annotated Output for Proc Univariate</h2></center>";
	longStr += demo1 + demo2 + demo3;
	
	wholeWin = window.open("","wWin", "width=800,height=500,dependent=yes,scrollbars=yes,resizable=yes,toolbar=yes,menubar=yes");
	wholeWin.document.open("text/html","replace");
	wholeWin.document.write(htmlOpener);
	wholeWin.document.write(longStr);
	wholeWin.document.write(htmlCloser);
	wholeWin.document.close();
	wholeWin.focus();}

/*******End of popup window stuff*********/


/***************************Tooltip Part Begins***************************/
  var style = ((NS4 && document.test) || IE4) ? 1 : 0;
  var timerID = null;
  var padding = 3; // < 4 recommended
  var bgcolor = "beige";
  var borWid = 1; // for no border, assign null
  var borCol = "#0000cc";
  var borSty = "solid";
  var str = "<STYLE TYPE='text/css'>";

  str += ".tooltip {";
  str += "position: absolute;";
  str += "visibility: hidden;";
  str += "left: 0; top: 0;";

  if (borWid > 0) { // if a border is specified

  str += "border-width: " + borWid + ";";
  str += "border-color: " + borCol + ";";
  str += "border-style: " + borSty + ";";

}

  if (NS4) {

  if (borWid > 0 && padding <= 3) {
    str += "padding: 0;";
    str += "layer-background-color: " + bgcolor + ";"; } 
    
    else if (borWid > 0 && padding > 3) {
    str += "padding: " + (padding - 3) + ";";
    str += "background-color: " + bgcolor + ";";

  } else if (borWid == 0) {
    str += "padding: " + padding + ";";
    str += "layer-background-color: " + bgcolor + ";";

  }

} else {
  str += "padding: " + padding + ";";
  str += "background-color: " + bgcolor + ";";
}

  str += "}";
  str += "</STYLE>";


  if (style) {
  document.write(str);
  if (NS4) window.onload = init;
}

/**************************************************
*        Making your tooltip text here            *
* This is the only place that need to be modified.*
* The first argument is the name of the tooltip.  *
* The second argument is the width and last one   *
* is the content of the tooltip.                  *
**************************************************/


makeEl("map", 200, "<font size=3>This will do an interval regression using your data against the chromosome you just selected </font>");
makeEl("chrs", 200, "<font size=3>This will allow you to choose the chromosome you want to do the interval mapping</font>");
makeEl("normal", 200, "<font size=3>This will generate a graph to assess if your data is normally distributed</font>");
makeEl("link", 200, "<font size=3>This will do a Marker Regression using your data.</font>");
makeEl("save", 200, "<font size=3>This will save the data you just input into a text file</font>");


/*************************End of making tooltip text*************************/

function init() {
  setTimeout("window.onresize = redo", 1000);
}

function redo() {
  window.location.reload();
}

function makeEl(id, width, code) {
  if (!style) return;

  var str = "<STYLE TYPE='text/css'>";
  str += "#" + id + " {";
  str += "width: " + width + ";";
  str += "}";
  str += "</STYLE>";
  str += "<DIV CLASS='tooltip' ID='" + id + "'><center>" + code + "</center></DIV>";
   
  document.write(str);
}

function displayEl(left, top) {

  if (NS4) document.releaseEvents(Event.MOUSEMOVE);
  document.onmousemove = null;
  var whichEl = (NS4) ? document[active] : document.all[active].style;
  whichEl.left = left;
  whichEl.top = top;
  whichEl.visibility = (NS4) ? "show" : "visible";
}

function clearEl() {

  if (!style) return;
  var whichEl = (NS4) ? document[active] : document.all[active].style;
  whichEl.visibility = (NS4) ? "hide" : "hidden";
  active = null;

  if (timerID) clearTimeout(timerID);
  if (NS4) document.releaseEvents(Event.MOUSEMOVE);
  document.onmousemove = null;

}

function activateEl(id, e) {
  if (!style) return;
  active = id;

  if (NS4) document.captureEvents(Event.MOUSEMOVE);
  document.onmousemove = checkEl;
  checkEl(e);

  }

function checkEl(e) {
  if (timerID) clearTimeout(timerID);
  var left = (NS4) ? e.pageX : event.clientX + document.body.scrollLeft;
  var top = (NS4) ? e.pageY + 20 : event.clientY + document.body.scrollTop + 20;
  timerID = setTimeout("displayEl(" + left + ", " + top + ")", 300);
}

