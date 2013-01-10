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
    
    class Manhattan_Plot
        constructor: ->
            @process_data()
            @display_graph()
            
        process_data: ->
            qtl_results = js_data.qtl_results
            #console.log("qtl_results: ", qtl_results)
            @plot_points = []
            @max_mb = 0
            for result in qtl_results
                if result.locus.chromosome == '1'
                    if parseInt(result.locus.mb) > @max_mb
                        @max_mb = result.locus.mb
                    @plot_points.push([result.locus.mb, result.lrs])
                
        display_graph: ->
            x_axis_max = Math.ceil(@max_mb/25) * 25
            x_axis_ticks = []
            x_tick = 0
            while (x_tick <= x_axis_max)
                x_axis_ticks.push(x_tick)
                x_tick += 25
            #console.log("@plot_points is:", @plot_points)
            $.jqplot('manhattan_plot',  [@plot_points],
                title: '1'
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
                        label: "Megabases"
                    yaxis:
                        min: 0
                        label: "LRS"
                        tickOptions:
                            showGridline: false
            )

    new Permutation_Histogram
    new Manhattan_Plot