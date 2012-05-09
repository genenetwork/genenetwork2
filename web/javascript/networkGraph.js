// This JavaScript was written by Zach Sloan in 2009-2010.
// This script is used in the Network Graph output from the Trait Collection window

var searchResults = document.getElementById('searchResult').value.split("\t");
var symbolList = document.getElementById('symbolList').value.split("\t");
var originalThreshold = document.getElementById('kValue').value;
addTraitSelection();
		
function addTraitSelection()
{
    var gType = document.getElementById('gType').value;
    var nodeSelect = document.getElementById('nodeSelect');
    var newDropDown = document.createElement('newDrop');
        
    newDropDown.innerHTML = generateDropdownHtml();
    
    if (gType == "radial"){         
        nodeSelect.appendChild(newDropDown);
        originalLock = document.getElementById('lock').value;
        document.getElementById('lock').value = "yes";
        if ( originalThreshold == "undefined"){
            originalThreshold = document.getElementById('kValue').value;
        }
        document.getElementById('kValue').value = "0.0";
        
    }
    else{   
        try{
            nodeSelect.removeChild(nodeSelect.childNodes[0]);
            document.getElementById('lock').value = originalLock;
            document.getElementById('kValue').value = originalThreshold;
        } catch(err){
            originalLock = document.getElementById('lock').value;
            originalThreshold = document.getElementById('kValue').value;
        }
    }
}

function generateDropdownHtml(){
    var html = "";
    
    html += "<td align='right'>&nbsp;<select name='traitNode' id='traitNode'>";
    
    html += "<option value='none'>Select Central Node</option>";
    html += "<option value='auto'>Auto</option>";
    
    for (var i=0, len=searchResults.length; i<len; ++i)
    {
        html += "<option value='" + searchResults[i] + "'>" + symbolList[i] + ": " + searchResults[i] + "</option>";
    }
    
    html += "</select>";
    html += "</td>";
    
    return html;
}

function sortSearchResults(myForm)
{
    var newSearchResults = searchResults
    
    if (document.getElementById('traitNode')){
        var selectedNode = document.getElementById('traitNode').value;
        
        if (selectedNode == "none")
        {
            alert("Please select a central node for your radial graph.");
            return false;
        }
    
        else if (selectedNode == "auto")
        {
            var newSelectedNode = String(searchResults[parseInt(document.getElementById('optimalNode').value)]);
        }
        
        else
        {
            var newSelectedNode = selectedNode;
        }
        
        newSearchResults.splice(searchResults.indexOf(newSelectedNode), 1);
    
        newSearchResults.splice(0, 0, newSelectedNode);      
    }
    
    var gType = document.getElementById('gType').value;
    
    if (gType == "none")
    {
        alert("Please select a graph method.");
        return false;
    }
           
    document.getElementById('searchResult').value = newSearchResults.join("\t"); 
    
    databaseFunc(myForm, 'networkGraph');
    
}

function changeThreshold(){
    var lock = document.getElementById('lock').value;
    var threshold = document.getElementById('kValue').value;
    
    if (lock == "yes"){
        if(threshold != 0){
            originalThreshold = threshold;
            document.getElementById('kValue').value = "0.0";
        }
    }
    
    else if (lock == "no" && originalThreshold != 0){
        document.getElementById('kValue').value = originalThreshold;
    }
}

