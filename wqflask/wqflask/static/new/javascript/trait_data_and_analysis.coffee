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


    update_stat_values = (the_values)->
        for category in ['primary', 'other', 'all']
            id = "#" + process_id(category, "mean")
            console.log("id:", id)
            total = 0
            total += value for value in the_values[category]
            the_mean = total / the_values[category].length
            the_mean = the_mean.toFixed(2)
            console.log("aaa")
            in_box = $(id).html
            console.log("in_box:", in_box)
            current_mean = parseFloat($(in_box)).toFixed(2)
            console.log("the_mean:", the_mean)
            console.log("current_mean:", current_mean)
            console.log("aab")
            if the_mean != current_mean
                console.log("setting mean")
                $(id).html(the_mean).effect("highlight")
                console.log("should be set")

            n_of_samples = the_values[category].length
            id = "#" + process_id(category, "n_of_samples")
            console.log("n_of_samples id:", id)
            current_n_of_samples = $(id).html()
            console.log("cnos:", current_n_of_samples)
            console.log("n_of_samples:", n_of_samples)
            if n_of_samples != current_n_of_samples
                $(id).html(n_of_samples).effect("highlight")



    edit_data_change = ->
        the_values =
            primary: []
            other: []
            all: []
        console.log("at beginning:", the_values)
        values = $('#value_table').find(".edit_strain_value")
        #console.log("values are:", values)
        for value in values
            real_value = $(value).val()
            #console.log("parent is:", $(value).closest("tr"))
            row = $(value).closest("tr")
            console.log("row is:", row)
            console.log("row[0].id is:", row[0].id)
            category = row[0].id
            checkbox = $(row).find(".edit_strain_checkbox")
            checked = $(checkbox).attr('checked')
            if not checked
                console.log("Not checked")
                continue
            if is_number(real_value) and real_value != ""
                real_value = parseFloat(real_value)
                if _(category).startsWith("Primary")
                    the_values.primary.push(real_value)
                else if _(category).startsWith("Other")
                    the_values.other.push(real_value)
                the_values.all.push(real_value)
        console.log("torwads end:", the_values)
        update_stat_values(the_values)

    make_table = ->
        header = "<thead><tr><th>&nbsp;</th>"
        for column in basic_table['columns']
            console.log("column:", column)
            the_id = process_id("column", column.t)
            header += """<th id="#{ the_id }">#{ column.n }</th>"""
        header += "</thead>"

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
                }
        ]

        console.log("rows are:", rows)
        the_rows = "<tbody>"
        console.log("length of rows:", rows.length)
        for row in rows
            console.log("rowing")
            row_line = """<tr>"""
            row_line += """<td id="#{ row.vn  }">#{ row.pretty }</td>"""
            for column in basic_table['columns']
                console.log("apple:", column)
                the_id = process_id(column.t, row.vn)
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

    _.mixin(_.str.exports());  # Add string fuctions directly to underscore
    $('#value_table').change(edit_data_change)
    console.log("loaded")
    console.log("basic_table is:", basic_table)
    make_table()
    edit_data_change()   # Set the values at the beginning
    #$("#all-mean").html('foobar8')
    console.log("end")
