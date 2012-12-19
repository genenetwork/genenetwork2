$ ->
    run_marker_regression = ->
        console.log("In marker regression")
        url = "/marker_regression"
        $("#trait_data_form").attr("action", url);
        $("#trait_data_form").submit()
    
    $("#marker_regression_btn").click(run_marker_regression)