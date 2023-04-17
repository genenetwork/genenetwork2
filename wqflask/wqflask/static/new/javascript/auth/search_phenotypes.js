/**
 * Global variables: Bad idea - figure out how to pass them down a call stack.
 */
search_table = new TableDataSource(
    "#tbl-phenotypes", "data-traits",
    function(trait) {build_checkbox(trait, "search_traits")});
link_table = new TableDataSource(
    "#tbl-link-phenotypes", "data-traits",
    function(trait) {build_checkbox(trait, "selected")});

/**
 * Toggle the state for the "Link Traits" button
 */
function toggle_link_button() {
    num_groups = $("#frm-link-phenotypes select option").length - 1;
    num_selected = JSON.parse(
	$("#tbl-link-phenotypes").attr("data-datasets")).length;
    if(num_groups > 0 && num_selected > 0) {
	$("#frm-link-phenotypes input[type='submit']").prop("disabled", false);
    } else {
	$("#frm-link-phenotypes input[type='submit']").prop("disabled", true);
    }
}

/**
 * Default error function: print out debug messages
 */
function default_error_fn(jqXHR, textStatus, errorThrown) {
    console.debug("XHR:", jqXHR);
    console.debug("STATUS:", textStatus);
    console.debug("ERROR:", errorThrown);
}

function display_search_results(data, textStatus, jqXHR) {
    $("#tbl-phenotypes").attr(
	"data-traits", JSON.stringify(data.search_results));
    render_table(search_table);
}

/**
 * Fetch the search results
 * @param {UUID}: The job id to fetch data for
 */
function fetch_search_results(job_id, success, error=default_error_fn) {
    endpoint = $("#frm-search-traits").attr("data-search-results-endpoint");
    $.ajax(
	endpoint,
	{
	    "method": "GET",
	    "contentType": "application/json; charset=utf-8",
	    "dataType": "json",
	    "error": error,
	    "success": success
	}
    );
}

function search_phenotypes() {
    query = document.getElementById("txt-query").value;
    selected = JSON.parse(document.getElementById(
	"tbl-link-phenotypes").getAttribute("data-traitss"));
    species_name = document.getElementById("txt-species-name").value
    per_page = document.getElementById("txt-per-page").value
    search_table = new TableDataSource(
	"#tbl-phenotypes", "data-traits", search_checkbox);
    $.ajax(
	"/oauth2/data/search",
	{
	    "method": "GET",
	    "contentType": "application/json; charset=utf-8",
	    "dataType": "json",
	    "data": JSON.stringify({
		"query": query,
		"species_name": species_name,
		"dataset_type": "phenotype",
		"per_page": per_page
	    }),
	    "error": default_error_fn,
	    "success": (data, textStatus, jqXHR) => {
		fetch_search_results(data.job_id);
	    }
	});
}

$(document).ready(function() {
    $("#frm-search-traits").submit(event => {
	event.preventDefault();
	return false;
    });

    $("#txt-query").keyup(debounce(search_phenotypes));

    $("#tbl-phenotypes").on("change", ".checkbox-selected", function(event) {
	if(this.checked) {
	    select_deselect(JSON.parse(this.value), search_table, link_table);
	    toggle_link_button();
	}
    });

    $("#tbl-link-phenotypes").on("change", ".checkbox-search", function(event) {
	if(!this.checked) {
	    select_deselect(JSON.parse(this.value), search_table, link_table);
	    toggle_link_button();
	}
    });

    setTimeout(
	function() {
	    fetch_search_results(
		$("#tbl-phenotypes").attr("data-initial-job-id"),
		display_search_results)
	},
	500);
});
