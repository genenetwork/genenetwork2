root = exports ? this

class Histogram
    constructor: (@sample_list, @sample_group) ->
        @sort_by = "name"
        @format_count = d3.format(",.0f") #a formatter for counts
        @get_sample_vals()
        
        @margin = {top: 10, right: 30, bottom: 30, left: 30}
        @plot_width = 960 - @margin.left - @margin.right
        @plot_height = 500 - @margin.top - @margin.bottom

        @x_buffer = @plot_width/20
        @y_buffer = @plot_height/20

        @y_min = d3.min(@sample_vals)  
        @y_max = d3.max(@sample_vals) * 1.1
        
        @plot_height -= @y_buffer
        @create_x_scale()
        @get_histogram_data()
        @create_y_scale()
        
        @svg = @create_svg()

        @create_graph()

    get_sample_vals: () ->
        @sample_vals = (sample.value for sample in @sample_list when sample.value != null)

    create_svg: () ->
        svg = d3.select("#histogram")
          .append("svg")
            .attr("class", "histogram")
            .attr("width", @plot_width + @margin.left + @margin.right)
            .attr("height", @plot_height + @margin.top + @margin.bottom)
          .append("g")
            .attr("transform", "translate(" + @margin.left + "," + @margin.top + ")")

        return svg

    create_x_scale: () ->
        console.log("min/max:", d3.min(@sample_vals) + "," + d3.max(@sample_vals))
        if (d3.min(@sample_vals) < 0)
            min_domain = d3.min(@sample_vals)
        else
            min_domain = 0
        @x_scale = d3.scale.linear()
            .domain([min_domain, parseFloat(d3.max(@sample_vals))])
            .range([0, @plot_width]) 

    get_histogram_data: () ->
        console.log("sample_vals:", @sample_vals)
        @histogram_data = d3.layout.histogram()
            .bins(@x_scale.ticks(20))(@sample_vals)
        console.log("histogram_data:", @histogram_data[0])

    create_y_scale: () ->
        @y_scale = d3.scale.linear()
            .domain([0, d3.max(@histogram_data, (d) => return d.y )])
            .range([@plot_height, 0])

    create_graph: () ->
        @add_x_axis()
        @add_bars()

    add_x_axis: () ->
        x_axis = d3.svg.axis()
            .scale(@x_scale)
            .orient("bottom");
        
        @svg.append("g")
            .attr("class", "x axis")
            .attr("transform", "translate(0," + @plot_height + ")")
            .call(x_axis)
            
    add_y_axis: () ->
        y_axis = d3.svg.axis()
                .scale(@y_scale)
                .orient("left")
                .ticks(5)
                
    add_bars: () ->
        console.log("bar_width:", @x_scale(@histogram_data[0].dx))
        bar = @svg.selectAll(".bar")
            .data(@histogram_data)
          .enter().append("g")
            .attr("class", "bar")
            .attr("transform", (d) =>
                return "translate(" + @x_scale(d.x) + "," + @y_scale(d.y) + ")")
        
        bar.append("rect")
            .attr("x", 1)
            .attr("width", @x_scale(@histogram_data[0].x + @histogram_data[0].dx) - 1)
            .attr("height", (d) =>
                return @plot_height - @y_scale(d.y)
            )
        bar.append("text")
            .attr("dy", ".75em")
            .attr("y", 6)
            .attr("x", @x_scale(@histogram_data[0].dx)/2)
            .attr("text-anchor", "middle")
            .style("fill", "#fff")
            .text((d) =>
                bar_height = @plot_height - @y_scale(d.y)
                if bar_height > 20
                    return @format_count(d.y)
            )

root.Histogram = Histogram