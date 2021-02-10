import hashlib
import json
import os

from datetime import datetime
from datetime import timedelta
from math import floor
from redis.client import Redis  # Used only in type hinting
from uuid import uuid4
from typing import Dict
from typing import Optional
from typing import Union


def get_hash_of_dirs(directory: str, verbose: int = 0) -> Union[str, int]:
    """Return the hash of a DIRECTORY"""
    md5hash = hashlib.md5()
    if not os.path.exists(directory):
        return "-1"
    try:
        for root, dirs, files in os.walk(directory):
            for names in files:
                if verbose == 1:
                    print(f"Hashing: {names}")
                filepath = os.path.join(root, names)
                try:
                    f1 = open(filepath, 'r', encoding="utf-8")
                except Exception:
                    # You can't open the file for some reason
                    f1.close()
                    continue
                while 1:
                    # Read file in as little chunks
                    buf = f1.read(4096)
                    if not buf:
                        break
                    md5hash.update(
                        bytearray(hashlib.md5(
                            bytearray(buf, "utf-8")).hexdigest(),
                                  "utf-8"))
                f1.close()
    except Exception as e:
        import traceback
        # Print the stack traceback
        traceback.print_exc(e)
        return -1

    return md5hash.hexdigest()


def lookup_file(environ_var: str,
                file_home_dir: str,
                file_name: str) -> Union[str, int]:
    """Look up FILE_NAME in the path defined by
ENVIRON_VAR/FILE_HOME_DIR/; If ENVIRON_VAR/FILE_HOME_DIR/FILE_NAME
does not exist, return -1

    """
    _dir = os.environ.get(environ_var)
    if _dir:
        _file = os.path.join(_dir, file_home_dir, file_name)
        if os.path.isfile(_file):
            return _file
    return -1


def jsonfile_to_dict(metadata_file: str) -> Union[str, int]:
    try:
        with open(metadata_file) as _file:
            data = json.load(_file)
            return data
    except Exception:
        return -1


def compose_gemma_cmd(
        token: str,
        metadata_filename: str,
        gemma_wrapper_kwargs: Optional[Dict] = None,
        gemma_kwargs: Optional[Dict] = None,
        *args: str) -> Union[str, int]:
    """Compose a valid GEMMA command to run given the correct values.
TOKEN is the hash returned after a successful user upload;
METADATA_FILENAME is the file that contains the metadata;
GEMMA_WRAPPER_KWARGS is a key value pair that contains extra opts for
the gemma_wrapper command; GEMMA_KWARGS are the key value pairs that
are passed to Gemma; and *ARGS are any other argsuments passed to
GEMMA.

    """
    metadata_filepath = lookup_file("TMPDIR", token, metadata_filename)
    if metadata_filepath != -1:
        data = jsonfile_to_dict(metadata_filepath)
        if data != -1:
            geno_file = lookup_file("GENENETWORK_FILES",
                                    "genotype", data.get("geno"))
            pheno_file = lookup_file("TMPDIR", token, data.get("pheno"))
            # Return in the event the geno or pheno files don't exist!
            if -1 in [geno_file, pheno_file]:
                return -1
            cmd = f"{GEMMA_WRAPPER_COMMAND} --json"
            if gemma_wrapper_kwargs:
                cmd += (" "  # Add extra space between commands
                        " ".join([f" --{key} {val}" for key, val
                                  in gemma_wrapper_kwargs.items()]))
            cmd += f" -- -g {geno_file} -p {pheno_file}"
            if gemma_kwargs:
                cmd += (" "
                        " ".join([f" -{key} {val}"
                                  for key, val in gemma_kwargs.items()]))
            if args:
                cmd += (" "
                        " ".join([f" {arg}" for arg in args]))
            return cmd
    return -1



def queue_command(cmd: str, redis_conn: Redis) -> Union[int, str]:
    """Given a command, queue it in redis with an initial status of 1.
The following status codes-- in the hash-- are used:

    queued:  Yet to be running
    running: Still running
    success: Successful completion
    error:   Erroneous completion

A UNIQUE_ID is returned which can be used by the redis worker to check
the status of the background command.

    """
    unique_id = ("cmd::"
                 f"{datetime.now().strftime('%Y-%m-%d%H-%M%S-%M%S-')}"
                 f"{str(uuid4())}")
    try:
        ttl = datetime.today() + timedelta(minutes=30)
        for key, value in {"cmd": cmd,
                           "result": "", "status": "queued"}.items():
            redis_conn.hset(key, value, unique_id)
            redis_conn.rpush("GN2::job-queue",
                             unique_id)
            redis_conn.expire(key, floor(ttl.timestamp()))
        return unique_id
    except Exception:
        return -1
