function filterDatable(datatable){
        let visitedColumns=[]
        let columnCount=datatable.columns().header().length;
        let numberOfRows=datatable.data().length;
        for (let i=0;i<numberOfRows;i++){
            if (visitedColumns.length==columnCount){
                break;
            }
            let rowObj=datatable.rows(i).data()
            rowObj.data().each(function(rowData,v){
                if (visitedColumns.length==columnCount){
                    return false;
                }
                for (let j=0;j<rowData.length;j++){
                    if (j in visitedColumns||visitedColumns.length==columnCount){
                        break;
                    }
                    if (rowData[j]!="N/A" && rowData[j]!=""){

                        visitedColumns.push(j)
                    }
                }
            })
        }
        emptyColumns=Array.from(Array(columnCount).keys()).filter((item)=>visitedColumns.indexOf(item)<0);
        return datatable.columns(emptyColumns).visible(false);

}
