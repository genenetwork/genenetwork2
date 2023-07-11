var statTableRows, isNumber,
  __hasProp = {}.hasOwnProperty,
  __slice = [].slice;

isNumber = function(o) {
  return !isNaN((o - 0) && o !== null);
};

statTableRows = [
  {
    vn: "n_of_samples",
    pretty: "N of Samples",
    digits: 0
  }, {
    vn: "mean",
    pretty: "Mean",
    digits: 3
  }, {
    vn: "median",
    pretty: "Median",
    digits: 3
  }, {
    vn: "std_error",
    pretty: "Standard Error (SE)",
    digits: 3
  }, {
    vn: "std_dev",
    pretty: "Standard Deviation (SD)",
    digits: 3
  }, {
    vn: "min",
    pretty: "Minimum",
    digits: 3
  }, {
    vn: "max",
    pretty: "Maximum",
    digits: 3
  }
]

if (js_data.dataset_type == "ProbeSet"){
  if (js_data.data_scale == "linear_positive" || js_data.data_scale == "log2") {
    statTableRows.push({
                           vn: "range",
                           pretty: "Range (log2)",
                           digits: 3
                         })
  } else {
    statTableRows.push({
                           vn: "range",
                           pretty: "Range",
                           digits: 3
                         })
  }
} else {
  statTableRows.push({
                       vn: "range",
                       pretty: "Range",
                       digits: 3
                     })
}

statTableRows.push(
  {
    vn: "range_fold",
    pretty: "Range (fold)",
    digits: 3
  }, {
    vn: "interquartile",
    pretty: "<font color='black'>Interquartile Range</font>",
    url: "http://www.genenetwork.org/glossary.html#Interquartile",
    digits: 3
  }, {
    vn: "skewness",
    pretty: "Skewness",
    url: "https://en.wikipedia.org/wiki/Skewness",
    digits: 3
  }, {
    vn: "kurtosis",
    pretty: "Excess Kurtosis",
    url: "https://en.wikipedia.org/wiki/Kurtosis",
    digits: 3
  }
);

var add, blockByAttributeValue, blockByIndex, blockOutliers, changeStatsValue, createValueDropdown, editDataChange, exportSampleTableData, getSampleTableData, hideNoValue, hideTabs, makeTable, onCorrMethodChange, openTraitSelection, populateSampleAttributesValuesDropdown, processId, updateBarChart, updateHistogram, updateProbPlot, resetSamplesTable, sampleGroupTypes, sampleLists, showHideOutliers, statsMdpChange, updateStatValues;
add = function() {
  var trait;
  trait = $("input[name=trait_hmac]").val();
  return $.colorbox({
    href: "/collections/add",
    data: {
      "traits": trait
    }
  });
};
$('#add_to_collection').click(add);

sampleLists = js_data.sample_lists;
sampleGroupTypes = js_data.sample_group_types;

$(".select_covariates").click(function () {
  openCovariateSelection();
});

$(".remove_covariates").click(function () {
  $(".selected-covariates option:selected").each(function() {
    this_val = $(this).val();
    $(".selected-covariates option").each(function(){
      if ($(this).val() == this_val){
        $(this).remove();
      }
    })
    cofactor_count = $(".selected-covariates:first option").length
    if (cofactor_count > 2 && cofactor_count < 11){
      $(".selected-covariates").each(function() {
        $(this).attr("size", $(".selected-covariates:first option").length)
      });
    } else if (cofactor_count > 10) {
      $(".selected-covariates").each(function() {
        $(this).attr("size", 10)
      });
    } else {
      $(".selected-covariates").each(function() {
        $(this).attr("size", 2)
      });
    }
    if (cofactor_count == 0){
      $(".selected-covariates").each(function() {
        $(this).append($("<option/>", {
          value: "",
          text: "No covariates selected"
        }))
      })
    }
  });

  covariates_list = [];
  $(".selected-covariates:first option").each(function() {
    covariates_list.push($(this).val());
  })
  $("input[name=covariates]").val(covariates_list.join(","))
});

$(".remove_all_covariates").click(function() {
  $(".selected-covariates option").each(function() {
    $(this).remove();
  });
  $(".selected-covariates").attr("size", 2)
  $("input[name=covariates]").val("");
})

openTraitSelection = function() {
  return $('#collections_holder').load('/collections/list?color_by_trait #collections_list', (function(_this) {
    return function() {
      $.colorbox({
        inline: true,
        href: "#collections_holder",
        onComplete: function(){
            $.getScript("/static/new/javascript/get_traits_from_collection.js");
        }
      });
      return $('a.collection_name').attr('onClick', 'return false');
    };
  })(this));
};
openCovariateSelection = function() {
  return $('#collections_holder').load('/collections/list #collections_list', (function(_this) {
    return function() {
      $.colorbox({
        inline: true,
        href: "#collections_holder",
        width: "1000px",
        height: "700px",
        onComplete: function(){
            $.getScript("/static/new/javascript/get_covariates_from_collection.js");
        }
      });
      return $('a.collection_name').attr('onClick', 'return false');
    };
  })(this));
};
hideTabs = function(start) {
  var x, _i, _results;
  _results = [];
  for (x = _i = start; start <= 10 ? _i <= 10 : _i >= 10; x = start <= 10 ? ++_i : --_i) {
    _results.push($("#stats_tabs" + x).hide());
  }
  return _results;
};
statsMdpChange = function() {
  var selected;
  selected = $(this).val();
  hideTabs(0);
  return $("#stats_tabs" + selected).show();
};
changeStatsValue = function(sample_sets, category, value_type, decimal_places, effects) {
  var current_value, id, in_box, the_value, title_value;
  id = "#" + processId(category, value_type);
  in_box = $(id).html;
  current_value = parseFloat($(in_box)).toFixed(decimal_places);
  the_value = sample_sets[category][value_type]();
  if (decimal_places > 0) {
    title_value = the_value.toFixed(decimal_places * 2);
    the_value = the_value.toFixed(decimal_places);
  } else {
    title_value = null;
  }
  if (the_value !== current_value) {
    if (effects) {
      $(id).html(the_value).effect("highlight");
    } else {
      $(id).html(the_value);
    }
  }
  if (title_value) {
    return $(id).attr('title', title_value);
  }
};
updateStatValues = function(sample_sets) {
  var category, row, show_effects, _i, _len, _ref, _results;
  show_effects = $(".tab-pane.active").attr("id") === "stats_tab";
  _ref = ['samples_primary', 'samples_other', 'samples_all'];
  _results = [];
  for (_i = 0, _len = _ref.length; _i < _len; _i++) {
    category = _ref[_i];
    _results.push((function() {
      var _j, _len1, _results1;
      _results1 = [];
      for (_j = 0, _len1 = statTableRows.length; _j < _len1; _j++) {
        row = statTableRows[_j];
        _results1.push(changeStatsValue(sample_sets, category, row.vn, row.digits, show_effects));
      }
      return _results1;
    })());
  }
  return _results;
};

