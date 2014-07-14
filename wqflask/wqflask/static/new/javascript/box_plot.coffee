root = exports ? this

class Box_Plot
    constructor: (@sample_list, @sample_group) ->
        @get_samples()
        
        @margin = {top: 10, right: 50, bottom: 20, left: 50}
        @plot_width = 200 - @margin.left - @margin.right
        @plot_height = 500 - @margin.top - @margin.bottom
        
        @min = d3.min(@sample_vals)  
        @max = d3.max(@sample_vals)
        
        @svg = @create_svg()
        @enter_data()
        
        
    get_samples: () ->
        @sample_vals = (sample.value for sample in @sample_list when sample.value != null)
        
    create_svg: () ->
        svg = d3.box()
            .whiskers(@inter_quartile_range(1.5))
            .width(@plot_width - 30)
            .height(@plot_height - 30)
            .domain([@min, @max])
        return svg
                    
    enter_data: () ->
        d3.select("#box_plot").selectAll("svg")
            .data([@sample_vals])
            .enter().append("svg:svg")
            .attr("class", "box")
            .attr("width", @plot_width)
            .attr("height", @plot_height)
            .append("svg:g")
            .call(@svg)
                        
    inter_quartile_range: (k) ->
        return (d, i) =>
            console.log("iqr d:", d)
            q1 = d.quartiles[0]
            q3 = d.quartiles[2]
            inter_quartile_range = (q3 - q1) * k
            console.log("iqr:", inter_quartile_range)
            i = 0
            j = d.length
            console.log("d[-1]:", d[1])
            console.log("q1 - iqr:", q1 - inter_quartile_range)
            i++ while (d[i] < q1 - inter_quartile_range)
            j-- while (d[j] > q3 + inter_quartile_range)
            #while (d[++i] < q1 - inter_quartile_range
            #while d[--j] > q3 + inter_quartile_range
            console.log("[i, j]", [i, j])
            return [i, j]

root.Box_Plot = Box_Plot