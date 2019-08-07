console.log("THE FILES:", js_data.browser_files)

snps_filename = "/browser_input?filename=" + js_data.browser_files[0]
annot_filename = "/browser_input?filename=" + js_data.browser_files[1]

localUrls = 
{
  snps: snps_filename,
  annotations: null
};

var vscaleWidth = 90.0;
var legendWidth = 140.0;
var score = { min: 0.0, max: 30.0, sig: 4 };
var gwasPadding = { top: 35.0,
                    bottom: 35.0,
                    left: vscaleWidth,
                    right: legendWidth };
var gwasHeight = 420.0;
var genePadding = { top: 10.0,
                    bottom: 35.0,
                    left: vscaleWidth,
                    right: legendWidth };
var geneHeight = 140.0;


var config =
{ trackHeight: 400.0,
  padding: gwasPadding,
  score: score,
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
      }
  },
  chrs: {
      chrBG1: "#FFFFFF",
      chrBG2: "#DDDDDD",
      chrLabels: { fontSize: 16 },
  },
  initialChrs: { left: "1", right: "19" }
};

GenomeBrowser.main(config)();

document.getElementById("controls").style.visibility = "visible";