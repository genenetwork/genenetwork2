/**
 * These are REALLY simple serialisation tools meant for simple Hash-like
objects in the for key=val
 */
var PrefUtils = {
  deserialize:function(inStr){
    return eval('('+inStr+')');
  },
  serialize:function(inObj){
    var buf = '{';
    var cma = '';
    var quote = "'";
    for (i in inObj){
      if (typeof i == 'string'){
        buf += cma + quote + i + quote + " : " 
          + quote +inObj[i]+ quote;
          cma = ',';
      }
    }
    buf += '}';
    return buf;
  },
  testCookie:function(){
    setCookie('cookieTest', 'cookieTest', 1);
    var cookieTest = getCookie('cookieTest');
    delCookie('cookieTest');
    if (cookieTest) return true;
    else return false;
  },
  form2Cookie:function(thisForm, cookieName){
    if (!this.testCookie()){
      alert("You need to enable Cookie in your browser!");
    }
    else{
      var pref = getCookie(cookieName);
      var options = this.deserialize(pref);
      if(!options){
  	  options = new Array();
      }/**/
      for( var x = 0; thisForm.elements[x]; x++ ) {
  	  if( thisForm.elements[x].type ) {
  	    var oE = thisForm.elements[x]; 
  	    var oT = oE.type.toLowerCase();
  	    if( oT == 'text' || oT == 'textarea' || oT == 'select-one' ) {
  	      options[oE.name] = oE.value;
  	    }
        }
      }
      setCookie(cookieName, this.serialize(options), 10);
      alert("Your preference has been saved.");
    }	
  }
};

function updateInner(Id, str){
  document.getElementById(Id).innerHTML = str;
}


function popWindow(myId){
	if (!document.getElementById || !myId) return false;
	else{
		var div = document.getElementById(myId);
		if (!div){
			div = document.createElement("div");
			div.id = myId;
			div.style.position = "absolute";
			div.style.top = "50%";
			div.style.left = "50%";
			div.style.width = "400px";
			div.style.height = "250px";
			div.style.margin = "-125px 0 0 -200px";
			div.style.border = "4px double #3366cc";
			div.style.padding = "0px";
			div.style.opacity = "0.99";
			div.style.backgroundColor = "#FFFFFF";
			div.style.fontSize = "60px";
			div.style.lineHeight = "60px";
			div.style.textAlign = "right";
			document.body.appendChild(div);
		}
		else{
			//alert("Layer already exists;")
		}
		xmlhttpPost('/webqtl/AJAX_pref.py', 'tab=assembly&divId='+myId, myId);
		div.style.visibility = 'visible';
	}
}

/*New added by NL*/
/*
Used by PartialCorrTraitPage.py, CorrelationPage.py, 
*/
function xmlhttpPost(strURL, div, querystring) {
	
    var xmlHttpReq = false;
    var self = this;
    var lay  = document.getElementById('warningLayer');
    if (lay != null) {lay.style.visibility = "visible";}
    // Mozilla/Safari
    if (window.XMLHttpRequest) {
        self.xmlHttpReq = new XMLHttpRequest();
    }
    // IE
    else if (window.ActiveXObject) {
        self.xmlHttpReq = new ActiveXObject("Microsoft.XMLHTTP");
    }
    self.xmlHttpReq.open('POST', strURL, true);
    self.xmlHttpReq.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
    self.xmlHttpReq.onreadystatechange = function() {
        if (self.xmlHttpReq.readyState == 4) {
                responseText = self.xmlHttpReq.responseText;
            updatepage(div, responseText);
            if (lay != null) lay.style.visibility = "hidden";
        }
    }
    self.xmlHttpReq.send(querystring);
}

function updatepage(Id, str){
        document.getElementById(Id).innerHTML = str;
}
/*
Used by CorrelationPage.py,
elements: name,customizer, trait, filename, strainIds and vals are required by getquerystring function
*/
function getquerystring(thisform) {
    var db = thisform.customizer.value;
    var dbname = thisform.databaseFull.value;
    var form = thisform.name;
    var trait = thisform.identification.value;
    var file = thisform.filename.value;
    var ids = thisform.strainIds.value;
    var vals = thisform.vals.value;
    qstr = 'cmd=addCorr&db=' + escape(db) + '&dbname=' + escape(dbname) + '&form=' + escape(form) + '&trait=' + escape(trait) + '&file=' + escape(file)+ '&ids=' + escape(ids) + '&vals=' + escape(vals);  
        // NOTE: no '?' before querystring
    return qstr;
}

