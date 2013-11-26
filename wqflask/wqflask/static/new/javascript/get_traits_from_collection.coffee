
console.log("before get_traits_from_collection")


collection_hover = () ->
    console.log("Hovering over:", $(this))
    this_collection_url = $(this).find('.collection_name').prop("href")
    this_collection_url += "&json"
    console.log("this_collection_url", this_collection_url)
    $.ajax(
        dataType: "json",
        url: this_collection_url,
        success: process_traits
      )

process_traits = (trait_data, textStatus, jqXHR) ->
    console.log('in process_traits with trait_data:', trait_data)
    html = "<table>"


$ ->
    console.log("inside get_traits_from_collection")
    $(document).on("mouseover", ".collection_line", collection_hover)
