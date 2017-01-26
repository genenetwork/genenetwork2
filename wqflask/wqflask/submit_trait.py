from __future__ import print_function, division

from flask import Flask, g

from pprint import pformat as pf

def get_species_groups():

    species_query = "SELECT SpeciesId, MenuName FROM Species"

    species_ids_and_names = g.db.execute(species_query).fetchall()

    
    species_and_groups = []
    for species_id, species_name in species_ids_and_names:
        this_species_groups = {}
        this_species_groups['species'] = species_name
        groups_query = "SELECT InbredSetName FROM InbredSet WHERE SpeciesId = %s" % (species_id)       
        groups = [group[0] for group in g.db.execute(groups_query).fetchall()]
                       
        this_species_groups['groups'] = groups
        species_and_groups.append(this_species_groups)
    
    return species_and_groups