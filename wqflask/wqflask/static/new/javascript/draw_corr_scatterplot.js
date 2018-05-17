// http://gn2-lei.genenetwork.org/corr_scatter_plot2?dataset_1=HC_M2_0606_P&dataset_2=HC_M2_0606_P&dataset_3=HC_M2_0606_P&trait_1=1427571_at&trait_2=1457022_at&trait_3=1427571_at

var chart;
var srchart;

function drawg() {
    //
    chart = nv.models.scatterChart();
    //
    chart.showLegend(false);
    chart.duration(300);
    //chart.color(d3.scale.category10().range());
    chart.pointRange([0, 400]);
    chart.pointDomain([0, 10]);
    //
    chart.xAxis.axisLabel(js_data.trait_1);
    chart.xAxis.axisLabelDistance(11);
    chart.yAxis.axisLabel(js_data.trait_2);
    chart.yAxis.axisLabelDistance(11);
    //
    xmin = d3.min(js_data.data[0]);
    xmax = d3.max(js_data.data[0]);
    xrange = xmax - xmin;
    ymin = d3.min(js_data.data[1]);
    ymax = d3.max(js_data.data[1]);
    yrange = ymax - ymin;
    chart.xDomain([xmin - xrange/10, xmax + xrange/10]);
    chart.yDomain([ymin - yrange/10, ymax + yrange/10]);
    chart.xAxis.tickFormat(d3.format(checkformat(xrange)));
    chart.yAxis.tickFormat(d3.format(checkformat(yrange)));
    //
    chart.tooltip.contentGenerator(function (obj) {
        return tiptext(obj);
    });
}

function srdrawg() {
    //
    srchart = nv.models.scatterChart();
    //
    srchart.showLegend(false);
    srchart.duration(300);
    srchart.color(d3.scale.category10().range());
    srchart.pointRange([0, 400]);
    srchart.pointDomain([0, 10]);
    //
    srchart.xAxis.axisLabel(js_data.trait_1);
    srchart.xAxis.axisLabelDistance(11);
    srchart.yAxis.axisLabel(js_data.trait_2);
    srchart.yAxis.axisLabelDistance(11);
    //
    xmin = d3.min(js_data.rdata[0]);
    xmax = d3.max(js_data.rdata[0]);
    xrange = xmax - xmin;
    ymin = d3.min(js_data.rdata[1]);
    ymax = d3.max(js_data.rdata[1]);
    yrange = ymax - ymin;
    srchart.xDomain([0, xmax + xrange/10]);
    srchart.yDomain([0, ymax + yrange/10]);
    srchart.xAxis.tickFormat(d3.format(checkformat(xrange)));
    srchart.yAxis.tickFormat(d3.format(checkformat(yrange)));
    //
    srchart.tooltip.contentGenerator(function (obj) {
        return tiptext(obj);
    });
}

function tiptext(obj) {
    return '<b style="font-size: 18px">' + obj.point.name + " (" + obj.point.x + ', ' + obj.point.y + ')</b>';
}

function getdata(size, shape) {
    var data = [];
    data.push({
            values: [],
            slope: js_data.slope,
            intercept: js_data.intercept
        });

    sizemin = 1;
    sizemax = 50;
    if ('vals_3' in js_data) {
        datamin = d3.min(js_data.vals_3);
        datamax = d3.max(js_data.vals_3);
        colormin = $("#cocolorfrom").val();
        colormax = $("#cocolorto").val();
        compute = d3.interpolate(colormin, colormax);
        linear = d3.scale.linear().domain([datamin, datamax]).range([0,1]);
    }

    for (j = 0; j < js_data.data[0].length; j++) {
        if ('trait3' in js_data) {
          if (js_data.indIDs[j] in js_data.trait3) {
            datav = js_data.trait3[js_data.indIDs[j]].value;
            // size = (sizemax - sizemin) * (datav - datamin) / (datamax - datamin) + sizemin;
            sizev = map1to2(datamin, datamax, sizemin, sizemax, datav);
          }
        } else {
            datav = 0;
            sizev = sizemin;
        }
        data[0].values.push({
            x: js_data.data[0][j],
            y: js_data.data[1][j],
            name: js_data.indIDs[j],
            size: sizev,
            shape: shape,
            v3: datav
        });
    }
    console.log(data);
    return data;
}

function map1to2 (min1, max1, min2, max2, v1) {
    v2 = (v1 - min1) * (max2 - min2) / (max1 - min1) + min2;
    return v2;
}

function srgetdata(size, shape) {
    var data = [];
    data.push({
            values: [],
            slope: js_data.srslope,
            intercept: js_data.srintercept
        });
    for (j = 0; j < js_data.rdata[0].length; j++) {
        if (js_data.indIDs[j] in js_data.trait3) {
            size = js_data.trait3[js_data.indIDs[j]].value;
            //console.log("yes "+js_data.indIDs[j]+", "+size);
        } else {
            //console.log("no "+js_data.indIDs[j]);
        }
        data[0].values.push({
            x: js_data.rdata[0][j],
            y: js_data.rdata[1][j],
            name: js_data.indIDs[j],
            size: size,
            shape: shape
        });
    }
    return data;
}
    
