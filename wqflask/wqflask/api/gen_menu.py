from flask import g


def gen_dropdown_json():
    """Generates and outputs (as json file) the data for the main dropdown menus on
    the home page
    """

    species = get_species()
    groups = get_groups(species)
    types = get_types(groups)
    datasets = get_datasets(types)

    data = dict(species=species,
                groups=groups,
                types=types,
                datasets=datasets)

    return data


def get_species():
    """Build species list"""
    results = g.db.execute(
        "SELECT Name, MenuName FROM Species ORDER BY OrderId").fetchall()
    return [[name, menu_name] for name, menu_name in results]


def get_groups(species):
    """Build groups list"""
    groups = {}
    for species_name, _species_full_name in species:
        groups[species_name] = []

        results = g.db.execute(
            ("SELECT InbredSet.Name, InbredSet.FullName, "
             "IFNULL(InbredSet.Family, 'None') "
             "FROM InbredSet, Species WHERE Species.Name = '{}' "
             "AND InbredSet.SpeciesId = Species.Id GROUP by InbredSet.Name "
             "ORDER BY IFNULL(InbredSet.FamilyOrder, InbredSet.FullName) "
             "ASC, IFNULL(InbredSet.Family, InbredSet.FullName) ASC, "
             "InbredSet.FullName ASC, InbredSet.MenuOrderId ASC")
            .format(species_name)).fetchall()

        for result in results:
            family_name = "Family:" + str(result[2])
            groups[species_name].append(
                [str(result[0]), str(result[1]), family_name])

    return groups


def get_types(groups):
    """Build types list"""
    types = {}

    for species, group_dict in list(groups.items()):
        types[species] = {}
        for group_name, _group_full_name, _family_name in group_dict:
            if phenotypes_exist(group_name):
                types[species][group_name] = [
                    ("Phenotypes", "Traits and Cofactors", "Phenotypes")]
            if genotypes_exist(group_name):
                if group_name in types[species]:
                    types[species][group_name] += [
                        ("Genotypes", "DNA Markers and SNPs", "Genotypes")]
                else:
                    types[species][group_name] = [
                        ("Genotypes", "DNA Markers and SNPs", "Genotypes")]
            if group_name in types[species]:
                types_list = build_types(species, group_name)
                if len(types_list) > 0:
                    types[species][group_name] += types_list
            else:
                types_list = build_types(species, group_name)
                if len(types_list) > 0:
                    types[species][group_name] = types_list
                else:
                    types[species].pop(group_name, None)
                    groups[species] = list(
                        group for group in groups[species]
                        if group[0] != group_name)
    return types


def phenotypes_exist(group_name):
    results = g.db.execute(
        ("SELECT Name FROM PublishFreeze "
         "WHERE PublishFreeze.Name = "
         "'{}'").format(group_name + "Publish")).fetchone()
    return bool(results)


def genotypes_exist(group_name):
    results = g.db.execute(
        ("SELECT Name FROM GenoFreeze " +
         "WHERE GenoFreeze.Name = '{}'").format(group_name + "Geno")).fetchone()
    return bool(results)


def build_types(species, group):
    """Fetches tissues

    Gets the tissues with data for this species/group
    (all types except phenotype/genotype are tissues)

    """

    query = ("SELECT DISTINCT Tissue.Name "
             "FROM ProbeFreeze, ProbeSetFreeze, InbredSet, "
             "Tissue, Species WHERE Species.Name = '{0}' "
             "AND Species.Id = InbredSet.SpeciesId AND "
             "InbredSet.Name = '{1}' AND ProbeFreeze.TissueId = "
             "Tissue.Id AND ProbeFreeze.InbredSetId = InbredSet.Id "
             "AND ProbeSetFreeze.ProbeFreezeId = ProbeFreeze.Id "
             "ORDER BY Tissue.Name").format(species, group)

    results = []
    for result in g.db.execute(query).fetchall():
        if bool(result):
            these_datasets = build_datasets(species, group, result[0])
            if len(these_datasets) > 0:
                results.append([str(result[0]), str(result[0]),
                                "Molecular Traits"])

    return results


