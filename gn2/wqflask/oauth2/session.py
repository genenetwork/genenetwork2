"""Deal with user sessions"""
from uuid import UUID, uuid4
from datetime import datetime
from typing import Any, Optional, TypedDict

from flask import request, session
from pymonad.either import Left, Right, Either

class UserDetails(TypedDict):
    """Session information relating specifically to the user."""
    user_id: UUID
    name: str
    email: str
    token: Either
    logged_in: bool

class SessionInfo(TypedDict):
    """All Session information we save."""
    session_id: UUID
    user: UserDetails
    anon_id: UUID
    user_agent: str
    ip_addr: str
    masquerade: Optional[UserDetails]

__SESSION_KEY__ = "GN::2::session_info" # Do not use this outside this module!!

def clear_session_info():
    """Clears the session."""
    session.pop(__SESSION_KEY__)

def save_session_info(sess_info: SessionInfo) -> SessionInfo:
    """Save `session_info`."""
    # TODO: if it is an existing session, verify that certain important security
    #       bits have not changed before saving.
    # old_session_info = session.get(__SESSION_KEY__)
    # if bool(old_session_info):
    #     if old_session_info["user_agent"] == request.headers.get("User-Agent"):
    #         session[__SESSION_KEY__] = sess_info
    #         return sess_info
    #     # request session verification
    #     return verify_session(sess_info)
    # New session
    session[__SESSION_KEY__] = sess_info
    return sess_info

def session_info() -> SessionInfo:
    """Retrieve the session information"""
    anon_id = uuid4()
    return save_session_info(
        session.get(__SESSION_KEY__, {
            "session_id": uuid4(),
            "user": {
                "user_id": anon_id,
                "name": "Anonymous User",
                "email": "anon@ymous.user",
                "token": Left("INVALID-TOKEN"),
                "logged_in": False
            },
            "anon_id": anon_id,
            "user_agent": request.headers.get("User-Agent"),
            "ip_addr": request.environ.get("HTTP_X_FORWARDED_FOR",
                                           request.remote_addr),
            "masquerading": None
        }))

def expired():
    the_session = session_info()
    def __expired__(token):
        return datetime.now() > datetime.fromtimestamp(token["expires_at"])
    return the_session["user"]["token"].either(
        lambda left: False,
        __expired__)

def set_user_token(token: str) -> SessionInfo:
    """Set the user's token."""
    info = session_info()
    return save_session_info({
        **info, "user": {**info["user"], "token": Right(token)}})

def set_user_details(userdets: UserDetails) -> SessionInfo:
    """Set the user details information"""
    return save_session_info({**session_info(), "user": userdets})

def user_token() -> Either:
    """Retrieve the user token."""
    return session_info()["user"]["token"]

def set_masquerading(masq_info):
    """Save the masquerading user information."""
    orig_user = session_info()["user"]
    return save_session_info({
        **session_info(),
        "user": {
            "user_id": UUID(masq_info["masquerade_as"]["user"]["user_id"]),
            "name": masq_info["masquerade_as"]["user"]["name"],
            "email": masq_info["masquerade_as"]["user"]["email"],
            "token": Right(masq_info["masquerade_as"]["token"]),
            "logged_in": True
        },
        "masquerading": orig_user
    })

def unset_masquerading():
    """Restore the original session."""
    the_session = session_info()
    return save_session_info({
        **the_session,
        "user": the_session["masquerading"],
        "masquerading": None
    })
