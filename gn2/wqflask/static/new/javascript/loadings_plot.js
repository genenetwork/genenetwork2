var margin = {top: 20, right: 70, bottom: 60, left: 60}
  , width = 960 - margin.left - margin.right
  , height = 500 - margin.top - margin.bottom;
    
var x = d3.scale.linear()
          .domain([d3.min(loadings, function(d) { return d[0]; }) + 0.1*d3.min(loadings, function(d) { return d[0]; }), d3.max(loadings, function(d) { return d[0]; })])
          .range([ 0, width ]);
    
var y = d3.scale.linear()
    	  .domain([d3.min(loadings, function(d) { return d[1]; }) + 0.1*d3.min(loadings, function(d) { return d[1]; }), d3.max(loadings, function(d) { return d[1]; })])
    	  .range([ height, 0 ]);
 
var chart = d3.select('#loadings_plot')
    .append('svg:svg')
    .attr('width', width + margin.right + margin.left)
    .attr('height', height + margin.top + margin.bottom)
    .attr('class', 'chart')

var main = chart.append('g')
    .attr('transform', 'translate(' + margin.left + ',' + margin.top + ')')
    .attr('width', width)
    .attr('height', height)
    .attr('class', 'main')   
        
// draw the x axis
var xAxis = d3.svg.axis()
    .scale(x)
    .orient('bottom');

main.append('g')
    .attr('transform', 'translate(0,' + height + ')')
    .attr('class', 'x axis')
    .call(xAxis);
    
chart.append("text")
    .attr("class", "x label")
    .attr("text-anchor", "end")
    .attr("x", 550)
    .attr("y", 480)
    .style("font-size", 14)
    .style("fill", "blue")
    .text("Factor (1)");
    
chart.append("text")
    .attr("class", "y label")
    .attr("text-anchor", "end")
    .attr("x", -200)
    .attr("y", 5)
    .attr("dy", ".75em")
    .attr("transform", "rotate(-90)")
    .style("font-size", 14)
    .style("fill", "blue")
    .text("Factor (2)");

// draw the y axis
var yAxis = d3.svg.axis()
    .scale(y)
    .orient('left');

main.append('g')
    .attr('transform', 'translate(0,0)')
    .attr('class', 'y axis')
    .call(yAxis);

chart.select('.x.axis')
    .selectAll("text")
        .style("font-size","14px");
        
chart.select('.y.axis')
    .selectAll("text")
        .style("font-size","14px");
    
var g = main.append("svg:g"); 
    
g.selectAll("scatter-dots")
  .data(loadings)
  .enter().append("svg:circle")
            .attr("cx", function (d,i) { return x(d[0]); } )
            .attr("cy", function (d) { return y(d[1]); } )
            .attr("r", 4)
            .style("fill", "blue");
       
traits_and_loadings = []
for (i = 0; i < js_data.traits.length; i++) {
    this_trait_loadings = []
    this_trait_loadings[0] = js_data.traits[i]
    this_trait_loadings[1] = [loadings[i][0], loadings[i][1]]  
    traits_and_loadings[i] = this_trait_loadings
}
       
g.selectAll("scatter-dots")
  .data(traits_and_loadings)
  .enter().append("text")
            .attr("x", function(d, i) { return x(d[1][0]); })
            .attr("y", function(d) { return y(d[1][1]); })
            .text(function(d) { return d[0]; })
                .style("font-size", 12)
                .style("fill", "blue");
            
g.selectAll("scatter-lines")
  .data(loadings)
  .enter().append("svg:line")
            .attr("x1", x(0))
            .attr("y1", y(0))
            .attr("x2", function (d,i) {return x(d[0]); } )
            .attr("y2", function (d) { return y(d[1]); } )
            .attr("stroke-width", 1)
            .attr("stroke", "red");
      