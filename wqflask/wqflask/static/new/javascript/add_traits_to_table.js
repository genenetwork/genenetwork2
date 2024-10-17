var add_trait_data, assemble_into_json, back_to_collections, collection_click, collection_list, create_trait_data_csv, get_this_trait_vals, get_trait_data, process_traits, submit_click, this_trait_data, trait_click,
  __indexOf = [].indexOf || function(item) { for (var i = 0, l = this.length; i < l; i++) { if (i in this && this[i] === item) return i; } return -1; };

this_trait_data = null;

var selected_traits = {};

var attributeStartPos = 3;
if (js_data.se_exists) {
  attributeStartPos += 2;
}
if (js_data.has_num_cases === true) {
  attributeStartPos += 1;
}

$('#collections_list').attr("style", "width: 100%;");
$('#trait_table').dataTable( {
    "drawCallback": function( settings ) {
         $('#trait_table tr').click(function(event) {
             if (event.target.type !== 'checkbox') {
                 $(':checkbox', this).trigger('click');
             }
         });
    },
    "columns": [
        { "type": "natural", "width": "3%" },
        { "type": "natural", "width": "8%" },
        { "type": "natural", "width": "20%" },
        { "type": "natural", "width": "25%" },
        { "type": "natural", "width": "25%" },
        { "type": "natural", "width": "15%" }
    ],
    "columnDefs": [ {
        "targets": 0,
        "orderable": false
    } ],
    "order": [[1, "asc" ]],
    "sDom": "RZtr",
    "iDisplayLength": -1,
    "autoWidth": true,
    "bDeferRender": true,
    "bSortClasses": false,
    "paging": false,
    "orderClasses": true
} );

if ( ! $.fn.DataTable.isDataTable( '#collection_table' ) ) {
  $('#collection_table').dataTable( {
    "createdRow": function ( row, data, index ) {
        if ($('td', row).eq(2).text().length > 40) {
            $('td', row).eq(2).text($('td', row).eq(2).text().substring(0, 40));
            $('td', row).eq(2).text($('td', row).eq(2).text() + '...')
        }
        if ($('td', row).eq(4).text().length > 50) {
            $('td', row).eq(4).text($('td', row).eq(4).text().substring(0, 50));
            $('td', row).eq(4).text($('td', row).eq(4).text() + '...')
        }
    },
    "columnDefs": [ {
        "targets": 0,
        "orderable": false
    } ],
    "order": [[1, "asc" ]],
    "sDom": "ZRtr",
    "iDisplayLength": -1,
    "autoWidth": true,
    "bSortClasses": false,
    "paging": false,
    "orderClasses": true
  } );
}

collection_click = function() {
  var this_collection_url;
  this_collection_url = $(this).find('.collection_name').prop("href");
  this_collection_url += "&json";
  collection_list = $("#collections_holder").html();
  return $.ajax({
    dataType: "json",
    url: this_collection_url,
    success: process_traits
  });
};

submit_click = function() {
  var sample, samples, scatter_matrix, this_trait_vals, trait, trait_names, trait_vals_csv, traits, _i, _j, _len, _len1, _ref;
  new_data = js_data['sample_lists'];
  traits = [];
  $('#collections_holder').find('input[type=checkbox]:checked').each(function() {
    var this_dataset, this_trait, this_trait_url;
    this_trait = $(this).parents('tr').find('.trait').text();
    this_dataset = $(this).parents('tr').find('.dataset').data("dataset");
    this_trait_url = "/trait/get_sample_data?trait=" + this_trait + "&dataset=" + this_dataset;
    return $.ajax({
      dataType: "json",
      url: this_trait_url,
      async: false,
      success: add_trait_data
    });
  });

  tableIds = ["samples_primary"]
  $('#primary_container').width($('#primary_container').width() + 40*Object.keys(selected_traits).length)
  if (js_data.sample_lists.length > 1) {
    tableIds.push("samples_other")
    $('#other_container').width($('#primary_container').width() + 40*selected_traits.length)
  }

  for (var i = 0; i < tableIds.length; i++) {
    for (var j = 0; j < js_data['sample_lists'][i].length; j++){
        for (const [key, value] of Object.entries(selected_traits)) {
            if (js_data['sample_lists'][i][j].name in selected_traits[key]){
                new_data[i][j][key] = selected_traits[key][js_data['sample_lists'][i][j].name]
            } else {
                new_data[i][j][key] = "x"
            }
        }
    }
  }

  attrIds = Object.keys(js_data.attributes).sort((a, b) => (parseInt(js_data.attributes[a].id) > parseInt(js_data.attributes[b].id)) ? 1 : -1)
  maxAttrId = attrIds[attrIds.length - 1]

  i = 0;
  for (const [key, _value] of Object.entries(selected_traits)) {
    let distinctVals = [...new Set(Object.keys(selected_traits[key]).map((key2) => selected_traits[key][key2]))];

    js_data.attributes[parseInt(maxAttrId) + i] = {
      id: (parseInt(maxAttrId) + i).toString(),
      name: key,
      description: key,
      distinct_values: distinctVals,
      alignment: 'right',
      data: key
    }

    $('#filter_column').append(new Option(key, attributeStartPos + i))

    if (distinctVals.length <= 10 && distinctVals.length > 1) {
      $('#exclude_column').append(new Option(key, attrIds.length + i))
    }

    i++;
  }

  initialize_show_trait_tables(new_data=new_data)
  populateSampleAttributesValuesDropdown();

  return $.colorbox.close();
};

trait_click = function() {
  var dataset, this_trait_url, trait;

  trait = $(this).parent().find('.trait').text();
  dataset = $(this).parent().find('.dataset').text();
  this_trait_url = "/trait/get_sample_data?trait=" + trait + "&dataset=" + dataset;
  $.ajax({
    dataType: "json",
    url: this_trait_url,
    success: get_trait_data
  });
  return $.colorbox.close();
};

