class Chr_Manhattan_Plot
    constructor: (@plot_height, @plot_width, @chr) ->
        @qtl_results = js_data.qtl_results
        console.log("qtl_results are:", @qtl_results)
        console.log("chr is:", @chr)
        
        @get_max_chr()

        @filter_qtl_results()
        console.log("filtered results:", @these_results)
        @get_qtl_count()

        @x_coords = []
        @y_coords = []
        @marker_names = []

        console.time('Create coordinates')
        @create_coordinates()
        console.log("@x_coords: ", @x_coords)
        console.log("@y_coords: ", @y_coords)
        console.timeEnd('Create coordinates')
        
        # Buffer to allow for the ticks/labels to be drawn
        @x_buffer = @plot_width/30
        @y_buffer = @plot_height/20
        
        @x_max = d3.max(@x_coords)
        @y_max = d3.max(@y_coords) * 1.2
    
        @y_threshold = @get_lod_threshold()
    
        @svg = @create_svg()

        @plot_coordinates = _.zip(@x_coords, @y_coords, @marker_names)
        console.log("coordinates:", @plot_coordinates)

        @plot_height -= @y_buffer

        @create_scales()

        console.time('Create graph')
        @create_graph()
        console.timeEnd('Create graph')
       
    get_max_chr: () ->
        @max_chr = 0
        for key of js_data.chromosomes
            console.log("key is:", key)
            if parseInt(key) > @max_chr
                @max_chr = parseInt(key)
        
    filter_qtl_results: () ->
        @these_results = []
        this_chr = 100
        for result in @qtl_results
            if result.chr == "X"
                this_chr = @max_chr
            else
                this_chr = result.chr
            console.log("this_chr is:", this_chr)
            console.log("@chr[0] is:", parseInt(@chr[0]))
            if this_chr > parseInt(@chr[0])
                break
            if parseInt(this_chr) == parseInt(@chr[0])
                @these_results.push(result)

    get_qtl_count: () ->
        high_qtl_count = 0
        for result in @these_results
            if result.lod_score > 1
                high_qtl_count += 1
        console.log("high_qtl_count:", high_qtl_count)
        
        #if high_qtl_count > 10000
        @y_axis_filter = 2
        #else if high_qtl_count > 1000
        #    @y_axis_filter = 1
        #else
        #    @y_axis_filter = 0

    create_coordinates: () ->
        for result in @these_results
            @x_coords.push(parseFloat(result.Mb))
            @y_coords.push(result.lod_score)
            @marker_names.push(result.name)
            
    create_svg: () ->
        svg = d3.select("#topchart")
            .append("svg")
            .attr("class", "chr_manhattan_plot")
            .attr("width", @plot_width+@x_buffer)
            .attr("height", @plot_height+@y_buffer)
            .append("g")
        return svg

    create_scales: () ->
        @x_scale = d3.scale.linear()
            .domain([0, @chr[1]])
            .range([@x_buffer, @plot_width])
        @y_scale = d3.scale.linear()
            .domain([0, @y_max])
            .range([@plot_height, @y_buffer])
            
    get_lod_threshold: () ->
        if @y_max/2 > 2
            return @y_max/2
        else
            return 2

    create_graph: () ->
        @add_border()
        @add_x_axis()
        @add_y_axis()
        @add_title()
        @add_back_button()
        @add_plot_points()

    add_border: () ->
        border_coords = [[@y_buffer, @plot_height, @x_buffer, @x_buffer],
                         [@y_buffer, @plot_height, @plot_width, @plot_width],
                         [@y_buffer, @y_buffer, @x_buffer, @plot_width],
                         [@plot_height, @plot_height, @x_buffer, @plot_width]]
            
        @svg.selectAll("line")
            .data(border_coords)
            .enter()
            .append("line")
            .attr("y1", (d) =>
                return d[0]
            )
            .attr("y2", (d) =>
                return d[1]
            )
            .attr("x1", (d) =>
                return d[2]
            )
            .attr("x2", (d) =>
                return d[3]
            )             
            .style("stroke", "#000")

    add_x_axis: () ->
        @xAxis = d3.svg.axis()
                .scale(@x_scale)
                .orient("bottom")
                .ticks(20)

        @xAxis.tickFormat((d) =>
            d3.format("d") #format as integer
            return (d)
        )

        @svg.append("g")
            .attr("class", "x_axis")
            .attr("transform", "translate(0," + @plot_height + ")")
            .call(@xAxis)
            .selectAll("text")
                .attr("text-anchor", "right")
                .attr("font-size", "12px")
                .attr("dx", "-1.6em")
                .attr("transform", (d) =>
                    return "translate(-12,0) rotate(-90)"
                )
                
    add_y_axis: () ->
        @yAxis = d3.svg.axis()
                .scale(@y_scale)
                .orient("left")
                .ticks(5)
        
        @svg.append("g")
            .attr("class", "y_axis")
            .attr("transform", "translate(" + @x_buffer + ",0)")
            .call(@yAxis)

    add_title: () ->
        @svg.append("text")
            .attr("class", "title")
            .text("Chr " + @chr[0])
            .attr("x", (d) =>
                return (@plot_width + @x_buffer)/2
            )
            .attr("y", @y_buffer + 20)
            .attr("dx", "0em")
            .attr("text-anchor", "middle")
            .attr("font-family", "sans-serif")
            .attr("font-size", "18px")
            .attr("fill", "black")

    add_back_button: () ->
        @svg.append("text")
            .attr("class", "back")
            .text("Return to full view")
            .attr("x", @x_buffer*2)
            .attr("y", @y_buffer/2)
            .attr("dx", "0em")
            .attr("text-anchor", "middle")
            .attr("font-family", "sans-serif")
            .attr("font-size", "18px")
            .attr("cursor", "pointer")
            .attr("fill", "black")
            .on("click", @return_to_full_view)


    add_plot_points: () ->
        @plot_point = @svg.selectAll("circle")
            .data(@plot_coordinates)
            .enter()
            .append("circle")
            .attr("cx", (d) =>
                return @x_scale(d[0])
            )
            .attr("cy", (d) =>
                return @y_scale(d[1])
            )
            .attr("r", (d) =>
                #if d[1] > 2
                #    return 3
                #else
                return 2
            )
            .attr("fill", (d) =>
                #if d[1] > 2
                #    return "white"
                #else
                return "black"
            )
            .attr("stroke", "black")
            .attr("stroke-width", "1")
            .attr("id", (d) =>
                return "point_" + String(d[2])
            )
            .classed("circle", true)
            .on("mouseover", (d) =>
                console.log("d3.event is:", d3.event)
                console.log("d is:", d)
                this_id = "point_" + String(d[2])
                d3.select("#" + this_id).classed("d3_highlight", true)
                    .attr("r", 5)
                    .attr("stroke", "none")
                    .attr("fill", "blue")
                    .call(@show_marker_in_table(d))
            )
            .on("mouseout", (d) =>
                this_id = "point_" + String(d[2])
                d3.select("#" + this_id).classed("d3_highlight", false)
                    .attr("r", (d) =>
                        #if d[1] > 2
                        #    return 3
                        #else
                        return 2
                    )
                    .attr("fill", (d) =>
                        #if d[1] > 2
                        #    return "white"
                        #else
                        return "black"
                    )
                    .attr("stroke", "black")
                    .attr("stroke-width", "1")
            )
            .append("svg:title")
                .text((d) =>
                    return d[2]
                )

    return_to_full_view: () ->
        $('#topchart').remove()
        $('#chart_container').append('<div class="qtlcharts" id="topchart"></div>')
        create_manhattan_plot()

    show_marker_in_table: (marker_info) ->
        console.log("in show_marker_in_table")
        ### Searches for the select marker in the results table below ###
        if marker_info
            marker_name = marker_info[2]
            $("#qtl_results_filter").find("input:first").val(marker_name).change()
        #else
        #    marker_name = ""
        #$("#qtl_results_filter").find("input:first").val(marker_name).change()
