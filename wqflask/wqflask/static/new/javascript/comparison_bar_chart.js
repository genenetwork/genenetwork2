generate_traces = function() {
  traces = [];
  for (i = 0, _len = js_data.traits.length; i < _len; i++) {
    this_trace = {
      x: js_data.samples,
      y: js_data.sample_data[i],
      name: js_data.traits[i],
      type: 'bar',
      bargap: 20
    }

    traces.push(this_trace)   
  }

  return traces
}

create_bar_chart = function() {
  var data = generate_traces()
  var layout = {barmode: 'group', bargap: 5};

  Plotly.newPlot('comp_bar_chart', data, layout);
}

create_bar_chart();