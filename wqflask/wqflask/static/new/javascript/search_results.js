$(function() {
  var add, change_buttons, checked_traits, deselect_all, invert, remove, removed_traits, select_all;

  checked_traits = null;
  select_all = function() {
    console.log("selected_all");
    $(".trait_checkbox").each(function() {
        $(this).prop('checked', true);
        if (!$(this).closest('tr').hasClass('selected')) {
            $(this).closest('tr').addClass('selected')
        }
    });
  };

  deselect_all = function() {
    $(".trait_checkbox").each(function() {
        $(this).prop('checked', false);
        if ($(this).closest('tr').hasClass('selected')) {
            $(this).closest('tr').removeClass('selected')
        }
    });
  };

  invert = function() {
    $(".trait_checkbox").each(function() {
        if ($(this).prop('checked') == true) {
            $(this).prop('checked', false)
        }
        else {
            $(this).prop('checked', true)
        }

        if ($(this).closest('tr').hasClass('selected')) {
            $(this).closest('tr').removeClass('selected')
        }
        else {
            $(this).closest('tr').addClass('selected')
        }
    });
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

  $('.trait_checkbox:checkbox').change(function() {
      change_buttons()

      if ($(this).is(":checked")) {
          if (!$(this).closest('tr').hasClass('selected')) {
              $(this).closest('tr').addClass('selected')
          }
      }
      else {
          if ($(this).closest('tr').hasClass('selected')) {
              $(this).closest('tr').removeClass('selected')
          }
      }

  });

  add = function() {
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
    console.log('in removed_traits with checked_traits:', checked_traits);
    return checked_traits.closest("tr").fadeOut();
  };
  change_buttons = function() {
    var button, buttons, item, num_checked, text, _i, _j, _k, _l, _len, _len2, _len3, _len4, _results, _results2;
    buttons = ["#add", "#remove"];
    num_checked = $('.trait_checkbox:checked').length;
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

  submit_bnw = function() {
    trait_data = get_traits_from_table("trait_table", "submit_bnw")
  }

  export_traits = function() {
    trait_data = get_traits_from_table("trait_table", "export_csv")
  };

  get_traits_from_table = function(table_name, destination) {
    trait_table = $('#'+table_name);
    table_dict = {};

    headers = [];
    trait_table.find('th').each(function () {
      if ($(this).data('export')){
        headers.push($(this).data('export'))
      }
    });
    table_dict['headers'] = headers;

    rows = [];
    trait_table.find('tbody tr').each(function (i, tr) {
      if (trait_table.find('input[name="searchResult"]:checked').length > 0) {
        if ($(this).find('input[name="searchResult"]').is(':checked')){
          rows.push($(this).find('input[name="searchResult"]:checked').val())
        }
      }
      else {
        rows.push($(this).find('input[name="searchResult"]').val())
      }
    });
    table_dict['rows'] = rows;

    json_table_dict = JSON.stringify(table_dict);
    $('input[name=export_data]').val(json_table_dict);

    if (destination == "export_csv"){
        $('#export_form').attr('action', '/export_traits_csv');
    } else{
        $('#export_form').attr('action', '/submit_bnw');
    }
    $('#export_form').submit();
  };

  $("#corr_matrix").on("click", function() {
      traits = $("#trait_table input:checked").map(function() {
          return $(this).val();
      }).get();
      $("#trait_list").val(traits)
      $("input[name=tool_used]").val("Correlation Matrix")
      $("input[name=form_url]").val($(this).data("url"))
      return submit_special("/loading")
  });
  $("#network_graph").on("click", function() {
      traits = $("#trait_table input:checked").map(function() {
         return $(this).val();
      }).get();
      $("#trait_list").val(traits)
      $("input[name=tool_used]").val("Network Graph")
      $("input[name=form_url]").val($(this).data("url"))
      return submit_special("/loading")
  });
  $("#wgcna_setup").on("click", function() {
      traits = $("#trait_table input:checked").map(function() {
          return $(this).val();
      }).get();
      $("#trait_list").val(traits)
      $("input[name=tool_used]").val("WGCNA Setup")
      $("input[name=form_url]").val($(this).data("url"))
      return submit_special("/loading")
  });
  $("#ctl_setup").on("click", function() {
      traits = $("#trait_table input:checked").map(function() {
          return $(this).val();
      }).get();
      $("#trait_list").val(traits)
      $("input[name=tool_used]").val("CTL Setup")
      $("input[name=form_url]").val($(this).data("url"))
      return submit_special("/loading")
  });
  $("#heatmap").on("click", function() {
      traits = $("#trait_table input:checked").map(function() {
          return $(this).val();
      }).get();
      $("#trait_list").val(traits)
      $("input[name=tool_used]").val("Heatmap")
      $("input[name=form_url]").val($(this).data("url"))
      return submit_special("/loading")
  });
  $("#comp_bar_chart").on("click", function() {
      traits = $("#trait_table input:checked").map(function() {
          return $(this).val();
      }).get();
      $("#trait_list").val(traits)
      $("input[name=tool_used]").val("Comparison Bar Chart")
      $("input[name=form_url]").val($(this).data("url"))
      return submit_special("/loading")
  });

  $("#send_to_webgestalt, #send_to_bnw, #send_to_geneweaver").on("click", function() {
      traits = $("#trait_table input:checked").map(function() {
          return $(this).val();
      }).get();
      $("#trait_list").val(traits)
      url = $(this).data("url")
      return submit_special(url)
  });


  $("#select_all").click(select_all);
  $("#deselect_all").click(deselect_all);
  $("#invert").click(invert);
  $("#add").click(add);
  $("#submit_bnw").click(submit_bnw);
  $("#export_traits").click(export_traits);
  $('.trait_checkbox, .btn').click(change_buttons);
});