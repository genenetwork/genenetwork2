$ ->

    ## Handle menu changes

    process_json = (data) ->
        window.jdata = data
        populate_species()
        apply_default()

    $.ajax '/static/new/javascript/dataset_menu_structure.json',
        dataType: 'json'
        success: process_json

    populate_species = ->
        species_list = @jdata.species
        redo_dropdown($('#species'), species_list)
        populate_group()
    window.populate_species = populate_species

    populate_group = ->
        console.log("in populate group")
        species = $('#species').val()
        group_list = @jdata.groups[species]
        redo_dropdown($('#group'), group_list)
        populate_type()
    window.populate_group = populate_group

    populate_type = ->
        species = $('#species').val()
        group = $('#group').val()
        type_list = @jdata.types[species][group]
        redo_dropdown($('#type'), type_list)
        populate_dataset()
    window.populate_type = populate_type

    populate_dataset = ->
        species = $('#species').val()
        group = $('#group').val()
        type = $('#type').val()
        console.log("sgt:", species, group, type)
        dataset_list = @jdata.datasets[species][group][type]
        console.log("pop_dataset:", dataset_list)
        redo_dropdown($('#dataset'), dataset_list)
    window.populate_dataset = populate_dataset

    redo_dropdown = (dropdown, items) ->
        console.log("in redo:", dropdown, items)
        dropdown.empty()
        for item in items
            dropdown.append($("<option />").val(item[0]).text(item[1]))

    $('#species').change =>
        populate_group()

    $('#group').change =>
        populate_type()

    $('#type').change =>
        populate_dataset()

    ## Info buttons

    open_window = (url, name) ->
        options = "menubar=1,toolbar=1,location=1,resizable=1,status=1,scrollbars=1,directories=1,width=900"
        open(url, name, options).focus()

    # Link to info on selected group; use of "Cross"
    # in the url is outdated and should be changed to group
    group_info = ->
        species = $('#species').val()
        group = $('#group').val()
        url = "/" + species + "Cross.html#" + group
        open_window(url, "Group Info")

    $('#group_info').click(group_info)

    # Link to dataset info
    dataset_info = ->
        dataset = $('#dataset').val()
        url = "/webqtl/main.py?FormID=sharinginfo&InfoPageName=" + dataset
        open_window(url, "Dataset Info")

    $('#dataset_info').click(dataset_info)


    ## Handle setting new default drop downs

    make_default = ->
        holder = {}
        for item in ['species', 'group', 'type', 'dataset']
            holder[item] = $("##{item}").val()
        jholder = JSON.stringify(holder)
        $.cookie('search_defaults', jholder,
                 expires: 365)

    apply_default = ->
        defaults = $.cookie('search_defaults')
        if defaults
            # defaults are stored as a JSON string in a cookie
            defaults = $.parseJSON(defaults)
        else
            # If user hasn't set a default we use this
            # (Most of GN's data is from BXD mice)
            defaults =
                species: "mouse"
                group: "BXD"
                type: "Hippocampus mRNA"
                dataset: "HC_M2_0606_P"

        for item in [['species', 'group']
                     ['group', 'type']
                     ['type', 'dataset'],
                     ['dataset', null]]
            $("##{item[0]}").val(defaults[item[0]])

            if item[1]
                populate_function = "populate_" + item[1]
                console.log("Calling:", populate_function)
                window[populate_function]()

    check_search_term = ->
        search_term = $('#tfor').val()
        console.log("search_term:", search_term)
        if (search_term == "")
            alert("Please enter one or more search terms or search equations.")
            return false

    $("#make_default").click(make_default)
    $("#btsearch").click(check_search_term)