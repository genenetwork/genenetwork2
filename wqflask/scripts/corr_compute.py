"""Compute the correlations."""

import sys
import json
import pickle
import pathlib
import datetime

from flask import g

from gn2_main import app

from wqflask.user_session import UserSession
from wqflask.correlation.show_corr_results import set_template_vars
from wqflask.correlation.correlation_gn3_api import compute_correlation

class UserSessionSimulator():

    def __init__(self, user_id):
        self._user_id = user_id

    @property
    def user_id(self):
        return self._user_id

error_types = {
    "WrongCorrelationType": "Wrong Correlation Type",
    "CalledProcessError": "Called Process Error"
}

def e_time():
    return datetime.datetime.utcnow().isoformat()

def compute(form):
    import subprocess
    from gn3.settings import CORRELATION_COMMAND
    try:
        correlation_results = compute_correlation(form, compute_all=True)
    except Exception as exc:
        return {
            "error-type": error_types[type(exc).__name__],
            "error-message": exc.args[0]
        }

    return set_template_vars(form, correlation_results)

if __name__ == "__main__":
    ARGS_COUNT = 3
    if len(sys.argv) < ARGS_COUNT:
        print(f"{e_time()}: You need to pass the file with the picked form",
              file=sys.stderr)
        sys.exit(1)

    if len(sys.argv) > ARGS_COUNT:
        print(f"{e_time()}: Unknown arguments {sys.argv[ARGS_COUNT:]}",
              file=sys.stderr)
        sys.exit(1)

    filepath = pathlib.Path(sys.argv[1])
    if not filepath.exists():
        print(f"File not found '{filepath}'", file=sys.stderr)
        sys.exit(2)

    with open(filepath, "rb") as pfile:
        form = pickle.Unpickler(pfile).load()

    with app.app_context():
        g.user_session = UserSessionSimulator(sys.argv[2])
        results = compute(form)

    print(json.dumps(results), file=sys.stdout)

    if "error-type" in results:
        print(
            f"{results['error-type']}: {results['error-message']}",
            file=sys.stderr)
        sys.exit(3)

    sys.exit(0)
