import hashlib
import json
import os
import subprocess

from itertools import chain

from utility.tools import GEMMA_WRAPPER_COMMAND

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
        with open(metadata_filepath) as _file:
            data = json.load(_file)
            geno_file = lookup_file("GENENETWORK_FILES",
                                    "genotype", data.get("geno"))
            pheno_file = lookup_file("TMPDIR", token, data.get("pheno"))
            cmd = f"{GEMMA_WRAPPER_COMMAND} --json"
            if gemma_wrapper_kwargs:
                cmd += (" "  # Add extra space between commands
                        " ".join([f"--{key} {val}" for key, val
                                  in gemma_wrapper_kwargs.items()]))
            cmd += f" -- -g {geno_file} -p {pheno_file}"
            if gemma_kwargs:
                cmd += (" "
                        " ".join([f"-{key} {val}"
                                  for key, val in gemma_kwargs.items()]))
            if args:
                cmd += (" "
                        " ".join([f"{arg}" for arg in args]))
            return cmd
    return -1


def run_gemma_cmd(cmd: str) -> Union[str, int]:
    """Run CMD and return a str that contains the file name, otherwise
signal an error.

    """
    proc = subprocess.Popen(cmd.rstrip().split(" "), stdout=subprocess.PIPE)
    result = {}
    files_ = []
    while True:
        line = proc.stdout.readline().rstrip()
        if not line:  # End of STDOUT
            break
        try:
            result = json.loads(line)
            break
        # Exception is thrown is thrown when an invalid json file is
        # passed.
        except ValueError:
            pass
    files_ = list(
        filter(lambda xs: (xs is not None),
               list(chain(*result.get("files", [])))))
    if len(files_) > 0:
        return files_
    else:
        return -1
