from gn2.base import data_set
from gn2.base.trait import create_trait
from gn2.base.species import TheSpecies

from gn2.utility import hmac
from gn2.utility.tools import get_setting

from gn2.wqflask.database import database_connection



def clean_xapian_query(query: str) -> str:
    """
    Clean and optimize a Xapian query string by removing filler words,
    and ensuring the query is tailored for optimal results from Fahamu.

    Args:
        query (str): The original Xapian query string.

    Returns:
        str: The cleaned and optimized query string.
    """
    xapian_prefixes = {
        "author",
        "species",
        "group",
        "tissue",
        "dataset",
        "symbol",
        "description",
        "rif",
        "wiki",
    }
    xapian_operators = {"AND", "NOT", "OR", "XOR", "NEAR", "ADJ"}
    range_prefixes = {"mean", "peak", "position", "peakmb", "additive", "year"}
    query_context = ["genes"]
    cleaned_query_parts = []
    for token in query.split():
        if token in xapian_operators:
            continue
        prefix, _, suffix = token.partition(":")
        if ".." in suffix and prefix in range_prefixes:
            continue
        if prefix in xapian_prefixes:
            query_context.insert(0, prefix)
            cleaned_query_parts.append(f"{prefix} {suffix}")
        else:
            cleaned_query_parts.append(prefix)
    cleaned_query = " ".join(cleaned_query_parts)
    context = ",".join(query_context)
    return f"Provide answer on {cleaned_query} context {context}"




def get_species_dataset_trait(self, start_vars):
    if "temp_trait" in list(start_vars.keys()):
        if start_vars['temp_trait'] == "True":
            self.dataset = data_set.create_dataset(
                dataset_name="Temp",
                dataset_type="Temp",
                group_name=start_vars['group'])
        else:
            self.dataset = data_set.create_dataset(start_vars['dataset'])
    else:
        self.dataset = data_set.create_dataset(start_vars['dataset'])
    self.species = TheSpecies(dataset=self.dataset)
    self.this_trait = create_trait(dataset=self.dataset,
                                   name=start_vars['trait_id'],
                                   cellid=None,
                                   get_qtl_info=True)

def get_trait_db_obs(self, trait_db_list):
    if isinstance(trait_db_list, str):
        trait_db_list = trait_db_list.split(",")

    self.trait_list = []
    for trait in trait_db_list:
        data, _separator, hmac_string = trait.rpartition(':')
        data = data.strip()
        assert hmac_string == hmac.hmac_creation(data), "Data tampering?"
        trait_name, dataset_name = data.split(":")[:2]
        if dataset_name == "Temp":
            dataset_ob = data_set.create_dataset(
                dataset_name=dataset_name, dataset_type="Temp",
                group_name=trait_name.split("_")[2])
        else:
            dataset_ob = data_set.create_dataset(dataset_name)
        trait_ob = create_trait(dataset=dataset_ob,
                                name=trait_name,
                                cellid=None)
        if trait_ob:
            self.trait_list.append((trait_ob, dataset_ob))


def get_species_groups():
    """Group each species into a group"""
    _menu = {}
    species, group_name = None, None
    with database_connection(get_setting("SQL_URI")) as conn, conn.cursor() as cursor:
        cursor.execute(
            "SELECT s.MenuName, i.InbredSetName FROM InbredSet i "
            "INNER JOIN Species s ON s.SpeciesId = i.SpeciesId "
            "ORDER BY i.SpeciesId ASC, i.Name ASC"
        )
        for species, group_name in cursor.fetchall():
            if species in _menu:
                if _menu.get(species):
                    _menu = _menu[species].append(group_name)
                else:
                    _menu[species] = [group_name]
        return [{"species": key,
                 "groups": value} for key, value in
                list(_menu.items())]
