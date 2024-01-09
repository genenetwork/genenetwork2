"""Job management functions"""

import sys
import json
import shlex
import subprocess
from uuid import UUID, uuid4

from redis import Redis
from pymonad.maybe import Maybe

JOBS_NAMESPACE="gn2:jobs" # The namespace where jobs are kept

class NoSuchJob(Exception):
    """Raised if a given job does not exist"""

    def __init__(self, job_id: UUID):
        """Initialise the exception object."""
        super().__init__(f"Could not find a job with the id '{job_id}'.")

class InvalidJobCommand(Exception):
    """Raised if the job command is invalid."""

    def __init__(self, job_command: list[str]):
        """Initialise the exception object."""
        super().__init__(f"The job command '{job_command}' is invalid.")

def job_namespace(job_id: UUID):
    return f"{JOBS_NAMESPACE}:{job_id}"

def job(redis_conn: Redis, job_id: UUID):
    job = redis_conn.hgetall(job_namespace(job_id))
    return Maybe(job, bool(job))

def status(the_job: Maybe) -> str:
    return job.maybe("NOT-FOUND", lambda val: val.get("status", "NOT-FOUND"))

def command(job: Maybe) -> list[str]:
    return job.maybe(
        ["NOT-FOUND"], lambda val: shlex.split(val.get("command", "NOT-FOUND")))

def __validate_command__(job_command):
    try:
        assert isinstance(job_command, list), "Not a list"
        assert all((isinstance(val, str) for val in job_command))
        assert all((len(val) > 1 for val in job_command))
    except AssertionError as assert_err:
        raise InvalidJobCommand(job_command)

def queue(redis_conn: Redis, job: dict) -> UUID:
    command = job["command"]
    __validate_command__(command)
    job_id = uuid4()
    redis_conn.hset(
        name=job_namespace(job_id),
        mapping={"job_id": str(job_id), **job, "command": shlex.join(command)})
    return job_id

def run(job_id: UUID, redis_uri: str):
    command = [
        sys.executable, "-m", "gn2.scripts.run_external",
        f"--redis-uri={redis_uri}", "run-job", str(job_id)]
    print(f"COMMAND: {shlex.join(command)}")
    subprocess.Popen(command)

def completed_successfully(job):
    return (
        job.get("status") == "completed" and
        job.get("completion-status") == "success")

def completed_erroneously(job):
    return (
        job.get("status") == "completed" and
        job.get("completion-status") == "error")
