search_table = new TableDataSource(
    "#tbl-genotypes", "data-traits", (trait) => {
	return build_checkbox(trait, "search_traits", "checkbox-search");
    });
link_table = new TableDataSource(
    "#tbl-link-genotypes", "data-traits", (trait) => {
	return build_checkbox(
	    trait, "selected", "checkbox-selected", checked=true);
    });

function toggle_link_button() {
    num_groups = $("#frm-link-genotypes select option").length - 1;
    num_selected = JSON.parse(
	$("#tbl-link-genotypes").attr("data-traits")).length;
    if(num_groups > 0 && num_selected > 0) {
	$("#frm-link-genotypes input[type='submit']").prop("disabled", false);
    } else {
	$("#frm-link-genotypes input[type='submit']").prop("disabled", true);
    }
}

function render_geno_table(table_data_source) {
    table_id = table_data_source.table_id.selector;
    data_attr_name = table_data_source.data_attribute_name;
    $(table_id + " tbody tr").remove();
    table_data = JSON.parse($(table_id).attr(data_attr_name)).sort((t1, t2) => {
	return (t1.name > t2.name ? 1 : (t1.name < t2.name ? -1 : 0))
    });
    console.debug("WOULD RENDER THE TABLE!!!")
}

function display_search_results(data, textStatus, jqXHR) {
    if(data.status == "queued" || data.status == "started") {
	setTimeout(() => {
	    fetch_search_results(data.job_id, display_search_results);
	}, 250);
	return;
    }
    if(data.status == "completed") {
	$("#tbl-genotypes").attr(
	    "data-traits", JSON.stringify(data.search_results));
	console.debug("THE SEARCH RESULTS: ", data.search_results);
	// Remove this reference to global variable
	render_geno_table(search_table);
    }
    $("#txt-search").prop("disabled", false);
}

/**
 * Fetch the search results
 * @param {UUID}: The job id to fetch data for
 */
function fetch_search_results(job_id, success, error=default_error_fn) {
    host = $("#frm-search").attr("data-gn-server-url");
    endpoint = host + "oauth2/data/search/results/" + job_id
    $("#txt-search").prop("disabled", true);
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

function search_genotypes() {
    query = document.getElementById("txt-query").value;
    selected = JSON.parse(document.getElementById(
	"tbl-link-genotypes").getAttribute("data-traits"));
    species_name = document.getElementById("txt-species-name").value
    search_endpoint = "/oauth2/data/genotype/search"
    search_table = new TableDataSource(
	"#tbl-genotypes", "data-traits", search_checkbox);
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
		console.debug("**************************************")
		data = jqXHR.responseJSON
		elt = document.getElementById("search-error").setAttribute(
		    "style", "display: block;");
		document.getElementById("search-error-text").innerHTML = (
		    data.error + " (" + data.status_code + "): " +
			data.error_description);
		document.getElementById("tbl-genotypes").setAttribute(
		    "data-traits", JSON.stringify([]));
		render_table(search_table);
		console.debug("**************************************")
	    },
	    "success": (data, textStatus, jqXHR) => {
		console.debug("++++++++++++++++++++++++++++++++++++++")
		fetch_search_results(data.job_id, display_search_results)
		console.debug("++++++++++++++++++++++++++++++++++++++")
	    }
	});
}

/*
  function(data, textStatus, jqXHR) {
		document.getElementById("search-error").setAttribute(
		    "style", "display: none;");
		document.getElementById("tbl-genotypes").setAttribute(
		    "data-datasets", JSON.stringify(data));
		render_table(search_table);
		}
*/

/**
 * Return function to check whether `dataset` is in array of `datasets`.
 * @param {GenotypeDataset} A genotype dataset.
 * @param {Array} An array of genotype datasets.
 */
function make_filter(trait) {
    return (dst) => {
	return (dst.SpeciesId == dataset.SpeciesId &&
		dst.InbredSetId == dataset.InbredSetId &&
		dst.GenoFreezeId == dataset.GenoFreezeId);
    };
}

$(document).ready(function() {
    let search_table = new TableDataSource(
	"#tbl-genotypes", "data-traits", search_checkbox);
    let link_table = new TableDataSource(
	"#tbl-link-genotypes", "data-traits", link_checkbox);

    $("#frm-search-traits").submit(function(event) {
	event.preventDefault();
	return false;
    });

    $("#txt-query").keyup(debounce(search_genotypes));

    $("#tbl-genotypes").on("change", ".checkbox-search", function(event) {
        if(this.checked) {
	    dataset = JSON.parse(this.value);
	    select_deselect(
		dataset, search_table, link_table, make_filter(dataset));
	    toggle_link_button();
        }
    });

    $("#tbl-link-genotypes").on("change", ".checkbox-selected", function(event) {
	if(!this.checked) {
	    dataset = JSON.parse(this.value);
	    select_deselect(
		dataset, link_table, search_table, make_filter(dataset));
	    toggle_link_button();
	}
    });

    setTimeout(() => {
	fetch_search_results(
	    $("#tbl-genotypes").attr("data-initial-job-id"),
	    display_search_results);
    }, 500);
});
