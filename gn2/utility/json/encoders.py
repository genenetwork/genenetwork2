"""Custom JSON encoders"""
from uuid import UUID
from json import JSONEncoder

# Do not use this `__ENCODERS__` variable outside of this module.
__ENCODERS__ = {
    UUID: lambda obj: str(obj)
}

class CustomJSONEncoder(JSONEncoder):
    """Custom JSONEncoder class."""
    def default(self, obj):
        """Serialise `obj` to a JSON representation."""
        obj_type = type(obj)
        if obj_type in __ENCODERS__:
            return __ENCODERS__[obj_type](obj)
        return JSONEncoder.default(self, obj)
