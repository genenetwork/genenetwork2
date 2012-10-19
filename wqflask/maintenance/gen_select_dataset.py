# Copyright (C) University of Tennessee Health Science Center, Memphis, TN.
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License
# as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU Affero General Public License for more details.
#
# This program is available from Source Forge: at GeneNetwork Project
# (sourceforge.net/projects/genenetwork/).
#
# Contact Drs. Robert W. Williams and Xiaodong Zhou (2010)
# at rwilliams@uthsc.edu and xzhou15@uthsc.edu
#
#
#
# This module is used by GeneNetwork project (www.genenetwork.org)
#
# Created by GeneNetwork Core Team 2010/08/10
#
# Last updated by NL 2011/01/27

# created by Ning Liu 07/01/2010
# This script is to generate selectDatasetMenu.js file for cascade menu in the main search page http://www.genenetwork.org/.
# This script will be run automatically every one hour or manually when database has been changed .

from __future__ import print_function, division

import sys, os

current_file_name = __file__
pathname = os.path.dirname( current_file_name )
abs_path = os.path.abspath(pathname)
sys.path.insert(0, abs_path + '/..')

import MySQLdb
import os
import string
import time
import datetime

from base import template
from base import webqtlConfig

#################################################################################
# input: searchArray, targetValue
# function: retrieve index info of target value in designated array (searchArray)
# output: return index info
##################################################################################
def getIndex(searchArray=None, targetValue=None):
    for index in range(len(searchArray)):
        if searchArray[index][0]==targetValue:
            return index

# build MySql database connection
con = MySQLdb.Connect(db=webqtlConfig.DB_NAME,host=webqtlConfig.MYSQL_SERVER, user=webqtlConfig.DB_USER,passwd=webqtlConfig.DB_PASSWD)
cursor = con.cursor()

# create js_select.js file
fileHandler = open(webqtlConfig.HTMLPATH + 'javascript/selectDatasetMenu.js', 'w')

# define SpeciesString, GroupString, TypeString, DatabasingString, LinkageString for output
# outputSpeciesStr is for building Species Array(sArr) in js file; outputGroupStr is for Group Array(gArr)
# outputTypeStr is for Type Array(tArr); outputDatabaseStr is for Database Array(dArr)
# outputLinkStr is for Linkage Array(lArr)
outputTimeStr ="/* Generated Date : %s , Time : %s */ \n" % (datetime.date.today(),time.strftime("%H:%M ", time.localtime()))
outputTimeStr =""
outputSpeciesStr ='var sArr = [\n{txt:\'\',val:\'\'},\n'
outputGroupStr ='var gArr = [\n{txt:\'\',val:\'\'},\n'
outputTypeStr ='var tArr = [\n{txt:\'\',val:\'\'},\n'
outputDatabaseStr ='var dArr = [\n{txt:\'\',val:\'\'},\n'
outputLinkStr ='var lArr = [\n null,\n'

# built speices array in js file for select menu in the main search page http://www.genenetwork.org/
cursor.execute("select Name, MenuName from Species order by OrderId")
speciesResult = cursor.fetchall()
speciesTotalResult = list(speciesResult)
speciesResultsTotalNum = cursor.rowcount
if speciesResultsTotalNum >0:
    for speciesItem in speciesResult:
        speciesVal = speciesItem[0]
        speciesTxt = speciesItem[1]
        outputSpeciesStr += '{txt:\'%s\',val:\'%s\'},\n'%(speciesTxt,speciesVal)
# 'All Species' option for 'Species' select menu
outputSpeciesStr +='{txt:\'All Species\',val:\'All Species\'}];\n\n'
#speciesTotalResult is a list which inclues all species' options
speciesTotalResult.append(('All Species','All Species'))

