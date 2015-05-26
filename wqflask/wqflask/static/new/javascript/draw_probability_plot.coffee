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

# samples is {'samples_primary': {'name1': value1, ...},
#             'samples_other': {'nameN': valueN, ...},
#             'samples_all': {'name1': value1, ...}}
redraw_prob_plot = (samples, sample_group) ->
    h = 600
    w = 600
    margin = {left:60, top:40, right:40, bottom: 40, inner:5}
    totalh = h + margin.top + margin.bottom
    totalw = w + margin.left + margin.right

    container = $("#prob_plot_container")
    container.width(totalw)
    container.height(totalh)

    nv.addGraph(() =>
        chart = nv.models.scatterChart()
                  .width(w)
                  .height(h)
                  .showLegend(true)
                  .color(d3.scale.category10().range())

        # size settings are quite counter-intuitive in NVD3!
        chart.pointRange([50,50]) # (50 is the area, not radius)

        chart.legend.updateState(false)

        chart.xAxis
             .axisLabel("Theoretical quantiles")
             .tickFormat(d3.format('.02f'))

        chart.yAxis
             .axisLabel("Sample quantiles")
             .tickFormat(d3.format('.02f'))

        chart.tooltipContent((obj) =>
            return '<b style="font-size: 20px">' + obj.point.name + '</b>'
        )

        all_samples = samples[sample_group]
        names = (x for x in _.keys(all_samples) when all_samples[x] != null)
        sorted_names = names.sort((x, y) => all_samples[x].value - all_samples[y].value)
        sorted_values = (all_samples[x].value for x in sorted_names)
        sw_result = ShapiroWilkW(sorted_values)
        W = sw_result.w.toFixed(3)
        pvalue = sw_result.p.toFixed(3)
        pvalue_str = if pvalue > 0.05 then\
                        pvalue.toString()\
                     else\
                        "<span style='color:red'>"+pvalue+"</span>"
        test_str = "Shapiro-Wilk test statistic is #{W} (p = #{pvalue_str})"

        z_scores = get_z_scores(sorted_values.length)
        slope = jStat.stdev(sorted_values)
        intercept = jStat.mean(sorted_values)

        make_data = (group_name) ->
            return {
                 key: js_data.sample_group_types[group_name],
                 slope: slope,
                 intercept: intercept,
                 values: ({x: z_score, y: value, name: sample}\
                          for [z_score, value, sample] in\
                          _.zip(get_z_scores(sorted_values.length),
                                sorted_values,
                                sorted_names)\
                          when sample of samples[group_name])
                }

        data = [make_data('samples_primary'), make_data('samples_other')]
        console.log("THE DATA IS:", data)
        d3.select("#prob_plot_container svg")
          .datum(data)
          .call(chart)

        $("#prob_plot_title").html("<h3>Normal probability plot</h3>"+test_str)
        $("#prob_plot_container .nv-legendWrap").toggle(sample_group == "samples_all")

        return chart
        )

root.redraw_prob_plot_impl = redraw_prob_plot