/*
* Used by snpBrowserPage.py and AJAX_snpbrowser.py, 
*/
function xmlhttpPostSNP(strURL) {
    var xmlHttpReq = false;
    var self = this;
    // Mozilla/Safari
    if (window.XMLHttpRequest) {
        self.xmlHttpReq = new XMLHttpRequest();
    }
    // IE
    else if (window.ActiveXObject) {
        self.xmlHttpReq = new ActiveXObject("Microsoft.XMLHTTP");
    }
    self.xmlHttpReq.open('POST', strURL, true);
    self.xmlHttpReq.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
    self.xmlHttpReq.onreadystatechange = function() {
        if (self.xmlHttpReq.readyState == 4) {
        	responseTextArray = self.xmlHttpReq.responseText.split("__split__");
            updatepage('menu_group', responseTextArray[0]);
            updatepage('menu_s1', responseTextArray[1]);
            updatepage('menu_s2', responseTextArray[2]);
            updatepage('menu_s3', responseTextArray[3]);
        }
    }    
    self.xmlHttpReq.send(getquerystringSNP());  
}
/*
* used by snpBrowserPage.py, html elements:newSNPPadding, group, s1 and s2 are required
*/
function getquerystringSNP() {
    var form = document.newSNPPadding;
    var group = form.group.value;
    var s1 = form.s1.value;
    var s2 = form.s2.value;
    qstr = 'group=' + escape(group) + '&s1=' + escape(s1) + '&s2=' + escape(s2);  
    	// NOTE: no '?' before querystring
    return qstr;
}


/*
Used by CorrelationPage.py, element's Id named 'warningLayer' is required
*/
function pageOffset() {
    lay  = document.getElementById('warningLayer');
    lay.style.top = document.body.scrollTop + 300; //document.body.clientWidth/2;
    lay.style.left = (windowWidth() -250)/2;
    setTimeout('pageOffset()',100);
}

/*
* Used by CorrelationPage.py, 
*/
function windowWidth(){
   if (document.getElementById){

       if (window.innerWidth)
         return window.innerWidth;
       if (document.documentElement&&document.documentElement.clientWidth)
         return document.documentElement.clientWidth;
       if (document.body.clientWidth)
         return document.body.clientWidth;
   }
}

/*
* Used by PartialCorrInputPage.py, 
*/
function setAllAsTarget(thisForm, inputRadioNames){
    var radioArray = new Array();
    radioArray = inputRadioNames.split(',');

        for (var i = 0; i < radioArray.length; i++){
	    radioElement = thisForm[radioArray[i]];
		
        for (var j = 0; j < radioElement.length; j++){
            radioElement[j].checked = false;
            value = radioElement[j].value;
            if (value == "target"){
                    radioElement[j].checked = true;
                }
        }
	}
}

/*
* Used by PartialCorrInputPage.py, 
*/
function setAllAsIgnore(thisForm, inputRadioNames){
    var radioArray = new Array();
    radioArray = inputRadioNames.split(',');

        for (var i = 0; i < radioArray.length; i++){
	    radioElement = thisForm[radioArray[i]];
		
	    for (var j = 0; j < radioElement.length; j++){
		    radioElement[j].checked = false;
		    value = radioElement[j].value;
	        if (value == "ignored"){
                    radioElement[j].checked = true;
                }
	    }
	}
}

/*
* moved from beta2.js 
*/
function checkUncheck(value, permCheck, bootCheck) {
		 if(value=="physic") {
			  permCheck.checked=true
			  bootCheck.checked=false
	 } else {
		  permCheck.checked=true
			  bootCheck.checked=true
		 }
}

/*
updated by NL: 06-07-2010
add new item at the top
*/
function addToList(text, value, list) {
	for (var j = list.length-1; j >=0; j--){
		list.options[j+1]= new Option(list.options[j].text,list.options[j].value);
	}
	list.options[0] = new Option(text, value)
}

function removeFromList(index, list) {
	list.options[index] = null
	list.options[index].selected = true
	if (list.length == 1) {
		list.options[0].selected = true
	}
}

function swapOptions(index1, index2, list) {
	 text1 = list.options[index1].text
	 value1 = list.options[index1].value
	 text2 = list.options[index2].text
	 value2 = list.options[index2].value
	 list.options[index1] = new Option(text2, value2)
	 list.options[index2] = new Option(text1, value1)
	 list.options[index2].selected = true
}

function selectAllElements(list) {
	 for(i=0; i<list.length; i++) {
		  list.options[i].selected = true
	 }
}

function deleteAllElements(list) {
	 list.length=0
}

function formInNewWindow(thisform) {
	 var d = new Date()
	 winName = "Intvl"+d.getDate()+""+d.getMonth()+""+d.getHours()+""+d.getMinutes()+""+d.getSeconds();
	 win = window.open("", winName, "toolbar=yes,location=yes,directories=yes,status=yes,menubar=yes,scrollbars=yes,copyhistory=yes,resizable=yes");
	 thisform.target = winName;
	 thisform.submit();
}

/*
* moved from whats_new.html 
*/
function colapse(id)
{
    if( document.getElementById(id).style.display =='none')
    {
        document.getElementById(id).style.display ='';
    }
    else if( document.getElementById(id).style.display =='')
    {
        document.getElementById(id).style.display ='none';
    }
}
