recheckRows = function(theTable, checkedRows){
  // This is meant to recheck checkboxes after columns are resized
  checkCells = theTable.column(0).nodes().to$();
  for (let i = 0; i < checkCells.length; i++) {
    if (checkedRows.includes(i)){
      checkCells[i].childNodes[0].checked = true;
    }
  }

  checkRows = traitTable.rows().nodes();
  for (let i =0; i < checkRows.length; i++) {
    if (checkedRows.includes(i)){
      checkRows[i].classList.add("selected")
    }
  }
}

getCheckedRows = function(tableId){
  let checkedRows = []
  $("#" + tableId + " input.checkbox").each(function(index){
    if ($(this).prop("checked") == true){
      checkedRows.push(index);
    }
  });

  return checkedRows
}

function setUserColumnsDefWidths(tableId, columnDefs) {
  var userColumnDef;

  // Get the settings for this table from localStorage
  var userColumnDefs = JSON.parse(localStorage.getItem(tableId)) || [];

  if (userColumnDefs.length === 0 ) return;

  columnDefs.forEach( function(columnDef) {
    // Check if there is a width specified for this column
    userColumnDef = userColumnDefs.find( function(column) {
      return column.targets === columnDef.targets;
    });

    // If there is, set the width of this columnDef in px
    if ( userColumnDef ) {

      columnDef.sWidth = userColumnDef.width + 'px';
      columnDef.width = userColumnDef.width + 'px';

      $('.toggle-vis').each(function(){
        if ($(this).attr('data-column') == columnDef.targets){
          if ($(this).hasClass("active")){
            columnDef.bVisible = false
          } else {
            columnDef.bVisible = true
          }
        }
      })
    }
  });

  return columnDefs
}

function saveColumnSettings(tableId, traitTable) {
  var userColumnDefs = JSON.parse(localStorage.getItem(tableId)) || [];
  var width, header, existingSetting; 

  traitTable.columns().every( function ( targets ) {
    // Check if there is a setting for this column in localStorage
    existingSetting = userColumnDefs.findIndex( function(column) { return column.targets === targets;});

    // Get the width of this column
    header = this.header();
    width = $(header).width();

    if ( existingSetting !== -1 ) {
    // Update the width
    userColumnDefs[existingSetting].width = width;
    } else {
      // Add the width for this column
      userColumnDefs.push({
          targets: targets,
          width:  width,
      });
    }
  });

  // Save (or update) the settings in localStorage
  localStorage.setItem(tableId, JSON.stringify(userColumnDefs));
}
