root = exports ? this

class Bar_Chart
    constructor: (sample_lists) ->
        @sample_lists = {}
        l1 = @sample_lists['samples_primary'] = sample_lists[0] or []
        l2 = @sample_lists['samples_other'] = sample_lists[1] or []

        l1_names = (x.name for x in l1)
        l3 = l1.concat((x for x in l2 when x.name not in l1_names))
        @sample_lists['samples_all'] = l3
        longest_sample_name_len = d3.max(sample.name.length for sample in l3)
        @margin = {
                   top: 20,
                   right: 20,
                   bottom: longest_sample_name_len * 6,
                   left: 40
                  }

        @attributes = (key for key of sample_lists[0][0]["extra_attributes"])
        @sample_attr_vals = (@extra(s) for s in @sample_lists['samples_all']\
                                       when s.value != null)
        @get_distinct_attr_vals()
        @get_attr_color_dict(@distinct_attr_vals)
        @attribute_name = "None"

        @sort_by = "name"
        @chart = null

        @select_attribute_box = $ "#color_attribute"

        d3.select("#color_attribute").on("change", =>
            @attribute_name = @select_attribute_box.val()
            @rebuild_bar_graph()
        )

        $(".sort_by_value").on("click", =>
            console.log("sorting by value")
            @sort_by = "value"
            @rebuild_bar_graph()
        )

        $(".sort_by_name").on("click", =>
            console.log("sorting by name")
            @sort_by = "name"
            @rebuild_bar_graph()
        )

        d3.select("#color_by_trait").on("click", =>
            @open_trait_selection()
        )

    value: (sample) ->
        @value_dict[sample.name].value

    variance: (sample) ->
        @value_dict[sample.name].variance

    extra: (sample) ->
        attr_vals = {}
        for attribute in @attributes
            attr_vals[attribute] = sample["extra_attributes"][attribute]
        attr_vals

    # takes a dict: name -> value and rebuilds the graph
    redraw: (samples_dict, selected_group) ->
        @value_dict = samples_dict[selected_group]
        @raw_data = (x for x in @sample_lists[selected_group] when\
                     x.name of @value_dict and @value(x) != null)
        @rebuild_bar_graph()

    rebuild_bar_graph: ->
        raw_data = @raw_data.slice()
        if @sort_by == 'value'
            raw_data = raw_data.sort((x, y) => @value(x) - @value(y))
        console.log("raw_data: ", raw_data)

        h = 600
        container = $("#bar_chart_container")
        container.height(h + @margin.top + @margin.bottom)
        if @chart is null
            @chart = nv.models.multiBarChart()
                       .height(h)
                       .errorBarColor(=> 'red')
                       .reduceXTicks(false)
                       .staggerLabels(false)
                       .showControls(false)
                       .showLegend(false)

            # show value, sd, and attributes in tooltip
            @chart.multibar.dispatch.on('elementMouseover.tooltip',
            (evt) =>
                evt.value = @chart.x()(evt.data);
                evt['series'] = [{
                    key: 'Value',
                    value: evt.data.y,
                    color: evt.color
                }];
                if evt.data.yErr
                    evt['series'].push({key: 'SE', value: evt.data.yErr})
                if evt.data.attr
                    for k, v of evt.data.attr
                        evt['series'].push({key: k, value: v})
                @chart.tooltip.data(evt).hidden(false);
            )

            @chart.tooltip.valueFormatter((d, i) -> d)

        nv.addGraph(() =>
            @remove_legend()
            values = ({x: s.name, y: @value(s), yErr: @variance(s) or 0,\
                       attr: s.extra_attributes}\
                      for s in raw_data)

            if @attribute_name != "None"
                @color_dict = @attr_color_dict[@attribute_name]
                @chart.barColor((d) => @color_dict[d.attr[@attribute_name]])
                @add_legend()
            else
                @chart.barColor(=> 'steelblue')

            @chart.width(raw_data.length * 20)
            @chart.yDomain([0.9 * _.min((d.y - 1.5 * d.yErr for d in values)),
                            1.05 * _.max((d.y + 1.5 * d.yErr for d in values))])
            console.log("values: ", values)
            d3.select("#bar_chart_container svg")
              .datum([{values: values}])
              .style('width', raw_data.length * 20 + 'px')
              .transition().duration(1000)
              .call(@chart)

            d3.select("#bar_chart_container .nv-x")
              .selectAll('.tick text')
               .style("font-size", "12px")
               .style("text-anchor", "end")
               .attr("dx", "-.8em")
               .attr("dy", "-.3em")
               .attr("transform", (d) =>
                   return "rotate(-90)"
               )

            return @chart
            )

    get_attr_color_dict: (vals) ->
        @attr_color_dict = {}
        @is_discrete = {}
        @minimum_values = {}
        @maximum_values = {}
        console.log("vals:", vals)
        for own key, distinct_vals of vals
            @min_val = d3.min(distinct_vals)
            @max_val = d3.max(distinct_vals)
            this_color_dict = {}
            discrete = distinct_vals.length < 10
            if discrete
                color = d3.scale.category10()
                for value, i in distinct_vals
                    this_color_dict[value] = color(i)
            else
                console.log("distinct_values:", distinct_vals)
                #Check whether all values are numbers, and if they are get a corresponding
                #color gradient
                if _.every(distinct_vals, (d) =>
                    if isNaN(d)
                        return false
                    else
                        return true
                )
                    color_range = d3.scale.linear()
                                    .domain([@min_val, @max_val])
                                    .range([0,255])
                    for value, i in distinct_vals
                        console.log("color_range(value):", parseInt(color_range(value)))
                        this_color_dict[value] = d3.rgb(parseInt(color_range(value)),0, 0)
                        #this_color_dict[value] = d3.rgb("lightblue").darker(color_range(parseInt(value)))
                        #this_color_dict[value] = "rgb(0, 0, " + color_range(parseInt(value)) + ")"
            @attr_color_dict[key] = this_color_dict
            @is_discrete[key] = discrete
            @minimum_values[key] = @min_val
            @maximum_values[key] = @max_val

    get_distinct_attr_vals: () ->
        # FIXME: this has quadratic behaviour, may cause issues with many samples and continuous attributes
        @distinct_attr_vals = {}
        for sample in @sample_attr_vals
            for attribute of sample
                if not @distinct_attr_vals[attribute]
                    @distinct_attr_vals[attribute] = []
                if sample[attribute] not in @distinct_attr_vals[attribute]
                    @distinct_attr_vals[attribute].push(sample[attribute])
        #console.log("distinct_attr_vals:", @distinct_attr_vals)

    add_legend: =>
        if @is_discrete[@attribute_name]
            @add_legend_discrete()
        else
            @add_legend_continuous()

    remove_legend: =>
        $(".legend").remove()
        $("#legend-left,#legend-right,#legend-colors").empty()

    add_legend_continuous: =>
        $('#legend-left').html(@minimum_values[@attribute_name])
        $('#legend-right').html(@maximum_values[@attribute_name])
        svg_html = '<svg height="15" width="120"> \
                        <rect x="0" width="20" height="15" style="fill: rgb(0, 0, 0);"></rect> \
                        <rect x="20" width="20" height="15" style="fill: rgb(50, 0, 0);"></rect> \
                        <rect x="40" width="20" height="15" style="fill: rgb(100, 0, 0);"></rect> \
                        <rect x="60" width="20" height="15" style="fill: rgb(150, 0, 0);"></rect> \
                        <rect x="80" width="20" height="15" style="fill: rgb(200, 0, 0);"></rect> \
                        <rect x="100" width="20" height="15" style="fill: rgb(255, 0, 0);"></rect> \
                    </svg>'
        console.log("svg_html:", svg_html)
        $('#legend-colors').html(svg_html)

    add_legend_discrete: =>
        legend_span = d3.select('#bar_chart_legend')
            .append('div').style('word-wrap', 'break-word')
            .attr('class', 'legend').selectAll('span')
            .data(@distinct_attr_vals[@attribute_name])
          .enter().append('span').style({'word-wrap': 'normal', 'display': 'inline-block'})

        legend_span.append('span')
            .style("background-color", (d) =>
                return @attr_color_dict[@attribute_name][d]
            )
            .style({'display': 'inline-block', 'width': '15px', 'height': '15px',\
                    'margin': '0px 5px 0px 15px'})
        legend_span.append('span').text((d) => return d).style('font-size', '20px')

    open_trait_selection: () ->
        $('#collections_holder').load('/collections/list?color_by_trait #collections_list', =>
            $.colorbox(
                inline: true
                href: "#collections_holder"
            )
            #Removes the links from the collection names, because clicking them would leave the page
            #instead of loading the list of traits in the colorbox
            $('a.collection_name').attr( 'onClick', 'return false' )
            #$('.collection_name').each (index, element) =>
            #    console.log("contents:", $(element).contents())
            #    $(element).contents().unwrap()
        )

    color_by_trait: (trait_sample_data) ->
        console.log("BXD1:", trait_sample_data["BXD1"])
        console.log("trait_sample_data:", trait_sample_data)
        trimmed_samples = @trim_values(trait_sample_data)
        distinct_values = {}
        distinct_values["collection_trait"] = @get_distinct_values(trimmed_samples)
        #@get_attr_color_dict(distinct_values)
        @get_trait_color_dict(trimmed_samples, distinct_values)
        console.log("TRAIT_COLOR_DICT:", @trait_color_dict)
        console.log("SAMPLES:", @samples)
        # TODO

    trim_values: (trait_sample_data) ->
        trimmed_samples = {}
        for sample in @sample_names
            if sample of trait_sample_data
                trimmed_samples[sample] = trait_sample_data[sample]
        console.log("trimmed_samples:", trimmed_samples)
        return trimmed_samples

    get_distinct_values: (samples) ->
        distinct_values = _.uniq(_.values(samples))
        console.log("distinct_values:", distinct_values)
        return distinct_values
        #distinct_values = []
        #for sample in samples
        #    if samples[sample] in distinct_values

root.Bar_Chart = Bar_Chart
