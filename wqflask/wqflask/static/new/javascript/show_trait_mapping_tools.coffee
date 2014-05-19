# http://stackoverflow.com/a/4215132/1175849
root = exports ? this

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

    update_time_remaining = (percent_complete) ->
        now = new Date()
        period = now.getTime() - root.start_time
        console.log("period is:", period)
        if period > 8000
            total_seconds_remaining = (period / percent_complete * (100 - percent_complete))/1000
            minutes_remaining = Math.round(total_seconds_remaining / 60)
            #seconds_remaining = Math.round(total_seconds_remaining % 60)
            #console.log("seconds_remaining:", seconds_remaining)
            if minutes_remaining < 3
                $('#time_remaining').text(Math.round(total_seconds_remaining) + " seconds remaining")
            else
                $('#time_remaining').text(minutes_remaining + " minutes remaining")

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
                percent_complete = progress_data['percent_complete']
                console.log("in get_progress data:", progress_data)

                $('#marker_regression_progress').css("width", percent_complete + "%")
                
                if root.start_time
                    unless isNaN(percent_complete)
                        update_time_remaining(percent_complete)
                else
                    root.start_time = new Date().getTime()
        )
        return false

    $("#interval_mapping_compute").click(() =>
        console.log("In interval mapping")
        $("#progress_bar_container").modal()
        url = "/interval_mapping"
        $('input[name=method]').val("reaper")
        $('input[name=mapping_display_all]').val($('input[name=display_all_reaper]'))
        $('input[name=suggestive]').val($('input[name=suggestive_reaper]'))
        form_data = $('#trait_data_form').serialize()
        console.log("form_data is:", form_data)
        $.ajax(
            type: "POST"
            url: url
            data: form_data
            error: (xhr, ajaxOptions, thrownError) =>
                alert("Sorry, an error occurred")
                console.log(xhr)
                clearInterval(this.my_timer)
                $('#progress_bar_container').modal('hide')
                $("body").html("We got an error.")        
            success: (data) =>
                clearInterval(this.my_timer)
                $('#progress_bar_container').modal('hide')
                $("body").html(data)
        )
        console.log("settingInterval")

        this.my_timer = setInterval(get_progress, 1000)
        return false
    )

    $('#suggestive').hide()

    $('input[name=display_all]').change(() =>
        console.log("check")
        if $('input[name=display_all]:checked').val() == "False"
            $('#suggestive').show()
        else
            $('#suggestive').hide()
    )

    $("#marker_regression_compute").click(() =>
        $("#progress_bar_container").modal()
        url = "/marker_regression"
        $('input[name=method]').val("pylmm")
        form_data = $('#trait_data_form').serialize()
        console.log("form_data is:", form_data)
        $.ajax(
            type: "POST"
            url: url
            data: form_data
            error: (xhr, ajaxOptions, thrownError) =>
                alert("Sorry, an error occurred")
                console.log(xhr)
                clearInterval(this.my_timer)
                $('#progress_bar_container').modal('hide')
                $("body").html("We got an error.")        
            success: (data) =>
                clearInterval(this.my_timer)
                $('#progress_bar_container').modal('hide')
                $("body").html(data)
        )
        console.log("settingInterval")

        this.my_timer = setInterval(get_progress, 1000)
        return false
    )

    $("#plink_compute").click(() =>
        url = "/marker_regression"
        $('input[name=method]').val("plink")
        $('input[name=mapping_display_all]').val($('input[name=display_all_plink]'))
        $('input[name=suggestive]').val($('input[name=suggestive_plink]'))
        $('input[name=maf]').val($('input[name=maf_plink]'))
        form_data = $('#trait_data_form').serialize()
        console.log("form_data is:", form_data)
        $.ajax(
            type: "POST"
            url: url
            data: form_data
            error: (xhr, ajaxOptions, thrownError) =>
                alert("Sorry, an error occurred")
                console.log(xhr)
                clearInterval(this.my_timer)
                $('#progress_bar_container').modal('hide')
                $("body").html("We got an error.")        
            success: (data) =>
                clearInterval(this.my_timer)
                $('#progress_bar_container').modal('hide')
                $("body").html(data)
        )
        console.log("settingInterval")

        this.my_timer = setInterval(get_progress, 1000)
        return false
    )

    $("#gemma_compute").click(() =>
        url = "/marker_regression"
        $('input[name=method]').val("gemma")
        $('input[name=mapping_display_all]').val($('input[name=display_all_gemma]'))
        $('input[name=suggestive]').val($('input[name=suggestive_gemma]'))
        $('input[name=maf]').val($('input[name=maf_gemma]'))
        form_data = $('#trait_data_form').serialize()
        console.log("form_data is:", form_data)
        $.ajax(
            type: "POST"
            url: url
            data: form_data
            error: (xhr, ajaxOptions, thrownError) =>
                alert("Sorry, an error occurred")
                console.log(xhr)
                clearInterval(this.my_timer)
                $('#progress_bar_container').modal('hide')
                $("body").html("We got an error.")        
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
    mapping_method_fields = ->
        $(".mapping_method_fields").toggle()
        

    $("#use_composite_choice").change(composite_mapping_fields)
    $("#mapping_method_choice").change(mapping_method_fields)


    #### Todo: Redo below so its like submit_special and requires no js hardcoding
    toggle_enable_disable = (elem) ->
        $(elem).prop("disabled", !$(elem).prop("disabled"))
    
    $("#choose_closet_control").change(->
        toggle_enable_disable("#control_locus")
    )
    
    $("#display_all_lrs").change(->
        toggle_enable_disable("#suggestive_lrs")
    );