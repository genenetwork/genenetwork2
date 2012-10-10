$ ->

    remove_samples_is_valid = (input)->
        return $.isNumeric(input)
    
    #invalidate_block_by_index = ->
    #    $('#remove_samples_invalid').show()
    
    validate_remove_samples = ->
        input = $('#remove_samples_field').val()
        console.log("input is:", input)
        $('#remove_samples_invalid').hide()
        if remove_samples_is_valid(input)
            console.log("input is valid")
        else
            console.log("input isn't valid")
            $('#remove_samples_invalid').show()
    
    $('#remove_samples_field').change(validate_remove_samples)