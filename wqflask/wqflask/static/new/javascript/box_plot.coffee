root = exports ? this

class Box_Plot
    constructor: (@sample_list, @sample_group) ->
        @get_samples()
        
        @margin = {top: 10, right: 50, bottom: 20, left: 50}
        @plot_width = 120 - @margin.left - @margin.right
        @plot_height = 500 - @margin.top - @margin.bottom
        
        @min = d3.min(@sample_vals)  
        @max = d3.max(@sample_vals) * 1.1
        
        @svg = @create_svg()
        
        @enter_data()
        

    get_samples: () ->
        @sample_names = (sample.name for sample in @sample_list when sample.value != null)
        @sample_vals = (sample.value for sample in @sample_list when sample.value != null)
        @samples = _.zip(@sample_names, @sample_vals)
        
    create_svg: () -> d3.chart.box()
                        .whiskers(@inter_quartile_range(1.5))
                        .width(@plot_width)
                        .height(@plot_height)
                        .domain([@min, @max])
                        
    enter_data: () ->
        d3.select("#box_plot").selectAll("svg")
            .data(@sample_vals)
            .enter().append("svg:svg")
            .attr("class", "box")
            .attr("width", @plot_width)
            .attr("height", @plot_height)
            .call(@svg)
                        
    inter_quartile_range: (k) ->
        return (d, i) =>
            q1 = d.quartiles[0],
            q3 = d.quartiles[2],
            inter_quartile_range = (q3 - q1) * k
            i = -1
            j = d.length
            while (d[++i] < q1 - inter_quartile_range)
            while (d[--j] > q3 + inter_quartile_range)
            return [i, j]

   