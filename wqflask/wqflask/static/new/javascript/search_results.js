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
                  }
              }
              i += 1
          });
      }
      else {
          $('#trait_table > tbody > tr').each(function(){
              $(this).closest('tr').removeClass('selected')
          });
      }
      change_buttons();
  });            

  $('.trait_checkbox:checkbox').change(function() {
      console.log("CHANGED")
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
    console.log("checked length is:", traits.length);
    console.log("checked is:", traits);
    return $.colorbox({
      href: "/collections/add?traits=" + traits
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
    console.log("num_checked is:", num_checked);
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

  remove = function() {
    var traits, uc_id;
    checked_traits = $("#trait_table input:checked");
    traits = checked_traits.map(function() {
      return $(this).val();
    }).get();
    console.log("checked length is:", traits.length);
    console.log("checked is:", traits);
    uc_id = $("#uc_id").val();
    console.log("uc.id is:", uc_id);
    return $.ajax({
      type: "POST",
      url: "/collections/remove",
      data: {
        uc_id: uc_id,
        traits: traits
      },
      success: removed_traits
    });
  };
  $("#select_all").click(select_all);
  $("#deselect_all").click(deselect_all);
  $("#invert").click(invert);
  $("#add").click(add);
  $("#remove").click(remove);
  $('.trait_checkbox, .btn').click(change_buttons);
});