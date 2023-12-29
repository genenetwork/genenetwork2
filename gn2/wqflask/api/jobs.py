import uuid
from datetime import datetime

from redis import Redis
from pymonad.io import IO
from flask import Blueprint, render_template

from gn2.jobs.jobs import job

jobs = Blueprint("jobs", __name__)

@jobs.route("/debug/<uuid:job_id>")
def debug_job(job_id: uuid.UUID):
    """Display job data to assist in debugging."""
    from gn2.utility.tools import REDIS_URL # Avoids circular import error

    def __stream_to_lines__(stream):
        removables = (
            "Set global log level to", "runserver.py: ******",
            "APPLICATION_ROOT:", "DB_", "DEBUG:", "ELASTICSEARCH_", "ENV:",
            "EXPLAIN_TEMPLATE_LOADING:", "GEMMA_", "GENENETWORK_FILES",
            "GITHUB_", "GN2_", "GN3_", "GN_", "HOME:", "JSONIFY_", "JS_",
            "JSON_", "LOG_", "MAX_", "ORCID_", "PERMANENT_", "PLINK_",
            "PREFERRED_URL_SCHEME", "PRESERVE_CONTEXT_ON_EXCEPTION",
            "PROPAGATE_EXCEPTIONS", "REAPER_COMMAND", "REDIS_URL", "SECRET_",
            "SECURITY_", "SEND_FILE_MAX_AGE_DEFAULT", "SERVER_", "SESSION_",
            "SMTP_", "SQL_", "TEMPLATES_", "TESTING:", "TMPDIR", "TRAP_",
            "USE_", "WEBSERVER_")
        return tuple(filter(
            lambda line: not any(line.startswith(item) for item in removables),
            stream.split("\n")))

    def __fmt_datetime(val):
        return datetime.strptime(val, "%Y-%m-%dT%H:%M:%S.%f").strftime(
            "%A, %d %B %Y at %H:%M:%S.%f")

    def __render_debug_page__(job):
        job_details = {key.replace("-", "_"): val for key,val in job.items()}
        return render_template(
            "jobs/debug.html",
            **{
                **job_details,
                "request_received_time": __fmt_datetime(
                    job_details["request_received_time"]),
                "stderr": __stream_to_lines__(job_details["stderr"]),
                "stdout": __stream_to_lines__(job_details["stdout"])
            })

    with Redis.from_url(REDIS_URL, decode_responses=True) as rconn:
        the_job = job(rconn, job_id)

    return the_job.maybe(
        render_template("jobs/no-such-job.html", job_id=job_id),
        lambda job: __render_debug_page__(job))
