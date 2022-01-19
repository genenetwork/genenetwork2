import requests

from utility.tools import GN3_LOCAL_URL


def parse_form_data(form_data: dict):
    """function to parse/validate form data
    input: dict containing required data
    output: dict with parsed data

    """

    form_data["nperm"] = int(form_data["nperm"])
    form_data["significance"] = float(int(form_data["significance"]))
    form_data["strategy"] = form_data["strategy"].capitalize()

    return form_data


def run_ctl():
    """function to make an api call
    to gn3 and run ctl"""

    ctl_api = f"{GN3_LOCAL_URL}/api/wgcna/run_wgcna"

    response = requests.post(ctl_api, json={

    })

    # todo check for errors

    return response.json()
