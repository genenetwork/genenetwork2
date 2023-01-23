import json
import os
import sys
import time

from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from functools import partial

# Required Evils!
from flask import g
from wqflask import app

from wqflask.api.gen_menu import gen_dropdown_json
from wqflask.show_trait import show_trait
from wqflask.database import database_connection
from wqflask.search_results import SearchResultPage


class UserSessionSimulator():
    def __init__(self, user_id):
        self._user_id = user_id

    @property
    def user_id(self):
        return self._user_id


def dump_sample_data(dataset_name, trait_id):
    """Given a DATASET_NAME e.g. 'BXDPublish' and a TRAIT_ID
    e.g. '10007', dump the sample data as json object"""
    with database_connection() as conn, conn.cursor() as cursor:
        sample_data = {"headers": ["Name", "Value", "SE"], "data": []}

        with app.app_context():
            g.user_session = UserSessionSimulator(None)
            data = show_trait.ShowTrait(
                cursor, user_id=None,
                kw={
                    "trait_id": trait_id,
                    "dataset": dataset_name
                }
            )
            attributes = data.js_data.get("attributes")
            for id_ in attributes:
                sample_data["headers"].append(attributes[id_].name)
            for sample in data.js_data.get("sample_lists")[0]:
                sample_data["data"].append(
                    [
                        sample.name,
                        sample.value or 'x',
                        sample.variance or 'x',
                        *[str(sample.extra_attributes.get(str(key), "x"))
                          for key in attributes],
                    ])
            return sample_data


def fetch_all_traits(species, group, type_, dataset):
    with app.app_context():
        g.user_session = UserSessionSimulator(None)
        for result in SearchResultPage({
                "species": species,
                "group": group,
                "type": type_,
                "dataset": dataset,
                "search_terms_or": "*",
        }).trait_list:
            yield result.get('name') or result.get('display_name')


def dump_json(base_dir, dataset_name, trait):
    print(f"\033[FDumping: {dataset_name}/{trait}]")
    with open(os.path.join(base_dir, f"{trait}.json"), "w") as f:
        json.dump(dump_sample_data(dataset_name, trait), f)


def dump_dataset(target_dir, species, group_name, dataset_type, dataset):
    start = time.perf_counter()
    dataset_name = dataset[1]
    if not os.path.isdir(
            BASE_DIR := os.path.join(
                target_dir,
                dataset_name
            )
    ):
        os.makedirs(BASE_DIR)
    _l = len(f"Dumping {dataset_name} into {target_dir}:")
    print(f"""
{'='*_l}
Dumping {dataset_name} into {sys.argv[1]}:
{'='*_l}
""")
    with ThreadPoolExecutor() as executor:
        executor.map(
            partial(
                dump_json,
                BASE_DIR,
                dataset_name
            ),
            fetch_all_traits(
                species=species,
                group=group_name,
                type_=dataset_type,
                dataset=dataset_name
            )
        )
    print(f"\033[FDONE DUMPING: {BASE_DIR} !!")
    finish = time.perf_counter()
    print(f"It took {finish-start: .2f} second(s) to finish")


def main():
    # Dump all sampledata into a given directory
    with database_connection() as conn:
        for species, group in gen_dropdown_json(conn).get("datasets").items():
            for group_name, type_ in group.items():
                for dataset_type, datasets in type_.items():
                    with ProcessPoolExecutor() as p_exec:
                        p_exec.map(
                            partial(
                                dump_dataset,
                                sys.argv[1],
                                species,
                                group_name,
                                dataset_type
                            ),
                            datasets
                        )


if __name__ == "__main__":
    main()