trait_row_click = function() {
  var dataset, this_trait_url, trait;
  trait = $(this).find('.trait').text();
  dataset = $(this).find('.dataset').data("dataset");
  this_trait_url = "/trait/get_sample_data?trait=" + trait + "&dataset=" + dataset;
  $.ajax({
    dataType: "json",
    url: this_trait_url,
    success: get_trait_data
  });
  return $.colorbox.close();
};

add_trait_data = function(trait_data) {
  selected_traits[trait_data[0].name] = trait_data[1];
  return false;
};

get_trait_data = function(trait_data) {
  var sample, samples, this_trait_vals, trait_sample_data, vals, _i, _len;
  trait_sample_data = trait_data[1];
  if ( $('input[name=allsamples]').length ) {
    samples = $('input[name=allsamples]').val().split(" ");
  } else {
    samples = js_data.indIDs
  }
  sample_vals = [];
  vals = [];
  for (_i = 0, _len = samples.length; _i < _len; _i++) {
    sample = samples[_i];
    if (sample in trait_sample_data) {
      sample_vals.push(sample + ":" + parseFloat(trait_sample_data[sample]))
      vals.push(parseFloat(trait_sample_data[sample]))
    } else {
      sample_vals.push(null)
      vals.push(null)
    }
  }
  if ( $('input[name=allsamples]').length ) {
    if ($('input[name=samples]').length < 1) {
      $('#hidden_inputs').append('<input type="hidden" name="samples" value="[' + samples.toString() + ']" />');
    }
    $('#hidden_inputs').append('<input type="hidden" name="vals" value="[' + vals.toString() + ']" />');
    this_trait_vals = get_this_trait_vals(samples);
    return color_by_trait(trait_sample_data);
  } else{
    sorted = vals.slice().sort(function(a,b){return a-b})
    ranks = vals.slice().map(function(v){ return sorted.indexOf(v)+1 });
    sample_ranks = []
    for (_i = 0; _i < samples.length; _i++){
      if (samples[_i] in trait_sample_data){
        sample_ranks.push(samples[_i] + ":" + ranks[_i])
      } else {
        sample_ranks.push(null)
      }
    }
    return false
  }
};

get_this_trait_vals = function(samples) {
  var sample, this_trait_vals, this_val, this_vals_json, _i, _len;
  this_trait_vals = [];
  for (_i = 0, _len = samples.length; _i < _len; _i++) {
    sample = samples[_i];
    this_val = parseFloat($("input[name='value:" + sample + "']").val());
    if (!isNaN(this_val)) {
      this_trait_vals.push(this_val);
    } else {
      this_trait_vals.push(null);
    }
  }
  this_vals_json = '[' + this_trait_vals.toString() + ']';
  return this_trait_vals;
};

assemble_into_json = function(this_trait_vals) {
  var json_data, json_ids, num_traits, samples;
  num_traits = $('input[name=vals]').length;
  samples = $('input[name=samples]').val();
  json_ids = samples;
  json_data = '[' + this_trait_vals;
  $('input[name=vals]').each((function(_this) {
    return function(index, element) {
      return json_data += ',' + $(element).val();
    };
  })(this));
  json_data += ']';
  return [json_ids, json_data];
};

process_traits = function(trait_data, textStatus, jqXHR) {
  var the_html, trait, _i, _len;
  the_html = "<button id='back_to_collections' class='btn btn-inverse btn-small'>";
  the_html += "<i class='icon-white icon-arrow-left'></i> Back </button>";
  the_html += "    <button id='submit_cofactors' class='btn btn-primary btn-small submit'> Submit </button>";
  the_html += "<table id='collection_table' style='padding-top: 10px;' class='table table-hover'>";
  the_html += "<thead><tr><th></th><th>Record</th><th>Data Set</th><th>Description</th></tr></thead>";
  the_html += "<tbody>";
  for (_i = 0, _len = trait_data.length; _i < _len; _i++) {
    trait = trait_data[_i];
    the_html += "<tr class='trait_line'>";
    the_html += "<td class='select_trait'><input type='checkbox' name='selectCheck' class='checkbox edit_sample_checkbox'></td>";
    if ("abbreviation" in trait) {
        the_html += "<td class='trait' data-display_name='" + trait.name + " - " + trait.abbreviation + "'>" + trait.name + "</td>";
    } else if ("symbol" in trait) {
      the_html += "<td class='trait' data-display_name='" + trait.name + " - " + trait.symbol + "'>" + trait.name + "</td>";
    } else {
      the_html += "<td class='trait' data-display_name='" + trait.name + "'>" + trait.name + "</td>";
    }
    the_html += "<td class='dataset' data-dataset='" + trait.dataset + "'>" + trait.dataset_name + "</td>";
    the_html += "<td class='description'>" + trait.description + "</td>";
  }
  the_html += "</tbody>";
  the_html += "</table>";
  the_html += "<script type='text/javascript' src='/static/new/javascript/add_traits_to_table.js'></script>"
  $("#collections_holder").html(the_html);
  return $('#collections_holder').colorbox.resize();
};

back_to_collections = function() {
  $("#collections_holder").html(collection_list);
  $(document).on("click", ".collection_line", collection_click);
  return $('#collections_holder').colorbox.resize();
};

$(".collection_line").on("click", collection_click);
$("#submit_cofactors").on("click", submit_click);

if ($('#scatterplot2').length){
  $(".trait_line").on("click", trait_row_click);
} else {
  $(".trait").on("click", trait_click);
}
$("#back_to_collections").on("click", back_to_collections);
