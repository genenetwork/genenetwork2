root = exports ? this

root.create_scatterplot = (json_ids, json_data) ->
    
    console.log("TESTING TESTING2")
    
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

root.create_scatterplots = (json_ids, json_data) ->
    h = 400
    w = 500
    margin = {left:60, top:40, right:40, bottom: 40, inner:5}
    halfh = (h+margin.top+margin.bottom)
    totalh = halfh*2
    halfw = (w+margin.left+margin.right)
    totalw = halfw*2
    
    # Example 2: three scatterplots within one SVG, with brushing
    #d3.json "data.json", (data) ->
    xvar = [1, 2, 2]
    yvar = [0, 0, 1]
    xshift = [0, halfw, halfw]
    yshift = [0, 0, halfh]
    
    svg = d3.select("div#chart2")
            .append("svg")
            .attr("height", totalh)
            .attr("width", totalw)
    
    mychart = []
    chart = []
    for i in [0..2]
      mychart[i] = scatterplot().xvar(xvar[i])
                                .yvar(yvar[i])
                                .nxticks(6)
                                .height(h)
                                .width(w)
                                .margin(margin)
                                .pointsize(4)
                                .xlab("X#{xvar[i]+1}")
                                .ylab("X#{yvar[i]+1}")
                                .title("X#{yvar[i]+1} vs. X#{xvar[i]+1}")
    
      chart[i] = svg.append("g").attr("id", "chart#{i}")
                    .attr("transform", "translate(#{xshift[i]},#{yshift[i]})")
      chart[i].datum({data:data}).call(mychart[i])
    
    brush = []
    brushstart = (i) ->
      () ->
       for j in [0..2]
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
    
    for i in [0..2]
      brush[i] = d3.svg.brush().x(xscale).y(yscale)
                      .on("brushstart", brushstart(i))
                      .on("brush", brushmove(i))
                      .on("brushend", brushend)
    
      chart[i].call(brush[i])