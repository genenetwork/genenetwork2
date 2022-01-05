/**
 * This is, hopefully, a short-term stop-gap measure to get the system working
 * and to get some feedback, even as better optimisation is done in the
 * background to get better response/performance for the partial correlation
 * computations
 */

function key_value(keys, values) {
    if(!(keys.length == values.length)) {
	Error("The 'keys' and 'values' objects MUST be the same length");
	return null;
    }
    return values.reduce(function(accumulator, item, index) {
	accumulator[keys[index]] = item;
	return accumulator;
    }, {});
}

function trait(trait_str) {
    return key_value(
	["name", "dataset", "symbol", "description", "location", "mean_expr",
	 "max_lrs", "data_hmac"],
	trait_str.split(":::"));
}

function primary_trait() {
    trait_string = document.querySelector(
	"#partial-correlations-form input[name=primary_trait]").value;
    return trait(trait_string);
}

function control_traits() {
    return document.querySelector(
	"#partial-correlations-form input[name=control_traits]").value.split(
	    "|||").map(trait).filter(trait => !(trait === null));
}

function correlation_method() {
    return document.querySelector(
	"#partial-correlations-form select[name=method]").value;
}

function criteria() {
    return document.querySelector(
	"#partial-correlations-form select[name=criteria]").value;
}

function target_db() {
    return document.querySelector(
	"#partial-correlations-form select[name=target_db]").value;
}

function partial_corr_request_data() {
    return {
	"primary_trait": primary_trait(),
	"control_traits": control_traits(),
	"method": correlation_method(),
	"criteria": criteria(),
	"target_db": target_db()
    }
}

function rho_or_r(method) {
    if (method === "spearman") {
	return "rho";
    }
    return "r";
}

function format_number(num) {
    if(num === null) {
	return NaN;
    }
    if(Math.abs(num) <= 1.04e-4) {
	return num.toExponential(2);
    }
    return num.toFixed(5);
}

function display_publish_results(primary, controls, correlations, method) {
    table = document.getElementById("part-corr-results-publish");
    table.setAttribute("style", "display: block;");
    table_body = document.querySelector("#part-corr-results-publish tbody");
    template_row = document.querySelector(
	"#part-corr-results-publish tr.template-publish-results-row");
    correlations.forEach(function(item, index, arr) {
	new_row = template_row.cloneNode(true);
	new_row.setAttribute("class", "results-row");
	new_row.querySelector(
	    'td[data-column-heading="Record"]').innerHTML = item["trait_name"];
	new_row.querySelector(
	    'td[data-column-heading="Phenotype"]').innerHTML = (
	    item["post_publication_description"]);
	new_row.querySelector(
	    'td[data-column-heading="Authors"]').innerHTML = item["authors"];
	new_row.querySelector(
	    'td[data-column-heading="Year"]').innerHTML = item["year"];
	new_row.querySelector(
	    'td[data-column-heading="N"]').innerHTML = item["noverlap"];
	new_row.querySelector(
	    `td[data-column-heading="Partial ${rho_or_r(method)}"]`
	).innerHTML = format_number(item["partial_corr"]);
	new_row.querySelector(
	    `td[data-column-heading="p(partial ${rho_or_r(method)})"]`
	).innerHTML = format_number(item["partial_corr_p_value"]);
	new_row.querySelector(
	    `td[data-column-heading="${rho_or_r(method)}"]`
	).innerHTML = format_number(item["corr"]);
	new_row.querySelector(
	    `td[data-column-heading="p(${rho_or_r(method)})"]`
	).innerHTML = format_number(item["corr_p_value"]);
	new_row.querySelector(
	    `td[data-column-heading="delta ${rho_or_r(method)}"]`
	).innerHTML = format_number(item["delta"]);
	table_body.appendChild(new_row);
    });
    table_body.removeChild(template_row);
}

function display_geno_results(primary, controls, correlations, method) {
    table = document.getElementById("part-corr-results-geno");
    table.setAttribute("style", "display: block;");
    table_body = document.querySelector("#part-corr-results-geno tbody");
    template_row = document.querySelector(
	"#part-corr-results-geno tr.template-geno-results-row");
    correlations.forEach(function(item, index, arr) {
	new_row = template_row.cloneNode(true);
	new_row.setAttribute("class", "results-row");
	new_row.querySelector(
	    'td[data-column-heading="Locus"]').innerHTML = item["trait_name"];
	new_row.querySelector(
	    'td[data-column-heading="Chr"]').innerHTML = item["chr"];
	new_row.querySelector(
	    'td[data-column-heading="Megabase"]').innerHTML = item["mb"];
	new_row.querySelector(
	    'td[data-column-heading="N"]').innerHTML = item["noverlap"];
	new_row.querySelector(
	    `td[data-column-heading="Partial ${rho_or_r(method)}"]`
	).innerHTML = format_number(item["partial_corr"]);
	new_row.querySelector(
	    `td[data-column-heading="p(partial ${rho_or_r(method)})"]`
	).innerHTML = format_number(item["partial_corr_p_value"]);
	new_row.querySelector(
	    `td[data-column-heading="${rho_or_r(method)}"]`
	).innerHTML = format_number(item["corr"]);
	new_row.querySelector(
	    `td[data-column-heading="p(${rho_or_r(method)})"]`
	).innerHTML = format_number(item["corr_p_value"]);
	new_row.querySelector(
	    `td[data-column-heading="delta ${rho_or_r(method)}"]`
	).innerHTML = format_number(item["delta"]);
	table_body.appendChild(new_row);
    });
    table_body.removeChild(template_row);
}

