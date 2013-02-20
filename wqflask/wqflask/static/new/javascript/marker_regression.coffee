$ ->
    class Manhattan_Plot
        constructor: (@plot_height, @plot_width) ->
            @qtl_results = js_data.qtl_results
            @chromosomes = js_data.chromosomes
            
            #@plot_height = 500
            #@plot_width = 100 
            @total_length = 0
            
            @max_chr = @get_max_chr()
            @scaled_chr_lengths = @get_chr_lengths()
            console.log("scaled_chr_lengths is", @scaled_chr_lengths)

            @x_coords = []
            @y_coords = []
            @marker_names = []
            @get_coordinates()

            @x_max = d3.max(@x_coords)
            console.log("x_max is:", @x_max)
            @y_max = d3.max(@y_coords) 

            @plot_coordinates = _.zip(@x_coords, @y_coords, @marker_names)
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
                
            console.log("@plot_width:", @plot_width)
            console.log("lengths:", cumulative_chr_lengths)
            console.log("total_length:", total_length)
            
            #scaled_chr_lengths = (@plot_width * (x/total_length) for x in cumulative_chr_lengths)
            return cumulative_chr_lengths

        get_coordinates: () -> 
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

            console.log("chr_lengths are:", chr_lengths)


        display_info: (d) -> 
            $("#qtl_results_filter").find("input:first").val(d[2]).keyup()
            
        undisplay_info: () ->
            $("#qtl_results_filter").find("input:first").val("").keyup()

        create_graph: () ->
            svg = d3.select("#manhattan_plots")
                        .append("svg")
                        .style('border', '2px solid black')
                        .attr("width", @plot_width)
                        .attr("height", @plot_height)
        
            #svg.selectAll("text")
            #    .data(@plot_coordinates);
            #    .enter()
            #    .append("text")
            #    .attr("x", (d) =>
            #        return (@plot_width * d[0]/@x_max)
            #    )
            #    .attr("y", (d) =>
            #        return @plot_height - ((0.8*@plot_height) * d[1]/@y_max)
            #    )
            #    .text((d) => d[2])
            #    .attr("font-family", "sans-serif")
            #    .attr("font-size", "12px")
            #    .attr("fill", "black");
            
            svg.selectAll("circle")
                .data(@plot_coordinates)
                .enter()
                .append("circle")
                .attr("cx", (d) =>
                    return (@plot_width * d[0]/@x_max)
                )
                .attr("cy", (d) =>
                    return @plot_height - ((0.8*@plot_height) * d[1]/@y_max)
                )
                .attr("r", 2)
                .classed("circle", true)
                .on("mouseover", (d) =>
                    d3.select(d3.event.target).classed("d3_highlight", true)
                        .attr("r", 5)
                        .attr("fill", "yellow")
                        .call(@display_info(d))
                )
                .on("mouseout", () =>
                    d3.select(d3.event.target).classed("d3_highlight", false)
                        .attr("r", 2)
                        .attr("fill", "black")
                        .call(@undisplay_info())
                )
                .attr("title", "foobar")
                
                        #.append("svg:text")
                        #.text("test")
                        #.attr("dx", 12)
                        #.attr("dy", ".35em")
                        #.attr("font-family", "sans-serif")
                        #.attr("font-size", "11px")
                        #.attr("fill", "red")
                        #.attr("x", @plot_width * d[0]/@x_max)
                        #.attr("y", @plot_height - ((0.8*@plot_height) * d[1]/@y_max))                 

                        
                    #d3.select(this).enter().append("svg:text") 
                    #                .text("test") 
                    #                .attr("x", function(d, i) { return i; } ) 
                    #                .attr("y", function(d) { return -1 * d; }) 
                    #                          }) 
                        #.attr("font-family", "sans-serif")
                        #.attr("font-size", "11px")
                        #.attr("fill", "red")
                        #.text(d[1])
                        #.attr("x", @plot_width * d[0]/@x_max)
                        #.attr("y", @plot_height - ((0.8*@plot_height) * d[1]/@y_max))
                        #.attr("font-family", "sans-serif")
                        #.attr("font-size", "11px")
                        #.attr("fill", "red")              
                


            x = d3.scale.linear()
                .domain([0, @x_max])
                .range([0, @plot_width])
                
            y = d3.scale.linear()
                .domain([0, @y_max])
                .range([0, @plot_height])
                
            svg.selectAll("line")
                .data(@scaled_chr_lengths)
                .enter()
                .append("line")
                .attr("x1", x)
                .attr("x2", x)
                .attr("y1", 0)
                .attr("y2", @plot_height)
                .style("stroke", "#ccc")

    new Manhattan_Plot(600, 1200)
