"""This module contains gn2 decorators"""
import json
import requests
from functools import wraps
from urllib.parse import urljoin
from typing import Dict, Callable

from flask import g, flash, request, url_for, redirect, current_app

from gn3.authentication import AdminRole

from gn2.wqflask.oauth2 import client
from gn2.wqflask.oauth2.session import session_info
from gn2.wqflask.oauth2.checks import user_logged_in
from gn2.wqflask.oauth2.request_utils import process_error


def login_required(pagename: str = ""):
    """Use this for endpoints where login is required"""
    def __build_wrap__(func):
        @wraps(func)
        def wrap(*args, **kwargs):
            if not user_logged_in():
                msg = ("You need to be logged in to access that page."
                       if not bool(pagename) else
                       ("You need to be logged in to access the "
                        f"'{pagename.title()}' page."))
                flash(msg, "alert-warning")
                return redirect("/")
            return func(*args, **kwargs)
        return wrap
    return __build_wrap__


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

class AuthorisationError(Exception):
    """Raise when there is an authorisation issue."""
    def __init__(self, description, user):
        self.description = description
        self.user = user
        super().__init__(self, description, user)

def required_access(access_levels: tuple[str, ...],
                    dataset_key: str = "dataset_name",
                    trait_key: str = "name") -> Callable:
    def __build_access_checker__(func: Callable):
        @wraps(func)
        def __checker__(*args, **kwargs):
            def __error__(err):
                error = process_error(err)
                raise AuthorisationError(
                    f"{error['error']}: {error['error_description']}",
                    session_info()["user"])

            def __success__(priv_info):
                if all(priv in priv_info[0]["privileges"] for priv in access_levels):
                    return func(*args, **kwargs)
                missing = tuple(f"'{priv}'" for priv in access_levels
                                if priv not in priv_info[0]["privileges"])
                raise AuthorisationError(
                    f"Missing privileges: {', '.join(missing)}",
                    session_info()["user"])
            dataset_name = kwargs.get(
                dataset_key,
                request.args.get(dataset_key, request.form.get(dataset_key, "")))
            if not bool(dataset_name):
                raise AuthorisationError(
                    "DeveloperError: Dataset name not provided. It is needed "
                    "for the authorisation checks.",
                    session_info()["user"])
            trait_name = kwargs.get(
                trait_key,
                request.args.get(trait_key, request.form.get(trait_key, "")))
            if not bool(trait_name):
                raise AuthorisationError(
                    "DeveloperError: Trait name not provided. It is needed for "
                    "the authorisation checks.",
                    session_info()["user"])
            return client.post(
                "auth/data/authorisation",
                json={"traits": [f"{dataset_name}::{trait_name}"]}).either(
                    __error__, __success__)
        return __checker__
    return __build_access_checker__
