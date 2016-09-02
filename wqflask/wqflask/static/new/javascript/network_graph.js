window.onload=function() {
    // id of Cytoscape Web container div
    //var div_id = "cytoscapeweb";

    var cy = cytoscape({
      container: $('#cytoscapeweb'), // container to render in

      elements: elements_list,

      style: [ // the stylesheet for the graph
          {    
            selector: 'node',
            style: {
              'background-color': '#666',
              'label': 'data(id)',
              'font-size': 8
            }
          },

          {
            selector: 'edge',
            style: {
              'width': 'data(width)',
              'line-color': 'data(color)',
              'target-arrow-color': '#ccc',
              'target-arrow-shape': 'triangle',
              'font-size': 8
            }
          }
      ],
      
      zoom: 12,
      layout: { name: 'cose',
                fit: true, // whether to fit the viewport to the graph
                padding: 100, // the padding on fit
                idealEdgeLength: function( edge ){ return edge.data['correlation']*10; },                
              }, 

      
      zoomingEnabled: true,
      userZoomingEnabled: true,
      panningEnabled: true,
      userPanningEnabled: true,
      boxSelectionEnabled: false,
      selectionType: 'single',

      // rendering options:
      styleEnabled: true
    });

    var defaults = {
      zoomFactor: 0.05, // zoom factor per zoom tick
      zoomDelay: 45, // how many ms between zoom ticks
      minZoom: 0.1, // min zoom level
      maxZoom: 10, // max zoom level
      fitPadding: 30, // padding when fitting
      panSpeed: 10, // how many ms in between pan ticks
      panDistance: 10, // max pan distance per tick
      panDragAreaSize: 75, // the length of the pan drag box in which the vector for panning is calculated (bigger = finer control of pan speed and direction)
      panMinPercentSpeed: 0.25, // the slowest speed we can pan by (as a percent of panSpeed)
      panInactiveArea: 8, // radius of inactive area in pan drag box
      panIndicatorMinOpacity: 0.5, // min opacity of pan indicator (the draggable nib); scales from this to 1.0
      zoomOnly: false, // a minimal version of the ui only with zooming (useful on systems with bad mousewheel resolution)
      fitSelector: undefined, // selector of elements to fit
      animateOnFit: function(){ // whether to animate on fit
        return false;
      },
      fitAnimationDuration: 1000, // duration of animation on fit

      // icon class names
      sliderHandleIcon: 'fa fa-minus',
      zoomInIcon: 'fa fa-plus',
      zoomOutIcon: 'fa fa-minus',
      resetIcon: 'fa fa-expand'
    };

    cy.panzoom( defaults );
    
    cy.nodes().qtip({
                        content: function(){
                            gn_link = '<b>'+'<a href="http://gn2.genenetwork.org/show_trait?trait_id=' + this.data().id + '&dataset=' + this.data().dataset + '" >'+this.data().id +'</a>'+'</b><br>'
                            ncbi_link = '<a href="http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?db=gene&cmd=Retrieve&dopt=Graphics&list_uids=' + this.data().geneid + '" >NCBI<a>'+'<br>' 
                            omim_link = '<a href="http://www.ncbi.nlm.nih.gov/omim/' + this.data().omim + '" >OMIM<a>'+'<br>' 
                            qtip_content = gn_link + ncbi_link + omim_link
                            return qtip_content
                            //return '<b>'+'<a href="http://gn2.genenetwork.org/show_trait?trait_id=' + this.data().id + '&dataset=' + this.data().dataset + '" >'+this.data().id +'<a>'+'</b>' 
                        },
                        // content: {
                            // title: '<b>'+'<a href="http://gn2.genenetwork.org/show_trait?trait_id=' + this.target() + '&dataset=' + this.dataset() + '" >'+this.target() +'<a>'+'</b>',
                            // text: this.target,
                            // button: true
                        // },
                        position: {
                            my: 'top center',
                            at: 'bottom center'
                        },
                        style: {
                            classes: 'qtip-bootstrap',
                            tip: {
                                width: 16,
                                height: 8
                            }
                        }
                    });
                    
    cy.edges().qtip({
                        content: function(){
                            scatter_plot = '<b>'+'<a href="http://gn2-zach.genenetwork.org/corr_scatter_plot?dataset_1=' + this.data().source_dataset + '&dataset_2=' + this.data().target_dataset + '&trait_1=' + this.data().source + '&trait_2=' + this.data().target + '" >View Scatterplot</a>'+'</b>'
                            return scatter_plot
                        },
                        position: {
                            my: 'top center',
                            at: 'bottom center'
                        },
                        style: {
                            classes: 'qtip-bootstrap',
                            tip: {
                                width: 16,
                                height: 8
                            }
                        }
                    });
    
    // var options = {
      // name: 'breadthfirst',

      // fit: true, // whether to fit the viewport to the graph
      // directed: false, // whether the tree is directed downwards (or edges can point in any direction if false)
      // padding: 30, // padding on fit
      // circle: false, // put depths in concentric circles if true, put depths top down if false
      // spacingFactor: 1.75, // positive spacing factor, larger => more space between nodes (N.B. n/a if causes overlap)
      // boundingBox: undefined, // constrain layout bounds; { x1, y1, x2, y2 } or { x1, y1, w, h }
      // avoidOverlap: true, // prevents node overlap, may overflow boundingBox if not enough space
      // roots: undefined, // the roots of the trees
      // maximalAdjustments: 0, // how many times to try to position the nodes in a maximal way (i.e. no backtracking)
      // animate: false, // whether to transition the node positions
      // animationDuration: 500, // duration of animation in ms if enabled
      // animationEasing: undefined, // easing of animation if enabled
      // ready: undefined, // callback on layoutready
      // stop: undefined // callback on layoutstop
    // };

    // cy.layout( options );
    
};


