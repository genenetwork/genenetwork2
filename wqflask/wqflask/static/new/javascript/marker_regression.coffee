$ ->
    class Manhattan_Plot
        constructor: (@plot_height, @plot_width) ->
            @qtl_results = js_data.qtl_results
            console.log("qtl_results are:", @qtl_results)
            @chromosomes = js_data.chromosomes

            @total_length = 0

            @max_chr = @get_max_chr()

            @x_coords = []
            @y_coords = []
            @marker_names = []
            console.time('Create coordinates')
            @create_coordinates()
            console.log("@x_coords: ", @x_coords)
            console.log("@y_coords: ", @y_coords)
            console.timeEnd('Create coordinates')
            [@chr_lengths, @cumulative_chr_lengths] = @get_chr_lengths()

            # Buffer to allow for the ticks/labels to be drawn
            @x_buffer = @plot_width/30
            @y_buffer = @plot_height/20
            
            #@x_max = d3.max(@x_coords)
            @x_max = @total_length
            console.log("@x_max: ", @x_max)
            console.log("@x_buffer: ", @x_buffer)
            @y_max = d3.max(@y_coords) * 1.2

            @svg = @create_svg()
            @plot_coordinates = _.zip(@x_coords, @y_coords, @marker_names)
            
            @plot_height -= @y_buffer
            @create_scales()
            console.time('Create graph')
            @create_graph()
            console.timeEnd('Create graph')

        get_max_chr: () ->
            max_chr = 0
            for result in @qtl_results
                chr = parseInt(result.chr)
                if not _.isNaN(chr) 
                    if chr > max_chr
                        max_chr = chr
            return max_chr

        get_chr_lengths: () ->
            ###
            Gets a list of both individual and cumulative (the position of one on the graph
            is its own length plus the lengths of all preceding chromosomes) lengths in order
            to draw the vertical lines separating chromosomes and the chromosome labels
            
            ###
            
            console.log("@chromosomes: ", @chromosomes)
            
            cumulative_chr_lengths = []
            chr_lengths = []
            total_length = 0
            for key of @chromosomes
                this_length = @chromosomes[key]
                chr_lengths.push(this_length)
                cumulative_chr_lengths.push(total_length + this_length)
                total_length += this_length

            console.log("chr_lengths: ", chr_lengths)

            return [chr_lengths, cumulative_chr_lengths]

        create_coordinates: () -> 
            chr_lengths = []
            chr_seen = []
            for result in js_data.qtl_results
                if result.chr == "X"
                    chr_length = parseFloat(@chromosomes[20])
                else
                    chr_length = parseFloat(@chromosomes[result.chr])
                if not(result.chr in chr_seen)
                    chr_seen.push(result.chr) 
                    chr_lengths.push(chr_length) 
                    if result.chr != "1"
                        @total_length += parseFloat(chr_lengths[chr_lengths.length - 2])
                @x_coords.push(@total_length + parseFloat(result.Mb))
                @y_coords.push(result.lod_score)
                @marker_names.push(result.name)
            @total_length += parseFloat(chr_lengths[chr_lengths.length-1])
            #console.log("chr_lengths: ", chr_lengths)

        show_marker_in_table: (marker_info) ->
            console.log("in show_marker_in_table")
            ### Searches for the select marker in the results table below ###
            if marker_info
                marker_name = marker_info[2]
            else
                marker_name = ""
            $("#qtl_results_filter").find("input:first").val(marker_name).keypress()

        create_svg: () ->
            svg = d3.select("#manhattan_plots")
                .append("svg")
                .attr("class", "manhattan_plot")
                .attr("width", @plot_width+@x_buffer)
                .attr("height", @plot_height+@y_buffer)
            
            return svg

        create_graph: () ->
            @add_border()
            @add_x_axis()
            @add_y_axis()
            @add_chr_lines()
            @fill_chr_areas()
            @add_chr_labels()
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

        create_scales: () ->
            @x_scale = d3.scale.linear()
                .domain([0, d3.max(@x_coords)])
                .range([@x_buffer, @plot_width])

            @y_scale = d3.scale.linear()
                .domain([0, @y_max])
                .range([@plot_height, @y_buffer])

        create_x_axis_tick_values: () ->
            tick_vals = []
            for val in [25..@cumulative_chr_lengths[0]] when val%25 == 0
                tick_vals.push(val)
                
            for length, i in @cumulative_chr_lengths
                if i == 0
                    continue
                chr_ticks = []
                tick_count = Math.floor(@chr_lengths[i]/25)
                tick_val = parseInt(@cumulative_chr_lengths[i-1])
                for tick in [0..(tick_count-1)]
                    tick_val += 25
                    chr_ticks.push(tick_val)
                Array::push.apply tick_vals, chr_ticks    
                    
            #console.log("tick_vals:", tick_vals)
            return tick_vals

        add_x_axis: () ->
            xAxis = d3.svg.axis()
                    .scale(@x_scale)
                    .orient("bottom")
                    .tickValues(@create_x_axis_tick_values())

            next_chr = 1
            tmp_tick_val = 0
            xAxis.tickFormat((d) =>
                d3.format("d") #format as integer
                if d < @cumulative_chr_lengths[0]
                    tick_val = d
                else
                    next_chr_length = @cumulative_chr_lengths[next_chr]
                    if d > next_chr_length
                        next_chr += 1
                        tmp_tick_val = 25
                        tick_val = tmp_tick_val
                    else
                        tmp_tick_val += 25
                        tick_val = tmp_tick_val
                return (tick_val)
            )

            @svg.append("g")
                .attr("class", "x_axis")
                .attr("transform", "translate(0," + @plot_height + ")")
                .call(xAxis)
                .selectAll("text")
                    .attr("text-anchor", "right")
                    .attr("dx", "-1.6em")
                    .attr("transform", (d) =>
                        return "translate(-12,0) rotate(-90)"
                    )
                    #.attr("dy", "-1.0em")                        
                                    

        add_y_axis: () ->
            yAxis = d3.svg.axis()
                    .scale(@y_scale)
                    .orient("left")
                    .ticks(5)
            
            @svg.append("g")
                .attr("class", "y_axis")
                .attr("transform", "translate(" + @x_buffer + ",0)")
                .call(yAxis)

        add_chr_lines: () ->
            @svg.selectAll("line")
                .data(@cumulative_chr_lengths, (d) =>
                    return d
                )
                .enter()
                .append("line")
                .attr("x1", @x_scale)
                .attr("x2", @x_scale)
                .attr("y1", @y_buffer)
                .attr("y2", @plot_height)
                .style("stroke", "#ccc")
                
        fill_chr_areas: () ->
            @svg.selectAll("rect.chr_fill_area_1")
                .data(_.zip(@chr_lengths, @cumulative_chr_lengths), (d) =>
                    return d
                )
                .enter()
                .append("rect")
                .attr("class", "chr_fill_area_1")
                .attr("x", (d, i) =>
                    if i == 0
                        return @x_scale(0)
                    else
                        return @x_scale(@cumulative_chr_lengths[i-1])
                )
                .attr("y", @y_buffer)
                .attr("width", (d) =>
                    return @x_scale(d[0])
                )
                .attr("height", @plot_height-@y_buffer)                

        add_chr_labels: () ->
            chr_names = []
            for key of @chromosomes
                chr_names.push(key)
            chr_info = _.zip(chr_names, @chr_lengths, @cumulative_chr_lengths)
            @svg.selectAll("text")
                .data(chr_info, (d) =>
                    return d
                )
                .enter()
                .append("text")
                .text((d) =>
                    return d[0]
                )
                .attr("x", (d) =>
                    return @x_scale(d[2] - d[1]/2)
                )
                .attr("y", @plot_height * 0.1)
                .attr("dx", "0em")
                .attr("text-anchor", "middle")
                .attr("font-family", "sans-serif")
                .attr("font-size", "18px")
                .attr("fill", "grey")

        add_plot_points: () ->
            @svg.selectAll("circle")
                .data(@plot_coordinates)
                .enter()
                .append("circle")
                .attr("cx", (d) =>
                    return parseFloat(@x_buffer) + ((parseFloat(@plot_width)-parseFloat(@x_buffer)) * d[0]/parseFloat(@x_max))
                )
                .attr("cy", (d) =>
                    return @plot_height - ((@plot_height-@y_buffer) * d[1]/@y_max)
                )
                .attr("r", 2)
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
                        .attr("fill", "yellow")
                        .call(@show_marker_in_table(d))
                )
                .on("mouseout", (d) =>
                    this_id = "point_" + String(d[2])
                    d3.select("#" + this_id).classed("d3_highlight", false)
                        .attr("r", 2)
                        .attr("fill", "black")
                        .call(@show_marker_in_table())
                )

    console.time('Create manhattan plot')
    new Manhattan_Plot(600, 1200)
    console.timeEnd('Create manhattan plot')