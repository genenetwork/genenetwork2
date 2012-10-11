console.log("start_b")

# this is our isNumber, do not confuse with the underscore.js one
is_number = (o) ->
    return ! isNaN (o-0) && o != null

$ ->
    hide_tabs = (start) ->
        for x in [start..10]
            $("#stats_tabs" + x).hide()

    #hide_tabs(1)

    # Changes stats table between all, bxd only and non-bxd, etc.
    stats_mdp_change = ->
        selected = $(this).val()
        hide_tabs(0)
        $("#stats_tabs" + selected).show()

    #$(".stats_mdp").change(stats_mdp_change)

    change_stats_value = (sample_sets, category, value_type, decimal_places)->
        id = "#" + process_id(category, value_type)
        console.log("the_id:", id)
        in_box = $(id).html
        
        current_value = parseFloat($(in_box)).toFixed(decimal_places)
        
        the_value = sample_sets[category][value_type]()
        if decimal_places > 0
            the_value = the_value.toFixed(decimal_places)
        
        if the_value != current_value
            $(id).html(the_value).effect("highlight")

    update_stat_values = (sample_sets)->
        for category in ['primary_only', 'other_only', 'all_cases']
            change_stats_value(sample_sets, category, "n_of_samples", 0)
            for stat in ["mean", "median", "std_dev", "std_error"]
                change_stats_value(sample_sets, category, stat, 2)

    edit_data_change = ->                
        sample_sets =
            primary_only: new Stats([])
            other_only: new Stats([])
            all_cases: new Stats([])
                
        console.log("at beginning:", sample_sets)
        values = $('#value_table').find(".edit_sample_value")

        for value in values
            real_value = $(value).val()
            row = $(value).closest("tr")
            category = row[0].id
            checkbox = $(row).find(".edit_sample_checkbox")
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
        console.log("js_data.sample_group_types:", js_data.sample_group_types)
        for own key, value of js_data.sample_group_types
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
                    vn: "std_error"
                    pretty: "Standard Error (SE)"
                },
                {
                    vn: "std_dev"
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
            console.log("box - js_data.sample_group_types:", js_data.sample_group_types)
            for own key, value of js_data.sample_group_types
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

    
    ##Calculate Correlations Code
    
    
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
    
    
    ##End Calculate Correlations Code
    
    ##Populate Samples Attribute Values Code
    
    create_value_dropdown = (value) ->
        return """<option val=#{value}>#{value}</option>"""
    
    populate_sample_attributes_values_dropdown = ->
        console.log("in beginning of psavd")
        $('#attribute_values').empty()
        sample_attributes = {}
        for own key, attribute_info of js_data.attribute_names
            sample_attributes[attribute_info.name] = attribute_info.distinct_values
        console.log("[visa] attributes is:", sample_attributes)
        selected_attribute = $('#exclude_menu').val().replace("_", " ")
        console.log("selected_attribute is:", selected_attribute)
        for value in sample_attributes[selected_attribute]
            $(create_value_dropdown(value))
                .appendTo($('#attribute_values'))

    # Must run once at beginning
    populate_sample_attributes_values_dropdown()
    $('#exclude_menu').change(populate_sample_attributes_values_dropdown)
    
    ##End Populate Samples Attribute Values Codess

    ##Block Samples By Attribute Value Code
    block_by_attribute_value = ->
        attribute_name = $('#exclude_menu').val()
        exclude_by_value = $('#attribute_values').val()
        
        cell_class = ".column_name-#{attribute_name}"
        $(cell_class).each (index, element) =>
            if $.trim($(element).text()) == exclude_by_value
                row = $(element).parent('tr')
                $(row).find(".trait_value_input").val("x")

    $('#exclude_group').click(block_by_attribute_value)
    
    ##End Block Samples By Attribute Value Code
    
    ##Block Samples By Index Code
    
    block_by_index = ->
        index_string = $('#remove_samples_field').val()
        console.log("index_string is:", index_string)
        index_list = []
        for index_set in index_string.split(",")
            if index_set.indexOf('-') != -1
                try
                    start_index = parseInt(index_set.split("-")[0])
                    console.log("start_index:", start_index)
                    end_index = parseInt(index_set.split("-")[1])
                    console.log("end_index:", end_index)
                    index_list.push(index) for index in [start_index..end_index]
                catch error
                    alert("Syntax error")
            else
                #try
                    index = parseInt(index_set)
                    console.log("index:", index)
                    index_list.push(index)
                #catch(erro) 
                #    alert("Syntax error")
        console.log("index_list:", index_list)
        for index in index_list
            if $('#block_group').val() == "primary"
                console.log("block_group:", $('#block_group').val())
                console.log("row:", $('#Primary_'+index.toString()))
                $('#Primary_'+index.toString()).find('.trait_value_input').val("x")
            else if $('#block_group').val() == "other"
                $('#Other_'+index.toString()).find('.trait_value_input').val("x")
    
    $('#block_by_index').click(block_by_index)

    ##End Block Samples By Index Code
    
    ##Hide Sample Rows With No Value (value of 'x') Code
    
    hide_no_value = ->
        $('.value_se').each (_index, element) =>
            if $(element).find('.trait_value_input').val() == 'x'
                $(element).hide()
                
    $('#hide_no_value').click(hide_no_value)

    ##End Hide Sample Rows With No Value Code
    
    ##Block Outliers Code
    block_outliers = ->
        $('.outlier').each (_index, element) =>
            $(element).find('.trait_value_input').val('x')
            
    $('#block_outliers').click(block_outliers)
    
    ##End Block Outliers Code
    
    ##Reset Table Values Code
    reset_samples_table = ->
        $('.trait_value_input').each (_index, element) =>
            console.log("value is:", $(element).val())
            $(element).val($(element).data('value'))
            console.log("data-value is:", $(element).data('value'))
            $(element).parents('.value_se').show()

    $('#reset').click(reset_samples_table)

    ##End Reset Table Values Code
    
    ##Get Sample Data From Table Code
    
    get_sample_table_data = ->
        samples = {}
        primary_samples = []
        other_samples = []
        $('#sortable1').find('.value_se').each (_index, element) =>
            row_data = {}
            row_data.name = $.trim($(element).find('.column_name-Sample').text())
            row_data.value = $(element).find('.edit_sample_value').val()
            if $(element).find('.edit_sample_se').length != -1
                row_data.se = $(element).find('.edit_sample_se').val()
            for own key, attribute_info of js_data.attribute_names
                row_data[attribute_info.name] = $.trim($(element).find(
                    '.column_name-'+attribute_info.name.replace(" ", "_")).text())
            console.log("row_data is:", row_data)
            primary_samples.push(row_data)
        console.log("primary_samples is:", primary_samples)
        samples.primary_samples = primary_samples
        samples.other_samples = other_samples
        return samples


    export_sample_table_data = ->
        sample_data = get_sample_table_data()
        console.log("sample_data is:", sample_data)
        json_sample_data = JSON.stringify(sample_data)
        console.log("json_sample_data is:", json_sample_data)
        $.ajax(
            url: '/export_trait_data'
            type: 'POST'
            data: "json_data=" + json_sample_data
        )

    $('#export').click(export_sample_table_data)
    
    

    ##End Get Sample Data from Table Code

    ##Export Sample Table Data Code
    
    ##End Export Sample Table Data Code


    console.log("before registering block_outliers")
    $('#block_outliers').click(block_outliers)
    console.log("after registering block_outliers")

    _.mixin(_.str.exports());  # Add string fuctions directly to underscore
    $('#value_table').change(edit_data_change)
    console.log("loaded")
    #console.log("basic_table is:", basic_table)
    # Add back following two lines later
    make_table()
    edit_data_change()   # Set the values at the beginning
    #$("#all-mean").html('foobar8')
    console.log("end")
