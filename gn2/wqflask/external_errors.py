"""Errors caused by calls to external services."""
import traceback
from uuid import uuid4

class ExternalRequestError(Exception):
    """Raise when a request to an external endpoint fails."""

    def __init__(self,
                 externaluri: str,
                 error: Exception):
        """Initialise the error message."""
        self.errorid = uuid4()
        self.error = error
        self.extrainfo = extrainfo
        super().__init__(
            f"error-id: {self.errorid}: We got an error of type "
            f"'{type(error).__name__}' trying to access {externaluri}:\n\n "
            f"{''.join(traceback.format_exception(error))}")
