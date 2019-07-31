var chart;
var srchart;

x_val_range = js_data.x_range[1] - js_data.x_range[0]
y_val_range = js_data.y_range[1] - js_data.y_range[0]

if (x_val_range >= 2 && x_val_range < 9){
  x_tick_digits = '.1f'
} else if (x_val_range >= 0.8 && x_val_range < 2) {
  x_tick_digits = '.2f'
} else if (x_val_range < 0.8) {
  x_tick_digits = '.3f'
} else {
  x_tick_digits = 'f'
}

if (y_val_range >= 2 && y_val_range < 8){
  y_tick_digits = '.1f'
} else if (y_val_range >= 0.8 && y_val_range < 2) {
  y_tick_digits = '.2f'
} else if (y_val_range < 0.8) {
  y_tick_digits = '.3f'
} else {
  y_tick_digits = 'f'
}

console.log("y_digits:", y_tick_digits)

var layout = {
    height: 700,
    width: 800,
    margin: {
        l: 70,
        r: 30,
        t: 90,
        b: 50
    },
    xaxis: {
        range: [js_data.x_range[0], js_data.x_range[1]],
        title: js_data.trait_1,
        zeroline: false,
        visible: true,
        linecolor: 'black',
        linewidth: 1,
        ticklen: 4,
        tickformat: x_tick_digits
    },
    yaxis: {
        range: [js_data.y_range[0], js_data.y_range[1]],
        title: js_data.trait_2,
        zeroline: false,
        visible: true,
        linecolor: 'black',
        linewidth: 1,
        ticklen: 4,
        tickformat: y_tick_digits,
        automargin: true
    },
    hovermode: "closest",
    showlegend: false,
    annotations:[{
      xref: 'paper',
      yref: 'paper',
      x: 1,
      xanchor: 'right',
      y: 1.05,
      yanchor: 'top',
      text: '<i>r</i> = ' + js_data.r_value.toFixed(3) + ', <i>p</i> = ' + js_data.p_value.toExponential(3) + ', <i>n</i> = ' + js_data.num_overlap,
      showarrow: false,
      font: {
        size: 14
      },
    }
  ]
}

var sr_layout = {
  height: 700,
  width: 800,
  margin: {
      l: 60,
      r: 30,
      t: 80,
      b: 50
  },
  xaxis: {
      range: [js_data.sr_range[0], js_data.sr_range[1]],
      title: js_data.trait_1,
      zeroline: false,
      visible: true,
      linecolor: 'black',
      linewidth: 1,
  },
  yaxis: {
      range: [js_data.sr_range[0], js_data.sr_range[1]],
      title: js_data.trait_2,
      zeroline: false,
      visible: true,
      linecolor: 'black',
      linewidth: 1,
  },
  hovermode: "closest",
  showlegend: false,
  annotations:[{
    xref: 'paper',
    yref: 'paper',
    x: 1,
    xanchor: 'right',
    y: 1.05,
    yanchor: 'top',
    text: '<i>r</i> = ' + js_data.srr_value.toFixed(3) + ', <i>P</i> = ' + js_data.srp_value.toExponential(3) + ', <i>n</i> = ' + js_data.num_overlap,
    showarrow: false,
    font: {
      size: 14
    },
  }
]
}

cofactor1_dict = {}
ranked_cofactor1_dict = {}
//cofactor1_values = []
//ranked_cofactor1_values = []
cofactor2_dict = {}
ranked_cofactor2_dict = {}
//cofactor2_values = []
//ranked_cofactor2_values = []
cofactor3_dict = {}
ranked_cofactor3_dict = {}

function drawg() {
    x_values = []
    y_values = []
    sample_names = []
    for (j = 0; j < js_data.data[0].length; j++) {
      x_values.push(js_data.data[0][j])
      y_values.push(js_data.data[1][j])
      sample_names.push(js_data.indIDs[j])
    }

    var trace1 = {
        x: x_values,
        y: y_values,
        mode: 'markers',
        text: sample_names
    }

    var trace2 = {
      x: [js_data.intercept_coords[0][0], js_data.intercept_coords[1][0]],
      y: [js_data.intercept_coords[0][1], js_data.intercept_coords[1][1]],
      mode: 'lines',
      line: {
        color: 'rgb(250, 60, 73)'
      }
    }

    Plotly.newPlot('scatterplot2', [trace2, trace1], layout)

}

