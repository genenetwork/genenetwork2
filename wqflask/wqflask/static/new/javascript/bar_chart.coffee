root = exports ? this

class Bar_Chart
    constructor: (@sample_list) ->
        @sort_by = "name"
        @get_samples()
        console.log("sample names:", @sample_names)
        if @sample_attr_vals.length > 0
            @get_distinct_attr_vals()
            @get_attr_color_dict(@distinct_attr_vals)
        
        #Used to calculate the bottom margin so sample names aren't cut off
        longest_sample_name = d3.max(sample.length for sample in @sample_names)
        
        @margin = {top: 20, right: 20, bottom: longest_sample_name * 7, left: 40}
        @plot_width = @sample_vals.length * 20 - @margin.left - @margin.right
        @range = @sample_vals.length * 20
        @plot_height = 500 - @margin.top - @margin.bottom

        @x_buffer = @plot_width/20
        @y_buffer = @plot_height/20

        @y_min = d3.min(@sample_vals)  
        @y_max = d3.max(@sample_vals) * 1.1

        @svg = @create_svg()

        @plot_height -= @y_buffer
        @create_scales()
        @create_graph()

        d3.select("#color_attribute").on("change", =>
            @attribute = $("#color_attribute").val()
            console.log("attr_color_dict:", @attr_color_dict)
            #if $("#update_bar_chart").html() == 'Sort By Name'
            if @sort_by = "name" 
                @svg.selectAll(".bar")
                    .data(@sorted_samples())
                    .transition()
                    .duration(1000)
                    .style("fill", (d) =>
                        if @attribute == "None"
                            return "steelblue"
                        else
                            return @attr_color_dict[@attribute][d[2][@attribute]]
                    )
                    .select("title")
                    .text((d) =>
                        return d[1]
                    )
            else
                @svg.selectAll(".bar")
                    .data(@samples)
                    .transition()
                    .duration(1000)
                    .style("fill", (d) =>
                        if @attribute == "None"
                            return "steelblue"
                        else
                            return @attr_color_dict[@attribute][d[2][@attribute]]
                    )
            @draw_legend()
            @add_legend(@attribute, @distinct_attr_vals[@attribute])
        )

        $(".sort_by_value").on("click", =>
            console.log("sorting by value")
            @sort_by = "value"
            if @attributes.length > 0
                @attribute = $("#color_attribute").val()
            #sortItems = (a, b) ->
            #    return a[1] - b[1]
            @rebuild_bar_graph(@sorted_samples())
            #@svg.selectAll(".bar")
            #    .data(@sorted_samples())
            #    .transition()
            #    .duration(1000)
            #    .attr("y", (d) =>
            #        return @y_scale(d[1])
            #    )
            #    .attr("height", (d) =>
            #        return @plot_height - @y_scale(d[1])
            #    )
            #    .select("title")
            #    .text((d) =>
            #        return d[1]
            #    )
            #    #.style("fill", (d) =>
            #    #    if @attributes.length > 0
            #    #        return @attr_color_dict[attribute][d[2][attribute]]
            #    #    else
            #    #        return "steelblue"
            #    #)
            #sorted_sample_names = (sample[0] for sample in @sorted_samples())
            #x_scale = d3.scale.ordinal()
            #    .domain(sorted_sample_names)
            #    .rangeBands([0, @plot_width], .1)
            #$('.x.axis').remove()
            #@add_x_axis(x_scale)
        )
        
        $(".sort_by_name").on("click", =>
            console.log("sorting by name")
            @sort_by = "name"
            if @attributes.length > 0
                @attribute = $("#color_attribute").val()
            @rebuild_bar_graph(@samples)
            #@svg.selectAll(".bar")
            #    .data(@samples)
            #    .transition()
            #    .duration(1000)
            #    .attr("y", (d) =>
            #        return @y_scale(d[1])
            #    )
            #    .attr("height", (d) =>
            #        return @plot_height - @y_scale(d[1])
            #    )
            #    .select("title")
            #    .text((d) =>
            #        return d[1]
            #    )
            #    .style("fill", (d) =>
            #        if @attributes.length > 0
            #            return @attr_color_dict[attribute][d[2][attribute]]
            #        else
            #            return "steelblue"
            #    )
            #x_scale = d3.scale.ordinal()
            #    .domain(@sample_names)
            #    .rangeBands([0, @plot_width], .1)
            #$('.x.axis').remove()
            #@add_x_axis(x_scale)
        )

        d3.select("#color_by_trait").on("click", =>
            @open_trait_selection()
        )

    # takes a dict: name -> value and rebuilds the graph
    redraw: (samples_dict) ->
        updated_samples = []
        for [name, val, attr] in @full_sample_list
            if name of samples_dict
                updated_samples.push [name, samples_dict[name], attr]

        @samples = updated_samples
        # TODO: update underscore.js and replace the below with an _.unzip call
        @sample_names = (x[0] for x in @samples)
        @sample_vals = (x[1] for x in @samples)
        @sample_attr_vals = (x[2] for x in @samples)

        @rebuild_bar_graph(if @sort_by == 'name' then @samples else @sorted_samples())

    rebuild_bar_graph: (samples) ->
        console.log("samples:", samples)
        @svg.selectAll(".bar")
            .data(samples)
            .transition()
            .duration(1000)
            .style("fill", (d) =>
                if @attributes.length == 0 and @trait_color_dict?
                    console.log("SAMPLE:", d[0])
                    console.log("CHECKING:", @trait_color_dict[d[0]])
                    #return "steelblue"
                    return @trait_color_dict[d[0]]
                else if @attributes.length > 0 and @attribute != "None"
                    console.log("@attribute:", @attribute)
                    console.log("d[2]", d[2])
                    console.log("the_color:", @attr_color_dict[@attribute][d[2][@attribute]])
                    return @attr_color_dict[@attribute][d[2][@attribute]]
                else
                    return "steelblue"
            )
            .attr("y", (d) =>
                return @y_scale(d[1])
            )
            .attr("height", (d) =>
                return @plot_height - @y_scale(d[1])
            )
            .select("title")
            .text((d) =>
                return d[1]
            )
            #.style("fill", (d) =>
            #    return @trait_color_dict[d[0]]
            #    #return @attr_color_dict["collection_trait"][trimmed_samples[d[0]]]
            #)
        @create_scales()
        $('.bar_chart').find('.x.axis').remove()
        $('.bar_chart').find('.y.axis').remove()
        @add_x_axis()
        @add_y_axis() 

    get_attr_color_dict: (vals) ->
        @attr_color_dict = {}
        console.log("vals:", vals)
        for own key, distinct_vals of vals
            @min_val = d3.min(distinct_vals)
            @max_val = d3.max(distinct_vals)
            this_color_dict = {}
            if distinct_vals.length < 10
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
                                    .domain([min_val,
                                            max_val])
                                    .range([0,255])
                    for value, i in distinct_vals
                        console.log("color_range(value):", parseInt(color_range(value)))
                        this_color_dict[value] = d3.rgb(parseInt(color_range(value)),0, 0)
                        #this_color_dict[value] = d3.rgb("lightblue").darker(color_range(parseInt(value)))
                        #this_color_dict[value] = "rgb(0, 0, " + color_range(parseInt(value)) + ")"
            @attr_color_dict[key] = this_color_dict
       


    draw_legend: () ->
        $('#legend-left').html(@min_val)
        $('#legend-right').html(@max_val)
        svg_html = '<svg height="10" width="90"> \
                        <rect x="0" width="15" height="10" style="fill: rgb(0, 0, 0);"></rect> \
                        <rect x="15" width="15" height="10" style="fill: rgb(50, 0, 0);"></rect> \
                        <rect x="30" width="15" height="10" style="fill: rgb(100, 0, 0);"></rect> \
                        <rect x="45" width="15" height="10" style="fill: rgb(150, 0, 0);"></rect> \
                        <rect x="60" width="15" height="10" style="fill: rgb(200, 0, 0);"></rect> \
                        <rect x="75" width="15" height="10" style="fill: rgb(255, 0, 0);"></rect> \
                    </svg>'
        console.log("svg_html:", svg_html)
        $('#legend-colors').html(svg_html)
            
    get_trait_color_dict: (samples, vals) ->
        @trait_color_dict = {}
        console.log("vals:", vals)
        for own key, distinct_vals of vals
            this_color_dict = {}
            @min_val = d3.min(distinct_vals)
            @max_val = d3.max(distinct_vals)
            if distinct_vals.length < 10
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
                                    .domain([d3.min(distinct_vals),
                                            d3.max(distinct_vals)])
                                    .range([0,255])
                    for value, i in distinct_vals
                        console.log("color_range(value):", parseInt(color_range(value)))
                        this_color_dict[value] = d3.rgb(parseInt(color_range(value)),0, 0)
        for own sample, value of samples
            @trait_color_dict[sample] = this_color_dict[value]

    convert_into_colors: (values) ->
        color_range = d3.scale.linear()
                        .domain([d3.min(values),
                                d3.max(values)])
                        .range([0,255])
        for value, i in values
            console.log("color_range(value):", color_range(parseInt(value)))
            this_color_dict[value] = d3.rgb(color_range(parseInt(value)),0, 0)
            #this_color_dict[value] = d3.rgb("lightblue").darker(color_range(parseInt(value)))

    get_samples: () ->
        @sample_names = (sample.name for sample in @sample_list when sample.value != null)
        @sample_vals = (sample.value for sample in @sample_list when sample.value != null)
        @attributes = (key for key of @sample_list[0]["extra_attributes"])
        console.log("attributes:", @attributes)
        @sample_attr_vals = []
        # WTF??? how can they be zipped later???
        # TODO find something with extra_attributes for testing
        if @attributes.length > 0
            for sample in @sample_list
                attr_vals = {}
                for attribute in @attributes
                    attr_vals[attribute] = sample["extra_attributes"][attribute]
                @sample_attr_vals.push(attr_vals)
        @samples = _.zip(@sample_names, @sample_vals, @sample_attr_vals)
        @full_sample_list = @samples.slice() # keeps attributes across redraws

    get_distinct_attr_vals: () ->
        @distinct_attr_vals = {}
        for sample in @sample_attr_vals
            for attribute of sample
                if not @distinct_attr_vals[attribute]
                    @distinct_attr_vals[attribute] = []
                if sample[attribute] not in @distinct_attr_vals[attribute]
                    @distinct_attr_vals[attribute].push(sample[attribute])
        #console.log("distinct_attr_vals:", @distinct_attr_vals)
        
    create_svg: () ->
        svg = d3.select("#bar_chart")
            .append("svg")
            .attr("class", "bar_chart")
            .attr("width", @plot_width + @margin.left + @margin.right)
            .attr("height", @plot_height + @margin.top + @margin.bottom)
            .append("g")
            .attr("transform", "translate(" + @margin.left + "," + @margin.top + ")")
            
        return svg
        
    create_scales: () ->
        @x_scale = d3.scale.ordinal()
            .domain(@sample_names)
            .rangeRoundBands([0, @range], 0.1, 0)

        @y_scale = d3.scale.linear()
            .domain([@y_min * 0.75, @y_max])
            .range([@plot_height, @y_buffer])
            
    create_graph: () ->
        
        #@add_border()
        @add_x_axis()
        @add_y_axis() 
        
        @add_bars()
        
    add_x_axis: (scale) ->
        xAxis = d3.svg.axis()
            .scale(@x_scale)
            .orient("bottom");
        
        @svg.append("g")
            .attr("class", "x axis")
            .attr("transform", "translate(0," + @plot_height + ")")
            .call(xAxis)
            .selectAll("text")  
                .style("text-anchor", "end")
                .style("font-size", "12px")
                .attr("dx", "-.8em")
                .attr("dy", "-.3em")
                .attr("transform", (d) =>
                    return "rotate(-90)" 
                )

    add_y_axis: () ->
        yAxis = d3.svg.axis()
                .scale(@y_scale)
                .orient("left")
                .ticks(5)

        @svg.append("g")
            .attr("class", "y axis")
            .call(yAxis)
          .append("text")
            .attr("transform", "rotate(-90)")
            .attr("y", 6)
            .attr("dy", ".71em")
            .style("text-anchor", "end")

    add_bars: () ->
        @svg.selectAll(".bar")
            .data(@samples)
          .enter().append("rect")
            .style("fill", "steelblue")
            .attr("class", "bar")
            .attr("x", (d) =>
                return @x_scale(d[0])
            )
            .attr("width", @x_scale.rangeBand())
            .attr("y", (d) =>
                return @y_scale(d[1])
            )
            .attr("height", (d) =>
                return @plot_height - @y_scale(d[1])
            )
            .append("svg:title")
            .text((d) =>
                return d[1]
            )
            

    sorted_samples: () ->
        #if @sample_attr_vals.length > 0
        sample_list = _.zip(@sample_names, @sample_vals, @sample_attr_vals)
        #else
        #    sample_list = _.zip(@sample_names, @sample_vals)
        sorted = _.sortBy(sample_list, (sample) =>
            return sample[1]
        )
        console.log("sorted:", sorted)
        return sorted

    add_legend: (attribute, distinct_vals) ->
        legend = @svg.append("g")
            .attr("class", "legend")
            .attr("height", 100)
            .attr("width", 100)
            .attr('transform', 'translate(-20,50)')

        legend_rect = legend.selectAll('rect')
                        .data(distinct_vals)
                        .enter()
                        .append("rect")
                        .attr("x", @plot_width - 65)
                        .attr("width", 10)
                        .attr("height", 10)
                        .attr("y", (d, i) =>
                            return i * 20
                        )
                        .style("fill", (d) =>
                            console.log("TEST:", @attr_color_dict[attribute][d])
                            return @attr_color_dict[attribute][d]
                        )

        legend_text = legend.selectAll('text')
                        .data(distinct_vals)
                        .enter()
                        .append("text")
                        .attr("x", @plot_width - 52)
                        .attr("y", (d, i) =>
                            return i*20 + 9    
                        )
                        .text((d) =>
                            return d
                        )

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
        if @sort_by = "value"
            @svg.selectAll(".bar")
                .data(@samples)
                .transition()
                .duration(1000)
                .style("fill", (d) =>
                    console.log("this color:", @trait_color_dict[d[0]])
                    return @trait_color_dict[d[0]]
                )
                .select("title")
                .text((d) =>
                    return d[1]
                ) 
            @draw_legend()      
        else
            @svg.selectAll(".bar")
                .data(@sorted_samples())
                .transition()
                .duration(1000)
                .style("fill", (d) =>
                    console.log("this color:", @trait_color_dict[d[0]])
                    return @trait_color_dict[d[0]]
                )
                .select("title")
                .text((d) =>
                    return d[1]
                )  
            @draw_legend()          

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
