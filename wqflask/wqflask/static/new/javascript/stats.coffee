class Stats
    constructor: (@the_values) ->
        
    add_value: (value) ->
        @the_values.push(value)
    
    n_of_samples: ->
        return @the_values.length
        
    sum: ->
        total = 0
        total += value for value in @the_values
        return total
    
    mean: ->
        return @sum() / @n_of_samples()
    
    median: ->
        is_odd = @the_values.length % 2
        median_position = Math.floor(@the_values.length / 2)
        the_values_sorted = @the_values.sort((a,b) -> return a - b)
        if is_odd
            return the_values_sorted[median_position]
        else
            return (the_values_sorted[median_position] +
                    the_values_sorted[median_position - 1]) / 2
        
    std_dev: ->
        sum = 0
        for value in @the_values
            step_a = Math.pow(value - @mean(), 2)
            sum += step_a
        step_b = sum / @the_values.length
        return Math.sqrt(step_b)
    
    std_error: ->
        return @std_dev() / Math.sqrt(@n_of_samples())


bxd_only = new Stats([3, 5, 7, 8])
console.log("[red] bxd_only mean:", bxd_only.mean())
console.log("[green] bxd_only median:", bxd_only.median())
console.log("[purple] bxd_only std_dev:", bxd_only.std_dev())
console.log("[magenta] bxd_only std_error:", bxd_only.std_error())

window.Stats = Stats