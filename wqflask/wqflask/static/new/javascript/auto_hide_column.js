
$(function (){
$("table th").each(function(index,col_th){
	var filter_counter = 0;
	// map each column to row ie  column i to ith element
	var column_tds = $(this).closest('table').find('tr td:nth-child(' + (index + 1) + ')')
	column_tds.each(function(j,col_td){
		if(this.innerHTML==''||this.innerHTML=="N/A"){
			filter_counter+=1;
		}
		else{
			// break
			return false;
		}
	})
	if (filter_counter == ($('table tr').length - 1)){
		$(this).hide();
        column_tds.hide();

	}
})
})