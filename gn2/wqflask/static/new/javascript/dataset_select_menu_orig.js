var apply_default, check_search_term, dataset_info, group_info, make_default, open_window, populate_dataset, populate_group, populate_species, populate_type, process_json, redo_dropdown;
process_json = function(data) {
  window.jdata = data;
  populate_species();
  if ($('#type').length > 0) { //This is to determine if it's the index page or the submit_trait page (which only has species and group selection and no make default option)
    return apply_default();
  }
};

range = function(size, startAt=0) {
  return [...Array(size).keys()].map(idx => idx + startAt);
};

indicate_error = function (jqXHR, textStatus, errorThrown) {
  errorElement = document.createElement("span");
  errorElement.setAttribute("class", "alert-danger");
  fallbackLink = document.createElement('a');
  fallbackLink.href = "https://fallback.genenetwork.org";
  fallbackLink.title = "GN2 Fallback";
  fallbackLink.appendChild(document.createTextNode("GN2 Fallback Server."));
  errorText = document.createTextNode(
	  "There was an error retrieving and setting the menu. Try visiting the ");
  errorElement.appendChild(errorText);
  errorElement.appendChild(fallbackLink);
  if (document.getElementById("search")){
    form = document.getElementById("search").getElementsByTagName("form")[0];
    form.prepend(errorElement);
    disable_element = function(select) {
      select.setAttribute("disabled", "disabled");
    };
    Array.from(form.getElementsByTagName("select")).forEach(disable_element);
    Array.from(form.getElementsByTagName("textarea")).forEach(disable_element);
  }
};

defaultStatusCodeFunctions = range(200, 400).reduce(
  function(acc, scode) {
	  acc[scode] = indicate_error;
	  return acc;
  }, {});

if (typeof gn_server_url === 'undefined'){
  gn_server_url = $("#search form").attr("data-gn_server_url")
}

$.ajax(gn_server_url +'/menu/generate/json', {
  dataType: 'json',
  success: process_json,
  statusCode: {
	  ...defaultStatusCodeFunctions,
  }
});

populate_species = function() {
  var species_list;
  species_list = this.jdata.species;
  redo_dropdown($('#species'), species_list);
  return populate_group();
};
window.populate_species = populate_species;

populate_group = function() {
  var group_list, species;
  species = $('#species').val();
  group_list = this.jdata.groups[species];
  for (_i = 0, _len = group_list.length; _i < (_len - 1); _i++) {
     if (group_list[_i][0] == "BXD300"){
         group_list.splice(_i, 1)
     }
  }
  redo_dropdown($('#group'), group_list);
  if ($('#type').length > 0) { //This is to determine if it's the index page or the submit_trait page (which only has species and group selection and no make default option)
    return populate_type();
  }
};
window.populate_group = populate_group;

populate_type = function() {
  var group, species, type_list;
  species = $('#species').val();
  group = $('#group').val();
  type_list = this.jdata.types[species][group];
  redo_dropdown($('#type'), type_list);
  return populate_dataset();
};
window.populate_type = populate_type;

populate_dataset = function() {
  var dataset_list, group, species, type;
  species = $('#species').val();
  group = $('#group').val();
  type = $('#type').val();
  dataset_list = this.jdata.datasets[species][group][type];
  return redo_dropdown($('#dataset'), dataset_list);
};
window.populate_dataset = populate_dataset;

