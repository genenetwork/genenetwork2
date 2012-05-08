/* Generated Date : 2010-07-20  */ 
var sArr = [
{txt:'',val:''},
{txt:'Database name',val:'1'},
{txt:'ID number of trait',val:'2'},
{txt:'Symbol, Gene, Phenotype',val:'3'},
{txt:'Chr and Mb',val:'4'},
{txt:'LRS or LOD',val:'5'},
{txt:'Mean Value',val:'6'}

];

var gArr = [
{txt:'',val:''},
{txt:'Database name',val:'1'},
{txt:'ID number of trait',val:'2'},
{txt:'Symbol, Gene, Phenotype',val:'3'},
{txt:'Chr and Mb',val:'4'},
{txt:'LRS or LOD',val:'5'},
{txt:'Mean Value',val:'6'}];

var tArr = [
{txt:'',val:''},
{txt:'Database name',val:'1'},
{txt:'ID number of trait',val:'2'},
{txt:'Symbol, Gene, Phenotype',val:'3'},
{txt:'Chr and Mb',val:'4'},
{txt:'LRS or LOD',val:'5'},
{txt:'Mean Value',val:'6'}];

var lArr = [
 null,
[1,2,3],
[1,2,4],
[1,2,5],
[1,2,6],
[1,3,2],
[1,3,4],
[1,3,5],
[1,3,6],
[1,4,2],
[1,4,3],
[1,4,5],
[1,4,6],
[1,5,2],
[1,5,3],
[1,5,4],
[1,5,6],
[1,6,2],
[1,6,3],
[1,6,4],
[1,6,5],
[2,1,3],
[2,1,4],
[2,1,5],
[2,1,6],
[2,3,1],
[2,3,4],
[2,3,5],
[2,3,6],
[2,4,1],
[2,4,3],
[2,4,5],
[2,4,6],
[2,5,1],
[2,5,3],
[2,5,4],
[2,5,6],
[2,6,1],
[2,6,3],
[2,6,4],
[2,6,5],
[3,1,2],
[3,1,4],
[3,1,5],
[3,1,6],
[3,2,1],
[3,2,4],
[3,2,5],
[3,2,6],
[3,4,1],
[3,4,2],
[3,4,5],
[3,4,6],
[3,5,1],
[3,5,2],
[3,5,4],
[3,5,6],
[3,6,1],
[3,6,2],
[3,6,4],
[3,6,5],
[4,1,2],
[4,1,3],
[4,1,5],
[4,1,6],
[4,2,1],
[4,2,3],
[4,2,5],
[4,2,6],
[4,3,1],
[4,3,2],
[4,3,5],
[4,3,6],
[4,5,1],
[4,5,2],
[4,5,3],
[4,5,6],
[4,6,1],
[4,6,2],
[4,6,4],
[4,6,5],
[5,1,2],
[5,1,3],
[5,1,4],
[5,1,6],
[5,2,1],
[5,2,3],
[5,2,4],
[5,2,6],
[5,3,1],
[5,3,2],
[5,3,4],
[5,3,6],
[5,4,1],
[5,4,2],
[5,4,3],
[5,4,6],
[5,6,1],
[5,6,2],
[5,6,3],
[5,6,4],
[6,1,2],
[6,1,3],
[6,1,4],
[6,1,5],
[6,2,1],
[6,2,3],
[6,2,4],
[6,2,5],
[6,3,1],
[6,3,2],
[6,3,4],
[6,3,5],
[6,4,1],
[6,4,2],
[6,4,3],
[6,4,5],
[6,5,1],
[6,5,2],
[6,5,3],
[6,5,4]];

/* 
*  input: selectObjId (designated select menu, such as sort1, sort2, etc... )
*  function: setting options value for select menu dynamically based on linkage array(lArr)
*  output: null
*/
function fillOptions(selectObjId)
{
    
		
	if(selectObjId==null)
	{
		var sort1Obj = document.getElementsByName('sort1')[0];
		
		var len = sArr.length;
		for (var i=1; i < len; i++) { 
		// setting sort1' option
		sort1Obj.options[i-1] = new Option(sArr[i].txt, sArr[i].val);

		
		}
		fillOptions('sort1');
	}else if(selectObjId=='sort1')
	{
	    var sort1Obj = document.getElementsByName('sort1')[0];
		var sort2Obj = document.getElementsByName('sort2')[0];
		var len = lArr.length;
		var arr = [];
		var idx = 0;
		for (var i=1; i < len; i++) {
			//get sort2 info from lArr
			if(lArr[i][0]==(getIndexByValue('sort1',sort1Obj.value)).toString()&&!Contains(arr,lArr[i][1]))
			{
				arr[idx++]=lArr[i][1];
			}  
		}
		idx=0;
		len = arr.length;
		removeOptions("sort2");
		for (var i=0; i < len; i++) {
			// setting sort2's option
			sort2Obj.options[idx++] = new Option(gArr[arr[i]].txt, gArr[arr[i]].val); 
		}
		fillOptions('sort2');
	}else if(selectObjId=='sort2')
	{
	    var sort1Obj = document.getElementsByName('sort1')[0];
		var sort2Obj = document.getElementsByName('sort2')[0];
		var sort3Obj = document.getElementsByName('sort3')[0];
		var len = lArr.length;
		var arr = [];
		var idx = 0;
		for (var i=1; i < len; i++) {
			//get sort2 info from lArr
			if(lArr[i][0]==(getIndexByValue('sort1',sort1Obj.value)).toString()&&lArr[i][1]==(getIndexByValue('sort2',sort2Obj.value)).toString()&&!Contains(arr,lArr[i][2]))
			{
				arr[idx++]=lArr[i][2];
			}  
		}
		idx=0;
		len = arr.length;
		removeOptions("sort3");
		for (var i=0; i < len; i++) {
			// setting sort3's option
			sort3Obj.options[idx++] = new Option(tArr[arr[i]].txt, tArr[arr[i]].val); 
		}
		fillOptions('sort3');
	}
}

