/**
 * Global variables: Bad idea - figure out how to pass them down a call stack.
 */
search_table = new TableDataSource(
    "#tbl-phenotypes", "data-traits", (trait) => {
	return build_checkbox(trait, "search_traits", "checkbox-search");
    });
link_table = new TableDataSource(
    "#tbl-link-phenotypes", "data-traits", (trait) => {
	return build_checkbox(
	    trait, "selected", "checkbox-selected", checked=true);
    });

/**
 * Toggle the state for the "Link Traits" button
 */
function toggle_link_button() {
    num_groups = $("#frm-link-phenotypes select option").length - 1;
    num_selected = JSON.parse(
	$("#tbl-link-phenotypes").attr("data-traits")).length;
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

/**
 * Render the table(s) for the phenotype traits
 * @param {TableDataSource} The table to render
 */
function render_pheno_table(table_data_source) {
    table_id = table_data_source.table_id.selector;
    data_attr_name = table_data_source.data_attribute_name;
    $(table_id + " tbody tr").remove();
    table_data = JSON.parse($(table_id).attr(data_attr_name)).sort((t1, t2) => {
	return (t1.name > t2.name ? 1 : (t1.name < t2.name ? -1 : 0))
    });
    if(table_data.length < 1) {
	row = $("<tr>")
	cell = $('<td colspan="100%" align="center">');
	cell.append(
	    $('<span class="glyphicon glyphicon-info-sign text-info">'));
	cell.append("&nbsp;");
	cell.append("No phenotype traits to select from.");
	row.append(cell);
	$(table_id + " tbody").append(row);
    }
    table_data.forEach(function(trait) {
	row = $("<tr>")
	row.append(table_data_source.checkbox_creation_function(trait));
	row.append(table_cell(trait.name));
	row.append(table_cell(trait.group));
	row.append(table_cell(trait.dataset));
	row.append(table_cell(trait.dataset_fullname));
	row.append(table_cell(trait.description));
	row.append(table_cell(trait.authors.join(", ")));
	row.append(table_cell(
	    '<a href="' + trait.pubmed_link +
		'" title="Pubmed link for trait ' + trait.name + '.">' +
		trait.year + "</a>"));
	row.append(table_cell("Chr:" + trait.geno_chr + "@" + trait.geno_mb));
	row.append(table_cell(trait.lrs));
	row.append(table_cell(trait.additive));
	$(table_id + " tbody").append(row);
    });
}

function display_search_results(data, textStatus, jqXHR) {
    if(data.status == "queued" || data.status == "started") {
	setTimeout(() => {
	    fetch_search_results(data.job_id, display_search_results);
	}, 250);
	return;
    }
    if(data.status == "completed") {
	$("#tbl-phenotypes").attr(
	    "data-traits", JSON.stringify(data.search_results));
	// Remove this reference to global variable
	render_pheno_table(search_table);
    }
    $("#txt-search").prop("disabled", false);
}

/**
 * Fetch the search results
 * @param {UUID}: The job id to fetch data for
 */
function fetch_search_results(job_id, success, error=default_error_fn) {
    host = $("#frm-search-traits").attr("data-gn-server-url");
    endpoint = host + "auth/data/search/phenotype/" + job_id
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

function search_phenotypes() {
    query = document.getElementById("txt-query").value;
    selected = JSON.parse(document.getElementById(
	"tbl-link-phenotypes").getAttribute("data-traits"));
    species_name = document.getElementById("txt-species-name").value
    per_page = document.getElementById("txt-per-page").value
    search_table = new TableDataSource(
	"#tbl-phenotypes", "data-traits", search_checkbox);
    endpoint = "/auth/data/phenotype/search"
    $.ajax(
	endpoint,
	{
	    "method": "POST",
	    "contentType": "application/json; charset=utf-8",
	    "dataType": "json",
	    "data": JSON.stringify({
		"query": query,
		"species_name": species_name,
		"dataset_type": "phenotype",
		"per_page": per_page,
		"selected_traits": selected
	    }),
	    "error": default_error_fn,
	    "success": (data, textStatus, jqXHR) => {
		fetch_search_results(data.job_id, display_search_results);
	    }
	});
}

/**
 * Return a function to check whether `trait` is in array of `traits`.
 * @param {PhenotypeTrait} A phenotype trait.
 * @param {Array} An array of phenotype traits.
 */
function make_filter(trait) {
    return (trt) => {
	return (trt.species == trait.species &&
		trt.group == trait.group &&
		trt.dataset == trait.dataset &&
		trt.name == trait.name);
    };
}

$(document).ready(function() {
    $("#frm-search-traits").submit(event => {
	event.preventDefault();
	return false;
    });

    $("#txt-query").keyup(debounce(search_phenotypes));

    $("#tbl-link-phenotypes").on("change", ".checkbox-selected", function(event) {
	if(!this.checked) {
	    trait = JSON.parse(this.value);
	    select_deselect(trait, link_table, search_table,
			    make_filter(trait), render_pheno_table);
	    toggle_link_button();
	}
    });

    $("#tbl-phenotypes").on("change", ".checkbox-search", function(event) {
	if(this.checked) {
	    trait = JSON.parse(this.value)
	    select_deselect(trait, search_table, link_table,
			    make_filter(trait), render_pheno_table);
	    toggle_link_button();
	}
    });

    setTimeout(() => {
	fetch_search_results(
	    $("#tbl-phenotypes").attr("data-initial-job-id"),
	    display_search_results);
    }, 500);
});
