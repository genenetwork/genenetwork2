change_buttons = function(check_node = 0) {
  var button, buttons, item, num_checked, text, _i, _j, _k, _l, _len, _len2, _len3, _len4, _results, _results2;
  buttons = ["#add", "#remove"];

  num_checked = 0
  table_api = $('#trait_table').DataTable();
  check_cells = table_api.column(0).nodes().to$();
  for (let i = 0; i < check_cells.length; i++) {
    if (check_cells[i].childNodes[check_node].checked){
      num_checked += 1
    }
  }

  if (num_checked === 0) {
    for (_i = 0, _len = buttons.length; _i < _len; _i++) {
      button = buttons[_i];
      $(button).prop("disabled", true);
    }
  } else {
    for (_j = 0, _len2 = buttons.length; _j < _len2; _j++) {
      button = buttons[_j];
      $(button).prop("disabled", false);
    }
  }
};

$(function() {
  let selectAll, deselectAll, invert;

  selectAll = function() {
    table_api = $('#trait_table').DataTable();

    check_cells = table_api.column(0).nodes().to$();
    for (let i = 0; i < check_cells.length; i++) {
      check_cells[i].childNodes[0].checked = true;
    }

    check_rows = table_api.rows().nodes();
    for (let i =0; i < check_rows.length; i++) {
      check_rows[i].classList.add("selected");
    }

    change_buttons();
  };

  deselectAll = function() {
    table_api = $('#trait_table').DataTable();

    check_cells = table_api.column(0).nodes().to$();
    for (let i = 0; i < check_cells.length; i++) {
      check_cells[i].childNodes[0].checked = false;
    }

    check_rows = table_api.rows().nodes();
    for (let i =0; i < check_rows.length; i++) {
      check_rows[i].classList.remove("selected")
    }

    change_buttons();
  };

  invert = function() {
    table_api = $('#trait_table').DataTable();

    check_cells = table_api.column(0).nodes().to$();
    for (let i = 0; i < check_cells.length; i++) {
      if (check_cells[i].childNodes[0].checked){
        check_cells[i].childNodes[0].checked = false;
      } else {
        check_cells[i].childNodes[0].checked = true;
      }
    }

    check_rows = table_api.rows().nodes();
    for (let i =0; i < check_rows.length; i++) {
      if (check_rows[i].classList.contains("selected")){
        check_rows[i].classList.remove("selected")
      } else {
        check_rows[i].classList.add("selected")
      }
    }

    change_buttons();
  };

  $('#searchbox').keyup(function(){
      if ($(this).val() != ""){
        $('#filter_term').val($(this).val());
      } else {
        $('#filter_term').val("None");
      }
      $('#trait_table').DataTable().search($(this).val()).draw();
  });

  /**
   * parseIndexString takes a string consisting of integers,
   * hyphens, and/or commas to indicate range(s) of indices
   * to select a rows and returns the corresponding set of indices
   * For example - "1, 5-10, 15" would return a set of 8 rows
   * @return {Set} The list of indices as a Set
   */
  parseIndexString = function(idx_string) {
    index_list = [];

    _ref = idx_string.split(",");
    for (_i = 0; _i < _ref.length; _i++) {
      index_set = _ref[_i];
      if (!/^ *([0-9]+$) *| *([0-9]+ *- *[0-9]+$) *|(^$)$/.test(index_set)) {
        $('#select_samples_invalid').show();
        break
      } else {
        $('#select_samples_invalid').hide();
      }
      if (index_set.indexOf('-') !== -1) {
          start_index = parseInt(index_set.split("-")[0]);
          end_index = parseInt(index_set.split("-")[1]);

          // If start index is higher than end index (for example is the string "10-5" exists) swap values so it'll be interpreted as "5-10" instead
          if (start_index > end_index) {
            [start_index, end_index] = [end_index, start_index]
          }

          for (index = start_index; index <= end_index; index++) {
            index_list.push(index);
          }
      } else {
        index = parseInt(index_set);
        index_list.push(index);
      }
    }
    return new Set(index_list)
  }

  filterByIndex = function() {
    indexString = $('#select_top').val()
    indexSet = parseIndexString(indexString)

    tableApi = $('#trait_table').DataTable();
    checkNodes = tableApi.column(0).nodes().to$();
    checkNodes.each(function(index) {
      if (indexSet.has(index + 1)){
        $(this)[0].childNodes[0].checked = true
      }
    })

    checkRows = tableApi.rows().nodes().to$();
    checkRows.each(function(index) {
      if (indexSet.has(index + 1)){
        $(this)[0].classList.add("selected");
      }
    })
  }

  $(window).keydown(function(event){
    if((event.keyCode == 13)) {
      event.preventDefault();
      return false;
    }
  });

  $('#select_top').keyup(function(event){
    if (event.keyCode === 13) {
      filterByIndex()
    }
  });

  $('#select_top').blur(function() {
    filterByIndex()
  });

  addToCollection = function() {
    var traits;
    table_api = $('#trait_table').DataTable();
    check_nodes = table_api.column(0).nodes().to$();
    traits = Array.from(check_nodes.map(function() {
      if ($(this)[0].childNodes[0].checked){
        return $(this)[0].childNodes[0].value
      }
    }))

    var traits_hash = md5(traits.toString());

    $.ajax({
          type: "POST",
          url: "/collections/store_trait_list",
          data: {
            hash: traits_hash,
            traits: traits.toString()
          }
    });

    return $.colorbox({
	href: "/collections/add",
	data: {
	    "traits": traits.toString(),
	    "hash": traits_hash
	}
    });

  };

  submitBnw = function() {
    trait_data = submitTraits("trait_table", "submit_bnw")
  }

  exportTraits = function() {
    trait_data = submitTraits("trait_table", "export_traits_csv")
  };

  exportCollection = function() {
    trait_data = submitTraits("trait_table", "export_collection")
  }

  fetchTraits = function(table_name){
    trait_table = $('#'+table_name);
    table_dict = {};

    headers = [];
    trait_table.find('th').each(function () {
      if ($(this).data('export')){
        headers.push($(this).data('export'))
      }
    });
    table_dict['headers'] = headers;

    selected_rows = [];
    all_rows = []; // If no rows are checked, export all
    table_api = $('#' + table_name).DataTable();
    check_cells = table_api.column(0).nodes().to$();
    for (let i = 0; i < check_cells.length; i++) {
      this_node = check_cells[i].childNodes[0];
      all_rows.push(this_node.value)
      if (this_node.checked){
        selected_rows.push(this_node.value)
      }
    }

    if (selected_rows.length > 0){
      table_dict['rows'] = selected_rows;
    } else {
      table_dict['rows'] = all_rows;
    }

    json_table_dict = JSON.stringify(table_dict);
    $('input[name=export_data]').val(json_table_dict);
  }

  submitTraits = function(table_name, destination) {
    fetchTraits(table_name);
    $('#export_form').attr('action', '/' + destination);
    $('#export_form').submit();
  };

  getTraitsFromTable = function(){
    traits = $("#trait_table input:checked").map(function() {
      return $(this).val();
    }).get();
    if (traits.length == 0){
      num_traits = $("#trait_table input").length
      if (num_traits <= 100){
        traits = $("#trait_table input").map(function() {
          return $(this).val();
        }).get();
      }
    }
    return traits
  }

  $("#corr_matrix").on("click", function() {
      traits = getTraitsFromTable()
      $("#trait_list").val(traits)
      $("input[name=tool_used]").val("Correlation Matrix")
      $("input[name=form_url]").val($(this).data("url"))
      return submit_special("/loading")
  });
  $("#network_graph").on("click", function() {
      traits = getTraitsFromTable()
      $("#trait_list").val(traits)
      $("input[name=tool_used]").val("Network Graph")
      $("input[name=form_url]").val($(this).data("url"))
      return submit_special("/loading")
  });
  $("#wgcna_setup").on("click", function() {
      traits = getTraitsFromTable()
      $("#trait_list").val(traits)
      $("input[name=tool_used]").val("WGCNA Setup")
      $("input[name=form_url]").val($(this).data("url"))
      return submit_special("/loading")
  });
  $("#ctl_setup").on("click", function() {
      traits = getTraitsFromTable()
      $("#trait_list").val(traits)
      $("input[name=tool_used]").val("CTL Setup")
      $("input[name=form_url]").val($(this).data("url"))
      return submit_special("/loading")
  });
  $("#heatmap").on("click", function() {
      traits = getTraitsFromTable()
      $("#trait_list").val(traits)
      $("input[name=tool_used]").val("Heatmap")
      $("input[name=form_url]").val($(this).data("url"))
      return submit_special("/loading")
  });
  $("#comp_bar_chart").on("click", function() {
      traits = getTraitsFromTable()
      $("#trait_list").val(traits)
      $("input[name=tool_used]").val("Comparison Bar Chart")
      $("input[name=form_url]").val($(this).data("url"))
      return submit_special("/loading")
  });

  $("#send_to_webgestalt, #send_to_bnw, #send_to_geneweaver").on("click", function() {
      traits = getTraitsFromTable()
      $("#trait_list").val(traits)
      url = $(this).data("url")
      return submit_special(url)
  });


  $("#select_all").click(selectAll);
  $("#deselect_all").click(deselectAll);
  $("#invert").click(invert);
  $("#add").click(addToCollection);
  $("#submit_bnw").click(submitBnw);
  $("#export_traits").click(exportTraits);
  $("#export_collection").click(exportCollection);

  let naturalAsc = $.fn.dataTableExt.oSort["natural-ci-asc"]
  let naturalDesc = $.fn.dataTableExt.oSort["natural-ci-desc"]

  let na_equivalent_vals = ["N/A", "--", ""]; //ZS: Since there are multiple values that should be treated the same as N/A

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

  applyDefault = function() {
    let default_collection_id = $.cookie('default_collection');
    if (default_collection_id) {
      let the_option = $('[name=existing_collection] option').filter(function() {
        return ($(this).text().split(":")[0] == default_collection_id);
      })
      the_option.prop('selected', true);
    }
  }
  applyDefault();

});
