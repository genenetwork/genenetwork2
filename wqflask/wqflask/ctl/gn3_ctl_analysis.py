import requests

from utility.tools import GN3_LOCAL_URL


def run_ctl():
    """function to make an api call
    to gn3 and run ctl"""

    ctl_api = f"{GN3_LOCAL_URL}/api/wgcna/run_wgcna"

    response = requests.post(ctl_api, json={

    })

    # todo check for errors

    return response.json()
