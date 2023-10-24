create_table = function(tableId="trait_table", tableData = [], columnDefs = [], customSettings = {}) {

    loadDataTable(tableId=tableId, tableData=tableData, customSettings, firstRun=true)

    var widthChange = 0; // For storing the change in width so overall table width can be adjusted by that amount
    function loadDataTable(tableId, tableData, customSettings, firstRun=false){
        if (!firstRun){
            columnDefs = setUserColumnsDefWidths(tableId, columnDefs);
        }

        tableSettings = {
            "drawCallback": function( settings ) {
                $('#' + tableId + ' tr').off().on("click", function(event) {
                  if (event.target.type !== 'checkbox' && event.target.tagName.toLowerCase() !== 'a') {
                    var obj =$(this).find('input');
                    obj.prop('checked', !obj.is(':checked'));
                  }
                  if ($(this).hasClass("selected") && event.target.tagName.toLowerCase() !== 'a'){
                    $(this).removeClass("selected")
                  } else if (event.target.tagName.toLowerCase() !== 'a') {
                    $(this).addClass("selected")
                  }
                  change_buttons()
                });
            },
            "columns": columnDefs,
            "sDom": "iti",
            "destroy": true,
            "autoWidth": false,
            "bSortClasses": false,
            "scrollY": "100vh",
            "scrollX": "100%",
            "scrollCollapse": true,
            "scroller":  true,
            "iDisplayLength": -1,
            "initComplete": function (settings) {
                // Add JQueryUI resizable functionality to each th in the ScrollHead table
                $('#' + tableId + '_wrapper .dataTables_scrollHead thead th').resizable({
                    handles: "e",
                    alsoResize: '#' + tableId + '_wrapper .dataTables_scrollHead table', //Not essential but makes the resizing smoother
                    resize: function( event, ui ) {
                        widthChange = ui.size.width - ui.originalSize.width;
                    },
                    stop: function () {
                        saveColumnSettings(tableId, theTable);
                        loadDataTable(tableId, tableData, customSettings, firstRun=false);
                    }
                });
            }
        }

        if (tableData.length > 0){
            tableSettings["data"] = tableData
        }

        // Replace default settings with custom settings or add custom settings if not already set in default settings
        $.each(customSettings, function(key, value) {
            tableSettings[key] = value
        });

        if (!firstRun){
            $('#' + tableId + '_container').css("width", String($('#' + tableId).width() + widthChange + 17) + "px"); // Change the container width by the change in width of the adjusted column, so the overall table size adjusts properly

            let checkedRows = getCheckedRows(tableId);
            theTable = $('#' + tableId).DataTable(tableSettings);
            if (checkedRows.length > 0){
                recheckRows(theTable, checkedRows);
            }
        } else {
            theTable = $('#' + tableId).DataTable(tableSettings);
            theTable.draw();
            $('#' + tableId + '_container').css("width", String($('#' + tableId).width() + 17) + "px");
            theTable.columns.adjust().draw();
        }
    }

    theTable.on( 'order.dt search.dt draw.dt', function () {
        theTable.column(1, {search:'applied', order:'applied'}).nodes().each( function (cell, i) {
        cell.innerHTML = i+1;
        } );
    } ).draw();

    window.addEventListener('resize', function(){
        theTable.columns.adjust();
    });

    $('#' + tableId + '_searchbox').on( 'keyup', function () {
        theTable.search($(this).val()).draw();
    } );

    $('.toggle-vis').on('click', function (e) {
        e.preventDefault();

        function toggleColumn(column) {
            // Toggle column visibility
            column.visible( ! column.visible() );
            if (column.visible()){
                $(this).removeClass("active");
            } else {
                $(this).addClass("active");
            }
        }

        // Get the column API object
        var targetCols = $(this).attr('data-column').split(",")
        for (let i = 0; i < targetCols.length; i++){
            var column = theTable.column( targetCols[i] );
            toggleColumn(column);
        }
    } );

    $('#redraw').on('click', function (e) {
        e.preventDefault();
        trait_table.columns().visible( true );
        $('.toggle-vis.active').removeClass('active');
    });
}