function srdrawg() {
    x_values = []
    y_values = []
    sample_names = []
    for (j = 0; j < js_data.rdata[0].length; j++) {
      x_values.push(js_data.rdata[0][j])
      y_values.push(js_data.rdata[1][j])
      sample_names.push(js_data.indIDs[j])
    }

    var trace1 = {
        x: x_values,
        y: y_values,
        mode: 'markers',
        text: sample_names
    }

    Plotly.newPlot('srscatterplot2', [trace1], sr_layout)
}

function getdata() {
    var data = [];
    data.push({
            values: [],
            slope: js_data.slope,
            intercept: js_data.intercept
        });

    sizemin = 8;
    sizemax = 30;

    samples1 = [];
    samples2 = [];
    samples3 = [];

    if ($('input[name=cofactor1_vals]').val()){
        vals1 = []
        val_sample_dict = {}
        val_sample_pairs = $('input[name=cofactor1_vals]').val().split(",")
        for (i=0; i < val_sample_pairs.length; i++) {
          samples1.push(val_sample_pairs[i].split(":")[0])
          vals1.push(parseFloat(val_sample_pairs[i].split(":")[1]))
          val_sample_dict[val_sample_pairs[i].split(":")[0]] = parseFloat(val_sample_pairs[i].split(":")[1])
        }
        datamin1 = d3.min(vals1);
        datamax1 = d3.max(vals1);

        cofactor1_dict = val_sample_dict
        cofactor1_values = vals1
    }

    if ($('input[name=cofactor2_vals]').val()){
        vals2 = [];
        val_sample_dict = {}
        val_sample_pairs = $('input[name=cofactor2_vals]').val().split(",")
        for (i=0; i < val_sample_pairs.length; i++) {
          samples2.push(val_sample_pairs[i].split(":")[0])
          vals2.push(parseFloat(val_sample_pairs[i].split(":")[1]))
          val_sample_dict[val_sample_pairs[i].split(":")[0]] = val_sample_pairs[i].split(":")[1]
        }
        datamin2 = d3.min(vals2);
        datamax2 = d3.max(vals2);

        cofactor2_dict = val_sample_dict
        cofactor2_values = vals2
    }

    if ($('input[name=cofactor3_vals]').val()){
        vals3 = [];
        val_sample_dict = {}
        val_sample_pairs = $('input[name=cofactor3_vals]').val().split(",")
        for (i=0; i < val_sample_pairs.length; i++) {
          samples3.push(val_sample_pairs[i].split(":")[0])
          vals3.push(parseFloat(val_sample_pairs[i].split(":")[1]))
          val_sample_dict[val_sample_pairs[i].split(":")[0]] = val_sample_pairs[i].split(":")[1]
        }

        datamin3 = d3.min(vals3);
        datamax3 = d3.max(vals3);

        cofactor3_dict = val_sample_dict
        cofactor3_values = vals3
    }

    x_values = []
    y_values = []
    sample_names = []
    sizes = []

    size_cofactor_vals = []
    if ($('#cofactor1_type option:selected').val() == "size" && $('input[name=cofactor1_vals]').val()){
      size_cofactor_vals = cofactor1_values
      cofactor_samples = samples1
      datamin = datamin1
      datamax = datamax1
    } else if ($('#cofactor2_type option:selected').val() == "size" && $('input[name=cofactor2_vals]').val()) {
      size_cofactor_vals = cofactor2_values
      cofactor_samples = samples2
      datamin = datamin2
      datamax = datamax2
    } else if ($('#cofactor3_type option:selected').val() == "size" && $('input[name=cofactor3_vals]').val()) {
      size_cofactor_vals = cofactor3_values
      cofactor_samples = samples3
      datamin = datamin3
      datamax = datamax3
    }

    unique_vals = []
    symbol_cofactor_vals = []
    if ($('#cofactor1_type option:selected').val() == "symbol" && $('input[name=cofactor1_vals]').val()){
      symbol_cofactor_vals = cofactor1_values
      cofactor_samples = samples1
    } else if ($('#cofactor2_type option:selected').val() == "symbol" && $('input[name=cofactor2_vals]').val()) {
      symbol_cofactor_vals = cofactor2_values
      cofactor_samples = samples2
    } else if ($('#cofactor3_type option:selected').val() == "symbol" && $('input[name=cofactor3_vals]').val()) {
      symbol_cofactor_vals = cofactor3_values
      cofactor_samples = samples3
    }

    symbol_list = []
    if (symbol_cofactor_vals.length > 0) {
      unique_vals = [...new Set(symbol_cofactor_vals)]
      for (i=0; i<symbol_cofactor_vals.length; i++){
        val_pos = unique_vals.indexOf(symbol_cofactor_vals[i])
        if (val_pos != "-1") {
          symbol_list.push(val_pos)
        } else {
          symbol_list.push(0)
        }
      }
    }

    //This is needed to calculate samples shared by cofactors
    cofactor_samples_array = []
    if (samples1.length > 0){
      cofactor_samples_array.push(samples1)
    }
    if (samples2.length > 0){
      cofactor_samples_array.push(samples2)
    }
    if (samples3.length > 0){
      cofactor_samples_array.push(samples3)
    }
    if (cofactor_samples_array.length > 0){
      shared_samples = _.intersection.apply(_, cofactor_samples_array)
    } else {
      shared_samples = js_data.indIDs
    }

    for (j = 0; j < js_data.data[0].length; j++) {

        if (shared_samples.indexOf(js_data.indIDs[j]) == -1) {
          continue
        }

        if (size_cofactor_vals.length > 0){
          if (cofactor_samples.indexOf(js_data.indIDs[j])) {
            datav = size_cofactor_vals[j]
            sizev = map1to2(datamin, datamax, sizemin, sizemax, datav);
          }
        } else {
            datav = 0;
            sizev = 10;
        }

        x_values.push(js_data.data[0][j])
        y_values.push(js_data.data[1][j])
        sample_names.push(js_data.indIDs[j])
        sizes.push(sizev)

        data[0].values.push({
            type: "normal",
            x: js_data.data[0][j],
            y: js_data.data[1][j],
            name: js_data.indIDs[j],
            size: sizev,
            v3: datav
        });
    }

    point_text = []
    for (j = 0; j < sample_names.length; j++) {
      this_text = ""
      this_text += sample_names[j]
      if (sample_names[j] in cofactor1_dict){
        this_text += "<br>Cofactor 1: " + cofactor1_dict[sample_names[j]]
      }
      if (sample_names[j] in cofactor2_dict){
        this_text += "<br>Cofactor 2: " + cofactor2_dict[sample_names[j]]
      }
      if (sample_names[j] in cofactor3_dict){
        this_text += "<br>Cofactor 3: " + cofactor3_dict[sample_names[j]]
      }
      point_text.push(this_text)
    }

    if (symbol_list.length > 0) {
      var trace1 = {
        x: x_values,
        y: y_values,
        mode: 'markers',
        text: point_text,
        marker: {
          color: 'rgb(66, 66, 245)',
          symbol: symbol_list,
          size: sizes
        }
      }
    } else {
      var trace1 = {
        x: x_values,
        y: y_values,
        mode: 'markers',
        text: point_text,
        marker: {
          color: 'rgb(66, 66, 245)',
          size: sizes
        }
      }
    }

    var trace2 = {
      x: [js_data.intercept_coords[0][0], js_data.intercept_coords[1][0]],
      y: [js_data.intercept_coords[0][1], js_data.intercept_coords[1][1]],
      mode: 'lines',
      line: {
        color: 'rgb(250, 60, 73)'
      }
    }

    return [trace2, trace1];
}

