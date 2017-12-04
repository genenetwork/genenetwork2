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
              'label': 'data(label )',
              'font-size': 10
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
      layout: { name: 'circle',
                fit: true, // whether to fit the viewport to the graph
                padding: 30 // the padding on fit
                //idealEdgeLength: function( edge ){ return edge.data['correlation']*10; },                
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

    var eles = cy.$() // var containing all elements, so elements can be restored after being removed
    
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
    
    function create_qtips(cy){
        cy.nodes().qtip({
                            content: function(){
                                qtip_content = ''
                                gn_link = '<b>'+'<a href="http://gn2.genenetwork.org/show_trait?trait_id=' + this.data().id.split(":")[0] + '&dataset=' + this.data().id.split(":")[1] + '" >'+this.data().id +'</a>'+'</b><br>'
                                qtip_content += gn_link
                                if (typeof(this.data().geneid) !== 'undefined'){
                                    ncbi_link = '<a href="http://www.ncbi.nlm.nih.gov/entrez/query.fcgi?db=gene&cmd=Retrieve&dopt=Graphics&list_uids=' + this.data().geneid + '" >NCBI<a>'+'<br>'
                                    qtip_content += ncbi_link
                                }
                                if (typeof(this.data().omim) !== 'undefined'){
                                    omim_link = '<a href="http://www.ncbi.nlm.nih.gov/omim/' + this.data().omim + '" >OMIM<a>'+'<br>'
                                    qtip_content += omim_link
                                }
                                return qtip_content
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
                        
        cy.edges().qtip({
                            content: function(){
                                correlation_line = '<b>Sample r: ' + this.data().correlation + '</b><br>'
                                p_value_line = 'Sample p(r): ' + this.data().p_value + '<br>'
                                overlap_line = 'Overlap: ' + this.data().overlap + '<br>'
                                scatter_plot = '<a href="http://gn2-zach.genenetwork.org/corr_scatter_plot?dataset_1=' + this.data().source.split(":")[1] + '&dataset_2=' + this.data().target.split(":")[1] + '&trait_1=' + this.data().source.split(":")[0] + '&trait_2=' + this.data().target.split(":")[0] + '" >View Scatterplot</a>'
                                return correlation_line + p_value_line + overlap_line + scatter_plot
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
    }
    
    create_qtips(cy)
    
    $('#slide').change(function() {
        eles.restore()
        
        console.log(eles)
        
        // nodes_to_restore = eles.filter("node[max_corr >= " + $(this).val() + "], edge[correlation >= " + $(this).val() + "][correlation <= -" + $(this).val() + "]")
        // nodes_to_restore.restore()
        
        // edges_to_restore = eles.filter("edge[correlation >= " + $(this).val() + "][correlation <= -" + $(this).val() + "]")
        // edges_to_restore.restore()
        
        //cy.$("node[max_corr >= " + $(this).val() + "]").restore();
        //cy.$("edge[correlation >= " + $(this).val() + "][correlation <= -" + $(this).val() + "]").restore();
        
        cy.$("node[max_corr < " + $(this).val() + "]").remove(); 
        cy.$("edge[correlation < " + $(this).val() + "][correlation > -" + $(this).val() + "]").remove();

        cy.layout({ name: $('select[name=layout_select]').val(),
                    fit: true, // whether to fit the viewport to the graph
                    padding: 25 // the padding on fit              
                  });
        
    });
    
    $('#reset_graph').click(function() {
        eles.restore() 
        $('#slide').val(0)
        cy.layout({ name: $('select[name=layout_select]').val(),
                    fit: true, // whether to fit the viewport to the graph
                    padding: 25 // the padding on fit              
                  });
    });
    
    $('select[name=focus_select]').change(function() {
        focus_trait = $(this).val()

        eles.restore()
        cy.$('edge[source != "' + focus_trait + '"][target != "' + focus_trait + '"]').remove()

        cy.layout({ name: $('select[name=layout_select]').val(),
                    fit: true, // whether to fit the viewport to the graph
                    padding: 25 // the padding on fit              
                  });
    });
    
    $('select[name=layout_select]').change(function() {
        layout_type = $(this).val()
        console.log("LAYOUT:", layout_type)
        cy.layout({ name: layout_type,
                    fit: true, // whether to fit the viewport to the graph
                    padding: 25 // the padding on fit              
                  });
    });
    
    $("a#image_link").click(function(e) {
      var pngData = cy.png();

      $(this).attr('href', pngData);
      $(this).attr('download', 'network_graph.png');
      
      console.log("TESTING:", image_link)
      
    });

    
};


