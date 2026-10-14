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
    var PLOT_HEIGHT = 390;           // mirrors the original plot area (600-110-100)

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

    var state = {
        focusChr: null,
        /* client-side track toggles (Gene / Homology / Haplotype) */
        tracks: { gene: false, homology: false, haplotype: false },
        tracksInitialized: false,
        /* manual Mb-range zoom applied to the focused chromosome */
        range: null,
        layout: null,            // most recent layout (for focus-by-name)
        viewInitialized: false,  // first-render carry-over from original view
        initialFocusChrName: null,
        /* on-demand track data cache + in-flight markers, keyed by chr/range */
        trackData: {},
        trackLoading: {},
        containerId: null,
        data: null,
        /* whether the payload's coordinates (and chromosome lengths) are in
           cM rather than Mb - set per render from usesCmAxis() */
        cmAxis: false,
        /* chromosome name -> the position its band starts at (0 for Mb, and
           for cM when the map is numbered per chromosome) - set per render by
           layoutChromosomes() */
        chrOrigins: null,
        /* signature of the last view we announced, so the page is only told
           about a change when the focused chromosome/range actually changes */
        lastViewKey: null
    };

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

    /* Which marker field carries the coordinate the figure plots against.
       The server says so directly: run_mapping built the chromosome lengths
       from the same field and reports it as chr_lengths_in_cm. Deriving it
       from the mapping method here instead meant the figure and the domain
       could disagree - rqtl on a genetic scale plots cM (as the results export
       and the table header already do) but was drawn against Mb lengths. */
    function usesCmAxis(data) {
        return data.chr_lengths_in_cm === true;
    }

    /* Marker position in bases, on whichever of Mb/cM the axis is built from
       (see usesCmAxis). Set once per render in state.cmAxis, so the plotting
       code does not have to thread the payload through every call.

       The value returned is the marker's position WITHIN its chromosome, which
       is what the layout needs: chromosome bands are laid out end to end, so
       xForMarker() adds the band's start. Mb is already measured from the start
       of its chromosome, but a genetic map can be numbered from the start of
       the first chromosome, so the server reports the offset the band leaves
       for as chr_lengths[].start (see run_mapping.get_chr_lengths). Without
       subtracting it, every chromosome's markers would be drawn at their
       genome-wide distance from chromosome 1 and pile up beyond the layout. */
    function markerBases(marker) {
        var v = state.cmAxis ? toNum(marker.cM) : toNum(marker.Mb);
        if (v === null) return null;
        var origin = 0;
        if (state.cmAxis && state.chrOrigins) {
            origin = toNum(state.chrOrigins[String(marker.chr)]) || 0;
        }
        return (v - origin) * 1e6;
    }

    /* Build chromosome layout from chr_lengths (numeric first, then X/Y/...). */
    function layoutChromosomes(data) {
        var origins = {};
        var lengths = (data.chr_lengths || []).map(function (c) {
            origins[String(c.chr)] = toNum(c.start) || 0;
            return { chr: String(c.chr), size: toNum(c.size) || 0 };
        }).filter(function (c) { return c.size > 0; });
        state.chrOrigins = origins;

        function sortKey(c) {
            var n = parseInt(c.chr, 10);
            return isNaN(n) ? [1, c.chr] : [0, n];
        }
        lengths.sort(function (a, b) {
            var ka = sortKey(a), kb = sortKey(b);
            if (ka[0] !== kb[0]) return ka[0] - kb[0];
            return ka[1] < kb[1] ? -1 : (ka[1] > kb[1] ? 1 : 0);
        });

        /* Gap between chromosome bands. Proportional to the layout - which is
           what the physical scale already used - rather than a fixed 5e6: on a
           genetic scale the coordinates are of the order of 1e6 per
           chromosome, so a fixed physical gap swamped them and every band
           collapsed to a hairline separated by empty space. */
        var total = lengths.reduce(function (s, c) { return s + c.size; }, 0);
        var interval = lengths.length ? total / (lengths.length * 12) : 0;

        var startsInfo = computeStarts(lengths, interval);
        return {
            lengths: lengths,
            starts: startsInfo.starts,
            interval: interval,
            totalBases: startsInfo.totalBases
        };
    }

    /* Per-chromosome start offsets (with the inter-chromosome gap) from a
       list of lengths. Shared by layoutChromosomes and filterEmptyChromosomes. */
    function computeStarts(lengths, interval) {
        var starts = [];
        var cursor = 0;
        lengths.forEach(function (c) {
            starts.push(cursor);
            cursor += c.size + interval;
        });
        return {
            starts: starts,
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
        var startsInfo = computeStarts(lengths, layout.interval);
        return {
            lengths: lengths,
            starts: startsInfo.starts,
            interval: layout.interval,
            totalBases: startsInfo.totalBases
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

    /* Decimals needed to tell two values a tick step apart from each other:
       a step of 0.1 wants one decimal, 0.02 wants two, 5 wants none. Capped
       at 6, which is base resolution on an Mb axis, so a step finer than
       that still gets as much precision as is meaningful. */
    function stepDecimals(step) {
        if (!(step > 0)) return 0;
        var decimals = Math.ceil(-Math.log(step) / Math.LN10);
        if (!(decimals > 0)) decimals = 0;
        if (decimals > 6) decimals = 6;
        return decimals;
    }

    /* Tick labels for a linear scale, formatted the way the original PIL
       plots do: whole numbers while every tick is a whole number, otherwise
       decimals. The number of decimals follows the tick step, so an axis
       spanning a very small range still tells its ticks apart (a single
       decimal would otherwise print, say, "0.0" for every one of them). */
    function tickNumberFormat(scale, count) {
        var ticks = scale.ticks(count);
        var wholeNumbers = true;
        ticks.forEach(function (v) {
            if (v !== Math.round(v)) wholeNumbers = false;
        });
        if (wholeNumbers) {
            return function (v) { return String(Math.round(v)); };
        }
        var step = ticks.length > 1
            ? Math.abs(ticks[1] - ticks[0])
            : (Math.abs(ticks[0]) || 1);
        /* at least one decimal: this branch is only reached when the ticks
           are not whole numbers */
        return d3.format("." + Math.max(1, stepDecimals(step)) + "f");
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

    /* Position of a marker for the tooltip, in the units the axis uses.
       Only plotted markers get a tooltip, and those always carry the axis
       coordinate (markerBases() drops the others), so there is no need to
       fall back to the other field here. */
    function markerPosLabel(marker, data) {
        if (usesCmAxis(data)) {
            return "Chr" + marker.chr + ": " + (+marker.cM).toFixed(2) + " cM";
        }
        return "Chr" + marker.chr + ": " + (+marker.Mb).toFixed(3) + " Mb";
    }

    function showTip(marker, data) {
        var t = tip();
        var link = markerTraitLink(marker, data);
        t.html(
            "<b>" + (marker.name || "") + "</b><br/>" +
            markerPosLabel(marker, data) + "<br/>" +
            (data.LRS_LOD || "LRS") + ": " + markerScore(marker, data).toFixed(2) +
            (link ? "<br/><span style='color:#9fb6ff'>Click to view trait page</span>" : "")
        );
        t.style("display", "block");
        repositionTip();
    }

    /* Trait-page link for a marker, or null when markers aren't databased.
       Mirrors the results-table links (only shown when geno_db_exists). */
    function markerTraitLink(marker, data) {
        if (!data || data.geno_db_exists !== true || !data.marker_dataset) {
            return null;
        }
        var name = marker && marker.name;
        if (!name) return null;
        return "/show_trait?trait_id=" + encodeURIComponent(name) +
            "&dataset=" + encodeURIComponent(data.marker_dataset);
    }

    /* Open the marker's trait page in a new tab (like the table's target=_blank). */
    function openMarkerTrait(marker, data) {
        var link = markerTraitLink(marker, data);
        if (link) window.open(link, "_blank");
    }

    /* Shared hover/click behaviour for marker elements (points, peaks, and
       the invisible line-mode hover circles): pointer cursor + tooltip when a
       trait page link exists, and open that link on click. */
    function attachMarkerInteractions(sel, data) {
        return sel
            .style("cursor", function (m) {
                return markerTraitLink(m, data) ? "pointer" : "default";
            })
            .on("mouseover", function (m) { showTip(m, data); })
            .on("mouseout", hideTip)
            .on("click", function (m) { openMarkerTrait(m, data); });
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

    /* Simple tooltip for non-marker elements (e.g. threshold lines). */
    function showLineTip(title, sub) {
        var t = tip();
        t.html("<b>" + title + "</b>" + (sub ? "<br/>" + sub : ""));
        t.style("display", "block");
        repositionTip();
    }

    /* Threshold line: the visible line plus a wider transparent hit-area that
       shows a labelled tooltip on hover (mirrors the PIL threshold labels). */
    function drawThresholdLine(g, chartW, yScale, value, color, label, data) {
        var y = yScale(value);
        var yLabel = value.toFixed(2);
        g.append("line")
            .attr("x1", 0).attr("x2", chartW)
            .attr("y1", y).attr("y2", y)
            .attr("stroke", color)
            .attr("stroke-width", 3);
        g.append("line")
            .attr("x1", 0).attr("x2", chartW)
            .attr("y1", y).attr("y2", y)
            .attr("stroke", "transparent")
            .attr("stroke-width", 16)
            .style("cursor", "pointer")
            .on("mouseover", function () {
                showLineTip(label + " threshold",
                            (data.LRS_LOD || "LRS") + ": " + yLabel);
            })
            .on("mouseout", hideTip);
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
       vertical middle of the plot area (AdditiveHeightThresh = drawAreaHeight/2);
       negative values are reflected above the baseline. */
    function additiveY(v, additiveMax, chartH, topInset) {
        var plotH = chartH - topInset;
        return chartH - (v * (plotH / 2)) / additiveMax;
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

    function drawAdditiveLines(g, markers, focusLayout, xScale, additiveMax,
                               chartH, topInset) {
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
                    xScale(xForMarker(focusLayout, a)),
                    additiveY(v0, additiveMax, chartH, topInset), v0,
                    xScale(xForMarker(focusLayout, b)),
                    additiveY(v1, additiveMax, chartH, topInset), v1,
                    chartH);
            }
        });
    }

    /* Green right-hand axis for the additive-effect scale (0..additiveMax). */
    function drawAdditiveAxis(g, chartW, additiveMax, chartH, topInset) {
        var plotH = chartH - topInset;
        var scale = d3.scale.linear()
            .domain([0, additiveMax])
            .range([chartH, chartH - plotH / 2]);
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

    /* ---- browser-link bands (PhenoGen / UCSC / Ensembl) ----
       Shown only in the single-chromosome (focused) view. Each band spans the
       plot width and is divided into clickable segments; clicking a segment
       links to the proportional genomic range underneath it (mirroring the
       original clickable-region bands). */
    var BAND_H = 18;
    var BAND_PAD = 4;

    function browserBandURL(data, band, chr, calBase, startB, endB) {
        var flank = Math.min((endB - startB) / 2, 5e6);
        var s = Math.max(0, Math.round(calBase - flank));
        var e = Math.round(calBase + flank);
        var ucsc = data.ucsc_db || "";
        var genomeVer = ucsc || (data.species === "rat" ? "rn6" : "mm10");
        var ensSpecies = data.species === "rat"
            ? "Rattus_norvegicus" : "Mus_musculus";
        if (band === "phenogen") {
            return "https://phenogen.org/gene.jsp?speciesCB=Mm&auto=Y&" +
                "geneTxt=chr" + chr + ":" + s + "-" + e + "&genomeVer=" + genomeVer;
        }
        if (band === "ucsc") {
            return "http://genome.ucsc.edu/cgi-bin/hgTracks?db=" + ucsc +
                "&position=chr" + chr + ":" + s + "-" + e;
        }
        return "http://www.ensembl.org/" + ensSpecies +
            "/contigview?highlight=&chr=" + chr + "&vc_start=" + s +
            "&vc_end=" + e + "&x=35&y=12";
    }

    function drawBrowserBands(g, data, layout, focus, chartW, startB, endB) {
        if (focus === null) return;
        var fl = layout.lengths[focus];
        var chr = fl.chr;
        var bands = [
            { key: "phenogen", fill: "#A2FB94", text: "#1FD504",
              divider: "#FFFFFF",
              msg: "Click to view the corresponding section of the genome in " +
                   "PhenoGen" },
            { key: "ucsc", fill: "#DDDDEE", text: "#333366",
              divider: "#FFFFFF",
              msg: "Click to view the corresponding section of the genome in " +
                   "the UCSC Genome Browser" },
            { key: "ensembl", fill: "#EEEEDD", text: "#555500",
              divider: "#FFFFFF",
              msg: "Click to view the corresponding section of the genome in " +
                   "the Ensembl Genome Browser" }
        ];
        /* The number of on-screen intervals is fixed by the plot width (mirrors
           the original MAX_CLICKABLE_REGION_DIVISIONS = 100). When pan/zoom is
           added, startB/endB just become the currently visible window and every
           segment (plus its divider) recomputes its proportional genomic range
           automatically, so this code needs no structural changes for zoom. */
        var nSeg = Math.max(20, Math.min(100, Math.round(chartW / 10)));
        var segW = chartW / nSeg;
        /* wrapper group so SVG export can strip the bands from a "map only"
           export (class mapping-browser-bands) */
        var bandsG = g.append("g").attr("class", "mapping-browser-bands");
        bands.forEach(function (band, i) {
            var yTop = BAND_PAD + i * (BAND_H + BAND_PAD);
            bandsG.append("rect")
                .attr("x", 0).attr("y", yTop)
                .attr("width", chartW).attr("height", BAND_H)
                .attr("fill", band.fill)
                .attr("stroke", "#FFFFFF");
            /* clickable segments -> proportional genomic range */
            for (var s = 0; s < nSeg; s++) {
                var x0 = segW * s;
                var x1 = segW * (s + 1);
                var frac = (x0 + x1) / 2 / chartW;
                var calBase = startB + (endB - startB) * frac;
                bandsG.append("a")
                    .attr("xlink:href", browserBandURL(
                        data, band.key, chr, calBase, startB, endB))
                    .attr("target", "_blank")
                    .append("rect")
                    .attr("x", x0).attr("y", yTop)
                    .attr("width", Math.max(1, x1 - x0))
                    .attr("height", BAND_H)
                    .attr("fill", "transparent")
                    .style("cursor", "pointer");
            }
            /* divider lines marking each interval boundary. Drawn on top of the
               link segments so they are visible, but pointer-events:none so they
               never intercept clicks meant for the links underneath. */
            for (var d = 0; d <= nSeg; d++) {
                var dx = segW * d;
                bandsG.append("line")
                    .attr("x1", dx).attr("y1", yTop)
                    .attr("x2", dx).attr("y2", yTop + BAND_H)
                    .attr("stroke", band.divider)
                    .attr("stroke-width", 1)
                    .style("pointer-events", "none");
            }
            /* band label drawn last so it sits on a layer above the dividers */
            bandsG.append("text")
                .attr("x", 6).attr("y", yTop + BAND_H / 2 + 4)
                .attr("font-family", FONT)
                .attr("font-size", "11px")
                .attr("fill", band.text)
                .text(band.msg);
        });
    }

    /* ---- gene / homology / haplotype tracks ----
       These mirror the original PIL Gene Band, Homology Band and Haplotype
       Band. They are shown only in the focused (single-chromosome) view, and
       their data is fetched on demand from /mapping/track_data for the focused
       chromosome. The drawing functions take the visible range through xScale,
       so future pan/zoom just refetches with a new start/end window. */

    var EACH_GENE_HEIGHT = 6;    // pixel height of a gene/homology row
    var NUM_GENE_ROWS = 10;      // genes/homology wrap onto this many rows
    var GENE_TRACK_H = NUM_GENE_ROWS * EACH_GENE_HEIGHT;
    var HAPLOTYPE_ROW_H = 2 * EACH_GENE_HEIGHT;    // 12 px per strain row
    var HAPLOTYPE_LINE_W = EACH_GENE_HEIGHT + 2;   // 8 px line thickness
    var DRAW_DETAIL_MB = 4;      // zoom level at which exon detail is drawn
    var HAPLOTYPE_COLORS = {
        pos: "#0000FF",          // BLUE
        neg: "#FF0000",          // RED
        het: "#FFA500",          // ORANGE
        rec: "#A9A9A9"           // DARKGRAY
    };
    var TRACK_HEADER_H = 16;     // collapse/expand header height per track
    var SNP_MAX_H = 18;          // max SNP-density bar height (SNP_HEIGHT_MODIFIER)

    /* Strand chevrons along a gene/homology segment. The apex of each chevron
       sits at `ax`; the base is pushed left/right by the strand direction. */
    function drawStrandArrows(link, x0, x1, y, midY, dir, color, divisor) {
        var step = Math.max(6, Math.min(14, (x1 - x0) / divisor));
        for (var ax = x0 + step; ax < x1; ax += step) {
            var baseX = dir > 0 ? ax - 3 : ax + 3;
            link.append("line")
                .attr("x1", baseX).attr("y1", y)
                .attr("x2", ax).attr("y2", midY)
                .attr("stroke", color).attr("stroke-width", 1)
                .style("cursor", "pointer");
            link.append("line")
                .attr("x1", baseX).attr("y1", y + EACH_GENE_HEIGHT)
                .attr("x2", ax).attr("y2", midY)
                .attr("stroke", color).attr("stroke-width", 1)
                .style("cursor", "pointer");
        }
    }

    /* Collapsible header band at the top of each track. Clicking it toggles
       the track between expanded (content shown) and minimized (just this
       band, labelled "Expand ..."). */
    function drawTrackHeader(g, chartW, yTop, label, expanded, toggleFn) {
        var band = g.append("g")
            .attr("class", "mapping-track-header")
            .style("cursor", "pointer")
            .on("click", toggleFn);
        band.append("rect")
            .attr("x", 0).attr("y", yTop)
            .attr("width", chartW).attr("height", TRACK_HEADER_H)
            .attr("fill", "#ECECF2")
            .attr("stroke", "#B8B8C8");
        band.append("text")
            .attr("x", 6).attr("y", yTop + TRACK_HEADER_H - 4)
            .attr("font-family", FONT)
            .attr("font-size", "11px")
            .attr("fill", "#333366")
            .text((expanded ? "\u25BE Minimize " : "\u25B8 Expand ") + label);
    }

    /* One collapsible track: header + (when expanded) its content, returning
       the y position just below it. Each track is wrapped in its own <g> with
       a class + data-expanded attribute so SVG export can include just the
       currently-maximized tracks (stripping the "Expand ..." sections). */
    function drawTrackSection(g, chartW, trackY, label, expanded, toggleFn,
                              drawContent, contentH) {
        var trackG = g.append("g")
            .attr("class", "mapping-track")
            .attr("data-track", label)
            .attr("data-expanded", expanded ? "true" : "false");
        drawTrackHeader(trackG, chartW, trackY, label, expanded, toggleFn);
        trackY += TRACK_HEADER_H;
        if (expanded) {
            drawContent(trackG, trackY);
            trackY += contentH;
        }
        return trackY;
    }

    /* Strains plotted in the haplotype band: those with an expression value
       (not "x"), sorted by value descending (mirrors smd in drawHaplotypeBand). */
    function haplotypePlottedStrains(hp) {
        var rows = [];
        if (!hp) return rows;
        var strains = hp.strains || [];
        var values = hp.values || {};
        for (var i = 0; i < strains.length; i++) {
            var v = values[strains[i]];
            if (v === undefined || v === null) continue;
            var vs = String(v).trim().toLowerCase();
            if (vs === "x" || vs === "" || vs === "none") continue;
            var nv = parseFloat(v);
            if (isNaN(nv)) continue;
            rows.push({ strain: strains[i], value: nv });
        }
        rows.sort(function (a, b) { return b.value - a.value; });
        return rows;
    }

    /* Height (px) reserved for each track in the focused view. Every track
       that has data keeps its collapsible header; an expanded track adds the
       content height on top. */
    /* Whether the tracks whose data is positioned in Mb can be shown at all.
       Gene, homology, haplotype and SNP-density data all arrive from the track
       endpoint in physical coordinates - genes and homology are queried by Mb,
       the haplotype is taken from the genotype dataset's Mb, and the SNP bins
       are Mb bins - so none of them can be placed on a genetic (cM) axis. (The
       payload likewise sends no gene_position on that scale.)

       Keyed on state.cmAxis rather than plotScale: a genetic-scale run whose
       results carry no cM (gemma) is still plotted in Mb, and there these
       tracks are valid. */
    function physicalTracksUsable() {
        return !state.cmAxis;
    }

    function trackHeights(state, focus, trackData) {
        var h = { gene: 0, homology: 0, haplotype: 0 };
        if (focus === null || !trackData) return h;
        /* Leave the tracks out entirely rather than reserve space for one that
           would be drawn in the wrong place. */
        var showMbTracks = physicalTracksUsable();
        var gd = showMbTracks && trackData.genes && trackData.genes.length;
        var hd = showMbTracks && trackData.homology &&
            trackData.homology.length;
        var hap = showMbTracks && trackData.haplotype &&
            trackData.haplotype.markers &&
            trackData.haplotype.markers.length;
        if (gd) h.gene = TRACK_HEADER_H + (state.tracks.gene ? GENE_TRACK_H : 0);
        if (hd) {
            h.homology = TRACK_HEADER_H +
                (state.tracks.homology ? GENE_TRACK_H : 0);
        }
        if (hap) {
            h.haplotype = TRACK_HEADER_H + (state.tracks.haplotype
                ? (haplotypePlottedStrains(trackData.haplotype).length + 8)
                    * HAPLOTYPE_ROW_H
                : 0);
        }
        return h;
    }

    /* clamp an [x0, x1] segment to the visible [0, chartW] range */
    function clampRange(x0, x1, chartW) {
        return [Math.max(0, Math.min(chartW, x0)),
                Math.max(0, Math.min(chartW, x1))];
    }

    /* Cache key for track data: chromosome plus the visible range, so a
       manual range zoom refetches the data for the zoomed window.
       Keyed in bases rather than Mb: rounding the Mb endpoints to three
       decimals merged distinct windows (anything closer together than a
       kilobase produced the same key), so zooming into a neighbouring window
       silently reused the previous one's genes, SNPs and haplotypes. */
    function trackDataKey(chr, rangeB) {
        if (!rangeB) return String(chr) + ":full";
        return String(chr) + ":" +
            Math.round(rangeB.start) + "-" + Math.round(rangeB.end);
    }

    /* fetch the gene/homology/haplotype data for the focused chromosome/range.
       Fetches whenever a track could be shown (mouse/rat) so the collapsible
       track headers are always available - except on a genetic axis, where no
       track in the response has positions that can be placed (see
       physicalTracksUsable), so there is nothing to fetch. */
    function ensureTrackData(containerId, data, focus, layout, rangeB) {
        if (focus === null) return;
        if (!physicalTracksUsable()) return;
        var sp = String(data.species || "").toLowerCase();
        if (sp !== "mouse" && sp !== "rat") return;
        var chr = layout.lengths[focus].chr;
        var chrSize = layout.lengths[focus].size || 0;
        var startMb = 0;
        var endMb = chrSize / 1e6;
        if (rangeB) {
            startMb = rangeB.start / 1e6;
            endMb = rangeB.end / 1e6;
        }
        var key = trackDataKey(chr, rangeB);
        if (state.trackData[key] || state.trackLoading[key]) return;
        state.trackLoading[key] = true;
        var body = {
            dataset: data.dataset_name || "",
            group_name: data.group_name || "",
            species: data.species || "",
            chr: chr,
            start_mb: startMb,
            end_mb: endMb,
            diff_col: data.diff_col || [],
            genofile_string: data.genofile_string || "",
            sample_vals: data.sample_vals || {}
        };
        if (window.$ && window.$.ajax) {
            window.$.ajax({
                url: "/mapping/track_data",
                method: "POST",
                contentType: "application/json",
                data: JSON.stringify(body),
                dataType: "json"
            }).done(function (resp) {
                state.trackData[key] = resp || {};
                state.trackLoading[key] = false;
                render(containerId, data);
            }).fail(function () {
                state.trackData[key] = null;   // allow a later retry
                state.trackLoading[key] = false;
            });
        }
    }

    /* ---- Gene Band (mirrors drawGeneBand) ---- */
    function drawGeneTrack(g, xScale, chartW, yTop, genes, detail) {
        if (!genes || !genes.length) return;
        var ncbi = "http://www.ncbi.nlm.nih.gov/gene?term=";
        genes.forEach(function (gene, i) {
            var row = i % NUM_GENE_ROWS;
            var y = yTop + row * EACH_GENE_HEIGHT;
            var mb0 = toNum(gene.txStart);
            var mb1 = toNum(gene.txEnd);
            if (mb0 === null || mb1 === null) return;
            var r = clampRange(xScale(Math.min(mb0, mb1) * 1e6),
                               xScale(Math.max(mb0, mb1) * 1e6), chartW);
            var x0 = r[0], x1 = r[1];
            var color = gene.color || "#000000";
            var title = "Gene: " + gene.sym + " (" + gene.nm + ")\nFrom " +
                mb0.toFixed(3) + " to " + mb1.toFixed(3) + " Mb (" +
                gene.strand + ")";
            var href = ncbi + gene.sym;
            if (x1 - x0 < 1) {
                /* Too narrow for a visible rectangle at this zoom - draw a 1px
                   vertical mark so the band stays dense (mirrors the PIL,
                   which draws every gene's rectangle at least 1px wide). */
                g.append("a").attr("xlink:href", href).attr("target", "_blank")
                    .append("rect")
                    .attr("x", Math.floor((x0 + x1) / 2)).attr("y", y)
                    .attr("width", 1).attr("height", EACH_GENE_HEIGHT)
                    .attr("fill", color).attr("stroke", color)
                    .style("cursor", "pointer")
                    .append("title").text(title);
                return;
            }
            if (!detail || (x1 - x0 <= 20)) {
                /* simple rectangle (whole-chromosome / too narrow for detail) */
                g.append("a").attr("xlink:href", href).attr("target", "_blank")
                    .append("rect")
                    .attr("x", x0).attr("y", y)
                    .attr("width", Math.max(1, x1 - x0))
                    .attr("height", EACH_GENE_HEIGHT)
                    .attr("fill", color).attr("stroke", color)
                    .style("cursor", "pointer")
                    .append("title").text(title);
                return;
            }
            /* detail view: central line + UTRs + exons + strand arrows */
            var link = g.append("a")
                .attr("xlink:href", href).attr("target", "_blank");
            var midY = y + EACH_GENE_HEIGHT / 2;
            link.append("line")
                .attr("x1", x0).attr("y1", midY)
                .attr("x2", x1).attr("y2", midY)
                .attr("stroke", color).attr("stroke-width", 1)
                .style("cursor", "pointer");
            var cdsS = toNum(gene.cdsStart);
            var cdsE = toNum(gene.cdsEnd);
            if (cdsS !== null && cdsE !== null && cdsS > mb0 && cdsE < mb1) {
                var u0 = clampRange(x0, xScale(cdsS * 1e6), chartW);
                var u1 = clampRange(xScale(cdsE * 1e6), x1, chartW);
                [u0, u1].forEach(function (u) {
                    if (u[1] - u[0] > 0) {
                        link.append("rect")
                            .attr("x", u[0]).attr("y", y)
                            .attr("width", u[1] - u[0])
                            .attr("height", EACH_GENE_HEIGHT)
                            .attr("fill", "#A9A9A9").attr("stroke", "#A9A9A9")
                            .style("cursor", "pointer");
                    }
                });
            }
            (gene.exons || []).forEach(function (ex) {
                var es = clampRange(xScale(toNum(ex[0]) * 1e6),
                                    xScale(toNum(ex[1]) * 1e6), chartW);
                if (es[1] - es[0] > 0) {
                    link.append("rect")
                        .attr("x", es[0]).attr("y", y)
                        .attr("width", es[1] - es[0])
                        .attr("height", EACH_GENE_HEIGHT)
                        .attr("fill", color).attr("stroke", color)
                        .style("cursor", "pointer");
                }
            });
            var dir = gene.strand === "-" ? -1 : 1;
            drawStrandArrows(link, x0, x1, y, midY, dir, "#999999", 10);
            link.append("title").text(title);
        });
    }

    /* ---- Homology Band (mirrors drawHomologyBand; mouse -> human) ---- */
    function drawHomologyTrack(g, xScale, chartW, yTop, homology) {
        if (!homology || !homology.length) return;
        homology.forEach(function (h, i) {
            var row = i % NUM_GENE_ROWS;
            var y = yTop + row * EACH_GENE_HEIGHT;
            var rs = toNum(h.ref_start), re = toNum(h.ref_end);
            if (rs === null || re === null) return;
            var r = clampRange(xScale(Math.min(rs, re) * 1e6),
                               xScale(Math.max(rs, re) * 1e6), chartW);
            var x0 = r[0], x1 = r[1];
            if (x1 - x0 < 0.5) return;
            var qs = toNum(h.query_start), qe = toNum(h.query_end);
            var href = "http://genome.ucsc.edu/cgi-bin/hgTracks?db=hg38" +
                "&position=chr" + h.query_chr + ":" +
                Math.round(qs * 1e6) + "-" + Math.round(qe * 1e6);
            var title = "hg38: Chr " + h.query_chr + " from " +
                qs.toFixed(3) + " to " + qe.toFixed(3) + " Mb";
            var link = g.append("a")
                .attr("xlink:href", href).attr("target", "_blank");
            var midY = y + EACH_GENE_HEIGHT / 2;
            link.append("line")
                .attr("x1", x0).attr("y1", midY)
                .attr("x2", x1).attr("y2", midY)
                .attr("stroke", "#000000").attr("stroke-width", 1)
                .style("cursor", "pointer");
            var dir = h.query_strand === "-" ? -1 : 1;
            drawStrandArrows(link, x0, x1, y, midY, dir, "#666666", 8);
            link.append("title").text(title);
        });
    }

    /* ---- SNP track (mirrors drawSNPTrackNew) ----
       Dense orange density bars at the bottom of the plot, one per Mb-bin,
       normalised 0..1 (snp data comes from the track endpoint). Each bar is
       a full-width rect centred on the x-axis (extending above and below it)
       so adjacent bins form a contiguous, gapless band like the original. */
    function drawSNPTrack(g, chartW, chartH, snp) {
        if (!snp || !snp.length) return;
        var snpG = g.append("g").attr("class", "mapping-snp-track");
        var nbins = snp.length;
        snp.forEach(function (d, i) {
            var h = d * SNP_MAX_H;
            if (h < 0.5) return;
            var x0 = (chartW * i) / nbins;
            var x1 = (chartW * (i + 1)) / nbins;
            snpG.append("rect")
                .attr("x", x0)
                .attr("y", chartH - h)
                .attr("width", Math.max(1, x1 - x0))
                .attr("height", 2 * h)
                .attr("fill", "#FFA500");   // SNP_COLOR = ORANGE
        });
    }

    /* ---- Haplotype Band (mirrors drawHaplotypeBand) ---- */
    function haplotypeSegmentColor(prev, cur) {
        if (prev === -1 && cur === -1) return HAPLOTYPE_COLORS.neg;
        if (prev === 1 && cur === 1) return HAPLOTYPE_COLORS.pos;
        if (prev === 0 && cur === 0) return HAPLOTYPE_COLORS.het;
        return HAPLOTYPE_COLORS.rec;
    }

    function drawHaplotypeTrack(g, xScale, chartW, yTop, haplotype) {
        var rows = haplotypePlottedStrains(haplotype);
        if (!rows.length) return;
        var strains = haplotype.strains || [];
        var markers = haplotype.markers || [];
        var mX = markers.map(function (m) { return xScale(toNum(m.m) * 1e6); });

        /* coloured horizontal segments between consecutive markers */
        for (var j = 1; j < markers.length; j++) {
            var x0 = Math.max(0, mX[j - 1]);
            var x1 = Math.min(chartW, mX[j]);
            if (x1 - x0 < 0.5) continue;
            for (var rI = 0; rI < rows.length; rI++) {
                var k = strains.indexOf(rows[rI].strain);
                if (k < 0) continue;
                var color = haplotypeSegmentColor(
                    markers[j - 1].g[k], markers[j].g[k]);
                g.append("line")
                    .attr("x1", x0).attr("y1", yTop + 7 + rI * HAPLOTYPE_ROW_H)
                    .attr("x2", x1).attr("y2", yTop + 7 + rI * HAPLOTYPE_ROW_H)
                    .attr("stroke", color)
                    .attr("stroke-width", HAPLOTYPE_LINE_W);
            }
        }

        /* black marker ticks + rotated marker names at the bottom */
        var lastRow = rows.length - 1;
        markers.forEach(function (m, j) {
            var mx = mX[j];
            if (mx < 0 || mx > chartW) return;
            g.append("rect")
                .attr("x", mx - 1).attr("y", yTop)
                .attr("width", 2)
                .attr("height", rows.length * HAPLOTYPE_ROW_H)
                .attr("fill", "#000000");
            g.append("text")
                .attr("transform", "translate(" + mx + "," +
                       (yTop + 17 + 2 * lastRow * EACH_GENE_HEIGHT) +
                       ") rotate(-90)")
                .attr("text-anchor", "middle")
                .attr("font-family", FONT)
                .attr("font-size", "12px")
                .attr("fill", "#000000")
                .text(m.n);
        });

        /* strain names + expression values on the right of the plot */
        rows.forEach(function (r, rI) {
            var y = yTop + 11 + rI * HAPLOTYPE_ROW_H;
            g.append("text")
                .attr("x", chartW + 10).attr("y", y)
                .attr("font-family", FONT)
                .attr("font-size", "12px")
                .attr("fill", "#000000")
                .text(r.strain);
            g.append("text")
                .attr("x", chartW + 80).attr("y", y)
                .attr("font-family", FONT)
                .attr("font-size", "12px")
                .attr("fill", "#000000")
                .text(r.value.toFixed(2));
        });
    }

    /* ---- view-change notification ----
       The page shows a different results table per view: the whole-genome QTL
       results table, or the server-rendered "Interval Analyst" gene table for
       a chromosome/range. Because the figure switches views without reloading
       the page, tell the page whenever the view changes so it can keep the
       table in step. Listeners get the chr (null = whole genome) plus the
       visible Mb range. */
    function announceView(container, data, focusLayout, focus, rangeB) {
        var viewChr = (focus === null)
            ? null
            : String(focusLayout.lengths[0].chr);
        var startMb = null;
        var endMb = null;
        if (viewChr !== null) {
            if (rangeB) {
                startMb = rangeB.start / 1e6;
                endMb = rangeB.end / 1e6;
            } else {
                startMb = 0;
                endMb = focusLayout.lengths[0].size / 1e6;
            }
        }

        var viewKey = (viewChr === null)
            ? "all"
            : viewChr + ":" + startMb.toFixed(6) + "-" + endMb.toFixed(6);
        if (viewKey === state.lastViewKey) return;
        state.lastViewKey = viewKey;

        var detail = {
            chr: viewChr,
            startMb: startMb,
            endMb: endMb,
            species: data.species || ""
        };
        var evt;
        try {
            evt = new CustomEvent("mappingfigure:viewchange", {
                bubbles: true,
                detail: detail
            });
        } catch (err) {
            /* older browsers without the CustomEvent constructor */
            evt = document.createEvent("CustomEvent");
            evt.initCustomEvent("mappingfigure:viewchange", true, false, detail);
        }
        container.dispatchEvent(evt);
    }

    function render(containerId, data) {
        var container = document.getElementById(containerId);
        if (!container) return;

        /* preserve the page scroll across re-renders so expanding/collapsing
           tracks (or async track-data arriving) doesn't make the page jump */
        var scrollY = window.scrollY;

        container.innerHTML = "";

        state.containerId = containerId;
        state.data = data;
        /* whether the markers and the chromosome lengths are both in cM */
        state.cmAxis = usesCmAxis(data);

        /* initialise track toggles + carried-over view the first render */
        if (!state.tracksInitialized) {
            state.tracks.gene = data.gene_checked === true;
            state.tracks.homology = data.homology_checked === true;
            state.tracks.haplotype = data.haplotype_checked === true;
            state.tracksInitialized = true;
        }
        if (!state.viewInitialized) {
            var _sc = parseInt(data.selected_chr, 10);
            if (_sc > 0) {
                var _chrs = data.chr_lengths || [];
                var _cname = _chrs[_sc - 1] ? String(_chrs[_sc - 1].chr) : null;
                if (_cname) state.initialFocusChrName = _cname;
                var _sm = toNum(data.startMb);
                var _em = toNum(data.endMb);
                if (_sm !== null && _em !== null && _sm >= 0 && _em > _sm) {
                    state.range = { startMb: _sm, endMb: _em };
                }
            }
            state.viewInitialized = true;
        }

        var fullLayout = layoutChromosomes(data);
        var markers = (data.markers || []).filter(function (m) {
            return chrIndex(fullLayout, m.chr) >= 0 && markerBases(m) !== null;
        });
        var layout = filterEmptyChromosomes(fullLayout, markers, data);
        state.layout = layout;

        /* resolve any carried-over focus-by-name into a layout index */
        if (state.initialFocusChrName) {
            var _fi = chrIndex(layout, state.initialFocusChrName);
            if (_fi >= 0) state.focusChr = _fi;
            state.initialFocusChrName = null;
        }

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

        /* on-demand track data for the focused chromosome/range */
        var trackData = null;
        var trackKey = null;
        var rangeB = null;
        if (focus !== null) {
            var chrName = layout.lengths[focus].chr;
            var chrSizeB = layout.lengths[focus].size;
            if (state.range) {
                var rs = Math.max(0, toNum(state.range.startMb) || 0);
                var re = Math.min(chrSizeB / 1e6,
                                  toNum(state.range.endMb) || 0);
                if (re > rs) {
                    rangeB = { start: rs * 1e6, end: re * 1e6 };
                }
            }
            trackKey = trackDataKey(chrName, rangeB);
            trackData = state.trackData[trackKey] || null;
            ensureTrackData(containerId, data, focus, layout, rangeB);
        }

        var width = Math.min(
            Math.max(container.clientWidth || DEFAULT_WIDTH, 600), MAX_WIDTH);
        /* extra right room for haplotype strain labels when that track is on */
        var th = trackHeights(state, focus, trackData);
        var rightExtra = (focus !== null && th.haplotype > 0) ? 110 : 0;
        var chartW = width - MARGIN.left - MARGIN.right - rightExtra;

        /* extra vertical room for the browser-link bands + tracks (focused) */
        var hasBands = focus !== null;
        var bandStack = hasBands
            ? (BAND_PAD + 3 * (BAND_H + BAND_PAD))
            : 0;
        var topStack = bandStack + th.gene + th.homology + th.haplotype;
        var height = PLOT_HEIGHT + MARGIN.top + MARGIN.bottom + topStack;
        var chartH = height - MARGIN.top - MARGIN.bottom;
        var chrLabelY = 24 + topStack;
        var topInset = TOP_LABEL_INSET + topStack;

        var xScale = d3.scale.linear()
            .domain(rangeB ? [rangeB.start, rangeB.end]
                            : [0, focusLayout.totalBases])
            .range([0, chartW]);

        /* restrict plotted markers to the visible range when zoomed */
        if (rangeB) {
            focusMarkers = focusMarkers.filter(function (m) {
                var b = markerBases(m);
                return b !== null && b >= rangeB.start && b <= rangeB.end;
            });
        }
        var yMax = yDomain(data, focusMarkers)[1];
        var yScale = d3.scale.linear()
            .domain([0, yMax])
            .range([chartH, topInset]);

        var svg = d3.select(container).append("svg")
            .attr("width", width)
            .attr("height", height)
            .attr("class", "mapping-figure")
            .on("mousemove", repositionTip);

        var g = svg.append("g")
            .attr("transform", "translate(" + MARGIN.left + "," + MARGIN.top + ")");

        /* chromosome bands + labels */
        if (focus === null) {
            focusLayout.lengths.forEach(function (c, i) {
                var x0 = xScale(focusLayout.starts[i]);
                var x1 = xScale(focusLayout.starts[i] + c.size);
                g.append("rect")
                    .attr("x", x0).attr("y", 0)
                    .attr("width", Math.max(1, x1 - x0))
                    .attr("height", chartH)
                    .attr("fill", i % 2 === 0 ? COLORS.backLight : COLORS.backDark)
                    .attr("stroke", COLORS.chrStroke)
                    .style("cursor", "pointer")
                    .on("click", function () {
                        state.focusChr = i;
                        state.range = null;
                        render(containerId, data);
                    });
                /* chromosome label at the TOP of the band (like the original:
                   regular weight, sitting just inside the top of the plot) */
                g.append("text")
                    .attr("x", (x0 + x1) / 2)
                    .attr("y", chrLabelY)
                    .attr("text-anchor", "middle")
                    .attr("font-family", FONT)
                    .attr("font-size", "22px")
                    .attr("fill", COLORS.text)
                    .style("cursor", "pointer")
                    .text(c.chr)
                    .on("click", function () {
                        state.focusChr = i;
                        state.range = null;
                        render(containerId, data);
                    });
            });
        } else {
            /* focused single chromosome: fixed-width alternating vertical
               bands (mirrors the original's plotWidth/13.5 background) */
            var nBands = 14;
            var bandW = chartW / nBands;
            for (var b = 0; b < nBands; b++) {
                g.append("rect")
                    .attr("x", b * bandW).attr("y", 0)
                    .attr("width", Math.max(1, bandW))
                    .attr("height", chartH)
                    .attr("fill", b % 2 === 0 ? COLORS.backDark : COLORS.backLight);
            }
            /* focused chromosome label at the top, centred */
            g.append("text")
                .attr("x", chartW / 2)
                .attr("y", chrLabelY)
                .attr("text-anchor", "middle")
                .attr("font-family", FONT)
                .attr("font-size", "22px")
                .attr("fill", COLORS.text)
                .text(focusLayout.lengths[0].chr);
        }

        /* browser-link bands (focused view only) */
        if (hasBands) {
            var bandStartB = rangeB ? rangeB.start : 0;
            var bandEndB = rangeB ? rangeB.end : focusLayout.lengths[0].size;
            drawBrowserBands(g, data, layout, focus, chartW,
                             bandStartB, bandEndB);
        }

        /* gene / homology / haplotype tracks (focused view only). Each track
           has a collapsible header: expanded shows the content, minimized
           shows just the "Expand ..." band. */
        if (hasBands && trackData) {
            var trackY = bandStack;
            var rangeMb = rangeB ? (rangeB.end - rangeB.start) / 1e6
                                  : focusLayout.lengths[0].size / 1e6;
            var detail = rangeMb <= DRAW_DETAIL_MB;
            if (th.gene && trackData.genes) {
                trackY = drawTrackSection(
                    g, chartW, trackY, "Gene track",
                    state.tracks.gene, function () {
                        state.tracks.gene = !state.tracks.gene;
                        render(containerId, data);
                    },
                    function (trackG, y) {
                        drawGeneTrack(trackG, xScale, chartW, y,
                                      trackData.genes, detail);
                    },
                    GENE_TRACK_H);
            }
            if (th.homology && trackData.homology) {
                trackY = drawTrackSection(
                    g, chartW, trackY, "Homology track",
                    state.tracks.homology, function () {
                        state.tracks.homology = !state.tracks.homology;
                        render(containerId, data);
                    },
                    function (trackG, y) {
                        drawHomologyTrack(trackG, xScale, chartW, y,
                                          trackData.homology);
                    },
                    GENE_TRACK_H);
            }
            if (th.haplotype && trackData.haplotype) {
                trackY = drawTrackSection(
                    g, chartW, trackY, "Haplotype track",
                    state.tracks.haplotype, function () {
                        state.tracks.haplotype = !state.tracks.haplotype;
                        render(containerId, data);
                    },
                    function (trackG, y) {
                        drawHaplotypeTrack(trackG, xScale, chartW, y,
                                           trackData.haplotype);
                    },
                    (haplotypePlottedStrains(
                        trackData.haplotype).length + 8) * HAPLOTYPE_ROW_H);
            }
        }

        /* brief "loading" hint, only while a track fetch for this chromosome
           is genuinely in flight. Keyed on the request state rather than on
           "no data yet", so it cannot outlive a request that failed - or one
           that was never made at all, which is the case on a genetic axis
           where nothing the endpoint returns can be placed (see
           physicalTracksUsable). */
        var _species = String(data.species || "").toLowerCase();
        if (hasBands && physicalTracksUsable() && trackKey &&
            state.trackLoading[trackKey] &&
            (_species === "mouse" || _species === "rat")) {
            g.append("text")
                .attr("class", "mapping-loading")
                .attr("x", 10).attr("y", 8)
                .attr("font-family", FONT)
                .attr("font-size", "12px")
                .attr("fill", "#666666")
                .text("Loading track data\u2026");
        }

        /* SNP density track (orange bars at the bottom of the plot). Its bins
           are Mb bins, so - like the other physical tracks - it is left out on
           a genetic axis. It would not even look wrong there: the bars are
           placed by index across the whole width, so they would chart a
           Mb-sized window of the chromosome stretched over the cM range. */
        if (hasBands && physicalTracksUsable() && trackData &&
            trackData.snp && trackData.snp.length && data.snp_checked) {
            drawSNPTrack(g, chartW, chartH, trackData.snp);
        }

        /* Mb tick marks + labels (physic scale, mirrors PIL) */
        if (data.plotScale === "physic") {
            if (focus === null) {
                /* whole-genome: the original works out one tick step from the
                   first chromosome and then reuses it for every chromosome
                   (its distScale is only ever assigned while it is still
                   zero), so the gap between ticks is the same all the way
                   across the figure. A chromosome shorter than the step just
                   gets no tick, or a single one where the step falls inside
                   it - far better than a per-chromosome step that packs
                   labels on top of each other wherever a chromosome is small
                   relative to the others. */
                var firstMb = fullLayout.lengths.length
                    ? fullLayout.lengths[0].size / 1e6
                    : 0;
                var distScale = firstMb > 75 ? 25 : (firstMb > 30 ? 10 : 5);
                focusLayout.lengths.forEach(function (c, i) {
                    var lenMb = c.size / 1e6;
                    var j = 0;
                    for (var tick = distScale; tick < Math.ceil(lenMb); tick += distScale) {
                        var x = xScale(focusLayout.starts[i] + tick * 1e6);
                        g.append("line")
                            .attr("x1", x).attr("y1", chartH)
                            .attr("x2", x).attr("y2", chartH + 8)
                            .attr("stroke", "#000")
                            .attr("stroke-width", 1);
                        if (j % 2 === 0) {
                            /* labels read downwards, as in the original (which
                               draws them with PIL at angle 270, i.e. a quarter
                               turn clockwise) and hang below their tick */
                            g.append("text")
                                .attr("transform", "translate(" + x + "," + (chartH + 10) + ") rotate(90)")
                                .attr("text-anchor", "start")
                                .attr("font-family", FONT)
                                .attr("font-size", "14px")
                                .attr("fill", "#000")
                                .text(String(tick));
                        }
                        j += 1;
                    }
                });
            } else {
                /* single chromosome / Mb range: nice continuous scale, with
                   major + minor ticks labelled in absolute Mb. The grid is
                   snapped to multiples of minorStep rather than starting at
                   the range boundary: a range such as 10.013-11.013 used to
                   generate ticks that never coincided with a multiple of
                   step, so nothing was ever a major tick and the axis came
                   out with no labels at all. */
                var mbStart = rangeB ? rangeB.start / 1e6 : 0;
                var lenMb = rangeB ? (rangeB.end - rangeB.start) / 1e6
                                   : focusLayout.lengths[0].size / 1e6;
                var step = niceStep(lenMb);
                var minorStep = step / 5;
                var mbDecimals = stepDecimals(step);
                var firstTick = Math.ceil(mbStart / minorStep - 1e-9) * minorStep;
                var lastMb = mbStart + lenMb;
                var nTicks = Math.floor((lastMb - firstTick) / minorStep + 1e-9);
                for (var vi = 0; vi <= nTicks; vi += 1) {
                    var v = firstTick + vi * minorStep;
                    /* step is exactly five minor steps, so a tick within half
                       a step of a multiple of step is a major one. Measured
                       against the tick spacing rather than a fixed epsilon,
                       which only worked while the grid happened to start on
                       a multiple of step. */
                    var nearMajor =
                        Math.abs(v - Math.round(v / step) * step) < minorStep / 2;
                    var x = xScale(v * 1e6);
                    g.append("line")
                        .attr("x1", x).attr("y1", chartH)
                        .attr("x2", x).attr("y2", chartH + (nearMajor ? 12 : 6))
                        .attr("stroke", "#000")
                        .attr("stroke-width", nearMajor ? 2 : 1);
                    if (nearMajor && v > mbStart) {
                        g.append("text")
                            .attr("transform", "translate(" + x + "," + (chartH + 26) + ") rotate(-90)")
                            .attr("text-anchor", "middle")
                            .attr("font-family", FONT)
                            .attr("font-size", "14px")
                            .attr("fill", "#000")
                            .text(v.toFixed(mbDecimals));
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
                .text(usesCmAxis(data) ? "Centimorgans" : "Megabases");
        }

        /* suggestive / significant threshold lines (with hover tooltips) */
        var sugg = toNum(data.suggestive);
        var sig = toNum(data.significant);
        if (sugg !== null) {
            drawThresholdLine(g, chartW, yScale, sugg, COLORS.suggestive,
                              "Suggestive", data);
        }
        if (sig !== null) {
            drawThresholdLine(g, chartW, yScale, sig, COLORS.significant,
                              "Significant", data);
        }

        if (data.manhattan_plot) {
            /* scatter points (larger when focused on a single chromosome) */
            var dotR = focus === null ? 2 : 3.5;
            var pts = g.append("g").attr("class", "points");
            attachMarkerInteractions(
                pts.selectAll("circle").data(focusMarkers).enter().append("circle")
                    .attr("r", dotR)
                    .attr("cx", function (m) { return xScale(xForMarker(focusLayout, m)); })
                    .attr("cy", function (m) { return yScale(markerScore(m, data)); })
                    .attr("fill", function (m) { return pointColor(data, layout, m); })
                    .style("opacity", 1.0),
                data);

            /* peak markers (>= significant threshold) as purple triangles */
            if (sig !== null) {
                var halfW = focus === null ? 4.5 : 7;
                var triH = focus === null ? 7 : 10;
                var peaks = focusMarkers.filter(function (m) {
                    return markerScore(m, data) >= sig;
                });
                attachMarkerInteractions(
                    pts.selectAll("path.peak").data(peaks).enter().append("path")
                        .attr("d", function (m) {
                            var x = xScale(xForMarker(focusLayout, m));
                            var y = yScale(markerScore(m, data));
                            return "M" + x + "," + (y - triH) +
                                   "L" + (x - halfW) + "," + y +
                                   "L" + (x + halfW) + "," + y + "Z";
                        })
                        .attr("fill", COLORS.peak)
                        .attr("stroke", COLORS.peak),
                    data);
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
            /* invisible hover targets along the line so hovering any position
               (e.g. a peak) shows that marker's tooltip */
            attachMarkerInteractions(
                g.append("g").selectAll("circle").data(focusMarkers).enter()
                    .append("circle")
                    .attr("r", 5)
                    .attr("cx", function (m) { return xScale(xForMarker(focusLayout, m)); })
                    .attr("cy", function (m) { return yScale(markerScore(m, data)); })
                    .attr("fill", "transparent"),
                data);
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
                              additiveMax, chartH, topInset);
            drawAdditiveAxis(g, chartW, additiveMax, chartH, topInset);
        }

        /* gene location marker (purple triangle at the bottom) */
        drawGeneMarker(g, data, layout, focus, xScale, chartH);

        /* y axis: mirrors the original PIL figure - a blue axis line with
           short ticks pointing outwards and blue tick labels. d3 v3 does not
           set a stroke on the domain/tick lines and GN2 does not load d3's
           axis stylesheet (which normally supplies the stroke), so it has to
           be set explicitly or the line and ticks do not render at all. */
        var yAxis = d3.svg.axis().scale(yScale).orient("left")
            .ticks(5).tickSize(4, 0).tickPadding(5)
            .tickFormat(tickNumberFormat(yScale, 5));
        var yAxisG = g.append("g").attr("class", "y axis").call(yAxis);
        /* The original runs this line from the bottom of the plot all the way
           up to its top edge, which is above the highest tick: the scale's
           range stops at topInset to leave room for the chromosome label (and
           the bands/tracks) at the top of the drawing area. d3's domain path
           would stop there instead, leaving the axis short of the top of the
           figure, so drop it and draw the line ourselves. */
        yAxisG.select("path").remove();
        yAxisG.append("line")
            .attr("class", "y-axis-line")
            .attr("x1", 0).attr("y1", 0)
            .attr("x2", 0).attr("y2", chartH)
            .attr("stroke", COLORS.axis)
            .style("stroke-width", 1);
        yAxisG.selectAll("g.tick line")
            .attr("stroke", COLORS.axis)
            .style("stroke-width", 1);
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
                .attr("class", "mapping-toolbar")
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
                    state.range = null;
                    render(containerId, data);
                });
        }

        /* metadata block (top-left) */
        drawMetadata(svg, data, MARGIN.left);

        /* Announce the view so the page can keep in step with the figure.
           The results table below the figure is rendered server-side for the
           mapped chromosome, so it needs to refresh whenever we focus a
           different chromosome or range (and revert to the whole-genome table
           when we go back to all chromosomes). */
        announceView(container, data, focusLayout, focus, rangeB);

        window.scrollTo(0, scrollY);
    }

    /* ------------------------------ SVG export --------------------------- */

    /* Serialize the current figure to a standalone .svg file and download it.
       mode "map"  -> just the plot (strips browser bands, all tracks, SNP)
       mode "full" -> plot + currently-maximized tracks; collapsed tracks are
                      dropped entirely (no "Expand ..." sections in the file). */
    function downloadSVG(mode) {
        var container = state.containerId &&
            document.getElementById(state.containerId);
        if (!container) return;
        var svg = container.querySelector("svg.mapping-figure");
        if (!svg) return;

        var clone = svg.cloneNode(true);
        var removeEls = function (selector) {
            var nodes = clone.querySelectorAll(selector);
            for (var i = nodes.length - 1; i >= 0; i--) {
                nodes[i].parentNode.removeChild(nodes[i]);
            }
        };

        /* interactive chrome is never exported */
        removeEls(".mapping-toolbar");
        removeEls(".mapping-loading");

        if (mode === "map") {
            removeEls(".mapping-browser-bands");
            removeEls(".mapping-snp-track");
            /* drop all track sections (header + content) */
            removeEls(".mapping-track");
        } else {
            /* "full": keep maximized tracks, drop collapsed ("Expand") ones */
            removeEls('.mapping-track[data-expanded="false"]');
        }

        /* make it a valid standalone SVG */
        clone.setAttribute("xmlns", "http://www.w3.org/2000/svg");
        clone.setAttribute("xmlns:xlink", "http://www.w3.org/1999/xlink");

        var str = new XMLSerializer().serializeToString(clone);
        var blob = new Blob([str], { type: "image/svg+xml;charset=utf-8" });
        var url = URL.createObjectURL(blob);

        var chrLabel = "";
        if (state.focusChr !== null && state.layout &&
            state.layout.lengths[state.focusChr]) {
            chrLabel = "_chr" + state.layout.lengths[state.focusChr].chr;
        }
        var traitName = (state.data && state.data.this_trait &&
                         state.data.this_trait.name) || "mapping";

        var a = document.createElement("a");
        a.href = url;
        a.download = (mode === "map" ? "mapping_" : "mapping_full_") +
            traitName + chrLabel + ".svg";
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
    }

    /* Store the manual Mb-range zoom (or clear it) without rendering, so a
       caller can change the chromosome and the range together and draw once.
       Rendering in between would fetch - and cache - the whole chromosome's
       track data that the range then makes unnecessary. */
    function applyRange(range) {
        if (range && range.startMb !== undefined &&
            range.endMb !== undefined) {
            state.range = {
                startMb: parseFloat(range.startMb),
                endMb: parseFloat(range.endMb)
            };
        } else {
            state.range = null;
        }
    }

    /* ------------------------------ public API --------------------------- */

    return {
        render: render,
        downloadSVG: downloadSVG,
        reset: function (containerId, data) {
            state.focusChr = null;
            state.range = null;
            render(containerId || state.containerId, data || state.data);
        },
        /* client-side toggles for the Gene / Homology / Haplotype tracks */
        setTracks: function (tracks) {
            if (tracks.gene !== undefined) state.tracks.gene = !!tracks.gene;
            if (tracks.homology !== undefined) {
                state.tracks.homology = !!tracks.homology;
            }
            if (tracks.haplotype !== undefined) {
                state.tracks.haplotype = !!tracks.haplotype;
            }
            if (state.containerId) render(state.containerId, state.data);
        },
        getTracks: function () {
            return {
                gene: !!state.tracks.gene,
                homology: !!state.tracks.homology,
                haplotype: !!state.tracks.haplotype
            };
        },
        /* focus a chromosome by name (used by the Chr dropdown), optionally
           zooming to an Mb range in the same call so that only the requested
           window is ever fetched */
        focusChromosome: function (chrName, range) {
            if (!state.layout) return;
            var idx = chrIndex(state.layout, String(chrName));
            if (idx < 0) return;
            state.focusChr = idx;
            applyRange(range);
            if (state.containerId) render(state.containerId, state.data);
        },
        /* manual Mb-range zoom applied to the focused chromosome */
        setRange: function (range) {
            applyRange(range);
            if (state.containerId) render(state.containerId, state.data);
        },
        getRange: function () {
            return state.range ? {
                startMb: state.range.startMb,
                endMb: state.range.endMb
            } : null;
        }
    };
})();
