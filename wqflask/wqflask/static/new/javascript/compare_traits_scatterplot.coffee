root = exports ? this

root.create_scatterplot = (json_ids, json_data) ->
    
    console.log("TESTING2")
    
    h = 400
    w = 500
    margin = {left:60, top:40, right:40, bottom: 40, inner:5}
    halfh = (h+margin.top+margin.bottom)
    totalh = halfh*2
    halfw = (w+margin.left+margin.right)
    totalw = halfw*2
    
    # Example 1: simplest use
    #d3.json "data.json", (data) ->
    mychart = scatterplot().xvar(0)
                           .yvar(1)
                           .xlab("X")
                           .ylab("Y")
                           .height(h)
                           .width(w)
                           .margin(margin)
    
    data = json_data
    indID = json_ids
    #slope = js_data.slope
    #intercept = js_data.intercept
    
    d3.select("div#comparison_scatterplot")
      .datum({data:data, indID:indID})
      .call(mychart)
    
    # animate points
    mychart.pointsSelect()
              .on "mouseover", (d) ->
                 d3.select(this).attr("r", mychart.pointsize()*3)
              .on "mouseout", (d) ->
                 d3.select(this).attr("r", mychart.pointsize())

root.create_scatterplots = (trait_names, json_ids, json_data) ->
    
    #There are various places where 1 is subtracted from the number of traits; this is because
    #we don't want to show a first graph consisting of the trait vs itself. There might be a better
    #way to deal with this.
    
    console.log("json_data:", json_data)
    console.log("trait_names:", trait_names)
    
    num_traits = json_data.length
    console.log("num_traits:", num_traits)
    
    h = 300
    w = 400
    margin = {left:60, top:40, right:40, bottom: 40, inner:5}
    halfh = (h+margin.top+margin.bottom)
    totalh = halfh*(num_traits-1)
    #totalh = halfh*2
    halfw = (w+margin.left+margin.right)
    #totalw = halfw*2
    totalw = halfw
    
    xvar = []
    yvar = []
    xshift = []
    yshift = []
    for i in [0..num_traits-1]
        xvar.push(i)
        yvar.push(0)
        xshift.push(0)
        yshift.push(halfh*i) 
    
    console.log("xvar:", xvar)
    console.log("yvar:", yvar)
    
    # Example 2: three scatterplots within one SVG, with brushing
    #d3.json "data.json", (data) ->
    #xvar = [1, 2, 2]
    #yvar = [0, 0, 1]
    #console.log("num_traits_array:", xvar)
    #xshift = [0, halfw, halfw]
    #yshift = [0, 0, halfh]
    #xshift = [0, 0]
    #yshift = [0, halfh]

    svg = d3.select("div#comparison_scatterplot")
            .append("svg")
            .attr("height", totalh)
            .attr("width", totalw)
    
    mychart = []
    chart = []
    for i in [1..num_traits-1]
      mychart[i-1] = scatterplot().xvar(xvar[i])
                                .yvar(yvar[i])
                                .nxticks(6)
                                .height(h)
                                .width(w)
                                .margin(margin)
                                .pointsize(4)
                                .xlab("#{trait_names[i-1]}")
                                .ylab("#{trait_names[0]}")
                                .title("#{trait_names[0]} vs. #{trait_names[i-1]}")
    
      data = json_data
      indID = json_ids
    
      chart[i-1] = svg.append("g").attr("id", "chart#{i-1}")
                  .attr("transform", "translate(#{xshift[i]},#{yshift[i-1]})")
      chart[i-1].datum({data:data, indID:indID}).call(mychart[i-1])
    
    brush = []
    brushstart = (i) ->
      () ->
       for j in [0..num_traits-2]
         chart[j].call(brush[j].clear()) if j != i
       svg.selectAll("circle").attr("opacity", 0.6).classed("selected", false)
    
    brushmove = (i) ->
      () ->
        svg.selectAll("circle").classed("selected", false)
        e = brush[i].extent()
        chart[i].selectAll("circle")
           .classed("selected", (d,j) ->
                              circ = d3.select(this)
                              cx = circ.attr("cx")
                              cy = circ.attr("cy")
                              selected =   e[0][0] <= cx and cx <= e[1][0] and
                                           e[0][1] <= cy and cy <= e[1][1]
                              svg.selectAll("circle.pt#{j}").classed("selected", true) if selected
                              selected)
    
    brushend = () ->
      svg.selectAll("circle").attr("opacity", 1)
    
    xscale = d3.scale.linear().domain([margin.left,margin.left+w]).range([margin.left,margin.left+w])
    yscale = d3.scale.linear().domain([margin.top,margin.top+h]).range([margin.top,margin.top+h])
    
    for i in [0..num_traits-2]
      brush[i] = d3.svg.brush().x(xscale).y(yscale)
                      .on("brushstart", brushstart(i))
                      .on("brush", brushmove(i))
                      .on("brushend", brushend)
    
      chart[i].call(brush[i])