console.log("before get_traits_from_collection")

# Going to be used to hold collection list
# So we can repopulate it when the back button is clicked
collection_list = null
this_trait_data = null

selected_traits = {}

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

submit_click = () ->
    
    selected_traits = {}
    
    traits = []
    $('#collections_holder').find('input[type=checkbox]:checked').each ->
        this_trait = $(@).parents('tr').find('.trait').text()
        console.log("this_trait is:", this_trait)
        this_dataset = $(@).parents('tr').find('.dataset').text()
        console.log("this_dataset is:", this_dataset)
        this_trait_url = "/trait/get_sample_data?trait="+this_trait+"&dataset="+this_dataset
        $.ajax(
            dataType: "json",
            url: this_trait_url,
            async: false,
            success: add_trait_data
        )
    
    console.log("SELECTED_TRAITS IS:", selected_traits)
    
    trait_names = []
    samples = $('input[name=allsamples]').val().split(" ")
    all_vals = []
    
    this_trait_vals = get_this_trait_vals(samples)
    all_vals.push(this_trait_vals)
    
    for trait in Object.keys(selected_traits)
        trait_names.push(trait)
        
        this_trait_vals = []
        for sample in samples
            if sample in Object.keys(selected_traits[trait])
                this_trait_vals.push(parseFloat(selected_traits[trait][sample]))
            else
                this_trait_vals.push(null)
        all_vals.push(this_trait_vals)
    
    create_scatterplots(trait_names, samples, all_vals)
    
    $.colorbox.close()

trait_click = () ->
    console.log("Clicking on:", $(this))
    trait = $(this).parent().find('.trait').text()
    dataset = $(this).parent().find('.dataset').text()
    this_trait_url = "/trait/get_sample_data?trait="+trait+"&dataset="+dataset
    console.log("this_trait_url", this_trait_url)
    $.ajax(
        dataType: "json",
        url: this_trait_url,
        success: get_trait_data
      )
    $.colorbox.close()
    
add_trait_data = (trait_data, textStatus, jqXHR) ->
    trait_name = trait_data[0]
    trait_sample_data = trait_data[1]
    selected_traits[trait_name] = trait_sample_data
    console.log("selected_traits:", selected_traits)

get_trait_data = (trait_data, textStatus, jqXHR) ->
    #trait_list = $('input[name=compare_traits]')
    #console.log("trait_list:", trait_list.val())
    console.log("trait:", trait_data[0])
    trait_sample_data = trait_data[1]
    console.log("trait_sample_data:", trait_sample_data)
    samples = $('input[name=allsamples]').val().split(" ")
    vals = []
    
    for sample in samples
        if sample in Object.keys(trait_sample_data)
            vals.push(parseFloat(trait_sample_data[sample]))
        else
            vals.push(null)

    #console.log("sorted_samples:", samples)
    #console.log("sorted_vals:", vals)
    
    if $('input[name=samples]').length < 1
        $('#hidden_inputs').append('<input type="hidden" name="samples" value="[' + samples.toString() + ']" />')
    $('#hidden_inputs').append('<input type="hidden" name="vals" value="[' + vals.toString() + ']" />')

    this_trait_vals = get_this_trait_vals(samples)

    #json_data = assemble_into_json(this_trait_vals_json)
    
    #console.log("json_data[1]:", json_data[1])
    
    console.log("THE LENGTH IS:", $('input[name=vals]').length)
    if $('input[name=vals]').length == 1
        create_scatterplot(samples, [this_trait_vals, vals])


get_this_trait_vals = (samples) ->
    this_trait_vals = []
    for sample in samples
        this_val = parseFloat($("input[name='value:"+sample+"']").val())
        if !isNaN(this_val)
            this_trait_vals.push(this_val)
        else
            this_trait_vals.push(null)
    console.log("this_trait_vals:", this_trait_vals)
    
    this_vals_json = '[' + this_trait_vals.toString() + ']'
        
    return this_trait_vals

assemble_into_json = (this_trait_vals) ->
    num_traits = $('input[name=vals]').length
    samples = $('input[name=samples]').val()
    json_ids = samples
    
    json_data = '[' + this_trait_vals

    $('input[name=vals]').each (index, element) =>
        json_data += ',' + $(element).val()
    json_data += ']'

    return [json_ids, json_data]

color_by_trait =  (trait_sample_data, textStatus, jqXHR) ->
    #trait_sample_data = trait_sample_data
    #console.log('in color_by_trait:', trait_sample_data)
    root.bar_chart.color_by_trait(trait_sample_data)

process_traits = (trait_data, textStatus, jqXHR) ->
    console.log('in process_traits with trait_data:', trait_data)
    
    the_html = "<button id='back_to_collections' class='btn btn-inverse btn-small'>"
    the_html += "<i class='icon-white icon-arrow-left'></i> Back </button>"
    the_html += "    <button id='submit' class='btn btn-primary btn-small'> Submit </button>"
    
    the_html += "<table class='table table-hover'>"
    the_html += "<thead><tr><th></th><th>Record</th><th>Data Set</th><th>Description</th><th>Mean</th></tr></thead>"
    the_html += "<tbody>"
    for trait in trait_data
        the_html += "<tr class='trait_line'>"
        the_html += "<td class='select_trait'><input type='checkbox' name='selectCheck' class='checkbox edit_sample_checkbox'></td>"
        the_html += "<td class='trait'>#{ trait.name }</td>"
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
    $(document).on("click", "#submit", submit_click)
    $(document).on("click", ".trait", trait_click)
    $(document).on("click", "#back_to_collections", back_to_collections)
    