# built group array in js file for select menu in the main search page http://www.genenetwork.org/
cursor.execute("select distinct InbredSet.Name, InbredSet.FullName from InbredSet, Species, ProbeFreeze, GenoFreeze, PublishFreeze where InbredSet.SpeciesId= Species.Id and InbredSet.Name != 'BXD300' and (PublishFreeze.InbredSetId = InbredSet.Id or GenoFreeze.InbredSetId = InbredSet.Id or ProbeFreeze.InbredSetId = InbredSet.Id) order by InbredSet.Name")
groupResults = cursor.fetchall()
groupTotalResults = list(groupResults)
groupResultsTotalNum = cursor.rowcount
if groupResultsTotalNum > 0:
    for groupItem in groupResults:
        groupVal = groupItem[0]
        groupTxt = groupItem[1]
        outputGroupStr += '{txt:\'%s\',val:\'%s\'},\n'%(groupTxt,groupVal)
# add 'All Groups' option for 'Group' select menu
outputGroupStr +='{txt:\'All Groups\',val:\'all groups\'}];\n\n'
# groupTotalResults is a list which inclues all groups' options
groupTotalResults.append(('all groups','All Groups'))

# built type array in js file for select menu in the main search page http://www.genenetwork.org/
cross = groupVal
cursor.execute("select distinct Tissue.Name, concat(Tissue.Name, ' mRNA') from ProbeFreeze, ProbeSetFreeze, InbredSet, Tissue where ProbeFreeze.TissueId = Tissue.Id and ProbeFreeze.InbredSetId = InbredSet.Id and ProbeSetFreeze.ProbeFreezeId = ProbeFreeze.Id and ProbeSetFreeze.public > %d order by Tissue.Name" % (webqtlConfig.PUBLICTHRESH))
typeResults = cursor.fetchall()
typeTotalResults = list(typeResults)
typeResultsTotalNum = cursor.rowcount
if typeResultsTotalNum > 0:
    for typeItem in typeResults:
        typeVal = typeItem[0]
        typeTxt = typeItem[1]
        outputTypeStr += '{txt:\'%s\',val:\'%s\'},\n'%(typeTxt,typeVal)
# add 'Phenotypes' and 'Genotypes' options for 'Type' select menu
outputTypeStr +='{txt:\'Phenotypes\',val:\'Phenotypes\'},\n'
outputTypeStr +='{txt:\'Genotypes\',val:\'Genotypes\'}];\n\n'
# typeTotalResults is a list which inclues all types' options
typeTotalResults.append(('Phenotypes','Phenotypes'))
typeTotalResults.append(('Genotypes','Genotypes'))

# built dataset array in js file for select menu in the main search page http://www.genenetwork.org/
tissue = typeVal
cursor.execute("select ProbeSetFreeze.Name, ProbeSetFreeze.FullName from ProbeSetFreeze, ProbeFreeze, InbredSet, Tissue where ProbeSetFreeze.ProbeFreezeId = ProbeFreeze.Id and ProbeFreeze.TissueId = Tissue.Id and ProbeFreeze.InbredSetId = InbredSet.Id and ProbeSetFreeze.public > %d order by ProbeSetFreeze.CreateTime desc" % (webqtlConfig.PUBLICTHRESH))
datasetResults = cursor.fetchall()
datasetTotalResults = list(datasetResults)
datasetResultsTotalNum = cursor.rowcount
if datasetResultsTotalNum > 0:
    for datasetItem in datasetResults:
        datasetVal = datasetItem[0]
        datasetTxt = datasetItem[1]
        outputDatabaseStr += '{txt:\'%s\',val:\'%s\'},\n'%(datasetTxt,datasetVal)

