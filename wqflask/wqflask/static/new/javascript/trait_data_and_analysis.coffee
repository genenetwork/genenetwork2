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
                row_line += """<td id="#{ the_id }">&nbsp;</td>"""
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
                processed += ":"
            processed += value
        return processed

    $('#primary').change(edit_data_change)
    console.log("loaded")
    console.log("basic_table is:", basic_table)
    make_table()
    console.log("end")
