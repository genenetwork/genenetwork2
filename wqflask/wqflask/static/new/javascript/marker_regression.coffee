$ ->

    class Manhattan_Plot

        constructor: ->
            @qtl_results = js_data.qtl_results
            @max_chr = @get_max_chr()
            
            @x_coords = []
            @y_coords = []
            @get_coordinates()
            
            @x_max = d3.max(@x_coords)
            @y_max = d3.max(@y_coords)
            
            @plot_coordinates = _.zip(@x_coords, @y_coords)
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


        get_coordinates: () ->
            for result in js_data.qtl_results
                chr = parseInt(result.chr)
                if _.isNaN(chr)
                    if result.chr == "X"
                        chr = @max_chr + 1
                    else if result.chr == "Y"
                        chr = @max_chr + 2
        
                @x_coords.push((chr * 200) + parseFloat(result.Mb))
                @y_coords.push(result.lrs_value)


        create_graph: () ->
            svg = d3.select("#manhattan_plots")
                        .append("svg")
                        .attr("width", 1000)
                        .attr("height", 800)
        
            svg.selectAll("circle")
                .data(@plot_coordinates)
                .enter()
                .append("circle")
                .attr("cx", (d) =>
                    return (1000 * d[0]/@x_max)
                     #return ((900 * (d[0]/x_max)) + 50)
                )
                .attr("cy", (d) =>
                     return 800 - (600 * d[1]/@y_max)
                )
                .attr("r", 3)

    new Manhattan_Plot
