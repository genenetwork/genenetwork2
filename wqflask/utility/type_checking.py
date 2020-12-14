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

def get_float(vars_obj,name,default=None):
    if name in vars_obj:
        if is_float(vars_obj[name]):
            return float(vars_obj[name])
    return default

def get_int(vars_obj,name,default=None):
    if name in vars_obj:
        if is_int(vars_obj[name]):
            return float(vars_obj[name])
    return default

def get_string(vars_obj,name,default=None):
    if name in vars_obj:
        if not vars_obj[name] is None:
            return str(vars_obj[name])
    return default
