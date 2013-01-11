/*
 jquery part
*/
/*
used by index (base/indexBody.py)
*/
$(document).ready(function () {
    options_visible = 0; //Whether advanced options are being shown
    $('tr .advanced_option').hide();

    $('.toggle_advanced').click(function () {
        $('tr .advanced_option').toggle();

        if (options_visible = 0) {
            $('.full_search_td').css('display', 'none;');
            $('.search_td').css('display', 'inline');
            options_visible = 1;
        } else {
            if ($('#type_menu.type_menu').val() = 'Hippocampus') {
                $('.search_td').css('display', 'none;');
                $('.full_search_td').css('display', 'inline');
            }
            options_visible = 0;
        }
    });

    $('#full_search').click(function () {
        gene_symbol = $('input[name=keyword]').val();
        scriptable_interface_url = 'http://alexandria.uthsc.edu:89/webqtl/main.py?cmd=sch&gene=' + gene_symbol;
        window.open(scriptable_interface_url, '_self');
    });
});

$('select.type_menu').live('change', function () {
    var trait_type = $('select.type_menu option:selected').val();
    $('#tissue').val(trait_type);
    $('#tissue').trigger('change');
});


/*
used by CorrelationPage.py, AddToSelectionPage.py, and SearchResultPage.py
*/
$(document).ready(function () {
    $('img[name=addselect], img[name=networkgraph], img[name=corrmatrix], img[name=partialCorr], img[name=comparecorr], img[name=mintmap], img[name=heatmap]').click(function () {
        if ($('input[name=searchResult]:checked').length < 1) {
            for (i = 0; i < 10; i++) {
                $('input[name=searchResult]:eq(' + i + ')').attr('checked', true);
            }
        }
    });

    $('img[name=addselect]').click(function () {
        addRmvSelection($('input[name=RISet]').val(), document.getElementsByName('showDatabase' + $('input[name=RISet]').val())[0], 'addToSelection');
    });

    $('.toggleShowHide').click(function () {
        var className = '.extra_options';
        if ($(className).css('display') == 'none') {
            var less = 'less';
            $('input[name=showHideOptions]').val(less);
            $(className).show();
            $('input[name=options]').val('Fewer Options');
            var display = $('input[name=options]').css('display')
            $(display).val('block');
        } else {
            var more = 'more';
            $('input[name=showHideOptions]').val(more);
            $(className).hide();
            $('input[name=options]').val('More Options');
            var display = $('input[name=showHideOptions]').css('display')
            $(display).val('block');
        }
    });
});

/*
used by AddToSelectionPage.py
*/
function validateTraitNumber() {
    var checkBoxes = $('.checkallbox');
    if (checkBoxes.filter(":checked").length < 2) {
        alert("Please select at least two traits.");
        return false;
    } else {
        return true;
    }
}

/*
used by TextSearchPage.py
*/
$(document).ready(function () {

    $('.add_traits').click(function () {
        $('input[name=searchResult]').each(function () {
            if ($(this).is(':checked')) {
                groupName = $(this).parents().next().next().children('[href]').text();
                addORrmv = 'addToSelection';
                thisForm = $('form[name=showDatabase]');
                addRmvSelection_allGroups(groupName, thisForm, addORrmv);
            }
        });
    });

    function addRmvSelection_allGroups(groupName, thisForm, addORrmv) {
        thisForm.attr('target', groupName);
        thisForm.children('input[name=FormID]:hidden').val(addORrmv);
        thisForm.children('input[name=RISet]:hidden').val(groupName);
        var newWindow = open("", thisForm.attr('target'), "menubar=1,toolbar=1,location=1,resizable=1,status=1,scrollbars=1,directories=1,width=900");
        thisForm.submit();
    }

    $('.tab_content').hide(); //Hide all tab content
    $('div.tab_container').each(function () {
        $(this).parent('td').find('div.tab_container:first').find('div.tab_content:first').show();
    });
    $('ul.tabs').each(function () {
        $(this).find('li:first').addClass('active');
    });
    $('ul.tabs:first').find('li:first').show();
    $('.tab_container:first').find('.tab_content:first').show();

    //On Click Event
    $('ul.tabs li').click(function () {
        $('ul.tabs').find('li').removeClass('last_viewed');
        if ($(this).parent('ul.tabs').next('div.tab_container').attr('id').indexOf('stats') != 1) {
            $(this).addClass('last_viewed');
        }
        $(this).parent('ul.tabs').find('li').removeClass('active');
        $(this).addClass('active');
        $(this).parent('ul.tabs').next('div.tab_container').find('.tab_content').hide();
        var activeTab = $(this).find('a').attr('href');
        if ($.browser.msie) {
            $(activeTab).show();
        } else {
            $(activeTab).fadeIn();
        } //Fade in the active ID content
        return false;
    });

});

