"""This module contains gn2 decorators"""
from flask import g
from typing import Dict
from functools import wraps
from utility.hmac import hmac_creation

import json
import requests


def edit_access_required(f):
    """Use this for endpoints where admins are required"""
    @wraps(f)
    def wrap(*args, **kwargs):
        resource_id: str = ""
        if kwargs.get("inbredset_id"):  # data type: dataset-publish
            resource_id = hmac_creation("dataset-publish:"
                                        f"{kwargs.get('inbredset_id')}:"
                                        f"{kwargs.get('name')}")
        if kwargs.get("dataset_name"):  # data type: dataset-probe
            resource_id = hmac_creation("dataset-probeset:"
                                        f"{kwargs.get('dataset_name')}")
        response: Dict = {}
        try:
            _user_id = g.user_session.record.get(b"user_id",
                                                 "").decode("utf-8")
            response = json.loads(
                requests.get("http://localhost:8080/"
                             "available?resource="
                             f"{resource_id}&user={_user_id}").content)
        except:
            response = {}
        if "edit" not in response.get("data", []):
            return "You need to be admin", 401
        return f(*args, **kwargs)
    return wrap
