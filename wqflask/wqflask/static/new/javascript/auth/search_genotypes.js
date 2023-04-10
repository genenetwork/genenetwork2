/**
 * Build a checkbox: For internal use only
 * @param {Genotype Dataset object} A genotype dataset object
 * @param {String} A string to initialise the checkbox
 */
function __build_checkbox__(dataset, checkbox_str) {
    cell = $("<td>");
    check = $(checkbox_str);
    check.val(JSON.stringify(dataset));
    cell.append(check);
    return cell;
}

function link_checkbox(dataset) {
    return __build_checkbox__(
	dataset,
	'<input type="checkbox" class="checkbox checkbox-selected" ' +
	    'name="selected" checked="checked">');
}

function search_checkbox(dataset) {
    return __build_checkbox__(
	dataset,
	'<input type="checkbox" class="checkbox checkbox-search" ' +
	    'name="search_datasets">');
}

function table_cell(value) {
    cell = $("<td>");
    cell.html(value);
    return cell;
}

/**
 * Render the table
 * @param {String} The selector for the table's ID
 * @param {String} The name of the data-* attribute holding the table's data
 * @param {Function} The function to call to generate the appropriate checkbox
 */
function render_table(table_id, data_attr_name, checkbox_function) {
    $(table_id + " tbody tr").remove();
    table_data = JSON.parse($(table_id).attr(data_attr_name));
    if(table_data.length < 1) {
	row = $("<tr>")
	cell = $('<td colspan="100%" align="center">');
	cell.append(
	    $('<span class="glyphicon glyphicon-info-sign text-info">'));
	cell.append("&nbsp;");
	cell.append("No genotype datasets remaining.");
	row.append(cell);
	$(table_id + " tbody").append(row);
    }
    table_data.forEach(function(dataset) {
	row = $("<tr>")
	row.append(checkbox_function(dataset));
	row.append(table_cell(dataset.InbredSetName));
	row.append(table_cell(dataset.dataset_name));
	row.append(table_cell(dataset.dataset_fullname));
	row.append(table_cell(dataset.dataset_shortname));
	$(table_id + " tbody").append(row);
    });
}

function in_array(dataset, datasets) {
    found = datasets.filter(function(dst) {
	return (dst.SpeciesId == dataset.SpeciesId &&
		dst.InbredSetId == dataset.InbredSetId &&
		dst.GenoFreezeId == dataset.GenoFreezeId);
    });
    return found.length > 0;
}

function remove_from_table_data(dataset, table_data_source) {
    let table_id = table_data_source.table_id.selector;
    let data_attr_name = table_data_source.data_attribute_name;
    without_dataset = JSON.parse($(table_id).attr(data_attr_name)).filter(
	function(dst) {
	    return !(dst.SpeciesId == dataset.SpeciesId &&
		     dst.InbredSetId == dataset.InbredSetId &&
		     dst.GenoFreezeId == dataset.GenoFreezeId);
	});
    $(table_id).attr(data_attr_name, JSON.stringify(without_dataset));
}

function add_to_table_data(dataset, table_data_source) {
    let table_id = table_data_source.table_id.selector;
    let data_attr_name = table_data_source.data_attribute_name;
    table_data = JSON.parse($(table_id).attr(data_attr_name));
    if(!in_array(dataset, table_data)) {
	table_data.push(dataset);
    }
    $(table_id).attr(data_attr_name, JSON.stringify(Array.from(table_data)));
}

function toggle_link_button() {
    num_groups = $("#frm-link-genotypes select option").length - 1;
    num_selected = JSON.parse(
	$("#tbl-link-genotypes").attr("data-selected-datasets")).length;
    if(num_groups > 0 && num_selected > 0) {
	$("#frm-link-genotypes input[type='submit']").prop("disabled", false);
    } else {
	$("#frm-link-genotypes input[type='submit']").prop("disabled", true);
    }
}

class InvalidCSSIDSelector extends Error {
    constructor(message) {
	super(message);
	this.name = "InvalidCSSIDSelector";
    }
}

class InvalidDataAttributeName extends Error {
    constructor(message) {
	super(message);
	this.name = "InvalidDataAttributeName";
    }
}

/**
 * CSSIDSelector: A CSS ID Selector
 * @param {String} A CSS selector of the form '#...'
 */
