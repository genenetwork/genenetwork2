$('#add_to_admins').click(function() {
    add_emails('admin')
})

$('#add_to_members').click(function() {
    add_emails('member')
})

$('#clear_admins').click(function(){
    clear_emails('admin')
})

$('#clear_members').click(function(){
    clear_emails('member')
})


function add_emails(user_type){
    var email_address = $('input[name=user_email]').val();
    var email_list_string = $('input[name=' + user_type + '_emails_to_add]').val().trim()
    console.log(email_list_string)
    if (email_list_string == ""){
        var email_set = new Set();
    } else {
        var email_set = new Set(email_list_string.split(","))
    }
    email_set.add(email_address)

    $('input[name=' + user_type + '_emails_to_add]').val(Array.from(email_set).join(','))

    var emails_display_string = Array.from(email_set).join('\n')
    $('.added_' + user_type + 's').val(emails_display_string)
}

function clear_emails(user_type){
    $('input[name=' + user_type + '_emails_to_add]').val("")
    $('.added_' + user_type + 's').val("")
}