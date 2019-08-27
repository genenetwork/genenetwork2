console.log("THE FILES:", js_data.browser_files)

snps_filename = "/browser_input?filename=" + js_data.browser_files[0]
annot_filename = "/browser_input?filename=" + js_data.browser_files[1]

localUrls =
{
  snps: snps_filename,
  annotations: annot_filename
};

var coordinateSystem = js_data.chr_lengths

var vscaleWidth = 90.0;
var legendWidth = 150.0;

if ('significant' in js_data) {
  var significant_score = parseFloat(js_data.significant)
} else {
  var significant_score = js_data.max_score * 0.75
}
var score = { min: 0.0, max: js_data.max_score, sig: significant_score };
var gwasPadding = { top: 35.0,
                    bottom: 35.0,
                    left: vscaleWidth,
                    right: legendWidth };
var gwasHeight = 500.0;
var config =
{   score: score,
    urls: localUrls,
    tracks: {
        gwas: {
            trackHeight: gwasHeight,
            padding: gwasPadding,
            snps: {
                radius: 3.75,
                lineWidth: 1.0,
                color: { outline: "#FFFFFF",
                         fill:    "#00008B" },
                pixelOffset: {x: 0.0, y: 0.0}
            },
            annotations: {
                urls: {
                    url: "GeneNetwork"
                },
                radius: 5.5,
                outline:   "#000000",
                snpColor:  "#0074D9",
                geneColor: "#FF4136"
            },
            score: score,
            legend: {
                fontSize: 14,
                hPad: 0.1,
                vPad: 0.2
            },
            vscale: {
                color: "#000000",
                hPad: 0.125,
                numSteps: 3,
                fonts: { labelSize: 18, scaleSize: 16 }
            },
        },
    },
    chrs: {
        chrBG1: "#FFFFFF",
        chrBG2: "#EEEEEE",
        chrLabels: { fontSize: 16 },
    },
    // initialChrs: { left: "1", right: "5" }
    coordinateSystem: coordinateSystem,
};

if (js_data.selected_chr != -1) {
    config['initialChrs'] = {left: js_data.selected_chr, right: js_data.selected_chr}
}

$('#browser_tab').click(function() {
  if ($('#gwas').length == 0){
    GenomeBrowser.main(config)();
  }
});

document.getElementById("controls").style.visibility = "visible";