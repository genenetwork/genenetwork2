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
    constructor(table_id, data_attribute_name, checkbox_creation_function) {
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
	this.checkbox_creation_function = checkbox_creation_function;
    }
}

/**
 * Render the table
 * @param {String} The selector for the table's ID
 * @param {String} The name of the data-* attribute holding the table's data
 * @param {Function} The function to call to generate the appropriate checkbox
 */
function render_table(table_data_source) {
    table_id = table_data_source.table_id.selector;
    data_attr_name = table_data_source.data_attribute_name;
    $(table_id + " tbody tr").remove();
    table_data = JSON.parse($(table_id).attr(data_attr_name)).sort((d1, d2) => {
	return (d1.dataset_name > d2.dataset_name ? 1 : (
	    d1.dataset_name < d2.dataset_name ? -1 : 0))
    });
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
	row.append(table_data_source.checkbox_creation_function(dataset));
	row.append(table_cell(dataset.InbredSetName));
	row.append(table_cell(dataset.dataset_name));
	row.append(table_cell(dataset.dataset_fullname));
	row.append(table_cell(dataset.dataset_shortname));
	$(table_id + " tbody").append(row);
    });
}

function in_array(items, filter_fn) {
    return items.filter(filter_fn).length > 0;
}

function remove_from_table_data(dataset, table_data_source, filter_fn) {
    let table_id = table_data_source.table_id.selector;
    let data_attr_name = table_data_source.data_attribute_name;
    without_dataset = JSON.parse($(table_id).attr(data_attr_name)).filter(
	filter_fn);
    $(table_id).attr(data_attr_name, JSON.stringify(without_dataset));
}

function add_to_table_data(dataset, table_data_source, filter_fn) {
    let table_id = table_data_source.table_id.selector;
    let data_attr_name = table_data_source.data_attribute_name;
    table_data = JSON.parse($(table_id).attr(data_attr_name));
    if(!in_array(table_data, filter_fn)) {
	table_data.push(dataset);
    }
    $(table_id).attr(data_attr_name, JSON.stringify(Array.from(table_data)));
}

/**
 * Switch the dataset/trait from search table to selection table and vice versa
 * @param {Object} A dataset/trait object
 * @param {TableDataSource} The source table for the dataset/trait
 * @param {TableDataSource} The destination table for the dataset/trait
 */
function select_deselect(item, source, destination, filter_fn, render_fn=render_table) {
    dest_selector = destination.table_id.selector
    dest_data = JSON.parse(
	$(dest_selector).attr(destination.data_attribute_name));
    add_to_table_data(item, destination, filter_fn); // Add to destination table
    remove_from_table_data(item, source, (arg) => {return !filter_fn(arg)}); // Remove from source table
    /***** BEGIN: Re-render tables *****/
    render_fn(destination);
    render_fn(source);
    /***** END: Re-render tables *****/
}

function debounce(func, delay=500) {
    var timeout;
    return function search(event) {
	clearTimeout(timeout);
	timeout = setTimeout(func, delay);
    };
}

/**
 * Build a checkbox
 * @param {Dataset Object} A JSON.stringify-able object
 * @param {String} The name to assign the checkbox
 */
function build_checkbox(data_object, checkbox_name, checkbox_aux_classes="", checked=false) {
    cell = $("<td>");
    check = $(
	'<input type="checkbox" class="checkbox" ' +
	    'name="' + checkbox_name + '">');
    check.val(JSON.stringify(data_object));
    check.prop("checked", checked);
    auxilliary_classes = checkbox_aux_classes.trim();
    if(Boolean(auxilliary_classes)) {
	check.attr("class",
		   check.attr("class") + " " + auxilliary_classes.trim());
    }
    cell.append(check);
    return cell;
}

function link_checkbox(dataset) {
    return build_checkbox(dataset, "selected", "checkbox-selected", true);
}

function search_checkbox(dataset) {
    return build_checkbox(dataset, "search_datasets", "checkbox-search");
}

function table_cell(value) {
    cell = $("<td>");
    cell.html(value);
    return cell;
}
