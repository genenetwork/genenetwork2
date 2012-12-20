$ ->
    run_marker_regression = ->
        console.log("In marker regression")
        url = "/marker_regression"
        $("#trait_data_form").attr("action", url);
        $("#trait_data_form").submit()
        
    $("#do_marker_regression").click(run_marker_regression)


    composite_mapping_fields = ->
        $(".composite_fields").toggle()

    $("#use_composite_choice").change(composite_mapping_fields)


    toggle_enable_disable = (elem) ->
        $(elem).prop("disabled", !$(elem.prop("disabled")))
    

    $("#choose_closet_control").change(->
        toggle_enable_disable("#control_locus")
    )
    
    $("#display_all_lrs").change(->
        toggle_enable_disable("#suggestive_lrs")
    )