function checkformat(range) {
    cell = range / 10.0;
    if (cell >= 1) {
        return ",r";
    } else {
        cell = -Math.log(cell);
        n = cell.toString().split(".")[0].length;
        return ",.0" + n + "f";
    }
}

function chartupdate() {
    //
    var labelcolor = $("#labelcolor").val();
    $(".nvd3 .nv-axis.nv-x text").css("fill", labelcolor);
    $(".nvd3 .nv-axis.nv-y text").css("fill", labelcolor);
    //
    var labelfont = $("#labelfont").val();
    $(".nvd3 .nv-axis.nv-x text").css("font-size", labelfont);
    $(".nvd3 .nv-axis.nv-y text").css("font-size", labelfont);
    //
    var numbercolor = $("#numbercolor").val();
    $("g.tick text").css("fill", numbercolor);
    //
    var numberfont = $("#numberfont").val();
    $("g.tick text").css("font-size", numberfont);
    //
    var axiscolor = $("#axiscolor").val();
    $(".nv-x .nv-axis g path.domain").css("stroke", axiscolor);
    $(".nv-y .nv-axis g path.domain").css("stroke", axiscolor);
    //
    var axiswidth = $("#axiswidth").val();
    $(".nv-x .nv-axis g path.domain").css("stroke-width", axiswidth);
    $(".nv-y .nv-axis g path.domain").css("stroke-width", axiswidth);
    //
    var linecolor = $("#linecolor").val();
    $("line.nv-regLine").css("stroke", linecolor);
    //
    var linewidth = $("#linewidth").val();
    $("line.nv-regLine").css("stroke-width", linewidth);
    //
    var markcolor = $("#markcolor").val();
    $(".nvd3 g path").css("fill", markcolor);
}

function chartupdatewh() {
    //
    var width = $("#width").val();
    $("#scatterplot2 svg").css("width", width);
    $("#srscatterplot2 svg").css("width", width);
    //
    var height = $("#height").val();
    $("#scatterplot2 svg").css("height", height);
    $("#srscatterplot2 svg").css("height", height);
    //
    window.dispatchEvent(new Event('resize'));
}

 function colorer(d) {
    datamin = d3.min(js_data.vals_3);
    datamax = d3.max(js_data.vals_3);
    //colormin = d3.rgb(255,0,0);
    //colormax = d3.rgb(0,255,0);
    colormin = $("#cocolorfrom").val();
    colormax = $("#cocolorto").val();

    console.log("colormin: "+colormin);
    console.log("colormax: "+colormax);

    compute = d3.interpolate(colormin, colormax);
    linear = d3.scale.linear().domain([datamin, datamax]).range([0,1]);
    //console.log(d[0].x);
          c= compute(linear(d[0].x));
          //console.log(c);
          return c;
  }

function chartupdatedata() {
    //
    var size = $("#marksize").val();
    var shape = $("#markshape").val();
    //
    d3.select('#scatterplot2 svg').datum(getdata(size, shape)).call(chart);
    d3.select('#srscatterplot2 svg').datum(nv.log(srgetdata(size, shape))).call(srchart);
    //
    d3.selectAll('.nv-point')
      .attr({
          'stroke': colorer,
          'fill':   colorer
      });
    //
    nv.utils.windowResize(chart.update);
    nv.utils.windowResize(srchart.update);
}

function savesvg(svgEl, name) {
    svgEl.setAttribute("xmlns", "http://www.w3.org/2000/svg");
    var svgData = svgEl.outerHTML;
    var preface = '<?xml version="1.0" standalone="no"?>\r\n';
    preface += '<?xml-stylesheet type="text/css" href="http://cdnjs.cloudflare.com/ajax/libs/nvd3/1.8.5/nv.d3.min.css"?>\r\n';
    var svgBlob = new Blob([preface, svgData], {type:"image/svg+xml;charset=utf-8"});
    var svgUrl = URL.createObjectURL(svgBlob);
    var downloadLink = document.createElement("a");
    downloadLink.href = svgUrl;
    downloadLink.download = name;
    document.body.appendChild(downloadLink);
    downloadLink.click();
    document.body.removeChild(downloadLink);
}

function saveassvg_pcs() {
    savesvg($("#svg_pcs")[0], "Pearson Correlation Scatterplot.svg");
}

function saveassvg_srcs() {
    savesvg($("#svg_srcs")[0], "Spearman Rank Correlation Scatterplot.svg");
}

drawg();
srdrawg();

$(".chartupdate").change(function () {
    chartupdate();
});

$(".chartupdatewh").change(function () {
    chartupdatewh();
    chartupdate();
});

$(".chartupdatedata").change(function () {
    chartupdatedata();
    chartupdate();
});

$(document).ready(function(){
    chartupdatedata();
    chartupdate();
});
