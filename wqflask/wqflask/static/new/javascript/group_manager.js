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
    let email_address = $('input[name=user_email]').val();
    let email_list_string = $('input[name=' + user_type + '_emails_to_add]').val().trim()
    if (email_list_string == ""){
        let email_set = new Set();
    } else {
        let email_set = new Set(email_list_string.split(","))
    }
    email_set.add(email_address)

    $('input[name=' + user_type + '_emails_to_add]').val(Array.from(email_set).join(','))

    let emails_display_string = Array.from(email_set).join('\n')
    $('.added_' + user_type + 's').val(emails_display_string)
}

function clear_emails(user_type){
    $('input[name=' + user_type + '_emails_to_add]').val("")
    $('.added_' + user_type + 's').val("")
}
