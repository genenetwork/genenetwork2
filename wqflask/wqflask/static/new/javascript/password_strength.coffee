$ ->


    $("#password").keyup ->
        passtext = $(this).val()
        result = zxcvbn(passtext)
        if passtext.length < 6
            $("#password_strength").html('')
            $("#password_alert").fadeOut()
        else
            word = word_score(result.score)
            crack_time = result.crack_time_display
            if crack_time == "instant"
                crack_time = "a second"
            display = "This is #{word} password. It can be cracked in #{crack_time}."
            $("#password_strength").html(display)
            $("#password_alert").fadeIn()

    

    word_score = (num_score) ->
        num_score = parseInt(num_score)
        console.log("num_score is:", num_score)
        mapping =
            0:     "a <strong>terrible</strong>"
            1:     "a <strong>bad</strong>"
            2:     "a <strong>mediocre</strong>"
            3:     "a <strong>good</strong>"
            4:     "an <strong>excellent</strong>"
        console.log("mapping is:", mapping)
        result = mapping[num_score]
        console.log("result is:", result)
        return result