/**
 * mapping_figure.js
 *
 * Client-side d3 rendering of the GeneNetwork mapping figure.
 * This replaces the server-side PIL figure + HTML imagemap so that
 * interactions (zoom to a chromosome, etc.) happen entirely in the
 * browser without reloading the page.
 *
 * Requires: d3 v3 (d3.scale.linear / d3.svg.axis), jQuery.
 *
 * Usage:
 *   window.MappingFigure.render("mapping-figure", mapping_data);
 *
 * `mapping_data` is provided by the server and has the shape:
 *   {
 *     markers: [ {chr, name, Mb|cM, lrs_value|lod_score, ...}, ... ],
 *     chr_lengths: [ {chr, size}, ... ],      // size in bases
 *     significant: <display-scale threshold> | null,
 *     suggestive:  <display-scale threshold> | null,
 *     lrsMax: 0,                              // fixed y-max, 0 = sliding
 *     LRS_LOD: "LRS" | "LOD" | "-logP",
 *     LODFACTOR: 4.61,
 *     plotScale: "physic" | ...,
 *     manhattan_plot: bool,
 *     color_scheme: "alternating" | "varied" | "single",
 *     manhattan_single_color: "#RRGGBB" | null,
 *     selected_chr, startMb, endMb, total_markers, this_trait,
 *     metadata_lines: [ "...", ... ],       // top-left metadata block
 *     gene_position: { chr, mb } | null,    // trait gene location marker
 *     n_samples, mapping_method
 *   }
 */
