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

from db.call import fetch1
from utility.tools import USE_GN_SERVER

from utility.logger import getLogger
logger = getLogger(__name__)

###########################################################################
# output: cursor instance
# function: connect to database and return cursor instance
###########################################################################

def retrieve_species(group):
    """Get the species of a group (e.g. returns string "mouse" on "BXD"

    """
    result = fetch1("select Species.Name from Species, InbredSet where InbredSet.Name = '%s' and InbredSet.SpeciesId = Species.Id" % (group), "/cross/" + group + ".json", lambda r: (r["species"],))[0]
    logger.debug("retrieve_species result:", result)
    return result


def retrieve_species_id(group):

    result = fetch1("select SpeciesId from InbredSet where Name = '%s'" % (group), "/cross/" + group + ".json", lambda r: (r["species_id"],))[0]
    logger.debug("retrieve_species_id result:", result)
    return result
