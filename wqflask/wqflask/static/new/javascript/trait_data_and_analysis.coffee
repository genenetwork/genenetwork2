console.log("start_b")

isNumber = (o) ->
    return ! isNaN (o-0) && o != null

console.log("isNumber 7:", isNumber(7))
console.log("isNumber 13.1:", isNumber(13.1))
console.log("isNumber x:", isNumber("x"))
console.log("isNumber '9':", isNumber('9'))
console.log("isNumber:", isNumber())


$ ->
    hide_tabs = (start) ->
        for x in [start..10]
            $("#stats_tabs" + x).hide()
            console.log("hidden:", x)

    console.log("start_a")
    hide_tabs(1)


    console.log("hidden?")

    # Changes stats table between all, bxd only and non-bxd, etc.
    stats_mdp_change = ->
        console.log("In stats_mdp_change")
        selected = $(this).val()
        console.log("Change was:", selected)
        hide_tabs(0)
        $("#stats_tabs" + selected).show()

    $(".stats_mdp").change(stats_mdp_change)

    console.log("tape")


    mean = (the_values)->
        total = 0
        total += value for value in the_values
        console.log("yeap")
        console.log(total)
        the_mean = total / the_values.length
        return the_mean.toFixed(2)



    edit_data_change = ->
        console.log("In edit_data_change")
        the_values = []
        #console.log($(this))
        #$(this).each (counter, element) =>
        #    #console.log("counter is:" + counter)
        #    console.log("element is:")
        #    console.log(element)
        console.log("foo")
        values = $('#primary').find(".edit_strain_value")
        console.log("values are:", values)
        for value in values
            console.log(value)
            real_value = $(value).val()
            #if real_value
            console.log(real_value)
            if isNumber(real_value) and real_value != ""
                the_values.push(parseFloat(real_value))
        console.log(the_values)
        the_mean = mean(the_values)
        console.log(the_mean)
        $("#mean_value").html(the_mean)

    $('#primary').change(edit_data_change)
    console.log("loaded")