class CSSIDSelector {
    constructor(selector) {
	if(!selector.startsWith("#")) {
	    throw new InvalidCSSIDSelector(
		"Expected the CSS selector to begin with a `#` character.");
	}
	let id_str = selector.slice(1, selector.length);
	if(document.getElementById(id_str) == null) {
	    throw new InvalidCSSIDSelector(
		"Element with ID '" + id_str + "' does not exist.");
	}
	this.selector = selector;
    }
}

/**
 * TableDataSource: A type to represent a table's data source
 * @param {String} A CSS selector for an ID
 * @param {String} A `data-*` attribute name
 */
class TableDataSource {
    constructor(table_id, data_attribute_name) {
	this.table_id = new CSSIDSelector(table_id);
	let data = document.querySelector(
	    table_id).getAttribute(data_attribute_name);
	if(data == null) {
	    throw new InvalidDataAttributeName(
		"data-* attribute '" + data_attribute_name + "' does not exist " +
		    "for table with ID '" + table_id.slice(1, table_id.length) +
		    "'.");
	} else {
	    this.data_attribute_name = data_attribute_name;
	}
    }
}

/**
 * Switch the dataset from search table to selection table and vice versa
 * @param {Object} A genotype dataset
 * @param {TableDataSource} The table to switch the dataset from
 * @param {TableDataSource} The table to switch the dataset to
 */
function select_deselect_dataset(dataset, source, destination) {
    dest_selector = destination.table_id.selector
    dest_data = JSON.parse(
	$(dest_selector).attr(destination.data_attribute_name));
    add_to_table_data(dataset, destination); // Add to destination table
    remove_from_table_data(dataset, source); // Remove from source table
    /***** BEGIN: Re-render tables *****/
    // The `render_table` could be modified to use the checkbox creator function
    // from the `TableDataSource` object, once that is modified to have that.
    render_table(
	"#tbl-link-genotypes", "data-selected-datasets", link_checkbox);
    render_table("#tbl-genotypes", "data-datasets", search_checkbox);
    toggle_link_button();
    /***** END: Re-render tables *****/
}

function debounce(func, delay=500) {
    var timeout;
    return function search(event) {
	clearTimeout(timeout);
	timeout = setTimeout(func, delay);
    };
}

function search_genotypes() {
    query = document.getElementById("txt-query").value;
    selected = JSON.parse(document.getElementById(
	"tbl-link-genotypes").getAttribute("data-selected-datasets"));
    species_name = document.getElementById("txt-species-name").value
    search_endpoint = "/oauth2/data/genotype/search"
    $.ajax(
	search_endpoint,
	{
	    "method": "POST",
	    "contentType": "application/json; charset=utf-8",
	    "dataType": "json",
	    "data": JSON.stringify({
		"query": query,
		"selected": selected,
		"dataset_type": "genotype",
		"species_name": species_name}),
	    "error": function(jqXHR, textStatus, errorThrown) {
		data = jqXHR.responseJSON
		elt = document.getElementById("search-error").setAttribute(
		    "style", "display: block;");
		document.getElementById("search-error-text").innerHTML = (
		    data.error + " (" + data.status_code + "): " +
			data.error_description);
		document.getElementById("tbl-genotypes").setAttribute(
		    "data-datasets", JSON.stringify([]));
		render_table("#tbl-genotypes", "data-datasets", search_checkbox);
	    },
	    "success": function(data, textStatus, jqXHR) {
		document.getElementById("search-error").setAttribute(
		    "style", "display: none;");
		document.getElementById("tbl-genotypes").setAttribute(
		    "data-datasets", JSON.stringify(data));
		render_table("#tbl-genotypes", "data-datasets", search_checkbox);
	    }
	});
}

$(document).ready(function() {
    let search_table = new TableDataSource("#tbl-genotypes", "data-datasets");
    let link_table = new TableDataSource(
	"#tbl-link-genotypes", "data-selected-datasets");

    $("#frm-search-traits").submit(function(event) {
	event.preventDefault();
	return false;
    });

    $("#txt-query").keyup(debounce(search_genotypes));

    $("#tbl-genotypes").on("change", ".checkbox-search", function(event) {
        if(this.checked) {
	    select_deselect_dataset(
		JSON.parse(this.value), search_table, link_table);
        }
    });

    $("#tbl-link-genotypes").on("change", ".checkbox-selected", function(event) {
	if(!this.checked) {
	    select_deselect_dataset(
		JSON.parse(this.value), link_table, search_table);
	}
    });
});
