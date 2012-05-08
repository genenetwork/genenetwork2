
function xchange() {  
  var select = document.crossChoice.RISet;
  var value = select.options[select.selectedIndex].value;
  
  if (value !="BDAI") return;
  document.crossChoice.variance.checked = false;
}

function showSample(){
	document.crossChoice.submitID.value = "sample";
	document.crossChoice.submit();
}

function showNext(){
	document.crossChoice.submitID.value = "next";
	document.crossChoice.submit();
}