/*
used by DataEditingPage.py
*/
$(document).ready(function () {

    // ZS: This checks the number of columns in order to determine which column to not sort; in this case the plus-minus symbol shouldn't be sortable
    $('#sortable1,#sortable2').find('th').each(function () {
        if ($(this).text() == 'SE') {
            $.tablesorter.defaults.headers = {
                3: {
                    sorter: false
                }
            };
            return false;
        }
    });

    if ($('#sortable1,#sortable2').find('.outlier').size() > 0) {
        $('input[name=sample_method]:eq(1)').attr('checked','checked');
        $('input[name=tissue_method]:eq(1)').attr('checked','checked');
    }


/*
 ZS: This segment is called by tablesorter.js; it determines where to get the text used when sorting, based on the type of cell. 
 If a cell has a text input field, it gets the text from its class, which is changed when the user changes the value.

 This segment is repeated twice. Ideally this wouldn't be the case, but I can't find a way to reuse the inner textExtraction function.
*/

    //ZS: Defining these here, so they don't need to be searched for in the DOM for every single node
    primaryTable = $("#sortable1");
    otherTable = $("#sortable2");

    primaryValueHeader = primaryTable.find('th:contains("Value"):eq(0)');
    primarySEHeader = primaryTable.find('th:contains("SE"):eq(0)');
    otherValueHeader = otherTable.find('th:contains("Value"):eq(1)');
    otherSEHeader = otherTable.find('th:contains("SE"):eq(1)');

    $("#sortable1").tablesorter({
        textExtraction: function (node) {
            if ((node.children[0] == "[object HTMLInputElement]" && node.children[0].type == "text") || (/\S/.test(node.id))) {
                cellId = node.id;
                thisCell = $('#' + cellId).children(':eq(0)')
                valueClassNames = thisCell.attr('class').split(/\s+/);
                capitalized_column_name = cellId.split('_')[0].charAt(0).toUpperCase() + cellId.split('_')[0].slice(1);
                value = valueClassNames[valueClassNames.length - 1];
                newValue = thisCell.val();

                if (newValue == 'x' || value == '9999' || value == '-9999') {
                    valueType = cellId.split('_')[0];
                    if (valueType == 'value') {
                        header = primaryValueHeader;
                    } else {
                        header = primarySEHeader;
                    }

                    if (header.hasClass('headerSortUp')) {
                        sort_order = 'desc';
                    } else if (header.hasClass('headerSortDown')) {
                        sort_order = 'asc';
                    } else {
                        sort_order = 'desc';
                    }

                    if (sort_order == 'desc') {
                        value = 9999;
                        thisCell.removeClass(value).addClass('9999');
                    } else if (sort_order == 'asc') {
                        value = -9999;
                        thisCell.removeClass(value).addClass('-9999');
                    } else {
                        value = 9999;
                        thisCell.removeClass(value).addClass('9999');
                    }
                }

                text = value;
            } else {
                if (node.textContent) {
                    text = node.textContent;
                } else {
                    if (node.childNodes[0] && node.childNodes[0].hasChildNodes()) {
                        text = node.childNodes[0].innerHTML;
                    } else {
                        text = node.innerText;
                    }
                }
            }
            return text
        }
    });

    $("#sortable2").tablesorter({
        textExtraction: function (node) {
            if ((node.children[0] == "[object HTMLInputElement]" && node.children[0].type == "text") || (/\S/.test(node.id))) {
                cellId = node.id;
                thisCell = $('#' + cellId).children(':eq(0)')
                valueClassNames = thisCell.attr('class').split(/\s+/);
                capitalized_column_name = cellId.split('_')[0].charAt(0).toUpperCase() + cellId.split('_')[0].slice(1);
                value = valueClassNames[valueClassNames.length - 1];
                newValue = thisCell.val();

                if (newValue == 'x' || value == '9999' || value == '-9999') {
                    valueType = cellId.split('_')[0];
                    if (valueType == 'value') {
                        header = otherValueHeader;
                    } else {
                        header = otherSEHeader;
                    }

                    if (header.hasClass('headerSortUp')) {
                        sort_order = 'desc';
                    } else if (header.hasClass('headerSortDown')) {
                        sort_order = 'asc';
                    } else {
                        sort_order = 'desc';
                    }

                    if (sort_order == 'desc') {
                        value = 9999;
                        thisCell.removeClass(value).addClass('9999');
                    } else if (sort_order == 'asc') {
                        value = -9999;
                        thisCell.removeClass(value).addClass('-9999');
                    } else {
                        value = 9999;
                        thisCell.removeClass(value).addClass('9999');
                    }
                }

                text = value;
            } else {
                if (node.textContent) {
                    text = node.textContent;
                } else {
                    if (node.childNodes[0] && node.childNodes[0].hasChildNodes()) {
                        text = node.childNodes[0].innerHTML;
                    } else {
                        text = node.innerText;
                    }
                }
            }
            return text
        }
    });

    /*
 ZS: When the user changes the value in the text field, the new value is added as a class. This is because 
 $('input[type=text]').val() gets the value attribute, which is always the default value, instead of the 
 value property (which can be changed)
*/

    var thisTable = $('#sortable1,#sortable2');

    thisTable.bind("update propertychange keyup input paste", function (e) {

        var target = e.target;
        $target = $(target);

        if (target.nodeName.toLowerCase() == 'input') {
            thisClassNames = $target.attr('class').split(/\s+/);
            valueClass = thisClassNames[thisClassNames.length - 1];
            newValue = $target.val();
            thisParent = $target.parent('td');
            thisParentId = thisParent.attr('id');

            $target.removeClass(valueClass);

            if (newValue == 'x') {
                thisParent.parent('tr').addClass('blocked');
            } else {
                $('#' + thisParentId).children('input.valueField:eq(0)').addClass(newValue);
            }
        }
    });

    ////////////////////////////////////
    // Initially close tabs
    ////////////////////////////////////
    thisForm = $('form[name="dataInput"]');

    $('#sectionbody2').hide();
    $('#sectionbody3').hide();
    $('#sectionbody4').hide();

    $('#title1').click(function () {
        $('#sectionbody1').toggle();
        return false;
    });
    $('#title2').click(function () {
        $('#sectionbody2').toggle();
        return false;
    });
    $('#title3').click(function () {
        $('#sectionbody3').toggle();
        return false;
    });
    $('#title4').click(function () {
        $('#sectionbody4').toggle();
        return false;
    });
    $('#title5').click(function () {
        $('#sectionbody5').toggle();
        return false;
    });



    //////////////////////////////////////////////////////////////
    // Switch out + and - icon when you click each section header
    //////////////////////////////////////////////////////////////
    var expand_html = "<span class=\"expand_container\">&nbsp;&nbsp;<IMG src=\"/images/Expand.gif\" alt=\"Expand\"></span>";
    var contract_html = "<span class=\"contract_container\">&nbsp;&nbsp;<IMG src=\"/images/Contract.gif\" alt=\"Contract\"></span>";

    $('#title2, #title3, #title4').prepend(expand_html).addClass('1');

    $('#title1, #title5').prepend(contract_html).addClass('0');

    for (i = 1; i <= 5; i++) {
        $('#title' + i).click(function () {
            if ($(this).hasClass('0')) {
                $(this).find('span').replaceWith(expand_html);
                $(this).removeClass('0');
                $(this).addClass('1');
            } else {
                $(this).find('span').replaceWith(contract_html);
                $(this).removeClass('1');
                $(this).addClass('0');
            }
        });
    }

    // Exclude cases by attributes
    $('div.attribute_values:first').css('display', 'inline'); //Display the dropdown menu with the first attribute's distinct values
    $('select[name=exclude_menu]').change(function () {
        $('div.attribute_values').css('display', 'none'); //clear all other menus when a new attribute is selected
        attribute = $(this).val();
        //attribute = $('select[name=exclude_menu]').val();
        menu = $('div.attribute_values').find('[name=\'' + attribute + '\']');
        menu.parent().css('display', 'inline');
    });

    primary_row_count = $('#primary').find('tr').length - 1;
    other_row_count = $('#other').find('tr').length - 1;

    if (primary_row_count >= other_row_count) {
        row_count = primary_row_count;
    } else {
        row_count = other_row_count;
    }

    $('div.attribute_values').children('select').change(function () {
        exclude_value = $(this).val();
    });
});

