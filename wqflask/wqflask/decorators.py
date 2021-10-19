"""This module contains gn2 decorators"""
import hashlib
import hmac
import redis

from flask import current_app, g
from typing import Dict
from functools import wraps

import json
import requests


def create_hmac(data: str, secret: str) -> str:
    return hmac.new(bytearray(secret, "latin-1"),
                    bytearray(data, "utf-8"),
                    hashlib.sha1).hexdigest()[:20]


def login_required(f):
    """Use this for endpoints where login is required"""
    @wraps(f)
    def wrap(*args, **kwargs):
        user_id = (g.user_session.record.get(b"user_id",
                                        b"").decode("utf-8") or
                   g.user_session.record.get("user_id", ""))
        redis_conn = redis.from_url(current_app.config["REDIS_URL"],
                                    decode_responses=True)
        if not redis_conn.hget("users", user_id):
            return "You need to be logged in!", 401
        return f(*args, **kwargs)
    return wrap


def edit_access_required(f):
    """Use this for endpoints where admins are required"""
    @wraps(f)
    def wrap(*args, **kwargs):
        resource_id: str = ""
        if kwargs.get("inbredset_id"):  # data type: dataset-publish
            resource_id = create_hmac(
                data=("dataset-publish:"
                      f"{kwargs.get('inbredset_id')}:"
                      f"{kwargs.get('name')}"),
                secret=current_app.config.get("SECRET_HMAC_CODE"))
        if kwargs.get("dataset_name"):  # data type: dataset-probe
            resource_id = create_hmac(
                data=("dataset-probeset:"
                      f"{kwargs.get('dataset_name')}"),
                secret=current_app.config.get("SECRET_HMAC_CODE"))
        response: Dict = {}
        try:
            _user_id = g.user_session.record.get(b"user_id",
                                                 "").decode("utf-8")
            response = json.loads(
                requests.get(GN_PROXY_URL + "available?resource="
                                f"{resource_id}&user={_user_id}").content)
        except:
            response = {}

        if "edit" not in response.get("data", []):
            return "You need to be admin", 401
        return f(*args, **kwargs)
    return wrap