function map1to2 (min1, max1, min2, max2, v1) {
    v2 = (v1 - min1) * (max2 - min2) / (max1 - min1) + min2;
    return v2;
}

function srgetdata() {
    var data = [];
    data.push({
            values: [],
            slope: js_data.srslope,
            intercept: js_data.srintercept
        });

    sizemin = 8;
    sizemax = 30;

    ranked_cofactor_vals = ""

    samples1 = [];
    samples2 = [];
    samples3 = [];

    if ($('input[name=ranked_cofactor1_vals]').val()){
        vals1 = []
        val_sample_dict = {}
        val_sample_pairs = $('input[name=ranked_cofactor1_vals]').val().split(",")
        for (i=0; i < val_sample_pairs.length; i++) {
          samples1.push(val_sample_pairs[i].split(":")[0])
          vals1.push(parseFloat(val_sample_pairs[i].split(":")[1]))
          val_sample_dict[val_sample_pairs[i].split(":")[0]] = parseFloat(val_sample_pairs[i].split(":")[1])
        }
        datamin1 = d3.min(vals1);
        datamax1 = d3.max(vals1);

        ranked_cofactor1_dict = val_sample_dict
        ranked_cofactor1_values = vals1
    }

    if ($('input[name=ranked_cofactor2_vals]').val()){
        vals2 = [];
        val_sample_dict = {}
        val_sample_pairs = $('input[name=ranked_cofactor2_vals]').val().split(",")
        for (i=0; i < val_sample_pairs.length; i++) {
          samples2.push(val_sample_pairs[i].split(":")[0])
          vals2.push(parseFloat(val_sample_pairs[i].split(":")[1]))
          val_sample_dict[val_sample_pairs[i].split(":")[0]] = val_sample_pairs[i].split(":")[1]
        }
        datamin2 = d3.min(vals2);
        datamax2 = d3.max(vals2);

        ranked_cofactor2_dict = val_sample_dict
        ranked_cofactor2_values = vals2
    }

    if ($('input[name=ranked_cofactor3_vals]').val()){
        vals3 = [];
        val_sample_dict = {}
        val_sample_pairs = $('input[name=ranked_cofactor3_vals]').val().split(",")
        for (i=0; i < val_sample_pairs.length; i++) {
          samples3.push(val_sample_pairs[i].split(":")[0])
          vals3.push(parseFloat(val_sample_pairs[i].split(":")[1]))
          val_sample_dict[val_sample_pairs[i].split(":")[0]] = val_sample_pairs[i].split(":")[1]
        }

        datamin3 = d3.min(vals3);
        datamax3 = d3.max(vals3);

        ranked_cofactor3_dict = val_sample_dict
        ranked_cofactor3_values = vals3
    }

    x_values = []
    y_values = []
    sample_names = []
    sizes = []

    if ($('#cofactor1_type option:selected').val() == "size" && $('input[name=ranked_cofactor1_vals]').val()){
      size_cofactor_vals = ranked_cofactor1_values
      cofactor_samples = samples1
      datamin = datamin1
      datamax = datamax1
    } else if ($('#cofactor2_type option:selected').val() == "size" && $('input[name=ranked_cofactor2_vals]').val()) {
      size_cofactor_vals = ranked_cofactor2_values
      cofactor_samples = samples2
      datamin = datamin2
      datamax = datamax2
    } else if ($('#cofactor3_type option:selected').val() == "size" && $('input[name=ranked_cofactor3_vals]').val()) {
      size_cofactor_vals = ranked_cofactor3_values
      cofactor_samples = samples3
      datamin = datamin3
      datamax = datamax3
    }

    unique_vals = []
    symbol_cofactor_vals = []
    if ($('#cofactor1_type option:selected').val() == "symbol" && $('input[name=ranked_cofactor1_vals]').val()){
      symbol_cofactor_vals = cofactor1_values
      cofactor_samples = samples1
    } else if ($('#cofactor2_type option:selected').val() == "symbol" && $('input[name=ranked_cofactor2_vals]').val()) {
      symbol_cofactor_vals = cofactor2_values
      cofactor_samples = samples2
    } else if ($('#cofactor3_type option:selected').val() == "symbol" && $('input[name=ranked_cofactor3_vals]').val()) {
      symbol_cofactor_vals = cofactor3_values
      cofactor_samples = samples3
    }

    symbol_list = []
    if (symbol_cofactor_vals.length > 0) {
      unique_vals = [...new Set(symbol_cofactor_vals)]
      for (i=0; i<symbol_cofactor_vals.length; i++){
        val_pos = unique_vals.indexOf(symbol_cofactor_vals[i])
        if (val_pos != "-1") {
          symbol_list.push(val_pos)
        } else {
          symbol_list.push(0)
        }
      }
    }

    //This is needed to calculate samples shared by cofactors
    cofactor_samples_array = []
    if (samples1.length > 0){
      cofactor_samples_array.push(samples1)
    }
    if (samples2.length > 0){
      cofactor_samples_array.push(samples2)
    }
    if (samples3.length > 0){
      cofactor_samples_array.push(samples3)
    }
    if (cofactor_samples_array.length > 0){
      shared_samples = _.intersection.apply(_, cofactor_samples_array)
    } else {
      shared_samples = js_data.indIDs
    }

    for (j = 0; j < js_data.rdata[0].length; j++) {

        if (shared_samples.indexOf(js_data.indIDs[j]) == -1) {
          continue
        }

        if (size_cofactor_vals.length > 0){
          if (cofactor_samples.indexOf(js_data.indIDs[j])) {
            datav = size_cofactor_vals[j]
            sizev = map1to2(datamin, datamax, sizemin, sizemax, datav);
          }
        } else {
            sizev = 10;
        }

        x_values.push(js_data.rdata[0][j])
        y_values.push(js_data.rdata[1][j])
        sample_names.push(js_data.indIDs[j])
        sizes.push(sizev)

        data[0].values.push({
            type: "ranked",
            x: js_data.rdata[0][j],
            y: js_data.rdata[1][j],
            name: js_data.indIDs[j],
            size: sizev,
        });
    }

    point_text = []
    for (j = 0; j < sample_names.length; j++) {
      this_text = ""
      this_text += sample_names[j]
      if (sample_names[j] in ranked_cofactor1_dict){
        this_text += "<br>Cofactor 1: " + ranked_cofactor1_dict[sample_names[j]]
      }
      if (sample_names[j] in ranked_cofactor2_dict){
        this_text += "<br>Cofactor 2: " + ranked_cofactor2_dict[sample_names[j]]
      }
      if (sample_names[j] in cofactor3_dict){
        this_text += "<br>Cofactor 3: " + ranked_cofactor3_dict[sample_names[j]]
      }
      point_text.push(this_text)
    }

    var trace1 = {
        x: x_values,
        y: y_values,
        mode: 'markers',
        text: point_text,
        marker: {
          color: 'rgb(66, 66, 245)',
          symbol: symbol_list,
          size: sizes
        }
    }

    var trace2 = {
      x: [js_data.sr_intercept_coords[0][0], js_data.sr_intercept_coords[1][0]],
      y: [js_data.sr_intercept_coords[0][1], js_data.sr_intercept_coords[1][1]],
      mode: 'lines',
      line: {
        color: 'rgb(250, 60, 73)'
      }
    }

    return [trace2, trace1];
}

