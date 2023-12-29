"""
Run jobs in external processes.
"""

import os
import sys
import shlex
import argparse
import traceback
import subprocess
from uuid import UUID
from time import sleep
from datetime import datetime
from urllib.parse import urlparse
from tempfile import TemporaryDirectory

# import psutil
from redis import Redis

import gn2.jobs.jobs as jobs

def print_help(args, parser):
    print(parser.format_help())

def UUID4(val):
    return UUID(val)

def redis_connection(parsed_url):
    return Redis.from_url(
        f"redis://{parsed_url.netloc}{parsed_url.path}", decode_responses=True)

def update_status(redis_conn: Redis, job_id: UUID, value: str):
    "Update the job's status."
    redis_conn.hset(jobs.job_namespace(job_id), key="status", value=value)

def __update_stdout_stderr__(
        redis_conn: Redis, job_id: UUID, bytes_read: bytes, stream: str):
    job = jobs.job(redis_conn, job_id)
    if job.is_nothing():
        raise jobs.NoSuchJob(job_id)

    job = job.maybe({}, lambda x: x)
    redis_conn.hset(
        jobs.job_namespace(job_id), key=stream,
        value=(job.get(stream, "") + bytes_read.decode("utf-8")))

def set_stdout(redis_conn: Redis, job_id:UUID, bytes_read: bytes):
    """Set the stdout value for the given job."""
    job = jobs.job(redis_conn, job_id)
    if job.is_nothing():
        raise jobs.NoSuchJob(job_id)

    job = job.maybe({}, lambda x: x)
    redis_conn.hset(
        jobs.job_namespace(job_id), key="stdout",
        value=bytes_read.decode("utf-8"))

def update_stdout(redis_conn: Redis, job_id:UUID, bytes_read: bytes):
    """Update the stdout value for the given job."""
    __update_stdout_stderr__(redis_conn, job_id, bytes_read, "stdout")

def update_stderr(redis_conn: Redis, job_id:UUID, bytes_read: bytes):
    """Update the stderr value for the given job."""
    __update_stdout_stderr__(redis_conn, job_id, bytes_read, "stderr")

def set_meta(redis_conn: Redis, job_id: UUID, meta_key: str, meta_val: str):
    job = jobs.job(redis_conn, job_id)
    if job.is_nothing():
        raise jobs.NoSuchJob(job_id)

    redis_conn.hset(jobs.job_namespace(job_id), key=meta_key, value=meta_val)

def run_job(redis_conn: Redis, job_id: UUID):
    """Run the job in an external process."""
    print(f"THE ARGUMENTS TO RUN_JOB:\n\tConnection: {redis_conn}\n\tJob ID: {job_id}\n")

    the_job = jobs.job(redis_conn, job_id)
    if the_job.is_nothing():
        raise jobs.NoSuchJob(job_id)

    with TemporaryDirectory() as tmpdir:
        stdout_file = f"{tmpdir}/{job_id}.stdout"
        stderr_file = f"{tmpdir}/{job_id}.stderr"
        with open(stdout_file, "w+b") as outfl, open(stderr_file, "w+b") as errfl:
            with subprocess.Popen(
                    jobs.command(the_job), stdout=outfl,
                    stderr=errfl) as process:
                while process.poll() is None:
                    update_status(redis_conn, job_id, "running")
                    update_stdout(redis_conn, job_id, outfl.read1())
                    sleep(1)

            update_status(redis_conn, job_id, "completed")
            with open(stdout_file, "rb") as outfl, open(stderr_file, "rb") as errfl:
                set_stdout(redis_conn, job_id, outfl.read())
                update_stderr(redis_conn, job_id, errfl.read())

            os.remove(stdout_file)
            os.remove(stderr_file)

    returncode = process.returncode
    set_meta(redis_conn, job_id, "completion-status",
             ("success" if returncode == 0 else "error"))
    set_meta(redis_conn, job_id, "return-code", returncode)
    return process.returncode

def run_job_parser(parent_parser):
    parser = parent_parser.add_parser(
        "run-job",
        help="run job with given id")
    parser.add_argument(
        "job_id", type=UUID4, help="A string representing a UUID4 value.")
    parser.set_defaults(
        run=lambda conn, args, parser: run_job(conn, args.job_id))

def add_subparsers(parent_parser, *subparser_fns):
    sub_parsers = parent_parser.add_subparsers(
        title="subcommands", description="valid subcommands", required=True)
    for parser_fn in subparser_fns:
        parser_fn(sub_parsers)
        pass

    return parent_parser

def parse_cli_args():
    parser = add_subparsers(argparse.ArgumentParser(
        description=sys.modules[__name__].__doc__.strip()), run_job_parser)
    parser.add_argument(
        "--redis-uri", required=True,
        help=(
            "URI to use to connect to job management db."
            "The URI should be of the form "
            "'<scheme>://<user>:<passwd>@<host>:<port>/<path>'"),
        type=urlparse)
    return parser, parser.parse_args()

def launch_manager():
    parser, args = parse_cli_args()
    with redis_connection(args.redis_uri) as conn:
        try:
            return args.run(conn, args, parser)
        except Exception as nsj:
            prev_msg = (
                conn.hget(f"{jobs.JOBS_NAMESPACE}:manager", key="stderr") or "")
            if bool(prev_msg):
                prev_msg = f"{prev_msg}\n"

            notfoundmsg = (
                f"{prev_msg}"
                f"{datetime.now().isoformat()}: {type(nsj).__name__}: {traceback.format_exc()}")
            conn.hset(
                f"{jobs.JOBS_NAMESPACE}:manager",
                key="stderr",
                value=notfoundmsg)

if __name__ == "__main__":
    def run():
        sys.exit(launch_manager())
    run()
