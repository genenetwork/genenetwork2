# illustration of use of the scatterplot function

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
                       .height(h)
                       .width(w)
                       .margin(margin)

data = js_data.probability_plot_data
#indID = js_data.indIDs
#slope = js_data.slope
#intercept = js_data.intercept

console.log("THE DATA IS:", data)

d3.select("div#prob_plot")
  .datum({data:data})
  .call(mychart)

# animate points
mychart.pointsSelect()
          .on "mouseover", (d) ->
             d3.select(this).attr("r", mychart.pointsize()*3)
          .on "mouseout", (d) ->
             d3.select(this).attr("r", mychart.pointsize())
