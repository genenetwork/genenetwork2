"""Utilities that act on responses before they are sent back."""
from flask import Response, send_from_directory as flask_send_from_directory


def enforce_utf8_charset(resp: Response) -> Response:
    """Enforce utf-8 character set for responses"""
    resp.headers["Content-Type"] = "; ".join(tuple(
        part.strip() for part in resp.headers["Content-Type"].split(";")
        if not part.strip().startswith("charset=")) + ("charset=utf-8"))
    return resp


def send_from_directory(*args, **kwargs):
    """Wrapper around flask's `send_from_directory` that ensures the responses
    use the utf-8 character set."""
    return enforce_utf8_charset(flask_send_from_directory(*args, **kwargs))