redo_dropdown = function(dropdown, items) {
  var item, _i, _len, _results;
  dropdown.empty();
  _results = [];

  if (dropdown.attr('id') == "species"){
    species_family_list = [];
    for (_i = 0, _len = items.length; _i < _len; _i++) {
      item = items[_i];
      species_family = item[2].toString()
      species_family_list.push([item[0], item[1], species_family])
    }

    current_family = ""
    this_opt_group = null
    for (_i = 0, _len = species_family_list.length; _i < _len; _i++) {
      item = species_family_list[_i];
      if (item[2] != "None" && current_family == ""){
        current_family = item[2]
        this_opt_group = $("<optgroup label=\"" + item[2] + "\">")
        this_opt_group.append($("<option />").val(item[0]).text(item[1]));
      } else if (current_family != "" && item[2] == current_family){
        this_opt_group.append($("<option />").val(item[0]).text(item[1]));
        if (_i == species_family_list.length - 1){
          _results.push(dropdown.append(this_opt_group))
        }
      } else if (current_family != "" && item[2] != current_family && item[2] != "None"){
        current_family = item[2]
        _results.push(dropdown.append(this_opt_group))
        this_opt_group = $("<optgroup label=\"" + current_family + "\">")
        this_opt_group.append($("<option />").val(item[0]).text(item[1]));
        if (_i == species_family_list.length - 1){
          _results.push(dropdown.append(this_opt_group))
        }
      } else if (current_family != "" && this_opt_group != null && item[2] == "None"){
        _results.push(dropdown.append(this_opt_group))
        current_family = ""
        _results.push(dropdown.append($("<option />").val(item[0]).text(item[1])));
      } else {
        _results.push(dropdown.append($("<option />").val(item[0]).text(item[1])));
      }
    }
  } else if (dropdown.attr('id') == "group"){
    group_family_list = [];
    for (_i = 0, _len = items.length; _i < _len; _i++) {
      item = items[_i];
      group_family = item[2].toString().split(":")[1]
      group_family_list.push([item[0], item[1], group_family])
    }

    current_family = ""
    this_opt_group = null
    for (_i = 0, _len = group_family_list.length; _i < _len; _i++) {
      item = group_family_list[_i];
      if (item[2] != "None" && current_family == ""){
        current_family = item[2]
        this_opt_group = $("<optgroup label=\"" + item[2] + "\">")
        this_opt_group.append($("<option />").val(item[0]).text(item[1]));
      } else if (current_family != "" && item[2] == current_family){
        this_opt_group.append($("<option />").val(item[0]).text(item[1]));
        if (_i == group_family_list.length - 1){
          _results.push(dropdown.append(this_opt_group))
        }
      } else if (current_family != "" && item[2] != current_family && item[2] != "None"){
        current_family = item[2]
        _results.push(dropdown.append(this_opt_group))
        this_opt_group = $("<optgroup label=\"" + current_family + "\">")
        this_opt_group.append($("<option />").val(item[0]).text(item[1]));
        if (_i == group_family_list.length - 1){
          _results.push(dropdown.append(this_opt_group))
        }
      } else if (current_family != "" && this_opt_group != null && item[2] == "None"){
        _results.push(dropdown.append(this_opt_group))
        current_family = ""
        _results.push(dropdown.append($("<option />").val(item[0]).text(item[1])));
      } else {
        _results.push(dropdown.append($("<option />").val(item[0]).text(item[1])));
      }
    }
  } else if (dropdown.attr('id') == "type"){
    type_family_list = [];
    for (_i = 0, _len = items.length; _i < _len; _i++) {
      item = items[_i];
      type_family_list.push([item[0], item[1], item[2]])
    }

    current_family = ""
    this_opt_group = null
    for (_i = 0, _len = type_family_list.length; _i < _len; _i++) {
      item = type_family_list[_i];
      if (item[2] != "None" && current_family == ""){
        current_family = item[2]
        this_opt_group = $("<optgroup label=\"" + item[2] + "\">")
        this_opt_group.append($("<option />").val(item[0]).text(item[1]));
        if (_i == type_family_list.length - 1){
          _results.push(dropdown.append(this_opt_group))
        }
      } else if (current_family != "" && item[2] == current_family){
        this_opt_group.append($("<option />").val(item[0]).text(item[1]));
        if (_i == type_family_list.length - 1){
          _results.push(dropdown.append(this_opt_group))
        }
      } else if (current_family != "" && item[2] != current_family && item[2] != "None"){
        current_family = item[2]
        _results.push(dropdown.append(this_opt_group))
        this_opt_group = $("<optgroup label=\"" + current_family + "\">")
        this_opt_group.append($("<option />").val(item[0]).text(item[1]));
        if (_i == type_family_list.length - 1){
          _results.push(dropdown.append(this_opt_group))
        }
      } else {
        _results.push(dropdown.append(this_opt_group))
        current_family = ""
        _results.push(dropdown.append($("<option />").val(item[0]).text(item[1])));
      } 
    }
  } else {
    for (_i = 0, _len = items.length; _i < _len; _i++) {
      item = items[_i];
      if (item.length > 2){
        _results.push(dropdown.append($("<option data-id=\""+item[0]+"\" />").val(item[1]).text(item[2])));
      } else {
        _results.push(dropdown.append($("<option />").val(item[0]).text(item[1])));
      }
    }
  }

  return _results;
};

