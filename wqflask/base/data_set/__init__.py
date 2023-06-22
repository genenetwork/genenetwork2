"The data_set package ..."

# builtins imports
import json
import pickle as pickle

# 3rd-party imports
from redis import Redis
from flask import current_app as app

# local imports
from .dataset import DataSet
from base import webqtlConfig
from utility.tools import get_setting_bool
from .datasettype import DatasetType
from .tempdataset import TempDataSet
from .datasetgroup import DatasetGroup
from .utils import query_table_timestamp
from .genotypedataset import GenotypeDataSet
from .phenotypedataset import PhenotypeDataSet
from .mrnaassaydataset import MrnaAssayDataSet
from wqflask.database import database_connection

# Used by create_database to instantiate objects
# Each subclass will add to this

DS_NAME_MAP = {
    "Temp": "TempDataSet",
    "Geno": "GenotypeDataSet",
    "Publish": "PhenotypeDataSet",
    "ProbeSet": "MrnaAssayDataSet"
}

def __dataset_type__(dataset_name):
    """Get dataset type."""
    if "Temp" in dataset_name:
        return "Temp"
    if "Geno" in dataset_name:
        return "Geno"
    if "Publish" in dataset_name:
        return "Publish"
    return "ProbeSet"

def create_dataset(dataset_name, dataset_type=None,
                   get_samplelist=True, group_name=None, redis_conn=Redis()):
    dataset_type = dataset_type or __dataset_type__(dataset_name)

    dataset_ob = DS_NAME_MAP[dataset_type]
    dataset_class = globals()[dataset_ob]
    if dataset_type == "Temp":
        return dataset_class(dataset_name, get_samplelist, group_name)
    else:
        return dataset_class(dataset_name, get_samplelist)

def datasets(group_name, this_group=None, redis_conn=Redis()):
    key = "group_dataset_menu:v2:" + group_name
    dataset_menu = []
    with database_connection() as conn, conn.cursor() as cursor:
        cursor.execute('''
            (SELECT '#PublishFreeze',PublishFreeze.FullName,PublishFreeze.Name
            FROM PublishFreeze,InbredSet
            WHERE PublishFreeze.InbredSetId = InbredSet.Id
                and InbredSet.Name = '%s'
            ORDER BY PublishFreeze.Id ASC)
            UNION
            (SELECT '#GenoFreeze',GenoFreeze.FullName,GenoFreeze.Name
            FROM GenoFreeze, InbredSet
            WHERE GenoFreeze.InbredSetId = InbredSet.Id
                and InbredSet.Name = '%s')
            UNION
            (SELECT Tissue.Name, ProbeSetFreeze.FullName,ProbeSetFreeze.Name
            FROM ProbeSetFreeze, ProbeFreeze, InbredSet, Tissue
            WHERE ProbeSetFreeze.ProbeFreezeId = ProbeFreeze.Id
                and ProbeFreeze.TissueId = Tissue.Id
                and ProbeFreeze.InbredSetId = InbredSet.Id
                and InbredSet.Name like %s
            ORDER BY Tissue.Name, ProbeSetFreeze.OrderList DESC)
            ''' % (group_name,
                group_name,
                "'" + group_name + "'"))
        the_results = cursor.fetchall()

    sorted_results = sorted(the_results, key=lambda kv: kv[0])

    # ZS: This is kind of awkward, but need to ensure Phenotypes show up before Genotypes in dropdown
    pheno_inserted = False
    geno_inserted = False
    for dataset_item in sorted_results:
        tissue_name = dataset_item[0]
        dataset = dataset_item[1]
        dataset_short = dataset_item[2]
        if tissue_name in ['#PublishFreeze', '#GenoFreeze']:
            if tissue_name == '#PublishFreeze' and (dataset_short == group_name + 'Publish'):
                dataset_menu.insert(
                    0, dict(tissue=None, datasets=[(dataset, dataset_short)]))
                pheno_inserted = True
            elif pheno_inserted and tissue_name == '#GenoFreeze':
                dataset_menu.insert(
                    1, dict(tissue=None, datasets=[(dataset, dataset_short)]))
                geno_inserted = True
            else:
                dataset_menu.append(
                    dict(tissue=None, datasets=[(dataset, dataset_short)]))
        else:
            tissue_already_exists = False
            for i, tissue_dict in enumerate(dataset_menu):
                if tissue_dict['tissue'] == tissue_name:
                    tissue_already_exists = True
                    break

            if tissue_already_exists:
                dataset_menu[i]['datasets'].append((dataset, dataset_short))
            else:
                dataset_menu.append(dict(tissue=tissue_name,
                                         datasets=[(dataset, dataset_short)]))

    if get_setting_bool(app, "USE_REDIS"):
        redis_conn.set(key, pickle.dumps(dataset_menu, pickle.HIGHEST_PROTOCOL))
        redis_conn.expire(key, 60 * 5)

    if this_group != None:
        this_group._datasets = dataset_menu
        return this_group._datasets
    else:
        return dataset_menu