function chartupdatewh() {
    var width = $("#width").val();
    var height = $("#height").val();

    width_height_update = {
      height: height,
      width: width
    }

    Plotly.newPlot('scatterplot2', getdata(), layout)
    Plotly.relayout('scatterplot2', width_height_update)

    Plotly.newPlot('srscatterplot2', srgetdata(), sr_layout)
    Plotly.relayout('srscatterplot2', width_height_update)
}

function colorer(d) {
    if ($('#cofactor1_type option:selected').val() == "color"){
        datamin = d3.min(cofactor1_values);
        datamax = d3.max(cofactor1_values);
    } else if ($('#cofactor2_type option:selected').val() == "color"){
        datamin = d3.min(cofactor2_values);
        datamax = d3.max(cofactor2_values);
    } else {
        datamin = d3.min(cofactor3_values);
        datamax = d3.max(cofactor3_values);
    }
    colormin = $("#cocolorfrom").val();
    colormax = $("#cocolorto").val();

    compute = d3.interpolate("#"+colormin, "#"+colormax);
    linear = d3.scale.linear().domain([datamin, datamax]).range([0,1]);

    this_sample = d.tx.split("<br>")[0]

    if ($('#cofactor1_type option:selected').val() == "color"){
      c= compute(linear(cofactor1_dict[this_sample]));
    } else if ($('#cofactor2_type option:selected').val() == "color"){
      c= compute(linear(cofactor2_dict[this_sample]));
    } else {
      c= compute(linear(cofactor3_dict[this_sample]));
    }

    return c;
}

