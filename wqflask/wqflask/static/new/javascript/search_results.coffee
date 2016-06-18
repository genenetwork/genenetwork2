$ ->
    # These are also used by collections view
    # So the name search_results in the filename is misleading

    checked_traits = null

    select_all = ->
        console.log("selected_all")
        $(".trait_checkbox").prop('checked', true)

    deselect_all = ->
        $(".trait_checkbox").prop('checked', false)

    invert = ->
        $(".trait_checkbox").trigger('click')

    add = ->
        traits = $("#trait_table input:checked").map(-> return $(this).val()).get()
        console.log("checked length is:", traits.length)
        console.log("checked is:", traits)
        $.colorbox({href:"/collections/add?traits=#{traits}"})

    removed_traits = ->
        # After we've removed the traits from the database we get rid of them in the table
        console.log('in removed_traits with checked_traits:', checked_traits)
        checked_traits.closest("tr").fadeOut()


    change_buttons = ->
        buttons = ["#add", "#remove"]
        num_checked = $('.trait_checkbox:checked').length
        console.log("num_checked is:", num_checked)
        if (num_checked == 0)
            for button in buttons
                $(button).prop("disabled", true)
        else
            for button in buttons
                $(button).prop("disabled", false)


        if (num_checked > 1)
            console.log("in loop")
            for item in buttons
                console.log("  processing item:", item)
                text = $(item).html()
                #if text.indexOf("Records") == -1
                #    text = text.replace("Record", "Records")
                #    $(item).html(text)
        else
            console.log("in loop")
            for item in buttons
                console.log("  processing item:", item)
                text = $(item).html()
                #text = text.replace("Records", "Record")
                #$(item).html(text)


    # remove is only used by collections view
    remove = ->
        checked_traits = $("#trait_table input:checked")
        traits = checked_traits.map(->
            return $(this).val()).get()
        console.log("checked length is:", traits.length)
        console.log("checked is:", traits)
        uc_id = $("#uc_id").val()
        console.log("uc.id is:", uc_id)
        # Todo: Consider adding a failure message
        $.ajax(
              type: "POST"
              url: "/collections/remove"
              data:
                uc_id: uc_id
                traits: traits
              success: removed_traits
            )



    $("#select_all").click(select_all)
    $("#deselect_all").click(deselect_all)
    $("#invert").click(invert)
    $("#add").click(add)
    $("#remove").click(remove)

    $('.trait_checkbox').click(change_buttons)
    $('.btn').click(change_buttons)
