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

let naturalAsc = $.fn.dataTableExt.oSort["natural-ci-asc"]
let naturalDesc = $.fn.dataTableExt.oSort["natural-ci-desc"]

let na_equivalent_vals = ["N/A", "--", "", "NULL"]; //ZS: Since there are multiple values that should be treated the same as N/A

function extractInnerText(the_string){
  var span = document.createElement('span');
  span.innerHTML = the_string;
  return span.textContent || span.innerText;
}

function sortNAs(a, b, sort_function){
  if ( na_equivalent_vals.includes(a) && na_equivalent_vals.includes(b)) {
    return 0;
  }
  if (na_equivalent_vals.includes(a)){
    return 1
  }
  if (na_equivalent_vals.includes(b)) {
    return -1;
  }
  return sort_function(a, b)
}

$.extend( $.fn.dataTableExt.oSort, {
  "natural-minus-na-asc": function (a, b) {
    return sortNAs(extractInnerText(a), extractInnerText(b), naturalAsc)
  },
  "natural-minus-na-desc": function (a, b) {
    return sortNAs(extractInnerText(a), extractInnerText(b), naturalDesc)
  }
});

$.fn.dataTable.ext.order['dom-checkbox'] = function  ( settings, col )
{
    return this.api().column( col, {order:'index'} ).nodes().map( function ( td, i ) {
        return $('input', td).prop('checked') ? '1' : '0';
    } );
};

$.fn.dataTable.ext.order['dom-inner-text'] = function  ( settings, col )
{
    return this.api().column( col, {order:'index'} ).nodes().map( function ( td, i ) {
        return $(td).text();
    } );
}