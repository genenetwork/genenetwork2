"use strict";

var createBDBrowser = function(chr, start, end, sources) {
    console.log("creating BD browser");
    var b = new Browser({
        chr: chr,
        viewStart: start,
        viewEnd: end,

        coordSystem: {
            speciesName: 'Mouse'
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
