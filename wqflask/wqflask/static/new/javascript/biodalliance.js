"use strict";

var bd_browser = null;
var bd_data = {};

var getChrLen = function(chr) {
    return js_data[chr * 1];
};

var createBDBrowser = function(chr, start, end, speciesName, sources) {
    console.log("creating BD browser");
    var b = new Browser({
        chr: chr,
        viewStart: start,
        viewEnd: end,

        coordSystem: {
            speciesName: speciesName
        },

        sources: sources,

        setDocumentTitle: false,
        prefix: '/dalliance/',
        noPersist: true,
        pageName: 'bd_container'
    });

    console.log("created BD browser");
    return b;
};

var showBDButton = function() {
    $('#open_bd').show();
    $('#close_bd').hide();
};

var hideBDButton = function() {
    $('#close_bd').show();
    $('#open_bd').hide();
};


var setBDData = function(chr, length) {
    // bd_data = { chr: chr, length: length };
    bd_data.chr = chr;
    bd_data.length = length;
};

var setBDSpecies = function(species) {
    bd_data.species = species;
};


var openBDBrowser = function() {
    console.log("opening browser");
    if (!bd_browser) {
        bd_browser = createBDBrowser(bd_data.chr, 0, bd_data.length * 1000000, bd_data.species,
                                     [{name: 'Genome',
                                       twoBitURI:  'http://www.biodalliance.org/datasets/GRCm38/mm10.2bit',
                                       desc: 'Mouse reference genome build GRCm38',
                                       tier_type: 'sequence',
                                       provides_entrypoints: true},
                                      {name: 'QTL',
                                       tier_type: 'qtl',
                                       uri: 'http://gsocbox:8880/static/qtl/lod2.csv',
                                       stylesheet_uri: "http://gsocbox:8880/stylesheets/qtl-stylesheet.xml"
                                      }]
                                    );
    } else {
        bd_browser.setLocation(bd_data.chr, 0, bd_data.length * 1000000);
    }

    bd_browser.maxViewWidth = bd_data.length * 1000000;
};