window.MappingFigure = (function () {
    "use strict";

    var MAX_SCORE = 460;             // webqtlConfig.MAXLRS cap
    var DEFAULT_WIDTH = 1280;        // GRAPH_DEFAULT_WIDTH
    var MAX_WIDTH = 2400;
    var PLOT_HEIGHT = 460;

    var MARGIN = { top: 110, right: 70, bottom: 95, left: 70 };
    var TOP_LABEL_INSET = 32;        // room at the top of the plot for chr labels
    var FONT = "Verdana, sans-serif";

    /* Colours mirror display_mapping_results.py */
    var COLORS = {
        backLight: "#FBFBFF",
        backDark: "#F1F1F9",
        chrStroke: "#DCDCDC",
        red: "#E8000B",
        blue: "#1f77b4",
        axis: "#0000FF",
        significant: "#EBC7C7",
        suggestive: "#DCDCDC",
        peak: "#7B2D8E",
        geneMarker: "#9370DB",       // MEDIUMPURPLE (TRANSCRIPT_LOCATION_COLOR)
        additivePositive: "#008000", // GREEN (ADDITIVE_COLOR_POSITIVE)
        additiveNegative: "#FFA500", // ORANGE (ADDITIVE_COLOR_NEGATIVE)
        text: "#000000",
        link: "#1f77b4"
    };

    var DISTINCT = [
        "#FF0000", "#00FF00", "#0000FF", "#FFFF00", "#FF00FF", "#00FFFF",
        "#000000", "#800000", "#008000", "#000080", "#808000", "#800080",
        "#008080", "#808080", "#C00000", "#00C000", "#0000C0", "#C0C000",
        "#C000C0", "#00C0C0", "#C0C0C0", "#400000", "#004000", "#000040"
    ];

    var state = { focusChr: null };

    var tipEl = null;

    /* ------------------------------ helpers ------------------------------ */

    function isLOD(mode) {
        return mode === "LOD" || mode === "-logP";
    }

    function toNum(v) {
        if (v === undefined || v === null || v === "") return null;
        if (typeof v === "string" && v.trim().toLowerCase() === "inf") {
            return MAX_SCORE;
        }
        var n = parseFloat(v);
        return isNaN(n) ? null : n;
    }

    /* Marker score in the display scale (mirrors drawQTL). */
    function markerScore(marker, data) {
        var f = data.LODFACTOR || 4.61;
        var mode = data.LRS_LOD || "LRS";
        var lrs = toNum(marker.lrs_value);
        var lod = toNum(marker.lod_score);
        var score;
        if (lrs !== null) {
            score = isLOD(mode) ? lrs / f : lrs;
        } else if (lod !== null) {
            score = (mode === "LRS") ? lod * f : lod;
        } else {
            score = 0;
        }
        return score > MAX_SCORE ? MAX_SCORE : score;
    }

    /* Marker position in bases (Mb or cM -> bases). */
    function markerBases(marker) {
        var mb = toNum(marker.Mb);
        if (mb !== null) return mb * 1e6;
        var cm = toNum(marker.cM);
        if (cm !== null) return cm * 1e6;
        return null;
    }

    /* Build chromosome layout from chr_lengths (numeric first, then X/Y/...). */
    function layoutChromosomes(data) {
        var lengths = (data.chr_lengths || []).map(function (c) {
            return { chr: String(c.chr), size: toNum(c.size) || 0 };
        }).filter(function (c) { return c.size > 0; });

        function sortKey(c) {
            var n = parseInt(c.chr, 10);
            return isNaN(n) ? [1, c.chr] : [0, n];
        }
        lengths.sort(function (a, b) {
            var ka = sortKey(a), kb = sortKey(b);
            if (ka[0] !== kb[0]) return ka[0] - kb[0];
            return ka[1] < kb[1] ? -1 : (ka[1] > kb[1] ? 1 : 0);
        });

        var total = lengths.reduce(function (s, c) { return s + c.size; }, 0);
        var interval = data.plotScale !== "physic"
            ? 5 * 1e6
            : (lengths.length ? total / (lengths.length * 12) : 0);

        var starts = [];
        var cursor = 0;
        lengths.forEach(function (c) {
            starts.push(cursor);
            cursor += c.size + interval;
        });
        return {
            lengths: lengths,
            starts: starts,
            interval: interval,
            totalBases: lengths.length ? cursor - interval : 0
        };
    }

    /* Drop chromosomes that have neither markers nor the gene position. */
    function filterEmptyChromosomes(layout, markers, data) {
        var used = {};
        markers.forEach(function (m) { used[String(m.chr)] = true; });
        if (data.gene_position && data.gene_position.chr !== undefined) {
            used[String(data.gene_position.chr)] = true;
        }
        var kept = [];
        layout.lengths.forEach(function (c, i) {
            if (used[c.chr]) kept.push({ c: c, start: layout.starts[i] });
        });
        var lengths = kept.map(function (k) { return k.c; });
        var starts = [];
        var cursor = 0;
        lengths.forEach(function (c) {
            starts.push(cursor);
            cursor += c.size + layout.interval;
        });
        return {
            lengths: lengths,
            starts: starts,
            interval: layout.interval,
            totalBases: lengths.length ? cursor - layout.interval : 0
        };
    }

    function chrIndex(layout, name) {
        name = String(name);
        for (var i = 0; i < layout.lengths.length; i++) {
            if (layout.lengths[i].chr === name) return i;
        }
        return -1;
    }

    function pointColor(data, layout, marker) {
        var idx = chrIndex(layout, marker.chr);
        if (data.color_scheme === "single") {
            return data.manhattan_single_color || "#D9D9D9";
        }
        if (data.color_scheme === "varied") {
            return DISTINCT[(idx < 0 ? 0 : idx) % DISTINCT.length];
        }
        return (idx % 2 === 1) ? COLORS.red : COLORS.blue;
    }

    function yDomain(data, markers) {
        if (data.lrsMax && data.lrsMax > 0) return [0, data.lrsMax];
        var max = 0;
        markers.forEach(function (m) {
            var s = markerScore(m, data);
            if (s > max) max = s;
        });
        if (max === 0) max = 1;
        max = max * 1.05;
        /* Mirror drawQTL: LRS_LOD_Max = max(significant, LRS_LOD_Max) so the
           significant/suggestive lines stay inside the plot when they exceed
           the highest marker score (the significant line then defines the top
           of the y axis, as in the original figure). */
        var sig = toNum(data.significant);
        if (sig !== null && sig > max) max = sig;
        var sugg = toNum(data.suggestive);
        if (sugg !== null && sugg > max) max = sugg;
        return [0, max];
    }

    /* "Nice" tick step for a range (1, 2, 5 x 10^n) aiming for ~8 ticks. */
    function niceStep(range) {
        if (range <= 0) return 1;
        var raw = range / 8;
        var mag = Math.pow(10, Math.floor(Math.log(raw) / Math.LN10));
        var norm = raw / mag;
        var step = norm < 1.5 ? 1 : (norm < 3 ? 2 : (norm < 7 ? 5 : 10));
        return step * mag;
    }

    /* ------------------------------ tooltip ------------------------------ */

    function tip() {
        if (!tipEl) {
            tipEl = d3.select("body").append("div")
                .attr("class", "mapping-tip")
                .style("position", "absolute")
                .style("display", "none")
                .style("pointer-events", "none")
                .style("background", "rgba(30,30,30,0.85)")
                .style("color", "#fff")
                .style("padding", "6px 9px")
                .style("border-radius", "4px")
                .style("font-size", "12px")
                .style("font-family", FONT)
                .style("line-height", "1.35")
                .style("z-index", 10000);
        }
        return tipEl;
    }

    function markerPosLabel(marker) {
        if (marker.Mb !== undefined && marker.Mb !== null) {
            return "Chr" + marker.chr + ": " + (+marker.Mb).toFixed(3) + " Mb";
        }
        return "Chr" + marker.chr + ": " + (+marker.cM).toFixed(2) + " cM";
    }

    function showTip(marker, data) {
        var t = tip();
        t.html(
            "<b>" + (marker.name || "") + "</b><br/>" +
            markerPosLabel(marker) + "<br/>" +
            (data.LRS_LOD || "LRS") + ": " + markerScore(marker, data).toFixed(2)
        );
        t.style("display", "block");
        repositionTip();
    }

    function repositionTip() {
        if (!tipEl) return;
        var node = tipEl.node();
        var w = node.offsetWidth || 150;
        var x = (d3.event && d3.event.pageX != null)
            ? d3.event.pageX - w / 2
            : 0;
        var y = (d3.event && d3.event.pageY != null)
            ? d3.event.pageY - 30
            : 0;
        tipEl.style("left", x + "px").style("top", y + "px");
    }

    function hideTip() {
        if (tipEl) tipEl.style("display", "none");
    }

    /* ------------------------------ rendering ---------------------------- */

    function xForMarker(focusLayout, marker) {
        var bases = markerBases(marker);
        if (focusLayout.lengths.length === 1) return bases;
        var idx = chrIndex(focusLayout, marker.chr);
        return focusLayout.starts[idx] + bases;
    }

    /* Metadata text block in the top-left (mirrors the PIL legend info). */
    function drawMetadata(svg, data, left) {
        var lines = data.metadata_lines || [];
        if (!lines.length) return;
        var block = svg.append("g").attr("class", "mapping-metadata");
        lines.forEach(function (line, i) {
            block.append("text")
                .attr("x", left + 4)
                .attr("y", 20 + i * 16)
                .attr("font-family", FONT)
                .attr("font-size", "14px")
                .attr("fill", COLORS.text)
                .text(line);
        });
    }

    /* Purple triangle at the bottom marking the trait's gene location. */
    function drawGeneMarker(g, data, layout, focusChr, xScale, chartH) {
        if (data.plotScale !== "physic") return;
        var gp = data.gene_position;
        if (!gp || gp.mb === undefined || gp.mb === null) return;
        var idx = chrIndex(layout, gp.chr);
        if (idx < 0) return;
        if (focusChr !== null && idx !== focusChr) return;
        var bases = toNum(gp.mb) * 1e6;
        var x = (focusChr !== null)
            ? xScale(bases)
            : xScale(layout.starts[idx] + bases);
        g.append("path")
            .attr("d", "M" + x + "," + chartH +
                       "L" + (x - 7) + "," + (chartH + 14) +
                       "L" + (x + 7) + "," + (chartH + 14) + "Z")
            .attr("fill", COLORS.geneMarker)
            .attr("stroke", "#000")
            .attr("stroke-width", 1)
            .style("cursor", "pointer")
            .on("mouseover", function () {
                var t = tip();
                t.html("<b>Gene location</b><br/>Chr" + gp.chr + ": " +
                       (+gp.mb).toFixed(3) + " Mb");
                t.style("display", "block");
                repositionTip();
            })
            .on("mouseout", hideTip);
    }

    /* Additive-effect lines (green = positive, orange = negative), mirroring
       drawQTL: value 0 sits at the plot baseline (bottom), additiveMax at the
       vertical middle; negative values are reflected above the baseline. */
    function additiveY(v, additiveMax, chartH) {
        return chartH - (v * (chartH / 2)) / additiveMax;
    }

    function drawAdditiveSegment(g, x0, y0, v0, x1, y1, v1, chartH) {
        var plus = COLORS.additivePositive;
        var minus = COLORS.additiveNegative;
        var mirror = function (y) { return 2 * chartH - y; };
        var seg = function (xa, ya, xb, yb, color) {
            g.append("line")
                .attr("x1", xa).attr("y1", ya)
                .attr("x2", xb).attr("y2", yb)
                .attr("stroke", color)
                .attr("stroke-width", 1);
        };
        if (v0 >= 0 && v1 >= 0) {
            seg(x0, y0, x1, y1, plus);
        } else if (v0 < 0 && v1 < 0) {
            seg(x0, mirror(y0), x1, mirror(y1), minus);
        } else {
            var t = -v0 / (v1 - v0);
            var xm = x0 + t * (x1 - x0);
            if (v0 >= 0) {
                seg(x0, y0, xm, chartH, plus);
                seg(xm, chartH, x1, mirror(y1), minus);
            } else {
                seg(x0, mirror(y0), xm, chartH, minus);
                seg(xm, chartH, x1, y1, plus);
            }
        }
    }

    function drawAdditiveLines(g, markers, focusLayout, xScale, additiveMax, chartH) {
        var byChr = {};
        markers.forEach(function (m) {
            if (m.additive === undefined || m.additive === null || m.additive === "") {
                return;
            }
            var k = String(m.chr);
            (byChr[k] = byChr[k] || []).push(m);
        });
        Object.keys(byChr).forEach(function (k) {
            var pts = byChr[k];
            for (var i = 1; i < pts.length; i++) {
                var a = pts[i - 1], b = pts[i];
                var v0 = parseFloat(a.additive), v1 = parseFloat(b.additive);
                if (isNaN(v0) || isNaN(v1)) continue;
                drawAdditiveSegment(
                    g,
                    xScale(xForMarker(focusLayout, a)), additiveY(v0, additiveMax, chartH), v0,
                    xScale(xForMarker(focusLayout, b)), additiveY(v1, additiveMax, chartH), v1,
                    chartH);
            }
        });
    }

    /* Green right-hand axis for the additive-effect scale (0..additiveMax). */
    function drawAdditiveAxis(g, chartW, additiveMax, chartH) {
        var scale = d3.scale.linear()
            .domain([0, additiveMax])
            .range([chartH, chartH / 2]);
        var axis = d3.svg.axis().scale(scale).orient("right")
            .ticks(5).tickSize(-6, 0).tickPadding(6)
            .tickFormat(d3.format(".3f"));
        var ax = g.append("g").attr("class", "additive axis")
            .attr("transform", "translate(" + chartW + ",0)")
            .call(axis);
        ax.selectAll("path,line")
            .attr("stroke", COLORS.additivePositive)
            .style("stroke-width", 1).style("fill", "none");
        ax.selectAll("text")
            .attr("fill", COLORS.additivePositive)
            .attr("font-family", FONT)
            .attr("font-size", "15px");
    }

    function render(containerId, data) {
        var container = document.getElementById(containerId);
        if (!container) return;

        container.innerHTML = "";

        var width = Math.min(
            Math.max(container.clientWidth || DEFAULT_WIDTH, 600), MAX_WIDTH);
        var height = PLOT_HEIGHT + MARGIN.top + MARGIN.bottom;
        var chartW = width - MARGIN.left - MARGIN.right;
        var chartH = height - MARGIN.top - MARGIN.bottom;

        var fullLayout = layoutChromosomes(data);
        var markers = (data.markers || []).filter(function (m) {
            return chrIndex(fullLayout, m.chr) >= 0 && markerBases(m) !== null;
        });
        var layout = filterEmptyChromosomes(fullLayout, markers, data);

        var focus = (state.focusChr !== null &&
                     state.focusChr >= 0 &&
                     state.focusChr < layout.lengths.length)
            ? state.focusChr
            : null;

        var focusLayout, focusMarkers;
        if (focus !== null) {
            var fl = layout.lengths[focus];
            focusLayout = {
                lengths: [fl],
                starts: [0],
                interval: 0,
                totalBases: fl.size
            };
            focusMarkers = markers.filter(function (m) {
                return chrIndex(layout, m.chr) === focus;
            });
        } else {
            focusLayout = layout;
            focusMarkers = markers;
        }

        var xScale = d3.scale.linear()
            .domain([0, focusLayout.totalBases])
            .range([0, chartW]);
        var yMax = yDomain(data, focusMarkers)[1];
        var yScale = d3.scale.linear()
            .domain([0, yMax])
            .range([chartH, TOP_LABEL_INSET]);

        var svg = d3.select(container).append("svg")
            .attr("width", width)
            .attr("height", height)
            .attr("class", "mapping-figure")
            .on("mousemove", repositionTip);

        var g = svg.append("g")
            .attr("transform", "translate(" + MARGIN.left + "," + MARGIN.top + ")");

        /* chromosome bands + labels */
        focusLayout.lengths.forEach(function (c, i) {
            var x0 = xScale(focusLayout.starts[i]);
            var x1 = xScale(focusLayout.starts[i] + c.size);
            g.append("rect")
                .attr("x", x0).attr("y", 0)
                .attr("width", Math.max(1, x1 - x0))
                .attr("height", chartH)
                .attr("fill", i % 2 === 0 ? COLORS.backLight : COLORS.backDark)
                .attr("stroke", COLORS.chrStroke)
                .style("cursor", focus === null ? "pointer" : "default")
                .on("click", function () {
                    if (focus === null) {
                        state.focusChr = i;
                        render(containerId, data);
                    }
                });
            /* chromosome label at the TOP of the band (like the original:
               regular weight, sitting just inside the top of the plot) */
            g.append("text")
                .attr("x", (x0 + x1) / 2)
                .attr("y", 24)
                .attr("text-anchor", "middle")
                .attr("font-family", FONT)
                .attr("font-size", "22px")
                .attr("fill", COLORS.text)
                .style("cursor", focus === null ? "pointer" : "default")
                .text(c.chr)
                .on("click", function () {
                    if (focus === null) {
                        state.focusChr = i;
                        render(containerId, data);
                    }
                });
        });

        /* Mb tick marks + labels (physic scale, mirrors PIL) */
        if (data.plotScale === "physic") {
            if (focus === null) {
                /* whole-genome: fixed spacing per chromosome */
                focusLayout.lengths.forEach(function (c, i) {
                    var lenMb = c.size / 1e6;
                    var distScale = lenMb > 75 ? 25 : (lenMb > 30 ? 10 : 5);
                    var j = 0;
                    for (var tick = distScale; tick < Math.ceil(lenMb); tick += distScale) {
                        var x = xScale(focusLayout.starts[i] + tick * 1e6);
                        g.append("line")
                            .attr("x1", x).attr("y1", chartH)
                            .attr("x2", x).attr("y2", chartH + 8)
                            .attr("stroke", "#000")
                            .attr("stroke-width", 1);
                        if (j % 2 === 0) {
                            g.append("text")
                                .attr("transform", "translate(" + x + "," + (chartH + 26) + ") rotate(-90)")
                                .attr("text-anchor", "middle")
                                .attr("font-family", FONT)
                                .attr("font-size", "14px")
                                .attr("fill", "#000")
                                .text(String(tick));
                        }
                        j += 1;
                    }
                });
            } else {
                /* single chromosome: nice continuous scale, major + minor ticks */
                var lenMb = focusLayout.lengths[0].size / 1e6;
                var step = niceStep(lenMb);
                var minorStep = step / 5;
                var vi = 0;
                for (var v = 0; v <= lenMb + 1e-9; vi += 1, v = vi * minorStep) {
                    var nearMajor = Math.abs(v - Math.round(v / step) * step) < 1e-6;
                    var x = xScale(v * 1e6);
                    g.append("line")
                        .attr("x1", x).attr("y1", chartH)
                        .attr("x2", x).attr("y2", chartH + (nearMajor ? 12 : 6))
                        .attr("stroke", "#000")
                        .attr("stroke-width", nearMajor ? 2 : 1);
                    if (nearMajor && v > 0) {
                        g.append("text")
                            .attr("transform", "translate(" + x + "," + (chartH + 26) + ") rotate(-90)")
                            .attr("text-anchor", "middle")
                            .attr("font-family", FONT)
                            .attr("font-size", "14px")
                            .attr("fill", "#000")
                            .text(String(Math.round(v)));
                    }
                }
            }
            g.append("text")
                .attr("x", chartW / 2)
                .attr("y", chartH + 82)
                .attr("text-anchor", "middle")
                .attr("font-family", FONT)
                .attr("font-size", "20px")
                .attr("fill", COLORS.text)
                .text("Megabases");
        }

        /* suggestive / significant threshold lines */
        var sugg = toNum(data.suggestive);
        var sig = toNum(data.significant);
        if (sugg !== null) {
            g.append("line")
                .attr("x1", 0).attr("x2", chartW)
                .attr("y1", yScale(sugg)).attr("y2", yScale(sugg))
                .attr("stroke", COLORS.suggestive)
                .attr("stroke-width", 3);
        }
        if (sig !== null) {
            g.append("line")
                .attr("x1", 0).attr("x2", chartW)
                .attr("y1", yScale(sig)).attr("y2", yScale(sig))
                .attr("stroke", COLORS.significant)
                .attr("stroke-width", 3);
        }

        if (data.manhattan_plot) {
            /* scatter points (larger when focused on a single chromosome) */
            var dotR = focus === null ? 2 : 3.5;
            var pts = g.append("g").attr("class", "points");
            pts.selectAll("circle").data(focusMarkers).enter().append("circle")
                .attr("r", dotR)
                .attr("cx", function (m) { return xScale(xForMarker(focusLayout, m)); })
                .attr("cy", function (m) { return yScale(markerScore(m, data)); })
                .attr("fill", function (m) { return pointColor(data, layout, m); })
                .style("opacity", 0.85)
                .on("mouseover", function (m) { showTip(m, data); })
                .on("mouseout", hideTip);

            /* peak markers (>= significant threshold) as purple triangles */
            if (sig !== null) {
                var halfW = focus === null ? 4.5 : 7;
                var triH = focus === null ? 7 : 10;
                var peaks = focusMarkers.filter(function (m) {
                    return markerScore(m, data) >= sig;
                });
                pts.selectAll("path.peak").data(peaks).enter().append("path")
                    .attr("d", function (m) {
                        var x = xScale(xForMarker(focusLayout, m));
                        var y = yScale(markerScore(m, data));
                        return "M" + x + "," + (y - triH) +
                               "L" + (x - halfW) + "," + y +
                               "L" + (x + halfW) + "," + y + "Z";
                    })
                    .attr("fill", COLORS.peak)
                    .attr("stroke", COLORS.peak)
                    .style("cursor", "pointer")
                    .on("mouseover", function (m) { showTip(m, data); })
                    .on("mouseout", hideTip);
            }
        } else {
            /* connected LRS line, one path per chromosome. A single colour
               across the whole figure (blue, the PIL LRS_COLOR) so it stays
               distinguishable from the additive-effect lines, and thicker to
               match the original plot. */
            var lineColor = COLORS.axis;
            var lineWidth = focus === null ? 3 : 4;
            var lineFn = d3.svg.line()
                .x(function (m) { return xScale(xForMarker(focusLayout, m)); })
                .y(function (m) { return yScale(markerScore(m, data)); });
            var byChr = {};
            focusMarkers.forEach(function (m) {
                var k = String(m.chr);
                (byChr[k] = byChr[k] || []).push(m);
            });
            Object.keys(byChr).forEach(function (k) {
                g.append("path")
                    .attr("d", lineFn(byChr[k]))
                    .attr("fill", "none")
                    .attr("stroke", lineColor)
                    .attr("stroke-width", lineWidth);
            });
        }

        /* additive-effect lines + green right-hand axis */
        var addChecked = data.additive_checked === true;
        var hasAdditive = focusMarkers.some(function (m) {
            return m.additive !== undefined && m.additive !== null &&
                m.additive !== "";
        });
        if (addChecked && hasAdditive) {
            var additiveMax = 0;
            focusMarkers.forEach(function (m) {
                var v = parseFloat(m.additive);
                if (!isNaN(v) && Math.abs(v) > additiveMax) {
                    additiveMax = Math.abs(v);
                }
            });
            if (additiveMax === 0) additiveMax = 0.000001;
            drawAdditiveLines(g, focusMarkers, focusLayout, xScale,
                              additiveMax, chartH);
            drawAdditiveAxis(g, chartW, additiveMax, chartH);
        }

        /* gene location marker (purple triangle at the bottom) */
        drawGeneMarker(g, data, layout, focus, xScale, chartH);

        /* y axis (thin line, ticks pointing inward) */
        var yAxis = d3.svg.axis().scale(yScale).orient("left")
            .ticks(5).tickSize(-6, 0).tickPadding(6);
        var yAxisG = g.append("g").attr("class", "y axis").call(yAxis);
        yAxisG.selectAll("path")
            .style("stroke-width", 1).style("fill", "none");
        yAxisG.selectAll("line").style("stroke-width", 1);
        yAxisG.selectAll("text")
            .attr("fill", COLORS.axis)
            .attr("font-family", FONT)
            .attr("font-size", "15px");

        g.append("text")
            .attr("transform", "rotate(-90)")
            .attr("y", -MARGIN.left + 18)
            .attr("x", -chartH / 2)
            .attr("text-anchor", "middle")
            .attr("font-family", FONT)
            .attr("font-size", "24px")
            .attr("fill", COLORS.text)
            .text(data.LRS_LOD || "LRS");

        /* toolbar / back-to-full-view (top-right, clear of the metadata) */
        if (focus !== null) {
            svg.append("text")
                .attr("text-anchor", "end")
                .attr("x", width - 10)
                .attr("y", 16)
                .attr("font-family", FONT)
                .attr("font-size", "15px")
                .attr("fill", COLORS.link)
                .style("cursor", "pointer")
                .text("\u2190 Back to all chromosomes (focused: Chr " +
                      layout.lengths[focus].chr + ")")
                .on("click", function () {
                    state.focusChr = null;
                    render(containerId, data);
                });
        }

        /* metadata block (top-left) */
        drawMetadata(svg, data, MARGIN.left);
    }

    /* ------------------------------ public API --------------------------- */

    return {
        render: render,
        reset: function (containerId, data) {
            state.focusChr = null;
            render(containerId, data);
        }
    };
})();
