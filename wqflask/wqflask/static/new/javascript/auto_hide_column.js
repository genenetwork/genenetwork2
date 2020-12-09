    function filterDatatable(datatable){
        let invalidColumns=[]
        let columnCount=datatable.columns().header().length;
        let numberOfRows=datatable.rows().count();
        for (let col=0; col<columnCount; col++){
            colObj = datatable.column(col).nodes().to$();
            allNAs = true;
            for (let i=0;i<numberOfRows;i++){
                cellContent = colObj[i].childNodes[0].data
                if (cellContent != "N/A" && cellContent != ""){
                    allNAs = false;
                    break;
                }
            }
            if (allNAs){
                invalidColumns.push(col)
            }
        }
        return datatable.columns(invalidColumns).visible(false);

    }