function ranked_colorer(d) {
    if ($('#cofactor1_type option:selected').val() == "color"){
        datamin = d3.min(ranked_cofactor1_values);
        datamax = d3.max(ranked_cofactor1_values);
    } else if ($('#cofactor2_type option:selected').val() == "color"){
        datamin = d3.min(ranked_cofactor2_values);
        datamax = d3.max(ranked_cofactor2_values);
    } else {
        datamin = d3.min(ranked_cofactor3_values);
        datamax = d3.max(ranked_cofactor3_values);
    }
    colormin = $("#cocolorfrom").val();
    colormax = $("#cocolorto").val();

    compute = d3.interpolate("#"+colormin, "#"+colormax);
    linear = d3.scale.linear().domain([datamin, datamax]).range([0,1]);

    this_sample = d.tx.split("<br>")[0]

    if ($('#cofactor1_type option:selected').val() == "color"){
      c= compute(linear(ranked_cofactor1_dict[this_sample]));
    } else if ($('#cofactor2_type option:selected').val() == "color"){
      c= compute(linear(ranked_cofactor2_dict[this_sample]));
    } else {
      c= compute(linear(ranked_cofactor3_dict[this_sample]));
    }

    return c;
}

function chartupdatedata() {
    var size = $("#marksize").val();
    var shape = $("#markshape").val();

    var pearson_title_update = {
      title: "Pearson Correlation Scatterplot"
    }
    var spearman_title_update = {
      title: "Spearman Rank Correlation Scatterplot"
    }

    Plotly.newPlot('scatterplot2', getdata(), layout)
    Plotly.relayout('scatterplot2', pearson_title_update)
    Plotly.newPlot('srscatterplot2', srgetdata(), sr_layout)
    Plotly.relayout('srscatterplot2', spearman_title_update)

    if ($('#cofactor1_type option:selected').val() == "color"){
      $('#cofactor_color_selector').css("display", "inline")
      if ($('input[name=cofactor1_vals]').val()){
        d3.select('#scatterplot2 svg').selectAll('.point')
          .style({
              'stroke': colorer,
              'fill':   colorer
        });
        d3.select('#srscatterplot2 svg').selectAll('.point')
          .style({
              'stroke': ranked_colorer,
              'fill':   ranked_colorer
        });
      }
    } else if ($('#cofactor2_type option:selected').val() == "color"){
      $('#cofactor_color_selector').css("display", "inline")
      if ($('input[name=cofactor2_vals]').val()){
        d3.select('#scatterplot2 svg').selectAll('.point')
          .style({
              'stroke': colorer,
              'fill':   colorer
        });
        d3.select('#srscatterplot2 svg').selectAll('.point')
          .style({
              'stroke': ranked_colorer,
              'fill':   ranked_colorer
        });
      }
    } else {
      $('#cofactor_color_selector').css("display", "inline")
      if ($('input[name=cofactor3_vals]').val()){
        d3.select('#scatterplot2 svg').selectAll('.point')
          .style({
              'stroke': colorer,
              'fill':   colorer
        });
        d3.select('#srscatterplot2 svg').selectAll('.point')
          .style({
              'stroke': ranked_colorer,
              'fill':   ranked_colorer
        });
      }
    }
}