def get_datasets(types):
    """Build datasets list"""
    datasets = {}
    for species, group_dict in list(types.items()):
        datasets[species] = {}
        for group, type_list in list(group_dict.items()):
            datasets[species][group] = {}
            for type_name in type_list:
                these_datasets = build_datasets(species, group, type_name[0])
                if bool(these_datasets):
                    datasets[species][group][type_name[0]] = these_datasets

    return datasets


def build_datasets(species, group, type_name):
    """Gets dataset names from database"""
    dataset_text = dataset_value = None
    datasets = []
    if type_name == "Phenotypes":
        results = g.db.execute(
            ("SELECT InfoFiles.GN_AccesionId, PublishFreeze.Name, "
             "PublishFreeze.FullName FROM InfoFiles, PublishFreeze, "
             "InbredSet WHERE InbredSet.Name = '{}' AND "
             "PublishFreeze.InbredSetId = InbredSet.Id AND "
             "InfoFiles.InfoPageName = PublishFreeze.Name "
             "ORDER BY PublishFreeze.CreateTime ASC").format(group)).fetchall()
        if bool(results):
            for result in results:
                dataset_id = str(result[0])
                dataset_value = str(result[1])
                dataset_text = str(result[2])
                if group == 'MDP':
                    dataset_text = "Mouse Phenome Database"

                datasets.append([dataset_id, dataset_value, dataset_text])
        else:
            result = g.db.execute(
                ("SELECT PublishFreeze.Name, PublishFreeze.FullName "
                 "FROM PublishFreeze, InbredSet "
                 "WHERE InbredSet.Name = '{}' AND "
                 "PublishFreeze.InbredSetId = InbredSet.Id "
                 "ORDER BY PublishFreeze.CreateTime ASC")
                .format(group)).fetchone()

            dataset_id = "None"
            dataset_value = str(result[0])
            dataset_text = str(result[1])
            datasets.append([dataset_id, dataset_value, dataset_text])

    elif type_name == "Genotypes":
        results = g.db.execute(
            ("SELECT InfoFiles.GN_AccesionId " +
             "FROM InfoFiles, GenoFreeze, InbredSet "
             + "WHERE InbredSet.Name = '{}' AND "
             + "GenoFreeze.InbredSetId = InbredSet.Id AND "
             + "InfoFiles.InfoPageName = GenoFreeze.ShortName "
             + "ORDER BY GenoFreeze.CreateTime DESC").format(group)).fetchone()

        dataset_id = "None"
        if bool(results):
            dataset_id = str(results[0])

        dataset_value = "%sGeno" % group
        dataset_text = "%s Genotypes" % group
        datasets.append([dataset_id, dataset_value, dataset_text])

    else:  # for mRNA expression/ProbeSet
        results = g.db.execute(
            ("SELECT ProbeSetFreeze.Id, ProbeSetFreeze.Name, "
             "ProbeSetFreeze.FullName FROM ProbeSetFreeze, "
             "ProbeFreeze, InbredSet, Tissue, Species WHERE "
             "Species.Name = '{0}' AND Species.Id = "
             "InbredSet.SpeciesId AND InbredSet.Name = '{1}' "
             "AND ProbeSetFreeze.ProbeFreezeId = ProbeFreeze.Id "
             "AND Tissue.Name = '{2}' AND ProbeFreeze.TissueId = "
             "Tissue.Id AND ProbeFreeze.InbredSetId = InbredSet.Id "
             "AND ProbeSetFreeze.public > 0 "
             "ORDER BY -ProbeSetFreeze.OrderList DESC, ProbeSetFreeze.CreateTime DESC").format(species, group, type_name)).fetchall()

        datasets = []
        for dataset_info in results:
            this_dataset_info = []
            for info in dataset_info:
                this_dataset_info.append(str(info))
            datasets.append(this_dataset_info)

    return datasets
