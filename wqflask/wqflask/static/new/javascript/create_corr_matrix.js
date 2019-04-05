var neg_color_scale = chroma.scale(['#FF0000', '#FFFFFF']).domain([-1, -0.4]);
var pos_color_scale = chroma.scale(['#FFFFFF', '#00FFFF']).domain([0.4, 1])
$('.corr_cell').each( function () {
  corr_value = parseFloat($(this).find('span.corr_value').text())
  if (corr_value >= 0.5){
    $(this).css('background-color', pos_color_scale(parseFloat(corr_value))._rgb)
  }
  else if (corr_value <= -0.5) {
    $(this).css('background-color', neg_color_scale(parseFloat(corr_value))._rgb)
  }
  else {
    $(this).css('background-color', 'white')
  }
});

$('#short_labels').click( function (){
  $('.shortName').each( function() {
    if ($(this).css("display") == "none"){
      $(this).css("display", "block");
    }
    else {
      $(this).css("display", "none");
    }
  });
});

$('#long_labels').click( function (){
  $('.verboseName').each( function() {
    if ($(this).css("display") == "none"){
      $(this).css("display", "block");
    }
    else {
      $(this).css("display", "none");
    }
  });
});

select_all = function() {
  $(".trait_checkbox").each(function() {
      $(this).prop('checked', true);
  });
};

deselect_all = function() {
  $(".trait_checkbox").each(function() {
      $(this).prop('checked', false);
  });
};

change_buttons = function() {
  num_checked = $('.trait_checkbox:checked').length;
  if (num_checked === 0) {
    $("#add").prop("disabled", true);
  } else {
    $("#add").prop("disabled", false);
  }
};

add = function() {
  var traits;
  traits = $("input[name=pca_trait]:checked").map(function() {
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
}

$("#select_all").click(select_all);
$("#deselect_all").click(deselect_all);
$("#add").click(add);
$(".btn, .trait_checkbox").click(change_buttons);