$(window).load(function () {

    //ZS: These are needed in a few places; looping through rows by index is faster than doing a "find" search
    numPrimaryRows = $('#sortable1').find('tr').length;
    numOtherRows = $('#sortable2').find('tr').length;


    ///////////////////////////////
    //Basic Statistics
    ///////////////////////////////
    /////////////////////////////////////////////////////////////////
    // Hide unselected Basic Statistics tabs (when just BXD strains
    // are selected, hide the results for all strains/non-BXD)
    /////////////////////////////////////////////////////////////////
    $('#stats_tabs1').hide();
    $('#stats_tabs2').hide();

    $('#sectionbody2').find('select[name=stats_mdp]').change(function () {
        selected = $('#sectionbody2').find('select[name=stats_mdp] option:selected').val();
        for (i = 0; i <= 2; i++) {
            $('#stats_tabs' + i).hide();
        }
        $('#stats_tabs' + selected).show();
    });

    ////////////////////////////////////////////////////////////////////////
    // Select the same tab across each sample group (when a Box Plot is 
    // selected for BXD, switching to Non-BXD will also display a Box Plot)
    ////////////.///////////////////////////////////////////////////////////
    var $tabs1 = $('#stats_tabs0').tabs();
    var $tabs2 = $('#stats_tabs1').tabs();
    var $tabs3 = $('#stats_tabs2').tabs();

    $tabs1.tabs({
        show: function (event, ui) {
            var selected = $tabs1.tabs('option', 'selected');
            $tabs2.tabs('select', selected);
            $tabs3.tabs('select', selected);
        }
    });
    $tabs2.tabs({
        show: function (event, ui) {
            var selected = $tabs2.tabs('option', 'selected');
            $tabs1.tabs('select', selected);
            $tabs3.tabs('select', selected);
        }
    });
    $tabs3.tabs({
        show: function (event, ui) {
            var selected = $tabs3.tabs('option', 'selected');
            $tabs1.tabs('select', selected);
            $tabs2.tabs('select', selected);
        }
    });


    ///////////////////////////////
    //Calculate Correlations
    ///////////////////////////////
    $('#sectionbody3').find('input[name="sample_corr"]').click(function () {
        dbValue = $('select[name=database1] option:selected').val();
        $('input[name=database]').val(dbValue);
        criteriaValue = $('select[name=criteria1] option:selected').val();
        $('input[name=criteria]').val(criteriaValue);
        MDPValue = $('select[name=MDPChoice1] option:selected').val();
        $('input[name=MDPChoice]').val(MDPValue);

        methodValue = $('input[name=sample_method]:checked').val();

        //This simple method can be used now that 'method' is defaulted to None instead of ''
        if (methodValue == "1") {
            $('input[name=method]').val('1');
        } else {
            $('input[name=method]').val('2');
        }

        dataEditingFunc(this.form, 'correlation');
    });

    $('#sectionbody3').find('input[name="lit_corr"]').click(function () {
        dbValue = $('select[name=database2] option:selected').val();
        $('input[name=database]').val(dbValue);
        criteriaValue = $('select[name=criteria2] option:selected').val();
        $('input[name=criteria]').val(criteriaValue);
        MDPValue = $('select[name=MDPChoice2] option:selected').val();
        $('input[name=MDPChoice]').val(MDPValue);

        $('input[name=method]').val('3');

        dataEditingFunc(this.form, 'correlation');
    });

    $('#sectionbody3').find('input[name="tiss_corr"]').click(function () {
        dbValue = $('select[name=database3] option:selected').val();
        $('input[name=database]').val(dbValue);
        criteriaValue = $('select[name=criteria3] option:selected').val();
        $('input[name=criteria]').val(criteriaValue);
        MDPValue = $('select[name=MDPChoice3] option:selected').val();
        $('input[name=MDPChoice]').val(MDPValue);

        methodValue = $('input[name=tissue_method]:checked').val();

        if (methodValue == "4") {
            $('input[name=method]').val('4');
        } else {
            $('input[name=method]').val('5');
        }
        dataEditingFunc(this.form, 'correlation');
    });

    ///////////////////////////////
    //Mapping Tools
    ///////////////////////////////
    $('#sectionbody4').find('input[name=interval]').click(function () {
        chrValue = $('select[name=chromosomes1] option:selected').val();
        $('input[name=chromosomes]').val(chrValue);
        scaleValue = $('select[name=scale1] option:selected').val();
        $('input[name=scale]').val(scaleValue);
        $('input[name=controlLocus]').val('');

        //Changed the way permValue, bootValue, and parentsValue are acquired; before it was $(____).is(':checked');
        permValue = $('input[name=permCheck1]:checked').val();
        $('input[name=permCheck]').val(permValue);

        bootValue = $('input[name=bootCheck1]:checked').val();
        $('input[name=bootCheck]').val(bootValue);

        if ($('input[name=parentsf14regression1]:checked').length > 0) {
            $('input[name=parentsf14regression]').val('on');
        } else {
            $('input[name=parentsf14regression]').val('off');
        }

        varValue = $('input[name=applyVarianceSE1]:checked').val();
        $('input[name=applyVarianceSE]').val(varValue);

        dataEditingFunc(this.form, 'intervalMap');
    });

    var tiptext = "e.g., rs12345";
    controlLocus = $('#sectionbody4').find('input[name=controlLocus]');

    if (controlLocus.val() == '' || controlLocus == tiptext) {
        controlLocus.addClass('searchtip').val(tiptext);
    }

    controlLocus.focus(function (e) {
        if (controlLocus.val() == tiptext) {
            controlLocus.val('');
        }
        controlLocus.removeClass('searchtip');
    });

    controlLocus.blur(function (e) {
        if (controlLocus.val() == '') {
            controlLocus.addClass('searchtip').val(tiptext);
        } else if (controlLocus.val() == tiptext) {
            controlLocus.addClass('searchtip');
        } else {
            controlLocus.removeClass('searchtip');
        }
    });

    $('#sectionbody4').find('input[name=composite]').click(function () {
        chrValue = $('select[name=chromosomes2] option:selected').val();
        $('input[name=chromosomes]').val(chrValue);
        scaleValue = $('select[name=scale2] option:selected').val();
        $('input[name=scale]').val(scaleValue);
        controlValue = controlLocus.val();
        if (controlValue != tiptext) {
            controlLocus.val(controlValue);
        } else {
            controlLocus.val('');
        }

        //Changed the way permValue, bootValue, and parentsValue are acquired; before it was $(____).is(':checked');
        permValue = $('input[name=permCheck2]:checked').val();
        $('input[name=permCheck]').val(permValue);

        bootValue = $('input[name=bootCheck2]:checked').val();
        $('input[name=bootCheck]').val(bootValue);

        if ($('input[name=parentsf14regression3]:checked').length > 0) {
            $('input[name=parentsf14regression]').val('on');
        } else {
            $('input[name=parentsf14regression]').val('off');
        }

        dataEditingFunc(this.form, 'intervalMap');

    });

    $('#sectionbody4').find('input[name=marker]').click(function () {
        //Changed the way parentsValue is acquired; before it was $(____).is(':checked');
        if ($('input[name=parentsf14regression2]:checked').length > 0) {
            $('input[name=parentsf14regression]').val('on');
        } else {
            $('input[name=parentsf14regression]').val('off');
        }

        varValue = $('input[name=applyVarianceSE2]:checked').val();
        $('input[name=applyVarianceSE]').val(varValue);

        dataEditingFunc(this.form, 'markerRegression');
    });

    ///////////////////////////////
    //Review and Edit Data
    ///////////////////////////////
    $('input[name=excludeGroup]').click(function () {
        for (i = 1; i <= Math.max(primary_row_count, other_row_count) - 1; i++) {
            valueExists = 0;
            $('#Primary_' + i + ',#Other_' + i).children().each(function () {
                if ($(this).text() == exclude_value) {
                    $('#Primary_' + i + ',#Other_' + i).addClass('blocked').find('input[type=text]').val('x');
                    valueExists = 1;
                    return false;
                }
            });
        }
    });

    $('.update').click(function () {
        windowName = 'formTarget' + (new Date().getTime());
        var windowHeight; // windowHeight and windowWidth are used to place the window in the center of the screen
        var windowWidth;
        windowHeight = (window.screen.height/2) - (350 + 10)
        windowWidth = (window.screen.width/2) - (450 + 50)
        newWindow = open("",windowName,"menubar=1,toolbar=1,resizable=1,left=" + windowWidth + ",top=" + windowHeight + ",screenX=" + windowWidth + ",screenY=" + windowHeight + ",status=1,scrollbars=0,directories=1");

        document.dataInput.target = windowName;
        document.dataInput.submitID.value = "basicStatistics";

        primaryData = getTraitData()[0];
        otherData = getTraitData()[1];
        allData = getTraitData()[2];

        if (otherData[0].length > 0) {
            if ($('select[name="stats_mdp"] option:selected').val() == 0) {
                document.dataInput.strainNames.value = allData[0].toString();
                document.dataInput.strainVals.value = allData[1].toString();
                document.dataInput.strainVars.value = allData[2].toString();
            } else if ($('select[name="stats_mdp"] option:selected').val() == 1) {
                document.dataInput.strainNames.value = primaryData[0].toString();
                document.dataInput.strainVals.value = primaryData[1].toString();
                document.dataInput.strainVars.value = primaryData[2].toString();
            } else {
                document.dataInput.strainNames.value = otherData[0].toString();
                document.dataInput.strainVals.value = otherData[1].toString();
                document.dataInput.strainVars.value = otherData[2].toString();
            }
        } else {
            document.dataInput.strainNames.value = allData[0].toString();
            document.dataInput.strainVals.value = allData[1].toString();
            document.dataInput.strainVars.value = allData[2].toString();
        }

        document.dataInput.submit();
    });

    $('input[name="export"]').click(function () {
        windowName = 'formTarget' + (new Date().getTime());
        newWindow = open("", windowName, "menubar=1,toolbar=1,location=1,resizable=1,status=1,scrollbars=0,directories=1,width=900");
        document.dataInput.target = windowName;
        document.dataInput.submitID.value = "exportData";

        primaryData = getTraitData()[0];
        otherData = getTraitData()[1];

        document.dataInput.strainNames.value = primaryData[0].toString();
        document.dataInput.strainVals.value = primaryData[1].toString();
        document.dataInput.strainVars.value = primaryData[2].toString();

        document.dataInput.otherStrainNames.value = otherData[0].toString();
        document.dataInput.otherStrainVals.value = otherData[1].toString();
        document.dataInput.otherStrainVars.value = otherData[2].toString();

        attribute_names = new Array();
        $('#primary,#other').find('th.attribute_name').each(function () {
            attribute_names.push($(this).val().toString());
        });

        primary_attribute_values = ""; //This string will be structured as a dictionary with a set of values for each attribute; it will be parsed in the ExportPage class
        other_attribute_values = "";

        attr_counter = 1; // Counter for each different attribute
        row_counter = 1; // Counter for each value for each attribute
        while (attr_counter <= attribute_names.length) {
            attribute_name = $('#primary,#other').find('th.attribute_name:eq(' + (attr_counter - 1).toString() + ')').text();
            primary_row_count = $('#primary').find('tr').length - 1;
            other_row_count = $('#other').find('tr').length - 1;

            primary_attribute_values += attribute_name + " : ";
            other_attribute_values += attribute_name + " : ";

            primary_value_string = ""; //This string of values (in the format 'a,b,c', etc) will be appended to the primary_attribute_values string
            for (row_counter = 1; row_counter <= numPrimaryRows; row_counter++) {
                value = $('#primary_attribute' + attr_counter.toString() + '_sample' + row_counter.toString()).text();
                if (row_counter == primary_row_count) {
                    primary_value_string += (value + " / ");
                } else {
                    primary_value_string += (value + ",");
                }
            }

            primary_attribute_values += primary_value_string;

            other_value_string = ""; //This string of values (in the format 'a,b,c', etc) will be appended to the other_attribute_values string
            for (row_counter = 1; row_counter <= numOtherRows; row_counter++) {
                value = $('#other_attribute' + attr_counter.toString() + '_sample' + row_counter.toString()).text();
                if (row_counter == other_row_count) {
                    other_value_string += (value + " / ");
                } else {
                    other_value_string += (value + ",");
                }
            }
            other_attribute_values += other_value_string;
            attr_counter += 1
        }

        document.dataInput.extra_attributes.value = primary_attribute_values;
        document.dataInput.other_extra_attributes.value = other_attribute_values;

        document.dataInput.submit();
    });

    var thisTable = $('#sortable1,#sortable2'); //ZS: variable representing each table, because it's used often	
    thisTable.find('input[name="selectCheck"]').click(function () {
        if ($(this).is(':checked')) {
            $(this).parent("").parent("").children("td").css("background-color", "yellow");
        } else {
            if (!($(this).parent().parent().hasClass('outlier'))) {
                $(this).parent().parent().children("td").css("background-color", "white");
            }
        }
    });

    $('input[name=resetButton]').click(function () {

        //ZS: Reset "hide no value" and "hide outliers"
        $('#showHideOptions').find('input[name=showHideNoValue]').val(' Hide No Value ');
        $('#showHideOptions').find('input[name=showHideOutliers]').val(' Hide Outliers ');
        noValShown = 1;
        outliersShown = 1;

        for (i = 1; i <= numPrimaryRows - 1; i++) {
            var thisRow = $('#Primary_' + i);
            if (thisRow.is('.invisible')) {
                thisRow.removeClass('invisible');
            }
            if (thisRow.is('.blocked')) {
                thisRow.removeClass('blocked');
            }
            if (thisRow.is(':not(.outlier)')) {
                thisRow.css("background-color", "white");
            }

            var thisValueField = thisRow.find('.valueField');

            var originalValue = thisValueField[0].defaultValue;
            var thisClassNames = thisRow.find('input:eq(1)').attr('class').split(/\s+/);
            var valueClass = thisClassNames[thisClassNames.length - 1];
            thisRow.find('input:eq(1)').removeClass(valueClass).addClass(originalValue).val(originalValue);

            if (thisValueField.length > 1) {
                var originalValue = thisValueField[1].defaultValue;
                var thisClassNames = thisRow.find('input:eq(2)').attr('class').split(/\s+/);
                var valueClass = thisClassNames[thisClassNames.length - 1];
                thisRow.find('input:eq(2)').removeClass(valueClass).addClass(originalValue).val(originalValue);
            }
        }
        for (i = 1; i <= numOtherRows - 1; i++) {
            var thisRow = $('#Other_' + i);
            if (thisRow.is('.invisible')) {
                thisRow.removeClass('invisible')
            }
            if (thisRow.is('.blocked')) {
                thisRow.removeClass('blocked');
            }
            if (thisRow.is(':not(.outlier)')) {
                thisRow.css("background-color", "white");
            }

            var thisValueField = thisRow.find('.valueField');

            var originalValue = thisValueField[0].defaultValue;
            var thisClassNames = thisRow.find('input:eq(1)').attr('class').split(/\s+/);
            var valueClass = thisClassNames[thisClassNames.length - 1];
            thisRow.find('input:eq(1)').removeClass(valueClass).addClass(originalValue).val(originalValue);

            if (thisValueField.length > 1) {
                var originalValue = thisValueField[1].defaultValue;
                var thisClassNames = thisRow.find('input:eq(2)').attr('class').split(/\s+/);
                var valueClass = thisClassNames[thisClassNames.length - 1];
                thisRow.find('input:eq(2)').removeClass(valueClass).addClass(originalValue).val(originalValue);
            }
        }
    });

    var tiptext2 = "e.g., 4, 6-30, 43";
    var blockField = $('#showHideOptions').find('input[name=removeField]'); //ZS: Field where user inputs the index of the samples he/she wants to block; created variable because it's used often
    if (blockField.val() == '' || blockField.val() == tiptext2) {
        blockField.addClass('searchtip');
        blockField.val(tiptext2);
    }

    blockField.focus(function (e) {
        if (blockField.val() == tiptext2) {
            blockField.val('');
        }
        blockField.removeClass('searchtip');
    });

    blockField.blur(function (e) {
        if (blockField.val() == '') {
            blockField.addClass('searchtip');
            blockField.val(tiptext2);
        } else if (blockField.val() == tiptext2) {
            blockField.addClass('searchtip');
        } else {
            blockField.removeClass('searchtip');
        }
    });

    var noValShown = new Boolean(1);
    var outliersShown = new Boolean(1);

    $('#showHideOptions').bind('click', function (e) {
        var target = e.target;
        $target = $(target);

        if (target.name === 'blockSamples') {
            if (blockField.val() == tiptext2) {
                blockField.val('')
            }
            blockedText = blockField.val();
            blockedTextSplit = new Array();
            blockedItems = new Array();

            blockedTextSplit = blockedText.split(/\,/);

            for (i = 0; i <= blockedTextSplit.length - 1; i++) {
                var item = blockedTextSplit[i];
                if (item.indexOf('-') != -1) {
                    subArray = new Array();
                    subArray = item.split('-');
                    num1 = parseInt(subArray[0]);
                    num2 = parseInt(subArray[1]);
                    for (j = num1; j <= num2; j = j + 1) {
                        blockedItems.push(j);
                    }
                } else if (!(isNaN(item))) {
                    blockedItems.push(item);
                }
            }

            for (i = 0; i <= blockedItems.length - 1; i++) {
                item = blockedItems[i];
                if ($('select[name=block_method]').val() == '0') {
                    var thisRow = $('#Other_' + item);
                } else {
                    var thisRow = $('#Primary_' + item);
                }

                if (thisRow.is('.novalue')) {
                    continue;
                } else {
                    thisRow.addClass('blocked').find('input.valueField').val('x');
                }

                //First look at value cell
                var thisCell = thisRow.find('input:eq(1)');
                var thisClassNames = thisCell.attr('class').split(/\s+/);
                var valueClass = thisClassNames[thisClassNames.length - 1];
                var header = thisRow.parents('table.tablesorter').find('th.header:contains("Value"):eq(0)');
                if (header.hasClass('headerSortUp')) {
                    thisCell.removeClass(valueClass).addClass('-9999');
                } else if (header.hasClass('headerSortDown')) {
                    thisCell.removeClass(valueClass).addClass('9999');
                } else {
                    thisCell.removeClass(valueClass).addClass('-9999');
                }

                //Check if there is an SE column			
                if (thisRow.find('input.valueField').length > 1) {
                    var thisCell = thisRow.find('input:eq(2)');
                    var thisClassNames = thisCell.attr('class').split(/\s+/);
                    var valueClass = thisClassNames[thisClassNames.length - 1];
                    var header = thisRow.parents('table.tablesorter').find('th.header:contains("SE"):eq(0)');
                    if (header.hasClass('headerSortUp')) {
                        thisCell.removeClass(valueClass).addClass('-9999');
                    } else if (header.hasClass('headerSortDown')) {
                        thisCell.removeClass(valueClass).addClass('9999');
                    } else {
                        thisCell.removeClass(valueClass).addClass('-9999');
                    }
                }
            }
        } else if (target.name === 'showHideNoValue') {
            if (noValShown) {
                $('#showHideOptions').find('input[name=showHideNoValue]').val(' Show No Value ');
                for (i = 1; i <= Math.max(numPrimaryRows, numOtherRows) - 1; i++) {
                    if (i <= numPrimaryRows - 1) {
                        var thisRow = $('#Primary_' + i);
                        if (thisRow.is('.novalue:visible') || thisRow.is('.blocked:visible')) {
                            jQuery(thisRow).addClass('invisible');
                        }
                    }
                    if (i <= numOtherRows - 1) {
                        var thisOtherRow = $('#Other_' + i);
                        if (thisOtherRow.is('.novalue:visible') || thisOtherRow.is('.blocked:visible')) {
                            if (thisOtherRow.is(':visible')) {
                                jQuery(thisOtherRow).addClass('invisible');
                            }
                        }
                    }
                }
                noValShown = 0;
            } else {
                $('#showHideOptions').find('input[name=showHideNoValue]').val(' Hide No Value ');
                for (i = 1; i <= Math.max(numPrimaryRows, numOtherRows) - 1; i++) {
                    if (i <= numPrimaryRows - 1) {
                        var thisRow = $('#Primary_' + i);
                        if (thisRow.is('.novalue') || thisRow.is('.blocked')) {
                            jQuery(thisRow).removeClass('invisible');
                            if (!(outliersShown)) {
                                if (thisRow.is('.outlier:visible')) {
                                    jQuery(thisRow).addClass('invisible');
                                }
                            }
                        }
                    }
                    if (i <= numOtherRows - 1) {
                        var thisOtherRow = $('#Other_' + i);
                        if (thisOtherRow.is('.novalue') || thisOtherRow.is('.blocked')) {
                            jQuery(thisOtherRow).removeClass('invisible');
                            if (!(outliersShown)) {
                                if (thisOtherRow.is('.outlier:visible')) {
                                    jQuery(thisOtherRow).addClass('invisible');
                                }
                            }
                        }
                    }
                }
                noValShown = 1;
            }
        } else if (target.name === 'showHideOutliers') {
            if (outliersShown) {
                $('#showHideOptions').find('input[name=showHideOutliers]').val(' Show Outliers ');
                for (i = 1; i <= Math.max(numPrimaryRows, numOtherRows) - 1; i++) {
                    if (i <= numPrimaryRows - 1) {
                        thisRow = $('#Primary_' + i);
                        if (thisRow.is('.outlier:visible') && (!(thisRow.is('.invisible')))) {
                            thisRow.addClass('invisible')
                        }
                    }
                    if (i <= numOtherRows - 1) {
                        thisOtherRow = $('#Other_' + i);
                        if (thisOtherRow.is('.outlier:visible') && (!(thisOtherRow.is('.invisible')))) {
                            thisOtherRow.addClass('invisible')
                        }
                    }
                }
                outliersShown = 0;
            } else {
                $('#showHideOptions').find('input[name=showHideOutliers]').val(' Hide Outliers ');
                for (i = 1; i <= Math.max(numPrimaryRows, numOtherRows) - 1; i++) {
                    if (i <= numPrimaryRows - 1) {
                        thisRow = $('#Primary_' + i);
                        if (thisRow.is('.outlier') && (!(thisRow.is(':visible')))) {
                            if (!(noValShown)) {
                                if (thisRow.is('.blocked')) {
                                    continue;
                                }
                            }
                            jQuery(thisRow).removeClass('invisible')
                        }
                    }
                    if (i <= numOtherRows - 1) {
                        thisOtherRow = $('#Other_' + i);
                        if (thisOtherRow.is('.outlier') && (!(thisOtherRow.is(':visible')))) {
                            if (!(noValShown)) {
                                if (thisOtherRow.is('.blocked')) {
                                    continue;
                                }
                            }
                            jQuery(thisOtherRow).removeClass('invisible')
                        }
                    }
                }
                outliersShown = 1;
            }
        }
        return false;
    });
});

