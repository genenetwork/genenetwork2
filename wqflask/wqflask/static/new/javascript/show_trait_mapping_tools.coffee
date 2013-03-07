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
        
    get_progress = ->
        console.log("temp_uuid:", $("#temp_uuid").val())
        temp_uuid = $("#temp_uuid").val()
        params = { key:temp_uuid }
        params_str = $.param(params)
        url = "/get_temp_data?" + params_str
        console.log("url:", url)
        $.ajax(
            type: "GET"
            url: url
            success: (progress_data) =>
                console.log("in get_progress data:", progress_data)
                console.log(progress_data['percent_complete'] + "%")
                $('#marker_regression_progress').css("width", progress_data['percent_complete'] + "%")
        )
        return false

    $("#marker_regression").click(() =>
        $("#progress_bar_container").modal()
        url = "/marker_regression"
        form_data = $('#trait_data_form').serialize()
        console.log("form_data is:", form_data)
        $.ajax(
            type: "POST"
            url: url
            data: form_data
            success: (data) =>
                clearInterval(this.my_timer)
                $('#progress_bar_container').modal('hide')
                $("body").html(data)
        )
        console.log("settingInterval")
        this.my_timer = setInterval(get_progress, 1000)
        return false
    )

    #$(".submit_special").click(submit_special)

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
    );