updateHistogram_width = function() {
  num_bins = $('#histogram').find('g.trace.bars').find('g.point').length

  if (num_bins < 10) {
    width_update = {
      width: 400
    }

    Plotly.relayout('histogram', width_update)
  }
}

updateHistogram = function() {
  var x;
  var _i, _len, _ref, data;
  _ref = _.values(root.selected_samples[root.stats_group]);
  var trait_vals = [];
  for (_i = 0, _len = _ref.length; _i < _len; _i++) {
    x = _ref[_i];
    trait_vals.push(x.value);
  }
  root.histogram_data[0]['x'] = trait_vals

  if ($('input[name="transform"]').val() != ""){
    root.histogram_layout['xaxis']['title'] = "<b>" + js_data.unit_type +  " (" + $('input[name="transform"]').val() + ")</b>"
  } else {
    root.histogram_layout['xaxis']['title'] = "<b>" + js_data.unit_type + "</b>"
  }

  Plotly.newPlot('histogram', root.histogram_data, root.histogram_layout, root.modebar_options);
  updateHistogram_width()
};

updateBarChart = function() {
  var x;
  var _i, _len, _ref, data;
  _ref = _.values(root.selected_samples[root.stats_group]);
  names_and_values = []
  for (i = 0; i < _ref.length; i++){
      _ref[i]["name"] = Object.keys(root.selected_samples[root.stats_group])[i]
  }
  trait_vals = [];
  trait_vars = [];
  trait_samples = [];

  function sortFunction(a, b) {
    if (a.value === b.value) {
      return 0;
    }
    else {
      return (a.value < b.value) ? -1 : 1;
    }
  }

  if (root.bar_sort == "value") {
    _ref.sort(sortFunction)
  }

  for (_i = 0, _len = _ref.length; _i < _len; _i++) {
    x = _ref[_i];
    trait_samples.push(x.name)
    trait_vals.push(x.value);
    if (x["variance"] != undefined) {
      trait_vars.push(x.variance);
    } else{
      trait_vars.push(null)
    }
  }

  new_chart_range = getBarRange(trait_vals, trait_vars)

  root.bar_layout['yaxis']['range'] = new_chart_range

  if ($('input[name="transform"]').val() != ""){
    root.bar_layout['yaxis']['title'] = "<b>" + js_data.unit_type +  " (" + $('input[name="transform"]').val() + ")</b>"
  } else {
    root.bar_layout['yaxis']['title'] = "<b>" + js_data.unit_type + "</b>"
  }

  root.bar_data[0]['y'] = trait_vals
  root.bar_data[0]['error_y'] = {
    type: 'data',
    array: trait_vars,
    visible: root.errors_exist
  }
  root.bar_data[0]['x'] = trait_samples

  if (trait_vals.length < 256) {
    Plotly.newPlot('bar_chart', root.bar_data, root.bar_layout, root.modebar_options);
  }
};

updateViolinPlot = function() {
  var y_value_list = []
  if (sampleLists.length > 1) {
    i = 0;
    for (var sample_group in root.selected_samples){
      var trait_sample_data = _.values(root.selected_samples[sample_group])
      var trait_vals = [];
      for (j = 0, len = trait_sample_data.length; j < len; j++) {
        this_sample_data = trait_sample_data[j];
        trait_vals.push(this_sample_data.value);
      }
      root.violin_data[i]['y'] = trait_vals
      i++;
    }
  } else {
    var trait_sample_data = _.values(root.selected_samples['samples_all'])
    var trait_vals = [];
    for (j = 0, len = trait_sample_data.length; j < len; j++) {
      this_sample_data = trait_sample_data[j];
      trait_vals.push(this_sample_data.value);
    }
    root.violin_data[0]['y'] = trait_vals
  }

  if ($('input[name="transform"]').val() != ""){
    root.violin_layout['yaxis']['title'] = "<b>" + js_data.unit_type +  " (" + $('input[name="transform"]').val() + ")</b>"
  } else {
    root.violin_layout['yaxis']['title'] = "<b>" + js_data.unit_type + "</b>"
  }

  Plotly.newPlot('violin_plot', root.violin_data, root.violin_layout, root.modebar_options)
}


updateProbPlot = function() {
  return root.redraw_prob_plot_impl(root.selected_samples, root.prob_plot_group);
};

