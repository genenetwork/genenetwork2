import sys
sys.path.insert(0, './')
import urllib.parse

import numpy as np
import pandas as pd

from flask import Flask, g, request

from gn2.wqflask import app
from gn2.wqflask.database import database_connection
from gn2.utility.tools import get_setting


def create_dataframe(input_file):
    with open(input_file) as f:
        ncols = len(f.readline().split("\t"))

    input_array = np.loadtxt(open(
        input_file, "rb"), delimiter="\t", skiprows=1, usecols=list(range(1, ncols)))
    return pd.DataFrame(input_array)

# This function taken from https://github.com/ShawnLYU/Quantile_Normalize


def quantileNormalize(df_input):
    df = df_input.copy()
    # compute rank
    dic = {}
    for col in df:
        dic.update({col: sorted(df[col])})
    sorted_df = pd.DataFrame(dic)
    rank = sorted_df.mean(axis=1).tolist()
    # sort
    for col in df:
        t = np.searchsorted(np.sort(df[col]), df[col])
        df[col] = [rank[i] for i in t]
    return df


def set_data(cursor, dataset_name):
    orig_file = "/home/zas1024/cfw_data/" + dataset_name + ".txt"

    sample_list = []
    with open(orig_file, 'r') as orig_fh, open('/home/zas1024/cfw_data/quant_norm.csv', 'r') as quant_fh:
        for i, (line1, line2) in enumerate(zip(orig_fh, quant_fh)):
            trait_dict = {}
            sample_list = []
            if i == 0:
                sample_names = line1.split('\t')[1:]
            else:
                trait_name = line1.split('\t')[0]
                for i, sample in enumerate(sample_names):
                    this_sample = {
                        "name": sample,
                        "value": line1.split('\t')[i + 1],
                        "qnorm": line2.split('\t')[i + 1]
                    }
                    sample_list.append(this_sample)
                query = """SELECT Species.SpeciesName, InbredSet.InbredSetName, ProbeSetFreeze.FullName
                           FROM Species, InbredSet, ProbeSetFreeze, ProbeFreeze, ProbeSetXRef, ProbeSet
                           WHERE Species.Id = InbredSet.SpeciesId and
                                 InbredSet.Id = ProbeFreeze.InbredSetId and
                                 ProbeFreeze.Id = ProbeSetFreeze.ProbeFreezeId and
                                 ProbeSetFreeze.Name = '%s' and
                                 ProbeSetFreeze.Id = ProbeSetXRef.ProbeSetFreezeId and
                                 ProbeSetXRef.ProbeSetId = ProbeSet.Id and
                                 ProbeSet.Name = '%s'""" % (dataset_name, line1.split('\t')[0])
                cursor.execute(query)
                result_info = cursor.fetchone()

                yield {
                    "_index": "traits",
                    "_type": "trait",
                    "_source": {
                        "name": trait_name,
                        "species": result_info[0],
                        "group": result_info[1],
                        "dataset": dataset_name,
                        "dataset_fullname": result_info[2],
                        "samples": sample_list,
                        "transform_types": "qnorm"
                    }
                }


if __name__ == '__main__':
    with database_connection(get_setting("SQL_URI")) as conn:
        with conn.cursor() as cursor:
            success, _ = bulk(es, set_data(cursor, sys.argv[1]))

            response = es.search(
                index="traits", doc_type="trait", body={
                    "query": {"match": {"name": "ENSMUSG00000028982"}}
                }
            )

            print(response)
