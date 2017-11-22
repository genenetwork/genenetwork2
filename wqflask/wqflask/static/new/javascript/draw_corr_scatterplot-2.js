var chart;

function drawg () {
    //
    chart = nv.models.scatterChart();
    //
    chart.showLegend(false);
    chart.duration(300);
    chart.color(d3.scale.category10().range());
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
        // return '<b style="font-size: 18px">(' + obj.point.x + ', ' + obj.point.y + ')</b>';
        return '<b style="font-size: 18px">' + obj.point.name + '</b>';
    });
}

function getdata(size, shape) {
    var data = [];
    data.push({
            values: [],
            slope: js_data.slope,
            intercept: js_data.intercept
        });
    for (j = 0; j < js_data.data[0].length; j++) {
        data[0].values.push({
            x: js_data.data[0][j],
            y: js_data.data[1][j],
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
    var axisxcolor = $("#axisxcolor").val();
    $(".nvd3 .nv-axis.nv-x text").css("fill", axisxcolor);
    //
    var axisycolor = $("#axisycolor").val();
    $(".nvd3 .nv-axis.nv-y text").css("fill", axisycolor);
    //
    var axisxfont = $("#axisxfont").val();
    $(".nvd3 .nv-axis.nv-x text").css("font-size", axisxfont);
    //
    var axisyfont = $("#axisyfont").val();
    $(".nvd3 .nv-axis.nv-y text").css("font-size", axisyfont);
    //
    var domainxcolor = $("#domainxcolor").val();
    $(".nv-x .nv-axis g path.domain").css("stroke", domainxcolor);
    //
    var domainycolor = $("#domainycolor").val();
    $(".nv-y .nv-axis g path.domain").css("stroke", domainycolor);
    //
    var domainxwidth = $("#domainxwidth").val();
    $(".nv-x .nv-axis g path.domain").css("stroke-width", domainxwidth);
    //
    var domainywidth = $("#domainywidth").val();
    $(".nv-y .nv-axis g path.domain").css("stroke-width", domainywidth);
    //
    var clinecolor = $("#clinecolor").val();
    $("line.nv-regLine").css("stroke", clinecolor);
    //
    var clinewidth = $("#clinewidth").val();
    $("line.nv-regLine").css("stroke-width", clinewidth);
    //
    var axiscolor = $("#axiscolor").val();
    $(".tick").css("stroke", axiscolor);
    //
    var axiswidth = $("#axiswidth").val();
    $("line.nv-regLine").css("stroke-width", axiswidth); 
}

function chartupdatewh() {
    //
    var width = $("#width").val();
    $("#scatterplot2 svg").css("width", width);
    //
    var height = $("#height").val();
    $("#scatterplot2 svg").css("height", height);
    //
    window.dispatchEvent(new Event('resize'));
}

function chartupdatedata() {
    //
    var size = $("#marksize").val();
    var shape = $("#markshape").val();
    //
    d3.select('#scatterplot2 svg').datum(nv.log(getdata(size, shape))).call(chart);
    nv.utils.windowResize(chart.update);
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

drawg();
chartupdate();
chartupdatewh();
chartupdatedata();

$(".chartupdate").change(function () {
    chartupdate();
});

$(".chartupdatewh").change(function () {
    chartupdatewh();
});

$(".chartupdatedata").change(function () {
    chartupdatedata();
});
