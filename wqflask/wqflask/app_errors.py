"""Handle errors at the application's top-level"""
import datetime
import traceback

import werkzeug
from flask import request, render_template, current_app as app

from wqflask.decorators import AuthorisationError

def handle_generic_exceptions(exc):
    err_msg = str(exc)
    now = datetime.datetime.utcnow()
    time_str = now.strftime('%l:%M%p UTC %b %d, %Y')
    # get the stack trace and send it to the logger
    exc_type, exc_value, exc_traceback = sys.exc_info()
    formatted_lines = (f"{request.url} ({time_str}) \n"
                       f"{traceback.format_exc()}")
    _message_templates = {
        werkzeug.exceptions.NotFound: (
            f"404: Not Found: {time_str}: {request.url}"),
        werkzeug.exceptions.BadRequest: (
            f"400: Bad Request: {time_str}: {request.url}"),
        werkzeug.exceptions.RequestTimeout: (
            f"408: Request Timeout: {time_str}: {request.url}")
    }
    # Default to the lengthy stack trace!
    app.logger.error(_message_templates.get(exc_type, formatted_lines))
    # Handle random animations
    # Use a cookie to have one animation on refresh
    animation = request.cookies.get(err_msg[:32])
    if not animation:
        animation = random.choice([fn for fn in os.listdir(
            "./wqflask/static/gif/error") if fn.endswith(".gif")])

    resp = make_response(render_template("error.html", message=err_msg,
                                         stack={formatted_lines},
                                         error_image=animation,
                                         version=app.config["GN_VERSION"]))
    resp.set_cookie(err_msg[:32], animation)
    return resp

def handle_authorisation_error(exc: AuthorisationError):
    """Handle AuthorisationError if not handled anywhere else."""
    app.logger.error(exc)
    return render_template(
        "authorisation_error.html", error_type=type(exc).__name__, error=exc)
