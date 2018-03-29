# Type checking functions

def is_float(value):
    try:
        float(value)
        return True
    except:
        return False

def is_int(value):
    try:
        int(value)
        return True
    except:
        return False

def is_str(value):
    if value is None:
        return False
    try:
        str(value)
        return True
    except:
        return False

def get_float(vars,name,default=None):
    if name in vars:
        if is_float(vars[name]):
            return float(vars[name])
    return None

def get_int(vars,name,default=None):
    if name in vars:
        if is_int(vars[name]):
            return float(vars[name])
    return default

def get_string(vars,name,default=None):
    if name in vars:
        if not vars[name] is None:
            return str(vars[name])
    return default
