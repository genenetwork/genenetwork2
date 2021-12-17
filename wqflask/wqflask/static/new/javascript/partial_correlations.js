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
	["name", "dataset", "symbol", "description", "data_hmac"],
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

function display_partial_corr_results(data, status, xhr) {
    progress_indicator = document.getElementById(
	"partial-correlations-progress-indicator").style.display = "none";
    parent = document.getElementById("part-corr-success");
    child = document.createElement("p");
    child.textContent = data;
    parent.appendChild(child);
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
