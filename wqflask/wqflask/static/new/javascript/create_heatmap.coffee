create_heatmap = () ->

    h = 700
    w = 1000

    mychart = lodheatmap().height(h)
                          .width(w)
                          .zthresh(0.5)

    data = js_data.json_data

    console.log("data:", data)

    d3.select("div#chart")
      .datum(data)
      .call(mychart)
      
create_heatmap()