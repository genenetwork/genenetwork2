create_manhattan_plot = ->
    h = 500
    w = 1200
    margin = {left:60, top:40, right:40, bottom: 40, inner:5}
    halfh = (h+margin.top+margin.bottom)
    totalh = halfh*2
    totalw = (w+margin.left+margin.right)
    
    # simplest use
    #d3.json "data.json", (data) ->
    mychart = lodchart().lodvarname("lod.hk")
                        .height(h)
                        .width(w)
                        .margin(margin)
    
    data = js_data.json_data
    
    d3.select("div#topchart")
      .datum(data)
      .call(mychart)
    
    # grab chromosome rectangles; color pink on hover
    chrrect = mychart.chrSelect()
    chrrect.on "mouseover", ->
                d3.select(this).attr("fill", "#E9CFEC")
           .on "mouseout", (d,i) ->
                d3.select(this).attr("fill", ->
                      return "#F1F1F9"  if i % 2
                      "#FBFBFF")
    
    # animate points at markers on click
    mychart.markerSelect()
              .on "click", (d) ->
                    r = d3.select(this).attr("r")
                    d3.select(this)
                      .transition().duration(500).attr("r", r*3)
                      .transition().duration(500).attr("r", r)
                  
create_manhattan_plot()

$("#export").click =>
    #Get d3 SVG element
    svg = $("#topchart").find("svg")[0]
    
    #Extract SVG text string
    svg_xml = (new XMLSerializer).serializeToString(svg)
    console.log("svg_xml:", svg_xml)
        
    #Set filename
    filename = "manhattan_plot_" + js_data.this_trait

    #Make a form with the SVG data
    form = $("#exportform")
    form.find("#data").val(svg_xml)
    form.find("#filename").val(filename)
    form.submit()

$("#export_pdf").click =>
    
    #$('#topchart').remove()
    #$('#chart_container').append('<div class="qtlcharts" id="topchart"></div>')
    #create_interval_map()
    
    #Get d3 SVG element
    svg = $("#topchart").find("svg")[0]
    
    #Extract SVG text string
    svg_xml = (new XMLSerializer).serializeToString(svg)
    console.log("svg_xml:", svg_xml)
        
    #Set filename
    filename = "manhattan_plot_" + js_data.this_trait

    #Make a form with the SVG data
    form = $("#exportpdfform")
    form.find("#data").val(svg_xml)
    form.find("#filename").val(filename)
    form.submit()