drawg();
srdrawg();

$(".chartupdatewh").change(function () {
    chartupdatewh();
});

$(".chartupdatedata").change(function () {
    chartupdatedata();
});

$("#cofactor1_type").change(function () {

    the_types = ["color", "size", "symbol"]

    cofactor1_type = $(this).val()
    cofactor2_type = $("#cofactor2_type option:selected").val()
    cofactor3_type = $("#cofactor3_type option:selected").val()

    if (cofactor2_type == cofactor1_type){
      for (i=0; i<3; i++){
        if (the_types[i] != cofactor1_type && the_types[i] != cofactor3_type) {
          $("#cofactor2_type").val(the_types[i]);
        }
      }
    }
    else if (cofactor3_type == cofactor1_type){
      for (i=0; i<3; i++){
        if (the_types[i] != cofactor1_type && the_types[i] != cofactor2_type) {
          $("#cofactor3_type").val(the_types[i]);
        }
      }
    }

    chartupdatedata();
});

$("#cofactor2_type").change(function () {

    the_types = ["color", "size", "symbol"]

    cofactor2_type = $(this).val()
    cofactor1_type = $("#cofactor1_type option:selected").val()
    cofactor3_type = $("#cofactor3_type option:selected").val()

    if (cofactor1_type == cofactor2_type){
      for (i=0; i<3; i++){
        if (the_types[i] != cofactor2_type && the_types[i] != cofactor3_type){
          $("#cofactor1_type").val(the_types[i]);
        }
      }
    }
    else if (cofactor3_type == cofactor2_type){
      for (i=0; i<3; i++){
        if (the_types[i] != cofactor2_type && the_types[i] != cofactor1_type){
          $("#cofactor3_type").val(the_types[i]);
        }
      }
    }

    chartupdatedata();
});

