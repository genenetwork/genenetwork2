root = exports ? this

# calculations here use the same formulae as scipy.stats.probplot
get_z_scores = (n) ->
    # order statistic medians (Filliben's approximation)
    osm_uniform = new Array(n)
    osm_uniform[n - 1] = Math.pow(0.5, 1.0 / n)
    osm_uniform[0] = 1 - osm_uniform[n - 1]
    for i in [1 .. (n - 2)]
       osm_uniform[i] = (i + 1 - 0.3175) / (n + 0.365)

    return (jStat.normal.inv(x, 0, 1) for x in osm_uniform)

# input: dictionary sample name -> sample value
redraw_prob_plot = (samples) ->
    h = 600
    w = 600
    margin = {left:60, top:40, right:40, bottom: 40, inner:5}
    totalh = h + margin.top + margin.bottom
    totalw = w + margin.left + margin.right

    container = $("#prob_plot_container")
    container.width(totalw)
    container.height(totalh)

    nv.addGraph(() =>
        chart = nv.models.scatterChart().width(w).height(h).showLegend(false)
        chart.xAxis
             .axisLabel("Theoretical quantiles")
             .tickFormat(d3.format('.02f'));
        chart.yAxis
             .axisLabel("Sample quantiles")
             .tickFormat(d3.format('.02f'));
        chart.tooltipContent((obj) =>
            return '<b style="font-size: 20px">' + obj.point.name + '</b>';
        )

        names = (x for x in _.keys(samples) when samples[x] != null)
        sorted_names = names.sort((x, y) => samples[x] - samples[y])
        sorted_values = (samples[x] for x in sorted_names)
        sw_result = ShapiroWilkW(sorted_values)
        W = sw_result.w.toFixed(3)
        pvalue = sw_result.p.toFixed(3)
        pvalue_str = if pvalue > 0.05 then\
                        pvalue.toString()\
                     else\
                        "<span style='color:red'>"+pvalue+"</span>"
        test_str = "Shapiro-Wilk test statistic is #{W} (p = #{pvalue_str})"
        data = [{
                 slope: jStat.stdev(sorted_values),
                 intercept: jStat.mean(sorted_values),
                 size: 10,
                 values: ({x: z_score, y: value, name: sample}\
                          for [z_score, value, sample] in\
                          _.zip(get_z_scores(sorted_values.length),
                                sorted_values,
                                sorted_names))
                }]
        console.log("THE DATA IS:", data)
        d3.select("#prob_plot_container svg")
          .datum(data)
          .call(chart)

        $("#prob_plot_title").html("<h3>Normal probability plot</h3>"+test_str)

        return chart
        )

root.redraw_prob_plot_impl = redraw_prob_plot
