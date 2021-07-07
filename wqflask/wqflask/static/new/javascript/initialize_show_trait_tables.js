// ZS: This file initializes the tables for the show_trait page

// ZS: This variable is just created to get the column position of the first case attribute (if case attributes exist), since it's needed to set the row classes in createdRow for the DataTable
var attribute_start_pos = 3;
if (js_data.se_exists) {
  attribute_start_pos += 2;
}
if (js_data.has_num_cases === true) {
  attribute_start_pos += 1;
}

build_columns = function() {
  let column_list = [
    {
      'data': null,
      'orderDataType': "dom-checkbox",
      'searchable' : false,
      'targets': 0,
      'width': "25px",
      'render': function(data, type, row, meta) {
      return '<input type="checkbox" name="searchResult" class="checkbox edit_sample_checkbox" value="">'
      }
    },
    {
      'title': "ID",
      'type': "natural",
      'searchable' : false,
      'targets': 1,
      'width': "35px",
      'data': "this_id"
    },
    {
      'title': "Sample",
      'type': "natural",
      'data': null,
      'targets': 2,
      'width': "60px",
      'render': function(data, type, row, meta) {
      return '<span class="edit_sample_sample_name">' + data.name + '</span>'
      }
    },
    {
      'title': "<div style='text-align: right;'>Value</div>",
      'orderDataType': "dom-input",
      'type': "cust-txt",
      'data': null,
      'targets': 3,
      'width': "60px",
      'render': function(data, type, row, meta) {
        if (data.value == null) {
            return '<input type="text" data-value="x" data-qnorm="x" data-zscore="x" name="value:' + data.name + '" style="text-align: right;" class="trait_value_input edit_sample_value" value="x" size=' + js_data.max_digits[0] + '>'
        } else {
            return '<input type="text" data-value="' + data.value.toFixed(3) + '" data-qnorm="' + js_data['qnorm_values'][0][parseInt(data.this_id) - 1] + '" data-zscore="' + js_data['zscore_values'][0][parseInt(data.this_id) - 1] + '" name="value:' + data.name + '" class="trait_value_input edit_sample_value" value="' + data.value.toFixed(3) + '" size=' + js_data.max_digits[0] + '>'
        }
      }
    }
  ];

  attr_start = 4
  if (js_data.se_exists) {
    attr_start += 2
    column_list.push(
      {
        'bSortable': false,
        'type': "natural",
        'data': null,
        'targets': 4,
        'searchable' : false,
        'width': "25px",
        'render': function(data, type, row, meta) {
        return '±'
        }
      },
      {
        'title': "<div style='text-align: right;'>SE</div>",
        'orderDataType': "dom-input",
        'type': "cust-txt",
        'data': null,
        'targets': 5,
        'width': "60px",
        'render': function(data, type, row, meta) {
          if (data.variance == null) {
              return '<input type="text" data-value="x" data-qnorm="x" data-zscore="x" name="value:' + data.name + '" class="trait_value_input edit_sample_se" value="x" size=6>'
          } else {
              return '<input type="text" data-value="' + data.variance.toFixed(3) + '" data-qnorm="x" data-zscore="x" name="value:' + data.name + '" class="trait_value_input edit_sample_se" value="' + data.variance.toFixed(3) + '" size=6>'
          }
        }
      }
    );

    if (js_data.has_num_cases === true) {
      attr_start += 1
      column_list.push(
        {
          'title': "<div style='text-align: right;'>N</div>",
          'orderDataType': "dom-input",
          'type': "cust-txt",
          'data': null,
          'targets': 6,
          'width': "60px",
          'render': function(data, type, row, meta) {
            if (data.num_cases == null || data.num_cases == undefined) {
                return '<input type="text" data-value="x" data-qnorm="x" data-zscore="x" name="value:' + data.name + '" class="trait_value_input edit_sample_num_cases" value="x" size=4 maxlength=4>'
            } else {
                return '<input type="text" data-value="' + data.num_cases + '" data-qnorm="x" data-zscore="x" name="value:' + data.name + '" class="trait_value_input edit_sample_num_cases" value="' + data.num_cases + '" size=4 maxlength=4>'
            }
          }
        }
      );
    }
  }
  else {
    if (js_data.has_num_cases === true) {
      attr_start += 1
      column_list.push(
        {
          'title': "<div style='text-align: right;'>N</div>",
          'orderDataType': "dom-input",
          'type': "cust-txt",
          'data': null,
          'targets': 4,
          'width': "60px",
          'render': function(data, type, row, meta) {
            if (data.num_cases == null || data.num_cases == undefined) {
                return '<input type="text" data-value="x" data-qnorm="x" data-zscore="x" name="value:' + data.name + '" class="trait_value_input edit_sample_num_cases" value="x" size=4 maxlength=4>'
            } else {
                return '<input type="text" data-value="' + data.num_cases + '" data-qnorm="x" data-zscore="x" name="value:' + data.name + '" class="trait_value_input edit_sample_num_cases" value="' + data.num_cases + '" size=4 maxlength=4>'
            }
          }
        }
      );
    }
  }

  attr_keys = Object.keys(js_data.attributes).sort((a, b) => (js_data.attributes[a].name.toLowerCase() > js_data.attributes[b].name.toLowerCase()) ? 1 : -1)
  for (i = 0; i < attr_keys.length; i++){
    column_list.push(
      {
        'title': "<div style='text-align: " + js_data.attributes[attr_keys[i]].alignment + "'>" + js_data.attributes[attr_keys[i]].name + "</div>",
        'type': "natural",
        'data': null,
        'targets': attr_start + i,
        'render': function(data, type, row, meta) {
          attr_name = Object.keys(data.extra_attributes).sort()[meta.col - data.first_attr_col]

          if (attr_name != null && attr_name != undefined){
            if (Array.isArray(data.extra_attributes[attr_name])){
              return '<a href="' + data.extra_attributes[attr_name][1] + '">' + data.extra_attributes[attr_name][0] + '</a>'
            } else {
              return data.extra_attributes[attr_name]
            }
          } else {
              return ""
          }
        }
      }
    )
  }
  return column_list
}