$("#cofactor3_type").change(function () {

    the_types = ["color", "size", "symbol"]

    cofactor3_type = $(this).val()
    cofactor1_type = $("#cofactor1_type option:selected").val()
    cofactor2_type = $("#cofactor2_type option:selected").val()

    if (cofactor1_type == cofactor3_type){
      for (i=0; i<3; i++){
        if (the_types[i] != cofactor2_type && the_types[i] != cofactor3_type){
          $("#cofactor1_type").val(the_types[i]);
        }
      }
    }
    else if (cofactor2_type == cofactor3_type){
      for (i=0; i<3; i++){
        if (the_types[i] != cofactor2_type && the_types[i] != cofactor1_type){
          $("#cofactor3_type").val(the_types[i]);
        }
      }
    }
});

open_covariate_selection = function() {
  return $('#collections_holder').load('/collections/list #collections_list', (function(_this) {
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

remove_cofactors = function() {
  $('input[name=cofactor1_vals]').val("");
  $('input[name=ranked_cofactor1_vals]').val("");
  $('input[name=cofactor2_vals]').val("");
  $('input[name=ranked_cofactor2_vals]').val("");
  $('input[name=cofactor3_vals]').val("");
  $('input[name=ranked_cofactor3_vals]').val("");

  $('#select_cofactor1').text("Select Cofactor 1");
  $('#cofactor2_button').css("display", "none");
  $('#cofactor3_button').css("display", "none");

  $('#cofactor_color_select').css("display", "none");

  $('#cofactor1_info_container').css("display", "none");
  $('#cofactor2_info_container').css("display", "none");
  $('#cofactor3_info_container').css("display", "none");

  chartupdatedata();
};

$(document).ready(function(){
    chartupdatedata();

    $('#select_cofactor1').click(function () {
        $('input[name=selecting_which_cofactor]').val("1");
        open_covariate_selection();
    });

    $('#select_cofactor2').click(function () {
        $('input[name=selecting_which_cofactor]').val("2");
        open_covariate_selection();
    });

    $('#select_cofactor3').click(function () {
        $('input[name=selecting_which_cofactor]').val("3");
        open_covariate_selection();
    });

    $('#remove_cofactors').click(function () {
        remove_cofactors();
    });

});
