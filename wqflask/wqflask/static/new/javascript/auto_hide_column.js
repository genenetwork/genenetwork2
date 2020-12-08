function filterDatatable(datatable){
    let visitedFoundColumns=[]
    let columnCount=datatable.columns().header().length;
    let numberOfRows=datatable.data().length;
    for (let i=0;i<numberOfRows;i++){
        if (visitedFoundColumns.length==columnCount){
            break;
        }
        let rowObj=datatable.rows(i).data()[0]
        for(let col=0;col<rowObj.length;col++){
            if (visitedFoundColumns.length==columnCount){
                break;
            }
            if (visitedFoundColumns.includes(col) || rowObj[col]=="N/A"||rowObj[col]==""){
                continue;
            }
            visitedFoundColumns.push(col)
        }
    }
    emptyColumns=Array.from(Array(columnCount).keys()).filter((item)=>visitedFoundColumns.indexOf(item)<0);
    return datatable.columns(emptyColumns).visible(false);

}