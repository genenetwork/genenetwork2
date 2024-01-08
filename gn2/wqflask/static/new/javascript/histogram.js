// Generated by CoffeeScript 1.9.2
(function() {
  var Histogram, root;

  root = typeof exports !== "undefined" && exports !== null ? exports : this;

  Histogram = (function() {
    function Histogram(sample_list1, sample_group) {
      this.sample_list = sample_list1;
      this.sample_group = sample_group;
      this.sort_by = "name";
      this.format_count = d3.format(",.0f");
      this.margin = {
        top: 10,
        right: 30,
        bottom: 30,
        left: 30
      };
      this.plot_width = 960 - this.margin.left - this.margin.right;
      this.plot_height = 500 - this.margin.top - this.margin.bottom;
      this.x_buffer = this.plot_width / 20;
      this.y_buffer = this.plot_height / 20;
      this.plot_height -= this.y_buffer;
      this.get_sample_vals(this.sample_list);
      this.redraw(this.sample_vals);
    }

    Histogram.prototype.redraw = function(sample_vals) {
      this.sample_vals = sample_vals;
      this.y_min = d3.min(this.sample_vals);
      this.y_max = d3.max(this.sample_vals) * 1.1;
      this.create_x_scale();
      this.get_histogram_data();
      this.create_y_scale();
      $("#histogram").empty();
      this.svg = this.create_svg();
      return this.create_graph();
    };

    Histogram.prototype.get_sample_vals = function(sample_list) {
      var sample;
      return this.sample_vals = (function() {
        var i, len, results;
        results = [];
        for (i = 0, len = sample_list.length; i < len; i++) {
          sample = sample_list[i];
          if (sample.value !== null) {
            results.push(sample.value);
          }
        }
        return results;
      })();
    };

    Histogram.prototype.create_svg = function() {
      var svg;
      svg = d3.select("#histogram").append("svg").attr("class", "histogram").attr("width", this.plot_width + this.margin.left + this.margin.right).attr("height", this.plot_height + this.margin.top + this.margin.bottom).append("g").attr("transform", "translate(" + this.margin.left + "," + this.margin.top + ")");
      return svg;
    };

    Histogram.prototype.create_x_scale = function() {
      var x0;
      console.log("min/max:", d3.min(this.sample_vals) + "," + d3.max(this.sample_vals));
      x0 = Math.max(-d3.min(this.sample_vals), d3.max(this.sample_vals));
      return this.x_scale = d3.scale.linear().domain([d3.min(this.sample_vals), d3.max(this.sample_vals)]).range([0, this.plot_width]).nice();
    };

    Histogram.prototype.get_histogram_data = function() {
      var n_bins;
      console.log("sample_vals:", this.sample_vals);
      n_bins = 2*Math.sqrt(this.sample_vals.length); //Was originally just the square root, but increased to 2*; ideally would be a GUI for changing this
      this.histogram_data = d3.layout.histogram().bins(this.x_scale.ticks(n_bins))(this.sample_vals);
      return console.log("histogram_data:", this.histogram_data[0]);
    };

    Histogram.prototype.create_y_scale = function() {
      return this.y_scale = d3.scale.linear().domain([
        0, d3.max(this.histogram_data, (function(_this) {
          return function(d) {
            return d.y;
          };
        })(this))
      ]).range([this.plot_height, 0]);
    };

    Histogram.prototype.create_graph = function() {
      this.add_x_axis();
      this.add_y_axis();
      return this.add_bars();
    };

    Histogram.prototype.add_x_axis = function() {
      var x_axis;
      x_axis = d3.svg.axis().scale(this.x_scale).orient("bottom");
      return this.svg.append("g").attr("class", "x axis").attr("transform", "translate(0," + this.plot_height + ")").call(x_axis);
    };

    Histogram.prototype.add_y_axis = function() {
      var yAxis;
      yAxis = d3.svg.axis().scale(this.y_scale).orient("left").ticks(5);
      return this.svg.append("g").attr("class", "y axis").call(yAxis).append("text").attr("transform", "rotate(-90)").attr("y", 6).attr("dy", ".71em").style("text-anchor", "end");
    };

    Histogram.prototype.add_bars = function() {
      var bar, rect_width;
      bar = this.svg.selectAll(".bar").data(this.histogram_data).enter().append("g").attr("class", "bar").attr("transform", (function(_this) {
        return function(d) {
          return "translate(" + _this.x_scale(d.x) + "," + _this.y_scale(d.y) + ")";
        };
      })(this));
      rect_width = this.x_scale(this.histogram_data[0].x + this.histogram_data[0].dx) - this.x_scale(this.histogram_data[0].x);
      bar.append("rect").attr("x", 1).attr("width", rect_width - 1).attr("height", (function(_this) {
        return function(d) {
          return _this.plot_height - _this.y_scale(d.y);
        };
      })(this));
      return bar.append("text").attr("dy", ".75em").attr("y", 6).attr("x", rect_width / 2).attr("text-anchor", "middle").style("fill", "#fff").text((function(_this) {
        return function(d) {
          var bar_height;
          bar_height = _this.plot_height - _this.y_scale(d.y);
          if (bar_height > 20) {
            return _this.format_count(d.y);
          }
        };
      })(this));
    };

    return Histogram;

  })();

  root.Histogram = Histogram;

}).call(this);