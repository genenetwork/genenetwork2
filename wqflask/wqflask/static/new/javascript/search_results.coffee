$ ->

    select_all = ->
        console.log("selected_all")
        $(".trait_checkbox").prop('checked', true)

    deselect_all = ->
        $(".trait_checkbox").prop('checked', false)

    invert = ->
        $(".trait_checkbox").trigger('click')

    add = ->
        traits = $("#trait_table input:checked").map(->
            return $(this).val()).get()
        console.log("checked length is:", traits.length)
        console.log("checked is:", traits)
        $.colorbox({href:"/collections/add?traits=#{traits}"})




    $("#select_all").click(select_all)
    $("#deselect_all").click(deselect_all)
    $("#invert").click(invert)
    $("#add").click(add)