makeTable = function() {
  var header, key, row, row_line, table, the_id, the_rows, value, _i, _len, _ref, _ref1;
  if (js_data.trait_symbol != null) {
    header = "<thead><tr><th style=\"color: white; background-color: #369; text-align: center;\" colspan=\"100%\">Trait " + js_data.trait_id + " - " + js_data.trait_symbol + "</th></tr><tr><th style=\"text-align: right; padding-left: 5px;\">Statistic</th>";
  } else if (js_data.dataset_type == "Geno"){
    header = "<thead><tr><th style=\"color: white; background-color: #369; text-align: center;\" colspan=\"100%\">Marker " + js_data.trait_id + "</th></tr><tr><th style=\"text-align: right; padding-left: 5px;\">Statistic</th>";
  } else {
    header = "<thead><tr><th style=\"color: white; background-color: #369; text-align: center;\" colspan=\"100%\">Trait " + js_data.trait_id + ": " + js_data.short_description + "</th></tr><tr><th style=\"text-align: right; padding-left: 5px;\">Statistic</th>";
  }
  _ref = js_data.sample_group_types;
  for (key in _ref) {
    if (!__hasProp.call(_ref, key)) continue;
    value = _ref[key];
    the_id = processId("column", key);
    if (Object.keys(_ref).length > 1) {
        header += "<th id=\"" + the_id + "\" style=\"text-align: right; padding-left: 5px;\">" + value + "</th>";
    } else {
        header += "<th id=\"" + the_id + "\" style=\"text-align: right; padding-left: 5px;\">Value</th>";
    }
  }

  header += "</thead>";
  the_rows = "<tbody>";
  for (_i = 0, _len = statTableRows.length; _i < _len; _i++) {
    row = statTableRows[_i];
    if ((row.vn == "range_fold") && js_data.dataset_type == "Publish"){
        continue;
    }
    row_line = "<tr>";
    if (row.url != null) {
      row_line += "<td id=\"" + row.vn + "\" align=\"right\"><a href=\"" + row.url + "\" style=\"color: #0000EE;\">" + row.pretty + "</a></td>";
    } else {
      row_line += "<td id=\"" + row.vn + "\" align=\"right\">" + row.pretty + "</td>";
    }
    _ref1 = js_data.sample_group_types;
    for (key in _ref1) {
      if (!__hasProp.call(_ref1, key)) continue;
      value = _ref1[key];
      the_id = processId(key, row.vn);
      row_line += "<td id=\"" + the_id + "\" align=\"right\">N/A</td>";
    }
    row_line += "</tr>";
    the_rows += row_line;
  }
  the_rows += "</tbody>";
  table = header + the_rows;
  return $("#stats_table").append(table);
};
processId = function() {
  var processed, value, values, _i, _len;
  values = 1 <= arguments.length ? __slice.call(arguments, 0) : [];

  /* Make an id or a class valid javascript by, for example, eliminating spaces */
  processed = "";
  for (_i = 0, _len = values.length; _i < _len; _i++) {
    value = values[_i];
    value = value.replace(" ", "_");
    if (processed.length) {
      processed += "-";
    }
    processed += value;
  }
  return processed;
};

fetchSampleValues = function() {
  // This is meant to fetch all sample values using DataTables API, since they can't all be submitted with the form when using Scroller (and this should also be faster)
  sample_val_dict = {};

  table = 'samples_primary';
  if ($('#' + table).length){
    tableApi = $('#' + table).DataTable();
    val_nodes = tableApi.column(3).nodes().to$();
    for (_j = 0; _j < val_nodes.length; _j++){
      sample_name = val_nodes[_j].childNodes[0].name.split(":")[1]
      sample_val = val_nodes[_j].childNodes[0].value
      sample_val_dict[sample_name] = sample_val
    }
  }

  return sample_val_dict;
}

editDataChange = function() {
  var already_seen, sample_sets, table, tables, _i, _j, _len;
  already_seen = {};
  sample_sets = {
    samples_primary: new Stats([]),
    samples_other: new Stats([]),
    samples_all: new Stats([])
  };
  root.selected_samples = {
    samples_primary: {},
    samples_other: {},
    samples_all: {}
  };

  tables = ['samples_primary', 'samples_other'];
  for (_i = 0, _len = tables.length; _i < _len; _i++) {
    table = tables[_i];
    if ($('#' + table).length){
      tableApi = $('#' + table).DataTable();
      sample_vals = [];
      name_nodes = tableApi.column(2).nodes().to$();
      val_nodes = tableApi.column(3).nodes().to$();
      var_nodes = tableApi.column(5).nodes().to$();
      for (_j = 0; _j < val_nodes.length; _j++){
        sample_val = val_nodes[_j].childNodes[0].value
        sample_name = $.trim(name_nodes[_j].childNodes[0].textContent)
        if (isNumber(sample_val) && sample_val !== "") {
          sample_val = parseFloat(sample_val);
          sample_sets[table].add_value(sample_val);
          try {
            sample_var = var_nodes[_j].childNodes[0].value
            if (isNumber(sample_var)) {
              sample_var = parseFloat(sample_var)
            } else {
              sample_var = null;
            }
          } catch {
            sample_var = null;
          }
          sample_dict = {
            value: sample_val,
            variance: sample_var
          }
          root.selected_samples[table][sample_name] = sample_dict;
          if (!(sample_name in already_seen)) {
            sample_sets['samples_all'].add_value(sample_val);
            root.selected_samples['samples_all'][sample_name] = sample_dict;
            already_seen[sample_name] = true;
          }
        }
      }
    }

  }

  updateStatValues(sample_sets);

  if ($('#histogram').hasClass('js-plotly-plot')){
    updateHistogram();
  }
  if ($('#bar_chart').hasClass('js-plotly-plot')){
    updateBarChart();
  }
  if ($('#violin_plot').hasClass('js-plotly-plot')){
    updateViolinPlot();
  }
  if ($('#prob_plot_div').hasClass('js-plotly-plot')){
    return updateProbPlot();
  }
};

showHideOutliers = function() {
  var label;
  label = $('#showHideOutliers').val();
  if (label === "Hide Outliers") {
    return $('#showHideOutliers').val("Show Outliers");
  } else if (label === "Show Outliers") {
    $('#showHideOutliers').val("Hide Outliers");
    return console.log("Should be now Hide Outliers");
  }
};

onCorrMethodChange = function() {
  var corr_method;
  corr_method = $('select[name=corr_type]').val();
  $('.correlation_desc').hide();
  $('#' + corr_method + "_r_desc").show().effect("highlight");
  if (corr_method === "lit") {
    return $("#corr_sample_method").hide();
  } else {
    return $("#corr_sample_method").show();
  }
};
$('select[name=corr_type]').change(onCorrMethodChange);

on_dataset_change = function() {
  let dataset_type = $('select[name=corr_dataset] option:selected').data('type');
  let location_type = $('select[name=location_type] option:selected').val();

  if (dataset_type == "mrna_assay"){
    $('#min_expr_filter').show();
    $('select[name=location_type] option:disabled').prop('disabled', false)
  }
  else if (dataset_type == "pheno"){
    $('#min_expr_filter').show();
    $('select[name=location_type]>option:eq(0)').prop('disabled', true).attr('selected', false);
    $('select[name=location_type]>option:eq(1)').prop('disabled', false).attr('selected', true);
  }
  else {
    $('#min_expr_filter').hide();
    $('select[name=location_type]>option:eq(0)').prop('disabled', false).attr('selected', true);
    $('select[name=location_type]>option:eq(1)').prop('disabled', true).attr('selected', false);
  }
}

$('select[name=corr_dataset]').change(on_dataset_change);
$('select[name=location_type]').change(on_dataset_change);

submit_special = function(url) {
  $("input[name=sample_vals]").val(JSON.stringify(fetchSampleValues()))
  $("#trait_data_form").attr("action", url);

  $("#trait_data_form").submit();
};

