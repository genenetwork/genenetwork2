"""This module contains gn2 decorators"""
import hashlib
import hmac
import redis

from flask import current_app, g
from typing import Dict
from urllib.parse import urljoin
from functools import wraps
from wqflask.access_roles import AdminRole
from wqflask.access_roles import DataRole

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
    """Use this for endpoints where people with admin or edit privileges are required"""
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
        if kwargs.get("resource_id"):  # The resource_id is already provided
            resource_id = kwargs.get("resource_id")
        response: Dict = {}
        try:
            _user_id = g.user_session.record.get(b"user_id",
                                                 "").decode("utf-8")
            response = json.loads(
                requests.get(urljoin(
                    current_app.config.get("GN2_PROXY"),
                    ("available?resource="
                     f"{resource_id}&user={_user_id}"))).content)
        except:
            response = {}
        if max([DataRole(role) for role in response.get(
                "data", ["no-access"])]) < DataRole.EDIT:
            return "You need to have edit access", 401
        return f(*args, **kwargs)
    return wrap


def edit_admins_access_required(f):
    """Use this for endpoints where ownership of a resource is required"""
    @wraps(f)
    def wrap(*args, **kwargs):
        resource_id: str = kwargs.get("resource_id", "")
        response: Dict = {}
        try:
            _user_id = g.user_session.record.get(b"user_id",
                                                 "").decode("utf-8")
            response = json.loads(
                requests.get(urljoin(
                    current_app.config.get("GN2_PROXY"),
                    ("available?resource="
                     f"{resource_id}&user={_user_id}"))).content)
        except:
            response = {}
        if max([AdminRole(role) for role in response.get(
                "data", ["not-admin"])]) >= AdminRole.EDIT_ADMINS:
            return "You need to have edit-admins access", 401
        return f(*args, **kwargs)
    return wrap

