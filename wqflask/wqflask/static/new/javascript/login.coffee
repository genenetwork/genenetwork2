$ ->
    #$(".modalize").colorbox(
    #                        onComplete: ->
    #                            $(".focused").focus()
    #                        )

    $(".modalize").on("click", (event) ->
        console.log("modalizing!!!")
        event.preventDefault()
        $.colorbox(
            href: $(this).attr("href")
            onComplete: ->
                $(".focused").focus()
        )

    )

    modal_replace = (event) ->
        event.preventDefault()
        console.log("in modal_replace:", $(this).attr("href"))
        $.colorbox(
            open: true
            href: this.href
            onComplete: ->
                $(".focused").focus()
        )
        return false



    $(document).on("click", ".modal_replace", modal_replace)

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


    $("form").on("submit", submit_form)
