console.log("THE FILES:", js_data.browser_files)

snps_filename = "/browser_input?filename=" + js_data.browser_files[0]
annot_filename = "/browser_input?filename=" + js_data.browser_files[1]

localUrls =
{
  snps: snps_filename,
  annotations: annot_filename
};

var coordinateSystem =
          [
              { chr: "1", size: "195471971" },
              { chr: "2", size: "182113224" },
              { chr: "3", size: "160039680" },
              { chr: "4", size: "156508116" },
              { chr: "5", size: "151834684" },
              { chr: "6", size: "149736546" },
              { chr: "7", size: "145441459" },
              { chr: "8", size: "129401213" },
              { chr: "9", size: "124595110" },
              { chr: "10", size: "130694993" },
              { chr: "11", size: "122082543" },
              { chr: "12", size: "120129022" },
              { chr: "13", size: "120421639" },
              { chr: "14", size: "124902244" },
              { chr: "15", size: "104043685" },
              { chr: "16", size: "98207768" },
              { chr: "17", size: "94987271" },
              { chr: "18", size: "90702639" },
              { chr: "19", size: "61431566" },
          ];

var vscaleWidth = 90.0;
var legendWidth = 140.0;

if ('significant' in js_data) {
  var significant_score = parseFloat(js_data.significant)
} else {
  var significant_score = 4
}
var score = { min: 0.0, max: js_data.max_score, sig: significant_score };
var gwasPadding = { top: 35.0,
                    bottom: 35.0,
                    left: vscaleWidth,
                    right: legendWidth };
var gwasHeight = 320.0;
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
                hPad: 0.2,
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

GenomeBrowser.main(config)();

document.getElementById("controls").style.visibility = "visible";