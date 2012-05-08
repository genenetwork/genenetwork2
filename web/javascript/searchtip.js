// search tips for 'Get Any' and 'Combined' in the main search page http://www.genenetwork.org/
function searchtip(){

	var tfor     = document.getElementById("tfor");
	var tfand    = document.getElementById("tfand");
	var btsearch = document.getElementById("btsearch");
	var tiptextor  = "Enter list here (APOE, APOA, etc.): logical OR";
	var tiptextand = "Enter terms to combine (blood pressure): logical AND";

	if(tfor.value == "" || tfor.value == tiptextor) {
		tfor.className = "searchtip";
		tfor.value = tiptextor;
	}
	
	tfor.onfocus = function(e) {
		if(tfor.value == tiptextor) {
			tfor.value = "";
		}
		tfor.className = "";
	}
	tfor.onblur = function(e) {
		if(tfor.value == "") {
			tfor.className = "searchtip";
			tfor.value = tiptextor;
		} else if(tfor.value == tiptextor){
			tfor.className = "searchtip";
		} else {
			tfor.className = "";
		}
	}

	if(tfand.value == "" || tfand.value == tiptextand) {
		tfand.className = "searchtip";
        tfand.value = tiptextand;
	}
    
	tfand.onfocus = function(e) {
		if(tfand.value == tiptextand) {
			tfand.value = "";
        }
		tfand.className = "";
    }
	tfand.onblur = function(e) {
		if(tfand.value == "") {
			tfand.className = "searchtip";
			tfand.value = tiptextand;
		} else if(tfand.value == tiptextand) {
			tfand.className = "searchtip";		
		} else {
			tfand.className = "";
		}
    }
	
	btsearch.onclick = function(e) {
		if(tfor.value == tiptextor) {
			tfor.value = "";
		}
		if(tfand.value == tiptextand) {
			tfand.value = "";
        }
		return true;
	}
	
}