var corrInputList = ['sample_vals', 'corr_type', 'primary_samples', 'trait_id', 'dataset', 'group', 'tool_used', 'form_url', 'corr_sample_method', 'corr_samples_group', 'corr_dataset', 'min_expr',
                        'corr_return_results', 'location_type', 'loc_chr', 'min_loc_mb', 'max_loc_mb', 'p_range_lower', 'p_range_upper',"use_cache"]

$(".test_corr_compute").on("click", (function(_this) {
  return function() {
    $('input[name=tool_used]').val("Correlation");
    $('input[name=form_url]').val("/test_corr_compute");
    $('input[name=wanted_inputs]').val(corrInputList.join(","));
    

    url = "/loading";
    return submit_special(url);
  };
})(this));

$(".corr_compute").on("click", (function(_this) {

    return function() {


    $('input[name=tool_used]').val("Correlation");
    $('input[name=form_url]').val("/corr_compute");
    $('input[name=wanted_inputs]').val(corrInputList.join(","));


    $('input[name=use_cache]').val($('#use_cache').is(":checked") ? "true": "false");

    url = "/loading";
    return submit_special(url);
  };
})(this));

createValueDropdown = function(value) {
  return "<option val=" + value + ">" + value + "</option>";
};

populateSampleAttributesValuesDropdown = function() {
  var attribute_info, key, sample_attributes, selected_attribute, value, _i, _len, _ref, _ref1, _results;
  $('#attribute_values').empty();
  sample_attributes = [];

  var attributesAsList = Object.keys(js_data.attributes).map(function(key) {
    return [key, js_data.attributes[key].id];
  });

  attributesAsList.sort(function(first, second) {
    if (second[1] > first[1]){
      return -1
    }
    if (first[1] > second[1]){
      return 1
    }
    return 0
  });

  for (i=0; i < attributesAsList.length; i++) {
    attribute_info = js_data.attributes[attributesAsList[i][1]]
    sample_attributes.push(attribute_info.distinct_values);
  }

  selected_attribute = $('#exclude_column').val()
  _ref1 = sample_attributes[selected_attribute - 1];
  _results = [];
  for (_i = 0, _len = _ref1.length; _i < _len; _i++) {
    value = _ref1[_i];
    if (value != ""){
      _results.push($(createValueDropdown(value)).appendTo($('#attribute_values')));
    }
  }
  return _results;
};

if (js_data.categorical_attr_exists == "true"){
  populateSampleAttributesValuesDropdown();
}

$('#exclude_column').change(populateSampleAttributesValuesDropdown);
blockByAttributeValue = function() {
  var attribute_name, cell_class, exclude_by_value;

  let exclude_group = $('#exclude_by_attr_group').val();
  let exclude_column = $('#exclude_column').val();

  if (exclude_group === "other") {
    var tableApi = $('#samples_other').DataTable();
  } else {
    var tableApi = $('#samples_primary').DataTable();
  }

  exclude_by_value = $('#attribute_values').val();

  let val_nodes = tableApi.column(3).nodes().to$();
  let exclude_val_nodes = tableApi.column(attributeStartPos + parseInt(exclude_column)).nodes().to$();

  for (i = 0; i < exclude_val_nodes.length; i++) {
    if (exclude_val_nodes[i].hasChildNodes()) {
      let this_col_value = exclude_val_nodes[i].childNodes[0].data;
      let this_val_node = val_nodes[i].childNodes[0];

      if (this_col_value == exclude_by_value){
        this_val_node.value = "x";
      }
    }
  }

  editDataChange();
};
$('#exclude_by_attr').click(blockByAttributeValue);

blockByIndex = function() {
  var end_index, error, index, index_list, index_set, index_string, start_index, _i, _j, _k, _len, _len1, _ref;
  index_string = $('#remove_samples_field').val();
  index_list = [];
  _ref = index_string.split(",");
  for (_i = 0, _len = _ref.length; _i < _len; _i++) {
    index_set = _ref[_i];
    if (index_set.indexOf('-') !== -1) {
      try {
        start_index = parseInt(index_set.split("-")[0]);
        end_index = parseInt(index_set.split("-")[1]);
        for (index = _j = start_index; start_index <= end_index ? _j <= end_index : _j >= end_index; index = start_index <= end_index ? ++_j : --_j) {
          index_list.push(index);
        }
      } catch (_error) {
        error = _error;
        alert("Syntax error");
      }
    } else {
      index = parseInt(index_set);
      index_list.push(index);
    }
  }

  let block_group = $('#block_group').val();
  if (block_group === "other") {
    tableApi = $('#samples_other').DataTable();
  } else {
    tableApi = $('#samples_primary').DataTable();
  }
  val_nodes = tableApi.column(3).nodes().to$();
  for (_k = 0, _len1 = index_list.length; _k < _len1; _k++) {
    index = index_list[_k];
    val_nodes[index - 1].childNodes[0].value = "x";
  }
};

filter_by_study = function() {
  let this_study = $('#filter_study').val();

  let study_sample_data = JSON.parse($('input[name=study_samplelists]').val())
  let filter_samples = study_sample_data[parseInt(this_study)]['samples']

  if ($('#filter_study_group').length){
    let block_group = $('#filter_study_group').val();
    if (block_group === "other") {
      tableApi = $('#samples_other').DataTable();
    } else {
      tableApi = $('#samples_primary').DataTable();
    }
  }

  let sample_nodes = tableApi.column(2).nodes().to$();
  let val_nodes = tableApi.column(3).nodes().to$();
  for (i = 0; i < sample_nodes.length; i++) {
    this_sample = sample_nodes[i].childNodes[0].innerText;
    if (!filter_samples.includes(this_sample)){
      val_nodes[i].childNodes[0].value = "x";
    }
  }
}

