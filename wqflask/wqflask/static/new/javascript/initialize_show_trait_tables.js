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
      'render': function(data, type, row, meta) {
      return '<input type="checkbox" name="searchResult" class="checkbox edit_sample_checkbox" value="">'
      }
    },
    {
      'title': "ID",
      'type': "natural",
      'searchable' : false,
      'data': "this_id"
    },
    {
      'title': "Sample",
      'type': "natural",
      'data': null,
      'render': function(data, type, row, meta) {
      return '<span class="edit_sample_sample_name">' + data.name + '</span>'
      }
    },
    {
      'title': "<div style='text-align: right;'>Value</div>",
      'orderDataType': "dom-input",
      'type': "cust-txt",
      'data': null,
      'render': function(data, type, row, meta) {
        if (data.value == null) {
            return '<input type="text" data-value="x" data-qnorm="x" data-zscore="x" name="value:' + data.name + '" style="text-align: right;" class="trait_value_input edit_sample_value" value="x" size=6 maxlength=6>'
        } else {
            return '<input type="text" data-value="' + data.value.toFixed(3) + '" data-qnorm="' + js_data['qnorm_values'][0][parseInt(data.this_id) - 1] + '" data-zscore="' + js_data['zscore_values'][0][parseInt(data.this_id) - 1] + '" name="value:' + data.name + '" class="trait_value_input edit_sample_value" value="' + data.value.toFixed(3) + '" size=6 maxlength=6>'
        }
      }
    }
  ];

  if (js_data.se_exists) {
    column_list.push(
      {
        'bSortable': false,
        'type': "natural",
        'data': null,
        'searchable' : false,
        'render': function(data, type, row, meta) {
        return '±'
        }
      },
      {
        'title': "<div style='text-align: right;'>SE</div>",
        'orderDataType': "dom-input",
        'type': "cust-txt",
        'data': null,
        'render': function(data, type, row, meta) {
          if (data.variance == null) {
              return '<input type="text" data-value="x" data-qnorm="x" data-zscore="x" name="value:' + data.name + '" class="trait_value_input edit_sample_se" value="x" size=6 maxlength=6>'
          } else {
              return '<input type="text" data-value="' + data.variance.toFixed(3) + '" data-qnorm="x" data-zscore="x" name="value:' + data.name + '" class="trait_value_input edit_sample_se" value="' + data.variance.toFixed(3) + '" size=6 maxlength=6>'
          }
        }
      }
    );
  }

  if (js_data.has_num_cases === true) {
    column_list.push(
      {
        'title': "<div style='text-align: right;'>N</div>",
        'orderDataType': "dom-input",
        'type': "cust-txt",
        'data': null,
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

  attr_keys = Object.keys(js_data.attributes).sort((a, b) => (js_data.attributes[a].name > js_data.attributes[b].name) ? 1 : -1)
  for (i = 0; i < attr_keys.length; i++){
    column_list.push(
      {
        'title': "<div style='text-align: " + js_data.attributes[attr_keys[i]].alignment + "'>" + js_data.attributes[attr_keys[i]].name + "</div>",
        'type': "natural",
        'data': null,
        'render': function(data, type, row, meta) {
          attr_name = Object.keys(data.extra_attributes).sort()[meta.col - data.first_attr_col]

          if (attr_name != null && attr_name != undefined){
              return data.extra_attributes[attr_name]
          } else {
              return ""
          }
        }
      }
    )
  }
  return column_list
}

var primary_table = $('#samples_primary').DataTable( {
    'initComplete': function(settings, json) {
    $('.edit_sample_value').change(function() {
        edit_data_change();
    });
    },
    'createdRow': function ( row, data, index ) {
      $(row).attr('id', "Primary_" + data.this_id)
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
        $('td', row).eq(attribute_start_pos + i).addClass("column_name-" + js_data.attributes[attr_keys[i]].name)
        $('td', row).eq(attribute_start_pos + i).attr("style", "text-align: " + js_data.attributes[attr_keys[i]].alignment + "; padding-top: 2px; padding-bottom: 0px;")
      }
    },
    'data': js_data['sample_lists'][0],
    'columns': build_columns(),
    'order': [[1, "asc"]],
    'sDom': "Ztr",
    'autoWidth': true,
    'orderClasses': true,
    "scrollY": "50vh",
    'scroller':  true,
    'scrollCollapse': true
} );

primary_table.on( 'order.dt search.dt draw.dt', function () {
    primary_table.column(1, {search:'applied', order:'applied'}).nodes().each( function (cell, i) {
    cell.innerHTML = i+1;
    } );
} ).draw();

$('#primary_searchbox').on( 'keyup', function () {
    primary_table.search($(this).val()).draw();
} );

if (js_data.sample_lists.length > 1){
  var other_table = $('#samples_other').DataTable( {
      'initComplete': function(settings, json) {
      $('.edit_sample_value').change(function() {
          edit_data_change();
      });
      },
      'createdRow': function ( row, data, index ) {
        $(row).attr('id', "Primary_" + data.this_id)
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
      'data': js_data['sample_lists'][1],
      'columns': build_columns(),
      'order': [[1, "asc"]],
      'sDom': "Ztr",
      'autoWidth': true,
      'orderClasses': true,
      "scrollY": "50vh",
      'scroller':  true,
      'scrollCollapse': true
  } );
}