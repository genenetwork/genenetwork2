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

from wqflask.database import database_connection


def retrieve_species(group):
    """Get the species of a group (e.g. returns string "mouse" on "BXD"

    """
    with database_connection() as conn, conn.cursor() as cursor:
        cursor.execute(
            "SELECT Species.Name FROM Species, InbredSet WHERE InbredSet.Name = %s AND InbredSet.SpeciesId = Species.Id",
            (group,))
        return cursor.fetchone()[0]
    return result


def retrieve_species_id(group):
    with database_connection() as conn, conn.cursor() as cursor:
        cursor.execute("SELECT SpeciesId FROM InbredSet WHERE Name = %s",
                       (group,))
        return cursor.fetchone()[0]
