$ ->
    console.log("Starting transform")
    $('#login_out').text('Sign out').attr('href', '/logout').removeClass('modalize')
    console.log("Transformed to sign out I hope")
