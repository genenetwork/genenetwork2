root = exports ? this

console.log("start_b")

# this is our isNumber, do not confuse with the underscore.js one
is_number = (o) ->
    return ! isNaN (o-0) && o != null

Stat_Table_Rows = [
                {
                    vn: "n_of_samples"
                    pretty: "N of Samples"
                    digits: 0
                },
                {
                    vn: "mean"
                    pretty: "Mean"
                    digits: 2
                },
                {
                    vn: "median"
                    pretty: "Median"
                    digits: 2
                },
                {
                    vn: "std_error"
                    pretty: "Standard Error (SE)"
                    digits: 2
                },
                {
                    vn: "std_dev"
                    pretty: "Standard Deviation (SD)"
                    digits: 2
                },
                {
                    vn: "min"
                    pretty: "Minimum"
                    digits: 2
                },
                {
                    vn: "max"
                    pretty: "Maximum"
                    digits: 2
                },
                {
                    vn: "range"
                    pretty: "Range (log2)"
                    digits: 2
                },
                {
                    vn: "range_fold"
                    pretty: "Range (fold)"
                    digits: 2
                },
                {
                    vn: "interquartile"
                    pretty: "Interquartile Range"
                    url: "/glossary.html#Interquartile"
                    digits: 2
                }
        ]

$ ->
    sample_lists = js_data.sample_lists
    sample_group_types = js_data.sample_group_types

    #if $("#update_bar_chart").length
    #    $("#update_bar_chart.btn-group").button()
    root.bar_chart = new Bar_Chart(sample_lists[0])
    root.histogram = new Histogram(sample_lists[0])
    new Box_Plot(sample_lists[0])

    $('.bar_chart_samples_group').change ->
        $('#bar_chart').remove()
        $('#bar_chart_container').append('<div id="bar_chart"></div>')
        group = $(this).val()
        if group == "samples_primary"
            root.bar_chart = new Bar_Chart(sample_lists[0])
        else if group == "samples_other"
            root.bar_chart = new Bar_Chart(sample_lists[1])
        else if group == "samples_all"
            all_samples = sample_lists[0].concat sample_lists[1]
            root.bar_chart = new Bar_Chart(all_samples)

    $('.box_plot_samples_group').change ->
        $('#box_plot').remove()
        $('#box_plot_container').append('<div id="box_plot"></div>')
        group = $(this).val()
        if group == "samples_primary"
            new Box_Plot(sample_lists[0])
        else if group == "samples_other"
            new Box_Plot(sample_lists[1])
        else if group == "samples_all"
            all_samples = sample_lists[0].concat sample_lists[1]
            new Box_Plot(all_samples)


    hide_tabs = (start) ->
        for x in [start..10]
            $("#stats_tabs" + x).hide()


    # Changes stats table between all, bxd only and non-bxd, etc.
    stats_mdp_change = ->
        selected = $(this).val()
        hide_tabs(0)
        $("#stats_tabs" + selected).show()


    change_stats_value = (sample_sets, category, value_type, decimal_places)->
        id = "#" + process_id(category, value_type)
        console.log("the_id:", id)
        in_box = $(id).html

        current_value = parseFloat($(in_box)).toFixed(decimal_places)

        the_value = sample_sets[category][value_type]()
        console.log("After running sample_sets, the_value is:", the_value)
        if decimal_places > 0
            title_value = the_value.toFixed(decimal_places * 2)
            the_value = the_value.toFixed(decimal_places)
        else
            title_value = null

        console.log("*-* the_value:", the_value)
        console.log("*-* current_value:", current_value)
        if the_value != current_value
            $(id).html(the_value).effect("highlight")

        # We go ahead and always change the title value if we have it
        if title_value
            $(id).attr('title', title_value)


    update_stat_values = (sample_sets)->
        for category in ['samples_primary', 'samples_other', 'samples_all']
            for row in Stat_Table_Rows
                console.log("Calling change_stats_value")
                change_stats_value(sample_sets, category, row.vn, row.digits)


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

        #console.log("rows are:", rows)
        the_rows = "<tbody>"
        #console.log("length of rows:", rows.length)
        for row in Stat_Table_Rows
            console.log("rowing")
            row_line = """<tr>"""
            if row.url?
                row_line += """<td id="#{ row.vn  }"><a href="#{row.url }">#{ row.pretty }</a></td>"""
            else
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

    edit_data_change = ->
        already_seen = {}
        sample_sets =
            samples_primary: new Stats([])
            samples_other: new Stats([])
            samples_all: new Stats([])

        console.log("at beginning:", sample_sets)

        tables = ['samples_primary', 'samples_other']
        for table in tables
            rows = $("#" + table).find('tr')
            for row in rows
                name = $(row).find('.edit_sample_sample_name').html()
                name = $.trim(name)
                real_value = $(row).find('.edit_sample_value').val()
                console.log("real_value:", real_value)
                checkbox = $(row).find(".edit_sample_checkbox")
                checked = $(checkbox).attr('checked')

                if checked and is_number(real_value) and real_value != ""
                    console.log("in the iffy if")
                    real_value = parseFloat(real_value)

                    sample_sets[table].add_value(real_value)
                    console.log("checking name of:", name)
                    if not (name of already_seen)
                        console.log("haven't seen")
                        sample_sets['samples_all'].add_value(real_value)
                        already_seen[name] = true
        console.log("towards end:", sample_sets)
        update_stat_values(sample_sets)

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
    if js_data.attribute_names.length > 0
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
        index_list = []
        for index_set in index_string.split(",")
            if index_set.indexOf('-') != -1
                try
                    start_index = parseInt(index_set.split("-")[0])
                    end_index = parseInt(index_set.split("-")[1])
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
                console.log("block_group:", $('#block_group').val())
                console.log("row:", $('#Other_'+index.toString()))
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

    ##End Get Sample Data from Table Code

    ##Export Sample Table Data Code

    export_sample_table_data = ->
        sample_data = get_sample_table_data()
        console.log("sample_data is:", sample_data)
        json_sample_data = JSON.stringify(sample_data)
        console.log("json_sample_data is:", json_sample_data)

        $('input[name=export_data]').val(json_sample_data)
        console.log("export_data is", $('input[name=export_data]').val())

        format = $('#export_format').val()
        if format == "excel"
            $('#trait_data_form').attr('action', '/export_trait_excel')
        else
            $('#trait_data_form').attr('action', '/export_trait_csv')
        console.log("action is:", $('#trait_data_form').attr('action'))

        $('#trait_data_form').submit()

    $('#export').click(export_sample_table_data)

    ##End Export Sample Table Data Code


    console.log("before registering block_outliers")
    $('#block_outliers').click(block_outliers)
    console.log("after registering block_outliers")

    _.mixin(_.str.exports());  # Add string fuctions directly to underscore
    $('#edit_sample_lists').change(edit_data_change)
    console.log("loaded")
    #console.log("basic_table is:", basic_table)
    # Add back following two lines later
    make_table()
    edit_data_change()   # Set the values at the beginning
    #$("#all-mean").html('foobar8')
    console.log("end")