filter_by_value = function() {
  let filter_logic = $('#filter_logic').val();
  let filter_column = $('#filter_column').val();
  let filter_value = $('#filter_value').val();
  let block_group = $('#filter_group').val();

  if (block_group === "other") {
    var tableApi = $('#samples_other').DataTable();
  } else {
    var tableApi = $('#samples_primary').DataTable();
  }

  let val_nodes = tableApi.column(3).nodes().to$();
  if (filter_column == "value"){
    var filter_val_nodes = tableApi.column(3).nodes().to$();
  }
  else if (filter_column == "stderr"){
    var filter_val_nodes = tableApi.column(5).nodes().to$();
  }
  else if (!isNaN(filter_column)){
    var filter_val_nodes = tableApi.column(attributeStartPos + parseInt(filter_column)).nodes().to$();
  }
  else {
    return false
  }

  for (i = 0; i < filter_val_nodes.length; i++) {
    if (filter_column == "value" || filter_column == "stderr"){
      var this_col_value = filter_val_nodes[i].childNodes[0].value;
    } else {
      if (filter_val_nodes[i].childNodes[0] !== undefined){
        var this_col_value = filter_val_nodes[i].innerText;
      } else {
        continue
      }
    }
    let this_val_node = val_nodes[i].childNodes[0];

    if(!isNaN(this_col_value) && !isNaN(filter_value)) {
      if (filter_logic == "greater_than"){
        if (parseFloat(this_col_value) <= parseFloat(filter_value)){
          this_val_node.value = "x";
        }
      }
      else if (filter_logic == "less_than"){
        if (parseFloat(this_col_value) >= parseFloat(filter_value)){
          this_val_node.value = "x";
        }
      }
      else if (filter_logic == "greater_or_equal"){
        if (parseFloat(this_col_value) < parseFloat(filter_value)){
          this_val_node.value = "x";
        }
      }
      else if (filter_logic == "less_or_equal"){
        if (parseFloat(this_col_value) > parseFloat(filter_value)){
          this_val_node.value = "x";
        }
      }
    }
  }
};

hideNoValue_filter = function( settings, data, dataIndex ) {
  this_value = tableApi.column(3).nodes().to$()[dataIndex].childNodes[0].value;
  if (this_value == "x"){
    return false
  } else {
    return true
  }
}

hideNoValue = function() {
  tables = ['samples_primary', 'samples_other'];
  filter_active = $(this).data("active");
  for (_i = 0, _len = tables.length; _i < _len; _i++) {
    table = tables[_i];
    if ($('#' + table).length) {
      tableApi = $('#' + table).DataTable();
      if (filter_active == "true"){
        $(this).val("Hide No Value")
        tableApi.draw();
        $(this).data("active", "false");
      } else {
        $(this).val("Show No Value")
        $.fn.dataTable.ext.search.push(hideNoValue_filter);
        tableApi.search();
        tableApi.draw();
        $.fn.dataTable.ext.search.splice($.fn.dataTable.ext.search.indexOf(hideNoValue_filter, 1));
        $(this).data("active", "true");
      }
    }
  }
};
$('#hideNoValue').click(hideNoValue);

blockOutliers = function() {
  return $('.outlier').each((function(_this) {
    return function(_index, element) {
      return $(element).find('.trait-value-input').val('x');
    };
  })(this));
};
$('#blockOutliers').click(blockOutliers);

resetSamplesTable = function() {
  $('input[name="transform"]').val("");
  $('span[name="transform_text"]').text("")
  $('#hideNoValue').val("Hide No Value")
  tables = ['samples_primary', 'samples_other'];
  for (_i = 0, _len = tables.length; _i < _len; _i++) {
    table = tables[_i];
    if ($('#' + table).length) {
      tableApi = $('#' + table).DataTable();
      val_nodes = tableApi.column(3).nodes().to$();
      for (i = 0; i < val_nodes.length; i++) {
        this_node = val_nodes[i].childNodes[0];
        this_node.value = this_node.attributes["data-value"].value;
      }
      if (js_data.se_exists){
        se_nodes = tableApi.column(5).nodes().to$();
        for (i = 0; i < val_nodes.length; i++) {
          this_node = val_nodes[i].childNodes[0];
          this_node.value = this_node.attributes["data-value"].value;
        }
      }
      tableApi.draw();
    }
  }
};
$('.reset').click(function() {
  $('.selected').each(function() {
    $(this).removeClass('selected');
    $(this).find('.edit_sample_checkbox').prop("checked", false);
  })
  resetSamplesTable();
  $('input[name="transform"]').val("");
  editDataChange();
});

checkForZeroToOneVals = function() {
  tables = ['samples_primary', 'samples_other'];
  for (_i = 0, _len = tables.length; _i < _len; _i++) {
    table = tables[_i];
    if ($('#' + table).length) {
      tableApi = $('#' + table).DataTable();
      val_nodes = tableApi.column(3).nodes().to$();
      for (i = 0; i < val_nodes.length; i++) {
        this_node = val_nodes[i].childNodes[0];
        if(!isNaN(this_node.value)) {
          if (0 <= this_node.value && this_node.value < 1){
            return true
          }
        }
      }
    }
  }
  return false
}

log2Data = function(this_node) {
  current_value = this_node.value;
  original_value = this_node.attributes['data-value'].value;
  if(!isNaN(current_value) && !isNaN(original_value)) {
    if (zeroToOneValsExist){
      original_value = parseFloat(original_value) + 1;
    }
    this_node.value = Math.log2(original_value).toFixed(3);
  }
};

log10Data = function() {
  current_value = this_node.value;
  original_value = this_node.attributes['data-value'].value;
  if(!isNaN(current_value) && !isNaN(original_value)) {
    if (zeroToOneValsExist){
      original_value = parseFloat(original_value) + 1;
    }
    this_node.value = Math.log10(original_value).toFixed(3);
  }
};

sqrtData = function() {
  current_value = this_node.value;
  original_value = this_node.attributes['data-value'].value;
  if(!isNaN(current_value) && !isNaN(original_value)) {
    if (zeroToOneValsExist){
      original_value = parseFloat(original_value) + 1;
    }
    this_node.value = Math.sqrt(original_value).toFixed(3);
  }
};

invertData = function() {
  current_value = this_node.value;
  if(!isNaN(current_value)) {
    this_node.value = parseFloat(-(current_value)).toFixed(3);
  }
};

qnormData = function() {
  current_value = this_node.value;
  qnorm_value = this_node.attributes['data-qnorm'].value;
  if(!isNaN(current_value)) {
    this_node.value = qnorm_value;
  }
};

zScoreData = function() {
  current_value = this_node.value;
  zscore_value = this_node.attributes['data-zscore'].value;
  if(!isNaN(current_value)) {
    this_node.value = zscore_value;
  }
};

