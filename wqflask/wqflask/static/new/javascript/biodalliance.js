"use strict";


var BD = {};
BD.browser = null;
BD.data = {};
BD.sources = [];

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

        maxHeight: 1400,
        setDocumentTitle: false,
        prefix: '/dalliance/',
        workerPrefix: 'build/',
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

BD.putSource = function(source) {
    BD.sources.push(source);
};

BD.openBrowser = function() {
    console.log("opening browser");
    if (!BD.browser) {
        BD.browser = BD.createBrowser(BD.data.chr,
                                      0,
                                      BD.data.length * 1000000,
                                      BD.data.species,
                                      BD.sources);
    } else {
        BD.browser.setLocation(BD.data.chr, 0, BD.data.length * 1000000);
    }

    BD.browser.maxViewWidth = BD.data.length * 1000000;
};