function getTraitData() {
    primary_row_count = $('#sortable1').find('tr').length - 1;
    other_row_count = $('#sortable2').find('tr').length - 1;

    primaryStrainNames = new Array();
    primaryVals = new Array();
    primaryVars = new Array();

    allStrainNames = new Array();
    allVals = new Array();
    allVars = new Array();

    for (i = 1; i <= primary_row_count; i++) {
        thisRow = $('#Primary_' + i);
        strainName = thisRow.find('span:first').text();
        primaryStrainNames.push(strainName);
        allStrainNames.push(strainName);
        strainVal = thisRow.find('input:eq(1)').val();
        primaryVals.push(strainVal);
        allVals.push(strainVal);
        strainVar = ''; // Just to initialize it in case there is no var
        strainVar = thisRow.find('input:eq(2)').val();
        primaryVars.push(strainVar);
        allVars.push(strainVar);
    }

    otherStrainNames = new Array();
    otherVals = new Array();
    otherVars = new Array();

    for (j = 1; j <= other_row_count; j++) {
        thisRow = $('#Other_' + j)
        strainName = thisRow.find('span:first').text();
        otherStrainNames.push(strainName);
        strainVal = thisRow.find('input:eq(1)').val();
        otherVals.push(strainVal);
        strainVar = ''; // Just to initialize it in case there is no var
        strainVar = thisRow.find('input:eq(2)').val();
        otherVars.push(strainVar);

        if (jQuery.inArray(strainName, allStrainNames) == -1) {
            allStrainNames.push(strainName);
            allVals.push(strainVal);
            allVars.push(strainVar);
        }
    }

    primaryData = [primaryStrainNames, primaryVals, primaryVars];
    otherData = [otherStrainNames, otherVals, otherVars];
    allData = [allStrainNames, allVals, allVars];

    return [primaryData, otherData, allData];
}

