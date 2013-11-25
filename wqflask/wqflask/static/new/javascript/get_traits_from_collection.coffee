
console.log("before get_traits_from_collection")


collection_hover = () ->
    console.log("Hovering over:", $(this))
    this_collection_url = $(this).find('.collection_name').prop("href")
    this_collection_url += "&json"
    console.log("this_collection_url", this_collection_url)

$ ->
    console.log("inside get_traits_from_collection")
    $(document).on("mouseover", ".collection_line", collection_hover)

   