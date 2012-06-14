console.log("start_b")

$ ->
    hide_tabs = (start) ->
        for x in [start..10]
            $("#stats_tabs" + x).hide()
            console.log("hidden:", x)

    console.log("start_a")
    hide_tabs(1)


    console.log("hidden?")


    stats_mdp_change = ->
        console.log("In stats_mdp_change")
        selected = $(this).val()
        console.log("Change was:", selected)
        hide_tabs(0)
        $("#stats_tabs" + selected).show()

    $(".stats_mdp").change(stats_mdp_change)

    console.log("tape")

