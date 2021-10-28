"""This module contains gn2 decorators"""
import redis

from flask import current_app, g, redirect, request, url_for
from typing import Dict
from urllib.parse import urljoin
from functools import wraps
from wqflask.access_roles import AdminRole
from wqflask.access_roles import DataRole

import json
import requests


def login_required(f):
    """Use this for endpoints where login is required"""
    @wraps(f)
    def wrap(*args, **kwargs):
        user_id = ((g.user_session.record.get(b"user_id") or
                    b"").decode("utf-8")
                   or g.user_session.record.get("user_id") or "")
        redis_conn = redis.from_url(current_app.config["REDIS_URL"],
                                    decode_responses=True)
        if not redis_conn.hget("users", user_id):
            return "You need to be logged in!", 401
        return f(*args, **kwargs)
    return wrap


def edit_access_required(f):
    """Use this for endpoints where people with admin or edit privileges
are required"""
    @wraps(f)
    def wrap(*args, **kwargs):
        resource_id: str = ""
        if request.args.get("resource-id"):
            resource_id = request.args.get("resource-id")
        elif kwargs.get("resource_id"):
            resource_id = kwargs.get("resource_id")
        response: Dict = {}
        try:
            user_id = ((g.user_session.record.get(b"user_id") or
                        b"").decode("utf-8")
                       or g.user_session.record.get("user_id") or "")
            response = json.loads(
                requests.get(urljoin(
                    current_app.config.get("GN2_PROXY"),
                    ("available?resource="
                     f"{resource_id}&user={user_id}"))).content)
        except:
            response = {}
        if max([DataRole(role) for role in response.get(
                "data", ["no-access"])]) < DataRole.EDIT:
            return redirect(url_for("no_access_page"))
        return f(*args, **kwargs)
    return wrap


def edit_admins_access_required(f):
    """Use this for endpoints where ownership of a resource is required"""
    @wraps(f)
    def wrap(*args, **kwargs):
        resource_id: str = kwargs.get("resource_id", "")
        response: Dict = {}
        try:
            user_id = ((g.user_session.record.get(b"user_id") or
                        b"").decode("utf-8")
                       or g.user_session.record.get("user_id") or "")
            response = json.loads(
                requests.get(urljoin(
                    current_app.config.get("GN2_PROXY"),
                    ("available?resource="
                     f"{resource_id}&user={user_id}"))).content)
        except:
            response = {}
        if max([AdminRole(role) for role in response.get(
                "admin", ["not-admin"])]) < AdminRole.EDIT_ADMINS:
            return redirect(url_for("no_access_page"))
        return f(*args, **kwargs)
    return wrap
