$ ->

    x_coords = []
    y_coords = []
    
    largest_chr = 0
    for result in js_data.qtl_results
        chr = parseInt(result.chr)
        console.log("foo:", chr, typeof(chr))
        if _.isNaN(chr) 
            console.log("Got NaN")
        else
            if chr > largest_chr
                largest_chr = chr
                
    console.log("largest_chr is:", largest_chr)
    
    for result in js_data.qtl_results
        chr = parseInt(result.chr)
        if _.isNaN(chr)
            if result.chr == "X"
                chr = largest_chr + 1
            else if result.chr == "Y"
                chr = largest_chr + 2

        x_coords.push((chr * 200) + parseFloat(result.Mb))
        y_coords.push(result.lrs_value)
        #plot_coordinates.push([x_coord, y_coord])

    x_max = d3.max(x_coords)
    y_max = d3.max(y_coords)
        
    plot_coordinates = _.zip(x_coords, y_coords)
        
    console.log(plot_coordinates)
        
    svg = d3.select("#manhattan_plots")
                .append("svg")
                .attr("width", 1000)
                .attr("height", 800)
                #.attr("transform", "translate(0," + y_max + ")")
                #.attr("transform", "scale(1,-1)")


    svg.selectAll("circle")
        .data(plot_coordinates)
        .enter()
        .append("circle")
        .attr("cx", (d) =>
            return (1000 * d[0]/x_max)
             #return ((900 * (d[0]/x_max)) + 50)
        )
        .attr("cy", (d) =>
             return 800 - (600 * d[1]/y_max)
        )
        .attr("r", 3)