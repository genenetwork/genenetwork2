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

class GraphPage:

    def __init__(self, imagefile, mapfile):
        # open and read the image map file
        try:
            mapData = open(mapfile).read()
        except:
            mapData =  "<p><b>Unable to load image map with trait links</b></p>"

        self.content = '''%s
        <img border="0" alt="the graph" src="%s" usemap="#webqtlGraph" />
        ''' % (mapData, imagefile)

    def writeToFile(self, filename):
        """
        Output the contents of this HTML page to a file
        """
        handle = open(filename, "w")
        handle.write(self.content)
        handle.close()
