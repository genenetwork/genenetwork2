$(function(){
	$("table").each(function(table){
		$(this).find("th").each(function(col_index,col_th){
			var filter_counter=0
			var col_td=$(this).closest('table').find('tr td:nth-child(' + (col_index + 1) + ')')
			col_td.each(function(td_index,col_td){
				if(this.innerHTML==""||this.innerHTML=="N/A"){
					filter_counter+=1
				}
				else{
					return false
				}
			})
			if (filter_counter==$(this).closest("table").find("tr").length-1){
					$(this).hide();
                   col_td.hide();

			}
		})
	})
})
