var srchart;

function srdrawg () {
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
    srchart.xAxis.tickFormat(d3.format(srcheckformat(xrange)));
    srchart.yAxis.tickFormat(d3.format(srcheckformat(yrange)));
    //
    srchart.tooltip.contentGenerator(function (obj) {
        // return '<b style="font-size: 18px">(' + obj.point.x + ', ' + obj.point.y + ')</b>';
        return '<b style="font-size: 18px">' + obj.point.name + '</b>';
    });
}

function srgetdata(size, shape) {
    var data = [];
    data.push({
            values: [],
            slope: js_data.srslope,
            intercept: js_data.srintercept
        });
    for (j = 0; j < js_data.rdata[0].length; j++) {
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
    
function srcheckformat(range) {
    cell = range / 10.0;
    if (cell >= 1) {
        return ",r";
    } else {
        cell = -Math.log(cell);
        n = cell.toString().split(".")[0].length;
        return ",.0" + n + "f";
    }
}

function srchartupdate() {
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
}

function srchartupdatewh() {
    //
    var width = $("#srwidth").val();
    $("#srscatterplot2 svg").css("width", width);
    //
    var height = $("#srheight").val();
    $("#srscatterplot2 svg").css("height", height);
    //
    window.dispatchEvent(new Event('resize'));
}

function srchartupdatedata() {
    //
    var size = $("#srmarksize").val();
    var shape = $("#srmarkshape").val();
    //
    d3.select('#srscatterplot2 svg').datum(nv.log(srgetdata(size, shape))).call(srchart);
    nv.utils.windowResize(srchart.update);
}

function saveassvg_srcs() {
    savesvg($("#svg_srcs")[0], "Spearman Rank Correlation Scatterplot.svg");
}

srdrawg();
srchartupdate();
srchartupdatewh();
srchartupdatedata();

$(".srchartupdate").change(function () {
    srchartupdate();
});

$(".srchartupdatewh").change(function () {
    srchartupdatewh();
});

$(".srchartupdatedata").change(function () {
    srchartupdatedata();
});
