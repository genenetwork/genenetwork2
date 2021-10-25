from gn3.db.species import get_all_species
def gen_dropdown_json(conn):
    """Generates and outputs (as json file) the data for the main dropdown menus on
    the home page
    """
    species = get_all_species(conn)
    groups = get_groups(species, conn)
    types = get_types(groups, conn)
    datasets = get_datasets(types, conn)
    return dict(species=species,
                groups=groups,
                types=types,
                datasets=datasets)


def get_groups(species, conn):
    """Build groups list"""
    groups = {}
    with conn.cursor() as cursor:
        for species_name, _species_full_name in species:
            groups[species_name] = []
            cursor.execute(
                ("SELECT InbredSet.Name, InbredSet.FullName, "
                 "IFNULL(InbredSet.Family, 'None') "
                 "FROM InbredSet, Species WHERE Species.Name = '{}' "
                 "AND InbredSet.SpeciesId = Species.Id GROUP by "
                 "InbredSet.Name ORDER BY IFNULL(InbredSet.FamilyOrder, "
                 "InbredSet.FullName) ASC, IFNULL(InbredSet.Family, "
                 "InbredSet.FullName) ASC, InbredSet.FullName ASC, "
                 "InbredSet.MenuOrderId ASC")
                .format(species_name))
            results = cursor.fetchall()
            for result in results:
                family_name = "Family:" + str(result[2])
                groups[species_name].append(
                    [str(result[0]), str(result[1]), family_name])
    return groups


def get_types(groups, conn):
    """Build types list"""
    types = {}

    for species, group_dict in list(groups.items()):
        types[species] = {}
        for group_name, _group_full_name, _family_name in group_dict:
            if phenotypes_exist(group_name, conn):
                types[species][group_name] = [
                    ("Phenotypes", "Traits and Cofactors", "Phenotypes")]
            if genotypes_exist(group_name, conn):
                if group_name in types[species]:
                    types[species][group_name] += [
                        ("Genotypes", "DNA Markers and SNPs", "Genotypes")]
                else:
                    types[species][group_name] = [
                        ("Genotypes", "DNA Markers and SNPs", "Genotypes")]
            if group_name in types[species]:
                types_list = build_types(species, group_name, conn)
                if len(types_list) > 0:
                    types[species][group_name] += types_list
            else:
                types_list = build_types(species, group_name, conn)
                if len(types_list) > 0:
                    types[species][group_name] = types_list
                else:
                    types[species].pop(group_name, None)
                    groups[species] = list(
                        group for group in groups[species]
                        if group[0] != group_name)
    return types


def phenotypes_exist(group_name, conn):
    results = []
    with conn.cursor() as cursor:
        cursor.execute(
            ("SELECT Name FROM PublishFreeze "
             "WHERE PublishFreeze.Name = "
             "'{}'").format(group_name + "Publish"))
        results = cursor.fetchone()
    return bool(results)


def genotypes_exist(group_name, conn):
    with conn.cursor() as cursor:
        cursor.execute(
            ("SELECT Name FROM GenoFreeze " +
             "WHERE GenoFreeze.Name = '{}'").format(
                 group_name + "Geno"))
        results = cursor.fetchone()
        return bool(results)


def build_types(species, group, conn):
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
    with conn.cursor() as cursor:
        cursor.execute(query)
        for result in cursor.fetchall():
            if bool(result):
                these_datasets = build_datasets(species,
                                                group, result[0], conn)
                if len(these_datasets) > 0:
                    results.append([str(result[0]), str(result[0]),
                                    "Molecular Traits"])
    return results


def get_datasets(types, conn):
    """Build datasets list"""
    datasets = {}
    for species, group_dict in list(types.items()):
        datasets[species] = {}
        for group, type_list in list(group_dict.items()):
            datasets[species][group] = {}
            for type_name in type_list:
                these_datasets = build_datasets(species, group,
                                                type_name[0], conn)
                if bool(these_datasets):
                    datasets[species][group][type_name[0]] = these_datasets

    return datasets


def build_datasets(species, group, type_name, conn):
    """Gets dataset names from database"""
    dataset_text = dataset_value = None
    datasets = []
    with conn.cursor() as cursor:
        if type_name == "Phenotypes":
            cursor.execute(
                ("SELECT InfoFiles.GN_AccesionId, PublishFreeze.Name, "
                 "PublishFreeze.FullName FROM InfoFiles, PublishFreeze, "
                 "InbredSet WHERE InbredSet.Name = '{}' AND "
                 "PublishFreeze.InbredSetId = InbredSet.Id AND "
                 "InfoFiles.InfoPageName = PublishFreeze.Name "
                 "ORDER BY PublishFreeze.CreateTime ASC").format(group))
            results = cursor.fetchall()
            if bool(results):
                for result in results:
                    dataset_id = str(result[0])
                    dataset_value = str(result[1])
                    dataset_text = str(result[2])
                    if group == 'MDP':
                        dataset_text = "Mouse Phenome Database"

                    datasets.append([dataset_id, dataset_value, dataset_text])
            else:
                cursor.execute(
                    ("SELECT PublishFreeze.Name, PublishFreeze.FullName "
                     "FROM PublishFreeze, InbredSet "
                     "WHERE InbredSet.Name = '{}' AND "
                     "PublishFreeze.InbredSetId = InbredSet.Id "
                     "ORDER BY PublishFreeze.CreateTime ASC")
                    .format(group))
                result = cursor.fetchone()
                dataset_id = "None"
                dataset_value = str(result[0])
                dataset_text = str(result[1])
                datasets.append([dataset_id, dataset_value, dataset_text])

        elif type_name == "Genotypes":
            cursor.execute(
                ("SELECT InfoFiles.GN_AccesionId "
                 "FROM InfoFiles, GenoFreeze, InbredSet "
                 "WHERE InbredSet.Name = '{}' AND "
                 "GenoFreeze.InbredSetId = InbredSet.Id AND "
                 "InfoFiles.InfoPageName = GenoFreeze.ShortName "
                 "ORDER BY GenoFreeze.CreateTime "
                 "DESC").format(group))
            results = cursor.fetchone()
            dataset_id = "None"
            if bool(results):
                dataset_id = str(results[0])

            dataset_value = "%sGeno" % group
            dataset_text = "%s Genotypes" % group
            datasets.append([dataset_id, dataset_value, dataset_text])

        else:  # for mRNA expression/ProbeSet
            cursor.execute(
                ("SELECT ProbeSetFreeze.Id, ProbeSetFreeze.Name, "
                 "ProbeSetFreeze.FullName FROM ProbeSetFreeze, "
                 "ProbeFreeze, InbredSet, Tissue, Species WHERE "
                 "Species.Name = '{0}' AND Species.Id = "
                 "InbredSet.SpeciesId AND InbredSet.Name = '{1}' "
                 "AND ProbeSetFreeze.ProbeFreezeId = ProbeFreeze.Id "
                 "AND Tissue.Name = '{2}' AND ProbeFreeze.TissueId = "
                 "Tissue.Id AND ProbeFreeze.InbredSetId = InbredSet.Id "
                 "AND ProbeSetFreeze.public > 0 "
                 "ORDER BY -ProbeSetFreeze.OrderList DESC, "
                 "ProbeSetFreeze.CreateTime "
                 "DESC").format(species, group, type_name))
            results = cursor.fetchall()
            datasets = []
            for dataset_info in results:
                this_dataset_info = []
                for info in dataset_info:
                    this_dataset_info.append(str(info))
                datasets.append(this_dataset_info)

    return datasets
