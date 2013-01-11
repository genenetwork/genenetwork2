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
        self.fd = fd

        # This sets self.cursor
        assert self.openMysql(), "No database"

        # When is traitInfos used?
        if traitInfos:
            database, ProbeSetID, CellID = traitInfos
        else:
            print("fd is:", fd)
            database = fd['database']
            ProbeSetID = fd['ProbeSetID']

            CellID = fd.get('CellID')
      

        thisTrait = webqtlTrait(db=database, name=ProbeSetID, cellid=CellID, cursor=self.cursor)
        
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
            

        if thisTrait.db.type != 'ProbeSet' and thisTrait.cellid:
            heading = "Retrieve Data"
            detail = ['The Record you requested doesn\'t exist!']
            self.error(heading=heading,detail=detail)
            return

        ##identification, etc.
        fd.identification = '%s : %s' % (thisTrait.db.shortname,ProbeSetID)
        thisTrait.returnURL = webqtlConfig.CGIDIR + webqtlConfig.SCRIPTFILE + '?FormID=showDatabase&database=%s\
                &ProbeSetID=%s&RISet=%s&parentsf1=on' %(database, ProbeSetID, fd['RISet'])

        if CellID:
            fd.identification = '%s/%s'%(fd.identification, CellID)
            thisTrait.returnURL = '%s&CellID=%s' % (thisTrait.returnURL, CellID)

        thisTrait.retrieveInfo()
        thisTrait.retrieveData()
        self.updMysql()
        self.cursor.execute("insert into AccessLog(accesstime,ip_address) values(Now(),%s)", user_ip)
        self.openMysql()


        ##read genotype file
        fd.RISet = thisTrait.riset
        fd.readGenotype()

        #if webqtlUtil.ListNotNull(map(lambda x:x.var, thisTrait.data.values())):
        if any([x.variance for x in thisTrait.data.values()]):
            fd.display_variance = True
            fd.formID = 'varianceChoice'

        DataEditingPage.__init__(self, fd, thisTrait)
