var chart;

nv.addGraph(function() {
    //
    chart = nv.models.scatterChart();
    //
    chart.showLegend(false);
    chart.duration(300);
    chart.color(d3.scale.category10().range());
    chart.pointRange([200,0]);
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
        return '<b style="font-size: 18px">(' + obj.point.x + ', ' + obj.point.y + ')</b>';
    });
    //
    d3.select('#scatterplot2 svg').datum(nv.log(getdata())).call(chart);
    nv.utils.windowResize(chart.update);
    return chart;
});

function getdata () {
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
            size: 10,
            shape: 'circle'
        });
    }
    return data;
}
    
function checkformat (range) {
    cell = range / 10.0;
    if (cell >= 1) {
        return ",r";
    } else {
        cell = -Math.log(cell);
        n = cell.toString().split(".")[0].length;
        return ",.0" + n + "f";
    }
}
