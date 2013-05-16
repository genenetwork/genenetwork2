$ ->
    $(".modalize").colorbox()

    modal_replace = (event) ->
        event.preventDefault()
        console.log("in modal_replace:", $(this).attr("href"))
        $.colorbox(
            open: true
            href: this.href
        )
        return false


    $(".modal_replace").on("click", modal_replace)
