function selected_traits() {
    traits = $("#trait_table input:checked").map(function() {
      return $(this).attr("data-trait-info");
    }).get();
    if (traits.length == 0){
      num_traits = $("#trait_table input").length
      if (num_traits <= 100){
        traits = $("#trait_table input").map(function() {
          return $(this).attr("data-trait-info");
        }).get();
      }
    }
    return traits
}

$("#partial-correlations").on("click", function() {
    // Submit the form to the `partial_correlations` endpoint
    url = $(this).data("url")
    traits = selected_traits();
    $("#trait_list").val(traits.reduce(function(acc, str) {
	return acc.concat(";;;".concat(str));
    }));
    $("input[name=tool_used]").val("Partial Correlation")
    $("input[name=form_url]").val(url)
    return submit_special(url)
})
