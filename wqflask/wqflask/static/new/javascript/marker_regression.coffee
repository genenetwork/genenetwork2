$ ->
    class Manhattan_Plot
        constructor: (@plot_height, @plot_width) ->
            @qtl_results = js_data.qtl_results
            @chromosomes = js_data.chromosomes

            @total_length = 0

            @max_chr = @get_max_chr()

            @x_coords = []
            @y_coords = []
            @marker_names = []    
            @create_coordinates()
            @scaled_chr_lengths = @get_chr_lengths()

            # Buffer to allow for the ticks/labels to be drawn
            @x_buffer = @plot_width/25
            @y_buffer = @plot_height/20
            
            #@x_max = d3.max(@x_coords)
            console.log("x_max is", d3.max(@x_coords))
            @x_max = @total_length
            console.log("x_max is", @x_max)
            @y_max = d3.max(@y_coords) * 1.2

            @svg = @create_svg()
            @plot_coordinates = _.zip(@x_coords, @y_coords, @marker_names)
            @plot_height -= @y_buffer
            @create_scales()
            @create_graph()

        get_max_chr: () ->
            max_chr = 0
            for result in @qtl_results
                chr = parseInt(result.chr)
                console.log("foo:", chr, typeof(chr))
                if not _.isNaN(chr) 
                    if chr > max_chr
                        max_chr = chr
            return max_chr

        get_chr_lengths: () ->
            ###
            Gets a list of cumulative lengths in order to draw the vertical
            lines separating chromosomes (the position of one on the graph is its own length
            plus the lengths of all preceding chromosomes)
            
            ###
            
            cumulative_chr_lengths = []
            total_length = 0
            for key of @chromosomes
                this_length = @chromosomes[key]
                cumulative_chr_lengths.push(total_length + this_length)
                total_length += this_length
                
            console.log("total length is:", total_length)

            return cumulative_chr_lengths

        create_coordinates: () -> 
            chr_lengths = []
            chr_seen = []
            for result in js_data.qtl_results
                chr_length = @chromosomes[result.chr]
                if not(result.chr in chr_seen)
                    chr_seen.push(result.chr) 
                    chr_lengths.push(chr_length) 
                    if result.chr != "1"
                        @total_length += chr_lengths[chr_lengths.length - 2]
                        console.log("total_length is:", @total_length)                
                @x_coords.push(@total_length + parseFloat(result.Mb))
                @y_coords.push(result.lod_score)
                @marker_names.push(result.name)
            @total_length += chr_lengths[chr_lengths.length-1]
            console.log("total length is", @total_length)

            console.log("chr_lengths are:", chr_lengths)

        show_marker_in_table: (marker_info) ->
            ### Searches for the select marker in the results table below ###
            if marker_info
                marker_name = marker_info[2]
            else
                marker_name = ""
            $("#qtl_results_filter").find("input:first").val(marker_name).keyup()
            
        #unselect_marker: () ->
        #    $("#qtl_results_filter").find("input:first").val("").keyup()

        create_svg: () ->
            svg = d3.select("#manhattan_plots")
                .append("svg")
                .attr("width", @plot_width)
                .attr("height", @plot_height)
            
            return svg

        create_scales: () ->
            @x_scale = d3.scale.linear()
                .domain([0, d3.max(@x_coords)])
                .range([@x_buffer, @plot_width])

            @y_scale = d3.scale.linear()
                .domain([0, @y_max])
                .range([@plot_height, @y_buffer])

        create_graph: () ->
            @add_border()
            @add_y_axis()
            @add_chr_lines()
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

        add_y_axis: () ->
            yAxis = d3.svg.axis()
                    .scale(@y_scale)
                    .orient("left")
                    .ticks(5)
            
            @svg.append("g")
                .attr("class", "axis")
                .attr("transform", "translate(" + @x_buffer + ",0)")
                .call(yAxis)

        add_chr_lines: () ->
            @svg.selectAll("line")
                .data(@scaled_chr_lengths, (d) =>
                    return d
                )
                .enter()
                .append("line")
                .attr("x1", @x_scale)
                .attr("x2", @x_scale)
                .attr("y1", @y_buffer)
                .attr("y2", @plot_height)
                .style("stroke", "#ccc")
                

        add_plot_points: () ->
            @svg.selectAll("circle")
                .data(@plot_coordinates)
                .enter()
                .append("circle")
                .attr("cx", (d) =>
                    return @x_buffer + (@plot_width * d[0]/@x_max)
                )
                .attr("cy", (d) =>
                    return @plot_height - ((@plot_height) * d[1]/@y_max)
                )
                .attr("r", 2)
                .classed("circle", true)
                .on("mouseover", (d) =>
                    d3.select(d3.event.target).classed("d3_highlight", true)
                        .attr("r", 5)
                        .attr("fill", "yellow")
                        .call(@show_marker_in_table(d))
                )
                .on("mouseout", () =>
                    d3.select(d3.event.target).classed("d3_highlight", false)
                        .attr("r", 2)
                        .attr("fill", "black")
                        .call(@show_marker_in_table())
                )

    new Manhattan_Plot(600, 1200)
