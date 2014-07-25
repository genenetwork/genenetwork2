create_heatmap = () ->

    h = 500
    w = 1200

    mychart = lodheatmap().height(h)
                          .width(w)
                          #.zthresh(1)

    data = js_data.json_data

    console.log("data:", data)

    d3.select("div#chart")
      .datum(data)
      .call(mychart)
      
create_heatmap()