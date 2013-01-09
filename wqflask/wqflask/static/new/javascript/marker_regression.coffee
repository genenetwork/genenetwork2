$ ->
    sort_number = (a, b) ->
        return a - b

    process_lrs_array = ->
        lrs_array = js_data.lrs_array
        bars = {}
        for lrs in lrs_array
            floored = Math.floor(lrs)
            if floored not of bars
                bars[floored] = 0
            bars[floored] += 1
            
        keys = []
        for key of bars
            keys.push(key)
        keys.sort(sort_number)
        
        bars_ordered = []
        for key in keys
            bars_ordered.push([parseInt(key), bars[key]])
    
        console.log("bars is:", bars)
        console.log("keys are:", keys)
        console.log("bars_ordered are:", bars_ordered)
        return bars_ordered
    
    display_permutation_histogram = (bars_ordered) ->
        $.jqplot('permutation_histogram',  [bars_ordered], 
            seriesDefaults: 
                renderer:$.jqplot.BarRenderer
            axes: 
                xaxis: 
                  min: 0
                  label: "LRS",
                  pad: 0
                yaxis: 
                  label: "Count",
                  pad: 0
        )


    bars_ordered = process_lrs_array()
    display_permutation_histogram(bars_ordered)