$('#species').change((function(_this) {
  return function() {
    return populate_group();
  };
})(this));

$('#group').change((function(_this) {
  return function() {
    if ($('#type').length > 0) { //This is to determine if it's the index page or the submit_trait page (which only has species and group selection and no make default option)
      return populate_type();
    }
    else {
      return false
    }
  };
})(this));

$('#type').change((function(_this) {
  return function() {
    return populate_dataset();
  };
})(this));

open_window = function(url, name) {
  var options;
  options = "menubar=yes,toolbar=yes,titlebar=yes,location=yes,resizable=yes,status=yes,scrollbars=yes,directories=yes,width=900";
  return open(url, name, options).focus();
};

group_info = function() {
  $('input[name=accession_id]').val("None");
  $('#searchform').prop("action", "/db_info");
  $('#searchform').submit();
};
$('#group_info').click(group_info);

dataset_info = function() {
  accession_id = $('#dataset option:selected').data("id");
  if (accession_id != "None") {
    $('input[name=accession_id]').val(accession_id);
  } else {
    $('input[name=accession_id]').val("None");
  }

  $('#searchform').prop("action", "/db_info");
  $('#searchform').submit();
}

$('#dataset_info').click(dataset_info);

make_default = function() {
  var holder, item, jholder, _i, _len, _ref;
  alert("The current settings are now your default.")
  holder = {};
  _ref = ['species', 'group', 'type', 'dataset'];
  for (_i = 0, _len = _ref.length; _i < _len; _i++) {
    item = _ref[_i];
    holder[item] = $("#" + item).val();
  }
  jholder = JSON.stringify(holder);
  return $.cookie('search_defaults', jholder, {
    expires: 365
  });
};

apply_default = function() {
  var defaults, item, populate_function, _i, _len, _ref, _results;
  defaults = $.cookie('search_defaults');
  if (defaults) {
    defaults = $.parseJSON(defaults);
  } else {
    defaults = {
      species: "mouse",
      group: "BXD",
      type: "Hippocampus mRNA",
      dataset: "HC_M2_0606_P"
    };
  }

  _ref = [['species', 'group'], ['group', 'type'], ['type', 'dataset'], ['dataset', null]];
  _results = [];
  for (_i = 0, _len = _ref.length; _i < _len; _i++) {
    item = _ref[_i];
    $("#" + item[0]).val(defaults[item[0]]);
    if (item[1]) {
      populate_function = "populate_" + item[1];
      _results.push(window[populate_function]());
    } else {
      _results.push(void 0);
    }
  }
  return _results;
};

check_search_term = function() {
  var or_search_term, and_search_term;
  or_search_term = $('#or_search').val();
  and_search_term = $('#and_search').val();
  if (or_search_term === "" && and_search_term === "") {
    alert("Please enter one or more search terms or search equations.");
    return false;
  }
};

$("#make_default").click(make_default);
$("#btsearch").click(function() {
  $("#searchform").prop("action", "/search")
});
