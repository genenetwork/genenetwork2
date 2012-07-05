console.log("start_b")

isNumber = (o) ->
    return ! isNaN (o-0) && o != null

$ ->
    hide_tabs = (start) ->
        for x in [start..10]
            $("#stats_tabs" + x).hide()

    hide_tabs(1)


    # Changes stats table between all, bxd only and non-bxd, etc.
    stats_mdp_change = ->
        selected = $(this).val()
        hide_tabs(0)
        $("#stats_tabs" + selected).show()

    $(".stats_mdp").change(stats_mdp_change)


    mean = (the_values)->
        total = 0
        total += value for value in the_values
        the_mean = total / the_values.length
        the_mean = the_mean.toFixed(2)
        current_mean = parseFloat($("#mean_value").html).toFixed(2)
        if the_mean != current_mean
            $("#mean_value").html(the_mean).effect("highlight")

        n_of_samples = the_values.length
        current_n_of_samples = $("#n_of_samples_value").html()
        console.log("cnos:", current_n_of_samples)
        console.log("n_of_samples:", n_of_samples)
        if n_of_samples != current_n_of_samples
            $("#n_of_samples_value").html(current_n_of_samples).effect("highlight")



    edit_data_change = ->
        the_values = []
        values = $('#primary').find(".edit_strain_value")
        #console.log("values are:", values)
        for value in values
            real_value = $(value).val()
            #console.log("parent is:", $(value).closest("tr"))
            row = $(value).closest("tr")
            checkbox = $(row).find(".edit_strain_checkbox")
            checked = $(checkbox).attr('checked')
            if not checked
                console.log("Not checked")
                continue
            if isNumber(real_value) and real_value != ""
                the_values.push(parseFloat(real_value))
        mean(the_values)


    $('#primary').change(edit_data_change)
    console.log("loaded")
