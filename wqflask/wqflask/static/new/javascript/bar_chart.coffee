root = exports ? this

class Bar_Chart
    constructor: (@sample_list, @attribute_names) ->
        @get_samples()
        console.log("sample names:", @sample_names)
        
        #Used to calculate the bottom margin so sample names aren't cut off
        longest_sample_name = d3.max(sample.length for sample in @sample_names)
        
        @margin =
            top: 20
            right: 20
            bottom: longest_sample_name * 7
            left: 40
            
        @plot_width = @sample_vals.length * 15 - @margin.left - @margin.right
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
            attribute = $("#color_attribute").val()
            if $("#update_bar_chart").html() == 'Sort By Name' 
                @svg.selectAll(".bar")
                    .data(@sorted_samples())
                    .transition()
                    .duration(1000)
                    .style("fill", (d) =>
                        if attribute == "None"
                            return "steelblue"
                        else
                            return @attr_color_dict[attribute][d[2][attribute]]
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
                        if attribute == "None"
                            return "steelblue"
                        else
                            return @attr_color_dict[attribute][d[2][attribute]]
                    )
        )
    
    
        d3.select("#update_bar_chart").on("click", =>
            if @attributes.length > 0
                attribute = $("#color_attribute").val()
            if $("#update_bar_chart").html() == 'Sort By Value' 
                $("#update_bar_chart").html('Sort By Name')
                sortItems = (a, b) ->
                    return a[1] - b[1]

                @svg.selectAll(".bar")
                    .data(@sorted_samples())
                    .transition()
                    .duration(1000)
                    .attr("y", (d) =>
                        return @y_scale(d[1])
                    )
                    .attr("height", (d) =>
                        return @plot_height - @y_scale(d[1])
                    )
                    .style("fill", (d) =>
                        if @attributes.length > 0 && attribute != "None"
                            return @attr_color_dict[attribute][d[2][attribute]]
                        else
                            return "steelblue"
                    )
                    .select("title")
                    .text((d) =>
                        return d[1]
                    )
                sorted_sample_names = (sample[0] for sample in @sorted_samples())
                x_scale = d3.scale.ordinal()
                    .domain(sorted_sample_names)
                    .rangeBands([0, @plot_width], .1)
                $('.x.axis').remove()
                @add_x_axis(x_scale)
            else
                $("#update_bar_chart").html('Sort By Value')
                @svg.selectAll(".bar")
                    .data(@samples)
                    .transition()
                    .duration(1000)
                    .attr("y", (d) =>
                        return @y_scale(d[1])
                    )
                    .attr("height", (d) =>
                        return @plot_height - @y_scale(d[1])
                    )
                    .style("fill", (d) =>
                        if @attributes.length > 0 && attribute != "None"
                            return @attr_color_dict[attribute][d[2][attribute]]
                        else
                            return "steelblue"
                    )
                    .select("title")
                    .text((d) =>
                        return d[1]
                    )
                x_scale = d3.scale.ordinal()
                    .domain(@sample_names)
                    .rangeBands([0, @plot_width], .1)
                $('.x.axis').remove()
                @add_x_axis(x_scale)
        )
        
        d3.select("#color_by_trait").on("click", =>
            @color_by_trait()
        )

    get_attr_color_dict: () ->
        color = d3.scale.category20()
        @attr_color_dict = {}
        console.log("attribute_names:", @attribute_names)
        for own key, attribute_info of @attribute_names
            this_color_dict = {}
            for value, i in attribute_info.distinct_values
                this_color_dict[value] = color(i)
            @attr_color_dict[attribute_info.name] = this_color_dict
        
        
        

    get_samples: () ->
        @sample_names = (sample.name for sample in @sample_list when sample.value != null)
        @sample_vals = (sample.value for sample in @sample_list when sample.value != null)
        @attributes = (key for key of @sample_list[0]["extra_attributes"])
        console.log("attributes:", @attributes)
        @sample_attr_vals = []
        if @attributes.length > 0
            for sample in @sample_list
                attr_vals = {}
                for attribute in @attributes
                    attr_vals[attribute] = sample["extra_attributes"][attribute]
                @sample_attr_vals.push(attr_vals)
        @samples = _.zip(@sample_names, @sample_vals, @sample_attr_vals)
        @get_attr_color_dict()
        console.log("samples:", @samples)
        
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
            .rangeBands([0, @plot_width], .1)

        @y_scale = d3.scale.linear()
            .domain([@y_min * 0.75, @y_max])
            .range([@plot_height, @y_buffer])
            
    create_graph: () ->
        
        #@add_border()
        @add_x_axis(@x_scale)
        @add_y_axis() 
        
        @add_bars()
        
    add_x_axis: (scale) ->
        xAxis = d3.svg.axis()
            .scale(scale)
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
    
    color_by_trait: () ->
        console.log("Before load")
        $('#collections_holder').load('/collections/list #collections_list')
        console.log("After load")
        #$.colorbox({href:"/collections/list"})
        #$.get(
        #    url: /collections/list
        #    
        #)
    
root.Bar_Chart = Bar_Chart