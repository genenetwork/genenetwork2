var Stat_Table_Rows, is_number,
  __hasProp = {}.hasOwnProperty,
  __slice = [].slice;

is_number = function(o) {
  return !isNaN((o - 0) && o !== null);
};

Stat_Table_Rows = [
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
    Stat_Table_Rows.push({
                           vn: "range",
                           pretty: "Range (log2)",
                           digits: 3
                         })
  } else {
    Stat_Table_Rows.push({
                           vn: "range",
                           pretty: "Range",
                           digits: 3
                         })
  }
} else {
  Stat_Table_Rows.push({
                       vn: "range",
                       pretty: "Range",
                       digits: 3
                     })
}

Stat_Table_Rows.push(
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

var add, block_by_attribute_value, block_by_index, block_outliers, change_stats_value, create_value_dropdown, edit_data_change, export_sample_table_data, get_sample_table_data, hide_no_value, hide_tabs, make_table, on_corr_method_change, open_trait_selection, populate_sample_attributes_values_dropdown, process_id, update_bar_chart, update_histogram, update_prob_plot, reset_samples_table, sample_group_types, sample_lists, show_hide_outliers, stats_mdp_change, update_stat_values;
add = function() {
  var trait;
  trait = $("input[name=trait_hmac]").val();
  return $.colorbox({
    href: "/collections/add?traits=" + trait
  });
};
$('#add_to_collection').click(add);
sample_lists = js_data.sample_lists;
sample_group_types = js_data.sample_group_types;
d3.select("#select_compare_trait").on("click", (function(_this) {
  return function() {
    $('.scatter-matrix-container').remove();
    return open_trait_selection();
  };
})(this));
d3.select("#select_covariates").on("click", (function(_this) {
  return function() {
    return open_covariate_selection();
  };
})(this));
$("#remove_covariates").click(function () {
    $("input[name=covariates]").val("")
    $(".selected-covariates").val("")
});
$(".select_covariates").click(function () {
  open_covariate_selection();
});
$(".remove_covariates").click(function () {
  $("input[name=covariates]").val("")
  $(".selected-covariates").val("")
});
d3.select("#clear_compare_trait").on("click", (function(_this) {
  return function() {
    return $('.scatter-matrix-container').remove();
  };
})(this));
open_trait_selection = function() {
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
open_covariate_selection = function() {
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
hide_tabs = function(start) {
  var x, _i, _results;
  _results = [];
  for (x = _i = start; start <= 10 ? _i <= 10 : _i >= 10; x = start <= 10 ? ++_i : --_i) {
    _results.push($("#stats_tabs" + x).hide());
  }
  return _results;
};
stats_mdp_change = function() {
  var selected;
  selected = $(this).val();
  hide_tabs(0);
  return $("#stats_tabs" + selected).show();
};
change_stats_value = function(sample_sets, category, value_type, decimal_places, effects) {
  var current_value, id, in_box, the_value, title_value;
  id = "#" + process_id(category, value_type);
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
update_stat_values = function(sample_sets) {
  var category, row, show_effects, _i, _len, _ref, _results;
  show_effects = $(".tab-pane.active").attr("id") === "stats_tab";
  _ref = ['samples_primary', 'samples_other', 'samples_all'];
  _results = [];
  for (_i = 0, _len = _ref.length; _i < _len; _i++) {
    category = _ref[_i];
    _results.push((function() {
      var _j, _len1, _results1;
      _results1 = [];
      for (_j = 0, _len1 = Stat_Table_Rows.length; _j < _len1; _j++) {
        row = Stat_Table_Rows[_j];
        _results1.push(change_stats_value(sample_sets, category, row.vn, row.digits, show_effects));
      }
      return _results1;
    })());
  }
  return _results;
};

update_histogram_width = function() {
  num_bins = $('#histogram').find('g.trace.bars').find('g.point').length

  if (num_bins < 10) {
    width_update = {
      width: 400
    }

    Plotly.relayout('histogram', width_update)
  }
}

update_histogram = function() {
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
  }

  Plotly.newPlot('histogram', root.histogram_data, root.histogram_layout, root.modebar_options);
  update_histogram_width()
};

update_bar_chart = function() {
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

  new_chart_range = get_bar_range(trait_vals, trait_vars)

  root.bar_layout['yaxis']['range'] = new_chart_range

  if ($('input[name="transform"]').val() != ""){
    root.bar_layout['yaxis']['title'] = "<b>" + js_data.unit_type +  " (" + $('input[name="transform"]').val() + ")</b>"
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

update_box_plot = function() {
  var y_value_list = []
  if (sample_lists.length > 1) {
    i = 0;
    for (var sample_group in root.selected_samples){
      var trait_sample_data = _.values(root.selected_samples[sample_group])
      var trait_vals = [];
      for (j = 0, len = trait_sample_data.length; j < len; j++) {
        this_sample_data = trait_sample_data[j];
        trait_vals.push(this_sample_data.value);
      }
      root.box_data[i]['y'] = trait_vals
      i++;
    }
  } else {
    var trait_sample_data = _.values(root.selected_samples['samples_all'])
    var trait_vals = [];
    for (j = 0, len = trait_sample_data.length; j < len; j++) {
      this_sample_data = trait_sample_data[j];
      trait_vals.push(this_sample_data.value);
    }
    root.box_data[0]['y'] = trait_vals
  }

  if ($('input[name="transform"]').val() != ""){
    root.box_layout['yaxis']['title'] = "<b>" + js_data.unit_type +  " (" + $('input[name="transform"]').val() + ")</b>"
  }

  Plotly.newPlot('box_plot', root.box_data, root.box_layout, root.modebar_options)
}

update_violin_plot = function() {
  var y_value_list = []
  if (sample_lists.length > 1) {
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
  }

  Plotly.newPlot('violin_plot', root.violin_data, root.violin_layout, root.modebar_options)
}


update_prob_plot = function() {
  return root.redraw_prob_plot_impl(root.selected_samples, root.prob_plot_group);
};

make_table = function() {
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
    the_id = process_id("column", key);
    if (Object.keys(_ref).length > 1) {
        header += "<th id=\"" + the_id + "\" style=\"text-align: right; padding-left: 5px;\">" + value + "</th>";
    } else {
        header += "<th id=\"" + the_id + "\" style=\"text-align: right; padding-left: 5px;\">Value</th>";
    }
  }

  header += "</thead>";
  the_rows = "<tbody>";
  for (_i = 0, _len = Stat_Table_Rows.length; _i < _len; _i++) {
    row = Stat_Table_Rows[_i];
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
      the_id = process_id(key, row.vn);
      row_line += "<td id=\"" + the_id + "\" align=\"right\">N/A</td>";
    }
    row_line += "</tr>";
    the_rows += row_line;
  }
  the_rows += "</tbody>";
  table = header + the_rows;
  return $("#stats_table").append(table);
};
process_id = function() {
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
edit_data_change = function() {
  var already_seen, checkbox, name, real_dict, real_value, real_variance, row, rows, sample_sets, table, tables, _i, _j, _len, _len1;
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
      table_api = $('#' + table).DataTable();
      sample_vals = [];
      name_nodes = table_api.column(2).nodes().to$();
      val_nodes = table_api.column(3).nodes().to$();
      var_nodes = table_api.column(5).nodes().to$();
      for (_j = 0; _j < val_nodes.length; _j++){
        sample_val = val_nodes[_j].childNodes[0].value
        sample_name = $.trim(name_nodes[_j].childNodes[0].textContent)
        if (is_number(sample_val) && sample_val !== "") {
          sample_val = parseFloat(sample_val);
          sample_sets[table].add_value(sample_val);
          if (typeof var_nodes !== 'undefined'){
            sample_var = null;
          } else {
            sample_var = var_nodes[_j].childNodes[0].value
            if (is_number(sample_var)) {
              sample_var = parseFloat(sample_var)
            } else {
              sample_var = null;
            }
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

  update_stat_values(sample_sets);

  if ($('#histogram').hasClass('js-plotly-plot')){
    update_histogram();
  }
  if ($('#bar_chart').hasClass('js-plotly-plot')){
    update_bar_chart();
  }
  if ($('#box_plot').hasClass('js-plotly-plot')){
    update_box_plot();
  }
  if ($('#violin_plot').hasClass('js-plotly-plot')){
    update_violin_plot();
  }
  if ($('#prob_plot_div').hasClass('js-plotly-plot')){
    return update_prob_plot();
  }
};

show_hide_outliers = function() {
  var label;
  label = $('#show_hide_outliers').val();
  if (label === "Hide Outliers") {
    return $('#show_hide_outliers').val("Show Outliers");
  } else if (label === "Show Outliers") {
    $('#show_hide_outliers').val("Hide Outliers");
    return console.log("Should be now Hide Outliers");
  }
};

on_corr_method_change = function() {
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
$('select[name=corr_type]').change(on_corr_method_change);

submit_special = function(url) {
  get_table_contents_for_form_submit("trait_data_form");
  $("#trait_data_form").attr("action", url);
  $("#trait_data_form").submit();
};

get_table_contents_for_form_submit = function(form_id) {
  // Borrowed code from - https://stackoverflow.com/questions/31418047/how-to-post-data-for-the-whole-table-using-jquery-datatables
  let this_form = $("#" + form_id);
  var params = primary_table.$('input').serializeArray();

  $.each(params, function(){
    // If element doesn't exist in DOM
    if(!$.contains(document, this_form[this.name])){
       // Create a hidden element
       this_form.append(
          $('<input>')
             .attr('type', 'hidden')
             .attr('name', this.name)
             .val(this.value)
       );
    }
 });
}

var corr_input_list = ['corr_type', 'primary_samples', 'trait_id', 'dataset', 'group', 'tool_used', 'form_url', 'corr_sample_method', 'corr_samples_group', 'corr_dataset', 'min_expr',
                        'corr_return_results', 'loc_chr', 'min_loc_mb', 'max_loc_mb', 'p_range_lower', 'p_range_upper']

$(".corr_compute").on("click", (function(_this) {
  return function() {
    $('input[name=tool_used]').val("Correlation");
    $('input[name=form_url]').val("/corr_compute");
    $('input[name=wanted_inputs]').val(corr_input_list.join(","));
    url = "/loading";
    return submit_special(url);
  };
})(this));

create_value_dropdown = function(value) {
  return "<option val=" + value + ">" + value + "</option>";
};
populate_sample_attributes_values_dropdown = function() {
  var attribute_info, key, sample_attributes, selected_attribute, value, _i, _len, _ref, _ref1, _results;
  $('#attribute_values').empty();
  sample_attributes = {};
  attr_keys = Object.keys(js_data.attributes).sort();
  for (i=0; i < attr_keys.length; i++) {
    attribute_info = js_data.attributes[attr_keys[i]];
    sample_attributes[attribute_info.name] = attribute_info.distinct_values;
  }
  selected_attribute = $('#exclude_menu').val().replace("_", " ");
  _ref1 = sample_attributes[selected_attribute];
  _results = [];
  for (_i = 0, _len = _ref1.length; _i < _len; _i++) {
    value = _ref1[_i];
    if (value != ""){
      _results.push($(create_value_dropdown(value)).appendTo($('#attribute_values')));
    }
  }
  return _results;
};

if (Object.keys(js_data.attributes).length){
  populate_sample_attributes_values_dropdown();
}

$('#exclude_menu').change(populate_sample_attributes_values_dropdown);
block_by_attribute_value = function() {
  var attribute_name, cell_class, exclude_by_value;
  attribute_name = $('#exclude_menu').val();
  exclude_by_value = $('#attribute_values').val();
  cell_class = ".column_name-" + attribute_name;
  return $(cell_class).each((function(_this) {
    return function(index, element) {
      var row;
      if ($.trim($(element).text()) === exclude_by_value) {
        row = $(element).parent('tr');
        return $(row).find(".trait-value-input").val("x");
      }
    };
  })(this));
};
$('#exclude_group').click(block_by_attribute_value);
block_by_index = function() {
  var end_index, error, index, index_list, index_set, index_string, start_index, _i, _j, _k, _len, _len1, _ref, _results;
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
  _results = [];
  let block_group = $('#block_group').val();
  if (block_group === "other") {
    table_api = $('#samples_other').DataTable();
  } else {
    table_api = $('#samples_primary').DataTable();
  }
  val_nodes = table_api.column(3).nodes().to$();
  for (_k = 0, _len1 = index_list.length; _k < _len1; _k++) {
    index = index_list[_k];
    val_nodes[index - 1].childNodes[0].value = "x";

  }
};

hide_no_value = function() {
  return $('.value_se').each((function(_this) {
    return function(_index, element) {
      if ($(element).find('.trait-value-input').val() === 'x') {
        return $(element).hide();
      }
    };
  })(this));
};
$('#hide_no_value').click(hide_no_value);

block_outliers = function() {
  return $('.outlier').each((function(_this) {
    return function(_index, element) {
      return $(element).find('.trait-value-input').val('x');
    };
  })(this));
};
$('#block_outliers').click(block_outliers);

reset_samples_table = function() {
  $('input[name="transform"]').val("");
  $('span[name="transform_text"]').text("")
  tables = ['samples_primary', 'samples_other'];
  for (_i = 0, _len = tables.length; _i < _len; _i++) {
    table = tables[_i];
    if ($('#' + table).length) {
      table_api = $('#' + table).DataTable();
      val_nodes = table_api.column(3).nodes().to$();
      for (i = 0; i < val_nodes.length; i++) {
        this_node = val_nodes[i].childNodes[0];
        this_node.value = this_node.attributes["data-value"].value;
      }
      if (js_data.se_exists){
        se_nodes = table_api.column(5).nodes().to$();
        for (i = 0; i < val_nodes.length; i++) {
          this_node = val_nodes[i].childNodes[0];
          this_node.value = this_node.attributes["data-value"].value;
        }
      }
    }
  }
};
$('.reset').click(function() {
  reset_samples_table();
  edit_data_change();
});

check_for_zero_to_one_vals = function() {
  tables = ['samples_primary', 'samples_other'];
  for (_i = 0, _len = tables.length; _i < _len; _i++) {
    table = tables[_i];
    if ($('#' + table).length) {
      table_api = $('#' + table).DataTable();
      val_nodes = table_api.column(3).nodes().to$();
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

log2_data = function(this_node) {
  current_value = this_node.value;
  original_value = this_node.attributes['data-value'].value;
  if(!isNaN(current_value) && !isNaN(original_value)) {
    if (zero_to_one_vals_exist){
      original_value = parseFloat(original_value) + 1;
    }
    this_node.value = Math.log2(original_value).toFixed(3);
  }
};

log10_data = function() {
  current_value = this_node.value;
  original_value = this_node.attributes['data-value'].value;
  if(!isNaN(current_value) && !isNaN(original_value)) {
    if (zero_to_one_vals_exist){
      original_value = parseFloat(original_value) + 1;
    }
    this_node.value = Math.log10(original_value).toFixed(3);
  }
};

sqrt_data = function() {
  current_value = this_node.value;
  original_value = this_node.attributes['data-value'].value;
  if(!isNaN(current_value) && !isNaN(original_value)) {
    if (zero_to_one_vals_exist){
      original_value = parseFloat(original_value) + 1;
    }
    this_node.value = Math.sqrt(original_value).toFixed(3);
  }
};

invert_data = function() {
  current_value = this_node.value;
  if(!isNaN(current_value)) {
    this_node.value = parseFloat(-(current_value)).toFixed(3);
  }
};

qnorm_data = function() {
  current_value = this_node.value;
  qnorm_value = this_node.attributes['data-qnorm'].value;
  if(!isNaN(current_value)) {
    this_node.value = qnorm_value;
  }
};

zscore_data = function() {
  current_value = this_node.value;
  zscore_value = this_node.attributes['data-zscore'].value;
  if(!isNaN(current_value)) {
    this_node.value = zscore_value;
  }
};

do_transform = function(transform_type) {
  tables = ['samples_primary', 'samples_other'];
  for (_i = 0, _len = tables.length; _i < _len; _i++) {
    table = tables[_i];
    if ($('#' + table).length) {
      table_api = $('#' + table).DataTable();
      val_nodes = table_api.column(3).nodes().to$();
      for (i = 0; i < val_nodes.length; i++) {
        this_node = val_nodes[i].childNodes[0]
        if (transform_type == "log2"){
          log2_data(this_node)
        }
        if (transform_type == "log10"){
          log10_data(this_node)
        }
        if (transform_type == "sqrt"){
          sqrt_data(this_node)
        }
        if (transform_type == "invert"){
          invert_data(this_node)
        }
        if (transform_type == "qnorm"){
          qnorm_data(this_node)
        }
        if (transform_type == "zscore"){
          zscore_data(this_node)
        }
      }
    }
  }
}

normalize_data = function() {
  if ($('#norm_method option:selected').val() == 'log2' || $('#norm_method option:selected').val() == 'log10'){
    if ($('input[name="transform"]').val() != "log2" && $('#norm_method option:selected').val() == 'log2') {
      do_transform("log2")
      $('input[name="transform"]').val("log2")
      $('span[name="transform_text"]').text(" - log2 Transformed")
    } else {
      if ($('input[name="transform"]').val() != "log10" && $('#norm_method option:selected').val() == 'log10'){
        do_transform("log10")
        $('input[name="transform"]').val("log10")
        $('span[name="transform_text"]').text(" - log10 Transformed")
      }
    }
  }
  else if ($('#norm_method option:selected').val() == 'sqrt'){
    if ($('input[name="transform"]').val() != "sqrt") {
      do_transform("sqrt")
      $('input[name="transform"]').val("sqrt")
      $('span[name="transform_text"]').text(" - Square Root Transformed")
    }
  }
  else if ($('#norm_method option:selected').val() == 'invert'){
    do_transform("invert")
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
      do_transform("qnorm")
      $('input[name="transform"]').val("qnorm")
      $('span[name="transform_text"]').text(" - Quantile Normalized")
    }
  }
  else if ($('#norm_method option:selected').val() == 'zscore'){
    if ($('input[name="transform"]').val() != "zscore") {
      do_transform("zscore")
      $('input[name="transform"]').val("zscore")
      $('span[name="transform_text"]').text(" - Z-Scores")
    }
  }
}

zero_to_one_vals_exist = check_for_zero_to_one_vals();

show_transform_warning = function() {
  transform_type = $('#norm_method option:selected').val()
  if (transform_type == "log2" || transform_type == "log10"){
    if (zero_to_one_vals_exist){
      $('#transform_alert').css("display", "block")
    }
  } else {
    $('#transform_alert').css("display", "none")
  }
}

$('#norm_method').change(function(){
  show_transform_warning()
});
$('#normalize').hover(function(){
  show_transform_warning()
});

$('#normalize').click(normalize_data)

switch_qnorm_data = function() {
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
$('#qnorm').click(switch_qnorm_data);
get_sample_table_data = function(table_name) {
  var samples;
  samples = [];

  var se_exists = false;
  var n_exists = false;

  if ($('#' + table_name).length){
    table_api = $('#' + table).DataTable();
    sample_vals = [];

    name_nodes = table_api.column(2).nodes().to$();
    val_nodes = table_api.column(3).nodes().to$();
    if (js_data.se_exists){
      var_nodes = table_api.column(5).nodes().to$();
      if (js_data.has_num_cases) {
        n_nodes = table_api.column(6).nodes().to$();
      }
    } else {
      if (js_data.has_num_cases){
        n_nodes = table_api.column(4).nodes().to$();
      }
    }

    for (_j = 0; _j < val_nodes.length; _j++){
      sample_val = val_nodes[_j].childNodes[0].value
      sample_name = $.trim(name_nodes[_j].childNodes[0].textContent)
      if (is_number(sample_val) && sample_val !== "") {
        sample_val = parseFloat(sample_val);
        if (typeof var_nodes == 'undefined'){
          sample_var = null;
        } else {
          sample_var = var_nodes[_j].childNodes[0].value;
          if (is_number(sample_var)) {
            sample_var = parseFloat(sample_var);
            se_exists = true;
          } else {
            sample_var = null;
          }
        }
        if (typeof n_nodes == 'undefined'){
          sample_n = null;
        } else {
          sample_n = n_nodes[_j].childNodes[0].value;
          if (is_number(sample_n)) {
            n_exists = true;
            sample_n = parseInt(sample_n);
          } else {
            sample_n = null;
          }
        }
        row_dict = {
          name: sample_name,
          value: sample_val,
          se: sample_var,
          num_cases: sample_n
        }
        samples.push(row_dict)
      }
    }
  }

  return samples;
};
export_sample_table_data = function() {
  var format, json_sample_data, sample_data;
  sample_data = {};
  sample_data.primary_samples = get_sample_table_data('samples_primary');
  sample_data.other_samples = get_sample_table_data('samples_other');
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

$('.export').click(export_sample_table_data);
$('#block_outliers').click(block_outliers);
_.mixin(_.str.exports());

get_sample_vals = function(sample_list) {
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

get_sample_errors = function(sample_list) {
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

get_sample_names = function(sample_list) {
  var sample;
  return this.sample_names = (function() {
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

get_bar_bottom_margin = function(sample_list){
  bottom_margin = 80
  max_length = 0
  sample_names = get_sample_names(sample_list)
  for (i=0; i < sample_names.length; i++){
    if (sample_names[i].length > max_length) {
      max_length = sample_names[i].length
    }
  }

  if (max_length > 6){
    bottom_margin += 11*(max_length - 6)
  }

  return bottom_margin;
}

root.stats_group = 'samples_primary';

if (Object.keys(js_data.sample_group_types).length > 1) {
    full_sample_lists = [sample_lists[0], sample_lists[1], sample_lists[0].concat(sample_lists[1])]
    sample_group_list = [js_data.sample_group_types['samples_primary'], js_data.sample_group_types['samples_other'], js_data.sample_group_types['samples_all']]
} else {
    full_sample_lists = [sample_lists[0]]
    sample_group_list = [js_data.sample_group_types['samples_primary']]
}

// Define Plotly Options (for the options bar at the top of each figure)

root.modebar_options = {
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
  modeBarButtonsToRemove:['toImage', 'hoverClosest', 'hoverCompare', 'hoverClosestCartesian', 'hoverCompareCartesian', 'lasso2d', 'toggleSpikelines', 'resetScale2d'],
  displaylogo: false
  //modeBarButtons:['toImage2', 'zoom2d', 'pan2d', 'select2d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d'],
}

// Bar Chart

root.errors_exist = get_sample_errors(sample_lists[0])[1]
var bar_trace = {
    x: get_sample_names(sample_lists[0]),
    y: get_sample_vals(sample_lists[0]),
    error_y: {
        type: 'data',
        array: get_sample_errors(sample_lists[0])[0],
        visible: root.errors_exist
    },
    type: 'bar'
}

root.bar_data = [bar_trace]

get_bar_range = function(sample_vals, sample_errors = null){
  positive_error_vals = []
  negative_error_vals = []
  for (i = 0;i < sample_vals.length; i++){
    if (sample_errors[i] != undefined) {
        positive_error_vals.push(sample_vals[i] + sample_errors[i])
        negative_error_vals.push(sample_vals[i] - sample_errors[i])
    } else {
        positive_error_vals.push(sample_vals[i])
        negative_error_vals.push(sample_vals[i])
    }
  }

  min_y_val = Math.min(...negative_error_vals)
  max_y_val = Math.max(...positive_error_vals)

  if (min_y_val == 0) {
    range_top = max_y_val + Math.abs(max_y_val)*0.1
    range_bottom = 0;
  } else {
    range_top = max_y_val + Math.abs(max_y_val)*0.1
    range_bottom = min_y_val - Math.abs(min_y_val)*0.1
    if (min_y_val > 0) {
        range_bottom = min_y_val - 0.1*Math.abs(min_y_val)
    } else if (min_y_val < 0) {
        range_bottom = min_y_val + 0.1*min_y_val
    } else {
        range_bottom = 0
    }
  }

  return [range_bottom, range_top]
}

root.chart_range = get_bar_range(get_sample_vals(sample_lists[0]), get_sample_errors(sample_lists[0])[0])
val_range = root.chart_range[1] - root.chart_range[0]

if (val_range < 0.05){
  tick_digits = '.3f'
  left_margin = 80
} else if (val_range < 0.5) {
  tick_digits = '.2f'
  left_margin = 70
} else if (val_range < 5){
  tick_digits = '.1f'
  left_margin = 60
} else {
  tick_digits = 'f'
  left_margin = 55
}

if (js_data.num_values < 256) {
  bar_chart_width = 25 * get_sample_vals(sample_lists[0]).length

  //ZS: Set bottom margin dependent on longest sample name length, since those can get long
  bottom_margin = get_bar_bottom_margin(sample_lists[0])

  root.bar_layout = {
    title: "<b>Trait " + js_data.trait_id + ": " + js_data.short_description + "</b>",
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
        tickformat: tick_digits,
        fixedrange: true
    },
    width: bar_chart_width,
    height: 600,
    margin: {
        l: left_margin,
        r: 30,
        t: 30,
        b: bottom_margin
    }
  };

  $('.bar_chart_tab').click(function() {
    update_bar_chart();
  });
}

total_sample_count = 0
for (i = 0, i < sample_lists.length; i++;) {
  total_sample_count += get_sample_vals(sample_lists[i]).length
}

// Histogram
var hist_trace = {
    x: get_sample_vals(sample_lists[0]),
    type: 'histogram'
};
root.histogram_data = [hist_trace];
root.histogram_layout = {
  bargap: 0.05,
  title: "<b>Trait " + js_data.trait_id + ": " + js_data.short_description + "</b>",
  xaxis: {
           autorange: true,
           title: js_data.unit_type,
           titlefont: {
             family: "arial",
             size: 20
           },
           ticklen: 4,
           tickfont: {
             size: 16
           }
         },
  yaxis: {
           autorange: true,
           title: "<b>Count</b>",
           titlefont: {
             family: "arial",
             size: 20
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
      l: 70,
      r: 30,
      t: 100,
      b: 50
  }
};

$('.histogram_tab').click(function() {
  update_histogram();
  update_histogram_width();
});

$('.histogram_samples_group').val(root.stats_group);
$('.histogram_samples_group').change(function() {
  root.stats_group = $(this).val();
  return update_histogram();
});

root.box_layout = {
    xaxis: {
        showline: true,
        titlefont: {
          family: "arial",
          size: 20
        },
        tickfont: {
          size: 16
        },
    },
    yaxis: {
        title: "<b>" + js_data.unit_type +"</b>",
        autorange: true,
        showline: true,
        titlefont: {
          family: "arial",
          size: 20
        },
        ticklen: 4,
        tickfont: {
          size: 16
        },
        tickformat: tick_digits,
        zeroline: false,
        automargin: true
    },
    margin: {
        l: 90,
        r: 30,
        t: 30,
        b: 80
    }
};
if (full_sample_lists.length > 1) {
    root.box_layout['width'] = 600;
    root.box_layout['height'] = 500;
    var trace1 = {
        y: get_sample_vals(full_sample_lists[0]),
        type: 'box',
        name: sample_group_list[0],
        boxpoints: 'Outliers',
        jitter: 0.5,
        whiskerwidth: 0.2,
        fillcolor: 'cls',
        pointpos: -3,
        marker: {
            color: 'blue',
            size: 3
        },
        line: {
            width: 1
        }
    }
    var trace2 = {
        y: get_sample_vals(full_sample_lists[1]),
        type: 'box',
        name: sample_group_list[1],
        boxpoints: 'Outliers',
        jitter: 0.5,
        whiskerwidth: 0.2,
        fillcolor: 'cls',
        pointpos: -3,
        marker: {
            color: 'red',
            size: 3
        },
        line: {
            width: 1
        }
    }
    var trace3 = {
        y: get_sample_vals(full_sample_lists[2]),
        type: 'box',
        name: sample_group_list[2],
        boxpoints: 'Outliers',
        jitter: 0.5,
        whiskerwidth: 0.2,
        fillcolor: 'cls',
        pointpos: -3,
        marker: {
            color: 'green',
            size: 3
        },
        line: {
            width: 1
        }
    }
    root.box_data = [trace1, trace2, trace3]
} else {
    root.box_layout['width'] = 300;
    root.box_layout['height'] = 400;
    root.box_data = [
      {
        type: 'box',
        y: get_sample_vals(full_sample_lists[0]),
        name: "<b>Trait " + js_data.trait_id + "</b>",
        boxpoints: 'Outliers',
        jitter: 0.5,
        whiskerwidth: 0.2,
        fillcolor: 'cls',
        pointpos: -3,
        marker: {
            size: 3
        },
        line: {
            width: 1
        }
      }
    ]
}

box_obj = {
  data: box_data,
  layout: root.box_layout
}

$('.box_plot_tab').click(function() {
  update_box_plot();
});

// Violin Plot

root.violin_layout = {
  xaxis: {
      showline: true,
      titlefont: {
        family: "arial",
        size: 20
      },
      tickfont: {
        size: 16
      }
  },
  yaxis: {
      title: "<b>"+js_data.unit_type+"</b>",
      autorange: true,
      showline: true,
      titlefont: {
        family: "arial",
        size: 20
      },
      ticklen: 4,
      tickfont: {
        size: 16
      },
      tickformat: tick_digits,
      zeroline: false,
      automargin: true
  },
  margin: {
        l: 90,
        r: 30,
        t: 30,
        b: 80
  }
};

if (full_sample_lists.length > 1) {
    root.violin_layout['width'] = 600;
    root.violin_layout['height'] = 500;
    var trace1 = {
        y: get_sample_vals(full_sample_lists[2]),
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
        name: sample_group_list[2],
        x0: sample_group_list[2]
    }
    var trace2 = {
        y: get_sample_vals(full_sample_lists[1]),
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
        name: sample_group_list[1],
        x0: sample_group_list[1]
    }
    var trace3 = {
        y: get_sample_vals(full_sample_lists[0]),
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
        name: sample_group_list[0],
        x0: sample_group_list[0]
    }
    root.violin_data = [trace1, trace2, trace3]
} else {
    root.violin_layout['width'] = 300;
    root.violin_layout['height'] = 400;
    root.violin_data = [
      {
        y: get_sample_vals(full_sample_lists[0]),
        type: 'violin',
        points: 'none',
        box: {
          visible: true
        },
        meanline: {
          visible: true
        },
        name: "<b>Trait " + js_data.trait_id + "</b>",
        x0: "<b>Trait " + js_data.trait_id + "</b>"
      }
    ]
}

$('.violin_plot_tab').click(function() {
  update_violin_plot();
});

if (get_sample_vals(sample_lists[0]).length < 256) {
  $('.bar_chart_samples_group').change(function() {
    root.stats_group = $(this).val();
    return update_bar_chart();
  });
  root.bar_sort = "name"
}
$('.sort_by_name').click(function() {
  root.bar_sort = "name"
  return update_bar_chart();
});
$('.sort_by_value').click(function() {
  root.bar_sort = "value"
  return update_bar_chart();
});

root.prob_plot_group = 'samples_primary';
$('.prob_plot_samples_group').val(root.prob_plot_group);
$('.prob_plot_tab').click(function() {
  return update_prob_plot();
});
$('.prob_plot_samples_group').change(function() {
  root.prob_plot_group = $(this).val();
  return update_prob_plot();
});

function isEmpty( el ){
  return !$.trim(el.html())
}

$('.stats_panel').click(function() {
  if (isEmpty($('#stats_table'))){
    make_table();
    edit_data_change();
  } else {
    edit_data_change();
  }
});

$('#block_by_index').click(function(){
  block_by_index();
  edit_data_change();
});
$('#exclude_group').click(edit_data_change);
$('#block_outliers').click(edit_data_change);
$('#reset').click(edit_data_change);
$('#qnorm').click(edit_data_change);
$('#normalize').click(edit_data_change);

Number.prototype.countDecimals = function () {
  if(Math.floor(this.valueOf()) === this.valueOf()) return 0;
    return this.toString().split(".")[1].length || 0;
}