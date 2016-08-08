"use strict";


var BD = {};
BD.browser = null;
BD.data = {};

var getChrLen = function(chr) {
    return js_data[chr * 1];
};

BD.createBrowser = function(chr, start, end, speciesName, sources) {
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

BD.showButton = function() {
    $('#open_bd').show();
    $('#close_bd').hide();
};

BD.hideButton = function() {
    $('#close_bd').show();
    $('#open_bd').hide();
};


BD.putData = function(data) {
    for (var key in data) {
        BD.data[key] = data[key];
    }
};

BD.openBrowser = function() {
    console.log("opening browser");
    if (!BD.browser) {
        BD.browser = BD.createBrowser(BD.data.chr, 0, BD.data.length * 1000000, BD.data.species,
                                     [{name: 'Genome',
                                       twoBitURI:  'http://www.biodalliance.org/datasets/GRCm38/mm10.2bit',
                                       desc: 'Mouse reference genome build GRCm38',
                                       tier_type: 'sequence',
                                       provides_entrypoints: true},
                                      {name: 'QTL',
                                       tier_type: 'qtl',
                                       uri: 'http://localhost:8880/static/qtl/lod2.csv',
                                       stylesheet_uri: "http://localhost:8880/stylesheets/qtl-stylesheet.xml"
                                      }]
                                    );
    } else {
        BD.browser.setLocation(BD.data.chr, 0, BD.data.length * 1000000);
    }

    BD.browser.maxViewWidth = BD.data.length * 1000000;
};