/* 
*  input: arr (targeted array); obj (targeted value)
*  function: check whether targeted array contains targeted value or not
*  output: return true, if array contains targeted value, otherwise return false
*/
function Contains(arr,obj) { 
	var i = arr.length; 
	while (i--) { 
		if (arr[i] == obj) { 
		return true; 
		}
	} 
	return false; 
} 

updateChocie();

/* 
* input: selectObj (designated select menu, such as sort1, sort2, etc... )
* function: clear designated select menu's option
* output: null
*/
function removeOptions(selectObj) {     
	if (typeof selectObj != 'object'){         
		selectObj = document.getElementsByName(selectObj)[0];
	}        
	var len = selectObj.options.length;      
	for (var i=0; i < len; i++)     {         
	// clear current selection       
		selectObj.options[0] = null;    
	} 
} 

/* 
*  input: selectObjId (designated select menu, such as sort1, sort2, etc... )
*         Value: target value
*  function: retrieve Index info of target value in designated array
*  output: index info
*/
function getIndexByValue(selectObjId,val)
{
	if(selectObjId=='sort1')
	{
		for(var i=1;i<sArr.length;i++)
			if(sArr[i].val==val)
				return i;
	}else if(selectObjId=='sort2')
	{
		for(var i=1;i<gArr.length;i++)
			if(gArr[i].val==val)
				return i;
	}else if(selectObjId=='sort3')
	{
		for(var i=1;i<tArr.length;i++)
			if(tArr[i].val==val)
				return i;
	}
	else return;
}

function setDefault(thisform){
	setCookie('cookieTest', 'cookieTest', 1);
	var cookieTest = getCookie('cookieTest');
	delCookie('cookieTest');
	if (cookieTest){
		var defaultSort1 = thisform.sort1.value;
		setCookie('defaultSort1', defaultSort1, 10);
		var defaultSort2 = thisform.sort2.value;
		setCookie('defaultSort2', defaultSort2, 10);
		var defaultSort3 = thisform.sort3.value;
		setCookie('defaultSort3', defaultSort3, 10);
		updateChocie();			
	}
}
/* 
*  input: objId (designated select menu, such as sort1, sort2, etc... )
*  		  val(targeted value)
*  function: setting option's selected status for designated select menu based on target value, also update the following select menu 
*  output: return true if selected status has been set, otherwise return false.
*/
function setChoice(objId,val)
{
	var Obj = document.getElementsByName(objId)[0];
	var idx=-1;
	for(i=0;i<Obj.options.length;i++){
		if(Obj.options[i].value==val){
			idx=i;
			break;
		}
	}
	if(idx>=0){
		//setting option's selected status 
		Obj.options[idx].selected=true;
		//update the following select menu
		fillOptions(objId)
		return true;
	}else{
		return false;
	}
}

// setting option's selected status based on default setting or cookie setting for sort1, sort2, and sort3 select menu
function updateChocie(){
	fillOptions(null);	
	//define default value
	var defaultSort1 = 1
	var defaultSort2 = 3
	var defaultSort3 = 4
	
	//if cookie exists, then use cookie value, otherwise use default value
	var cookieSort1 = getCookie('defaultSort1');
	if(cookieSort1)  defaultSort1= cookieSort1 
	var cookieSort2 = getCookie('defaultSort2');
	if(cookieSort2)  defaultSort2 = cookieSort2;
	var cookieSort3 = getCookie('defaultSort3');
	if(cookieSort3 )  defaultSort3 = cookieSort3; 

	//setting option's selected status
	if(!setChoice('sort1',defaultSort1)){return;}
	if(!setChoice('sort2',defaultSort2)){return;}
	if(!setChoice('sort3',defaultSort3)){return;}
}