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
            # Figure out the largest key, so we can make sure the x axis max is one larger later on
            #max_lrs = bars_ordered[bars_ordered.length-1][0]
            #console.log("max_key is:", max_lrs)
        
            $.jqplot('permutation_histogram',  [@bars_ordered],
                title: 'Permutation Histogram'     
                seriesDefaults:
                    renderer:$.jqplot.BarRenderer
                    rendererOptions: 
                        #barPadding: 30
                        #barMargin: 30
                        barWidth: 15
                        #shadowOffset: 2
                        #shadowDepth: 5
                        #shadowAlpha: 0.8
                    pointLabels: 
                        show: true
                axesDefaults:
                    labelRenderer: $.jqplot.CanvasAxisLabelRenderer
                axes: 
                    xaxis: 
                      min: 0
                      #max: max_lrs + 2
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
    
    new Permutation_Histogram