doTransform = function(transform_type) {
  tables = ['samples_primary', 'samples_other'];
  for (_i = 0, _len = tables.length; _i < _len; _i++) {
    table = tables[_i];
    if ($('#' + table).length) {
      tableApi = $('#' + table).DataTable();
      val_nodes = tableApi.column(3).nodes().to$();
      for (i = 0; i < val_nodes.length; i++) {
        this_node = val_nodes[i].childNodes[0]
        if (transform_type == "log2"){
          log2Data(this_node)
        }
        if (transform_type == "log10"){
          log10Data(this_node)
        }
        if (transform_type == "sqrt"){
          sqrtData(this_node)
        }
        if (transform_type == "invert"){
          invertData(this_node)
        }
        if (transform_type == "qnorm"){
          qnormData(this_node)
        }
        if (transform_type == "zscore"){
          zScoreData(this_node)
        }
      }
    }
  }
}

normalizeData = function() {
  if ($('#norm_method option:selected').val() == 'log2' || $('#norm_method option:selected').val() == 'log10'){
    if ($('input[name="transform"]').val() != "log2" && $('#norm_method option:selected').val() == 'log2') {
      doTransform("log2")
      $('input[name="transform"]').val("log2")
      $('span[name="transform_text"]').text(" - log2 Transformed")
    } else {
      if ($('input[name="transform"]').val() != "log10" && $('#norm_method option:selected').val() == 'log10'){
        doTransform("log10")
        $('input[name="transform"]').val("log10")
        $('span[name="transform_text"]').text(" - log10 Transformed")
      }
    }
  }
  else if ($('#norm_method option:selected').val() == 'sqrt'){
    if ($('input[name="transform"]').val() != "sqrt") {
      doTransform("sqrt")
      $('input[name="transform"]').val("sqrt")
      $('span[name="transform_text"]').text(" - Square Root Transformed")
    }
  }
  else if ($('#norm_method option:selected').val() == 'invert'){
    doTransform("invert")
    $('input[name="transform"]').val("inverted")
    if ($('span[name="transform_text"]:eq(0)').text() != ""){
      current_text = $('span[name="transform_text"]:eq(0)').text();
      $('span[name="transform_text"]').text(current_text + " and Inverted");
    } else {
      $('span[name="transform_text"]').text(" - Inverted")
    }
  }
  else if ($('#norm_method option:selected').val() == 'qnorm'){
    if ($('input[name="transform"]').val() != "qnorm") {
      doTransform("qnorm")
      $('input[name="transform"]').val("qnorm")
      $('span[name="transform_text"]').text(" - Quantile Normalized")
    }
  }
  else if ($('#norm_method option:selected').val() == 'zscore'){
    if ($('input[name="transform"]').val() != "zscore") {
      doTransform("zscore")
      $('input[name="transform"]').val("zscore")
      $('span[name="transform_text"]').text(" - Z-Scores")
    }
  }
}

zeroToOneValsExist = checkForZeroToOneVals();

showTransformWarning = function() {
  transform_type = $('#norm_method option:selected').val()
  if (transform_type == "log2" || transform_type == "log10"){
    if (zeroToOneValsExist){
      $('#transform_alert').css("display", "block")
    }
  } else {
    $('#transform_alert').css("display", "none")
  }
}

$('#norm_method').change(function(){
  showTransformWarning()
});
$('#normalize').hover(function(){
  showTransformWarning()
});

$('#normalize').click(normalizeData)

switchQNormData = function() {
  return $('.trait-value-input').each((function(_this) {
    return function(_index, element) {
      transform_val = $(element).data('transform')
      if (transform_val != "") {
          $(element).val(transform_val.toFixed(3));
      }
      return transform_val
    };
  })(this));
};
$('#qnorm').click(switchQNormData);

getSampleTableData = function(tableName, attributesAsList, includeNAs=false) {
  var samples = [];

  if ($('#' + tableName).length){
    tableApi = $('#' + tableName).DataTable();
    attrCol = 4

    nameNodes = tableApi.column(2).nodes().to$();
    valNodes = tableApi.column(3).nodes().to$();
    if (js_data.se_exists){
      varNodes = tableApi.column(5).nodes().to$();
      attrCol = 6
      if (js_data.has_num_cases) {
        nNodes = tableApi.column(6).nodes().to$();
        attrCol = 7
      }
    } else {
      if (js_data.has_num_cases){
        nNodes = tableApi.column(4).nodes().to$();
        attrCol = 5
      }
    }

    attributeNodes = []
    for (_i = 0; _i < attributesAsList.length; _i++){
      attributeNodes.push(tableApi.column(attrCol + _i).nodes().to$())
    }

    checkedRows = getCheckedRows(tableName)

    for (_j = 0; _j < valNodes.length; _j++){
      if (!checkedRows.includes(_j) && checkedRows.length > 0) {
        continue
      }
      sampleVal = valNodes[_j].childNodes[0].value
      sampleName = $.trim(nameNodes[_j].childNodes[0].textContent)
      if (isNumber(sampleVal) && sampleVal !== "") {
        sampleVal = parseFloat(sampleVal);
      } else {
        sampleVal = 'x'
      }
      if (typeof varNodes == 'undefined'){
        sampleVar = null;
      } else {
        sampleVar = varNodes[_j].childNodes[0].value;
        if (isNumber(sampleVar)) {
          sampleVar = parseFloat(sampleVar);
        } else {
          sampleVar = 'x';
        }
      }
      if (typeof nNodes == 'undefined'){
        sampleN = null;
      } else {
        sampleN = nNodes[_j].childNodes[0].value;
        if (isNumber(sampleN)) {
          sampleN = parseInt(sampleN);
        } else {
          sampleN = 'x';
        }
      }

      rowDict = {
        name: sampleName,
        value: sampleVal,
        se: sampleVar,
        num_cases: sampleN
      }

      for (_k = 0; _k < attributeNodes.length; _k++){
        rowDict[attributesAsList[_k]] = attributeNodes[_k][_j].textContent;
      }
      if (includeNAs || sampleVal != 'x') {
        samples.push(rowDict)
      }
    }
  }

  return samples;
};
exportSampleTableData = function() {
  var format, json_sample_data, sample_data;

  var attributesAsList = Object.keys(js_data.attributes).map(function(key) {
    return js_data.attributes[key].name;
  });

  sample_data = {};
  sample_data.primary_samples = getSampleTableData('samples_primary', attributesAsList, true);
  sample_data.other_samples = getSampleTableData('samples_other', attributesAsList, true);
  sample_data.attributes = attributesAsList;
  json_sample_data = JSON.stringify(sample_data);
  $('input[name=export_data]').val(json_sample_data);
  format = $('input[name=export_format]').val();
  if (format === "excel") {
    $('#trait_data_form').attr('action', '/export_trait_excel');
  } else {
    $('#trait_data_form').attr('action', '/export_trait_csv');
  }
  return $('#trait_data_form').submit();
};

