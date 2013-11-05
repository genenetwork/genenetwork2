var data = new Array();
samples_1 = js_data.samples_1;
samples_2 = js_data.samples_2;
i = 0;
for (var samplename in samples_1){
	sample1 = samples_1[samplename];
	sample2 = samples_2[samplename];
	data[i] = [sample1.value, sample2.value];
	i++;
}
   
    var margin = {top: 20, right: 15, bottom: 60, left: 60}
      , width = 800 - margin.left - margin.right
      , height = 600 - margin.top - margin.bottom;
    
    var x = d3.scale.linear()
              .domain([d3.min(data, function(d){return d[0];})*0.95, d3.max(data, function(d) { return d[0]; })*1.05])
              .range([ 0, width ]);
    
    var y = d3.scale.linear()
    	      .domain([d3.min(data, function(d){return d[1];})*0.95, d3.max(data, function(d) { return d[1]; })*1.05])
    	      .range([ height, 0 ]);
 
    var chart = d3.select('#scatter_plot')
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
	.attr('class', 'main axis date')
	.call(xAxis);

    // draw the y axis
    var yAxis = d3.svg.axis()
	.scale(y)
	.orient('left');

    main.append('g')
	.attr('transform', 'translate(0,0)')
	.attr('class', 'main axis date')
	.call(yAxis);

    var g = main.append("svg:g"); 
    
    g.selectAll("scatter-dots")
      .data(data)
      .enter().append("svg:circle")
          .attr("cx", function (d,i) { return x(d[0]); } )
          .attr("cy", function (d) { return y(d[1]); } )
          .attr("r", 6);