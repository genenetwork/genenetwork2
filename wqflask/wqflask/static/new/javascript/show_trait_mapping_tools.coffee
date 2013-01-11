$ ->
    submit_special = ->
        # Add submit_special class plus a data-url field to any button
        # And it will submit to that url
        # No js changes necessary
        console.log("In submit_special")
        console.log("this is:", this)
        console.log("$(this) is:", $(this))
        url = $(this).data("url")
        console.log("url is:", url)
        $("#trait_data_form").attr("action", url);
        $("#trait_data_form").submit()
        
    $(".submit_special").click(submit_special)


    composite_mapping_fields = ->
        $(".composite_fields").toggle()

    $("#use_composite_choice").change(composite_mapping_fields)


    #### Todo: Redo below so its like submit_special and requires no js hardcoding
    toggle_enable_disable = (elem) ->
        $(elem).prop("disabled", !$(elem).prop("disabled"))
    
    $("#choose_closet_control").change(->
        toggle_enable_disable("#control_locus")
    )
    
    $("#display_all_lrs").change(->
        toggle_enable_disable("#suggestive_lrs")
    )