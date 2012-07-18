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

from __future__ import print_function, division

from pprint import pformat as pf
from collections import namedtuple

import requests

from dbFunction import webqtlDatabaseFunction
import SharingBody

import logging
logging.basicConfig(filename="/tmp/flask_gn_log", level=logging.INFO)

_log = logging.getLogger("search")
_ch = logging.StreamHandler()
_log.addHandler(_ch)



#########################################
#      Sharing Info
#########################################
class SharingInfo(object):

    def __init__(self, GN_AccessionId, InfoPageName):
        print("In SharingInfo")
        self.GN_AccessionId = GN_AccessionId
        self.InfoPageName = InfoPageName

    def getInfo(self):
        cursor = webqtlDatabaseFunction.getCursor()
        if (not cursor):
            return

        field_names = """Id, GEO_Series, Status, Title, Organism, Experiment_Type,
                Summary, Overall_Design, Contributor, Citation, Submission_Date,
                Contact_Name, Emails, Phone, URL, Organization_Name, Department,
                Laboratory, Street, City, State, ZIP, Country, Platforms,
                Samples, Species, Normalization, InbredSet, InfoPageName,
                DB_Name, Organism_Id, InfoPageTitle, GN_AccesionId, Tissue,
                AuthorizedUsers, About_Cases, About_Tissue, About_Download,
                About_Array_Platform, About_Data_Values_Processing,
                Data_Source_Acknowledge, Progreso """

        # We can use string interpolation here cause we own the string
        sql = """select %s from InfoFiles where """ % (field_names)
        if self.GN_AccessionId:
            sql += "GN_AccesionId = %s"
            cursor.execute(sql, self.GN_AccessionId)
        elif self.InfoPageName:
            sql += "InfoPageName = %s"
            cursor.execute(sql, self.InfoPageName)
        else:
            raise Exception('No correct parameter found')
        info = cursor.fetchone()

        info = todict(field_names, info)

        # fetch datasets file list
        filelist = []
        if info["GN_AccesionId"]:
            url = "http://atlas.uthsc.edu/scandatasets.php?GN_AccesionId=%s" % (
                info["GN_AccesionId"])
            try:
                response = requests.get(url)
            except Exception as why:
                log.exception("Problem conneting to:", url)
            if response:
                data = response.text
                filelist = data.split()

        return info, filelist


    def getBody(self, infoupdate=""):
        info, filelist = self.getInfo()
        if filelist:
            htmlfilelist = '<ul style="line-height:160%;">\n'
            for i in range(len(filelist)):
                if i%2==0:
                    filename = filelist[i]
                    filesize = filelist[i+1]
                    htmlfilelist += "<li>"
                    htmlfilelist += '<a href="ftp://atlas.uthsc.edu/users/shared/Genenetwork/GN%s/%s">%s</a>' % (self.GN_AccessionId, filename, filename)
                    htmlfilelist += '&nbsp;&nbsp;&nbsp;'
                    #r=re.compile(r'(?<=\d)(?=(\d\d\d)+(?!\d))')
                    #htmlfilelist += '[%s&nbsp;B]' % r.sub(r',',filesize)
                    if 12 < len(filesize):
                        filesize=filesize[0:-12]
                        filesize += ' T'
                    elif 9 < len(filesize):
                        filesize=filesize[0:-9]
                        filesize += ' G'
                    elif 6 < len(filesize):
                        filesize=filesize[0:-6]
                        filesize += ' M'
                    elif 3 < len(filesize):
                        filesize=filesize[0:-3]
                        filesize += ' K'
                    htmlfilelist += '[%sB]' % filesize
                    htmlfilelist += "</li>\n"
            htmlfilelist += "</ul>"
        else:
            htmlfilelist = "Data sets are not available or are not public yet."

        return info, htmlfilelist
        #return SharingBody.sharinginfo_body_string % (info[31], info[32], infoupdate, info[32], info[1], info[3], info[30], info[4], info[27], info[33], info[2], info[23], info[26], info[11], info[15], info[16], info[18], info[19], info[20], info[21], info[22], info[13], info[12], info[14], info[14], htmlfilelist, info[6], info[35], info[36], info[37], info[38], info[39], info[40], info[5], info[7], info[8], info[9], info[10], info[17], info[24])


def todict(fields, values):
    """Converts sql results into a user friendly dictionary"""
    new_dict = {}
    fields = fields.split(",")
    for counter, field in enumerate(fields):
        field = field.strip()
        value = values[counter]
        if isinstance(value, str):
            value = unicode(value, "utf-8")
        new_dict[field] = value
    return new_dict