# This part is to built linkage array in js file, the linkage is among Species, Group, Type and Database.
# The format of linkage array is [speciesIndex, groupIndex, typeIndex, databaseIndex]
if speciesResultsTotalNum >0:
    for speciesItem in speciesResult:
        speciesVal = speciesItem[0]
        sIndex = getIndex(searchArray=speciesTotalResult,targetValue=speciesVal)+1

        # retrieve group info based on specie
        cursor.execute("select distinct InbredSet.Name, InbredSet.FullName from InbredSet, Species, ProbeFreeze, GenoFreeze, PublishFreeze where InbredSet.SpeciesId= Species.Id and Species.Name='%s' and InbredSet.Name != 'BXD300' and (PublishFreeze.InbredSetId = InbredSet.Id or GenoFreeze.InbredSetId = InbredSet.Id or ProbeFreeze.InbredSetId = InbredSet.Id) order by InbredSet.Name" % speciesVal)
        groupResults = cursor.fetchall()
        groupResultsNum = cursor.rowcount

        if groupResultsNum > 0:
            for groupItem in groupResults:
                groupVal = groupItem[0]
                gIndex = getIndex(searchArray=groupTotalResults, targetValue=groupVal)+1

                cross = groupVal
                # if group also exists in PublishFreeze table, then needs to add related Published Phenotypes in Database Array(dArr) and Linkage Array(lArr)
                # 'MDP' case is related to 'Mouse Phenome Database'
                cursor.execute("select PublishFreeze.Id from PublishFreeze, InbredSet where PublishFreeze.InbredSetId = InbredSet.Id and InbredSet.Name = '%s'" % cross)
                if (cursor.fetchall()):
                    typeVal = "Phenotypes"
                    if cross=='MDP':
                        datasetTxt = "Mouse Phenome Database"
                    else:
                        datasetTxt = "%s Published Phenotypes" % cross
                    datasetVal = "%sPublish" % cross
                    outputDatabaseStr += '{txt:\'%s\',val:\'%s\'},\n'% (datasetTxt,datasetVal)
                    datasetTotalResults.append(('%s'% datasetVal,'%s' % datasetTxt))

                    tIndex = getIndex(searchArray=typeTotalResults,targetValue=typeVal)+1
                    dIndex = getIndex(searchArray=datasetTotalResults, targetValue=datasetVal)+1
                    outputLinkStr +='[%d,%d,%d,%d],\n'%(sIndex,gIndex,tIndex,dIndex)

                # if group also exists in GenoFreeze table, then needs to add related Genotypes in database Array(dArr)
                cursor.execute("select GenoFreeze.Id from GenoFreeze, InbredSet where GenoFreeze.InbredSetId = InbredSet.Id and InbredSet.Name = '%s'" % cross)
                if (cursor.fetchall()):
                    typeVal = "Genotypes"
                    datasetTxt = "%s Genotypes" % cross
                    datasetVal = "%sGeno" % cross
                    outputDatabaseStr += '{txt:\'%s\',val:\'%s\'},\n'%(datasetTxt,datasetVal)
                    typeTotalResults.append(('Genotypes','Genotypes'))
                    datasetTotalResults.append(('%s'% datasetVal,'%s' % datasetTxt))

                    tIndex = getIndex(searchArray=typeTotalResults,targetValue=typeVal)+1
                    dIndex = getIndex(searchArray=datasetTotalResults, targetValue=datasetVal)+1
                    outputLinkStr +='[%d,%d,%d,%d],\n'%(sIndex,gIndex,tIndex,dIndex)

                # retrieve type(tissue) info based on group
                # if cross is equal to 'BXD', then need to seach for 'BXD' and 'BXD300' InbredSet
                if cross == "BXD":
                    cross2 = "BXD', 'BXD300"
                else:
                    cross2 = cross
                cursor.execute("select distinct Tissue.Name, concat(Tissue.Name, ' mRNA') from ProbeFreeze, ProbeSetFreeze, InbredSet, Tissue where ProbeFreeze.TissueId = Tissue.Id and ProbeFreeze.InbredSetId = InbredSet.Id and InbredSet.Name in ('%s') and ProbeSetFreeze.ProbeFreezeId = ProbeFreeze.Id and ProbeSetFreeze.public > %d order by Tissue.Name" % (cross2, webqtlConfig.PUBLICTHRESH))
                typeResults = cursor.fetchall()
                typeResultsNum = cursor.rowcount

                if typeResultsNum > 0:
                    for typeItem in typeResults:
                        typeVal = typeItem[0]
                        tIndex = getIndex(searchArray=typeTotalResults, targetValue=typeVal)+1
                        # retrieve database(dataset) info based on group(InbredSet) and type(Tissue)
                        tissue = typeVal
                        cursor.execute("select ProbeSetFreeze.Name, ProbeSetFreeze.FullName from ProbeSetFreeze, ProbeFreeze, InbredSet, Tissue where ProbeSetFreeze.ProbeFreezeId = ProbeFreeze.Id and ProbeFreeze.TissueId = Tissue.Id and ProbeFreeze.InbredSetId = InbredSet.Id and InbredSet.Name in ('%s') and Tissue.name = '%s' and ProbeSetFreeze.public > %d order by ProbeSetFreeze.CreateTime desc" % (cross2, tissue, webqtlConfig.PUBLICTHRESH))
                        datasetResults = cursor.fetchall()
                        datasetResultsNum = cursor.rowcount

                        if datasetResultsNum > 0:
                            for datasetItem in datasetResults:
                                datasetVal = datasetItem[0]
                                dIndex = getIndex(searchArray=datasetTotalResults, targetValue=datasetVal)+1
                                outputLinkStr +='[%d,%d,%d,%d],\n'%(sIndex,gIndex,tIndex,dIndex)

