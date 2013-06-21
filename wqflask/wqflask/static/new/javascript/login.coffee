$ ->


    modalize = (event) ->
        event.preventDefault()
        console.log("in modal_replace:", $(this).attr("href"))
        $.colorbox(
            open: true
            href: this.href
            onComplete: ->
                $(".focused").focus()
        )




    $(document).on("click", ".modalize", modalize)

    form_success = (data) ->
        $.colorbox(
            open: true
            html: data
            onComplete: ->
                $("form").on("submit", submit_form)
        )


    submit_form = (event) ->
        event.preventDefault()
        submit_to = $(this).attr('action')
        data = $(this).serialize()
        console.log("submit_to is:", submit_to)
        $.ajax(
            type: "POST"
            url: submit_to
            data: data
            dataType: "html"
            success: form_success
        )


    $("#colorbox form").on("submit", submit_form)
