$ ->
  $("a[data-target=#utility]").click (ev) ->
    #  Based on http://stackoverflow.com/a/12513100/1175849
    ev.preventDefault()
    target = $(this).attr("href")

    # load the url and show modal on success
    $("#utility .modal-body").load(target, ->
        $("#utility").modal("show")
        )
