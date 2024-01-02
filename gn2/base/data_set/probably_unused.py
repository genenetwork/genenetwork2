"Functions that are probably unused in the code"

import pickle as pickle

from gn2.wqflask.database import database_connection
from gn2.utility.tools import get_setting

def create_datasets_list():
    if USE_REDIS:
        key = "all_datasets"
        result = redis_conn.get(key)

        if result:
            datasets = pickle.loads(result)

    if result is None:
        datasets = list()
        type_dict = {'Publish': 'PublishFreeze',
                     'ProbeSet': 'ProbeSetFreeze',
                     'Geno': 'GenoFreeze'}

        for dataset_type in type_dict:
            with database_connection(get_setting("SQL_URI")) as conn, conn.cursor() as cursor:
                cursor.execute("SELECT Name FROM %s",
                               (type_dict[dataset_type],))
                results = cursor.fetchall(query)
                if results:
                    for result in results:
                        datasets.append(
                            create_dataset(result.Name, dataset_type))
        if USE_REDIS:
            redis_conn.set(key, pickle.dumps(datasets, pickle.HIGHEST_PROTOCOL))
            redis_conn.expire(key, 60 * 60)

    return datasets