# add 'All Phenotypes' option for 'Database' select menu
# for 'All Species'option in 'Species' select menu, 'Database' select menu will show 'All Phenotypes' option
outputDatabaseStr += '{txt:\'%s\',val:\'%s\'}];\n\n'%('All Phenotypes','_allPublish')
datasetTotalResults.append(('_allPublish','All Phenotypes'))

sIndex = getIndex(searchArray=speciesTotalResult,targetValue='All Species')+1
gIndex = getIndex(searchArray=groupTotalResults, targetValue='all groups')+1
tIndex = getIndex(searchArray=typeTotalResults,targetValue='Phenotypes')+1
dIndex = getIndex(searchArray=datasetTotalResults, targetValue='_allPublish')+1
outputLinkStr +='[%d,%d,%d,%d]];\n\n'%(sIndex,gIndex,tIndex,dIndex)

# Combine sArr, gArr, tArr, dArr and lArr output string together
outputStr = outputTimeStr+outputSpeciesStr+outputGroupStr+outputTypeStr+outputDatabaseStr+outputLinkStr
outputStr +='''

/*
*  function: based on different browser use, will have different initial actions;
*  Once the index.html page is loaded, this function will be called
*/
function initialDatasetSelection()
{
        defaultSpecies =getDefaultValue('species');
        defaultSet =getDefaultValue('cross');
        defaultType =getDefaultValue('tissue');
        defaultDB =getDefaultValue('database');

        if (navigator.userAgent.indexOf('MSIE')>=0)
        {
                sOptions = fillOptionsForIE(null,defaultSpecies);
                var menu0 ="<SELECT NAME='species' ID='species' SIZE='1' onChange='fillOptions(\\"species\\");'>"+sOptions+"</Select>";
                document.getElementById('menu0').innerHTML = menu0;

                gOptions = fillOptionsForIE('species',defaultSet);
                var menu1 ="<Select NAME='cross' size=1 id='cross' onchange='fillOptions(\\"cross\\");'>"+gOptions+"</Select><input type=\\"button\\" class=\\"button\\" value=\\"Info\\" onCLick=\\"javascript:crossinfo();\\">";
                document.getElementById('menu1').innerHTML =menu1;

                tOptions = fillOptionsForIE('cross',defaultType);
                var menu2 ="<Select NAME='tissue' size=1 id='tissue' onchange='fillOptions(\\"tissue\\");'>"+tOptions+"</Select>";
                document.getElementById('menu2').innerHTML =menu2;

                dOptions = fillOptionsForIE('tissue',defaultDB);
                var menu3 ="<Select NAME='database' size=1 id='database'>"+dOptions+"</Select><input type=\\"button\\" class=\\"button\\" value=\\"Info\\" onCLick=\\"javascript:databaseinfo();\\">";
                document.getElementById('menu3').innerHTML =menu3;

        }else{
                fillOptions(null);
    }
        searchtip();
}

/*
*  input: selectObjId (designated select menu, such as species, cross, etc... )
*  defaultValue (default Value of species, cross,tissue or database)
*  function: special for IE browser,setting options value for select menu dynamically based on linkage array(lArr),
*  output: options string
*/
function fillOptionsForIE(selectObjId,defaultValue)
{
        var options='';
        if(selectObjId==null)
        {
                var len = sArr.length;
                for (var i=1; i < len; i++) {
                    // setting Species' option
                        if( sArr[i].val==defaultValue){
                                options =options+"<option selected=\\"selected\\" value='"+sArr[i].val+"'>"+sArr[i].txt+"</option>";
                        }else{
                                options =options+"<option value='"+sArr[i].val+"'>"+sArr[i].txt+"</option>";
                        }
                }
        }else if(selectObjId=='species')
        {
                var speciesObj = document.getElementById('species');
                var len = lArr.length;
                var arr = [];
                var idx = 0;
                for (var i=1; i < len; i++) {
                        //get group(cross) info from lArr
                        if(lArr[i][0]==(getIndexByValue('species',speciesObj.value)).toString()&&!Contains(arr,lArr[i][1]))
                        {
                                arr[idx++]=lArr[i][1];
                        }
                }
                idx=0;
                len = arr.length;
                removeOptions("cross");
                for (var i=0; i < len; i++) {
                        // setting Group's option
                        if( gArr[arr[i]].val==defaultValue){
                                options =options+"<option selected=\\"selected\\" value='"+gArr[arr[i]].val+"'>"+gArr[arr[i]].txt+"</option>";
                        }else{
                                options =options+"<option value='"+gArr[arr[i]].val+"'>"+gArr[arr[i]].txt+"</option>";
                        }

                }
        }else if(selectObjId=='cross')
        {
                var speciesObj = document.getElementById('species');
                var groupObj = document.getElementById('cross');
                var len = lArr.length;
                var arr = [];
                var idx = 0;
                for (var i=1; i < len; i++) {
                        //get type(tissue) info from lArr
                        if(lArr[i][0]==(getIndexByValue('species',speciesObj.value)).toString()&&lArr[i][1]==(getIndexByValue('cross',groupObj.value)).toString()&&!Contains(arr,lArr[i][2]))
                        {
                                arr[idx++]=lArr[i][2];
                        }
                }
                idx=0;
                len = arr.length;
                removeOptions("tissue");
                for (var i=0; i < len; i++) {
                        // setting Type's option
                        if( tArr[arr[i]].val==defaultValue){
                                options =options+"<option selected=\\"selected\\" value='"+tArr[arr[i]].val+"'>"+tArr[arr[i]].txt+"</option>";
                        }else{
                                options =options+"<option value='"+tArr[arr[i]].val+"'>"+tArr[arr[i]].txt+"</option>";
                        }
                }

        }else if(selectObjId=='tissue')
        {
                var speciesObj = document.getElementById('species');
                var groupObj = document.getElementById('cross');
                var typeObj = document.getElementById('tissue');

                var len = lArr.length;
                var arr = [];
                var idx = 0;
                for (var i=1; i < len; i++) {
                        //get dataset(database) info from lArr
                        if(lArr[i][0]==(getIndexByValue('species',speciesObj.value)).toString()&&lArr[i][1]==(getIndexByValue('cross',groupObj.value)).toString()&&lArr[i][2]==(getIndexByValue('tissue',typeObj.value)).toString()&&!Contains(arr,lArr[i][3]))
                        {
                                arr[idx++]=lArr[i][3];
                        }
                }
                idx=0;
                len = arr.length;
                removeOptions("database");
                for (var i=0; i < len; i++) {
                        // setting Database's option
                        if( dArr[arr[i]].val==defaultValue){
                                options =options+"<option SELECTED value='"+dArr[arr[i]].val+"'>"+dArr[arr[i]].txt+"</option>";
                        }else{
                                options =options+"<option value='"+dArr[arr[i]].val+"'>"+dArr[arr[i]].txt+"</option>";
                        }
                }
        }
        return options;
}
/*
*  input: selectObjId (designated select menu, such as species, cross, etc... )
*  function: setting options value for select menu dynamically based on linkage array(lArr)
*  output: null
*/
function fillOptions(selectObjId)
{
        if(selectObjId==null)
        {

                var speciesObj = document.getElementById('species');
                var len = sArr.length;
                for (var i=1; i < len; i++) {
                    // setting Species' option
                        speciesObj.options[i-1] = new Option(sArr[i].txt, sArr[i].val);
                }
                updateChocie('species');

        }else if(selectObjId=='species')
        {
                var speciesObj = document.getElementById('species');
                var groupObj = document.getElementById('cross');
                var len = lArr.length;
                var arr = [];
                var idx = 0;
                for (var i=1; i < len; i++) {
                        //get group(cross) info from lArr
                        if(lArr[i][0]==(getIndexByValue('species',speciesObj.value)).toString()&&!Contains(arr,lArr[i][1]))
                        {
                                arr[idx++]=lArr[i][1];
                        }
                }
                idx=0;
                len = arr.length;
                removeOptions("cross");
                for (var i=0; i < len; i++) {
                        // setting Group's option
                        groupObj.options[idx++] = new Option(gArr[arr[i]].txt, gArr[arr[i]].val);
                }
                updateChocie('cross');

        }else if(selectObjId=='cross')
        {
                var speciesObj = document.getElementById('species');
                var groupObj = document.getElementById('cross');
                var typeObj = document.getElementById('tissue');
                var len = lArr.length;
                var arr = [];
                var idx = 0;
                for (var i=1; i < len; i++) {
                        //get type(tissue) info from lArr
                        if(lArr[i][0]==(getIndexByValue('species',speciesObj.value)).toString()&&lArr[i][1]==(getIndexByValue('cross',groupObj.value)).toString()&&!Contains(arr,lArr[i][2]))
                        {
                                arr[idx++]=lArr[i][2];
                        }
                }
                idx=0;
                len = arr.length;
                removeOptions("tissue");
                for (var i=0; i < len; i++) {
                        // setting Type's option
                        typeObj.options[idx++] = new Option(tArr[arr[i]].txt, tArr[arr[i]].val);
                }
                updateChocie('tissue');

        }else if(selectObjId=='tissue')
        {
                var speciesObj = document.getElementById('species');
                var groupObj = document.getElementById('cross');
                var typeObj = document.getElementById('tissue');
                var databaseObj = document.getElementById('database');

                var len = lArr.length;
                var arr = [];
                var idx = 0;
                for (var i=1; i < len; i++) {
                        //get dataset(database) info from lArr
                        if(lArr[i][0]==(getIndexByValue('species',speciesObj.value)).toString()&&lArr[i][1]==(getIndexByValue('cross',groupObj.value)).toString()&&lArr[i][2]==(getIndexByValue('tissue',typeObj.value)).toString()&&!Contains(arr,lArr[i][3]))
                        {
                                arr[idx++]=lArr[i][3];
                        }
                }
                idx=0;
                len = arr.length;
                removeOptions("database");
                for (var i=0; i < len; i++) {
                        // setting Database's option
                        databaseObj.options[idx++] = new Option(dArr[arr[i]].txt, dArr[arr[i]].val);
                }
                updateChocie('database');
        }
}

/*
*  input: arr (targeted array); obj (targeted value)
*  function: check whether targeted array contains targeted value or not
*  output: return true, if array contains targeted value, otherwise return false
*/
function Contains(arr,obj) {
        var i = arr.length;
        while (i--) {
                if (arr[i] == obj) {
                        return true;
                }
        }
        return false;
}

/*
* input: selectObj (designated select menu, such as species, cross, etc... )
* function: clear designated select menu's option
* output: null
*/
function removeOptions(selectObj) {
        if (typeof selectObj != 'object'){
                selectObj = document.getElementById(selectObj);
        }
        var len = selectObj.options.length;
        for (var i=0; i < len; i++)     {
                // clear current selection
                selectObj.options[0] = null;
        }
}

/*
*  input: selectObjId (designated select menu, such as species, cross, etc... )
*         Value: target value
*  function: retrieve Index info of target value in designated array
*  output: index info
*/
function getIndexByValue(selectObjId,val)
{
        if(selectObjId=='species')
        {
                for(var i=1;i<sArr.length;i++){
                        if(sArr[i].val==val)
                                return i;
                }
        }else if(selectObjId=='cross')
        {
                for(var i=1;i<gArr.length;i++)
                        if(gArr[i].val==val)
                                return i;
        }else if(selectObjId=='tissue')
        {
                for(var i=1;i<tArr.length;i++)
                        if(tArr[i].val==val)
                                return i;
        }
        else return;
}

/*
*  input: objId (designated select menu, such as species, cross, etc... )
*                 val(targeted value)
*  function: setting option's selected status for designated select menu based on target value, also update the following select menu in the main search page
*  output: return true if selected status has been set, otherwise return false.
*/
function setChoice(objId,val)
{
        var Obj = document.getElementById(objId);
        var idx=-1;

        for(i=0;i<Obj.options.length;i++){
                if(Obj.options[i].value==val){
                        idx=i;
                        break;
                }
        }

        if(idx>=0){
                //setting option's selected status
                Obj.options[idx].selected=true;
                //update the following select menu
                fillOptions(objId);
        }else{
                Obj.options[0].selected=true;
                fillOptions(objId);
        }
}

// setting option's selected status based on default setting or cookie setting for Species, Group, Type and Database select menu in the main search page http://www.genenetwork.org/
function updateChocie(selectObjId){

        if (selectObjId =='species')
        {
                defaultSpecies= getDefaultValue('species');
                //setting option's selected status
                setChoice('species',defaultSpecies);
        }else if (selectObjId =='cross')
        {
                defaultSet= getDefaultValue('cross');
                //setting option's selected status
                setChoice('cross',defaultSet);
        }else if (selectObjId =='tissue')
        {
                defaultType= getDefaultValue('tissue');
                //setting option's selected status
                setChoice('tissue',defaultType);
        }else if (selectObjId =='database')
        {
                defaultDB= getDefaultValue('database');
                //setting option's selected status
                setChoice('database',defaultDB);
        }
}

//get default value;if cookie exists, then use cookie value, otherwise use default value
function getDefaultValue(selectObjId){
        //define default value
        var defaultSpecies = 'mouse'
        var defaultSet = 'BXD'
        var defaultType = 'Hippocampus'
        var defaultDB = 'HC_M2_0606_P'

        if (selectObjId =='species')
        {
                //if cookie exists, then use cookie value, otherwise use default value
                var cookieSpecies = getCookie('defaultSpecies');
                if(cookieSpecies)
                {
                        defaultSpecies= cookieSpecies;
                }
                return defaultSpecies;
        }else if (selectObjId =='cross'){
                var cookieSet = getCookie('defaultSet');
                if(cookieSet){
                        defaultSet= cookieSet;
                }
                return defaultSet;
        }else if (selectObjId =='tissue'){
                var cookieType = getCookie('defaultType');
                if(cookieType){
                        defaultType= cookieType;
                }
                return defaultType;
        }else if (selectObjId =='database')
        {
                var cookieDB = getCookie('defaultDB');
                if(cookieDB){
                        defaultDB= cookieDB;
                }
                return defaultDB;
        }

}

//setting default value into cookies for the dropdown menus: Species,Group, Type, and Database
function setDefault(thisform){

        setCookie('cookieTest', 'cookieTest', 1);
        var cookieTest = getCookie('cookieTest');
        delCookie('cookieTest');
        if (cookieTest){
                var defaultSpecies = thisform.species.value;
                setCookie('defaultSpecies', defaultSpecies, 10);
                var defaultSet = thisform.cross.value;
                setCookie('defaultSet', defaultSet, 10);
                var defaultType = thisform.tissue.value;
                setCookie('defaultType', defaultType, 10);
                var defaultDB = thisform.database.value;
                setCookie('defaultDB', defaultDB, 10);
                updateChocie('species');
                updateChocie('cross');
                updateChocie('tissue');
                updateChocie('database');
                alert("The current settings are now your default");
        }
        else{
                alert("You need to enable Cookies in your browser.");
        }
}

'''
# write all strings' info into selectDatasetMenu.js file
fileHandler.write(outputStr)
fileHandler.close()