columnDefs = build_columns()

loadDataTable(first_run=true, table_id="samples_primary", table_data=js_data['sample_lists'][0])
if (js_data.sample_lists.length > 1){
  loadDataTable(first_run=true, table_id="samples_other", table_data=js_data['sample_lists'][1])
}

function loadDataTable(first_run=false, table_id, table_data){

  console.log("COL DEFS:", columnDefs)

  if (!first_run){
    setUserColumnsDefWidths(table_id);
  }

  if (table_id == "samples_primary"){
    table_type = "Primary"
  } else {
    table_type = "Other"
  }

  table_settings = {
    'initComplete': function(settings, json) {
    $('.edit_sample_value').change(function() {
        edit_data_change();
    });
    },
    'createdRow': function ( row, data, index ) {
      $(row).attr('id', table_type + "_" + data.this_id)
      $(row).addClass("value_se");
      if (data.outlier) {
        $(row).addClass("outlier");
      }
      $('td', row).eq(1).addClass("column_name-Index")
      $('td', row).eq(2).addClass("column_name-Sample")
      $('td', row).eq(3).addClass("column_name-Value")
      if (js_data.se_exists) {
        $('td', row).eq(5).addClass("column_name-SE")
        if (js_data.has_num_cases === true) {
          $('td', row).eq(6).addClass("column_name-num_cases")
        } else {
          if (js_data.has_num_cases === true) {
            $('td', row).eq(4).addClass("column_name-num_cases")
          }
        }
      } else {
        if (js_data.has_num_cases === true) {
          $('td', row).eq(4).addClass("column_name-num_cases")
        }
      }

      for (i=0; i < attr_keys.length; i++) {
        $('td', row).eq(attribute_start_pos + i + 1).addClass("column_name-" + js_data.attributes[attr_keys[i]].name)
        $('td', row).eq(attribute_start_pos + i + 1).attr("style", "text-align: " + js_data.attributes[attr_keys[i]].alignment + "; padding-top: 2px; padding-bottom: 0px;")
      }
    },
    'data': table_data,
    'columns': columnDefs,
    "order": [[1, "asc" ]],
    "sDom": "iti",
    "destroy": true,
    "autoWidth": false,
    "deferRender": true,
    "bSortClasses": false,
    "scrollY": "100vh",
    "scrollCollapse": true,
    "scroller":  true,
    "iDisplayLength": -1,
    "initComplete": function (settings) {
      //Add JQueryUI resizable functionality to each th in the ScrollHead table
      $('#' + table_id + '_wrapper .dataTables_scrollHead thead th').resizable({
        handles: "e",
        alsoResize: '#' + table_id + '_wrapper .dataTables_scrollHead table', //Not essential but makes the resizing smoother
        resize: function( event, ui ) {
          width_change = ui.size.width - ui.originalSize.width;
        },
        stop: function () {
          saveColumnSettings(table_id, the_table);
          loadDataTable(first_run=false, table_id, table_data);
        }
      });
    }
  }

  if (!first_run){
    $('#' + table_type.toLowerCase() + '_container').css("width", String($('#' + table_id).width() + width_change + 17) + "px"); //ZS : Change the container width by the change in width of the adjusted column, so the overall table size adjusts properly

    let checked_rows = get_checked_rows(table_id);
    the_table = $('#' + table_id).DataTable(table_settings);
    if (checked_rows.length > 0){
      recheck_rows(the_table, checked_rows);
    }
  } else {
    the_table = $('#' + table_id).DataTable(table_settings);
    the_table.draw();
  }

  the_table.on( 'order.dt search.dt draw.dt', function () {
    the_table.column(1, {search:'applied', order:'applied'}).nodes().each( function (cell, i) {
    cell.innerHTML = i+1;
    } );
  } ).draw();


  if (first_run){
    $('#' + table_type.toLowerCase() + '_container').css("width", String($('#' + table_id).width() + 17) + "px");
  }

  $('#' + table_type.toLowerCase() + '_searchbox').on( 'keyup', function () {
    the_table.search($(this).val()).draw();
  } );

  $('.toggle-vis').on('click', function (e) {
    e.preventDefault();

    function toggle_column(column) {
        //ZS: Toggle column visibility
        column.visible( ! column.visible() );
        if (column.visible()){
            $(this).removeClass("active");
        } else {
            $(this).addClass("active");
        }
    }

    // Get the column API object
    var target_cols = $(this).attr('data-column').split(",")
    for (let i = 0; i < target_cols.length; i++){
        var column = the_table.column( target_cols[i] );
        toggle_column(column);
    }
  } );

}