$('.export_format').change(function() {
  if (this.value  == "csv"){
    $('#export_code').css("display", "block")
  } else{
    $('#export_code').css("display", "none")
  }
  $('input[name=export_format]').val( this.value );
  $('.export_format').val( this.value );
});

$('.export').click(exportSampleTableData);
$('#blockOutliers').click(blockOutliers);
_.mixin(_.str.exports());

getSampleVals = function(sample_list) {
  var sample;
  return this.sample_vals = (function() {
    var i, len, results;
    results = [];
    for (i = 0, len = sample_list.length; i < len; i++) {
      sample = sample_list[i];
      if (sample.value !== null) {
        results.push(sample.value);
      }
    }
    return results;
  })();
};

getSampleErrors = function(sample_list) {
  var sample;
  return this.sample_vals = (function() {
    var i, len, results;
    variance_exists = false;
    results = [];
    for (i = 0, len = sample_list.length; i < len; i++) {
      sample = sample_list[i];
      if (sample.variance !== null) {
        results.push(sample.variance);
        variance_exists = true;
      }
    }
    return [results, variance_exists];
  })();
};

getSampleNames = function(sample_list) {
  var sample;
  return this.sampleNames = (function() {
    var i, len, results;
    results = [];
    for (i = 0, len = sample_list.length; i < len; i++) {
      sample = sample_list[i];
      if (sample.value !== null) {
        results.push(sample.name);
      }
    }
    return results;
  })();
};

getBarBottomMargin = function(sample_list){
  bottomMargin = 80
  maxLength = 0
  sampleNames = getSampleNames(sample_list)
  for (i=0; i < sampleNames.length; i++){
    if (sampleNames[i].length > maxLength) {
      maxLength = sampleNames[i].length
    }
  }

  if (maxLength > 6){
    bottomMargin += 11*(maxLength - 6)
  }

  return bottomMargin;
}

root.stats_group = 'samples_primary';

if (Object.keys(js_data.sample_group_types).length > 1) {
    fullSampleLists = [sampleLists[0], sampleLists[1], sampleLists[0].concat(sampleLists[1])]
    sampleGroupList = [js_data.sample_group_types['samples_primary'], js_data.sample_group_types['samples_other'], js_data.sample_group_types['samples_all']]
} else {
    fullSampleLists = [sampleLists[0]]
    sampleGroupList = [js_data.sample_group_types['samples_primary']]
}

// Define Plotly Options (for the options bar at the top of each figure)

root.modebar_options = {
  displayModeBar: true,
  modeBarButtonsToAdd:[{
    name: 'Export as SVG',
    icon: Plotly.Icons.disk,
    click: function(gd) {
      Plotly.downloadImage(gd, {format: 'svg'})
    }
  },
  {
    name: 'Export as JPEG',
    icon: Plotly.Icons.camera,
    click: function(gd) {
      Plotly.downloadImage(gd, {format: 'jpeg'})
    }
  }],
  showEditInChartStudio: true,
  plotlyServerURL: "https://chart-studio.plotly.com",
  modeBarButtonsToRemove:['zoom2d', 'pan2d', 'toImage', 'hoverClosest', 'hoverCompare', 'hoverClosestCartesian', 'hoverCompareCartesian', 'lasso2d', 'toggleSpikelines', 'resetScale2d'],
  displaylogo: false
  //modeBarButtons:['toImage2', 'zoom2d', 'pan2d', 'select2d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d'],
}

// Bar Chart

root.errors_exist = getSampleErrors(sampleLists[0])[1]
var barTrace = {
    x: getSampleNames(sampleLists[0]),
    y: getSampleVals(sampleLists[0]),
    error_y: {
        type: 'data',
        array: getSampleErrors(sampleLists[0])[0],
        visible: root.errors_exist
    },
    type: 'bar'
}

root.bar_data = [barTrace]

getBarRange = function(sample_vals, sampleErrors = null){
  positiveErrorVals = []
  negativeErrorVals = []
  for (i = 0;i < sample_vals.length; i++){
    if (sampleErrors[i] != undefined) {
        positiveErrorVals.push(sample_vals[i] + sampleErrors[i])
        negativeErrorVals.push(sample_vals[i] - sampleErrors[i])
    } else {
        positiveErrorVals.push(sample_vals[i])
        negativeErrorVals.push(sample_vals[i])
    }
  }

  minYVal = Math.min(...negativeErrorVals)
  maxYVal = Math.max(...positiveErrorVals)

  if (minYVal == 0) {
    rangeTop = maxYVal + Math.abs(maxYVal)*0.1
    rangeBottom = 0;
  } else {
    rangeTop = maxYVal + Math.abs(maxYVal)*0.1
    rangeBottom = minYVal - Math.abs(minYVal)*0.1
    if (minYVal > 0) {
        rangeBottom = minYVal - 0.1*Math.abs(minYVal)
    } else if (minYVal < 0) {
        rangeBottom = minYVal + 0.1*minYVal
    } else {
        rangeBottom = 0
    }
  }

  return [rangeBottom, rangeTop]
}

root.chart_range = getBarRange(getSampleVals(sampleLists[0]), getSampleErrors(sampleLists[0])[0])
valRange = root.chart_range[1] - root.chart_range[0]

if (valRange < 0.05){
  tickDigits = '.3f'
  leftMargin = 80
} else if (valRange < 0.5) {
  tickDigits = '.2f'
  leftMargin = 70
} else if (valRange < 5){
  tickDigits = '.1f'
  leftMargin = 60
} else {
  tickDigits = 'f'
  leftMargin = 55
}