function display_probeset_results(primary, controls, correlations, method) {
    table = document.getElementById("part-corr-results-probeset");
    table.setAttribute("style", "display: block;");
    table_body = document.querySelector("#part-corr-results-probeset tbody");
    template_row = document.querySelector(
	"#part-corr-results-probeset tr.template-probeset-results-row");
    correlations.forEach(function(item, index, arr) {
	new_row = template_row.cloneNode(true);
	new_row.setAttribute("class", "results-row");
	new_row.querySelector(
	    'td[data-column-heading="Record"]').innerHTML = item["trait_name"];
	new_row.querySelector(
	    'td[data-column-heading="Gene ID"]').innerHTML = item["geneid"];
	new_row.querySelector(
	    'td[data-column-heading="Homologene ID"]').innerHTML = item["homologeneid"];
	new_row.querySelector(
	    'td[data-column-heading="Symbol"]').innerHTML = item["symbol"];
	new_row.querySelector(
	    'td[data-column-heading="Description"]').innerHTML = item["description"];
	new_row.querySelector(
	    'td[data-column-heading="Chr"]').innerHTML = item["chr"];
	new_row.querySelector(
	    'td[data-column-heading="Megabase"]').innerHTML = item["mb"];
	new_row.querySelector(
	    'td[data-column-heading="Mean Expr"]').innerHTML = item["mean_expr"];
	new_row.querySelector(
	    'td[data-column-heading="N"]').innerHTML = item["noverlap"];
	new_row.querySelector(
	    `td[data-column-heading="Sample Partial ${rho_or_r(method)}"]`
	).innerHTML = format_number(item["partial_corr"] || NaN);
	new_row.querySelector(
	    `td[data-column-heading="Sample p(partial ${rho_or_r(method)})"]`
	).innerHTML = format_number(item["partial_corr_p_value"] || NaN);
	new_row.querySelector(
	    `td[data-column-heading="Sample ${rho_or_r(method)}"]`
	).innerHTML = format_number(item["corr"] || NaN);
	new_row.querySelector(
	    `td[data-column-heading="Sample p(${rho_or_r(method)})"]`
	).innerHTML = format_number(item["corr_p_value"] || NaN);
	new_row.querySelector(
	    `td[data-column-heading="delta ${rho_or_r(method)}"]`
	).innerHTML = format_number(item["delta"] || NaN);
	new_row.querySelector(
	    `td[data-column-heading="Lit Corr"]`
	).innerHTML = format_number(item["l_corr"] || NaN);
	new_row.querySelector(
	    `td[data-column-heading="Tissue ${rho_or_r(method)}"]`
	).innerHTML = format_number(item["tissue_corr"] || NaN);
	new_row.querySelector(
	    `td[data-column-heading="Tissue p(${rho_or_r(method)})"]`
	).innerHTML = format_number(item["tissue_p_value"] || NaN);
	table_body.appendChild(new_row);
    });
    template_row.setAttribute("display", "none");
    /*table_body.removeChild(template_row);*/
}

function replace_r_with_rho(method) {
    /* Mostly utility: Replace `r` with `rho` in the appropriate places */
    pattern = /\br\b/;
    if(method == "spearman") {
        results_div = document.getElementById("partial-correlation-results");
	headers = results_div.getElementsByTagName("th");
	for(let header of headers) {
	    header.innerHTML = header.innerHTML.replace(pattern, "rho");
	}

	cells = results_div.getElementsByTagName("td");
	for(let cell of cells) {
	    cell.setAttribute(
		"data-column-heading",
		cell.getAttribute(
		    "data-column-heading").replace(pattern, "rho"));
	}
    }
}

function display_partial_corr_results(data, status, xhr) {
    progress_indicator = document.getElementById(
	"partial-correlations-progress-indicator").style.display = "none";
    console.log(data);

    replace_r_with_rho(data["results"]["method"]);

    display_functions = {
	"Publish": display_publish_results,
	"Geno": display_geno_results,
	"ProbeSet": display_probeset_results
    }

    display_functions[data["results"]["dataset_type"]](
	data["results"]["primary_traits"],
	data["results"]["control_traits"],
	data["results"]["correlations"],
	data["results"]["method"]);
}

function display_partial_corr_error(xhr, status, error) {
    document.getElementById(
	"partial-correlations-progress-indicator").style.display = "none";
    error_element = document.getElementById("part-corr-error");
    panel = document.createElement("div");
    panel.setAttribute("class", "panel panel-danger");
    error_element.appendChild(panel);

    panel_header = document.createElement("div");
    panel_header.setAttribute("class", "panel-heading");
    panel_header.textContent = "Error: " + xhr.status;
    panel.appendChild(panel_header);

    panel_body = document.createElement("div");
    panel_body.setAttribute("class", "panel-body");
    panel_body.textContent = xhr.statusText;
    panel.appendChild(panel_body);
    console.log(xhr)
}

function send_data_and_process_results(
    remote_url, request_data, success_fn, error_fn, indicator_id) {
    document.getElementById(indicator_id).style.display = "block";
    $.ajax({
	type: "POST",
	url: remote_url,
	contentType: "application/json",
	data: JSON.stringify(request_data),
	dataType: "JSON",
	success: success_fn,
	error: error_fn
    });
}

$("#partial-correlations-form").submit(function(e) {
    e.preventDefault();
});

$("#run-partial-corr-button").click(function(evt) {
    send_data_and_process_results(
	document.getElementById(
	    "run-partial-corr-button").getAttribute("data-url"),
	partial_corr_request_data(),
	display_partial_corr_results,
	display_partial_corr_error,
	"partial-correlations-progress-indicator");
})
