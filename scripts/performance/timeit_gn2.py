import sys
import timeit


print(timeit.timeit(
"""
class UserSessionSimulator():
    def __init__(self, user_id):
        self._user_id = user_id

    @property
    def user_id(self):
        return self._user_id


def dump_sample_data(dataset_name, trait_id):
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

print(dump_sample_data("HLCPublish", "10001"))
""",
    setup="""
# Required Evils!
from flask import g
from wqflask import app

from wqflask.database import database_connection
from wqflask.show_trait import show_trait
""",
    number=int(sys.argv[1])
))
