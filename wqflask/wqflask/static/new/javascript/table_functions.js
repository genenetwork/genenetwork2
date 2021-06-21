recheck_rows = function(the_table, checked_rows){
  //ZS: This is meant to recheck checkboxes after columns are resized
  check_cells = the_table.column(0).nodes().to$();
  for (let i = 0; i < check_cells.length; i++) {
    if (checked_rows.includes(i)){
      check_cells[i].childNodes[0].checked = true;
    }
  }

  check_rows = trait_table.rows().nodes();
  for (let i =0; i < check_rows.length; i++) {
    if (checked_rows.includes(i)){
      check_rows[i].classList.add("selected")
    }
  }
}

get_checked_rows = function(table_id){
  let checked_rows = []
  $("#" + table_id + " input").each(function(index){
    if ($(this).prop("checked") == true){
      checked_rows.push(index);
    }
  });

  return checked_rows
}

function setUserColumnsDefWidths(table_id) {
  var userColumnDef;

  // Get the settings for this table from localStorage
  var userColumnDefs = JSON.parse(localStorage.getItem(table_id)) || [];

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
}

function saveColumnSettings(table_id, trait_table) {
  var userColumnDefs = JSON.parse(localStorage.getItem(table_id)) || [];
  var width, header, existingSetting; 

  trait_table.columns().every( function ( targets ) {
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
  localStorage.setItem(table_id, JSON.stringify(userColumnDefs));
}
