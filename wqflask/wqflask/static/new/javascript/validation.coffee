$ ->

    remove_samples_is_valid = (input)->
        #Validate if input is empty or just white spaces
        if _.trim(input).length == 0 
            return true
        splats = input.split(",")
        new_splats = (_.trim(input) for input in splats)
        console.log("new_splats:", new_splats)
        pattern = /^\d+\s*(?:-\s*\d+)?\s*$/ #Pattern like 3, 10-15, 24
        for splat in new_splats
            console.log("splat is:", splat)
            if not splat.match(pattern)
                return false
        return true

    validate_remove_samples = ->
        ###
        Check if input for the remove samples function is valid and notify the user if not
        ###
        input = $('#remove_samples_field').val()
        console.log("input is:", input)
        if remove_samples_is_valid(input)
            console.log("input is valid")
            $('#remove_samples_invalid').hide()
        else
            console.log("input isn't valid")
            $('#remove_samples_invalid').show()


    $('#remove_samples_field').change(validate_remove_samples)