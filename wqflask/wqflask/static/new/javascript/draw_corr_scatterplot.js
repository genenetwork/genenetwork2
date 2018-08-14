var chart;
var srchart;

var layout = {
    height: 700,
    width: 800,
    margin: {
        l: 60,
        r: 30,
        t: 80,
        b: 50
    },
    xaxis: {
        title: js_data.trait_1,
        zeroline: false,
        visible: true,
        linecolor: 'black',
        linewidth: 1,
    },
    yaxis: {
        title: js_data.trait_2,
        zeroline: false,
        visible: true,
        linecolor: 'black',
        linewidth: 1,
    }
}

cofactor1_dict = {}
ranked_cofactor1_dict = {}
cofactor1_values = []
ranked_cofactor1_values = []
cofactor2_dict = {}
ranked_cofactor2_dict = {}

function drawg() {
    x_values = []
    y_values = []
    sample_names = []
    for (j = 0; j < js_data.data[0].length; j++) {
      x_values.push(js_data.data[0][j])
      y_values.push(js_data.data[1][j])
      sample_names.push(js_data.indIDs[j])
    }

    var trace = {
        x: x_values,
        y: y_values,
        mode: 'markers',
        text: sample_names
    }

    Plotly.newPlot('scatterplot2', [trace], layout)

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

    var trace = {
        x: x_values,
        y: y_values,
        mode: 'markers',
        text: sample_names
    }

    Plotly.newPlot('srscatterplot2', [trace], layout)
}

function getdata() {
    var data = [];
    data.push({
            values: [],
            slope: js_data.slope,
            intercept: js_data.intercept
        });

    sizemin = 1;
    sizemax = 50;

    if ($('input[name=cofactor1_vals]').val()){
        just_vals = []
        val_sample_dict = {}
        val_sample_pairs = $('input[name=cofactor1_vals]').val().split(",")
        for (i=0; i < val_sample_pairs.length; i++) {
          just_vals.push(parseFloat(val_sample_pairs[i].split(":")[1]))
          val_sample_dict[val_sample_pairs[i].split(":")[0]] = parseFloat(val_sample_pairs[i].split(":")[1])
        }

        cofactor1_dict = val_sample_dict
        cofactor1_values = just_vals
    }

    if ($('input[name=cofactor2_vals]').val()){
        vals_3 = [];
        samples_3 = [];
        val_sample_dict = {}
        val_sample_pairs = $('input[name=cofactor2_vals]').val().split(",")
        for (i=0; i < val_sample_pairs.length; i++) {
          samples_3.push(val_sample_pairs[i].split(":")[0])
          vals_3.push(parseFloat(val_sample_pairs[i].split(":")[1]))
          val_sample_dict[val_sample_pairs[i].split(":")[0]] = val_sample_pairs[i].split(":")[1]
        }
        datamin = d3.min(vals_3);
        datamax = d3.max(vals_3);

        cofactor2_dict = val_sample_dict
    }

    x_values = []
    y_values = []
    sample_names = []
    sizes = []

    for (j = 0; j < js_data.data[0].length; j++) {
        if ($('input[name=cofactor2_vals]').val()){
          if (samples_3.indexOf(js_data.indIDs[j])) {
            datav = vals_3[j]
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
      point_text.push(this_text)
    }

    var trace = {
        x: x_values,
        y: y_values,
        mode: 'markers',
        text: point_text,
        marker: {
          size: sizes
        }
    }

    return [trace];
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

    sizemin = 1;
    sizemax = 50;

    x_values = []
    y_values = []
    sample_names = []
    sizes = []

    if ($('input[name=ranked_cofactor1_vals]').val()){
        just_vals = []
        val_sample_dict = {}
        val_sample_pairs = $('input[name=ranked_cofactor1_vals]').val().split(",")
        for (i=0; i < val_sample_pairs.length; i++) {
          just_vals.push(parseFloat(val_sample_pairs[i].split(":")[1]))
          val_sample_dict[val_sample_pairs[i].split(":")[0]] = parseFloat(val_sample_pairs[i].split(":")[1])
        }

        ranked_cofactor1_dict = val_sample_dict
        ranked_cofactor1_values = just_vals
    }

    if ($('input[name=ranked_cofactor2_vals]').val()){
        vals_3 = []
        samples_3 = [];
        val_sample_dict = {}
        val_sample_pairs = $('input[name=ranked_cofactor2_vals]').val().split(",")
        for (i=0; i<val_sample_pairs.length; i++){
          samples_3.push(val_sample_pairs[i].split(":")[0])
          vals_3.push(val_sample_pairs[i].split(":")[1])
          val_sample_dict[val_sample_pairs[i].split(":")[0]] = val_sample_pairs[i].split(":")[1]
        }
        datamin = d3.min(vals_3);
        datamax = d3.max(vals_3);

        ranked_cofactor2_dict = val_sample_dict
    }

    for (j = 0; j < js_data.rdata[0].length; j++) {
        if ($('input[name=ranked_cofactor2_vals]').val()){
          if (samples_3.indexOf(js_data.indIDs[j])) {
            datav = vals_3[j]
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
      point_text.push(this_text)
    }

    var trace = {
        x: x_values,
        y: y_values,
        mode: 'markers',
        text: point_text,
        marker: {
          size: sizes
        }
    }

    return [trace];
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
    Plotly.newPlot('srscatterplot2', srgetdata(), layout)
    Plotly.relayout('srscatterplot2', width_height_update)
}

function colorer(d) {
    datamin = d3.min(cofactor1_values);
    datamax = d3.max(cofactor1_values);
    colormin = $("#cocolorfrom").val();
    colormax = $("#cocolorto").val();

    compute = d3.interpolate(colormin, colormax);
    linear = d3.scale.linear().domain([datamin, datamax]).range([0,1]);

    this_sample = d.tx.split("<br>")[0]

    c = compute(linear(cofactor1_dict[this_sample]));

    return c;
}

function ranked_colorer(d) {
    datamin = d3.min(ranked_cofactor1_values);
    datamax = d3.max(ranked_cofactor1_values);
    colormin = $("#cocolorfrom").val();
    colormax = $("#cocolorto").val();

    compute = d3.interpolate(colormin, colormax);
    linear = d3.scale.linear().domain([datamin, datamax]).range([0,1]);

    this_sample = d.tx.split("<br>")[0]

    c= compute(linear(ranked_cofactor1_dict[this_sample]));

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
    Plotly.newPlot('srscatterplot2', srgetdata(), layout)
    Plotly.relayout('srscatterplot2', spearman_title_update)

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
}

drawg();
srdrawg();

$(".chartupdatewh").change(function () {
    chartupdatewh();
});

$(".chartupdatedata").change(function () {
    chartupdatedata();
});

$(".cofactor1_type").change(function () {
    console.log("cofactor1 type:", $(".cofactor1_type").val())
    if ($(".cofactor1_type").val() == "color"){
      $(".cofactor2_type").val("size")
    } else {
      $(".cofactor2_type").val("color")
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
});
