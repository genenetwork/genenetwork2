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
# Last updated by GeneNetwork Core Team 2010/10/20

from __future__ import division, print_function

from flask import request

from htmlgen import HTMLgen2 as HT

from base import webqtlConfig
from utility import webqtlUtil
from base.webqtlTrait import webqtlTrait
from base.templatePage import templatePage
from DataEditingPage import DataEditingPage



class ShowTraitPage(DataEditingPage):

    def __init__(self, fd, traitInfos = None):

        #templatePage.__init__(self, fd)

        if not self.openMysql():
            return

        #TD_LR = HT.TD(height=200,width="100%",bgColor='#eeeeee')
        print("j2")
        # When is traitInfos used?
        if traitInfos:
            print("j2.2")
            database, ProbeSetID, CellID = traitInfos
        else:
            print("j2.3")
            print("fd is:", fd)
            database = fd['database'][0]
            ProbeSetID = fd['ProbeSetID'][0]
            print("j2.4")
            CellID = fd.get('CellID')
            print("j2.6")

        # We're no longer wrapping this in an exception. If we fail, let's fail hard
        # Log it and fix it
        #try:
        print("j3")
        thisTrait = webqtlTrait(db=database, name=ProbeSetID, cellid= CellID, cursor=self.cursor)
        #except:
        #       heading = "Trait Data and Analysis Form"
        #       detail = ["The trait isn't available currently."]
        #       self.error(heading=heading,detail=detail,error="Error")
        #       return
        print("j4")
        if thisTrait.db.type == "ProbeSet":

            self.cursor.execute('''SELECT Id, Name, FullName, confidentiality, AuthorisedUsers
                                    FROM ProbeSetFreeze WHERE Name = "%s"''' %  database)

            indId, indName, indFullName, confidential, AuthorisedUsers = self.cursor.fetchall()[0]

            if confidential == 1:
                access_to_confidential_dataset = 0

                #for the dataset that confidentiality is 1
                #1. 'admin' and 'root' can see all of the dataset
                #2. 'user' can see the dataset that AuthorisedUsers contains his id(stored in the Id field of User table)
                if webqtlConfig.USERDICT[self.privilege] > webqtlConfig.USERDICT['user']:
                    access_to_confidential_dataset = 1
                else:
                    AuthorisedUsersList=AuthorisedUsers.split(',')
                    if AuthorisedUsersList.__contains__(self.userName):
                        access_to_confidential_dataset = 1

                if not access_to_confidential_dataset:
                    #Error, Confidential Database
                    heading = "Show Database"
                    detail = ["The %s database you selected is not open to the public \
                    at this time, please go back and select other database." % indFullName]
                    self.error(heading=heading,detail=detail,error="Confidential Database")
                    return
        print("environ:", request.environ)

        # Becuase of proxying remote_addr is probably localhost, so we first try for
        # HTTP_X_FORWARDED_FOR
        user_ip = request.environ.get('HTTP_X_FORWARDED_FOR') or request.remote_addr   # in old app was fd.remote_ip
        print("user_ip is:", user_ip)
        query = "SELECT count(id) FROM AccessLog WHERE ip_address = %s and \
                        UNIX_TIMESTAMP()-UNIX_TIMESTAMP(accesstime)<86400"
        self.cursor.execute(query,user_ip)
        daycount = self.cursor.fetchall()
        if daycount:
            daycount = daycount[0][0]
            if daycount > webqtlConfig.DAILYMAXIMUM:
                heading = "Retrieve Data"
                detail = ['For security reasons, the maximum access to a database is \
                %d times per day per ip address. You have reached the limit, please \
                try it again tomorrow.' % webqtlConfig.DAILYMAXIMUM]
                self.error(heading=heading,detail=detail)
                return
            else:
                pass
        else:
            pass

        if thisTrait.db.type != 'ProbeSet' and thisTrait.cellid:
            heading = "Retrieve Data"
            detail = ['The Record you requested doesn\'t exist!']
            self.error(heading=heading,detail=detail)
            return

        #XZ: Aug 23, 2010: I commented out this block because this feature is not used anymore
        # check if animal information are available
        """
        self.cursor.execute('''
                                        SELECT
                                                SampleXRef.ProbeFreezeId
                                        FROM
                                                SampleXRef, ProbeSetFreeze
                                        WHERE
                                                SampleXRef.ProbeFreezeId = ProbeSetFreeze.ProbeFreezeId AND
                                                ProbeSetFreeze.Name = "%s"
                                        ''' % thisTrait.db.name)

        sampleId = self.cursor.fetchall()
        if sampleId:
                thisTrait.strainInfo = 1
        else:
                thisTrait.strainInfo = None
        """

        ##identification, etc.
        fd.identification = '%s : %s' % (thisTrait.db.shortname,ProbeSetID)
        thisTrait.returnURL = webqtlConfig.CGIDIR + webqtlConfig.SCRIPTFILE + '?FormID=showDatabase&database=%s\
                &ProbeSetID=%s&RISet=%s&parentsf1=on' %(database, ProbeSetID, fd['RISet'])

        if CellID:
            fd.identification = '%s/%s'%(fd.identification, CellID)
            thisTrait.returnURL = '%s&CellID=%s' % (thisTrait.returnURL, CellID)

        #retrieve trait information
        try:
            thisTrait.retrieveInfo()
            thisTrait.retrieveData()
            self.updMysql()
            self.cursor.execute("insert into AccessLog(accesstime,ip_address) values(Now(),%s)", user_ip)
            self.openMysql()
        except Exception as why:
            print("Got an exception:", why)
            heading = "Retrieve Data"
            detail = ["The information you requested is not avaiable at this time."]
            self.error(heading=heading, detail=detail)
            return

        ##read genotype file
        fd.RISet = thisTrait.riset
        fd.readGenotype()

        if webqtlUtil.ListNotNull(map(lambda x:x.var, thisTrait.data.values())):
            fd.displayVariance = 1
            fd.varianceDispName = 'SE'
            fd.formID = 'varianceChoice'

        #self.dict['body']= thisTrait
        DataEditingPage.__init__(self, fd, thisTrait)
        #self.dict['title'] = '%s: Display Trait' % fd.identification
