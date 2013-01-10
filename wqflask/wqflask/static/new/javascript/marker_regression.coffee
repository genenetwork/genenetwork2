$ ->
    sort_number = (a, b) ->
        return a - b


    class Permutation_Histogram
        constructor: ->
            @process_data()
            @display_graph()
            
        process_data: ->
            # Put the data in a format needed for graphing 
            # The permutation count for a particular integer range (10-11 or 12-13 for example)
            # will be on the y-axis; LRS values will be on the x-axis
            lrs_array = js_data.lrs_array
            bars = {}
            for lrs in lrs_array
                floored = Math.floor(lrs)
                if floored not of bars
                    bars[floored] = 0
                bars[floored] += 1
    
            # Now we need to take the unordered hash
            # And order the keys
            keys = []
            for key of bars
                keys.push(key)
        
            keys.sort(sort_number)
            
    
            # Now that we have the ordered keys above
            # We can build an array of arrays that jqPlot will use
            @bars_ordered = []
            for key in keys
                @bars_ordered.push([parseInt(key), bars[key]])
    
            console.log("bars is:", bars)
            console.log("keys are:", keys)
            console.log("bars_ordered are:", @bars_ordered)
            #return bars_ordered
    
        display_graph: ->
        
            $.jqplot('permutation_histogram',  [@bars_ordered],
                title: 'Permutation Histogram'     
                seriesDefaults:
                    renderer:$.jqplot.BarRenderer
                    rendererOptions: 
                        barWidth: 15
                    pointLabels: 
                        show: true
                axesDefaults:
                    labelRenderer: $.jqplot.CanvasAxisLabelRenderer
                axes: 
                    xaxis: 
                      min: 0
                      label: "LRS"
                      pad: 1.1
                    yaxis:
                      min: 0
                      label: "Frequency"
            )
        
    #process_qtl_results = ->
    #    qtl_results = js_data.qtl_results
        
    #display_manhattan_plot = ->



    #bars_ordered = process_lrs_array()
    #display_permutation_histogram(bars_ordered)
    
    class Chromosome
        constructor:  (@name) ->
            @max_mb = 0
            @plot_points = []
            
        process_point: (mb, lrs) ->
            if mb > @max_mb
                @max_mb = mb
            @plot_points.push([mb, lrs])
            
        display_graph: ->
            div_name = 'manhattan_plot_' + @name
            console.log("div_name:", div_name)
        
            x_axis_max = Math.ceil(@max_mb/25) * 25
            x_axis_ticks = []
            x_tick = 0
            while (x_tick <= x_axis_max)
                x_axis_ticks.push(x_tick)
                x_tick += 25
            $.jqplot(div_name,  [@plot_points],
                title: @name
                seriesDefaults:
                    showLine: false
                    markerRenderer: $.jqplot.MarkerRenderer
                    markerOptions:
                        style: "filledCircle"
                        size: 3
                axesDefaults:
                    tickRenderer: $.jqplot.CanvasAxisTickRenderer
                    labelRenderer: $.jqplot.CanvasAxisLabelRenderer
                axes: 
                    xaxis: 
                        min: 0
                        max: x_axis_max
                        ticks: x_axis_ticks
                        tickOptions:
                            angle: 90
                            showGridline: false
                            formatString: '%d' 
                        label: "Megabases"
                    yaxis:
                        min: 0
                        label: "LRS"
                        tickOptions:
                            showGridline: false
            )

    class Manhattan_Plot
        constructor: ->
            @chromosomes = {}   # Hash of chromosomes
            
            @build_chromosomes()
            
            #@process_data()
            @display_graphs()
            
        build_chromosomes: ->
            for result in js_data.qtl_results
                #if result.locus.chromosome == '1'
                chromosome = result.locus.chromosome
                if chromosome not of @chromosomes
                    @chromosomes[chromosome] = new Chromosome(chromosome)
                mb = parseInt(result.locus.mb)
                @chromosomes[chromosome].process_point(mb, result.lrs)
                 
                    #if mb > @max_mb
                    #    @max_mb = mb
                    #@plot_points.push([mb, result.lrs])
        
        display_graphs: ->
            ### Call display_graph for each chromosome ###
            
            # First get everything in the right order
            numbered_keys = []
            extra_keys = []
            for key of @chromosomes
                if isNaN(key)
                    extra_keys.push(key)
                else
                    numbered_keys.push(key)
        
            numbered_keys.sort(sort_number)
            extra_keys.sort()
            keys = numbered_keys.concat(extra_keys)
            console.log("keys are:", keys)
            
            for key in keys
                html = """<div id="manhattan_plot_#{ key }" class="manhattan_plot_segment"></div>"""
                console.log("html is:", html)
                $("#manhattan_plots").append(html)
                @chromosomes[key].display_graph()
            
            
            
        #process_data: ->
        #    qtl_results = js_data.qtl_results
        #    #console.log("qtl_results: ", qtl_results)
        #    @plot_points = []
        #    @max_mb = 0
        #    for result in qtl_results
        #        if result.locus.chromosome == '1'
        #            mb = parseInt(result.locus.mb)
        #            if mb > @max_mb
        #                @max_mb = mb
        #            @plot_points.push([mb, result.lrs])
                


    new Permutation_Histogram
    new Manhattan_Plot