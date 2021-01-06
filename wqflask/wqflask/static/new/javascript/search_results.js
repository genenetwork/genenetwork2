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
  var add, checked_traits, deselect_all, invert, remove, removed_traits, select_all;

  checked_traits = null;
  select_all = function() {
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

  deselect_all = function() {
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

  $('#select_top').keyup(function(){
      num_rows = $(this).val()
      if (num_rows = parseInt(num_rows)){
          i = 0
          $('#trait_table > tbody > tr').each(function(){
              if (i < num_rows) {
                  $(this).find('.trait_checkbox').prop("checked", true)
                  if (!$(this).closest('tr').hasClass('selected')) {
                      $(this).closest('tr').addClass('selected')
                  }
              }
              else {
                  if ($(this).closest('tr').hasClass('selected')) {
                      $(this).closest('tr').removeClass('selected')
                      $(this).find('.trait_checkbox').prop("checked", false)
                  }
              }
              i += 1
          });
      }
      else {
          $('#trait_table > tbody > tr').each(function(){
              $(this).closest('tr').removeClass('selected')
              $(this).find('.trait_checkbox').prop("checked", false)
          });
      }
      change_buttons();
  });

  add_to_collection = function() {
    var traits;
    traits = $("#trait_table input:checked").map(function() {
      return $(this).val();
    }).get();

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
      href: "/collections/add?hash=" + traits_hash
    });

  };

  removed_traits = function() {
    return checked_traits.closest("tr").fadeOut();
  };

  submit_bnw = function() {
    trait_data = submit_traits_to_export_or_bnw("trait_table", "submit_bnw")
  }

  export_traits = function() {
    trait_data = submit_traits_to_export_or_bnw("trait_table", "export_csv")
  };

  submit_traits_to_export_or_bnw = function(table_name, destination) {
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
    all_rows = []; //ZS: If no rows are checked, export all
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

    if (destination == "export_csv"){
        $('#export_form').attr('action', '/export_traits_csv');
    } else{
        $('#export_form').attr('action', '/submit_bnw');
    }
    $('#export_form').submit();
  };

  get_traits_from_table = function(){
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
      traits = get_traits_from_table()
      $("#trait_list").val(traits)
      $("input[name=tool_used]").val("Correlation Matrix")
      $("input[name=form_url]").val($(this).data("url"))
      return submit_special("/loading")
  });
  $("#network_graph").on("click", function() {
      traits = get_traits_from_table()
      $("#trait_list").val(traits)
      $("input[name=tool_used]").val("Network Graph")
      $("input[name=form_url]").val($(this).data("url"))
      return submit_special("/loading")
  });
  $("#wgcna_setup").on("click", function() {
      traits = get_traits_from_table()
      $("#trait_list").val(traits)
      $("input[name=tool_used]").val("WGCNA Setup")
      $("input[name=form_url]").val($(this).data("url"))
      return submit_special("/loading")
  });
  $("#ctl_setup").on("click", function() {
      traits = get_traits_from_table()
      $("#trait_list").val(traits)
      $("input[name=tool_used]").val("CTL Setup")
      $("input[name=form_url]").val($(this).data("url"))
      return submit_special("/loading")
  });
  $("#heatmap").on("click", function() {
      traits = get_traits_from_table()
      $("#trait_list").val(traits)
      $("input[name=tool_used]").val("Heatmap")
      $("input[name=form_url]").val($(this).data("url"))
      return submit_special("/loading")
  });
  $("#comp_bar_chart").on("click", function() {
      traits = get_traits_from_table()
      $("#trait_list").val(traits)
      $("input[name=tool_used]").val("Comparison Bar Chart")
      $("input[name=form_url]").val($(this).data("url"))
      return submit_special("/loading")
  });

  $("#send_to_webgestalt, #send_to_bnw, #send_to_geneweaver").on("click", function() {
      traits = get_traits_from_table()
      $("#trait_list").val(traits)
      url = $(this).data("url")
      return submit_special(url)
  });


  $("#select_all").click(select_all);
  $("#deselect_all").click(deselect_all);
  $("#invert").click(invert);
  $("#add").click(add_to_collection);
  $("#submit_bnw").click(submit_bnw);
  $("#export_traits").click(export_traits);

  let naturalAsc = $.fn.dataTableExt.oSort["natural-ci-asc"]
  let naturalDesc = $.fn.dataTableExt.oSort["natural-ci-desc"]

  let na_equivalent_vals = ["N/A", "--", ""]; //ZS: Since there are multiple values that should be treated the same as N/A

  function extract_inner_text(the_string){
    var span = document.createElement('span');
    span.innerHTML = the_string;
    return span.textContent || span.innerText;
  }

  function sort_NAs(a, b, sort_function){
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
      return sort_NAs(extract_inner_text(a), extract_inner_text(b), naturalAsc)
    },
    "natural-minus-na-desc": function (a, b) {
      return sort_NAs(extract_inner_text(a), extract_inner_text(b), naturalDesc)
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

});