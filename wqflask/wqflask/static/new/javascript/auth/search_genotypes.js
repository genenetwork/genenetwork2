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

function search_genotypes() {
    query = document.getElementById("txt-query").value;
    selected = JSON.parse(document.getElementById(
	"tbl-link-genotypes").getAttribute("data-selected-datasets"));
    species_name = document.getElementById("txt-species-name").value
    search_endpoint = "/auth/data/genotype/search"
    search_table = new TableDataSource(
	"#tbl-genotypes", "data-datasets", search_checkbox);
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
		render_table(search_table);
	    },
	    "success": function(data, textStatus, jqXHR) {
		document.getElementById("search-error").setAttribute(
		    "style", "display: none;");
		document.getElementById("tbl-genotypes").setAttribute(
		    "data-datasets", JSON.stringify(data));
		render_table(search_table);
	    }
	});
}

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
	"#tbl-genotypes", "data-datasets", search_checkbox);
    let link_table = new TableDataSource(
	"#tbl-link-genotypes", "data-selected-datasets", link_checkbox);

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
});