if (js_data.num_values < 256) {
  barChartWidth = 25 * getSampleVals(sampleLists[0]).length

  // Set bottom margin dependent on longest sample name length, since those can get long
  bottomMargin = getBarBottomMargin(sampleLists[0])

  root.bar_layout = {
    title: {
      x: 0,
      y: 10,
      xanchor: 'left',
      text: "<b>Trait " + js_data.trait_id + ": " + js_data.short_description + "</b>",
    },
    xaxis: {
        type: 'category',
        titlefont: {
          size: 16
        },
        showline: true,
        ticklen: 4,
        tickfont: {
          size: 16
        },
    },
    yaxis: {
        title: "<b>" + js_data.unit_type + "</b>",
        range: root.chart_range,
        titlefont: {
          size: 16
        },
        showline: true,
        ticklen: 4,
        tickfont: {
          size: 16
        },
        tickformat: tickDigits,
        fixedrange: true
    },
    width: barChartWidth,
    height: 600,
    margin: {
        l: leftMargin,
        r: 30,
        t: 100,
        b: bottomMargin
    },
    dragmode: false
  };

  $('.bar_chart_tab').click(function() {
    updateBarChart();
  });
}

total_sample_count = 0
for (i = 0, i < sampleLists.length; i++;) {
  total_sample_count += getSampleVals(sampleLists[i]).length
}

// Histogram
var hist_trace = {
    x: getSampleVals(sampleLists[0]),
    type: 'histogram'
};
root.histogram_data = [hist_trace];
root.histogram_layout = {
  bargap: 0.05,
  title: {
    x: 0,
    y: 10,
    xanchor: 'left',
    text: "<b> Trait " + js_data.trait_id + ": " + js_data.short_description + "</b>",
  },
  xaxis: {
           autorange: true,
           title: js_data.unit_type,
           titlefont: {
             family: "arial",
             size: 16
           },
           ticklen: 4,
           tickfont: {
             size: 16
           }
         },
  yaxis: {
           autorange: true,
           title: "<b>count</b>",
           titlefont: {
             family: "arial",
             size: 16
           },
           showline: true,
           ticklen: 4,
           tickfont: {
             size: 16
           },
           automargin: true,
           fixedrange: true
         },
  width: 500,
  height: 600,
  margin: {
      l: 100,
      r: 30,
      t: 100,
      b: 50
  }
};

$('.histogram_tab').click(function() {
  updateHistogram();
  updateHistogram_width();
});

$('.histogram_samples_group').val(root.stats_group);
$('.histogram_samples_group').change(function() {
  root.stats_group = $(this).val();
  return updateHistogram();
});

// Violin Plot

root.violin_layout = {
  title: "<b>Trait " + js_data.trait_id + ": " + js_data.short_description + "</b>",
  xaxis: {
      showline: true,
      titlefont: {
        family: "arial",
        size: 16
      },
      tickfont: {
        family: "arial",
        size: 16
      }
  },
  yaxis: {
      title: {
        text: "<b>"+js_data.unit_type+"</b>"
      },
      titlefont: {
        family: "arial",
        size: 16
      },
      autorange: true,
      showline: true,
      ticklen: 4,
      tickfont: {
        size: 16
      },
      tickformat: tickDigits,
      zeroline: false,
      automargin: true
  },
  margin: {
        l: 100,
        r: 30,
        t: 100,
        b: 80
  },
  dragmode: false,
  showlegend: false
};

if (fullSampleLists.length > 1) {
    root.violin_layout['width'] = 600;
    root.violin_layout['height'] = 500;
    var trace1 = {
        y: getSampleVals(fullSampleLists[2]),
        type: 'violin',
        points: 'none',
        box: {
          visible: true
        },
        line: {
          color: 'blue',
        },
        meanline: {
          visible: true
        },
        name: "<b>" + sampleGroupList[2] + "</b>",
        x0: "<b>" + sampleGroupList[2] + "</b>"
    }
    var trace2 = {
        y: getSampleVals(fullSampleLists[1]),
        type: 'violin',
        points: 'none',
        box: {
          visible: true
        },
        line: {
          color: 'red',
        },
        meanline: {
          visible: true
        },
        name: "<b>" + sampleGroupList[1] + "</b>",
        x0: "<b>" + sampleGroupList[1] + "</b>"
    }
    var trace3 = {
        y: getSampleVals(fullSampleLists[0]),
        type: 'violin',
        points: 'none',
        box: {
          visible: true
        },
        line: {
          color: 'green',
        },
        meanline: {
          visible: true
        },
        name: "<b>" + sampleGroupList[0] + "</b>",
        x0: "<b>" + sampleGroupList[0] + "</b>"
    }
    root.violin_data = [trace1, trace2, trace3]
} else {
    root.violin_layout['width'] = 320;
    root.violin_layout['height'] = 400;
    root.violin_data = [
      {
        y: getSampleVals(fullSampleLists[0]),
        type: 'violin',
        points: 'none',
        box: {
          visible: true
        },
        meanline: {
          visible: true
        },
        name: "<b>Trait " + js_data.trait_id + "</b>",
        x0: "<b>density</b>"
      }
    ]
}

$('.violin_plot_tab').click(function() {
  updateViolinPlot();
});

if (getSampleVals(sampleLists[0]).length < 256) {
  $('.bar_chart_samples_group').change(function() {
    root.stats_group = $(this).val();
    return updateBarChart();
  });
  root.bar_sort = "name"
}
$('.sort_by_name').click(function() {
  root.bar_sort = "name"
  return updateBarChart();
});
$('.sort_by_value').click(function() {
  root.bar_sort = "value"
  return updateBarChart();
});

root.prob_plot_group = 'samples_primary';
$('.prob_plot_samples_group').val(root.prob_plot_group);
$('.prob_plot_tab').click(function() {
  return updateProbPlot();
});
$('.prob_plot_samples_group').change(function() {
  root.prob_plot_group = $(this).val();
  return updateProbPlot();
});

function isEmpty( el ){
  return !$.trim(el.html())
}

$('.stats_panel').click(function() {
  if (isEmpty($('#stats_table'))){
    makeTable();
    editDataChange();
  } else {
    editDataChange();
  }
});

$('#block_by_index').click(function(){
  blockByIndex();
  editDataChange();
});

$('#filter_by_study').click(function(){
  filter_by_study();
  editDataChange();
})

$('#filter_by_value').click(function(){
  filter_by_value();
  editDataChange();
})

$('.edit_sample_value').change(function() {
  editDataChange();
});

$('#exclude_group').click(editDataChange);
$('#blockOutliers').click(editDataChange);
$('#reset').click(editDataChange);
$('#qnorm').click(editDataChange);
$('#normalize').click(editDataChange);

Number.prototype.countDecimals = function () {
  if(Math.floor(this.valueOf()) === this.valueOf()) return 0;
    return this.toString().split(".")[1].length || 0;
}
