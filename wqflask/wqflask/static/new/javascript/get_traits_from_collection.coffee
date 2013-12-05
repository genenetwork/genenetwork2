root = exports ? this

console.log("before get_traits_from_collection")

# Going to be used to hold collection list
# So we can repopulate it when the back button is clicked
collection_list = null
this_trait_data = null

collection_click = () ->
    console.log("Clicking on:", $(this))
    this_collection_url = $(this).find('.collection_name').prop("href")
    this_collection_url += "&json"
    console.log("this_collection_url", this_collection_url)
    collection_list = $("#collections_holder").html()
    $.ajax(
        dataType: "json",
        url: this_collection_url,
        success: process_traits
      )

trait_click = () ->
    console.log("Clicking on:", $(this))
    trait = $(this).find('.trait').text()
    dataset = $(this).find('.dataset').text()
    this_trait_url = "/trait/get_sample_data?trait="+trait+"&dataset="+dataset
    console.log("this_trait_url", this_trait_url)
    $.ajax(
        dataType: "json",
        url: this_trait_url,
        success: color_by_trait
      )

color_by_trait =  (trait_sample_data, textStatus, jqXHR) ->
    root.trait_sample_data = trait_sample_data
    #console.log('in color_by_trait:', trait_sample_data)
    

process_traits = (trait_data, textStatus, jqXHR) ->
    console.log('in process_traits with trait_data:', trait_data)
    
    the_html = "<button id='back_to_collections' class='btn btn-inverse btn-small'>"
    the_html += "<i class='icon-white icon-arrow-left'></i> Back </button>"
    
    the_html += "<table class='table table-hover'>"
    the_html += "<thead><tr><th>Record</th><th>Data Set</th><th>Description</th><th>Mean</th></tr></thead>"
    the_html += "<tbody>"
    for trait in trait_data
        the_html += "<tr class='trait_line'><td class='trait'>#{ trait.name }</td>"
        the_html += "<td class='dataset'>#{ trait.dataset }</td>"
        the_html += "<td>#{ trait.description }</td>"
        the_html += "<td>#{ trait.mean or '&nbsp;' }</td></tr>"
    the_html += "</tbody>"
    the_html += "</table>"

    $("#collections_holder").html(the_html)
    $('#collections_holder').colorbox.resize()

back_to_collections = () ->
    console.log("collection_list:", collection_list)
    $("#collections_holder").html(collection_list)
    
    $(document).on("click", ".collection_line", collection_click)
    $('#collections_holder').colorbox.resize()

$ ->
    console.log("inside get_traits_from_collection")
    
    $(document).on("click", ".collection_line", collection_click)
    $(document).on("click", ".trait_line", trait_click)
    $(document).on("click", "#back_to_collections", back_to_collections)
    
