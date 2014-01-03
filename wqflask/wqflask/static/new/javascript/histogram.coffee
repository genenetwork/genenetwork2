root = exports ? this

class Histogram
    constructor: (@sample_list, @sample_group) ->
        @sort_by = "name"
        @format_count = d3.format(",.0f") #a formatter for counts
        @get_samples()
        #if @sample_attr_vals.length > 0
        #    @get_distinct_attr_vals()
        #    @get_attr_color_dict(@distinct_attr_vals)
        
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

    create_svg: () ->
        svg = d3.select("#histogram")
          .append("svg")
            .attr("class", "bar_chart")
            .attr("width", @plot_width + @margin.left + @margin.right)
            .attr("height", @plot_height + @margin.top + @margin.bottom)
          .append("g")
            .attr("transform", "translate(" + @margin.left + "," + @margin.top + ")")
            
        return svg
        
    create_x_scale: () ->
        @x_scale = d3.scale.linear()
            .domain([d3.min(@sample_vals), d3.max(@sample_vals)])
            .range([0, @plot_width])    

    get_histogram_data: () ->
        console.log("sample_vals:", @sample_vals)
        @histogram_data = d3.layout.histogram()
            .bins(@x_scale.ticks(10))(@sample_vals)
        console.log("histogram_data:", @histogram_data[0])

    create_y_scale: () ->
        @y_scale = d3.scale.linear()
            .domain([0, d3.max(@histogram_data, (d) => return d.y )])
            .range([@plot_height, 0])

    create_graph: () ->
        
        @add_x_axis()
        #@add_y_axis() 

        @add_bars()
        
    add_x_axis: () ->
        x_axis = d3.svg.axis()
            .scale(@x_scale)
            .orient("bottom");
        
        @svg.append("g")
            .attr("class", "x axis")
            .attr("transform", "translate(0," + @plot_height + ")")
            .call(x_axis)
            #.selectAll("text")  
            #    .style("text-anchor", "end")
            #    .style("font-size", "12px")
            #    .attr("dx", "-.8em")
            #    .attr("dy", "-.3em")
            #    .attr("transform", (d) =>
            #        return "rotate(-90)" 
            #    )

    #add_y_axis: () ->
    #    y_axis = d3.svg.axis()
    #            .scale(@y_scale)
    #            .orient("left")
    #            .ticks(5)
    #
    #    @svg.append("g")
    #        .attr("class", "y axis")
    #        .call(y_axis)
    #      .append("text")
    #        .attr("transform", "rotate(-90)")
    #        .attr("y", 6)
    #        .attr("dy", ".71em")
    #        .style("text-anchor", "end")

    add_bars: () ->
        @svg.selectAll(".bar")
            .data(@histogram_data)
          .enter().append("g")
            .attr("class", "bar")
            .attr("transform", (d) =>
                return "translate(" + @margin.left + "," + @margin.top + ")")
          .append("rect")
            .attr("x", 1)
            .attr("width", @x_scale(@histogram_data[0].dx) - 1)
            .attr("height", (d) =>
                return @plot_height - @y_scale(d.y)
            )
          .append("text")
            .attr("dy", ".75em")
            .attr("y", 6)
            .attr("x", @x_scale(@histogram_data[0].dx) / 2)
            .attr("text-anchor", "middle")
            .text((d) =>
                return @format_count(d.y)
            )

    #open_trait_selection: () ->
    #    $('#collections_holder').load('/collections/list?color_by_trait #collections_list', =>
    #        $.colorbox(
    #            inline: true
    #            href: "#collections_holder"
    #        )
    #        #Removes the links from the collection names, because clicking them would leave the page
    #        #instead of loading the list of traits in the colorbox
    #        $('a.collection_name').attr( 'onClick', 'return false' )
    #        #$('.collection_name').each (index, element) =>
    #        #    console.log("contents:", $(element).contents())
    #        #    $(element).contents().unwrap()
    #    )

root.Histogram = Histogram