/*
used by networkGraphPageBody.py
*/

//Default to plain text + symbol for the "Export Graph File" button
$('input[name=exportGraphFile]').live('click', function () {
    window.open($('input[name=exportFilename]').val() + "_plain_symbol.txt")
});

function changeFormat(graphName) {
    var graphFormat = $('#exportFormat').val();
    var traitType = $('#traitType').val();

    $('input[name=exportGraphFile]').die('click');

    if (graphFormat == "xgmml") {
        if (traitType == "symbol") {
            var graphFile = graphName + "_xgmml_symbol.txt";
            $('input[name=exportGraphFile]').live('click', function () {
                window.open(graphFile)
            });
        } else if (traitType == "name") {
            var graphFile = graphName + "_xgmml_name.txt";
            $('input[name=exportGraphFile]').live('click', function () {
                window.open(graphFile)
            });
        }
    } else if (graphFormat == "plain") {
        if (traitType == "symbol") {
            var graphFile = graphName + "_plain_symbol.txt";
            $('input[name=exportGraphFile]').live('click', function () {
                window.open(graphFile)
            });
        } else if (traitType == "name") {
            var graphFile = graphName + "_plain_name.txt";
            $('input[name=exportGraphFile]').live('click', function () {
                window.open(graphFile)
            });
        }
    }
}