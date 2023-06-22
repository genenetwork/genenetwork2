"DatasetType class ..."

import json
import requests
from typing import Optional, Dict


from redis import Redis
from flask import current_app as app

from utility.tools import get_setting
from wqflask.database import database_connection


class DatasetType:
    """Create a dictionary of samples where the value is set to Geno,
    Publish or ProbeSet. E.g.

        {'AD-cases-controls-MyersGeno': 'Geno',
         'AD-cases-controls-MyersPublish': 'Publish',
         'AKXDGeno': 'Geno',
         'AXBXAGeno': 'Geno',
         'AXBXAPublish': 'Publish',
         'Aging-Brain-UCIPublish': 'Publish',
         'All Phenotypes': 'Publish',
         'B139_K_1206_M': 'ProbeSet',
         'B139_K_1206_R': 'ProbeSet' ...
        }
        """

    def __init__(self, redis_conn):
        "Initialise the object"
        self.datasets = {}
        self.data = {}
        # self.redis_instance = redis_instance
        data = redis_conn.get("dataset_structure")
        if data:
            self.datasets = json.loads(data)
        else:
            # ZS: I don't think this should ever run unless Redis is
            # emptied
            try:
                data = json.loads(requests.get(
                    get_setting(app, "GN2_BASE_URL") + "/api/v_pre1/gen_dropdown",
                    timeout=5).content)
                for _species in data['datasets']:
                    for group in data['datasets'][_species]:
                        for dataset_type in data['datasets'][_species][group]:
                            for dataset in data['datasets'][_species][group][dataset_type]:
                                short_dataset_name = dataset[1]
                                if dataset_type == "Phenotypes":
                                    new_type = "Publish"
                                elif dataset_type == "Genotypes":
                                    new_type = "Geno"
                                else:
                                    new_type = "ProbeSet"
                                self.datasets[short_dataset_name] = new_type
            except Exception:  # Do nothing
                pass

            redis_conn.set("dataset_structure", json.dumps(self.datasets))
        self.data = data

    def set_dataset_key(self, t, name, redis_conn, db_cursor):
        """If name is not in the object's dataset dictionary, set it, and
        update dataset_structure in Redis
        args:
          t: Type of dataset structure which can be: 'mrna_expr', 'pheno',
             'other_pheno', 'geno'
          name: The name of the key to inserted in the datasets dictionary

        """
        sql_query_mapping = {
            'mrna_expr': ("SELECT ProbeSetFreeze.Id FROM "
                          "ProbeSetFreeze WHERE "
                          "ProbeSetFreeze.Name = %s "),
            'pheno': ("SELECT InfoFiles.GN_AccesionId "
                      "FROM InfoFiles, PublishFreeze, InbredSet "
                      "WHERE InbredSet.Name = %s AND "
                      "PublishFreeze.InbredSetId = InbredSet.Id AND "
                      "InfoFiles.InfoPageName = PublishFreeze.Name"),
            'other_pheno': ("SELECT PublishFreeze.Name "
                            "FROM PublishFreeze, InbredSet "
                            "WHERE InbredSet.Name = %s AND "
                            "PublishFreeze.InbredSetId = InbredSet.Id"),
            'geno': ("SELECT GenoFreeze.Id FROM GenoFreeze WHERE "
                     "GenoFreeze.Name = %s ")
        }

        dataset_name_mapping = {
            "mrna_expr": "ProbeSet",
            "pheno": "Publish",
            "other_pheno": "Publish",
            "geno": "Geno",
        }

        group_name = name
        if t in ['pheno', 'other_pheno']:
            group_name = name.replace("Publish", "")

        db_cursor.execute(sql_query_mapping[t], (group_name,))
        if db_cursor.fetchone():
            self.datasets[name] = dataset_name_mapping[t]
            redis_conn.set(
                "dataset_structure", json.dumps(self.datasets))
            return True


    def __call__(self, name, redis_conn, db_cursor):
        if name not in self.datasets:
            for t in ["mrna_expr", "pheno", "other_pheno", "geno"]:
                # This has side-effects, with the end result being a
                # truth-y value
                if(self.set_dataset_key(t, name, redis_conn, db_cursor)):
                    break
        # Return None if name has not been set
        return self.datasets.get(name, None)
