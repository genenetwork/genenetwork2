console.log("start_b")

# this is our isNumber, do not confuse with the underscore.js one
is_number = (o) ->
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

    change_stats_value = (category, value_type, the_value)->
        id = "#" + process_id(category, value_type)
        in_box = $(id).html
        
        current_value = parseFloat($(in_box)).toFixed(2)
        
        if the_value != current_value
            $(id).html(the_value).effect("highlight")

    update_stat_values = (sample_sets)->
        for category in ['primary_only', 'other_only', 'all_cases']

            # Number of samples
            n_of_samples = sample_sets[category].n_of_samples()
            id = "#" + process_id(category, "n_of_samples")
            current_n_of_samples = $(id).html()
            if n_of_samples != current_n_of_samples
                $(id).html(n_of_samples).effect("highlight")

            # Mean
            #id = "#" + process_id(category, "mean")

            the_mean = sample_sets[category].mean()
            the_mean = the_mean.toFixed(2)
            change_stats_value(category, "mean", the_mean)
            #in_box = $(id).html
            
            #current_mean = parseFloat($(in_box)).toFixed(2)

            #if the_mean != current_mean
            #    $(id).html(the_mean).effect("highlight")            
            
            # Median
            id = "#" + process_id(category, "median")
            the_median = sample_sets[category].median()
            the_median = the_median.toFixed(2)
            in_box = $(id).html

            current_median = parseFloat($(in_box)).toFixed(2)

            if the_median != current_median
                $(id).html(the_median).effect("highlight")

            # Todo: Compare stat values to genenetwork.org current code / sample vs. population
            # Standard deviation
            sum = 0
            for value in sample_sets[category]
                step_a = Math.pow(value - the_mean, 2)
                sum += step_a
            step_b = sum / sample_sets[category].length
            sd = Math.sqrt(step_b)
            sd = sd.toFixed(2)
            
            id = "#" + process_id(category, "sd")
            current_sd = $(id).html()
            if sd != current_sd
                $(id).html(sd).effect("highlight")
            

    edit_data_change = ->                
        sample_sets =
            primary_only: new Stats([])
            other_only: new Stats([])
            all_cases: new Stats([])
                
        console.log("at beginning:", sample_sets)
        values = $('#value_table').find(".edit_strain_value")

        for value in values
            real_value = $(value).val()
            row = $(value).closest("tr")
            category = row[0].id
            checkbox = $(row).find(".edit_strain_checkbox")
            checked = $(checkbox).attr('checked')

            if checked and is_number(real_value) and real_value != ""
                real_value = parseFloat(real_value)
                if _(category).startsWith("Primary")
                    sample_sets.primary_only.add_value(real_value)
                else if _(category).startsWith("Other")
                    sample_sets.other_only.add_value(real_value)
                sample_sets.all_cases.add_value(real_value)
        console.log("towards end:", sample_sets)
        update_stat_values(sample_sets)
        

    make_table = ->
        header = "<thead><tr><th>&nbsp;</th>"
        console.log("js_data.sample_groups:", js_data.sample_groups)
        for key, value of js_data.sample_groups
            console.log("aa key:", key)
            console.log("aa value:", value)
            the_id = process_id("column", key)
            header += """<th id="#{ the_id }">#{ value }</th>"""
        header += "</thead>"
        console.log("windex header is:", header)

        rows = [
                {
                    vn: "n_of_samples"
                    pretty: "N of Samples"
                },
                {
                    vn: "mean"
                    pretty: "Mean"
                },
                {
                    vn: "median"
                    pretty: "Median"
                },
                {
                    vn: "se"
                    pretty: "Standard Error (SE)"
                },
                {
                    vn: "sd"
                    pretty: "Standard Deviation (SD)"
                }
        ]

        console.log("rows are:", rows)
        the_rows = "<tbody>"
        console.log("length of rows:", rows.length)
        for row in rows
            console.log("rowing")
            row_line = """<tr>"""
            row_line += """<td id="#{ row.vn  }">#{ row.pretty }</td>"""
            console.log("box - js_data.sample_groups:", js_data.sample_groups)
            for key, value of js_data.sample_groups
                console.log("apple key:", key)
                the_id = process_id(key, row.vn)
                console.log("the_id:", the_id)
                row_line += """<td id="#{ the_id }">foo</td>"""
            row_line += """</tr>"""
            console.log("row line:", row_line)
            the_rows += row_line
        the_rows += "</tbody>"
        table = header + the_rows
        console.log("table is:", table)
        $("#stats_table").append(table)



    process_id = (values...) ->
        ### Make an id or a class valid javascript by, for example, eliminating spaces ###
        processed = ""
        for value in values
            console.log("value:", value)
            value = value.replace(" ", "_")
            if processed.length
                processed += "-"
            processed += value
        return processed
    
    
    show_hide_outliers = ->
        console.log("FOOBAR in beginning of show_hide_outliers")
        label = $('#show_hide_outliers').val()
        console.log("lable is:", label)
        if label == "Hide Outliers"
            $('#show_hide_outliers').val("Show Outliers")
        else if label == "Show Outliers"
            console.log("Found Show Outliers")
            $('#show_hide_outliers').val("Hide Outliers")
            console.log("Should be now Hide Outliers")

    
    #Calculate Correlations Code
    
    
    on_corr_method_change = ->
        console.log("in beginning of on_corr_method_change")
        corr_method = $('select[name=corr_method]').val()
        console.log("corr_method is:", corr_method)
        $('.correlation_desc').hide()
        $('#' + corr_method + "_r_desc").show().effect("highlight")
        if corr_method == "lit"
            $("#corr_sample_method_options").hide()
        else
            $("#corr_sample_method_options").show()

    $('select[name=corr_method]').change(on_corr_method_change)
    
    #on_corr_submit = ->
    #    console.log("in beginning of on_corr_submit")
    #    values = $('#trait_data_form').serialize()
    #    console.log("in on_corr_submit, values are:", values)
    #    
    #    params = $.param(values)
    #    window.location.href = "/corr_compute?" + params
    #    
    #    #$.ajax "/corr_compute",
    #    #    type: 'GET'
    #    #    dataType: 'html'
    #    #    data: values
    #        
    #$('#corr_compute').click(on_corr_submit)

    
    #End Calculate Correlations Code
    


    console.log("before registering show_hide_outliers")
    $('#show_hide_outliers').click(show_hide_outliers)
    console.log("after registering show_hide_outliers")

    _.mixin(_.str.exports());  # Add string fuctions directly to underscore
    $('#value_table').change(edit_data_change)
    console.log("loaded")
    #console.log("basic_table is:", basic_table)
    # Add back following two lines later
    make_table()
    edit_data_change()   # Set the values at the beginning
    #$("#all-mean").html('foobar8')
    console.log("end")
